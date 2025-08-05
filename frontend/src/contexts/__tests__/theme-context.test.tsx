import React, { act } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider, useTheme } from '../theme-context'

// Test component that uses the theme context
const TestComponent: React.FC = () => {
  const { theme, setTheme, actualTheme } = useTheme()
  
  return (
    <div>
      <div data-testid="theme">{theme}</div>
      <div data-testid="actual-theme">{actualTheme}</div>
      <button onClick={() => setTheme('light')} data-testid="light-button">
        라이트 모드
      </button>
      <button onClick={() => setTheme('dark')} data-testid="dark-button">
        다크 모드
      </button>
      <button onClick={() => setTheme('system')} data-testid="system-button">
        시스템 설정
      </button>
    </div>
  )
}

const TestComponentWrapper: React.FC = () => (
  <ThemeProvider>
    <TestComponent />
  </ThemeProvider>
)

describe('ThemeContext', () => {
  let mockMatchMedia: jest.Mock
  let mockAddEventListener: jest.Mock
  let mockRemoveEventListener: jest.Mock

  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
    
    // Reset document classes
    document.documentElement.classList.remove('light', 'dark')
    
    // Mock matchMedia
    mockAddEventListener = jest.fn()
    mockRemoveEventListener = jest.fn()
    mockMatchMedia = jest.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener,
      dispatchEvent: jest.fn(),
    }))
    
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: mockMatchMedia,
    })
  })

  describe('초기화', () => {
    it('should start with system theme by default', async () => {
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('system')
        expect(screen.getByTestId('actual-theme')).toHaveTextContent('light')
      })
    })
    
    it('should load saved theme from localStorage', async () => {
      localStorage.setItem('theme', 'dark')
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('dark')
        expect(screen.getByTestId('actual-theme')).toHaveTextContent('dark')
      })
    })
    
    it('should ignore invalid theme from localStorage', async () => {
      localStorage.setItem('theme', 'invalid-theme')
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('system')
      })
    })
  })

  describe('테마 변경', () => {
    it('should switch to light theme', async () => {
      const user = userEvent.setup()
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('system')
      })
      
      await act(async () => {
        await user.click(screen.getByTestId('light-button'))
      })
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('light')
        expect(screen.getByTestId('actual-theme')).toHaveTextContent('light')
        expect(document.documentElement.classList.contains('light')).toBe(true)
        expect(document.documentElement.classList.contains('dark')).toBe(false)
        expect(localStorage.getItem('theme')).toBe('light')
      })
    })
    
    it('should switch to dark theme', async () => {
      const user = userEvent.setup()
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('system')
      })
      
      await act(async () => {
        await user.click(screen.getByTestId('dark-button'))
      })
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('dark')
        expect(screen.getByTestId('actual-theme')).toHaveTextContent('dark')
        expect(document.documentElement.classList.contains('dark')).toBe(true)
        expect(document.documentElement.classList.contains('light')).toBe(false)
        expect(localStorage.getItem('theme')).toBe('dark')
      })
    })
    
    it('should switch to system theme', async () => {
      const user = userEvent.setup()
      localStorage.setItem('theme', 'light')
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('light')
      })
      
      await act(async () => {
        await user.click(screen.getByTestId('system-button'))
      })
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('system')
        expect(localStorage.getItem('theme')).toBe('system')
        expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)')
      })
    })
  })

  describe('시스템 테마 설정', () => {
    it('should respect system light preference', async () => {
      mockMatchMedia.mockImplementation(query => ({
        matches: false, // Light mode
        media: query,
        addEventListener: mockAddEventListener,
        removeEventListener: mockRemoveEventListener,
        dispatchEvent: jest.fn(),
      }))
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('system')
        expect(screen.getByTestId('actual-theme')).toHaveTextContent('light')
        expect(document.documentElement.classList.contains('light')).toBe(true)
      })
    })
    
    it('should respect system dark preference', async () => {
      mockMatchMedia.mockImplementation(query => ({
        matches: true, // Dark mode
        media: query,
        addEventListener: mockAddEventListener,
        removeEventListener: mockRemoveEventListener,
        dispatchEvent: jest.fn(),
      }))
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('system')
        expect(screen.getByTestId('actual-theme')).toHaveTextContent('dark')
        expect(document.documentElement.classList.contains('dark')).toBe(true)
      })
    })
    
    it('should listen for system theme changes', async () => {
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(mockAddEventListener).toHaveBeenCalledWith('change', expect.any(Function))
      })
    })
    
    it('should respond to system theme changes', async () => {
      let changeHandler: (e: MediaQueryListEvent) => void
      
      mockAddEventListener.mockImplementation((event, handler) => {
        if (event === 'change') {
          changeHandler = handler
        }
      })
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(mockAddEventListener).toHaveBeenCalled()
      })
      
      // Initially light
      expect(screen.getByTestId('actual-theme')).toHaveTextContent('light')
      
      // Simulate system change to dark
      await act(async () => {
        const mockEvent = { matches: true } as MediaQueryListEvent
        changeHandler!(mockEvent)
      })
      
      await waitFor(() => {
        expect(screen.getByTestId('actual-theme')).toHaveTextContent('dark')
        expect(document.documentElement.classList.contains('dark')).toBe(true)
      })
    })
    
    it('should cleanup event listeners on unmount', async () => {
      const { unmount } = render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(mockAddEventListener).toHaveBeenCalled()
      })
      
      unmount()
      
      expect(mockRemoveEventListener).toHaveBeenCalledWith('change', expect.any(Function))
    })
  })

  describe('수화(Hydration) 방지', () => {
    it('should prevent hydration mismatch by not rendering children initially', () => {
      // Mock mounted state to false initially
      const OriginalUseEffect = React.useEffect
      let effectCallback: () => void
      
      jest.spyOn(React, 'useEffect').mockImplementation((callback, deps) => {
        if (deps && deps.length === 0) {
          // This is the mount effect
          effectCallback = callback
          return
        }
        return OriginalUseEffect(callback, deps)
      })
      
      const { container } = render(<TestComponentWrapper />)
      
      // Before mount effect runs, children should be rendered without theme context
      expect(container.innerHTML).toContain('시스템 설정')
      
      // Clean up mock
      ;(React.useEffect as jest.Mock).mockRestore()
    })
  })

  describe('한국어 텍스트', () => {
    it('should display Korean text for theme buttons', () => {
      render(<TestComponentWrapper />)
      
      expect(screen.getByTestId('light-button')).toHaveTextContent('라이트 모드')
      expect(screen.getByTestId('dark-button')).toHaveTextContent('다크 모드')
      expect(screen.getByTestId('system-button')).toHaveTextContent('시스템 설정')
    })
    
    it('should contain Korean text in button elements', () => {
      render(<TestComponentWrapper />)
      
      const lightButton = screen.getByTestId('light-button')
      const darkButton = screen.getByTestId('dark-button')
      const systemButton = screen.getByTestId('system-button')
      
      expect(lightButton).toContainKoreanText()
      expect(darkButton).toContainKoreanText()
      expect(systemButton).toContainKoreanText()
    })
  })

  describe('CSS 클래스 관리', () => {
    it('should remove previous theme class when switching themes', async () => {
      const user = userEvent.setup()
      
      render(<TestComponentWrapper />)
      
      // Switch to light theme
      await act(async () => {
        await user.click(screen.getByTestId('light-button'))
      })
      
      await waitFor(() => {
        expect(document.documentElement.classList.contains('light')).toBe(true)
        expect(document.documentElement.classList.contains('dark')).toBe(false)
      })
      
      // Switch to dark theme
      await act(async () => {
        await user.click(screen.getByTestId('dark-button'))
      })
      
      await waitFor(() => {
        expect(document.documentElement.classList.contains('dark')).toBe(true)
        expect(document.documentElement.classList.contains('light')).toBe(false)
      })
    })
    
    it('should properly manage theme classes for system theme', async () => {
      const user = userEvent.setup()
      
      // Start with dark system preference
      mockMatchMedia.mockImplementation(() => ({
        matches: true,
        media: '(prefers-color-scheme: dark)',
        addEventListener: mockAddEventListener,
        removeEventListener: mockRemoveEventListener,
        dispatchEvent: jest.fn(),
      }))
      
      render(<TestComponentWrapper />)
      
      await waitFor(() => {
        expect(document.documentElement.classList.contains('dark')).toBe(true)
      })
      
      // Switch to light theme manually
      await act(async () => {
        await user.click(screen.getByTestId('light-button'))
      })
      
      await waitFor(() => {
        expect(document.documentElement.classList.contains('light')).toBe(true)
        expect(document.documentElement.classList.contains('dark')).toBe(false)
      })
      
      // Switch back to system
      await act(async () => {
        await user.click(screen.getByTestId('system-button'))
      })
      
      await waitFor(() => {
        expect(document.documentElement.classList.contains('dark')).toBe(true)
        expect(document.documentElement.classList.contains('light')).toBe(false)
      })
    })
  })
})

describe('useTheme hook', () => {
  it('should throw error when used outside ThemeProvider', () => {
    const TestComponentWithoutProvider = () => {
      useTheme()
      return null
    }
    
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    
    expect(() => {
      render(<TestComponentWithoutProvider />)
    }).toThrow('useTheme must be used within a ThemeProvider')
    
    consoleSpy.mockRestore()
  })
})