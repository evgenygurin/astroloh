"""
Recommendation engine with collaborative filtering, content-based filtering, and hybrid approaches.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.database import User, HoroscopeRequest
from app.models.recommendation_models import (
    UserPreference,
    UserInteraction,
    RecommendationItem,
    UserRecommendation,
    UserSimilarity,
    ABTestGroup,
    UserABTestAssignment,
)


class CollaborativeFilter:
    """
    Collaborative filtering recommendation algorithm.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.min_interactions = 5  # Minimum interactions for reliable similarity
        self.similarity_threshold = 0.3  # Minimum similarity score

    async def calculate_user_similarities(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Calculate similarity scores between users based on preferences and behavior.
        
        Args:
            user_id: Target user ID
            
        Returns:
            List of similar users with similarity scores
        """
        try:
            # Get target user preferences
            target_prefs = await self._get_user_preference_vector(user_id)
            if target_prefs is None:
                logger.warning(f"No preferences found for user {user_id}")
                return []

            # Get all other users with sufficient interaction history
            similar_users = []
            
            result = await self.db.execute(
                select(User.id).where(
                    User.id != user_id,
                    User.data_consent == True
                ).limit(1000)  # Limit for performance
            )
            candidate_users = result.scalars().all()

            for candidate_id in candidate_users:
                candidate_prefs = await self._get_user_preference_vector(candidate_id)
                if candidate_prefs is None:
                    continue

                # Calculate preference similarity
                pref_similarity = self._calculate_cosine_similarity(target_prefs, candidate_prefs)
                
                # Calculate behavioral similarity
                behavior_similarity = await self._calculate_behavioral_similarity(
                    user_id, candidate_id
                )
                
                # Calculate astrological similarity
                astro_similarity = await self._calculate_astrological_similarity(
                    user_id, candidate_id
                )

                # Combined similarity score
                overall_similarity = (
                    0.4 * pref_similarity + 
                    0.4 * behavior_similarity + 
                    0.2 * astro_similarity
                )

                if overall_similarity >= self.similarity_threshold:
                    similar_users.append({
                        'user_id': candidate_id,
                        'similarity_score': overall_similarity,
                        'preference_similarity': pref_similarity,
                        'behavior_similarity': behavior_similarity,
                        'astrological_similarity': astro_similarity
                    })

            # Sort by similarity score
            similar_users.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Store similarities in database for future use
            await self._store_user_similarities(user_id, similar_users[:50])
            
            return similar_users[:20]  # Return top 20 similar users

        except Exception as e:
            logger.error(f"Error calculating user similarities: {e}")
            return []

    async def generate_collaborative_recommendations(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on similar users' preferences.
        
        Args:
            user_id: Target user ID
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended items with scores
        """
        try:
            # Get similar users
            similar_users = await self._get_stored_similarities(user_id)
            if not similar_users:
                similar_users = await self.calculate_user_similarities(user_id)

            if not similar_users:
                return []

            # Get items liked by similar users
            item_scores = {}
            
            for similar_user in similar_users[:10]:  # Top 10 similar users
                user_interactions = await self._get_positive_user_interactions(
                    similar_user['user_id']
                )
                
                similarity_weight = similar_user['similarity_score']
                
                for interaction in user_interactions:
                    item_key = f"{interaction.content_category}:{interaction.content_id}"
                    if item_key not in item_scores:
                        item_scores[item_key] = 0
                    
                    # Weight by similarity and interaction quality
                    interaction_weight = self._get_interaction_weight(interaction)
                    item_scores[item_key] += similarity_weight * interaction_weight

            # Convert to recommendations
            recommendations = []
            target_user_interactions = await self._get_user_interaction_history(user_id)
            interacted_items = {
                f"{i.content_category}:{i.content_id}" for i in target_user_interactions
            }

            for item_key, score in sorted(item_scores.items(), key=lambda x: x[1], reverse=True):
                if item_key not in interacted_items and len(recommendations) < limit:
                    category, item_id = item_key.split(':', 1)
                    recommendations.append({
                        'content_category': category,
                        'content_id': item_id,
                        'score': min(score, 1.0),  # Normalize to 0-1
                        'algorithm': 'collaborative_filtering',
                        'reason': f'Users similar to you enjoyed this {category}'
                    })

            return recommendations

        except Exception as e:
            logger.error(f"Error generating collaborative recommendations: {e}")
            return []

    async def _get_user_preference_vector(self, user_id: uuid.UUID) -> Optional[np.ndarray]:
        """Get user preference vector for similarity calculation."""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            return None

        # Create preference vector
        vector = np.array([
            prefs.career_interest,
            prefs.love_interest,
            prefs.health_interest,
            prefs.finance_interest,
            prefs.family_interest,
            prefs.spiritual_interest,
            self._encode_categorical(prefs.communication_style, ['formal', 'casual', 'balanced']),
            self._encode_categorical(prefs.complexity_level, ['beginner', 'intermediate', 'advanced']),
            self._encode_categorical(prefs.emotional_tone, ['positive', 'neutral', 'realistic']),
            float(prefs.optimal_frequency) / 7.0,  # Normalize frequency to 0-1
        ])
        
        return vector

    async def _calculate_behavioral_similarity(
        self, user_id1: uuid.UUID, user_id2: uuid.UUID
    ) -> float:
        """Calculate behavioral similarity between two users."""
        try:
            # Get interaction patterns for both users
            patterns1 = await self._get_interaction_patterns(user_id1)
            patterns2 = await self._get_interaction_patterns(user_id2)
            
            if not patterns1 or not patterns2:
                return 0.0

            # Compare patterns
            similarity_factors = []
            
            # Time of day preferences
            if 'time_preferences' in patterns1 and 'time_preferences' in patterns2:
                time_sim = self._calculate_time_preference_similarity(
                    patterns1['time_preferences'], patterns2['time_preferences']
                )
                similarity_factors.append(time_sim)
            
            # Content category preferences
            if 'category_preferences' in patterns1 and 'category_preferences' in patterns2:
                cat_sim = self._calculate_category_similarity(
                    patterns1['category_preferences'], patterns2['category_preferences']
                )
                similarity_factors.append(cat_sim)
            
            # Interaction frequency
            if 'avg_frequency' in patterns1 and 'avg_frequency' in patterns2:
                freq_sim = 1.0 - abs(patterns1['avg_frequency'] - patterns2['avg_frequency']) / 7.0
                freq_sim = max(0.0, freq_sim)
                similarity_factors.append(freq_sim)

            return np.mean(similarity_factors) if similarity_factors else 0.0

        except Exception as e:
            logger.error(f"Error calculating behavioral similarity: {e}")
            return 0.0

    async def _calculate_astrological_similarity(
        self, user_id1: uuid.UUID, user_id2: uuid.UUID
    ) -> float:
        """Calculate astrological compatibility between users."""
        try:
            # Get user zodiac signs
            result1 = await self.db.execute(select(User).where(User.id == user_id1))
            result2 = await self.db.execute(select(User).where(User.id == user_id2))
            
            user1 = result1.scalar_one_or_none()
            user2 = result2.scalar_one_or_none()
            
            if not user1 or not user2 or not user1.zodiac_sign or not user2.zodiac_sign:
                return 0.0

            # Basic zodiac compatibility matrix (simplified)
            compatibility_matrix = self._get_zodiac_compatibility_matrix()
            
            sign1 = user1.zodiac_sign.lower()
            sign2 = user2.zodiac_sign.lower()
            
            if sign1 in compatibility_matrix and sign2 in compatibility_matrix[sign1]:
                return compatibility_matrix[sign1][sign2]
            
            return 0.5  # Default neutral compatibility

        except Exception as e:
            logger.error(f"Error calculating astrological similarity: {e}")
            return 0.0

    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Reshape vectors for sklearn
            vec1 = vec1.reshape(1, -1)
            vec2 = vec2.reshape(1, -1)
            
            similarity = cosine_similarity(vec1, vec2)[0][0]
            return float(similarity)
        except:
            return 0.0

    def _encode_categorical(self, value: str, categories: List[str]) -> float:
        """Encode categorical value as numeric."""
        try:
            return float(categories.index(value)) / (len(categories) - 1)
        except (ValueError, ZeroDivisionError):
            return 0.5

    async def _get_positive_user_interactions(self, user_id: uuid.UUID) -> List[UserInteraction]:
        """Get interactions with positive feedback."""
        result = await self.db.execute(
            select(UserInteraction).where(
                UserInteraction.user_id == user_id,
                UserInteraction.response_rating >= 4.0
            ).order_by(desc(UserInteraction.timestamp)).limit(50)
        )
        return result.scalars().all()

    async def _get_user_interaction_history(self, user_id: uuid.UUID) -> List[UserInteraction]:
        """Get all user interactions."""
        result = await self.db.execute(
            select(UserInteraction).where(UserInteraction.user_id == user_id)
        )
        return result.scalars().all()

    def _get_interaction_weight(self, interaction: UserInteraction) -> float:
        """Calculate weight for interaction based on its quality."""
        weight = 0.5  # Base weight
        
        if interaction.response_rating:
            weight *= (interaction.response_rating / 5.0)
        
        if interaction.interaction_type == 'save':
            weight *= 1.5
        elif interaction.interaction_type == 'share':
            weight *= 1.3
        elif interaction.interaction_type == 'feedback':
            weight *= 1.2

        return min(weight, 1.0)

    async def _get_interaction_patterns(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Analyze user interaction patterns."""
        result = await self.db.execute(
            select(UserInteraction).where(UserInteraction.user_id == user_id)
            .order_by(desc(UserInteraction.timestamp)).limit(100)
        )
        interactions = result.scalars().all()
        
        if not interactions:
            return {}

        patterns = {}
        
        # Time preferences
        time_counts = {}
        for interaction in interactions:
            if interaction.time_of_day:
                time_counts[interaction.time_of_day] = time_counts.get(interaction.time_of_day, 0) + 1
        
        if time_counts:
            patterns['time_preferences'] = time_counts
        
        # Category preferences
        category_counts = {}
        for interaction in interactions:
            if interaction.content_category:
                category_counts[interaction.content_category] = category_counts.get(
                    interaction.content_category, 0
                ) + 1
        
        if category_counts:
            patterns['category_preferences'] = category_counts
        
        # Average frequency (days between interactions)
        if len(interactions) > 1:
            time_diffs = []
            for i in range(1, len(interactions)):
                diff = (interactions[i-1].timestamp - interactions[i].timestamp).days
                if diff > 0:
                    time_diffs.append(diff)
            
            if time_diffs:
                patterns['avg_frequency'] = np.mean(time_diffs)

        return patterns

    def _calculate_time_preference_similarity(self, prefs1: Dict, prefs2: Dict) -> float:
        """Calculate similarity in time preferences."""
        all_times = set(prefs1.keys()) | set(prefs2.keys())
        if not all_times:
            return 0.0

        total_diff = 0
        for time_slot in all_times:
            count1 = prefs1.get(time_slot, 0)
            count2 = prefs2.get(time_slot, 0)
            total1 = sum(prefs1.values())
            total2 = sum(prefs2.values())
            
            pref1 = count1 / total1 if total1 > 0 else 0
            pref2 = count2 / total2 if total2 > 0 else 0
            
            total_diff += abs(pref1 - pref2)

        return max(0.0, 1.0 - (total_diff / len(all_times)))

    def _calculate_category_similarity(self, prefs1: Dict, prefs2: Dict) -> float:
        """Calculate similarity in content category preferences."""
        all_categories = set(prefs1.keys()) | set(prefs2.keys())
        if not all_categories:
            return 0.0

        # Use cosine similarity for category preferences
        vec1 = np.array([prefs1.get(cat, 0) for cat in all_categories])
        vec2 = np.array([prefs2.get(cat, 0) for cat in all_categories])
        
        return self._calculate_cosine_similarity(vec1, vec2)

    def _get_zodiac_compatibility_matrix(self) -> Dict[str, Dict[str, float]]:
        """Simplified zodiac compatibility matrix."""
        # This is a simplified version - in a real implementation, 
        # you'd want a more comprehensive astrological compatibility system
        signs = [
            'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
            'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
        ]
        
        # Basic compatibility (0.0-1.0)
        matrix = {}
        for i, sign1 in enumerate(signs):
            matrix[sign1] = {}
            for j, sign2 in enumerate(signs):
                if i == j:
                    matrix[sign1][sign2] = 1.0  # Same sign
                else:
                    # Simple compatibility based on element and modality
                    compatibility = self._calculate_basic_zodiac_compatibility(i, j)
                    matrix[sign1][sign2] = compatibility
        
        return matrix

    def _calculate_basic_zodiac_compatibility(self, index1: int, index2: int) -> float:
        """Calculate basic zodiac compatibility."""
        # Elements: Fire (0,4,8), Earth (1,5,9), Air (2,6,10), Water (3,7,11)
        element1 = index1 % 4
        element2 = index2 % 4
        
        # Fire and Air are compatible, Earth and Water are compatible
        if (element1 in [0, 2] and element2 in [0, 2]) or (element1 in [1, 3] and element2 in [1, 3]):
            base_compatibility = 0.8
        elif abs(element1 - element2) == 2:  # Opposite elements
            base_compatibility = 0.6
        else:
            base_compatibility = 0.7

        # Modality compatibility (Cardinal, Fixed, Mutable)
        modality1 = index1 // 4
        modality2 = index2 // 4
        
        if modality1 == modality2:
            base_compatibility += 0.1
        
        return min(1.0, base_compatibility)

    async def _store_user_similarities(self, user_id: uuid.UUID, similar_users: List[Dict]) -> None:
        """Store calculated similarities in database."""
        try:
            # Delete old similarities for this user
            await self.db.execute(
                select(UserSimilarity).where(UserSimilarity.user_id_1 == user_id)
            )
            
            # Store new similarities
            for similar_user in similar_users:
                similarity = UserSimilarity(
                    user_id_1=user_id,
                    user_id_2=similar_user['user_id'],
                    overall_similarity=similar_user['similarity_score'],
                    preference_similarity=similar_user.get('preference_similarity'),
                    behavior_similarity=similar_user.get('behavior_similarity'),
                    astrological_similarity=similar_user.get('astrological_similarity'),
                    calculation_method='collaborative_filtering_v1',
                    data_points_used=len(similar_users)
                )
                self.db.add(similarity)
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing user similarities: {e}")

    async def _get_stored_similarities(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get previously calculated similarities from database."""
        try:
            # Get similarities calculated within last 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            result = await self.db.execute(
                select(UserSimilarity).where(
                    UserSimilarity.user_id_1 == user_id,
                    UserSimilarity.calculation_date >= cutoff_date
                ).order_by(desc(UserSimilarity.overall_similarity)).limit(20)
            )
            
            similarities = result.scalars().all()
            
            return [
                {
                    'user_id': sim.user_id_2,
                    'similarity_score': sim.overall_similarity,
                    'preference_similarity': sim.preference_similarity,
                    'behavior_similarity': sim.behavior_similarity,
                    'astrological_similarity': sim.astrological_similarity
                }
                for sim in similarities
            ]
            
        except Exception as e:
            logger.error(f"Error retrieving stored similarities: {e}")
            return []


class ContentBasedFilter:
    """
    Content-based filtering recommendation algorithm.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

    async def generate_content_recommendations(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on content similarity to user preferences.
        
        Args:
            user_id: Target user ID
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended items with scores
        """
        try:
            # Get user preferences
            user_profile = await self._build_user_content_profile(user_id)
            if not user_profile:
                return []

            # Get available recommendation items
            result = await self.db.execute(
                select(RecommendationItem).where(
                    RecommendationItem.is_active == True
                ).limit(1000)
            )
            available_items = result.scalars().all()
            
            if not available_items:
                return []

            # Calculate content similarity scores
            recommendations = []
            user_history = await self._get_user_content_history(user_id)
            
            for item in available_items:
                # Skip items user has already interacted with
                if self._has_user_seen_item(item, user_history):
                    continue
                
                # Calculate similarity score
                similarity_score = await self._calculate_content_similarity(user_profile, item)
                
                if similarity_score > 0.3:  # Minimum threshold
                    recommendations.append({
                        'item': item,
                        'score': similarity_score,
                        'algorithm': 'content_based',
                        'reason': self._generate_content_reason(user_profile, item)
                    })

            # Sort by score and return top recommendations
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error generating content-based recommendations: {e}")
            return []

    async def _build_user_content_profile(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Build user content profile from preferences and interactions."""
        try:
            # Get user preferences
            result = await self.db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            prefs = result.scalar_one_or_none()
            
            if not prefs:
                return None

            # Get user interactions to understand content preferences
            interactions_result = await self.db.execute(
                select(UserInteraction).where(
                    UserInteraction.user_id == user_id,
                    UserInteraction.response_rating >= 3.0
                ).order_by(desc(UserInteraction.timestamp)).limit(50)
            )
            interactions = interactions_result.scalars().all()

            profile = {
                'interest_scores': {
                    'career': prefs.career_interest,
                    'love': prefs.love_interest,
                    'health': prefs.health_interest,
                    'finance': prefs.finance_interest,
                    'family': prefs.family_interest,
                    'spiritual': prefs.spiritual_interest,
                },
                'communication_style': prefs.communication_style,
                'complexity_level': prefs.complexity_level,
                'emotional_tone': prefs.emotional_tone,
                'preferred_categories': self._extract_preferred_categories(interactions),
                'preferred_tags': self._extract_preferred_tags(interactions),
                'zodiac_sign': None,  # Will be filled from User table
                'cultural_context': prefs.cultural_context,
            }

            # Get zodiac sign from User table
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user:
                profile['zodiac_sign'] = user.zodiac_sign

            return profile

        except Exception as e:
            logger.error(f"Error building user content profile: {e}")
            return None

    async def _calculate_content_similarity(
        self, user_profile: Dict[str, Any], item: RecommendationItem
    ) -> float:
        """Calculate similarity between user profile and content item."""
        try:
            similarity_factors = []

            # Category interest matching
            if item.item_category:
                category_interest = user_profile['interest_scores'].get(item.item_category, 0.5)
                similarity_factors.append(category_interest)

            # Zodiac sign relevance
            if item.zodiac_signs and user_profile.get('zodiac_sign'):
                user_sign = user_profile['zodiac_sign'].lower()
                if user_sign in [sign.lower() for sign in item.zodiac_signs]:
                    similarity_factors.append(1.0)
                else:
                    # Check compatibility with user's zodiac sign
                    compatibility_score = self._get_zodiac_item_compatibility(
                        user_sign, item.zodiac_signs
                    )
                    similarity_factors.append(compatibility_score)

            # Tag matching
            if item.tags and user_profile.get('preferred_tags'):
                tag_similarity = self._calculate_tag_similarity(
                    user_profile['preferred_tags'], item.tags
                )
                similarity_factors.append(tag_similarity)

            # Quality scores
            quality_score = (
                item.popularity_score * 0.3 +
                item.engagement_score * 0.4 +
                item.feedback_score * 0.3
            )
            similarity_factors.append(quality_score)

            # Temporal relevance
            temporal_score = self._calculate_temporal_relevance(item)
            similarity_factors.append(temporal_score)

            # Calculate weighted average
            if similarity_factors:
                return np.mean(similarity_factors)
            else:
                return 0.5  # Default neutral score

        except Exception as e:
            logger.error(f"Error calculating content similarity: {e}")
            return 0.0

    def _extract_preferred_categories(self, interactions: List[UserInteraction]) -> Dict[str, float]:
        """Extract preferred content categories from interactions."""
        category_counts = {}
        total_interactions = len(interactions)
        
        for interaction in interactions:
            if interaction.content_category:
                category_counts[interaction.content_category] = (
                    category_counts.get(interaction.content_category, 0) + 1
                )

        # Convert to preferences (0-1 scale)
        preferences = {}
        for category, count in category_counts.items():
            preferences[category] = count / total_interactions if total_interactions > 0 else 0.0

        return preferences

    def _extract_preferred_tags(self, interactions: List[UserInteraction]) -> List[str]:
        """Extract preferred tags from user interactions."""
        # This would need to be implemented based on how tags are stored
        # in interaction context_data
        tags = []
        for interaction in interactions:
            if interaction.context_data and 'tags' in interaction.context_data:
                tags.extend(interaction.context_data['tags'])
        
        return list(set(tags))  # Return unique tags

    def _calculate_tag_similarity(self, user_tags: List[str], item_tags: List[str]) -> float:
        """Calculate Jaccard similarity between user tags and item tags."""
        if not user_tags or not item_tags:
            return 0.0

        user_set = set(tag.lower() for tag in user_tags)
        item_set = set(tag.lower() for tag in item_tags)
        
        intersection = len(user_set & item_set)
        union = len(user_set | item_set)
        
        return intersection / union if union > 0 else 0.0

    def _get_zodiac_item_compatibility(self, user_sign: str, item_signs: List[str]) -> float:
        """Calculate compatibility between user's zodiac sign and item's target signs."""
        if not user_sign or not item_signs:
            return 0.5

        # Get compatibility scores with all item signs
        compatibility_scores = []
        compatibility_matrix = CollaborativeFilter(self.db)._get_zodiac_compatibility_matrix()
        
        user_sign_lower = user_sign.lower()
        if user_sign_lower in compatibility_matrix:
            for item_sign in item_signs:
                item_sign_lower = item_sign.lower()
                if item_sign_lower in compatibility_matrix[user_sign_lower]:
                    compatibility_scores.append(
                        compatibility_matrix[user_sign_lower][item_sign_lower]
                    )

        return max(compatibility_scores) if compatibility_scores else 0.5

    def _calculate_temporal_relevance(self, item: RecommendationItem) -> float:
        """Calculate temporal relevance of an item."""
        now = datetime.utcnow()
        
        # Check if item has expired
        if item.valid_until and now > item.valid_until:
            return 0.0
        
        # Check if item is not yet valid
        if item.valid_from and now < item.valid_from:
            return 0.0
        
        # Check seasonal relevance
        if item.seasonal_relevance:
            current_month = now.month
            seasonal_score = item.seasonal_relevance.get(str(current_month), 0.5)
            return seasonal_score
        
        return 1.0  # Default full relevance

    async def _get_user_content_history(self, user_id: uuid.UUID) -> List[str]:
        """Get list of content items user has already seen."""
        result = await self.db.execute(
            select(UserInteraction.content_id).where(
                UserInteraction.user_id == user_id,
                UserInteraction.content_id.isnot(None)
            )
        )
        return [content_id for content_id in result.scalars().all() if content_id]

    def _has_user_seen_item(self, item: RecommendationItem, user_history: List[str]) -> bool:
        """Check if user has already seen this item."""
        return item.item_identifier in user_history

    def _generate_content_reason(self, user_profile: Dict[str, Any], item: RecommendationItem) -> str:
        """Generate explanation for why this item was recommended."""
        reasons = []
        
        # Interest matching
        if item.item_category in user_profile['interest_scores']:
            interest_score = user_profile['interest_scores'][item.item_category]
            if interest_score > 0.7:
                reasons.append(f"matches your high interest in {item.item_category}")
        
        # Zodiac relevance
        if item.zodiac_signs and user_profile.get('zodiac_sign'):
            user_sign = user_profile['zodiac_sign']
            if user_sign.lower() in [sign.lower() for sign in item.zodiac_signs]:
                reasons.append(f"specifically relevant for {user_sign}")
        
        # Quality
        if item.engagement_score > 0.8:
            reasons.append("highly engaging content")
        
        if reasons:
            return f"Recommended because it {', '.join(reasons)}"
        else:
            return "Recommended based on your preferences"


class HybridRecommendationEngine:
    """
    Hybrid recommendation engine combining collaborative and content-based filtering.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.collaborative_filter = CollaborativeFilter(db_session)
        self.content_filter = ContentBasedFilter(db_session)
        
        # Algorithm weights
        self.collaborative_weight = 0.6
        self.content_weight = 0.4
        self.diversity_factor = 0.3  # Factor to ensure recommendation diversity

    async def generate_hybrid_recommendations(
        self, user_id: uuid.UUID, limit: int = 10, include_reasoning: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate hybrid recommendations combining multiple algorithms.
        
        Args:
            user_id: Target user ID
            limit: Maximum number of recommendations
            include_reasoning: Whether to include explanation for recommendations
            
        Returns:
            List of recommended items with hybrid scores
        """
        try:
            # Get recommendations from both algorithms
            collaborative_recs = await self.collaborative_filter.generate_collaborative_recommendations(
                user_id, limit * 2
            )
            content_recs = await self.content_filter.generate_content_recommendations(
                user_id, limit * 2
            )

            # Combine and score recommendations
            hybrid_recs = {}
            
            # Add collaborative filtering recommendations
            for rec in collaborative_recs:
                key = f"{rec['content_category']}:{rec['content_id']}"
                hybrid_recs[key] = {
                    'content_category': rec['content_category'],
                    'content_id': rec['content_id'],
                    'collaborative_score': rec['score'],
                    'content_score': 0.0,
                    'collaborative_reason': rec.get('reason', ''),
                    'content_reason': '',
                }

            # Add content-based recommendations
            for rec in content_recs:
                item = rec['item']
                key = f"{item.item_category}:{item.item_identifier}"
                
                if key not in hybrid_recs:
                    hybrid_recs[key] = {
                        'content_category': item.item_category,
                        'content_id': item.item_identifier,
                        'collaborative_score': 0.0,
                        'content_score': rec['score'],
                        'collaborative_reason': '',
                        'content_reason': rec.get('reason', ''),
                    }
                else:
                    hybrid_recs[key]['content_score'] = rec['score']
                    hybrid_recs[key]['content_reason'] = rec.get('reason', '')

            # Calculate hybrid scores
            final_recommendations = []
            for key, rec in hybrid_recs.items():
                hybrid_score = (
                    self.collaborative_weight * rec['collaborative_score'] +
                    self.content_weight * rec['content_score']
                )
                
                # Apply diversity bonus for items that have both types of signals
                if rec['collaborative_score'] > 0 and rec['content_score'] > 0:
                    hybrid_score *= (1 + self.diversity_factor)
                
                # Combine reasoning
                reasons = []
                if rec['collaborative_reason']:
                    reasons.append(rec['collaborative_reason'])
                if rec['content_reason']:
                    reasons.append(rec['content_reason'])
                
                final_rec = {
                    'content_category': rec['content_category'],
                    'content_id': rec['content_id'],
                    'hybrid_score': min(hybrid_score, 1.0),  # Cap at 1.0
                    'collaborative_score': rec['collaborative_score'],
                    'content_score': rec['content_score'],
                    'algorithm': 'hybrid',
                }
                
                if include_reasoning and reasons:
                    final_rec['reason'] = ' | '.join(reasons)
                
                final_recommendations.append(final_rec)

            # Sort by hybrid score and apply diversity filtering
            final_recommendations.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            # Apply diversity filtering to avoid too many recommendations from same category
            diverse_recommendations = self._apply_diversity_filtering(
                final_recommendations, limit
            )
            
            # Store recommendations in database for tracking
            await self._store_recommendations(user_id, diverse_recommendations)
            
            return diverse_recommendations

        except Exception as e:
            logger.error(f"Error generating hybrid recommendations: {e}")
            return []

    def _apply_diversity_filtering(
        self, recommendations: List[Dict[str, Any]], limit: int
    ) -> List[Dict[str, Any]]:
        """Apply diversity filtering to ensure variety in recommendations."""
        if len(recommendations) <= limit:
            return recommendations

        diverse_recs = []
        category_counts = {}
        max_per_category = max(2, limit // 3)  # At most 1/3 from same category

        for rec in recommendations:
            category = rec['content_category']
            current_count = category_counts.get(category, 0)
            
            if current_count < max_per_category or len(diverse_recs) < limit * 0.7:
                diverse_recs.append(rec)
                category_counts[category] = current_count + 1
                
                if len(diverse_recs) >= limit:
                    break

        # Fill remaining slots with highest-scored items if we're under limit
        if len(diverse_recs) < limit:
            remaining_slots = limit - len(diverse_recs)
            added_keys = {
                f"{rec['content_category']}:{rec['content_id']}" for rec in diverse_recs
            }
            
            for rec in recommendations:
                key = f"{rec['content_category']}:{rec['content_id']}"
                if key not in added_keys:
                    diverse_recs.append(rec)
                    remaining_slots -= 1
                    if remaining_slots <= 0:
                        break

        return diverse_recs

    async def _store_recommendations(
        self, user_id: uuid.UUID, recommendations: List[Dict[str, Any]]
    ) -> None:
        """Store generated recommendations in database for tracking."""
        try:
            for rec in recommendations:
                # Try to find or create recommendation item
                result = await self.db.execute(
                    select(RecommendationItem).where(
                        RecommendationItem.item_type == rec['content_category'],
                        RecommendationItem.item_identifier == rec['content_id']
                    )
                )
                item = result.scalar_one_or_none()
                
                if not item:
                    # Create new recommendation item
                    item = RecommendationItem(
                        item_type=rec['content_category'],
                        item_category=rec['content_category'],
                        item_identifier=rec['content_id'],
                        title=f"{rec['content_category']} recommendation",
                        description=rec.get('reason', 'Personalized recommendation')
                    )
                    self.db.add(item)
                    await self.db.flush()  # Get the ID

                # Create user recommendation record
                user_rec = UserRecommendation(
                    user_id=user_id,
                    item_id=item.id,
                    relevance_score=rec['hybrid_score'],
                    confidence_score=min(rec['collaborative_score'] + rec['content_score'], 1.0),
                    priority_score=rec['hybrid_score'],
                    algorithm_used='hybrid',
                    algorithm_version='1.0',
                    recommendation_reason=rec.get('reason'),
                    context_factors={
                        'collaborative_score': rec['collaborative_score'],
                        'content_score': rec['content_score'],
                    },
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                self.db.add(user_rec)

            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error storing recommendations: {e}")


class TemporalPatternAnalyzer:
    """
    Analyzer for temporal patterns in user behavior.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def analyze_user_temporal_patterns(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Analyze user's temporal engagement patterns.
        
        Args:
            user_id: Target user ID
            
        Returns:
            Dictionary with temporal pattern analysis
        """
        try:
            # Get user interactions from last 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            result = await self.db.execute(
                select(UserInteraction).where(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= cutoff_date
                ).order_by(UserInteraction.timestamp)
            )
            interactions = result.scalars().all()

            if not interactions:
                return {}

            patterns = {}
            
            # Analyze daily patterns
            patterns['daily_patterns'] = self._analyze_daily_patterns(interactions)
            
            # Analyze weekly patterns
            patterns['weekly_patterns'] = self._analyze_weekly_patterns(interactions)
            
            # Analyze engagement frequency
            patterns['engagement_frequency'] = self._analyze_engagement_frequency(interactions)
            
            # Analyze session duration patterns
            patterns['session_patterns'] = self._analyze_session_patterns(interactions)
            
            # Predict optimal engagement times
            patterns['optimal_times'] = self._predict_optimal_engagement_times(patterns)
            
            return patterns

        except Exception as e:
            logger.error(f"Error analyzing temporal patterns: {e}")
            return {}

    def _analyze_daily_patterns(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze daily engagement patterns."""
        hourly_activity = [0] * 24
        
        for interaction in interactions:
            hour = interaction.timestamp.hour
            hourly_activity[hour] += 1

        # Find peak activity hours
        peak_hours = []
        avg_activity = np.mean(hourly_activity)
        
        for hour, activity in enumerate(hourly_activity):
            if activity > avg_activity * 1.5:  # 50% above average
                peak_hours.append(hour)

        return {
            'hourly_distribution': hourly_activity,
            'peak_hours': peak_hours,
            'most_active_hour': int(np.argmax(hourly_activity)),
            'least_active_hour': int(np.argmin(hourly_activity)),
        }

    def _analyze_weekly_patterns(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze weekly engagement patterns."""
        daily_activity = [0] * 7  # Monday = 0, Sunday = 6
        
        for interaction in interactions:
            day_of_week = interaction.timestamp.weekday()
            daily_activity[day_of_week] += 1

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'daily_distribution': daily_activity,
            'most_active_day': days[np.argmax(daily_activity)],
            'least_active_day': days[np.argmin(daily_activity)],
            'weekend_vs_weekday': {
                'weekday_avg': np.mean(daily_activity[:5]),
                'weekend_avg': np.mean(daily_activity[5:]),
            }
        }

    def _analyze_engagement_frequency(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze user engagement frequency patterns."""
        if len(interactions) < 2:
            return {'frequency_days': 7, 'consistency_score': 0.0}

        # Calculate gaps between interactions
        gaps = []
        for i in range(1, len(interactions)):
            gap = (interactions[i].timestamp - interactions[i-1].timestamp).total_seconds() / 86400
            gaps.append(gap)

        return {
            'average_gap_days': np.mean(gaps),
            'median_gap_days': np.median(gaps),
            'consistency_score': 1.0 / (1.0 + np.std(gaps)),  # Higher score = more consistent
            'frequency_category': self._categorize_frequency(np.mean(gaps)),
        }

    def _analyze_session_patterns(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze session duration and intensity patterns."""
        session_durations = [
            interaction.session_duration 
            for interaction in interactions 
            if interaction.session_duration is not None
        ]
        
        if not session_durations:
            return {}

        return {
            'average_duration': np.mean(session_durations),
            'median_duration': np.median(session_durations),
            'session_length_category': self._categorize_session_length(np.mean(session_durations)),
        }

    def _predict_optimal_engagement_times(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Predict optimal times for user engagement."""
        optimal_times = {}
        
        if 'daily_patterns' in patterns:
            daily = patterns['daily_patterns']
            optimal_times['best_hours'] = daily['peak_hours'][:3]  # Top 3 hours
            
        if 'weekly_patterns' in patterns:
            weekly = patterns['weekly_patterns']
            optimal_times['best_day'] = weekly['most_active_day']
            
        if 'engagement_frequency' in patterns:
            freq = patterns['engagement_frequency']
            optimal_times['recommended_frequency'] = max(1, int(freq['average_gap_days']))

        return optimal_times

    def _categorize_frequency(self, avg_gap_days: float) -> str:
        """Categorize user engagement frequency."""
        if avg_gap_days <= 1:
            return 'daily'
        elif avg_gap_days <= 3:
            return 'frequent'
        elif avg_gap_days <= 7:
            return 'weekly'
        elif avg_gap_days <= 30:
            return 'occasional'
        else:
            return 'rare'

    def _categorize_session_length(self, avg_duration: float) -> str:
        """Categorize session length."""
        if avg_duration <= 30:
            return 'quick'
        elif avg_duration <= 180:
            return 'normal'
        else:
            return 'extended'


class SeasonalAdaptationEngine:
    """
    Engine for adapting recommendations based on seasonal and astrological cycles.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def apply_seasonal_adaptation(
        self, recommendations: List[Dict[str, Any]], user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Apply seasonal adaptation to recommendations.
        
        Args:
            recommendations: Base recommendations
            user_id: Target user ID
            
        Returns:
            Seasonally adapted recommendations
        """
        try:
            # Get current astrological context
            astro_context = await self._get_current_astrological_context()
            
            # Get user's birth data for personalized seasonal factors
            user_context = await self._get_user_seasonal_context(user_id)
            
            # Apply seasonal scoring
            adapted_recs = []
            for rec in recommendations:
                seasonal_score = self._calculate_seasonal_relevance(
                    rec, astro_context, user_context
                )
                
                # Adjust recommendation score based on seasonal relevance
                original_score = rec.get('hybrid_score', rec.get('score', 0.5))
                adapted_score = original_score * (0.7 + 0.3 * seasonal_score)
                
                adapted_rec = rec.copy()
                adapted_rec['seasonal_score'] = seasonal_score
                adapted_rec['adapted_score'] = adapted_score
                adapted_rec['seasonal_context'] = astro_context
                
                adapted_recs.append(adapted_rec)

            # Resort by adapted scores
            adapted_recs.sort(key=lambda x: x['adapted_score'], reverse=True)
            
            return adapted_recs

        except Exception as e:
            logger.error(f"Error applying seasonal adaptation: {e}")
            return recommendations

    async def _get_current_astrological_context(self) -> Dict[str, Any]:
        """Get current astrological context for seasonal adaptation."""
        now = datetime.utcnow()
        
        # Basic seasonal context
        month = now.month
        season = self._get_season(month)
        
        # Moon phase (simplified)
        moon_phase = self._get_moon_phase(now)
        
        # Astrological season (based on sun sign periods)
        astro_season = self._get_astrological_season(month, now.day)
        
        return {
            'month': month,
            'season': season,
            'moon_phase': moon_phase,
            'astrological_season': astro_season,
            'date': now.date(),
        }

    async def _get_user_seasonal_context(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get user-specific seasonal context."""
        try:
            # Get user's zodiac sign and preferences
            result = await self.db.execute(
                select(User, UserPreference).join(
                    UserPreference, User.id == UserPreference.user_id
                ).where(User.id == user_id)
            )
            user_data = result.first()
            
            if not user_data:
                return {}

            user, prefs = user_data
            
            # Calculate personal season (based on birth date and current transits)
            personal_context = {
                'zodiac_sign': user.zodiac_sign,
                'cultural_context': prefs.cultural_context if prefs else None,
                'timezone': prefs.timezone if prefs else None,
            }
            
            # Add birth season if available (would need birth date from encrypted data)
            # This is a placeholder - actual implementation would decrypt birth data
            
            return personal_context

        except Exception as e:
            logger.error(f"Error getting user seasonal context: {e}")
            return {}

    def _calculate_seasonal_relevance(
        self, recommendation: Dict[str, Any], astro_context: Dict[str, Any], user_context: Dict[str, Any]
    ) -> float:
        """Calculate seasonal relevance score for a recommendation."""
        relevance_factors = []
        
        # Base seasonal relevance
        current_season = astro_context['season']
        seasonal_relevance = {
            'spring': {'love': 0.9, 'career': 0.8, 'health': 0.7, 'spiritual': 0.6},
            'summer': {'love': 0.8, 'health': 0.9, 'family': 0.8, 'career': 0.7},
            'autumn': {'career': 0.9, 'finance': 0.8, 'health': 0.7, 'spiritual': 0.8},
            'winter': {'spiritual': 0.9, 'family': 0.8, 'health': 0.6, 'love': 0.7}
        }
        
        category = recommendation.get('content_category', 'general')
        if current_season in seasonal_relevance and category in seasonal_relevance[current_season]:
            relevance_factors.append(seasonal_relevance[current_season][category])
        else:
            relevance_factors.append(0.5)  # Neutral relevance

        # Moon phase relevance
        moon_phase = astro_context['moon_phase']
        moon_relevance = {
            'new': {'career': 0.9, 'spiritual': 0.8},
            'waxing': {'love': 0.8, 'finance': 0.7},
            'full': {'love': 0.9, 'family': 0.8},
            'waning': {'health': 0.8, 'spiritual': 0.9}
        }
        
        if moon_phase in moon_relevance and category in moon_relevance[moon_phase]:
            relevance_factors.append(moon_relevance[moon_phase][category])
        else:
            relevance_factors.append(0.6)

        # Astrological season compatibility
        astro_season = astro_context['astrological_season']
        user_sign = user_context.get('zodiac_sign', '').lower()
        
        if astro_season and user_sign:
            # Higher relevance if current astrological season matches or complements user's sign
            if astro_season.lower() == user_sign:
                relevance_factors.append(1.0)  # Perfect match
            else:
                # Calculate compatibility
                compatibility = self._get_sign_compatibility(user_sign, astro_season.lower())
                relevance_factors.append(compatibility)

        return np.mean(relevance_factors) if relevance_factors else 0.5

    def _get_season(self, month: int) -> str:
        """Get meteorological season from month."""
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'

    def _get_moon_phase(self, date: datetime) -> str:
        """Get approximate moon phase (simplified calculation)."""
        # This is a simplified moon phase calculation
        # In a real implementation, you'd use astronomical libraries
        
        # Approximate lunar cycle (29.5 days)
        days_since_new_moon = (date.toordinal() - datetime(2000, 1, 6).toordinal()) % 29.5
        
        if days_since_new_moon < 3.7:
            return 'new'
        elif days_since_new_moon < 10.6:
            return 'waxing'
        elif days_since_new_moon < 18.4:
            return 'full'
        else:
            return 'waning'

    def _get_astrological_season(self, month: int, day: int) -> str:
        """Get current astrological season (sun sign)."""
        # Approximate sun sign dates
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return 'aries'
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return 'taurus'
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return 'gemini'
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return 'cancer'
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return 'leo'
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return 'virgo'
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return 'libra'
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return 'scorpio'
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return 'sagittarius'
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return 'capricorn'
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return 'aquarius'
        else:
            return 'pisces'

    def _get_sign_compatibility(self, sign1: str, sign2: str) -> float:
        """Get compatibility score between two zodiac signs."""
        # Use the same compatibility matrix as in CollaborativeFilter
        compatibility_matrix = CollaborativeFilter(self.db)._get_zodiac_compatibility_matrix()
        
        if sign1 in compatibility_matrix and sign2 in compatibility_matrix[sign1]:
            return compatibility_matrix[sign1][sign2]
        
        return 0.5  # Default neutral compatibility