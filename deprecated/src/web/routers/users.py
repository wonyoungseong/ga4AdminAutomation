"""
사용자 관리 라우터
===============

사용자 목록, 사용자 관리 API 등을 제공합니다.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from typing import Optional
from datetime import datetime, timedelta
import io

from src.infrastructure.database import db_manager
from ...services.ga4_user_manager import ga4_user_manager
from ...core.logger import get_ga4_logger
from ..utils.formatters import format_api_response, format_csv_data, format_pagination_data

logger = get_ga4_logger()
router = APIRouter()
templates = Jinja2Templates(directory="src/web/templates")


@router.get("/users", response_class=HTMLResponse)
async def users_list_page(request: Request):
    """사용자 목록 페이지"""
    try:
        return templates.TemplateResponse("users_list.html", {
            "request": request
        })
    except Exception as e:
        logger.error(f"❌ 사용자 목록 페이지 로드 실패: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다")


@router.get("/api/users")
async def get_users_list(
    status: Optional[str] = None,
    permission: Optional[str] = None,
    account_id: Optional[str] = None,
    property_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
):
    """사용자 목록 조회 API (필터링 및 페이징 지원)"""
    try:
        # 🔍 디버깅: 요청 파라미터 로그
        logger.info(f"🔍 [사용자 목록 조회] 요청 파라미터:")
        logger.info(f"   - status: {status}")
        logger.info(f"   - permission: {permission}")
        logger.info(f"   - account_id: {account_id}")
        logger.info(f"   - property_id: {property_id}")
        logger.info(f"   - start_date: {start_date}")
        logger.info(f"   - end_date: {end_date}")
        logger.info(f"   - search: {search}")
        logger.info(f"   - page: {page}")
        logger.info(f"   - per_page: {per_page}")
        # 기본 쿼리
        base_query = """
            SELECT 
                ur.id,
                ur.신청자 as applicant,
                ur.등록_계정 as user_email,
                ur.property_id,
                ur.권한 as permission_level,
                ur.status,
                ur.ga4_registered,
                ur.created_at,
                ur.expiry_date,
                ur.연장_횟수 as extension_count,
                p.property_display_name as property_name,
                a.account_display_name as account_name
            FROM user_registrations ur
            LEFT JOIN ga4_properties p ON ur.property_id = p.property_id
            LEFT JOIN ga4_accounts a ON p.account_id = a.account_id
        """
        
        conditions = []
        params = []
        
        # 기본 필터: deleted 상태 제외 (status 파라미터가 명시적으로 제공되지 않은 경우)
        if not status:
            conditions.append("ur.status != 'deleted'")
        
        # 필터 조건 추가
        if status:
            conditions.append("ur.status = ?")
            params.append(status)
            
        if permission:
            conditions.append("ur.권한 = ?")
            params.append(permission)
            
        if account_id:
            conditions.append("a.account_id = ?")
            params.append(account_id)
            
        if property_id:
            conditions.append("ur.property_id = ?")
            params.append(property_id)
            
        if start_date:
            conditions.append("DATE(ur.created_at) >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("DATE(ur.created_at) <= ?")
            params.append(end_date)
            
        if search:
            conditions.append("""
                (ur.신청자 LIKE ? OR 
                 ur.등록_계정 LIKE ? OR 
                 p.property_display_name LIKE ?)
            """)
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # WHERE 절 추가
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # 전체 개수 조회
        count_query = f"""
            SELECT COUNT(*) as total
            FROM ({base_query}) as filtered_results
        """
        
        count_result = await db_manager.execute_query(count_query, params)
        total = count_result[0]['total'] if count_result else 0
        
        # 페이징 적용
        offset = (page - 1) * per_page
        paginated_query = f"{base_query} ORDER BY ur.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        # 데이터 조회
        logger.info(f"🔍 [쿼리 실행] 페이징 쿼리 실행 중...")
        users = await db_manager.execute_query(paginated_query, params)
        logger.info(f"🔍 [쿼리 결과] 조회된 사용자 수: {len(users)}")
        
        # 사용자 목록 상세 로그 (처음 3명만)
        for i, user in enumerate(users[:3]):
            logger.info(f"🔍 [사용자 {i+1}] {user.get('user_email')} - {user.get('status')} - {user.get('permission_level')}")
        
        # 페이지네이션 정보
        pagination = format_pagination_data(page, per_page, total)
        logger.info(f"🔍 [페이지네이션] 페이지: {page}/{pagination.get('total_pages', 0)}, 전체: {total}개")
        
        response_data = {
            "users": users,
            "pagination": pagination
        }
        logger.info(f"🔍 [응답 구조] 키: {list(response_data.keys())}")
        
        return format_api_response(
            success=True,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"❌ 사용자 목록 조회 실패: {e}")
        return format_api_response(success=False, message=str(e))


@router.get("/api/users/export")
async def export_users_csv(
    status: Optional[str] = None,
    permission: Optional[str] = None,
    account_id: Optional[str] = None,
    property_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None
):
    """사용자 목록 CSV 내보내기"""
    try:
        # 기본 쿼리 (페이징 없이 전체 데이터)
        base_query = """
            SELECT 
                ur.id,
                ur.신청자 as applicant,
                ur.등록_계정 as user_email,
                ur.property_id,
                ur.권한 as permission_level,
                ur.status,
                ur.ga4_registered,
                ur.created_at,
                ur.expiry_date,
                ur.연장_횟수 as extension_count,
                p.property_display_name as property_name,
                a.account_display_name as account_name
            FROM user_registrations ur
            LEFT JOIN ga4_properties p ON ur.property_id = p.property_id
            LEFT JOIN ga4_accounts a ON p.account_id = a.account_id
        """
        
        conditions = []
        params = []
        
        # 필터 조건 추가 (동일한 로직)
        if status:
            conditions.append("ur.status = ?")
            params.append(status)
            
        if permission:
            conditions.append("ur.권한 = ?")
            params.append(permission)
            
        if account_id:
            conditions.append("a.account_id = ?")
            params.append(account_id)
            
        if property_id:
            conditions.append("ur.property_id = ?")
            params.append(property_id)
            
        if start_date:
            conditions.append("DATE(ur.created_at) >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("DATE(ur.created_at) <= ?")
            params.append(end_date)
            
        if search:
            conditions.append("""
                (ur.신청자 LIKE ? OR 
                 ur.등록_계정 LIKE ? OR 
                 p.property_display_name LIKE ?)
            """)
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # WHERE 절 추가
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # 정렬
        base_query += " ORDER BY ur.created_at DESC"
        
        # 데이터 조회
        users = await db_manager.execute_query(base_query, params)
        
        # CSV 생성
        csv_content = format_csv_data(users)
        
        # 파일명 생성 (현재 날짜 포함)
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ga4_users_{current_date}.csv"
        
        # StreamingResponse로 파일 다운로드
        def iter_csv():
            yield csv_content.encode('utf-8-sig')  # BOM 추가로 한글 깨짐 방지
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        
        return StreamingResponse(
            iter_csv(),
            media_type='text/csv',
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"❌ CSV 내보내기 실패: {e}")
        raise HTTPException(status_code=500, detail="CSV 내보내기에 실패했습니다")


@router.post("/api/approve/{registration_id}")
async def approve_registration(registration_id: int):
    """Editor 권한 승인 API"""
    try:
        # 등록 정보 조회
        registration = await db_manager.execute_query(
            """SELECT ur.*, p.property_id 
               FROM user_registrations ur
               JOIN ga4_properties p ON ur.property_id = p.property_id
               WHERE ur.id = ? AND ur.status = 'pending_approval'""",
            (registration_id,)
        )
        
        if not registration:
            raise HTTPException(status_code=404, detail="승인 대기 중인 등록을 찾을 수 없습니다")
        
        reg = registration[0]
        
        # GA4에 사용자 등록
        success, message, user_link_name = await ga4_user_manager.register_user_to_property(
            property_id=reg['property_id'],
            email=reg['등록_계정'],
            role=reg['권한']
        )
        
        if success:
            # 승인 상태로 업데이트
            rows_affected = await db_manager.execute_update(
                """UPDATE user_registrations 
                   SET status = 'active', ga4_registered = 1, user_link_name = ?, updated_at = ?
                   WHERE id = ?""",
                (user_link_name, datetime.now(), registration_id)
            )
            
            logger.info(f"📊 데이터베이스 업데이트 완료: {rows_affected}개 행 영향")
            logger.info(f"✅ Editor 권한 승인 완료: {reg['등록_계정']}")
            
            return JSONResponse(format_api_response(
                success=True,
                message="Editor 권한이 승인되었습니다"
            ))
        else:
            raise HTTPException(status_code=500, detail=f"GA4 등록 실패: {message}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Editor 권한 승인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/reject/{registration_id}")
async def reject_registration(registration_id: int):
    """Editor 권한 거부 API"""
    try:
        # 상태를 거부로 업데이트 (deleted 상태 사용)
        rows_affected = await db_manager.execute_update(
            """UPDATE user_registrations 
               SET status = 'deleted', updated_at = ?
               WHERE id = ? AND status = 'pending_approval'""",
            (datetime.now(), registration_id)
        )
        
        logger.info(f"📊 거부 업데이트 완료: {rows_affected}개 행 영향")
        logger.info(f"✅ Editor 권한 거부 완료: registration_id={registration_id}")
        
        return JSONResponse(format_api_response(
            success=True,
            message="Editor 권한 요청이 거부되었습니다"
        ))
        
    except Exception as e:
        logger.error(f"❌ Editor 권한 거부 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/extend/{registration_id}")
async def extend_registration(registration_id: int):
    """권한 연장 API"""
    try:
        # 등록 정보 조회
        registration = await db_manager.execute_query(
            """SELECT * FROM user_registrations WHERE id = ? AND status = 'active'""",
            (registration_id,)
        )
        
        if not registration:
            raise HTTPException(status_code=404, detail="활성 등록을 찾을 수 없습니다")
        
        reg = registration[0]
        
        # Editor 권한은 연장 불가
        if reg['권한'] == 'editor':
            raise HTTPException(status_code=400, detail="Editor 권한은 연장할 수 없습니다")
        
        # 30일 연장
        new_expiry = datetime.now() + timedelta(days=30)
        
        rows_affected = await db_manager.execute_update(
            """UPDATE user_registrations 
               SET 종료일 = ?, 연장_횟수 = 연장_횟수 + 1, 최근_연장일 = ?, updated_at = ?
               WHERE id = ?""",
            (new_expiry, datetime.now(), datetime.now(), registration_id)
        )
        
        logger.info(f"📊 연장 업데이트 완료: {rows_affected}개 행 영향")
        logger.info(f"✅ 권한 연장 완료: {reg['등록_계정']} -> {new_expiry.strftime('%Y-%m-%d')}")
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"권한이 {new_expiry.strftime('%Y-%m-%d')}까지 연장되었습니다"
        ))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 권한 연장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/registration/{registration_id}")
async def delete_registration(registration_id: int):
    """사용자 등록 삭제 API"""
    try:
        # 등록 정보 조회
        registration = await db_manager.execute_query(
            """SELECT ur.*, p.property_id 
               FROM user_registrations ur
               JOIN ga4_properties p ON ur.property_id = p.property_id
               WHERE ur.id = ? AND ur.status = 'active'""",
            (registration_id,)
        )
        
        if not registration:
            raise HTTPException(status_code=404, detail="활성 등록을 찾을 수 없습니다")
        
        reg = registration[0]
        
        # GA4에서 사용자 제거 (등록되어 있는 경우)
        if reg['ga4_registered']:
            success, message = await ga4_user_manager.remove_user_from_property(
                property_id=reg['property_id'],
                email=reg['등록_계정'],
                binding_name=reg['user_link_name']
            )
            
            if not success:
                logger.warning(f"⚠️ GA4 제거 실패: {reg['등록_계정']} -> {message}")
        
        # 데이터베이스에서 상태 업데이트
        rows_affected = await db_manager.execute_update(
            """UPDATE user_registrations 
               SET status = 'deleted', ga4_registered = 0, updated_at = ?
               WHERE id = ?""",
            (datetime.now(), registration_id)
        )
        
        logger.info(f"📊 삭제 업데이트 완료: {rows_affected}개 행 영향")
        logger.info(f"✅ 사용자 등록 삭제 완료: {reg['등록_계정']}")
        
        return JSONResponse(format_api_response(
            success=True,
            message="사용자 등록이 삭제되었습니다"
        ))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 등록 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/property/{property_id}/users")
async def get_property_users(property_id: str):
    """프로퍼티 사용자 목록 조회 API"""
    try:
        users = await ga4_user_manager.list_property_users(property_id)
        
        return JSONResponse(format_api_response(
            success=True,
            data={
                "users": users,
                "count": len(users)
            }
        ))
        
    except Exception as e:
        logger.error(f"❌ 프로퍼티 사용자 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/accounts")
async def get_accounts():
    """계정 목록 조회 API"""
    try:
        accounts = await db_manager.execute_query(
            """SELECT account_id as id, account_display_name as name 
               FROM ga4_accounts 
               WHERE 삭제여부 = 0
               ORDER BY account_display_name"""
        )
        
        return JSONResponse({
            "success": True,
            "accounts": accounts or []
        })
        
    except Exception as e:
        logger.error(f"❌ 계정 목록 조회 실패: {e}")
        return format_api_response(success=False, message=str(e)) 