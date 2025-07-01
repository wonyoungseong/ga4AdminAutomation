#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 서버 시작 테스트
=================

웹 서버가 정상적으로 시작되는지 테스트
"""

import pytest
import sys
import os
import asyncio

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_web_app_import():
    """웹 앱 import 테스트"""
    try:
        from src.web.main import app
        assert app is not None
        print("✅ FastAPI 앱 import 성공")
    except ImportError as e:
        pytest.fail(f"❌ FastAPI 앱 import 실패: {e}")


def test_scheduler_service_import():
    """스케줄러 서비스 import 테스트"""
    try:
        from src.api.scheduler import scheduler_service, ga4_scheduler
        assert scheduler_service is not None
        assert ga4_scheduler is not None
        assert scheduler_service is ga4_scheduler  # 같은 인스턴스인지 확인
        print("✅ 스케줄러 서비스 import 성공")
    except ImportError as e:
        pytest.fail(f"❌ 스케줄러 서비스 import 실패: {e}")


def test_all_services_available():
    """모든 서비스가 사용 가능한지 테스트"""
    try:
        from src.web.main import (
            app, property_scanner, notification_service, 
            ga4_user_manager, db_manager
        )
        from src.api.scheduler import scheduler_service
        
        # 모든 서비스 인스턴스 확인
        assert app is not None
        assert property_scanner is not None
        assert notification_service is not None
        assert ga4_user_manager is not None
        assert db_manager is not None
        assert scheduler_service is not None
        
        print("✅ 모든 서비스 인스턴스 확인 성공")
        
    except Exception as e:
        pytest.fail(f"❌ 서비스 인스턴스 확인 실패: {e}")


def test_scheduler_methods():
    """스케줄러 메서드 테스트"""
    try:
        from src.api.scheduler import scheduler_service
        
        # 스케줄러 상태 확인
        status = scheduler_service.get_scheduler_status()
        assert isinstance(status, dict)
        assert 'is_running' in status
        assert 'scheduled_jobs' in status
        
        print("✅ 스케줄러 메서드 테스트 성공")
        
    except Exception as e:
        pytest.fail(f"❌ 스케줄러 메서드 테스트 실패: {e}")


async def test_async_services():
    """비동기 서비스 테스트"""
    try:
        from src.services.notification_service import notification_service
        from src.services.ga4_user_manager import ga4_user_manager
        from src.infrastructure.database import db_manager
        
        # 초기화 테스트 (실제로는 하지 않고 메서드 존재만 확인)
        assert hasattr(notification_service, 'initialize')
        assert hasattr(ga4_user_manager, 'initialize')
        assert hasattr(db_manager, 'initialize_database')
        
        print("✅ 비동기 서비스 메서드 확인 성공")
        
    except Exception as e:
        pytest.fail(f"❌ 비동기 서비스 테스트 실패: {e}")


if __name__ == "__main__":
    print("🧪 웹 서버 시작 테스트 시작...")
    
    test_web_app_import()
    test_scheduler_service_import()
    test_all_services_available()
    test_scheduler_methods()
    
    # 비동기 테스트 실행
    asyncio.run(test_async_services())
    
    print("✅ 모든 웹 서버 테스트 완료!") 