"""
GA4 권한 관리 시스템 - 웹 서버 메인
==================================

리팩토링된 웹 애플리케이션 진입점
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 라우터 임포트
from .routers import (
    dashboard_router,
    users_router,
    admin_router,
    api_router,
    test_router
)

# 서비스 임포트
from ..infrastructure.database import db_manager
from ..services.property_scanner_service import GA4PropertyScannerService
from ..services.ga4_user_manager import ga4_user_manager
from ..services.notifications.notification_service import notification_service
from ..api.scheduler import scheduler_service
from ..core.logger import get_ga4_logger

logger = get_ga4_logger()

# 전역 서비스 인스턴스
property_scanner: GA4PropertyScannerService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 초기화
    try:
        logger.info("🚀 GA4 권한 관리 시스템 시작")
        
        # 데이터베이스 초기화
        await db_manager.initialize_database()
        logger.info("✅ 데이터베이스 초기화 완료")
        
        # 프로퍼티 스캐너 초기화
        global property_scanner
        property_scanner = GA4PropertyScannerService()
        await property_scanner.initialize()
        logger.info("✅ 프로퍼티 스캐너 초기화 완료")
        
        # 서비스 초기화
        await ga4_user_manager.initialize()
        await notification_service.initialize_system()
        logger.info("✅ 핵심 서비스 초기화 완료")
        
        # 스케줄러 시작 (배포 환경에서만)
        import os
        if os.getenv("ENVIRONMENT") == "production":
            scheduler_service.start_scheduler()
            logger.info("✅ 스케줄러 시작 완료")
        
        logger.info("🎉 시스템 초기화 완료!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 시스템 초기화 실패: {e}")
        raise
    
    finally:
        # 종료 시 정리
        try:
            logger.info("🔄 시스템 종료 중...")
            
            # 스케줄러 중지
            if scheduler_service.is_running:
                scheduler_service.stop_scheduler()
                logger.info("✅ 스케줄러 중지 완료")
            
            # 데이터베이스 연결 정리
            await db_manager.close()
            logger.info("✅ 데이터베이스 연결 정리 완료")
            
            logger.info("👋 시스템 정상 종료")
            
        except Exception as e:
            logger.error(f"❌ 시스템 종료 중 오류: {e}")


# FastAPI 앱 생성
app = FastAPI(
    title="GA4 권한 관리 시스템",
    description="Google Analytics 4 사용자 권한을 자동으로 관리하는 시스템",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# 라우터 등록
app.include_router(dashboard_router, tags=["대시보드"])
app.include_router(users_router, tags=["사용자 관리"])
app.include_router(admin_router, tags=["관리자 설정"])
app.include_router(api_router, tags=["API"])
app.include_router(test_router, tags=["테스트"])


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 에러 핸들러"""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={"error": "페이지를 찾을 수 없습니다", "status_code": 404}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500 에러 핸들러"""
    from fastapi.responses import JSONResponse
    logger.error(f"❌ 내부 서버 오류: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "내부 서버 오류가 발생했습니다", "status_code": 500}
    )


def get_property_scanner():
    """프로퍼티 스캐너 인스턴스 반환 (헬퍼 함수에서 사용)"""
    return property_scanner


# 모듈에 전역 변수로 등록 (기존 코드 호환성)
import sys
sys.modules[__name__].property_scanner = property_scanner


async def main():
    """메인 실행 함수"""
    try:
        config = uvicorn.Config(
            "src.web.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # 프로덕션에서는 False
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"❌ 서버 시작 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 