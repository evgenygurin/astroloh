"""
Personalization service for dynamic content adaptation and user profiling.
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.database import User, UserSession
from app.models.recommendation_models import UserPreference, UserInteraction
from app.services.encryption import data_protection


class PersonalizationService:
    """
    Service for personalizing user experience based on preferences and behavior.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.data_protection = data_protection

    async def create_user_preference(
        self, user_id: uuid.UUID, preferences: Dict[str, Any]
    ) -> UserPreference:
        """
        Create or update user preferences.
        
        Args:
            user_id: User ID
            preferences: Dictionary of preference values
            
        Returns:
            UserPreference object
        """
        try:
            # Check if preferences already exist
            result = await self.db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            user_pref = result.scalar_one_or_none()

            if user_pref:
                # Update existing preferences
                await self._update_preference_values(user_pref, preferences)
            else:
                # Create new preferences with defaults
                user_pref = UserPreference(
                    user_id=user_id,
                    career_interest=preferences.get('career_interest', 0.5),
                    love_interest=preferences.get('love_interest', 0.5),
                    health_interest=preferences.get('health_interest', 0.5),
                    finance_interest=preferences.get('finance_interest', 0.5),
                    family_interest=preferences.get('family_interest', 0.5),
                    spiritual_interest=preferences.get('spiritual_interest', 0.5),
                    communication_style=preferences.get('communication_style', 'balanced'),
                    complexity_level=preferences.get('complexity_level', 'intermediate'),
                    preferred_length=preferences.get('preferred_length', 'medium'),
                    emotional_tone=preferences.get('emotional_tone', 'neutral'),
                    cultural_context=preferences.get('cultural_context'),
                    timezone=preferences.get('timezone'),
                    language_preference=preferences.get('language_preference', 'ru'),
                    preferred_time_slot=preferences.get('preferred_time_slot'),
                    optimal_frequency=preferences.get('optimal_frequency', 1),
                    use_name_in_responses=preferences.get('use_name_in_responses', False),
                    include_lucky_numbers=preferences.get('include_lucky_numbers', True),
                    include_lucky_colors=preferences.get('include_lucky_colors', True),
                    include_compatibility_hints=preferences.get('include_compatibility_hints', True),
                )
                self.db.add(user_pref)

            await self.db.commit()
            await self.db.refresh(user_pref)
            return user_pref

        except Exception as e:
            logger.error(f"Error creating user preferences: {e}")
            await self.db.rollback()
            raise

    async def get_user_preferences(self, user_id: uuid.UUID) -> Optional[UserPreference]:
        """
        Get user preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            UserPreference object or None
        """
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_preferences_from_interaction(
        self, user_id: uuid.UUID, interaction: UserInteraction
    ) -> None:
        """
        Update user preferences based on interaction feedback.
        
        Args:
            user_id: User ID
            interaction: User interaction to learn from
        """
        try:
            user_prefs = await self.get_user_preferences(user_id)
            if not user_prefs:
                # Create default preferences first
                user_prefs = await self.create_user_preference(user_id, {})

            # Learn from interaction
            learning_rate = 0.1  # How much to adjust preferences
            
            if interaction.response_rating is not None and interaction.content_category:
                rating_normalized = interaction.response_rating / 5.0  # Normalize to 0-1
                adjustment = (rating_normalized - 0.5) * learning_rate
                
                # Update category interest based on feedback
                if interaction.content_category == 'career':
                    user_prefs.career_interest = max(0.0, min(1.0, user_prefs.career_interest + adjustment))
                elif interaction.content_category == 'love':
                    user_prefs.love_interest = max(0.0, min(1.0, user_prefs.love_interest + adjustment))
                elif interaction.content_category == 'health':
                    user_prefs.health_interest = max(0.0, min(1.0, user_prefs.health_interest + adjustment))
                elif interaction.content_category == 'finance':
                    user_prefs.finance_interest = max(0.0, min(1.0, user_prefs.finance_interest + adjustment))
                elif interaction.content_category == 'family':
                    user_prefs.family_interest = max(0.0, min(1.0, user_prefs.family_interest + adjustment))
                elif interaction.content_category == 'spiritual':
                    user_prefs.spiritual_interest = max(0.0, min(1.0, user_prefs.spiritual_interest + adjustment))

            # Learn from time patterns
            if interaction.time_of_day and not user_prefs.preferred_time_slot:
                # Analyze user's interaction times to set preferred time slot
                time_patterns = await self._analyze_user_time_patterns(user_id)
                most_active_time = max(time_patterns, key=time_patterns.get) if time_patterns else None
                if most_active_time:
                    user_prefs.preferred_time_slot = most_active_time

            # Learn communication style preferences from session duration
            if interaction.session_duration:
                if interaction.session_duration < 30 and user_prefs.communication_style == 'balanced':
                    # User prefers shorter interactions
                    user_prefs.preferred_length = 'short'
                elif interaction.session_duration > 180 and user_prefs.communication_style == 'balanced':
                    # User engages with longer content
                    user_prefs.preferred_length = 'long'
                    user_prefs.complexity_level = 'advanced'

            user_prefs.updated_at = datetime.utcnow()
            await self.db.commit()

        except Exception as e:
            logger.error(f"Error updating preferences from interaction: {e}")

    async def get_personalized_content_settings(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get personalized settings for content generation.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with personalized settings
        """
        try:
            user_prefs = await self.get_user_preferences(user_id)
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user_prefs or not user:
                return self._get_default_content_settings()

            # Get user's name if available and permitted
            user_name = None
            if user_prefs.use_name_in_responses and user.encrypted_name:
                try:
                    user_name = self.data_protection.decrypt_name(user.encrypted_name)
                except Exception:
                    user_name = None

            settings = {
                'communication_style': user_prefs.communication_style,
                'complexity_level': user_prefs.complexity_level,
                'preferred_length': user_prefs.preferred_length,
                'emotional_tone': user_prefs.emotional_tone,
                'language': user_prefs.language_preference,
                'cultural_context': user_prefs.cultural_context,
                'user_name': user_name,
                'zodiac_sign': user.zodiac_sign,
                'include_features': {
                    'lucky_numbers': user_prefs.include_lucky_numbers,
                    'lucky_colors': user_prefs.include_lucky_colors,
                    'compatibility_hints': user_prefs.include_compatibility_hints,
                },
                'interest_weights': {
                    'career': user_prefs.career_interest,
                    'love': user_prefs.love_interest,
                    'health': user_prefs.health_interest,
                    'finance': user_prefs.finance_interest,
                    'family': user_prefs.family_interest,
                    'spiritual': user_prefs.spiritual_interest,
                }
            }

            return settings

        except Exception as e:
            logger.error(f"Error getting personalized content settings: {e}")
            return self._get_default_content_settings()

    async def generate_dynamic_horoscope_prompt(
        self, user_id: uuid.UUID, horoscope_type: str, base_content: str
    ) -> str:
        """
        Generate personalized horoscope prompt based on user preferences.
        
        Args:
            user_id: User ID
            horoscope_type: Type of horoscope (daily, weekly, monthly, etc.)
            base_content: Base horoscope content
            
        Returns:
            Personalized prompt for horoscope generation
        """
        try:
            settings = await self.get_personalized_content_settings(user_id)
            
            # Build personalized prompt
            prompt_parts = []
            
            # Communication style adaptation
            if settings['communication_style'] == 'formal':
                prompt_parts.append("Write in a formal, respectful tone.")
            elif settings['communication_style'] == 'casual':
                prompt_parts.append("Write in a friendly, conversational tone.")
            else:
                prompt_parts.append("Write in a balanced, approachable tone.")

            # Complexity level adaptation
            if settings['complexity_level'] == 'beginner':
                prompt_parts.append("Use simple astrological terms and provide clear explanations.")
            elif settings['complexity_level'] == 'advanced':
                prompt_parts.append("Include detailed astrological aspects, transits, and technical terms.")
            else:
                prompt_parts.append("Balance accessibility with astrological depth.")

            # Length preference
            if settings['preferred_length'] == 'short':
                prompt_parts.append("Keep the response concise and to the point (2-3 sentences per topic).")
            elif settings['preferred_length'] == 'long':
                prompt_parts.append("Provide detailed insights and elaborations (4-6 sentences per topic).")
            else:
                prompt_parts.append("Provide moderate detail (3-4 sentences per topic).")

            # Emotional tone
            if settings['emotional_tone'] == 'positive':
                prompt_parts.append("Focus on positive aspects and opportunities.")
            elif settings['emotional_tone'] == 'realistic':
                prompt_parts.append("Provide balanced insights including both challenges and opportunities.")
            else:
                prompt_parts.append("Maintain a neutral, informative tone.")

            # Interest-based focus
            top_interests = sorted(
                settings['interest_weights'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            if top_interests:
                interest_names = [interest[0] for interest in top_interests if interest[1] > 0.6]
                if interest_names:
                    prompt_parts.append(f"Focus especially on {', '.join(interest_names)} aspects.")

            # Cultural adaptation
            if settings['cultural_context']:
                prompt_parts.append(f"Consider {settings['cultural_context']} cultural context.")

            # Personalization features
            features = settings['include_features']
            feature_list = []
            if features['lucky_numbers']:
                feature_list.append("lucky numbers")
            if features['lucky_colors']:
                feature_list.append("lucky colors")
            if features['compatibility_hints']:
                feature_list.append("compatibility insights")
            
            if feature_list:
                prompt_parts.append(f"Include {', '.join(feature_list)}.")

            # Name usage
            if settings['user_name']:
                prompt_parts.append(f"Address the user as {settings['user_name']} when appropriate.")

            # Combine all parts
            personalization_prompt = " ".join(prompt_parts)
            
            return f"{personalization_prompt}\n\nBase horoscope content: {base_content}"

        except Exception as e:
            logger.error(f"Error generating dynamic horoscope prompt: {e}")
            return base_content

    async def track_user_interaction(
        self, 
        user_id: uuid.UUID,
        interaction_type: str,
        content_category: Optional[str] = None,
        content_id: Optional[str] = None,
        session_duration: Optional[int] = None,
        response_rating: Optional[float] = None,
        feedback_text: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> UserInteraction:
        """
        Track user interaction for learning purposes.
        
        Args:
            user_id: User ID
            interaction_type: Type of interaction
            content_category: Content category
            content_id: Content identifier
            session_duration: Session duration in seconds
            response_rating: User rating (1-5)
            feedback_text: User feedback
            context_data: Additional context
            
        Returns:
            UserInteraction object
        """
        try:
            now = datetime.utcnow()
            
            # Determine time of day
            hour = now.hour
            if 6 <= hour < 12:
                time_of_day = 'morning'
            elif 12 <= hour < 18:
                time_of_day = 'afternoon'
            elif 18 <= hour < 22:
                time_of_day = 'evening'
            else:
                time_of_day = 'night'

            interaction = UserInteraction(
                user_id=user_id,
                interaction_type=interaction_type,
                content_category=content_category,
                content_id=content_id,
                session_duration=session_duration,
                response_rating=response_rating,
                feedback_text=feedback_text,
                time_of_day=time_of_day,
                day_of_week=now.strftime('%A').lower(),
                context_data=context_data,
                timestamp=now
            )

            self.db.add(interaction)
            await self.db.commit()
            await self.db.refresh(interaction)

            # Learn from this interaction
            await self.update_preferences_from_interaction(user_id, interaction)

            return interaction

        except Exception as e:
            logger.error(f"Error tracking user interaction: {e}")
            await self.db.rollback()
            raise

    async def get_user_profile_summary(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get comprehensive user profile summary.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user profile information
        """
        try:
            # Get user preferences
            user_prefs = await self.get_user_preferences(user_id)
            
            # Get user basic info
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            # Get interaction statistics
            interaction_stats = await self._get_user_interaction_stats(user_id)

            # Get engagement patterns
            engagement_patterns = await self._get_user_engagement_patterns(user_id)

            profile = {
                'user_id': str(user_id),
                'zodiac_sign': user.zodiac_sign if user else None,
                'registration_date': user.created_at.isoformat() if user and user.created_at else None,
                'last_active': user.last_accessed.isoformat() if user and user.last_accessed else None,
                'data_consent': user.data_consent if user else False,
                'preferences': {
                    'interests': {
                        'career': user_prefs.career_interest if user_prefs else 0.5,
                        'love': user_prefs.love_interest if user_prefs else 0.5,
                        'health': user_prefs.health_interest if user_prefs else 0.5,
                        'finance': user_prefs.finance_interest if user_prefs else 0.5,
                        'family': user_prefs.family_interest if user_prefs else 0.5,
                        'spiritual': user_prefs.spiritual_interest if user_prefs else 0.5,
                    },
                    'communication': {
                        'style': user_prefs.communication_style if user_prefs else 'balanced',
                        'complexity': user_prefs.complexity_level if user_prefs else 'intermediate',
                        'length': user_prefs.preferred_length if user_prefs else 'medium',
                        'tone': user_prefs.emotional_tone if user_prefs else 'neutral',
                    },
                    'personalization': {
                        'use_name': user_prefs.use_name_in_responses if user_prefs else False,
                        'lucky_numbers': user_prefs.include_lucky_numbers if user_prefs else True,
                        'lucky_colors': user_prefs.include_lucky_colors if user_prefs else True,
                        'compatibility_hints': user_prefs.include_compatibility_hints if user_prefs else True,
                    },
                    'cultural_context': user_prefs.cultural_context if user_prefs else None,
                    'language': user_prefs.language_preference if user_prefs else 'ru',
                    'timezone': user_prefs.timezone if user_prefs else None,
                } if user_prefs else None,
                'interaction_stats': interaction_stats,
                'engagement_patterns': engagement_patterns,
            }

            return profile

        except Exception as e:
            logger.error(f"Error getting user profile summary: {e}")
            return {'user_id': str(user_id), 'error': str(e)}

    async def adapt_communication_style(
        self, user_id: uuid.UUID, content: str
    ) -> str:
        """
        Adapt content based on user's communication style preferences.
        
        Args:
            user_id: User ID
            content: Original content
            
        Returns:
            Style-adapted content
        """
        try:
            settings = await self.get_personalized_content_settings(user_id)
            
            # This is a simplified adaptation - in a real implementation,
            # you'd use NLP techniques or AI models for style transfer
            
            style = settings['communication_style']
            complexity = settings['complexity_level']
            tone = settings['emotional_tone']
            
            adapted_content = content
            
            # Style adaptations (simplified)
            if style == 'formal':
                adapted_content = adapted_content.replace('you\'ll', 'you will')
                adapted_content = adapted_content.replace('don\'t', 'do not')
                adapted_content = adapted_content.replace('can\'t', 'cannot')
            elif style == 'casual':
                adapted_content = adapted_content.replace('you will', 'you\'ll')
                adapted_content = adapted_content.replace('do not', 'don\'t')
                adapted_content = adapted_content.replace('cannot', 'can\'t')

            # Add user name if appropriate
            if settings['user_name'] and not settings['user_name'].lower() in adapted_content.lower():
                adapted_content = f"{settings['user_name']}, {adapted_content}"

            return adapted_content

        except Exception as e:
            logger.error(f"Error adapting communication style: {e}")
            return content

    async def get_cultural_adaptations(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get cultural adaptations for user content.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with cultural adaptation settings
        """
        try:
            user_prefs = await self.get_user_preferences(user_id)
            
            if not user_prefs or not user_prefs.cultural_context:
                return {}

            cultural_context = user_prefs.cultural_context.lower()
            
            # Cultural adaptation mappings
            adaptations = {
                'russian': {
                    'calendar_system': 'gregorian',
                    'date_format': 'dd.mm.yyyy',
                    'time_format': '24h',
                    'cultural_holidays': ['new_year', 'orthodox_christmas', 'womens_day', 'victory_day'],
                    'lucky_colors_cultural': ['red', 'gold', 'white'],
                    'avoid_topics': [],
                    'preferred_greetings': ['Добро пожаловать', 'Приветствую'],
                },
                'chinese': {
                    'calendar_system': 'lunar',
                    'date_format': 'yyyy/mm/dd',
                    'time_format': '24h',
                    'cultural_holidays': ['chinese_new_year', 'mid_autumn', 'qingming'],
                    'lucky_colors_cultural': ['red', 'gold', 'yellow'],
                    'lucky_numbers_cultural': [8, 9, 6],
                    'avoid_numbers': [4],
                    'feng_shui_elements': True,
                },
                'indian': {
                    'calendar_system': 'hindu_lunar',
                    'date_format': 'dd/mm/yyyy',
                    'vedic_astrology': True,
                    'cultural_holidays': ['diwali', 'holi', 'navaratri'],
                    'lucky_colors_cultural': ['saffron', 'red', 'yellow'],
                    'include_mantras': True,
                    'chakra_references': True,
                },
                'western': {
                    'calendar_system': 'gregorian',
                    'date_format': 'mm/dd/yyyy',
                    'time_format': '12h',
                    'tropical_astrology': True,
                    'cultural_holidays': ['christmas', 'thanksgiving', 'new_year'],
                    'lucky_colors_cultural': ['blue', 'green', 'purple'],
                }
            }

            return adaptations.get(cultural_context, {})

        except Exception as e:
            logger.error(f"Error getting cultural adaptations: {e}")
            return {}

    async def _update_preference_values(
        self, user_pref: UserPreference, preferences: Dict[str, Any]
    ) -> None:
        """Update user preference values."""
        for key, value in preferences.items():
            if hasattr(user_pref, key):
                setattr(user_pref, key, value)
        
        user_pref.updated_at = datetime.utcnow()
        await self.db.commit()

    async def _analyze_user_time_patterns(self, user_id: uuid.UUID) -> Dict[str, int]:
        """Analyze user's interaction time patterns."""
        result = await self.db.execute(
            select(UserInteraction.time_of_day, func.count(UserInteraction.id)).
            where(UserInteraction.user_id == user_id).
            group_by(UserInteraction.time_of_day)
        )
        
        patterns = {}
        for time_slot, count in result:
            if time_slot:
                patterns[time_slot] = count
        
        return patterns

    async def _get_user_interaction_stats(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get user interaction statistics."""
        # Total interactions
        total_result = await self.db.execute(
            select(func.count(UserInteraction.id)).
            where(UserInteraction.user_id == user_id)
        )
        total_interactions = total_result.scalar() or 0

        # Average rating
        rating_result = await self.db.execute(
            select(func.avg(UserInteraction.response_rating)).
            where(
                UserInteraction.user_id == user_id,
                UserInteraction.response_rating.isnot(None)
            )
        )
        avg_rating = rating_result.scalar() or 0.0

        # Most recent interaction
        recent_result = await self.db.execute(
            select(UserInteraction.timestamp).
            where(UserInteraction.user_id == user_id).
            order_by(desc(UserInteraction.timestamp)).
            limit(1)
        )
        last_interaction = recent_result.scalar()

        return {
            'total_interactions': total_interactions,
            'average_rating': float(avg_rating) if avg_rating else None,
            'last_interaction': last_interaction.isoformat() if last_interaction else None,
        }

    async def _get_user_engagement_patterns(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get user engagement patterns."""
        # Get interactions from last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        result = await self.db.execute(
            select(UserInteraction).
            where(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= cutoff_date
            ).
            order_by(UserInteraction.timestamp)
        )
        interactions = result.scalars().all()

        if not interactions:
            return {}

        # Analyze patterns
        time_patterns = {}
        category_patterns = {}
        
        for interaction in interactions:
            # Time patterns
            if interaction.time_of_day:
                time_patterns[interaction.time_of_day] = time_patterns.get(interaction.time_of_day, 0) + 1
            
            # Category patterns
            if interaction.content_category:
                category_patterns[interaction.content_category] = category_patterns.get(
                    interaction.content_category, 0
                ) + 1

        return {
            'preferred_times': time_patterns,
            'preferred_categories': category_patterns,
            'interaction_frequency': len(interactions) / 30,  # Per day
        }

    def _get_default_content_settings(self) -> Dict[str, Any]:
        """Get default content settings for users without preferences."""
        return {
            'communication_style': 'balanced',
            'complexity_level': 'intermediate',
            'preferred_length': 'medium',
            'emotional_tone': 'neutral',
            'language': 'ru',
            'cultural_context': None,
            'user_name': None,
            'zodiac_sign': None,
            'include_features': {
                'lucky_numbers': True,
                'lucky_colors': True,
                'compatibility_hints': True,
            },
            'interest_weights': {
                'career': 0.5,
                'love': 0.5,
                'health': 0.5,
                'finance': 0.5,
                'family': 0.5,
                'spiritual': 0.5,
            }
        }


class InterestProfilingService:
    """
    Service for profiling user interests and learning preferences.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def analyze_user_interests(self, user_id: uuid.UUID) -> Dict[str, float]:
        """
        Analyze user interests from interaction history.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with interest scores (0-1)
        """
        try:
            # Get user interactions
            result = await self.db.execute(
                select(UserInteraction).
                where(UserInteraction.user_id == user_id).
                order_by(desc(UserInteraction.timestamp)).
                limit(100)  # Analyze last 100 interactions
            )
            interactions = result.scalars().all()

            if not interactions:
                return self._get_default_interests()

            # Analyze interest patterns
            category_scores = {}
            category_counts = {}
            
            for interaction in interactions:
                if not interaction.content_category:
                    continue
                
                category = interaction.content_category
                if category not in category_scores:
                    category_scores[category] = 0.0
                    category_counts[category] = 0

                # Weight by rating and recency
                score_weight = 1.0
                if interaction.response_rating:
                    score_weight = interaction.response_rating / 5.0
                
                # Recent interactions have higher weight
                days_ago = (datetime.utcnow() - interaction.timestamp).days
                recency_weight = max(0.1, 1.0 - (days_ago / 90))  # Decay over 90 days
                
                final_weight = score_weight * recency_weight
                category_scores[category] += final_weight
                category_counts[category] += 1

            # Normalize scores
            normalized_interests = {}
            for category, total_score in category_scores.items():
                count = category_counts[category]
                if count > 0:
                    avg_score = total_score / count
                    normalized_interests[category] = min(1.0, avg_score)

            # Fill in missing categories with defaults
            all_categories = ['career', 'love', 'health', 'finance', 'family', 'spiritual']
            for category in all_categories:
                if category not in normalized_interests:
                    normalized_interests[category] = 0.5

            return normalized_interests

        except Exception as e:
            logger.error(f"Error analyzing user interests: {e}")
            return self._get_default_interests()

    async def update_user_interests(
        self, user_id: uuid.UUID, interest_updates: Dict[str, float]
    ) -> None:
        """
        Update user interest scores.
        
        Args:
            user_id: User ID
            interest_updates: Dictionary with interest score updates
        """
        try:
            user_prefs = await self.db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            prefs = user_prefs.scalar_one_or_none()

            if not prefs:
                # Create preferences with updated interests
                prefs = UserPreference(
                    user_id=user_id,
                    career_interest=interest_updates.get('career', 0.5),
                    love_interest=interest_updates.get('love', 0.5),
                    health_interest=interest_updates.get('health', 0.5),
                    finance_interest=interest_updates.get('finance', 0.5),
                    family_interest=interest_updates.get('family', 0.5),
                    spiritual_interest=interest_updates.get('spiritual', 0.5),
                )
                self.db.add(prefs)
            else:
                # Update existing preferences
                if 'career' in interest_updates:
                    prefs.career_interest = interest_updates['career']
                if 'love' in interest_updates:
                    prefs.love_interest = interest_updates['love']
                if 'health' in interest_updates:
                    prefs.health_interest = interest_updates['health']
                if 'finance' in interest_updates:
                    prefs.finance_interest = interest_updates['finance']
                if 'family' in interest_updates:
                    prefs.family_interest = interest_updates['family']
                if 'spiritual' in interest_updates:
                    prefs.spiritual_interest = interest_updates['spiritual']
                
                prefs.updated_at = datetime.utcnow()

            await self.db.commit()

        except Exception as e:
            logger.error(f"Error updating user interests: {e}")
            await self.db.rollback()

    async def get_trending_interests(self, timeframe_days: int = 30) -> Dict[str, float]:
        """
        Get trending interest categories across all users.
        
        Args:
            timeframe_days: Days to look back for trends
            
        Returns:
            Dictionary with trending interest scores
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)
            
            result = await self.db.execute(
                select(
                    UserInteraction.content_category,
                    func.count(UserInteraction.id),
                    func.avg(UserInteraction.response_rating)
                ).
                where(
                    UserInteraction.timestamp >= cutoff_date,
                    UserInteraction.content_category.isnot(None),
                    UserInteraction.response_rating >= 3.0
                ).
                group_by(UserInteraction.content_category)
            )
            
            trends = {}
            for category, count, avg_rating in result:
                if category and avg_rating:
                    # Trend score based on volume and satisfaction
                    trend_score = (count * float(avg_rating)) / (timeframe_days * 5.0)
                    trends[category] = min(1.0, trend_score)

            return trends

        except Exception as e:
            logger.error(f"Error getting trending interests: {e}")
            return {}

    def _get_default_interests(self) -> Dict[str, float]:
        """Get default interest scores."""
        return {
            'career': 0.5,
            'love': 0.5,
            'health': 0.5,
            'finance': 0.5,
            'family': 0.5,
            'spiritual': 0.5,
        }