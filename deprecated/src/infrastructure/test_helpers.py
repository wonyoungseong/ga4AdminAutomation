"""
테스트 헬퍼 함수들

테스트 파일들에서 공통으로 사용되는 기능들을 제공합니다.
"""

import asyncio
from typing import Optional, Tuple
from ..infrastructure.database import DatabaseManager
from ..services.ga4_user_manager import GA4UserManager
from ..services.property_scanner_service import GA4PropertyScannerService
from ..services.notifications.notification_service import NotificationService
from ..api.scheduler import GA4Scheduler
from ..core.ga4_automation import GA4AutomationSystem
from ..core.logger import get_ga4_logger

# 전역 인스턴스들
db_manager = DatabaseManager()
ga4_user_manager = GA4UserManager()
property_scanner = GA4PropertyScannerService()


async def initialize_systems():
    """
    모든 시스템 컴포넌트 초기화
    
    Returns:
        Tuple: (db_manager, ga4_core, property_scanner, user_manager, notification_service, scheduler)
    """
    logger = get_ga4_logger()
    logger.info("🚀 전체 시스템 초기화 중...")
    
    try:
        # 1. 데이터베이스 초기화
        await db_manager.initialize_database()
        logger.info("✅ 데이터베이스 초기화 완료")
        
        # 2. GA4 코어 시스템 초기화
        ga4_core = GA4AutomationSystem()
        await ga4_core.initialize()
        logger.info("✅ GA4 코어 시스템 초기화 완료")
        
        # 3. 프로퍼티 스캐너 초기화
        await property_scanner.initialize()
        logger.info("✅ 프로퍼티 스캐너 초기화 완료")
        
        # 4. 사용자 관리자 초기화
        await ga4_user_manager.initialize()
        logger.info("✅ 사용자 관리자 초기화 완료")
        
        # 5. 알림 서비스 초기화
        notification_service = NotificationService()
        await notification_service.initialize()
        logger.info("✅ 알림 서비스 초기화 완료")
        
        # 6. 스케줄러 초기화
        scheduler = GA4Scheduler()
        await scheduler.initialize()
        logger.info("✅ 스케줄러 초기화 완료")
        
        logger.info("🎉 모든 시스템 컴포넌트 초기화 완료")
        
        return db_manager, ga4_core, property_scanner, ga4_user_manager, notification_service, scheduler
        
    except Exception as e:
        logger.error(f"❌ 시스템 초기화 실패: {e}")
        raise


async def initialize_test_systems() -> Tuple[bool, str]:
    """
    테스트용 시스템 초기화
    
    Returns:
        Tuple[bool, str]: (성공 여부, 메시지)
    """
    logger = get_ga4_logger()
    logger.info("📋 테스트 시스템 초기화 중...")
    
    try:
        # 데이터베이스 초기화
        await db_manager.initialize_database()
        logger.info("✅ 데이터베이스 초기화 완료")
        
        # GA4 사용자 관리자 초기화
        await ga4_user_manager.initialize()
        logger.info("✅ GA4 사용자 관리자 초기화 완료")
        
        logger.info("✅ 모든 테스트 시스템 초기화 완료")
        return True, "시스템 초기화 성공"
        
    except Exception as e:
        error_msg = f"시스템 초기화 실패: {e}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg


async def get_test_property() -> Optional[dict]:
    """
    테스트용 프로퍼티 조회
    
    Returns:
        Optional[dict]: 프로퍼티 정보 또는 None
    """
    logger = get_ga4_logger()
    
    try:
        # 프로퍼티 스캔
        await property_scanner.scan_all_accounts_and_properties()
        
        # 등록 가능한 프로퍼티 조회
        properties = await db_manager.execute_query(
            "SELECT * FROM ga4_properties WHERE 등록_가능여부 = 1 ORDER BY property_display_name LIMIT 1"
        )
        
        if properties:
            prop = properties[0]
            logger.info(f"🎯 테스트 프로퍼티: {prop['property_display_name']} ({prop['property_id']})")
            return prop
        else:
            logger.warning("⚠️ 테스트 가능한 프로퍼티가 없습니다")
            return None
            
    except Exception as e:
        logger.error(f"❌ 테스트 프로퍼티 조회 실패: {e}")
        return None


async def cleanup_test_users(property_id: str, test_emails: list) -> None:
    """
    테스트 사용자들 정리
    
    Args:
        property_id: 프로퍼티 ID
        test_emails: 정리할 이메일 목록
    """
    logger = get_ga4_logger()
    logger.info("🧹 테스트 사용자 정리 중...")
    
    for email in test_emails:
        try:
            success, message = await ga4_user_manager.remove_user_from_property(
                property_id, email
            )
            if success:
                logger.info(f"✅ 정리 완료: {email}")
            else:
                logger.warning(f"⚠️ 정리 실패: {email} - {message}")
                
            await asyncio.sleep(1)  # API 제한 고려
            
        except Exception as e:
            logger.error(f"❌ 정리 오류: {email} - {e}") 