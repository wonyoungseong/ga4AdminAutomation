"""
AI Insights API Router
Provides endpoints for AI-powered analytics insights, predictions, and recommendations
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth_dependencies import get_current_user, require_roles
from ...models.db_models import User, UserRole
from ...services.ai_insights_service import AIInsightsService, InsightType, Priority
from ...services.ml_model_service import MLModelService, ModelType, PredictionResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-insights", tags=["AI Insights"])

# Initialize services
ai_service = AIInsightsService()
ml_service = MLModelService()


# Pydantic Models for API

class InsightRequest(BaseModel):
    client_id: str
    ga4_data: Dict[str, Any] = Field(..., description="GA4 analytics data")
    insight_types: Optional[List[InsightType]] = Field(None, description="Specific insight types to generate")
    time_range_days: int = Field(30, ge=1, le=365, description="Time range for analysis in days")


class NaturalLanguageQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural language query about analytics")
    client_id: str
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for query")


class AnomalyDetectionRequest(BaseModel):
    client_id: str
    metric_data: Dict[str, List[float]] = Field(..., description="Metric data for anomaly detection")
    metric_name: str = Field(..., description="Name of the metric to analyze")
    threshold: Optional[float] = Field(2.5, ge=1.0, le=5.0, description="Anomaly detection threshold")


class TrendPredictionRequest(BaseModel):
    client_id: str
    historical_data: List[float] = Field(..., min_items=7, description="Historical data points")
    prediction_periods: int = Field(7, ge=1, le=30, description="Number of periods to predict")
    metric_name: str


class ConversionPredictionRequest(BaseModel):
    client_id: str
    user_features: Dict[str, Any] = Field(..., description="User behavior features")
    session_features: Optional[Dict[str, Any]] = Field(None, description="Session-level features")


class ModelTrainingRequest(BaseModel):
    model_type: ModelType
    training_data: Dict[str, Any] = Field(..., description="Training data for the model")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="Model hyperparameters")
    client_id: Optional[str] = Field(None, description="Client-specific model training")


class InsightResponse(BaseModel):
    insight_id: str
    type: InsightType
    priority: Priority
    title: str
    description: str
    data: Dict[str, Any]
    confidence: float
    timestamp: datetime
    client_id: Optional[str]
    metric_name: Optional[str]
    actionable_recommendations: Optional[List[str]]


class PredictionResponse(BaseModel):
    prediction: Any
    confidence: float
    model_version: str
    timestamp: datetime
    feature_importance: Optional[Dict[str, float]]


# API Endpoints

@router.post("/generate", response_model=List[InsightResponse])
async def generate_insights(
    request: InsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate comprehensive AI insights from GA4 data
    """
    try:
        # Validate client access
        # In production, add proper client access validation here
        
        insights = await ai_service.generate_comprehensive_insights(
            ga4_data=request.ga4_data,
            client_id=request.client_id,
            db=db
        )
        
        # Filter by requested insight types if specified
        if request.insight_types:
            insights = [insight for insight in insights if insight.type in request.insight_types]
        
        # Convert to response format
        response_insights = [
            InsightResponse(
                insight_id=insight.insight_id,
                type=insight.type,
                priority=insight.priority,
                title=insight.title,
                description=insight.description,
                data=insight.data,
                confidence=insight.confidence,
                timestamp=insight.timestamp,
                client_id=insight.client_id,
                metric_name=insight.metric_name,
                actionable_recommendations=insight.actionable_recommendations
            )
            for insight in insights
        ]
        
        logger.info(f"Generated {len(response_insights)} insights for client {request.client_id}")
        return response_insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI insights"
        )


