/**
 * Insight Card Component
 * Displays individual AI insights with detailed information and actions
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { 
  AlertTriangle, 
  TrendingUp, 
  Target, 
  Lightbulb, 
  ChevronDown, 
  ChevronUp,
  Clock,
  BarChart3,
  CheckCircle,
  XCircle
} from 'lucide-react';

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

interface InsightCardProps {
  insight: AIInsight;
  onActionTaken?: (insightId: string, action: string) => void;
}

export const InsightCard: React.FC<InsightCardProps> = ({ 
  insight, 
  onActionTaken 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [actionTaken, setActionTaken] = useState<string | null>(null);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'anomaly': return <AlertTriangle className="h-4 w-4" />;
      case 'trend': return <TrendingUp className="h-4 w-4" />;
      case 'prediction': return <Target className="h-4 w-4" />;
      case 'recommendation': return <Lightbulb className="h-4 w-4" />;
      default: return <BarChart3 className="h-4 w-4" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'secondary';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'anomaly': return 'text-orange-600';
      case 'trend': return 'text-blue-600';
      case 'prediction': return 'text-purple-600';
      case 'recommendation': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const handleAction = (action: string) => {
    setActionTaken(action);
    onActionTaken?.(insight.insight_id, action);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const renderDataVisualization = () => {
    if (!insight.data || typeof insight.data !== 'object') {
      return null;
    }

    switch (insight.type) {
      case 'anomaly':
        return (
          <div className="mt-4 p-3 bg-orange-50 rounded-lg">
            <h4 className="text-sm font-medium mb-2">Anomaly Details</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {insight.data.actual_value && (
                <div>
                  <span className="text-muted-foreground">Actual Value:</span>
                  <div className="font-medium">{insight.data.actual_value.toFixed(2)}</div>
                </div>
              )}
              {insight.data.expected_range && (
                <div>
                  <span className="text-muted-foreground">Expected Range:</span>
                  <div className="font-medium">
                    {insight.data.expected_range[0].toFixed(2)} - {insight.data.expected_range[1].toFixed(2)}
                  </div>
                </div>
              )}
              {insight.data.anomaly_score && (
                <div>
                  <span className="text-muted-foreground">Anomaly Score:</span>
                  <div className="font-medium">{insight.data.anomaly_score.toFixed(2)}</div>
                </div>
              )}
            </div>
          </div>
        );

      case 'trend':
        return (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium mb-2">Trend Analysis</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {insight.data.trend_direction && (
                <div>
                  <span className="text-muted-foreground">Direction:</span>
                  <div className="font-medium capitalize">{insight.data.trend_direction}</div>
                </div>
              )}
              {insight.data.trend_strength && (
                <div>
                  <span className="text-muted-foreground">Strength:</span>
                  <div className="font-medium">{(insight.data.trend_strength * 100).toFixed(1)}%</div>
                </div>
              )}
              {insight.data.projected_value && (
                <div>
                  <span className="text-muted-foreground">Projected Value:</span>
                  <div className="font-medium">{insight.data.projected_value.toFixed(2)}</div>
                </div>
              )}
              {insight.data.duration_days && (
                <div>
                  <span className="text-muted-foreground">Duration:</span>
                  <div className="font-medium">{insight.data.duration_days} days</div>
                </div>
              )}
            </div>
          </div>
        );

      case 'prediction':
        return (
          <div className="mt-4 p-3 bg-purple-50 rounded-lg">
            <h4 className="text-sm font-medium mb-2">Prediction Results</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {insight.data.predicted_sessions && (
                <div>
                  <span className="text-muted-foreground">Predicted Sessions:</span>
                  <div className="font-medium">{insight.data.predicted_sessions.toLocaleString()}</div>
                </div>
              )}
              {insight.data.predicted_conversion_rate && (
                <div>
                  <span className="text-muted-foreground">Conversion Rate:</span>
                  <div className="font-medium">{(insight.data.predicted_conversion_rate * 100).toFixed(2)}%</div>
                </div>
              )}
              {insight.data.time_horizon_days && (
                <div>
                  <span className="text-muted-foreground">Time Horizon:</span>
                  <div className="font-medium">{insight.data.time_horizon_days} days</div>
                </div>
              )}
              {insight.data.forecast_confidence && (
                <div>
                  <span className="text-muted-foreground">Forecast Confidence:</span>
                  <div className="font-medium">{(insight.data.forecast_confidence * 100).toFixed(1)}%</div>
                </div>
              )}
            </div>
          </div>
        );

      case 'recommendation':
        return (
          <div className="mt-4 p-3 bg-green-50 rounded-lg">
            <h4 className="text-sm font-medium mb-2">Recommendation Data</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {insight.data.current_bounce_rate && (
                <div>
                  <span className="text-muted-foreground">Current Bounce Rate:</span>
                  <div className="font-medium">{(insight.data.current_bounce_rate * 100).toFixed(1)}%</div>
                </div>
              )}
              {insight.data.potential_improvement && (
                <div>
                  <span className="text-muted-foreground">Potential Improvement:</span>
                  <div className="font-medium">{insight.data.potential_improvement}</div>
                </div>
              )}
              {insight.data.current_conversion_rate && (
                <div>
                  <span className="text-muted-foreground">Current Conversion:</span>
                  <div className="font-medium">{(insight.data.current_conversion_rate * 100).toFixed(2)}%</div>
                </div>
              )}
              {insight.data.industry_average && (
                <div>
                  <span className="text-muted-foreground">Industry Average:</span>
                  <div className="font-medium">{(insight.data.industry_average * 100).toFixed(2)}%</div>
                </div>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Card className="relative">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <div className={`mt-1 ${getTypeColor(insight.type)}`}>
              {getTypeIcon(insight.type)}
            </div>
            <div className="flex-1">
              <CardTitle className="text-lg">{insight.title}</CardTitle>
              <CardDescription className="mt-1">
                {insight.description}
              </CardDescription>
            </div>
          </div>
          <div className="flex flex-col items-end space-y-2">
            <Badge variant={getPriorityColor(insight.priority)}>
              {insight.priority.toUpperCase()}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {Math.round(insight.confidence * 100)}% confidence
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Metric and Timestamp */}
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center space-x-4">
              {insight.metric_name && (
                <span>Metric: <span className="font-medium">{insight.metric_name}</span></span>
              )}
              <div className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>{formatTimestamp(insight.timestamp)}</span>
              </div>
            </div>
          </div>

          {/* Expandable Details */}
          <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between p-0">
                <span>View Details</span>
                {isExpanded ? 
                  <ChevronUp className="h-4 w-4" /> : 
                  <ChevronDown className="h-4 w-4" />
                }
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-4">
              {renderDataVisualization()}

              {/* Actionable Recommendations */}
              {insight.actionable_recommendations && insight.actionable_recommendations.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium mb-2">Recommended Actions</h4>
                  <ul className="space-y-2">
                    {insight.actionable_recommendations.map((recommendation, index) => (
                      <li key={index} className="flex items-start space-x-2 text-sm">
                        <div className="w-1.5 h-1.5 rounded-full bg-current mt-2 flex-shrink-0" />
                        <span>{recommendation}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CollapsibleContent>
          </Collapsible>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t">
            <div className="flex space-x-2">
              {!actionTaken ? (
                <>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleAction('acknowledged')}
                  >
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Acknowledge
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleAction('dismissed')}
                  >
                    <XCircle className="h-3 w-3 mr-1" />
                    Dismiss
                  </Button>
                </>
              ) : (
                <Badge variant="secondary" className="text-xs">
                  {actionTaken === 'acknowledged' ? 'Acknowledged' : 'Dismissed'}
                </Badge>
              )}
            </div>
            
            <Badge variant="outline" className="text-xs capitalize">
              {insight.type}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};