from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Optional
import json
import math
from datetime import datetime, timedelta

class InterventionData(BaseModel):
    """Input schema for Intervention Effectiveness Tracker Tool."""
    intervention_type: str = Field(
        ..., 
        description="Type of intervention (conversational, visual, reminder, educational, behavioral_nudge)"
    )
    patient_id: str = Field(
        ..., 
        description="Patient identifier for personalized tracking"
    )
    intervention_timestamp: str = Field(
        ..., 
        description="When intervention was delivered (ISO format: YYYY-MM-DD HH:MM:SS)"
    )
    engagement_metrics: Dict[str, float] = Field(
        ..., 
        description="Response data (completion_rate, time_spent_minutes, quality_score, interaction_count)"
    )
    outcome_metrics: Dict[str, float] = Field(
        ..., 
        description="Measured results (goal_achievement_score, behavior_change_rating, adherence_rate)"
    )
    patient_feedback: Optional[Dict[str, float]] = Field(
        default=None, 
        description="Optional satisfaction or preference ratings (satisfaction_score, usefulness_rating, preference_level)"
    )
    contextual_factors: Dict[str, Any] = Field(
        ..., 
        description="Context data (hour_of_day, day_of_week, patient_state, location, weather_condition)"
    )
    historical_data: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Previous intervention data for pattern analysis"
    )

