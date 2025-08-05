/**
 * Trend Predictor Component
 * Predictive analytics for GA4 metrics trends
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  TrendingDown,
  Minus,
  Target, 
  RefreshCw,
  BarChart3,
  AlertCircle,
  Calendar
} from 'lucide-react';

import { useAIInsights } from '@/hooks/useAIInsights';

interface TrendPredictorProps {
  clientId: string;
}

interface TrendPrediction {
  predictions: number[];
  confidence: number;
  trend_direction: 'increasing' | 'decreasing' | 'stable';
  trend_strength: number;
  model_version: string;
}

export const TrendPredictor: React.FC<TrendPredictorProps> = ({ clientId }) => {
  const [selectedMetric, setSelectedMetric] = useState('sessions');
  const [predictionPeriod, setPredictionPeriod] = useState(7);
  const [predictions, setPredictions] = useState<Record<string, TrendPrediction | null>>({});
  const [isPredicting, setIsPredicting] = useState(false);

  const { predictTrends, error } = useAIInsights();

  const metrics = [
    { value: 'sessions', label: 'Sessions', icon: <BarChart3 className="h-4 w-4" /> },
    { value: 'users', label: 'Users', icon: <BarChart3 className="h-4 w-4" /> },
    { value: 'page_views', label: 'Page Views', icon: <BarChart3 className="h-4 w-4" /> },
    { value: 'bounce_rate', label: 'Bounce Rate', icon: <TrendingDown className="h-4 w-4" /> },
    { value: 'conversion_rate', label: 'Conversion Rate', icon: <TrendingUp className="h-4 w-4" /> },
    { value: 'revenue', label: 'Revenue', icon: <TrendingUp className="h-4 w-4" /> }
  ];

  const periods = [
    { value: 3, label: '3 Days' },
    { value: 7, label: '1 Week' },
    { value: 14, label: '2 Weeks' },
    { value: 30, label: '1 Month' }
  ];

  // Sample historical data - in production this would come from GA4 API
  const getHistoricalData = (metric: string): number[] => {
    const baseData = {
      sessions: [100, 120, 95, 110, 105, 130, 140, 155, 142, 168, 185, 195, 175, 160, 145, 170, 180, 190, 185, 200],
      users: [80, 95, 75, 88, 85, 105, 115, 125, 118, 135, 150, 155, 140, 130, 115, 135, 145, 150, 145, 160],
      page_views: [250, 280, 220, 265, 245, 310, 330, 365, 340, 395, 420, 445, 400, 375, 350, 390, 410, 430, 415, 450],
      bounce_rate: [0.65, 0.62, 0.68, 0.60, 0.63, 0.58, 0.55, 0.52, 0.54, 0.48, 0.45, 0.42, 0.46, 0.50, 0.48, 0.44, 0.41, 0.39, 0.42, 0.38],
      conversion_rate: [0.025, 0.030, 0.022, 0.028, 0.026, 0.032, 0.035, 0.038, 0.034, 0.041, 0.044, 0.046, 0.042, 0.039, 0.041, 0.045, 0.048, 0.051, 0.047, 0.053],
      revenue: [1500, 1800, 1200, 1600, 1400, 1900, 2100, 2300, 2000, 2500, 2700, 2900, 2600, 2400, 2200, 2600, 2800, 3000, 2900, 3200]
    };
    return baseData[metric] || [];
  };

  const runTrendPrediction = async (metric: string = selectedMetric) => {
    setIsPredicting(true);
    
    try {
      const historicalData = getHistoricalData(metric);
      
      const result = await predictTrends({
        client_id: clientId,
        historical_data: historicalData,
        prediction_periods: predictionPeriod,
        metric_name: metric
      });

      // Create prediction result
      const predictionResult: TrendPrediction = {
        predictions: Array.isArray(result.prediction) ? result.prediction : [result.prediction],
        confidence: result.confidence,
        trend_direction: historicalData[historicalData.length - 1] > historicalData[historicalData.length - 7] ? 'increasing' : 'decreasing',
        trend_strength: result.confidence,
        model_version: result.model_version
      };

      setPredictions(prev => ({
        ...prev,
        [metric]: predictionResult
      }));

    } catch (error) {
      console.error('Error predicting trends:', error);
    } finally {
      setIsPredicting(false);
    }
  };

  // Auto-run prediction when parameters change
  useEffect(() => {
    runTrendPrediction();
  }, [selectedMetric, predictionPeriod]);

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing': return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'decreasing': return <TrendingDown className="h-4 w-4 text-red-500" />;
      default: return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'increasing': return 'text-green-600';
      case 'decreasing': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const formatMetricValue = (metric: string, value: number) => {
    switch (metric) {
      case 'bounce_rate':
      case 'conversion_rate':
        return `${(value * 100).toFixed(2)}%`;
      case 'revenue':
        return `$${value.toLocaleString()}`;
      default:
        return Math.round(value).toLocaleString();
    }
  };

  const calculatePercentageChange = (current: number, predicted: number) => {
    const change = ((predicted - current) / current) * 100;
    return change.toFixed(1);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Trend Prediction & Forecasting
          </CardTitle>
          <CardDescription>
            Predict future trends based on historical GA4 data patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 mb-6">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Select Metric</label>
              <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {metrics.map((metric) => (
                    <SelectItem key={metric.value} value={metric.value}>
                      <div className="flex items-center space-x-2">
                        {metric.icon}
                        <span>{metric.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Prediction Period</label>
              <Select value={predictionPeriod.toString()} onValueChange={(value) => setPredictionPeriod(parseInt(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {periods.map((period) => (
                    <SelectItem key={period.value} value={period.value.toString()}>
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4" />
                        <span>{period.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex-shrink-0 pt-6">
              <Button 
                onClick={() => runTrendPrediction()} 
                disabled={isPredicting}
                variant="outline"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isPredicting ? 'animate-spin' : ''}`} />
                Predict
              </Button>
            </div>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Prediction Results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Prediction */}
        {predictions[selectedMetric] && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{metrics.find(m => m.value === selectedMetric)?.label} Forecast</span>
                {getTrendIcon(predictions[selectedMetric]!.trend_direction)}
              </CardTitle>
              <CardDescription>
                {periods.find(p => p.value === predictionPeriod)?.label} prediction
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-3xl font-bold">
                  {formatMetricValue(
                    selectedMetric, 
                    predictions[selectedMetric]!.predictions[predictions[selectedMetric]!.predictions.length - 1]
                  )}
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Trend Direction:</span>
                    <div className={`flex items-center space-x-1 ${getTrendColor(predictions[selectedMetric]!.trend_direction)}`}>
                      {getTrendIcon(predictions[selectedMetric]!.trend_direction)}
                      <span className="text-sm font-medium capitalize">
                        {predictions[selectedMetric]!.trend_direction}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Confidence:</span>
                    <div className="flex items-center space-x-2">
                      <Progress value={predictions[selectedMetric]!.confidence * 100} className="w-16 h-2" />
                      <span className="text-sm font-medium">
                        {Math.round(predictions[selectedMetric]!.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Trend Strength:</span>
                    <Badge variant="outline">
                      {Math.round(predictions[selectedMetric]!.trend_strength * 100)}%
                    </Badge>
                  </div>
                  
                  {/* Percentage change calculation */}
                  {(() => {
                    const historicalData = getHistoricalData(selectedMetric);
                    const currentValue = historicalData[historicalData.length - 1];
                    const predictedValue = predictions[selectedMetric]!.predictions[predictions[selectedMetric]!.predictions.length - 1];
                    const change = calculatePercentageChange(currentValue, predictedValue);
                    const isPositive = parseFloat(change) > 0;
                    
                    return (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Expected Change:</span>
                        <div className={`flex items-center space-x-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                          {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                          <span className="text-sm font-medium">{change}%</span>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* All Metrics Overview */}
        <Card>
          <CardHeader>
            <CardTitle>All Metrics Forecast</CardTitle>
            <CardDescription>
              Quick overview of all metric predictions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {metrics.map((metric) => {
                const prediction = predictions[metric.value];
                const historicalData = getHistoricalData(metric.value);
                const isSelected = selectedMetric === metric.value;
                
                if (!prediction) {
                  return (
                    <div 
                      key={metric.value}
                      className={`flex items-center justify-between p-2 rounded cursor-pointer hover:bg-muted ${
                        isSelected ? 'bg-muted' : ''
                      }`}
                      onClick={() => setSelectedMetric(metric.value)}
                    >
                      <div className="flex items-center space-x-2">
                        {metric.icon}
                        <span className="text-sm">{metric.label}</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        Click to predict
                      </Badge>
                    </div>
                  );
                }
                
                const currentValue = historicalData[historicalData.length - 1];
                const predictedValue = prediction.predictions[prediction.predictions.length - 1];
                const change = calculatePercentageChange(currentValue, predictedValue);
                const isPositive = parseFloat(change) > 0;
                
                return (
                  <div 
                    key={metric.value}
                    className={`flex items-center justify-between p-2 rounded cursor-pointer hover:bg-muted ${
                      isSelected ? 'bg-muted' : ''
                    }`}
                    onClick={() => setSelectedMetric(metric.value)}
                  >
                    <div className="flex items-center space-x-2">
                      {metric.icon}
                      <span className="text-sm">{metric.label}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`flex items-center space-x-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        <span className="text-xs font-medium">{change}%</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {Math.round(prediction.confidence * 100)}%
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis */}
      {predictions[selectedMetric] && (
        <Card>
          <CardHeader>
            <CardTitle>Detailed Forecast Analysis</CardTitle>
            <CardDescription>
              Day-by-day predictions and insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Prediction Breakdown</h4>
                <div className="space-y-2">
                  {predictions[selectedMetric]!.predictions.slice(0, 7).map((value, index) => (
                    <div key={index} className="flex justify-between items-center text-sm">
                      <span>Day {index + 1}:</span>
                      <span className="font-medium">
                        {formatMetricValue(selectedMetric, value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Key Insights</h4>
                <ul className="space-y-1 text-sm">
                  <li className="flex items-start space-x-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                    <span>
                      Model confidence: {Math.round(predictions[selectedMetric]!.confidence * 100)}%
                    </span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                    <span>
                      Trend strength: {Math.round(predictions[selectedMetric]!.trend_strength * 100)}%
                    </span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                    <span>
                      Pattern: {predictions[selectedMetric]!.trend_direction} trend detected
                    </span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                    <span>
                      Model: {predictions[selectedMetric]!.model_version}
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};