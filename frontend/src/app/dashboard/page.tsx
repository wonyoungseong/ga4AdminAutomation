"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ServiceAccountDashboard } from "@/components/dashboard/service-account-dashboard";
import { apiClient } from "@/lib/api";
import { Users, Shield, Building2, FileText, Activity, TrendingUp, Key, BarChart3 } from "lucide-react";

interface DashboardStats {
  total_users: number;
  active_users: number;
  total_permissions: number;
  active_permissions: number;
  total_clients: number;
  total_audit_logs: number;
  recent_activities: Array<{
    id: number;
    action: string;
    user: string;
    timestamp: string;
  }>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      // API가 아직 구현되지 않았을 수 있으므로 목업 데이터 사용
      const mockStats: DashboardStats = {
        total_users: 156,
        active_users: 142,
        total_permissions: 89,
        active_permissions: 76,
        total_clients: 23,
        total_audit_logs: 1247,
        recent_activities: [
          {
            id: 1,
            action: "사용자 생성",
            user: "admin@example.com",
            timestamp: "2024-01-20T10:30:00Z"
          },
          {
            id: 2,
            action: "권한 수정",
            user: "manager@example.com",
            timestamp: "2024-01-20T09:15:00Z"
          },
          {
            id: 3,
            action: "클라이언트 삭제",
            user: "admin@example.com",
            timestamp: "2024-01-20T08:45:00Z"
          }
        ]
      };
      
      setStats(mockStats);
    } catch (error) {
      console.error("대시보드 통계 조회 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">대시보드</h1>
          <p className="text-muted-foreground">시스템 현황을 한눈에 확인하세요</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-8 bg-gray-200 rounded w-1/2"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">대시보드</h1>
        <p className="text-muted-foreground">시스템 현황을 한눈에 확인하세요</p>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            시스템 개요
          </TabsTrigger>
          <TabsTrigger value="service-accounts" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            서비스 계정
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            분석
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-6">

        {/* 통계 카드 */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 사용자</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              활성: {stats?.active_users || 0}명
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">권한</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_permissions || 0}</div>
            <p className="text-xs text-muted-foreground">
              활성: {stats?.active_permissions || 0}개
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">클라이언트</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_clients || 0}</div>
            <p className="text-xs text-muted-foreground">
              관리 중
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">감사 로그</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_audit_logs || 0}</div>
            <p className="text-xs text-muted-foreground">
              총 기록
            </p>
          </CardContent>
        </Card>
        </div>

        {/* 최근 활동 */}
        <div className="grid gap-4 md:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              최근 활동
            </CardTitle>
            <CardDescription>
              시스템에서 최근 발생한 주요 활동들입니다
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats?.recent_activities.map((activity) => (
                <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{activity.action}</p>
                    <p className="text-sm text-muted-foreground">{activity.user}</p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDate(activity.timestamp)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              시스템 상태
            </CardTitle>
            <CardDescription>
              현재 시스템 운영 상태입니다
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">시스템 상태</span>
                <span className="text-sm font-medium text-green-600">정상</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">API 응답 시간</span>
                <span className="text-sm font-medium">~150ms</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">활성 세션</span>
                <span className="text-sm font-medium">{stats?.active_users || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">데이터베이스</span>
                <span className="text-sm font-medium text-green-600">연결됨</span>
              </div>
            </div>
          </CardContent>
        </Card>
        </div>
        </TabsContent>
        
        <TabsContent value="service-accounts">
          <ServiceAccountDashboard />
        </TabsContent>
        
        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                GA4 Analytics 대시보드
              </CardTitle>
              <CardDescription>
                Google Analytics 4 데이터 분석 및 인사이트
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-muted-foreground">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">분석 대시보드 준비 중</p>
                <p className="text-sm">
                  GA4 데이터 분석 대시보드가 곧 제공될 예정입니다.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}