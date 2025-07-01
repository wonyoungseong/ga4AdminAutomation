"""
Supabase 데이터베이스 연동 모듈
FastAPI에서 Supabase와의 연결 및 데이터 처리를 담당합니다.
"""

from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from functools import lru_cache
import logging

from .config import get_settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_supabase_client() -> Client:
    """
    Supabase 클라이언트 인스턴스를 반환합니다.
    LRU 캐시를 사용하여 싱글톤 패턴으로 관리됩니다.
    """
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise ValueError("Supabase 설정이 누락되었습니다. 환경 변수를 확인하세요.")
    
    try:
        client = create_client(settings.supabase_url, settings.supabase_anon_key)
        logger.info("✅ Supabase 클라이언트 연결 성공")
        return client
    except Exception as e:
        logger.error(f"❌ Supabase 클라이언트 연결 실패: {str(e)}")
        raise


class DatabaseService:
    """데이터베이스 서비스 클래스"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    async def test_connection(self) -> Dict[str, Any]:
        """데이터베이스 연결 테스트"""
        try:
            # 간단한 쿼리로 연결 확인
            result = self.client.table("website_users").select("count", count="exact").execute()
            
            return {
                "status": "connected",
                "message": "Supabase 연결 성공",
                "user_count": result.count,
                "timestamp": "2025-01-01T12:00:00Z"
            }
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {str(e)}")
            return {
                "status": "error",
                "message": f"연결 실패: {str(e)}",
                "timestamp": "2025-01-01T12:00:00Z"
            }
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """모든 사용자 목록 조회"""
        try:
            # 사용자 목록 조회
            response = self.client.table("website_users").select("*").range(offset, offset + limit - 1).execute()
            
            # 전체 개수 조회
            count_response = self.client.table("website_users").select("count", count="exact").execute()
            
            return {
                "users": response.data,
                "total_count": count_response.count,
                "offset": offset,
                "limit": limit
            }
        except Exception as e:
            logger.error(f"사용자 목록 조회 실패: {str(e)}")
            raise Exception(f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """특정 사용자 조회"""
        try:
            response = self.client.table("website_users").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"사용자 조회 실패 (ID: {user_id}): {str(e)}")
            raise Exception(f"사용자 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 사용자 생성"""
        try:
            response = self.client.table("website_users").insert(user_data).execute()
            
            if response.data:
                logger.info(f"새 사용자 생성 성공: {response.data[0]['email']}")
                return response.data[0]
            
            raise Exception("사용자 생성에 실패했습니다")
        except Exception as e:
            logger.error(f"사용자 생성 실패: {str(e)}")
            raise Exception(f"사용자 생성 중 오류가 발생했습니다: {str(e)}")
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """관리자 대시보드 통계 조회"""
        try:
            # 각 테이블의 레코드 수 조회
            users_count = self.client.table("website_users").select("count", count="exact").execute()
            clients_count = self.client.table("clients").select("count", count="exact").execute()
            permissions_count = self.client.table("permission_grants").select("count", count="exact").execute()
            
            # 활성 권한 수 조회
            active_permissions = self.client.table("permission_grants").select("count", count="exact").eq("status", "active").execute()
            
            return {
                "total_users": users_count.count,
                "total_clients": clients_count.count,
                "total_permissions": permissions_count.count,
                "active_permissions": active_permissions.count,
                "pending_approvals": 0,  # TODO: 실제 승인 대기 로직 구현
                "expiring_soon": 0  # TODO: 실제 만료 예정 로직 구현
            }
        except Exception as e:
            logger.error(f"대시보드 통계 조회 실패: {str(e)}")
            raise Exception(f"통계 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def get_table_info(self) -> Dict[str, Any]:
        """모든 테이블의 기본 정보 조회"""
        try:
            tables = ["website_users", "clients", "service_accounts", "permission_grants", "audit_logs"]
            table_info = {}
            
            for table in tables:
                try:
                    count_response = self.client.table(table).select("count", count="exact").execute()
                    table_info[table] = {
                        "count": count_response.count,
                        "status": "accessible"
                    }
                except Exception as e:
                    table_info[table] = {
                        "count": 0,
                        "status": f"error: {str(e)}"
                    }
            
            return {
                "tables": table_info,
                "total_tables": len(tables),
                "accessible_tables": len([t for t in table_info.values() if t["status"] == "accessible"])
            }
        except Exception as e:
            logger.error(f"테이블 정보 조회 실패: {str(e)}")
            raise Exception(f"테이블 정보 조회 중 오류가 발생했습니다: {str(e)}")


# 전역 데이터베이스 서비스 인스턴스
@lru_cache()
def get_database_service() -> DatabaseService:
    """데이터베이스 서비스 싱글톤 인스턴스 반환"""
    return DatabaseService()


# FastAPI 의존성으로 사용할 함수
def get_db() -> DatabaseService:
    """FastAPI 의존성 주입용 데이터베이스 서비스 반환"""
    return get_database_service() 