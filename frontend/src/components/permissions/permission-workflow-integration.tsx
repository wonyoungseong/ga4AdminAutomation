"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Shield,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Plus,
  RefreshCw,
  Eye,
  Settings,
  BarChart3,
  Key
} from "lucide-react";
import { typeSafeApiClient } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";

interface PermissionRequest {
  id: number;
  requester_email: string;
  requester_name: string;
  property_id: string;
  property_name: string;
  service_account_name: string;
  permission_type: 'viewer' | 'analyst' | 'marketer' | 'editor' | 'administrator';
  request_reason: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
  reviewer_comments?: string;
  expires_at?: string;
}

interface GA4Property {
  id: number;
  property_id: string;
  display_name: string;
  service_account_name: string;
  client_name?: string;
  is_accessible: boolean;
}

interface ServiceAccount {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  health_status: string;
  properties_count: number;
}

const STATUS_COLORS = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  expired: "bg-gray-100 text-gray-800"
};

const STATUS_ICONS = {
  pending: Clock,
  approved: CheckCircle,
  rejected: XCircle,
  expired: AlertTriangle
};

const PERMISSION_TYPES = {
  viewer: "Viewer (조회)",
  analyst: "Analyst (분석)",
  marketer: "Marketer (마케팅)",
  editor: "Editor (편집)",
  administrator: "Administrator (관리자)"
};

