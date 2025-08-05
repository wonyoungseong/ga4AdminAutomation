'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Brain, 
  Zap, 
  BarChart3, 
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  RefreshCw,
  Settings,
  Download,
  Info
} from 'lucide-react';

import AIInsights from '@/components/analytics/AIInsights';
import AnomalyDetection from '@/components/analytics/AnomalyDetection';
import PredictiveAnalytics from '@/components/analytics/PredictiveAnalytics';
import { generateMockTimeSeriesData } from '@/lib/ai-insights';

// Mock data generator for demo
const generateMockAnalyticsData = () => {
  const metrics = ['sessions', 'page_views', 'bounce_rate', 'conversion_rate', 'revenue'];
  
  return metrics.map(metric => {
    const timeSeriesData = generateMockTimeSeriesData(metric, 60, 'day');
    return {
      metric,
      values: timeSeriesData.dataPoints.map(d => ({
        timestamp: d.timestamp,
        value: d.value
      }))
    };
  });
};

export default function AnalyticsAIPage() {
  const [mockData, setMockData] = useState<Array<{
    metric: string;
    values: Array<{ timestamp: Date; value: number }>;
  }>>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('overview');

  // Generate mock data on component mount
  useEffect(() => {
    const generateData = async () => {
      setLoading(true);
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      const data = generateMockAnalyticsData();
      setMockData(data);
      setLoading(false);
    };

    generateData();
  }, []);

  const refreshData = async () => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    const data = generateMockAnalyticsData();
    setMockData(data);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            AI-Powered Analytics Dashboard
          </h1>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
            Enterprise-grade AI insights system with anomaly detection, predictive analytics, 
            and intelligent recommendations for GA4 data analysis.
          </p>
          
          <div className="flex justify-center space-x-4">
            <Badge variant="secondary" className="px-3 py-1">
              <Brain className="w-4 h-4 mr-1" />
              Machine Learning
            </Badge>
            <Badge variant="secondary" className="px-3 py-1">
              <Zap className="w-4 h-4 mr-1" />
              Real-time Analysis
            </Badge>
            <Badge variant="secondary" className="px-3 py-1">
              <TrendingUp className="w-4 h-4 mr-1" />
              Predictive Models
            </Badge>
          </div>
        </div>

        {/* System Status */}
        <Card className="border-2 border-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">AI System Status: Active</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  Last updated: {new Date().toLocaleTimeString()}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" onClick={refreshData} disabled={loading}>
                  <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh Data
                </Button>
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Configure
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export All
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Feature Overview */}
        {selectedTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedTab('insights')}>
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <Brain className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">AI Insights</CardTitle>
                    <p className="text-sm text-muted-foreground">Smart recommendations</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Get intelligent insights from your analytics data with automated pattern recognition and actionable recommendations.
                </p>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <Lightbulb className="w-4 h-4 mr-2 text-yellow-500" />
                    Automated insight generation
                  </div>
                  <div className="flex items-center text-sm">
                    <TrendingUp className="w-4 h-4 mr-2 text-green-500" />
                    Trend analysis and correlation
                  </div>
                  <div className="flex items-center text-sm">
                    <BarChart3 className="w-4 h-4 mr-2 text-blue-500" />
                    Cross-metric relationships
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedTab('anomalies')}>
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-orange-100 rounded-lg">
                    <Zap className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Anomaly Detection</CardTitle>
                    <p className="text-sm text-muted-foreground">Real-time monitoring</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Detect unusual patterns and anomalies in your data with advanced statistical algorithms and machine learning.
                </p>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <AlertTriangle className="w-4 h-4 mr-2 text-red-500" />
                    Statistical anomaly detection
                  </div>
                  <div className="flex items-center text-sm">
                    <Brain className="w-4 h-4 mr-2 text-purple-500" />
                    Root cause analysis
                  </div>
                  <div className="flex items-center text-sm">
                    <Zap className="w-4 h-4 mr-2 text-orange-500" />
                    Real-time alerts
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedTab('predictions')}>
              <CardHeader className="pb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-3 bg-purple-100 rounded-lg">
                    <BarChart3 className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Predictive Analytics</CardTitle>
                    <p className="text-sm text-muted-foreground">Future forecasting</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Forecast future trends and business outcomes using advanced machine learning models and statistical analysis.
                </p>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <TrendingUp className="w-4 h-4 mr-2 text-green-500" />
                    Multi-model forecasting
                  </div>
                  <div className="flex items-center text-sm">
                    <BarChart3 className="w-4 h-4 mr-2 text-blue-500" />
                    Business impact analysis
                  </div>
                  <div className="flex items-center text-sm">
                    <Brain className="w-4 h-4 mr-2 text-purple-500" />
                    Confidence intervals
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="insights">AI Insights</TabsTrigger>
            <TabsTrigger value="anomalies">Anomaly Detection</TabsTrigger>
            <TabsTrigger value="predictions">Predictive Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Overview content is handled above */}
          </TabsContent>

          <TabsContent value="insights" className="space-y-6">
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                AI Insights analyzes your data to identify patterns, trends, and actionable recommendations. 
                The system uses multiple algorithms including anomaly detection, correlation analysis, and pattern recognition.
              </AlertDescription>
            </Alert>
            
            <AIInsights 
              data={mockData}
              refreshInterval={30000}
              maxInsights={20}
              enableRealTime={true}
            />
          </TabsContent>

          <TabsContent value="anomalies" className="space-y-6">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Anomaly Detection uses statistical methods and machine learning to identify unusual patterns in your data. 
                Configure sensitivity levels and detection parameters to match your monitoring needs.
              </AlertDescription>
            </Alert>
            
            <AnomalyDetection 
              data={mockData}
              onAnomalyAlert={(anomaly) => {
                console.log('Anomaly alert:', anomaly);
                // Handle anomaly alerts (notifications, etc.)
              }}
            />
          </TabsContent>

          <TabsContent value="predictions" className="space-y-6">
            <Alert>
              <BarChart3 className="h-4 w-4" />
              <AlertDescription>
                Predictive Analytics uses advanced machine learning models to forecast future trends and business outcomes. 
                Choose from multiple forecasting models and timeframes to get the most accurate predictions.
              </AlertDescription>
            </Alert>
            
            <PredictiveAnalytics 
              data={mockData}
              forecastDays={30}
            />
          </TabsContent>
        </Tabs>

        {/* Technical Information */}
        <Card className="bg-gradient-to-r from-gray-50 to-gray-100">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Info className="w-5 h-5 mr-2" />
              Technical Implementation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div>
                <h4 className="font-semibold mb-2">Anomaly Detection</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• Z-score based detection</li>
                  <li>• Isolation Forest approximation</li>
                  <li>• Seasonal pattern analysis</li>
                  <li>• Configurable sensitivity</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Predictive Models</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• Linear regression</li>
                  <li>• Seasonal decomposition</li>
                  <li>• Moving averages</li>
                  <li>• Confidence intervals</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Pattern Recognition</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• Trend analysis</li>
                  <li>• Correlation detection</li>
                  <li>• Seasonal patterns</li>
                  <li>• Cross-metric relationships</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Performance</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• Client-side processing</li>
                  <li>• Real-time analysis</li>
                  <li>• Efficient algorithms</li>
                  <li>• Optimized for large datasets</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-muted-foreground">
          <p>
            AI-Powered Analytics Dashboard - Built with TypeScript, React, and advanced machine learning algorithms
          </p>
          <p className="mt-1">
            Ready for integration with your GA4 analytics pipeline
          </p>
        </div>
      </div>
    </div>
  );
}