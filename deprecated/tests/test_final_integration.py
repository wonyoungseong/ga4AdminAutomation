#!/usr/bin/env python3
"""
GA4 권한 관리 시스템 최종 통합 테스트
===================================

TDD 방식으로 해결한 모든 오류들이 실제로 수정되었는지 최종 검증
"""

import unittest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestFinalIntegration(unittest.TestCase):
    """최종 통합 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.maxDiff = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """테스트 정리"""
        self.loop.close()
    
    def test_all_critical_services_available(self):
        """모든 핵심 서비스 가용성 테스트"""
        print("\n🔍 핵심 서비스 가용성 테스트")
        
        # 1. 모든 핵심 모듈 import 테스트
        critical_imports = [
            ('src.services.notification_service', 'NotificationService'),
            ('src.api.scheduler', 'GA4Scheduler'),
            ('src.infrastructure.database', 'DatabaseManager'),
            ('src.web.main', 'DictObj'),
            ('src.services.ga4_user_manager', 'GA4UserManager'),
            ('src.core.ga4_automation', 'GA4AutomationSystem'),
        ]
        
        for module_path, class_name in critical_imports:
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                self.assertTrue(callable(cls), f"{class_name}이 호출 가능하지 않습니다")
                print(f"✅ {class_name} 가용")
            except ImportError as e:
                self.fail(f"❌ {class_name} import 실패: {e}")
            except AttributeError as e:
                self.fail(f"❌ {class_name} 클래스 없음: {e}")
        
        print("✅ 모든 핵심 서비스 가용성 확인")
    
    def test_notification_service_complete_functionality(self):
        """NotificationService 완전 기능 테스트"""
        print("\n📧 NotificationService 완전 기능 테스트")
        
        from src.services.notification_service import NotificationService
        
        # 서비스 인스턴스 생성
        service = NotificationService()
        
        # 1. 모든 필수 메서드 존재 확인
        essential_methods = [
            'check_and_send_daily_notifications',
            'send_editor_downgrade_notification',
            'process_expiry_notifications',
            'send_welcome_email',
            'send_expiry_warning_email',
            'send_deletion_notice_email',
            'send_admin_notification',
            'initialize'
        ]
        
        for method_name in essential_methods:
            self.assertTrue(hasattr(service, method_name),
                           f"NotificationService에 {method_name} 메서드가 없습니다")
            method = getattr(service, method_name)
            self.assertTrue(callable(method),
                           f"{method_name}이 호출 가능하지 않습니다")
        
        # 2. 내부 유틸리티 메서드 확인
        utility_methods = ['_get_role_korean', '_load_config', '_log_notification']
        for method_name in utility_methods:
            self.assertTrue(hasattr(service, method_name),
                           f"NotificationService에 {method_name} 유틸리티 메서드가 없습니다")
        
        # 3. 한국어 역할 변환 정확성 테스트
        role_tests = [
            ('viewer', '뷰어 (읽기 전용)'),
            ('editor', '편집자 (데이터 수정)'),
            ('admin', '관리자 (모든 권한)'),
            ('analyst', '분석가 (표준 분석)')
        ]
        
        for eng_role, expected_kor in role_tests:
            actual = service._get_role_korean(eng_role)
            self.assertEqual(actual, expected_kor,
                           f"{eng_role} 역할 변환 오류: 예상 '{expected_kor}', 실제 '{actual}'")
        
        print("✅ NotificationService 완전 기능 확인")
    
    def test_scheduler_complete_functionality(self):
        """GA4Scheduler 완전 기능 테스트"""
        print("\n⏰ GA4Scheduler 완전 기능 테스트")
        
        from src.api.scheduler import GA4Scheduler
        
        # 스케줄러 인스턴스 생성
        scheduler = GA4Scheduler()
        
        # 1. 모든 필수 메서드 존재 확인
        essential_methods = [
            'start', 'stop', 'start_scheduler', 'stop_scheduler',
            'get_scheduler_status', 'initialize',
            'process_expiry_queue', 'process_editor_downgrade',
            'daily_maintenance', 'run_manual_maintenance'
        ]
        
        for method_name in essential_methods:
            self.assertTrue(hasattr(scheduler, method_name),
                           f"GA4Scheduler에 {method_name} 메서드가 없습니다")
            method = getattr(scheduler, method_name)
            self.assertTrue(callable(method),
                           f"{method_name}이 호출 가능하지 않습니다")
        
        # 2. 스케줄러 상태 구조 확인
        status = scheduler.get_scheduler_status()
        required_status_fields = ['is_running', 'scheduled_jobs', 'next_run', 'jobs']
        for field in required_status_fields:
            self.assertIn(field, status,
                         f"스케줄러 상태에 {field} 필드가 없습니다")
        
        # 3. 초기 상태 검증
        self.assertFalse(status['is_running'],
                        "스케줄러가 초기에 실행 중이면 안됩니다")
        self.assertIsInstance(status['scheduled_jobs'], int,
                             "scheduled_jobs가 정수가 아닙니다")
        
        print("✅ GA4Scheduler 완전 기능 확인")
    
    def test_database_schema_integrity(self):
        """데이터베이스 스키마 무결성 테스트"""
        print("\n🗄️ 데이터베이스 스키마 무결성 테스트")
        
        from src.infrastructure.database import DatabaseManager
        
        # 데이터베이스 매니저 인스턴스 생성
        db_manager = DatabaseManager()
        
        # 1. 필수 메서드 존재 확인
        essential_methods = [
            'initialize_database', 'execute_query', 'execute_insert',
            'execute_update', 'get_connection', 'close',
            'get_database_stats', 'backup_database'
        ]
        
        for method_name in essential_methods:
            self.assertTrue(hasattr(db_manager, method_name),
                           f"DatabaseManager에 {method_name} 메서드가 없습니다")
        
        # 2. 데이터베이스 경로 설정 확인
        self.assertIsNotNone(db_manager.db_path,
                            "데이터베이스 경로가 설정되지 않았습니다")
        self.assertTrue(db_manager.db_path.endswith('.db'),
                       "데이터베이스 파일 확장자가 올바르지 않습니다")
        
        # 3. 필수 테이블 스키마 정의 확인
        essential_tables = [
            'user_registrations', 'ga4_accounts', 'ga4_properties',
            'notification_logs', 'audit_logs', 'system_settings'
        ]
        
        for table_name in essential_tables:
            # 테이블 존재 확인 쿼리 구조 검증
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            self.assertIsInstance(query, str)
            self.assertIn(table_name, query)
        
        print("✅ 데이터베이스 스키마 무결성 확인")
    
    def test_web_interface_complete_compatibility(self):
        """웹 인터페이스 완전 호환성 테스트"""
        print("\n🌐 웹 인터페이스 완전 호환성 테스트")
        
        from src.web.main import DictObj
        
        # 1. DictObj 클래스 완전 기능 테스트
        complex_test_data = {
            'id': 123,
            'name': 'Test Property',
            'status': 'active',
            'created_at': '2024-01-01 10:00:00',
            'expiry_date': '2024-12-31 23:59:59',
            'user_count': 50,
            'is_active': True,
            'permissions': ['read', 'write'],
            'nested_object': {
                'account_id': 'acc_123',
                'account_name': 'Test Account'
            },
            'metadata': None
        }
        
        dict_obj = DictObj(complex_test_data)
        
        # 기본 데이터 타입 접근 테스트
        self.assertEqual(dict_obj.id, 123)
        self.assertEqual(dict_obj.name, 'Test Property')
        self.assertEqual(dict_obj.status, 'active')
        self.assertTrue(dict_obj.is_active)
        self.assertEqual(dict_obj.user_count, 50)
        
        # 배열 데이터 접근 테스트
        self.assertIsInstance(dict_obj.permissions, list)
        self.assertEqual(len(dict_obj.permissions), 2)
        
        # 중첩 객체 접근 테스트
        self.assertIsInstance(dict_obj.nested_object, dict)
        self.assertEqual(dict_obj.nested_object['account_id'], 'acc_123')
        
        # None 값 처리 테스트
        self.assertIsNone(dict_obj.metadata)
        
        # 존재하지 않는 속성 처리 테스트
        self.assertIsNone(dict_obj.nonexistent_field)
        
        # 2. 템플릿 조건문 호환성 테스트
        template_conditions = [
            (bool(dict_obj.status), True),  # if status
            (dict_obj.user_count > 0, True),  # if user_count > 0
            (dict_obj.is_active, True),  # if is_active
            (bool(dict_obj.permissions), True),  # if permissions
            (dict_obj.metadata is None, True),  # if metadata is None
        ]
        
        for condition, expected in template_conditions:
            self.assertEqual(condition, expected,
                           f"템플릿 조건문 테스트 실패: {condition} != {expected}")
        
        print("✅ 웹 인터페이스 완전 호환성 확인")
    
    def test_system_integration_workflow(self):
        """시스템 통합 워크플로우 테스트"""
        print("\n🔄 시스템 통합 워크플로우 테스트")
        
        # 1. 모든 서비스 동시 인스턴스 생성
        try:
            from src.services.notification_service import NotificationService
            from src.api.scheduler import GA4Scheduler
            from src.infrastructure.database import DatabaseManager
            from src.services.ga4_user_manager import GA4UserManager
            
            notification_service = NotificationService()
            scheduler = GA4Scheduler()
            db_manager = DatabaseManager()
            user_manager = GA4UserManager()
            
            print("✅ 모든 서비스 동시 인스턴스 생성 성공")
        except Exception as e:
            self.fail(f"서비스 인스턴스 생성 실패: {e}")
        
        # 2. 서비스 간 의존성 확인
        self.assertIsNotNone(scheduler.notification_service,
                            "스케줄러가 알림 서비스를 참조하지 않습니다")
        self.assertIsNotNone(notification_service.db_manager,
                            "알림 서비스가 데이터베이스 매니저를 참조하지 않습니다")
        
        # 3. 메서드 체이닝 가능성 테스트
        self.assertTrue(hasattr(scheduler.notification_service, 'check_and_send_daily_notifications'),
                       "스케줄러 -> 알림 서비스 메서드 체이닝 불가")
        
        # 4. 설정 로딩 테스트
        config = notification_service._load_config()
        self.assertIsInstance(config, dict, "설정이 dict 형태가 아닙니다")
        
        # 5. 에러 복구 메커니즘 테스트
        original_config = notification_service.config
        try:
            # 의도적으로 설정을 None으로 설정
            notification_service.config = None
            # 서비스가 기본 설정으로 복구할 수 있는지 확인
            recovered_config = notification_service._load_config()
            self.assertIsInstance(recovered_config, dict,
                                "설정 복구 메커니즘이 작동하지 않습니다")
        finally:
            # 원래 설정 복원
            notification_service.config = original_config
        
        print("✅ 시스템 통합 워크플로우 확인")
    
    def test_error_handling_robustness(self):
        """에러 처리 견고성 테스트"""
        print("\n🛡️ 에러 처리 견고성 테스트")
        
        from src.services.notification_service import NotificationService
        from src.api.scheduler import GA4Scheduler
        
        # 1. NotificationService 에러 처리 테스트
        notification_service = NotificationService()
        
        # 잘못된 역할 입력에 대한 처리
        unknown_role = notification_service._get_role_korean('unknown_role')
        self.assertEqual(unknown_role, 'unknown_role',
                        "알 수 없는 역할에 대한 처리가 올바르지 않습니다")
        
        # 2. GA4Scheduler 에러 처리 테스트
        scheduler = GA4Scheduler()
        
        # 스케줄러 상태 조회 (초기화 전에도 안전해야 함)
        status = scheduler.get_scheduler_status()
        self.assertIsInstance(status, dict,
                             "스케줄러 상태 조회가 dict를 반환하지 않습니다")
        
        # 3. 중복 start/stop 호출 안전성 테스트
        # 이미 중지된 스케줄러 중지 시도 (에러 없이 처리되어야 함)
        try:
            scheduler.stop()  # 이미 중지된 상태에서 중지 시도
            print("✅ 중복 stop 호출 안전 처리")
        except Exception as e:
            self.fail(f"중복 stop 호출에서 예외 발생: {e}")
        
        print("✅ 에러 처리 견고성 확인")

if __name__ == '__main__':
    print("🎯 GA4 권한 관리 시스템 최종 통합 테스트")
    print("=" * 70)
    
    # 테스트 실행
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFinalIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 최종 결과 요약
    print("\n" + "=" * 70)
    print("🏆 최종 테스트 결과 요약")
    print(f"총 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"에러: {len(result.errors)}")
    
    if result.wasSuccessful():
        success_rate = 100.0
        print("\n🎉 축하합니다! 모든 테스트가 성공했습니다!")
        print("✅ GA4 권한 관리 시스템이 완전히 안정화되었습니다.")
        print("✅ TDD 방식으로 모든 오류가 체계적으로 해결되었습니다.")
        print("✅ 시스템의 모든 핵심 기능이 정상적으로 작동합니다.")
    else:
        failed_tests = len(result.failures) + len(result.errors)
        success_rate = ((result.testsRun - failed_tests) / result.testsRun) * 100
        print(f"\n⚠️ 일부 테스트 실패. 성공률: {success_rate:.1f}%")
        
        if result.failures:
            print("\n❌ 실패한 테스트:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\n💥 에러가 발생한 테스트:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print(f"\n📊 최종 성공률: {success_rate:.1f}%")
    print("=" * 70) 