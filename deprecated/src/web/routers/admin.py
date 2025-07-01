"""
관리자 설정 라우터
===============

관리자 설정 페이지 및 관련 API를 제공합니다.
"""

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime
from typing import List

from src.infrastructure.database import db_manager
from ...core.logger import get_ga4_logger
from ..utils.formatters import format_api_response

logger = get_ga4_logger()
router = APIRouter()
templates = Jinja2Templates(directory="src/web/templates")


@router.get("/admin", response_class=HTMLResponse)
async def admin_config(request: Request):
    """관리자 설정 페이지"""
    try:
        return templates.TemplateResponse("admin_config.html", {
            "request": request
        })
    except Exception as e:
        logger.error(f"❌ 관리자 설정 페이지 로드 실패: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다")


# 유효기간 설정 관련 API
@router.get("/api/admin/validity-periods")
async def get_validity_periods():
    """유효기간 설정 조회"""
    try:
        periods = await db_manager.execute_query(
            "SELECT * FROM validity_periods ORDER BY role, period_days"
        )
        return JSONResponse({
            "success": True,
            "periods": periods or []
        })
    except Exception as e:
        logger.error(f"❌ 유효기간 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/admin/validity-periods/{period_id}")
async def get_validity_period(period_id: int):
    """특정 유효기간 설정 조회"""
    try:
        period = await db_manager.execute_query(
            "SELECT * FROM validity_periods WHERE id = ?", (period_id,)
        )
        if not period:
            raise HTTPException(status_code=404, detail="유효기간 설정을 찾을 수 없습니다")
        
        period_data = period[0]
        # JavaScript에서 기대하는 구조로 응답 (data.period.role 형태)
        return JSONResponse({
            "success": True,
            "period": {
                "role": period_data.get("role"),
                "period_days": period_data.get("period_days"),
                "description": period_data.get("description"),
                "is_active": period_data.get("is_active")
            }
        })
    except Exception as e:
        logger.error(f"❌ 유효기간 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/validity-periods")
async def create_validity_period(request: Request):
    """유효기간 설정 생성"""
    try:
        data = await request.json()
        
        # 중복 체크
        existing = await db_manager.execute_query(
            "SELECT id FROM validity_periods WHERE role = ?", (data['role'],)
        )
        if existing:
            return JSONResponse(format_api_response(
                success=False,
                message=f"{data['role']} 권한의 유효기간이 이미 설정되어 있습니다."
            ))
        
        await db_manager.execute_insert(
            """INSERT INTO validity_periods (role, period_days, description, is_active)
               VALUES (?, ?, ?, ?)""",
            (data['role'], data['period_days'], data.get('description'), data.get('is_active', True))
        )
        
        return JSONResponse(format_api_response(
            success=True,
            message="유효기간 설정이 생성되었습니다."
        ))
    except Exception as e:
        logger.error(f"❌ 유효기간 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/admin/validity-periods/{period_id}")
