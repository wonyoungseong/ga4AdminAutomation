import React, { act } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  KoreanFormField,
  KoreanInput,
  KoreanTextarea,
  koreanValidation,
  validateKoreanField,
  useKoreanForm
} from '../korean-form'
import { koreanTextUtils } from '@/test/test-utils'

describe('KoreanFormField', () => {
  it('should render label and children', () => {
    render(
      <KoreanFormField label="테스트 필드">
        <input data-testid="test-input" />
      </KoreanFormField>
    )
    
    expect(screen.getByText('테스트 필드')).toBeInTheDocument()
    expect(screen.getByTestId('test-input')).toBeInTheDocument()
  })
  
  it('should show required indicator', () => {
    render(
      <KoreanFormField label="필수 필드" required>
        <input />
      </KoreanFormField>
    )
    
    expect(screen.getByText('*')).toBeInTheDocument()
    expect(screen.getByText('*')).toHaveClass('text-destructive')
  })
  
  it('should display description', () => {
    render(
      <KoreanFormField label="테스트 필드" description="도움말 텍스트">
        <input />
      </KoreanFormField>
    )
    
    expect(screen.getByText('도움말 텍스트')).toBeInTheDocument()
    expect(screen.getByText('도움말 텍스트')).toHaveClass('korean-text')
  })
  
  it('should display error message', () => {
    render(
      <KoreanFormField label="테스트 필드" error="오류 메시지">
        <input />
      </KoreanFormField>
    )
    
    const errorElement = screen.getByText('오류 메시지')
    expect(errorElement).toBeInTheDocument()
    expect(errorElement).toHaveClass('text-destructive', 'korean-text')
    expect(errorElement).toHaveAttribute('role', 'alert')
  })
  
  it('should have korean-text class on label', () => {
    render(
      <KoreanFormField label="한글 레이블">
        <input />
      </KoreanFormField>
    )
    
    const label = screen.getByText('한글 레이블')
    expect(label).toHaveClass('korean-text')
  })
  
  it('should contain Korean text', () => {
    render(
      <KoreanFormField label="사용자 이름" description="한글로 입력하세요" error="잘못된 형식입니다">
        <input />
      </KoreanFormField>
    )
    
    expect(screen.getByText('사용자 이름')).toContainKoreanText()
    expect(screen.getByText('한글로 입력하세요')).toContainKoreanText()
    expect(screen.getByText('잘못된 형식입니다')).toContainKoreanText()
  })
})

describe('KoreanInput', () => {
  it('should render input with Korean label', () => {
    render(<KoreanInput label="이름" placeholder="이름을 입력하세요" />)
    
    expect(screen.getByText('이름')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('이름을 입력하세요')).toBeInTheDocument()
  })
  
  it('should handle user input', async () => {
    const user = userEvent.setup()
    
    render(<KoreanInput label="이름" />)
    
    const input = screen.getByRole('textbox')
    await act(async () => {
      await user.type(input, '홍길동')
    })
    
    expect(input).toHaveValue('홍길동')
  })
  
  it('should show error styling', () => {
    render(<KoreanInput label="이름" error="필수 입력 항목입니다" />)
    
    const input = screen.getByRole('textbox')
    expect(input).toHaveClass('border-destructive', 'focus-visible:ring-destructive')
  })
  
  it('should have korean-text class', () => {
    render(<KoreanInput label="이름" />)
    
    const input = screen.getByRole('textbox')
    expect(input).toHaveClass('korean-text')
  })
  
  it('should support required attribute', () => {
    render(<KoreanInput label="이름" required />)
    
    const input = screen.getByRole('textbox')
    expect(input).toBeRequired()
    expect(screen.getByText('*')).toBeInTheDocument()
  })
  
  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLInputElement>()
    
    render(<KoreanInput ref={ref} label="이름" />)
    
    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })
})

