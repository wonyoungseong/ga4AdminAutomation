"""
AI Insights Service for GA4 Analytics
Provides machine learning powered insights, anomaly detection, and predictive analytics
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from ..models.db_models import Client, User
from ..core.config import settings

logger = logging.getLogger(__name__)


class InsightType(Enum):
    ANOMALY = "anomaly"
    TREND = "trend"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AIInsight:
    """AI-generated insight data structure"""
    insight_id: str
    type: InsightType
    priority: Priority
    title: str
    description: str
    data: Dict[str, Any]
    confidence: float
    timestamp: datetime
    client_id: Optional[str] = None
    metric_name: Optional[str] = None
    actionable_recommendations: Optional[List[str]] = None


@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    is_anomaly: bool
    anomaly_score: float
    expected_range: Tuple[float, float]
    actual_value: float
    severity: Priority
    description: str


@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1
    trend_duration_days: int
    projected_value: Optional[float]
    confidence_interval: Optional[Tuple[float, float]]


@dataclass
class UserBehaviorPrediction:
    """User behavior prediction result"""
    predicted_sessions: int
    predicted_users: int
    predicted_conversion_rate: float
    predicted_bounce_rate: float
    time_horizon_days: int
    confidence: float


class AIInsightsService:
    """Service for AI-powered analytics insights"""
    
    def __init__(self):
        self.anomaly_threshold = 2.5  # Standard deviations
        self.trend_min_days = 7  # Minimum days for trend analysis
        self.confidence_threshold = 0.7  # Minimum confidence for insights
        
    async def generate_comprehensive_insights(
        self,
        ga4_data: Dict[str, Any],
        client_id: str,
        db: AsyncSession
    ) -> List[AIInsight]:
        """
        Generate comprehensive AI insights from GA4 data
        
        Args:
            ga4_data: Raw GA4 analytics data
            client_id: Client identifier
            db: Database session
            
        Returns:
            List of AI-generated insights
        """
        insights = []
        
        try:
            # Anomaly Detection
            anomaly_insights = await self._detect_anomalies(ga4_data, client_id)
            insights.extend(anomaly_insights)
            
            # Trend Analysis
            trend_insights = await self._analyze_trends(ga4_data, client_id)
            insights.extend(trend_insights)
            
            # Predictive Analytics
            prediction_insights = await self._generate_predictions(ga4_data, client_id)
            insights.extend(prediction_insights)
            
            # Recommendation Engine
            recommendation_insights = await self._generate_recommendations(ga4_data, client_id, db)
            insights.extend(recommendation_insights)
            
            # Filter by confidence threshold
            filtered_insights = [
                insight for insight in insights 
                if insight.confidence >= self.confidence_threshold
            ]
            
            # Sort by priority and confidence
            filtered_insights.sort(
                key=lambda x: (x.priority.value, -x.confidence), 
                reverse=True
            )
            
            logger.info(f"Generated {len(filtered_insights)} AI insights for client {client_id}")
            return filtered_insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return []
    
    async def _detect_anomalies(self, ga4_data: Dict[str, Any], client_id: str) -> List[AIInsight]:
        """Detect anomalies in GA4 metrics using statistical methods"""
        insights = []
        
        # Key metrics to monitor for anomalies
        metrics_to_check = [
            'sessions', 'users', 'page_views', 'bounce_rate', 
            'conversion_rate', 'avg_session_duration'
        ]
        
        for metric in metrics_to_check:
            if metric in ga4_data and len(ga4_data[metric]) > 7:  # Need minimum data
                anomaly_result = self._detect_metric_anomaly(ga4_data[metric], metric)
                
                if anomaly_result.is_anomaly:
                    insight = AIInsight(
                        insight_id=f"anomaly_{metric}_{client_id}_{datetime.now().isoformat()}",
                        type=InsightType.ANOMALY,
                        priority=anomaly_result.severity,
                        title=f"Anomaly Detected: {metric.replace('_', ' ').title()}",
                        description=anomaly_result.description,
                        data={
                            "metric": metric,
                            "anomaly_score": anomaly_result.anomaly_score,
                            "expected_range": anomaly_result.expected_range,
                            "actual_value": anomaly_result.actual_value,
                            "historical_data": ga4_data[metric][-30:]  # Last 30 days
                        },
                        confidence=min(0.95, anomaly_result.anomaly_score / 5.0),
                        timestamp=datetime.now(),
                        client_id=client_id,
                        metric_name=metric,
                        actionable_recommendations=self._get_anomaly_recommendations(metric, anomaly_result)
                    )
                    insights.append(insight)
        
        return insights
    
    def _detect_metric_anomaly(self, data: List[float], metric_name: str) -> AnomalyDetection:
        """Detect anomaly in a single metric using Z-score method"""
        if len(data) < 7:
            return AnomalyDetection(False, 0.0, (0, 0), 0, Priority.LOW, "Insufficient data")
        
        # Convert to numpy array
        values = np.array(data)
        
        # Calculate rolling statistics (exclude last value for comparison)
        historical_values = values[:-1]
        current_value = values[-1]
        
        mean = np.mean(historical_values)
        std = np.std(historical_values)
        
        if std == 0:  # No variation in data
            return AnomalyDetection(False, 0.0, (mean, mean), current_value, Priority.LOW, "No variation in data")
        
        # Calculate Z-score
        z_score = abs((current_value - mean) / std)
        
        # Determine if it's an anomaly
        is_anomaly = z_score > self.anomaly_threshold
        
        # Expected range (2 standard deviations)
        expected_range = (mean - 2*std, mean + 2*std)
        
        # Determine severity
        if z_score > 4:
            severity = Priority.CRITICAL
        elif z_score > 3:
            severity = Priority.HIGH
        elif z_score > self.anomaly_threshold:
            severity = Priority.MEDIUM
        else:
            severity = Priority.LOW
        
        # Generate description
        direction = "higher" if current_value > mean else "lower"
        percentage_change = abs((current_value - mean) / mean * 100)
        
        description = f"{metric_name.replace('_', ' ').title()} is {percentage_change:.1f}% {direction} than expected (Z-score: {z_score:.2f})"
        
        return AnomalyDetection(
            is_anomaly=is_anomaly,
            anomaly_score=z_score,
            expected_range=expected_range,
            actual_value=current_value,
            severity=severity,
            description=description
        )
    
    async def _analyze_trends(self, ga4_data: Dict[str, Any], client_id: str) -> List[AIInsight]:
        """Analyze trends in GA4 metrics"""
        insights = []
        
        metrics_to_analyze = [
            'sessions', 'users', 'page_views', 'conversion_rate', 'revenue'
        ]
        
        for metric in metrics_to_analyze:
            if metric in ga4_data and len(ga4_data[metric]) >= self.trend_min_days:
                trend_analysis = self._analyze_metric_trend(ga4_data[metric], metric)
                
                if trend_analysis.trend_strength > 0.6:  # Strong trend
                    priority = Priority.HIGH if trend_analysis.trend_strength > 0.8 else Priority.MEDIUM
                    
                    insight = AIInsight(
                        insight_id=f"trend_{metric}_{client_id}_{datetime.now().isoformat()}",
                        type=InsightType.TREND,
                        priority=priority,
                        title=f"Trend Alert: {metric.replace('_', ' ').title()} {trend_analysis.trend_direction.title()}",
                        description=f"{metric.replace('_', ' ').title()} has been {trend_analysis.trend_direction} for {trend_analysis.trend_duration_days} days with {trend_analysis.trend_strength:.1%} confidence",
                        data={
                            "metric": metric,
                            "trend_direction": trend_analysis.trend_direction,
                            "trend_strength": trend_analysis.trend_strength,
                            "duration_days": trend_analysis.trend_duration_days,
                            "projected_value": trend_analysis.projected_value,
                            "confidence_interval": trend_analysis.confidence_interval,
                            "historical_data": ga4_data[metric]
                        },
                        confidence=trend_analysis.trend_strength,
                        timestamp=datetime.now(),
                        client_id=client_id,
                        metric_name=metric,
                        actionable_recommendations=self._get_trend_recommendations(metric, trend_analysis)
                    )
                    insights.append(insight)
        
        return insights
    
    def _analyze_metric_trend(self, data: List[float], metric_name: str) -> TrendAnalysis:
        """Analyze trend in a single metric using linear regression"""
        if len(data) < self.trend_min_days:
            return TrendAnalysis("stable", 0.0, 0, None, None)
        
        # Convert to numpy arrays
        values = np.array(data)
        x = np.arange(len(values))
        
        # Linear regression
        slope, intercept = np.polyfit(x, values, 1)
        
        # Calculate R-squared (trend strength)
        y_pred = slope * x + intercept
        ss_res = np.sum((values - y_pred) ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction
        if abs(slope) < 0.01 * np.mean(values):  # Less than 1% change per day
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
        
        # Project next value
        projected_value = slope * len(values) + intercept
        
        # Calculate confidence interval (simplified)
        std_error = np.std(values - y_pred)
        confidence_interval = (projected_value - 1.96*std_error, projected_value + 1.96*std_error)
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=r_squared,
            trend_duration_days=len(data),
            projected_value=projected_value,
            confidence_interval=confidence_interval
        )
    
    async def _generate_predictions(self, ga4_data: Dict[str, Any], client_id: str) -> List[AIInsight]:
        """Generate predictive analytics insights"""
        insights = []
        
        # Predict user behavior for next 7 days
        prediction = self._predict_user_behavior(ga4_data)
        
        if prediction.confidence > self.confidence_threshold:
            insight = AIInsight(
                insight_id=f"prediction_user_behavior_{client_id}_{datetime.now().isoformat()}",
                type=InsightType.PREDICTION,
                priority=Priority.MEDIUM,
                title="7-Day User Behavior Forecast",
                description=f"Predicted {prediction.predicted_sessions} sessions with {prediction.predicted_conversion_rate:.2%} conversion rate",
                data={
                    "predicted_sessions": prediction.predicted_sessions,
                    "predicted_users": prediction.predicted_users,
                    "predicted_conversion_rate": prediction.predicted_conversion_rate,
                    "predicted_bounce_rate": prediction.predicted_bounce_rate,
                    "time_horizon_days": prediction.time_horizon_days,
                    "forecast_confidence": prediction.confidence
                },
                confidence=prediction.confidence,
                timestamp=datetime.now(),
                client_id=client_id,
                actionable_recommendations=self._get_prediction_recommendations(prediction)
            )
            insights.append(insight)
        
        return insights
    
    def _predict_user_behavior(self, ga4_data: Dict[str, Any]) -> UserBehaviorPrediction:
        """Predict user behavior using simple time series forecasting"""
        # Simple moving average prediction (can be enhanced with more sophisticated models)
        try:
            sessions_data = ga4_data.get('sessions', [])
            users_data = ga4_data.get('users', [])
            conversion_data = ga4_data.get('conversion_rate', [])
            bounce_data = ga4_data.get('bounce_rate', [])
            
            if not all([sessions_data, users_data]):
                return UserBehaviorPrediction(0, 0, 0.0, 0.0, 7, 0.0)
            
            # Moving average prediction
            window = min(7, len(sessions_data))
            
            predicted_sessions = int(np.mean(sessions_data[-window:]) * 7)  # 7-day total
            predicted_users = int(np.mean(users_data[-window:]) * 7)
            
            predicted_conversion_rate = np.mean(conversion_data[-window:]) if conversion_data else 0.02
            predicted_bounce_rate = np.mean(bounce_data[-window:]) if bounce_data else 0.5
            
            # Confidence based on data stability
            sessions_std = np.std(sessions_data[-window:]) if len(sessions_data) >= window else 0
            sessions_mean = np.mean(sessions_data[-window:]) if len(sessions_data) >= window else 1
            coefficient_of_variation = sessions_std / sessions_mean if sessions_mean > 0 else 1
            confidence = max(0.3, 1 - coefficient_of_variation)
            
            return UserBehaviorPrediction(
                predicted_sessions=predicted_sessions,
                predicted_users=predicted_users,
                predicted_conversion_rate=predicted_conversion_rate,
                predicted_bounce_rate=predicted_bounce_rate,
                time_horizon_days=7,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in user behavior prediction: {e}")
            return UserBehaviorPrediction(0, 0, 0.0, 0.0, 7, 0.0)
    
    async def _generate_recommendations(
        self, 
        ga4_data: Dict[str, Any], 
        client_id: str, 
        db: AsyncSession
    ) -> List[AIInsight]:
        """Generate AI-powered recommendations"""
        insights = []
        
        # Analyze performance and generate recommendations
        recommendations = await self._analyze_performance_recommendations(ga4_data, client_id, db)
        
        for rec in recommendations:
            insight = AIInsight(
                insight_id=f"recommendation_{rec['category']}_{client_id}_{datetime.now().isoformat()}",
                type=InsightType.RECOMMENDATION,
                priority=Priority(rec['priority']),
                title=rec['title'],
                description=rec['description'],
                data=rec['data'],
                confidence=rec['confidence'],
                timestamp=datetime.now(),
                client_id=client_id,
                actionable_recommendations=rec['actions']
            )
            insights.append(insight)
        
        return insights
    
    async def _analyze_performance_recommendations(
        self, 
        ga4_data: Dict[str, Any], 
        client_id: str, 
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Analyze performance data and generate specific recommendations"""
        recommendations = []
        
        try:
            # Analyze bounce rate
            bounce_rate = ga4_data.get('bounce_rate', [])
            if bounce_rate and np.mean(bounce_rate[-7:]) > 0.6:  # High bounce rate
                recommendations.append({
                    'category': 'user_experience',
                    'priority': 'high',
                    'title': 'High Bounce Rate Optimization',
                    'description': f'Bounce rate is {np.mean(bounce_rate[-7:]):.1%}, which is above the recommended 60% threshold',
                    'data': {
                        'current_bounce_rate': np.mean(bounce_rate[-7:]),
                        'recommended_threshold': 0.6,
                        'potential_improvement': '15-25%'
                    },
                    'confidence': 0.85,
                    'actions': [
                        'Improve page loading speed',
                        'Enhance content relevance',
                        'Optimize mobile experience',
                        'Review and improve call-to-action placement'
                    ]
                })
            
            # Analyze conversion rate
            conversion_rate = ga4_data.get('conversion_rate', [])
            if conversion_rate and np.mean(conversion_rate[-7:]) < 0.02:  # Low conversion rate
                recommendations.append({
                    'category': 'conversion_optimization',
                    'priority': 'high',
                    'title': 'Conversion Rate Optimization',
                    'description': f'Conversion rate is {np.mean(conversion_rate[-7:]):.2%}, below industry average of 2%',
                    'data': {
                        'current_conversion_rate': np.mean(conversion_rate[-7:]),
                        'industry_average': 0.02,
                        'potential_revenue_increase': '50-150%'
                    },
                    'confidence': 0.8,
                    'actions': [
                        'A/B test landing pages',
                        'Simplify checkout process',
                        'Add social proof and testimonials',
                        'Optimize form fields and reduce friction'
                    ]
                })
            
            # Analyze session duration
            session_duration = ga4_data.get('avg_session_duration', [])
            if session_duration and np.mean(session_duration[-7:]) < 120:  # Less than 2 minutes
                recommendations.append({
                    'category': 'engagement',
                    'priority': 'medium',
                    'title': 'User Engagement Enhancement',
                    'description': f'Average session duration is {np.mean(session_duration[-7:]):.0f} seconds, indicating low engagement',
                    'data': {
                        'current_duration': np.mean(session_duration[-7:]),
                        'recommended_minimum': 120,
                        'engagement_score': 'Low'
                    },
                    'confidence': 0.75,
                    'actions': [
                        'Add interactive content elements',
                        'Improve internal linking',
                        'Create engaging multimedia content',
                        'Implement personalization features'
                    ]
                })
            
        except Exception as e:
            logger.error(f"Error generating performance recommendations: {e}")
        
        return recommendations
    
    def _get_anomaly_recommendations(self, metric: str, anomaly: AnomalyDetection) -> List[str]:
        """Get specific recommendations for anomaly types"""
        recommendations = []
        
        is_increase = anomaly.actual_value > anomaly.expected_range[1]
        
        if metric == 'sessions':
            if is_increase:
                recommendations = [
                    "Investigate traffic sources for quality",
                    "Monitor server capacity for increased load",
                    "Check for any marketing campaigns or viral content"
                ]
            else:
                recommendations = [
                    "Review recent website changes or issues",
                    "Check for technical problems or outages",
                    "Analyze competitor activity or market changes"
                ]
        
        elif metric == 'bounce_rate':
            if is_increase:
                recommendations = [
                    "Review landing page performance",
                    "Check page loading speeds",
                    "Analyze content relevance to traffic sources"
                ]
            else:
                recommendations = [
                    "Identify what improved user engagement",
                    "Replicate successful strategies across other pages",
                    "Document changes for future reference"
                ]
        
        elif metric == 'conversion_rate':
            if is_increase:
                recommendations = [
                    "Document successful strategies",
                    "Scale effective campaigns",
                    "Test similar approaches on other pages"
                ]
            else:
                recommendations = [
                    "Review checkout process for issues",
                    "Check payment gateway functionality",
                    "Analyze user feedback and complaints"
                ]
        
        return recommendations or ["Monitor closely and investigate root causes"]
    
    def _get_trend_recommendations(self, metric: str, trend: TrendAnalysis) -> List[str]:
        """Get specific recommendations for trend types"""
        recommendations = []
        
        if trend.trend_direction == "increasing":
            if metric in ['sessions', 'users', 'revenue']:
                recommendations = [
                    "Scale successful strategies",
                    "Increase budget for effective channels",
                    "Prepare infrastructure for continued growth"
                ]
            elif metric == 'bounce_rate':
                recommendations = [
                    "Investigate causes of increasing bounce rate",
                    "Review recent content or design changes",
                    "Optimize user experience and page speed"
                ]
        
        elif trend.trend_direction == "decreasing":
            if metric in ['sessions', 'users', 'revenue']:
                recommendations = [
                    "Investigate causes of decline",
                    "Review marketing strategy effectiveness",
                    "Consider new user acquisition channels"
                ]
            elif metric == 'bounce_rate':
                recommendations = [
                    "Continue current optimization efforts",
                    "Document successful strategies",
                    "Expand improvements to other pages"
                ]
        
        return recommendations or ["Continue monitoring trend patterns"]
    
    def _get_prediction_recommendations(self, prediction: UserBehaviorPrediction) -> List[str]:
        """Get recommendations based on predictions"""
        recommendations = []
        
        if prediction.predicted_conversion_rate < 0.02:
            recommendations.append("Focus on conversion rate optimization initiatives")
        
        if prediction.predicted_bounce_rate > 0.6:
            recommendations.append("Implement user experience improvements")
        
        if prediction.predicted_sessions > 0:
            recommendations.append("Prepare for forecasted traffic levels")
            recommendations.append("Monitor server performance and capacity")
        
        return recommendations or ["Monitor predictions vs actual performance"]
    
    @lru_cache(maxsize=100)  # Cache results for performance
    async def get_cached_insights(self, client_id: str, cache_key: str) -> Optional[List[AIInsight]]:
        """Get cached insights (implement with Redis in production)"""
        # This would integrate with Redis or another caching solution
        # For now, using in-memory cache
        return None
    
    async def natural_language_query(self, query: str, ga4_data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """
        Process natural language queries about analytics data
        This is a simplified implementation - in production, would use NLP models
        """
        query_lower = query.lower()
        response = {
            "query": query,
            "answer": "I don't understand that query yet.",
            "data": {},
            "suggestions": []
        }
        
        # Simple keyword matching (would be replaced with NLP in production)
        if any(word in query_lower for word in ['sessions', 'visits', 'traffic']):
            sessions = ga4_data.get('sessions', [])
            if sessions:
                response["answer"] = f"Your average daily sessions are {np.mean(sessions[-7:]):.0f} over the last week."
                response["data"] = {"recent_sessions": sessions[-7:]}
        
        elif any(word in query_lower for word in ['bounce', 'bounce rate']):
            bounce_rate = ga4_data.get('bounce_rate', [])
            if bounce_rate:
                avg_bounce = np.mean(bounce_rate[-7:])
                response["answer"] = f"Your average bounce rate is {avg_bounce:.1%}. " + \
                                   ("This is above the recommended 60% threshold." if avg_bounce > 0.6 else "This looks good!")
                response["data"] = {"bounce_rate": avg_bounce}
        
        elif any(word in query_lower for word in ['conversion', 'convert']):
            conversion_rate = ga4_data.get('conversion_rate', [])
            if conversion_rate:
                avg_conversion = np.mean(conversion_rate[-7:])
                response["answer"] = f"Your conversion rate is {avg_conversion:.2%}."
                response["data"] = {"conversion_rate": avg_conversion}
        
        response["suggestions"] = [
            "What's my bounce rate?",
            "How many sessions did I have this week?",
            "What's my conversion rate?",
            "Show me traffic trends"
        ]
        
        return response