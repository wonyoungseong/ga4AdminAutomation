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
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Activity,
  Settings,
  Calendar,
  Clock,
  Target,
  Zap,
  AlertCircle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Download,
  Bell,
  BellOff,
  Eye,
  BarChart3,
  LineChart,
  PieChart,
  Filter
} from 'lucide-react';

import {
  Anomaly,
  AnomalyDetector,
  AnomalyDetectionConfig,
  TimeSeriesData,
  generateMockTimeSeriesData
} from '@/lib/ai-insights';

// Chart component (simplified - you can replace with your preferred charting library)
interface SimpleLineChartProps {
  data: Array<{ timestamp: Date; value: number; isAnomaly?: boolean }>;
  width?: number;
  height?: number;
  showAnomalies?: boolean;
}

const SimpleLineChart: React.FC<SimpleLineChartProps> = ({ 
  data, 
  width = 800, 
  height = 200,
  showAnomalies = true 
}) => {
  if (data.length === 0) return null;
  
  const values = data.map(d => d.value);
  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  const range = maxValue - minValue;
  
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * (width - 40) + 20;
    const y = height - 20 - ((d.value - minValue) / range) * (height - 40);
    return { x, y, isAnomaly: d.isAnomaly };
  });
  
  const pathData = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
    .join(' ');
  
  return (
    <div className="w-full overflow-x-auto">
      <svg width={width} height={height} className="border rounded">
        {/* Grid lines */}
        <defs>
          <pattern id="grid" width="40" height="20" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 20" fill="none" stroke="#e2e8f0" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        
        {/* Main line */}
        <path
          d={pathData}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
        />
        
        {/* Data points */}
        {points.map((point, i) => (
          <circle
            key={i}
            cx={point.x}
            cy={point.y}
            r={point.isAnomaly ? 6 : 3}
            fill={point.isAnomaly ? "#ef4444" : "#3b82f6"}
            stroke={point.isAnomaly ? "#dc2626" : "#2563eb"}
            strokeWidth={point.isAnomaly ? 2 : 1}
          />
        ))}
        
        {/* Anomaly highlights */}
        {showAnomalies && points.map((point, i) => 
          point.isAnomaly ? (
            <circle
              key={`anomaly-${i}`}
              cx={point.x}
              cy={point.y}
              r="10"
              fill="none"
              stroke="#ef4444"
              strokeWidth="2"
              strokeDasharray="2,2"
              opacity="0.7"
            />
          ) : null
        )}
      </svg>
    </div>
  );
};

// Anomaly timeline component
interface AnomalyTimelineProps {
  anomalies: Anomaly[];
  onAnomalySelect: (anomaly: Anomaly) => void;
  selectedAnomaly: Anomaly | null;
}

