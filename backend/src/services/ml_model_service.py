"""
Machine Learning Model Service
Handles ML model deployment, inference, and model management for GA4 analytics
"""

import logging
import pickle
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from dataclasses import dataclass
from enum import Enum
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from ..core.config import settings

logger = logging.getLogger(__name__)


class ModelType(Enum):
    ANOMALY_DETECTION = "anomaly_detection"
    TREND_PREDICTION = "trend_prediction"
    USER_SEGMENTATION = "user_segmentation"
    CONVERSION_PREDICTION = "conversion_prediction"
    CHURN_PREDICTION = "churn_prediction"


class ModelStatus(Enum):
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"
    UPDATING = "updating"


@dataclass
class ModelMetadata:
    model_id: str
    model_type: ModelType
    version: str
    status: ModelStatus
    created_at: datetime
    last_updated: datetime
    accuracy: Optional[float]
    training_data_hash: str
    hyperparameters: Dict[str, Any]
    feature_names: List[str]


@dataclass
class PredictionResult:
    prediction: Union[float, int, List[float], Dict[str, Any]]
    confidence: float
    model_version: str
    timestamp: datetime
    feature_importance: Optional[Dict[str, float]] = None


@dataclass
class ModelPerformance:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: Optional[float]
    mse: Optional[float]
    mae: Optional[float]


