"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Key, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Activity,
  Building2,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Clock,
  Users,
  Shield,
  Database,
  Link,
  Unlink
} from "lucide-react";
import { apiClient } from "@/lib/api";

interface ServiceAccountStats {
  total_service_accounts: number;
  healthy_service_accounts: number;
  warning_service_accounts: number;
  error_service_accounts: number;
  total_properties: number;
  assigned_properties: number;
  unassigned_properties: number;
  sync_pending: number;
  recent_health_checks: number;
}

interface ServiceAccountSummary {
  id: number;
  name: string;
  email: string;
  client_name?: string;
  health_status: 'healthy' | 'warning' | 'error' | 'unknown';
  properties_count: number;
  permissions_sync_status: 'synced' | 'pending' | 'error' | 'never';
  last_health_check?: string;
  is_active: boolean;
}

interface GA4PropertySummary {
  id: number;
  property_id: string;
  display_name: string;
  service_account_name: string;
  client_name?: string;
  access_status: 'valid' | 'invalid' | 'unknown';
  permissions_granted: number;
  last_access_check?: string;
}

interface RecentActivity {
  id: string;
  type: 'service_account_created' | 'property_discovered' | 'health_check' | 'sync_completed' | 'client_assigned';
  title: string;
  description: string;
  timestamp: string;
  status: 'success' | 'warning' | 'error';
}

const HEALTH_STATUS_COLORS = {
  healthy: "bg-green-100 text-green-800",
  warning: "bg-yellow-100 text-yellow-800",
  error: "bg-red-100 text-red-800",
  unknown: "bg-gray-100 text-gray-800"
};

const ACCESS_STATUS_COLORS = {
  valid: "bg-green-100 text-green-800",
  invalid: "bg-red-100 text-red-800",
  unknown: "bg-gray-100 text-gray-800"
};

const SYNC_STATUS_COLORS = {
  synced: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  error: "bg-red-100 text-red-800",
  never: "bg-gray-100 text-gray-800"
};

