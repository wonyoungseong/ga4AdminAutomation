import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../button'

describe('Button', () => {
  describe('렌더링', () => {
    it('should render button with text', () => {
      render(<Button>클릭하세요</Button>)
      
      expect(screen.getByRole('button')).toHaveTextContent('클릭하세요')
    })
    
    it('should render as child component when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">링크 버튼</a>
        </Button>
      )
      
      const link = screen.getByRole('link')
      expect(link).toHaveTextContent('링크 버튼')
      expect(link).toHaveAttribute('href', '/test')
    })
    
    it('should forward ref correctly', () => {
      const ref = React.createRef<HTMLButtonElement>()
      
      render(<Button ref={ref}>테스트</Button>)
      
      expect(ref.current).toBeInstanceOf(HTMLButtonElement)
      expect(ref.current).toHaveTextContent('테스트')
    })
  })

  describe('변형(Variants)', () => {
    it('should apply default variant styling', () => {
      render(<Button>기본 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-primary', 'text-primary-foreground', 'shadow')
    })
    
    it('should apply destructive variant styling', () => {
      render(<Button variant="destructive">삭제 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-destructive', 'text-destructive-foreground')
    })
    
    it('should apply outline variant styling', () => {
      render(<Button variant="outline">외곽선 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border', 'border-input', 'bg-background')
    })
    
    it('should apply secondary variant styling', () => {
      render(<Button variant="secondary">보조 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-secondary', 'text-secondary-foreground')
    })
    
    it('should apply ghost variant styling', () => {
      render(<Button variant="ghost">고스트 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:bg-accent', 'hover:text-accent-foreground')
    })
    
    it('should apply link variant styling', () => {
      render(<Button variant="link">링크 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('text-primary', 'underline-offset-4', 'hover:underline')
    })
  })

  describe('크기(Sizes)', () => {
    it('should apply default size styling', () => {
      render(<Button>기본 크기</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10', 'px-4', 'py-2', 'min-w-[2.5rem]')
    })
    
    it('should apply small size styling', () => {
      render(<Button size="sm">작은 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-9', 'px-3', 'text-xs', 'min-w-[2rem]')
    })
    
    it('should apply large size styling', () => {
      render(<Button size="lg">큰 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-11', 'px-6', 'text-base', 'min-w-[3rem]')
    })
    
    it('should apply icon size styling', () => {
      render(<Button size="icon">🔍</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10', 'w-10')
    })
    
    it('should apply extra small size styling', () => {
      render(<Button size="xs">아주 작은</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-8', 'px-2', 'text-xs', 'min-w-[1.75rem]')
    })
  })

  describe('한국어 텍스트', () => {
    it('should have korean-text class for Korean text support', () => {
      render(<Button>한글 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('korean-text')
    })
    
    it('should contain Korean text', () => {
      render(<Button>로그인</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toContainKoreanText()
    })
    
    it('should render Korean text with proper typography', () => {
      const koreanButtons = [
        '로그인',
        '회원가입',
        '비밀번호 재설정',
        '계정 삭제',
        '프로필 수정'
      ]
      
      koreanButtons.forEach((text, index) => {
        render(<Button key={index}>{text}</Button>)
        
        const button = screen.getByText(text)
        expect(button).toHaveClass('korean-text')
        expect(button).toContainKoreanText()
      })
    })
    
    it('should handle mixed Korean and English text', () => {
      render(<Button>Save 저장</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveTextContent('Save 저장')
      expect(button).toHaveClass('korean-text')
    })
  })

  describe('상호작용', () => {
    it('should handle click events', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()
      
      render(<Button onClick={handleClick}>클릭 테스트</Button>)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })
    
    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>비활성화 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(button).toHaveClass('disabled:pointer-events-none', 'disabled:opacity-50')
    })
    
    it('should not call onClick when disabled', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()
      
      render(<Button disabled onClick={handleClick}>비활성화 버튼</Button>)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleClick).not.toHaveBeenCalled()
    })
    
    it('should support keyboard navigation', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()
      
      render(<Button onClick={handleClick}>키보드 테스트</Button>)
      
      const button = screen.getByRole('button')
      button.focus()
      
      expect(button).toHaveFocus()
      
      await user.keyboard('{Enter}')
      expect(handleClick).toHaveBeenCalledTimes(1)
      
      await user.keyboard(' ')
      expect(handleClick).toHaveBeenCalledTimes(2)
    })
  })

  describe('접근성', () => {
    it('should have proper button role', () => {
      render(<Button>접근성 테스트</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })
    
    it('should support aria-label', () => {
      render(<Button aria-label="검색 버튼">🔍</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveAccessibleName('검색 버튼')
    })
    
    it('should support aria-describedby', () => {
      render(
        <div>
          <Button aria-describedby="button-help">도움말 버튼</Button>
          <div id="button-help">이 버튼은 도움말을 표시합니다</div>
        </div>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-describedby', 'button-help')
    })
    
    it('should have focus-visible styles', () => {
      render(<Button>포커스 테스트</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass(
        'focus-visible:outline-none',
        'focus-visible:ring-2',
        'focus-visible:ring-ring',
        'focus-visible:ring-offset-2'
      )
    })
    
    it('should have minimum touch target size for mobile', () => {
      render(<Button>터치 타겟</Button>)
      
      const button = screen.getByRole('button')
      // Default size should meet minimum 44px touch target
      expect(button).toHaveClass('h-10') // 40px minimum height + padding
      expect(button).toHaveClass('min-w-[2.5rem]') // 40px minimum width
    })
  })

  describe('애니메이션', () => {
    it('should have hover animation classes', () => {
      render(<Button>애니메이션 테스트</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass(
        'transition-all',
        'duration-[var(--animation-duration-fast)]',
        'ease-[var(--animation-easing)]',
        'hover:scale-[1.02]',
        'active:scale-[0.98]'
      )
    })
    
    it('should have SVG icon animation classes', () => {
      render(<Button>테스트 <svg><path /></svg></Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass(
        '[&_svg]:transition-transform',
        '[&_svg]:duration-[var(--animation-duration-fast)]',
        'hover:[&_svg]:scale-105'
      )
    })
    
    it('should have shadow animation for default variant', () => {
      render(<Button>그림자 애니메이션</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:shadow-lg')
    })
  })

  describe('커스텀 클래스', () => {
    it('should merge custom className with default classes', () => {
      render(<Button className="custom-class">커스텀 클래스</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
      expect(button).toHaveClass('bg-primary') // Should still have default classes
    })
    
    it('should allow className to override default styles', () => {
      render(<Button className="bg-red-500">빨간 버튼</Button>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-red-500')
    })
  })

  describe('다양한 콘텐츠', () => {
    it('should render with icon and text', () => {
      render(
        <Button>
          <svg data-testid="icon"><path /></svg>
          저장하기
        </Button>
      )
      
      expect(screen.getByTestId('icon')).toBeInTheDocument()
      expect(screen.getByText('저장하기')).toBeInTheDocument()
    })
    
    it('should render icon-only button', () => {
      render(
        <Button size="icon" aria-label="메뉴">
          <svg data-testid="menu-icon"><path /></svg>
        </Button>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveAccessibleName('메뉴')
      expect(screen.getByTestId('menu-icon')).toBeInTheDocument()
    })
    
    it('should handle complex children', () => {
      render(
        <Button>
          <span className="font-bold">굵은 텍스트</span>
          <span className="text-sm ml-2">작은 텍스트</span>
        </Button>
      )
      
      expect(screen.getByText('굵은 텍스트')).toHaveClass('font-bold')
      expect(screen.getByText('작은 텍스트')).toHaveClass('text-sm', 'ml-2')
    })
  })

  describe('폼 통합', () => {
    it('should work as form submit button', async () => {
      const handleSubmit = jest.fn()
      const user = userEvent.setup()
      
      render(
        <form onSubmit={handleSubmit}>
          <Button type="submit">제출</Button>
        </form>
      )
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleSubmit).toHaveBeenCalled()
    })
    
    it('should work as reset button', () => {
      render(
        <form>
          <input defaultValue="test" />
          <Button type="reset">초기화</Button>
        </form>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'reset')
    })
  })
})