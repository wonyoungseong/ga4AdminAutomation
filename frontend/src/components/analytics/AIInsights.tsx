'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Brain, 
  Search, 
  Filter,
  Eye,
  EyeOff,
  Clock,
  Target,
  Lightbulb,
  BarChart3,
  Activity,
  CheckCircle,
  XCircle,
  RefreshCw,
  Settings,
  Download,
  Share
} from 'lucide-react';

import {
  AIInsight,
  Anomaly,
  TrendAnalysis,
  PredictiveInsight,
  PatternInsight,
  InsightRecommendation,
  createInsightEngine,
  generateMockTimeSeriesData
} from '@/lib/ai-insights';

// Severity color mapping
const severityColors = {
  critical: 'destructive',
  warning: 'default',
  info: 'secondary',
  positive: 'default'
} as const;

const severityIcons = {
  critical: AlertTriangle,
  warning: AlertTriangle,
  info: Brain,
  positive: TrendingUp
};

// Interface for component props
interface AIInsightsProps {
  className?: string;
  data?: Array<{
    metric: string;
    values: Array<{ timestamp: Date; value: number }>;
  }>;
  refreshInterval?: number;
  maxInsights?: number;
  enableRealTime?: boolean;
}

// Individual insight card component
interface InsightCardProps {
  insight: AIInsight;
  onDismiss: (id: string) => void;
  onAction: (id: string, action: string) => void;
  onExpand: (id: string) => void;
  isExpanded: boolean;
}

