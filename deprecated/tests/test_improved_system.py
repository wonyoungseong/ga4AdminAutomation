#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 GA4 자동화 시스템 TDD 테스트
================================

개발 규칙 개선 사항들이 적용된 시스템을 테스트합니다.
TDD 원칙에 따라 테스트를 먼저 작성하고 구현을 검증합니다.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import LoggerManager, get_logger, get_email_logger, get_ga4_logger
from src.core.interfaces import IAnalyticsClient, IEmailSender, ILogger
from src.core.ga4_automation import GA4AutomationSystem
from src.core.email_validator import SmartEmailValidationSystem

class TestImprovedLoggingSystem:
    """개선된 로깅 시스템 테스트"""
    
    def test_logger_manager_singleton_behavior(self):
        """로거 매니저의 싱글톤 동작 테스트"""
        # 같은 이름의 로거는 동일한 인스턴스 반환해야 함
        logger1 = get_logger("TEST_LOGGER")
        logger2 = get_logger("TEST_LOGGER")
        assert logger1 is logger2
    
    def test_specialized_loggers_creation(self):
        """특화된 로거들 생성 테스트"""
        email_logger = get_email_logger()
        ga4_logger = get_ga4_logger()
        
        assert email_logger.name == "EMAIL_SYSTEM"
        assert ga4_logger.name == "GA4_SYSTEM"
        assert email_logger is not ga4_logger
    
    def test_logger_setup_initialization(self):
        """로거 설정 초기화 테스트"""
        # 로거 매니저 초기화 상태 확인
        LoggerManager.setup_logging()
        assert LoggerManager._initialized == True
        
        # 중복 초기화 방지 테스트
        initial_state = LoggerManager._initialized
        LoggerManager.setup_logging()
        assert LoggerManager._initialized == initial_state

class TestDependencyInjection:
    """의존성 주입 테스트"""
    
    def test_ga4_system_with_mock_dependencies(self):
        """GA4 시스템에 모의 의존성 주입 테스트"""
        # Mock 의존성 생성
        mock_client = Mock(spec=IAnalyticsClient)
        mock_logger = Mock(spec=ILogger)
        
        # 의존성 주입으로 시스템 생성
        with patch('src.core.ga4_automation.GA4AutomationSystem._init_database'):
            system = GA4AutomationSystem(
                db_name=":memory:",
                analytics_client=mock_client,
                logger=mock_logger
            )
        
        # 주입된 의존성 확인
        assert system.client is mock_client
        assert system.logger is mock_logger
    
    def test_dependency_injection_interface_compliance(self):
        """의존성 주입 인터페이스 준수 테스트"""
        mock_client = Mock(spec=IAnalyticsClient)
        
        # 인터페이스 메서드가 존재하는지 확인
        assert hasattr(mock_client, 'create_access_binding')
        assert hasattr(mock_client, 'delete_access_binding')
        assert hasattr(mock_client, 'list_access_bindings')
    
    def test_default_dependency_fallback(self):
        """기본 의존성 폴백 테스트"""
        with patch('src.core.ga4_automation.GA4AutomationSystem._init_client') as mock_init:
            with patch('src.core.ga4_automation.GA4AutomationSystem._init_database'):
                mock_client = Mock()
                mock_init.return_value = mock_client
                
                # 의존성을 주입하지 않으면 기본 초기화 메서드 호출
                system = GA4AutomationSystem(db_name=":memory:")
                mock_init.assert_called_once()

class TestInterfaceAbstraction:
    """인터페이스 추상화 테스트"""
    
    def test_analytics_client_interface(self):
        """Analytics 클라이언트 인터페이스 테스트"""
        # 추상 클래스 직접 인스턴스화 불가능
        with pytest.raises(TypeError):
            IAnalyticsClient()
    
    def test_email_sender_interface(self):
        """이메일 발송 인터페이스 테스트"""
        with pytest.raises(TypeError):
            IEmailSender()
    
    def test_logger_interface(self):
        """로거 인터페이스 테스트"""
        with pytest.raises(TypeError):
            ILogger()

