"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  BarChart3, 
  Building2, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Eye,
  Settings,
  Activity,
  Search,
  Filter,
  Link,
  Unlink,
  Shield,
  Users,
  Key,
  Plus,
  Edit3,
  Trash2
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";

interface GA4Property {
  id: number;
  property_id: string;
  display_name: string;
  service_account_id: number;
  service_account_name: string;
  service_account_email: string;
  client_id?: number;
  client_name?: string;
  is_active: boolean;
  access_status: 'valid' | 'invalid' | 'unknown';
  last_access_check?: string;
  sync_status: 'synced' | 'pending' | 'error' | 'never';
  last_sync?: string;
  permissions_granted: number;
  created_at: string;
  updated_at: string;
}

interface ServiceAccount {
  id: number;
  name: string;
  email: string;
  is_active: boolean;
  health_status: string;
}

interface Client {
  id: number;
  name: string;
  description?: string;
}

interface PropertyPermission {
  id: number;
  property_id: number;
  user_email: string;
  permission_type: string;
  granted_at: string;
  granted_by: string;
  is_active: boolean;
}

const ACCESS_STATUS_COLORS = {
  valid: "bg-green-100 text-green-800 border-green-200",
  invalid: "bg-red-100 text-red-800 border-red-200",
  unknown: "bg-gray-100 text-gray-800 border-gray-200"
};

const ACCESS_STATUS_ICONS = {
  valid: CheckCircle,
  invalid: XCircle,
  unknown: Activity
};

const SYNC_STATUS_COLORS = {
  synced: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  error: "bg-red-100 text-red-800",
  never: "bg-gray-100 text-gray-800"
};

