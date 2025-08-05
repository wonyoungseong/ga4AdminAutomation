/**
 * Machine Learning Models for GA4 Analytics
 * Client-side ML implementation using statistical methods and algorithms
 */

import { MetricDataPoint, TimeSeriesData } from './ai-insights';

// Data Preprocessing Utilities

export interface PreprocessingConfig {
  normalize: boolean;
  fillMissing: 'forward' | 'backward' | 'interpolate' | 'mean';
  removeOutliers: boolean;
  outlierThreshold: number; // Standard deviations
  smoothing: boolean;
  smoothingWindow: number;
}

export interface ProcessedData {
  original: number[];
  processed: number[];
  metadata: {
    mean: number;
    std: number;
    min: number;
    max: number;
    missingCount: number;
    outlierCount: number;
  };
}

export class DataPreprocessor {
  private config: PreprocessingConfig;
  
  constructor(config: PreprocessingConfig) {
    this.config = config;
  }
  
  /**
   * Preprocess time series data for ML models
   */
  public preprocess(data: number[]): ProcessedData {
    let processed = [...data];
    let missingCount = 0;
    let outlierCount = 0;
    
    // Calculate initial statistics
    const validData = data.filter(val => val !== null && val !== undefined && !isNaN(val));
    const mean = validData.reduce((sum, val) => sum + val, 0) / validData.length;
    const std = Math.sqrt(validData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / validData.length);
    const min = Math.min(...validData);
    const max = Math.max(...validData);
    
    // Handle missing values
    if (this.config.fillMissing) {
      const result = this.handleMissingValues(processed, this.config.fillMissing);
      processed = result.data;
      missingCount = result.missingCount;
    }
    
    // Remove outliers
    if (this.config.removeOutliers) {
      const result = this.removeOutliers(processed, mean, std, this.config.outlierThreshold);
      processed = result.data;
      outlierCount = result.outlierCount;
    }
    
    // Apply smoothing
    if (this.config.smoothing) {
      processed = this.applySmoothingFilter(processed, this.config.smoothingWindow);
    }
    
    // Normalize data
    if (this.config.normalize) {
      processed = this.normalizeData(processed);
    }
    
    return {
      original: data,
      processed,
      metadata: {
        mean,
        std,
        min,
        max,
        missingCount,
        outlierCount
      }
    };
  }
  
  private handleMissingValues(data: number[], method: string): { data: number[]; missingCount: number } {
    const result = [...data];
    let missingCount = 0;
    
    for (let i = 0; i < result.length; i++) {
      if (result[i] === null || result[i] === undefined || isNaN(result[i])) {
        missingCount++;
        
        switch (method) {
          case 'forward':
            result[i] = i > 0 ? result[i - 1] : 0;
            break;
          case 'backward':
            result[i] = i < result.length - 1 ? result[i + 1] : 0;
            break;
          case 'interpolate':
            result[i] = this.interpolateValue(result, i);
            break;
          case 'mean':
            const validValues = result.filter(val => val !== null && val !== undefined && !isNaN(val));
            result[i] = validValues.length > 0 ? validValues.reduce((sum, val) => sum + val, 0) / validValues.length : 0;
            break;
        }
      }
    }
    
    return { data: result, missingCount };
  }
  
  private interpolateValue(data: number[], index: number): number {
    let prevIndex = index - 1;
    let nextIndex = index + 1;
    
    // Find previous valid value
    while (prevIndex >= 0 && (data[prevIndex] === null || isNaN(data[prevIndex]))) {
      prevIndex--;
    }
    
    // Find next valid value
    while (nextIndex < data.length && (data[nextIndex] === null || isNaN(data[nextIndex]))) {
      nextIndex++;
    }
    
    if (prevIndex >= 0 && nextIndex < data.length) {
      const prevValue = data[prevIndex];
      const nextValue = data[nextIndex];
      const weight = (index - prevIndex) / (nextIndex - prevIndex);
      return prevValue + (nextValue - prevValue) * weight;
    } else if (prevIndex >= 0) {
      return data[prevIndex];
    } else if (nextIndex < data.length) {
      return data[nextIndex];
    }
    
    return 0;
  }
  
