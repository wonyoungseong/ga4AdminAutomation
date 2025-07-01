"""
테스트 라우터
===========

테스트 및 디버그 관련 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime

from src.infrastructure.database import db_manager
from ...core.logger import get_ga4_logger
from ..utils.formatters import format_api_response

logger = get_ga4_logger()
router = APIRouter()
templates = Jinja2Templates(directory="src/web/templates")


@router.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """테스트 페이지"""
    try:
        return templates.TemplateResponse("test_js.html", {
            "request": request
        })
    except Exception as e:
        logger.error(f"❌ 테스트 페이지 로드 실패: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다")


@router.get("/debug", response_class=HTMLResponse)
async def debug_page(request: Request):
    """디버그 페이지"""
    try:
        return templates.TemplateResponse("debug_stats.html", {
            "request": request
        })
    except Exception as e:
        logger.error(f"❌ 디버그 페이지 로드 실패: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다")


@router.get("/api/test/health")
async def health_check():
    """헬스 체크 API"""
    try:
        # 데이터베이스 연결 테스트
        test_query = await db_manager.execute_query("SELECT 1 as test")
        
        return format_api_response(
            success=True,
            message="시스템이 정상 작동 중입니다",
            data={
                "timestamp": datetime.now().isoformat(),
                "database": "connected" if test_query else "disconnected",
                "status": "healthy"
            }
        )
    except Exception as e:
        logger.error(f"❌ 헬스 체크 실패: {e}")
        return format_api_response(
            success=False,
            message=f"시스템 오류: {str(e)}",
            data={
                "timestamp": datetime.now().isoformat(),
                "status": "unhealthy"
            }
        )


@router.get("/api/test/database")
async def test_database():
    """데이터베이스 연결 테스트"""
    try:
        # 각 테이블 테스트
        results = {}
        
        # 사용자 등록 테이블
        user_count = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM user_registrations"
        )
        results["user_registrations"] = user_count[0]["count"] if user_count else 0
        
        # GA4 계정 테이블
        account_count = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM ga4_accounts WHERE 삭제여부 = 0"
        )
        results["ga4_accounts"] = account_count[0]["count"] if account_count else 0
        
        # GA4 프로퍼티 테이블
        property_count = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM ga4_properties WHERE 삭제여부 = 0"
        )
        results["ga4_properties"] = property_count[0]["count"] if property_count else 0
        
        return format_api_response(
            success=True,
            data={
                "timestamp": datetime.now().isoformat(),
                "table_counts": results,
                "status": "all_tables_accessible"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 테스트 실패: {e}")
        return format_api_response(
            success=False,
            message=str(e),
            data={"timestamp": datetime.now().isoformat()}
        )


@router.get("/api/test/logs")
async def get_recent_logs():
    """최근 로그 조회"""
    try:
        # 최근 감사 로그 조회 (있는 경우)
        logs = await db_manager.execute_query(
            """SELECT * FROM audit_logs 
               ORDER BY created_at DESC 
               LIMIT 10"""
        )
        
        return format_api_response(
            success=True,
            data={
                "recent_logs": logs or [],
                "count": len(logs) if logs else 0,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        # 테이블이 없을 수도 있으므로 warning으로 처리
        logger.warning(f"⚠️ 로그 테이블 접근 실패 (정상일 수 있음): {e}")
        return format_api_response(
            success=True,
            data={
                "recent_logs": [],
                "count": 0,
                "message": "로그 테이블이 없거나 접근할 수 없습니다",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/api/test/sample-data")
async def create_sample_data():
    """샘플 데이터 생성 (개발용)"""
    try:
        sample_data_created = 0
        
        # 샘플 사용자 등록 데이터 생성
        sample_users = [
            {
                "신청자": "테스트 관리자",
                "등록_계정": "test@example.com",
                "property_id": "123456789",
                "권한": "viewer",
                "status": "active"
            },
            {
                "신청자": "테스트 분석가",
                "등록_계정": "analyst@example.com",
                "property_id": "123456789",
                "권한": "analyst",
                "status": "active"
            }
        ]
        
        for user in sample_users:
            # 중복 체크
            existing = await db_manager.execute_query(
                """SELECT id FROM user_registrations 
                   WHERE 등록_계정 = ? AND property_id = ?""",
                (user["등록_계정"], user["property_id"])
            )
            
            if not existing:
                await db_manager.execute_insert(
                    """INSERT INTO user_registrations 
                       (신청자, 등록_계정, property_id, 권한, 신청일, status, ga4_registered)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user["신청자"], user["등록_계정"], user["property_id"],
                        user["권한"], datetime.now(), user["status"], 0
                    )
                )
                sample_data_created += 1
        
        return format_api_response(
            success=True,
            message=f"샘플 데이터 {sample_data_created}개 생성 완료",
            data={
                "created_count": sample_data_created,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 샘플 데이터 생성 실패: {e}")
        return format_api_response(
            success=False,
            message=str(e)
        )


@router.delete("/api/test/clean-sample-data")
async def clean_sample_data():
    """샘플 데이터 정리 (개발용)"""
    try:
        # 테스트 데이터 삭제
        deleted_count = await db_manager.execute_update(
            """DELETE FROM user_registrations 
               WHERE 등록_계정 LIKE '%@example.com' 
               OR 신청자 LIKE '테스트%'"""
        )
        
        return format_api_response(
            success=True,
            message=f"샘플 데이터 {deleted_count}개 정리 완료",
            data={
                "deleted_count": deleted_count,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 샘플 데이터 정리 실패: {e}")
        return format_api_response(
            success=False,
            message=str(e)
        )


@router.get("/api/test/config")
async def get_test_config():
    """테스트 설정 조회"""
    try:
        import os
        
        config_info = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug_mode": os.getenv("DEBUG", "False").lower() == "true",
            "database_url": "configured" if os.getenv("DATABASE_URL") else "not_configured",
            "service_account": "configured" if os.path.exists("config/ga4-automatio-797ec352f393.json") else "not_configured",
            "current_time": datetime.now().isoformat()
        }
        
        return format_api_response(
            success=True,
            data=config_info
        )
        
    except Exception as e:
        logger.error(f"❌ 테스트 설정 조회 실패: {e}")
        return format_api_response(
            success=False,
            message=str(e)
        ) 