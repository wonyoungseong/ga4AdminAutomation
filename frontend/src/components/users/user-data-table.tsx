"use client";

import React, { useState, useMemo } from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  SortingState,
  ColumnFiltersState,
  VisibilityState,
  RowSelectionState,
} from '@tanstack/react-table';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { RoleBadge } from '@/components/rbac/role-badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  MoreHorizontal, 
  ArrowUpDown, 
  Search, 
  Filter,
  UserPlus,
  Download,
  Trash2,
  Edit,
  Eye,
  Settings2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { User, UserRole, UserStatus } from '@/types/api';
import { cn } from '@/lib/utils';

interface UserDataTableProps {
  data: User[];
  loading?: boolean;
  onUserCreate?: () => void;
  onUserEdit?: (user: User) => void;
  onUserView?: (user: User) => void;
  onUserDelete?: (users: User[]) => void;
  onBulkAction?: (action: string, users: User[]) => void;
  className?: string;
}

export function UserDataTable({
  data,
  loading = false,
  onUserCreate,
  onUserEdit,
  onUserView,
  onUserDelete,
  onBulkAction,
  className
}: UserDataTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [globalFilter, setGlobalFilter] = useState('');

  // 사용자 이름 이니셜 생성
  const getUserInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // 상태별 스타일링
  const getStatusBadgeStyle = (status: UserStatus) => {
    const styles = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
      suspended: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    };
    return styles[status];
  };

  const getStatusLabel = (status: UserStatus) => {
    const labels = {
      active: '활성',
      inactive: '비활성', 
      suspended: '정지됨'
    };
    return labels[status];
  };

  // 테이블 컬럼 정의
  const columns: ColumnDef<User>[] = useMemo(() => [
    {
      id: "select",
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected()}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="모든 사용자 선택"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label={`${row.original.name} 선택`}
        />
      ),
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "name",
      header: ({ column }) => (
        <Button
          variant="ghost"
          className="h-auto p-0 font-semibold"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          사용자
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const user = row.original;
        return (
          <div className="flex items-center space-x-3">
            <Avatar className="h-8 w-8">
              <AvatarImage src={user.avatar} alt={user.name} />
              <AvatarFallback className="text-xs">
                {getUserInitials(user.name)}
              </AvatarFallback>
            </Avatar>
            <div>
              <div className="font-medium korean-text">{user.name}</div>
              <div className="text-sm text-muted-foreground">{user.email}</div>
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: "role",
      header: ({ column }) => (
        <Button
          variant="ghost"
          className="h-auto p-0 font-semibold"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          역할
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const user = row.original;
        return <RoleBadge role={user.role} status={user.status} size="sm" />;
      },
    },
    {
      accessorKey: "status",
      header: ({ column }) => (
        <Button
          variant="ghost"
          className="h-auto p-0 font-semibold"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          상태
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const status = row.original.status;
        return (
          <Badge className={cn('korean-text', getStatusBadgeStyle(status))}>
            {getStatusLabel(status)}
          </Badge>
        );
      },
    },
    {
      accessorKey: "organization",
      header: "조직",
      cell: ({ row }) => (
        <div className="korean-text">{row.original.organization || '-'}</div>
      ),
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <Button
          variant="ghost"
          className="h-auto p-0 font-semibold"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          등록일
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const date = new Date(row.original.created_at);
        return (
          <div className="text-sm">
            {date.toLocaleDateString('ko-KR')}
          </div>
        );
      },
    },
    {
      accessorKey: "last_login",
      header: "최근 로그인",
      cell: ({ row }) => {
        const lastLogin = row.original.last_login;
        if (!lastLogin) return <span className="text-muted-foreground">-</span>;
        
        const date = new Date(lastLogin);
        const now = new Date();
        const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
        
        if (diffHours < 24) {
          return <span className="text-sm">{diffHours}시간 전</span>;
        } else {
          return <span className="text-sm">{date.toLocaleDateString('ko-KR')}</span>;
        }
      },
    },
    {
      id: "actions",
      enableHiding: false,
      cell: ({ row }) => {
        const user = row.original;
        
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">메뉴 열기</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>작업</DropdownMenuLabel>
              <DropdownMenuItem
                onClick={() => navigator.clipboard.writeText(user.email)}
              >
                이메일 복사
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {onUserView && (
                <DropdownMenuItem onClick={() => onUserView(user)}>
                  <Eye className="mr-2 h-4 w-4" />
                  상세보기
                </DropdownMenuItem>
              )}
              {onUserEdit && (
                <DropdownMenuItem onClick={() => onUserEdit(user)}>
                  <Edit className="mr-2 h-4 w-4" />
                  수정하기
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              {onUserDelete && (
                <DropdownMenuItem 
                  onClick={() => onUserDelete([user])}
                  className="text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  삭제하기
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ], [onUserView, onUserEdit, onUserDelete]);

  const table = useReactTable({
    data,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: 'includesString',
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      globalFilter,
    },
  });

  const selectedUsers = table.getFilteredSelectedRowModel().rows.map(row => row.original);

  return (
    <div className={cn('space-y-4', className)}>
      {/* 툴바 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="사용자 검색..."
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="pl-8 w-64"
            />
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <Filter className="mr-2 h-4 w-4" />
                필터
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuLabel>역할별 필터</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {['Super Admin', 'Admin', 'Requester', 'Viewer'].map((role) => (
                <DropdownMenuCheckboxItem
                  key={role}
                  checked={columnFilters.some(
                    filter => filter.id === 'role' && filter.value === role
                  )}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setColumnFilters(prev => [...prev, { id: 'role', value: role }]);
                    } else {
                      setColumnFilters(prev => 
                        prev.filter(filter => !(filter.id === 'role' && filter.value === role))
                      );
                    }
                  }}
                >
                  {role}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <Settings2 className="mr-2 h-4 w-4" />
                컬럼
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {table
                .getAllColumns()
                .filter((column) => column.getCanHide())
                .map((column) => {
                  return (
                    <DropdownMenuCheckboxItem
                      key={column.id}
                      className="capitalize"
                      checked={column.getIsVisible()}
                      onCheckedChange={(value) =>
                        column.toggleVisibility(!!value)
                      }
                    >
                      {column.id}
                    </DropdownMenuCheckboxItem>
                  );
                })}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex items-center space-x-2">
          {selectedUsers.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">
                {selectedUsers.length}개 선택됨
              </span>
              
              {onBulkAction && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      일괄 작업
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem
                      onClick={() => onBulkAction('activate', selectedUsers)}
                    >
                      활성화
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => onBulkAction('deactivate', selectedUsers)}
                    >
                      비활성화
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => onBulkAction('export', selectedUsers)}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      내보내기
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => onBulkAction('delete', selectedUsers)}
                      className="text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      삭제하기
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          )}
          
          {onUserCreate && (
            <Button onClick={onUserCreate} size="sm">
              <UserPlus className="mr-2 h-4 w-4" />
              사용자 추가
            </Button>
          )}
        </div>
      </div>

      {/* 테이블 */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {loading ? (
              // 로딩 상태
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={index}>
                  {columns.map((_, colIndex) => (
                    <TableCell key={colIndex}>
                      <div className="h-4 bg-muted animate-pulse rounded" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  <div className="text-muted-foreground korean-text">
                    등록된 사용자가 없습니다.
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* 페이지네이션 */}
      <div className="flex items-center justify-between space-x-2 py-4">
        <div className="flex-1 text-sm text-muted-foreground">
          {table.getFilteredSelectedRowModel().rows.length}개 중{" "}
          {table.getFilteredRowModel().rows.length}개 선택됨
        </div>
        <div className="flex items-center space-x-6 lg:space-x-8">
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium">페이지당 표시</p>
            <select
              value={table.getState().pagination.pageSize}
              onChange={(e) => {
                table.setPageSize(Number(e.target.value));
              }}
              className="h-8 w-[70px] rounded-md border border-input bg-background px-3 py-1 text-sm"
            >
              {[10, 20, 30, 40, 50].map((pageSize) => (
                <option key={pageSize} value={pageSize}>
                  {pageSize}
                </option>
              ))}
            </select>
          </div>
          <div className="flex w-[100px] items-center justify-center text-sm font-medium">
            페이지 {table.getState().pagination.pageIndex + 1} /{" "}
            {table.getPageCount()}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <span className="sr-only">이전 페이지</span>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              <span className="sr-only">다음 페이지</span>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}