  private removeOutliers(data: number[], mean: number, std: number, threshold: number): { data: number[]; outlierCount: number } {
    const result = [...data];
    let outlierCount = 0;
    
    for (let i = 0; i < result.length; i++) {
      if (Math.abs(result[i] - mean) > threshold * std) {
        outlierCount++;
        // Replace with clamped value
        result[i] = result[i] > mean ? mean + threshold * std : mean - threshold * std;
      }
    }
    
    return { data: result, outlierCount };
  }
  
  private applySmoothingFilter(data: number[], window: number): number[] {
    const result: number[] = [];
    const halfWindow = Math.floor(window / 2);
    
    for (let i = 0; i < data.length; i++) {
      const start = Math.max(0, i - halfWindow);
      const end = Math.min(data.length, i + halfWindow + 1);
      const slice = data.slice(start, end);
      const average = slice.reduce((sum, val) => sum + val, 0) / slice.length;
      result.push(average);
    }
    
    return result;
  }
  
  private normalizeData(data: number[]): number[] {
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min;
    
    if (range === 0) return data.map(() => 0);
    
    return data.map(val => (val - min) / range);
  }
}

// Linear Regression Model

export interface LinearRegressionResult {
  slope: number;
  intercept: number;
  rSquared: number;
  predictions: number[];
  residuals: number[];
  confidence: number;
  standardError: number;
}

export class LinearRegression {
  private model: {
    slope: number;
    intercept: number;
    rSquared: number;
    standardError: number;
  } | null = null;
  
  /**
   * Train linear regression model
   */
  public train(x: number[], y: number[]): LinearRegressionResult {
    if (x.length !== y.length || x.length < 2) {
      throw new Error('Invalid input data for linear regression');
    }
    
    const n = x.length;
    const sumX = x.reduce((sum, val) => sum + val, 0);
    const sumY = y.reduce((sum, val) => sum + val, 0);
    const sumXY = x.reduce((sum, val, i) => sum + val * y[i], 0);
    const sumXX = x.reduce((sum, val) => sum + val * val, 0);
    const sumYY = y.reduce((sum, val) => sum + val * val, 0);
    
    // Calculate slope and intercept
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    // Calculate predictions and residuals
    const predictions = x.map(xi => slope * xi + intercept);
    const residuals = y.map((yi, i) => yi - predictions[i]);
    
    // Calculate R²
    const yMean = sumY / n;
    const ssRes = residuals.reduce((sum, res) => sum + res * res, 0);
    const ssTot = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
    const rSquared = 1 - (ssRes / ssTot);
    
    // Calculate standard error
    const standardError = Math.sqrt(ssRes / (n - 2));
    
    // Store model
    this.model = { slope, intercept, rSquared, standardError };
    
    return {
      slope,
      intercept,
      rSquared,
      predictions,
      residuals,
      confidence: Math.max(0, rSquared),
      standardError
    };
  }
  
  /**
   * Make predictions with trained model
   */
  public predict(x: number[]): number[] {
    if (!this.model) {
      throw new Error('Model not trained. Call train() first.');
    }
    
    return x.map(xi => this.model!.slope * xi + this.model!.intercept);
  }
  
  /**
   * Get prediction intervals
   */
  public getPredictionIntervals(x: number[], confidence: number = 0.95): Array<{value: number; lower: number; upper: number}> {
    if (!this.model) {
      throw new Error('Model not trained. Call train() first.');
    }
    
    const predictions = this.predict(x);
    const tValue = this.getTValue(confidence);
    const margin = tValue * this.model.standardError;
    
    return predictions.map(pred => ({
      value: pred,
      lower: pred - margin,
      upper: pred + margin
    }));
  }
  
  private getTValue(confidence: number): number {
    // Simplified t-value lookup for common confidence levels
    const tValues: Record<number, number> = {
      0.90: 1.645,
      0.95: 1.96,
      0.99: 2.576
    };
    
    return tValues[confidence] || 1.96;
  }
}

// Polynomial Regression Model

export class PolynomialRegression {
  private degree: number;
  private coefficients: number[] = [];
  
