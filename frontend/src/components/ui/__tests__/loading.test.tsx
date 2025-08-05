import React from 'react'
import { render, screen } from '@testing-library/react'
import {
  LoadingSpinner,
  LoadingSkeleton,
  LoadingCard,
  LoadingPage
} from '../loading'

describe('LoadingSpinner', () => {
  describe('렌더링', () => {
    it('should render spinner with default props', () => {
      render(<LoadingSpinner />)
      
      const container = screen.getByRole('generic')
      expect(container).toHaveClass('flex', 'items-center', 'justify-center')
      
      // Should have Loader2 icon
      const icon = container.querySelector('svg')
      expect(icon).toHaveClass('animate-spin', 'text-primary')
    })
    
    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      
      render(<LoadingSpinner ref={ref} />)
      
      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('크기 변형', () => {
    it('should apply small size classes', () => {
      render(<LoadingSpinner size="sm" />)
      
      const icon = screen.getByRole('generic').querySelector('svg')
      expect(icon).toHaveClass('h-4', 'w-4')
    })
    
    it('should apply medium size classes (default)', () => {
      render(<LoadingSpinner size="md" />)
      
      const icon = screen.getByRole('generic').querySelector('svg')
      expect(icon).toHaveClass('h-6', 'w-6')
    })
    
    it('should apply large size classes', () => {
      render(<LoadingSpinner size="lg" />)
      
      const icon = screen.getByRole('generic').querySelector('svg')
      expect(icon).toHaveClass('h-8', 'w-8')
    })
  })

  describe('변형(Variants)', () => {
    it('should apply default variant classes', () => {
      render(<LoadingSpinner variant="default" />)
      
      const container = screen.getByRole('generic')
      expect(container).toHaveClass('flex', 'items-center', 'justify-center')
      expect(container).not.toHaveClass('fixed', 'inset-0')
    })
    
    it('should apply overlay variant classes', () => {
      render(<LoadingSpinner variant="overlay" />)
      
      const container = screen.getByRole('generic')
      expect(container).toHaveClass(
        'fixed',
        'inset-0',
        'z-50',
        'flex',
        'items-center',
        'justify-center',
        'bg-background/80',
        'backdrop-blur-sm'
      )
    })
  })

  describe('커스텀 속성', () => {
    it('should accept custom className', () => {
      render(<LoadingSpinner className="custom-spinner" />)
      
      const container = screen.getByRole('generic')
      expect(container).toHaveClass('custom-spinner')
    })
    
    it('should pass through additional props', () => {
      render(<LoadingSpinner data-testid="custom-spinner" />)
      
      expect(screen.getByTestId('custom-spinner')).toBeInTheDocument()
    })
  })
})

describe('LoadingSkeleton', () => {
  describe('렌더링', () => {
    it('should render skeleton with default props', () => {
      render(<LoadingSkeleton />)
      
      const container = screen.getByRole('generic')
      expect(container).toHaveClass('animate-pulse', 'space-y-3')
      
      // Should have 3 lines by default
      const lines = container.querySelectorAll('.h-4.rounded.bg-muted')
      expect(lines).toHaveLength(3)
    })
    
    it('should render custom number of lines', () => {
      render(<LoadingSkeleton lines={5} />)
      
      const container = screen.getByRole('generic')
      const lines = container.querySelectorAll('.h-4.rounded.bg-muted')
      expect(lines).toHaveLength(5)
    })
    
    it('should render avatar when avatar prop is true', () => {
      render(<LoadingSkeleton avatar />)
      
      const container = screen.getByRole('generic')
      const avatar = container.querySelector('.h-10.w-10.rounded-full.bg-muted')
      expect(avatar).toBeInTheDocument()
      
      // Should also have avatar text placeholders
      const avatarTexts = container.querySelectorAll('.h-4.w-32.rounded.bg-muted, .h-3.w-24.rounded.bg-muted')
      expect(avatarTexts).toHaveLength(2)
    })
    
    it('should have proper line width styling', () => {
      render(<LoadingSkeleton lines={2} />)
      
      const container = screen.getByRole('generic')
      const lines = container.querySelectorAll('.h-4.rounded.bg-muted')
      
      // First line should be full width, last line should be 3/4 width
      expect(lines[0]).toHaveClass('w-full')
      expect(lines[1]).toHaveClass('w-3/4')
    })
  })

  describe('커스텀 속성', () => {
    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      
      render(<LoadingSkeleton ref={ref} />)
      
      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
    
    it('should accept custom className', () => {
      render(<LoadingSkeleton className="custom-skeleton" />)
      
      const container = screen.getByRole('generic')
      expect(container).toHaveClass('custom-skeleton')
    })
  })
})

describe('LoadingCard', () => {
  describe('렌더링', () => {
    it('should render card with default props', () => {
      render(<LoadingCard />)
      
      const container = screen.getByRole('generic')
      expect(container).toHaveClass(
        'rounded-xl',
        'border',
        'bg-card',
        'p-6',
        'shadow',
        'animate-pulse',
        'space-y-4'
      )
      
      // Should have header elements
      const headerTitle = container.querySelector('.h-5.w-32.rounded.bg-muted')
      const headerSubtitle = container.querySelector('.h-4.w-48.rounded.bg-muted')
      expect(headerTitle).toBeInTheDocument()
      expect(headerSubtitle).toBeInTheDocument()
      
      // Should have content lines
      const contentLines = container.querySelectorAll('.space-y-2 .h-4.rounded.bg-muted')
      expect(contentLines).toHaveLength(3)
    })
    
    it('should show avatar when showAvatar is true', () => {
      render(<LoadingCard showAvatar />)
      
      const container = screen.getByRole('generic')
      const avatar = container.querySelector('.h-10.w-10.rounded-full.bg-muted')
      expect(avatar).toBeInTheDocument()
    })
    
    it('should show actions when showActions is true', () => {
      render(<LoadingCard showActions />)
      
      const container = screen.getByRole('generic')
      const actions = container.querySelectorAll('.h-9.rounded.bg-muted')
      expect(actions).toHaveLength(2) // Two action buttons
      
      const firstAction = container.querySelector('.h-9.w-20.rounded.bg-muted')
      const secondAction = container.querySelector('.h-9.w-16.rounded.bg-muted')
      expect(firstAction).toBeInTheDocument()
      expect(secondAction).toBeInTheDocument()
    })
    
    it('should have proper content line widths', () => {
      render(<LoadingCard />)
      
      const container = screen.getByRole('generic')
      const contentContainer = container.querySelector('.space-y-2')
      const lines = contentContainer?.querySelectorAll('.h-4.rounded.bg-muted')
      
      expect(lines![0]).toHaveClass('w-full')
      expect(lines![1]).toHaveClass('w-5/6')
      expect(lines![2]).toHaveClass('w-4/6')
    })
  })

  describe('커스텀 속성', () => {
    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLDivElement>()
      
      render(<LoadingCard ref={ref} />)
      
      expect(ref.current).toBeInstanceOf(HTMLDivElement)
    })
    
    it('should accept custom className', () => {
      render(<LoadingCard className="custom-card" />)
      
      const container = screen.getByRole('generic')
      expect(container).toHaveClass('custom-card')
    })
  })
})

