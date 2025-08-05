const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  // Add more setup options before each test is run
  setupFilesAfterEnv: ['<rootDir>/src/test/setupTests.ts'],
  
  // The test environment that will be used for testing
  testEnvironment: 'jsdom',
  
  // Test file patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}'
  ],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,ts,jsx,tsx}',
    '!src/**/*.d.ts',
    '!src/app/**/*', // Exclude Next.js app directory pages
    '!src/**/types.ts',
    '!src/test/**/*',
    '!**/node_modules/**',
  ],
  
  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    // Specific thresholds for critical components
    './src/contexts/**/*.{ts,tsx}': {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95,
    },
    './src/components/ui/**/*.{ts,tsx}': {
      branches: 85,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
  
  // Test timeout for async operations
  testTimeout: 10000,
  
  // Verbose output for debugging
  verbose: true,
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Restore mocks after each test
  restoreMocks: true,
  
  // Module name mapping
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@/test/(.*)$': '<rootDir>/src/test/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)