  constructor(degree: number = 2) {
    this.degree = degree;
  }
  
  /**
   * Train polynomial regression model
   */
  public train(x: number[], y: number[]): {
    coefficients: number[];
    rSquared: number;
    predictions: number[];
  } {
    if (x.length !== y.length || x.length <= this.degree) {
      throw new Error('Invalid input data for polynomial regression');
    }
    
    // Create design matrix
    const X = this.createDesignMatrix(x);
    
    // Solve normal equation: coefficients = (X^T * X)^-1 * X^T * y
    const XTX = this.matrixMultiply(this.transpose(X), X);
    const XTy = this.matrixVectorMultiply(this.transpose(X), y);
    
    // Solve linear system (simplified approach)
    this.coefficients = this.solveLinearSystem(XTX, XTy);
    
    // Calculate predictions and R²
    const predictions = this.predict(x);
    const yMean = y.reduce((sum, val) => sum + val, 0) / y.length;
    const ssRes = y.reduce((sum, yi, i) => sum + Math.pow(yi - predictions[i], 2), 0);
    const ssTot = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
    const rSquared = 1 - (ssRes / ssTot);
    
    return {
      coefficients: this.coefficients,
      rSquared,
      predictions
    };
  }
  
  /**
   * Make predictions with trained model
   */
  public predict(x: number[]): number[] {
    if (this.coefficients.length === 0) {
      throw new Error('Model not trained. Call train() first.');
    }
    
    return x.map(xi => {
      let prediction = 0;
      for (let i = 0; i <= this.degree; i++) {
        prediction += this.coefficients[i] * Math.pow(xi, i);
      }
      return prediction;
    });
  }
  
  private createDesignMatrix(x: number[]): number[][] {
    const matrix: number[][] = [];
    
    for (let i = 0; i < x.length; i++) {
      const row: number[] = [];
      for (let j = 0; j <= this.degree; j++) {
        row.push(Math.pow(x[i], j));
      }
      matrix.push(row);
    }
    
    return matrix;
  }
  
  private transpose(matrix: number[][]): number[][] {
    const rows = matrix.length;
    const cols = matrix[0].length;
    const result: number[][] = [];
    
    for (let j = 0; j < cols; j++) {
      const row: number[] = [];
      for (let i = 0; i < rows; i++) {
        row.push(matrix[i][j]);
      }
      result.push(row);
    }
    
    return result;
  }
  
  private matrixMultiply(a: number[][], b: number[][]): number[][] {
    const rows = a.length;
    const cols = b[0].length;
    const inner = b.length;
    const result: number[][] = [];
    
    for (let i = 0; i < rows; i++) {
      const row: number[] = [];
      for (let j = 0; j < cols; j++) {
        let sum = 0;
        for (let k = 0; k < inner; k++) {
          sum += a[i][k] * b[k][j];
        }
        row.push(sum);
      }
      result.push(row);
    }
    
    return result;
  }
  
  private matrixVectorMultiply(matrix: number[][], vector: number[]): number[] {
    const result: number[] = [];
    
    for (let i = 0; i < matrix.length; i++) {
      let sum = 0;
      for (let j = 0; j < matrix[i].length; j++) {
        sum += matrix[i][j] * vector[j];
      }
      result.push(sum);
    }
    
    return result;
  }
  
  private solveLinearSystem(A: number[][], b: number[]): number[] {
    // Simplified Gaussian elimination
    const n = A.length;
    const augmented: number[][] = A.map((row, i) => [...row, b[i]]);
    
    // Forward elimination
    for (let i = 0; i < n; i++) {
      // Find pivot
      let maxRow = i;
      for (let k = i + 1; k < n; k++) {
        if (Math.abs(augmented[k][i]) > Math.abs(augmented[maxRow][i])) {
          maxRow = k;
        }
      }
      
      // Swap rows
      if (maxRow !== i) {
        [augmented[i], augmented[maxRow]] = [augmented[maxRow], augmented[i]];
      }
      
      // Make diagonal element 1
      const pivot = augmented[i][i];
      if (Math.abs(pivot) < 1e-10) continue;
      
      for (let j = i; j <= n; j++) {
        augmented[i][j] /= pivot;
      }
      
      // Eliminate column
      for (let k = i + 1; k < n; k++) {
        const factor = augmented[k][i];
        for (let j = i; j <= n; j++) {
          augmented[k][j] -= factor * augmented[i][j];
        }
      }
    }
    
    // Back substitution
    const x: number[] = new Array(n).fill(0);
    for (let i = n - 1; i >= 0; i--) {
      x[i] = augmented[i][n];
      for (let j = i + 1; j < n; j++) {
        x[i] -= augmented[i][j] * x[j];
      }
    }
    
    return x;
  }
}

