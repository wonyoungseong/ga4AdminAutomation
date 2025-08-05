import React, { act } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '../auth-context'
import { typeSafeApiClient, ApiClientError } from '@/lib/api-client'
import { mockAuthenticatedUser, mockApiResponses } from '@/test/test-utils'

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  typeSafeApiClient: {
    login: jest.fn(),
    getCurrentUser: jest.fn(),
    refreshAuthToken: jest.fn(),
  },
  ApiClientError: class MockApiClientError extends Error {
    constructor(message: string, public statusCode?: number, public details?: string) {
      super(message)
      this.name = 'ApiClientError'
    }
  }
}))

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
  }),
}))

// Mock useClientOnly hook
jest.mock('@/hooks/use-client-only', () => ({
  useClientOnly: () => true,
}))

// Test component that uses the auth context
const TestComponent: React.FC = () => {
  const { user, login, logout, isLoading, isInitialized, isRefreshing, token } = useAuth()
  
  const handleLogin = async () => {
    await login('test@example.com', 'password123')
  }
  
  return (
    <div>
      <div data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="initialized">{isInitialized ? 'initialized' : 'not-initialized'}</div>
      <div data-testid="refreshing">{isRefreshing ? 'refreshing' : 'not-refreshing'}</div>
      <div data-testid="user">{user ? user.name : 'no-user'}</div>
      <div data-testid="token">{token ? 'has-token' : 'no-token'}</div>
      <button onClick={handleLogin} data-testid="login-button">
        로그인
      </button>
      <button onClick={logout} data-testid="logout-button">
        로그아웃
      </button>
    </div>
  )
}

const TestComponentWrapper: React.FC = () => (
  <AuthProvider>
    <TestComponent />
  </AuthProvider>
)

