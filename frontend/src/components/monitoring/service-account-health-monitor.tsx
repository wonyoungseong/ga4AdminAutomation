"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { 
  Activity, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Shield,
  Eye,
  EyeOff
} from "lucide-react";
import { typeSafeApiClient } from "@/lib/api-client";

interface HealthMetrics {
  service_account_id: number;
  service_account_name: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  response_time: number;
  last_check: string;
  error_rate: number;
  success_rate: number;
  properties_accessible: number;
  properties_total: number;
  quota_usage: number;
  quota_limit: number;
  recent_errors: string[];
}

interface HealthSummary {
  total_accounts: number;
  healthy_accounts: number;
  warning_accounts: number;
  error_accounts: number;
  average_response_time: number;
  overall_success_rate: number;
  total_properties: number;
  accessible_properties: number;
  quota_usage_percentage: number;
}

const STATUS_COLORS = {
  healthy: "bg-green-100 text-green-800 border-green-200",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
  error: "bg-red-100 text-red-800 border-red-200",
  unknown: "bg-gray-100 text-gray-800 border-gray-200"
};

const STATUS_ICONS = {
  healthy: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  unknown: Activity
};

export function ServiceAccountHealthMonitor() {
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics[]>([]);
  const [healthSummary, setHealthSummary] = useState<HealthSummary>({
    total_accounts: 0,
    healthy_accounts: 0,
    warning_accounts: 0,
    error_accounts: 0,
    average_response_time: 0,
    overall_success_rate: 0,
    total_properties: 0,
    accessible_properties: 0,
    quota_usage_percentage: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  const fetchHealthData = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // 서비스 계정 목록 가져오기
      const serviceAccountsResponse = await typeSafeApiClient.getServiceAccounts(1, 100);
      const serviceAccounts = serviceAccountsResponse.service_accounts || [];
      
      // 각 서비스 계정의 상태 확인 (모의 데이터)
      const mockHealthMetrics: HealthMetrics[] = serviceAccounts.map((account, index) => ({
        service_account_id: account.id,
        service_account_name: account.name,
        status: account.health_status as 'healthy' | 'warning' | 'error' | 'unknown',
        response_time: Math.random() * 1000 + 100, // 100-1100ms
        last_check: new Date().toISOString(),
        error_rate: Math.random() * 5, // 0-5%
        success_rate: 95 + Math.random() * 5, // 95-100%
        properties_accessible: account.properties_count - Math.floor(Math.random() * 2),
        properties_total: account.properties_count,
        quota_usage: Math.random() * 80 + 10, // 10-90%
        quota_limit: 100,
        recent_errors: account.health_status === 'error' ? [
          'API quota exceeded',
          'Authentication failed'
        ] : account.health_status === 'warning' ? [
          'Slow response time detected'
        ] : []
      }));
      
      setHealthMetrics(mockHealthMetrics);
      
      // 요약 통계 계산
      const summary: HealthSummary = {
        total_accounts: mockHealthMetrics.length,
        healthy_accounts: mockHealthMetrics.filter(m => m.status === 'healthy').length,
        warning_accounts: mockHealthMetrics.filter(m => m.status === 'warning').length,
        error_accounts: mockHealthMetrics.filter(m => m.status === 'error').length,
        average_response_time: mockHealthMetrics.reduce((sum, m) => sum + m.response_time, 0) / mockHealthMetrics.length,
        overall_success_rate: mockHealthMetrics.reduce((sum, m) => sum + m.success_rate, 0) / mockHealthMetrics.length,
        total_properties: mockHealthMetrics.reduce((sum, m) => sum + m.properties_total, 0),
        accessible_properties: mockHealthMetrics.reduce((sum, m) => sum + m.properties_accessible, 0),
        quota_usage_percentage: mockHealthMetrics.reduce((sum, m) => sum + m.quota_usage, 0) / mockHealthMetrics.length
      };
      
      setHealthSummary(summary);
      setLastUpdate(new Date());
      
    } catch (error) {
      console.error("상태 데이터 조회 실패:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const toggleRealTimeMonitoring = () => {
    if (isRealTimeEnabled) {
      // 실시간 모니터링 비활성화
      if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        setAutoRefreshInterval(null);
      }
      setIsRealTimeEnabled(false);
    } else {
      // 실시간 모니터링 활성화 (30초마다 업데이트)
      const interval = setInterval(fetchHealthData, 30000);
      setAutoRefreshInterval(interval);
      setIsRealTimeEnabled(true);
    }
  };

  const handleManualRefresh = async () => {
    await fetchHealthData();
  };

  const performHealthCheck = async (serviceAccountId: number) => {
    try {
      await typeSafeApiClient.testServiceAccountHealth(serviceAccountId);
      await fetchHealthData();
    } catch (error) {
      console.error("상태 확인 실패:", error);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    return () => {
      if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
      }
    };
  }, [fetchHealthData]);

  const formatResponseTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getOverallHealthStatus = () => {
    const errorPercentage = (healthSummary.error_accounts / healthSummary.total_accounts) * 100;
    const warningPercentage = (healthSummary.warning_accounts / healthSummary.total_accounts) * 100;
    
    if (errorPercentage > 10) return { status: 'critical', color: 'text-red-600', icon: XCircle };
    if (errorPercentage > 0 || warningPercentage > 20) return { status: 'warning', color: 'text-yellow-600', icon: AlertTriangle };
    return { status: 'healthy', color: 'text-green-600', icon: CheckCircle };
  };

  const overallHealth = getOverallHealthStatus();

  if (isLoading && healthMetrics.length === 0) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 및 제어 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">서비스 계정 상태 모니터링</h2>
          <p className="text-muted-foreground">
            실시간으로 서비스 계정의 상태를 모니터링합니다
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={toggleRealTimeMonitoring}
            className={isRealTimeEnabled ? "bg-green-50 border-green-200" : ""}
          >
            {isRealTimeEnabled ? (
              <>
                <EyeOff className="h-4 w-4 mr-2" />
                실시간 모니터링 중지
              </>
            ) : (
              <>
                <Eye className="h-4 w-4 mr-2" />
                실시간 모니터링 시작
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleManualRefresh}
            disabled={isLoading}
          >
            {isLoading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </>
            )}
          </Button>
        </div>
      </div>

      {/* 전체 상태 요약 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 상태</CardTitle>
            <overallHealth.icon className={`h-4 w-4 ${overallHealth.color}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${overallHealth.color}`}>
              {overallHealth.status.toUpperCase()}
            </div>
            <p className="text-xs text-muted-foreground">
              {healthSummary.healthy_accounts}/{healthSummary.total_accounts} 정상
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 응답 시간</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatResponseTime(healthSummary.average_response_time)}
            </div>
            <p className="text-xs text-muted-foreground">
              API 응답 속도
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">성공률</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {healthSummary.overall_success_rate.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              전체 요청 성공률
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Property 접근</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {healthSummary.accessible_properties}/{healthSummary.total_properties}
            </div>
            <p className="text-xs text-muted-foreground">
              접근 가능한 Property
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">할당량 사용률</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {healthSummary.quota_usage_percentage.toFixed(0)}%
            </div>
            <div className="mt-2">
              <Progress value={healthSummary.quota_usage_percentage} className="h-2" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 실시간 상태 표시 */}
      {isRealTimeEnabled && (
        <Alert className="border-green-200 bg-green-50">
          <Activity className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            <strong>실시간 모니터링 활성화</strong> - 30초마다 자동으로 상태를 업데이트합니다.
            {lastUpdate && (
              <span className="ml-2 text-sm">
                마지막 업데이트: {formatDate(lastUpdate.toISOString())}
              </span>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* 서비스 계정별 상세 상태 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            서비스 계정별 상태
          </CardTitle>
          <CardDescription>
            각 서비스 계정의 상세한 상태 정보를 확인하세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {healthMetrics.map((metric) => {
              const StatusIcon = STATUS_ICONS[metric.status];
              
              return (
                <div key={metric.service_account_id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <StatusIcon className={`h-5 w-5 ${getStatusColor(metric.status)}`} />
                      <div>
                        <h3 className="font-semibold">{metric.service_account_name}</h3>
                        <Badge className={STATUS_COLORS[metric.status]} variant="outline">
                          {metric.status.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-right text-sm text-muted-foreground">
                      <div>마지막 확인: {formatDate(metric.last_check)}</div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => performHealthCheck(metric.service_account_id)}
                        className="mt-2"
                      >
                        <Activity className="h-3 w-3 mr-1" />
                        상태 확인
                      </Button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="font-medium">응답 시간</span>
                      <div className={`font-mono ${metric.response_time > 1000 ? 'text-red-600' : metric.response_time > 500 ? 'text-yellow-600' : 'text-green-600'}`}>
                        {formatResponseTime(metric.response_time)}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium">성공률</span>
                      <div className={`font-mono ${metric.success_rate < 95 ? 'text-red-600' : metric.success_rate < 98 ? 'text-yellow-600' : 'text-green-600'}`}>
                        {metric.success_rate.toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <span className="font-medium">Property 접근</span>
                      <div className="font-mono">
                        {metric.properties_accessible}/{metric.properties_total}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium">할당량 사용</span>
                      <div className={`font-mono ${metric.quota_usage > 80 ? 'text-red-600' : metric.quota_usage > 60 ? 'text-yellow-600' : 'text-green-600'}`}>
                        {metric.quota_usage.toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  
                  {metric.recent_errors.length > 0 && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                      <div className="font-medium text-red-800 text-sm mb-2">최근 오류:</div>
                      <ul className="text-sm text-red-700 space-y-1">
                        {metric.recent_errors.map((error, index) => (
                          <li key={index} className="flex items-center gap-2">
                            <XCircle className="h-3 w-3" />
                            {error}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
            
            {healthMetrics.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                모니터링할 서비스 계정이 없습니다.
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}