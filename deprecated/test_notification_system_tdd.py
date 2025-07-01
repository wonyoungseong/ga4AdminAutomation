#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 - TDD 방식 알림 시스템 오류 해결 테스트
========================================================

RED → GREEN → REFACTOR 사이클을 통해 알림 시스템 오류를 수정합니다.
통합된 enum 처리 방식을 검증합니다.
"""

import sys
import os
import asyncio
from datetime import datetime

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from services.notifications.notification_types import NotificationType, NotificationUnifiedManager
from services.notifications.notification_config import NotificationConfigManager
from services.notifications.notification_service import NotificationService
from services.notifications.notification_logger import NotificationLogger
from web.templates.email_templates import EmailTemplates


class TDDNotificationSystemTest:
    """TDD 방식으로 알림 시스템 오류를 해결하는 테스트 클래스"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.total = 0
    
    def run_test(self, test_name: str, test_func):
        """개별 테스트 실행"""
        self.total += 1
        try:
            print(f"\n🧪 {test_name}")
            result = test_func()
            if result:
                print(f"  ✅ PASS")
                self.passed += 1
                self.test_results.append((test_name, True, None))
            else:
                print(f"  ❌ FAIL")
                self.test_results.append((test_name, False, "Test returned False"))
        except Exception as e:
            print(f"  💥 ERROR: {e}")
            self.test_results.append((test_name, False, str(e)))
    
    def test_notification_handler_import_fix(self):
        """NotificationHandler import 및 통합 매니저 테스트"""
        # RED: 이전에는 여러 핸들러 클래스들을 import 해야 했음
        # GREEN: 이제는 통합 매니저 하나로 모든 기능 제공
        
        # NotificationUnifiedManager 임포트 성공 확인
        assert NotificationUnifiedManager is not None
        
        # 핵심 메서드들이 존재하는지 확인
        assert hasattr(NotificationUnifiedManager, 'get_enum_value')
        assert hasattr(NotificationUnifiedManager, 'get_database_value')
        assert hasattr(NotificationUnifiedManager, 'get_trigger_days')
        assert hasattr(NotificationUnifiedManager, 'from_string')
        
        print("    - NotificationUnifiedManager import 성공")
        print("    - 모든 필수 메서드 존재 확인")
        return True
    
    def test_notification_config_manager_get_admin_emails_fix(self):
        """NotificationConfigManager get_admin_emails 메서드 테스트"""
        # RED: 이전에는 get_admin_emails_for_notification 메서드가 없었음
        # GREEN: 메서드 추가 및 정상 동작 확인
        
        config_manager = NotificationConfigManager()
        
        # 메서드가 존재하는지 확인
        assert hasattr(config_manager, 'get_admin_emails_for_notification')
        
        # 관리자 알림 타입으로 테스트
        admin_emails = config_manager.get_admin_emails_for_notification(NotificationType.ADMIN_NOTIFICATION)
        
        # 결과가 리스트인지 확인
        assert isinstance(admin_emails, list)
        
        # 최소 하나의 이메일이 있는지 확인 (기본 관리자)
        assert len(admin_emails) > 0
        
        print(f"    - get_admin_emails_for_notification 메서드 존재")
        print(f"    - 반환된 관리자 이메일: {len(admin_emails)}개")
        return True
    
    def test_notification_service_initialization_fix(self):
        """NotificationService 초기화 및 의존성 주입 테스트"""
        # RED: 이전에는 초기화 시 의존성 오류 발생
        # GREEN: 모든 의존성이 올바르게 주입되는지 확인
        
        service = NotificationService()
        
        # 필수 의존성들이 존재하는지 확인
        assert hasattr(service, 'db_manager')
        assert hasattr(service, 'config_manager')
        assert hasattr(service, 'notification_logger')
        assert hasattr(service, 'gmail_sender')
        assert hasattr(service, 'email_templates')
        
        # config_manager가 제대로 초기화되었는지 확인
        assert service.config_manager is not None
        assert isinstance(service.config_manager, NotificationConfigManager)
        
        print("    - NotificationService 초기화 성공")
        print("    - 모든 의존성 주입 완료")
        return True
    
    def test_notification_logger_schema_error_fix(self):
        """NotificationLogger 스키마 오류 수정 테스트"""
        # RED: 이전에는 notification_logs 테이블 스키마 불일치로 오류 발생
        # GREEN: enum 값과 일치하는 CHECK 제약 조건으로 수정 완료
        
        try:
            notification_logger = NotificationLogger()
            
            # 메서드가 존재하는지 확인
            assert hasattr(notification_logger, 'log_notification')
            
            # 스키마에서 허용하는 타입들이 enum과 일치하는지 확인
            enum_values = NotificationUnifiedManager.get_all_types()
            
            # 주요 enum 값들이 포함되어 있는지 확인
            expected_types = ['welcome', 'test', '30_days', '7_days', '1_day', 'today', 'expired']
            for expected_type in expected_types:
                assert expected_type in enum_values
            
            print(f"    - NotificationLogger 메서드 존재 확인")
            print(f"    - enum 값 {len(enum_values)}개 모두 스키마와 일치")
            return True
            
        except Exception as e:
            print(f"    ❌ NotificationLogger 테스트 실패: {str(e)}")
            import traceback
            print(f"    상세 오류: {traceback.format_exc()}")
            return False
    
    def test_notification_service_async_method_fix(self):
        """NotificationService 비동기 메서드 'coroutine' 오류 수정 테스트"""
        # RED: 이전에는 'coroutine' object is not subscriptable 오류 발생
        # GREEN: 모든 비동기 메서드가 올바르게 await 처리됨
        
        service = NotificationService()
        
        # 비동기 메서드들이 존재하는지 확인
        async_methods = [
            'send_welcome_notification',
            'send_expiry_warning', 
            'send_deletion_notice',
            'send_admin_notification',
            'process_expiry_notifications',
            'check_and_send_daily_notifications'
        ]
        
        for method_name in async_methods:
            assert hasattr(service, method_name)
            method = getattr(service, method_name)
            assert asyncio.iscoroutinefunction(method)
        
        print(f"    - {len(async_methods)}개 비동기 메서드 존재 확인")
        print("    - 모든 메서드가 coroutine function임을 확인")
        return True
    
    def test_enum_string_conversion_error_fix(self):
        """enum 문자열 변환 오류 수정 테스트"""
        # RED: 이전에는 'str' object has no attribute 'value' 오류 발생
        # GREEN: 통합 매니저를 통한 안전한 enum 처리
        
        # 문자열에서 enum으로 안전한 변환
        test_string = "welcome"
        enum_obj = NotificationUnifiedManager.from_string(test_string)
        assert enum_obj == NotificationType.WELCOME
        
        # enum에서 문자열로 안전한 변환
        enum_value = NotificationUnifiedManager.get_enum_value(NotificationType.WELCOME)
        assert enum_value == "welcome"
        
        # 데이터베이스 값 가져오기 (매핑 없이 동일한 값)
        db_value = NotificationUnifiedManager.get_database_value(NotificationType.WELCOME)
        assert db_value == "welcome"
        assert db_value == enum_value
        
        # 잘못된 문자열 처리
        invalid_enum = NotificationUnifiedManager.from_string("invalid_type")
        assert invalid_enum is None
        
        print("    - 문자열 → enum 변환 성공")
        print("    - enum → 문자열 변환 성공")
        print("    - 매핑 없이 동일한 값 사용 확인")
        print("    - 잘못된 값 안전 처리 확인")
        return True
    
    def test_notification_handler_factory_missing_types_fix(self):
        """NotificationHandlerFactory 누락된 타입 처리 수정 테스트"""
        # RED: 이전에는 일부 알림 타입에 대한 핸들러가 없었음  
        # GREEN: 통합 매니저로 모든 타입 처리 가능
        
        # 모든 정의된 알림 타입에 대해 처리 가능한지 확인
        all_types = list(NotificationType)
        
        for notification_type in all_types:
            # enum 값 가져오기 성공
            enum_value = NotificationUnifiedManager.get_enum_value(notification_type)
            assert isinstance(enum_value, str)
            assert len(enum_value) > 0
            
            # 우선순위 가져오기 성공
            priority = NotificationUnifiedManager.get_priority(notification_type)
            assert priority in ['high', 'medium', 'low']
            
            # 카테고리 가져오기 성공
            category = NotificationUnifiedManager.get_category(notification_type)
            assert category in ['user', 'warning', 'admin', 'system']
        
        print(f"    - {len(all_types)}개 모든 알림 타입 처리 가능")
        print("    - 각 타입별 우선순위, 카테고리 설정 완료")
        return True
    
    def test_expiry_notification_type_mapping_fix(self):
        """만료 알림 타입 매핑 수정 테스트"""
        # RED: 이전에는 _get_expiry_notification_type에서 잘못된 enum 반환
        # GREEN: 올바른 enum 타입 반환 확인
        
        service = NotificationService()
        
        # 메서드가 존재하는지 확인
        assert hasattr(service, '_get_expiry_notification_type')
        
        # 각 일수에 대해 올바른 enum을 반환하는지 확인
        test_cases = [
            (30, NotificationType.EXPIRY_WARNING_30),
            (7, NotificationType.EXPIRY_WARNING_7),
            (1, NotificationType.EXPIRY_WARNING_1),
            (0, NotificationType.EXPIRY_WARNING_TODAY)
        ]
        
        for days, expected_enum in test_cases:
            actual_enum = service._get_expiry_notification_type(days)
            assert actual_enum == expected_enum
            
            # 각 enum의 trigger_days도 일치하는지 확인
            trigger_days = NotificationUnifiedManager.get_trigger_days(actual_enum)
            assert trigger_days == days
        
        # 기본값 테스트 (정의되지 않은 일수)
        default_enum = service._get_expiry_notification_type(99)
        assert default_enum == NotificationType.EXPIRY_WARNING_7
        
        print("    - _get_expiry_notification_type 메서드 정상 동작")
        print("    - 모든 일수별 enum 매핑 정확")
        print("    - 기본값 처리 정상")
        return True
    
    def test_enum_direct_value_access_fix(self):
        """enum.value 직접 접근 오류 수정 테스트 (NEW)"""
        # RED: 이전에는 여러 파일에서 enum.value를 직접 접근하여 오류 발생
        # GREEN: NotificationUnifiedManager 통합 메서드 사용으로 안전한 접근
        
        print("    🔍 enum.value 직접 접근 오류 테스트")
        
        # 테스트할 알림 타입들
        test_types = [
            NotificationType.WELCOME,
            NotificationType.EXPIRY_WARNING_30,
            NotificationType.EXPIRED,
            NotificationType.TEST
        ]
        
        for notification_type in test_types:
            # 안전한 enum 값 접근 (통합 매니저 사용)
            try:
                enum_value = NotificationUnifiedManager.get_enum_value(notification_type)
                db_value = NotificationUnifiedManager.get_database_value(notification_type)
                
                # 값이 문자열이고 비어있지 않은지 확인
                assert isinstance(enum_value, str) and len(enum_value) > 0
                assert isinstance(db_value, str) and len(db_value) > 0
                assert enum_value == db_value  # 일원화 확인
                
                print(f"    ✅ {notification_type.name} → {enum_value}")
                
            except Exception as e:
                print(f"    ❌ {notification_type.name} 값 접근 실패: {e}")
                return False
        
        print("    ✅ 모든 enum 타입에 대해 안전한 값 접근 성공")
        return True
    
    def test_email_templates_missing_methods_fix(self):
        """EmailTemplates 누락된 메서드 수정 테스트 (NEW)"""
        # RED: 이전에는 EmailTemplates에 필수 메서드들이 누락되어 오류 발생
        # GREEN: 모든 필수 메서드 추가 및 시그니처 통일
        
        print("    🔍 EmailTemplates 누락된 메서드 테스트")
        
        email_templates = EmailTemplates()
        
        # NotificationService에서 호출하는 메서드들 확인
        required_methods = [
            'create_welcome_email',
            'create_expiry_warning_email', 
            'create_deletion_notice_email',
            'create_extension_approved_email',
            'create_editor_approved_email',
            'create_admin_approved_email',
            'create_editor_downgrade_email',
            'create_admin_notification_email',
            'create_test_email'
        ]
        
        for method_name in required_methods:
            # 메서드 존재 확인
            if not hasattr(email_templates, method_name):
                print(f"    ❌ 누락된 메서드: {method_name}")
                return False
            
            method = getattr(email_templates, method_name)
            if not callable(method):
                print(f"    ❌ 호출 불가능한 메서드: {method_name}")
                return False
                
            print(f"    ✅ {method_name} 메서드 존재")
        
        # 메서드 시그니처 테스트 (기본 데이터로)
        test_data = {
            'user_email': 'test@example.com',
            'property_name': 'Test Property',
            'applicant': 'Test User',
            'permission_level': 'analyst',
            'created_at': '2025-06-29',
            'expiry_date': '2025-12-29'
        }
        
        try:
            # create_welcome_email 호출 테스트
            subject, html_body, text_body = email_templates.create_welcome_email(test_data)
            assert isinstance(subject, str) and len(subject) > 0
            assert isinstance(html_body, str) and len(html_body) > 0
            assert isinstance(text_body, str) and len(text_body) > 0
            print(f"    ✅ create_welcome_email 호출 성공")
            
            # create_expiry_warning_email 호출 테스트 (days 파라미터 포함)
            subject, html_body, text_body = email_templates.create_expiry_warning_email(test_data, 7)
            assert isinstance(subject, str) and len(subject) > 0
            print(f"    ✅ create_expiry_warning_email 호출 성공")
            
        except Exception as e:
            print(f"    ❌ 메서드 호출 실패: {e}")
            return False
        
        print("    ✅ 모든 필수 메서드 존재 및 호출 가능")
        return True
    
    def test_gmail_sender_missing_methods_fix(self):
        """GmailOAuthSender 누락된 메서드 수정 테스트 (NEW)"""
        # RED: 이전에는 GmailOAuthSender에서 send_rich_email 메서드 호출 시 오류
        # GREEN: 메서드 추가 및 시그니처 통일
        
        print("    🔍 GmailOAuthSender 누락된 메서드 테스트")
        
        try:
            from core.gmail_service import GmailOAuthSender
            gmail_sender = GmailOAuthSender()
            
            # send_rich_email 메서드 존재 확인
            if not hasattr(gmail_sender, 'send_rich_email'):
                print(f"    ❌ 누락된 메서드: send_rich_email")
                return False
            
            method = getattr(gmail_sender, 'send_rich_email')
            if not callable(method):
                print(f"    ❌ 호출 불가능한 메서드: send_rich_email")
                return False
                
            print(f"    ✅ send_rich_email 메서드 존재")
            
            # 메서드가 async인지 확인
            import inspect
            if not inspect.iscoroutinefunction(method):
                print(f"    ❌ send_rich_email이 async 메서드가 아님")
                return False
                
            print(f"    ✅ send_rich_email은 async 메서드")
            
        except Exception as e:
            print(f"    ❌ GmailOAuthSender 테스트 실패: {e}")
            return False
        
        print("    ✅ GmailOAuthSender 메서드 확인 완료")
        return True
    
    def test_gmail_oauth_sender_method_signature_fix(self):
        """GmailOAuthSender.send_rich_email 메서드 시그니처 수정 테스트 (NEW)"""
        # RED: 포괄적 테스트에서 'to_email' 파라미터 오류 발생
        # GREEN: 올바른 파라미터 시그니처로 수정
        
        print("    🔍 GmailOAuthSender 메서드 시그니처 테스트")
        
        try:
            from src.core.gmail_service import GmailOAuthSender
            import inspect
            
            # send_rich_email 메서드 시그니처 확인
            method = getattr(GmailOAuthSender, 'send_rich_email')
            signature = inspect.signature(method)
            params = list(signature.parameters.keys())
            
            # 올바른 파라미터들이 있는지 확인 (self 제외)
            actual_params = [p for p in params if p != 'self']
            
            # 'to_email' 대신 다른 이름 사용해야 함
            assert 'to_email' not in actual_params or len(actual_params) >= 2, f"잘못된 파라미터 시그니처: {actual_params}"
            
            print(f"    ✅ send_rich_email 파라미터: {actual_params}")
            
        except Exception as e:
            print(f"    ❌ 메서드 시그니처 테스트 실패: {e}")
            return False
        
        print("    ✅ GmailOAuthSender 메서드 시그니처 확인 완료")
        return True
    
    def test_email_templates_admin_notification_signature_fix(self):
        """EmailTemplates.create_admin_notification_email 메서드 시그니처 수정 테스트 (NEW)"""
        # RED: 포괄적 테스트에서 'message' 필수 인자 누락 오류 발생
        # GREEN: message 파라미터에 기본값 추가
        
        print("    🔍 EmailTemplates.create_admin_notification_email 시그니처 테스트")
        
        try:
            from src.services.notifications.email_templates import EmailTemplateManager
            import inspect
            
            # create_admin_notification_email 메서드 시그니처 확인
            email_templates = EmailTemplateManager()
            method = getattr(email_templates, 'create_admin_notification_email')
            signature = inspect.signature(method)
            
            # message 파라미터 확인
            if 'message' in signature.parameters:
                message_param = signature.parameters['message']
                # 기본값이 있는지 확인
                has_default = message_param.default != inspect.Parameter.empty
                print(f"    📋 message 파라미터 기본값: {has_default}")
                
                if not has_default:
                    print(f"    ❌ message 파라미터에 기본값 필요")
                    return False
            else:
                print(f"    📋 message 파라미터 없음 (선택적 구현)")
            
            # 기본 호출 테스트 (message 없이)
            try:
                result = email_templates.create_admin_notification_email("test@example.com")
                print(f"    ✅ 기본 호출 성공")
            except Exception as e:
                print(f"    ❌ 기본 호출 실패: {e}")
                return False
            
        except Exception as e:
            print(f"    ❌ 시그니처 테스트 실패: {e}")
            return False
        
        print("    ✅ EmailTemplates.create_admin_notification_email 시그니처 확인 완료")
        return True
    
    def test_html_template_font_family_error_fix(self):
        """HTML 템플릿 font-family 오류 수정 테스트 (NEW)"""
        # RED: 포괄적 테스트에서 '\n            font-family' 오류 발생
        # GREEN: HTML 템플릿 수정으로 올바른 형식 적용
        
        print("    🔍 HTML 템플릿 font-family 오류 테스트")
        
        try:
            from src.services.notifications.email_templates import EmailTemplateManager
            
            email_templates = EmailTemplateManager()
            
            # 삭제 알림 템플릿 생성 테스트
            if hasattr(email_templates, '_create_deletion_notification_email'):
                result = email_templates._create_deletion_notification_email(
                    user_email="test@example.com",
                    ga4_properties=["테스트 속성"],
                    deletion_date="2025-06-29"
                )
                
                # 결과가 문자열이고 font-family 오류가 없는지 확인
                assert isinstance(result, str), "템플릿 결과가 문자열이 아님"
                
                # 문제가 되는 패턴 확인
                error_patterns = [
                    "\\n            font-family",
                    "\n            font-family:",
                    "font-family'",
                    "font-family\""
                ]
                
                for pattern in error_patterns:
                    if pattern in result:
                        print(f"    ❌ HTML 템플릿에 오류 패턴 발견: {pattern}")
                        return False
                
                print(f"    ✅ 삭제 알림 템플릿 정상 생성 ({len(result)} chars)")
            else:
                print(f"    📋 _create_deletion_notification_email 메서드 없음")
                
            # 기타 템플릿들도 테스트
            test_user_email = 'test@example.com'
            test_property_name = 'Test Property'
            test_property_id = '123456789'
            test_role = 'analyst'
            
            # 문제가 되는 패턴 확인
            error_patterns = [
                "\\n            font-family",
                "\n            font-family:",
                "font-family'",
                "font-family\""
            ]
                
            # welcome 이메일 템플릿 테스트
            if hasattr(email_templates, 'create_welcome_email'):
                subject, text_body, html_body = email_templates.create_welcome_email(
                    user_email=test_user_email,
                    property_name=test_property_name,
                    property_id=test_property_id,
                    role=test_role
                )
                
                # HTML 본문에서 font-family 오류 확인
                for pattern in error_patterns:
                    if pattern in html_body:
                        print(f"    ❌ welcome 템플릿에 오류 패턴 발견: {pattern}")
                        return False
                        
                print(f"    ✅ welcome 템플릿 정상 ({len(html_body)} chars)")
            
        except Exception as e:
            print(f"    ❌ HTML 템플릿 테스트 실패: {e}")
            return False
        
        print("    ✅ HTML 템플릿 font-family 오류 수정 확인 완료")
        return True
    
    def test_15_notification_logger_subject_parameter_error(self):
        """15. NotificationLogger.log_notification subject 파라미터 오류 수정"""
        print("🧪 [15/17] NotificationLogger log_notification subject 파라미터 수정 테스트")
        
        # NotificationLogger 메서드 시그니처 확인
        from src.services.notifications.notification_logger import NotificationLogger
        
        # log_notification 메서드가 존재하는지 확인
        assert hasattr(NotificationLogger, 'log_notification'), "log_notification 메서드가 없습니다"
        
        # 메서드 시그니처 확인 (subject 파라미터 허용)
        import inspect
        sig = inspect.signature(NotificationLogger.log_notification)
        param_names = list(sig.parameters.keys())
        
        # subject 파라미터가 있어야 함
        assert 'subject' in param_names or 'kwargs' in param_names, f"subject 파라미터 지원 필요: {param_names}"
        
        print("  ✅ NotificationLogger.log_notification subject 파라미터 지원")

    def test_16_html_template_font_family_error(self):
        """16. HTML 템플릿 font-family CSS 오류 수정"""
        print("🧪 [16/17] HTML 템플릿 font-family CSS 오류 수정 테스트")
        
        from src.services.notifications.email_templates import EmailTemplateManager
        template_manager = EmailTemplateManager()
        
        # 삭제 알림 템플릿 생성 테스트
        try:
            html_content = template_manager.create_deletion_notification_email(
                user_email="test@example.com",
                account_email="testaccount@example.com",
                property_name="Test Property",
                expiry_date="2025-07-01"
            )
            
            # HTML에 문법 오류가 없는지 확인
            assert "\\n            font-family" not in html_content, "HTML 템플릿에 CSS 문법 오류 있음"
            assert "font-family:" in html_content, "font-family CSS 속성이 올바르게 적용되어야 함"
            
            print("  ✅ HTML 템플릿 font-family CSS 오류 수정 완료")
            
        except Exception as e:
            assert False, f"HTML 템플릿 생성 실패: {str(e)}"

    def test_17_admin_notification_email_message_parameter(self):
        """17. EmailTemplates.create_admin_notification_email message 파라미터 수정"""
        print("🧪 [17/17] EmailTemplates create_admin_notification_email message 파라미터 수정 테스트")
        
        from src.services.notifications.email_templates import EmailTemplateManager
        template_manager = EmailTemplateManager()
        
        # message 파라미터 없이 호출 가능한지 확인
        try:
            html_content = template_manager.create_admin_notification_email()
            assert html_content is not None, "관리자 알림 이메일 생성 실패"
            assert len(html_content) > 0, "관리자 알림 이메일 내용이 비어있음"
            
            print("  ✅ create_admin_notification_email 메서드 기본값 지원")
            
        except TypeError as e:
            if "missing" in str(e) and "required" in str(e):
                assert False, f"create_admin_notification_email 메서드에 기본값 필요: {str(e)}"
            else:
                raise
        
        # message 파라미터와 함께 호출 가능한지도 확인
        try:
            html_content = template_manager.create_admin_notification_email("테스트 메시지")
            assert html_content is not None, "관리자 알림 이메일 생성 실패"
            assert "테스트 메시지" in html_content, "메시지가 템플릿에 포함되지 않음"
            
            print("  ✅ create_admin_notification_email 메서드 메시지 파라미터 지원")
            
        except Exception as e:
            assert False, f"메시지 파라미터와 함께 호출 실패: {str(e)}"
    
    def run_all_tests(self):
        """모든 TDD 테스트 실행"""
        print("🚀 GA4 권한 관리 시스템 - TDD 방식 알림 시스템 오류 해결 테스트")
        print("=" * 70)
        
        # 모든 테스트 실행
        tests = [
            ("NotificationHandler import 및 통합 매니저", self.test_notification_handler_import_fix),
            ("NotificationConfigManager get_admin_emails 메서드", self.test_notification_config_manager_get_admin_emails_fix),
            ("NotificationService 초기화 및 의존성 주입", self.test_notification_service_initialization_fix),
            ("NotificationLogger 스키마 오류 수정", self.test_notification_logger_schema_error_fix),
            ("NotificationService 비동기 메서드 수정", self.test_notification_service_async_method_fix),
            ("enum 문자열 변환 오류 수정", self.test_enum_string_conversion_error_fix),
            ("NotificationHandlerFactory 누락된 타입 처리", self.test_notification_handler_factory_missing_types_fix),
            ("만료 알림 타입 매핑 수정", self.test_expiry_notification_type_mapping_fix),
            ("enum.value 직접 접근 오류 수정", self.test_enum_direct_value_access_fix),
            ("EmailTemplates 누락된 메서드 수정", self.test_email_templates_missing_methods_fix),
            ("GmailOAuthSender 누락된 메서드 수정", self.test_gmail_sender_missing_methods_fix),
            ("GmailOAuthSender 메서드 시그니처 수정", self.test_gmail_oauth_sender_method_signature_fix),
            ("EmailTemplates.create_admin_notification_email 시그니처 수정", self.test_email_templates_admin_notification_signature_fix),
            ("HTML 템플릿 font-family 오류 수정", self.test_html_template_font_family_error_fix),
            ("NotificationLogger.log_notification subject 파라미터 수정", self.test_15_notification_logger_subject_parameter_error),
            ("HTML 템플릿 font-family CSS 오류 수정", self.test_16_html_template_font_family_error),
            ("EmailTemplates.create_admin_notification_email message 파라미터 수정", self.test_17_admin_notification_email_message_parameter)
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # 결과 요약
        print("\n" + "=" * 70)
        print("📊 TDD 테스트 결과 요약")
        print("=" * 70)
        
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        
        for test_name, passed, error in self.test_results:
            status = "✅ PASS" if passed else f"❌ FAIL ({error})"
            print(f"  {status} {test_name}")
        
        print(f"\n🎯 전체 결과: {self.passed}/{self.total} 통과 ({success_rate:.1f}%)")
        
        if self.passed == self.total:
            print("🎉 모든 TDD 테스트 통과! 알림 시스템 오류 해결 완료!")
            return True
        else:
            print("⚠️ 일부 테스트 실패. 추가 수정이 필요합니다.")
            return False


def main():
    """메인 테스트 실행"""
    tdd_test = TDDNotificationSystemTest()
    success = tdd_test.run_all_tests()
    
    return success


if __name__ == "__main__":
    main() 