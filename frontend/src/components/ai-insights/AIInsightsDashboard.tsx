/**
 * AI Insights Dashboard Component
 * Main dashboard for displaying AI-powered analytics insights
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  Brain, 
  TrendingUp, 
  AlertTriangle, 
  Target, 
  Lightbulb,
  BarChart3,
  Activity,
  Zap,
  RefreshCw,
  MessageSquare
} from 'lucide-react';

import { InsightCard } from './InsightCard';
import { AnomalyDetector } from './AnomalyDetector';
import { TrendPredictor } from './TrendPredictor';
import { NaturalLanguageQuery } from './NaturalLanguageQuery';
import { ModelPerformance } from './ModelPerformance';
import { useAIInsights } from '@/hooks/useAIInsights';

interface DashboardSummary {
  total_insights: number;
  critical_alerts: number;
  anomalies_detected: number;
  predictions_generated: number;
  recommendations_active: number;
  model_accuracy: {
    anomaly_detection: number;
    trend_prediction: number;
    conversion_prediction: number;
  };
  recent_insights: Array<{
    type: string;
    title: string;
    priority: string;
    timestamp: string;
  }>;
  performance_metrics: {
    insights_generated_today: number;
    avg_confidence: number;
    recommendations_implemented: number;
    model_prediction_accuracy: number;
  };
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

interface AIInsightsDashboardProps {
  clientId: string;
  refreshInterval?: number;
}

export const AIInsightsDashboard: React.FC<AIInsightsDashboardProps> = ({
  clientId,
  refreshInterval = 30000 // 30 seconds
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const { 
    generateInsights, 
    getDashboardSummary, 
    isGeneratingInsights,
    error 
  } = useAIInsights();

  // Load dashboard data
  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      
      // Load dashboard summary
      const summary = await getDashboardSummary(clientId);
      setDashboardSummary(summary);
      
      // Generate fresh insights
      const sampleGA4Data = {
        sessions: [100, 120, 95, 110, 105, 130, 140, 155, 142, 168],
        users: [80, 95, 75, 88, 85, 105, 115, 125, 118, 135],
        bounce_rate: [0.65, 0.62, 0.68, 0.60, 0.63, 0.58, 0.55, 0.52, 0.54, 0.48],
        conversion_rate: [0.025, 0.030, 0.022, 0.028, 0.026, 0.032, 0.035, 0.038, 0.034, 0.041],
        page_views: [250, 280, 220, 265, 245, 310, 330, 365, 340, 395],
        avg_session_duration: [120, 135, 110, 140, 125, 150, 165, 170, 160, 180]
      };
      
      const generatedInsights = await generateInsights({
        client_id: clientId,
        ga4_data: sampleGA4Data,
        time_range_days: 30
      });
      
      setInsights(generatedInsights);
      setLastRefresh(new Date());
      
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    loadDashboardData();
    
    const interval = setInterval(loadDashboardData, refreshInterval);
    return () => clearInterval(interval);
  }, [clientId, refreshInterval]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'secondary';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'anomaly': return <AlertTriangle className="h-4 w-4" />;
      case 'trend': return <TrendingUp className="h-4 w-4" />;
      case 'prediction': return <Target className="h-4 w-4" />;
      case 'recommendation': return <Lightbulb className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span>Loading AI insights...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="h-8 w-8" />
            AI Insights Dashboard
          </h1>
          <p className="text-muted-foreground">
            AI-powered analytics insights and predictions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </Badge>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={loadDashboardData}
            disabled={isGeneratingInsights}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isGeneratingInsights ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      {dashboardSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Insights</CardTitle>
              <Brain className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardSummary.total_insights}</div>
              <p className="text-xs text-muted-foreground">
                +{dashboardSummary.performance_metrics.insights_generated_today} today
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">
                {dashboardSummary.critical_alerts}
              </div>
              <p className="text-xs text-muted-foreground">
                Require immediate attention
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Anomalies Detected</CardTitle>
              <Zap className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardSummary.anomalies_detected}</div>
              <p className="text-xs text-muted-foreground">
                In the last 24 hours
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
              <BarChart3 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Math.round(dashboardSummary.performance_metrics.avg_confidence * 100)}%
              </div>
              <Progress 
                value={dashboardSummary.performance_metrics.avg_confidence * 100} 
                className="mt-2" 
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          <TabsTrigger value="chat">AI Chat</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Insights */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Insights</CardTitle>
                <CardDescription>
                  Latest AI-generated insights and recommendations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {insights.slice(0, 5).map((insight) => (
                    <div key={insight.insight_id} className="flex items-start space-x-3 p-3 border rounded-lg">
                      <div className="flex-shrink-0 mt-1">
                        {getTypeIcon(insight.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium truncate">
                            {insight.title}
                          </p>
                          <Badge variant={getPriorityColor(insight.priority)} className="text-xs">
                            {insight.priority}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {insight.description}
                        </p>
                        <div className="flex items-center mt-2 space-x-2">
                          <Badge variant="outline" className="text-xs">
                            {Math.round(insight.confidence * 100)}% confidence
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(insight.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Model Performance */}
            {dashboardSummary && (
              <Card>
                <CardHeader>
                  <CardTitle>Model Performance</CardTitle>
                  <CardDescription>
                    Current AI model accuracy and performance metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium">Anomaly Detection</span>
                        <span className="text-sm">
                          {Math.round(dashboardSummary.model_accuracy.anomaly_detection * 100)}%
                        </span>
                      </div>
                      <Progress value={dashboardSummary.model_accuracy.anomaly_detection * 100} />
                    </div>
                    
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium">Trend Prediction</span>
                        <span className="text-sm">
                          {Math.round(dashboardSummary.model_accuracy.trend_prediction * 100)}%
                        </span>
                      </div>
                      <Progress value={dashboardSummary.model_accuracy.trend_prediction * 100} />
                    </div>
                    
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium">Conversion Prediction</span>
                        <span className="text-sm">
                          {Math.round(dashboardSummary.model_accuracy.conversion_prediction * 100)}%
                        </span>
                      </div>
                      <Progress value={dashboardSummary.model_accuracy.conversion_prediction * 100} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* All Insights */}
          <Card>
            <CardHeader>
              <CardTitle>All Insights</CardTitle>
              <CardDescription>
                Complete list of AI-generated insights with detailed analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {insights.map((insight) => (
                  <InsightCard key={insight.insight_id} insight={insight} />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Anomalies Tab */}
        <TabsContent value="anomalies">
          <AnomalyDetector clientId={clientId} />
        </TabsContent>

        {/* Predictions Tab */}
        <TabsContent value="predictions">
          <TrendPredictor clientId={clientId} />
        </TabsContent>

        {/* AI Chat Tab */}
        <TabsContent value="chat">
          <NaturalLanguageQuery clientId={clientId} />
        </TabsContent>

        {/* Models Tab */}
        <TabsContent value="models">
          <ModelPerformance />
        </TabsContent>
      </Tabs>
    </div>
  );
};