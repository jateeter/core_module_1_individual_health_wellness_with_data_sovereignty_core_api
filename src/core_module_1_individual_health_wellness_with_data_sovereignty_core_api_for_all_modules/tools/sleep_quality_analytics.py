from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, Optional
import json
import math
from datetime import datetime, time

class SleepQualityAnalyticsInput(BaseModel):
    """Input schema for Sleep Quality Analytics Tool."""
    sleep_duration: float = Field(..., description="Total sleep time in hours", ge=0, le=24)
    time_in_bed: float = Field(..., description="Total time from bedtime to wake in hours", ge=0, le=24)
    deep_sleep_minutes: int = Field(..., description="Deep sleep stage duration in minutes", ge=0)
    light_sleep_minutes: int = Field(..., description="Light sleep stage duration in minutes", ge=0)
    rem_sleep_minutes: int = Field(..., description="REM sleep duration in minutes", ge=0)
    awakenings: int = Field(..., description="Number of sleep interruptions", ge=0)
    bedtime: str = Field(..., description="Sleep start time in HH:MM format (24-hour)")
    wake_time: str = Field(..., description="Wake up time in HH:MM format (24-hour)")
    room_temp: float = Field(..., description="Bedroom temperature in Celsius", ge=0, le=50)
    caffeine_hours: float = Field(..., description="Hours since last caffeine consumption", ge=0)
    screen_time_before_bed: int = Field(..., description="Minutes of screen exposure before sleep", ge=0)
    age: Optional[int] = Field(30, description="Age for personalized scoring (default: 30)", ge=1, le=120)
    historical_scores: Optional[list] = Field([], description="Previous sleep quality scores for trend analysis")

