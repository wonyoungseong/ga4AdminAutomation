"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PermissionWorkflowIntegration } from "@/components/permissions/permission-workflow-integration";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Search, Edit, Trash2, Shield, Clock, CheckCircle, XCircle, ArrowRight, Building2, ChevronDown, ChevronRight, Eye, EyeOff } from "lucide-react";
import { typeSafeApiClient } from "@/lib/api-client";

interface PropertyPermission {
  property_id: string;
  property_name: string;
  current_permission: string;
  requested_permission: string;
}

interface Permission {
  id: number;
  requester_email: string;
  requester_name: string;
  client_name: string;
  properties: PropertyPermission[];
  status: string;
  requested_at: string;
  approved_at?: string;
  approved_by?: string;
  notes?: string;
}

export default function PermissionsPage() {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [filteredPermissions, setFilteredPermissions] = useState<Permission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedPermission, setSelectedPermission] = useState<Permission | null>(null);
  const [newPermission, setNewPermission] = useState({
    requester_email: "",
    client_name: "",
    properties: [{ property_id: "", property_name: "", current_permission: "", requested_permission: "" }] as PropertyPermission[],
    notes: "",
  });
  const [editedPermission, setEditedPermission] = useState<Permission | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchPermissions();
  }, []);

  useEffect(() => {
    // 검색 및 상태 필터링
    let filtered = permissions.filter(permission =>
      permission.requester_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      permission.requester_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      permission.client_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      permission.properties.some(prop => 
        prop.property_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        prop.property_name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    );

    if (statusFilter !== "all") {
      filtered = filtered.filter(permission => permission.status === statusFilter);
    }

    setFilteredPermissions(filtered);
  }, [permissions, searchTerm, statusFilter]);

  const fetchPermissions = async () => {
    try {
      const data = await typeSafeApiClient.getPermissions();
      setPermissions(data);
    } catch (error) {
      console.error("권한 목록 조회 실패:", error);
      // 에러 발생 시 기본 빈 배열 설정
      setPermissions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreatePermission = async () => {
    try {
      await typeSafeApiClient.createPermission(newPermission);
      
      // 목록 새로고침
      await fetchPermissions();
      
      // 폼 초기화
      setNewPermission({
        requester_email: "",
        client_name: "",
        properties: [{ property_id: "", property_name: "", current_permission: "", requested_permission: "" }],
        notes: "",
      });
      setIsCreateDialogOpen(false);
    } catch (error) {
      console.error("권한 생성 실패:", error);
    }
  };

  const handleUpdatePermissionStatus = async (permissionId: number, status: string, notes?: string) => {
    try {
      await typeSafeApiClient.updatePermission(permissionId, { status, notes });
      
      // 목록 새로고침
      await fetchPermissions();
    } catch (error) {
      console.error("권한 상태 변경 실패:", error);
    }
  };

  const handleDeletePermission = async (permissionId: number) => {
    if (confirm("정말로 이 권한 요청을 삭제하시겠습니까?")) {
      try {
        await typeSafeApiClient.deletePermission(permissionId);
        
        // 목록 새로고침
        await fetchPermissions();
      } catch (error) {
        console.error("권한 삭제 실패:", error);
      }
    }
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "bg-green-100 text-green-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "rejected":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "approved":
        return <CheckCircle className="h-4 w-4" />;
      case "pending":
        return <Clock className="h-4 w-4" />;
      case "rejected":
        return <XCircle className="h-4 w-4" />;
      default:
        return <Shield className="h-4 w-4" />;
    }
  };

  const getPermissionTypeColor = (type: string) => {
    switch (type) {
      case "Administrator":
        return "bg-red-100 text-red-800";
      case "Editor":
        return "bg-blue-100 text-blue-800";
      case "Viewer":
        return "bg-green-100 text-green-800";
      case "None":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const toggleRowExpansion = (permissionId: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(permissionId)) {
      newExpanded.delete(permissionId);
    } else {
      newExpanded.add(permissionId);
    }
    setExpandedRows(newExpanded);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">권한 관리</h1>
          <p className="text-muted-foreground">GA4 접근 권한을 관리합니다</p>
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">권한 관리</h1>
          <p className="text-muted-foreground">GA4 접근 권한을 관리합니다</p>
        </div>
        <div />
      </div>

      <Tabs defaultValue="workflow" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="workflow">권한 요청 워크플로우</TabsTrigger>
          <TabsTrigger value="legacy">기존 권한 관리</TabsTrigger>
        </TabsList>
        
        <TabsContent value="workflow">
          <PermissionWorkflowIntegration />
        </TabsContent>
        
        <TabsContent value="legacy" className="space-y-6">
          <div className="flex items-center justify-between">
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              새 권한 요청
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>새 권한 요청</DialogTitle>
              <DialogDescription>
                새로운 GA4 접근 권한을 요청합니다.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="new-requester-email">요청자 이메일</Label>
                <Input
                  id="new-requester-email"
                  type="email"
                  value={newPermission.requester_email}
                  onChange={(e) => setNewPermission({ ...newPermission, requester_email: e.target.value })}
                  placeholder="requester@example.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-client-name">클라이언트명</Label>
                <Input
                  id="new-client-name"
                  value={newPermission.client_name}
                  onChange={(e) => setNewPermission({ ...newPermission, client_name: e.target.value })}
                  placeholder="클라이언트 회사명"
                />
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>GA4 Properties</Label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setNewPermission({
                      ...newPermission,
                      properties: [...newPermission.properties, { property_id: "", property_name: "", current_permission: "", requested_permission: "" }]
                    })}
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Property 추가
                  </Button>
                </div>
                {newPermission.properties.map((prop, index) => (
                  <div key={index} className="p-4 border rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">Property {index + 1}</h4>
                      {newPermission.properties.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setNewPermission({
                            ...newPermission,
                            properties: newPermission.properties.filter((_, i) => i !== index)
                          })}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label>Property ID</Label>
                        <Input
                          value={prop.property_id}
                          onChange={(e) => {
                            const updatedProperties = [...newPermission.properties];
                            updatedProperties[index].property_id = e.target.value;
                            setNewPermission({ ...newPermission, properties: updatedProperties });
                          }}
                          placeholder="GA_123456789"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Property 이름</Label>
                        <Input
                          value={prop.property_name}
                          onChange={(e) => {
                            const updatedProperties = [...newPermission.properties];
                            updatedProperties[index].property_name = e.target.value;
                            setNewPermission({ ...newPermission, properties: updatedProperties });
                          }}
                          placeholder="웹사이트 이름"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label>현재 권한</Label>
                        <Select
                          value={prop.current_permission}
                          onValueChange={(value) => {
                            const updatedProperties = [...newPermission.properties];
                            updatedProperties[index].current_permission = value;
                            setNewPermission({ ...newPermission, properties: updatedProperties });
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="현재 권한" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="None">없음</SelectItem>
                            <SelectItem value="Viewer">Viewer</SelectItem>
                            <SelectItem value="Editor">Editor</SelectItem>
                            <SelectItem value="Administrator">Administrator</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>요청 권한</Label>
                        <Select
                          value={prop.requested_permission}
                          onValueChange={(value) => {
                            const updatedProperties = [...newPermission.properties];
                            updatedProperties[index].requested_permission = value;
                            setNewPermission({ ...newPermission, properties: updatedProperties });
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="요청할 권한" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Viewer">Viewer</SelectItem>
                            <SelectItem value="Editor">Editor</SelectItem>
                            <SelectItem value="Administrator">Administrator</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    {prop.current_permission && prop.requested_permission && (
                      <div className="flex items-center gap-2 p-2 bg-blue-50 rounded text-sm">
                        <Badge variant="outline" className={getPermissionTypeColor(prop.current_permission)}>
                          {prop.current_permission}
                        </Badge>
                        <ArrowRight className="h-4 w-4 text-blue-600" />
                        <Badge className={getPermissionTypeColor(prop.requested_permission)}>
                          {prop.requested_permission}
                        </Badge>
                        <span className="text-blue-700 ml-2">권한 변경 요청</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-notes">요청 사유</Label>
                <Textarea
                  id="new-notes"
                  value={newPermission.notes}
                  onChange={(e) => setNewPermission({ ...newPermission, notes: e.target.value })}
                  placeholder="권한이 필요한 사유를 입력하세요"
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleCreatePermission}>요청</Button>
            </DialogFooter>
          </DialogContent>
          </Dialog>
          </div>

          {/* 통계 카드 */}
          <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 요청</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{permissions.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">승인됨</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {permissions.filter(p => p.status === "approved").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">대기 중</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {permissions.filter(p => p.status === "pending").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">거부됨</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {permissions.filter(p => p.status === "rejected").length}
            </div>
          </CardContent>
        </Card>
          </div>

          <Card>
        <CardHeader>
          <CardTitle>권한 요청 목록</CardTitle>
          <CardDescription>
            총 {permissions.length}개의 권한 요청이 있습니다.
          </CardDescription>
          <div className="flex items-center space-x-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="권한 요청 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">전체</SelectItem>
                <SelectItem value="pending">대기 중</SelectItem>
                <SelectItem value="approved">승인됨</SelectItem>
                <SelectItem value="rejected">거부됨</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="space-y-4 p-6">
            {filteredPermissions.map((permission) => (
              <div key={permission.id} className="border rounded-lg bg-white">
                {/* 메인 정보 행 */}
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      {/* 요청자 정보 */}
                      <div className="min-w-48">
                        <div className="font-semibold">{permission.requester_name}</div>
                        <div className="text-sm text-gray-600">{permission.requester_email}</div>
                        <div className="text-sm text-blue-600 font-medium">{permission.client_name}</div>
                      </div>

                      {/* Property 요약 */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Building2 className="h-4 w-4 text-gray-500" />
                          <span className="font-medium">
                            {permission.properties.length}개 Property
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleRowExpansion(permission.id)}
                            className="p-1 h-6 w-6"
                          >
                            {expandedRows.has(permission.id) ? 
                              <ChevronDown className="h-4 w-4" /> : 
                              <ChevronRight className="h-4 w-4" />
                            }
                          </Button>
                        </div>
                        
                        {/* 첫 2개 Property 미리보기 */}
                        <div className="flex flex-wrap gap-2">
                          {permission.properties.slice(0, 2).map((prop, index) => (
                            <div key={index} className="flex items-center gap-1 text-xs bg-gray-50 px-2 py-1 rounded">
                              <span className="font-medium truncate max-w-24">{prop.property_name}</span>
                              <span className="text-gray-400">:</span>
                              <Badge variant="outline" className={`${getPermissionTypeColor(prop.current_permission)} text-xs px-1 py-0`}>
                                {prop.current_permission || "None"}
                              </Badge>
                              <ArrowRight className="h-2 w-2 text-gray-400" />
                              <Badge className={`${getPermissionTypeColor(prop.requested_permission)} text-xs px-1 py-0`}>
                                {prop.requested_permission}
                              </Badge>
                            </div>
                          ))}
                          {permission.properties.length > 2 && (
                            <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              +{permission.properties.length - 2}개 더
                            </div>
                          )}
                        </div>
                      </div>

                      {/* 상태 및 날짜 */}
                      <div className="text-right min-w-32">
                        <div className="flex items-center justify-end gap-2 mb-1">
                          {getStatusIcon(permission.status)}
                          <Badge className={getStatusColor(permission.status)}>
                            {permission.status === "approved" ? "승인됨" : 
                             permission.status === "pending" ? "대기 중" : "거부됨"}
                          </Badge>
                        </div>
                        <div className="text-xs text-gray-500">
                          요청: {formatDate(permission.requested_at).split(' ')[0]}
                        </div>
                        {permission.approved_at && (
                          <div className="text-xs text-green-600">
                            승인: {formatDate(permission.approved_at).split(' ')[0]}
                          </div>
                        )}
                      </div>

                      {/* 액션 버튼 */}
                      <div className="flex items-center gap-1 min-w-fit">
                        {permission.status === "pending" && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleUpdatePermissionStatus(permission.id, "approved")}
                              className="text-green-600 hover:text-green-700 text-xs px-2"
                            >
                              승인
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleUpdatePermissionStatus(permission.id, "rejected")}
                              className="text-red-600 hover:text-red-700 text-xs px-2"
                            >
                              거부
                            </Button>
                          </>
                        )}
                        {permission.status === "rejected" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleUpdatePermissionStatus(permission.id, "approved")}
                            className="text-green-600 hover:text-green-700 text-xs px-2"
                          >
                            승인
                          </Button>
                        )}
                        {permission.status === "approved" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleUpdatePermissionStatus(permission.id, "rejected")}
                            className="text-red-600 hover:text-red-700 text-xs px-2"
                          >
                            거부
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedPermission(permission);
                            setEditedPermission({ ...permission });
                            setIsEditDialogOpen(true);
                          }}
                          className="p-1 h-7 w-7"
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeletePermission(permission.id)}
                          className="p-1 h-7 w-7 text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 확장된 Property 상세 정보 */}
                {expandedRows.has(permission.id) && (
                  <div className="border-t bg-gray-50 p-4">
                    <div className="space-y-3">
                      <h4 className="font-semibold text-sm text-gray-700 mb-3">전체 Property 권한 변경 내역</h4>
                      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                        {permission.properties.map((prop, index) => (
                          <div key={index} className="bg-white p-3 rounded-lg border">
                            <div className="flex items-center gap-2 mb-2">
                              <Building2 className="h-4 w-4 text-gray-500" />
                              <span className="font-medium text-sm">{prop.property_name}</span>
                            </div>
                            <div className="text-xs text-gray-600 font-mono mb-2">{prop.property_id}</div>
                            <div className="flex items-center justify-between">
                              <Badge variant="outline" className={`${getPermissionTypeColor(prop.current_permission)} text-xs`}>
                                {prop.current_permission || "None"}
                              </Badge>
                              <ArrowRight className="h-3 w-3 text-gray-400" />
                              <Badge className={`${getPermissionTypeColor(prop.requested_permission)} text-xs`}>
                                {prop.requested_permission}
                              </Badge>
                            </div>
                            {prop.current_permission !== prop.requested_permission && (
                              <div className="mt-2 text-xs text-center">
                                {prop.current_permission === "None" || !prop.current_permission ? (
                                  <span className="text-blue-600 font-medium">새 권한 요청</span>
                                ) : (
                                  <span className="text-orange-600 font-medium">권한 변경</span>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                      {permission.notes && (
                        <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                          <div className="text-sm font-medium text-blue-800 mb-1">요청 사유:</div>
                          <div className="text-sm text-blue-700">{permission.notes}</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {filteredPermissions.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <Shield className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">권한 요청이 없습니다</p>
                <p className="text-sm">검색 조건을 확인하거나 새로운 권한을 요청해보세요.</p>
              </div>
            )}
          </div>
        </CardContent>
          </Card>

          {/* 상세 보기/수정 다이얼로그 */}
          <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>권한 요청 상세</DialogTitle>
            <DialogDescription>
              권한 요청의 상세 정보를 확인하고 수정할 수 있습니다.
            </DialogDescription>
          </DialogHeader>
          {editedPermission && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>요청자 이름</Label>
                  <Input value={editedPermission.requester_name} disabled />
                </div>
                <div className="space-y-2">
                  <Label>요청자 이메일</Label>
                  <Input value={editedPermission.requester_email} disabled />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>클라이언트명</Label>
                <Input value={editedPermission.client_name} disabled />
              </div>

              <div className="space-y-4">
                <Label className="text-lg font-semibold">GA4 Properties 권한 변경</Label>
                {editedPermission.properties.map((prop, index) => (
                  <div key={index} className="p-4 border rounded-lg space-y-4">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-gray-500" />
                      <h4 className="font-semibold">{prop.property_name}</h4>
                      <Badge variant="outline" className="text-xs">{prop.property_id}</Badge>
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-center justify-center gap-4">
                        <div className="text-center">
                          <div className="text-sm text-gray-600 mb-2">현재 권한</div>
                          <Badge variant="outline" className={`${getPermissionTypeColor(prop.current_permission)} text-sm px-3 py-1`}>
                            {prop.current_permission || "None"}
                          </Badge>
                        </div>
                        
                        <ArrowRight className="h-6 w-6 text-gray-400" />
                        
                        <div className="text-center">
                          <div className="text-sm text-gray-600 mb-2">변경될 권한</div>
                          <Select
                            value={prop.requested_permission}
                            onValueChange={(value) => {
                              const updatedProperties = [...editedPermission.properties];
                              updatedProperties[index].requested_permission = value;
                              setEditedPermission({ ...editedPermission, properties: updatedProperties });
                            }}
                          >
                            <SelectTrigger className="w-32">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="None">없음</SelectItem>
                              <SelectItem value="Viewer">Viewer</SelectItem>
                              <SelectItem value="Editor">Editor</SelectItem>
                              <SelectItem value="Administrator">Administrator</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      {prop.current_permission !== prop.requested_permission && (
                        <div className="mt-3 p-2 bg-blue-100 rounded text-center">
                          <span className="text-blue-700 text-sm font-medium">
                            {prop.current_permission === "None" || !prop.current_permission 
                              ? `새 권한: ${prop.requested_permission}` 
                              : `권한 변경: ${prop.current_permission} → ${prop.requested_permission}`
                            }
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>상태</Label>
                  <Select
                    value={editedPermission.status}
                    onValueChange={(value) => setEditedPermission({ ...editedPermission, status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">대기 중</SelectItem>
                      <SelectItem value="approved">승인됨</SelectItem>
                      <SelectItem value="rejected">거부됨</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>요청일</Label>
                  <Input value={formatDate(editedPermission.requested_at)} disabled />
                </div>
              </div>

              <div className="space-y-2">
                <Label>요청 사유 / 관리자 비고</Label>
                <Textarea
                  value={editedPermission.notes || ""}
                  onChange={(e) => setEditedPermission({ ...editedPermission, notes: e.target.value })}
                  rows={3}
                  placeholder="권한 요청 사유나 관리자 비고를 입력하세요..."
                />
              </div>

              {editedPermission.approved_at && (
                <div className="space-y-2">
                  <Label>승인일</Label>
                  <Input value={formatDate(editedPermission.approved_at)} disabled />
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={async () => {
              if (editedPermission) {
                try {
                  await typeSafeApiClient.updatePermission(editedPermission.id, {
                    status: editedPermission.status,
                    notes: editedPermission.notes
                  });
                  
                  // 목록 새로고침
                  await fetchPermissions();
                  
                  setIsEditDialogOpen(false);
                  setEditedPermission(null);
                } catch (error) {
                  console.error("권한 수정 실패:", error);
                }
              }
            }}>
              저장
            </Button>
          </DialogFooter>
        </DialogContent>
          </Dialog>
        </TabsContent>
      </Tabs>
    </div>
  );
}