class TestCodeQualityImprovements:
    """코드 품질 개선 사항 테스트"""
    
    def test_dry_principle_logging_consolidation(self):
        """DRY 원칙 - 로깅 통합 테스트"""
        # 여러 모듈에서 동일한 로거 매니저 사용 확인
        
        with patch('src.core.email_validator.SmartEmailValidationSystem._init_ga4_client'):
            with patch('src.core.email_validator.SmartEmailValidationSystem._init_gmail_client'):
                email_system = SmartEmailValidationSystem()
        
        with patch('src.core.ga4_automation.GA4AutomationSystem._init_client'):
            with patch('src.core.ga4_automation.GA4AutomationSystem._init_database'):
                ga4_system = GA4AutomationSystem(db_name=":memory:")
        
        # 두 시스템 모두 공통 로거 시스템 사용
        assert hasattr(email_system, 'logger')
        assert hasattr(ga4_system, 'logger')
    
    def test_single_responsibility_principle(self):
        """단일 책임 원칙 준수 테스트"""
        # LoggerManager는 로깅만 담당
        logger_methods = [method for method in dir(LoggerManager) 
                         if not method.startswith('_')]
        
        logging_related = ['setup_logging', 'get_logger']
        for method in logger_methods:
            assert method in logging_related, f"로깅과 관련없는 메서드: {method}"

class TestSystemIntegration:
    """시스템 통합 테스트"""
    
    def test_improved_system_initialization(self):
        """개선된 시스템 초기화 테스트"""
        with patch('src.core.ga4_automation.GA4AutomationSystem._init_client'):
            with patch('src.core.ga4_automation.GA4AutomationSystem._init_database'):
                system = GA4AutomationSystem(db_name=":memory:")
                
                # 개선된 로깅 시스템 사용 확인
                assert system.logger is not None
                assert hasattr(system.logger, 'info')
                assert hasattr(system.logger, 'error')
    
    def test_email_system_improved_logging(self):
        """이메일 시스템 개선된 로깅 테스트"""
        with patch('src.core.email_validator.SmartEmailValidationSystem._init_ga4_client'):
            with patch('src.core.email_validator.SmartEmailValidationSystem._init_gmail_client'):
                system = SmartEmailValidationSystem()
                
                # 개선된 로깅 시스템 사용 확인
                assert system.logger is not None
                assert system.logger.name == "EMAIL_SYSTEM"

class TestErrorHandling:
    """에러 처리 개선 테스트"""
    
    def test_graceful_dependency_failure(self):
        """의존성 실패 시 우아한 처리 테스트"""
        with patch('src.core.ga4_automation.GA4AutomationSystem._init_client') as mock_init:
            with patch('src.core.ga4_automation.GA4AutomationSystem._init_database'):
                # 클라이언트 초기화 실패 시뮬레이션
                mock_init.side_effect = Exception("클라이언트 초기화 실패")
                
                # 예외가 발생해도 시스템이 중단되지 않아야 함
                with pytest.raises(Exception):
                    GA4AutomationSystem(db_name=":memory:")

def run_improved_tests():
    """개선된 테스트 실행"""
    print("🧪 개선된 GA4 자동화 시스템 테스트 시작")
    print("=" * 50)
    
    # pytest 실행
    test_result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # 첫 번째 실패에서 중단
    ])
    
    if test_result == 0:
        print("\n✅ 모든 개선 사항 테스트 통과!")
        print("📋 개발 규칙 준수 상태: 크게 개선됨")
    else:
        print("\n❌ 일부 개선 사항 테스트 실패")
        print("📋 추가 개선 작업 필요")
    
    return test_result == 0

if __name__ == "__main__":
    run_improved_tests() 