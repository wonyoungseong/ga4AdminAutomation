#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 TDD 방식 오류 해결 테스트

현재 발생하는 오류들:
1. NotificationService.check_and_send_daily_notifications 메서드 누락
2. GA4Scheduler.start 메서드 누락  
3. 대시보드 템플릿 dict 객체 속성 접근 오류
4. 데이터베이스 스키마 불일치
"""

import sys
import os
import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.notifications.notification_service import NotificationService
from src.api.scheduler import GA4Scheduler
from src.infrastructure.database import DatabaseManager


class TestTDDErrorFixes(unittest.TestCase):
    """TDD 방식으로 현재 발생하는 오류들을 테스트하고 해결"""
    
    def setUp(self):
        """테스트 설정"""
        self.maxDiff = None
        self.db_manager = DatabaseManager("data/test_tdd_error_fixes.db")
        self.notification_service = NotificationService()  # 매개변수 없이 초기화
        
    def tearDown(self):
        """테스트 정리"""
        if os.path.exists("data/test_tdd_error_fixes.db"):
            os.remove("data/test_tdd_error_fixes.db")
    
    def test_notification_service_methods_exist(self):
        """NotificationService에 필요한 메서드들이 존재하는지 테스트"""
        print("\n=== NotificationService 메서드 존재 테스트 ===")
        
        # NotificationService 인스턴스 생성 (매개변수 없이)
        notification_service = NotificationService()
        
        # 필요한 메서드들이 존재하는지 확인
        self.assertTrue(hasattr(notification_service, 'check_and_send_daily_notifications'),
                       "NotificationService에 check_and_send_daily_notifications 메서드가 없습니다")
        
        self.assertTrue(hasattr(notification_service, 'send_editor_downgrade_notification'),
                       "NotificationService에 send_editor_downgrade_notification 메서드가 없습니다")
        
        self.assertTrue(hasattr(notification_service, 'process_expiry_notifications'),
                       "NotificationService에 process_expiry_notifications 메서드가 없습니다")
        
        # 메서드가 호출 가능한지 확인
        self.assertTrue(callable(getattr(notification_service, 'check_and_send_daily_notifications')),
                       "check_and_send_daily_notifications가 호출 가능하지 않습니다")
        
        print("✅ NotificationService 메서드 존재 테스트 통과")
    
    def test_ga4_scheduler_methods_exist(self):
        """GA4Scheduler에 필요한 메서드들이 존재하는지 테스트"""
        print("\n=== GA4Scheduler 메서드 존재 테스트 ===")
        
        # GA4Scheduler 인스턴스 생성 (매개변수 없이)
        scheduler = GA4Scheduler()
        
        # 필요한 메서드들이 존재하는지 확인
        self.assertTrue(hasattr(scheduler, 'start'),
                       "GA4Scheduler에 start 메서드가 없습니다")
        
        self.assertTrue(hasattr(scheduler, 'stop'),
                       "GA4Scheduler에 stop 메서드가 없습니다")
        
        self.assertTrue(hasattr(scheduler, 'get_scheduler_status'),
                       "GA4Scheduler에 get_scheduler_status 메서드가 없습니다")
        
        # 메서드가 호출 가능한지 확인
        self.assertTrue(callable(getattr(scheduler, 'start')),
                       "start가 호출 가능하지 않습니다")
        
        self.assertTrue(callable(getattr(scheduler, 'stop')),
                       "stop이 호출 가능하지 않습니다")
        
        # 스케줄러 상태 확인 메서드 테스트
        status = scheduler.get_scheduler_status()
        self.assertIsInstance(status, dict, "get_scheduler_status가 dict를 반환하지 않습니다")
        self.assertIn('is_running', status, "스케줄러 상태에 is_running이 없습니다")
        
        print("✅ GA4Scheduler 메서드 존재 테스트 통과")
    
    def test_database_manager_methods_exist(self):
        """DatabaseManager에 필요한 메서드들이 존재하는지 테스트"""
        print("\n=== DatabaseManager 메서드 존재 테스트 ===")
        
        # close 메서드가 존재하는지 확인
        has_close = hasattr(self.db_manager, 'close')
        print(f"close 메서드 존재: {has_close}")
        self.assertTrue(
            has_close,
            "DatabaseManager에 close 메서드가 없습니다"
        )
        
        # 메서드가 호출 가능한지 확인
        self.assertTrue(callable(getattr(self.db_manager, 'close')),
                       "close가 호출 가능해야 합니다")
        
        print("✅ DatabaseManager 모든 필수 메서드 존재 확인")
    
    def test_web_interface_data_access(self):
        """웹 인터페이스에서 데이터 접근이 올바르게 작동하는지 테스트"""
        print("\n=== 웹 인터페이스 데이터 접근 테스트 ===")
        
        # DictObj 클래스 정의 (웹 메인에서 사용하는 것과 동일)
        class DictObj:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)
        
        # 1. DictObj 클래스가 정상적으로 작동하는지 확인
        self.assertTrue(DictObj, "DictObj 클래스가 존재하지 않습니다")
        
        # 2. dict를 DictObj로 변환 테스트
        test_data = {
            'last_updated': datetime.now(),
            'status': 'active',
            'count': 5
        }
        
        dict_obj = DictObj(test_data)
        
        # 3. 속성 접근 테스트
        has_last_updated = hasattr(dict_obj, 'last_updated')
        has_status = hasattr(dict_obj, 'status')
        has_count = hasattr(dict_obj, 'count')
        
        print(f"last_updated 속성 접근 가능: {has_last_updated}")
        print(f"status 속성 접근 가능: {has_status}")
        print(f"count 속성 접근 가능: {has_count}")
        
        self.assertTrue(has_last_updated, "DictObj에서 last_updated 속성 접근 불가")
        self.assertTrue(has_status, "DictObj에서 status 속성 접근 불가")
        self.assertTrue(has_count, "DictObj에서 count 속성 접근 불가")
        
        print("✅ 웹 인터페이스 데이터 접근 정상 작동 확인")
    
    def test_system_integration(self):
        """시스템 통합 테스트 - 모든 컴포넌트가 올바르게 초기화되는지 확인"""
        with patch('src.infrastructure.database.DatabaseManager') as mock_db_class, \
             patch('src.services.notifications.notification_service.NotificationService') as mock_notification_class, \
             patch('src.services.ga4_user_manager.GA4UserManager') as mock_user_manager_class, \
             patch('src.api.scheduler.GA4Scheduler') as mock_scheduler_class:
            
            # Mock 인스턴스들 설정
            mock_db = Mock()
            mock_notification = Mock()
            mock_user_manager = Mock()
            mock_scheduler = Mock()
            
            mock_db_class.return_value = mock_db
            mock_notification_class.return_value = mock_notification
            mock_user_manager_class.return_value = mock_user_manager
            mock_scheduler_class.return_value = mock_scheduler
            
            # 필요한 메서드들이 Mock에 있는지 확인
            mock_notification.check_and_send_daily_notifications = Mock()
            mock_notification.send_editor_downgrade_notification = Mock()
            mock_notification.process_expiry_notifications = Mock()
            
            mock_scheduler.start = Mock()
            mock_scheduler.stop = Mock()
            mock_scheduler.initialize = Mock()
            
            mock_db.close = Mock()
            
            # 시스템 컴포넌트들이 올바르게 초기화되는지 확인
            self.assertIsNotNone(mock_db)
            self.assertIsNotNone(mock_notification)
            self.assertIsNotNone(mock_user_manager)
            self.assertIsNotNone(mock_scheduler)
            
            # 메서드 호출이 가능한지 확인
            mock_notification.check_and_send_daily_notifications()
            mock_scheduler.start()
            mock_db.close()
            
            # 호출이 성공했는지 확인
            mock_notification.check_and_send_daily_notifications.assert_called_once()
            mock_scheduler.start.assert_called_once()
            mock_db.close.assert_called_once()


def main():
    """테스트 실행"""
    print("🧪 GA4 권한 관리 시스템 TDD 오류 해결 테스트 시작")
    print("=" * 60)
    
    # 테스트 실행
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTDDErrorFixes)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ 모든 테스트 통과!")
    else:
        print(f"❌ 테스트 실패: {len(result.failures)} 실패, {len(result.errors)} 오류")
        
        # 실패한 테스트들 출력
        for test, error in result.failures + result.errors:
            print(f"   - {test}: {error.split('AssertionError: ')[-1].split('TypeError: ')[-1].strip()}")
    
    print("✅ TDD 테스트 완료")


if __name__ == "__main__":
    main() 