const InsightCard: React.FC<InsightCardProps> = ({ 
  insight, 
  onDismiss, 
  onAction, 
  onExpand,
  isExpanded 
}) => {
  const SeverityIcon = severityIcons[insight.severity];
  
  const formatConfidence = (confidence: number) => {
    return `${Math.round(confidence * 100)}%`;
  };
  
  const formatTimestamp = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(timestamp);
  };
  
  const renderInsightDetails = () => {
    switch (insight.type) {
      case 'anomaly':
        const anomaly = insight.data as Anomaly;
        return (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Value:</span>
                <span className="ml-2 font-medium">{anomaly.value.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Expected:</span>
                <span className="ml-2 font-medium">{anomaly.expectedValue.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Deviation:</span>
                <span className={`ml-2 font-medium ${anomaly.deviation > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {anomaly.deviation > 0 ? '+' : ''}{anomaly.deviation.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Type:</span>
                <span className="ml-2 font-medium capitalize">{anomaly.type.replace('_', ' ')}</span>
              </div>
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground mb-2">Potential Causes:</p>
              <ul className="text-sm space-y-1">
                {anomaly.potentialCauses.map((cause, idx) => (
                  <li key={idx} className="flex items-center">
                    <span className="w-1 h-1 bg-current rounded-full mr-2"></span>
                    {cause}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-1">Impact Assessment</p>
              <p className="text-sm text-muted-foreground">{anomaly.impactAssessment}</p>
            </div>
          </div>
        );
        
      case 'trend':
        const trend = insight.data as TrendAnalysis;
        return (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Direction:</span>
                <span className="ml-2 font-medium capitalize">{trend.direction}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Strength:</span>
                <span className="ml-2 font-medium">{Math.round(trend.strength * 100)}%</span>
              </div>
              <div>
                <span className="text-muted-foreground">Rate:</span>
                <span className={`ml-2 font-medium ${trend.rate > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {trend.rate > 0 ? '+' : ''}{trend.rate.toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">R²:</span>
                <span className="ml-2 font-medium">{trend.R2.toFixed(3)}</span>
              </div>
            </div>
            
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm">
                <span className="font-medium">Period:</span> {formatTimestamp(trend.startDate)} - {formatTimestamp(trend.endDate)}
              </p>
            </div>
          </div>
        );
        
      case 'prediction':
        const prediction = insight.data as PredictiveInsight;
        return (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Predicted Value:</span>
                <span className="ml-2 font-medium">{prediction.prediction.value.toFixed(2)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Timeframe:</span>
                <span className="ml-2 font-medium">{prediction.timeframe}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Method:</span>
                <span className="ml-2 font-medium">{prediction.methodology}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Impact:</span>
                <span className="ml-2 font-medium">{prediction.businessImpact}</span>
              </div>
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground mb-2">Confidence Range:</p>
              <div className="flex items-center space-x-2 text-sm">
                <span>{prediction.prediction.range.lower.toFixed(2)}</span>
                <Progress value={insight.confidence * 100} className="flex-1" />
                <span>{prediction.prediction.range.upper.toFixed(2)}</span>
              </div>
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground mb-2">Key Factors:</p>
              <div className="flex flex-wrap gap-1">
                {prediction.factors.map((factor, idx) => (
                  <Badge key={idx} variant="outline">{factor}</Badge>
                ))}
              </div>
            </div>
          </div>
        );
        
      case 'pattern':
        const pattern = insight.data as PatternInsight;
        return (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Pattern:</span>
                <span className="ml-2 font-medium capitalize">{pattern.pattern}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Strength:</span>
                <span className="ml-2 font-medium">{Math.round(pattern.strength * 100)}%</span>
              </div>
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground mb-2">Implications:</p>
              <ul className="text-sm space-y-1">
                {pattern.implications.map((implication, idx) => (
                  <li key={idx} className="flex items-center">
                    <Lightbulb className="w-3 h-3 mr-2 text-yellow-500" />
                    {implication}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        );
        
      case 'recommendation':
        const recommendation = insight.data as InsightRecommendation;
        return (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Priority:</span>
                <Badge variant={recommendation.priority === 'critical' ? 'destructive' : 'default'} className="ml-2">
                  {recommendation.priority}
                </Badge>
              </div>
              <div>
                <span className="text-muted-foreground">Category:</span>
                <span className="ml-2 font-medium capitalize">{recommendation.category}</span>
              </div>
            </div>
            
            <div>
              <p className="text-sm text-muted-foreground mb-2">Recommended Actions:</p>
              <div className="space-y-2">
                {recommendation.actions.map((action, idx) => (
                  <div key={idx} className="p-2 border rounded-lg">
                    <p className="font-medium text-sm">{action.title}</p>
                    <p className="text-xs text-muted-foreground">{action.description}</p>
                    <div className="flex space-x-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        Effort: {action.effort}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        Impact: {action.impact}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-1">Potential Impact</p>
              <p className="text-sm text-muted-foreground">{recommendation.potentialImpact}</p>
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <Card className={`transition-all duration-200 ${insight.dismissed ? 'opacity-50' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <div className={`p-2 rounded-lg ${
              insight.severity === 'critical' ? 'bg-red-100 text-red-600' :
              insight.severity === 'warning' ? 'bg-yellow-100 text-yellow-600' :
              insight.severity === 'positive' ? 'bg-green-100 text-green-600' :
              'bg-blue-100 text-blue-600'
            }`}>
              <SeverityIcon className="w-4 h-4" />
            </div>
            
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="font-semibold text-sm">{insight.title}</h3>
                <Badge variant={severityColors[insight.severity]} className="text-xs">
                  {insight.severity}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{insight.description}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onExpand(insight.id)}
              className="p-1"
            >
              {isExpanded ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDismiss(insight.id)}
              className="p-1"
            >
              <XCircle className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center space-x-4 text-xs text-muted-foreground">
            <div className="flex items-center space-x-1">
              <Clock className="w-3 h-3" />
              <span>{formatTimestamp(insight.createdAt)}</span>
            </div>
            
            <div className="flex items-center space-x-1">
              <Target className="w-3 h-3" />
              <span>Confidence: {formatConfidence(insight.confidence)}</span>
            </div>
            
            <div className="flex items-center space-x-1">
              <BarChart3 className="w-3 h-3" />
              <span>{insight.metrics.join(', ')}</span>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-1">
            {insight.tags.map((tag, idx) => (
              <Badge key={idx} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="pt-0">
          <Separator className="mb-4" />
          {renderInsightDetails()}
          
          {insight.actions && insight.actions.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-sm font-medium mb-2">Actions</p>
              <div className="flex flex-wrap gap-2">
                {insight.actions.map((action, idx) => (
                  <Button
                    key={idx}
                    variant={action.primary ? "default" : "outline"}
                    size="sm"
                    onClick={() => onAction(insight.id, action.action)}
                  >
                    {action.label}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
};

// Main AI Insights Dashboard Component
const AIInsights: React.FC<AIInsightsProps> = ({
  className = '',
  data = [],
  refreshInterval = 30000,
  maxInsights = 50,
  enableRealTime = true
}) => {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [expandedInsight, setExpandedInsight] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('all');
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  
  // Initialize insight engine
  const insightEngine = useMemo(() => createInsightEngine({
    sensitivity: 'medium',
    lookbackPeriod: 30,
    seasonalityWindow: 14,
    minimumDeviation: 2.0
  }), []);
  
  // Generate insights from data
  const generateInsights = async () => {
    try {
      setLoading(true);
      setError(null);
      
      let timeSeriesData;
      
      if (data.length > 0) {
        // Use provided data
        timeSeriesData = data.map(item => ({
          metric: item.metric,
          dataPoints: item.values.map(v => ({
            timestamp: v.timestamp,
            value: v.value,
            metric: item.metric,
            confidence: 0.95
          })),
          interval: 'day' as const,
          period: {
            start: new Date(Math.min(...item.values.map(v => v.timestamp.getTime()))),
            end: new Date(Math.max(...item.values.map(v => v.timestamp.getTime())))
          }
        }));
      } else {
        // Generate mock data for demo
        timeSeriesData = [
          generateMockTimeSeriesData('sessions', 30, 'day'),
          generateMockTimeSeriesData('page_views', 30, 'day'),
          generateMockTimeSeriesData('bounce_rate', 30, 'day'),
          generateMockTimeSeriesData('conversion_rate', 30, 'day'),
          generateMockTimeSeriesData('revenue', 30, 'day')
        ];
      }
      
      const newInsights = await insightEngine.generateInsights(timeSeriesData);
      
      // Limit insights
      const limitedInsights = newInsights.slice(0, maxInsights);
      
      setInsights(limitedInsights);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate insights');
    } finally {
      setLoading(false);
    }
  };
  
  // Initialize and set up refresh interval
  useEffect(() => {
    generateInsights();
    
    if (enableRealTime && refreshInterval > 0) {
      const interval = setInterval(generateInsights, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [data, refreshInterval, enableRealTime, maxInsights]);
  
  // Filter insights based on search and filters
  const filteredInsights = useMemo(() => {
    return insights.filter(insight => {
      const matchesSearch = searchTerm === '' || 
        insight.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        insight.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        insight.metrics.some(metric => metric.toLowerCase().includes(searchTerm.toLowerCase()));
      
      const matchesSeverity = filterSeverity === 'all' || insight.severity === filterSeverity;
      const matchesType = filterType === 'all' || insight.type === filterType;
      const matchesTab = selectedTab === 'all' || 
        (selectedTab === 'active' && !insight.dismissed) ||
        (selectedTab === 'dismissed' && insight.dismissed) ||
        insight.severity === selectedTab;
      
      return matchesSearch && matchesSeverity && matchesType && matchesTab;
    });
  }, [insights, searchTerm, filterSeverity, filterType, selectedTab]);
  
  // Group insights by type for tabs
  const insightsByType = useMemo(() => {
    const active = insights.filter(i => !i.dismissed);
    const dismissed = insights.filter(i => i.dismissed);
    const critical = insights.filter(i => i.severity === 'critical');
    const warnings = insights.filter(i => i.severity === 'warning');
    const positive = insights.filter(i => i.severity === 'positive');
    
    return { active, dismissed, critical, warnings, positive };
  }, [insights]);
  
  // Handle insight actions
  const handleDismissInsight = (id: string) => {
    setInsights(prev => prev.map(insight => 
      insight.id === id ? { ...insight, dismissed: true } : insight
    ));
  };
  
  const handleInsightAction = (id: string, action: string) => {
    console.log(`Action ${action} triggered for insight ${id}`);
    // Implement action handlers based on action type
    switch (action) {
      case 'investigate':
        // Open investigation view
        break;
      case 'view_forecast':
        // Open forecast view
        break;
      case 'set_alert':
        // Set up alert
        break;
      default:
        break;
    }
  };
  
  const handleExpandInsight = (id: string) => {
    setExpandedInsight(prev => prev === id ? null : id);
  };
  
  const handleExport = () => {
    const dataStr = JSON.stringify(filteredInsights, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ai-insights-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };
  
  if (error) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-lg font-semibold">Error Loading Insights</p>
            <p className="text-muted-foreground">{error}</p>
            <Button onClick={generateInsights} className="mt-4">
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
            <Brain className="w-8 h-8 mr-3 text-blue-600" />
            AI Insights
          </h2>
          <p className="text-muted-foreground">
            AI-powered analytics insights and recommendations
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={generateInsights} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>
      
      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Insights</p>
                <p className="text-2xl font-bold">{insights.length}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Critical</p>
                <p className="text-2xl font-bold text-red-600">{insightsByType.critical.length}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active</p>
                <p className="text-2xl font-bold text-blue-600">{insightsByType.active.length}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Last Updated</p>
                <p className="text-sm font-medium">
                  {new Intl.DateTimeFormat('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                  }).format(lastRefresh)}
                </p>
              </div>
              <Clock className="w-8 h-8 text-gray-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Filters and Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search insights, metrics, or descriptions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              
              <Select value={filterSeverity} onValueChange={setFilterSeverity}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severity</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                  <SelectItem value="info">Info</SelectItem>
                  <SelectItem value="positive">Positive</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="anomaly">Anomaly</SelectItem>
                  <SelectItem value="trend">Trend</SelectItem>
                  <SelectItem value="prediction">Prediction</SelectItem>
                  <SelectItem value="pattern">Pattern</SelectItem>
                  <SelectItem value="recommendation">Recommendation</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Insights Tabs and List */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="all">All ({insights.length})</TabsTrigger>
          <TabsTrigger value="active">Active ({insightsByType.active.length})</TabsTrigger>
          <TabsTrigger value="critical">Critical ({insightsByType.critical.length})</TabsTrigger>
          <TabsTrigger value="warning">Warnings ({insightsByType.warnings.length})</TabsTrigger>
          <TabsTrigger value="positive">Positive ({insightsByType.positive.length})</TabsTrigger>
          <TabsTrigger value="dismissed">Dismissed ({insightsByType.dismissed.length})</TabsTrigger>
        </TabsList>
        
        <TabsContent value={selectedTab} className="mt-6">
          {loading ? (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
                  <p className="text-lg font-semibold">Generating AI Insights...</p>
                  <p className="text-muted-foreground">Analyzing patterns and anomalies</p>
                </div>
              </CardContent>
            </Card>
          ) : filteredInsights.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center">
                  <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-semibold">No Insights Found</p>
                  <p className="text-muted-foreground">
                    {searchTerm || filterSeverity !== 'all' || filterType !== 'all' 
                      ? 'Try adjusting your filters or search terms'
                      : 'No insights available for the current data'
                    }
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="space-y-4">
                {filteredInsights.map((insight) => (
                  <InsightCard
                    key={insight.id}
                    insight={insight}
                    onDismiss={handleDismissInsight}
                    onAction={handleInsightAction}
                    onExpand={handleExpandInsight}
                    isExpanded={expandedInsight === insight.id}
                  />
                ))}
              </div>
            </ScrollArea>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AIInsights;