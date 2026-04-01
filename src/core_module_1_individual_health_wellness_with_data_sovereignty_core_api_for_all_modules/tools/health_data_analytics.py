from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, List, Optional, Union
import json
import math
from statistics import mean, median, stdev

class HealthDataAnalyticsInput(BaseModel):
    """Input schema for Health Data Analytics Tool."""
    patient_id: str = Field(..., description="Patient identifier for personalized analysis")
    health_metrics: Dict[str, List[Union[float, int]]] = Field(..., description="Dictionary of health measurements (glucose, blood_pressure_systolic, blood_pressure_diastolic, heart_rate, weight, temperature, etc.)")
    lifestyle_data: Dict[str, List[Union[float, int, str]]] = Field(..., description="Sleep, activity, nutrition, medication data")
    measurement_timestamps: List[str] = Field(..., description="When each measurement was taken (ISO format)")
    historical_data: Optional[Dict[str, List[Union[float, int]]]] = Field(default={}, description="Previous health measurements for trend analysis")
    patient_profile: Dict[str, Any] = Field(..., description="Age, health conditions, goals for contextual analysis")

class HealthDataAnalyticsTool(BaseTool):
    """Tool for comprehensive health data analytics and pattern recognition without making medical predictions."""

    name: str = "Health Data Analytics"
    description: str = (
        "Analyzes patient health metrics to identify trends, patterns, and correlations without making medical predictions. "
        "Provides comprehensive health scoring and lifestyle correlation analysis for healthcare provider review."
    )
    args_schema: Type[BaseModel] = HealthDataAnalyticsInput

    def _run(self, patient_id: str, health_metrics: Dict[str, List[Union[float, int]]], 
             lifestyle_data: Dict[str, List[Union[float, int, str]]], measurement_timestamps: List[str],
             historical_data: Optional[Dict[str, List[Union[float, int]]]] = None,
             patient_profile: Dict[str, Any] = None) -> str:
        try:
            if historical_data is None:
                historical_data = {}
            if patient_profile is None:
                patient_profile = {}
                
            # Initialize analysis results
            analysis_results = {
                "patient_id": patient_id,
                "analysis_timestamp": measurement_timestamps[-1] if measurement_timestamps else "",
                "vital_signs_analysis": {},
                "pattern_recognition": {},
                "health_scores": {},
                "lifestyle_correlations": {},
                "data_quality_assessment": {},
                "summary": {}
            }

            # 1. Vital Signs Analysis
            analysis_results["vital_signs_analysis"] = self._analyze_vital_signs(health_metrics, historical_data)

            # 2. Pattern Recognition
            analysis_results["pattern_recognition"] = self._identify_patterns(health_metrics, measurement_timestamps)

            # 3. Health Scoring
            analysis_results["health_scores"] = self._calculate_health_scores(health_metrics, patient_profile)

            # 4. Lifestyle Correlations
            analysis_results["lifestyle_correlations"] = self._analyze_lifestyle_correlations(
                health_metrics, lifestyle_data, measurement_timestamps
            )

            # 5. Data Quality Assessment
            analysis_results["data_quality_assessment"] = self._assess_data_quality(
                health_metrics, lifestyle_data, measurement_timestamps
            )

            # 6. Generate Summary
            analysis_results["summary"] = self._generate_summary(analysis_results)

            return json.dumps(analysis_results, indent=2)

        except Exception as e:
            error_result = {
                "error": f"Health data analysis failed: {str(e)}",
                "patient_id": patient_id,
                "analysis_status": "failed"
            }
            return json.dumps(error_result, indent=2)

    def _analyze_vital_signs(self, health_metrics: Dict, historical_data: Dict) -> Dict:
        """Analyze trends in vital signs."""
        vital_analysis = {}
        
        vital_signs = ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                      'weight', 'temperature', 'glucose']
        
        for vital in vital_signs:
            if vital in health_metrics and health_metrics[vital]:
                values = [float(v) for v in health_metrics[vital] if v is not None]
                if values:
                    analysis = {
                        "current_values": values,
                        "mean": round(mean(values), 2),
                        "median": round(median(values), 2),
                        "range": {
                            "min": round(min(values), 2),
                            "max": round(max(values), 2)
                        }
                    }
                    
                    if len(values) > 1:
                        analysis["standard_deviation"] = round(stdev(values), 2)
                        analysis["trend"] = self._calculate_trend(values)
                    
                    # Compare with historical data if available
                    if vital in historical_data and historical_data[vital]:
                        hist_values = [float(v) for v in historical_data[vital] if v is not None]
                        if hist_values:
                            analysis["historical_comparison"] = {
                                "historical_mean": round(mean(hist_values), 2),
                                "change_from_historical": round(analysis["mean"] - mean(hist_values), 2)
                            }
                    
                    vital_analysis[vital] = analysis
        
        return vital_analysis

    def _identify_patterns(self, health_metrics: Dict, timestamps: List[str]) -> Dict:
        """Identify patterns and anomalies in health data."""
        patterns = {
            "outliers": {},
            "correlations": {},
            "cyclical_patterns": {}
        }
        
        # Outlier detection using IQR method
        for metric, values in health_metrics.items():
            if isinstance(values, list) and len(values) >= 4:
                numeric_values = [float(v) for v in values if v is not None and str(v).replace('.', '').replace('-', '').isdigit()]
                if len(numeric_values) >= 4:
                    outliers = self._detect_outliers(numeric_values)
                    if outliers:
                        patterns["outliers"][metric] = {
                            "outlier_values": outliers,
                            "outlier_count": len(outliers),
                            "total_measurements": len(numeric_values)
                        }
        
        # Simple correlation analysis between metrics
        metric_pairs = [(m1, m2) for i, m1 in enumerate(health_metrics.keys()) 
                       for m2 in list(health_metrics.keys())[i+1:]]
        
        for m1, m2 in metric_pairs:
            if (isinstance(health_metrics[m1], list) and isinstance(health_metrics[m2], list) 
                and len(health_metrics[m1]) == len(health_metrics[m2]) and len(health_metrics[m1]) >= 3):
                
                corr = self._calculate_correlation(health_metrics[m1], health_metrics[m2])
                if abs(corr) > 0.3:  # Only include meaningful correlations
                    patterns["correlations"][f"{m1}_vs_{m2}"] = {
                        "correlation_coefficient": round(corr, 3),
                        "strength": self._interpret_correlation(corr)
                    }
        
        return patterns

    def _calculate_health_scores(self, health_metrics: Dict, patient_profile: Dict) -> Dict:
        """Calculate comprehensive health scores."""
        scores = {}
        
        # Overall health trend score (0-100)
        metric_scores = []
        
        # Score each vital sign based on typical healthy ranges
        scoring_rules = {
            "heart_rate": {"optimal_range": (60, 100), "weight": 0.2},
            "blood_pressure_systolic": {"optimal_range": (90, 120), "weight": 0.25},
            "blood_pressure_diastolic": {"optimal_range": (60, 80), "weight": 0.25},
            "weight": {"weight": 0.1},  # Weight scoring depends on patient profile
            "glucose": {"optimal_range": (70, 140), "weight": 0.2}
        }
        
        for metric, values in health_metrics.items():
            if metric in scoring_rules and values:
                numeric_values = [float(v) for v in values if v is not None]
                if numeric_values:
                    avg_value = mean(numeric_values)
                    
                    if "optimal_range" in scoring_rules[metric]:
                        opt_min, opt_max = scoring_rules[metric]["optimal_range"]
                        if opt_min <= avg_value <= opt_max:
                            metric_score = 100
                        else:
                            # Calculate distance from optimal range
                            if avg_value < opt_min:
                                distance = opt_min - avg_value
                                metric_score = max(0, 100 - (distance / opt_min * 100))
                            else:
                                distance = avg_value - opt_max
                                metric_score = max(0, 100 - (distance / opt_max * 100))
                        
                        metric_scores.append(metric_score * scoring_rules[metric]["weight"])
        
        if metric_scores:
            scores["composite_health_score"] = round(sum(metric_scores) / sum([rule["weight"] for rule in scoring_rules.values()]), 1)
        
        # Consistency score based on variability
        consistency_scores = []
        for metric, values in health_metrics.items():
            if isinstance(values, list) and len(values) > 1:
                numeric_values = [float(v) for v in values if v is not None]
                if len(numeric_values) > 1:
                    cv = (stdev(numeric_values) / mean(numeric_values)) * 100  # Coefficient of variation
                    consistency_score = max(0, 100 - cv)  # Lower variability = higher consistency
                    consistency_scores.append(consistency_score)
        
        if consistency_scores:
            scores["consistency_score"] = round(mean(consistency_scores), 1)
        
        return scores

    def _analyze_lifestyle_correlations(self, health_metrics: Dict, lifestyle_data: Dict, timestamps: List[str]) -> Dict:
        """Analyze correlations between lifestyle factors and health metrics."""
        correlations = {}
        
        # Analyze correlations between lifestyle and health metrics
        for lifestyle_factor, lifestyle_values in lifestyle_data.items():
            for health_metric, health_values in health_metrics.items():
                if (len(lifestyle_values) == len(health_values) and 
                    len(lifestyle_values) >= 3):
                    
                    # Convert to numeric if possible
                    try:
                        numeric_lifestyle = [float(v) for v in lifestyle_values if v is not None]
                        numeric_health = [float(v) for v in health_values if v is not None]
                        
                        if len(numeric_lifestyle) == len(numeric_health) and len(numeric_lifestyle) >= 3:
                            corr = self._calculate_correlation(numeric_lifestyle, numeric_health)
                            
                            if abs(corr) > 0.2:
                                correlations[f"{lifestyle_factor}_vs_{health_metric}"] = {
                                    "correlation": round(corr, 3),
                                    "interpretation": self._interpret_correlation(corr),
                                    "data_points": len(numeric_lifestyle)
                                }
                    except (ValueError, TypeError):
                        continue
        
        return correlations

    def _assess_data_quality(self, health_metrics: Dict, lifestyle_data: Dict, timestamps: List[str]) -> Dict:
        """Assess the quality and completeness of the data."""
        assessment = {
            "completeness": {},
            "consistency": {},
            "temporal_coverage": {}
        }
        
        # Completeness assessment
        total_expected = len(timestamps) if timestamps else 0
        
        for metric, values in {**health_metrics, **lifestyle_data}.items():
            if isinstance(values, list):
                non_null_count = len([v for v in values if v is not None and str(v).strip() != ""])
                completeness_rate = (non_null_count / total_expected * 100) if total_expected > 0 else 0
                assessment["completeness"][metric] = {
                    "completeness_rate": round(completeness_rate, 1),
                    "missing_values": total_expected - non_null_count,
                    "total_expected": total_expected
                }
        
        # Temporal coverage
        if timestamps:
            assessment["temporal_coverage"] = {
                "measurement_count": len(timestamps),
                "time_span": {
                    "start": timestamps[0],
                    "end": timestamps[-1]
                }
            }
        
        return assessment

    def _generate_summary(self, analysis_results: Dict) -> Dict:
        """Generate a comprehensive summary of the analysis."""
        summary = {
            "key_findings": [],
            "data_quality_status": "good",
            "recommendations": []
        }
        
        # Key findings from vital signs
        if "vital_signs_analysis" in analysis_results:
            for vital, analysis in analysis_results["vital_signs_analysis"].items():
                if "trend" in analysis:
                    trend = analysis["trend"]
                    if abs(trend) > 5:
                        direction = "increasing" if trend > 0 else "decreasing"
                        summary["key_findings"].append(f"{vital.replace('_', ' ').title()} shows {direction} trend")
        
        # Key findings from correlations
        if "lifestyle_correlations" in analysis_results:
            strong_correlations = [k for k, v in analysis_results["lifestyle_correlations"].items() 
                                 if abs(v["correlation"]) > 0.5]
            if strong_correlations:
                summary["key_findings"].append(f"Strong lifestyle-health correlations found: {len(strong_correlations)} relationships")
        
        # Data quality assessment
        if "data_quality_assessment" in analysis_results and "completeness" in analysis_results["data_quality_assessment"]:
            avg_completeness = mean([v["completeness_rate"] for v in analysis_results["data_quality_assessment"]["completeness"].values()])
            if avg_completeness < 70:
                summary["data_quality_status"] = "poor"
                summary["recommendations"].append("Improve data collection consistency")
            elif avg_completeness < 85:
                summary["data_quality_status"] = "fair"
        
        # Health score recommendations
        if "health_scores" in analysis_results:
            if "composite_health_score" in analysis_results["health_scores"]:
                score = analysis_results["health_scores"]["composite_health_score"]
                if score < 70:
                    summary["recommendations"].append("Focus on improving key health metrics")
                elif score > 85:
                    summary["recommendations"].append("Maintain current healthy patterns")
        
        return summary

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend using simple linear regression slope."""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        x_mean = mean(x)
        y_mean = mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return round(slope, 3)

    def _detect_outliers(self, values: List[float]) -> List[float]:
        """Detect outliers using IQR method."""
        if len(values) < 4:
            return []
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = [v for v in values if v < lower_bound or v > upper_bound]
        return outliers

    def _calculate_correlation(self, x: List, y: List) -> float:
        """Calculate Pearson correlation coefficient."""
        try:
            x_numeric = [float(v) for v in x if v is not None]
            y_numeric = [float(v) for v in y if v is not None]
            
            if len(x_numeric) != len(y_numeric) or len(x_numeric) < 2:
                return 0
            
            n = len(x_numeric)
            sum_x = sum(x_numeric)
            sum_y = sum(y_numeric)
            sum_xy = sum(x_numeric[i] * y_numeric[i] for i in range(n))
            sum_x2 = sum(x ** 2 for x in x_numeric)
            sum_y2 = sum(y ** 2 for y in y_numeric)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
            
            if denominator == 0:
                return 0
            
            return numerator / denominator
        
        except (ValueError, TypeError, ZeroDivisionError):
            return 0

    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.3:
            strength = "moderate"
        else:
            strength = "weak"
        
        direction = "positive" if corr > 0 else "negative"
        return f"{strength} {direction}"