async def update_validity_period(period_id: int, request: Request):
    """유효기간 설정 수정"""
    try:
        data = await request.json()
        
        await db_manager.execute_update(
            """UPDATE validity_periods 
               SET role = ?, period_days = ?, description = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (data['role'], data['period_days'], data.get('description'), 
             data.get('is_active', True), period_id)
        )
        
        return JSONResponse(format_api_response(
            success=True,
            message="유효기간 설정이 수정되었습니다."
        ))
    except Exception as e:
        logger.error(f"❌ 유효기간 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/admin/validity-periods/{period_id}")
async def delete_validity_period(period_id: int):
    """유효기간 설정 삭제"""
    try:
        await db_manager.execute_update(
            "DELETE FROM validity_periods WHERE id = ?", (period_id,)
        )
        
        return JSONResponse(format_api_response(
            success=True,
            message="유효기간 설정이 삭제되었습니다."
        ))
    except Exception as e:
        logger.error(f"❌ 유효기간 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 담당자 관리 관련 API
@router.get("/api/admin/responsible-persons")
async def get_responsible_persons():
    """담당자 목록 조회"""
    try:
        persons = await db_manager.execute_query(
            """SELECT * FROM responsible_persons
               ORDER BY name"""
        )
        return JSONResponse({
            "success": True,
            "persons": persons or []
        })
    except Exception as e:
        logger.error(f"❌ 담당자 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/admin/responsible-persons/{person_id}")
async def get_responsible_person(person_id: int):
    """특정 담당자 조회"""
    try:
        person = await db_manager.execute_query(
            "SELECT * FROM responsible_persons WHERE id = ?", (person_id,)
        )
        if not person:
            raise HTTPException(status_code=404, detail="담당자를 찾을 수 없습니다")
        
        person_data = person[0]
        # JavaScript에서 기대하는 구조로 응답 (data.person.name 형태)
        return JSONResponse({
            "success": True,
            "person": {
                "name": person_data.get("name"),
                "email": person_data.get("email"),
                "account_id": person_data.get("account_id"),
                "property_id": person_data.get("property_id"),
                "role": person_data.get("role"),
                "notification_enabled": person_data.get("notification_enabled"),
                "is_active": person_data.get("is_active")
            }
        })
    except Exception as e:
        logger.error(f"❌ 담당자 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/admin/responsible-persons")
async def create_responsible_person(request: Request):
    """담당자 생성"""
    try:
        data = await request.json()
        
        await db_manager.execute_insert(
            """INSERT INTO responsible_persons 
               (name, email, account_id, property_id, role, notification_enabled, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (data['name'], data['email'], data.get('account_id'), data.get('property_id'),
             data['role'], data.get('notification_enabled', True), data.get('is_active', True))
        )
        
        return JSONResponse(format_api_response(
            success=True,
            message="담당자가 생성되었습니다."
        ))
    except Exception as e:
        logger.error(f"❌ 담당자 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/admin/responsible-persons/{person_id}")
async def update_responsible_person(person_id: int, request: Request):
    """담당자 수정"""
    try:
        data = await request.json()
        
        await db_manager.execute_update(
            """UPDATE responsible_persons 
               SET name = ?, email = ?, account_id = ?, property_id = ?, role = ?, 
                   notification_enabled = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (data['name'], data['email'], data.get('account_id'), data.get('property_id'),
             data['role'], data.get('notification_enabled', True), 
             data.get('is_active', True), person_id)
        )
        
        return JSONResponse(format_api_response(
            success=True,
            message="담당자 정보가 수정되었습니다."
        ))
    except Exception as e:
        logger.error(f"❌ 담당자 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/admin/responsible-persons/{person_id}")
async def delete_responsible_person(person_id: int):
    """담당자 삭제"""
    try:
        await db_manager.execute_update(
            "DELETE FROM responsible_persons WHERE id = ?", (person_id,)
        )
        
        return JSONResponse(format_api_response(
            success=True,
            message="담당자가 삭제되었습니다."
        ))
    except Exception as e:
        logger.error(f"❌ 담당자 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 알림 설정 관련 API
@router.get("/api/admin/notification-settings")
async def get_notification_settings():
    """알림 설정 조회"""
    try:
        settings = await db_manager.execute_query(
            "SELECT * FROM notification_settings ORDER BY notification_type"
        )
        return JSONResponse({
            "success": True,
            "settings": settings or []
        })
    except Exception as e:
        logger.error(f"❌ 알림 설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/admin/notification-settings/{notification_type}")
async def update_notification_setting(notification_type: str, request: Request):
    """알림 설정 수정 (엄격한 입력 검증 포함)"""
    try:
        data = await request.json()
        
        # 1. 알림 유형 존재 여부 확인
        valid_notification_types = ['daily_summary', 'expiry_warning', 'expiry_notice', 'immediate_approval']
        if notification_type not in valid_notification_types:
            raise HTTPException(
                status_code=400, 
                detail=f"유효하지 않은 알림 유형입니다. 허용된 유형: {', '.join(valid_notification_types)}"
            )
        
        # 2. 데이터베이스에서 해당 알림 설정 존재 확인
        existing_setting = await db_manager.execute_query(
            "SELECT * FROM notification_settings WHERE notification_type = ?",
            (notification_type,)
        )
        if not existing_setting:
            raise HTTPException(
                status_code=404,
                detail=f"알림 설정을 찾을 수 없습니다: {notification_type}"
            )
        
        # 3. 허용되는 필드만 처리
        allowed_fields = {'enabled', 'trigger_days', 'template_subject', 'template_body'}
        invalid_fields = set(data.keys()) - allowed_fields
        if invalid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"허용되지 않는 필드: {', '.join(invalid_fields)}. 허용된 필드: {', '.join(allowed_fields)}"
            )
        
        # 4. 동적으로 업데이트할 필드들 결정 및 검증
        update_fields = []
        update_values = []
        
        # enabled 필드 처리 (boolean 검증)
        if 'enabled' in data:
            enabled_value = data['enabled']
            if not isinstance(enabled_value, bool):
                raise HTTPException(
                    status_code=400,
                    detail=f"enabled 필드는 boolean 타입이어야 합니다. 받은 값: {enabled_value} ({type(enabled_value).__name__})"
                )
            update_fields.append("enabled = ?")
            update_values.append(enabled_value)
        
        # trigger_days 필드 처리 (문자열 및 형식 검증)
        if 'trigger_days' in data:
            trigger_days = data['trigger_days']
            if not isinstance(trigger_days, str):
                raise HTTPException(
                    status_code=400,
                    detail=f"trigger_days 필드는 문자열이어야 합니다. 받은 값: {trigger_days} ({type(trigger_days).__name__})"
                )
            
            # trigger_days 형식 검증 (0 또는 쉼표로 구분된 숫자들)
            import re
            if trigger_days != '0' and not re.match(r'^\d+(,\d+)*$', trigger_days):
                raise HTTPException(
                    status_code=400,
                    detail=f"trigger_days 형식이 올바르지 않습니다. 예시: '30,7,1' 또는 '0'. 받은 값: {trigger_days}"
                )
            
            update_fields.append("trigger_days = ?")
            update_values.append(trigger_days)
        
        # template_subject 필드 처리 (문자열 검증)
        if 'template_subject' in data:
            template_subject = data['template_subject']
            if not isinstance(template_subject, str):
                raise HTTPException(
                    status_code=400,
                    detail=f"template_subject 필드는 문자열이어야 합니다. 받은 값: {template_subject} ({type(template_subject).__name__})"
                )
            update_fields.append("template_subject = ?")
            update_values.append(template_subject)
        
        # template_body 필드 처리 (문자열 검증)
        if 'template_body' in data:
            template_body = data['template_body']
            if not isinstance(template_body, str):
                raise HTTPException(
                    status_code=400,
                    detail=f"template_body 필드는 문자열이어야 합니다. 받은 값: {template_body} ({type(template_body).__name__})"
                )
            update_fields.append("template_body = ?")
            update_values.append(template_body)
        
        # 5. 수정할 필드가 없는 경우 에러
        if not update_fields:
            raise HTTPException(status_code=400, detail="수정할 필드가 없습니다")
        
        # 6. 업데이트 쿼리 실행
        query = f"""UPDATE notification_settings 
                   SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                   WHERE notification_type = ?"""
        
        update_values.append(notification_type)
        
        rows_affected = await db_manager.execute_update(query, tuple(update_values))
        
        if rows_affected == 0:
            raise HTTPException(
                status_code=404,
                detail=f"알림 설정 업데이트 실패: {notification_type}"
            )
        
        return JSONResponse(format_api_response(
            success=True,
            message="알림 설정이 수정되었습니다."
        ))
        
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        logger.error(f"❌ 알림 설정 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")


# 시스템 설정 관련 API
@router.get("/api/admin/system-settings")
async def get_system_settings():
    """시스템 설정 조회"""
    try:
        settings_list = await db_manager.execute_query(
            "SELECT setting_key, setting_value FROM admin_settings"
        )
        
        # 딕셔너리로 변환
        settings = {}
        for setting in settings_list or []:
            settings[setting['setting_key']] = setting['setting_value']
        
        return JSONResponse({
            "success": True,
            "settings": settings
        })
    except Exception as e:
        logger.error(f"❌ 시스템 설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/admin/system-settings")
async def update_system_settings(request: Request):
    """시스템 설정 수정"""
    try:
        data = await request.json()
        
        for key, value in data.items():
            await db_manager.execute_update(
                """INSERT OR REPLACE INTO admin_settings (setting_key, setting_value, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, value)
            )
        
        return JSONResponse(format_api_response(
            success=True,
            message="시스템 설정이 수정되었습니다."
        ))
    except Exception as e:
        logger.error(f"❌ 시스템 설정 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/admin/notification-stats")
async def get_admin_notification_stats():
    """관리자용 알림 통계 조회"""
    try:
        stats = await notification_service.get_notification_statistics()
        return JSONResponse(format_api_response(
            success=True,
            data=stats
        ))
        
    except Exception as e:
        logger.error(f"❌ 관리자 알림 통계 조회 실패: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ), status_code=500) 