// Moving Average Models

export class MovingAverageModel {
  private window: number;
  private type: 'simple' | 'exponential' | 'weighted';
  private alpha?: number; // For exponential moving average
  
  constructor(window: number, type: 'simple' | 'exponential' | 'weighted' = 'simple', alpha?: number) {
    this.window = window;
    this.type = type;
    this.alpha = alpha || 0.3;
  }
  
  /**
   * Calculate moving average
   */
  public calculate(data: number[]): number[] {
    switch (this.type) {
      case 'simple':
        return this.calculateSimpleMA(data);
      case 'exponential':
        return this.calculateExponentialMA(data);
      case 'weighted':
        return this.calculateWeightedMA(data);
      default:
        return this.calculateSimpleMA(data);
    }
  }
  
  /**
   * Forecast next values using moving average
   */
  public forecast(data: number[], periods: number): number[] {
    const ma = this.calculate(data);
    const lastValue = ma[ma.length - 1];
    
    if (this.type === 'exponential') {
      // For exponential MA, use exponential smoothing forecast
      const forecast: number[] = [];
      let currentForecast = lastValue;
      
      for (let i = 0; i < periods; i++) {
        forecast.push(currentForecast);
        // For simplicity, assume the trend continues
        const trend = ma.length > 1 ? ma[ma.length - 1] - ma[ma.length - 2] : 0;
        currentForecast = currentForecast + trend * Math.pow(this.alpha!, i + 1);
      }
      
      return forecast;
    } else {
      // For simple/weighted MA, use last value
      return new Array(periods).fill(lastValue);
    }
  }
  
  private calculateSimpleMA(data: number[]): number[] {
    const result: number[] = [];
    
    for (let i = 0; i < data.length; i++) {
      if (i < this.window - 1) {
        result.push(data[i]);
        continue;
      }
      
      const slice = data.slice(i - this.window + 1, i + 1);
      const average = slice.reduce((sum, val) => sum + val, 0) / slice.length;
      result.push(average);
    }
    
    return result;
  }
  
  private calculateExponentialMA(data: number[]): number[] {
    const result: number[] = [];
    let ema = data[0];
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        result.push(data[0]);
        continue;
      }
      
      ema = this.alpha! * data[i] + (1 - this.alpha!) * ema;
      result.push(ema);
    }
    
    return result;
  }
  
  private calculateWeightedMA(data: number[]): number[] {
    const result: number[] = [];
    
    for (let i = 0; i < data.length; i++) {
      if (i < this.window - 1) {
        result.push(data[i]);
        continue;
      }
      
      const slice = data.slice(i - this.window + 1, i + 1);
      let weightedSum = 0;
      let weightSum = 0;
      
      slice.forEach((val, idx) => {
        const weight = idx + 1; // Linear weighting
        weightedSum += val * weight;
        weightSum += weight;
      });
      
      result.push(weightedSum / weightSum);
    }
    
    return result;
  }
}

// Seasonal Decomposition Model

export interface SeasonalDecomposition {
  trend: number[];
  seasonal: number[];
  residual: number[];
  seasonalityStrength: number;
  trendStrength: number;
}

export class SeasonalDecompositionModel {
  private period: number;
  private model: 'additive' | 'multiplicative';
  
  constructor(period: number, model: 'additive' | 'multiplicative' = 'additive') {
    this.period = period;
    this.model = model;
  }
  
