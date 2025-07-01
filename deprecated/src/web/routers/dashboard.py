"""
대시보드 라우터
=============

메인 대시보드와 등록 페이지 관련 라우터를 제공합니다.
"""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional, Dict
from datetime import datetime

from src.infrastructure.database import db_manager
from ...services.notifications.notification_service import notification_service
from ...services.ga4_user_manager import ga4_user_manager
from ...core.logger import get_ga4_logger
from ..utils.helpers import get_dashboard_data, get_property_scanner, format_accounts_data, format_properties_data, format_registration_data, validate_email_list, calculate_expiry_date
from ..utils.formatters import format_api_response

logger = get_ga4_logger()
router = APIRouter()
templates = Jinja2Templates(directory="src/web/templates")

# notification_service는 이미 import되어 있음


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """메인 대시보드"""
    try:
        # 등록 가능한 프로퍼티 조회
        property_scanner = get_property_scanner()
        if property_scanner is not None:
            try:
                properties = await property_scanner.get_available_properties()
            except Exception as e:
                logger.warning(f"⚠️ 프로퍼티 스캔 서비스 오류: {e}")
                properties = []
        else:
            logger.warning("⚠️ 프로퍼티 스캐너가 초기화되지 않음")
            properties = []
        
        # GA4 계정 목록 (템플릿에서 사용)
        accounts_raw = await db_manager.execute_query(
            """SELECT account_id, account_display_name as account_name, 
                      account_display_name as display_name, 
                      최근_업데이트일 as last_updated
               FROM ga4_accounts 
               WHERE 삭제여부 = 0
               ORDER BY account_display_name"""
        )
        
        accounts = format_accounts_data(accounts_raw)
        
        # GA4 프로퍼티 목록 (템플릿에서 사용)
        all_properties_raw = await db_manager.execute_query(
            """SELECT p.property_id, p.property_display_name as property_name,
                      a.account_display_name as account_name,
                      'Asia/Seoul' as time_zone,
                      p.최근_업데이트일 as last_updated
               FROM ga4_properties p
               JOIN ga4_accounts a ON p.account_id = a.account_id
               WHERE p.삭제여부 = 0
               ORDER BY p.property_display_name"""
        )
        
        all_properties = format_properties_data(all_properties_raw)
        
        # 현재 등록된 사용자 현황
        registrations_raw = await db_manager.execute_query(
            """SELECT ur.id, ur.신청자 as applicant, ur.등록_계정 as user_email, 
                      ur.property_id, ur.권한 as permission_level, ur.status,
                      ur.신청일 as created_at, ur.종료일 as expiry_date, ur.ga4_registered,
                      p.property_display_name as property_name, a.account_display_name as account_name
               FROM user_registrations ur
               JOIN ga4_properties p ON ur.property_id = p.property_id
               JOIN ga4_accounts a ON p.account_id = a.account_id
               ORDER BY ur.신청일 DESC"""
        )
        
        registrations = format_registration_data(registrations_raw)
        
        # 통계 정보
        stats = await db_manager.get_database_stats()
        
        # stats가 None이거나 비어있을 경우 기본값 설정
        if not stats:
            stats = {
                'total_accounts': 0,
                'total_properties': 0,
                'active_users': 0,
                'expiring_soon': 0,
                'total_notifications': 0,
                'total_audit_logs': 0,
                'total_registrations': 0
            }
        
        # 현재 시간 추가 (만료 체크용)
        now = datetime.now().isoformat()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "accounts": accounts,
            "properties": all_properties,
            "available_properties": properties,  # 등록 가능한 프로퍼티
            "registrations": registrations,
            "stats": stats,
            "now": now
        })
        
    except Exception as e:
        logger.error(f"❌ 대시보드 로딩 실패: {e}")
        raise HTTPException(status_code=500, detail="대시보드 로딩에 실패했습니다.")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """사용자 등록 페이지"""
    try:
        # 등록 가능한 프로퍼티 목록
        property_scanner = get_property_scanner()
        if property_scanner:
            properties = await property_scanner.get_available_properties()
        else:
            properties = []
        
        return templates.TemplateResponse("register.html", {
            "request": request,
            "properties": properties
        })
        
    except Exception as e:
        logger.error(f"❌ 등록 페이지 로딩 실패: {e}")
        raise HTTPException(status_code=500, detail="등록 페이지 로딩에 실패했습니다.")


