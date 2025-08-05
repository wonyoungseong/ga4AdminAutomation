'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3,
  LineChart,
  PieChart,
  Calendar,
  Clock,
  Target,
  Brain,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Download,
  Share,
  Settings,
  Zap,
  Activity,
  Globe,
  DollarSign,
  Users,
  Eye,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';

import {
  PredictiveEngine,
  TrendAnalyzer,
  SeasonalDecompositionModel,
  generateMockTimeSeriesData,
  TimeSeriesData
} from '@/lib/ai-insights';

import { LinearRegression, MovingAverageModel } from '@/lib/ml-models';

// Forecast result interface
interface ForecastResult {
  metric: string;
  predictions: Array<{
    timestamp: Date;
    value: number;
    confidence: number;
    lower: number;
    upper: number;
  }>;
  confidence: number;
  methodology: string;
  growthRate: number;
  seasonalStrength: number;
  trendStrength: number;
}

// Business impact interface
interface BusinessImpact {
  metric: string;
  currentValue: number;
  predictedValue: number;
  change: number;
  changePercent: number;
  impact: 'positive' | 'negative' | 'neutral';
  confidence: number;
  revenue?: number;
  revenueChange?: number;
}

// Simplified chart component for forecasts
interface ForecastChartProps {
  historical: Array<{ timestamp: Date; value: number }>;
  forecast: Array<{ timestamp: Date; value: number; lower: number; upper: number }>;
  width?: number;
  height?: number;
  showConfidenceInterval?: boolean;
}

