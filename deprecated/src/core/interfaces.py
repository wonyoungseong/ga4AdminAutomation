#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 인터페이스 정의
====================

의존성 역전 원칙(DIP)을 적용하기 위한 추상 인터페이스들을 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

class IAnalyticsClient(ABC):
    """Google Analytics 클라이언트 인터페이스"""
    
    @abstractmethod
    def create_access_binding(self, request: Any) -> Any:
        """사용자 권한 바인딩 생성"""
        pass
    
    @abstractmethod
    def delete_access_binding(self, name: str) -> None:
        """사용자 권한 바인딩 삭제"""
        pass
    
    @abstractmethod
    def list_access_bindings(self, parent: str) -> List[Any]:
        """사용자 권한 바인딩 목록 조회"""
        pass

class IEmailSender(ABC):
    """이메일 발송 인터페이스"""
    
    @abstractmethod
    def send_email(self, to_email: str, subject: str, content: str) -> bool:
        """이메일 발송"""
        pass
    
    @abstractmethod
    def send_html_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """HTML 이메일 발송"""
        pass

class IEmailValidator(ABC):
    """이메일 검증 인터페이스"""
    
    @abstractmethod
    def validate_email_format(self, email: str) -> bool:
        """이메일 형식 검증"""
        pass
    
    @abstractmethod
    def check_google_account(self, email: str) -> bool:
        """Google 계정 존재 여부 확인"""
        pass

class IDatabase(ABC):
    """데이터베이스 인터페이스"""
    
    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()) -> Any:
        """쿼리 실행"""
        pass
    
    @abstractmethod
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """단일 레코드 조회"""
        pass
    
    @abstractmethod
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """다중 레코드 조회"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """연결 종료"""
        pass

class ILogger(ABC):
    """로거 인터페이스"""
    
    @abstractmethod
    def info(self, message: str) -> None:
        """정보 로그"""
        pass
    
    @abstractmethod
    def error(self, message: str) -> None:
        """에러 로그"""
        pass
    
    @abstractmethod
    def warning(self, message: str) -> None:
        """경고 로그"""
        pass
    
    @abstractmethod
    def debug(self, message: str) -> None:
        """디버그 로그"""
        pass

class IConfigManager(ABC):
    """설정 관리 인터페이스"""
    
    @abstractmethod
    def get_config(self, key: str) -> Any:
        """설정 값 조회"""
        pass
    
    @abstractmethod
    def get_account_id(self) -> str:
        """GA4 계정 ID 조회"""
        pass
    
    @abstractmethod
    def get_property_id(self) -> str:
        """GA4 속성 ID 조회"""
        pass 