@router.post("/query", response_model=Dict[str, Any])
async def natural_language_query(
    request: NaturalLanguageQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process natural language queries about analytics data
    """
    try:
        # For demonstration, we'll need GA4 data - in production this would be fetched
        # from the GA4 service based on client_id
        sample_ga4_data = {
            "sessions": [100, 120, 95, 110, 105, 130, 140],
            "users": [80, 95, 75, 88, 85, 105, 115],
            "bounce_rate": [0.65, 0.62, 0.68, 0.60, 0.63, 0.58, 0.55],
            "conversion_rate": [0.025, 0.030, 0.022, 0.028, 0.026, 0.032, 0.035]
        }
        
        response = await ai_service.natural_language_query(
            query=request.query,
            ga4_data=sample_ga4_data,
            client_id=request.client_id
        )
        
        logger.info(f"Processed NL query for client {request.client_id}: {request.query}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing natural language query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process natural language query"
        )


@router.post("/anomaly-detection", response_model=PredictionResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect anomalies in GA4 metrics using ML models
    """
    try:
        prediction = await ml_service.predict_anomaly(
            data=request.metric_data,
            metric=request.metric_name,
            client_id=request.client_id
        )
        
        response = PredictionResponse(
            prediction=prediction.prediction,
            confidence=prediction.confidence,
            model_version=prediction.model_version,
            timestamp=prediction.timestamp,
            feature_importance=prediction.feature_importance
        )
        
        logger.info(f"Anomaly detection completed for {request.metric_name} (client: {request.client_id})")
        return response
        
    except Exception as e:
        logger.error(f"Error in anomaly detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform anomaly detection"
        )


@router.post("/trend-prediction", response_model=PredictionResponse)
async def predict_trends(
    request: TrendPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict future trends based on historical data
    """
    try:
        prediction = await ml_service.predict_trend(
            data=request.historical_data,
            periods=request.prediction_periods
        )
        
        response = PredictionResponse(
            prediction=prediction.prediction,
            confidence=prediction.confidence,
            model_version=prediction.model_version,
            timestamp=prediction.timestamp,
            feature_importance=prediction.feature_importance
        )
        
        logger.info(f"Trend prediction completed for {request.metric_name} (client: {request.client_id})")
        return response
        
    except Exception as e:
        logger.error(f"Error in trend prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict trends"
        )


@router.post("/conversion-prediction", response_model=PredictionResponse)
async def predict_conversion(
    request: ConversionPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict conversion probability for users/sessions
    """
    try:
        # Combine user and session features
        all_features = {**request.user_features}
        if request.session_features:
            all_features.update(request.session_features)
        
        prediction = await ml_service.predict_conversion_probability(all_features)
        
        response = PredictionResponse(
            prediction=prediction.prediction,
            confidence=prediction.confidence,
            model_version=prediction.model_version,
            timestamp=prediction.timestamp,
            feature_importance=prediction.feature_importance
        )
        
        logger.info(f"Conversion prediction completed for client {request.client_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in conversion prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict conversion"
        )


@router.get("/models", response_model=List[Dict[str, Any]])
async def list_models(
    model_type: Optional[ModelType] = Query(None, description="Filter by model type"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.ANALYST])),
    db: AsyncSession = Depends(get_db)
):
    """
    List available ML models
    """
    try:
        models = await ml_service.list_models(model_type)
        
        response = [
            {
                "model_id": model.model_id,
                "model_type": model.model_type.value,
                "version": model.version,
                "status": model.status.value,
                "accuracy": model.accuracy,
                "created_at": model.created_at.isoformat(),
                "last_updated": model.last_updated.isoformat(),
                "feature_names": model.feature_names
            }
            for model in models
        ]
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list models"
        )


@router.post("/models/train", response_model=Dict[str, str])
async def train_model(
    request: ModelTrainingRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Train a new ML model (Admin only)
    """
    try:
        model_id = await ml_service.train_model(
            model_type=request.model_type,
            training_data=request.training_data,
            hyperparameters=request.hyperparameters
        )
        
        logger.info(f"Model training initiated: {model_id}")
        return {
            "model_id": model_id,
            "status": "training_started",
            "message": f"Training started for {request.model_type.value} model"
        }
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start model training"
        )


@router.get("/models/{model_id}", response_model=Dict[str, Any])
async def get_model_info(
    model_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.ANALYST])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific model
    """
    try:
        model_info = await ml_service.get_model_info(model_id)
        
        if not model_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        return {
            "model_id": model_info.model_id,
            "model_type": model_info.model_type.value,
            "version": model_info.version,
            "status": model_info.status.value,
            "accuracy": model_info.accuracy,
            "created_at": model_info.created_at.isoformat(),
            "last_updated": model_info.last_updated.isoformat(),
            "training_data_hash": model_info.training_data_hash,
            "hyperparameters": model_info.hyperparameters,
            "feature_names": model_info.feature_names
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model information"
        )


@router.get("/insights/history", response_model=List[InsightResponse])
async def get_insights_history(
    client_id: str = Query(..., description="Client ID"),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    insight_type: Optional[InsightType] = Query(None, description="Filter by insight type"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical insights for a client
    """
    try:
        # In production, this would query a database of stored insights
        # For now, return empty list as placeholder
        
        logger.info(f"Retrieved insights history for client {client_id}")
        return []
        
    except Exception as e:
        logger.error(f"Error getting insights history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get insights history"
        )


@router.get("/dashboard-summary", response_model=Dict[str, Any])
async def get_dashboard_summary(
    client_id: str = Query(..., description="Client ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI insights dashboard summary
    """
    try:
        # Sample dashboard data - in production this would aggregate real insights
        summary = {
            "total_insights": 15,
            "critical_alerts": 2,
            "anomalies_detected": 3,
            "predictions_generated": 5,
            "recommendations_active": 8,
            "model_accuracy": {
                "anomaly_detection": 0.92,
                "trend_prediction": 0.87,
                "conversion_prediction": 0.79
            },
            "recent_insights": [
                {
                    "type": "anomaly",
                    "title": "Unusual Traffic Spike",
                    "priority": "high",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "recommendation",
                    "title": "Conversion Rate Optimization",
                    "priority": "medium",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
                }
            ],
            "performance_metrics": {
                "insights_generated_today": 8,
                "avg_confidence": 0.84,
                "recommendations_implemented": 12,
                "model_prediction_accuracy": 0.86
            }
        }
        
        logger.info(f"Generated dashboard summary for client {client_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dashboard summary"
        )


# Initialize ML models on startup
@router.on_event("startup")
async def startup_event():
    """Initialize ML models when the router starts"""
    try:
        await ml_service.initialize_models()
        logger.info("AI Insights API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI Insights API: {e}")


# Health check for AI services
@router.get("/health", response_model=Dict[str, Any])
async def ai_health_check():
    """Health check for AI services"""
    try:
        # Check if models are loaded
        models_loaded = len(ml_service.loaded_models) > 0
        
        return {
            "status": "healthy" if models_loaded else "degraded",
            "models_loaded": len(ml_service.loaded_models),
            "services": {
                "ai_insights_service": "operational",
                "ml_model_service": "operational" if models_loaded else "degraded"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }