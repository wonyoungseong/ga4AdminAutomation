/**
 * AI-Powered Insights Engine for GA4 Analytics Dashboard
 * Enterprise-grade anomaly detection, trend prediction, and pattern recognition
 */

// Core Data Structures
export interface MetricDataPoint {
  timestamp: Date;
  value: number;
  metric: string;
  dimensions?: Record<string, string>;
  confidence?: number;
}

export interface TimeSeriesData {
  metric: string;
  dataPoints: MetricDataPoint[];
  interval: 'hour' | 'day' | 'week' | 'month';
  period: {
    start: Date;
    end: Date;
  };
}

export interface SeasonalPattern {
  type: 'weekly' | 'monthly' | 'yearly' | 'daily';
  strength: number; // 0-1
  peak: string; // description of peak period
  trough: string; // description of trough period
}

export interface TrendAnalysis {
  direction: 'increasing' | 'decreasing' | 'stable' | 'volatile';
  strength: number; // 0-1
  rate: number; // percentage change
  confidence: number; // 0-1
  startDate: Date;
  endDate: Date;
  R2: number; // coefficient of determination
}

// Anomaly Detection Types
export interface Anomaly {
  id: string;
  timestamp: Date;
  metric: string;
  value: number;
  expectedValue: number;
  deviation: number;
  severity: 'critical' | 'warning' | 'info';
  confidence: number;
  type: 'spike' | 'drop' | 'trend_break' | 'seasonal_deviation';
  description: string;
  potentialCauses: string[];
  impactAssessment: string;
}

export interface AnomalyDetectionConfig {
  sensitivity: 'low' | 'medium' | 'high';
  lookbackPeriod: number; // days
  seasonalityWindow: number; // days
  minimumDeviation: number; // standard deviations
  excludeWeekends?: boolean;
}

// Insights Types
export interface InsightRecommendation {
  id: string;
  title: string;
  description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  confidence: number;
  category: 'traffic' | 'conversion' | 'engagement' | 'technical' | 'content';
  actions: Array<{
    title: string;
    description: string;
    effort: 'low' | 'medium' | 'high';
    impact: 'low' | 'medium' | 'high';
  }>;
  potentialImpact: string;
  evidencePoints: string[];
  createdAt: Date;
  expiresAt?: Date;
}

export interface PredictiveInsight {
  id: string;
  metric: string;
  prediction: {
    value: number;
    confidence: number;
    range: {
      lower: number;
      upper: number;
    };
  };
  timeframe: string;
  methodology: string;
  factors: string[];
  businessImpact: string;
}

export interface PatternInsight {
  id: string;
  pattern: string;
  description: string;
  frequency: number;
  strength: number;
  examples: Array<{
    date: Date;
    value: number;
    context: string;
  }>;
  implications: string[];
}

// Main Insights Interface
export interface AIInsight {
  id: string;
  type: 'anomaly' | 'trend' | 'prediction' | 'pattern' | 'recommendation';
  title: string;
  description: string;
  severity: 'critical' | 'warning' | 'info' | 'positive';
  confidence: number;
  createdAt: Date;
  metrics: string[];
  data: Anomaly | TrendAnalysis | PredictiveInsight | PatternInsight | InsightRecommendation;
  tags: string[];
  dismissed?: boolean;
  actions?: Array<{
    label: string;
    action: string;
    primary?: boolean;
  }>;
}

// Statistical Analysis Functions

/**
 * Calculate moving average for trend analysis
 */
export function calculateMovingAverage(
  data: number[], 
  window: number
): number[] {
  const result: number[] = [];
  
  for (let i = 0; i < data.length; i++) {
    if (i < window - 1) {
      result.push(data[i]);
      continue;
    }
    
    const slice = data.slice(i - window + 1, i + 1);
    const average = slice.reduce((sum, val) => sum + val, 0) / slice.length;
    result.push(average);
  }
  
  return result;
}

/**
 * Calculate exponential moving average
 */
export function calculateExponentialMovingAverage(
  data: number[], 
  alpha: number = 0.3
): number[] {
  const result: number[] = [];
  let ema = data[0];
  
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      result.push(data[0]);
      continue;
    }
    
    ema = alpha * data[i] + (1 - alpha) * ema;
    result.push(ema);
  }
  
  return result;
}

/**
 * Calculate standard deviation
 */
export function calculateStandardDeviation(data: number[]): number {
  const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
  const squaredDiffs = data.map(val => Math.pow(val - mean, 2));
  const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / data.length;
  return Math.sqrt(variance);
}

/**
 * Linear regression for trend analysis
 */
export function calculateLinearRegression(data: MetricDataPoint[]): {
  slope: number;
  intercept: number;
  R2: number;
  predictions: number[];
} {
  const n = data.length;
  const x = data.map((_, i) => i);
  const y = data.map(d => d.value);
  
  const sumX = x.reduce((sum, val) => sum + val, 0);
  const sumY = y.reduce((sum, val) => sum + val, 0);
  const sumXY = x.reduce((sum, val, i) => sum + val * y[i], 0);
  const sumXX = x.reduce((sum, val) => sum + val * val, 0);
  const sumYY = y.reduce((sum, val) => sum + val * val, 0);
  
  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  
  // Calculate R²
  const yMean = sumY / n;
  const predictions = x.map(xi => slope * xi + intercept);
  const ssRes = y.reduce((sum, yi, i) => sum + Math.pow(yi - predictions[i], 2), 0);
  const ssTot = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
  const R2 = 1 - (ssRes / ssTot);
  
  return { slope, intercept, R2, predictions };
}

/**
 * Seasonal decomposition using simple moving averages
 */
export function decomposeTimeSeries(data: MetricDataPoint[], seasonPeriod: number): {
  trend: number[];
  seasonal: number[];
  residual: number[];
} {
  const values = data.map(d => d.value);
  const trend = calculateMovingAverage(values, seasonPeriod);
  
  // Calculate seasonal component
  const seasonal: number[] = new Array(values.length).fill(0);
  const seasonalAverages: number[] = new Array(seasonPeriod).fill(0);
  const seasonalCounts: number[] = new Array(seasonPeriod).fill(0);
  
  for (let i = 0; i < values.length; i++) {
    const seasonIndex = i % seasonPeriod;
    if (trend[i] !== 0) {
      seasonalAverages[seasonIndex] += values[i] - trend[i];
      seasonalCounts[seasonIndex]++;
    }
  }
  
  for (let i = 0; i < seasonPeriod; i++) {
    if (seasonalCounts[i] > 0) {
      seasonalAverages[i] /= seasonalCounts[i];
    }
  }
  
  for (let i = 0; i < values.length; i++) {
    seasonal[i] = seasonalAverages[i % seasonPeriod];
  }
  
  // Calculate residual
  const residual = values.map((val, i) => val - trend[i] - seasonal[i]);
  
  return { trend, seasonal, residual };
}

// Anomaly Detection Engine

export class AnomalyDetector {
  private config: AnomalyDetectionConfig;
  
  constructor(config: AnomalyDetectionConfig) {
    this.config = config;
  }
  
  /**
   * Detect anomalies using statistical methods
   */
  public detectAnomalies(data: TimeSeriesData): Anomaly[] {
    const anomalies: Anomaly[] = [];
    const values = data.dataPoints.map(d => d.value);
    
    // Z-score based detection
    const zScoreAnomalies = this.detectZScoreAnomalies(data);
    anomalies.push(...zScoreAnomalies);
    
    // Isolation Forest approximation
    const isolationAnomalies = this.detectIsolationAnomalies(data);
    anomalies.push(...isolationAnomalies);
    
    // Seasonal anomalies
    const seasonalAnomalies = this.detectSeasonalAnomalies(data);
    anomalies.push(...seasonalAnomalies);
    
    return this.deduplicateAnomalies(anomalies);
  }
  
  private detectZScoreAnomalies(data: TimeSeriesData): Anomaly[] {
    const anomalies: Anomaly[] = [];
    const values = data.dataPoints.map(d => d.value);
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const stdDev = calculateStandardDeviation(values);
    
    const threshold = this.getSensitivityThreshold();
    
    data.dataPoints.forEach((point, index) => {
      const zScore = Math.abs((point.value - mean) / stdDev);
      
      if (zScore > threshold) {
        const deviation = point.value - mean;
        const severity = this.classifySeverity(zScore, threshold);
        
        anomalies.push({
          id: `zscore_${data.metric}_${index}_${Date.now()}`,
          timestamp: point.timestamp,
          metric: data.metric,
          value: point.value,
          expectedValue: mean,
          deviation,
          severity,
          confidence: Math.min(zScore / (threshold * 2), 1),
          type: deviation > 0 ? 'spike' : 'drop',
          description: `${data.metric} shows ${deviation > 0 ? 'unusual spike' : 'significant drop'} (${Math.abs(deviation).toFixed(2)} from expected ${mean.toFixed(2)})`,
          potentialCauses: this.generatePotentialCauses(data.metric, deviation > 0 ? 'spike' : 'drop'),
          impactAssessment: this.assessImpact(data.metric, severity, Math.abs(deviation))
        });
      }
    });
    
    return anomalies;
  }
  
  private detectIsolationAnomalies(data: TimeSeriesData): Anomaly[] {
    // Simplified isolation forest using distance-based approach
    const anomalies: Anomaly[] = [];
    const values = data.dataPoints.map(d => d.value);
    
    if (values.length < 10) return anomalies;
    
    const windowSize = Math.min(10, Math.floor(values.length / 4));
    
    for (let i = windowSize; i < values.length - windowSize; i++) {
      const window = values.slice(i - windowSize, i + windowSize + 1);
      const current = values[i];
      const windowMean = window.reduce((sum, val) => sum + val, 0) / window.length;
      const distances = window.map(val => Math.abs(val - current));
      const avgDistance = distances.reduce((sum, val) => sum + val, 0) / distances.length;
      
      // Anomaly score based on isolation
      const isolationScore = avgDistance / (windowMean + 1);
      
      if (isolationScore > this.getIsolationThreshold()) {
        const point = data.dataPoints[i];
        anomalies.push({
          id: `isolation_${data.metric}_${i}_${Date.now()}`,
          timestamp: point.timestamp,
          metric: data.metric,
          value: current,
          expectedValue: windowMean,
          deviation: current - windowMean,
          severity: this.classifySeverity(isolationScore * 2, 2),
          confidence: Math.min(isolationScore, 1),
          type: current > windowMean ? 'spike' : 'drop',
          description: `Isolated ${current > windowMean ? 'spike' : 'drop'} detected in ${data.metric}`,
          potentialCauses: this.generatePotentialCauses(data.metric, current > windowMean ? 'spike' : 'drop'),
          impactAssessment: this.assessImpact(data.metric, this.classifySeverity(isolationScore * 2, 2), Math.abs(current - windowMean))
        });
      }
    }
    
    return anomalies;
  }
  
  private detectSeasonalAnomalies(data: TimeSeriesData): Anomaly[] {
    const anomalies: Anomaly[] = [];
    
    if (data.dataPoints.length < this.config.seasonalityWindow) {
      return anomalies;
    }
    
    const seasonPeriod = this.getSeasonPeriod(data.interval);
    const decomposition = decomposeTimeSeries(data.dataPoints, seasonPeriod);
    
    const residualStdDev = calculateStandardDeviation(decomposition.residual);
    const threshold = this.getSensitivityThreshold() * residualStdDev;
    
    decomposition.residual.forEach((residual, index) => {
      if (Math.abs(residual) > threshold && index < data.dataPoints.length) {
        const point = data.dataPoints[index];
        const expectedValue = point.value - residual;
        
        anomalies.push({
          id: `seasonal_${data.metric}_${index}_${Date.now()}`,
          timestamp: point.timestamp,
          metric: data.metric,
          value: point.value,
          expectedValue,
          deviation: residual,
          severity: this.classifySeverity(Math.abs(residual) / residualStdDev, threshold / residualStdDev),
          confidence: Math.min(Math.abs(residual) / (threshold * 2), 1),
          type: 'seasonal_deviation',
          description: `Seasonal pattern deviation detected in ${data.metric}`,
          potentialCauses: ['Unusual external events', 'Campaign changes', 'Technical issues', 'Market shifts'],
          impactAssessment: this.assessImpact(data.metric, this.classifySeverity(Math.abs(residual) / residualStdDev, threshold / residualStdDev), Math.abs(residual))
        });
      }
    });
    
    return anomalies;
  }
  
  private deduplicateAnomalies(anomalies: Anomaly[]): Anomaly[] {
    const sorted = anomalies.sort((a, b) => b.confidence - a.confidence);
    const unique: Anomaly[] = [];
    
    for (const anomaly of sorted) {
      const isDuplicate = unique.some(existing => 
        Math.abs(existing.timestamp.getTime() - anomaly.timestamp.getTime()) < 3600000 && // 1 hour
        existing.metric === anomaly.metric &&
        Math.abs(existing.value - anomaly.value) < 0.1 * existing.value
      );
      
      if (!isDuplicate) {
        unique.push(anomaly);
      }
    }
    
    return unique;
  }
  
  private getSensitivityThreshold(): number {
    switch (this.config.sensitivity) {
      case 'low': return 3.0;
      case 'medium': return 2.5;
      case 'high': return 2.0;
      default: return 2.5;
    }
  }
  