class InterventionEffectivenessTracker(BaseTool):
    """Tool for measuring and analyzing the success of wellness micro-interventions."""

    name: str = "intervention_effectiveness_tracker"
    description: str = (
        "Comprehensive tool that tracks individual patient responses to different intervention types, "
        "measures engagement rates, calculates effectiveness scores, analyzes response patterns, "
        "and provides personalized optimization recommendations for wellness micro-interventions."
    )
    args_schema: Type[BaseModel] = InterventionData

    def _calculate_base_effectiveness_score(self, engagement: Dict[str, float], outcomes: Dict[str, float]) -> float:
        """Calculate base effectiveness score from engagement and outcome metrics."""
        try:
            # Engagement component (40% weight)
            completion_rate = engagement.get('completion_rate', 0.0)
            time_quality = min(engagement.get('time_spent_minutes', 0.0) / 10.0, 1.0)  # Normalize to max 10 min
            quality_score = engagement.get('quality_score', 0.0) / 10.0  # Assume 0-10 scale
            interaction_factor = min(engagement.get('interaction_count', 1.0) / 5.0, 1.0)  # Normalize to max 5
            
            engagement_score = (completion_rate * 0.4 + time_quality * 0.3 + 
                              quality_score * 0.2 + interaction_factor * 0.1) * 40

            # Outcome component (60% weight)
            goal_achievement = outcomes.get('goal_achievement_score', 0.0)
            behavior_change = outcomes.get('behavior_change_rating', 0.0) / 10.0  # Assume 0-10 scale
            adherence = outcomes.get('adherence_rate', 0.0)
            
            outcome_score = (goal_achievement * 0.5 + behavior_change * 0.3 + adherence * 0.2) * 60

            return min(engagement_score + outcome_score, 100.0)
        except Exception as e:
            return 50.0  # Default neutral score on error

    def _apply_intervention_type_weights(self, base_score: float, intervention_type: str, 
                                       engagement: Dict[str, float]) -> float:
        """Apply intervention-specific weightings to base score."""
        try:
            type_multipliers = {
                'conversational': 1.1 if engagement.get('quality_score', 0) > 7 else 1.0,
                'visual': 1.15 if engagement.get('time_spent_minutes', 0) > 2 else 0.9,
                'reminder': 1.2 if engagement.get('completion_rate', 0) > 0.8 else 0.8,
                'educational': 1.1 if engagement.get('time_spent_minutes', 0) > 5 else 0.9,
                'behavioral_nudge': 1.25 if engagement.get('completion_rate', 0) > 0.9 else 0.85
            }
            
            multiplier = type_multipliers.get(intervention_type.lower(), 1.0)
            return min(base_score * multiplier, 100.0)
        except Exception:
            return base_score

    def _calculate_contextual_adjustments(self, base_score: float, context: Dict[str, Any]) -> float:
        """Apply contextual factor adjustments to effectiveness score."""
        try:
            adjusted_score = base_score
            
            # Time-of-day adjustments
            hour = int(context.get('hour_of_day', 12))
            if 8 <= hour <= 10 or 19 <= hour <= 21:  # Peak engagement hours
                adjusted_score *= 1.1
            elif hour < 7 or hour > 22:  # Low engagement hours
                adjusted_score *= 0.8

            # Day-of-week adjustments
            day = context.get('day_of_week', 'monday').lower()
            if day in ['monday', 'tuesday', 'wednesday']:  # Higher motivation days
                adjusted_score *= 1.05
            elif day in ['friday', 'saturday']:  # Lower motivation days
                adjusted_score *= 0.95

            # Patient state adjustments
            patient_state = context.get('patient_state', 'normal').lower()
            if patient_state == 'motivated':
                adjusted_score *= 1.2
            elif patient_state == 'stressed':
                adjusted_score *= 0.7
            elif patient_state == 'tired':
                adjusted_score *= 0.8

            return min(adjusted_score, 100.0)
        except Exception:
            return base_score

    def _analyze_historical_patterns(self, historical_data: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze patterns from historical intervention data."""
        if not historical_data:
            return {
                'optimal_timing': 'No historical data available',
                'intervention_fatigue': False,
                'trend_analysis': 'Insufficient data',
                'effectiveness_trend': 0.0
            }

        try:
            # Extract effectiveness scores from historical data
            scores = []
            timing_data = {}
            intervention_counts = {}

            for record in historical_data:
                score = record.get('effectiveness_score', 0)
                scores.append(score)
                
                # Timing analysis
                hour = record.get('hour_of_day', 12)
                if hour not in timing_data:
                    timing_data[hour] = []
                timing_data[hour].append(score)
                
                # Intervention type counting
                int_type = record.get('intervention_type', 'unknown')
                intervention_counts[int_type] = intervention_counts.get(int_type, 0) + 1

            # Calculate trends
            if len(scores) >= 3:
                recent_avg = sum(scores[-3:]) / 3
                earlier_avg = sum(scores[:-3]) / len(scores[:-3]) if len(scores) > 3 else recent_avg
                trend = recent_avg - earlier_avg
            else:
                trend = 0.0

            # Find optimal timing
            optimal_hour = 12
            if timing_data:
                best_hour = max(timing_data.keys(), key=lambda h: sum(timing_data[h]) / len(timing_data[h]))
                optimal_hour = best_hour

            # Detect intervention fatigue (declining scores over time)
            fatigue_detected = len(scores) > 5 and all(
                scores[i] >= scores[i+1] for i in range(-3, -1)
            )

            return {
                'optimal_timing': f"Hour {optimal_hour}:00",
                'intervention_fatigue': fatigue_detected,
                'trend_analysis': 'Improving' if trend > 5 else 'Declining' if trend < -5 else 'Stable',
                'effectiveness_trend': round(trend, 2),
                'total_interventions': len(historical_data),
                'intervention_distribution': intervention_counts
            }

        except Exception:
            return {
                'optimal_timing': 'Analysis error',
                'intervention_fatigue': False,
                'trend_analysis': 'Unable to determine',
                'effectiveness_trend': 0.0
            }

    def _generate_recommendations(self, effectiveness_score: float, intervention_type: str, 
                                context: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """Generate personalized optimization recommendations."""
        recommendations = []
        
        try:
            # Score-based recommendations
            if effectiveness_score < 30:
                recommendations.append("Consider switching to a different intervention type")
                recommendations.append("Assess patient motivation and readiness for change")
            elif effectiveness_score < 60:
                recommendations.append("Optimize intervention timing based on patient preferences")
                recommendations.append("Increase engagement through personalization")
            elif effectiveness_score >= 80:
                recommendations.append("Maintain current intervention approach - highly effective")
                recommendations.append("Consider reducing intervention frequency to prevent fatigue")

            # Type-specific recommendations
            if intervention_type.lower() == 'conversational':
                if effectiveness_score < 70:
                    recommendations.append("Enhance conversational flow and natural language processing")
            elif intervention_type.lower() == 'visual':
                if effectiveness_score < 70:
                    recommendations.append("Optimize visual design and user interface elements")
            elif intervention_type.lower() == 'reminder':
                if effectiveness_score < 70:
                    recommendations.append("Adjust reminder frequency and timing")

            # Pattern-based recommendations
            if patterns.get('intervention_fatigue'):
                recommendations.append("Implement intervention variety to combat fatigue")
                recommendations.append("Consider temporary reduction in intervention frequency")

            if patterns.get('trend_analysis') == 'Declining':
                recommendations.append("Investigate factors causing effectiveness decline")
                recommendations.append("Refresh intervention content or delivery method")

            # Contextual recommendations
            optimal_time = patterns.get('optimal_timing', '').replace('Hour ', '').replace(':00', '')
            if optimal_time.isdigit():
                recommendations.append(f"Schedule future interventions around {optimal_time}:00 for optimal engagement")

            return recommendations[:6]  # Limit to top 6 recommendations

        except Exception:
            return ["Unable to generate recommendations due to data processing error"]

    def _run(self, intervention_type: str, patient_id: str, intervention_timestamp: str,
             engagement_metrics: Dict[str, float], outcome_metrics: Dict[str, float],
             patient_feedback: Optional[Dict[str, float]], contextual_factors: Dict[str, Any],
             historical_data: Optional[List[Dict[str, Any]]]) -> str:
        try:
            # Calculate base effectiveness score
            base_score = self._calculate_base_effectiveness_score(engagement_metrics, outcome_metrics)
            
            # Apply intervention-type specific weights
            type_adjusted_score = self._apply_intervention_type_weights(base_score, intervention_type, engagement_metrics)
            
            # Apply contextual adjustments
            final_score = self._calculate_contextual_adjustments(type_adjusted_score, contextual_factors)
            
            # Apply patient feedback if available
            if patient_feedback:
                feedback_score = sum(patient_feedback.values()) / len(patient_feedback) / 10.0  # Normalize
                final_score = (final_score * 0.8) + (feedback_score * 100 * 0.2)
            
            final_score = min(round(final_score, 2), 100.0)
            
            # Analyze historical patterns
            pattern_analysis = self._analyze_historical_patterns(historical_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(final_score, intervention_type, contextual_factors, pattern_analysis)
            
            # Create engagement analytics
            engagement_analytics = {
                'completion_rate': engagement_metrics.get('completion_rate', 0.0),
                'average_engagement_time': engagement_metrics.get('time_spent_minutes', 0.0),
                'quality_assessment': 'High' if engagement_metrics.get('quality_score', 0) > 7 else 'Medium' if engagement_metrics.get('quality_score', 0) > 4 else 'Low',
                'interaction_intensity': 'High' if engagement_metrics.get('interaction_count', 0) > 3 else 'Medium' if engagement_metrics.get('interaction_count', 0) > 1 else 'Low'
            }
            
            # Create outcome analysis
            outcome_analysis = {
                'goal_achievement_level': 'High' if outcome_metrics.get('goal_achievement_score', 0) > 0.8 else 'Medium' if outcome_metrics.get('goal_achievement_score', 0) > 0.5 else 'Low',
                'behavior_change_impact': 'Significant' if outcome_metrics.get('behavior_change_rating', 0) > 7 else 'Moderate' if outcome_metrics.get('behavior_change_rating', 0) > 4 else 'Minimal',
                'adherence_level': 'Excellent' if outcome_metrics.get('adherence_rate', 0) > 0.9 else 'Good' if outcome_metrics.get('adherence_rate', 0) > 0.7 else 'Needs Improvement'
            }
            
            # Compile comprehensive result
            result = {
                'intervention_analysis': {
                    'patient_id': patient_id,
                    'intervention_type': intervention_type,
                    'timestamp': intervention_timestamp,
                    'effectiveness_score': final_score,
                    'score_category': 'Highly Effective' if final_score >= 80 else 'Moderately Effective' if final_score >= 60 else 'Low Effectiveness' if final_score >= 40 else 'Ineffective'
                },
                'engagement_analytics': engagement_analytics,
                'outcome_analysis': outcome_analysis,
                'pattern_insights': pattern_analysis,
                'personalized_recommendations': recommendations,
                'optimization_strategies': {
                    'timing_optimization': pattern_analysis.get('optimal_timing', 'Insufficient data'),
                    'intervention_frequency': 'Reduce frequency' if pattern_analysis.get('intervention_fatigue') else 'Maintain current frequency',
                    'content_personalization': 'High priority' if final_score < 60 else 'Medium priority',
                    'contextual_targeting': 'Focus on ' + contextual_factors.get('patient_state', 'optimal') + ' state interventions'
                },
                'summary': {
                    'overall_effectiveness': f"{final_score}% effective",
                    'primary_strength': 'Engagement' if sum(engagement_metrics.values()) / len(engagement_metrics) > sum(outcome_metrics.values()) / len(outcome_metrics) else 'Outcomes',
                    'improvement_focus': 'Engagement strategies' if final_score < 60 else 'Outcome optimization' if final_score < 80 else 'Maintain excellence',
                    'next_intervention_timing': pattern_analysis.get('optimal_timing', 'Standard schedule')
                }
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            error_result = {
                'error': 'Intervention effectiveness analysis failed',
                'message': f'Error processing intervention data: {str(e)}',
                'patient_id': patient_id,
                'intervention_type': intervention_type,
                'fallback_recommendations': [
                    'Review input data format and completeness',
                    'Ensure all required metrics are provided',
                    'Verify timestamp format (YYYY-MM-DD HH:MM:SS)',
                    'Check that numeric values are within expected ranges'
                ]
            }
            return json.dumps(error_result, indent=2)