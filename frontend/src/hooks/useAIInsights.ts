/**
 * AI Insights Hook
 * Custom hook for managing AI insights functionality
 */

import { useState, useCallback } from 'react';

// Types
interface InsightRequest {
  client_id: string;
  ga4_data: Record<string, any>;
  insight_types?: string[];
  time_range_days?: number;
}

interface NaturalLanguageQueryRequest {
  query: string;
  client_id: string;
  context?: Record<string, any>;
}

interface AnomalyDetectionRequest {
  client_id: string;
  metric_data: Record<string, number[]>;
  metric_name: string;
  threshold?: number;
}

interface TrendPredictionRequest {
  client_id: string;
  historical_data: number[];
  prediction_periods?: number;
  metric_name: string;
}

interface AIInsight {
  insight_id: string;
  type: 'anomaly' | 'trend' | 'prediction' | 'recommendation';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  data: any;
  confidence: number;
  timestamp: string;
  client_id?: string;
  metric_name?: string;
  actionable_recommendations?: string[];
}

interface PredictionResult {
  prediction: any;
  confidence: number;
  model_version: string;
  timestamp: string;
  feature_importance?: Record<string, number>;
}

export const useAIInsights = () => {
  const [isGeneratingInsights, setIsGeneratingInsights] = useState(false);
  const [isProcessingQuery, setIsProcessingQuery] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Base API URL - adjust according to your backend setup
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const makeRequest = useCallback(async (endpoint: string, options: RequestInit = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          // Add authorization header if needed
          // 'Authorization': `Bearer ${token}`,
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error('API request failed:', err);
      throw err;
    }
  }, [API_BASE_URL]);

  const generateInsights = useCallback(async (request: InsightRequest): Promise<AIInsight[]> => {
    setIsGeneratingInsights(true);
    setError(null);

    try {
      const response = await makeRequest('/ai-insights/generate', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate insights';
      setError(errorMessage);
      throw err;
    } finally {
      setIsGeneratingInsights(false);
    }
  }, [makeRequest]);

  const processNaturalLanguageQuery = useCallback(async (request: NaturalLanguageQueryRequest) => {
    setIsProcessingQuery(true);
    setError(null);

    try {
      const response = await makeRequest('/ai-insights/query', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process query';
      setError(errorMessage);
      throw err;
    } finally {
      setIsProcessingQuery(false);
    }
  }, [makeRequest]);

  const detectAnomalies = useCallback(async (request: AnomalyDetectionRequest): Promise<PredictionResult> => {
    setError(null);

    try {
      const response = await makeRequest('/ai-insights/anomaly-detection', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to detect anomalies';
      setError(errorMessage);
      throw err;
    }
  }, [makeRequest]);

  const predictTrends = useCallback(async (request: TrendPredictionRequest): Promise<PredictionResult> => {
    setError(null);

    try {
      const response = await makeRequest('/ai-insights/trend-prediction', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to predict trends';
      setError(errorMessage);
      throw err;
    }
  }, [makeRequest]);

  const getDashboardSummary = useCallback(async (clientId: string) => {
    setError(null);

    try {
      const response = await makeRequest(`/ai-insights/dashboard-summary?client_id=${clientId}`);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get dashboard summary';
      setError(errorMessage);
      throw err;
    }
  }, [makeRequest]);

  const getInsightsHistory = useCallback(async (
    clientId: string, 
    days: number = 7, 
    insightType?: string, 
    priority?: string
  ): Promise<AIInsight[]> => {
    setError(null);

    try {
      const params = new URLSearchParams({
        client_id: clientId,
        days: days.toString(),
      });

      if (insightType) params.append('insight_type', insightType);
      if (priority) params.append('priority', priority);

      const response = await makeRequest(`/ai-insights/insights/history?${params}`);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get insights history';
      setError(errorMessage);
      throw err;
    }
  }, [makeRequest]);

  const getModels = useCallback(async (modelType?: string) => {
    setError(null);

    try {
      const params = modelType ? `?model_type=${modelType}` : '';
      const response = await makeRequest(`/ai-insights/models${params}`);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get models';
      setError(errorMessage);
      throw err;
    }
  }, [makeRequest]);

  const getModelInfo = useCallback(async (modelId: string) => {
    setError(null);

    try {
      const response = await makeRequest(`/ai-insights/models/${modelId}`);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get model info';
      setError(errorMessage);
      throw err;
    }
  }, [makeRequest]);

  const trainModel = useCallback(async (request: {
    model_type: string;
    training_data: Record<string, any>;
    hyperparameters?: Record<string, any>;
    client_id?: string;
  }) => {
    setError(null);

    try {
      const response = await makeRequest('/ai-insights/models/train', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to train model';
      setError(errorMessage);
      throw err;
    }
  }, [makeRequest]);

  const checkHealthStatus = useCallback(async () => {
    setError(null);

    try {
      const response = await makeRequest('/ai-insights/health');
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to check health status';
      setError(errorMessage);
      throw err;
    }
  }, [makeRequest]);

  // Clear error function
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    // Data and state
    isGeneratingInsights,
    isProcessingQuery,
    error,

    // Functions
    generateInsights,
    processNaturalLanguageQuery,
    detectAnomalies,
    predictTrends,
    getDashboardSummary,
    getInsightsHistory,
    getModels,
    getModelInfo,
    trainModel,
    checkHealthStatus,
    clearError,
  };
};