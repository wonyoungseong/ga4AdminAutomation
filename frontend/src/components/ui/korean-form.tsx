"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Label } from "./label";
import { Input } from "./input";
import { Textarea } from "./textarea";

interface KoreanFormFieldProps {
  label: string;
  required?: boolean;
  error?: string;
  description?: string;
  className?: string;
  children: React.ReactNode;
}

const KoreanFormField = React.forwardRef<HTMLDivElement, KoreanFormFieldProps>(
  ({ label, required = false, error, description, className, children }, ref) => {
    return (
      <div ref={ref} className={cn("space-y-2", className)}>
        <Label className="korean-text flex items-center gap-1">
          {label}
          {required && <span className="text-destructive">*</span>}
        </Label>
        {children}
        {description && (
          <p className="text-sm text-muted-foreground korean-text">
            {description}
          </p>
        )}
        {error && (
          <p className="text-sm text-destructive korean-text" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);
KoreanFormField.displayName = "KoreanFormField";

interface KoreanInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  description?: string;
}

const KoreanInput = React.forwardRef<HTMLInputElement, KoreanInputProps>(
  ({ label, error, description, className, required, ...props }, ref) => {
    return (
      <KoreanFormField
        label={label}
        required={required}
        error={error}
        description={description}
      >
        <Input
          ref={ref}
          className={cn(
            "korean-text",
            error && "border-destructive focus-visible:ring-destructive",
            className
          )}
          required={required}
          {...props}
        />
      </KoreanFormField>
    );
  }
);
KoreanInput.displayName = "KoreanInput";

interface KoreanTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  description?: string;
}

const KoreanTextarea = React.forwardRef<HTMLTextAreaElement, KoreanTextareaProps>(
  ({ label, error, description, className, required, ...props }, ref) => {
    return (
      <KoreanFormField
        label={label}
        required={required}
        error={error}
        description={description}
      >
        <Textarea
          ref={ref}
          className={cn(
            "korean-text min-h-[80px] resize-y",
            error && "border-destructive focus-visible:ring-destructive",
            className
          )}
          required={required}
          {...props}
        />
      </KoreanFormField>
    );
  }
);
KoreanTextarea.displayName = "KoreanTextarea";

// Korean-specific validation patterns
export const koreanValidation = {
  // Korean name validation (allows Korean characters, English letters, and common punctuation)
  name: {
    pattern: /^[가-힣a-zA-Z\s\-\.]+$/,
    message: "한글, 영문, 공백, 하이픈(-), 점(.)만 입력 가능합니다."
  },
  
  // Korean company name validation
  company: {
    pattern: /^[가-힣a-zA-Z0-9\s\-\(\)\[\]\.]+$/,
    message: "한글, 영문, 숫자, 공백, 특수문자(-,(),[],.)만 입력 가능합니다."
  },
  
  // Korean phone number validation
  phone: {
    pattern: /^(010|011|016|017|018|019)-?\d{3,4}-?\d{4}$/,
    message: "올바른 휴대폰 번호를 입력해주세요. (예: 010-1234-5678)"
  },
  
  // Korean email validation with Korean domain support
  email: {
    pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    message: "올바른 이메일 주소를 입력해주세요."
  },
  
  // Business registration number (사업자등록번호)
  businessNumber: {
    pattern: /^\d{3}-?\d{2}-?\d{5}$/,
    message: "올바른 사업자등록번호를 입력해주세요. (예: 123-45-67890)"
  },
  
  // Korean postal code
  postalCode: {
    pattern: /^\d{5}$/,
    message: "올바른 우편번호를 입력해주세요. (5자리 숫자)"
  }
};

// Utility function for Korean text validation
export function validateKoreanField(
  value: string,
  type: keyof typeof koreanValidation,
  required: boolean = false
): string | null {
  if (required && !value.trim()) {
    return "필수 입력 항목입니다.";
  }
  
  if (value && !koreanValidation[type].pattern.test(value)) {
    return koreanValidation[type].message;
  }
  
  return null;
}

// Hook for Korean form validation
export function useKoreanForm() {
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  
  const validate = React.useCallback((
    fieldName: string,
    value: string,
    type: keyof typeof koreanValidation,
    required: boolean = false
  ) => {
    const error = validateKoreanField(value, type, required);
    
    setErrors(prev => ({
      ...prev,
      [fieldName]: error || ""
    }));
    
    return !error;
  }, []);
  
  const clearError = React.useCallback((fieldName: string) => {
    setErrors(prev => ({
      ...prev,
      [fieldName]: ""
    }));
  }, []);
  
  const clearAllErrors = React.useCallback(() => {
    setErrors({});
  }, []);
  
  const hasErrors = React.useMemo(() => {
    return Object.values(errors).some(error => error);
  }, [errors]);
  
  return {
    errors,
    validate,
    clearError,
    clearAllErrors,
    hasErrors
  };
}

export { KoreanFormField, KoreanInput, KoreanTextarea };