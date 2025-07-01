#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import 및 메서드 오류 수정 테스트
===============================

현재 발생하는 오류들을 테스트하고 수정
"""

import pytest
import sys
import os
import asyncio

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_notification_service_methods():
    """NotificationService 메서드 존재 확인"""
    try:
        from src.services.notification_service import NotificationService
        
        service = NotificationService()
        
        # 필요한 메서드들이 있는지 확인
        required_methods = [
            'process_expiry_notifications',
            'check_and_send_expiry_warnings',
            'send_notification'
        ]
        
        for method_name in required_methods:
            assert hasattr(service, method_name), f"NotificationService에 {method_name} 메서드가 없습니다"
            assert callable(getattr(service, method_name)), f"{method_name}가 호출 가능하지 않습니다"
        
        print("✅ NotificationService 메서드 확인 완료")
        return True
        
    except Exception as e:
        print(f"❌ NotificationService 메서드 확인 실패: {e}")
        return False


def test_scheduler_methods():
    """GA4Scheduler 메서드 존재 확인"""
    try:
        from src.api.scheduler import GA4Scheduler
        
        scheduler = GA4Scheduler()
        
        # 필요한 메서드들이 있는지 확인
        required_methods = [
            'initialize',
            'start_scheduler',
            'stop_scheduler'
        ]
        
        for method_name in required_methods:
            assert hasattr(scheduler, method_name), f"GA4Scheduler에 {method_name} 메서드가 없습니다"
            assert callable(getattr(scheduler, method_name)), f"{method_name}가 호출 가능하지 않습니다"
        
        print("✅ GA4Scheduler 메서드 확인 완료")
        return True
        
    except Exception as e:
        print(f"❌ GA4Scheduler 메서드 확인 실패: {e}")
        return False


async def test_async_initialization():
    """비동기 초기화 테스트"""
    try:
        from src.api.scheduler import GA4Scheduler
        from src.services.notification_service import NotificationService
        
        # 스케줄러 초기화
        scheduler = GA4Scheduler()
        await scheduler.initialize()
        print("✅ 스케줄러 초기화 성공")
        
        # 알림 서비스 초기화
        notification_service = NotificationService()
        await notification_service.initialize()
        print("✅ 알림 서비스 초기화 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 비동기 초기화 실패: {e}")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("🔧 Import 및 메서드 오류 수정 테스트 시작...")
    
    # 동기 테스트들
    test1 = test_notification_service_methods()
    test2 = test_scheduler_methods()
    
    # 비동기 테스트
    test3 = asyncio.run(test_async_initialization())
    
    if all([test1, test2, test3]):
        print("🎉 모든 테스트 통과!")
        return True
    else:
        print("❌ 일부 테스트 실패")
        return False


if __name__ == "__main__":
    run_all_tests() 