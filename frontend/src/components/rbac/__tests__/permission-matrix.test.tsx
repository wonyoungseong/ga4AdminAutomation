/**
 * PermissionMatrix Component Tests
 * 
 * Comprehensive testing for permission management matrix component
 * covering permission management, role hierarchy validation, Korean localization,
 * and interactive functionality.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PermissionMatrix, PermissionSummary } from '../permission-matrix';
import { UserRole, PermissionLevel } from '@/types/api';

// Mock permission data
const mockPermissions = [
  {
    id: 'user.create',
    name: '사용자 생성',
    description: '새로운 사용자를 생성할 수 있습니다',
    category: 'user_management',
    requiredRole: 'Admin' as UserRole,
  },
  {
    id: 'user.edit',
    name: '사용자 편집',
    description: '기존 사용자 정보를 수정할 수 있습니다',
    category: 'user_management',
    requiredRole: 'Admin' as UserRole,
  },
  {
    id: 'user.delete',
    name: '사용자 삭제',
    description: '사용자를 삭제할 수 있습니다',
    category: 'user_management',
    requiredRole: 'Super Admin' as UserRole,
  },
  {
    id: 'permission.grant',
    name: '권한 부여',
    description: '다른 사용자에게 권한을 부여할 수 있습니다',
    category: 'permission_management',
    requiredRole: 'Admin' as UserRole,
  },
  {
    id: 'audit.view',
    name: '감사 로그 조회',
    description: '시스템 감사 로그를 조회할 수 있습니다',
    category: 'audit_logs',
    requiredRole: 'Requester' as UserRole,
  },
  {
    id: 'system.config',
    name: '시스템 설정',
    description: '시스템 전체 설정을 변경할 수 있습니다',
    category: 'system_config',
    requiredRole: 'Super Admin' as UserRole,
  },
];

describe('PermissionMatrix Component', () => {
  const mockOnPermissionChange = jest.fn();

  beforeEach(() => {
    mockOnPermissionChange.mockClear();
  });

  describe('Basic Rendering', () => {
    it('should render permission matrix with Korean title', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      expect(screen.getByText('권한 매트릭스')).toBeInTheDocument();
    });

    it('should display user role badge', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      expect(screen.getByText('관리자')).toBeInTheDocument();
    });

    it('should group permissions by category', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      expect(screen.getByText('사용자 관리')).toBeInTheDocument();
      expect(screen.getByText('권한 관리')).toBeInTheDocument();
      expect(screen.getByText('감사 로그')).toBeInTheDocument();
      expect(screen.getByText('시스템 설정')).toBeInTheDocument();
    });

    it('should display permission count for each category', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      expect(screen.getByText('3개 권한')).toBeInTheDocument(); // user_management
      expect(screen.getByText('1개 권한')).toBeInTheDocument(); // permission_management, audit_logs, system_config
    });
  });

  describe('Category Expansion', () => {
    it('should expand category when clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      expect(categoryButton).toBeInTheDocument();

      await user.click(categoryButton!);

      // Should show expanded content
      expect(screen.getByText('사용자 생성')).toBeInTheDocument();
      expect(screen.getByText('사용자 편집')).toBeInTheDocument();
      expect(screen.getByText('사용자 삭제')).toBeInTheDocument();
    });

    it('should collapse category when clicked again', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      
      // Expand
      await user.click(categoryButton!);
      expect(screen.getByText('사용자 생성')).toBeInTheDocument();

      // Collapse
      await user.click(categoryButton!);
      expect(screen.queryByText('사용자 생성')).not.toBeInTheDocument();
    });

    it('should show expansion indicator', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      
      // Should show collapsed indicator
      expect(screen.getByText('▶')).toBeInTheDocument();

      await user.click(categoryButton!);

      // Should show expanded indicator
      expect(screen.getByText('▼')).toBeInTheDocument();
    });
  });

  describe('Permission Table Structure', () => {
    beforeEach(async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      // Expand user management category
      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);
    });

    it('should display table headers in Korean', () => {
      expect(screen.getByText('권한명')).toBeInTheDocument();
      expect(screen.getByText('설명')).toBeInTheDocument();
      expect(screen.getByText('읽기')).toBeInTheDocument();
      expect(screen.getByText('편집')).toBeInTheDocument();
      expect(screen.getByText('관리')).toBeInTheDocument();
      expect(screen.getByText('필요 역할')).toBeInTheDocument();
    });

    it('should display permission details', () => {
      expect(screen.getByText('사용자 생성')).toBeInTheDocument();
      expect(screen.getByText('새로운 사용자를 생성할 수 있습니다')).toBeInTheDocument();
      expect(screen.getByText('사용자 편집')).toBeInTheDocument();
      expect(screen.getByText('기존 사용자 정보를 수정할 수 있습니다')).toBeInTheDocument();
    });

    it('should display required role badges', () => {
      // Should show Admin badge for user.create and user.edit
      const adminBadges = screen.getAllByText('관리자');
      expect(adminBadges.length).toBeGreaterThan(0);

      // Should show Super Admin badge for user.delete
      expect(screen.getByText('최고 관리자')).toBeInTheDocument();
    });
  });

  describe('Permission Checkboxes', () => {
    beforeEach(async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      // Expand user management category
      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);
    });

    it('should render checkboxes for each permission level', () => {
      const checkboxes = screen.getAllByRole('checkbox');
      // Should have 3 levels × 3 permissions = 9 checkboxes in user_management category
      expect(checkboxes.length).toBe(9);
    });

    it('should call onPermissionChange when checkbox is clicked', async () => {
      const user = userEvent.setup();
      
      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[0]); // Click first checkbox

      expect(mockOnPermissionChange).toHaveBeenCalledTimes(1);
      expect(mockOnPermissionChange).toHaveBeenCalledWith('user.create', 'read', true);
    });

    it('should toggle checkbox state correctly', async () => {
      const user = userEvent.setup();
      
      const checkboxes = screen.getAllByRole('checkbox');
      const firstCheckbox = checkboxes[0];

      // Initially unchecked
      expect(firstCheckbox).not.toBeChecked();

      // Click to check
      await user.click(firstCheckbox);
      await waitFor(() => {
        expect(firstCheckbox).toBeChecked();
      });

      // Click again to uncheck
      await user.click(firstCheckbox);
      expect(mockOnPermissionChange).toHaveBeenLastCalledWith('user.create', 'read', false);
    });
  });

  describe('Role-Based Access Control', () => {
    it('should disable checkboxes for permissions above user role', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Requester"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      // Expand user management category
      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      const checkboxes = screen.getAllByRole('checkbox');
      
      // Requester should not be able to access Admin-level permissions
      // First 6 checkboxes are for user.create and user.edit (Admin level)
      for (let i = 0; i < 6; i++) {
        expect(checkboxes[i]).toBeDisabled();
      }
    });

    it('should enable checkboxes for permissions within user role', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      // Expand user management category
      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      const checkboxes = screen.getAllByRole('checkbox');
      
      // Admin should be able to access Admin-level permissions (user.create, user.edit)
      // First 6 checkboxes are for user.create and user.edit
      for (let i = 0; i < 6; i++) {
        expect(checkboxes[i]).not.toBeDisabled();
      }
    });

    it('should disable checkboxes for Super Admin permissions when user is Admin', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      const checkboxes = screen.getAllByRole('checkbox');
      
      // Last 3 checkboxes are for user.delete (Super Admin level)
      const userDeleteCheckboxes = checkboxes.slice(-3);
      userDeleteCheckboxes.forEach(checkbox => {
        expect(checkbox).toBeDisabled();
      });
    });
  });

  describe('Readonly Mode', () => {
    it('should disable all checkboxes in readonly mode', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Super Admin"
          onPermissionChange={mockOnPermissionChange}
          readonly={true}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      const checkboxes = screen.getAllByRole('checkbox');
      checkboxes.forEach(checkbox => {
        expect(checkbox).toBeDisabled();
      });
    });

    it('should not show action buttons in readonly mode', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
          readonly={true}
        />
      );

      expect(screen.queryByText('초기화')).not.toBeInTheDocument();
      expect(screen.queryByText('권한 저장')).not.toBeInTheDocument();
    });

    it('should not call onPermissionChange in readonly mode', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Super Admin"
          onPermissionChange={mockOnPermissionChange}
          readonly={true}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[0]);

      expect(mockOnPermissionChange).not.toHaveBeenCalled();
    });
  });

  describe('Action Buttons', () => {
    it('should show action buttons when not readonly', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      expect(screen.getByText('초기화')).toBeInTheDocument();
      expect(screen.getByText('권한 저장')).toBeInTheDocument();
    });

    it('should clear all selections when reset button is clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      // First select some permissions
      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[0]);

      // Then click reset
      const resetButton = screen.getByText('초기화');
      await user.click(resetButton);

      // All checkboxes should be unchecked
      checkboxes.forEach(checkbox => {
        expect(checkbox).not.toBeChecked();
      });
    });

    it('should log save action when save button is clicked', async () => {
      const user = userEvent.setup();
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const saveButton = screen.getByText('권한 저장');
      await user.click(saveButton);

      expect(consoleSpy).toHaveBeenCalledWith('Save permissions', expect.any(Set));
      
      consoleSpy.mockRestore();
    });
  });

  describe('Korean Localization', () => {
    it('should display all category labels in Korean', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      expect(screen.getByText('사용자 관리')).toBeInTheDocument();
      expect(screen.getByText('권한 관리')).toBeInTheDocument();
      expect(screen.getByText('감사 로그')).toBeInTheDocument();
      expect(screen.getByText('시스템 설정')).toBeInTheDocument();
    });

    it('should display permission level headers in Korean', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      expect(screen.getByText('읽기')).toBeInTheDocument();
      expect(screen.getByText('편집')).toBeInTheDocument();
      expect(screen.getByText('관리')).toBeInTheDocument();
    });

    it('should apply korean-text class to Korean text elements', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      const koreanTexts = document.querySelectorAll('.korean-text');
      expect(koreanTexts.length).toBeGreaterThan(0);
    });
  });

  describe('Custom Styling', () => {
    it('should apply custom className', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
          className="custom-matrix"
        />
      );

      const container = screen.getByText('권한 매트릭스').closest('.custom-matrix');
      expect(container).toBeInTheDocument();
    });

    it('should have proper hover effects on category buttons', () => {
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      expect(categoryButton).toHaveClass('hover:bg-gray-50', 'dark:hover:bg-gray-800');
    });

    it('should have proper table row hover effects', async () => {
      const user = userEvent.setup();
      
      render(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole="Admin"
          onPermissionChange={mockOnPermissionChange}
        />
      );

      const categoryButton = screen.getByText('사용자 관리').closest('button');
      await user.click(categoryButton!);

      const tableRows = screen.getAllByRole('row');
      // Skip header row
      const dataRows = tableRows.slice(1);
      
      dataRows.forEach(row => {
        expect(row).toHaveClass('hover:bg-white', 'dark:hover:bg-gray-800');
      });
    });
  });
});

describe('PermissionSummary Component', () => {
  const mockPermissions = ['사용자 생성', '사용자 편집', '권한 부여', '감사 로그 조회'];

  describe('Basic Rendering', () => {
    it('should render permission summary with Korean title', () => {
      render(
        <PermissionSummary
          userRole="Admin"
          permissions={mockPermissions}
        />
      );

      expect(screen.getByText('권한 요약')).toBeInTheDocument();
    });

    it('should display user role badge', () => {
      render(
        <PermissionSummary
          userRole="Admin"
          permissions={mockPermissions}
        />
      );

      expect(screen.getByText('관리자')).toBeInTheDocument();
    });

    it('should display all permissions when count is 6 or less', () => {
      render(
        <PermissionSummary
          userRole="Admin"
          permissions={mockPermissions}
        />
      );

      mockPermissions.forEach(permission => {
        expect(screen.getByText(permission)).toBeInTheDocument();
      });

      expect(screen.queryByText(/\+\d+개 더/)).not.toBeInTheDocument();
    });

    it('should truncate permissions and show remainder when count exceeds 6', () => {
      const manyPermissions = [
        '사용자 생성', '사용자 편집', '사용자 삭제', '권한 부여',
        '권한 취소', '감사 로그 조회', '시스템 설정', '대시보드 관리'
      ];

      render(
        <PermissionSummary
          userRole="Admin"
          permissions={manyPermissions}
        />
      );

      // Should show first 6 permissions
      manyPermissions.slice(0, 6).forEach(permission => {
        expect(screen.getByText(permission)).toBeInTheDocument();
      });

      // Should show remainder count
      expect(screen.getByText('+2개 더')).toBeInTheDocument();

      // Should not show truncated permissions
      expect(screen.queryByText('시스템 설정')).not.toBeInTheDocument();
      expect(screen.queryByText('대시보드 관리')).not.toBeInTheDocument();
    });
  });

  describe('Layout and Styling', () => {
    it('should apply custom className', () => {
      render(
        <PermissionSummary
          userRole="Admin"
          permissions={mockPermissions}
          className="custom-summary"
        />
      );

      const container = screen.getByText('권한 요약').closest('.custom-summary');
      expect(container).toBeInTheDocument();
    });

    it('should have proper flex layout for permissions', () => {
      render(
        <PermissionSummary
          userRole="Admin"
          permissions={mockPermissions}
        />
      );

      const permissionContainer = screen.getByText('사용자 생성').closest('div');
      expect(permissionContainer).toHaveClass('flex', 'flex-wrap', 'gap-1');
    });

    it('should apply korean-text class to permission badges', () => {
      render(
        <PermissionSummary
          userRole="Admin"
          permissions={mockPermissions}
        />
      );

      const koreanTexts = document.querySelectorAll('.korean-text');
      expect(koreanTexts.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty permissions array', () => {
      render(
        <PermissionSummary
          userRole="Admin"
          permissions={[]}
        />
      );

      expect(screen.getByText('권한 요약')).toBeInTheDocument();
      expect(screen.getByText('관리자')).toBeInTheDocument();
      expect(screen.queryByText(/\+\d+개 더/)).not.toBeInTheDocument();
    });

    it('should handle single permission', () => {
      render(
        <PermissionSummary
          userRole="Admin"
          permissions={['사용자 생성']}
        />
      );

      expect(screen.getByText('사용자 생성')).toBeInTheDocument();
      expect(screen.queryByText(/\+\d+개 더/)).not.toBeInTheDocument();
    });

    it('should handle exactly 6 permissions', () => {
      const sixPermissions = [
        '사용자 생성', '사용자 편집', '사용자 삭제',
        '권한 부여', '권한 취소', '감사 로그 조회'
      ];

      render(
        <PermissionSummary
          userRole="Admin"
          permissions={sixPermissions}
        />
      );

      sixPermissions.forEach(permission => {
        expect(screen.getByText(permission)).toBeInTheDocument();
      });

      expect(screen.queryByText(/\+\d+개 더/)).not.toBeInTheDocument();
    });

    it('should handle exactly 7 permissions', () => {
      const sevenPermissions = [
        '사용자 생성', '사용자 편집', '사용자 삭제',
        '권한 부여', '권한 취소', '감사 로그 조회', '시스템 설정'
      ];

      render(
        <PermissionSummary
          userRole="Admin"
          permissions={sevenPermissions}
        />
      );

      // Should show first 6
      sevenPermissions.slice(0, 6).forEach(permission => {
        expect(screen.getByText(permission)).toBeInTheDocument();
      });

      // Should show +1개 더
      expect(screen.getByText('+1개 더')).toBeInTheDocument();
      expect(screen.queryByText('시스템 설정')).not.toBeInTheDocument();
    });
  });
});

describe('Accessibility', () => {
  it('should have proper table structure with headers', async () => {
    const user = userEvent.setup();
    
    render(
      <PermissionMatrix
        permissions={mockPermissions}
        userRole="Admin"
        onPermissionChange={jest.fn()}
      />
    );

    const categoryButton = screen.getByText('사용자 관리').closest('button');
    await user.click(categoryButton!);

    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();

    const columnHeaders = screen.getAllByRole('columnheader');
    expect(columnHeaders.length).toBe(6); // 권한명, 설명, 읽기, 편집, 관리, 필요 역할
  });

  it('should have accessible checkboxes', async () => {
    const user = userEvent.setup();
    
    render(
      <PermissionMatrix
        permissions={mockPermissions}
        userRole="Admin"
        onPermissionChange={jest.fn()}
      />
    );

    const categoryButton = screen.getByText('사용자 관리').closest('button');
    await user.click(categoryButton!);

    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      expect(checkbox).toBeInTheDocument();
      expect(checkbox).toHaveAttribute('type', 'checkbox');
    });
  });

  it('should have proper button accessibility', () => {
    render(
      <PermissionMatrix
        permissions={mockPermissions}
        userRole="Admin"
        onPermissionChange={jest.fn()}
      />
    );

    const categoryButtons = screen.getAllByRole('button');
    categoryButtons.forEach(button => {
      expect(button).toBeInTheDocument();
    });
  });
});

describe('Performance', () => {
  it('should handle large permission sets efficiently', () => {
    const start = performance.now();
    
    const largePermissionSet = Array(100).fill(null).map((_, index) => ({
      id: `permission.${index}`,
      name: `권한 ${index}`,
      description: `권한 ${index} 설명`,
      category: `category_${index % 5}`,
      requiredRole: 'Admin' as UserRole,
    }));

    render(
      <PermissionMatrix
        permissions={largePermissionSet}
        userRole="Admin"
        onPermissionChange={jest.fn()}
      />
    );

    const end = performance.now();
    expect(end - start).toBeLessThan(500); // Should render in less than 500ms
  });

  it('should not cause memory leaks with frequent state changes', async () => {
    const user = userEvent.setup();
    
    const { rerender } = render(
      <PermissionMatrix
        permissions={mockPermissions}
        userRole="Admin"
        onPermissionChange={jest.fn()}
      />
    );

    // Simulate frequent re-renders
    for (let i = 0; i < 50; i++) {
      rerender(
        <PermissionMatrix
          permissions={mockPermissions}
          userRole={i % 2 === 0 ? 'Admin' : 'Requester'}
          onPermissionChange={jest.fn()}
        />
      );
    }

    // Should still function correctly
    expect(screen.getByText('권한 매트릭스')).toBeInTheDocument();
  });
});