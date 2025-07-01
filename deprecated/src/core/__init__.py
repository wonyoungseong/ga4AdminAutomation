"""
Core Module
===========

시스템의 핵심 기능과 유틸리티를 제공하는 모듈입니다.

주요 클래스:
- SmartEmailValidationSystem: 이메일 검증 시스템
- GA4AutomationSystem: GA4 자동화 시스템  
- GmailOAuthSender: Gmail 발송 서비스
"""

from .email_validator import SmartEmailValidationSystem
from .gmail_service import GmailOAuthSender

__all__ = [
    'SmartEmailValidationSystem',
    'GmailOAuthSender'
] 