@router.post("/api/register")
async def register_users(
    신청자: str = Form(...),
    등록_계정_목록: str = Form(...),  # 쉼표로 구분된 이메일 목록
    property_ids: List[str] = Form(...),
    권한: str = Form(...)
):
    """사용자 등록 API (중복 체크 개선)"""
    try:
        # 🔍 디버깅: 요청 데이터 로그
        logger.info(f"🔍 [등록 요청] 신청자: {신청자}")
        logger.info(f"🔍 [등록 요청] 등록_계정_목록: {등록_계정_목록}")
        logger.info(f"🔍 [등록 요청] property_ids: {property_ids}")
        logger.info(f"🔍 [등록 요청] 권한: {권한}")
        
        # 이메일 목록 파싱 및 검증
        email_list = validate_email_list(등록_계정_목록)
        logger.info(f"🔍 [파싱 결과] 이메일 목록: {email_list}")
        
        if not email_list:
            logger.error("❌ [검증 실패] 등록할 이메일이 없습니다")
            raise HTTPException(status_code=400, detail="등록할 이메일을 입력해주세요.")
        
        if not property_ids:
            logger.error("❌ [검증 실패] 프로퍼티가 선택되지 않았습니다")
            raise HTTPException(status_code=400, detail="프로퍼티를 선택해주세요.")
        
        results = []
        
        for property_id in property_ids:
            logger.info(f"🔍 [프로퍼티 처리] 프로퍼티 ID: {property_id}")
            for email in email_list:
                logger.info(f"🔍 [사용자 처리] 이메일: {email}")
                try:
                    # 1. 기존 등록 여부 체크 (DB)
                    logger.info(f"🔍 [단계 1] 기존 등록 체크: {email} @ {property_id}")
                    existing_registration = await _check_existing_registration(email, property_id)
                    
                    if existing_registration:
                        logger.info(f"🔍 [기존 등록] 발견됨: {existing_registration}")
                        # 기존 등록이 있는 경우 처리
                        result = await _handle_existing_user(existing_registration, 신청자, 권한)
                        results.append(result)
                        logger.info(f"🔍 [기존 등록 처리] 결과: {result}")
                        continue
                    
                    # 2. GA4에서 기존 사용자 체크
                    logger.info(f"🔍 [단계 2] GA4 기존 사용자 체크: {email}")
                    ga4_check_result = await _check_ga4_existing_user(email, property_id)
                    logger.info(f"🔍 [GA4 체크 결과]: {ga4_check_result}")
                    
                    if ga4_check_result['exists']:
                        logger.info(f"🔍 [GA4 기존 사용자] 발견됨")
                        # GA4에 이미 등록된 경우 처리
                        result = await _handle_ga4_existing_user(
                            email, property_id, 신청자, 권한, ga4_check_result
                        )
                        results.append(result)
                        logger.info(f"🔍 [GA4 기존 사용자 처리] 결과: {result}")
                        continue
                    
                    # 3. 신규 등록 처리
                    logger.info(f"🔍 [단계 3] 신규 등록 처리: {email}")
                    result = await _register_new_user(신청자, email, property_id, 권한)
                    results.append(result)
                    logger.info(f"🔍 [신규 등록 처리] 결과: {result}")
                    
                    logger.info(f"✅ 사용자 등록 성공: {email} -> {property_id} ({권한})")
                    
                except Exception as e:
                    logger.error(f"❌ 사용자 등록 실패 {email}: {e}")
                    logger.error(f"❌ 오류 상세: {type(e).__name__}: {str(e)}")
                    results.append({
                        "email": email,
                        "property_id": property_id,
                        "status": "error",
                        "error": str(e)
                    })
        
        # 등록 성공 시 알림 발송
        await _send_registration_notifications(results, 신청자, 권한)
        
        success_count = len([r for r in results if r['status'] == 'success'])
        existing_count = len([r for r in results if r['status'] == 'existing'])
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"처리 완료 - 신규등록: {success_count}건, 기존등록: {existing_count}건",
            data={"results": results}
        ))
        
    except Exception as e:
        logger.error(f"❌ 사용자 등록 API 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _check_existing_registration(email: str, property_id: str) -> Optional[Dict]:
    """기존 등록 여부 체크 (DB)"""
    try:
        registrations = await db_manager.execute_query(
            """SELECT ur.*, p.property_display_name 
               FROM user_registrations ur
               JOIN ga4_properties p ON ur.property_id = p.property_id
               WHERE ur.등록_계정 = ? AND ur.property_id = ? 
               AND ur.status IN ('active', 'pending_approval')
               ORDER BY ur.created_at DESC
               LIMIT 1""",
            (email, property_id)
        )
        
        return registrations[0] if registrations else None
        
    except Exception as e:
        logger.error(f"❌ 기존 등록 체크 실패: {e}")
        return None


async def _check_ga4_existing_user(email: str, property_id: str) -> Dict:
    """GA4에서 기존 사용자 체크"""
    try:
        users = await ga4_user_manager.list_property_users(property_id)
        
        for user in users:
            if user.get('email', '').lower() == email.lower():
                return {
                    'exists': True,
                    'user_data': user,
                    'current_roles': user.get('roles', []),
                    'binding_name': user.get('name')
                }
        
        return {'exists': False}
        
    except Exception as e:
        logger.error(f"❌ GA4 사용자 체크 실패: {e}")
        return {'exists': False}


async def _handle_existing_user(existing_reg: Dict, 신청자: str, 권한: str) -> Dict:
    """기존 등록 사용자 처리"""
    try:
        email = existing_reg['등록_계정']
        property_id = existing_reg['property_id']
        property_name = existing_reg['property_display_name']
        current_status = existing_reg['status']
        current_permission = existing_reg['권한']
        
        logger.info(f"📋 기존 등록 발견: {email} -> {property_name} (상태: {current_status}, 권한: {current_permission})")
        
        # 권한 변경이 필요한 경우
        if current_permission != 권한:
            # 권한 업데이트
            await db_manager.execute_update(
                """UPDATE user_registrations 
                   SET 권한 = ?, 신청자 = ?, updated_at = ?, 
                       approval_required = ?, 
                       status = ?
                   WHERE id = ?""",
                (
                    권한, 
                    신청자, 
                    datetime.now(),
                    권한 in ['editor', 'admin'],  # Editor와 Admin은 승인 필요
                    'pending_approval' if 권한 in ['editor', 'admin'] else 'active',
                    existing_reg['id']
                )
            )
            
            # 기존 사용자 권한 변경 알림 발송
            await notification_service.send_admin_notification(
                subject="GA4 권한 변경 요청",
                message=f"기존 사용자의 권한 변경이 요청되었습니다.",
                details=f"""
                사용자: {email}
                프로퍼티: {property_name}
                기존 권한: {current_permission}
                요청 권한: {권한}
                신청자: {신청자}
                """
            )
            
            return {
                "email": email,
                "property_id": property_id,
                "status": "updated",
                "message": f"기존 등록 권한 업데이트: {current_permission} → {권한}",
                "registration_id": existing_reg['id']
            }
        else:
            # 동일한 권한으로 이미 등록됨 - 만료일 연장
            종료일 = calculate_expiry_date(권한)
            
            await db_manager.execute_update(
                """UPDATE user_registrations 
                   SET 종료일 = ?, 신청자 = ?, updated_at = ?, 연장_횟수 = 연장_횟수 + 1
                   WHERE id = ?""",
                (종료일, 신청자, datetime.now(), existing_reg['id'])
            )
            
            # 기존 등록 알림 발송
            await notification_service.send_admin_notification(
                subject="GA4 권한 연장 요청",
                message=f"기존 등록 사용자의 권한이 연장되었습니다.",
                details=f"""
                사용자: {email}
                프로퍼티: {property_name}
                권한: {권한}
                새 만료일: {종료일.strftime('%Y-%m-%d') if 종료일 else 'N/A'}
                신청자: {신청자}
                """
            )
            
            return {
                "email": email,
                "property_id": property_id,
                "status": "existing",
                "message": "이미 등록된 사용자 - 권한 연장됨",
                "registration_id": existing_reg['id']
            }
            
    except Exception as e:
        logger.error(f"❌ 기존 사용자 처리 실패: {e}")
        return {
            "email": existing_reg['등록_계정'],
            "property_id": existing_reg['property_id'],
            "status": "error",
            "error": f"기존 사용자 처리 실패: {str(e)}"
        }


async def _handle_ga4_existing_user(email: str, property_id: str, 신청자: str, 권한: str, ga4_data: Dict) -> Dict:
    """GA4에 이미 등록된 사용자 처리"""
    try:
        # GA4에는 있지만 DB에 등록 기록이 없는 경우 - DB에 등록 기록 생성
        종료일 = calculate_expiry_date(권한)
        current_roles = ga4_data.get('current_roles', [])
        binding_name = ga4_data.get('binding_name')
        
        registration_id = await db_manager.execute_insert(
            """INSERT INTO user_registrations 
               (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, approval_required, status, ga4_registered, user_link_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                신청자, email, property_id, 권한, datetime.now(), 종료일,
                권한 in ['editor', 'admin'],  # Editor와 Admin은 승인 필요
                'active',  # GA4에 이미 등록되어 있으므로 active
                1,  # GA4에 등록되어 있음
                binding_name
            )
        )
        
        # GA4 기존 등록 알림 발송
        await notification_service.send_admin_notification(
            subject="GA4 기존 등록 사용자 발견",
            message=f"GA4에 이미 등록된 사용자가 DB에 추가되었습니다.",
            details=f"""
            사용자: {email}
            프로퍼티: {property_id}
            GA4 현재 권한: {', '.join(current_roles)}
            요청 권한: {권한}
            신청자: {신청자}
            상태: DB 등록 기록 추가됨
            """
        )
        
        logger.info(f"📋 GA4 기존 사용자 DB 등록: {email} -> {property_id}")
        
        return {
            "email": email,
            "property_id": property_id,
            "status": "ga4_existing",
            "message": "GA4에 이미 등록된 사용자 - DB 기록 추가됨",
            "registration_id": registration_id,
            "current_roles": current_roles
        }
        
    except Exception as e:
        logger.error(f"❌ GA4 기존 사용자 처리 실패: {e}")
        return {
            "email": email,
            "property_id": property_id,
            "status": "error",
            "error": f"GA4 기존 사용자 처리 실패: {str(e)}"
        }


async def _register_new_user(신청자: str, email: str, property_id: str, 권한: str) -> Dict:
    """신규 사용자 등록"""
    try:
        logger.info(f"🔍 [신규 등록] 시작 - 신청자: {신청자}, 이메일: {email}, 프로퍼티: {property_id}, 권한: {권한}")
        
        # 만료일 계산
        종료일 = calculate_expiry_date(권한)
        logger.info(f"🔍 [만료일 계산] 종료일: {종료일}")
        
        # 승인 필요 여부 계산
        approval_required = 권한 in ['editor', 'admin']
        status = 'pending_approval' if approval_required else 'active'
        logger.info(f"🔍 [승인 설정] 승인 필요: {approval_required}, 상태: {status}")
        
        # 데이터베이스에 등록
        logger.info(f"🔍 [DB 등록] 데이터베이스 INSERT 시작")
        registration_id = await db_manager.execute_insert(
            """INSERT INTO user_registrations 
               (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, approval_required, status, ga4_registered)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                신청자, email, property_id, 권한, datetime.now(), 종료일,
                approval_required,
                status,
                0  # 아직 GA4에 등록되지 않음
            )
        )
        logger.info(f"🔍 [DB 등록] 완료 - registration_id: {registration_id}")
        
        # Editor가 아닌 경우 즉시 GA4에 등록 시도
        user_link_name = None
        if 권한 not in ['editor', 'admin']:
            logger.info(f"🔍 [GA4 등록] 즉시 등록 시도 - 권한: {권한}")
            try:
                success, message, user_link_name = await ga4_user_manager.register_user_to_property(
                    property_id=property_id,
                    email=email,
                    role=권한
                )
                logger.info(f"🔍 [GA4 등록] 결과 - 성공: {success}, 메시지: {message}, 바인딩: {user_link_name}")
                
                if success:
                    # GA4 등록 성공 시 데이터베이스 업데이트
                    logger.info(f"🔍 [DB 업데이트] GA4 등록 성공 업데이트 시작")
                    await db_manager.execute_update(
                        """UPDATE user_registrations 
                           SET ga4_registered = 1, user_link_name = ?, updated_at = ?
                           WHERE id = ?""",
                        (user_link_name, datetime.now(), registration_id)
                    )
                    logger.info(f"🔍 [DB 업데이트] 완료")
                    logger.info(f"✅ GA4 등록 완료: {email} -> {property_id}")
                else:
                    logger.warning(f"⚠️ GA4 등록 실패: {email} -> {message}")
                    
            except Exception as ga4_error:
                logger.error(f"❌ GA4 등록 중 오류: {email} -> {ga4_error}")
                logger.error(f"❌ GA4 오류 상세: {type(ga4_error).__name__}: {str(ga4_error)}")
        else:
            logger.info(f"🔍 [GA4 등록] 승인 필요 권한으로 GA4 등록 생략 - 권한: {권한}")
        
        result = {
            "email": email,
            "property_id": property_id,
            "status": status,  # 실제 데이터베이스 상태 사용 (pending_approval 또는 active)
            "registration_id": registration_id,
            "ga4_registered": user_link_name is not None
        }
        logger.info(f"🔍 [최종 결과] 신규 등록 성공: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 신규 사용자 등록 실패: {e}")
        logger.error(f"❌ 신규 등록 오류 상세: {type(e).__name__}: {str(e)}")
        error_result = {
            "email": email,
            "property_id": property_id,
            "status": "error",
            "error": str(e)
        }
        logger.info(f"🔍 [최종 결과] 신규 등록 실패: {error_result}")
        return error_result


