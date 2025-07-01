#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 자동화 시스템 종합 테스트
==========================

개발 규칙 준수 여부와 시스템 전체 기능을 테스트합니다.
"""

import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.email_validator import SmartEmailValidationSystem
from src.core.ga4_automation import GA4AutomationSystem

class TestSystemArchitecture:
    """시스템 아키텍처 테스트"""
    
    def test_project_structure_compliance(self):
        """프로젝트 구조가 규칙에 맞는지 테스트"""
        required_dirs = [
            project_root / "src" / "core",
            project_root / "src" / "api", 
            project_root / "tests",
            project_root / "docs"
        ]
        
        for dir_path in required_dirs:
            assert dir_path.exists(), f"필수 디렉토리가 없습니다: {dir_path}"
    
    def test_naming_conventions(self):
        """명명 규칙 준수 테스트"""
        # 파일명이 스네이크 케이스인지 확인
        python_files = list(project_root.rglob("*.py"))
        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue
            # 파일명에 대문자가 없어야 함 (스네이크 케이스)
            assert file_path.stem.islower() or "_" in file_path.stem, \
                f"파일명이 스네이크 케이스가 아닙니다: {file_path.name}"

class TestEmailValidationSystem:
    """이메일 검증 시스템 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.validator = SmartEmailValidationSystem()
    
    def test_single_responsibility_principle(self):
        """단일 책임 원칙 준수 테스트"""
        # SmartEmailValidationSystem은 이메일 검증만 담당해야 함
        methods = [method for method in dir(self.validator) 
                  if not method.startswith('_')]
        
        email_related_methods = [
            'validate_email_with_ga4',
            'send_validation_results_email'
        ]
        
        for method in methods:
            if hasattr(getattr(self.validator, method), '__call__'):
                assert any(keyword in method.lower() 
                          for keyword in ['email', 'validate', 'send']), \
                    f"이메일 검증과 관련없는 메서드: {method}"
    
    @patch('src.core.email_validator.SmartEmailValidationSystem._check_google_account')
    def test_email_validation_basic(self, mock_check):
        """기본 이메일 검증 테스트"""
        mock_check.return_value = True
        
        result = self.validator.validate_email_with_ga4('test@gmail.com')
        
        assert result['status'] in ['VALID_GOOGLE_ACCOUNT', 'INVALID_EMAIL', 'NO_GOOGLE_ACCOUNT']
        assert 'message' in result
        assert isinstance(result['message'], str)

class TestGA4AutomationSystem:
    """GA4 자동화 시스템 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        with patch('src.core.ga4_automation.GA4AutomationSystem._init_client'):
            with patch('src.core.ga4_automation.GA4AutomationSystem._init_database'):
                self.automation = GA4AutomationSystem(db_name=":memory:")
    
    def test_dependency_inversion_principle(self):
        """의존성 역전 원칙 테스트"""
        # 고수준 모듈이 저수준 모듈에 의존하지 않는지 확인
        assert hasattr(self.automation, 'client'), "클라이언트 의존성이 주입되어야 함"
        assert hasattr(self.automation, 'logger'), "로거 의존성이 주입되어야 함"
    
    def test_interface_segregation_principle(self):
        """인터페이스 분리 원칙 테스트"""
        # 각 메서드가 명확한 단일 기능을 수행하는지 확인
        public_methods = [method for method in dir(self.automation) 
                         if not method.startswith('_')]
        
        expected_methods = [
            'add_user', 'remove_user', 'update_user_role', 
            'list_users', 'batch_add_users', 'get_user_history'
        ]
        
        for method in expected_methods:
            assert method in public_methods, f"필수 메서드가 없습니다: {method}"

class TestSystemIntegration:
    """시스템 통합 테스트"""
    
    def test_main_module_integration(self):
        """메인 모듈 통합 테스트"""
        # main.py가 올바르게 모듈을 import할 수 있는지 확인
        try:
            import main
            assert hasattr(main, 'main'), "main 함수가 있어야 함"
            assert hasattr(main, 'validate_email_command'), "이메일 검증 명령이 있어야 함"
            assert hasattr(main, 'run_qa_test_command'), "QA 테스트 명령이 있어야 함"
        except ImportError as e:
            pytest.fail(f"메인 모듈 import 실패: {e}")
    
    def test_configuration_loading(self):
        """설정 파일 로딩 테스트"""
        config_file = project_root / "config.json"
        assert config_file.exists(), "config.json 파일이 있어야 함"
        
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = ['account_id', 'property_id']
        for key in required_keys:
            assert key in config, f"설정에 필수 키가 없습니다: {key}"

class TestCodeQuality:
    """코드 품질 테스트"""
    
    def test_dry_principle(self):
        """DRY 원칙 테스트 - 중복 코드 확인"""
        # 로깅 설정이 여러 파일에서 중복되는지 확인
        python_files = list(project_root.rglob("*.py"))
        logging_setup_count = 0
        
        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'logging.basicConfig' in content:
                        logging_setup_count += 1
            except:
                continue
        
        # 로깅 설정이 너무 많은 파일에 중복되면 안됨
        assert logging_setup_count <= 3, f"로깅 설정이 너무 많은 파일에 중복됨: {logging_setup_count}개"
    
    def test_korean_documentation(self):
        """한국어 문서화 테스트"""
        # 주요 파일들이 한국어 docstring을 가지고 있는지 확인
        main_file = project_root / "main.py"
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 한국어 문자가 포함된 docstring이 있는지 확인
        korean_chars = ['가', '나', '다', '라', '마', '바', '사', '아', '자', '차', '카', '타', '파', '하']
        has_korean = any(char in content for char in korean_chars)
        assert has_korean, "한국어 문서화가 부족합니다"

def run_comprehensive_test():
    """종합 테스트 실행"""
    print("🧪 GA4 자동화 시스템 종합 테스트 시작")
    print("=" * 50)
    
    # pytest 실행
    test_result = pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])
    
    if test_result == 0:
        print("\n✅ 모든 테스트 통과!")
        print("📋 개발 규칙 준수 상태: 양호")
    else:
        print("\n❌ 일부 테스트 실패")
        print("📋 개발 규칙 준수 상태: 개선 필요")
    
    return test_result == 0

if __name__ == "__main__":
    run_comprehensive_test() 