#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로깅 시스템

GA4 권한 관리 시스템의 로깅 설정을 제공합니다.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

class GA4Logger:
    """GA4 시스템 전용 로거"""
    
    def __init__(self, name: str = "GA4PermissionManager"):
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(self.name)
        
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.INFO)
        
        # 로그 디렉토리 생성
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 포맷터 생성
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 파일 핸들러 (일반 로그)
        today = datetime.now().strftime('%Y%m%d')
        file_handler = logging.FileHandler(
            log_dir / f"ga4_permission_manager_{today}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 에러 파일 핸들러
        error_handler = logging.FileHandler(
            log_dir / f"ga4_permission_manager_error_{today}.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        return logger
    
    def info(self, message: str) -> None:
        """정보 로그"""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """경고 로그"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """에러 로그"""
        self.logger.error(message)
    
    def debug(self, message: str) -> None:
        """디버그 로그"""
        self.logger.debug(message)
    
    def critical(self, message: str) -> None:
        """치명적 에러 로그"""
        self.logger.critical(message)


# 전역 로거 인스턴스
_ga4_logger: Optional[GA4Logger] = None


def get_ga4_logger() -> GA4Logger:
    """GA4 로거 인스턴스 반환"""
    global _ga4_logger
    
    if _ga4_logger is None:
        _ga4_logger = GA4Logger()
    
    return _ga4_logger


def setup_logging(log_level: str = "INFO") -> None:
    """로깅 레벨 설정"""
    logger = get_ga4_logger()
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.logger.setLevel(level)
    
    for handler in logger.logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(level)


# 특수 목적 로거들
def get_email_logger() -> logging.Logger:
    """이메일 관련 로거"""
    return logging.getLogger("EMAIL_SYSTEM")

def get_gmail_logger() -> logging.Logger:
    """Gmail 관련 로거"""
    return logging.getLogger("GMAIL_SERVICE") 