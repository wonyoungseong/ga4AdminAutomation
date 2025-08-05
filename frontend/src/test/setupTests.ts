import '@testing-library/jest-dom'
import { TextEncoder, TextDecoder } from 'util'

// Polyfills for Node.js environment
Object.assign(global, { TextDecoder, TextEncoder })

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value.toString()
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key]
    }),
    clear: jest.fn(() => {
      store = {}
    }),
    key: jest.fn((index: number) => {
      const keys = Object.keys(store)
      return keys[index] || null
    }),
    get length() {
      return Object.keys(store).length
    }
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', {
  value: localStorageMock
})

// Mock matchMedia for theme testing
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock ResizeObserver for responsive testing
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock IntersectionObserver for lazy loading tests
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
}))

// Mock fetch for API testing
global.fetch = jest.fn()

// Korean text testing utilities
declare global {
  namespace jest {
    interface Matchers<R> {
      toContainKoreanText(): R
      toHaveAccessibleName(name: string): R
      toHaveMinimumTouchTarget(): R
      toBeResponsiveElement(): R
    }
  }
}

// Custom matcher for Korean text
expect.extend({
  toContainKoreanText(received: HTMLElement) {
    const koreanRegex = /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/
    const textContent = received.textContent || ''
    const hasKoreanText = koreanRegex.test(textContent)

    return {
      message: () =>
        hasKoreanText
          ? `Expected element not to contain Korean text, but found: "${textContent}"`
          : `Expected element to contain Korean text, but got: "${textContent}"`,
      pass: hasKoreanText,
    }
  },

  toHaveAccessibleName(received: HTMLElement, expectedName: string) {
    const accessibleName = received.getAttribute('aria-label') ||
                          received.getAttribute('aria-labelledby') ||
                          received.textContent ||
                          received.getAttribute('title') ||
                          ''

    const hasCorrectName = accessibleName.includes(expectedName)

    return {
      message: () =>
        hasCorrectName
          ? `Expected element not to have accessible name "${expectedName}"`
          : `Expected element to have accessible name "${expectedName}", but got "${accessibleName}"`,
      pass: hasCorrectName,
    }
  },

  toHaveMinimumTouchTarget(received: HTMLElement) {
    const computedStyle = window.getComputedStyle(received)
    const width = parseInt(computedStyle.width, 10)
    const height = parseInt(computedStyle.height, 10)
    const minSize = 44 // WCAG minimum touch target size

    const hasMinimumSize = width >= minSize && height >= minSize

    return {
      message: () =>
        hasMinimumSize
          ? `Expected element not to have minimum touch target size`
          : `Expected element to have minimum touch target size (${minSize}px), but got ${width}x${height}px`,
      pass: hasMinimumSize,
    }
  },

  toBeResponsiveElement(received: HTMLElement) {
    const classList = Array.from(received.classList)
    const hasResponsiveClasses = classList.some(className => 
      className.includes('sm:') ||
      className.includes('md:') ||
      className.includes('lg:') ||
      className.includes('xl:') ||
      className.includes('2xl:') ||
      className.includes('responsive')
    )

    return {
      message: () =>
        hasResponsiveClasses
          ? `Expected element not to have responsive classes`
          : `Expected element to have responsive classes (sm:, md:, lg:, etc.), but found: ${classList.join(' ')}`,
      pass: hasResponsiveClasses,
    }
  },
})

// Mock console methods to reduce noise in tests
const originalError = console.error
const originalWarn = console.warn

console.error = (...args: any[]) => {
  // Ignore specific React/Next.js warnings in tests
  if (
    typeof args[0] === 'string' &&
    (args[0].includes('Warning: ReactDOM.render is no longer supported') ||
     args[0].includes('Warning: Each child in a list should have a unique "key" prop'))
  ) {
    return
  }
  originalError.call(console, ...args)
}

console.warn = (...args: any[]) => {
  // Ignore specific warnings in tests
  if (
    typeof args[0] === 'string' &&
    args[0].includes('componentWillReceiveProps has been renamed')
  ) {
    return
  }
  originalWarn.call(console, ...args)
}

// Setup for each test
beforeEach(() => {
  // Clear all mocks
  jest.clearAllMocks()
  
  // Reset localStorage
  localStorageMock.clear()
  
  // Reset fetch mock
  ;(global.fetch as jest.Mock).mockClear()
})

// Cleanup after each test
afterEach(() => {
  // Clear any timers
  jest.clearAllTimers()
  
  // Clear DOM
  document.body.innerHTML = ''
})