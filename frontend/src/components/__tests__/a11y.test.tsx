import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { a11yUtils } from '@/test/test-utils'
import { Button } from '@/components/ui/button'
import { KoreanInput, KoreanFormField } from '@/components/ui/korean-form'
import { LoadingSpinner, LoadingPage } from '@/components/ui/loading'

describe('Accessibility (WCAG 2.1 AA) Tests', () => {
  describe('1. 인식 가능성 (Perceivable)', () => {
    describe('1.1 대체 텍스트', () => {
      it('should provide accessible names for interactive elements', () => {
        render(
          <div>
            <Button aria-label="검색">🔍</Button>
            <Button aria-label="메뉴 열기">☰</Button>
            <Button>저장</Button>
          </div>
        )
        
        const searchButton = screen.getByLabelText('검색')
        const menuButton = screen.getByLabelText('메뉴 열기')
        const saveButton = screen.getByText('저장')
        
        expect(searchButton).toHaveAccessibleName('검색')
        expect(menuButton).toHaveAccessibleName('메뉴 열기')
        expect(saveButton).toHaveAccessibleName('저장')
      })
      
      it('should provide accessible names for form elements', () => {
        render(
          <div>
            <KoreanInput label="사용자 이름" required />
            <KoreanInput label="이메일 주소" type="email" />
            <KoreanFormField label="설명" description="선택사항입니다">
              <textarea aria-describedby="description-help" />
            </KoreanFormField>
          </div>
        )
        
        const nameInput = screen.getByLabelText('사용자 이름 *')
        const emailInput = screen.getByLabelText('이메일 주소')
        const descriptionField = screen.getByLabelText('설명')
        
        expect(nameInput).toHaveAccessibleName('사용자 이름 *')
        expect(emailInput).toHaveAccessibleName('이메일 주소')
        expect(descriptionField).toHaveAccessibleName('설명')
      })
      
      it('should provide context for loading states', () => {
        render(
          <div>
            <LoadingSpinner aria-label="데이터 로딩 중" />
            <LoadingPage title="사용자 정보 로딩 중" description="프로필을 불러오고 있습니다" />
          </div>
        )
        
        const spinner = screen.getByLabelText('데이터 로딩 중')
        const loadingTitle = screen.getByText('사용자 정보 로딩 중')
        const loadingDescription = screen.getByText('프로필을 불러오고 있습니다')
        
        expect(spinner).toHaveAccessibleName('데이터 로딩 중')
        expect(loadingTitle).toBeInTheDocument()
        expect(loadingDescription).toBeInTheDocument()
      })
    })

    describe('1.3 적응 가능', () => {
      it('should use proper heading hierarchy', () => {
        render(
          <div>
            <h1>GA4 관리자 시스템</h1>
            <h2>대시보드</h2>
            <h3>사용자 통계</h3>
            <h3>시스템 상태</h3>
            <h2>설정</h2>
            <h3>계정 설정</h3>
          </div>
        )
        
        const h1 = screen.getByRole('heading', { level: 1 })
        const h2Elements = screen.getAllByRole('heading', { level: 2 })
        const h3Elements = screen.getAllByRole('heading', { level: 3 })
        
        expect(h1).toHaveTextContent('GA4 관리자 시스템')
        expect(h2Elements).toHaveLength(2)
        expect(h3Elements).toHaveLength(3)
      })
      
      it('should use semantic HTML elements', () => {
        render(
          <div>
            <header>
              <nav aria-label="주 내비게이션">
                <Button>홈</Button>
                <Button>대시보드</Button>
              </nav>
            </header>
            <main>
              <article>
                <h1>메인 콘텐츠</h1>
                <p>시스템 개요입니다.</p>
              </article>
            </main>
            <footer>
              <p>© 2024 GA4 Admin System</p>
            </footer>
          </div>
        )
        
        const header = screen.getByRole('banner')
        const nav = screen.getByRole('navigation')
        const main = screen.getByRole('main')
        const article = screen.getByRole('article')
        const footer = screen.getByRole('contentinfo')
        
        expect(header).toBeInTheDocument()
        expect(nav).toHaveAttribute('aria-label', '주 내비게이션')
        expect(main).toBeInTheDocument()
        expect(article).toBeInTheDocument()
        expect(footer).toBeInTheDocument()
      })
      
      it('should provide logical reading order', () => {
        render(
          <div>
            <h1>폼 제목</h1>
            <form>
              <fieldset>
                <legend>개인 정보</legend>
                <KoreanInput label="이름" />
                <KoreanInput label="이메일" />
              </fieldset>
              <fieldset>
                <legend>연락처 정보</legend>
                <KoreanInput label="전화번호" />
                <KoreanInput label="주소" />
              </fieldset>
              <Button type="submit">제출</Button>
            </form>
          </div>
        )
        
        const title = screen.getByRole('heading')
        const form = screen.getByRole('form')
        const fieldsets = screen.getAllByRole('group')
        const submitButton = screen.getByRole('button', { name: '제출' })
        
        expect(title).toBeInTheDocument()
        expect(form).toBeInTheDocument()
        expect(fieldsets).toHaveLength(2)
        expect(submitButton).toBeInTheDocument()
        
        // Check legends
        expect(screen.getByText('개인 정보')).toBeInTheDocument()
        expect(screen.getByText('연락처 정보')).toBeInTheDocument()
      })
    })

    describe('1.4 구별 가능', () => {
      it('should have proper color contrast (mock test)', () => {
        render(
          <div>
            <Button variant="default">기본 버튼</Button>
            <Button variant="destructive">삭제 버튼</Button>
            <Button variant="outline">외곽선 버튼</Button>
            <p className="text-muted-foreground">보조 텍스트</p>
          </div>
        )
        
        const defaultButton = screen.getByText('기본 버튼')
        const destructiveButton = screen.getByText('삭제 버튼')
        const outlineButton = screen.getByText('외곽선 버튼')
        const mutedText = screen.getByText('보조 텍스트')
        
        // Mock contrast check (in real implementation, you'd use actual contrast calculation)
        expect(a11yUtils.hasProperContrast(defaultButton)).toBe(true)
        expect(a11yUtils.hasProperContrast(destructiveButton)).toBe(true)
        expect(a11yUtils.hasProperContrast(outlineButton)).toBe(true)
        expect(a11yUtils.hasProperContrast(mutedText)).toBe(true)
      })
      
      it('should not rely solely on color for information', () => {
        render(
          <div>
            <KoreanInput 
              label="필수 입력" 
              required 
              error="오류가 발생했습니다"
            />
            <div className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>성공적으로 저장되었습니다</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-red-600">✗</span>
              <span>오류가 발생했습니다</span>
            </div>
          </div>
        )
        
        const requiredInput = screen.getByLabelText('필수 입력 *')
        const errorMessage = screen.getByText('오류가 발생했습니다')
        const successMessage = screen.getByText('성공적으로 저장되었습니다')
        const errorStatus = screen.getByText('오류가 발생했습니다')
        
        // Required indicator is * not just color
        expect(screen.getByText('*')).toBeInTheDocument()
        
        // Error state uses role="alert" not just color
        expect(errorMessage).toHaveAttribute('role', 'alert')
        
        // Status messages have icons not just color
        expect(screen.getByText('✓')).toBeInTheDocument()
        expect(screen.getByText('✗')).toBeInTheDocument()
      })
      
      it('should be resizable up to 200% without loss of functionality', () => {
        // Simulate zoom by testing responsive behavior
        Object.defineProperty(window, 'innerWidth', {
          writable: true,
          configurable: true,
          value: 640, // Half of normal desktop width (simulating 200% zoom)
        })
        
        render(
          <div className="max-w-lg mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">확대된 뷰</h1>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Button className="w-full sm:w-auto">버튼 1</Button>
              <Button className="w-full sm:w-auto">버튼 2</Button>
            </div>
            <p className="mt-4 text-wrap break-words">
              이 텍스트는 200% 확대 시에도 읽기 쉬워야 합니다.
            </p>
          </div>
        )
        
        const title = screen.getByRole('heading')
        const buttons = screen.getAllByRole('button')
        const text = screen.getByText(/이 텍스트는/)
        
        expect(title).toBeInTheDocument()
        expect(buttons).toHaveLength(2)
        expect(text).toHaveClass('text-wrap', 'break-words')
      })
    })
  })

  describe('2. 운용 가능성 (Operable)', () => {
    describe('2.1 키보드 접근성', () => {
      it('should be fully keyboard accessible', async () => {
        const user = userEvent.setup()
        
        render(
          <div>
            <input placeholder="첫 번째 입력" />
            <Button>첫 번째 버튼</Button>
            <Button>두 번째 버튼</Button>
            <input placeholder="두 번째 입력" />
            <Button disabled>비활성화된 버튼</Button>
          </div>
        )
        
        const firstInput = screen.getByPlaceholderText('첫 번째 입력')
        const firstButton = screen.getByText('첫 번째 버튼')
        const secondButton = screen.getByText('두 번째 버튼')
        const secondInput = screen.getByPlaceholderText('두 번째 입력')
        const disabledButton = screen.getByText('비활성화된 버튼')
        
        // Tab through interactive elements
        await user.tab()
        expect(firstInput).toHaveFocus()
        
        await user.tab()
        expect(firstButton).toHaveFocus()
        
        await user.tab()
        expect(secondButton).toHaveFocus()
        
        await user.tab()
        expect(secondInput).toHaveFocus()
        
        await user.tab()
        // Disabled button should be skipped
        expect(disabledButton).not.toHaveFocus()
      })
      
      it('should handle keyboard activation', async () => {
        const handleClick = jest.fn()
        const user = userEvent.setup()
        
        render(<Button onClick={handleClick}>키보드 테스트</Button>)
        
        const button = screen.getByText('키보드 테스트')
        button.focus()
        
        // Test Enter key
        await user.keyboard('{Enter}')
        expect(handleClick).toHaveBeenCalledTimes(1)
        
        // Test Space key
        await user.keyboard(' ')
        expect(handleClick).toHaveBeenCalledTimes(2)
      })
      
      it('should provide visible focus indicators', () => {
        render(
          <div>
            <Button>포커스 테스트</Button>
            <KoreanInput label="입력 필드" />
          </div>
        )
        
        const button = screen.getByText('포커스 테스트')
        const input = screen.getByRole('textbox')
        
        // Check focus-visible classes
        expect(button).toHaveClass(
          'focus-visible:outline-none',
          'focus-visible:ring-2',
          'focus-visible:ring-ring',
          'focus-visible:ring-offset-2'
        )
        
        // Input should also have focus styling
        expect(input.className).toMatch(/focus/)
      })
    })

    describe('2.2 발작 및 물리적 반응', () => {
      it('should not have rapidly flashing content', () => {
        render(
          <div>
            <LoadingSpinner />
            <div className="animate-pulse">
              <div className="h-4 bg-muted rounded"></div>
            </div>
          </div>
        )
        
        const spinner = screen.getByRole('generic')
        const pulseElement = screen.getByRole('generic').querySelector('.animate-pulse')
        
        // Animations should be smooth, not rapid flashing
        const spinnerIcon = spinner.querySelector('svg')
        expect(spinnerIcon).toHaveClass('animate-spin')
        expect(pulseElement).toHaveClass('animate-pulse')
        
        // These animations are smooth CSS transitions, not rapid flashing
      })
    })

    describe('2.3 탐색', () => {
      it('should provide clear navigation structure', () => {
        render(
          <div>
            <nav aria-label="주 내비게이션">
              <Button>홈</Button>
              <Button>대시보드</Button>
              <Button>설정</Button>
            </nav>
            <nav aria-label="보조 내비게이션">
              <Button>도움말</Button>
              <Button>문의</Button>
            </nav>
          </div>
        )
        
        const mainNav = screen.getByLabelText('주 내비게이션')
        const secondaryNav = screen.getByLabelText('보조 내비게이션')
        
        expect(mainNav).toContain(screen.getByText('홈'))
        expect(mainNav).toContain(screen.getByText('대시보드'))
        expect(mainNav).toContain(screen.getByText('설정'))
        
        expect(secondaryNav).toContain(screen.getByText('도움말'))
        expect(secondaryNav).toContain(screen.getByText('문의'))
      })
      
      it('should provide skip links for keyboard users', () => {
        render(
          <div>
            <a href="#main-content" className="sr-only focus:not-sr-only">
              메인 콘텐츠로 건너뛰기
            </a>
            <nav>
              <Button>내비게이션 링크</Button>
            </nav>
            <main id="main-content">
              <h1>메인 콘텐츠</h1>
            </main>
          </div>
        )
        
        const skipLink = screen.getByText('메인 콘텐츠로 건너뛰기')
        const mainContent = screen.getByRole('main')
        
        expect(skipLink).toHaveAttribute('href', '#main-content')
        expect(skipLink).toHaveClass('sr-only', 'focus:not-sr-only')
        expect(mainContent).toHaveAttribute('id', 'main-content')
      })
    })

    describe('2.4 내비게이션 가능', () => {
      it('should have descriptive page titles', () => {
        // Mock document.title
        Object.defineProperty(document, 'title', {
          writable: true,
          value: 'GA4 관리자 시스템 - 대시보드'
        })
        
        render(
          <div>
            <h1>대시보드</h1>
            <p>GA4 관리자 시스템에 오신 것을 환영합니다.</p>
          </div>
        )
        
        expect(document.title).toBe('GA4 관리자 시스템 - 대시보드')
        expect(document.title).toContainKoreanText()
      })
      
      it('should provide breadcrumb navigation', () => {
        render(
          <nav aria-label="경로">
            <ol className="flex items-center space-x-2">
              <li><a href="/">홈</a></li>
              <li aria-hidden="true">›</li>
              <li><a href="/dashboard">대시보드</a></li>
              <li aria-hidden="true">›</li>
              <li aria-current="page">사용자 관리</li>
            </ol>
          </nav>
        )
        
        const breadcrumb = screen.getByLabelText('경로')
        const currentPage = screen.getByText('사용자 관리')
        
        expect(breadcrumb).toBeInTheDocument()
        expect(currentPage).toHaveAttribute('aria-current', 'page')
        
        // Separators should be hidden from screen readers
        const separators = screen.getAllByText('›')
        separators.forEach(separator => {
          expect(separator).toHaveAttribute('aria-hidden', 'true')
        })
      })
    })

    describe('2.5 입력 방식', () => {
      it('should support multiple input methods', async () => {
        const user = userEvent.setup()
        
        render(
          <div>
            <KoreanInput label="텍스트 입력" />
            <Button>클릭/터치 버튼</Button>
          </div>
        )
        
        const input = screen.getByRole('textbox')
        const button = screen.getByText('클릭/터치 버튼')
        
        // Text input
        await user.type(input, '한글 입력')
        expect(input).toHaveValue('한글 입력')
        
        // Button interaction
        const handleClick = jest.fn()
        button.onclick = handleClick
        await user.click(button)
        expect(handleClick).toHaveBeenCalled()
      })
    })
  })

  describe('3. 이해 가능성 (Understandable)', () => {
    describe('3.1 읽기 가능', () => {
      it('should specify language for Korean content', () => {
        // Mock document.documentElement.lang
        Object.defineProperty(document.documentElement, 'lang', {
          writable: true,
          value: 'ko'
        })
        
        render(
          <div>
            <p>한국어 콘텐츠입니다.</p>
            <p lang="en">This is English content.</p>
          </div>
        )
        
        const englishText = screen.getByText('This is English content.')
        
        expect(document.documentElement.lang).toBe('ko')
        expect(englishText).toHaveAttribute('lang', 'en')
      })
      
      it('should use clear and simple language', () => {
        render(
          <div>
            <h1>사용자 계정 설정</h1>
            <p>개인 정보를 수정하거나 비밀번호를 변경할 수 있습니다.</p>
            <Button>저장</Button>
            <Button>취소</Button>
          </div>
        )
        
        const title = screen.getByText('사용자 계정 설정')
        const description = screen.getByText(/개인 정보를 수정하거나/)
        const saveButton = screen.getByText('저장')
        const cancelButton = screen.getByText('취소')
        
        // Text should be clear and actionable
        expect(title).toContainKoreanText()
        expect(description).toContainKoreanText()
        expect(saveButton).toContainKoreanText()
        expect(cancelButton).toContainKoreanText()
      })
    })

    describe('3.2 예측 가능', () => {
      it('should have consistent navigation patterns', () => {
        render(
          <div>
            <nav aria-label="주 내비게이션">
              <Button variant="ghost">홈</Button>
              <Button variant="ghost">대시보드</Button>
              <Button variant="ghost">설정</Button>
            </nav>
            <main>
              <nav aria-label="페이지 액션">
                <Button variant="default">추가</Button>
                <Button variant="outline">편집</Button>
                <Button variant="destructive">삭제</Button>
              </nav>
            </main>
          </div>
        )
        
        const mainNav = screen.getByLabelText('주 내비게이션')
        const actionNav = screen.getByLabelText('페이지 액션')
        
        // Main navigation uses ghost variant consistently
        const mainNavButtons = mainNav.querySelectorAll('button')
        mainNavButtons.forEach(button => {
          expect(button).toHaveClass('hover:bg-accent')
        })
        
        // Action buttons use appropriate variants
        const addButton = screen.getByText('추가')
        const editButton = screen.getByText('편집')
        const deleteButton = screen.getByText('삭제')
        
        expect(addButton).toHaveClass('bg-primary')
        expect(editButton).toHaveClass('border-input')
        expect(deleteButton).toHaveClass('bg-destructive')
      })
      
      it('should not trigger unexpected changes on focus', async () => {
        const user = userEvent.setup()
        let contextChanged = false
        
        render(
          <div>
            <Button
              onFocus={() => {
                // This should NOT happen on focus alone
                // contextChanged = true
              }}
              onClick={() => {
                contextChanged = true
              }}
            >
              테스트 버튼
            </Button>
            <div data-testid="status">
              {contextChanged ? '변경됨' : '변경되지 않음'}
            </div>
          </div>
        )
        
        const button = screen.getByText('테스트 버튼')
        const status = screen.getByTestId('status')
        
        // Focus should not trigger change
        button.focus()
        expect(status).toHaveTextContent('변경되지 않음')
        
        // Click should trigger change
        await user.click(button)
        expect(status).toHaveTextContent('변경됨')
      })
    })

    describe('3.3 입력 지원', () => {
      it('should provide clear error identification and description', () => {
        render(
          <form>
            <KoreanInput 
              label="이메일 주소" 
              error="올바른 이메일 형식을 입력해주세요"
              required
            />
            <KoreanInput 
              label="비밀번호" 
              type="password"
              error="비밀번호는 8자리 이상이어야 합니다"
              required
            />
            <Button type="submit">제출</Button>
          </form>
        )
        
        const emailError = screen.getByText('올바른 이메일 형식을 입력해주세요')
        const passwordError = screen.getByText('비밀번호는 8자리 이상이어야 합니다')
        
        // Errors should have alert role
        expect(emailError).toHaveAttribute('role', 'alert')
        expect(passwordError).toHaveAttribute('role', 'alert')
        
        // Errors should be in Korean and clear
        expect(emailError).toContainKoreanText()
        expect(passwordError).toContainKoreanText()
      })
      
      it('should provide helpful form labels and instructions', () => {
        render(
          <form>
            <KoreanFormField 
              label="비밀번호" 
              description="8자리 이상, 영문자와 숫자를 포함해야 합니다"
              required
            >
              <input type="password" />
            </KoreanFormField>
            <KoreanFormField 
              label="비밀번호 확인" 
              description="위에서 입력한 비밀번호를 다시 입력하세요"
              required
            >
              <input type="password" />
            </KoreanFormField>
          </form>
        )
        
        const passwordLabel = screen.getByText('비밀번호')
        const passwordHelp = screen.getByText('8자리 이상, 영문자와 숫자를 포함해야 합니다')
        const confirmLabel = screen.getByText('비밀번호 확인')
        const confirmHelp = screen.getByText('위에서 입력한 비밀번호를 다시 입력하세요')
        
        expect(passwordLabel).toContainKoreanText()
        expect(passwordHelp).toContainKoreanText()
        expect(confirmLabel).toContainKoreanText()
        expect(confirmHelp).toContainKoreanText()
      })
    })
  })

  describe('4. 견고성 (Robust)', () => {
    describe('4.1 호환성', () => {
      it('should use valid HTML structure', () => {
        render(
          <article>
            <header>
              <h1>기사 제목</h1>
              <time dateTime="2024-01-01">2024년 1월 1일</time>
            </header>
            <p>기사 내용입니다.</p>
            <footer>
              <p>작성자: 관리자</p>
            </footer>
          </article>
        )
        
        const article = screen.getByRole('article')
        const heading = screen.getByRole('heading')
        const time = screen.getByText('2024년 1월 1일')
        
        expect(article).toBeInTheDocument()
        expect(heading).toBeInTheDocument()
        expect(time).toHaveAttribute('dateTime', '2024-01-01')
      })
      
      it('should provide proper ARIA attributes', () => {
        render(
          <div>
            <button aria-expanded="false" aria-controls="menu">
              메뉴 열기
            </button>
            <div id="menu" hidden>
              <ul role="menu">
                <li role="menuitem">
                  <button>홈</button>
                </li>
                <li role="menuitem">
                  <button>설정</button>
                </li>
              </ul>
            </div>
            <div aria-live="polite" aria-atomic="true">
              <p>상태 메시지가 여기에 표시됩니다</p>
            </div>
          </div>
        )
        
        const menuButton = screen.getByText('메뉴 열기')
        const menu = screen.getByRole('menu', { hidden: true })
        const liveRegion = screen.getByText('상태 메시지가 여기에 표시됩니다').parentElement
        
        expect(menuButton).toHaveAttribute('aria-expanded', 'false')
        expect(menuButton).toHaveAttribute('aria-controls', 'menu')
        expect(menu).toHaveAttribute('id', 'menu')
        expect(liveRegion).toHaveAttribute('aria-live', 'polite')
        expect(liveRegion).toHaveAttribute('aria-atomic', 'true')
      })
      
      it('should work with assistive technologies', () => {
        const LiveRegionTest = () => {
          const [message, setMessage] = React.useState('')
          
          return (
            <div>
              <Button onClick={() => setMessage('작업이 완료되었습니다')}>
                작업 실행
              </Button>
              <div aria-live="polite" aria-atomic="true" data-testid="live-region">
                {message}
              </div>
            </div>
          )
        }
        
        const user = userEvent.setup()
        render(<LiveRegionTest />)
        
        const button = screen.getByText('작업 실행')
        const liveRegion = screen.getByTestId('live-region')
        
        expect(liveRegion).toBeEmptyDOMElement()
        
        user.click(button)
        
        expect(liveRegion).toHaveTextContent('작업이 완료되었습니다')
        expect(liveRegion).toHaveAttribute('aria-live', 'polite')
      })
    })
  })

  describe('한국어 특화 접근성', () => {
    it('should handle Korean text input accessibility', async () => {
      const user = userEvent.setup()
      
      render(
        <div>
          <KoreanInput 
            label="한국어 이름" 
            description="한글로 이름을 입력하세요"
            placeholder="예: 홍길동"
          />
        </div>
      )
      
      const input = screen.getByRole('textbox')
      const label = screen.getByText('한국어 이름')
      const description = screen.getByText('한글로 이름을 입력하세요')
      
      expect(input).toHaveAccessibleName('한국어 이름')
      expect(input).toHaveAttribute('placeholder', '예: 홍길동')
      expect(label).toContainKoreanText()
      expect(description).toContainKoreanText()
      
      await user.type(input, '김철수')
      expect(input).toHaveValue('김철수')
    })
    
    it('should provide Korean language context', () => {
      render(
        <div lang="ko">
          <h1>GA4 관리자 자동화 시스템</h1>
          <p>
            Google Analytics 4 속성을 효율적으로 관리할 수 있는 
            통합 관리 시스템입니다.
          </p>
          <section lang="en">
            <h2>System Status</h2>
            <p>All systems operational</p>
          </section>
        </div>
      )
      
      const container = screen.getByText('GA4 관리자 자동화 시스템').parentElement
      const englishSection = screen.getByText('System Status').parentElement
      
      expect(container).toHaveAttribute('lang', 'ko')
      expect(englishSection).toHaveAttribute('lang', 'en')
    })
  })
})