export default function GA4PropertiesPage() {
  const { user } = useAuth();
  const [properties, setProperties] = useState<GA4Property[]>([]);
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccount[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<GA4Property | null>(null);
  const [propertyPermissions, setPropertyPermissions] = useState<PropertyPermission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAssignDialogOpen, setIsAssignDialogOpen] = useState(false);
  const [isPermissionsDialogOpen, setIsPermissionsDialogOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [serviceAccountFilter, setServiceAccountFilter] = useState("");
  const [clientFilter, setClientFilter] = useState("");
  const [accessStatusFilter, setAccessStatusFilter] = useState("");
  const [isOperationLoading, setIsOperationLoading] = useState<{ [key: string]: boolean }>({});
  const [assignToClient, setAssignToClient] = useState("");

  useEffect(() => {
    fetchProperties();
    fetchServiceAccounts();
    fetchClients();
  }, [currentPage, searchTerm, serviceAccountFilter, clientFilter, accessStatusFilter]);

  const fetchProperties = async () => {
    try {
      setIsLoading(true);
      const serviceAccountId = serviceAccountFilter ? parseInt(serviceAccountFilter) : undefined;
      const clientId = clientFilter ? parseInt(clientFilter) : undefined;
      const response = await apiClient.getGA4PropertiesManagement(currentPage, 20, serviceAccountId, clientId);
      setProperties(response.properties || []);
      setTotalPages(Math.ceil((response.total || 0) / 20));
    } catch (error) {
      console.error("GA4 Property 조회 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchServiceAccounts = async () => {
    try {
      const response = await apiClient.getServiceAccounts(1, 100);
      setServiceAccounts(response.service_accounts || []);
    } catch (error) {
      console.error("서비스 계정 조회 실패:", error);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await apiClient.getClients(1, 100);
      setClients(response.clients || []);
    } catch (error) {
      console.error("클라이언트 조회 실패:", error);
    }
  };

  const fetchPropertyPermissions = async (propertyId: number) => {
    try {
      // Note: This would need to be implemented in the backend
      // const response = await apiClient.getPropertyPermissions(propertyId);
      // setPropertyPermissions(response.permissions || []);
      setPropertyPermissions([]);
    } catch (error) {
      console.error("Property 권한 조회 실패:", error);
      setPropertyPermissions([]);
    }
  };

  const handleAssignToClient = async (propertyId: number, clientId: number) => {
    try {
      setIsOperationLoading({ [`assign_${propertyId}`]: true });
      await apiClient.assignPropertyToClient(propertyId, clientId);
      await fetchProperties();
      setIsAssignDialogOpen(false);
      setAssignToClient("");
    } catch (error) {
      console.error("클라이언트 할당 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const handleUnassignFromClient = async (propertyId: number) => {
    if (!confirm("정말로 이 Property의 클라이언트 할당을 해제하시겠습니까?")) return;

    try {
      setIsOperationLoading({ [`unassign_${propertyId}`]: true });
      await apiClient.unassignPropertyFromClient(propertyId);
      await fetchProperties();
    } catch (error) {
      console.error("클라이언트 할당 해제 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const handleValidateAccess = async (propertyId: number) => {
    try {
      setIsOperationLoading({ [`validate_${propertyId}`]: true });
      await apiClient.validatePropertyAccess(propertyId);
      await fetchProperties();
    } catch (error) {
      console.error("접근 검증 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const handleDeleteProperty = async (propertyId: number) => {
    if (!confirm("정말로 이 GA4 Property를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")) return;

    try {
      setIsOperationLoading({ [`delete_${propertyId}`]: true });
      await apiClient.deleteGA4Property(propertyId);
      await fetchProperties();
    } catch (error) {
      console.error("Property 삭제 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAccessStatusText = (status: string) => {
    switch (status) {
      case 'valid': return '접근 가능';
      case 'invalid': return '접근 불가';
      default: return '확인되지 않음';
    }
  };

  const getSyncStatusText = (status: string) => {
    switch (status) {
      case 'synced': return '동기화됨';
      case 'pending': return '대기중';
      case 'error': return '오류';
      default: return '동기화되지 않음';
    }
  };

  const filteredProperties = properties.filter(property => {
    const matchesSearch = property.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         property.property_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesServiceAccount = !serviceAccountFilter || property.service_account_id.toString() === serviceAccountFilter;
    const matchesClient = !clientFilter || property.client_id?.toString() === clientFilter;
    const matchesAccessStatus = !accessStatusFilter || property.access_status === accessStatusFilter;
    
    return matchesSearch && matchesServiceAccount && matchesClient && matchesAccessStatus;
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">GA4 Property 관리</h1>
          <p className="text-muted-foreground">Google Analytics 4 Property 관리 및 모니터링</p>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
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
          <h1 className="text-3xl font-bold tracking-tight">GA4 Property 관리</h1>
          <p className="text-muted-foreground">Google Analytics 4 Property 관리 및 클라이언트 할당</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchProperties}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 Property</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{properties.length}</div>
            <p className="text-xs text-muted-foreground">등록된 Property</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">할당된 Property</CardTitle>
            <Link className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {properties.filter(p => p.client_id).length}
            </div>
            <p className="text-xs text-muted-foreground">클라이언트에 할당됨</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">접근 가능</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {properties.filter(p => p.access_status === 'valid').length}
            </div>
            <p className="text-xs text-muted-foreground">정상 접근 가능</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">접근 불가</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {properties.filter(p => p.access_status === 'invalid').length}
            </div>
            <p className="text-xs text-muted-foreground">접근 문제 발생</p>
          </CardContent>
        </Card>
      </div>

      {/* 필터 및 검색 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">필터 및 검색</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Property 이름 또는 ID로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={serviceAccountFilter} onValueChange={setServiceAccountFilter}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="서비스 계정 필터" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">모든 서비스 계정</SelectItem>
                {serviceAccounts.map((sa) => (
                  <SelectItem key={sa.id} value={sa.id.toString()}>
                    {sa.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={clientFilter} onValueChange={setClientFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="클라이언트 필터" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">모든 클라이언트</SelectItem>
                <SelectItem value="unassigned">할당되지 않음</SelectItem>
                {clients.map((client) => (
                  <SelectItem key={client.id} value={client.id.toString()}>
                    {client.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={accessStatusFilter} onValueChange={setAccessStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="접근 상태" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">모든 상태</SelectItem>
                <SelectItem value="valid">접근 가능</SelectItem>
                <SelectItem value="invalid">접근 불가</SelectItem>
                <SelectItem value="unknown">확인되지 않음</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* GA4 Property 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>GA4 Property 목록</CardTitle>
          <CardDescription>
            등록된 GA4 Property들의 상태와 클라이언트 할당 정보를 확인하세요.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredProperties.map((property) => {
              const AccessIcon = ACCESS_STATUS_ICONS[property.access_status];
              
              return (
                <div key={property.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg">{property.display_name}</h3>
                        <Badge className={ACCESS_STATUS_COLORS[property.access_status]}>
                          <AccessIcon className="w-3 h-3 mr-1" />
                          {getAccessStatusText(property.access_status)}
                        </Badge>
                        <Badge className={SYNC_STATUS_COLORS[property.sync_status]}>
                          {getSyncStatusText(property.sync_status)}
                        </Badge>
                        {!property.is_active && (
                          <Badge variant="secondary">비활성</Badge>
                        )}
                        {property.client_id && (
                          <Badge variant="outline" className="bg-blue-50 text-blue-700">
                            <Link className="w-3 h-3 mr-1" />
                            할당됨
                          </Badge>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-muted-foreground mb-3">
                        <div>
                          <span className="font-medium">Property ID:</span><br/>
                          <span className="font-mono">{property.property_id}</span>
                        </div>
                        <div>
                          <span className="font-medium">서비스 계정:</span><br/>
                          <span>{property.service_account_name}</span>
                        </div>
                        <div>
                          <span className="font-medium">할당 클라이언트:</span><br/>
                          <span>{property.client_name || '할당되지 않음'}</span>
                        </div>
                        <div>
                          <span className="font-medium">권한 수:</span><br/>
                          <span className="font-semibold">{property.permissions_granted}</span>
                        </div>
                      </div>

                      <div className="flex gap-4 text-xs text-muted-foreground">
                        <span>생성일: {formatDate(property.created_at)}</span>
                        <span>최종 접근 확인: {formatDate(property.last_access_check)}</span>
                        <span>최종 동기화: {formatDate(property.last_sync)}</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedProperty(property);
                          fetchPropertyPermissions(property.id);
                        }}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        상세보기
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleValidateAccess(property.id)}
                        disabled={isOperationLoading[`validate_${property.id}`]}
                      >
                        {isOperationLoading[`validate_${property.id}`] ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Activity className="w-4 h-4 mr-1" />
                        )}
                        접근확인
                      </Button>

                      {(user?.role === 'super_admin' || user?.role === 'admin') && (
                        <>
                          {property.client_id ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleUnassignFromClient(property.id)}
                              disabled={isOperationLoading[`unassign_${property.id}`]}
                            >
                              {isOperationLoading[`unassign_${property.id}`] ? (
                                <RefreshCw className="w-4 h-4 animate-spin" />
                              ) : (
                                <Unlink className="w-4 h-4 mr-1" />
                              )}
                              할당해제
                            </Button>
                          ) : (
                            <Dialog open={isAssignDialogOpen} onOpenChange={setIsAssignDialogOpen}>
                              <DialogTrigger asChild>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setSelectedProperty(property)}
                                >
                                  <Link className="w-4 h-4 mr-1" />
                                  클라이언트할당
                                </Button>
                              </DialogTrigger>
                              <DialogContent>
                                <DialogHeader>
                                  <DialogTitle>클라이언트 할당</DialogTitle>
                                  <DialogDescription>
                                    {property.display_name}을 클라이언트에 할당합니다.
                                  </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4">
                                  <div className="space-y-2">
                                    <Label htmlFor="client">클라이언트 선택</Label>
                                    <Select value={assignToClient} onValueChange={setAssignToClient}>
                                      <SelectTrigger>
                                        <SelectValue placeholder="클라이언트를 선택하세요" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {clients.map((client) => (
                                          <SelectItem key={client.id} value={client.id.toString()}>
                                            {client.name}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>
                                </div>
                                <DialogFooter>
                                  <Button variant="outline" onClick={() => setIsAssignDialogOpen(false)}>
                                    취소
                                  </Button>
                                  <Button 
                                    onClick={() => assignToClient && handleAssignToClient(property.id, parseInt(assignToClient))}
                                    disabled={!assignToClient || isOperationLoading[`assign_${property.id}`]}
                                  >
                                    {isOperationLoading[`assign_${property.id}`] ? (
                                      <>
                                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                                        할당 중...
                                      </>
                                    ) : (
                                      <>
                                        <Link className="mr-2 h-4 w-4" />
                                        할당
                                      </>
                                    )}
                                  </Button>
                                </DialogFooter>
                              </DialogContent>
                            </Dialog>
                          )}

                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteProperty(property.id)}
                            disabled={isOperationLoading[`delete_${property.id}`]}
                            className="text-red-600 hover:text-red-700"
                          >
                            {isOperationLoading[`delete_${property.id}`] ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            
            {filteredProperties.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                {searchTerm || serviceAccountFilter || clientFilter || accessStatusFilter 
                  ? "검색 조건에 맞는 GA4 Property가 없습니다."
                  : "등록된 GA4 Property가 없습니다."
                }
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Property 상세 정보 (선택된 경우) */}
      {selectedProperty && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Property 상세: {selectedProperty.display_name}</span>
              <Button
                variant="outline"
                onClick={() => setSelectedProperty(null)}
              >
                닫기
              </Button>
            </CardTitle>
            <CardDescription>
              Property ID: {selectedProperty.property_id}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="info" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="info">기본 정보</TabsTrigger>
                <TabsTrigger value="access">접근 상태</TabsTrigger>
                <TabsTrigger value="permissions">권한 ({propertyPermissions.length})</TabsTrigger>
              </TabsList>
              
              <TabsContent value="info" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <Label className="text-sm font-medium">Property 이름</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedProperty.display_name}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Property ID</Label>
                    <p className="text-sm text-muted-foreground mt-1 font-mono">{selectedProperty.property_id}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">서비스 계정</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedProperty.service_account_name}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">서비스 계정 이메일</Label>
                    <p className="text-sm text-muted-foreground mt-1 break-all">{selectedProperty.service_account_email}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">할당 클라이언트</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedProperty.client_name || '할당되지 않음'}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">권한 수</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedProperty.permissions_granted}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label className="text-sm font-medium">접근 상태</Label>
                    <div className="mt-1">
                      <Badge className={ACCESS_STATUS_COLORS[selectedProperty.access_status]}>
                        {getAccessStatusText(selectedProperty.access_status)}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">동기화 상태</Label>
                    <div className="mt-1">
                      <Badge className={SYNC_STATUS_COLORS[selectedProperty.sync_status]}>
                        {getSyncStatusText(selectedProperty.sync_status)}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">활성 상태</Label>
                    <div className="mt-1">
                      <Badge variant={selectedProperty.is_active ? "default" : "secondary"}>
                        {selectedProperty.is_active ? "활성" : "비활성"}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">할당 상태</Label>
                    <div className="mt-1">
                      <Badge variant={selectedProperty.client_id ? "default" : "secondary"}>
                        {selectedProperty.client_id ? "할당됨" : "할당되지 않음"}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium">생성일</Label>
                    <p className="text-sm text-muted-foreground mt-1">{formatDate(selectedProperty.created_at)}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">최종 수정일</Label>
                    <p className="text-sm text-muted-foreground mt-1">{formatDate(selectedProperty.updated_at)}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">최종 접근 확인</Label>
                    <p className="text-sm text-muted-foreground mt-1">{formatDate(selectedProperty.last_access_check)}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">최종 동기화</Label>
                    <p className="text-sm text-muted-foreground mt-1">{formatDate(selectedProperty.last_sync)}</p>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="access">
                <div className="space-y-4">
                  <Alert>
                    <Activity className="h-4 w-4" />
                    <AlertDescription>
                      서비스 계정의 이 Property에 대한 접근 상태를 확인합니다.
                    </AlertDescription>
                  </Alert>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium">현재 접근 상태</Label>
                      <div className="mt-2">
                        <Badge className={ACCESS_STATUS_COLORS[selectedProperty.access_status]} variant="outline">
                          {getAccessStatusText(selectedProperty.access_status)}
                        </Badge>
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">최종 확인 시간</Label>
                      <p className="text-sm text-muted-foreground mt-1">
                        {formatDate(selectedProperty.last_access_check)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleValidateAccess(selectedProperty.id)}
                      disabled={isOperationLoading[`validate_${selectedProperty.id}`]}
                    >
                      {isOperationLoading[`validate_${selectedProperty.id}`] ? (
                        <>
                          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                          확인 중...
                        </>
                      ) : (
                        <>
                          <Activity className="mr-2 h-4 w-4" />
                          접근 상태 확인
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="permissions">
                <div className="space-y-4">
                  {propertyPermissions.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>사용자 이메일</TableHead>
                          <TableHead>권한 유형</TableHead>
                          <TableHead>부여일</TableHead>
                          <TableHead>부여자</TableHead>
                          <TableHead>상태</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {propertyPermissions.map((permission) => (
                          <TableRow key={permission.id}>
                            <TableCell>{permission.user_email}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{permission.permission_type}</Badge>
                            </TableCell>
                            <TableCell>{formatDate(permission.granted_at)}</TableCell>
                            <TableCell>{permission.granted_by}</TableCell>
                            <TableCell>
                              <Badge variant={permission.is_active ? "default" : "secondary"}>
                                {permission.is_active ? "활성" : "비활성"}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      이 Property에 부여된 권한이 없습니다.
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
}