  /**
   * Decompose time series into trend, seasonal, and residual components
   */
  public decompose(data: number[]): SeasonalDecomposition {
    if (data.length < 2 * this.period) {
      throw new Error('Data length must be at least twice the seasonal period');
    }
    
    // Calculate trend using centered moving average
    const trend = this.calculateTrend(data);
    
    // Calculate seasonal component
    const seasonal = this.calculateSeasonal(data, trend);
    
    // Calculate residual
    const residual = this.calculateResidual(data, trend, seasonal);
    
    // Calculate strength metrics
    const seasonalityStrength = this.calculateSeasonalityStrength(data, seasonal);
    const trendStrength = this.calculateTrendStrength(data, trend);
    
    return {
      trend,
      seasonal,
      residual,
      seasonalityStrength,
      trendStrength
    };
  }
  
  /**
   * Forecast using seasonal decomposition
   */
  public forecast(data: number[], periods: number): {
    forecast: number[];
    trendForecast: number[];
    seasonalForecast: number[];
  } {
    const decomposition = this.decompose(data);
    
    // Forecast trend using linear regression
    const trendData = decomposition.trend.filter(val => !isNaN(val));
    const trendX = trendData.map((_, i) => i);
    const linearModel = new LinearRegression();
    const trendResult = linearModel.train(trendX, trendData);
    
    const futureTrendX = Array.from({ length: periods }, (_, i) => trendData.length + i);
    const trendForecast = linearModel.predict(futureTrendX);
    
    // Forecast seasonal component by repeating the pattern
    const seasonalPattern = decomposition.seasonal.slice(-this.period);
    const seasonalForecast: number[] = [];
    
    for (let i = 0; i < periods; i++) {
      seasonalForecast.push(seasonalPattern[i % this.period]);
    }
    
    // Combine forecasts
    const forecast = trendForecast.map((trend, i) => {
      if (this.model === 'additive') {
        return trend + seasonalForecast[i];
      } else {
        return trend * (1 + seasonalForecast[i]);
      }
    });
    
    return {
      forecast,
      trendForecast,
      seasonalForecast
    };
  }
  
  private calculateTrend(data: number[]): number[] {
    const trend: number[] = new Array(data.length).fill(NaN);
    const halfPeriod = Math.floor(this.period / 2);
    
    for (let i = halfPeriod; i < data.length - halfPeriod; i++) {
      let sum = 0;
      let count = 0;
      
      // Centered moving average
      for (let j = -halfPeriod; j <= halfPeriod; j++) {
        if (i + j >= 0 && i + j < data.length) {
          sum += data[i + j];
          count++;
        }
      }
      
      trend[i] = count > 0 ? sum / count : NaN;
    }
    
    return trend;
  }
  
  private calculateSeasonal(data: number[], trend: number[]): number[] {
    const seasonal: number[] = new Array(data.length).fill(0);
    const seasonalAverages: number[] = new Array(this.period).fill(0);
    const seasonalCounts: number[] = new Array(this.period).fill(0);
    
    // Calculate seasonal averages
    for (let i = 0; i < data.length; i++) {
      if (!isNaN(trend[i])) {
        const seasonIndex = i % this.period;
        
        if (this.model === 'additive') {
          seasonalAverages[seasonIndex] += data[i] - trend[i];
        } else {
          seasonalAverages[seasonIndex] += data[i] / trend[i] - 1;
        }
        
        seasonalCounts[seasonIndex]++;
      }
    }
    
    // Average the seasonal components
    for (let i = 0; i < this.period; i++) {
      if (seasonalCounts[i] > 0) {
        seasonalAverages[i] /= seasonalCounts[i];
      }
    }
    
    // Ensure seasonal components sum to zero (additive) or average to 1 (multiplicative)
    if (this.model === 'additive') {
      const seasonalMean = seasonalAverages.reduce((sum, val) => sum + val, 0) / this.period;
      for (let i = 0; i < this.period; i++) {
        seasonalAverages[i] -= seasonalMean;
      }
    } else {
      const seasonalMean = seasonalAverages.reduce((sum, val) => sum + val, 0) / this.period;
      for (let i = 0; i < this.period; i++) {
        seasonalAverages[i] -= seasonalMean;
      }
    }
    
    // Assign seasonal components
    for (let i = 0; i < data.length; i++) {
      seasonal[i] = seasonalAverages[i % this.period];
    }
    
    return seasonal;
  }
  