const AnomalyTimeline: React.FC<AnomalyTimelineProps> = ({
  anomalies,
  onAnomalySelect,
  selectedAnomaly
}) => {
  const sortedAnomalies = [...anomalies].sort((a, b) => 
    b.timestamp.getTime() - a.timestamp.getTime()
  );
  
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'warning': return 'border-yellow-500 bg-yellow-50';
      default: return 'border-blue-500 bg-blue-50';
    }
  };
  
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      default: return <Activity className="w-4 h-4 text-blue-600" />;
    }
  };
  
  return (
    <ScrollArea className="h-[400px]">
      <div className="space-y-2">
        {sortedAnomalies.map((anomaly) => (
          <Card
            key={anomaly.id}
            className={`cursor-pointer transition-all duration-200 ${
              selectedAnomaly?.id === anomaly.id 
                ? 'ring-2 ring-blue-500 ' + getSeverityColor(anomaly.severity)
                : getSeverityColor(anomaly.severity)
            }`}
            onClick={() => onAnomalySelect(anomaly)}
          >
            <CardContent className="p-4">
              <div className="flex items-start space-x-3">
                <div className="p-2 rounded-full bg-white">
                  {getSeverityIcon(anomaly.severity)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-sm truncate">
                      {anomaly.metric} {anomaly.type === 'spike' ? 'Spike' : 'Drop'}
                    </h4>
                    <Badge variant={anomaly.severity === 'critical' ? 'destructive' : 'default'}>
                      {anomaly.severity}
                    </Badge>
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-2">
                    {anomaly.description}
                  </p>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Value:</span>
                      <span className="ml-1 font-medium">{anomaly.value.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Expected:</span>
                      <span className="ml-1 font-medium">{anomaly.expectedValue.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Deviation:</span>
                      <span className={`ml-1 font-medium ${
                        anomaly.deviation > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {anomaly.deviation > 0 ? '+' : ''}{anomaly.deviation.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Confidence:</span>
                      <span className="ml-1 font-medium">{Math.round(anomaly.confidence * 100)}%</span>
                    </div>
                  </div>
                  
                  <div className="mt-2 text-xs text-muted-foreground">
                    {new Intl.DateTimeFormat('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    }).format(anomaly.timestamp)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {sortedAnomalies.length === 0 && (
          <Card>
            <CardContent className="flex items-center justify-center h-32">
              <div className="text-center">
                <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-sm font-medium">No Anomalies Detected</p>
                <p className="text-xs text-muted-foreground">All metrics are within normal ranges</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </ScrollArea>
  );
};

// Root cause analysis component
interface RootCauseAnalysisProps {
  anomaly: Anomaly;
}

const RootCauseAnalysis: React.FC<RootCauseAnalysisProps> = ({ anomaly }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center">
          <Target className="w-5 h-5 mr-2" />
          Root Cause Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="font-semibold mb-2">Anomaly Details</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Type:</span>
              <span className="ml-2 font-medium capitalize">{anomaly.type.replace('_', ' ')}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Severity:</span>
              <Badge variant={anomaly.severity === 'critical' ? 'destructive' : 'default'} className="ml-2">
                {anomaly.severity}
              </Badge>
            </div>
            <div>
              <span className="text-muted-foreground">Detected:</span>
              <span className="ml-2 font-medium">
                {new Intl.DateTimeFormat('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                }).format(anomaly.timestamp)}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Confidence:</span>
              <span className="ml-2 font-medium">{Math.round(anomaly.confidence * 100)}%</span>
            </div>
          </div>
        </div>
        
        <Separator />
        
        <div>
          <h4 className="font-semibold mb-2">Potential Causes</h4>
          <div className="space-y-2">
            {anomaly.potentialCauses.map((cause, idx) => (
              <div key={idx} className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-sm">{cause}</span>
              </div>
            ))}
          </div>
        </div>
        
        <Separator />
        
        <div>
          <h4 className="font-semibold mb-2">Impact Assessment</h4>
          <div className="p-3 bg-muted rounded-lg">
            <p className="text-sm">{anomaly.impactAssessment}</p>
          </div>
        </div>
        
        <Separator />
        
        <div>
          <h4 className="font-semibold mb-2">Recommended Actions</h4>
          <div className="space-y-2">
            {anomaly.severity === 'critical' && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Critical anomaly detected. Immediate investigation required.
                </AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Eye className="w-4 h-4 mr-2" />
                Investigate in detail
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Bell className="w-4 h-4 mr-2" />
                Set up alert
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <BarChart3 className="w-4 h-4 mr-2" />
                View related metrics
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Alert configuration component
interface AlertConfigProps {
  config: AnomalyDetectionConfig;
  onConfigChange: (config: AnomalyDetectionConfig) => void;
}

const AlertConfig: React.FC<AlertConfigProps> = ({ config, onConfigChange }) => {
  const [sensitivity, setSensitivity] = useState<number[]>([
    config.sensitivity === 'low' ? 1 : config.sensitivity === 'medium' ? 2 : 3
  ]);
  
  const handleSensitivityChange = (value: number[]) => {
    setSensitivity(value);
    const sensitivityMap = { 1: 'low', 2: 'medium', 3: 'high' } as const;
    onConfigChange({
      ...config,
      sensitivity: sensitivityMap[value[0] as keyof typeof sensitivityMap]
    });
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center">
          <Settings className="w-5 h-5 mr-2" />
          Detection Configuration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <Label className="text-sm font-medium">Sensitivity Level</Label>
          <div className="mt-2">
            <Slider
              value={sensitivity}
              onValueChange={handleSensitivityChange}
              max={3}
              min={1}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Low</span>
              <span>Medium</span>
              <span>High</span>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Higher sensitivity detects more anomalies but may increase false positives
          </p>
        </div>
        
        <div>
          <Label htmlFor="lookback" className="text-sm font-medium">
            Lookback Period (days)
          </Label>
          <Select
            value={config.lookbackPeriod.toString()}
            onValueChange={(value) => onConfigChange({
              ...config,
              lookbackPeriod: parseInt(value)
            })}
          >
            <SelectTrigger id="lookback" className="mt-2">
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
        </div>
        
        <div>
          <Label htmlFor="seasonality" className="text-sm font-medium">
            Seasonality Window (days)
          </Label>
          <Select
            value={config.seasonalityWindow.toString()}
            onValueChange={(value) => onConfigChange({
              ...config,
              seasonalityWindow: parseInt(value)
            })}
          >
            <SelectTrigger id="seasonality" className="mt-2">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 days</SelectItem>
              <SelectItem value="14">14 days</SelectItem>
              <SelectItem value="28">28 days</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="flex items-center space-x-2">
          <Switch
            id="exclude-weekends"
            checked={config.excludeWeekends || false}
            onCheckedChange={(checked) => onConfigChange({
              ...config,
              excludeWeekends: checked
            })}
          />
          <Label htmlFor="exclude-weekends" className="text-sm">
            Exclude weekends from analysis
          </Label>
        </div>
        
        <div>
          <Label className="text-sm font-medium">
            Minimum Deviation (standard deviations)
          </Label>
          <div className="mt-2">
            <Slider
              value={[config.minimumDeviation]}
              onValueChange={(value) => onConfigChange({
                ...config,
                minimumDeviation: value[0]
              })}
              max={5}
              min={1}
              step={0.1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>1.0</span>
              <span>{config.minimumDeviation.toFixed(1)}</span>
              <span>5.0</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Main Anomaly Detection Component
interface AnomalyDetectionProps {
  className?: string;
  data?: Array<{
    metric: string;
    values: Array<{ timestamp: Date; value: number }>;
  }>;
  onAnomalyAlert?: (anomaly: Anomaly) => void;
}

const AnomalyDetection: React.FC<AnomalyDetectionProps> = ({
  className = '',
  data = [],
  onAnomalyAlert
}) => {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState<Array<{ timestamp: Date; value: number; isAnomaly?: boolean }>>([]);
  const [selectedMetric, setSelectedMetric] = useState<string>('');
  const [config, setConfig] = useState<AnomalyDetectionConfig>({
    sensitivity: 'medium',
    lookbackPeriod: 30,
    seasonalityWindow: 14,
    minimumDeviation: 2.0,
    excludeWeekends: false
  });
  
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
  
  // Detect anomalies when metric or config changes
  useEffect(() => {
    if (!selectedMetric) return;
    
    const detectAnomalies = async () => {
      try {
        setLoading(true);
        
        let timeSeriesData: TimeSeriesData;
        
        // Get data for selected metric
        const metricData = data.find(d => d.metric === selectedMetric);
        
        if (metricData) {
          timeSeriesData = {
            metric: selectedMetric,
            dataPoints: metricData.values.map(v => ({
              timestamp: v.timestamp,
              value: v.value,
              metric: selectedMetric,
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
          timeSeriesData = generateMockTimeSeriesData(selectedMetric, 30, 'day');
        }
        
        // Create anomaly detector with current config
        const detector = new AnomalyDetector(config);
        const detectedAnomalies = detector.detectAnomalies(timeSeriesData);
        
        setAnomalies(detectedAnomalies);
        
        // Prepare chart data with anomaly markers
        const anomalyTimestamps = new Set(detectedAnomalies.map(a => a.timestamp.getTime()));
        const chartDataWithAnomalies = timeSeriesData.dataPoints.map(point => ({
          timestamp: point.timestamp,
          value: point.value,
          isAnomaly: anomalyTimestamps.has(point.timestamp.getTime())
        }));
        
        setChartData(chartDataWithAnomalies);
        
        // Alert about critical anomalies
        const criticalAnomalies = detectedAnomalies.filter(a => a.severity === 'critical');
        criticalAnomalies.forEach(anomaly => {
          onAnomalyAlert?.(anomaly);
        });
        
        // Auto-select first anomaly if none selected
        if (!selectedAnomaly && detectedAnomalies.length > 0) {
          setSelectedAnomaly(detectedAnomalies[0]);
        }
        
      } catch (error) {
        console.error('Error detecting anomalies:', error);
      } finally {
        setLoading(false);
      }
    };
    
    detectAnomalies();
  }, [selectedMetric, config, data, onAnomalyAlert, selectedAnomaly]);
  
  const severityStats = useMemo(() => {
    const stats = { critical: 0, warning: 0, info: 0, total: anomalies.length };
    anomalies.forEach(anomaly => {
      stats[anomaly.severity as keyof typeof stats]++;
    });
    return stats;
  }, [anomalies]);
  
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center">
            <Zap className="w-8 h-8 mr-3 text-orange-600" />
            Anomaly Detection
          </h2>
          <p className="text-muted-foreground">
            Real-time anomaly detection and root cause analysis
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
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
          
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>
      
      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Anomalies</p>
                <p className="text-2xl font-bold">{severityStats.total}</p>
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
                <p className="text-2xl font-bold text-red-600">{severityStats.critical}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Warnings</p>
                <p className="text-2xl font-bold text-yellow-600">{severityStats.warning}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Detection Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {chartData.length > 0 ? Math.round((severityStats.total / chartData.length) * 100) : 0}%
                </p>
              </div>
              <Target className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart and Timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <LineChart className="w-5 h-5 mr-2" />
                {selectedMetric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-48">
                  <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
                </div>
              ) : (
                <SimpleLineChart 
                  data={chartData} 
                  showAnomalies={true}
                  width={600}
                  height={200}
                />
              )}
            </CardContent>
          </Card>
          
          {/* Anomaly Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Clock className="w-5 h-5 mr-2" />
                Anomaly Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AnomalyTimeline
                anomalies={anomalies}
                onAnomalySelect={setSelectedAnomaly}
                selectedAnomaly={selectedAnomaly}
              />
            </CardContent>
          </Card>
        </div>
        
        {/* Sidebar */}
        <div className="space-y-6">
          {/* Root Cause Analysis */}
          {selectedAnomaly && (
            <RootCauseAnalysis anomaly={selectedAnomaly} />
          )}
          
          {/* Alert Configuration */}
          <AlertConfig
            config={config}
            onConfigChange={setConfig}
          />
        </div>
      </div>
      
      {/* Tabs for Additional Views */}
      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="patterns">Patterns</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>
        
        <TabsContent value="summary" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Detection Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Sensitivity</p>
                    <p className="font-medium capitalize">{config.sensitivity}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Lookback Period</p>
                    <p className="font-medium">{config.lookbackPeriod} days</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Min Deviation</p>
                    <p className="font-medium">{config.minimumDeviation}σ</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Data Points</p>
                    <p className="font-medium">{chartData.length}</p>
                  </div>
                </div>
                
                {severityStats.total > 0 && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Severity Distribution</p>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Critical</span>
                        <div className="flex items-center space-x-2">
                          <Progress 
                            value={(severityStats.critical / severityStats.total) * 100} 
                            className="w-20" 
                          />
                          <span className="text-sm">{severityStats.critical}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Warning</span>
                        <div className="flex items-center space-x-2">
                          <Progress 
                            value={(severityStats.warning / severityStats.total) * 100} 
                            className="w-20" 
                          />
                          <span className="text-sm">{severityStats.warning}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Info</span>
                        <div className="flex items-center space-x-2">
                          <Progress 
                            value={(severityStats.info / severityStats.total) * 100} 
                            className="w-20" 
                          />
                          <span className="text-sm">{severityStats.info}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="patterns" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Anomaly Patterns</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Most Common Type</p>
                    <p className="font-medium">
                      {anomalies.length > 0 
                        ? (() => {
                            const counts = anomalies.reduce((acc, curr) => 
                              (acc[curr.type] = (acc[curr.type] || 0) + 1, acc), 
                              {} as Record<string, number>
                            );
                            return Object.entries(counts).sort(([,a], [,b]) => b - a)[0]?.[0] || 'None';
                          })()
                        : 'None'
                      }
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Peak Detection Time</p>
                    <p className="font-medium">
                      {anomalies.length > 0
                        ? new Intl.DateTimeFormat('en-US', { hour: '2-digit' }).format(
                            new Date(Math.max(...anomalies.map(a => a.timestamp.getTime())))
                          )
                        : 'N/A'
                      }
                    </p>
                  </div>
                </div>
                
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Common Causes</p>
                  <div className="space-y-1">
                    {Array.from(new Set(anomalies.flatMap(a => a.potentialCauses)))
                      .slice(0, 5)
                      .map((cause, idx) => (
                        <div key={idx} className="flex items-center text-sm">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                          {cause}
                        </div>
                      ))
                    }
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="alerts" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="w-5 h-5 mr-2" />
                Alert Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="enable-alerts">Enable Real-time Alerts</Label>
                  <Switch id="enable-alerts" />
                </div>
                
                <div className="flex items-center justify-between">
                  <Label htmlFor="critical-only">Critical Anomalies Only</Label>
                  <Switch id="critical-only" />
                </div>
                
                <div className="flex items-center justify-between">
                  <Label htmlFor="email-alerts">Email Notifications</Label>
                  <Switch id="email-alerts" />
                </div>
                
                <Separator />
                
                <div>
                  <Label>Alert Channels</Label>
                  <div className="mt-2 space-y-2">
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Bell className="w-4 h-4 mr-2" />
                      Browser Notifications
                    </Button>
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Bell className="w-4 h-4 mr-2" />
                      Slack Integration
                    </Button>
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Bell className="w-4 h-4 mr-2" />
                      Webhook
                    </Button>
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

export default AnomalyDetection;