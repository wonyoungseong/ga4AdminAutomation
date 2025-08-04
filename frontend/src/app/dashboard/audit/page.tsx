"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, FileText, Activity, Shield, Users, Calendar } from "lucide-react";
import { apiClient } from "@/lib/api";

interface AuditLog {
  id: number;
  action: string;
  user_email: string;
  user_name: string;
  target_type: string;
  target_id?: string;
  target_name?: string;
  ip_address: string;
  user_agent: string;
  timestamp: string;
  details?: string;
  status: "success" | "failure" | "warning";
}

export default function AuditPage() {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [dateFilter, setDateFilter] = useState("all");
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetchAuditLogs();
    fetchAuditStats();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [auditLogs, searchTerm, actionFilter, statusFilter, dateFilter]);

  // 필터가 변경될 때 API를 다시 호출
  useEffect(() => {
    if (actionFilter !== "all" || statusFilter !== "all") {
      fetchAuditLogs();
    }
  }, [actionFilter, statusFilter]);

  const fetchAuditLogs = async () => {
    try {
      // 실제 API 호출 - 필터 적용
      const filters: any = {};
      if (actionFilter !== "all") filters.action = actionFilter;
      if (statusFilter !== "all") filters.status = statusFilter;
      
      const response = await apiClient.getAuditLogs(1, 100, filters);
      setAuditLogs(response || []);
    } catch (error) {
      console.error("감사 로그 조회 실패:", error);
      setAuditLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAuditStats = async () => {
    try {
      const response = await apiClient.getAuditLogStats();
      setStats(response);
    } catch (error) {
      console.error("감사 로그 통계 조회 실패:", error);
      setStats(null);
    }
  };

  const applyFilters = () => {
    let filtered = auditLogs;

    // 검색 필터
    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.user_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.target_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // 액션 필터
    if (actionFilter !== "all") {
      filtered = filtered.filter(log => log.action === actionFilter);
    }

    // 상태 필터
    if (statusFilter !== "all") {
      filtered = filtered.filter(log => log.status === statusFilter);
    }

    // 날짜 필터
    if (dateFilter !== "all") {
      const now = new Date();
      const filterDate = new Date();
      
      switch (dateFilter) {
        case "today":
          filterDate.setDate(now.getDate() - 1);
          break;
        case "week":
          filterDate.setDate(now.getDate() - 7);
          break;
        case "month":
          filterDate.setMonth(now.getMonth() - 1);
          break;
      }
      
      filtered = filtered.filter(log => new Date(log.timestamp) >= filterDate);
    }

    setFilteredLogs(filtered);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case "login":
      case "logout":
        return <Users className="h-4 w-4" />;
      case "create_user":
      case "update_user":
      case "delete_user":
        return <Users className="h-4 w-4" />;
      case "approve_permission":
      case "reject_permission":
      case "create_permission":
      case "update_permission":
      case "delete_permission":
        return <Shield className="h-4 w-4" />;
      case "create_client":
      case "update_client":
      case "delete_client":
        return <Activity className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getActionLabel = (action: string) => {
    const actionLabels: Record<string, string> = {
      login: "로그인",
      logout: "로그아웃",
      create_user: "사용자 생성",
      update_user: "사용자 수정",
      delete_user: "사용자 삭제",
      create_permission: "권한 생성",
      update_permission: "권한 수정",
      delete_permission: "권한 삭제",
      approve_permission: "권한 승인",
      reject_permission: "권한 거부",
      create_client: "클라이언트 생성",
      update_client: "클라이언트 수정",
      delete_client: "클라이언트 삭제",
    };
    return actionLabels[action] || action;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-100 text-green-800";
      case "failure":
        return "bg-red-100 text-red-800";
      case "warning":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "success":
        return "성공";
      case "failure":
        return "실패";
      case "warning":
        return "경고";
      default:
        return status;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">감사 로그</h1>
          <p className="text-muted-foreground">시스템 활동 로그를 확인합니다</p>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-12 bg-gray-200 rounded"></div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">감사 로그</h1>
        <p className="text-muted-foreground">시스템 활동 로그를 확인합니다</p>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 로그</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_logs || auditLogs.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">성공</CardTitle>
            <Activity className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.success_logs || auditLogs.filter(log => log.status === "success").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">실패</CardTitle>
            <Shield className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.failure_logs || auditLogs.filter(log => log.status === "failure").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">경고</CardTitle>
            <Calendar className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.warning_logs || auditLogs.filter(log => log.status === "warning").length}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>활동 로그</CardTitle>
          <CardDescription>
            총 {auditLogs.length}개의 활동 기록이 있습니다. (필터링된 결과: {filteredLogs.length}개)
          </CardDescription>
          
          {/* 필터 영역 */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="로그 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-xs">액션</Label>
              <Select value={actionFilter} onValueChange={setActionFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="login">로그인</SelectItem>
                  <SelectItem value="create_user">사용자 생성</SelectItem>
                  <SelectItem value="update_user">사용자 수정</SelectItem>
                  <SelectItem value="approve_permission">권한 승인</SelectItem>
                  <SelectItem value="create_client">클라이언트 생성</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-xs">상태</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="success">성공</SelectItem>
                  <SelectItem value="failure">실패</SelectItem>
                  <SelectItem value="warning">경고</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-xs">기간</Label>
              <Select value={dateFilter} onValueChange={setDateFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="today">오늘</SelectItem>
                  <SelectItem value="week">7일</SelectItem>
                  <SelectItem value="month">30일</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>시간</TableHead>
                <TableHead>사용자</TableHead>
                <TableHead>액션</TableHead>
                <TableHead>대상</TableHead>
                <TableHead>상태</TableHead>
                <TableHead>IP 주소</TableHead>
                <TableHead>세부사항</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-mono text-sm">
                    {formatDate(log.timestamp)}
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{log.user_name}</div>
                      <div className="text-sm text-muted-foreground">{log.user_email}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getActionIcon(log.action)}
                      <span>{getActionLabel(log.action)}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {log.target_name ? (
                      <div>
                        <div className="font-medium">{log.target_name}</div>
                        <div className="text-sm text-muted-foreground">{log.target_type}</div>
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(log.status)}>
                      {getStatusLabel(log.status)}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {log.ip_address}
                  </TableCell>
                  <TableCell>
                    <div className="max-w-xs truncate text-sm text-muted-foreground">
                      {log.details || "-"}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          
          {filteredLogs.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              필터 조건에 맞는 로그가 없습니다.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}