  private calculateResidual(data: number[], trend: number[], seasonal: number[]): number[] {
    const residual: number[] = [];
    
    for (let i = 0; i < data.length; i++) {
      if (!isNaN(trend[i])) {
        if (this.model === 'additive') {
          residual.push(data[i] - trend[i] - seasonal[i]);
        } else {
          residual.push(data[i] / (trend[i] * (1 + seasonal[i])));
        }
      } else {
        residual.push(NaN);
      }
    }
    
    return residual;
  }
  
  private calculateSeasonalityStrength(data: number[], seasonal: number[]): number {
    const seasonalVariance = this.calculateVariance(seasonal);
    const residualVariance = this.calculateVariance(data.map((val, i) => val - seasonal[i]));
    
    return seasonalVariance / (seasonalVariance + residualVariance);
  }
  
  private calculateTrendStrength(data: number[], trend: number[]): number {
    const validTrend = trend.filter(val => !isNaN(val));
    const validData = data.slice(0, validTrend.length);
    
    const trendVariance = this.calculateVariance(validTrend);
    const residualVariance = this.calculateVariance(validData.map((val, i) => val - validTrend[i]));
    
    return trendVariance / (trendVariance + residualVariance);
  }
  
  private calculateVariance(data: number[]): number {
    const validData = data.filter(val => !isNaN(val));
    if (validData.length === 0) return 0;
    
    const mean = validData.reduce((sum, val) => sum + val, 0) / validData.length;
    return validData.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / validData.length;
  }
}

// Outlier Detection Model

export interface OutlierResult {
  outliers: Array<{
    index: number;
    value: number;
    score: number;
    method: string;
  }>;
  cleanData: number[];
  threshold: number;
}

export class OutlierDetector {
  private method: 'zscore' | 'iqr' | 'isolation' | 'lof';
  private threshold: number;
  
  constructor(method: 'zscore' | 'iqr' | 'isolation' | 'lof' = 'zscore', threshold: number = 2.5) {
    this.method = method;
    this.threshold = threshold;
  }
  
  /**
   * Detect outliers in data
   */
  public detect(data: number[]): OutlierResult {
    switch (this.method) {
      case 'zscore':
        return this.detectZScoreOutliers(data);
      case 'iqr':
        return this.detectIQROutliers(data);
      case 'isolation':
        return this.detectIsolationOutliers(data);
      case 'lof':
        return this.detectLOFOutliers(data);
      default:
        return this.detectZScoreOutliers(data);
    }
  }
  
  private detectZScoreOutliers(data: number[]): OutlierResult {
    const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
    const std = Math.sqrt(data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length);
    
    const outliers: Array<{index: number; value: number; score: number; method: string}> = [];
    const cleanData: number[] = [];
    
    data.forEach((value, index) => {
      const zScore = Math.abs((value - mean) / std);
      
      if (zScore > this.threshold) {
        outliers.push({
          index,
          value,
          score: zScore,
          method: 'zscore'
        });
      } else {
        cleanData.push(value);
      }
    });
    
    return {
      outliers,
      cleanData,
      threshold: this.threshold
    };
  }
  
  private detectIQROutliers(data: number[]): OutlierResult {
    const sorted = [...data].sort((a, b) => a - b);
    const q1Index = Math.floor(sorted.length * 0.25);
    const q3Index = Math.floor(sorted.length * 0.75);
    
    const q1 = sorted[q1Index];
    const q3 = sorted[q3Index];
    const iqr = q3 - q1;
    
    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;
    
    const outliers: Array<{index: number; value: number; score: number; method: string}> = [];
    const cleanData: number[] = [];
    
    data.forEach((value, index) => {
      if (value < lowerBound || value > upperBound) {
        const score = Math.max(
          Math.abs(value - lowerBound) / iqr,
          Math.abs(value - upperBound) / iqr
        );
        
        outliers.push({
          index,
          value,
          score,
          method: 'iqr'
        });
      } else {
        cleanData.push(value);
      }
    });
    
    return {
      outliers,
      cleanData,
      threshold: 1.5 // IQR multiplier
    };
  }
  
