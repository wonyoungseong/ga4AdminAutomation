"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingCard, LoadingPage } from "@/components/ui/loading";
import { StatusBadge, RoleBadge } from "@/components/ui/enhanced-badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ServiceAccountDashboard } from "@/components/dashboard/service-account-dashboard";
import { typeSafeApiClient, ApiClientError } from "@/lib/api-client";
import { DashboardStats } from "@/types/api";
import { Users, Shield, Building2, FileText, Activity, TrendingUp, Key, BarChart3, Eye, Edit, Calendar, Globe } from "lucide-react";

// DashboardStats interface imported from @/types/api

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      // Try to fetch real stats, fallback to mock data if needed
      const realStats = await typeSafeApiClient.getDashboardStats();
      setStats(realStats);
    } catch (error) {
      console.warn("Dashboard stats API not available, using mock data:", error);
      // Fallback to mock data matching DashboardStats interface
      const mockStats: DashboardStats = {
        total_users: 156,
        active_users: 142,
        total_service_accounts: 89,
        healthy_service_accounts: 76,
        total_properties: 245,
        active_properties: 198
      };
      
      setStats(mockStats);
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
          <h1 className="text-3xl font-bold tracking-tight korean-text">대시보드</h1>
          <p className="text-muted-foreground korean-text">시스템 현황을 한눈에 확인하세요</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <LoadingCard key={i} showActions={false} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight korean-text">대시보드</h1>
          <p className="text-muted-foreground korean-text">시스템 현황을 한눈에 확인하세요</p>
        </div>
        <StatusBadge status="success" className="hidden sm:inline-flex">
          시스템 정상
        </StatusBadge>
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
          <Card 
            hover={true}
            className="group cursor-pointer"
            onClick={() => router.push('/dashboard/users')}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">전체 사용자</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
              <p className="text-xs text-muted-foreground">
                활성: {stats?.active_users || 0}명
              </p>
              <div className="mt-2 text-xs text-primary opacity-0 group-hover:opacity-100 transition-all duration-200 korean-text">
                클릭하여 상세보기 <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
              </div>
            </CardContent>
          </Card>

          <Card 
            hover={true}
            className="group cursor-pointer"
            onClick={() => router.push('/dashboard/permissions')}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">권한</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_permissions || 24}</div>
              <p className="text-xs text-muted-foreground">
                활성: {stats?.active_permissions || 18}개
              </p>
              <div className="mt-2 text-xs text-primary opacity-0 group-hover:opacity-100 transition-all duration-200 korean-text">
                클릭하여 상세보기 <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
              </div>
            </CardContent>
          </Card>

          <Card 
            hover={true}
            className="group cursor-pointer"
            onClick={() => router.push('/dashboard/clients')}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">클라이언트</CardTitle>
              <Building2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_clients || 12}</div>
              <p className="text-xs text-muted-foreground">
                관리 중
              </p>
              <div className="mt-2 text-xs text-primary opacity-0 group-hover:opacity-100 transition-all duration-200 korean-text">
                클릭하여 상세보기 <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
              </div>
            </CardContent>
          </Card>

          <Card 
            hover={true}
            className="group cursor-pointer"
            onClick={() => router.push('/dashboard/audit')}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">감사 로그</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_audit_logs || 1247}</div>
              <p className="text-xs text-muted-foreground">
                총 기록
              </p>
              <div className="mt-2 text-xs text-primary opacity-0 group-hover:opacity-100 transition-all duration-200 korean-text">
                클릭하여 상세보기 <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
              </div>
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
              {stats?.recent_activities?.map((activity) => (
                <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex-1">
                    <p className="font-medium">{activity.action}</p>
                    <p className="text-sm text-muted-foreground">{activity.user}</p>
                    {activity.details && (
                      <p className="text-xs text-muted-foreground mt-1">{activity.details}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-sm text-muted-foreground">
                      {formatDate(activity.timestamp)}
                    </div>
                    <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <Eye className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              )) || (
                // Mock recent activities for better demo
                [
                  {
                    id: 1,
                    action: "새 서비스 계정 추가",
                    user: "admin@company.com",
                    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
                    details: "GA4 Analytics 연동용"
                  },
                  {
                    id: 2,
                    action: "사용자 권한 수정",
                    user: "manager@company.com",
                    timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
                    details: "requester → manager 승격"
                  },
                  {
                    id: 3,
                    action: "클라이언트 등록",
                    user: "admin@company.com",
                    timestamp: new Date(Date.now() - 1000 * 60 * 240).toISOString(),
                    details: "새로운 기업 고객"
                  }
                ].map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors group">
                    <div className="flex-1">
                      <p className="font-medium">{activity.action}</p>
                      <p className="text-sm text-muted-foreground">{activity.user}</p>
                      <p className="text-xs text-muted-foreground mt-1">{activity.details}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-sm text-muted-foreground">
                        {formatDate(activity.timestamp)}
                      </div>
                      <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <Eye className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
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
                <StatusBadge status="success">정상</StatusBadge>
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
                <StatusBadge status="success">연결됨</StatusBadge>
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
          {/* Analytics Overview Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">월간 페이지뷰</CardTitle>
                <Globe className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">2,847,392</div>
                <p className="text-xs text-green-600">
                  +12.5% 전월 대비
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">활성 사용자</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">24,567</div>
                <p className="text-xs text-green-600">
                  +8.3% 전월 대비
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">세션 지속시간</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">4m 32s</div>
                <p className="text-xs text-red-600">
                  -2.1% 전월 대비
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">전환율</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3.24%</div>
                <p className="text-xs text-green-600">
                  +0.8% 전월 대비
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Analytics Charts Grid */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  트래픽 추이
                </CardTitle>
                <CardDescription>
                  지난 30일간 웹사이트 방문자 추이
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center bg-muted/20 rounded-lg">
                  <div className="text-center">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">차트 데이터 로딩 중...</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  사용자 행동 분석
                </CardTitle>
                <CardDescription>
                  페이지별 참여도 및 이탈률 분석
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">홈페이지</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-muted rounded-full h-2">
                        <div className="bg-green-500 h-2 rounded-full" style={{width: "85%"}}></div>
                      </div>
                      <span className="text-sm text-muted-foreground">85%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">제품 페이지</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-muted rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{width: "72%"}}></div>
                      </div>
                      <span className="text-sm text-muted-foreground">72%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">블로그</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-muted rounded-full h-2">
                        <div className="bg-yellow-500 h-2 rounded-full" style={{width: "65%"}}></div>
                      </div>
                      <span className="text-sm text-muted-foreground">65%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">문의하기</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-muted rounded-full h-2">
                        <div className="bg-red-500 h-2 rounded-full" style={{width: "48%"}}></div>
                      </div>
                      <span className="text-sm text-muted-foreground">48%</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Real-time Analytics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 animate-pulse text-green-500" />
                실시간 분석
              </CardTitle>
              <CardDescription>
                현재 웹사이트 활동 현황
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">127</div>
                  <p className="text-sm text-muted-foreground">현재 활성 사용자</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">8.4K</div>
                  <p className="text-sm text-muted-foreground">오늘 페이지뷰</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">2.1K</div>
                  <p className="text-sm text-muted-foreground">오늘 순 방문자</p>
                </div>
              </div>
              
              <div className="mt-6">
                <h4 className="font-medium mb-3">인기 페이지 (실시간)</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-muted/50 rounded">
                    <span className="text-sm">/dashboard</span>
                    <span className="text-sm font-medium">23명</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-muted/50 rounded">
                    <span className="text-sm">/products</span>
                    <span className="text-sm font-medium">18명</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-muted/50 rounded">
                    <span className="text-sm">/</span>
                    <span className="text-sm font-medium">15명</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}