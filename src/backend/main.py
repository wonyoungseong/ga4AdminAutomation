"""
GA4 Admin Automation - FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from src.backend.core.config import get_settings, Settings
from src.backend.core.database import get_db, DatabaseService
from src.backend.core.middleware import (
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware
)
from src.backend.api.routers import users, admin, auth, ga4, permissions

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="GA4 Admin Automation API",
    description="Google Analytics 4 관리자 권한 자동화 시스템",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


def setup_middleware(app: FastAPI, settings: Settings):
    """모든 미들웨어 설정"""
    
    # 1. 로깅 미들웨어 (가장 바깥쪽)
    app.add_middleware(LoggingMiddleware)
    
    # 2. 요청 ID 미들웨어
    app.add_middleware(RequestIDMiddleware)
    
    # 3. 속도 제한 미들웨어 (개발 환경에서만)
    if settings.debug:
        app.add_middleware(RateLimitMiddleware, max_requests=1000, window_seconds=60)
    
    # 4. 보안 헤더 미들웨어
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 5. CORS 미들웨어 (가장 안쪽)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )


# 모든 미들웨어 설정을 앱 시작 시 바로 적용
settings = get_settings()
setup_middleware(app, settings)

# API 라우터 등록
app.include_router(users.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ga4.router, prefix="/api/v1")
app.include_router(permissions.router, prefix="/api/v1")

# 애플리케이션 시작 시 실행되는 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화 작업"""
    print(f"🚀 {settings.app_name} v{settings.app_version} 시작됨")
    print(f"🌐 문서: http://{settings.host}:{settings.port}/docs")


# 기본 헬스체크 엔드포인트
@app.get("/")
async def root():
    """기본 루트 엔드포인트"""
    return {
        "message": "GA4 Admin Automation API",
        "status": "healthy",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """상세한 헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production"
    }


@app.get("/api/v1/status")
async def api_status():
    """API 상태 확인 엔드포인트"""
    return {
        "api_status": "active",
        "api_version": "v1",
        "timestamp": "2025-01-01T00:00:00Z"
    }


@app.get("/api/v1/database/test")
async def test_database_connection(db: DatabaseService = Depends(get_db)):
    """데이터베이스 연결 테스트 엔드포인트"""
    return await db.test_connection()


@app.get("/api/v1/database/tables")
async def get_database_tables(db: DatabaseService = Depends(get_db)):
    """데이터베이스 테이블 정보 조회 엔드포인트"""
    return await db.get_table_info()


# 개선된 예외 처리 핸들러들
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 Not Found 처리"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "요청한 리소스를 찾을 수 없습니다.",
            "path": str(request.url.path),
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """입력 검증 오류 처리"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "입력 데이터에 오류가 있습니다.",
            "details": exc.errors() if hasattr(exc, 'errors') else str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    import traceback
    
    # 로깅
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {str(exc)}")
    if get_settings().debug:
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "서버에서 오류가 발생했습니다.",
            "detail": str(exc) if get_settings().debug else "자세한 정보는 관리자에게 문의하세요.",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


if __name__ == "__main__":
    # 개발 서버 실행
    settings = get_settings()
    uvicorn.run(
        "src.backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    ) 