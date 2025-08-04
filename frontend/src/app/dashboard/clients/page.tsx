"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
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
import { Textarea } from "@/components/ui/textarea";
import { Plus, Search, Edit, Trash2, Building2, Users, BarChart3 } from "lucide-react";
import { apiClient } from "@/lib/api";

interface Client {
  id: number;
  name: string;
  company_name: string;
  contact_email: string;
  contact_phone?: string;
  ga4_property_id: string;
  is_active: boolean;
  created_at: string;
  last_updated: string;
  user_count: number;
  description?: string;
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [filteredClients, setFilteredClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [newClient, setNewClient] = useState({
    name: "",
    company_name: "",
    contact_email: "",
    contact_phone: "",
    ga4_property_id: "",
    description: "",
  });

  useEffect(() => {
    fetchClients();
  }, []);

  useEffect(() => {
    // 검색 필터링
    const filtered = clients.filter(client =>
      client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      client.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      client.contact_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      client.ga4_property_id.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredClients(filtered);
  }, [clients, searchTerm]);

  const fetchClients = async () => {
    try {
      // 실제 API 호출
      const response = await apiClient.getClients();
      setClients(response || []);
    } catch (error) {
      console.error("클라이언트 목록 조회 실패:", error);
      setClients([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateClient = async () => {
    try {
      const response = await apiClient.createClient(newClient);
      setClients([...clients, response]);
      setNewClient({
        name: "",
        company_name: "",
        contact_email: "",
        contact_phone: "",
        ga4_property_id: "",
        description: "",
      });
      setIsCreateDialogOpen(false);
    } catch (error) {
      console.error("클라이언트 생성 실패:", error);
      alert("클라이언트 생성에 실패했습니다.");
    }
  };

  const handleEditClient = async () => {
    if (!selectedClient) return;
    
    try {
      const response = await apiClient.updateClient(selectedClient.id, selectedClient);
      setClients(clients.map(client => 
        client.id === selectedClient.id ? response : client
      ));
      setIsEditDialogOpen(false);
      setSelectedClient(null);
    } catch (error) {
      console.error("클라이언트 수정 실패:", error);
      alert("클라이언트 수정에 실패했습니다.");
    }
  };

  const handleDeleteClient = async (clientId: number) => {
    if (confirm("정말로 이 클라이언트를 삭제하시겠습니까?")) {
      try {
        await apiClient.deleteClient(clientId);
        setClients(clients.filter(client => client.id !== clientId));
      } catch (error) {
        console.error("클라이언트 삭제 실패:", error);
        alert("클라이언트 삭제에 실패했습니다.");
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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">클라이언트 관리</h1>
          <p className="text-muted-foreground">GA4 클라이언트를 관리합니다</p>
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
          <h1 className="text-3xl font-bold tracking-tight">클라이언트 관리</h1>
          <p className="text-muted-foreground">GA4 클라이언트를 관리합니다</p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              새 클라이언트
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>새 클라이언트 등록</DialogTitle>
              <DialogDescription>
                새로운 클라이언트를 시스템에 등록합니다.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="new-name">클라이언트명</Label>
                  <Input
                    id="new-name"
                    value={newClient.name}
                    onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
                    placeholder="ABC 마케팅"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new-company-name">회사명</Label>
                  <Input
                    id="new-company-name"
                    value={newClient.company_name}
                    onChange={(e) => setNewClient({ ...newClient, company_name: e.target.value })}
                    placeholder="ABC 회사"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="new-contact-email">담당자 이메일</Label>
                  <Input
                    id="new-contact-email"
                    type="email"
                    value={newClient.contact_email}
                    onChange={(e) => setNewClient({ ...newClient, contact_email: e.target.value })}
                    placeholder="contact@example.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new-contact-phone">담당자 전화번호</Label>
                  <Input
                    id="new-contact-phone"
                    value={newClient.contact_phone}
                    onChange={(e) => setNewClient({ ...newClient, contact_phone: e.target.value })}
                    placeholder="02-1234-5678"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-ga4-property-id">GA4 속성 ID</Label>
                <Input
                  id="new-ga4-property-id"
                  value={newClient.ga4_property_id}
                  onChange={(e) => setNewClient({ ...newClient, ga4_property_id: e.target.value })}
                  placeholder="GA_123456789"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-description">설명</Label>
                <Textarea
                  id="new-description"
                  value={newClient.description}
                  onChange={(e) => setNewClient({ ...newClient, description: e.target.value })}
                  placeholder="클라이언트에 대한 간단한 설명"
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleCreateClient}>등록</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 클라이언트</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{clients.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">활성 클라이언트</CardTitle>
            <BarChart3 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {clients.filter(c => c.is_active).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 사용자</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {clients.reduce((sum, client) => sum + client.user_count, 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 사용자/클라이언트</CardTitle>
            <Users className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {clients.length > 0 ? Math.round(clients.reduce((sum, client) => sum + client.user_count, 0) / clients.length) : 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>클라이언트 목록</CardTitle>
          <CardDescription>
            총 {clients.length}개의 클라이언트가 등록되어 있습니다.
          </CardDescription>
          <div className="flex items-center space-x-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="클라이언트 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>클라이언트명</TableHead>
                <TableHead>회사명</TableHead>
                <TableHead>담당자</TableHead>
                <TableHead>GA4 속성 ID</TableHead>
                <TableHead>사용자 수</TableHead>
                <TableHead>상태</TableHead>
                <TableHead>최종 업데이트</TableHead>
                <TableHead className="text-right">작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredClients.map((client) => (
                <TableRow key={client.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{client.name}</div>
                      {client.description && (
                        <div className="text-sm text-muted-foreground">{client.description}</div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{client.company_name}</TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{client.contact_email}</div>
                      {client.contact_phone && (
                        <div className="text-sm text-muted-foreground">{client.contact_phone}</div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{client.ga4_property_id}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      {client.user_count}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={client.is_active ? "default" : "secondary"}>
                      {client.is_active ? "활성" : "비활성"}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDate(client.last_updated)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedClient(client);
                          setIsEditDialogOpen(true);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteClient(client.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 수정 다이얼로그 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>클라이언트 수정</DialogTitle>
            <DialogDescription>
              클라이언트 정보를 수정합니다.
            </DialogDescription>
          </DialogHeader>
          {selectedClient && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-name">클라이언트명</Label>
                  <Input
                    id="edit-name"
                    value={selectedClient.name}
                    onChange={(e) => setSelectedClient({ ...selectedClient, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-company-name">회사명</Label>
                  <Input
                    id="edit-company-name"
                    value={selectedClient.company_name}
                    onChange={(e) => setSelectedClient({ ...selectedClient, company_name: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-contact-email">담당자 이메일</Label>
                  <Input
                    id="edit-contact-email"
                    type="email"
                    value={selectedClient.contact_email}
                    onChange={(e) => setSelectedClient({ ...selectedClient, contact_email: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-contact-phone">담당자 전화번호</Label>
                  <Input
                    id="edit-contact-phone"
                    value={selectedClient.contact_phone || ""}
                    onChange={(e) => setSelectedClient({ ...selectedClient, contact_phone: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-ga4-property-id">GA4 속성 ID</Label>
                <Input
                  id="edit-ga4-property-id"
                  value={selectedClient.ga4_property_id}
                  onChange={(e) => setSelectedClient({ ...selectedClient, ga4_property_id: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-description">설명</Label>
                <Textarea
                  id="edit-description"
                  value={selectedClient.description || ""}
                  onChange={(e) => setSelectedClient({ ...selectedClient, description: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-status">상태</Label>
                <select
                  id="edit-status"
                  value={selectedClient.is_active ? "active" : "inactive"}
                  onChange={(e) => setSelectedClient({ ...selectedClient, is_active: e.target.value === "active" })}
                  className="w-full p-2 border rounded-md"
                >
                  <option value="active">활성</option>
                  <option value="inactive">비활성</option>
                </select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleEditClient}>저장</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}