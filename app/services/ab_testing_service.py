"""
A/B testing framework for recommendation system optimization.
"""
import hashlib
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.recommendation_models import (
    ABTestGroup,
    UserABTestAssignment,
    RecommendationMetrics,
    UserRecommendation,
    UserInteraction,
)


class ABTestingService:
    """
    Service for managing A/B tests on recommendation algorithms and UI variations.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_ab_test(
        self,
        test_name: str,
        test_groups: List[Dict[str, Any]],
        description: str = None,
        duration_days: int = 30,
        created_by: str = None
    ) -> Dict[str, Any]:
        """
        Create a new A/B test with multiple groups.
        
        Args:
            test_name: Name of the test
            test_groups: List of test group configurations
            description: Test description
            duration_days: Test duration in days
            created_by: Creator identifier
            
        Returns:
            Dictionary with test creation results
        """
        try:
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=duration_days)
            
            # Validate traffic percentages sum to 100%
            total_traffic = sum(group['traffic_percentage'] for group in test_groups)
            if abs(total_traffic - 1.0) > 0.001:  # Allow small floating point errors
                raise ValueError(f"Traffic percentages must sum to 100%, got {total_traffic * 100}%")

            created_groups = []
            
            # Create test groups
            for group_config in test_groups:
                test_group = ABTestGroup(
                    test_name=test_name,
                    group_name=group_config['group_name'],
                    description=group_config.get('description', description),
                    algorithm_config=group_config['algorithm_config'],
                    traffic_percentage=group_config['traffic_percentage'],
                    start_date=start_date,
                    end_date=end_date,
                    created_by=created_by,
                    is_active=True
                )
                self.db.add(test_group)
                await self.db.flush()  # Get ID
                
                created_groups.append({
                    'id': str(test_group.id),
                    'group_name': test_group.group_name,
                    'traffic_percentage': test_group.traffic_percentage,
                    'algorithm_config': test_group.algorithm_config
                })

            await self.db.commit()
            
            logger.info(f"A/B test '{test_name}' created with {len(created_groups)} groups")
            
            return {
                'test_name': test_name,
                'groups': created_groups,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'status': 'active'
            }

        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            await self.db.rollback()
            raise

    async def assign_user_to_test(
        self, user_id: uuid.UUID, test_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Assign a user to a test group using consistent hashing.
        
        Args:
            user_id: User ID
            test_name: Test name
            
        Returns:
            Assignment information or None if test not found
        """
        try:
            # Check if user is already assigned
            existing_assignment = await self._get_user_assignment(user_id, test_name)
            if existing_assignment:
                return existing_assignment

            # Get active test groups
            result = await self.db.execute(
                select(ABTestGroup).where(
                    ABTestGroup.test_name == test_name,
                    ABTestGroup.is_active == True,
                    ABTestGroup.start_date <= datetime.utcnow(),
                    func.coalesce(ABTestGroup.end_date, datetime.utcnow() + timedelta(days=1)) > datetime.utcnow()
                ).order_by(ABTestGroup.group_name)
            )
            test_groups = result.scalars().all()

            if not test_groups:
                logger.warning(f"No active test groups found for test '{test_name}'")
                return None

            # Use consistent hashing for assignment
            selected_group = self._assign_user_to_group(user_id, test_groups)
            
            # Create assignment record
            assignment = UserABTestAssignment(
                user_id=user_id,
                test_group_id=selected_group.id,
                assignment_method='consistent_hash',
                is_active=True
            )
            self.db.add(assignment)
            await self.db.commit()

            return {
                'test_name': test_name,
                'group_name': selected_group.group_name,
                'group_id': str(selected_group.id),
                'algorithm_config': selected_group.algorithm_config,
                'assigned_at': assignment.assigned_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error assigning user to test: {e}")
            return None

    async def get_user_test_configuration(
        self, user_id: uuid.UUID, test_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's test configuration for a specific test.
        
        Args:
            user_id: User ID
            test_name: Test name
            
        Returns:
            Test configuration or None
        """
        assignment = await self.assign_user_to_test(user_id, test_name)
        return assignment

    async def record_test_interaction(
        self,
        user_id: uuid.UUID,
        test_name: str,
        interaction_type: str,
        value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a user interaction for A/B test analysis.
        
        Args:
            user_id: User ID
            test_name: Test name
            interaction_type: Type of interaction (click, conversion, etc.)
            value: Numeric value associated with interaction
            metadata: Additional metadata
            
        Returns:
            True if recorded successfully
        """
        try:
            # Get user's test assignment
            assignment = await self._get_user_assignment(user_id, test_name)
            if not assignment:
                return False

            # Record interaction (this could be stored in a separate table)
            # For now, we'll track it through the existing UserInteraction system
            # In a full implementation, you'd have a dedicated A/B test metrics table
            
            logger.info(
                f"A/B test interaction recorded: user={user_id}, test={test_name}, "
                f"group={assignment['group_name']}, type={interaction_type}, value={value}"
            )
            
            return True

        except Exception as e:
            logger.error(f"Error recording test interaction: {e}")
            return False

    async def get_test_results(self, test_name: str) -> Dict[str, Any]:
        """
        Get A/B test results and statistical analysis.
        
        Args:
            test_name: Test name
            
        Returns:
            Dictionary with test results
        """
        try:
            # Get all test groups
            result = await self.db.execute(
                select(ABTestGroup).where(ABTestGroup.test_name == test_name)
            )
            test_groups = result.scalars().all()

            if not test_groups:
                return {'error': 'Test not found'}

            # Get assignments for each group
            group_results = {}
            total_users = 0
            
            for group in test_groups:
                # Count assignments
                assignment_result = await self.db.execute(
                    select(func.count(UserABTestAssignment.id)).where(
                        UserABTestAssignment.test_group_id == group.id
                    )
                )
                user_count = assignment_result.scalar() or 0
                total_users += user_count

                # Get performance metrics (simplified)
                metrics = await self._calculate_group_metrics(group.id)
                
                group_results[group.group_name] = {
                    'group_id': str(group.id),
                    'user_count': user_count,
                    'traffic_percentage': group.traffic_percentage,
                    'algorithm_config': group.algorithm_config,
                    'metrics': metrics
                }

            # Calculate statistical significance (simplified)
            significance_results = self._calculate_statistical_significance(group_results)

            return {
                'test_name': test_name,
                'total_users': total_users,
                'groups': group_results,
                'statistical_analysis': significance_results,
                'test_status': 'active' if test_groups[0].is_active else 'completed',
                'start_date': test_groups[0].start_date.isoformat(),
                'end_date': test_groups[0].end_date.isoformat() if test_groups[0].end_date else None
            }

        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return {'error': str(e)}

    async def end_ab_test(self, test_name: str, winning_group: Optional[str] = None) -> Dict[str, Any]:
        """
        End an A/B test and optionally declare a winner.
        
        Args:
            test_name: Test name
            winning_group: Winning group name (optional)
            
        Returns:
            Test termination results
        """
        try:
            # Deactivate all test groups
            await self.db.execute(
                update(ABTestGroup).where(
                    ABTestGroup.test_name == test_name
                ).values(
                    is_active=False,
                    end_date=datetime.utcnow()
                )
            )

            # Deactivate user assignments
            result = await self.db.execute(
                select(ABTestGroup.id).where(ABTestGroup.test_name == test_name)
            )
            group_ids = [row[0] for row in result]

            if group_ids:
                await self.db.execute(
                    update(UserABTestAssignment).where(
                        UserABTestAssignment.test_group_id.in_(group_ids)
                    ).values(is_active=False)
                )

            await self.db.commit()

            # Get final results
            final_results = await self.get_test_results(test_name)

            logger.info(f"A/B test '{test_name}' ended. Winner: {winning_group or 'Not declared'}")

            return {
                'test_name': test_name,
                'status': 'completed',
                'winning_group': winning_group,
                'end_date': datetime.utcnow().isoformat(),
                'final_results': final_results
            }

        except Exception as e:
            logger.error(f"Error ending A/B test: {e}")
            await self.db.rollback()
            raise

    async def get_active_tests(self) -> List[Dict[str, Any]]:
        """
        Get all currently active A/B tests.
        
        Returns:
            List of active tests
        """
        try:
            result = await self.db.execute(
                select(ABTestGroup).where(
                    ABTestGroup.is_active == True,
                    ABTestGroup.start_date <= datetime.utcnow(),
                    func.coalesce(ABTestGroup.end_date, datetime.utcnow() + timedelta(days=1)) > datetime.utcnow()
                ).order_by(ABTestGroup.test_name, ABTestGroup.group_name)
            )
            
            test_groups = result.scalars().all()
            
            # Group by test name
            tests_by_name = {}
            for group in test_groups:
                test_name = group.test_name
                if test_name not in tests_by_name:
                    tests_by_name[test_name] = {
                        'test_name': test_name,
                        'start_date': group.start_date.isoformat(),
                        'end_date': group.end_date.isoformat() if group.end_date else None,
                        'groups': []
                    }
                
                tests_by_name[test_name]['groups'].append({
                    'group_name': group.group_name,
                    'traffic_percentage': group.traffic_percentage,
                    'description': group.description
                })

            return list(tests_by_name.values())

        except Exception as e:
            logger.error(f"Error getting active tests: {e}")
            return []

    async def _get_user_assignment(
        self, user_id: uuid.UUID, test_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing user assignment for a test."""
        result = await self.db.execute(
            select(UserABTestAssignment, ABTestGroup).
            join(ABTestGroup, UserABTestAssignment.test_group_id == ABTestGroup.id).
            where(
                UserABTestAssignment.user_id == user_id,
                ABTestGroup.test_name == test_name,
                UserABTestAssignment.is_active == True
            )
        )
        
        assignment_data = result.first()
        if not assignment_data:
            return None

        assignment, group = assignment_data
        return {
            'test_name': test_name,
            'group_name': group.group_name,
            'group_id': str(group.id),
            'algorithm_config': group.algorithm_config,
            'assigned_at': assignment.assigned_at.isoformat()
        }

    def _assign_user_to_group(
        self, user_id: uuid.UUID, test_groups: List[ABTestGroup]
    ) -> ABTestGroup:
        """Assign user to a group using consistent hashing."""
        # Create deterministic hash based on user ID
        user_hash = hashlib.md5(str(user_id).encode()).hexdigest()
        hash_int = int(user_hash[:8], 16)  # Use first 8 characters as integer
        
        # Normalize to 0-1 range
        normalized_hash = (hash_int % 10000000) / 10000000.0
        
        # Assign based on cumulative traffic percentages
        cumulative_percentage = 0.0
        for group in sorted(test_groups, key=lambda x: x.group_name):  # Sort for consistency
            cumulative_percentage += group.traffic_percentage
            if normalized_hash <= cumulative_percentage:
                return group
        
        # Fallback to last group (shouldn't happen if percentages sum to 1.0)
        return test_groups[-1]

    async def _calculate_group_metrics(self, group_id: uuid.UUID) -> Dict[str, Any]:
        """Calculate performance metrics for a test group."""
        try:
            # Get users in this group
            result = await self.db.execute(
                select(UserABTestAssignment.user_id).where(
                    UserABTestAssignment.test_group_id == group_id,
                    UserABTestAssignment.is_active == True
                )
            )
            user_ids = [row[0] for row in result]

            if not user_ids:
                return {'ctr': 0.0, 'avg_rating': 0.0, 'conversion_rate': 0.0, 'engagement_score': 0.0}

            # Calculate metrics from user interactions
            # This is a simplified version - in practice you'd have more sophisticated metrics
            
            # Get interactions for users in this group (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            interaction_result = await self.db.execute(
                select(UserInteraction).where(
                    UserInteraction.user_id.in_(user_ids),
                    UserInteraction.timestamp >= cutoff_date
                )
            )
            interactions = interaction_result.scalars().all()

            if not interactions:
                return {'ctr': 0.0, 'avg_rating': 0.0, 'conversion_rate': 0.0, 'engagement_score': 0.0}

            # Calculate CTR (interactions per user)
            ctr = len(interactions) / len(user_ids)

            # Calculate average rating
            ratings = [i.response_rating for i in interactions if i.response_rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

            # Calculate conversion rate (users with positive interactions)
            positive_interactions = set()
            for interaction in interactions:
                if interaction.response_rating and interaction.response_rating >= 4.0:
                    positive_interactions.add(interaction.user_id)
            
            conversion_rate = len(positive_interactions) / len(user_ids) if user_ids else 0.0

            # Calculate engagement score (simplified)
            total_duration = sum(i.session_duration for i in interactions if i.session_duration)
            avg_session_duration = total_duration / len(interactions) if interactions else 0.0
            engagement_score = min(1.0, avg_session_duration / 300)  # Normalize to 5 minutes

            return {
                'ctr': ctr,
                'avg_rating': avg_rating,
                'conversion_rate': conversion_rate,
                'engagement_score': engagement_score,
                'total_interactions': len(interactions),
                'avg_session_duration': avg_session_duration
            }

        except Exception as e:
            logger.error(f"Error calculating group metrics: {e}")
            return {'ctr': 0.0, 'avg_rating': 0.0, 'conversion_rate': 0.0, 'engagement_score': 0.0}

    def _calculate_statistical_significance(self, group_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical significance between groups (simplified)."""
        # This is a very simplified statistical analysis
        # In production, you'd use proper statistical tests (t-test, chi-square, etc.)
        
        if len(group_results) < 2:
            return {'significant': False, 'confidence': 0.0, 'winner': None}

        # Compare primary metric (CTR) between groups
        group_names = list(group_results.keys())
        group_ctrs = [(name, data['metrics']['ctr']) for name, data in group_results.items()]
        
        # Sort by CTR
        group_ctrs.sort(key=lambda x: x[1], reverse=True)
        
        winner = group_ctrs[0][0]
        winner_ctr = group_ctrs[0][1]
        
        # Calculate relative improvement
        if len(group_ctrs) > 1:
            baseline_ctr = group_ctrs[1][1]
            if baseline_ctr > 0:
                improvement = (winner_ctr - baseline_ctr) / baseline_ctr
            else:
                improvement = 0.0
        else:
            improvement = 0.0

        # Simple significance check (normally you'd use proper statistical tests)
        sample_sizes = [data['user_count'] for data in group_results.values()]
        min_sample_size = min(sample_sizes) if sample_sizes else 0
        
        # Very simplified: consider significant if improvement > 10% and sample size > 100
        significant = improvement > 0.1 and min_sample_size > 100
        confidence = min(0.95, improvement * 5) if significant else 0.0

        return {
            'significant': significant,
            'confidence': confidence,
            'winner': winner if significant else None,
            'improvement': improvement,
            'min_sample_size': min_sample_size
        }


class MetricsCollectionService:
    """
    Service for collecting and analyzing recommendation system metrics.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def record_recommendation_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_type: str = 'engagement',
        aggregation_period: str = 'daily',
        user_segment: Optional[str] = None,
        algorithm_version: Optional[str] = None,
        test_group: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a recommendation system metric.
        
        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            metric_type: Type of metric
            aggregation_period: Aggregation period
            user_segment: User segment
            algorithm_version: Algorithm version
            test_group: A/B test group
            additional_data: Additional context data
            
        Returns:
            True if recorded successfully
        """
        try:
            now = datetime.utcnow()
            
            # Determine period boundaries
            if aggregation_period == 'daily':
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(days=1)
            elif aggregation_period == 'weekly':
                days_since_monday = now.weekday()
                period_start = (now - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                period_end = period_start + timedelta(weeks=1)
            elif aggregation_period == 'monthly':
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if now.month == 12:
                    period_end = period_start.replace(year=now.year + 1, month=1)
                else:
                    period_end = period_start.replace(month=now.month + 1)
            else:
                period_start = now
                period_end = now + timedelta(hours=1)

            # Check if metric already exists for this period
            existing_result = await self.db.execute(
                select(RecommendationMetrics).where(
                    RecommendationMetrics.metric_name == metric_name,
                    RecommendationMetrics.aggregation_period == aggregation_period,
                    RecommendationMetrics.period_start == period_start,
                    RecommendationMetrics.user_segment == user_segment,
                    RecommendationMetrics.algorithm_version == algorithm_version,
                    RecommendationMetrics.test_group == test_group
                )
            )
            existing_metric = existing_result.scalar_one_or_none()

            if existing_metric:
                # Update existing metric (average or sum based on metric type)
                if metric_type in ['avg_rating', 'engagement_score']:
                    # For average metrics, calculate weighted average
                    current_sample = existing_metric.sample_size or 1
                    existing_metric.metric_value = (
                        (existing_metric.metric_value * current_sample + metric_value) / 
                        (current_sample + 1)
                    )
                    existing_metric.sample_size = current_sample + 1
                else:
                    # For count/sum metrics, add to existing value
                    existing_metric.metric_value += metric_value
                    existing_metric.sample_size = (existing_metric.sample_size or 0) + 1
                
                existing_metric.calculated_at = now
            else:
                # Create new metric record
                metric = RecommendationMetrics(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    aggregation_period=aggregation_period,
                    period_start=period_start,
                    period_end=period_end,
                    metric_value=metric_value,
                    sample_size=1,
                    user_segment=user_segment,
                    algorithm_version=algorithm_version,
                    test_group=test_group,
                    additional_data=additional_data
                )
                self.db.add(metric)

            await self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error recording recommendation metric: {e}")
            return False

    async def get_metrics_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        metric_names: Optional[List[str]] = None,
        user_segment: Optional[str] = None,
        test_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics summary for a time period.
        
        Args:
            start_date: Start date
            end_date: End date
            metric_names: Filter by metric names
            user_segment: Filter by user segment
            test_group: Filter by test group
            
        Returns:
            Dictionary with metrics summary
        """
        try:
            # Build query
            query = select(RecommendationMetrics).where(
                RecommendationMetrics.period_start >= start_date,
                RecommendationMetrics.period_end <= end_date
            )

            if metric_names:
                query = query.where(RecommendationMetrics.metric_name.in_(metric_names))
            if user_segment:
                query = query.where(RecommendationMetrics.user_segment == user_segment)
            if test_group:
                query = query.where(RecommendationMetrics.test_group == test_group)

            result = await self.db.execute(query.order_by(RecommendationMetrics.period_start))
            metrics = result.scalars().all()

            # Aggregate metrics by name
            summary = {}
            for metric in metrics:
                name = metric.metric_name
                if name not in summary:
                    summary[name] = {
                        'values': [],
                        'total_sample_size': 0,
                        'metric_type': metric.metric_type
                    }
                
                summary[name]['values'].append(metric.metric_value)
                summary[name]['total_sample_size'] += metric.sample_size or 1

            # Calculate aggregated statistics
            for name, data in summary.items():
                values = data['values']
                data['count'] = len(values)
                data['average'] = sum(values) / len(values) if values else 0.0
                data['min'] = min(values) if values else 0.0
                data['max'] = max(values) if values else 0.0
                data['latest'] = values[-1] if values else 0.0
                
                # Calculate trend (simple linear)
                if len(values) >= 2:
                    data['trend'] = values[-1] - values[0]
                else:
                    data['trend'] = 0.0

            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'filters': {
                    'user_segment': user_segment,
                    'test_group': test_group,
                    'metric_names': metric_names
                },
                'metrics': summary,
                'total_records': len(metrics)
            }

        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {'error': str(e)}

    async def calculate_kpi_dashboard(self) -> Dict[str, Any]:
        """
        Calculate KPI dashboard metrics for recommendation system.
        
        Returns:
            Dictionary with KPI metrics
        """
        try:
            now = datetime.utcnow()
            last_30_days = now - timedelta(days=30)
            last_7_days = now - timedelta(days=7)

            # Define key metrics to track
            key_metrics = [
                'click_through_rate',
                'conversion_rate',
                'avg_rating',
                'engagement_score',
                'retention_rate'
            ]

            kpis = {}
            
            for metric_name in key_metrics:
                # Get current period (last 7 days)
                current_result = await self.db.execute(
                    select(
                        func.avg(RecommendationMetrics.metric_value),
                        func.sum(RecommendationMetrics.sample_size)
                    ).where(
                        RecommendationMetrics.metric_name == metric_name,
                        RecommendationMetrics.period_start >= last_7_days
                    )
                )
                current_data = current_result.first()
                current_value = current_data[0] if current_data and current_data[0] else 0.0
                current_sample = current_data[1] if current_data and current_data[1] else 0

                # Get previous period (7-14 days ago)
                previous_start = now - timedelta(days=14)
                previous_end = last_7_days
                previous_result = await self.db.execute(
                    select(
                        func.avg(RecommendationMetrics.metric_value),
                        func.sum(RecommendationMetrics.sample_size)
                    ).where(
                        RecommendationMetrics.metric_name == metric_name,
                        RecommendationMetrics.period_start >= previous_start,
                        RecommendationMetrics.period_start < previous_end
                    )
                )
                previous_data = previous_result.first()
                previous_value = previous_data[0] if previous_data and previous_data[0] else 0.0

                # Calculate change percentage
                if previous_value > 0:
                    change_percent = ((current_value - previous_value) / previous_value) * 100
                else:
                    change_percent = 0.0

                kpis[metric_name] = {
                    'current_value': current_value,
                    'previous_value': previous_value,
                    'change_percent': change_percent,
                    'sample_size': current_sample,
                    'trend': 'up' if change_percent > 0 else 'down' if change_percent < 0 else 'stable'
                }

            # Overall system health score
            health_score = self._calculate_system_health_score(kpis)

            return {
                'dashboard_updated_at': now.isoformat(),
                'kpis': kpis,
                'system_health_score': health_score,
                'period_info': {
                    'current_period': f"{last_7_days.date()} to {now.date()}",
                    'comparison_period': f"{previous_start.date()} to {previous_end.date()}"
                }
            }

        except Exception as e:
            logger.error(f"Error calculating KPI dashboard: {e}")
            return {'error': str(e)}

    def _calculate_system_health_score(self, kpis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system health score based on KPIs."""
        try:
            scores = []
            
            # Define target values and weights for each metric
            targets = {
                'click_through_rate': {'target': 0.1, 'weight': 0.3},
                'conversion_rate': {'target': 0.05, 'weight': 0.3},
                'avg_rating': {'target': 4.0, 'weight': 0.2},
                'engagement_score': {'target': 0.7, 'weight': 0.2}
            }
            
            total_weight = 0
            for metric_name, config in targets.items():
                if metric_name in kpis:
                    current_value = kpis[metric_name]['current_value']
                    target_value = config['target']
                    weight = config['weight']
                    
                    # Calculate normalized score (0-1)
                    if target_value > 0:
                        score = min(1.0, current_value / target_value)
                    else:
                        score = 1.0 if current_value >= target_value else 0.0
                    
                    scores.append(score * weight)
                    total_weight += weight
            
            # Calculate weighted average
            if total_weight > 0:
                health_score = sum(scores) / total_weight
            else:
                health_score = 0.0
            
            # Categorize health
            if health_score >= 0.8:
                health_status = 'excellent'
            elif health_score >= 0.6:
                health_status = 'good'
            elif health_score >= 0.4:
                health_status = 'fair'
            else:
                health_status = 'needs_attention'
            
            return {
                'score': health_score,
                'status': health_status,
                'components_evaluated': len(scores)
            }
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return {'score': 0.0, 'status': 'error', 'components_evaluated': 0}