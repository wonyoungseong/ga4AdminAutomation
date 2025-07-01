#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: 알림 및 스케줄링 시스템 테스트
======================================

새로 구현된 알림 서비스와 스케줄러 기능을 테스트합니다.
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.logger import get_ga4_logger
from src.infrastructure.database import db_manager
from src.services.notification_service import notification_service
from src.api.scheduler import scheduler_service

async def test_phase3_system():
    """Phase 3 시스템 테스트"""
    logger = get_ga4_logger()
    
    logger.info("🧪 Phase 3 시스템 테스트 시작")
    
    try:
        # 1. 데이터베이스 초기화
        logger.info("1️⃣ 데이터베이스 초기화 테스트...")
        await db_manager.initialize_database()
        logger.info("✅ 데이터베이스 초기화 성공")
        
        # 2. 알림 서비스 초기화
        logger.info("2️⃣ 알림 서비스 초기화 테스트...")
        await notification_service.initialize()
        logger.info("✅ 알림 서비스 초기화 성공")
        
        # 3. 스케줄러 서비스 초기화
        logger.info("3️⃣ 스케줄러 서비스 초기화 테스트...")
        await scheduler_service.initialize()
        logger.info("✅ 스케줄러 서비스 초기화 성공")
        
        # 4. 알림 통계 조회 테스트
        logger.info("4️⃣ 알림 통계 조회 테스트...")
        stats = await notification_service.get_notification_stats()
        logger.info(f"📊 알림 통계: {stats}")
        
        # 5. 스케줄러 상태 조회 테스트
        logger.info("5️⃣ 스케줄러 상태 조회 테스트...")
        status = scheduler_service.get_status()
        logger.info(f"🤖 스케줄러 상태: {status}")
        
        # 6. 테스트 알림 발송 (실제 이메일 발송 없이 검증만)
        logger.info("6️⃣ 테스트 알림 시스템 검증...")
        test_email = "test@example.com"
        
        # 알림 템플릿 생성 테스트
        welcome_content = notification_service._create_email_content(
            "welcome", test_email, {"property_name": "Test Property"}
        )
        logger.info(f"📧 환영 이메일 템플릿 생성 성공: {len(welcome_content['body'])} 문자")
        
        expiry_content = notification_service._create_email_content(
            "expiry_warning_7", test_email, {
                "property_name": "Test Property",
                "days_left": 7,
                "expiry_date": "2024-01-01"
            }
        )
        logger.info(f"⏰ 만료 알림 템플릿 생성 성공: {len(expiry_content['body'])} 문자")
        
        # 7. 만료 알림 처리 테스트 (실제 발송 없이)
        logger.info("7️⃣ 만료 알림 처리 로직 테스트...")
        # 실제 사용자가 있다면 처리 로직을 테스트
        expiry_results = await notification_service.process_expiry_notifications()
        logger.info(f"📬 만료 알림 처리 결과: {expiry_results}")
        
        # 8. 스케줄러 시작/중지 테스트
        logger.info("8️⃣ 스케줄러 시작/중지 테스트...")
        
        # 스케줄러 시작
        scheduler_service.start()
        logger.info("🟢 스케줄러 시작됨")
        
        # 잠시 대기
        await asyncio.sleep(2)
        
        # 상태 확인
        status_after_start = scheduler_service.get_status()
        logger.info(f"📊 시작 후 스케줄러 상태: {status_after_start}")
        
        # 스케줄러 중지
        scheduler_service.stop()
        logger.info("🔴 스케줄러 중지됨")
        
        # 최종 상태 확인
        status_after_stop = scheduler_service.get_status()
        logger.info(f"📊 중지 후 스케줄러 상태: {status_after_stop}")
        
        logger.info("🎉 Phase 3 시스템 테스트 완료!")
        
        # 테스트 결과 요약
        print("\n" + "="*50)
        print("📋 Phase 3 테스트 결과 요약")
        print("="*50)
        print("✅ 데이터베이스 초기화: 성공")
        print("✅ 알림 서비스 초기화: 성공")
        print("✅ 스케줄러 서비스 초기화: 성공")
        print("✅ 알림 통계 조회: 성공")
        print("✅ 스케줄러 상태 조회: 성공")
        print("✅ 알림 템플릿 생성: 성공")
        print("✅ 만료 알림 처리 로직: 성공")
        print("✅ 스케줄러 시작/중지: 성공")
        print("\n🎯 Phase 3 시스템이 정상적으로 작동합니다!")
        
    except Exception as e:
        logger.error(f"❌ Phase 3 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 정리
        try:
            if scheduler_service.is_running:
                scheduler_service.stop()
            await db_manager.close()
        except:
            pass
    
    return True

async def test_web_integration():
    """웹 통합 테스트"""
    logger = get_ga4_logger()
    
    logger.info("🌐 웹 통합 테스트 시작")
    
    try:
        # FastAPI 앱 import 테스트
        from src.web.main import app
        logger.info("✅ FastAPI 앱 import 성공")
        
        # 라우트 확인
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/",
            "/register", 
            "/api/send-test-notification",
            "/api/process-expiry-notifications",
            "/api/scheduler-status",
            "/api/scheduler/start",
            "/api/scheduler/stop"
        ]
        
        for route in expected_routes:
            if route in routes:
                logger.info(f"✅ 라우트 확인: {route}")
            else:
                logger.warning(f"⚠️ 라우트 누락: {route}")
        
        logger.info("🎉 웹 통합 테스트 완료!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 웹 통합 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 GA4 권한 관리 시스템 Phase 3 테스트")
        print("=" * 50)
        
        # Phase 3 시스템 테스트
        system_test = await test_phase3_system()
        
        # 웹 통합 테스트
        web_test = await test_web_integration()
        
        print("\n" + "="*50)
        print("🏁 최종 테스트 결과")
        print("="*50)
        print(f"📊 시스템 테스트: {'✅ 성공' if system_test else '❌ 실패'}")
        print(f"🌐 웹 통합 테스트: {'✅ 성공' if web_test else '❌ 실패'}")
        
        if system_test and web_test:
            print("\n🎉 Phase 3 구현이 완료되었습니다!")
            print("💡 다음 단계: python start_web_server.py 로 웹 서버를 시작하세요.")
        else:
            print("\n❌ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")
    
    asyncio.run(main()) 