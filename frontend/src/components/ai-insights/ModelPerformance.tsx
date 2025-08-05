/**
 * Model Performance Component
 * Monitor and manage AI model performance and status
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  Brain, 
  Activity, 
  CheckCircle, 
  AlertCircle,
  Clock,
  RefreshCw,
  BarChart3,
  Target,
  TrendingUp,
  Lightbulb
} from 'lucide-react';

import { useAIInsights } from '@/hooks/useAIInsights';

interface ModelInfo {
  model_id: string;
  model_type: string;
  version: string;
  status: 'training' | 'ready' | 'failed' | 'updating';
  accuracy: number;
  created_at: string;
  last_updated: string;
  feature_names: string[];
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  models_loaded: number;
  services: Record<string, string>;
  timestamp: string;
}

export const ModelPerformance: React.FC = () => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  const { getModels, getModelInfo, checkHealthStatus, error } = useAIInsights();

  const loadModelData = async () => {
    setIsLoading(true);
    
    try {
      // Load all models
      const modelsData = await getModels();
      setModels(modelsData);

      // Check health status
      const health = await checkHealthStatus();
      setHealthStatus(health);

    } catch (error) {
      console.error('Error loading model data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadModelData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadModelData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'training': return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'updating': return <RefreshCw className="h-4 w-4 text-yellow-500 animate-spin" />;
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'default';
      case 'training': return 'secondary';
      case 'failed': return 'destructive';
      case 'updating': return 'default';
      default: return 'secondary';
    }
  };

  const getModelTypeIcon = (type: string) => {
    switch (type) {
      case 'anomaly_detection': return <AlertCircle className="h-4 w-4" />;
      case 'trend_prediction': return <TrendingUp className="h-4 w-4" />;
      case 'conversion_prediction': return <Target className="h-4 w-4" />;
      case 'user_segmentation': return <BarChart3 className="h-4 w-4" />;
      case 'recommendation': return <Lightbulb className="h-4 w-4" />;
      default: return <Brain className="h-4 w-4" />;
    }
  };

  const formatModelType = (type: string) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'unhealthy': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span>Loading model performance data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* System Health Overview */}
      {healthStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              System Health Status
            </CardTitle>
            <CardDescription>
              Overall AI system health and service status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className={`text-2xl font-bold ${getHealthStatusColor(healthStatus.status)}`}>
                  {healthStatus.status.toUpperCase()}
                </div>
                <p className="text-sm text-muted-foreground">Overall Status</p>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold">{healthStatus.models_loaded}</div>
                <p className="text-sm text-muted-foreground">Models Loaded</p>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {Object.values(healthStatus.services).filter(s => s === 'operational').length}
                </div>
                <p className="text-sm text-muted-foreground">Services Online</p>
              </div>
            </div>
            
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-medium">Service Status</h4>
              {Object.entries(healthStatus.services).map(([service, status]) => (
                <div key={service} className="flex items-center justify-between text-sm">
                  <span className="capitalize">{service.replace('_', ' ')}</span>
                  <Badge variant={status === 'operational' ? 'default' : 'destructive'}>
                    {status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Models Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {models.map((model) => (
          <Card 
            key={model.model_id}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedModel === model.model_id ? 'ring-2 ring-primary' : ''
            }`}
            onClick={() => setSelectedModel(model.model_id)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  {getModelTypeIcon(model.model_type)}
                  {formatModelType(model.model_type)}
                </CardTitle>
                <div className="flex items-center space-x-1">
                  {getStatusIcon(model.status)}
                </div>
              </div>
              <CardDescription className="text-xs">
                Version {model.version}
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Status:</span>
                  <Badge variant={getStatusColor(model.status)}>
                    {model.status.toUpperCase()}
                  </Badge>
                </div>
                
                {model.accuracy && (
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-muted-foreground">Accuracy:</span>
                      <span className="text-sm font-medium">
                        {Math.round(model.accuracy * 100)}%
                      </span>
                    </div>
                    <Progress value={model.accuracy * 100} className="h-2" />
                  </div>
                )}
                
                <div className="flex justify-between items-center text-xs text-muted-foreground">
                  <div className="flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>Updated:</span>
                  </div>
                  <span>{new Date(model.last_updated).toLocaleDateString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Detailed Model Information */}
      {selectedModel && (() => {
        const model = models.find(m => m.model_id === selectedModel);
        if (!model) return null;
        
        return (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getModelTypeIcon(model.model_type)}
                {formatModelType(model.model_type)} - Detailed Information
              </CardTitle>
              <CardDescription>
                Model ID: {model.model_id}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Model Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Type:</span>
                      <span className="font-medium">{formatModelType(model.model_type)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Version:</span>
                      <span className="font-medium">{model.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status:</span>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(model.status)}
                        <span className="font-medium">{model.status}</span>
                      </div>
                    </div>
                    {model.accuracy && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Accuracy:</span>
                        <span className="font-medium">{Math.round(model.accuracy * 100)}%</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Created:</span>
                      <span className="font-medium">
                        {new Date(model.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Last Updated:</span>
                      <span className="font-medium">
                        {new Date(model.last_updated).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-3">Features</h4>
                  {model.feature_names && model.feature_names.length > 0 ? (
                    <div className="space-y-1">
                      {model.feature_names.map((feature, index) => (
                        <div key={index} className="flex items-center space-x-2 text-sm">
                          <div className="w-1.5 h-1.5 rounded-full bg-current flex-shrink-0" />
                          <span className="capitalize">{feature.replace('_', ' ')}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No feature information available</p>
                  )}
                </div>
              </div>
              
              {/* Model Actions */}
              <div className="mt-6 flex space-x-2">
                <Button variant="outline" size="sm" disabled>
                  Retrain Model
                </Button>
                <Button variant="outline" size="sm" disabled>
                  Export Model
                </Button>
                <Button variant="outline" size="sm" disabled>
                  View Logs
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })()}

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Summary</CardTitle>
          <CardDescription>
            Overall model performance across all AI services
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {models.filter(m => m.status === 'ready').length}
              </div>
              <p className="text-sm text-muted-foreground">Ready Models</p>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold">
                {models.length > 0 
                  ? Math.round(models.reduce((acc, m) => acc + (m.accuracy || 0), 0) / models.length * 100)
                  : 0
                }%
              </div>
              <p className="text-sm text-muted-foreground">Avg Accuracy</p>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {models.filter(m => m.status === 'training').length}
              </div>
              <p className="text-sm text-muted-foreground">Training</p>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {models.filter(m => m.status === 'failed').length}
              </div>
              <p className="text-sm text-muted-foreground">Failed</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-2">
          <Button onClick={loadModelData} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        
        <Badge variant="outline" className="text-xs">
          Last updated: {new Date().toLocaleTimeString()}
        </Badge>
      </div>
    </div>
  );
};