  private detectIsolationOutliers(data: number[]): OutlierResult {
    // Simplified isolation forest using distance-based approach
    const outliers: Array<{index: number; value: number; score: number; method: string}> = [];
    const cleanData: number[] = [];
    
    data.forEach((value, index) => {
      const distances = data.map(otherValue => Math.abs(value - otherValue));
      distances.sort((a, b) => a - b);
      
      // Use k-nearest neighbors distance (k=5)
      const k = Math.min(5, distances.length - 1);
      const avgDistance = distances.slice(1, k + 1).reduce((sum, d) => sum + d, 0) / k;
      
      // Normalize by data range
      const dataRange = Math.max(...data) - Math.min(...data);
      const isolationScore = avgDistance / dataRange;
      
      if (isolationScore > this.threshold / 10) { // Adjusted threshold for isolation
        outliers.push({
          index,
          value,
          score: isolationScore,
          method: 'isolation'
        });
      } else {
        cleanData.push(value);
      }
    });
    
    return {
      outliers,
      cleanData,
      threshold: this.threshold / 10
    };
  }
  
  private detectLOFOutliers(data: number[]): OutlierResult {
    // Simplified Local Outlier Factor
    const outliers: Array<{index: number; value: number; score: number; method: string}> = [];
    const cleanData: number[] = [];
    const k = Math.min(5, Math.floor(data.length / 3));
    
    data.forEach((value, index) => {
      // Calculate k-nearest neighbors
      const distances = data.map((otherValue, otherIndex) => ({
        distance: Math.abs(value - otherValue),
        index: otherIndex
      }));
      
      distances.sort((a, b) => a.distance - b.distance);
      const neighbors = distances.slice(1, k + 1); // Exclude self
      
      // Calculate local reachability density
      const reachabilityDistance = neighbors.reduce((sum, neighbor) => {
        return sum + Math.max(neighbor.distance, this.getKDistance(data, neighbor.index, k));
      }, 0) / neighbors.length;
      
      const lrd = 1 / (reachabilityDistance + 1e-10);
      
      // Calculate LOF
      let lofSum = 0;
      neighbors.forEach(neighbor => {
        const neighborLRD = this.calculateLRD(data, neighbor.index, k);
        lofSum += neighborLRD / lrd;
      });
      
      const lof = lofSum / neighbors.length;
      
      if (lof > this.threshold) {
        outliers.push({
          index,
          value,
          score: lof,
          method: 'lof'
        });
      } else {
        cleanData.push(value);
      }
    });
    
    return {
      outliers,
      cleanData,
      threshold: this.threshold
    };
  }
  
  private getKDistance(data: number[], pointIndex: number, k: number): number {
    const point = data[pointIndex];
    const distances = data.map(otherValue => Math.abs(point - otherValue));
    distances.sort((a, b) => a - b);
    return distances[k]; // k-th nearest neighbor distance
  }
  
  private calculateLRD(data: number[], pointIndex: number, k: number): number {
    const point = data[pointIndex];
    const distances = data.map((otherValue, otherIndex) => ({
      distance: Math.abs(point - otherValue),
      index: otherIndex
    }));
    
    distances.sort((a, b) => a.distance - b.distance);
    const neighbors = distances.slice(1, k + 1);
    
    const reachabilityDistance = neighbors.reduce((sum, neighbor) => {
      return sum + Math.max(neighbor.distance, this.getKDistance(data, neighbor.index, k));
    }, 0) / neighbors.length;
    
    return 1 / (reachabilityDistance + 1e-10);
  }
}

// Model Performance Metrics

export interface ModelMetrics {
  mse: number;           // Mean Squared Error
  rmse: number;          // Root Mean Squared Error
  mae: number;           // Mean Absolute Error
  mape: number;          // Mean Absolute Percentage Error
  r2: number;            // R-squared
  adjustedR2?: number;   // Adjusted R-squared
  aic?: number;          // Akaike Information Criterion
  bic?: number;          // Bayesian Information Criterion
}

