/**
 * Anomaly Detector Component
 * Real-time anomaly detection for GA4 metrics
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  AlertTriangle, 
  Activity, 
  TrendingUp, 
  RefreshCw,
  BarChart3,
  AlertCircle
} from 'lucide-react';

import { useAIInsights } from '@/hooks/useAIInsights';

interface AnomalyDetectorProps {
  clientId: string;
}

interface AnomalyResult {
  is_anomaly: boolean;
  anomaly_score: number;
  expected_range: [number, number];
  actual_value: number;
  severity: string;
  description: string;
}

export const AnomalyDetector: React.FC<AnomalyDetectorProps> = ({ clientId }) => {
  const [selectedMetric, setSelectedMetric] = useState('sessions');
  const [anomalyResults, setAnomalyResults] = useState<Record<string, AnomalyResult | null>>({});
  const [isDetecting, setIsDetecting] = useState(false);
  const [threshold, setThreshold] = useState(2.5);

  const { detectAnomalies, error } = useAIInsights();

  const metrics = [
    { value: 'sessions', label: 'Sessions', icon: <Activity className="h-4 w-4" /> },
    { value: 'users', label: 'Users', icon: <Activity className="h-4 w-4" /> },
    { value: 'page_views', label: 'Page Views', icon: <BarChart3 className="h-4 w-4" /> },
    { value: 'bounce_rate', label: 'Bounce Rate', icon: <TrendingUp className="h-4 w-4" /> },
    { value: 'conversion_rate', label: 'Conversion Rate', icon: <TrendingUp className="h-4 w-4" /> },
    { value: 'avg_session_duration', label: 'Avg Session Duration', icon: <Activity className="h-4 w-4" /> }
  ];

  // Sample data - in production this would come from GA4 API
  const getSampleData = (metric: string) => {
    const baseData = {
      sessions: [100, 120, 95, 110, 105, 130, 140, 155, 142, 168, 185, 195, 175, 160, 145],
      users: [80, 95, 75, 88, 85, 105, 115, 125, 118, 135, 150, 155, 140, 130, 115],
      page_views: [250, 280, 220, 265, 245, 310, 330, 365, 340, 395, 420, 445, 400, 375, 350],
      bounce_rate: [0.65, 0.62, 0.68, 0.60, 0.63, 0.58, 0.55, 0.52, 0.54, 0.48, 0.45, 0.42, 0.46, 0.50, 0.85], // Anomaly in last value
      conversion_rate: [0.025, 0.030, 0.022, 0.028, 0.026, 0.032, 0.035, 0.038, 0.034, 0.041, 0.044, 0.046, 0.042, 0.039, 0.015], // Anomaly in last value
      avg_session_duration: [120, 135, 110, 140, 125, 150, 165, 170, 160, 180, 185, 190, 175, 165, 45] // Anomaly in last value
    };
    return baseData[metric] || [];
  };

  const runAnomalyDetection = async (metric: string = selectedMetric) => {
    setIsDetecting(true);
    
    try {
      const metricData = getSampleData(metric);
      
      const result = await detectAnomalies({
        client_id: clientId,
        metric_data: { [metric]: metricData },
        metric_name: metric,
        threshold
      });

      // Parse the prediction result
      const anomalyData = result.prediction as {
        is_anomaly: boolean;
        anomaly_score: number;
      };

      // Create anomaly result
      const anomalyResult: AnomalyResult = {
        is_anomaly: anomalyData.is_anomaly,
        anomaly_score: anomalyData.anomaly_score,
        expected_range: [0, 0], // Would be calculated in production
        actual_value: metricData[metricData.length - 1],
        severity: anomalyData.anomaly_score > 3 ? 'high' : anomalyData.anomaly_score > 2.5 ? 'medium' : 'low',
        description: `Anomaly score: ${anomalyData.anomaly_score.toFixed(2)}`
      };

      setAnomalyResults(prev => ({
        ...prev,
        [metric]: anomalyResult
      }));

    } catch (error) {
      console.error('Error detecting anomalies:', error);
    } finally {
      setIsDetecting(false);
    }
  };

  // Auto-run detection when metric changes
  useEffect(() => {
    runAnomalyDetection();
  }, [selectedMetric, threshold]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'secondary';
    }
  };

  const formatMetricValue = (metric: string, value: number) => {
    switch (metric) {
      case 'bounce_rate':
      case 'conversion_rate':
        return `${(value * 100).toFixed(2)}%`;
      case 'avg_session_duration':
        return `${Math.round(value)}s`;
      default:
        return value.toLocaleString();
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Real-time Anomaly Detection
          </CardTitle>
          <CardDescription>
            Monitor your GA4 metrics for unusual patterns and unexpected changes
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
              <label className="text-sm font-medium mb-2 block">Sensitivity Threshold</label>
              <Select value={threshold.toString()} onValueChange={(value) => setThreshold(parseFloat(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1.5">Low (1.5σ)</SelectItem>
                  <SelectItem value="2.0">Medium (2.0σ)</SelectItem>
                  <SelectItem value="2.5">High (2.5σ)</SelectItem>
                  <SelectItem value="3.0">Very High (3.0σ)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex-shrink-0 pt-6">
              <Button 
                onClick={() => runAnomalyDetection()} 
                disabled={isDetecting}
                variant="outline"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isDetecting ? 'animate-spin' : ''}`} />
                Detect
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

      {/* Results for All Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((metric) => {
          const result = anomalyResults[metric.value];
          const isSelected = selectedMetric === metric.value;
          const sampleData = getSampleData(metric.value);
          
          return (
            <Card 
              key={metric.value} 
              className={`cursor-pointer transition-all ${
                isSelected ? 'ring-2 ring-primary' : ''
              } ${result?.is_anomaly ? 'border-destructive' : ''}`}
              onClick={() => setSelectedMetric(metric.value)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    {metric.icon}
                    {metric.label}
                  </CardTitle>
                  {result && (
                    <Badge 
                      variant={result.is_anomaly ? 'destructive' : 'secondary'}
                      className="text-xs"
                    >
                      {result.is_anomaly ? 'Anomaly' : 'Normal'}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              
              <CardContent>
                {result ? (
                  <div className="space-y-3">
                    <div className="text-2xl font-bold">
                      {formatMetricValue(metric.value, result.actual_value)}
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Anomaly Score:</span>
                        <span className="font-medium">{result.anomaly_score.toFixed(2)}</span>
                      </div>
                      
                      <Progress 
                        value={Math.min(result.anomaly_score / 5 * 100, 100)} 
                        className={`h-2 ${result.is_anomaly ? 'bg-destructive/20' : ''}`}
                      />
                      
                      <div className="text-xs text-muted-foreground">
                        Threshold: {threshold}σ
                      </div>
                    </div>
                    
                    {result.is_anomaly && (
                      <Alert variant="destructive" className="mt-3">
                        <AlertTriangle className="h-3 w-3" />
                        <AlertDescription className="text-xs">
                          {result.description}
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-24 text-muted-foreground">
                    <div className="text-center">
                      <Activity className="h-6 w-6 mx-auto mb-2" />
                      <div className="text-sm">Click to analyze</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Detailed Analysis */}
      {anomalyResults[selectedMetric] && (
        <Card>
          <CardHeader>
            <CardTitle>Detailed Analysis: {metrics.find(m => m.value === selectedMetric)?.label}</CardTitle>
            <CardDescription>
              In-depth anomaly analysis with recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Statistical Analysis</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Current Value:</span>
                    <span className="font-medium">
                      {formatMetricValue(selectedMetric, anomalyResults[selectedMetric]!.actual_value)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Anomaly Score:</span>
                    <span className="font-medium">
                      {anomalyResults[selectedMetric]!.anomaly_score.toFixed(2)}σ
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Severity:</span>
                    <Badge variant={getSeverityColor(anomalyResults[selectedMetric]!.severity)}>
                      {anomalyResults[selectedMetric]!.severity.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Recommended Actions</h4>
                <ul className="space-y-1 text-sm">
                  {anomalyResults[selectedMetric]?.is_anomaly ? (
                    <>
                      <li className="flex items-start space-x-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                        <span>Investigate potential causes immediately</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                        <span>Check for technical issues or outages</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                        <span>Review recent changes or campaigns</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                        <span>Monitor closely for continued patterns</span>
                      </li>
                    </>
                  ) : (
                    <>
                      <li className="flex items-start space-x-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                        <span>Continue regular monitoring</span>
                      </li>
                      <li className="flex items-start space-x-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                        <span>Maintain current optimization strategies</span>
                      </li>
                    </>
                  )}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};