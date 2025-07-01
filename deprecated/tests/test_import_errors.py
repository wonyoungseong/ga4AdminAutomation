#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import 오류 테스트
================

시스템의 import 문제를 테스트하고 해결하는 테스트 파일
"""

import pytest
import sys
import os

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_scheduler_import():
    """스케줄러 모듈 import 테스트"""
    try:
        from src.api.scheduler import GA4Scheduler
        assert GA4Scheduler is not None
        print("✅ GA4Scheduler 클래스 import 성공")
    except ImportError as e:
        pytest.fail(f"❌ GA4Scheduler import 실패: {e}")


def test_scheduler_service_instance():
    """스케줄러 서비스 인스턴스 생성 테스트"""
    try:
        from src.api.scheduler import GA4Scheduler
        
        # 인스턴스 생성
        scheduler = GA4Scheduler()
        assert scheduler is not None
        print("✅ GA4Scheduler 인스턴스 생성 성공")
        
        # 기본 메서드 존재 확인
        assert hasattr(scheduler, 'start_scheduler')
        assert hasattr(scheduler, 'stop_scheduler')
        assert hasattr(scheduler, 'get_scheduler_status')
        print("✅ 필수 메서드 존재 확인")
        
    except Exception as e:
        pytest.fail(f"❌ 스케줄러 인스턴스 생성 실패: {e}")


def test_notification_service_import():
    """알림 서비스 import 테스트"""
    try:
        from src.services.notification_service import NotificationService, notification_service
        assert NotificationService is not None
        assert notification_service is not None
        print("✅ NotificationService import 성공")
    except ImportError as e:
        pytest.fail(f"❌ NotificationService import 실패: {e}")


def test_ga4_user_manager_import():
    """GA4 사용자 관리자 import 테스트"""
    try:
        from src.services.ga4_user_manager import GA4UserManager, ga4_user_manager
        assert GA4UserManager is not None
        assert ga4_user_manager is not None
        print("✅ GA4UserManager import 성공")
    except ImportError as e:
        pytest.fail(f"❌ GA4UserManager import 실패: {e}")


def test_database_manager_import():
    """데이터베이스 매니저 import 테스트"""
    try:
        from src.infrastructure.database import DatabaseManager
        assert DatabaseManager is not None
        print("✅ DatabaseManager import 성공")
    except ImportError as e:
        pytest.fail(f"❌ DatabaseManager import 실패: {e}")


if __name__ == "__main__":
    print("🧪 Import 오류 테스트 시작...")
    
    test_scheduler_import()
    test_scheduler_service_instance()
    test_notification_service_import()
    test_ga4_user_manager_import()
    test_database_manager_import()
    
    print("✅ 모든 import 테스트 완료!") 