async def _send_registration_notifications(results: List[Dict], 신청자: str, 권한: str):
    """등록 결과에 따른 알림 발송"""
    try:
        success_users = [r for r in results if r['status'] == 'success']
        pending_users = [r for r in results if r['status'] == 'pending_approval']  # 승인 대기 사용자 추가
        existing_users = [r for r in results if r['status'] in ['existing', 'ga4_existing', 'updated']]
        
        logger.info(f"🔄 등록 알림 발송 시작 - 신규: {len(success_users)}명, 승인대기: {len(pending_users)}명, 기존: {len(existing_users)}명")
        
        # 신규 등록 성공 시 알림 처리
        for result in success_users:
            try:
                await _send_user_notification(result, 신청자, 권한, "신규 등록")
            except Exception as e:
                logger.warning(f"⚠️ 신규 등록 알림 발송 실패: {e}")
        
        # 승인 대기 사용자 알림 처리 (새로 추가)
        for result in pending_users:
            try:
                await _send_user_notification(result, 신청자, 권한, "승인 대기")
            except Exception as e:
                logger.warning(f"⚠️ 승인 대기 알림 발송 실패: {e}")
        
        # 기존 사용자 처리 시 알림 발송 (추가됨)
        for result in existing_users:
            try:
                # 기존 사용자도 권한 변경/연장 시 알림 발송
                if result['status'] == 'updated':
                    await _send_user_notification(result, 신청자, 권한, "권한 변경")
                elif result['status'] == 'existing':
                    await _send_user_notification(result, 신청자, 권한, "권한 연장")
                elif result['status'] == 'ga4_existing':
                    await _send_user_notification(result, 신청자, 권한, "GA4 기존 사용자")
                    
            except Exception as e:
                logger.warning(f"⚠️ 기존 사용자 알림 발송 실패: {e}")
        
        # 기존 사용자 처리 요약 알림 (관리자용)
        if existing_users:
            details = []
            for result in existing_users:
                details.append(f"- {result['email']}: {result.get('message', '처리됨')}")
            
            await notification_service.send_admin_notification(
                subject="GA4 기존 사용자 처리 완료",
                message=f"{len(existing_users)}명의 기존 사용자가 처리되었습니다.",
                details=f"""
                신청자: {신청자}
                요청 권한: {권한}
                
                처리 결과:
                {chr(10).join(details)}
                """
            )
            
    except Exception as e:
        logger.error(f"❌ 등록 알림 발송 실패: {e}")