export function ServiceAccountDashboard() {
  const [stats, setStats] = useState<ServiceAccountStats>({
    total_service_accounts: 0,
    healthy_service_accounts: 0,
    warning_service_accounts: 0,
    error_service_accounts: 0,
    total_properties: 0,
    assigned_properties: 0,
    unassigned_properties: 0,
    sync_pending: 0,
    recent_health_checks: 0
  });
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccountSummary[]>([]);
  const [properties, setProperties] = useState<GA4PropertySummary[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      
      // 서비스 계정 데이터 가져오기
      const serviceAccountsResponse = await apiClient.getServiceAccounts(1, 10);
      const serviceAccountsData = serviceAccountsResponse.service_accounts || [];
      setServiceAccounts(serviceAccountsData);
      
      // GA4 Property 데이터 가져오기
      const propertiesResponse = await apiClient.getGA4PropertiesManagement(1, 10);
      const propertiesData = propertiesResponse.properties || [];
      setProperties(propertiesData);
      
      // 통계 계산
      const calculatedStats: ServiceAccountStats = {
        total_service_accounts: serviceAccountsData.length,
        healthy_service_accounts: serviceAccountsData.filter(sa => sa.health_status === 'healthy').length,
        warning_service_accounts: serviceAccountsData.filter(sa => sa.health_status === 'warning').length,
        error_service_accounts: serviceAccountsData.filter(sa => sa.health_status === 'error').length,
        total_properties: propertiesData.length,
        assigned_properties: propertiesData.filter(p => p.client_name).length,
        unassigned_properties: propertiesData.filter(p => !p.client_name).length,
        sync_pending: serviceAccountsData.filter(sa => sa.permissions_sync_status === 'pending').length,
        recent_health_checks: serviceAccountsData.filter(sa => {
          if (!sa.last_health_check) return false;
          const checkTime = new Date(sa.last_health_check);
          const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
          return checkTime > oneDayAgo;
        }).length
      };
      setStats(calculatedStats);
      
      // 최근 활동 시뮬레이션 (실제 구현에서는 백엔드에서 가져와야 함)
      const mockRecentActivity: RecentActivity[] = [
        {
          id: '1',
          type: 'service_account_created',
          title: '새 서비스 계정 생성',
          description: 'Analytics Service Account가 생성되었습니다.',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          status: 'success'
        },
        {
          id: '2',
          type: 'property_discovered',
          title: 'GA4 Property 발견',
          description: '3개의 새 GA4 Property가 발견되었습니다.',
          timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          status: 'success'
        },
        {
          id: '3',
          type: 'health_check',
          title: '상태 확인 완료',
          description: '모든 서비스 계정의 상태가 확인되었습니다.',
          timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
          status: 'success'
        },
        {
          id: '4',
          type: 'sync_completed',
          title: '권한 동기화 실패',
          description: 'Marketing Service Account의 권한 동기화가 실패했습니다.',
          timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
          status: 'error'
        },
        {
          id: '5',
          type: 'client_assigned',
          title: '클라이언트 할당',
          description: 'GA4 Property가 ABC Company에 할당되었습니다.',
          timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
          status: 'success'
        }
      ];
      setRecentActivity(mockRecentActivity);
      
    } catch (error) {
      console.error("대시보드 데이터 조회 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getHealthPercentage = () => {
    if (stats.total_service_accounts === 0) return 0;
    return Math.round((stats.healthy_service_accounts / stats.total_service_accounts) * 100);
  };

  const getAssignmentPercentage = () => {
    if (stats.total_properties === 0) return 0;
    return Math.round((stats.assigned_properties / stats.total_properties) * 100);
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'service_account_created': return Key;
      case 'property_discovered': return BarChart3;
      case 'health_check': return Activity;
      case 'sync_completed': return RefreshCw;
      case 'client_assigned': return Link;
      default: return Activity;
    }
  };

  const getActivityStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 주요 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">서비스 계정</CardTitle>
            <Key className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_service_accounts}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <CheckCircle className="mr-1 h-3 w-3 text-green-600" />
              {stats.healthy_service_accounts}개 정상 ({getHealthPercentage()}%)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GA4 Property</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_properties}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              <Link className="mr-1 h-3 w-3 text-blue-600" />
              {stats.assigned_properties}개 할당됨 ({getAssignmentPercentage()}%)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">동기화 대기</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.sync_pending}</div>
            <p className="text-xs text-muted-foreground">
              권한 동기화 필요
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">24시간 상태확인</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.recent_health_checks}</div>
            <p className="text-xs text-muted-foreground">
              최근 확인된 계정
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 경고 및 알림 */}
      {(stats.error_service_accounts > 0 || stats.sync_pending > 0) && (
        <div className="space-y-4">
          {stats.error_service_accounts > 0 && (
            <Alert className="border-red-200 bg-red-50">
              <XCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                <strong>{stats.error_service_accounts}개의 서비스 계정</strong>에서 오류가 발생했습니다. 
                즉시 확인이 필요합니다.
              </AlertDescription>
            </Alert>
          )}
          {stats.sync_pending > 0 && (
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <AlertDescription className="text-yellow-800">
                <strong>{stats.sync_pending}개의 서비스 계정</strong>이 권한 동기화를 기다리고 있습니다.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* 서비스 계정 상태 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg">서비스 계정 상태</CardTitle>
              <CardDescription>최근 등록된 서비스 계정들</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={fetchDashboardData}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {serviceAccounts.slice(0, 5).map((account) => (
                <div key={account.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{account.name}</span>
                      <Badge className={HEALTH_STATUS_COLORS[account.health_status]} variant="outline">
                        {account.health_status}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {account.client_name || '할당되지 않음'} • {account.properties_count}개 Property
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className={SYNC_STATUS_COLORS[account.permissions_sync_status]} variant="outline">
                      {account.permissions_sync_status}
                    </Badge>
                  </div>
                </div>
              ))}
              {serviceAccounts.length === 0 && (
                <div className="text-center text-muted-foreground py-4">
                  등록된 서비스 계정이 없습니다.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* GA4 Property 상태 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">GA4 Property 상태</CardTitle>
            <CardDescription>최근 발견된 GA4 Property들</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {properties.slice(0, 5).map((property) => (
                <div key={property.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{property.display_name}</span>
                      <Badge className={ACCESS_STATUS_COLORS[property.access_status]} variant="outline">
                        {property.access_status}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {property.service_account_name} • {property.client_name || '할당되지 않음'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-muted-foreground">
                      {property.permissions_granted}개 권한
                    </div>
                  </div>
                </div>
              ))}
              {properties.length === 0 && (
                <div className="text-center text-muted-foreground py-4">
                  발견된 GA4 Property가 없습니다.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 최근 활동 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">최근 활동</CardTitle>
          <CardDescription>서비스 계정 및 GA4 Property 관련 최근 활동들</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivity.map((activity) => {
              const Icon = getActivityIcon(activity.type);
              return (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${getActivityStatusColor(activity.status)} bg-opacity-10`}>
                    <Icon className={`h-4 w-4 ${getActivityStatusColor(activity.status)}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">{activity.title}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(activity.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {activity.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 빠른 작업 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">빠른 작업</CardTitle>
          <CardDescription>자주 사용하는 관리 작업들</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" className="h-auto p-4 flex flex-col items-center gap-2">
              <Key className="h-6 w-6" />
              <span className="text-sm">서비스 계정 추가</span>
            </Button>
            <Button variant="outline" className="h-auto p-4 flex flex-col items-center gap-2">
              <Activity className="h-6 w-6" />
              <span className="text-sm">전체 상태 확인</span>
            </Button>
            <Button variant="outline" className="h-auto p-4 flex flex-col items-center gap-2">
              <RefreshCw className="h-6 w-6" />
              <span className="text-sm">권한 동기화</span>
            </Button>
            <Button variant="outline" className="h-auto p-4 flex flex-col items-center gap-2">
              <BarChart3 className="h-6 w-6" />
              <span className="text-sm">Property 발견</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}