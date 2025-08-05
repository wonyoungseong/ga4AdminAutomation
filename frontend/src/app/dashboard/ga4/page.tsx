"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { BarChart3, Building2, Users, Plus, Eye, Settings } from "lucide-react";
import { typeSafeApiClient } from "@/lib/api-client";

interface GA4Account {
  id: string;
  name: string;
  resource_name: string;
}

interface GA4Property {
  id: string;
  name: string;
  resource_name: string;
  account_id: string;
  create_time: string;
  currency_code: string;
  time_zone: string;
  industry_category: string;
}

interface GA4Permission {
  name: string;
  user: string;
  roles: string[];
  resource_name: string;
}

export default function GA4Page() {
  const [accounts, setAccounts] = useState<GA4Account[]>([]);
  const [properties, setProperties] = useState<GA4Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<GA4Property | null>(null);
  const [propertyPermissions, setPropertyPermissions] = useState<GA4Permission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isPermissionDialogOpen, setIsPermissionDialogOpen] = useState(false);
  const [newPermission, setNewPermission] = useState({
    user_email: "",
    permission_type: "viewer"
  });

  useEffect(() => {
    fetchGA4Data();
  }, []);

  const fetchGA4Data = async () => {
    try {
      setIsLoading(true);
      
      // GA4 계정 목록 조회
      const accountsResponse = await typeSafeApiClient.getGA4Accounts();
      setAccounts(accountsResponse.accounts || []);
      
      // GA4 Property 목록 조회
      const propertiesResponse = await typeSafeApiClient.getGA4Properties();
      setProperties(propertiesResponse.properties || []);
      
    } catch (error) {
      console.error("GA4 데이터 조회 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPropertyPermissions = async (propertyId: string) => {
    try {
      const response = await typeSafeApiClient.getPropertyPermissions(propertyId);
      setPropertyPermissions(response.permissions || []);
    } catch (error) {
      console.error("Property 권한 조회 실패:", error);
      setPropertyPermissions([]);
    }
  };

  const handleGrantPermission = async () => {
    if (!selectedProperty) return;
    
    try {
      await typeSafeApiClient.grantPropertyPermission(
        selectedProperty.id,
        newPermission.user_email,
        newPermission.permission_type
      );
      
      // 권한 목록 새로고침
      await fetchPropertyPermissions(selectedProperty.id);
      
      // 폼 초기화
      setNewPermission({ user_email: "", permission_type: "viewer" });
      setIsPermissionDialogOpen(false);
      
    } catch (error) {
      console.error("권한 부여 실패:", error);
    }
  };

  const handleRevokePermission = async (propertyId: string, bindingName: string) => {
    try {
      await typeSafeApiClient.revokePropertyPermission(propertyId, bindingName);
      
      // 권한 목록 새로고침
      await fetchPropertyPermissions(propertyId);
      
    } catch (error) {
      console.error("권한 철회 실패:", error);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRoleDisplayName = (roles: string[]) => {
    if (roles.includes('predefinedRoles/admin')) return 'Administrator';
    if (roles.includes('predefinedRoles/edit')) return 'Editor';
    if (roles.includes('predefinedRoles/collaborate')) return 'Marketer';
    if (roles.includes('predefinedRoles/read')) return 'Viewer';
    return 'Unknown';
  };

  const getRoleBadgeColor = (roles: string[]) => {
    if (roles.includes('predefinedRoles/admin')) return 'bg-red-100 text-red-800';
    if (roles.includes('predefinedRoles/edit')) return 'bg-blue-100 text-blue-800';
    if (roles.includes('predefinedRoles/collaborate')) return 'bg-orange-100 text-orange-800';
    if (roles.includes('predefinedRoles/read')) return 'bg-green-100 text-green-800';
    return 'bg-gray-100 text-gray-800';
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">GA4 관리</h1>
          <p className="text-muted-foreground">Google Analytics 4 계정 및 Property 관리</p>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-4">
              {[1, 2, 3].map((i) => (
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
          <h1 className="text-3xl font-bold tracking-tight">GA4 관리</h1>
          <p className="text-muted-foreground">Google Analytics 4 계정 및 Property 관리</p>
        </div>
        <Button onClick={fetchGA4Data}>
          <Eye className="mr-2 h-4 w-4" />
          새로고침
        </Button>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GA4 계정</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{accounts.length}</div>
            <p className="text-xs text-muted-foreground">
              접근 가능한 계정
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GA4 Property</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{properties.length}</div>
            <p className="text-xs text-muted-foreground">
              관리 중인 Property
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">선택된 Property</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {selectedProperty ? "1" : "0"}
            </div>
            <p className="text-xs text-muted-foreground">
              권한 관리 중
            </p>
          </CardContent>
        </Card>
      </div>

      {/* GA4 계정 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>GA4 계정 목록</CardTitle>
          <CardDescription>
            Service Account로 접근 가능한 GA4 계정들입니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {accounts.map((account) => (
              <div key={account.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium">{account.name}</p>
                  <p className="text-sm text-muted-foreground">ID: {account.id}</p>
                </div>
                <Badge variant="outline">계정</Badge>
              </div>
            ))}
            {accounts.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                접근 가능한 GA4 계정이 없습니다.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* GA4 Property 목록 */}
      <Card>
        <CardHeader>
          <CardTitle>GA4 Property 목록</CardTitle>
          <CardDescription>
            관리 가능한 GA4 Property들입니다. Property를 선택하여 권한을 관리하세요.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {properties.map((property) => (
              <div 
                key={property.id} 
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedProperty?.id === property.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => {
                  setSelectedProperty(property);
                  fetchPropertyPermissions(property.id);
                }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{property.name}</p>
                    <p className="text-sm text-muted-foreground">ID: {property.id}</p>
                    <div className="flex gap-2 mt-2">
                      <Badge variant="outline">{property.currency_code}</Badge>
                      <Badge variant="outline">{property.time_zone}</Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">
                      생성일: {formatDate(property.create_time)}
                    </p>
                    {selectedProperty?.id === property.id && (
                      <Badge className="mt-2">선택됨</Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {properties.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                관리 가능한 GA4 Property가 없습니다.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 선택된 Property의 권한 관리 */}
      {selectedProperty && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Property 권한 관리: {selectedProperty.name}</span>
              <Dialog open={isPermissionDialogOpen} onOpenChange={setIsPermissionDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    권한 부여
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>새 권한 부여</DialogTitle>
                    <DialogDescription>
                      {selectedProperty.name}에 사용자 권한을 부여합니다.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="user-email">사용자 이메일</Label>
                      <Input
                        id="user-email"
                        type="email"
                        value={newPermission.user_email}
                        onChange={(e) => setNewPermission({ ...newPermission, user_email: e.target.value })}
                        placeholder="user@example.com"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="permission-type">권한 유형</Label>
                      <Select
                        value={newPermission.permission_type}
                        onValueChange={(value) => setNewPermission({ ...newPermission, permission_type: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="viewer">Viewer (조회)</SelectItem>
                          <SelectItem value="analyst">Analyst (분석)</SelectItem>
                          <SelectItem value="marketer">Marketer (마케팅)</SelectItem>
                          <SelectItem value="editor">Editor (편집)</SelectItem>
                          <SelectItem value="administrator">Administrator (관리자)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsPermissionDialogOpen(false)}>
                      취소
                    </Button>
                    <Button onClick={handleGrantPermission}>
                      권한 부여
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardTitle>
            <CardDescription>
              Property ID: {selectedProperty.id}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {propertyPermissions.map((permission) => (
                <div key={permission.name} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{permission.user}</p>
                    <p className="text-sm text-muted-foreground">{permission.name}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getRoleBadgeColor(permission.roles)}>
                      {getRoleDisplayName(permission.roles)}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRevokePermission(selectedProperty.id, permission.name)}
                      className="text-red-600 hover:text-red-700"
                    >
                      철회
                    </Button>
                  </div>
                </div>
              ))}
              {propertyPermissions.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  이 Property에 부여된 권한이 없습니다.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}