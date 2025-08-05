import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { mobileUtils } from '@/test/test-utils'
import { Button } from '@/components/ui/button'
import { KoreanInput } from '@/components/ui/korean-form'
import { LoadingSpinner } from '@/components/ui/loading'

describe('Mobile Responsiveness Tests', () => {
  beforeEach(() => {
    // Reset viewport to desktop by default
    mobileUtils.setDesktopViewport()
  })

  describe('Touch Target Requirements', () => {
    it('should meet minimum touch target size for buttons', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div>
          <Button size="default">기본 버튼</Button>
          <Button size="sm">작은 버튼</Button>
          <Button size="lg">큰 버튼</Button>
          <Button size="xs">매우 작은 버튼</Button>
        </div>
      )
      
      const defaultButton = screen.getByText('기본 버튼')
      const smallButton = screen.getByText('작은 버튼')
      const largeButton = screen.getByText('큰 버튼')
      const extraSmallButton = screen.getByText('매우 작은 버튼')
      
      // Default button should meet minimum touch target
      expect(defaultButton).toHaveClass('h-10') // 40px
      expect(defaultButton).toHaveClass('min-w-[2.5rem]') // 40px
      
      // Small button should still be accessible
      expect(smallButton).toHaveClass('h-9') // 36px
      expect(smallButton).toHaveClass('min-w-[2rem]') // 32px
      
      // Large button exceeds minimum
      expect(largeButton).toHaveClass('h-11') // 44px
      expect(largeButton).toHaveClass('min-w-[3rem]') // 48px
      
      // Extra small might be below minimum but should have proper spacing
      expect(extraSmallButton).toHaveClass('h-8') // 32px
      expect(extraSmallButton).toHaveClass('min-w-[1.75rem]') // 28px
    })
    
    it('should have adequate spacing between touch targets', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div className="space-y-2">
          <Button>첫 번째 버튼</Button>
          <Button>두 번째 버튼</Button>
          <Button>세 번째 버튼</Button>
        </div>
      )
      
      const container = screen.getByText('첫 번째 버튼').parentElement
      expect(container).toHaveClass('space-y-2') // 8px spacing
    })
    
    it('should handle input field touch targets', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div className="space-y-4">
          <KoreanInput label="이름" />
          <KoreanInput label="이메일" />
          <KoreanInput label="전화번호" />
        </div>
      )
      
      const inputs = screen.getAllByRole('textbox')
      
      inputs.forEach(input => {
        // Input fields should have reasonable height for touch
        const styles = window.getComputedStyle(input)
        expect(input.classList.toString()).toMatch(/h-\d+/) // Should have height class
      })
    })
  })

  describe('Viewport Responsive Behavior', () => {
    it('should adapt to mobile viewport', () => {
      const TestComponent = () => (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Button className="w-full md:w-auto">모바일 전체 너비</Button>
          <Button className="hidden md:block">데스크톱만 표시</Button>
          <Button className="md:hidden">모바일만 표시</Button>
        </div>
      )
      
      // Test mobile viewport
      mobileUtils.setMobileViewport()
      render(<TestComponent />)
      
      const fullWidthButton = screen.getByText('모바일 전체 너비')
      const mobileOnlyButton = screen.getByText('모바일만 표시')
      
      expect(fullWidthButton).toHaveClass('w-full', 'md:w-auto')
      expect(mobileOnlyButton).toHaveClass('md:hidden')
      
      // Desktop-only button should be hidden
      const desktopOnlyButton = screen.getByText('데스크톱만 표시')
      expect(desktopOnlyButton).toHaveClass('hidden', 'md:block')
    })
    
    it('should handle Korean text wrapping on mobile', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div className="max-w-sm">
          <p className="korean-text text-wrap break-words">
            이것은 긴 한국어 텍스트 예제입니다. 모바일 화면에서 적절히 줄바꿈되어야 합니다.
          </p>
        </div>
      )
      
      const text = screen.getByText(/이것은 긴 한국어 텍스트/)
      expect(text).toHaveClass('korean-text', 'text-wrap', 'break-words')
    })
  })

  describe('Touch Events', () => {
    it('should handle touch events on buttons', async () => {
      const handleClick = jest.fn()
      mobileUtils.setMobileViewport()
      
      render(<Button onClick={handleClick}>터치 테스트</Button>)
      
      const button = screen.getByText('터치 테스트')
      
      // Simulate touch event
      const touchEvent = mobileUtils.createTouchEvent('touchstart', [
        { clientX: 100, clientY: 100 }
      ])
      
      button.dispatchEvent(touchEvent)
      
      // Follow with click event (as browsers typically do)
      const user = userEvent.setup()
      await user.click(button)
      
      expect(handleClick).toHaveBeenCalled()
    })
    
    it('should handle touch events on form inputs', async () => {
      mobileUtils.setMobileViewport()
      
      render(<KoreanInput label="터치 입력 테스트" />)
      
      const input = screen.getByRole('textbox')
      
      // Simulate touch focus
      const touchEvent = mobileUtils.createTouchEvent('touchstart', [
        { clientX: 150, clientY: 50 }
      ])
      
      input.dispatchEvent(touchEvent)
      input.focus()
      
      expect(input).toHaveFocus()
    })
    
    it('should handle multi-touch gestures gracefully', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div data-testid="multi-touch-area" className="p-8 bg-gray-100">
          <p>다중 터치 영역</p>
        </div>
      )
      
      const area = screen.getByTestId('multi-touch-area')
      
      // Simulate multi-touch (pinch gesture)
      const multiTouchEvent = mobileUtils.createTouchEvent('touchstart', [
        { clientX: 100, clientY: 100 },
        { clientX: 200, clientY: 200 }
      ])
      
      expect(() => {
        area.dispatchEvent(multiTouchEvent)
      }).not.toThrow()
    })
  })

  describe('Mobile Navigation', () => {
    it('should handle mobile-friendly navigation patterns', () => {
      mobileUtils.setMobileViewport()
      
      const MobileNav = () => (
        <nav className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4">
          <Button variant="ghost" className="justify-start">홈</Button>
          <Button variant="ghost" className="justify-start">대시보드</Button>
          <Button variant="ghost" className="justify-start">설정</Button>
        </nav>
      )
      
      render(<MobileNav />)
      
      const nav = screen.getByRole('navigation')
      expect(nav).toHaveClass('flex', 'flex-col', 'md:flex-row', 'space-y-2', 'md:space-y-0')
      
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveClass('justify-start')
      })
    })
    
    it('should support hamburger menu pattern', async () => {
      mobileUtils.setMobileViewport()
      
      const MobileMenu = () => {
        const [isOpen, setIsOpen] = React.useState(false)
        
        return (
          <div>
            <Button 
              size="icon" 
              onClick={() => setIsOpen(!isOpen)}
              aria-label="메뉴 열기"
              className="md:hidden"
            >
              ☰
            </Button>
            {isOpen && (
              <div className="md:hidden">
                <Button variant="ghost" className="w-full justify-start">홈</Button>
                <Button variant="ghost" className="w-full justify-start">대시보드</Button>
              </div>
            )}
          </div>
        )
      }
      
      const user = userEvent.setup()
      render(<MobileMenu />)
      
      const menuButton = screen.getByLabelText('메뉴 열기')
      expect(menuButton).toHaveClass('md:hidden')
      
      // Menu should be closed initially
      expect(screen.queryByText('홈')).not.toBeInTheDocument()
      
      // Open menu
      await user.click(menuButton)
      
      expect(screen.getByText('홈')).toBeInTheDocument()
      expect(screen.getByText('대시보드')).toBeInTheDocument()
      
      const homeButton = screen.getByText('홈')
      expect(homeButton).toHaveClass('w-full', 'justify-start')
    })
  })

  describe('Mobile Forms', () => {
    it('should optimize form layout for mobile', () => {
      mobileUtils.setMobileViewport()
      
      const MobileForm = () => (
        <form className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <KoreanInput label="이름" />
            <KoreanInput label="이메일" />
          </div>
          <KoreanInput label="전화번호" />
          <Button type="submit" className="w-full md:w-auto">
            제출
          </Button>
        </form>
      )
      
      render(<MobileForm />)
      
      const form = screen.getByRole('form')
      const gridContainer = form.querySelector('.grid')
      const submitButton = screen.getByText('제출')
      
      expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'gap-4')
      expect(submitButton).toHaveClass('w-full', 'md:w-auto')
    })
    
    it('should handle mobile keyboard interactions', async () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div>
          <KoreanInput label="이메일" type="email" />
          <KoreanInput label="전화번호" type="tel" />
          <KoreanInput label="숫자" type="number" />
        </div>
      )
      
      const emailInput = screen.getByLabelText('이메일')
      const phoneInput = screen.getByLabelText('전화번호')
      const numberInput = screen.getByLabelText('숫자')
      
      expect(emailInput).toHaveAttribute('type', 'email')
      expect(phoneInput).toHaveAttribute('type', 'tel')
      expect(numberInput).toHaveAttribute('type', 'number')
    })
  })

  describe('Mobile Loading States', () => {
    it('should show appropriate loading states on mobile', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div>
          <LoadingSpinner size="sm" className="md:hidden" />
          <LoadingSpinner size="lg" className="hidden md:block" />
        </div>
      )
      
      const spinners = screen.getAllByRole('generic')
      const mobileSpinner = spinners.find(spinner => 
        spinner.classList.contains('md:hidden')
      )
      const desktopSpinner = spinners.find(spinner => 
        spinner.classList.contains('hidden') && spinner.classList.contains('md:block')
      )
      
      expect(mobileSpinner).toHaveClass('md:hidden')
      expect(desktopSpinner).toHaveClass('hidden', 'md:block')
    })
    
    it('should handle mobile-optimized loading cards', () => {
      mobileUtils.setMobileViewport()
      
      const MobileLoadingGrid = () => (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="w-full">
              <div className="rounded-lg border p-4 animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-muted rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      )
      
      render(<MobileLoadingGrid />)
      
      const grid = screen.getByRole('generic')
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3')
      
      const cards = screen.getAllByRole('generic').filter(el => 
        el.classList.contains('animate-pulse')
      )
      expect(cards).toHaveLength(3)
      
      cards.forEach(card => {
        expect(card).toHaveClass('w-full')
      })
    })
  })

  describe('Accessibility on Mobile', () => {
    it('should maintain accessibility on mobile devices', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div>
          <Button aria-label="검색">🔍</Button>
          <KoreanInput label="사용자명" required />
          <Button disabled>비활성화됨</Button>
        </div>
      )
      
      const searchButton = screen.getByLabelText('검색')
      const input = screen.getByLabelText('사용자명 *')
      const disabledButton = screen.getByText('비활성화됨')
      
      expect(searchButton).toHaveAccessibleName('검색')
      expect(input).toBeRequired()
      expect(disabledButton).toBeDisabled()
    })
    
    it('should support screen reader navigation on mobile', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div>
          <h1>모바일 페이지 제목</h1>
          <nav aria-label="주 내비게이션">
            <Button>홈</Button>
            <Button>설정</Button>
          </nav>
          <main>
            <h2>콘텐츠 영역</h2>
            <p>모바일에서도 스크린 리더가 잘 작동해야 합니다.</p>
          </main>
        </div>
      )
      
      const heading = screen.getByRole('heading', { level: 1 })
      const nav = screen.getByRole('navigation')
      const main = screen.getByRole('main')
      const subHeading = screen.getByRole('heading', { level: 2 })
      
      expect(heading).toHaveTextContent('모바일 페이지 제목')
      expect(nav).toHaveAttribute('aria-label', '주 내비게이션')
      expect(main).toBeInTheDocument()
      expect(subHeading).toHaveTextContent('콘텐츠 영역')
    })
  })

  describe('Korean Text on Mobile', () => {
    it('should render Korean text properly on mobile', () => {
      mobileUtils.setMobileViewport()
      
      render(
        <div className="p-4">
          <h1 className="korean-text text-xl font-bold mb-4">
            GA4 관리자 자동화 시스템
          </h1>
          <p className="korean-text text-sm text-gray-600 leading-relaxed">
            이 시스템은 Google Analytics 4 속성 관리를 자동화하여 효율성을 높이고 
            사용자 경험을 개선합니다.
          </p>
          <Button className="mt-4 w-full korean-text">
            시작하기
          </Button>
        </div>
      )
      
      const title = screen.getByText('GA4 관리자 자동화 시스템')
      const description = screen.getByText(/이 시스템은 Google Analytics/)
      const button = screen.getByText('시작하기')
      
      expect(title).toHaveClass('korean-text')
      expect(description).toHaveClass('korean-text', 'leading-relaxed')
      expect(button).toHaveClass('korean-text', 'w-full')
      
      expect(title).toContainKoreanText()
      expect(description).toContainKoreanText()
      expect(button).toContainKoreanText()
    })
    
    it('should handle Korean input on mobile keyboards', async () => {
      mobileUtils.setMobileViewport()
      const user = userEvent.setup()
      
      render(<KoreanInput label="한국어 입력" placeholder="한글을 입력하세요" />)
      
      const input = screen.getByRole('textbox')
      
      await user.type(input, '안녕하세요')
      
      expect(input).toHaveValue('안녕하세요')
      expect(input).toHaveClass('korean-text')
    })
  })

  describe('Performance on Mobile', () => {
    it('should render efficiently on mobile devices', () => {
      mobileUtils.setMobileViewport()
      
      const startTime = performance.now()
      
      render(
        <div>
          {Array.from({ length: 10 }, (_, i) => (
            <Button key={i} className="mb-2 w-full">
              버튼 {i + 1}
            </Button>
          ))}
        </div>
      )
      
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      // Render should complete reasonably quickly
      expect(renderTime).toBeLessThan(100) // 100ms threshold
      
      // All buttons should be rendered
      for (let i = 1; i <= 10; i++) {
        expect(screen.getByText(`버튼 ${i}`)).toBeInTheDocument()
      }
    })
    
    it('should handle rapid viewport changes', () => {
      render(
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button>모바일/데스크톱 버튼</Button>
        </div>
      )
      
      const container = screen.getByRole('generic')
      
      // Start mobile
      mobileUtils.setMobileViewport()
      expect(container).toHaveClass('grid-cols-1')
      
      // Switch to desktop
      mobileUtils.setDesktopViewport()
      expect(container).toHaveClass('md:grid-cols-3')
      
      // Switch back to mobile
      mobileUtils.setMobileViewport()
      expect(container).toHaveClass('grid-cols-1')
    })
  })
})