export function PermissionWorkflowIntegration() {
  const { user } = useAuth();
  const [permissionRequests, setPermissionRequests] = useState<PermissionRequest[]>([]);
  const [properties, setProperties] = useState<GA4Property[]>([]);
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isReviewDialogOpen, setIsReviewDialogOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<PermissionRequest | null>(null);
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve');
  const [reviewComments, setReviewComments] = useState('');

  const [newRequest, setNewRequest] = useState({
    property_id: '',
    permission_type: 'viewer' as const,
    request_reason: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      
      // Mock permission requests (실제 구현에서는 API에서 가져와야 함)
      const mockRequests: PermissionRequest[] = [
        {
          id: 1,
          requester_email: 'john.doe@example.com',
          requester_name: 'John Doe',
          property_id: 'GA_PROPERTY_123456789',
          property_name: 'Example Website - GA4',
          service_account_name: 'Analytics Service Account',
          permission_type: 'analyst',
          request_reason: '마케팅 캠페인 성과 분석을 위해 GA4 데이터 접근이 필요합니다.',
          status: 'pending',
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
        },
        {
          id: 2,
          requester_email: 'jane.smith@example.com',
          requester_name: 'Jane Smith',
          property_id: 'GA_PROPERTY_987654321',
          property_name: 'Mobile App - GA4',
          service_account_name: 'Mobile Analytics Account',
          permission_type: 'viewer',
          request_reason: 'UX 개선을 위한 사용자 행동 데이터 분석이 필요합니다.',
          status: 'approved',
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
          reviewed_at: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
          reviewed_by: 'admin@example.com',
          reviewer_comments: '승인되었습니다. UX 팀의 데이터 분석 목적으로 적절합니다.'
        },
        {
          id: 3,
          requester_email: 'bob.wilson@example.com',
          requester_name: 'Bob Wilson',
          property_id: 'GA_PROPERTY_555666777',
          property_name: 'E-commerce Site - GA4',
          service_account_name: 'E-commerce Analytics',
          permission_type: 'editor',
          request_reason: '컨버전 추적 설정 및 목표 구성을 위해 편집 권한이 필요합니다.',
          status: 'rejected',
          created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
          reviewed_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          reviewed_by: 'admin@example.com',
          reviewer_comments: '현재 프로젝트 범위에서 편집 권한은 필요하지 않습니다. Analyst 권한으로 재신청해주세요.'
        }
      ];
      
      setPermissionRequests(mockRequests);
      
      // GA4 Properties 가져오기
      const propertiesResponse = await typeSafeApiClient.getGA4PropertiesManagement(1, 100);
      setProperties(propertiesResponse.properties || []);
      
      // Service Accounts 가져오기
      const serviceAccountsResponse = await typeSafeApiClient.getServiceAccounts(1, 100);
      setServiceAccounts(serviceAccountsResponse.service_accounts || []);
      
    } catch (error) {
      console.error("권한 요청 데이터 조회 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateRequest = async () => {
    if (!newRequest.property_id || !newRequest.request_reason.trim()) {
      return;
    }

    try {
      // 실제 구현에서는 API 호출
      const selectedProperty = properties.find(p => p.property_id === newRequest.property_id);
      
      const mockNewRequest: PermissionRequest = {
        id: Date.now(),
        requester_email: user?.email || '',
        requester_name: user?.name || '',
        property_id: newRequest.property_id,
        property_name: selectedProperty?.display_name || 'Unknown Property',
        service_account_name: selectedProperty?.service_account_name || 'Unknown Service Account',
        permission_type: newRequest.permission_type,
        request_reason: newRequest.request_reason,
        status: 'pending',
        created_at: new Date().toISOString(),
      };
      
      setPermissionRequests(prev => [mockNewRequest, ...prev]);
      
      // 폼 초기화
      setNewRequest({
        property_id: '',
        permission_type: 'viewer',
        request_reason: ''
      });
      setIsCreateDialogOpen(false);
      
    } catch (error) {
      console.error("권한 요청 생성 실패:", error);
    }
  };

  const handleReviewRequest = async () => {
    if (!selectedRequest) return;

    try {
      // 실제 구현에서는 API 호출
      const updatedRequest: PermissionRequest = {
        ...selectedRequest,
        status: reviewAction === 'approve' ? 'approved' : 'rejected',
        reviewed_at: new Date().toISOString(),
        reviewed_by: user?.email || '',
        reviewer_comments: reviewComments.trim() || undefined
      };
      
      setPermissionRequests(prev => 
        prev.map(req => req.id === selectedRequest.id ? updatedRequest : req)
      );
      
      setIsReviewDialogOpen(false);
      setSelectedRequest(null);
      setReviewComments('');
      setReviewAction('approve');
      
    } catch (error) {
      console.error("권한 요청 검토 실패:", error);
    }
  };

  const openReviewDialog = (request: PermissionRequest, action: 'approve' | 'reject') => {
    setSelectedRequest(request);
    setReviewAction(action);
    setIsReviewDialogOpen(true);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '검토 대기';
      case 'approved': return '승인됨';
      case 'rejected': return '거부됨';
      case 'expired': return '만료됨';
      default: return '알 수 없음';
    }
  };

  const canReviewRequests = user?.role === 'super_admin' || user?.role === 'admin';
  const canCreateRequests = true; // 모든 사용자가 요청 생성 가능

  if (isLoading) {
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">권한 요청 관리</h2>
          <p className="text-muted-foreground">
            GA4 Property 접근 권한 요청을 관리하고 승인합니다
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
          {canCreateRequests && (
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  권한 요청
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>새 권한 요청</DialogTitle>
                  <DialogDescription>
                    GA4 Property에 대한 접근 권한을 요청합니다.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="property">GA4 Property</Label>
                    <Select value={newRequest.property_id} onValueChange={(value) => 
                      setNewRequest({ ...newRequest, property_id: value })
                    }>
                      <SelectTrigger>
                        <SelectValue placeholder="Property를 선택하세요" />
                      </SelectTrigger>
                      <SelectContent>
                        {properties.map((property) => (
                          <SelectItem key={property.id} value={property.property_id}>
                            <div className="flex items-center gap-2">
                              <BarChart3 className="h-4 w-4" />
                              <div>
                                <div className="font-medium">{property.display_name}</div>
                                <div className="text-xs text-muted-foreground">
                                  {property.property_id} • {property.service_account_name}
                                </div>
                              </div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="permission_type">요청 권한</Label>
                    <Select value={newRequest.permission_type} onValueChange={(value: string) =>
                      setNewRequest({ ...newRequest, permission_type: value })
                    }>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(PERMISSION_TYPES).map(([key, label]) => (
                          <SelectItem key={key} value={key}>
                            {label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="reason">요청 사유</Label>
                    <Textarea
                      id="reason"
                      value={newRequest.request_reason}
                      onChange={(e) => setNewRequest({ ...newRequest, request_reason: e.target.value })}
                      placeholder="권한이 필요한 이유를 상세히 작성해주세요..."
                      rows={4}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    취소
                  </Button>
                  <Button 
                    onClick={handleCreateRequest}
                    disabled={!newRequest.property_id || !newRequest.request_reason.trim()}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    요청 생성
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 요청</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{permissionRequests.length}</div>
            <p className="text-xs text-muted-foreground">총 권한 요청</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">검토 대기</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {permissionRequests.filter(r => r.status === 'pending').length}
            </div>
            <p className="text-xs text-muted-foreground">승인 대기 중</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">승인됨</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {permissionRequests.filter(r => r.status === 'approved').length}
            </div>
            <p className="text-xs text-muted-foreground">승인된 요청</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">거부됨</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {permissionRequests.filter(r => r.status === 'rejected').length}
            </div>
            <p className="text-xs text-muted-foreground">거부된 요청</p>
          </CardContent>
        </Card>
      </div>

      {/* 권한 요청 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>권한 요청 목록</CardTitle>
          <CardDescription>
            사용자들의 GA4 Property 접근 권한 요청을 확인하고 관리하세요.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {permissionRequests.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>요청자</TableHead>
                  <TableHead>Property</TableHead>
                  <TableHead>권한 유형</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>요청일</TableHead>
                  {canReviewRequests && <TableHead>작업</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {permissionRequests.map((request) => {
                  const StatusIcon = STATUS_ICONS[request.status];
                  
                  return (
                    <TableRow key={request.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{request.requester_name}</div>
                          <div className="text-sm text-muted-foreground">{request.requester_email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{request.property_name}</div>
                          <div className="text-sm text-muted-foreground">
                            {request.property_id} • {request.service_account_name}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {PERMISSION_TYPES[request.permission_type]}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={STATUS_COLORS[request.status]} variant="outline">
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {getStatusText(request.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {formatDate(request.created_at)}
                        </div>
                        {request.reviewed_at && (
                          <div className="text-xs text-muted-foreground">
                            검토: {formatDate(request.reviewed_at)}
                          </div>
                        )}
                      </TableCell>
                      {canReviewRequests && (
                        <TableCell>
                          <div className="flex gap-1">
                            {request.status === 'pending' && (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => openReviewDialog(request, 'approve')}
                                  className="text-green-600 hover:text-green-700"
                                >
                                  <CheckCircle className="w-3 h-3" />
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => openReviewDialog(request, 'reject')}
                                  className="text-red-600 hover:text-red-700"
                                >
                                  <XCircle className="w-3 h-3" />
                                </Button>
                              </>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                // 상세 보기 구현
                                alert(`요청 사유: ${request.request_reason}\n\n${request.reviewer_comments ? `검토 의견: ${request.reviewer_comments}` : ''}`);
                              }}
                            >
                              <Eye className="w-3 h-3" />
                            </Button>
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              권한 요청이 없습니다.
            </div>
          )}
        </CardContent>
      </Card>

      {/* 검토 다이얼로그 */}
      <Dialog open={isReviewDialogOpen} onOpenChange={setIsReviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              권한 요청 {reviewAction === 'approve' ? '승인' : '거부'}
            </DialogTitle>
            <DialogDescription>
              {selectedRequest?.requester_name}님의 {selectedRequest?.property_name} 접근 권한 요청을 
              {reviewAction === 'approve' ? '승인' : '거부'}하시겠습니까?
            </DialogDescription>
          </DialogHeader>
          
          {selectedRequest && (
            <div className="space-y-4">
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  <strong>요청 사유:</strong><br />
                  {selectedRequest.request_reason}
                </AlertDescription>
              </Alert>
              
              <div className="space-y-2">
                <Label htmlFor="reviewer-comments">검토 의견</Label>
                <Textarea
                  id="reviewer-comments"
                  value={reviewComments}
                  onChange={(e) => setReviewComments(e.target.value)}
                  placeholder={reviewAction === 'approve' ? 
                    "승인 사유를 입력하세요 (선택사항)..." : 
                    "거부 사유를 입력하세요..."
                  }
                  rows={3}
                />
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsReviewDialogOpen(false)}>
              취소
            </Button>
            <Button 
              onClick={handleReviewRequest}
              variant={reviewAction === 'approve' ? 'default' : 'destructive'}
            >
              {reviewAction === 'approve' ? (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  승인
                </>
              ) : (
                <>
                  <XCircle className="mr-2 h-4 w-4" />
                  거부
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}