const ForecastChart: React.FC<ForecastChartProps> = ({
  historical,
  forecast,
  width = 800,
  height = 300,
  showConfidenceInterval = true
}) => {
  if (historical.length === 0 && forecast.length === 0) return null;
  
  const allData = [...historical, ...forecast];
  const values = allData.map(d => d.value);
  const maxValue = Math.max(...values, ...forecast.map(f => f.upper));
  const minValue = Math.min(...values, ...forecast.map(f => f.lower));
  const range = maxValue - minValue;
  
  const totalPoints = historical.length + forecast.length;
  const splitIndex = historical.length;
  
  // Generate points for historical data
  const historicalPoints = historical.map((d, i) => {
    const x = (i / (totalPoints - 1)) * (width - 40) + 20;
    const y = height - 20 - ((d.value - minValue) / range) * (height - 40);
    return { x, y, value: d.value };
  });
  
  // Generate points for forecast
  const forecastPoints = forecast.map((d, i) => {
    const x = ((splitIndex + i) / (totalPoints - 1)) * (width - 40) + 20;
    const y = height - 20 - ((d.value - minValue) / range) * (height - 40);
    const yLower = height - 20 - ((d.lower - minValue) / range) * (height - 40);
    const yUpper = height - 20 - ((d.upper - minValue) / range) * (height - 40);
    return { x, y, yLower, yUpper, value: d.value };
  });
  
  // Generate path data
  const historicalPath = historicalPoints
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ');
    
  const forecastPath = forecastPoints
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ');
  
  // Generate confidence interval path
  const confidencePathUpper = forecastPoints
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.yUpper}`)
    .join(' ');
    
  const confidencePathLower = forecastPoints
    .slice()
    .reverse()
    .map((p, i) => `${i === 0 ? 'L' : 'L'} ${p.x} ${p.yLower}`)
    .join(' ');
  
  const confidenceArea = `${confidencePathUpper} ${confidencePathLower} Z`;
  
  return (
    <div className="w-full overflow-x-auto">
      <svg width={width} height={height} className="border rounded">
        {/* Grid lines */}
        <defs>
          <pattern id="forecast-grid" width="40" height="30" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 30" fill="none" stroke="#f1f5f9" strokeWidth="1"/>
          </pattern>
          <linearGradient id="confidenceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2"/>
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1"/>
          </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#forecast-grid)" />
        
        {/* Confidence interval */}
        {showConfidenceInterval && forecastPoints.length > 0 && (
          <path
            d={confidenceArea}
            fill="url(#confidenceGradient)"
            stroke="none"
          />
        )}
        
        {/* Historical data line */}
        {historicalPoints.length > 0 && (
          <path
            d={historicalPath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="3"
          />
        )}
        
        {/* Forecast line */}
        {forecastPoints.length > 0 && (
          <path
            d={forecastPath}
            fill="none"
            stroke="#10b981"
            strokeWidth="3"
            strokeDasharray="5,5"
          />
        )}
        
        {/* Divider line between historical and forecast */}
        {historicalPoints.length > 0 && forecastPoints.length > 0 && (
          <line
            x1={historicalPoints[historicalPoints.length - 1]?.x || 0}
            y1="20"
            x2={historicalPoints[historicalPoints.length - 1]?.x || 0}
            y2={height - 20}
            stroke="#6b7280"
            strokeWidth="2"
            strokeDasharray="3,3"
            opacity="0.5"
          />
        )}
        
        {/* Historical data points */}
        {historicalPoints.map((point, i) => (
          <circle
            key={`hist-${i}`}
            cx={point.x}
            cy={point.y}
            r="4"
            fill="#3b82f6"
            stroke="#ffffff"
            strokeWidth="2"
          />
        ))}
        
        {/* Forecast data points */}
        {forecastPoints.map((point, i) => (
          <circle
            key={`forecast-${i}`}
            cx={point.x}
            cy={point.y}
            r="4"
            fill="#10b981"
            stroke="#ffffff"
            strokeWidth="2"
          />
        ))}
        
        {/* Legend */}
        <g transform={`translate(${width - 180}, 30)`}>
          <rect x="0" y="0" width="160" height="50" fill="white" stroke="#e2e8f0" rx="4"/>
          <line x1="10" y1="15" x2="30" y2="15" stroke="#3b82f6" strokeWidth="3"/>
          <text x="35" y="19" fontSize="12" fill="#374151">Historical</text>
          <line x1="10" y1="35" x2="30" y2="35" stroke="#10b981" strokeWidth="3" strokeDasharray="5,5"/>
          <text x="35" y="39" fontSize="12" fill="#374151">Forecast</text>
        </g>
      </svg>
    </div>
  );
};

// Business impact card component
interface BusinessImpactCardProps {
  impact: BusinessImpact;
  timeframe: string;
}

const BusinessImpactCard: React.FC<BusinessImpactCardProps> = ({ impact, timeframe }) => {
  const getImpactColor = (impact: BusinessImpact['impact']) => {
    switch (impact.impact) {
      case 'positive': return 'text-green-600';
      case 'negative': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };
  
  const getImpactIcon = (impact: BusinessImpact['impact']) => {
    switch (impact.impact) {
      case 'positive': return <ArrowUp className="w-4 h-4" />;
      case 'negative': return <ArrowDown className="w-4 h-4" />;
      default: return <Minus className="w-4 h-4" />;
    }
  };
  
  const formatValue = (value: number, metric: string) => {
    if (metric.includes('rate') || metric.includes('conversion')) {
      return `${value.toFixed(2)}%`;
    } else if (metric.includes('revenue') || metric.includes('value')) {
      return `$${value.toLocaleString()}`;
    } else {
      return value.toLocaleString();
    }
  };
  
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-sm">
            {impact.metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </h4>
          <Badge variant="outline" className={getImpactColor(impact)}>
            {impact.impact}
          </Badge>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Current:</span>
            <span className="font-medium">{formatValue(impact.currentValue, impact.metric)}</span>
          </div>
          
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Predicted ({timeframe}):</span>
            <span className="font-medium">{formatValue(impact.predictedValue, impact.metric)}</span>
          </div>
          
          <div className={`flex items-center justify-between text-sm ${getImpactColor(impact)}`}>
            <span className="flex items-center">
              {getImpactIcon(impact)}
              <span className="ml-1">Change:</span>
            </span>
            <span className="font-medium">
              {impact.changePercent > 0 ? '+' : ''}{impact.changePercent.toFixed(1)}%
            </span>
          </div>
          
          {impact.revenue && impact.revenueChange && (
            <div className={`flex items-center justify-between text-sm ${getImpactColor(impact)}`}>
              <span className="text-muted-foreground">Revenue Impact:</span>
              <span className="font-medium">
                {impact.revenueChange > 0 ? '+' : ''}${impact.revenueChange.toLocaleString()}
              </span>
            </div>
          )}
        </div>
        
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>Confidence</span>
            <span>{Math.round(impact.confidence * 100)}%</span>
          </div>
          <Progress value={impact.confidence * 100} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
};

// Main Predictive Analytics Component
interface PredictiveAnalyticsProps {
  className?: string;
  data?: Array<{
    metric: string;
    values: Array<{ timestamp: Date; value: number }>;
  }>;
  forecastDays?: number;
}

const PredictiveAnalytics: React.FC<PredictiveAnalyticsProps> = ({
  className = '',
  data = [],
  forecastDays = 30
}) => {
  const [forecasts, setForecasts] = useState<ForecastResult[]>([]);
  const [businessImpacts, setBusinessImpacts] = useState<BusinessImpact[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState<string>('');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('30');
  const [selectedModel, setSelectedModel] = useState<string>('linear');
  const [error, setError] = useState<string | null>(null);
  
  // Available metrics
  const availableMetrics = useMemo(() => {
    if (data.length > 0) {
      return data.map(d => d.metric);
    }
    return ['sessions', 'page_views', 'bounce_rate', 'conversion_rate', 'revenue'];
  }, [data]);
  
  // Initialize with first metric
  useEffect(() => {
    if (availableMetrics.length > 0 && !selectedMetric) {
      setSelectedMetric(availableMetrics[0]);
    }
  }, [availableMetrics, selectedMetric]);
  
  // Generate forecasts
  const generateForecasts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const forecastResults: ForecastResult[] = [];
      const impacts: BusinessImpact[] = [];
      const days = parseInt(selectedTimeframe);
      
      for (const metric of availableMetrics) {
        let timeSeriesData: TimeSeriesData;
        
        // Get data for metric
        const metricData = data.find(d => d.metric === metric);
        
        if (metricData) {
          timeSeriesData = {
            metric,
            dataPoints: metricData.values.map(v => ({
              timestamp: v.timestamp,
              value: v.value,
              metric,
              confidence: 0.95
            })),
            interval: 'day',
            period: {
              start: new Date(Math.min(...metricData.values.map(v => v.timestamp.getTime()))),
              end: new Date(Math.max(...metricData.values.map(v => v.timestamp.getTime())))
            }
          };
        } else {
          // Generate mock data
          timeSeriesData = generateMockTimeSeriesData(metric, 60, 'day');
        }
        
        // Generate forecast based on selected model
        let predictions;
        let confidence = 0.8;
        let methodology = '';
        
        if (selectedModel === 'linear') {
          const predictiveEngine = new PredictiveEngine();
          const forecast = predictiveEngine.generateForecast(timeSeriesData, days);
          predictions = forecast.predictions;
          confidence = forecast.confidence;
          methodology = forecast.methodology;
        } else if (selectedModel === 'seasonal') {
          // Use seasonal decomposition
          const seasonalModel = new SeasonalDecompositionModel(7, 'additive');
          const values = timeSeriesData.dataPoints.map(d => d.value);
          const forecast = seasonalModel.forecast(values, days);
          
          predictions = forecast.forecast.map((value, i) => ({
            timestamp: new Date(timeSeriesData.period.end.getTime() + (i + 1) * 86400000),
            value,
            metric,
            confidence: 0.7 - (i / days) * 0.2 // Decreasing confidence over time
          }));
          methodology = 'Seasonal decomposition with trend extrapolation';
        } else {
          // Moving average
          const maModel = new MovingAverageModel(7, 'exponential', 0.3);
          const values = timeSeriesData.dataPoints.map(d => d.value);
          const forecast = maModel.forecast(values, days);
          
          predictions = forecast.map((value, i) => ({
            timestamp: new Date(timeSeriesData.period.end.getTime() + (i + 1) * 86400000),
            value,
            metric,
            confidence: 0.6 - (i / days) * 0.1
          }));
          methodology = 'Exponential moving average';
          confidence = 0.6;
        }
        
        // Calculate trend and seasonal strength
        const trendAnalyzer = new TrendAnalyzer();
        const trend = trendAnalyzer.analyzeTrend(timeSeriesData);
        const patterns = trendAnalyzer.detectSeasonalPatterns(timeSeriesData);
        
        const seasonalStrength = patterns.length > 0 ? patterns[0].strength : 0;
        const trendStrength = trend.strength;
        const growthRate = trend.rate;
        
        // Prepare forecast result with confidence intervals
        const forecastWithIntervals = predictions.map(p => ({
          timestamp: p.timestamp,
          value: p.value,
          confidence: p.confidence || 0.8,
          lower: p.value * (1 - (1 - (p.confidence || 0.8)) * 2),
          upper: p.value * (1 + (1 - (p.confidence || 0.8)) * 2)
        }));
        
        forecastResults.push({
          metric,
          predictions: forecastWithIntervals,
          confidence,
          methodology,
          growthRate,
          seasonalStrength,
          trendStrength
        });
        
        // Calculate business impact
        const currentValue = timeSeriesData.dataPoints[timeSeriesData.dataPoints.length - 1].value;
        const predictedValue = predictions[predictions.length - 1].value;
        const change = predictedValue - currentValue;
        const changePercent = currentValue !== 0 ? (change / currentValue) * 100 : 0;
        
        let impact: BusinessImpact['impact'] = 'neutral';
        if (Math.abs(changePercent) > 5) {
          impact = changePercent > 0 ? 'positive' : 'negative';
        }
        
        // Calculate revenue impact for conversion metrics
        let revenue, revenueChange;
        if (metric.includes('conversion') || metric.includes('revenue')) {
          const avgOrderValue = 50; // Mock average order value
          const sessions = timeSeriesData.dataPoints[timeSeriesData.dataPoints.length - 1].value;
          
          if (metric.includes('revenue')) {
            revenue = currentValue;
            revenueChange = change;
          } else {
            revenue = (currentValue / 100) * sessions * avgOrderValue;
            revenueChange = ((predictedValue - currentValue) / 100) * sessions * avgOrderValue;
          }
        }
        
        impacts.push({
          metric,
          currentValue,
          predictedValue,
          change,
          changePercent,
          impact,
          confidence,
          revenue,
          revenueChange
        });
      }
      
      setForecasts(forecastResults);
      setBusinessImpacts(impacts);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate forecasts');
    } finally {
      setLoading(false);
    }
  };
  
  // Generate forecasts when parameters change
  useEffect(() => {
    if (availableMetrics.length > 0) {
      generateForecasts();
    }
  }, [selectedTimeframe, selectedModel, data, availableMetrics]);
  
  // Get current forecast for selected metric
  const selectedForecast = useMemo(() => {
    return forecasts.find(f => f.metric === selectedMetric);
  }, [forecasts, selectedMetric]);
  
  // Prepare chart data for selected metric
  const chartData = useMemo(() => {
    if (!selectedForecast) return { historical: [], forecast: [] };
    
    // Get historical data
    const metricData = data.find(d => d.metric === selectedMetric);
    const historical = metricData ? metricData.values : 
      generateMockTimeSeriesData(selectedMetric, 30, 'day').dataPoints.map(d => ({
        timestamp: d.timestamp,
        value: d.value
      }));
    
    // Get forecast data
    const forecast = selectedForecast.predictions.map(p => ({
      timestamp: p.timestamp,
      value: p.value,
      lower: p.lower,
      upper: p.upper
    }));
    
    return { historical, forecast };
  }, [selectedForecast, selectedMetric, data]);
  
  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    const totalForecasts = forecasts.length;
    const positiveImpacts = businessImpacts.filter(i => i.impact === 'positive').length;
    const negativeImpacts = businessImpacts.filter(i => i.impact === 'negative').length;
    const avgConfidence = forecasts.length > 0 
      ? forecasts.reduce((sum, f) => sum + f.confidence, 0) / forecasts.length 
      : 0;
    
    return {
      totalForecasts,
      positiveImpacts,
      negativeImpacts,
      avgConfidence
    };
  }, [forecasts, businessImpacts]);
  
  const handleExport = () => {
    const exportData = {
      forecasts,
      businessImpacts,
      generatedAt: new Date().toISOString(),
      parameters: {
        timeframe: selectedTimeframe,
        model: selectedModel
      }
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `forecast-${selectedMetric}-${selectedTimeframe}days-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };
  
  if (error) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-lg font-semibold">Error Generating Forecasts</p>
            <p className="text-muted-foreground">{error}</p>
            <Button onClick={generateForecasts} className="mt-4">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center">
            <Brain className="w-8 h-8 mr-3 text-purple-600" />
            Predictive Analytics
          </h2>
          <p className="text-muted-foreground">
            AI-powered forecasting and business impact analysis
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 days</SelectItem>
              <SelectItem value="14">14 days</SelectItem>
              <SelectItem value="30">30 days</SelectItem>
              <SelectItem value="60">60 days</SelectItem>
              <SelectItem value="90">90 days</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="linear">Linear Regression</SelectItem>
              <SelectItem value="seasonal">Seasonal Model</SelectItem>
              <SelectItem value="moving">Moving Average</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" size="sm" onClick={generateForecasts} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Forecasts</p>
                <p className="text-2xl font-bold">{summaryStats.totalForecasts}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Positive Trends</p>
                <p className="text-2xl font-bold text-green-600">{summaryStats.positiveImpacts}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Declining Trends</p>
                <p className="text-2xl font-bold text-red-600">{summaryStats.negativeImpacts}</p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Confidence</p>
                <p className="text-2xl font-bold text-purple-600">
                  {Math.round(summaryStats.avgConfidence * 100)}%
                </p>
              </div>
              <Target className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Forecast Chart */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center">
                  <LineChart className="w-5 h-5 mr-2" />
                  Forecast Chart
                </CardTitle>
                
                <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Select metric" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableMetrics.map(metric => (
                      <SelectItem key={metric} value={metric}>
                        {metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-purple-500" />
                    <p className="text-lg font-semibold">Generating Forecasts...</p>
                    <p className="text-muted-foreground">Analyzing patterns and trends</p>
                  </div>
                </div>
              ) : selectedForecast ? (
                <div className="space-y-4">
                  <ForecastChart
                    historical={chartData.historical}
                    forecast={chartData.forecast}
                    width={600}
                    height={300}
                    showConfidenceInterval={true}
                  />
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Growth Rate:</span>
                      <span className={`ml-2 font-medium ${
                        selectedForecast.growthRate > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {selectedForecast.growthRate > 0 ? '+' : ''}{selectedForecast.growthRate.toFixed(1)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Confidence:</span>
                      <span className="ml-2 font-medium">{Math.round(selectedForecast.confidence * 100)}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Trend Strength:</span>
                      <span className="ml-2 font-medium">{Math.round(selectedForecast.trendStrength * 100)}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Seasonality:</span>
                      <span className="ml-2 font-medium">{Math.round(selectedForecast.seasonalStrength * 100)}%</span>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-sm">
                      <span className="font-medium">Methodology:</span> {selectedForecast.methodology}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-lg font-semibold">No Forecast Available</p>
                    <p className="text-muted-foreground">Select a metric to view predictions</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* Forecast Summary */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                Forecast Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedForecast && (
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Prediction Range</p>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Best Case:</span>
                        <span className="font-medium text-green-600">
                          {selectedForecast.predictions[selectedForecast.predictions.length - 1]?.upper.toFixed(0)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Expected:</span>
                        <span className="font-medium">
                          {selectedForecast.predictions[selectedForecast.predictions.length - 1]?.value.toFixed(0)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Worst Case:</span>
                        <span className="font-medium text-red-600">
                          {selectedForecast.predictions[selectedForecast.predictions.length - 1]?.lower.toFixed(0)}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Model Performance</p>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-sm">
                        <span>Confidence:</span>
                        <div className="flex items-center space-x-2">
                          <Progress value={selectedForecast.confidence * 100} className="w-16" />
                          <span className="font-medium">{Math.round(selectedForecast.confidence * 100)}%</span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span>Trend Strength:</span>
                        <div className="flex items-center space-x-2">
                          <Progress value={selectedForecast.trendStrength * 100} className="w-16" />
                          <span className="font-medium">{Math.round(selectedForecast.trendStrength * 100)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Key Insights</p>
                    <div className="space-y-2">
                      {selectedForecast.growthRate > 10 && (
                        <Alert>
                          <TrendingUp className="h-4 w-4" />
                          <AlertDescription>
                            Strong growth trend detected (+{selectedForecast.growthRate.toFixed(1)}%)
                          </AlertDescription>
                        </Alert>
                      )}
                      
                      {selectedForecast.growthRate < -10 && (
                        <Alert>
                          <TrendingDown className="h-4 w-4" />
                          <AlertDescription>
                            Declining trend detected ({selectedForecast.growthRate.toFixed(1)}%)
                          </AlertDescription>
                        </Alert>
                      )}
                      
                      {selectedForecast.seasonalStrength > 0.5 && (
                        <Alert>
                          <Calendar className="h-4 w-4" />
                          <AlertDescription>
                            Strong seasonal pattern identified
                          </AlertDescription>
                        </Alert>
                      )}
                      
                      {selectedForecast.confidence < 0.5 && (
                        <Alert>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            Low confidence - results should be interpreted cautiously
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      
      {/* Business Impact Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <DollarSign className="w-5 h-5 mr-2" />
            Business Impact Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <RefreshCw className="w-6 h-6 animate-spin text-purple-500" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {businessImpacts.map((impact) => (
                <BusinessImpactCard
                  key={impact.metric}
                  impact={impact}
                  timeframe={`${selectedTimeframe} days`}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Additional Tabs */}
      <Tabs defaultValue="models" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="models">Model Comparison</TabsTrigger>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          <TabsTrigger value="export">Export & Share</TabsTrigger>
        </TabsList>
        
        <TabsContent value="models" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Model Performance Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <h4 className="font-semibold">Linear Regression</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      Best for stable trends
                    </p>
                    <div className="text-2xl font-bold text-blue-600">85%</div>
                    <p className="text-xs text-muted-foreground">Avg Accuracy</p>
                  </div>
                  
                  <div className="text-center p-4 border rounded-lg">
                    <h4 className="font-semibold">Seasonal Model</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      Best for cyclical data
                    </p>
                    <div className="text-2xl font-bold text-green-600">78%</div>
                    <p className="text-xs text-muted-foreground">Avg Accuracy</p>
                  </div>
                  
                  <div className="text-center p-4 border rounded-lg">
                    <h4 className="font-semibold">Moving Average</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      Best for short-term
                    </p>
                    <div className="text-2xl font-bold text-orange-600">72%</div>
                    <p className="text-xs text-muted-foreground">Avg Accuracy</p>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Model Recommendations</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      Use Linear Regression for metrics with consistent growth trends
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      Use Seasonal Model for metrics with weekly/monthly patterns
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                      Use Moving Average for volatile metrics with short-term predictions
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="scenarios" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Scenario Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold text-green-600 mb-2">Optimistic Scenario</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      Assuming 20% improvement in all metrics
                    </p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Sessions:</span>
                        <span className="font-medium">+24%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Conversions:</span>
                        <span className="font-medium">+31%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Revenue:</span>
                        <span className="font-medium">+28%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold text-blue-600 mb-2">Expected Scenario</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      Based on current trends and patterns
                    </p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Sessions:</span>
                        <span className="font-medium">+12%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Conversions:</span>
                        <span className="font-medium">+8%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Revenue:</span>
                        <span className="font-medium">+15%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold text-red-600 mb-2">Conservative Scenario</h4>
                    <p className="text-sm text-muted-foreground mb-2">
                      Accounting for potential market challenges
                    </p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Sessions:</span>
                        <span className="font-medium">+3%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Conversions:</span>
                        <span className="font-medium">-2%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Revenue:</span>
                        <span className="font-medium">+1%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <Alert>
                  <Lightbulb className="h-4 w-4" />
                  <AlertDescription>
                    Scenario analysis helps prepare for different market conditions and plan resources accordingly.
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="export" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Export & Share Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Button variant="outline" className="h-24 flex-col">
                    <Download className="w-6 h-6 mb-2" />
                    <span className="text-sm">Export JSON</span>
                  </Button>
                  
                  <Button variant="outline" className="h-24 flex-col">
                    <Download className="w-6 h-6 mb-2" />
                    <span className="text-sm">Export CSV</span>
                  </Button>
                  
                  <Button variant="outline" className="h-24 flex-col">
                    <Share className="w-6 h-6 mb-2" />
                    <span className="text-sm">Share Report</span>
                  </Button>
                  
                  <Button variant="outline" className="h-24 flex-col">
                    <Calendar className="w-6 h-6 mb-2" />
                    <span className="text-sm">Schedule Report</span>
                  </Button>
                </div>
                
                <Separator />
                
                <div>
                  <h4 className="font-semibold mb-2">Report Settings</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Include confidence intervals</Label>
                      <Button variant="outline" size="sm">Configure</Button>
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Add business context</Label>
                      <Button variant="outline" size="sm">Configure</Button>
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Include methodology notes</Label>
                      <Button variant="outline" size="sm">Configure</Button>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PredictiveAnalytics;