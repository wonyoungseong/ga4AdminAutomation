#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
종합 QA 테스트
=============

모든 오류가 해결되었는지 종합적으로 테스트
"""

import sys
import os
import asyncio
import requests
import time
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_all_imports():
    """모든 중요 모듈 import 테스트"""
    try:
        print("🔧 모듈 Import 테스트...")
        
        # 핵심 모듈들
        from src.web.main import app, get_dashboard_data
        from src.api.scheduler import scheduler_service, ga4_scheduler, GA4Scheduler
        from src.services.notification_service import NotificationService
        from src.services.ga4_user_manager import GA4UserManager
        from src.services.property_scanner_service import GA4PropertyScannerService
        from src.infrastructure.database import db_manager, DatabaseManager
        from src.core.logger import get_ga4_logger
        
        print("✅ 모든 핵심 모듈 import 성공")
        return True
        
    except Exception as e:
        print(f"❌ 모듈 import 실패: {e}")
        return False


async def test_service_initialization():
    """서비스 초기화 테스트"""
    try:
        print("🔧 서비스 초기화 테스트...")
        
        from src.api.scheduler import GA4Scheduler
        from src.services.notification_service import NotificationService
        from src.services.ga4_user_manager import GA4UserManager
        from src.services.property_scanner_service import GA4PropertyScannerService
        from src.infrastructure.database import DatabaseManager
        
        # 각 서비스 초기화
        scheduler = GA4Scheduler()
        await scheduler.initialize()
        print("  ✅ 스케줄러 초기화 성공")
        
        notification_service = NotificationService()
        await notification_service.initialize()
        print("  ✅ 알림 서비스 초기화 성공")
        
        user_manager = GA4UserManager()
        await user_manager.initialize()
        print("  ✅ 사용자 관리 서비스 초기화 성공")
        
        property_scanner = GA4PropertyScannerService()
        print("  ✅ 프로퍼티 스캐너 서비스 초기화 성공")
        
        db_manager = DatabaseManager()
        await db_manager.initialize_database()
        print("  ✅ 데이터베이스 관리자 초기화 성공")
        
        print("✅ 모든 서비스 초기화 성공")
        return True
        
    except Exception as e:
        print(f"❌ 서비스 초기화 실패: {e}")
        return False


async def test_required_methods():
    """필수 메서드 존재 확인"""
    try:
        print("🔧 필수 메서드 존재 확인...")
        
        from src.api.scheduler import GA4Scheduler
        from src.services.notification_service import NotificationService
        
        # GA4Scheduler 메서드 확인
        scheduler = GA4Scheduler()
        required_scheduler_methods = ['initialize', 'start_scheduler', 'stop_scheduler']
        for method in required_scheduler_methods:
            assert hasattr(scheduler, method), f"GA4Scheduler에 {method} 메서드가 없습니다"
            assert callable(getattr(scheduler, method)), f"{method}가 호출 가능하지 않습니다"
        
        # NotificationService 메서드 확인
        notification_service = NotificationService()
        required_notification_methods = ['send_notification', 'process_expiry_notifications', 'initialize']
        for method in required_notification_methods:
            assert hasattr(notification_service, method), f"NotificationService에 {method} 메서드가 없습니다"
            assert callable(getattr(notification_service, method)), f"{method}가 호출 가능하지 않습니다"
        
        print("✅ 모든 필수 메서드 존재 확인 완료")
        return True
        
    except Exception as e:
        print(f"❌ 필수 메서드 확인 실패: {e}")
        return False


def test_web_server_response():
    """웹 서버 응답 테스트"""
    try:
        print("🔧 웹 서버 응답 테스트...")
        
        # 메인 페이지 테스트
        response = requests.get("http://localhost:8000/", timeout=10)
        assert response.status_code == 200, f"메인 페이지 응답 오류: {response.status_code}"
        
        # HTML 내용 확인
        html_content = response.text
        required_elements = ['GA4 권한 관리', 'dashboard', 'Bootstrap']
        for element in required_elements:
            assert element in html_content, f"HTML에 '{element}' 요소가 없습니다"
        
        # 등록 페이지 테스트
        response = requests.get("http://localhost:8000/register", timeout=10)
        assert response.status_code == 200, f"등록 페이지 응답 오류: {response.status_code}"
        
        print("✅ 웹 서버 응답 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 웹 서버 응답 테스트 실패: {e}")
        return False


async def test_dashboard_data():
    """대시보드 데이터 테스트"""
    try:
        print("🔧 대시보드 데이터 테스트...")
        
        from src.web.main import get_dashboard_data
        
        dashboard_data = await get_dashboard_data()
        
        # 필수 키 확인
        required_keys = ['properties', 'registrations', 'stats', 'notification_stats', 'recent_logs']
        for key in required_keys:
            assert key in dashboard_data, f"대시보드 데이터에 '{key}' 키가 없습니다"
        
        # 데이터 타입 확인
        assert isinstance(dashboard_data['properties'], list), "properties는 list 타입이어야 합니다"
        assert isinstance(dashboard_data['registrations'], list), "registrations는 list 타입이어야 합니다"
        assert isinstance(dashboard_data['stats'], dict), "stats는 dict 타입이어야 합니다"
        
        print("✅ 대시보드 데이터 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 대시보드 데이터 테스트 실패: {e}")
        return False


def run_all_qa_tests():
    """모든 QA 테스트 실행"""
    print("🎯 GA4 권한 관리 시스템 종합 QA 테스트 시작")
    print("=" * 60)
    
    start_time = time.time()
    
    # 비동기 테스트들
    test1 = asyncio.run(test_all_imports())
    test2 = asyncio.run(test_service_initialization())
    test3 = asyncio.run(test_required_methods())
    test4 = asyncio.run(test_dashboard_data())
    
    # 동기 테스트들
    test5 = test_web_server_response()
    
    end_time = time.time()
    
    print("=" * 60)
    
    # 결과 요약
    total_tests = 5
    passed_tests = sum([test1, test2, test3, test4, test5])
    
    print(f"📊 테스트 결과 요약:")
    print(f"   총 테스트: {total_tests}개")
    print(f"   성공: {passed_tests}개")
    print(f"   실패: {total_tests - passed_tests}개")
    print(f"   소요 시간: {end_time - start_time:.2f}초")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트 통과! 시스템이 정상적으로 작동합니다.")
        print("\n✅ 해결된 주요 문제들:")
        print("   - NotificationService.send_notification 메서드 추가")
        print("   - GA4Scheduler.initialize 메서드 추가")
        print("   - scheduler_service 별칭 추가")
        print("   - 데이터베이스 스키마 업데이트")
        print("   - 대시보드 템플릿에 'dashboard' 클래스 추가")
        print("   - get_dashboard_data 함수 추가")
        print("   - 웹 서버 정상 작동 확인")
        return True
    else:
        print("❌ 일부 테스트 실패. 추가 수정이 필요합니다.")
        return False


if __name__ == "__main__":
    success = run_all_qa_tests()
    sys.exit(0 if success else 1) 