class SleepQualityAnalyticsTool(BaseTool):
    """Tool for comprehensive sleep quality analysis and scoring."""

    name: str = "Sleep Quality Analytics"
    description: str = (
        "Analyzes sleep metrics and provides detailed scoring including sleep efficiency, "
        "stage distribution, consistency, environmental factors, and personalized insights. "
        "Returns comprehensive JSON with component scores and optimization recommendations."
    )
    args_schema: Type[BaseModel] = SleepQualityAnalyticsInput

    def _run(
        self,
        sleep_duration: float,
        time_in_bed: float,
        deep_sleep_minutes: int,
        light_sleep_minutes: int,
        rem_sleep_minutes: int,
        awakenings: int,
        bedtime: str,
        wake_time: str,
        room_temp: float,
        caffeine_hours: float,
        screen_time_before_bed: int,
        age: int = 30,
        historical_scores: list = []
    ) -> str:
        try:
            # Calculate individual component scores
            efficiency_score = self._calculate_sleep_efficiency(sleep_duration, time_in_bed)
            stage_score = self._calculate_stage_distribution(
                deep_sleep_minutes, light_sleep_minutes, rem_sleep_minutes, sleep_duration
            )
            consistency_score = self._calculate_consistency_score(bedtime, wake_time)
            interruption_score = self._calculate_interruption_score(awakenings, sleep_duration)
            environmental_score = self._calculate_environmental_score(room_temp, caffeine_hours, screen_time_before_bed)
            sleep_debt_score = self._calculate_sleep_debt(sleep_duration, age)
            
            # Calculate weighted composite score
            composite_score = self._calculate_composite_score({
                'efficiency': efficiency_score,
                'stages': stage_score,
                'consistency': consistency_score,
                'interruptions': interruption_score,
                'environment': environmental_score,
                'sleep_debt': sleep_debt_score
            })
            
            # Trend analysis
            trend_analysis = self._analyze_trends(historical_scores, composite_score)
            
            # Generate insights and recommendations
            insights = self._generate_insights(
                efficiency_score, stage_score, consistency_score, 
                interruption_score, environmental_score, sleep_debt_score,
                room_temp, caffeine_hours, screen_time_before_bed, awakenings
            )
            
            # Compile comprehensive results
            results = {
                "sleep_quality_analysis": {
                    "composite_score": round(composite_score, 1),
                    "grade": self._get_grade(composite_score),
                    "component_scores": {
                        "sleep_efficiency": {
                            "score": round(efficiency_score, 1),
                            "percentage": round((sleep_duration / time_in_bed) * 100, 1) if time_in_bed > 0 else 0,
                            "interpretation": self._interpret_efficiency(efficiency_score)
                        },
                        "sleep_stage_distribution": {
                            "score": round(stage_score, 1),
                            "deep_sleep_percentage": round((deep_sleep_minutes / (sleep_duration * 60)) * 100, 1) if sleep_duration > 0 else 0,
                            "light_sleep_percentage": round((light_sleep_minutes / (sleep_duration * 60)) * 100, 1) if sleep_duration > 0 else 0,
                            "rem_sleep_percentage": round((rem_sleep_minutes / (sleep_duration * 60)) * 100, 1) if sleep_duration > 0 else 0,
                            "interpretation": self._interpret_stages(stage_score)
                        },
                        "sleep_consistency": {
                            "score": round(consistency_score, 1),
                            "bedtime": bedtime,
                            "wake_time": wake_time,
                            "interpretation": self._interpret_consistency(consistency_score)
                        },
                        "sleep_interruptions": {
                            "score": round(interruption_score, 1),
                            "awakening_count": awakenings,
                            "awakenings_per_hour": round(awakenings / sleep_duration, 2) if sleep_duration > 0 else 0,
                            "interpretation": self._interpret_interruptions(interruption_score)
                        },
                        "environmental_factors": {
                            "score": round(environmental_score, 1),
                            "room_temperature": room_temp,
                            "caffeine_timing": caffeine_hours,
                            "screen_exposure": screen_time_before_bed,
                            "interpretation": self._interpret_environment(environmental_score)
                        },
                        "sleep_debt": {
                            "score": round(sleep_debt_score, 1),
                            "recommended_hours": self._get_recommended_sleep(age),
                            "actual_hours": sleep_duration,
                            "deficit_surplus": round(sleep_duration - self._get_recommended_sleep(age), 1),
                            "interpretation": self._interpret_sleep_debt(sleep_debt_score)
                        }
                    },
                    "trend_analysis": trend_analysis,
                    "personalized_insights": insights,
                    "optimization_recommendations": self._generate_recommendations(
                        efficiency_score, stage_score, consistency_score,
                        interruption_score, environmental_score, sleep_debt_score,
                        room_temp, caffeine_hours, screen_time_before_bed
                    )
                }
            }
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Sleep quality analysis failed: {str(e)}",
                "status": "failed"
            }, indent=2)

    def _calculate_sleep_efficiency(self, sleep_duration: float, time_in_bed: float) -> float:
        """Calculate sleep efficiency score (0-100)"""
        if time_in_bed == 0:
            return 0
        efficiency = (sleep_duration / time_in_bed) * 100
        # Score based on efficiency percentage (85%+ is excellent)
        if efficiency >= 85:
            return 100
        elif efficiency >= 75:
            return 80 + (efficiency - 75) * 2
        elif efficiency >= 65:
            return 60 + (efficiency - 65) * 2
        else:
            return max(0, efficiency - 5)

    def _calculate_stage_distribution(self, deep: int, light: int, rem: int, duration: float) -> float:
        """Calculate sleep stage distribution score"""
        if duration == 0:
            return 0
        
        total_minutes = duration * 60
        deep_pct = (deep / total_minutes) * 100
        light_pct = (light / total_minutes) * 100
        rem_pct = (rem / total_minutes) * 100
        
        # Optimal ranges: Deep 15-20%, Light 45-55%, REM 20-25%
        deep_score = max(0, 100 - abs(deep_pct - 17.5) * 4)
        light_score = max(0, 100 - abs(light_pct - 50) * 2)
        rem_score = max(0, 100 - abs(rem_pct - 22.5) * 3)
        
        return (deep_score + light_score + rem_score) / 3

    def _calculate_consistency_score(self, bedtime: str, wake_time: str) -> float:
        """Calculate consistency score based on regular sleep schedule"""
        try:
            bed_hour = int(bedtime.split(':')[0])
            wake_hour = int(wake_time.split(':')[0])
            
            # Ideal bedtime range: 21:00-23:00, wake time: 06:00-08:00
            bed_score = 100 if 21 <= bed_hour <= 23 else max(0, 100 - abs(bed_hour - 22) * 10)
            wake_score = 100 if 6 <= wake_hour <= 8 else max(0, 100 - abs(wake_hour - 7) * 10)
            
            return (bed_score + wake_score) / 2
        except:
            return 50  # Default score if time parsing fails

    def _calculate_interruption_score(self, awakenings: int, duration: float) -> float:
        """Calculate score based on sleep interruptions"""
        if duration == 0:
            return 0
        
        awakenings_per_hour = awakenings / duration
        # 0 awakenings = 100, 1/hour = 70, 2/hour = 40, 3+/hour = 0-20
        if awakenings_per_hour == 0:
            return 100
        elif awakenings_per_hour <= 0.5:
            return 90 - (awakenings_per_hour * 40)
        elif awakenings_per_hour <= 1:
            return 70 - ((awakenings_per_hour - 0.5) * 60)
        else:
            return max(0, 40 - ((awakenings_per_hour - 1) * 20))

    def _calculate_environmental_score(self, temp: float, caffeine_hrs: float, screen_time: int) -> float:
        """Calculate environmental factors score"""
        # Temperature: optimal 15.6-19.4°C (60-67°F)
        temp_score = 100 if 16 <= temp <= 19 else max(0, 100 - abs(temp - 17.5) * 8)
        
        # Caffeine: 6+ hours before bed is ideal
        caffeine_score = min(100, caffeine_hrs * 16.67)  # 100% at 6 hours
        
        # Screen time: 0 minutes is ideal, penalize heavily after 30 min
        screen_score = max(0, 100 - (screen_time * 2 if screen_time <= 30 else 60 + (screen_time - 30) * 4))
        
        return (temp_score + caffeine_score + screen_score) / 3

    def _calculate_sleep_debt(self, duration: float, age: int) -> float:
        """Calculate sleep debt score"""
        recommended = self._get_recommended_sleep(age)
        difference = duration - recommended
        
        # Perfect score at recommended hours, deduct for deficit/surplus
        if abs(difference) <= 0.5:
            return 100
        else:
            return max(0, 100 - abs(difference) * 20)

    def _get_recommended_sleep(self, age: int) -> float:
        """Get recommended sleep hours by age"""
        if age < 18:
            return 9.0
        elif age < 26:
            return 8.5
        elif age < 65:
            return 8.0
        else:
            return 7.5

    def _calculate_composite_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted composite score"""
        weights = {
            'efficiency': 0.25,
            'stages': 0.20,
            'consistency': 0.15,
            'interruptions': 0.20,
            'environment': 0.10,
            'sleep_debt': 0.10
        }
        return sum(scores[key] * weights[key] for key in scores.keys())

    def _analyze_trends(self, historical: list, current: float) -> Dict[str, Any]:
        """Analyze sleep quality trends"""
        if not historical:
            return {"trend": "no_data", "message": "No historical data available"}
        
        if len(historical) == 1:
            change = current - historical[0]
            return {
                "trend": "improving" if change > 0 else "declining" if change < 0 else "stable",
                "change": round(change, 1),
                "message": f"Sleep quality {'improved' if change > 0 else 'declined' if change < 0 else 'remained stable'} by {abs(change):.1f} points"
            }
        
        recent_avg = sum(historical[-3:]) / min(3, len(historical))
        change = current - recent_avg
        
        return {
            "trend": "improving" if change > 2 else "declining" if change < -2 else "stable",
            "change": round(change, 1),
            "recent_average": round(recent_avg, 1),
            "message": f"Current score is {change:+.1f} points vs recent average"
        }

    def _generate_insights(self, *scores) -> list:
        """Generate personalized insights"""
        efficiency, stages, consistency, interruptions, environment, debt = scores[:6]
        insights = []
        
        if efficiency < 70:
            insights.append("Sleep efficiency is below optimal. Consider reducing time spent awake in bed.")
        if stages < 70:
            insights.append("Sleep stage distribution could be improved for more restorative sleep.")
        if consistency < 70:
            insights.append("Irregular sleep schedule detected. Consistent bedtimes improve sleep quality.")
        if interruptions < 70:
            insights.append("Frequent awakenings are affecting sleep continuity.")
        if environment < 70:
            insights.append("Environmental factors may be impacting sleep quality.")
        if debt < 70:
            insights.append("Sleep duration doesn't match recommended hours for optimal health.")
        
        return insights if insights else ["Sleep quality metrics are within healthy ranges."]

    def _generate_recommendations(self, *scores) -> list:
        """Generate optimization recommendations"""
        efficiency, stages, consistency, interruptions, environment, debt, temp, caffeine, screen = scores[:6] + scores[6:]
        recommendations = []
        
        if efficiency < 70:
            recommendations.append("Limit bed activities to sleep only to improve sleep efficiency.")
        if stages < 70:
            recommendations.append("Focus on sleep hygiene to optimize deep sleep and REM cycles.")
        if consistency < 70:
            recommendations.append("Establish a consistent sleep schedule, even on weekends.")
        if interruptions < 70:
            recommendations.append("Address factors causing nighttime awakenings.")
        if temp < 16 or temp > 20:
            recommendations.append(f"Adjust room temperature to 16-19°C (currently {temp}°C).")
        if caffeine < 6:
            recommendations.append("Avoid caffeine 6+ hours before bedtime.")
        if screen > 30:
            recommendations.append("Reduce screen time to under 30 minutes before bed.")
        
        return recommendations if recommendations else ["Continue maintaining your healthy sleep habits."]

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90: return "A"
        elif score >= 80: return "B"
        elif score >= 70: return "C"
        elif score >= 60: return "D"
        else: return "F"

    def _interpret_efficiency(self, score: float) -> str:
        if score >= 85: return "Excellent sleep efficiency"
        elif score >= 75: return "Good sleep efficiency"
        elif score >= 65: return "Fair sleep efficiency"
        else: return "Poor sleep efficiency - consider sleep hygiene improvements"

    def _interpret_stages(self, score: float) -> str:
        if score >= 80: return "Optimal sleep stage distribution"
        elif score >= 70: return "Good sleep stage balance"
        elif score >= 60: return "Acceptable sleep stages"
        else: return "Suboptimal sleep stage distribution"

    def _interpret_consistency(self, score: float) -> str:
        if score >= 80: return "Excellent sleep schedule consistency"
        elif score >= 60: return "Good sleep timing"
        else: return "Irregular sleep schedule - consider standardizing bedtimes"

    def _interpret_interruptions(self, score: float) -> str:
        if score >= 85: return "Minimal sleep disruption"
        elif score >= 70: return "Moderate sleep continuity"
        else: return "Frequent sleep interruptions detected"

    def _interpret_environment(self, score: float) -> str:
        if score >= 80: return "Optimal sleep environment"
        elif score >= 65: return "Good sleep conditions"
        else: return "Environmental factors may be impacting sleep quality"

    def _interpret_sleep_debt(self, score: float) -> str:
        if score >= 85: return "Meeting sleep duration recommendations"
        elif score >= 70: return "Minor sleep debt"
        else: return "Significant sleep debt - consider increasing sleep duration"