  private getIsolationThreshold(): number {
    switch (this.config.sensitivity) {
      case 'low': return 1.5;
      case 'medium': return 1.2;
      case 'high': return 1.0;
      default: return 1.2;
    }
  }
  
  private getSeasonPeriod(interval: string): number {
    switch (interval) {
      case 'hour': return 24; // Daily seasonality
      case 'day': return 7;   // Weekly seasonality
      case 'week': return 4;  // Monthly seasonality
      case 'month': return 12; // Yearly seasonality
      default: return 7;
    }
  }
  
  private classifySeverity(score: number, threshold: number): 'critical' | 'warning' | 'info' {
    if (score > threshold * 1.5) return 'critical';
    if (score > threshold * 1.2) return 'warning';
    return 'info';
  }
  
  private generatePotentialCauses(metric: string, type: 'spike' | 'drop'): string[] {
    const causes: Record<string, Record<string, string[]>> = {
      traffic: {
        spike: ['Viral content', 'Marketing campaign', 'External mentions', 'SEO improvements'],
        drop: ['Technical issues', 'Server downtime', 'Algorithm changes', 'Competitor activity']
      },
      conversion: {
        spike: ['Promotional offers', 'UX improvements', 'Pricing changes', 'Product launches'],
        drop: ['Technical bugs', 'Payment issues', 'User experience problems', 'Price increases']
      },
      engagement: {
        spike: ['Content quality improvements', 'New features', 'Personalization', 'User campaigns'],
        drop: ['Content fatigue', 'Technical issues', 'Competition', 'Seasonal effects']
      }
    };
    
    const metricCategory = this.categorizeMetric(metric);
    return causes[metricCategory]?.[type] || ['External factors', 'Technical changes', 'Market conditions'];
  }
  
  private categorizeMetric(metric: string): string {
    const lowerMetric = metric.toLowerCase();
    if (lowerMetric.includes('conversion') || lowerMetric.includes('purchase')) return 'conversion';
    if (lowerMetric.includes('engagement') || lowerMetric.includes('time') || lowerMetric.includes('bounce')) return 'engagement';
    return 'traffic';
  }
  
  private assessImpact(metric: string, severity: string, deviation: number): string {
    const impactTemplates = {
      critical: 'High business impact - immediate attention required',
      warning: 'Moderate impact - monitor closely and investigate',
      info: 'Low impact - consider for future optimization'
    };
    
    return impactTemplates[severity as keyof typeof impactTemplates];
  }
}

// Trend Analysis Engine

export class TrendAnalyzer {
  /**
   * Analyze trends in time series data
   */
  public analyzeTrend(data: TimeSeriesData): TrendAnalysis {
    const regression = calculateLinearRegression(data.dataPoints);
    const values = data.dataPoints.map(d => d.value);
    const timeRange = data.dataPoints.length;
    
    // Calculate trend strength and direction
    const direction = this.determineTrendDirection(regression.slope, regression.R2);
    const strength = Math.min(Math.abs(regression.R2), 1);
    const rate = this.calculatePercentageChange(values);
    
    return {
      direction,
      strength,
      rate,
      confidence: regression.R2,
      startDate: data.period.start,
      endDate: data.period.end,
      R2: regression.R2
    };
  }
  
  /**
   * Detect seasonal patterns
   */
  public detectSeasonalPatterns(data: TimeSeriesData): SeasonalPattern[] {
    const patterns: SeasonalPattern[] = [];
    const values = data.dataPoints.map(d => d.value);
    
    // Weekly pattern detection
    if (data.dataPoints.length >= 14) {
      const weeklyPattern = this.analyzeWeeklyPattern(data.dataPoints);
      if (weeklyPattern.strength > 0.3) {
        patterns.push(weeklyPattern);
      }
    }
    
    // Monthly pattern detection
    if (data.dataPoints.length >= 60) {
      const monthlyPattern = this.analyzeMonthlyPattern(data.dataPoints);
      if (monthlyPattern.strength > 0.3) {
        patterns.push(monthlyPattern);
      }
    }
    
    return patterns;
  }
  
  private determineTrendDirection(slope: number, r2: number): 'increasing' | 'decreasing' | 'stable' | 'volatile' {
    if (r2 < 0.3) return 'volatile';
    if (Math.abs(slope) < 0.01) return 'stable';
    return slope > 0 ? 'increasing' : 'decreasing';
  }
  
