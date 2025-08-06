"""
Machine Learning analytics for user clustering, churn prediction, and engagement optimization.
"""
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.database import User
from app.models.recommendation_models import UserPreference, UserInteraction


class UserClusteringService:
    """
    Service for clustering users based on astrological and behavioral characteristics.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.scaler = StandardScaler()
        self.n_clusters = 5  # Default number of clusters

    async def perform_user_clustering(self) -> Dict[str, Any]:
        """
        Perform user clustering analysis.
        
        Returns:
            Dictionary with clustering results and insights
        """
        try:
            # Get user data for clustering
            user_features = await self._extract_user_features()
            
            if len(user_features) < 10:  # Need minimum users for clustering
                logger.warning("Insufficient users for clustering analysis")
                return {'error': 'Insufficient data'}

            # Prepare data
            df = pd.DataFrame(user_features)
            user_ids = df['user_id'].values
            feature_columns = [col for col in df.columns if col != 'user_id']
            X = df[feature_columns].values

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Determine optimal number of clusters using elbow method
            optimal_k = self._find_optimal_clusters(X_scaled)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)

            # Analyze clusters
            cluster_analysis = self._analyze_clusters(df, cluster_labels, feature_columns)

            # Store clustering results (in a real implementation, you'd save these)
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'n_clusters': optimal_k,
                'n_users': len(user_ids),
                'cluster_analysis': cluster_analysis,
                'feature_importance': self._calculate_feature_importance(X_scaled, cluster_labels),
            }

            logger.info(f"User clustering completed: {optimal_k} clusters, {len(user_ids)} users")
            return results

        except Exception as e:
            logger.error(f"Error performing user clustering: {e}")
            return {'error': str(e)}

    async def get_user_cluster(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get cluster assignment for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user's cluster information
        """
        try:
            # This would be implemented by loading saved clustering model
            # For now, we'll do a simplified assignment based on user characteristics
            
            user_features = await self._get_single_user_features(user_id)
            if not user_features:
                return None

            # Simplified cluster assignment based on primary interest
            interests = user_features.get('interests', {})
            if not interests:
                return {'cluster_id': 'unknown', 'cluster_name': 'Uncategorized'}

            top_interest = max(interests, key=interests.get)
            
            # Map interests to archetypal clusters
            cluster_mapping = {
                'career': {'id': 'achievers', 'name': 'Career Achievers', 'description': 'Focused on professional growth'},
                'love': {'id': 'romantics', 'name': 'Love Seekers', 'description': 'Interested in relationships and romance'},
                'health': {'id': 'wellness', 'name': 'Wellness Warriors', 'description': 'Health and wellbeing focused'},
                'finance': {'id': 'builders', 'name': 'Wealth Builders', 'description': 'Financial growth oriented'},
                'family': {'id': 'nurturers', 'name': 'Family Nurturers', 'description': 'Family and relationships focused'},
                'spiritual': {'id': 'seekers', 'name': 'Spiritual Seekers', 'description': 'Spiritually minded and growth-oriented'},
            }

            cluster_info = cluster_mapping.get(top_interest, {
                'id': 'balanced', 
                'name': 'Balanced Explorers', 
                'description': 'Well-rounded interests'
            })

            return {
                'cluster_id': cluster_info['id'],
                'cluster_name': cluster_info['name'],
                'cluster_description': cluster_info['description'],
                'primary_interest': top_interest,
                'interest_scores': interests,
                'assigned_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting user cluster: {e}")
            return None

    async def _extract_user_features(self) -> List[Dict[str, Any]]:
        """Extract features for all users for clustering."""
        # Get users with preferences and sufficient interaction history
        result = await self.db.execute(
            select(User, UserPreference).
            join(UserPreference, User.id == UserPreference.user_id).
            where(User.data_consent == True)
        )
        
        user_features = []
        for user, prefs in result:
            # Get interaction stats
            interaction_stats = await self._get_user_interaction_features(user.id)
            
            features = {
                'user_id': str(user.id),
                # Interest scores
                'career_interest': prefs.career_interest,
                'love_interest': prefs.love_interest,
                'health_interest': prefs.health_interest,
                'finance_interest': prefs.finance_interest,
                'family_interest': prefs.family_interest,
                'spiritual_interest': prefs.spiritual_interest,
                # Communication preferences
                'complexity_score': self._encode_complexity(prefs.complexity_level),
                'formality_score': self._encode_communication_style(prefs.communication_style),
                'length_preference': self._encode_length(prefs.preferred_length),
                'tone_preference': self._encode_tone(prefs.emotional_tone),
                # Behavioral features
                'interaction_frequency': interaction_stats.get('frequency', 0),
                'avg_rating': interaction_stats.get('avg_rating', 0),
                'session_diversity': interaction_stats.get('diversity', 0),
                'engagement_consistency': interaction_stats.get('consistency', 0),
                # Temporal features
                'days_active': interaction_stats.get('days_active', 0),
                'peak_hour': interaction_stats.get('peak_hour', 12),
                'weekend_activity': interaction_stats.get('weekend_ratio', 0.5),
                # Zodiac encoding (simplified)
                'zodiac_element': self._encode_zodiac_element(user.zodiac_sign),
                'zodiac_modality': self._encode_zodiac_modality(user.zodiac_sign),
            }
            user_features.append(features)
        
        return user_features

    async def _get_single_user_features(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get features for a single user."""
        result = await self.db.execute(
            select(User, UserPreference).
            join(UserPreference, User.id == UserPreference.user_id, isouter=True).
            where(User.id == user_id)
        )
        
        row = result.first()
        if not row:
            return None

        user, prefs = row
        if not prefs:
            return {'interests': {}}

        return {
            'interests': {
                'career': prefs.career_interest,
                'love': prefs.love_interest,
                'health': prefs.health_interest,
                'finance': prefs.finance_interest,
                'family': prefs.family_interest,
                'spiritual': prefs.spiritual_interest,
            },
            'zodiac_sign': user.zodiac_sign,
            'communication_style': prefs.communication_style,
            'complexity_level': prefs.complexity_level,
        }

    async def _get_user_interaction_features(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get interaction-based features for a user."""
        # Get interactions from last 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
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
            return {'frequency': 0, 'avg_rating': 0, 'diversity': 0, 'consistency': 0, 'days_active': 0}

        # Calculate features
        total_interactions = len(interactions)
        
        # Frequency (interactions per day)
        time_span = (datetime.utcnow() - interactions[0].timestamp).days or 1
        frequency = total_interactions / time_span

        # Average rating
        ratings = [i.response_rating for i in interactions if i.response_rating is not None]
        avg_rating = np.mean(ratings) if ratings else 0

        # Content diversity (unique categories)
        categories = set(i.content_category for i in interactions if i.content_category)
        diversity = len(categories) / 6.0  # Normalize by max categories

        # Engagement consistency (regularity of interactions)
        if len(interactions) > 1:
            time_diffs = []
            for i in range(1, len(interactions)):
                diff = (interactions[i].timestamp - interactions[i-1].timestamp).total_seconds() / 86400
                time_diffs.append(diff)
            consistency = 1.0 / (1.0 + np.std(time_diffs)) if time_diffs else 0
        else:
            consistency = 0

        # Active days
        unique_dates = set(i.timestamp.date() for i in interactions)
        days_active = len(unique_dates)

        # Peak activity hour
        hours = [i.timestamp.hour for i in interactions]
        peak_hour = max(set(hours), key=hours.count) if hours else 12

        # Weekend activity ratio
        weekdays = [i.timestamp.weekday() for i in interactions]
        weekend_interactions = sum(1 for day in weekdays if day >= 5)
        weekend_ratio = weekend_interactions / len(weekdays) if weekdays else 0.5

        return {
            'frequency': frequency,
            'avg_rating': avg_rating,
            'diversity': diversity,
            'consistency': consistency,
            'days_active': days_active,
            'peak_hour': peak_hour,
            'weekend_ratio': weekend_ratio,
        }

    def _find_optimal_clusters(self, X: np.ndarray, max_k: int = 10) -> int:
        """Find optimal number of clusters using elbow method."""
        inertias = []
        k_range = range(2, min(max_k + 1, len(X) // 2))
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)
        
        # Simple elbow detection
        if len(inertias) < 2:
            return 3
        
        # Find the point with maximum change in slope
        deltas = [inertias[i] - inertias[i+1] for i in range(len(inertias)-1)]
        optimal_idx = np.argmax(deltas)
        
        return k_range[optimal_idx]

    def _analyze_clusters(self, df: pd.DataFrame, labels: np.ndarray, features: List[str]) -> Dict[str, Any]:
        """Analyze cluster characteristics."""
        df['cluster'] = labels
        analysis = {}
        
        for cluster_id in np.unique(labels):
            cluster_data = df[df['cluster'] == cluster_id]
            cluster_size = len(cluster_data)
            
            # Calculate cluster centroid
            centroid = {}
            for feature in features:
                centroid[feature] = float(cluster_data[feature].mean())
            
            # Find dominant characteristics
            dominant_interests = {}
            interest_features = [f for f in features if '_interest' in f]
            for feature in interest_features:
                interest_name = feature.replace('_interest', '')
                dominant_interests[interest_name] = float(cluster_data[feature].mean())
            
            # Cluster name based on dominant interest
            top_interest = max(dominant_interests, key=dominant_interests.get) if dominant_interests else 'unknown'
            cluster_names = {
                'career': 'Professional Achievers',
                'love': 'Relationship Focused',
                'health': 'Wellness Oriented',
                'finance': 'Financial Planners',
                'family': 'Family Centered',
                'spiritual': 'Spiritual Explorers'
            }
            
            analysis[f'cluster_{cluster_id}'] = {
                'name': cluster_names.get(top_interest, f'Cluster {cluster_id}'),
                'size': cluster_size,
                'percentage': float(cluster_size / len(df) * 100),
                'centroid': centroid,
                'dominant_interests': dominant_interests,
                'primary_interest': top_interest,
            }
        
        return analysis

    def _calculate_feature_importance(self, X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """Calculate feature importance for clustering."""
        # Use random forest to understand feature importance for cluster prediction
        try:
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X, labels)
            
            feature_names = [
                'career_interest', 'love_interest', 'health_interest', 'finance_interest',
                'family_interest', 'spiritual_interest', 'complexity_score', 'formality_score',
                'length_preference', 'tone_preference', 'interaction_frequency', 'avg_rating',
                'session_diversity', 'engagement_consistency', 'days_active', 'peak_hour',
                'weekend_activity', 'zodiac_element', 'zodiac_modality'
            ]
            
            importance_dict = {}
            for name, importance in zip(feature_names, rf.feature_importances_):
                importance_dict[name] = float(importance)
            
            return importance_dict
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
            return {}

    def _encode_complexity(self, level: str) -> float:
        """Encode complexity level as numeric value."""
        mapping = {'beginner': 0.0, 'intermediate': 0.5, 'advanced': 1.0}
        return mapping.get(level, 0.5)

    def _encode_communication_style(self, style: str) -> float:
        """Encode communication style as numeric value."""
        mapping = {'casual': 0.0, 'balanced': 0.5, 'formal': 1.0}
        return mapping.get(style, 0.5)

    def _encode_length(self, length: str) -> float:
        """Encode length preference as numeric value."""
        mapping = {'short': 0.0, 'medium': 0.5, 'long': 1.0}
        return mapping.get(length, 0.5)

    def _encode_tone(self, tone: str) -> float:
        """Encode emotional tone as numeric value."""
        mapping = {'positive': 1.0, 'neutral': 0.5, 'realistic': 0.0}
        return mapping.get(tone, 0.5)

    def _encode_zodiac_element(self, zodiac_sign: Optional[str]) -> float:
        """Encode zodiac element as numeric value."""
        if not zodiac_sign:
            return 0.5
        
        elements = {
            'aries': 0.0, 'leo': 0.0, 'sagittarius': 0.0,  # Fire
            'taurus': 0.33, 'virgo': 0.33, 'capricorn': 0.33,  # Earth
            'gemini': 0.66, 'libra': 0.66, 'aquarius': 0.66,  # Air
            'cancer': 1.0, 'scorpio': 1.0, 'pisces': 1.0,  # Water
        }
        return elements.get(zodiac_sign.lower(), 0.5)

    def _encode_zodiac_modality(self, zodiac_sign: Optional[str]) -> float:
        """Encode zodiac modality as numeric value."""
        if not zodiac_sign:
            return 0.5
        
        modalities = {
            'aries': 0.0, 'cancer': 0.0, 'libra': 0.0, 'capricorn': 0.0,  # Cardinal
            'taurus': 0.5, 'leo': 0.5, 'scorpio': 0.5, 'aquarius': 0.5,  # Fixed
            'gemini': 1.0, 'virgo': 1.0, 'sagittarius': 1.0, 'pisces': 1.0,  # Mutable
        }
        return modalities.get(zodiac_sign.lower(), 0.5)


class ChurnPredictionService:
    """
    Service for predicting user churn and identifying at-risk users.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.churn_threshold_days = 30  # Days without activity = churned

    async def predict_user_churn_risk(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Predict churn risk for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with churn risk prediction
        """
        try:
            # Get user features
            user_features = await self._extract_churn_features(user_id)
            if not user_features:
                return {'error': 'Insufficient data'}

            # Calculate churn risk score
            risk_score = await self._calculate_churn_risk(user_features)
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = 'high'
                recommendation = 'Immediate intervention recommended'
            elif risk_score >= 0.6:
                risk_level = 'medium'
                recommendation = 'Engage with personalized content'
            elif risk_score >= 0.4:
                risk_level = 'low'
                recommendation = 'Monitor engagement patterns'
            else:
                risk_level = 'very_low'
                recommendation = 'User appears engaged'

            # Generate intervention strategies
            interventions = self._generate_intervention_strategies(user_features, risk_score)

            return {
                'user_id': str(user_id),
                'churn_risk_score': risk_score,
                'risk_level': risk_level,
                'recommendation': recommendation,
                'key_factors': user_features.get('risk_factors', []),
                'suggested_interventions': interventions,
                'prediction_date': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error predicting churn risk: {e}")
            return {'error': str(e)}

    async def identify_at_risk_users(self, risk_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Identify users at risk of churning.
        
        Args:
            risk_threshold: Minimum risk score to be considered at-risk
            
        Returns:
            List of at-risk users with predictions
        """
        try:
            # Get active users
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            result = await self.db.execute(
                select(User).where(
                    User.data_consent == True,
                    User.last_accessed >= cutoff_date
                )
            )
            users = result.scalars().all()

            at_risk_users = []
            for user in users:
                prediction = await self.predict_user_churn_risk(user.id)
                
                if ('churn_risk_score' in prediction and 
                    prediction['churn_risk_score'] >= risk_threshold):
                    at_risk_users.append(prediction)

            # Sort by risk score (highest first)
            at_risk_users.sort(key=lambda x: x.get('churn_risk_score', 0), reverse=True)
            
            return at_risk_users

        except Exception as e:
            logger.error(f"Error identifying at-risk users: {e}")
            return []

    async def _extract_churn_features(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Extract features for churn prediction."""
        # Get user basic info
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            return None

        # Get interaction history
        result = await self.db.execute(
            select(UserInteraction).
            where(UserInteraction.user_id == user_id).
            order_by(desc(UserInteraction.timestamp)).
            limit(100)
        )
        interactions = result.scalars().all()

        if not interactions:
            return {
                'days_since_last_activity': 999,
                'total_interactions': 0,
                'risk_factors': ['no_interactions']
            }

        # Calculate temporal features
        now = datetime.utcnow()
        last_interaction = interactions[0].timestamp
        days_since_last = (now - last_interaction).days

        # Calculate engagement features
        total_interactions = len(interactions)
        avg_rating = np.mean([i.response_rating for i in interactions if i.response_rating]) or 0
        
        # Interaction frequency over time
        if len(interactions) > 1:
            time_span = (interactions[0].timestamp - interactions[-1].timestamp).days or 1
            interaction_frequency = total_interactions / time_span
        else:
            interaction_frequency = 0

        # Recent engagement trend
        recent_interactions = [i for i in interactions if (now - i.timestamp).days <= 7]
        recent_frequency = len(recent_interactions) / 7
        
        # Session quality
        session_durations = [i.session_duration for i in interactions if i.session_duration]
        avg_session_duration = np.mean(session_durations) if session_durations else 0

        # Content diversity
        categories = set(i.content_category for i in interactions if i.content_category)
        content_diversity = len(categories)

        # Identify risk factors
        risk_factors = []
        if days_since_last > 7:
            risk_factors.append('inactive_recently')
        if avg_rating < 3.0:
            risk_factors.append('low_satisfaction')
        if interaction_frequency < 0.1:
            risk_factors.append('low_frequency')
        if recent_frequency == 0:
            risk_factors.append('no_recent_activity')
        if avg_session_duration < 30:
            risk_factors.append('short_sessions')
        if content_diversity <= 1:
            risk_factors.append('limited_content_variety')

        return {
            'days_since_last_activity': days_since_last,
            'total_interactions': total_interactions,
            'avg_rating': avg_rating,
            'interaction_frequency': interaction_frequency,
            'recent_frequency': recent_frequency,
            'avg_session_duration': avg_session_duration,
            'content_diversity': content_diversity,
            'days_since_registration': (now - user.created_at).days if user.created_at else 0,
            'risk_factors': risk_factors
        }

    async def _calculate_churn_risk(self, features: Dict[str, Any]) -> float:
        """Calculate churn risk score based on features."""
        # This is a simplified rule-based approach
        # In production, you'd use a trained ML model
        
        risk_score = 0.0
        
        # Days since last activity (most important factor)
        days_inactive = features.get('days_since_last_activity', 0)
        if days_inactive > 30:
            risk_score += 0.4
        elif days_inactive > 14:
            risk_score += 0.3
        elif days_inactive > 7:
            risk_score += 0.2
        elif days_inactive > 3:
            risk_score += 0.1

        # Interaction frequency
        frequency = features.get('interaction_frequency', 0)
        if frequency < 0.05:  # Less than once per 20 days
            risk_score += 0.2
        elif frequency < 0.1:  # Less than once per 10 days
            risk_score += 0.1

        # Recent activity trend
        recent_freq = features.get('recent_frequency', 0)
        if recent_freq == 0:
            risk_score += 0.15

        # User satisfaction
        avg_rating = features.get('avg_rating', 0)
        if avg_rating < 2.5:
            risk_score += 0.15
        elif avg_rating < 3.5:
            risk_score += 0.1

        # Session quality
        session_duration = features.get('avg_session_duration', 0)
        if session_duration < 15:
            risk_score += 0.1

        # Content diversity
        diversity = features.get('content_diversity', 0)
        if diversity <= 1:
            risk_score += 0.05

        return min(1.0, risk_score)

    def _generate_intervention_strategies(self, features: Dict[str, Any], risk_score: float) -> List[str]:
        """Generate intervention strategies based on risk factors."""
        interventions = []
        risk_factors = features.get('risk_factors', [])
        
        if 'inactive_recently' in risk_factors:
            interventions.append('Send re-engagement notification with personalized content')
            interventions.append('Offer special daily horoscope or reading')
        
        if 'low_satisfaction' in risk_factors:
            interventions.append('Request feedback and adjust personalization settings')
            interventions.append('Provide content matching higher-rated preferences')
        
        if 'low_frequency' in risk_factors:
            interventions.append('Suggest optimal engagement frequency based on preferences')
            interventions.append('Send gentle reminders during preferred time slots')
        
        if 'short_sessions' in risk_factors:
            interventions.append('Offer more engaging, interactive content')
            interventions.append('Suggest exploring different content categories')
        
        if 'limited_content_variety' in risk_factors:
            interventions.append('Recommend exploring other astrological topics')
            interventions.append('Highlight trending content in user\'s secondary interests')
        
        # General high-risk interventions
        if risk_score >= 0.8:
            interventions.append('Personal outreach with customized horoscope')
            interventions.append('Offer premium features or exclusive content')
            interventions.append('Survey user for improvement suggestions')
        
        return list(set(interventions))  # Remove duplicates


class EngagementOptimizationService:
    """
    Service for optimizing user engagement and content delivery.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def optimize_content_timing(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Determine optimal content delivery timing for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with timing optimization recommendations
        """
        try:
            # Get user interaction history
            result = await self.db.execute(
                select(UserInteraction).
                where(UserInteraction.user_id == user_id).
                order_by(desc(UserInteraction.timestamp)).
                limit(50)
            )
            interactions = result.scalars().all()

            if not interactions:
                return self._get_default_timing()

            # Analyze engagement patterns
            hourly_engagement = self._analyze_hourly_engagement(interactions)
            daily_engagement = self._analyze_daily_engagement(interactions)
            
            # Find optimal times
            best_hours = sorted(hourly_engagement.items(), key=lambda x: x[1], reverse=True)[:3]
            best_days = sorted(daily_engagement.items(), key=lambda x: x[1], reverse=True)[:2]

            # Calculate engagement consistency
            consistency_score = self._calculate_engagement_consistency(interactions)

            return {
                'optimal_hours': [hour for hour, score in best_hours],
                'optimal_days': [day for day, score in best_days],
                'hourly_pattern': hourly_engagement,
                'daily_pattern': daily_engagement,
                'consistency_score': consistency_score,
                'recommended_frequency': self._calculate_optimal_frequency(interactions),
                'best_content_types': self._analyze_content_preferences(interactions),
            }

        except Exception as e:
            logger.error(f"Error optimizing content timing: {e}")
            return self._get_default_timing()

    async def calculate_engagement_score(self, user_id: uuid.UUID) -> float:
        """
        Calculate overall engagement score for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Engagement score (0-1)
        """
        try:
            # Get recent interactions (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            result = await self.db.execute(
                select(UserInteraction).
                where(
                    UserInteraction.user_id == user_id,
                    UserInteraction.timestamp >= cutoff_date
                )
            )
            interactions = result.scalars().all()

            if not interactions:
                return 0.0

            # Calculate engagement factors
            factors = []
            
            # Frequency factor
            frequency = len(interactions) / 30  # Interactions per day
            frequency_score = min(1.0, frequency / 0.5)  # Normalize to 0.5 interactions/day
            factors.append(frequency_score)
            
            # Quality factor (ratings)
            ratings = [i.response_rating for i in interactions if i.response_rating]
            if ratings:
                quality_score = (np.mean(ratings) - 1) / 4  # Normalize 1-5 rating to 0-1
                factors.append(quality_score)
            
            # Duration factor
            durations = [i.session_duration for i in interactions if i.session_duration]
            if durations:
                avg_duration = np.mean(durations)
                duration_score = min(1.0, avg_duration / 120)  # Normalize to 2 minutes
                factors.append(duration_score)
            
            # Diversity factor
            categories = set(i.content_category for i in interactions if i.content_category)
            diversity_score = len(categories) / 6.0  # Normalize to max 6 categories
            factors.append(diversity_score)
            
            # Return weighted average
            return np.mean(factors) if factors else 0.0

        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0

    def _analyze_hourly_engagement(self, interactions: List[UserInteraction]) -> Dict[int, float]:
        """Analyze engagement patterns by hour of day."""
        hourly_scores = {}
        
        for interaction in interactions:
            hour = interaction.timestamp.hour
            if hour not in hourly_scores:
                hourly_scores[hour] = []
            
            # Score based on rating and session duration
            score = 0.5  # Base score
            if interaction.response_rating:
                score = interaction.response_rating / 5.0
            
            if interaction.session_duration:
                duration_bonus = min(0.3, interaction.session_duration / 600)  # Up to 10 minutes
                score += duration_bonus
            
            hourly_scores[hour].append(score)
        
        # Average scores for each hour
        return {hour: np.mean(scores) for hour, scores in hourly_scores.items()}

    def _analyze_daily_engagement(self, interactions: List[UserInteraction]) -> Dict[str, float]:
        """Analyze engagement patterns by day of week."""
        daily_scores = {}
        
        for interaction in interactions:
            day_name = interaction.timestamp.strftime('%A')
            if day_name not in daily_scores:
                daily_scores[day_name] = []
            
            # Score based on rating and session duration
            score = 0.5  # Base score
            if interaction.response_rating:
                score = interaction.response_rating / 5.0
            
            if interaction.session_duration:
                duration_bonus = min(0.3, interaction.session_duration / 600)
                score += duration_bonus
            
            daily_scores[day_name].append(score)
        
        return {day: np.mean(scores) for day, scores in daily_scores.items()}

    def _calculate_engagement_consistency(self, interactions: List[UserInteraction]) -> float:
        """Calculate how consistent user's engagement is over time."""
        if len(interactions) < 2:
            return 0.0
        
        # Calculate time gaps between interactions
        interactions_sorted = sorted(interactions, key=lambda x: x.timestamp)
        gaps = []
        
        for i in range(1, len(interactions_sorted)):
            gap = (interactions_sorted[i].timestamp - interactions_sorted[i-1].timestamp).total_seconds() / 86400
            gaps.append(gap)
        
        if not gaps:
            return 0.0
        
        # Consistency is inverse of variance (more consistent = lower variance)
        gap_variance = np.var(gaps)
        consistency_score = 1.0 / (1.0 + gap_variance)
        
        return consistency_score

    def _calculate_optimal_frequency(self, interactions: List[UserInteraction]) -> int:
        """Calculate optimal engagement frequency in days."""
        if len(interactions) < 2:
            return 7  # Default weekly
        
        # Calculate average gap between interactions
        interactions_sorted = sorted(interactions, key=lambda x: x.timestamp)
        gaps = []
        
        for i in range(1, len(interactions_sorted)):
            gap = (interactions_sorted[i].timestamp - interactions_sorted[i-1].timestamp).days
            gaps.append(gap)
        
        if gaps:
            avg_gap = np.mean(gaps)
            return max(1, min(7, int(avg_gap)))  # Between 1-7 days
        
        return 3  # Default every 3 days

    def _analyze_content_preferences(self, interactions: List[UserInteraction]) -> List[Dict[str, Any]]:
        """Analyze which content types have highest engagement."""
        content_scores = {}
        
        for interaction in interactions:
            if not interaction.content_category:
                continue
                
            category = interaction.content_category
            if category not in content_scores:
                content_scores[category] = {'scores': [], 'count': 0}
            
            score = 0.5
            if interaction.response_rating:
                score = interaction.response_rating / 5.0
            
            content_scores[category]['scores'].append(score)
            content_scores[category]['count'] += 1
        
        # Calculate average scores and sort
        content_prefs = []
        for category, data in content_scores.items():
            avg_score = np.mean(data['scores'])
            content_prefs.append({
                'category': category,
                'engagement_score': avg_score,
                'interaction_count': data['count']
            })
        
        content_prefs.sort(key=lambda x: x['engagement_score'], reverse=True)
        return content_prefs

    def _get_default_timing(self) -> Dict[str, Any]:
        """Get default timing recommendations for new users."""
        return {
            'optimal_hours': [9, 18, 21],  # Morning, evening, night
            'optimal_days': ['Monday', 'Wednesday', 'Friday'],
            'hourly_pattern': {},
            'daily_pattern': {},
            'consistency_score': 0.0,
            'recommended_frequency': 3,
            'best_content_types': [],
        }


class AnomalyDetectionService:
    """
    Service for detecting unusual patterns in user behavior.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)

    async def detect_user_anomalies(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Detect anomalies in a user's behavior patterns.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with anomaly detection results
        """
        try:
            # Get user interaction history
            result = await self.db.execute(
                select(UserInteraction).
                where(UserInteraction.user_id == user_id).
                order_by(desc(UserInteraction.timestamp)).
                limit(100)
            )
            interactions = result.scalars().all()

            if len(interactions) < 10:  # Need minimum data points
                return {'anomalies': [], 'risk_level': 'insufficient_data'}

            # Extract behavioral features for anomaly detection
            features = self._extract_behavioral_features(interactions)
            
            # Detect anomalies
            anomalies = self._detect_behavioral_anomalies(features)
            
            # Calculate risk level
            risk_level = self._assess_anomaly_risk(anomalies)

            return {
                'user_id': str(user_id),
                'anomalies': anomalies,
                'risk_level': risk_level,
                'total_interactions_analyzed': len(interactions),
                'analysis_date': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error detecting user anomalies: {e}")
            return {'error': str(e)}

    def _extract_behavioral_features(self, interactions: List[UserInteraction]) -> List[Dict[str, Any]]:
        """Extract features for each interaction for anomaly detection."""
        features = []
        
        for interaction in interactions:
            feature_vector = {
                'hour_of_day': interaction.timestamp.hour,
                'day_of_week': interaction.timestamp.weekday(),
                'session_duration': interaction.session_duration or 0,
                'response_rating': interaction.response_rating or 0,
                'content_category_encoded': self._encode_category(interaction.content_category),
                'interaction_type_encoded': self._encode_interaction_type(interaction.interaction_type),
            }
            features.append(feature_vector)
        
        return features

    def _detect_behavioral_anomalies(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in behavioral patterns."""
        if len(features) < 5:
            return []
        
        # Convert to numpy array
        feature_matrix = []
        for f in features:
            feature_matrix.append(list(f.values()))
        
        X = np.array(feature_matrix)
        
        # Detect anomalies
        anomaly_scores = self.isolation_forest.fit_predict(X)
        outlier_scores = self.isolation_forest.decision_function(X)
        
        anomalies = []
        for i, (is_anomaly, score) in enumerate(zip(anomaly_scores, outlier_scores)):
            if is_anomaly == -1:  # Anomaly detected
                anomaly_type = self._classify_anomaly_type(features[i])
                anomalies.append({
                    'interaction_index': i,
                    'anomaly_score': float(score),
                    'anomaly_type': anomaly_type,
                    'features': features[i],
                    'severity': 'high' if score < -0.5 else 'medium'
                })
        
        return anomalies

    def _classify_anomaly_type(self, feature_vector: Dict[str, Any]) -> str:
        """Classify the type of anomaly based on feature patterns."""
        # This is a simplified classification
        # In practice, you'd use more sophisticated methods
        
        if feature_vector['session_duration'] > 1800:  # > 30 minutes
            return 'unusually_long_session'
        elif feature_vector['session_duration'] < 5:  # < 5 seconds
            return 'unusually_short_session'
        elif feature_vector['hour_of_day'] < 5 or feature_vector['hour_of_day'] > 23:
            return 'unusual_time_activity'
        elif feature_vector['response_rating'] == 1:
            return 'very_low_satisfaction'
        else:
            return 'general_behavioral_anomaly'

    def _assess_anomaly_risk(self, anomalies: List[Dict[str, Any]]) -> str:
        """Assess overall risk level based on detected anomalies."""
        if not anomalies:
            return 'none'
        
        high_severity = sum(1 for a in anomalies if a['severity'] == 'high')
        total_anomalies = len(anomalies)
        
        if high_severity >= 3 or total_anomalies >= 10:
            return 'high'
        elif high_severity >= 1 or total_anomalies >= 5:
            return 'medium'
        else:
            return 'low'

    def _encode_category(self, category: Optional[str]) -> float:
        """Encode content category as numeric value."""
        categories = {
            'career': 0.0, 'love': 0.17, 'health': 0.33, 
            'finance': 0.5, 'family': 0.67, 'spiritual': 0.83
        }
        return categories.get(category, 1.0) if category else 1.0

    def _encode_interaction_type(self, interaction_type: str) -> float:
        """Encode interaction type as numeric value."""
        types = {
            'request': 0.0, 'feedback': 0.25, 'rating': 0.5, 
            'share': 0.75, 'save': 1.0
        }
        return types.get(interaction_type, 0.5)