describe('KoreanTextarea', () => {
  it('should render textarea with Korean label', () => {
    render(<KoreanTextarea label="설명" placeholder="내용을 입력하세요" />)
    
    expect(screen.getByText('설명')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('내용을 입력하세요')).toBeInTheDocument()
  })
  
  it('should handle user input', async () => {
    const user = userEvent.setup()
    
    render(<KoreanTextarea label="설명" />)
    
    const textarea = screen.getByRole('textbox')
    await act(async () => {
      await user.type(textarea, '한글 입력 테스트')
    })
    
    expect(textarea).toHaveValue('한글 입력 테스트')
  })
  
  it('should have minimum height and resize styling', () => {
    render(<KoreanTextarea label="설명" />)
    
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveClass('min-h-[80px]', 'resize-y', 'korean-text')
  })
  
  it('should show error styling', () => {
    render(<KoreanTextarea label="설명" error="내용이 너무 짧습니다" />)
    
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveClass('border-destructive', 'focus-visible:ring-destructive')
  })
  
  it('should forward ref correctly', () => {
    const ref = React.createRef<HTMLTextAreaElement>()
    
    render(<KoreanTextarea ref={ref} label="설명" />)
    
    expect(ref.current).toBeInstanceOf(HTMLTextAreaElement)
  })
})

describe('koreanValidation', () => {
  it('should have all validation patterns', () => {
    expect(koreanValidation).toHaveProperty('name')
    expect(koreanValidation).toHaveProperty('company')
    expect(koreanValidation).toHaveProperty('phone')
    expect(koreanValidation).toHaveProperty('email')
    expect(koreanValidation).toHaveProperty('businessNumber')
    expect(koreanValidation).toHaveProperty('postalCode')
  })
  
  it('should validate Korean names correctly', () => {
    const namePattern = koreanValidation.name.pattern
    
    // Valid names
    expect(namePattern.test('홍길동')).toBe(true)
    expect(namePattern.test('John Doe')).toBe(true)
    expect(namePattern.test('김 영희')).toBe(true)
    expect(namePattern.test('이-순신')).toBe(true)
    expect(namePattern.test('박.철수')).toBe(true)
    
    // Invalid names
    expect(namePattern.test('홍길동123')).toBe(false)
    expect(namePattern.test('홍길동!@#')).toBe(false)
    expect(namePattern.test('123홍길동')).toBe(false)
  })
  
  it('should validate phone numbers correctly', () => {
    const phonePattern = koreanValidation.phone.pattern
    
    // Valid phone numbers
    expect(phonePattern.test('010-1234-5678')).toBe(true)
    expect(phonePattern.test('01012345678')).toBe(true)
    expect(phonePattern.test('011-123-4567')).toBe(true)
    expect(phonePattern.test('016-1234-5678')).toBe(true)
    
    // Invalid phone numbers
    expect(phonePattern.test('010-12-34')).toBe(false)
    expect(phonePattern.test('123-456-7890')).toBe(false)
    expect(phonePattern.test('010-12345')).toBe(false)
  })
  
  it('should validate business numbers correctly', () => {
    const businessPattern = koreanValidation.businessNumber.pattern
    
    // Valid business numbers
    expect(businessPattern.test('123-45-67890')).toBe(true)
    expect(businessPattern.test('1234567890')).toBe(true)
    
    // Invalid business numbers
    expect(businessPattern.test('123-4-5678')).toBe(false)
    expect(businessPattern.test('12-345-6789')).toBe(false)
    expect(businessPattern.test('123456789')).toBe(false)
  })
  
  it('should have Korean error messages', () => {
    expect(koreanValidation.name.message).toContainKoreanText()
    expect(koreanValidation.phone.message).toContainKoreanText()
    expect(koreanValidation.email.message).toContainKoreanText()
    expect(koreanValidation.businessNumber.message).toContainKoreanText()
  })
})