  private calculatePercentageChange(values: number[]): number {
    if (values.length < 2) return 0;
    const start = values[0];
    const end = values[values.length - 1];
    return start !== 0 ? ((end - start) / start) * 100 : 0;
  }
  
  private analyzeWeeklyPattern(dataPoints: MetricDataPoint[]): SeasonalPattern {
    const weeklyData: number[][] = [[], [], [], [], [], [], []]; // Sun-Sat
    
    dataPoints.forEach(point => {
      const dayOfWeek = point.timestamp.getDay();
      weeklyData[dayOfWeek].push(point.value);
    });
    
    const weeklyAverages = weeklyData.map(dayData => 
      dayData.length > 0 ? dayData.reduce((sum, val) => sum + val, 0) / dayData.length : 0
    );
    
    const maxAvg = Math.max(...weeklyAverages);
    const minAvg = Math.min(...weeklyAverages);
    const strength = maxAvg > 0 ? (maxAvg - minAvg) / maxAvg : 0;
    
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const maxDay = dayNames[weeklyAverages.indexOf(maxAvg)];
    const minDay = dayNames[weeklyAverages.indexOf(minAvg)];
    
    return {
      type: 'weekly',
      strength,
      peak: maxDay,
      trough: minDay
    };
  }
  
  private analyzeMonthlyPattern(dataPoints: MetricDataPoint[]): SeasonalPattern {
    const monthlyData: number[][] = Array.from({ length: 12 }, () => []);
    
    dataPoints.forEach(point => {
      const month = point.timestamp.getMonth();
      monthlyData[month].push(point.value);
    });
    
    const monthlyAverages = monthlyData.map(monthData => 
      monthData.length > 0 ? monthData.reduce((sum, val) => sum + val, 0) / monthData.length : 0
    );
    
    const maxAvg = Math.max(...monthlyAverages);
    const minAvg = Math.min(...monthlyAverages);
    const strength = maxAvg > 0 ? (maxAvg - minAvg) / maxAvg : 0;
    
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
    const maxMonth = monthNames[monthlyAverages.indexOf(maxAvg)];
    const minMonth = monthNames[monthlyAverages.indexOf(minAvg)];
    
    return {
      type: 'monthly',
      strength,
      peak: maxMonth,
      trough: minMonth
    };
  }
}

// Predictive Analytics Engine

export class PredictiveEngine {
  /**
   * Generate traffic forecast using linear regression with seasonal adjustment
   */
  public generateForecast(
    data: TimeSeriesData, 
    forecastDays: number
  ): {
    predictions: MetricDataPoint[];
    confidence: number;
    methodology: string;
  } {
    const regression = calculateLinearRegression(data.dataPoints);
    const seasonalPatterns = new TrendAnalyzer().detectSeasonalPatterns(data);
    const lastTimestamp = data.dataPoints[data.dataPoints.length - 1].timestamp;
    
    const predictions: MetricDataPoint[] = [];
    const intervalMs = this.getIntervalMs(data.interval);
    
    for (let i = 1; i <= forecastDays; i++) {
      const futureIndex = data.dataPoints.length + i - 1;
      const baseValue = regression.slope * futureIndex + regression.intercept;
      
      // Apply seasonal adjustment
      let seasonalAdjustment = 0;
      if (seasonalPatterns.length > 0) {
        seasonalAdjustment = this.calculateSeasonalAdjustment(
          new Date(lastTimestamp.getTime() + i * intervalMs),
          seasonalPatterns,
          data.dataPoints
        );
      }
      
      const adjustedValue = Math.max(0, baseValue + seasonalAdjustment);
      
      predictions.push({
        timestamp: new Date(lastTimestamp.getTime() + i * intervalMs),
        value: adjustedValue,
        metric: data.metric,
        confidence: Math.max(0.1, regression.R2 * Math.exp(-i / forecastDays))
      });
    }
    
    return {
      predictions,
      confidence: regression.R2,
      methodology: 'Linear regression with seasonal adjustment'
    };
  }
  
  private getIntervalMs(interval: string): number {
    switch (interval) {
      case 'hour': return 3600000;
      case 'day': return 86400000;
      case 'week': return 604800000;
      case 'month': return 2629746000; // Average month
      default: return 86400000;
    }
  }
  
