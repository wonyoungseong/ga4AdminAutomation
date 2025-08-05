import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { AuthProvider } from '@/contexts/auth-context'
import { ThemeProvider } from '@/contexts/theme-context'
import { User } from '@/types/api'

// Mock user data for testing
export const mockUser: User = {
  id: 1,
  email: 'test@example.com',
  name: '테스트 사용자',
  role: 'Admin',
  created_at: '2024-01-01T00:00:00Z',
  is_active: true,
}

// Mock authenticated user
export const mockAuthenticatedUser: User = {
  ...mockUser,
  role: 'Admin',
  status: 'active',
  registration_status: 'approved',
  is_representative: false,
}

// Mock unauthenticated state
export const mockUnauthenticatedState = {
  user: null,
  token: null,
  isLoading: false,
  isInitialized: true,
  isRefreshing: false,
}

// Mock authenticated state
export const mockAuthenticatedState = {
  user: mockAuthenticatedUser,
  token: 'mock-jwt-token',
  isLoading: false,
  isInitialized: true,
  isRefreshing: false,
}

// Theme wrapper for testing
interface ThemeWrapperProps {
  children: React.ReactNode
  initialTheme?: 'light' | 'dark' | 'system'
}

export const ThemeWrapper: React.FC<ThemeWrapperProps> = ({ 
  children, 
  initialTheme = 'light' 
}) => {
  return <ThemeProvider>{children}</ThemeProvider>
}

// Auth wrapper for testing
interface AuthWrapperProps {
  children: React.ReactNode
  mockAuthState?: any
}

export const AuthWrapper: React.FC<AuthWrapperProps> = ({ 
  children, 
  mockAuthState 
}) => {
  if (mockAuthState) {
    // Mock the auth context using React.createContext
    const MockedAuthContext = React.createContext(mockAuthState);
    
    const MockedAuthProvider = ({ children }: { children: React.ReactNode }) => {
      const mockLogin = jest.fn().mockResolvedValue(true)
      const mockLogout = jest.fn()
      
      const contextValue = {
        ...mockAuthState,
        login: mockLogin,
        logout: mockLogout,
      }
      
      return (
        <MockedAuthContext.Provider value={contextValue}>
          {children}
        </MockedAuthContext.Provider>
      )
    }
    
    return <MockedAuthProvider>{children}</MockedAuthProvider>
  }
  
  return <AuthProvider>{children}</AuthProvider>
}

// All providers wrapper
interface AllProvidersProps {
  children: React.ReactNode
  mockAuthState?: any
  initialTheme?: 'light' | 'dark' | 'system'
}

export const AllProviders: React.FC<AllProvidersProps> = ({ 
  children, 
  mockAuthState,
  initialTheme = 'light'
}) => {
  return (
    <ThemeWrapper initialTheme={initialTheme}>
      <AuthWrapper mockAuthState={mockAuthState}>
        {children}
      </AuthWrapper>
    </ThemeWrapper>
  )
}

// Custom render function
export const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & {
    mockAuthState?: any
    initialTheme?: 'light' | 'dark' | 'system'
  }
) => {
  const { mockAuthState, initialTheme, ...renderOptions } = options || {}
  
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <AllProviders mockAuthState={mockAuthState} initialTheme={initialTheme}>
      {children}
    </AllProviders>
  )
  
  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Korean text utilities
export const koreanTextUtils = {
  // Check if text contains Korean characters
  hasKoreanText: (text: string): boolean => {
    const koreanRegex = /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/
    return koreanRegex.test(text)
  },
  
  // Common Korean test strings
  testStrings: {
    name: '홍길동',
    email: 'test@example.com',
    company: '테스트 회사',
    phone: '010-1234-5678',
    businessNumber: '123-45-67890',
    postalCode: '12345',
    invalidName: '홍길동123!@#',
    invalidPhone: '010-12-34',
    invalidBusinessNumber: '123-4-5678',
  },
  
  // Validation test cases
  validationCases: {
    name: [
      { input: '홍길동', valid: true },
      { input: 'John Doe', valid: true },
      { input: '홍 길동', valid: true },
      { input: '홍-길동', valid: true },
      { input: '홍.길동', valid: true },
      { input: '홍길동123', valid: false },
      { input: '홍길동!@#', valid: false },
    ],
    phone: [
      { input: '010-1234-5678', valid: true },
      { input: '01012345678', valid: true },
      { input: '011-123-4567', valid: true },
      { input: '010-12-34', valid: false },
      { input: '123-456-7890', valid: false },
    ],
    businessNumber: [
      { input: '123-45-67890', valid: true },
      { input: '1234567890', valid: true },
      { input: '123-4-5678', valid: false },
      { input: '12-345-6789', valid: false },
    ],
  }
}

// Mock API responses
export const mockApiResponses = {
  loginSuccess: {
    access_token: 'mock-jwt-token',
    refresh_token: 'mock-refresh-token',
    user: mockAuthenticatedUser,
  },
  
  loginError: {
    error: 'Invalid credentials',
    details: '이메일 또는 비밀번호가 올바르지 않습니다.',
  },
  
  userProfile: mockAuthenticatedUser,
  
  refreshTokenSuccess: {
    access_token: 'new-mock-jwt-token',
  },
  
  refreshTokenError: {
    error: 'Invalid refresh token',
  },
}

// Accessibility testing utilities
export const a11yUtils = {
  // Check if element has proper ARIA labels
  hasAccessibleName: (element: HTMLElement): boolean => {
    return !!(
      element.getAttribute('aria-label') ||
      element.getAttribute('aria-labelledby') ||
      element.textContent ||
      element.getAttribute('title')
    )
  },
  
  // Check if element has minimum touch target size
  hasMinimumTouchTarget: (element: HTMLElement): boolean => {
    const rect = element.getBoundingClientRect()
    return rect.width >= 44 && rect.height >= 44
  },
  
  // Check if element has proper color contrast (mock implementation)
  hasProperContrast: (element: HTMLElement): boolean => {
    // This would need a real contrast calculation in a full implementation
    const style = window.getComputedStyle(element)
    return !!(style.color && style.backgroundColor)
  },
}

// Mobile testing utilities
export const mobileUtils = {
  // Simulate mobile viewport
  setMobileViewport: () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    })
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 667,
    })
    window.dispatchEvent(new Event('resize'))
  },
  
  // Simulate desktop viewport
  setDesktopViewport: () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    })
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 768,
    })
    window.dispatchEvent(new Event('resize'))
  },
  
  // Simulate touch events
  createTouchEvent: (type: string, touches: Array<{ clientX: number; clientY: number }>) => {
    const touchList = touches.map(touch => ({
      ...touch,
      identifier: Math.random(),
      target: document.body,
      force: 1,
      radiusX: 1,
      radiusY: 1,
      rotationAngle: 0,
    }))
    
    return new TouchEvent(type, {
      bubbles: true,
      cancelable: true,
      touches: touchList as any,
      targetTouches: touchList as any,
      changedTouches: touchList as any,
    })
  },
}

// Export everything for easy importing
export * from '@testing-library/react'
export { customRender as render }
export { userEvent } from '@testing-library/user-event'