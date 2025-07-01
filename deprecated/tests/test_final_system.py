#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 시스템 테스트
================

모든 오류가 수정되었는지 최종 확인
"""

import sys
import os
import asyncio
import uvicorn
from threading import Thread
import time

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_all_components():
    """모든 컴포넌트 테스트"""
    print("🔧 GA4 권한 관리 시스템 최종 테스트 시작...")
    
    try:
        # 1. 모든 모듈 import 테스트
        print("\n1️⃣ 모듈 Import 테스트...")
        from src.web.main import app
        from src.api.scheduler import scheduler_service, ga4_scheduler
        from src.infrastructure.database import db_manager
        from src.services.notification_service import NotificationService
        from src.services.ga4_user_manager import GA4UserManager
        print("✅ 모든 모듈 import 성공")
        
        # 2. 데이터베이스 초기화 테스트
        print("\n2️⃣ 데이터베이스 초기화 테스트...")
        await db_manager.initialize_database()
        print("✅ 데이터베이스 초기화 성공")
        
        # 3. 스케줄러 초기화 테스트
        print("\n3️⃣ 스케줄러 초기화 테스트...")
        await scheduler_service.initialize()
        print("✅ 스케줄러 초기화 성공")
        
        # 4. 알림 서비스 테스트
        print("\n4️⃣ 알림 서비스 테스트...")
        notification_service = NotificationService()
        await notification_service.initialize()
        print("✅ 알림 서비스 초기화 성공")
        
        # 5. GA4 사용자 관리 서비스 테스트
        print("\n5️⃣ GA4 사용자 관리 서비스 테스트...")
        ga4_user_manager = GA4UserManager()
        await ga4_user_manager.initialize()
        print("✅ GA4 사용자 관리 서비스 초기화 성공")
        
        # 6. 웹 앱 기본 구조 테스트
        print("\n6️⃣ 웹 앱 구조 테스트...")
        assert app is not None
        assert hasattr(app, 'routes')
        print(f"✅ 웹 앱 구조 정상 - 등록된 라우트 수: {len(app.routes)}")
        
        # 7. 스케줄러 상태 테스트
        print("\n7️⃣ 스케줄러 상태 테스트...")
        status = scheduler_service.get_scheduler_status()
        print(f"✅ 스케줄러 상태: {status}")
        
        print("\n🎉 모든 테스트 통과! 시스템이 정상적으로 작동합니다.")
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_server_startup():
    """웹 서버 시작 테스트"""
    print("\n8️⃣ 웹 서버 시작 테스트...")
    
    try:
        from src.web.main import app
        
        # 웹 서버를 별도 스레드에서 시작
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")
        
        server_thread = Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # 서버 시작 대기
        time.sleep(3)
        
        # 서버 응답 테스트
        import requests
        try:
            response = requests.get("http://127.0.0.1:8001/", timeout=5)
            if response.status_code == 200:
                print("✅ 웹 서버 정상 작동 확인")
                return True
            else:
                print(f"⚠️ 웹 서버 응답 코드: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 웹 서버 연결 실패: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 웹 서버 시작 실패: {e}")
        return False


async def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("🚀 GA4 권한 관리 시스템 - 최종 통합 테스트")
    print("=" * 60)
    
    # 비동기 컴포넌트 테스트
    component_test_result = await test_all_components()
    
    # 웹 서버 테스트
    web_server_test_result = test_web_server_startup()
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"컴포넌트 테스트: {'✅ 통과' if component_test_result else '❌ 실패'}")
    print(f"웹 서버 테스트: {'✅ 통과' if web_server_test_result else '❌ 실패'}")
    
    if component_test_result and web_server_test_result:
        print("\n🎉 모든 테스트 통과! 시스템이 완전히 정상 작동합니다.")
        print("🌐 웹 서버 접속: http://localhost:8000")
        return True
    else:
        print("\n❌ 일부 테스트 실패. 문제를 해결해야 합니다.")
        return False


if __name__ == "__main__":
    asyncio.run(main()) 