  private calculateSeasonalAdjustment(
    date: Date, 
    patterns: SeasonalPattern[],
    historicalData: MetricDataPoint[]
  ): number {
    let adjustment = 0;
    
    patterns.forEach(pattern => {
      if (pattern.type === 'weekly') {
        const dayOfWeek = date.getDay();
        const weeklyAdjustment = this.getWeeklyAdjustment(dayOfWeek, historicalData);
        adjustment += weeklyAdjustment * pattern.strength;
      } else if (pattern.type === 'monthly') {
        const month = date.getMonth();
        const monthlyAdjustment = this.getMonthlyAdjustment(month, historicalData);
        adjustment += monthlyAdjustment * pattern.strength;
      }
    });
    
    return adjustment;
  }
  
  private getWeeklyAdjustment(dayOfWeek: number, historicalData: MetricDataPoint[]): number {
    const weeklyData: number[][] = Array.from({ length: 7 }, () => []);
    
    historicalData.forEach(point => {
      const day = point.timestamp.getDay();
      weeklyData[day].push(point.value);
    });
    
    const weeklyAverages = weeklyData.map(dayData => 
      dayData.length > 0 ? dayData.reduce((sum, val) => sum + val, 0) / dayData.length : 0
    );
    
    const overallAverage = weeklyAverages.reduce((sum, val) => sum + val, 0) / weeklyAverages.length;
    return weeklyAverages[dayOfWeek] - overallAverage;
  }
  
  private getMonthlyAdjustment(month: number, historicalData: MetricDataPoint[]): number {
    const monthlyData: number[][] = Array.from({ length: 12 }, () => []);
    
    historicalData.forEach(point => {
      const pointMonth = point.timestamp.getMonth();
      monthlyData[pointMonth].push(point.value);
    });
    
    const monthlyAverages = monthlyData.map(monthData => 
      monthData.length > 0 ? monthData.reduce((sum, val) => sum + val, 0) / monthData.length : 0
    );
    
    const overallAverage = monthlyAverages.reduce((sum, val) => sum + val, 0) / monthlyAverages.length;
    return monthlyAverages[month] - overallAverage;
  }
}

// Insight Generation Engine

export class InsightGenerator {
  private anomalyDetector: AnomalyDetector;
  private trendAnalyzer: TrendAnalyzer;
  private predictiveEngine: PredictiveEngine;
  
  constructor(config: AnomalyDetectionConfig) {
    this.anomalyDetector = new AnomalyDetector(config);
    this.trendAnalyzer = new TrendAnalyzer();
    this.predictiveEngine = new PredictiveEngine();
  }
  
  /**
   * Generate comprehensive insights from multiple data sources
   */
  public async generateInsights(dataSources: TimeSeriesData[]): Promise<AIInsight[]> {
    const insights: AIInsight[] = [];
    
    for (const data of dataSources) {
      // Anomaly insights
      const anomalies = this.anomalyDetector.detectAnomalies(data);
      anomalies.forEach(anomaly => {
        insights.push(this.createAnomalyInsight(anomaly));
      });
      
      // Trend insights
      const trend = this.trendAnalyzer.analyzeTrend(data);
      if (trend.confidence > 0.5) {
        insights.push(this.createTrendInsight(data.metric, trend));
      }
      
      // Seasonal pattern insights
      const patterns = this.trendAnalyzer.detectSeasonalPatterns(data);
      patterns.forEach(pattern => {
        insights.push(this.createPatternInsight(data.metric, pattern));
      });
      
      // Predictive insights
      const forecast = this.predictiveEngine.generateForecast(data, 7);
      if (forecast.confidence > 0.4) {
        insights.push(this.createPredictiveInsight(data.metric, forecast));
      }
    }
    
    // Cross-metric insights
    const correlationInsights = this.generateCorrelationInsights(dataSources);
    insights.push(...correlationInsights);
    
    return this.prioritizeInsights(insights);
  }
  
  private createAnomalyInsight(anomaly: Anomaly): AIInsight {
    return {
      id: anomaly.id,
      type: 'anomaly',
      title: `${anomaly.type === 'spike' ? 'Spike' : 'Drop'} detected in ${anomaly.metric}`,
      description: anomaly.description,
      severity: anomaly.severity,
      confidence: anomaly.confidence,
      createdAt: new Date(),
      metrics: [anomaly.metric],
      data: anomaly,
      tags: ['anomaly', anomaly.type, anomaly.severity],
      actions: [
        { label: 'Investigate', action: 'investigate', primary: true },
        { label: 'Dismiss', action: 'dismiss' }
      ]
    };
  }
  