describe('validateKoreanField', () => {
  it('should return null for valid values', () => {
    expect(validateKoreanField('홍길동', 'name')).toBeNull()
    expect(validateKoreanField('010-1234-5678', 'phone')).toBeNull()
    expect(validateKoreanField('test@example.com', 'email')).toBeNull()
  })
  
  it('should return error message for invalid values', () => {
    expect(validateKoreanField('홍길동123', 'name')).toBe(koreanValidation.name.message)
    expect(validateKoreanField('010-12-34', 'phone')).toBe(koreanValidation.phone.message)
    expect(validateKoreanField('invalid-email', 'email')).toBe(koreanValidation.email.message)
  })
  
  it('should handle required field validation', () => {
    expect(validateKoreanField('', 'name', true)).toBe('필수 입력 항목입니다.')
    expect(validateKoreanField('   ', 'name', true)).toBe('필수 입력 항목입니다.')
    expect(validateKoreanField('', 'name', false)).toBeNull()
  })
  
  it('should validate with Korean test data', () => {
    koreanTextUtils.validationCases.name.forEach(testCase => {
      const result = validateKoreanField(testCase.input, 'name')
      if (testCase.valid) {
        expect(result).toBeNull()
      } else {
        expect(result).not.toBeNull()
      }
    })
    
    koreanTextUtils.validationCases.phone.forEach(testCase => {
      const result = validateKoreanField(testCase.input, 'phone')
      if (testCase.valid) {
        expect(result).toBeNull()
      } else {
        expect(result).not.toBeNull()
      }
    })
  })
})

describe('useKoreanForm', () => {
  const TestFormComponent: React.FC = () => {
    const { errors, validate, clearError, clearAllErrors, hasErrors } = useKoreanForm()
    
    const handleValidate = () => {
      validate('name', '홍길동123', 'name', true)
      validate('phone', '010-1234-5678', 'phone', false)
    }
    
    const handleClearNameError = () => clearError('name')
    const handleClearAllErrors = () => clearAllErrors()
    
    return (
      <div>
        <div data-testid="has-errors">{hasErrors ? 'has-errors' : 'no-errors'}</div>
        <div data-testid="name-error">{errors.name || 'no-error'}</div>
        <div data-testid="phone-error">{errors.phone || 'no-error'}</div>
        <button onClick={handleValidate} data-testid="validate-button">
          유효성 검사
        </button>
        <button onClick={handleClearNameError} data-testid="clear-name-button">
          이름 오류 제거
        </button>
        <button onClick={handleClearAllErrors} data-testid="clear-all-button">
          모든 오류 제거
        </button>
      </div>
    )
  }
  
  it('should initialize with no errors', () => {
    render(<TestFormComponent />)
    
    expect(screen.getByTestId('has-errors')).toHaveTextContent('no-errors')
    expect(screen.getByTestId('name-error')).toHaveTextContent('no-error')
    expect(screen.getByTestId('phone-error')).toHaveTextContent('no-error')
  })
  
  it('should validate fields and set errors', async () => {
    const user = userEvent.setup()
    
    render(<TestFormComponent />)
    
    await act(async () => {
      await user.click(screen.getByTestId('validate-button'))
    })
    
    await waitFor(() => {
      expect(screen.getByTestId('has-errors')).toHaveTextContent('has-errors')
      expect(screen.getByTestId('name-error')).toHaveTextContent(koreanValidation.name.message)
      expect(screen.getByTestId('phone-error')).toHaveTextContent('no-error')
    })
  })
  
  it('should clear individual field errors', async () => {
    const user = userEvent.setup()
    
    render(<TestFormComponent />)
    
    // First add errors
    await act(async () => {
      await user.click(screen.getByTestId('validate-button'))
    })
    
    await waitFor(() => {
      expect(screen.getByTestId('name-error')).not.toHaveTextContent('no-error')
    })
    
    // Clear name error
    await act(async () => {
      await user.click(screen.getByTestId('clear-name-button'))
    })
    
    await waitFor(() => {
      expect(screen.getByTestId('name-error')).toHaveTextContent('no-error')
      expect(screen.getByTestId('has-errors')).toHaveTextContent('no-errors')
    })
  })
  
  it('should clear all errors', async () => {
    const user = userEvent.setup()
    
    render(<TestFormComponent />)
    
    // First add errors
    await act(async () => {
      await user.click(screen.getByTestId('validate-button'))
    })
    
    await waitFor(() => {
      expect(screen.getByTestId('has-errors')).toHaveTextContent('has-errors')
    })
    
    // Clear all errors
    await act(async () => {
      await user.click(screen.getByTestId('clear-all-button'))
    })
    
    await waitFor(() => {
      expect(screen.getByTestId('has-errors')).toHaveTextContent('no-errors')
      expect(screen.getByTestId('name-error')).toHaveTextContent('no-error')
      expect(screen.getByTestId('phone-error')).toHaveTextContent('no-error')
    })
  })
  
  it('should return validation result', async () => {
    const TestValidationResult: React.FC = () => {
      const { validate } = useKoreanForm()
      const [result, setResult] = React.useState<boolean | null>(null)
      
      const handleValidate = () => {
        const isValid = validate('name', '홍길동', 'name', true)
        setResult(isValid)
      }
      
      return (
        <div>
          <div data-testid="validation-result">{result === null ? 'not-tested' : result ? 'valid' : 'invalid'}</div>
          <button onClick={handleValidate} data-testid="validate-button">검증</button>
        </div>
      )
    }
    
    const user = userEvent.setup()
    render(<TestValidationResult />)
    
    expect(screen.getByTestId('validation-result')).toHaveTextContent('not-tested')
    
    await act(async () => {
      await user.click(screen.getByTestId('validate-button'))
    })
    
    await waitFor(() => {
      expect(screen.getByTestId('validation-result')).toHaveTextContent('valid')
    })
  })
})

