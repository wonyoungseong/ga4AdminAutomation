#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Validator Service
======================

이메일 주소 검증 및 도메인 관리 서비스
"""

import re
from typing import List, Set
from dataclasses import dataclass


@dataclass
class EmailValidationResult:
    """이메일 검증 결과"""
    is_valid: bool
    email: str
    domain: str
    is_company_email: bool
    error_message: str = ""


class EmailValidator:
    """이메일 검증 서비스"""
    
    # 허용된 도메인 목록
    ALLOWED_DOMAINS = {
        'gmail.com',
        'conentrix.com',
        'amorepacific.com'
    }
    
    # 회사 도메인 목록
    COMPANY_DOMAINS = {
        'conentrix.com',
        'amorepacific.com'
    }
    
    # 이메일 정규식 패턴
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def __init__(self):
        """초기화"""
        pass
    
    def validate_email(self, email: str) -> EmailValidationResult:
        """
        이메일 주소 검증
        
        Args:
            email: 검증할 이메일 주소
            
        Returns:
            EmailValidationResult: 검증 결과
        """
        email = email.strip().lower()
        
        # 기본 형식 검증
        if not self.EMAIL_PATTERN.match(email):
            return EmailValidationResult(
                is_valid=False,
                email=email,
                domain="",
                is_company_email=False,
                error_message="이메일 형식이 올바르지 않습니다."
            )
        
        # 도메인 추출
        domain = email.split('@')[1]
        
        # 허용된 도메인 검증
        if domain not in self.ALLOWED_DOMAINS:
            return EmailValidationResult(
                is_valid=False,
                email=email,
                domain=domain,
                is_company_email=False,
                error_message=f"허용되지 않은 도메인입니다. 허용된 도메인: {', '.join(self.ALLOWED_DOMAINS)}"
            )
        
        # 회사 이메일 여부 확인
        is_company_email = domain in self.COMPANY_DOMAINS
        
        return EmailValidationResult(
            is_valid=True,
            email=email,
            domain=domain,
            is_company_email=is_company_email
        )
    
    def validate_multiple_emails(self, emails: List[str]) -> List[EmailValidationResult]:
        """
        여러 이메일 주소 검증
        
        Args:
            emails: 검증할 이메일 주소 목록
            
        Returns:
            List[EmailValidationResult]: 검증 결과 목록
        """
        return [self.validate_email(email) for email in emails]
    
    def get_valid_emails(self, emails: List[str]) -> List[str]:
        """
        유효한 이메일 주소만 반환
        
        Args:
            emails: 검증할 이메일 주소 목록
            
        Returns:
            List[str]: 유효한 이메일 주소 목록
        """
        results = self.validate_multiple_emails(emails)
        return [result.email for result in results if result.is_valid]
    
    def get_invalid_emails(self, emails: List[str]) -> List[EmailValidationResult]:
        """
        유효하지 않은 이메일 주소와 오류 메시지 반환
        
        Args:
            emails: 검증할 이메일 주소 목록
            
        Returns:
            List[EmailValidationResult]: 유효하지 않은 이메일 검증 결과
        """
        results = self.validate_multiple_emails(emails)
        return [result for result in results if not result.is_valid]
    
    def is_company_email(self, email: str) -> bool:
        """
        회사 이메일인지 확인
        
        Args:
            email: 확인할 이메일 주소
            
        Returns:
            bool: 회사 이메일 여부
        """
        result = self.validate_email(email)
        return result.is_valid and result.is_company_email
    
    def add_allowed_domain(self, domain: str) -> None:
        """
        허용된 도메인 추가
        
        Args:
            domain: 추가할 도메인
        """
        self.ALLOWED_DOMAINS.add(domain.lower())
    
    def remove_allowed_domain(self, domain: str) -> None:
        """
        허용된 도메인 제거
        
        Args:
            domain: 제거할 도메인
        """
        self.ALLOWED_DOMAINS.discard(domain.lower())
    
    def add_company_domain(self, domain: str) -> None:
        """
        회사 도메인 추가
        
        Args:
            domain: 추가할 회사 도메인
        """
        domain = domain.lower()
        self.COMPANY_DOMAINS.add(domain)
        self.ALLOWED_DOMAINS.add(domain)  # 회사 도메인은 자동으로 허용 도메인에도 추가
    
    def remove_company_domain(self, domain: str) -> None:
        """
        회사 도메인 제거
        
        Args:
            domain: 제거할 회사 도메인
        """
        self.COMPANY_DOMAINS.discard(domain.lower())
    
    @property
    def allowed_domains(self) -> Set[str]:
        """허용된 도메인 목록 반환"""
        return self.ALLOWED_DOMAINS.copy()
    
    @property
    def company_domains(self) -> Set[str]:
        """회사 도메인 목록 반환"""
        return self.COMPANY_DOMAINS.copy()


# 전역 인스턴스
email_validator = EmailValidator() 