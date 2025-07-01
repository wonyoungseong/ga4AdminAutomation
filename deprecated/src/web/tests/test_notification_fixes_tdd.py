#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD 알림 수정 사항 테스트
======================

GA4 권한 관리 시스템의 알림 기능 수정 사항을 TDD 방식으로 검증합니다.
"""

import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import unittest
from datetime import datetime, timedelta
from database.database_manager import DatabaseManager
from services.notifications.notification_types import NotificationType, NotificationMetadata
from services.notifications.notification_config import NotificationConfigManager
from services.notifications.notification_handlers import NotificationHandlerFactory


class TestNotificationFixesTDD(unittest.TestCase):
    """TDD 방식 알림 수정 사항 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.db_manager = DatabaseManager()
        self.config_manager = NotificationConfigManager(self.db_manager)
        
        # 테스트용 사용자 데이터
        self.test_user_data = {
            'email': 'wonyoungseong@gmail.com',
            'property_id': 'GA4-TEST-12345',
            'property_name': 'TEST Property',
            'role': 'Editor',
            'expiry_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        }
    
    def test_notification_type_enum_values(self):
        """RED → GREEN: NotificationType enum 값들이 올바르게 정의되어 있는지 확인"""
        print("\n🔍 Testing NotificationType enum values...")
        
        # 모든 알림 타입이 정의되어 있는지 확인
        expected_types = [
            'welcome', '30_days', '7_days', '1_day', 'today', 'expired',
            'extension_approved', 'editor_auto_downgrade', 'admin_notification',
            'immediate_approval', 'daily_summary', 'test'
        ]
        
        for expected_type in expected_types:
            found = False
            for notification_type in NotificationType:
                if notification_type.value == expected_type:
                    found = True
                    break
            
            self.assertTrue(found, f"NotificationType enum에 '{expected_type}' 값이 없습니다")
            print(f"  ✅ {expected_type} - 정의됨")
    
    def test_database_type_mapping(self):
        """RED → GREEN: enum 값과 데이터베이스 타입 매핑이 올바른지 확인"""
        print("\n🔍 Testing database type mapping...")
        
        # 매핑 테스트 케이스
        test_cases = [
            (NotificationType.WELCOME, 'welcome'),
            (NotificationType.EXPIRY_WARNING_30, 'expiry_warning'),
            (NotificationType.EXPIRY_WARNING_7, 'expiry_warning'),
            (NotificationType.EXPIRY_WARNING_1, 'expiry_warning'),
            (NotificationType.EXPIRY_WARNING_TODAY, 'expiry_warning'),
            (NotificationType.EXPIRED, 'expiry_notice'),
            (NotificationType.TEST, 'welcome')
        ]
        
        for enum_type, expected_db_type in test_cases:
            actual_db_type = NotificationMetadata.get_database_type_mapping(enum_type)
            self.assertEqual(
                actual_db_type, 
                expected_db_type,
                f"{enum_type.value} -> 예상: {expected_db_type}, 실제: {actual_db_type}"
            )
            print(f"  ✅ {enum_type.value} -> {actual_db_type}")
    
    def test_trigger_days_mapping(self):
        """RED → GREEN: 알림 타입별 발송 일수 매핑이 올바른지 확인"""
        print("\n🔍 Testing trigger days mapping...")
        
        test_cases = [
            (NotificationType.EXPIRY_WARNING_30, 30),
            (NotificationType.EXPIRY_WARNING_7, 7),
            (NotificationType.EXPIRY_WARNING_1, 1),
            (NotificationType.EXPIRY_WARNING_TODAY, 0),
            (NotificationType.WELCOME, 0),
            (NotificationType.EXPIRED, 0)
        ]
        
        for enum_type, expected_days in test_cases:
            actual_days = NotificationMetadata.get_trigger_days_for_type(enum_type)
            self.assertEqual(
                actual_days,
                expected_days,
                f"{enum_type.value} -> 예상: {expected_days}, 실제: {actual_days}"
            )
            print(f"  ✅ {enum_type.value} -> {actual_days}일")
    
    def test_notification_config_manager_integration(self):
        """RED → GREEN: NotificationConfigManager가 새로운 enum과 매핑을 올바르게 사용하는지 확인"""
        print("\n🔍 Testing NotificationConfigManager integration...")
        
        # 각 알림 타입별로 설정 확인
        test_types = [
            NotificationType.WELCOME,
            NotificationType.EXPIRY_WARNING_30,
            NotificationType.EXPIRY_WARNING_7,
            NotificationType.EXPIRY_WARNING_1,
            NotificationType.EXPIRY_WARNING_TODAY
        ]
        
        for notification_type in test_types:
            # 알림 활성화 상태 확인 (예외 발생하지 않아야 함)
            try:
                is_enabled = self.config_manager.is_notification_enabled(notification_type)
                print(f"  ✅ {notification_type.value} - 활성화 상태: {is_enabled}")
            except Exception as e:
                self.fail(f"{notification_type.value} 설정 확인 실패: {e}")
            
            # 알림 설정 조회 (예외 발생하지 않아야 함)
            try:
                settings = self.config_manager.get_notification_settings(notification_type)
                print(f"  ✅ {notification_type.value} - 설정 조회 성공")
            except Exception as e:
                self.fail(f"{notification_type.value} 설정 조회 실패: {e}")
    
    def test_notification_handlers_creation(self):
        """RED → GREEN: 모든 알림 타입에 대해 핸들러가 올바르게 생성되는지 확인"""
        print("\n🔍 Testing notification handlers creation...")
        
        # 지원되는 알림 타입들
        supported_types = [
            NotificationType.WELCOME,
            NotificationType.EXPIRY_WARNING_30,
            NotificationType.EXPIRY_WARNING_7,
            NotificationType.EXPIRY_WARNING_1,
            NotificationType.EXPIRY_WARNING_TODAY,
            NotificationType.EXPIRED,
            NotificationType.TEST
        ]
        
        for notification_type in supported_types:
            try:
                handler = NotificationHandlerFactory.create_handler(
                    notification_type, 
                    self.db_manager, 
                    self.config_manager
                )
                
                # 핸들러가 올바른 알림 타입을 반환하는지 확인
                self.assertEqual(
                    handler.get_notification_type(),
                    notification_type,
                    f"핸들러가 잘못된 알림 타입 반환: {handler.get_notification_type()} != {notification_type}"
                )
                
                print(f"  ✅ {notification_type.value} - 핸들러 생성 성공")
                
            except Exception as e:
                self.fail(f"{notification_type.value} 핸들러 생성 실패: {e}")
    
    def test_expiry_warning_handler_date_calculation(self):
        """RED → GREEN: 만료 경고 핸들러의 날짜 계산이 올바른지 확인"""
        print("\n🔍 Testing expiry warning handler date calculation...")
        
        # 30일 후 만료되는 사용자 데이터
        expiry_30_data = self.test_user_data.copy()
        expiry_30_data['expiry_date'] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 7일 후 만료되는 사용자 데이터
        expiry_7_data = self.test_user_data.copy()
        expiry_7_data['expiry_date'] = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # 1일 후 만료되는 사용자 데이터
        expiry_1_data = self.test_user_data.copy()
        expiry_1_data['expiry_date'] = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 오늘 만료되는 사용자 데이터
        expiry_today_data = self.test_user_data.copy()
        expiry_today_data['expiry_date'] = datetime.now().strftime('%Y-%m-%d')
        
        test_cases = [
            (NotificationType.EXPIRY_WARNING_30, expiry_30_data, True),
            (NotificationType.EXPIRY_WARNING_30, expiry_7_data, False),
            (NotificationType.EXPIRY_WARNING_7, expiry_7_data, True),
            (NotificationType.EXPIRY_WARNING_7, expiry_30_data, False),
            (NotificationType.EXPIRY_WARNING_1, expiry_1_data, True),
            (NotificationType.EXPIRY_WARNING_TODAY, expiry_today_data, True)
        ]
        
        for notification_type, user_data, expected_result in test_cases:
            handler = NotificationHandlerFactory.create_handler(
                notification_type, 
                self.db_manager, 
                self.config_manager
            )
            
            should_send = handler.should_send_notification(user_data)
            self.assertEqual(
                should_send,
                expected_result,
                f"{notification_type.value} 날짜 계산 오류: 예상 {expected_result}, 실제 {should_send}"
            )
            
            print(f"  ✅ {notification_type.value} - 날짜 계산 정확")
    
    def test_test_notification_with_target_email(self):
        """RED → GREEN: wonyoungseong@gmail.com으로 테스트 알림 발송 테스트"""
        print("\n🔍 Testing notification to wonyoungseong@gmail.com...")
        
        test_data = {
            'email': 'wonyoungseong@gmail.com',
            'property_id': 'GA4-TEST-12345',
            'property_name': 'TDD Test Property',
            'role': 'Editor'
        }
        
        # 테스트 알림 핸들러 생성
        handler = NotificationHandlerFactory.create_handler(
            NotificationType.TEST, 
            self.db_manager, 
            self.config_manager
        )
        
        # 발송 조건 확인 (테스트 알림은 항상 True여야 함)
        should_send = handler.should_send_notification(test_data)
        self.assertTrue(should_send, "테스트 알림은 항상 발송되어야 합니다")
        
        # 메시지 내용 생성
        subject, body = handler.generate_message_content(test_data)
        
        # 메시지 내용 검증
        self.assertIn('테스트 알림', subject)
        self.assertIn('wonyoungseong@gmail.com', body)
        self.assertIn('GA4 권한 관리 시스템', body)
        
        print(f"  ✅ 테스트 알림 대상: {test_data['email']}")
        print(f"  ✅ 제목: {subject}")
        print(f"  ✅ 발송 조건: {should_send}")
    
    def test_comprehensive_integration(self):
        """REFACTOR: 종합 통합 테스트 - 모든 구성 요소가 함께 작동하는지 확인"""
        print("\n🔍 Comprehensive integration test...")
        
        # 모든 지원 알림 타입에 대해 통합 테스트
        all_types = [
            NotificationType.WELCOME,
            NotificationType.EXPIRY_WARNING_30,
            NotificationType.EXPIRY_WARNING_7,
            NotificationType.EXPIRY_WARNING_1,
            NotificationType.EXPIRY_WARNING_TODAY,
            NotificationType.EXPIRED,
            NotificationType.TEST
        ]
        
        success_count = 0
        total_count = len(all_types)
        
        for notification_type in all_types:
            try:
                # 1. enum 값 확인
                enum_value = notification_type.value
                
                # 2. 데이터베이스 매핑 확인
                db_type = NotificationMetadata.get_database_type_mapping(notification_type)
                
                # 3. 설정 관리자 통합 확인
                is_enabled = self.config_manager.is_notification_enabled(notification_type)
                
                # 4. 핸들러 생성 및 작동 확인
                handler = NotificationHandlerFactory.create_handler(
                    notification_type, 
                    self.db_manager, 
                    self.config_manager
                )
                
                # 5. 메시지 생성 확인
                subject, body = handler.generate_message_content(self.test_user_data)
                
                success_count += 1
                print(f"  ✅ {enum_value} - 통합 테스트 성공")
                
            except Exception as e:
                print(f"  ❌ {notification_type.value} - 통합 테스트 실패: {e}")
        
        # 성공률 확인
        success_rate = success_count / total_count * 100
        self.assertEqual(success_count, total_count, f"통합 테스트 실패: {success_count}/{total_count} 성공 ({success_rate:.1f}%)")
        
        print(f"\n🎉 종합 통합 테스트 결과: {success_count}/{total_count} 성공 ({success_rate:.1f}%)")


def run_tdd_notification_tests():
    """TDD 알림 테스트 실행"""
    print("=" * 70)
    print("🧪 TDD 알림 수정 사항 테스트 시작")
    print("=" * 70)
    
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNotificationFixesTDD)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📊 TDD 테스트 결과 요약")
    print("=" * 70)
    print(f"🔍 실행된 테스트: {result.testsRun}")
    print(f"✅ 성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 실패: {len(result.failures)}")
    print(f"🚨 오류: {len(result.errors)}")
    
    if result.failures:
        print("\n📋 실패한 테스트:")
        for test, failure in result.failures:
            print(f"  ❌ {test}: {failure}")
    
    if result.errors:
        print("\n📋 오류가 발생한 테스트:")
        for test, error in result.errors:
            print(f"  🚨 {test}: {error}")
    
    # 성공 여부 반환
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = run_tdd_notification_tests()
    exit(0 if success else 1) 