describe('LoadingPage', () => {
  describe('렌더링', () => {
    it('should render with default Korean text', () => {
      render(<LoadingPage />)
      
      expect(screen.getByText('로딩 중...')).toBeInTheDocument()
      expect(screen.getByText('잠시만 기다려 주세요')).toBeInTheDocument()
    })
    
    it('should render with custom title and description', () => {
      render(
        <LoadingPage 
          title="데이터 불러오는 중..." 
          description="서버에서 최신 정보를 가져오고 있습니다" 
        />
      )
      
      expect(screen.getByText('데이터 불러오는 중...')).toBeInTheDocument()
      expect(screen.getByText('서버에서 최신 정보를 가져오고 있습니다')).toBeInTheDocument()
    })
    
    it('should have proper layout structure', () => {
      render(<LoadingPage />)
      
      const container = screen.getByText('로딩 중...').closest('div')?.parentElement?.parentElement
      expect(container).toHaveClass('flex', 'min-h-[50vh]', 'items-center', 'justify-center')
      
      const textContainer = screen.getByText('로딩 중...').closest('div')?.parentElement
      expect(textContainer).toHaveClass('text-center', 'space-y-4')
    })
    
    it('should include LoadingSpinner', () => {
      render(<LoadingPage />)
      
      const container = screen.getByText('로딩 중...').closest('div')?.parentElement?.parentElement
      const spinner = container?.querySelector('svg')
      expect(spinner).toHaveClass('animate-spin')
    })
  })

  describe('한국어 텍스트', () => {
    it('should contain Korean text by default', () => {
      render(<LoadingPage />)
      
      const title = screen.getByText('로딩 중...')
      const description = screen.getByText('잠시만 기다려 주세요')
      
      expect(title).toContainKoreanText()
      expect(description).toContainKoreanText()
    })
    
    it('should have korean-text class', () => {
      render(<LoadingPage />)
      
      const title = screen.getByText('로딩 중...')
      const description = screen.getByText('잠시만 기다려 주세요')
      
      expect(title).toHaveClass('korean-text')
      expect(description).toHaveClass('korean-text')
    })
    
    it('should support custom Korean text', () => {
      const customTexts = [
        { title: '사용자 정보 로딩 중...', description: '계정 정보를 불러오고 있습니다' },
        { title: '파일 업로드 중...', description: '파일을 서버에 업로드하고 있습니다' },
        { title: '데이터 분석 중...', description: 'GA4 데이터를 분석하고 있습니다' }
      ]
      
      customTexts.forEach(({ title, description }) => {
        const { unmount } = render(<LoadingPage title={title} description={description} />)
        
        expect(screen.getByText(title)).toContainKoreanText()
        expect(screen.getByText(description)).toContainKoreanText()
        
        unmount()
      })
    })
  })

  describe('타이포그래피', () => {
    it('should have proper text styling', () => {
      render(<LoadingPage />)
      
      const title = screen.getByText('로딩 중...')
      const description = screen.getByText('잠시만 기다려 주세요')
      
      expect(title).toHaveClass('text-lg', 'font-semibold', 'korean-text')
      expect(description).toHaveClass('text-sm', 'text-muted-foreground', 'korean-text')
    })
  })
})