async def _send_user_notification(result: Dict, 신청자: str, 권한: str, notification_type: str):
    """개별 사용자 알림 발송"""
    try:
        종료일 = calculate_expiry_date(권한)
        
        # 프로퍼티 이름 조회
        property_info = await db_manager.execute_query(
            "SELECT property_display_name FROM ga4_properties WHERE property_id = ?",
            (result['property_id'],)
        )
        property_name = property_info[0]['property_display_name'] if property_info else f"Property {result['property_id']}"
        
        logger.info(f"🔄 {notification_type} 알림 시작: {result['email']}, 권한: {권한}")
        
        # Editor 또는 Admin 권한인 경우 승인 대기 알림
        if 권한 in ['editor', 'admin']:
            # 승인 대기 알림 발송
            approval_data = {
                'user_email': result['email'],
                'property_id': result['property_id'],
                'property_name': property_name,
                'role': 권한,
                'applicant': 신청자,
                'registration_id': result.get('registration_id'),
                'notification_type': notification_type
            }
            
            logger.info(f"🔄 승인 대기 알림 시작: {approval_data}")
            
            # 사용자에게 승인 대기 알림
            await notification_service.send_user_pending_approval_notification(approval_data)
            
            # 관리자에게 승인 요청 알림  
            await notification_service.send_pending_approval_notification(approval_data)
            
            # 추가로 관리자 알림도 발송
            await notification_service.send_admin_notification(
                subject=f"GA4 {권한.upper()} 권한 {notification_type} 승인 요청",
                message=f"{권한.upper()} 권한 {notification_type} 승인 요청이 접수되었습니다.",
                details=f"""
                사용자: {result['email']}
                프로퍼티: {property_name} ({result['property_id']})
                요청 권한: {권한.upper()}
                신청자: {신청자}
                처리 유형: {notification_type}
                등록 ID: {result.get('registration_id', 'N/A')}
                
                대시보드에서 승인/거부 처리를 해주세요.
                """
            )
            
            logger.info(f"✅ {notification_type} 승인 대기 알림 발송 완료: {result['email']}")
            
        else:
            # Viewer/Analyst 권한인 경우 환영 알림
            welcome_data = {
                'user_email': result['email'],
                'property_id': result['property_id'],
                'property_name': property_name,
                'role': 권한,
                'expiry_date': 종료일.strftime('%Y-%m-%d') if 종료일 else 'N/A',
                'applicant': 신청자,
                'notification_type': notification_type
            }
            
            logger.info(f"🔄 환영 알림 시작: {welcome_data}")
            
            await notification_service.send_welcome_notification(welcome_data)
            
            logger.info(f"✅ {notification_type} 환영 알림 발송 완료: {result['email']}")
            
    except Exception as e:
        logger.error(f"❌ {notification_type} 사용자 알림 발송 실패 ({result.get('email', 'Unknown')}): {e}") 