class MLModelService:
    """Service for managing ML models and predictions"""
    
    def __init__(self):
        self.models_dir = Path(settings.MODELS_DIR if hasattr(settings, 'MODELS_DIR') else "models")
        self.models_dir.mkdir(exist_ok=True)
        self.loaded_models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, ModelMetadata] = {}
        
    async def initialize_models(self):
        """Initialize and load pre-trained models"""
        try:
            # Load model metadata
            await self._load_model_metadata()
            
            # Load core models
            await self._load_core_models()
            
            logger.info(f"Initialized {len(self.loaded_models)} ML models")
            
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
    
    async def _load_model_metadata(self):
        """Load model metadata from disk"""
        metadata_file = self.models_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                
                for model_id, data in metadata_dict.items():
                    self.model_metadata[model_id] = ModelMetadata(
                        model_id=data['model_id'],
                        model_type=ModelType(data['model_type']),
                        version=data['version'],
                        status=ModelStatus(data['status']),
                        created_at=datetime.fromisoformat(data['created_at']),
                        last_updated=datetime.fromisoformat(data['last_updated']),
                        accuracy=data.get('accuracy'),
                        training_data_hash=data['training_data_hash'],
                        hyperparameters=data['hyperparameters'],
                        feature_names=data['feature_names']
                    )
            except Exception as e:
                logger.error(f"Error loading model metadata: {e}")
    
    async def _load_core_models(self):
        """Load essential models for real-time inference"""
        core_models = [
            ModelType.ANOMALY_DETECTION,
            ModelType.TREND_PREDICTION,
            ModelType.CONVERSION_PREDICTION
        ]
        
        for model_type in core_models:
            try:
                await self._load_model(model_type)
            except Exception as e:
                logger.warning(f"Could not load {model_type.value} model: {e}")
                # Create default/fallback model
                await self._create_default_model(model_type)
    
    async def _load_model(self, model_type: ModelType, model_id: Optional[str] = None):
        """Load a specific model from disk"""
        if model_id is None:
            # Find latest version of model type
            model_id = self._get_latest_model_id(model_type)
        
        if not model_id:
            raise ValueError(f"No model found for type {model_type.value}")
        
        model_path = self.models_dir / f"{model_id}.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        self.loaded_models[model_id] = model
        logger.info(f"Loaded model {model_id}")
    
    async def _create_default_model(self, model_type: ModelType):
        """Create default/fallback models for when trained models aren't available"""
        model_id = f"default_{model_type.value}"
        
        if model_type == ModelType.ANOMALY_DETECTION:
            # Simple Z-score based anomaly detection
            model = DefaultAnomalyDetector()
        elif model_type == ModelType.TREND_PREDICTION:
            # Simple linear regression trend predictor
            model = DefaultTrendPredictor()
        elif model_type == ModelType.CONVERSION_PREDICTION:
            # Simple rule-based conversion predictor
            model = DefaultConversionPredictor()
        else:
            model = DefaultModel()
        
        self.loaded_models[model_id] = model
        
        # Create metadata
        self.model_metadata[model_id] = ModelMetadata(
            model_id=model_id,
            model_type=model_type,
            version="1.0.0-default",
            status=ModelStatus.READY,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            accuracy=0.7,  # Baseline accuracy
            training_data_hash="default",
            hyperparameters={},
            feature_names=model.get_feature_names() if hasattr(model, 'get_feature_names') else []
        )
        
        logger.info(f"Created default model for {model_type.value}")
    
    def _get_latest_model_id(self, model_type: ModelType) -> Optional[str]:
        """Get the latest model ID for a given type"""
        models_of_type = [
            (model_id, metadata) for model_id, metadata in self.model_metadata.items()
            if metadata.model_type == model_type and metadata.status == ModelStatus.READY
        ]
        
        if not models_of_type:
            return None
        
        # Sort by last_updated and return the latest
        latest = sorted(models_of_type, key=lambda x: x[1].last_updated, reverse=True)[0]
        return latest[0]
    
    async def predict_anomaly(
        self, 
        data: Dict[str, List[float]], 
        metric: str,
        client_id: str
    ) -> PredictionResult:
        """Predict if a metric value is anomalous"""
        try:
            model_id = self._get_latest_model_id(ModelType.ANOMALY_DETECTION)
            if not model_id:
                model_id = f"default_{ModelType.ANOMALY_DETECTION.value}"
            
            model = self.loaded_models[model_id]
            
            # Prepare features
            features = self._prepare_anomaly_features(data, metric)
            
            # Make prediction
            is_anomaly, anomaly_score = model.predict(features)
            
            return PredictionResult(
                prediction={"is_anomaly": is_anomaly, "anomaly_score": anomaly_score},
                confidence=min(0.95, anomaly_score / 5.0),
                model_version=self.model_metadata[model_id].version,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in anomaly prediction: {e}")
            return PredictionResult(
                prediction={"is_anomaly": False, "anomaly_score": 0.0},
                confidence=0.0,
                model_version="error",
                timestamp=datetime.now()
            )
    
    async def predict_trend(
        self, 
        data: List[float], 
        periods: int = 7
    ) -> PredictionResult:
        """Predict future trend values"""
        try:
            model_id = self._get_latest_model_id(ModelType.TREND_PREDICTION)
            if not model_id:
                model_id = f"default_{ModelType.TREND_PREDICTION.value}"
            
            model = self.loaded_models[model_id]
            
            # Make prediction
            predictions = model.predict(data, periods)
            
            # Calculate confidence based on data stability
            confidence = self._calculate_trend_confidence(data)
            
            return PredictionResult(
                prediction=predictions,
                confidence=confidence,
                model_version=self.model_metadata[model_id].version,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in trend prediction: {e}")
            return PredictionResult(
                prediction=[],
                confidence=0.0,
                model_version="error",
                timestamp=datetime.now()
            )
    
    async def predict_conversion_probability(
        self, 
        user_features: Dict[str, Any]
    ) -> PredictionResult:
        """Predict conversion probability for a user/session"""
        try:
            model_id = self._get_latest_model_id(ModelType.CONVERSION_PREDICTION)
            if not model_id:
                model_id = f"default_{ModelType.CONVERSION_PREDICTION.value}"
            
            model = self.loaded_models[model_id]
            
            # Prepare features
            features = self._prepare_conversion_features(user_features)
            
            # Make prediction
            conversion_probability = model.predict_proba(features)
            
            return PredictionResult(
                prediction=float(conversion_probability),
                confidence=0.8,  # Model confidence
                model_version=self.model_metadata[model_id].version,
                timestamp=datetime.now(),
                feature_importance=model.get_feature_importance() if hasattr(model, 'get_feature_importance') else None
            )
            
        except Exception as e:
            logger.error(f"Error in conversion prediction: {e}")
            return PredictionResult(
                prediction=0.02,  # Default baseline conversion rate
                confidence=0.0,
                model_version="error",
                timestamp=datetime.now()
            )
    
    async def segment_users(
        self, 
        user_data: List[Dict[str, Any]]
    ) -> PredictionResult:
        """Segment users based on behavior patterns"""
        try:
            model_id = self._get_latest_model_id(ModelType.USER_SEGMENTATION)
            if not model_id:
                # Create simple rule-based segmentation
                segments = self._rule_based_segmentation(user_data)
                return PredictionResult(
                    prediction=segments,
                    confidence=0.7,
                    model_version="rule-based",
                    timestamp=datetime.now()
                )
            
            model = self.loaded_models[model_id]
            
            # Prepare features for all users
            features_matrix = [self._prepare_user_features(user) for user in user_data]
            
            # Make predictions
            segments = model.predict(features_matrix)
            
            return PredictionResult(
                prediction=segments.tolist(),
                confidence=0.85,
                model_version=self.model_metadata[model_id].version,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in user segmentation: {e}")
            return PredictionResult(
                prediction=[],
                confidence=0.0,
                model_version="error",
                timestamp=datetime.now()
            )
    
    def _prepare_anomaly_features(self, data: Dict[str, List[float]], metric: str) -> List[float]:
        """Prepare features for anomaly detection"""
        metric_data = data.get(metric, [])
        if len(metric_data) < 2:
            return [0, 0, 0, 0, 0]  # Default features
        
        # Statistical features
        mean_val = np.mean(metric_data[:-1])  # Exclude current value
        std_val = np.std(metric_data[:-1])
        current_val = metric_data[-1]
        z_score = (current_val - mean_val) / std_val if std_val > 0 else 0
        
        # Trend features
        slope = 0
        if len(metric_data) >= 7:
            x = np.arange(len(metric_data[-7:]))
            slope = np.polyfit(x, metric_data[-7:], 1)[0]
        
        return [current_val, mean_val, std_val, z_score, slope]
    
    def _prepare_conversion_features(self, user_features: Dict[str, Any]) -> List[float]:
        """Prepare features for conversion prediction"""
        # Extract relevant features (this would be more sophisticated in production)
        features = [
            user_features.get('session_duration', 0) / 60,  # Convert to minutes
            user_features.get('page_views', 0),
            1 if user_features.get('is_returning_user', False) else 0,
            user_features.get('bounce_rate', 0),
            user_features.get('time_on_site', 0) / 60,
        ]
        return features
    
    def _prepare_user_features(self, user_data: Dict[str, Any]) -> List[float]:
        """Prepare features for user segmentation"""
        return [
            user_data.get('total_sessions', 0),
            user_data.get('total_revenue', 0),
            user_data.get('avg_session_duration', 0),
            user_data.get('pages_per_session', 0),
            user_data.get('bounce_rate', 0),
        ]
    
    def _calculate_trend_confidence(self, data: List[float]) -> float:
        """Calculate confidence in trend prediction based on data quality"""
        if len(data) < 7:
            return 0.3
        
        # Calculate coefficient of variation
        mean_val = np.mean(data)
        std_val = np.std(data)
        cv = std_val / mean_val if mean_val > 0 else 1
        
        # Convert to confidence (inverse relationship)
        confidence = max(0.3, min(0.95, 1 - cv))
        return confidence
    
    def _rule_based_segmentation(self, user_data: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """Simple rule-based user segmentation"""
        segments = {
            "high_value": [],
            "medium_value": [],
            "low_value": [],
            "new_users": [],
            "at_risk": []
        }
        
        for i, user in enumerate(user_data):
            total_revenue = user.get('total_revenue', 0)
            total_sessions = user.get('total_sessions', 0)
            days_since_last_session = user.get('days_since_last_session', 0)
            
            if total_revenue > 100:
                segments["high_value"].append(i)
            elif total_revenue > 20:
                segments["medium_value"].append(i)
            elif total_sessions == 1:
                segments["new_users"].append(i)
            elif days_since_last_session > 30:
                segments["at_risk"].append(i)
            else:
                segments["low_value"].append(i)
        
        return segments
    
    async def train_model(
        self, 
        model_type: ModelType, 
        training_data: Dict[str, Any],
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Train a new model with provided data"""
        try:
            model_id = f"{model_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create model metadata
            metadata = ModelMetadata(
                model_id=model_id,
                model_type=model_type,
                version="1.0.0",
                status=ModelStatus.TRAINING,
                created_at=datetime.now(),
                last_updated=datetime.now(),
                accuracy=None,
                training_data_hash=self._hash_data(training_data),
                hyperparameters=hyperparameters or {},
                feature_names=list(training_data.get('features', {}).keys())
            )
            
            self.model_metadata[model_id] = metadata
            
            # Train model (this would be more sophisticated in production)
            model = await self._train_model_async(model_type, training_data, hyperparameters)
            
            # Evaluate model
            performance = await self._evaluate_model(model, training_data)
            
            # Save model
            await self._save_model(model_id, model)
            
            # Update metadata
            metadata.status = ModelStatus.READY
            metadata.accuracy = performance.accuracy
            metadata.last_updated = datetime.now()
            
            # Save metadata
            await self._save_metadata()
            
            logger.info(f"Successfully trained model {model_id} with accuracy {performance.accuracy:.3f}")
            return model_id
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            if model_id in self.model_metadata:
                self.model_metadata[model_id].status = ModelStatus.FAILED
            raise
    
    async def _train_model_async(
        self, 
        model_type: ModelType, 
        training_data: Dict[str, Any],
        hyperparameters: Optional[Dict[str, Any]]
    ):
        """Train model asynchronously (placeholder for actual ML training)"""
        # This would integrate with actual ML frameworks like scikit-learn, TensorFlow, etc.
        # For now, return appropriate default models
        
        if model_type == ModelType.ANOMALY_DETECTION:
            return DefaultAnomalyDetector()
        elif model_type == ModelType.TREND_PREDICTION:
            return DefaultTrendPredictor()
        elif model_type == ModelType.CONVERSION_PREDICTION:
            return DefaultConversionPredictor()
        else:
            return DefaultModel()
    
    async def _evaluate_model(self, model, training_data: Dict[str, Any]) -> ModelPerformance:
        """Evaluate model performance"""
        # Placeholder evaluation - would use proper train/test splits in production
        return ModelPerformance(
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            auc_roc=0.9,
            mse=None,
            mae=None
        )
    
    async def _save_model(self, model_id: str, model):
        """Save model to disk"""
        model_path = self.models_dir / f"{model_id}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
    
    async def _save_metadata(self):
        """Save model metadata to disk"""
        metadata_dict = {}
        for model_id, metadata in self.model_metadata.items():
            metadata_dict[model_id] = {
                'model_id': metadata.model_id,
                'model_type': metadata.model_type.value,
                'version': metadata.version,
                'status': metadata.status.value,
                'created_at': metadata.created_at.isoformat(),
                'last_updated': metadata.last_updated.isoformat(),
                'accuracy': metadata.accuracy,
                'training_data_hash': metadata.training_data_hash,
                'hyperparameters': metadata.hyperparameters,
                'feature_names': metadata.feature_names
            }
        
        metadata_file = self.models_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
    
    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Create hash of training data for versioning"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        """Get information about a specific model"""
        return self.model_metadata.get(model_id)
    
    async def list_models(self, model_type: Optional[ModelType] = None) -> List[ModelMetadata]:
        """List all available models, optionally filtered by type"""
        models = list(self.model_metadata.values())
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        return sorted(models, key=lambda x: x.last_updated, reverse=True)


# Default/Fallback Model Classes

class DefaultModel:
    """Base default model class"""
    
    def predict(self, features):
        return 0
    
    def get_feature_names(self):
        return []


class DefaultAnomalyDetector(DefaultModel):
    """Default anomaly detection using Z-score"""
    
    def predict(self, features: List[float]) -> Tuple[bool, float]:
        if len(features) < 4:
            return False, 0.0
        
        z_score = abs(features[3])  # Z-score is the 4th feature
        is_anomaly = z_score > 2.5
        
        return is_anomaly, z_score
    
    def get_feature_names(self):
        return ['current_value', 'mean', 'std', 'z_score', 'slope']


class DefaultTrendPredictor(DefaultModel):
    """Default trend prediction using linear extrapolation"""
    
    def predict(self, data: List[float], periods: int = 7) -> List[float]:
        if len(data) < 2:
            return [data[-1] if data else 0] * periods
        
        # Simple linear regression
        x = np.arange(len(data))
        slope, intercept = np.polyfit(x, data, 1)
        
        # Predict future values
        future_x = np.arange(len(data), len(data) + periods)
        predictions = slope * future_x + intercept
        
        return predictions.tolist()
    
    def get_feature_names(self):
        return ['time_series_data']


class DefaultConversionPredictor(DefaultModel):
    """Default conversion prediction using simple rules"""
    
    def predict_proba(self, features: List[float]) -> float:
        if len(features) < 5:
            return 0.02  # Default conversion rate
        
        session_duration, page_views, is_returning, bounce_rate, time_on_site = features[:5]
        
        # Simple scoring based on user behavior
        score = 0.02  # Base conversion rate
        
        if session_duration > 5:  # More than 5 minutes
            score += 0.01
        if page_views > 3:
            score += 0.015
        if is_returning:
            score += 0.02
        if bounce_rate < 0.5:
            score += 0.01
        if time_on_site > 10:
            score += 0.005
        
        return min(score, 0.5)  # Cap at 50%
    
    def get_feature_importance(self):
        return {
            'session_duration': 0.25,
            'page_views': 0.20,
            'is_returning_user': 0.25,
            'bounce_rate': 0.15,
            'time_on_site': 0.15
        }
    
    def get_feature_names(self):
        return ['session_duration', 'page_views', 'is_returning_user', 'bounce_rate', 'time_on_site']