describe('통합 테스트', () => {
  describe('애니메이션', () => {
    it('should have consistent animation classes across components', () => {
      render(
        <div>
          <LoadingSpinner data-testid="spinner" />
          <LoadingSkeleton data-testid="skeleton" />
          <LoadingCard data-testid="card" />
        </div>
      )
      
      const spinner = screen.getByTestId('spinner')
      const skeleton = screen.getByTestId('skeleton')
      const card = screen.getByTestId('card')
      
      // Spinner should have spin animation
      const spinnerIcon = spinner.querySelector('svg')
      expect(spinnerIcon).toHaveClass('animate-spin')
      
      // Skeleton should have pulse animation
      expect(skeleton).toHaveClass('animate-pulse')
      
      // Card should have pulse animation
      expect(card).toHaveClass('animate-pulse')
    })
  })

  describe('접근성', () => {
    it('should be accessible to screen readers', () => {
      render(
        <div>
          <LoadingSpinner aria-label="데이터 로딩 중" />
          <LoadingPage title="로딩 중..." description="잠시만 기다려 주세요" />
        </div>
      )
      
      const spinner = screen.getByLabelText('데이터 로딩 중')
      expect(spinner).toBeInTheDocument()
      
      // Loading page should have proper semantic structure
      const title = screen.getByText('로딩 중...')
      expect(title.tagName).toBe('H2')
    })
    
    it('should provide proper loading context', () => {
      render(<LoadingPage title="사용자 데이터 로딩 중" description="프로필 정보를 불러오고 있습니다" />)
      
      // Should provide clear loading context in Korean
      expect(screen.getByText('사용자 데이터 로딩 중')).toBeInTheDocument()
      expect(screen.getByText('프로필 정보를 불러오고 있습니다')).toBeInTheDocument()
    })
  })

  describe('반응형 디자인', () => {
    it('should work on different screen sizes', () => {
      render(
        <div>
          <LoadingSpinner size="sm" className="md:hidden" />
          <LoadingSpinner size="lg" className="hidden md:block" />
        </div>
      )
      
      const smallSpinner = screen.getByRole('generic', { hidden: true })
      expect(smallSpinner).toHaveClass('md:hidden')
      
      const containers = screen.getAllByRole('generic')
      const largeSpinner = containers.find(container => 
        container.classList.contains('hidden') && container.classList.contains('md:block')
      )
      expect(largeSpinner).toHaveClass('hidden', 'md:block')
    })
  })

  describe('성능', () => {
    it('should not cause memory leaks with overlay spinner', () => {
      const { unmount } = render(<LoadingSpinner variant="overlay" />)
      
      // Should unmount cleanly without errors
      expect(() => unmount()).not.toThrow()
    })
    
    it('should handle rapid re-renders', () => {
      let renderCount = 0
      
      const TestComponent = () => {
        renderCount++
        return <LoadingSkeleton lines={renderCount % 5 + 1} />
      }
      
      const { rerender } = render(<TestComponent />)
      
      // Rapidly re-render multiple times
      for (let i = 0; i < 10; i++) {
        rerender(<TestComponent />)
      }
      
      expect(renderCount).toBe(11) // Initial + 10 re-renders
    })
  })
})