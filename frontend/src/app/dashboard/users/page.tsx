"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  UserPlus, 
  Clock, 
  CheckCircle, 
  XCircle, 
  MoreHorizontal,
  Eye,
  Shield,
  AlertTriangle,
  Activity,
  Calendar,
  Building,
  Mail,
  Users,
  Filter,
  Download,
  RefreshCw,
  UserCheck,
  UserX
} from "lucide-react";
import { typeSafeApiClient } from "@/lib/api-client";
import { User, Client, UserCreate, UserRole } from "@/types/api";
import { toast } from "sonner";

// Types for enhanced user management
interface UserFormErrors {
  email?: string;
  name?: string;
  password?: string;
  company?: string;
}

interface UserStats {
  total: number;
  active: number;
  pending: number;
  byRole: Record<UserRole, number>;
}

export default function UsersPage() {
  // Core state
  const [users, setUsers] = useState<User[]>([]);
  const [pendingUsers, setPendingUsers] = useState<User[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // UI state
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [activeTab, setActiveTab] = useState("all");
  
  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isRegisterDialogOpen, setIsRegisterDialogOpen] = useState(false);
  const [isUserDetailDialogOpen, setIsUserDetailDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  
  // Form states
  const [newUser, setNewUser] = useState({
    email: "",
    name: "",
    role: "" as User['role'],
    password: "",
    company: "",
  });
  const [registrationData, setRegistrationData] = useState<UserCreate>({
    email: "",
    name: "",
    company: "",
    password: "",
    role: "Requester",
    requested_client_id: undefined,
    business_justification: "",
  });
  const [formErrors, setFormErrors] = useState<UserFormErrors>({});

  useEffect(() => {
    fetchUsers();
    fetchClients();
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      if (!isLoading) {
        fetchUsers(true); // Silent refresh
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Enhanced filtering with memoization
  const filteredUsers = useMemo(() => {
    const currentUsers = activeTab === 'pending' ? pendingUsers : users;
    return currentUsers.filter(user => {
      const matchesSearch = 
        user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.role.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesRole = roleFilter === 'all' || user.role === roleFilter;
      const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
      
      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, pendingUsers, searchTerm, roleFilter, statusFilter, activeTab]);
  
  // User statistics
  const userStats = useMemo((): UserStats => {
    const allUsers = [...users, ...pendingUsers];
    return {
      total: allUsers.length,
      active: users.length,
      pending: pendingUsers.length,
      byRole: allUsers.reduce((acc, user) => {
        acc[user.role] = (acc[user.role] || 0) + 1;
        return acc;
      }, {} as Record<UserRole, number>)
    };
  }, [users, pendingUsers]);

  const fetchUsers = async (silent = false) => {
    if (!silent) {
      setIsLoading(true);
    } else {
      setIsRefreshing(true);
    }
    
    try {
      const response = await typeSafeApiClient.getUsers(1, 1000); // Get all users
      const allUsers = response.items || [];
      
      // Separate active and pending users
      const activeUsers = allUsers.filter(user => user.status === 'active');
      const pendingUsersList = allUsers.filter(user => user.status === 'inactive' || user.status === 'suspended');
      
      setUsers(activeUsers);
      setPendingUsers(pendingUsersList);
      
      if (silent) {
        // Show subtle notification for silent updates
        const newPendingCount = pendingUsersList.length;
        const currentPendingCount = pendingUsers.length;
        if (newPendingCount > currentPendingCount) {
          toast.info(`${newPendingCount - currentPendingCount}개의 새로운 승인 요청이 있습니다.`);
        }
      }
    } catch (error) {
      console.error("사용자 목록 조회 실패:", error);
      if (!silent) {
        toast.error("사용자 목록을 불러오는데 실패했습니다.");
      }
      setUsers([]);
      setPendingUsers([]);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await typeSafeApiClient.getClients();
      setClients(response.items || []);
    } catch (error) {
      console.error("클라이언트 목록 조회 실패:", error);
      // Don't show error toast for clients as it's optional
    }
  };

  // Form validation
  const validateForm = (data: typeof newUser | UserCreate, isRegistration = false): boolean => {
    const errors: UserFormErrors = {};
    
    if (!data.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
      errors.email = "유효한 이메일 주소를 입력해주세요.";
    }
    
    if (!data.name || data.name.trim().length < 2) {
      errors.name = "이름은 2자 이상이어야 합니다.";
    }
    
    if (!data.password || data.password.length < 8) {
      errors.password = "비밀번호는 8자 이상이어야 합니다.";
    }
    
    if (isRegistration && !data.company?.trim()) {
      errors.company = "회사명을 입력해주세요.";
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  const handleCreateUser = async () => {
    if (!validateForm(newUser)) {
      toast.error("입력 정보를 확인해주세요.");
      return;
    }
    
    try {
      const response = await typeSafeApiClient.createUser(newUser);
      setUsers([...users, response]);
      setNewUser({ email: "", name: "", role: "" as User['role'], password: "", company: "" });
      setFormErrors({});
      setIsCreateDialogOpen(false);
      toast.success("사용자가 성공적으로 생성되었습니다.");
    } catch (error) {
      console.error("사용자 생성 실패:", error);
      toast.error("사용자 생성에 실패했습니다.");
    }
  };

  const handleRegisterUser = async () => {
    if (!validateForm(registrationData, true)) {
      toast.error("입력 정보를 확인해주세요.");
      return;
    }
    
    try {
      const response = await typeSafeApiClient.registerUser(registrationData);
      // Add to pending users if status is inactive
      if (response.status === 'inactive') {
        setPendingUsers([...pendingUsers, response]);
        toast.success("사용자 등록이 완료되었습니다. 관리자 승인을 기다려주세요.");
      } else {
        setUsers([...users, response]);
        toast.success("사용자 등록이 완료되었습니다.");
      }
      setRegistrationData({
        email: "",
        name: "",
        company: "",
        password: "",
        role: "Requester",
        requested_client_id: undefined,
        business_justification: "",
      });
      setFormErrors({});
      setIsRegisterDialogOpen(false);
    } catch (error) {
      console.error("사용자 등록 실패:", error);
      toast.error("사용자 등록에 실패했습니다.");
    }
  };

  const handleApproveUser = async (userId: number) => {
    try {
      const response = await typeSafeApiClient.updateUser(userId, { status: 'active' });
      // Move from pending to active users
      setPendingUsers(pendingUsers.filter(user => user.id !== userId));
      setUsers([...users, response]);
      toast.success("사용자가 승인되었습니다.");
    } catch (error) {
      console.error("사용자 승인 실패:", error);
      toast.error("사용자 승인에 실패했습니다.");
    }
  };

  const handleRejectUser = async (userId: number) => {
    try {
      await typeSafeApiClient.deleteUser(userId);
      setPendingUsers(pendingUsers.filter(user => user.id !== userId));
      toast.success("사용자 등록이 거절되었습니다.");
    } catch (error) {
      console.error("사용자 거절 실패:", error);
      toast.error("사용자 거절에 실패했습니다.");
    }
  };

  const handleEditUser = async () => {
    if (!selectedUser) return;
    
    try {
      const response = await typeSafeApiClient.updateUser(selectedUser.id, {
        name: selectedUser.name,
        company: selectedUser.company,
        role: selectedUser.role,
        status: selectedUser.status
      });
      
      // Update in the appropriate list
      if (response.status === 'active') {
        setUsers(users.map(user => 
          user.id === selectedUser.id ? response : user
        ));
        // Remove from pending if it was there
        setPendingUsers(pendingUsers.filter(user => user.id !== selectedUser.id));
      } else {
        setPendingUsers(pendingUsers.map(user => 
          user.id === selectedUser.id ? response : user
        ));
        // Remove from active if it was there
        setUsers(users.filter(user => user.id !== selectedUser.id));
      }
      
      setIsEditDialogOpen(false);
      setSelectedUser(null);
      toast.success("사용자 정보가 업데이트되었습니다.");
    } catch (error) {
      console.error("사용자 수정 실패:", error);
      toast.error("사용자 수정에 실패했습니다.");
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (confirm("정말로 이 사용자를 삭제하시겠습니까?")) {
      try {
        await typeSafeApiClient.deleteUser(userId);
        setUsers(users.filter(user => user.id !== userId));
      } catch (error) {
        console.error("사용자 삭제 실패:", error);
        toast.error("사용자 삭제에 실패했습니다.");
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

  const getRoleColor = (role: string) => {
    switch (role) {
      case "Super Admin":
        return "bg-red-100 text-red-800";
      case "Admin":
        return "bg-blue-100 text-blue-800";
      case "Requester":
        return "bg-green-100 text-green-800";
      case "Viewer":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">사용자 관리</h1>
          <p className="text-muted-foreground">시스템 사용자를 관리합니다</p>
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
          <h1 className="text-3xl font-bold tracking-tight">사용자 관리</h1>
          <p className="text-muted-foreground">시스템 사용자를 관리합니다</p>
        </div>
        
        <div className="flex gap-2">
          <Dialog open={isRegisterDialogOpen} onOpenChange={setIsRegisterDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <UserPlus className="mr-2 h-4 w-4" />
                사용자 등록
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>새 사용자 등록</DialogTitle>
                <DialogDescription>
                  시스템에 사용자 등록을 신청합니다. 관리자 승인이 필요할 수 있습니다.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="reg-email">이메일</Label>
                  <Input
                    id="reg-email"
                    type="email"
                    value={registrationData.email}
                    onChange={(e) => setRegistrationData({ ...registrationData, email: e.target.value })}
                    placeholder="user@example.com"
                    className={formErrors.email ? 'border-red-500' : ''}
                  />
                  {formErrors.email && (
                    <p className="text-sm text-red-600">{formErrors.email}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reg-name">이름</Label>
                  <Input
                    id="reg-name"
                    value={registrationData.name}
                    onChange={(e) => setRegistrationData({ ...registrationData, name: e.target.value })}
                    placeholder="사용자 이름"
                    className={formErrors.name ? 'border-red-500' : ''}
                  />
                  {formErrors.name && (
                    <p className="text-sm text-red-600">{formErrors.name}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reg-company">회사</Label>
                  <Input
                    id="reg-company"
                    value={registrationData.company}
                    onChange={(e) => setRegistrationData({ ...registrationData, company: e.target.value })}
                    placeholder="회사명"
                    className={formErrors.company ? 'border-red-500' : ''}
                  />
                  {formErrors.company && (
                    <p className="text-sm text-red-600">{formErrors.company}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reg-password">비밀번호</Label>
                  <Input
                    id="reg-password"
                    type="password"
                    value={registrationData.password}
                    onChange={(e) => setRegistrationData({ ...registrationData, password: e.target.value })}
                    placeholder="최소 8자"
                    className={formErrors.password ? 'border-red-500' : ''}
                  />
                  {formErrors.password && (
                    <p className="text-sm text-red-600">{formErrors.password}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reg-role">요청 역할</Label>
                  <Select 
                    value={registrationData.role} 
                    onValueChange={(value) => setRegistrationData({ ...registrationData, role: value as User['role'] })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="역할을 선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Requester">Requester</SelectItem>
                      <SelectItem value="Admin">Admin</SelectItem>
                      <SelectItem value="Super Admin">Super Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {clients.length > 0 && (
                  <div className="space-y-2">
                    <Label htmlFor="reg-client">요청 클라이언트 (선택사항)</Label>
                    <Select 
                      value={registrationData.requested_client_id?.toString() || ""} 
                      onValueChange={(value) => setRegistrationData({ 
                        ...registrationData, 
                        requested_client_id: value ? parseInt(value) : undefined 
                      })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="클라이언트 선택 (선택사항)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">선택하지 않음</SelectItem>
                        {clients.map((client) => (
                          <SelectItem key={client.id} value={client.id.toString()}>
                            {client.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="reg-justification">사업적 근거 (선택사항)</Label>
                  <Textarea
                    id="reg-justification"
                    value={registrationData.business_justification || ""}
                    onChange={(e) => setRegistrationData({ ...registrationData, business_justification: e.target.value })}
                    placeholder="접근이 필요한 이유를 설명해주세요..."
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsRegisterDialogOpen(false)}>
                  취소
                </Button>
                <Button onClick={handleRegisterUser}>등록 신청</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                새 사용자
              </Button>
            </DialogTrigger>
            <DialogContent>
            <DialogHeader>
              <DialogTitle>새 사용자 생성</DialogTitle>
              <DialogDescription>
                새로운 사용자를 시스템에 추가합니다.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="new-email">이메일</Label>
                <Input
                  id="new-email"
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  placeholder="user@example.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-name">이름</Label>
                <Input
                  id="new-name"
                  value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  placeholder="사용자 이름"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-company">회사</Label>
                <Input
                  id="new-company"
                  value={newUser.company}
                  onChange={(e) => setNewUser({ ...newUser, company: e.target.value })}
                  placeholder="회사명"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-role">역할</Label>
                <Select value={newUser.role} onValueChange={(value) => setNewUser({ ...newUser, role: value as User['role'] })}>
                  <SelectTrigger>
                    <SelectValue placeholder="역할을 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Super Admin">Super Admin</SelectItem>
                    <SelectItem value="Admin">Admin</SelectItem>
                    <SelectItem value="Requester">Requester</SelectItem>
                    <SelectItem value="Viewer">Viewer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">비밀번호</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  placeholder="비밀번호"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleCreateUser}>생성</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="all" className="flex items-center gap-2">
            <span>활성 사용자</span>
            <Badge variant="secondary">{users.length}</Badge>
          </TabsTrigger>
          <TabsTrigger value="pending" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            <span>승인 대기</span>
            <Badge variant="secondary">{pendingUsers.length}</Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>활성 사용자 목록</CardTitle>
              <CardDescription>
                총 {users.length}명의 활성 사용자가 등록되어 있습니다.
              </CardDescription>
              <div className="flex items-center space-x-2">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="사용자 검색..."
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
                    <TableHead>이름</TableHead>
                    <TableHead>이메일</TableHead>
                    <TableHead>역할</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>마지막 로그인</TableHead>
                    <TableHead>생성일</TableHead>
                    <TableHead className="text-right">작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.name}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Badge className={getRoleColor(user.role)}>
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={user.status === 'active' ? "default" : "secondary"}>
                          {user.status === 'active' ? "활성" : "비활성"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {user.last_login_at ? formatDate(user.last_login_at) : "없음"}
                      </TableCell>
                      <TableCell>{formatDate(user.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedUser(user);
                              setIsEditDialogOpen(true);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteUser(user.id)}
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
        </TabsContent>

        <TabsContent value="pending" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>승인 대기 사용자</CardTitle>
              <CardDescription>
                {pendingUsers.length}명의 사용자가 승인을 기다리고 있습니다.
              </CardDescription>
              <div className="flex items-center space-x-2">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="대기 사용자 검색..."
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
                    <TableHead>이름</TableHead>
                    <TableHead>이메일</TableHead>
                    <TableHead>회사</TableHead>
                    <TableHead>요청 역할</TableHead>
                    <TableHead>등록일</TableHead>
                    <TableHead className="text-right">승인/거절</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.name}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>{user.company || "-"}</TableCell>
                      <TableCell>
                        <Badge className={getRoleColor(user.role)}>
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(user.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleApproveUser(user.id)}
                            className="text-green-600 hover:text-green-700"
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            승인
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRejectUser(user.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            거절
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 수정 다이얼로그 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>사용자 수정</DialogTitle>
            <DialogDescription>
              사용자 정보를 수정합니다.
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="edit-email">이메일</Label>
                <Input
                  id="edit-email"
                  type="email"
                  value={selectedUser.email}
                  onChange={(e) => setSelectedUser({ ...selectedUser, email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-name">이름</Label>
                <Input
                  id="edit-name"
                  value={selectedUser.name}
                  onChange={(e) => setSelectedUser({ ...selectedUser, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-role">역할</Label>
                <Select
                  value={selectedUser.role}
                  onValueChange={(value) => setSelectedUser({ ...selectedUser, role: value as User['role'] })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Super Admin">Super Admin</SelectItem>
                    <SelectItem value="Admin">Admin</SelectItem>
                    <SelectItem value="Requester">Requester</SelectItem>
                    <SelectItem value="Viewer">Viewer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-status">상태</Label>
                <Select
                  value={selectedUser.status === 'active' ? "active" : "inactive"}
                  onValueChange={(value) => setSelectedUser({ ...selectedUser, status: value === "active" ? 'active' : 'inactive' })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">활성</SelectItem>
                    <SelectItem value="inactive">비활성</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleEditUser}>저장</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}