"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Key, 
  Plus, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Eye,
  Activity,
  Building2,
  Search,
  Trash2,
  Edit3
} from "lucide-react";
import { typeSafeApiClient, ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";
import { ServiceAccount, Client, GA4Property, HealthStatus, SyncStatus } from "@/types/api";

interface ServiceAccountFormData {
  name: string;
  email: string;
  description: string;
  client_id: string;
  project_id: string;
  credentials_file: File | null;
}

const HEALTH_STATUS_COLORS: Record<HealthStatus, string> = {
  healthy: "bg-green-100 text-green-800 border-green-200",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-200", 
  error: "bg-red-100 text-red-800 border-red-200",
  unknown: "bg-gray-100 text-gray-800 border-gray-200"
};

const HEALTH_STATUS_ICONS: Record<HealthStatus, React.ComponentType<{ className?: string }>> = {
  healthy: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  unknown: Activity
};

const SYNC_STATUS_COLORS: Record<SyncStatus, string> = {
  synced: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  error: "bg-red-100 text-red-800",
  never: "bg-gray-100 text-gray-800"
};

export default function ServiceAccountsPage() {
  const { user } = useAuth();
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccount[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedServiceAccount, setSelectedServiceAccount] = useState<ServiceAccount | null>(null);
  const [serviceAccountProperties, setServiceAccountProperties] = useState<GA4Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingServiceAccount, setEditingServiceAccount] = useState<ServiceAccount | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [clientFilter, setClientFilter] = useState("");
  const [healthFilter, setHealthFilter] = useState("");
  const [isOperationLoading, setIsOperationLoading] = useState<{ [key: string]: boolean }>({});

  const [formData, setFormData] = useState<ServiceAccountFormData>({
    name: "",
    email: "",
    description: "",
    client_id: "",
    project_id: "",
    credentials_file: null
  });

  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    fetchServiceAccounts();
    fetchClients();
  }, [currentPage, searchTerm, clientFilter, healthFilter]);

  const fetchServiceAccounts = async () => {
    try {
      setIsLoading(true);
      const clientId = clientFilter ? parseInt(clientFilter) : undefined;
      const response = await typeSafeApiClient.getServiceAccounts(currentPage, 20, clientId);
      setServiceAccounts(response.items || []);
      setTotalPages(response.pages || Math.ceil((response.total || 0) / 20));
    } catch (error) {
      console.error("서비스 계정 조회 실패:", error);
      if (error instanceof ApiClientError) {
        console.error("API Error Details:", error.details);
      }
      setServiceAccounts([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await typeSafeApiClient.getClients(1, 100);
      setClients(response.items || []);
    } catch (error) {
      console.error("클라이언트 조회 실패:", error);
      if (error instanceof ApiClientError) {
        console.error("API Error Details:", error.details);
      }
      setClients([]);
    }
  };

  const fetchServiceAccountProperties = async (serviceAccountId: number) => {
    try {
      const response = await typeSafeApiClient.getGA4PropertiesManagement(1, 100, serviceAccountId);
      setServiceAccountProperties(response.items || []);
    } catch (error) {
      console.error("서비스 계정 Property 조회 실패:", error);
      if (error instanceof ApiClientError) {
        console.error("API Error Details:", error.details);
      }
      setServiceAccountProperties([]);
    }
  };

  const validateForm = (): boolean => {
    const errors: { [key: string]: string } = {};

    if (!formData.name.trim()) errors.name = "서비스 계정 이름을 입력하세요.";
    if (!formData.email.trim()) errors.email = "서비스 계정 이메일을 입력하세요.";
    if (!formData.email.includes("@")) errors.email = "올바른 이메일 형식을 입력하세요.";
    if (!formData.project_id.trim()) errors.project_id = "프로젝트 ID를 입력하세요.";
    if (!formData.credentials_file && !editingServiceAccount) {
      errors.credentials_file = "서비스 계정 인증 파일을 업로드하세요.";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateServiceAccount = async () => {
    if (!validateForm()) return;

    try {
      setIsOperationLoading({ create: true });
      
      const formDataToSend = new FormData();
      formDataToSend.append('name', formData.name);
      formDataToSend.append('email', formData.email);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('project_id', formData.project_id);
      if (formData.client_id) {
        formDataToSend.append('client_id', formData.client_id);
      }
      if (formData.credentials_file) {
        formDataToSend.append('credentials_file', formData.credentials_file);
      }

      await typeSafeApiClient.createServiceAccount(formDataToSend);
      
      // 폼 초기화
      setFormData({
        name: "",
        email: "",
        description: "",
        client_id: "",
        project_id: "",
        credentials_file: null
      });
      setFormErrors({});
      setIsCreateDialogOpen(false);
      
      // 목록 새로고침
      await fetchServiceAccounts();
      
    } catch (error) {
      console.error("서비스 계정 생성 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const handleEditServiceAccount = async () => {
    if (!editingServiceAccount || !validateForm()) return;

    try {
      setIsOperationLoading({ edit: true });
      
      const updateData = {
        name: formData.name,
        email: formData.email,
        description: formData.description,
        client_id: formData.client_id ? parseInt(formData.client_id) : null,
        project_id: formData.project_id
      };

      await typeSafeApiClient.updateServiceAccount(editingServiceAccount.id, updateData);
      
      setFormData({
        name: "",
        email: "",
        description: "",
        client_id: "",
        project_id: "",
        credentials_file: null
      });
      setFormErrors({});
      setIsEditDialogOpen(false);
      setEditingServiceAccount(null);
      
      await fetchServiceAccounts();
      
    } catch (error) {
      console.error("서비스 계정 수정 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const handleDeleteServiceAccount = async (id: number) => {
    if (!confirm("정말로 이 서비스 계정을 삭제하시겠습니까?")) return;

    try {
      setIsOperationLoading({ [`delete_${id}`]: true });
      await typeSafeApiClient.deleteServiceAccount(id);
      await fetchServiceAccounts();
    } catch (error) {
      console.error("서비스 계정 삭제 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const handleDiscoverProperties = async (serviceAccountId: number) => {
    try {
      setIsOperationLoading({ [`discover_${serviceAccountId}`]: true });
      await typeSafeApiClient.discoverGA4Properties(serviceAccountId);
      await fetchServiceAccounts();
      if (selectedServiceAccount?.id === serviceAccountId) {
        await fetchServiceAccountProperties(serviceAccountId);
      }
    } catch (error) {
      console.error("Property 발견 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const handleSyncPermissions = async (serviceAccountId: number) => {
    try {
      setIsOperationLoading({ [`sync_${serviceAccountId}`]: true });
      await typeSafeApiClient.syncServiceAccountPermissions(serviceAccountId);
      await fetchServiceAccounts();
    } catch (error) {
      console.error("권한 동기화 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const handleHealthCheck = async (serviceAccountId: number) => {
    try {
      setIsOperationLoading({ [`health_${serviceAccountId}`]: true });
      await typeSafeApiClient.testServiceAccountHealth(serviceAccountId);
      await fetchServiceAccounts();
    } catch (error) {
      console.error("상태 확인 실패:", error);
    } finally {
      setIsOperationLoading({});
    }
  };

  const openEditDialog = (serviceAccount: ServiceAccount) => {
    setEditingServiceAccount(serviceAccount);
    setFormData({
      name: serviceAccount.name,
      email: serviceAccount.email,
      description: serviceAccount.description || "",
      client_id: serviceAccount.client_id?.toString() || "",
      project_id: serviceAccount.project_id,
      credentials_file: null
    });
    setFormErrors({});
    setIsEditDialogOpen(true);
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

  const getHealthStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return '정상';
      case 'warning': return '경고';
      case 'error': return '오류';
      default: return '알 수 없음';
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

  const filteredServiceAccounts = serviceAccounts.filter(account => {
    const matchesSearch = account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         account.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesClient = !clientFilter || account.client_id?.toString() === clientFilter;
    const matchesHealth = !healthFilter || account.health_status === healthFilter;
    
    return matchesSearch && matchesClient && matchesHealth;
  });

  const ServiceAccountForm = ({ isEdit = false }: { isEdit?: boolean }) => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">서비스 계정 이름 *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="예: GA4 서비스 계정"
          />
          {formErrors.name && <p className="text-sm text-red-600">{formErrors.name}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">서비스 계정 이메일 *</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="예: service-account@project.iam.gserviceaccount.com"
          />
          {formErrors.email && <p className="text-sm text-red-600">{formErrors.email}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="project_id">프로젝트 ID *</Label>
          <Input
            id="project_id"
            value={formData.project_id}
            onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
            placeholder="예: my-analytics-project"
          />
          {formErrors.project_id && <p className="text-sm text-red-600">{formErrors.project_id}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="client_id">할당 클라이언트</Label>
          <Select
            value={formData.client_id}
            onValueChange={(value) => setFormData({ ...formData, client_id: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="선택 안함" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">선택 안함</SelectItem>
              {clients.map((client) => (
                <SelectItem key={client.id} value={client.id.toString()}>
                  {client.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">설명</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="서비스 계정에 대한 설명을 입력하세요..."
          rows={3}
        />
      </div>

      {!isEdit && (
        <div className="space-y-2">
          <Label htmlFor="credentials_file">서비스 계정 인증 파일 (JSON) *</Label>
          <Input
            id="credentials_file"
            type="file"
            accept=".json"
            onChange={(e) => setFormData({ ...formData, credentials_file: e.target.files?.[0] || null })}
          />
          {formErrors.credentials_file && <p className="text-sm text-red-600">{formErrors.credentials_file}</p>}
          <p className="text-sm text-muted-foreground">
            Google Cloud Console에서 다운로드한 서비스 계정 JSON 키 파일을 업로드하세요.
          </p>
        </div>
      )}
    </div>
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">서비스 계정 관리</h1>
          <p className="text-muted-foreground">Google Analytics 4 서비스 계정 관리</p>
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
          <h1 className="text-3xl font-bold tracking-tight">서비스 계정 관리</h1>
          <p className="text-muted-foreground">Google Analytics 4 서비스 계정 관리 및 모니터링</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchServiceAccounts}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
          {(user?.role === 'super_admin' || user?.role === 'admin') && (
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  서비스 계정 추가
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>새 서비스 계정 추가</DialogTitle>
                  <DialogDescription>
                    Google Analytics 4에 접근할 새 서비스 계정을 추가합니다.
                  </DialogDescription>
                </DialogHeader>
                <ServiceAccountForm />
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    취소
                  </Button>
                  <Button 
                    onClick={handleCreateServiceAccount}
                    disabled={isOperationLoading.create}
                  >
                    {isOperationLoading.create ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        생성 중...
                      </>
                    ) : (
                      <>
                        <Plus className="mr-2 h-4 w-4" />
                        생성
                      </>
                    )}
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
            <CardTitle className="text-sm font-medium">총 서비스 계정</CardTitle>
            <Key className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceAccounts?.length || 0}</div>
            <p className="text-xs text-muted-foreground">등록된 계정</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">정상 상태</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {serviceAccounts?.filter(sa => sa.health_status === 'healthy')?.length || 0}
            </div>
            <p className="text-xs text-muted-foreground">정상 작동 중</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">경고 상태</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {serviceAccounts?.filter(sa => sa.health_status === 'warning')?.length || 0}
            </div>
            <p className="text-xs text-muted-foreground">주의 필요</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 Property</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {serviceAccounts.reduce((sum, sa) => sum + sa.properties_count, 0)}
            </div>
            <p className="text-xs text-muted-foreground">관리 Property</p>
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
                  placeholder="서비스 계정 이름 또는 이메일로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={clientFilter} onValueChange={setClientFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="클라이언트 필터" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">모든 클라이언트</SelectItem>
                {clients.map((client) => (
                  <SelectItem key={client.id} value={client.id.toString()}>
                    {client.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={healthFilter} onValueChange={setHealthFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="상태 필터" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">모든 상태</SelectItem>
                <SelectItem value="healthy">정상</SelectItem>
                <SelectItem value="warning">경고</SelectItem>
                <SelectItem value="error">오류</SelectItem>
                <SelectItem value="unknown">알 수 없음</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 서비스 계정 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>서비스 계정 목록</CardTitle>
          <CardDescription>
            등록된 서비스 계정들의 상태와 정보를 확인하세요.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredServiceAccounts.map((serviceAccount) => {
              const HealthIcon = HEALTH_STATUS_ICONS[serviceAccount.health_status];
              
              return (
                <div key={serviceAccount.id} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg">{serviceAccount.name}</h3>
                        <Badge className={HEALTH_STATUS_COLORS[serviceAccount.health_status]}>
                          <HealthIcon className="w-3 h-3 mr-1" />
                          {getHealthStatusText(serviceAccount.health_status)}
                        </Badge>
                        <Badge className={SYNC_STATUS_COLORS[serviceAccount.permissions_sync_status]}>
                          {getSyncStatusText(serviceAccount.permissions_sync_status)}
                        </Badge>
                        {!serviceAccount.is_active && (
                          <Badge variant="secondary">비활성</Badge>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-muted-foreground mb-3">
                        <div>
                          <span className="font-medium">이메일:</span><br/>
                          <span className="break-all">{serviceAccount.email}</span>
                        </div>
                        <div>
                          <span className="font-medium">프로젝트:</span><br/>
                          <span>{serviceAccount.project_id}</span>
                        </div>
                        <div>
                          <span className="font-medium">클라이언트:</span><br/>
                          <span>{serviceAccount.client_name || '할당되지 않음'}</span>
                        </div>
                        <div>
                          <span className="font-medium">Property 수:</span><br/>
                          <span className="font-semibold">{serviceAccount.properties_count}</span>
                        </div>
                      </div>

                      {serviceAccount.description && (
                        <p className="text-sm text-muted-foreground mb-3">
                          {serviceAccount.description}
                        </p>
                      )}

                      <div className="flex gap-4 text-xs text-muted-foreground">
                        <span>생성일: {formatDate(serviceAccount.created_at)}</span>
                        <span>최종 상태 확인: {formatDate(serviceAccount.last_health_check)}</span>
                        <span>최종 동기화: {formatDate(serviceAccount.last_sync)}</span>
                      </div>
                    </div>

                    <div className="flex flex-col gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedServiceAccount(serviceAccount);
                          fetchServiceAccountProperties(serviceAccount.id);
                        }}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        상세보기
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleHealthCheck(serviceAccount.id)}
                        disabled={isOperationLoading[`health_${serviceAccount.id}`]}
                      >
                        {isOperationLoading[`health_${serviceAccount.id}`] ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Activity className="w-4 h-4 mr-1" />
                        )}
                        상태확인
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDiscoverProperties(serviceAccount.id)}
                        disabled={isOperationLoading[`discover_${serviceAccount.id}`]}
                      >
                        {isOperationLoading[`discover_${serviceAccount.id}`] ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Search className="w-4 h-4 mr-1" />
                        )}
                        Property 발견
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSyncPermissions(serviceAccount.id)}
                        disabled={isOperationLoading[`sync_${serviceAccount.id}`]}
                      >
                        {isOperationLoading[`sync_${serviceAccount.id}`] ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4 mr-1" />
                        )}
                        권한동기화
                      </Button>

                      {(user?.role === 'super_admin' || user?.role === 'admin') && (
                        <div className="flex gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openEditDialog(serviceAccount)}
                          >
                            <Edit3 className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteServiceAccount(serviceAccount.id)}
                            disabled={isOperationLoading[`delete_${serviceAccount.id}`]}
                            className="text-red-600 hover:text-red-700"
                          >
                            {isOperationLoading[`delete_${serviceAccount.id}`] ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            
            {filteredServiceAccounts.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                {searchTerm || clientFilter || healthFilter 
                  ? "검색 조건에 맞는 서비스 계정이 없습니다."
                  : "등록된 서비스 계정이 없습니다."
                }
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 서비스 계정 상세 정보 (선택된 경우) */}
      {selectedServiceAccount && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>서비스 계정 상세: {selectedServiceAccount.name}</span>
              <Button
                variant="outline"
                onClick={() => setSelectedServiceAccount(null)}
              >
                닫기
              </Button>
            </CardTitle>
            <CardDescription>
              서비스 계정의 상세 정보와 연결된 GA4 Property 목록
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="info" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="info">기본 정보</TabsTrigger>
                <TabsTrigger value="properties">연결 Property ({serviceAccountProperties?.length || 0})</TabsTrigger>
              </TabsList>
              
              <TabsContent value="info" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <Label className="text-sm font-medium">서비스 계정 이름</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedServiceAccount.name}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">이메일</Label>
                    <p className="text-sm text-muted-foreground mt-1 break-all">{selectedServiceAccount.email}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">프로젝트 ID</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedServiceAccount.project_id}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Private Key ID</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedServiceAccount.private_key_id}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">인증 파일명</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedServiceAccount.credentials_file_name}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">할당 클라이언트</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedServiceAccount.client_name || '할당되지 않음'}</p>
                  </div>
                </div>
                
                {selectedServiceAccount.description && (
                  <div>
                    <Label className="text-sm font-medium">설명</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedServiceAccount.description}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label className="text-sm font-medium">상태</Label>
                    <div className="mt-1">
                      <Badge className={HEALTH_STATUS_COLORS[selectedServiceAccount.health_status || 'unknown']}>
                        {getHealthStatusText(selectedServiceAccount.health_status || 'unknown')}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">동기화 상태</Label>
                    <div className="mt-1">
                      <Badge className={SYNC_STATUS_COLORS[selectedServiceAccount.permissions_sync_status || 'never']}>
                        {getSyncStatusText(selectedServiceAccount.permissions_sync_status || 'never')}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">활성 상태</Label>
                    <div className="mt-1">
                      <Badge variant={selectedServiceAccount.is_active ? "default" : "secondary"}>
                        {selectedServiceAccount.is_active ? "활성" : "비활성"}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Property 수</Label>
                    <p className="text-sm font-semibold mt-1">{selectedServiceAccount.properties_count}</p>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="properties">
                <div className="space-y-4">
                  {serviceAccountProperties.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Property 이름</TableHead>
                          <TableHead>Property ID</TableHead>
                          <TableHead>할당 클라이언트</TableHead>
                          <TableHead>상태</TableHead>
                          <TableHead>최종 접근 확인</TableHead>
                          <TableHead>생성일</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {serviceAccountProperties.map((property) => (
                          <TableRow key={property.id}>
                            <TableCell className="font-medium">{property.display_name}</TableCell>
                            <TableCell>{property.property_id}</TableCell>
                            <TableCell>{property.client_name || '할당되지 않음'}</TableCell>
                            <TableCell>
                              <Badge variant={property.is_active ? "default" : "secondary"}>
                                {property.is_active ? "활성" : "비활성"}
                              </Badge>
                            </TableCell>
                            <TableCell>{formatDate(property.last_access_check)}</TableCell>
                            <TableCell>{formatDate(property.created_at)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      이 서비스 계정에 연결된 GA4 Property가 없습니다.
                      <br />
                      <Button 
                        variant="outline" 
                        className="mt-4"
                        onClick={() => handleDiscoverProperties(selectedServiceAccount.id)}
                        disabled={isOperationLoading[`discover_${selectedServiceAccount.id}`]}
                      >
                        {isOperationLoading[`discover_${selectedServiceAccount.id}`] ? (
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Search className="w-4 h-4 mr-2" />
                        )}
                        Property 발견하기
                      </Button>
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* 편집 다이얼로그 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>서비스 계정 편집</DialogTitle>
            <DialogDescription>
              서비스 계정의 정보를 수정합니다. 인증 파일은 변경할 수 없습니다.
            </DialogDescription>
          </DialogHeader>
          <ServiceAccountForm isEdit={true} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button 
              onClick={handleEditServiceAccount}
              disabled={isOperationLoading.edit}
            >
              {isOperationLoading.edit ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  수정 중...
                </>
              ) : (
                <>
                  <Edit3 className="mr-2 h-4 w-4" />
                  수정
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}