  private createTrendInsight(metric: string, trend: TrendAnalysis): AIInsight {
    const severity = this.determineTrendSeverity(trend);
    
    return {
      id: `trend_${metric}_${Date.now()}`,
      type: 'trend',
      title: `${metric} showing ${trend.direction} trend`,
      description: `${metric} has been ${trend.direction} by ${Math.abs(trend.rate).toFixed(1)}% with ${(trend.confidence * 100).toFixed(0)}% confidence`,
      severity,
      confidence: trend.confidence,
      createdAt: new Date(),
      metrics: [metric],
      data: trend,
      tags: ['trend', trend.direction, severity],
      actions: [
        { label: 'View Details', action: 'view_trend', primary: true },
        { label: 'Set Alert', action: 'set_alert' }
      ]
    };
  }
  
  private createPatternInsight(metric: string, pattern: SeasonalPattern): AIInsight {
    return {
      id: `pattern_${metric}_${pattern.type}_${Date.now()}`,
      type: 'pattern',
      title: `${pattern.type} pattern detected in ${metric}`,
      description: `Strong ${pattern.type} seasonality with peaks on ${pattern.peak} and troughs on ${pattern.trough}`,
      severity: 'info',
      confidence: pattern.strength,
      createdAt: new Date(),
      metrics: [metric],
      data: {
        id: `pattern_${metric}_${pattern.type}`,
        pattern: pattern.type,
        description: `${pattern.type} seasonality in ${metric}`,
        frequency: pattern.strength,
        strength: pattern.strength,
        examples: [],
        implications: [`Optimize for ${pattern.peak}`, `Investigate ${pattern.trough} performance`]
      } as PatternInsight,
      tags: ['pattern', pattern.type, 'seasonal'],
      actions: [
        { label: 'Optimize Schedule', action: 'optimize_schedule', primary: true },
        { label: 'View Pattern', action: 'view_pattern' }
      ]
    };
  }
  
  private createPredictiveInsight(metric: string, forecast: any): AIInsight {
    const lastValue = forecast.predictions[0]?.value || 0;
    const futureValue = forecast.predictions[forecast.predictions.length - 1]?.value || 0;
    const change = lastValue !== 0 ? ((futureValue - lastValue) / lastValue) * 100 : 0;
    
    return {
      id: `prediction_${metric}_${Date.now()}`,
      type: 'prediction',
      title: `${metric} forecast: ${change > 0 ? 'growth' : 'decline'} expected`,
      description: `Predicted ${Math.abs(change).toFixed(1)}% ${change > 0 ? 'increase' : 'decrease'} over next 7 days`,
      severity: Math.abs(change) > 20 ? 'warning' : 'info',
      confidence: forecast.confidence,
      createdAt: new Date(),
      metrics: [metric],
      data: {
        id: `prediction_${metric}`,
        metric,
        prediction: {
          value: futureValue,
          confidence: forecast.confidence,
          range: {
            lower: futureValue * 0.8,
            upper: futureValue * 1.2
          }
        },
        timeframe: '7 days',
        methodology: forecast.methodology,
        factors: ['Historical trends', 'Seasonal patterns'],
        businessImpact: change > 10 ? 'Significant' : 'Moderate'
      } as PredictiveInsight,
      tags: ['prediction', 'forecast', change > 0 ? 'growth' : 'decline'],
      actions: [
        { label: 'View Forecast', action: 'view_forecast', primary: true },
        { label: 'Plan Actions', action: 'plan_actions' }
      ]
    };
  }
  
  private generateCorrelationInsights(dataSources: TimeSeriesData[]): AIInsight[] {
    const insights: AIInsight[] = [];
    
    // Simple correlation analysis between metrics
    for (let i = 0; i < dataSources.length; i++) {
      for (let j = i + 1; j < dataSources.length; j++) {
        const correlation = this.calculateCorrelation(
          dataSources[i].dataPoints.map(d => d.value),
          dataSources[j].dataPoints.map(d => d.value)
        );
        
        if (Math.abs(correlation) > 0.7) {
          insights.push({
            id: `correlation_${dataSources[i].metric}_${dataSources[j].metric}_${Date.now()}`,
            type: 'recommendation',
            title: `Strong correlation between ${dataSources[i].metric} and ${dataSources[j].metric}`,
            description: `${correlation > 0 ? 'Positive' : 'Negative'} correlation (${(correlation * 100).toFixed(0)}%) suggests these metrics are related`,
            severity: 'info',
            confidence: Math.abs(correlation),
            createdAt: new Date(),
            metrics: [dataSources[i].metric, dataSources[j].metric],
            data: {
              id: `correlation_${dataSources[i].metric}_${dataSources[j].metric}`,
              title: 'Metric Correlation',
              description: `Strong ${correlation > 0 ? 'positive' : 'negative'} correlation detected`,
              priority: 'medium',
              confidence: Math.abs(correlation),
              category: 'technical',
              actions: [
                {
                  title: 'Monitor Together',
                  description: 'Set up combined monitoring for these metrics',
                  effort: 'low',
                  impact: 'medium'
                }
              ],
              potentialImpact: 'Improved monitoring and optimization opportunities',
              evidencePoints: [`Correlation coefficient: ${correlation.toFixed(3)}`],
              createdAt: new Date()
            } as InsightRecommendation,
            tags: ['correlation', 'metrics', 'relationship']
          });
        }
      }
    }
    
    return insights;
  }
  