describe('AuthContext', () => {
  const mockTypeSafeApiClient = typeSafeApiClient as jest.Mocked<typeof typeSafeApiClient>
  
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
    mockPush.mockClear()
    
    // Reset API client mocks
    mockTypeSafeApiClient.login.mockClear()
    mockTypeSafeApiClient.getCurrentUser.mockClear()
    mockTypeSafeApiClient.refreshAuthToken.mockClear()
  })

  describe('초기화', () => {
    it('should initialize with loading state', () => {
      render(<TestComponentWrapper />)
      
      expect(screen.getByTestId('loading')).toHaveTextContent('loading')
      expect(screen.getByTestId('initialized')).toHaveTextContent('not-initialized')
      expect(screen.getByTestId('user')).toHaveTextContent('no-user')
      expect(screen.getByTestId('token')).toHaveTextContent('no-token')
    })
    
    it('should complete initialization when no token is stored', async () => {
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
        expect(screen.getByTestId('initialized')).toHaveTextContent('initialized')
      })
    })
    
    it('should fetch user info when token is stored', async () => {
      // Set up stored token
      localStorage.setItem('auth_token', 'stored-token')
      mockTypeSafeApiClient.getCurrentUser.mockResolvedValue(mockAuthenticatedUser)
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(mockTypeSafeApiClient.getCurrentUser).toHaveBeenCalled()
        expect(screen.getByTestId('user')).toHaveTextContent(mockAuthenticatedUser.name)
        expect(screen.getByTestId('token')).toHaveTextContent('has-token')
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
        expect(screen.getByTestId('initialized')).toHaveTextContent('initialized')
      })
    })
  })

  describe('로그인', () => {
    it('should successfully log in user', async () => {
      const user = userEvent.setup()
      mockTypeSafeApiClient.login.mockResolvedValue(mockApiResponses.loginSuccess)
      
      render(<TestComponentWrapper />)
      
      // Wait for initial loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
      })
      
      await act(async () => {
        await user.click(screen.getByTestId('login-button'))
      })
      
      await waitFor(() => {
        expect(mockTypeSafeApiClient.login).toHaveBeenCalledWith('test@example.com', 'password123')
        expect(screen.getByTestId('user')).toHaveTextContent(mockAuthenticatedUser.name)
        expect(screen.getByTestId('token')).toHaveTextContent('has-token')
        expect(localStorage.getItem('auth_token')).toBe('mock-jwt-token')
        expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token')
      })
    })
    
    it('should handle login failure', async () => {
      const user = userEvent.setup()
      const loginError = new ApiClientError('Invalid credentials', 401, '이메일 또는 비밀번호가 올바르지 않습니다.')
      mockTypeSafeApiClient.login.mockRejectedValue(loginError)
      
      render(<TestComponentWrapper />)
      
      // Wait for initial loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
      })
      
      await act(async () => {
        await user.click(screen.getByTestId('login-button'))
      })
      
      await waitFor(() => {
        expect(mockTypeSafeApiClient.login).toHaveBeenCalledWith('test@example.com', 'password123')
        expect(screen.getByTestId('user')).toHaveTextContent('no-user')
        expect(screen.getByTestId('token')).toHaveTextContent('no-token')
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
      })
    })
    
    it('should set loading state during login', async () => {
      const user = userEvent.setup()
      
      // Create a promise that we can control
      let resolveLogin: (value: any) => void
      const loginPromise = new Promise(resolve => {
        resolveLogin = resolve
      })
      mockTypeSafeApiClient.login.mockReturnValue(loginPromise)
      
      render(<TestComponentWrapper />)
      
      // Wait for initial loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
      })
      
      // Start login
      await act(async () => {
        await user.click(screen.getByTestId('login-button'))
      })
      
      // Should be loading during login
      expect(screen.getByTestId('loading')).toHaveTextContent('loading')
      
      // Complete login
      await act(async () => {
        resolveLogin!(mockApiResponses.loginSuccess)
      })
      
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
      })
    })
  })

  describe('로그아웃', () => {
    it('should successfully log out user', async () => {
      const user = userEvent.setup()
      
      // Set up authenticated state
      localStorage.setItem('auth_token', 'stored-token')
      localStorage.setItem('refresh_token', 'stored-refresh-token')
      mockTypeSafeApiClient.getCurrentUser.mockResolvedValue(mockAuthenticatedUser)
      
      render(<TestComponentWrapper />)
      
      // Wait for initialization with user
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(mockAuthenticatedUser.name)
      })
      
      await act(async () => {
        await user.click(screen.getByTestId('logout-button'))
      })
      
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('no-user')
        expect(screen.getByTestId('token')).toHaveTextContent('no-token')
        expect(localStorage.getItem('auth_token')).toBeNull()
        expect(localStorage.getItem('refresh_token')).toBeNull()
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })
  })

  describe('토큰 갱신', () => {
    it('should refresh token when getCurrentUser returns 401', async () => {
      localStorage.setItem('auth_token', 'expired-token')
      
      // First call returns 401, second call succeeds after refresh
      mockTypeSafeApiClient.getCurrentUser
        .mockRejectedValueOnce(new ApiClientError('Token expired', 401))
        .mockResolvedValueOnce(mockAuthenticatedUser)
      
      mockTypeSafeApiClient.refreshAuthToken.mockResolvedValue('new-token')
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(mockTypeSafeApiClient.getCurrentUser).toHaveBeenCalled()
        expect(mockTypeSafeApiClient.refreshAuthToken).toHaveBeenCalled()
        expect(screen.getByTestId('user')).toHaveTextContent(mockAuthenticatedUser.name)
        expect(screen.getByTestId('token')).toHaveTextContent('has-token')
      })
    })
    
    it('should handle refresh token failure', async () => {
      localStorage.setItem('auth_token', 'expired-token')
      
      mockTypeSafeApiClient.getCurrentUser.mockRejectedValue(new ApiClientError('Token expired', 401))
      mockTypeSafeApiClient.refreshAuthToken.mockResolvedValue(null)
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(mockTypeSafeApiClient.refreshAuthToken).toHaveBeenCalled()
        expect(screen.getByTestId('user')).toHaveTextContent('no-user')
        expect(screen.getByTestId('token')).toHaveTextContent('no-token')
        expect(localStorage.getItem('auth_token')).toBeNull()
        expect(localStorage.getItem('refresh_token')).toBeNull()
      })
    })
    
    it('should set refreshing state during token refresh', async () => {
      localStorage.setItem('auth_token', 'expired-token')
      
      let resolveRefresh: (value: any) => void
      const refreshPromise = new Promise(resolve => {
        resolveRefresh = resolve
      })
      
      mockTypeSafeApiClient.getCurrentUser.mockRejectedValue(new ApiClientError('Token expired', 401))
      mockTypeSafeApiClient.refreshAuthToken.mockReturnValue(refreshPromise)
      
      render(<TestComponentWrapper />)
      
      // Should start refreshing
      await waitFor(() => {
        expect(screen.getByTestId('refreshing')).toHaveTextContent('refreshing')
      })
      
      // Complete refresh
      await act(async () => {
        resolveRefresh!('new-token')
      })
      
      await waitFor(() => {
        expect(screen.getByTestId('refreshing')).toHaveTextContent('not-refreshing')
      })
    })
  })

  describe('Storage 이벤트', () => {
    it('should handle storage changes from other tabs', async () => {
      render(<TestComponentWrapper />)
      
      // Wait for initialization
      await waitFor(() => {
        expect(screen.getByTestId('initialized')).toHaveTextContent('initialized')
      })
      
      mockTypeSafeApiClient.getCurrentUser.mockResolvedValue(mockAuthenticatedUser)
      
      // Simulate storage event from another tab
      await act(async () => {
        const storageEvent = new StorageEvent('storage', {
          key: 'auth_token',
          newValue: 'new-token-from-other-tab',
          oldValue: null,
        })
        window.dispatchEvent(storageEvent)
      })
      
      await waitFor(() => {
        expect(mockTypeSafeApiClient.getCurrentUser).toHaveBeenCalled()
        expect(screen.getByTestId('token')).toHaveTextContent('has-token')
      })
    })
    
    it('should handle token removal from other tabs', async () => {
      // Start with authenticated state
      localStorage.setItem('auth_token', 'stored-token')
      mockTypeSafeApiClient.getCurrentUser.mockResolvedValue(mockAuthenticatedUser)
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent(mockAuthenticatedUser.name)
      })
      
      // Simulate token removal from another tab
      await act(async () => {
        const storageEvent = new StorageEvent('storage', {
          key: 'auth_token',
          newValue: null,
          oldValue: 'stored-token',
        })
        window.dispatchEvent(storageEvent)
      })
      
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('no-user')
        expect(screen.getByTestId('token')).toHaveTextContent('no-token')
      })
    })
  })

  describe('에러 처리', () => {
    it('should handle non-401 errors gracefully', async () => {
      localStorage.setItem('auth_token', 'stored-token')
      mockTypeSafeApiClient.getCurrentUser.mockRejectedValue(new ApiClientError('Server error', 500))
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
        expect(screen.getByTestId('initialized')).toHaveTextContent('initialized')
        // Should not attempt refresh for non-401 errors
        expect(mockTypeSafeApiClient.refreshAuthToken).not.toHaveBeenCalled()
      })
    })
    
    it('should handle initialization errors', async () => {
      localStorage.setItem('auth_token', 'stored-token')
      mockTypeSafeApiClient.getCurrentUser.mockRejectedValue(new Error('Network error'))
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('not-loading')
        expect(screen.getByTestId('initialized')).toHaveTextContent('initialized')
      })
    })
  })

  describe('한국어 텍스트', () => {
    it('should contain Korean text in error messages', async () => {
      // This is tested through the API client mock, but we can verify
      // that Korean text appears in console logs
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      
      localStorage.setItem('auth_token', 'expired-token')
      mockTypeSafeApiClient.getCurrentUser.mockRejectedValue(new ApiClientError('Token expired', 401))
      mockTypeSafeApiClient.refreshAuthToken.mockRejectedValue(new Error('Refresh failed'))
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('initialized')).toHaveTextContent('initialized')
      })
      
      // Check that Korean error messages are logged
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('토큰 갱신 실패'),
        expect.any(Error)
      )
      
      consoleSpy.mockRestore()
    })
  })
})

describe('useAuth hook', () => {
  it('should throw error when used outside AuthProvider', () => {
    const TestComponentWithoutProvider = () => {
      useAuth()
      return null
    }
    
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    
    expect(() => {
      render(<TestComponentWithoutProvider />)
    }).toThrow('useAuth must be used within an AuthProvider')
    
    consoleSpy.mockRestore()
  })
})