export function calculateModelMetrics(
  actual: number[], 
  predicted: number[], 
  numberOfParameters?: number
): ModelMetrics {
  if (actual.length !== predicted.length) {
    throw new Error('Actual and predicted arrays must have the same length');
  }
  
  const n = actual.length;
  const errors = actual.map((a, i) => a - predicted[i]);
  const absErrors = errors.map(e => Math.abs(e));
  const squaredErrors = errors.map(e => e * e);
  const percentErrors = actual.map((a, i) => Math.abs((a - predicted[i]) / Math.max(a, 1e-10)) * 100);
  
  // Basic metrics
  const mse = squaredErrors.reduce((sum, e) => sum + e, 0) / n;
  const rmse = Math.sqrt(mse);
  const mae = absErrors.reduce((sum, e) => sum + e, 0) / n;
  const mape = percentErrors.reduce((sum, e) => sum + e, 0) / n;
  
  // R-squared
  const actualMean = actual.reduce((sum, a) => sum + a, 0) / n;
  const totalSumSquares = actual.reduce((sum, a) => sum + Math.pow(a - actualMean, 2), 0);
  const residualSumSquares = squaredErrors.reduce((sum, e) => sum + e, 0);
  const r2 = 1 - (residualSumSquares / totalSumSquares);
  
  const metrics: ModelMetrics = {
    mse,
    rmse,
    mae,
    mape,
    r2
  };
  
  // Optional metrics if parameters provided
  if (numberOfParameters !== undefined) {
    const adjustedR2 = 1 - ((1 - r2) * (n - 1)) / (n - numberOfParameters - 1);
    const aic = n * Math.log(mse) + 2 * numberOfParameters;
    const bic = n * Math.log(mse) + numberOfParameters * Math.log(n);
    
    metrics.adjustedR2 = adjustedR2;
    metrics.aic = aic;
    metrics.bic = bic;
  }
  
  return metrics;
}

// Cross-Validation Utilities

export interface CrossValidationResult {
  scores: number[];
  meanScore: number;
  stdScore: number;
  bestModel?: any;
}

export function timeSeriesCrossValidation(
  data: number[],
  modelFn: (trainData: number[]) => any,
  predictFn: (model: any, testSize: number) => number[],
  folds: number = 5,
  minTrainSize?: number
): CrossValidationResult {
  const scores: number[] = [];
  const n = data.length;
  const testSize = Math.floor(n / folds);
  const actualMinTrainSize = minTrainSize || Math.floor(n * 0.3);
  
  let bestScore = -Infinity;
  let bestModel: any = null;
  
  for (let i = 0; i < folds; i++) {
    const testStart = actualMinTrainSize + i * testSize;
    const testEnd = Math.min(testStart + testSize, n);
    
    if (testStart >= n) break;
    
    const trainData = data.slice(0, testStart);
    const testData = data.slice(testStart, testEnd);
    
    if (trainData.length < actualMinTrainSize || testData.length === 0) continue;
    
    try {
      const model = modelFn(trainData);
      const predictions = predictFn(model, testData.length);
      
      const metrics = calculateModelMetrics(testData, predictions);
      scores.push(metrics.r2);
      
      if (metrics.r2 > bestScore) {
        bestScore = metrics.r2;
        bestModel = model;
      }
    } catch (error) {
      console.warn(`Cross-validation fold ${i} failed:`, error);
      continue;
    }
  }
  
  const meanScore = scores.length > 0 ? scores.reduce((sum, s) => sum + s, 0) / scores.length : 0;
  const stdScore = scores.length > 1 ? 
    Math.sqrt(scores.reduce((sum, s) => sum + Math.pow(s - meanScore, 2), 0) / (scores.length - 1)) : 0;
  
  return {
    scores,
    meanScore,
    stdScore,
    bestModel
  };
}

// Export utility functions
export {
  calculateModelMetrics as modelMetrics,
  timeSeriesCrossValidation as crossValidate
};