describe('Integration Tests', () => {
  it('should work together in a complete form', async () => {
    const TestForm: React.FC = () => {
      const { errors, validate, hasErrors } = useKoreanForm()
      const [values, setValues] = React.useState({ name: '', phone: '' })
      
      const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        
        const nameValid = validate('name', values.name, 'name', true)
        const phoneValid = validate('phone', values.phone, 'phone', false)
        
        if (nameValid && phoneValid) {
          // Form is valid
        }
      }
      
      return (
        <form onSubmit={handleSubmit}>
          <KoreanInput
            label="이름"
            value={values.name}
            onChange={(e) => setValues(prev => ({ ...prev, name: e.target.value }))}
            error={errors.name}
            required
          />
          <KoreanInput
            label="전화번호"
            value={values.phone}
            onChange={(e) => setValues(prev => ({ ...prev, phone: e.target.value }))}
            error={errors.phone}
            placeholder="010-1234-5678"
          />
          <div data-testid="form-status">{hasErrors ? 'has-errors' : 'no-errors'}</div>
          <button type="submit" data-testid="submit-button">제출</button>
        </form>
      )
    }
    
    const user = userEvent.setup()
    render(<TestForm />)
    
    // Initially no errors
    expect(screen.getByTestId('form-status')).toHaveTextContent('no-errors')
    
    // Submit empty form
    await act(async () => {
      await user.click(screen.getByTestId('submit-button'))
    })
    
    await waitFor(() => {
      expect(screen.getByTestId('form-status')).toHaveTextContent('has-errors')
      expect(screen.getByText('필수 입력 항목입니다.')).toBeInTheDocument()
    })
    
    // Fill in valid data
    const nameInput = screen.getByLabelText('이름 *')
    const phoneInput = screen.getByLabelText('전화번호')
    
    await act(async () => {
      await user.type(nameInput, '홍길동')
      await user.type(phoneInput, '010-1234-5678')
    })
    
    // Submit valid form
    await act(async () => {
      await user.click(screen.getByTestId('submit-button'))
    })
    
    await waitFor(() => {
      expect(screen.getByTestId('form-status')).toHaveTextContent('no-errors')
    })
  })
  
  it('should have proper accessibility attributes', () => {
    render(
      <KoreanInput
        label="사용자 이름"
        error="오류가 발생했습니다"
        description="한글 또는 영문을 입력하세요"
        required
      />
    )
    
    const input = screen.getByRole('textbox')
    const label = screen.getByText('사용자 이름')
    const error = screen.getByText('오류가 발생했습니다')
    
    expect(input).toBeRequired()
    expect(error).toHaveAttribute('role', 'alert')
    expect(label).toHaveAccessibleName('사용자 이름')
  })
})