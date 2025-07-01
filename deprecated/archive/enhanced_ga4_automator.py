#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced GA4 Automation System with Comprehensive Error Handling
================================================================

This module provides advanced GA4 user management with comprehensive error handling,
retry logic, and detailed failure scenario management.

Author: GA4 Automation Team
Date: 2025-01-21
"""

import json
import sqlite3
import time
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import re

from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.admin.types import (
    AccessBinding, CreateAccessBindingRequest, DeleteAccessBindingRequest,
    ListAccessBindingsRequest, Property
)
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import requests


class RegistrationFailureType(Enum):
    """사용자 등록 실패 유형"""
    EMAIL_ALREADY_EXISTS = "email_already_exists"
    INVALID_EMAIL = "invalid_email"
    USER_NOT_FOUND = "user_not_found"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    INVALID_CREDENTIALS = "invalid_credentials"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    QUOTA_EXCEEDED = "quota_exceeded"
    INTERNAL_ERROR = "internal_error"
    NETWORK_ERROR = "network_error"
    INVALID_PROPERTY_ID = "invalid_property_id"
    USER_DISABLED = "user_disabled"
    DOMAIN_NOT_ALLOWED = "domain_not_allowed"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RegistrationAttempt:
    """등록 시도 정보"""
    user_email: str
    property_id: str
    role: str
    attempt_time: datetime
    failure_type: Optional[RegistrationFailureType] = None
    error_message: str = ""
    retry_count: int = 0
    success: bool = False


@dataclass
class FailureNotificationConfig:
    """실패 알림 설정"""
    send_to_user: bool = True
    send_to_admin: bool = True
    include_retry_instructions: bool = True
    escalate_after_attempts: int = 3
class EnhancedGA4Automator:
    """고도화된 GA4 자동화 시스템"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Enhanced GA4 Automator 초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.client = self._initialize_ga4_client()
        self.db_name = "enhanced_ga4_management.db"
        self._setup_database()
        
        # 재시도 설정
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 5)  # 초
        self.exponential_backoff = self.config.get("exponential_backoff", True)
        
        # 이메일 도메인 화이트리스트
        self.allowed_domains = self.config.get("allowed_email_domains", [])
        
    def _load_config(self, config_path: str) -> Dict:
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger("EnhancedGA4Automator")
        logger.setLevel(logging.INFO)
        
        # 파일 핸들러
        file_handler = logging.FileHandler("enhanced_ga4_automation.log", encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포매터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger    
    def _initialize_ga4_client(self) -> AnalyticsAdminServiceClient:
        """GA4 클라이언트 초기화"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.config.get("service_account_key_path", "ga4-automatio-797ec352f393.json"),
                scopes=["https://www.googleapis.com/auth/analytics.edit"]
            )
            return AnalyticsAdminServiceClient(credentials=credentials)
        except Exception as e:
            self.logger.error(f"GA4 클라이언트 초기화 실패: {e}")
            raise
    
    def _setup_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # 사용자 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_ga4_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                property_id TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_date TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                failure_count INTEGER DEFAULT 0,
                last_failure_type TEXT,
                last_failure_message TEXT,
                UNIQUE(user_email, property_id)
            )
        ''')
        
        # 등록 시도 로그 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registration_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                property_id TEXT NOT NULL,
                role TEXT NOT NULL,
                attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT FALSE,
                failure_type TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                response_code INTEGER,
                response_details TEXT
            )
        ''')
        
        # 실패 알림 로그 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failure_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                failure_type TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_subject TEXT,
                message_body TEXT,
                recipient_type TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("데이터베이스 초기화 완료")    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """
        이메일 유효성 검증
        
        Args:
            email: 검증할 이메일
            
        Returns:
            (유효성, 오류메시지)
        """
        if not email:
            return False, "이메일이 비어있습니다"
        
        # 이메일 형식 검증
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "유효하지 않은 이메일 형식입니다"
        
        # 도메인 화이트리스트 검증
        if self.allowed_domains:
            domain = email.split('@')[1]
            if domain not in self.allowed_domains:
                return False, f"허용되지 않은 도메인입니다: {domain}"
        
        return True, ""
    
    def check_user_exists(self, property_id: str, user_email: str) -> bool:
        """
        사용자가 이미 존재하는지 확인
        
        Args:
            property_id: GA4 속성 ID
            user_email: 사용자 이메일
            
        Returns:
            사용자 존재 여부
        """
        try:
            parent = f"properties/{property_id}"
            request = ListAccessBindingsRequest(parent=parent)
            
            response = self.client.list_access_bindings(request=request)
            
            for binding in response:
                if binding.user == user_email:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"사용자 존재 확인 중 오류: {e}")
            return False    
    def determine_failure_type(self, error: Exception) -> RegistrationFailureType:
        """
        오류 유형 분석
        
        Args:
            error: 발생한 오류
            
        Returns:
            실패 유형
        """
        error_message = str(error).lower()
        
        if isinstance(error, HttpError):
            status_code = error.resp.status
            
            if status_code == 400:
                if "invalid email" in error_message or "invalid user" in error_message:
                    return RegistrationFailureType.INVALID_EMAIL
                elif "already exists" in error_message:
                    return RegistrationFailureType.EMAIL_ALREADY_EXISTS
                else:
                    return RegistrationFailureType.INVALID_CREDENTIALS
            
            elif status_code == 401:
                return RegistrationFailureType.INVALID_CREDENTIALS
            
            elif status_code == 403:
                if "insufficient" in error_message or "permission" in error_message:
                    return RegistrationFailureType.INSUFFICIENT_PERMISSIONS
                elif "rate limit" in error_message:
                    return RegistrationFailureType.RATE_LIMIT_EXCEEDED
                elif "quota" in error_message:
                    return RegistrationFailureType.QUOTA_EXCEEDED
                else:
                    return RegistrationFailureType.INSUFFICIENT_PERMISSIONS
            
            elif status_code == 404:
                if "user not found" in error_message:
                    return RegistrationFailureType.USER_NOT_FOUND
                elif "property" in error_message:
                    return RegistrationFailureType.INVALID_PROPERTY_ID
            
            elif status_code >= 500:
                return RegistrationFailureType.INTERNAL_ERROR
        
        # 네트워크 오류 확인
        if "network" in error_message or "connection" in error_message:
            return RegistrationFailureType.NETWORK_ERROR
        
        return RegistrationFailureType.UNKNOWN_ERROR    
    def register_user_with_retry(
        self, 
        property_id: str, 
        user_email: str, 
        role: str = "viewer"
    ) -> RegistrationAttempt:
        """
        재시도 로직이 포함된 사용자 등록
        
        Args:
            property_id: GA4 속성 ID
            user_email: 사용자 이메일
            role: 사용자 역할
            
        Returns:
            등록 시도 결과
        """
        attempt = RegistrationAttempt(
            user_email=user_email,
            property_id=property_id,
            role=role,
            attempt_time=datetime.now()
        )
        
        # 이메일 유효성 검증
        is_valid, validation_error = self.validate_email(user_email)
        if not is_valid:
            attempt.failure_type = RegistrationFailureType.INVALID_EMAIL
            attempt.error_message = validation_error
            self._log_registration_attempt(attempt)
            return attempt
        
        # 중복 사용자 확인
        if self.check_user_exists(property_id, user_email):
            attempt.failure_type = RegistrationFailureType.EMAIL_ALREADY_EXISTS
            attempt.error_message = f"사용자가 이미 존재합니다: {user_email}"
            self._log_registration_attempt(attempt)
            return attempt
        
        # 재시도 로직
        for retry_count in range(self.max_retries + 1):
            attempt.retry_count = retry_count
            
            try:
                success = self._attempt_user_registration(property_id, user_email, role)
                
                if success:
                    attempt.success = True
                    self.logger.info(f"사용자 등록 성공: {user_email} (시도 {retry_count + 1}회)")
                    break
                
            except Exception as e:
                failure_type = self.determine_failure_type(e)
                attempt.failure_type = failure_type
                attempt.error_message = str(e)
                
                self.logger.warning(
                    f"사용자 등록 실패 (시도 {retry_count + 1}/{self.max_retries + 1}): "
                    f"{user_email} - {failure_type.value}: {e}"
                )
                
                # 재시도 불가능한 오류들
                non_retryable_errors = {
                    RegistrationFailureType.INVALID_EMAIL,
                    RegistrationFailureType.EMAIL_ALREADY_EXISTS,
                    RegistrationFailureType.INVALID_CREDENTIALS,
                    RegistrationFailureType.INSUFFICIENT_PERMISSIONS,
                    RegistrationFailureType.USER_DISABLED,
                    RegistrationFailureType.DOMAIN_NOT_ALLOWED,
                    RegistrationFailureType.INVALID_PROPERTY_ID
                }
                
                if failure_type in non_retryable_errors:
                    self.logger.error(f"재시도 불가능한 오류: {failure_type.value}")
                    break
                
                # 마지막 시도가 아니면 대기 후 재시도
                if retry_count < self.max_retries:
                    delay = self._calculate_retry_delay(retry_count)
                    self.logger.info(f"{delay}초 후 재시도...")
                    time.sleep(delay)
        
        # 등록 시도 로그 저장
        self._log_registration_attempt(attempt)
        
        # 사용자 정보 업데이트
        self._update_user_status(attempt)
        
        return attempt    
    def _attempt_user_registration(self, property_id: str, user_email: str, role: str) -> bool:
        """
        실제 사용자 등록 시도
        
        Args:
            property_id: GA4 속성 ID
            user_email: 사용자 이메일
            role: 사용자 역할
            
        Returns:
            등록 성공 여부
        """
        try:
            parent = f"properties/{property_id}"
            
            # 역할 매핑
            role_mapping = {
                "viewer": "predefinedRoles/viewer",
                "analyst": "predefinedRoles/analyst", 
                "editor": "predefinedRoles/editor",
                "admin": "predefinedRoles/admin"
            }
            
            access_binding = AccessBinding(
                user=user_email,
                roles=[role_mapping.get(role, "predefinedRoles/viewer")]
            )
            
            request = CreateAccessBindingRequest(
                parent=parent,
                access_binding=access_binding
            )
            
            response = self.client.create_access_binding(request=request)
            
            if response:
                self.logger.info(f"GA4 사용자 등록 성공: {user_email}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"GA4 사용자 등록 실패: {e}")
            raise
    
    def _calculate_retry_delay(self, retry_count: int) -> int:
        """
        재시도 지연 시간 계산
        
        Args:
            retry_count: 현재 재시도 횟수
            
        Returns:
            지연 시간 (초)
        """
        if self.exponential_backoff:
            return min(self.retry_delay * (2 ** retry_count), 60)  # 최대 60초
        else:
            return self.retry_delay    
    def _log_registration_attempt(self, attempt: RegistrationAttempt):
        """등록 시도 로그 저장"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO registration_attempts 
                (user_email, property_id, role, attempt_time, success, failure_type, 
                 error_message, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                attempt.user_email,
                attempt.property_id,
                attempt.role,
                attempt.attempt_time,
                attempt.success,
                attempt.failure_type.value if attempt.failure_type else None,
                attempt.error_message,
                attempt.retry_count
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"등록 시도 로그 저장 실패: {e}")
    
    def _update_user_status(self, attempt: RegistrationAttempt):
        """사용자 상태 업데이트"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            if attempt.success:
                # 성공 시 사용자 추가/업데이트
                expiry_date = datetime.now() + timedelta(days=30)  # 30일 후 만료
                
                cursor.execute('''
                    INSERT OR REPLACE INTO enhanced_ga4_users 
                    (user_email, property_id, role, status, expiry_date, last_updated, failure_count)
                    VALUES (?, ?, ?, 'active', ?, ?, 0)
                ''', (
                    attempt.user_email,
                    attempt.property_id,
                    attempt.role,
                    expiry_date,
                    datetime.now()
                ))
            else:
                # 실패 시 실패 정보 업데이트
                cursor.execute('''
                    INSERT OR REPLACE INTO enhanced_ga4_users 
                    (user_email, property_id, role, status, last_updated, failure_count,
                     last_failure_type, last_failure_message)
                    VALUES (?, ?, ?, 'failed', ?, 
                            COALESCE((SELECT failure_count FROM enhanced_ga4_users 
                                     WHERE user_email = ? AND property_id = ?), 0) + 1,
                            ?, ?)
                ''', (
                    attempt.user_email,
                    attempt.property_id,
                    attempt.role,
                    datetime.now(),
                    attempt.user_email,
                    attempt.property_id,
                    attempt.failure_type.value if attempt.failure_type else None,
                    attempt.error_message
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"사용자 상태 업데이트 실패: {e}")