  private calculateCorrelation(x: number[], y: number[]): number {
    const n = Math.min(x.length, y.length);
    if (n < 2) return 0;
    
    const xSlice = x.slice(0, n);
    const ySlice = y.slice(0, n);
    
    const sumX = xSlice.reduce((sum, val) => sum + val, 0);
    const sumY = ySlice.reduce((sum, val) => sum + val, 0);
    const sumXY = xSlice.reduce((sum, val, i) => sum + val * ySlice[i], 0);
    const sumXX = xSlice.reduce((sum, val) => sum + val * val, 0);
    const sumYY = ySlice.reduce((sum, val) => sum + val * val, 0);
    
    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumXX - sumX * sumX) * (n * sumYY - sumY * sumY));
    
    return denominator !== 0 ? numerator / denominator : 0;
  }
  
  private determineTrendSeverity(trend: TrendAnalysis): 'critical' | 'warning' | 'info' | 'positive' {
    if (trend.confidence < 0.3) return 'info';
    
    const changeRate = Math.abs(trend.rate);
    if (changeRate > 50) return 'critical';
    if (changeRate > 20) return 'warning';
    if (trend.direction === 'increasing' && changeRate > 5) return 'positive';
    
    return 'info';
  }
  
  private prioritizeInsights(insights: AIInsight[]): AIInsight[] {
    const severityScore = { critical: 4, warning: 3, positive: 2, info: 1 };
    
    return insights.sort((a, b) => {
      const aScore = severityScore[a.severity] * a.confidence;
      const bScore = severityScore[b.severity] * b.confidence;
      return bScore - aScore;
    });
  }
}

// Mock Data Generator for Development

export function generateMockTimeSeriesData(
  metric: string,
  days: number = 30,
  interval: 'hour' | 'day' = 'day'
): TimeSeriesData {
  const dataPoints: MetricDataPoint[] = [];
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  
  const intervalMs = interval === 'hour' ? 3600000 : 86400000;
  const pointCount = interval === 'hour' ? days * 24 : days;
  
  // Base value with trend and seasonality
  const baseValue = 1000;
  const trendRate = (Math.random() - 0.5) * 0.02; // -1% to +1% per day
  const seasonalAmplitude = baseValue * 0.3;
  const noiseAmplitude = baseValue * 0.1;
  
  for (let i = 0; i < pointCount; i++) {
    const timestamp = new Date(startDate.getTime() + i * intervalMs);
    
    // Calculate components
    const trend = baseValue * (1 + trendRate * i);
    const seasonal = seasonalAmplitude * Math.sin((2 * Math.PI * i) / (interval === 'hour' ? 24 : 7));
    const noise = (Math.random() - 0.5) * noiseAmplitude;
    
    // Add occasional anomalies
    const anomalyChance = Math.random();
    let anomalyMultiplier = 1;
    if (anomalyChance < 0.02) { // 2% chance of anomaly
      anomalyMultiplier = Math.random() < 0.5 ? 0.3 : 2.5; // Drop or spike
    }
    
    const value = Math.max(0, (trend + seasonal + noise) * anomalyMultiplier);
    
    dataPoints.push({
      timestamp,
      value,
      metric,
      confidence: 0.9 + Math.random() * 0.1
    });
  }
  
  return {
    metric,
    dataPoints,
    interval,
    period: {
      start: startDate,
      end: new Date()
    }
  };
}

// Export utility function for easy access
export function createInsightEngine(config?: Partial<AnomalyDetectionConfig>): InsightGenerator {
  const defaultConfig: AnomalyDetectionConfig = {
    sensitivity: 'medium',
    lookbackPeriod: 30,
    seasonalityWindow: 14,
    minimumDeviation: 2.0,
    excludeWeekends: false,
    ...config
  };
  
  return new InsightGenerator(defaultConfig);
}