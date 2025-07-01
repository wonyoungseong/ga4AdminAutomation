"""
일반 API 라우터
=============

프로퍼티 스캔, 통계, 스케줄러 관련 API를 제공합니다.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from src.infrastructure.database import db_manager
from ...services.ga4_user_manager import ga4_user_manager
from ...services.notifications.notification_service import notification_service
from ...api.scheduler import scheduler_service
from ...core.logger import get_ga4_logger
from ..utils.helpers import get_property_scanner
from ..utils.formatters import format_api_response

logger = get_ga4_logger()
router = APIRouter()


@router.post("/api/scan")
async def scan_properties():
    """프로퍼티 스캔 API"""
    try:
        logger.info("🔍 수동 프로퍼티 스캔 시작")
        
        property_scanner = get_property_scanner()
        if property_scanner is None:
            raise HTTPException(status_code=503, detail="프로퍼티 스캐너가 초기화되지 않았습니다")
        
        result = await property_scanner.scan_all_accounts_and_properties()
        
        return JSONResponse(format_api_response(
            success=True,
            message="스캔이 완료되었습니다.",
            data={
                "accounts_found": result.accounts_found,
                "accounts_new": result.accounts_new,
                "accounts_updated": result.accounts_updated,
                "properties_found": result.properties_found,
                "properties_new": result.properties_new,
                "properties_updated": result.properties_updated,
                "scan_duration": result.scan_duration
            }
        ))
        
    except Exception as e:
        logger.error(f"❌ 프로퍼티 스캔 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/properties")
async def get_properties():
    """등록 가능한 프로퍼티 목록 API"""
    try:
        property_scanner = get_property_scanner()
        if property_scanner is None:
            raise HTTPException(status_code=503, detail="프로퍼티 스캐너가 초기화되지 않았습니다")
            
        properties = await property_scanner.get_available_properties()
        return JSONResponse({
            "success": True,
            "properties": properties
        })
        
    except Exception as e:
        logger.error(f"❌ 프로퍼티 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/stats")
async def get_stats():
    """시스템 통계 API"""
    try:
        stats = await db_manager.get_database_stats()
        
        return JSONResponse(format_api_response(
            success=True,
            data={"stats": stats}
        ))
        
    except Exception as e:
        logger.error(f"❌ 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/process-queue")
async def process_registration_queue():
    """등록 대기열 처리 API"""
    try:
        logger.info("🔄 수동 등록 대기열 처리 시작")
        await ga4_user_manager.process_registration_queue()
        
        return JSONResponse(format_api_response(
            success=True,
            message="등록 대기열 처리 완료"
        ))
        
    except Exception as e:
        logger.error(f"❌ 등록 대기열 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 알림 관련 API
@router.post("/api/send-test-notification")
async def send_test_notification(request: Request):
    """테스트 알림 발송"""
    try:
        data = await request.json()
        email = data.get('email', 'test@example.com')
        notification_type = data.get('notification_type', 'welcome')
        
        # 기본 테스트 데이터 준비
        current_time = datetime.now()
        future_date = current_time + timedelta(days=10)  # 미래 날짜로 설정
        
        test_data = {
            'email': email,
            'user_email': email,
            '등록_계정': email,
            'property_name': 'Amorepacific GA4 테스트',
            'property_id': '462884506',
            'role': 'analyst',
            'expiry_date': future_date.isoformat(),
            'subject': '[테스트] GA4 관리자 알림',
            'message': '테스트 관리자 알림입니다.',
            'details': '상세 정보입니다.'
        }
        
        # 알림 타입별 발송 처리
        success = False
        if notification_type == 'welcome':
            success = await notification_service.send_welcome_notification(test_data)
        elif notification_type == 'expiry_warning_30':
            # 30일 전 템플릿 테스트용
            expiry_30_days = current_time + timedelta(days=30)
            test_data['expiry_date'] = expiry_30_days.isoformat()
            success = await notification_service.send_expiry_warning(test_data, 30)
        elif notification_type == 'expiry_warning':
            success = await notification_service.send_expiry_warning(test_data, 7)
        elif notification_type == '7_days':
            success = await notification_service.send_expiry_warning(test_data, 7)
        elif notification_type == '1_day':
            success = await notification_service.send_expiry_warning(test_data, 1)
        elif notification_type == 'deletion_notice':
            success = await notification_service.send_deletion_notice(test_data)
        elif notification_type == 'admin':
            success = await notification_service.send_admin_notification(
                test_data['subject'], test_data['message'], test_data['details']
            )
        elif notification_type == 'editor_downgrade':
            success = await notification_service.send_editor_downgrade_notification(test_data)
        else:
            return JSONResponse(format_api_response(
                success=False,
                message=f"지원하지 않는 알림 타입: {notification_type}"
            ))
        
        return JSONResponse(format_api_response(
            success=success,
            message=f"테스트 알림 발송 {'성공' if success else '실패'}: {email} ({notification_type})"
        ))
        
    except Exception as e:
        logger.error(f"테스트 알림 발송 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=f"테스트 알림 발송 실패: {str(e)}"
        ), status_code=500)


@router.post("/api/process-expiry-notifications")
async def process_expiry_notifications():
    """만료 알림 처리"""
    try:
        results = await notification_service.process_scheduled_notifications()
        
        # results가 딕셔너리 형태이므로 적절히 처리
        if isinstance(results, dict):
            processed = results.get('processed', 0)
            return JSONResponse(format_api_response(
                success=True,
                message=f"예약된 알림 처리 완료: {processed}개 처리됨",
                data={"details": results}
            ))
        else:
            return JSONResponse(format_api_response(
                success=True,
                message="예약된 알림 처리 완료",
                data={"details": results}
            ))
        
    except Exception as e:
        logger.error(f"예약된 알림 처리 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.post("/api/process-editor-downgrade")
async def process_editor_downgrade():
    """Editor 권한 자동 다운그레이드 처리"""
    try:
        downgraded_count = await scheduler_service.process_editor_downgrade()
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"Editor 권한 다운그레이드 완료: {downgraded_count}명 처리"
        ))
        
    except Exception as e:
        logger.error(f"Editor 권한 다운그레이드 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.get("/api/notification-stats")
async def get_notification_stats():
    """알림 통계 조회"""
    try:
        stats = await notification_service.get_notification_statistics()
        return JSONResponse(format_api_response(
            success=True,
            data=stats
        ))
        
    except Exception as e:
        logger.error(f"알림 통계 조회 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


# 스케줄러 관련 API
@router.get("/api/scheduler-status")
async def get_scheduler_status():
    """스케줄러 상태 조회"""
    try:
        status = scheduler_service.get_scheduler_status()
        return JSONResponse(format_api_response(
            success=True,
            data=status
        ))
        
    except Exception as e:
        logger.error(f"스케줄러 상태 조회 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.post("/api/scheduler/start")
async def start_scheduler():
    """스케줄러 시작"""
    try:
        if not scheduler_service.is_running:
            scheduler_service.start_scheduler()
            message = "스케줄러가 시작되었습니다"
        else:
            message = "스케줄러가 이미 실행 중입니다"
            
        return JSONResponse(format_api_response(
            success=True,
            message=message
        ))
            
    except Exception as e:
        logger.error(f"스케줄러 시작 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.post("/api/scheduler/stop")
async def stop_scheduler():
    """스케줄러 중지"""
    try:
        if scheduler_service.is_running:
            scheduler_service.stop_scheduler()
            message = "스케줄러가 중지되었습니다"
        else:
            message = "스케줄러가 이미 중지되어 있습니다"
            
        return JSONResponse(format_api_response(
            success=True,
            message=message
        ))
            
    except Exception as e:
        logger.error(f"스케줄러 중지 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.post("/api/run-maintenance")
async def run_manual_maintenance():
    """수동 유지보수 실행"""
    try:
        result = await scheduler_service.run_manual_maintenance()
        return JSONResponse(format_api_response(
            success=True,
            data=result
        ))
    except Exception as e:
        logger.error(f"❌ 유지보수 실행 실패: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.get("/api/debug/stats")
async def debug_stats():
    """디버깅용 통계 엔드포인트"""
    try:
        stats = await db_manager.get_database_stats()
        
        return format_api_response(
            success=True,
            data={
                "raw_stats": stats,
                "processed_stats": {
                    "total_accounts": stats.get('total_accounts', 0) if stats else 0,
                    "total_properties": stats.get('total_properties', 0) if stats else 0,
                    "active_users": stats.get('active_users', 0) if stats else 0,
                    "expiring_soon": stats.get('expiring_soon', 0) if stats else 0,
                    "total_notifications": stats.get('total_notifications', 0) if stats else 0,
                    "total_audit_logs": stats.get('total_audit_logs', 0) if stats else 0,
                    "total_registrations": stats.get('total_registrations', 0) if stats else 0
                },
                "stats_type": type(stats).__name__,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        return format_api_response(
            success=False,
            message=str(e),
            data={"timestamp": datetime.now().isoformat()}
        )


# 메일 전송 이력 관리 API
@router.get("/api/notification-logs")
async def get_notification_logs():
    """메일 전송 이력 조회"""
    try:
        logs = await db_manager.execute_query(
            """
            SELECT user_email, notification_type, message_subject as subject, sent_at, status, 
                   CASE 
                       WHEN status = 'sent' THEN '✅'
                       WHEN status = 'failed' THEN '❌'
                       ELSE '⏳'
                   END as status_icon
            FROM notification_logs 
            ORDER BY sent_at DESC 
            LIMIT 100
            """
        )
        
        return JSONResponse(format_api_response(
            success=True,
            data={"logs": logs, "total": len(logs)}
        ))
        
    except Exception as e:
        logger.error(f"알림 로그 조회 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.delete("/api/notification-logs")
async def clear_all_notification_logs():
    """모든 메일 전송 이력 초기화"""
    try:
        # 삭제 전 백업을 위한 카운트
        count_result = await db_manager.execute_query(
            "SELECT COUNT(*) as total FROM notification_logs"
        )
        total_count = count_result[0]['total'] if count_result else 0
        
        # 모든 로그 삭제
        await db_manager.execute_update("DELETE FROM notification_logs")
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"총 {total_count}개의 알림 로그가 삭제되었습니다"
        ))
        
    except Exception as e:
        logger.error(f"알림 로그 초기화 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.delete("/api/notification-logs/today")
async def clear_today_notification_logs():
    """오늘 날짜의 알림 전송 이력만 삭제"""
    try:
        # 오늘 날짜의 로그 카운트
        count_result = await db_manager.execute_query(
            "SELECT COUNT(*) as total FROM notification_logs WHERE DATE(sent_at) = DATE('now')"
        )
        total_count = count_result[0]['total'] if count_result else 0
        
        if total_count == 0:
            return JSONResponse(format_api_response(
                success=False,
                message="오늘 날짜의 알림 로그가 없습니다"
            ))
        
        # 오늘 날짜의 로그 삭제
        await db_manager.execute_update(
            "DELETE FROM notification_logs WHERE DATE(sent_at) = DATE('now')"
        )
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"오늘 날짜의 {total_count}개 알림 로그가 삭제되었습니다"
        ))
        
    except Exception as e:
        logger.error(f"오늘 알림 로그 삭제 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.delete("/api/notification-logs/{email}")
async def clear_notification_logs_by_email(email: str):
    """특정 이메일의 알림 전송 이력 삭제"""
    try:
        # 삭제 전 카운트
        count_result = await db_manager.execute_query(
            "SELECT COUNT(*) as total FROM notification_logs WHERE user_email = ?",
            (email,)
        )
        total_count = count_result[0]['total'] if count_result else 0
        
        if total_count == 0:
            return JSONResponse(format_api_response(
                success=False,
                message=f"{email}에 대한 알림 로그가 없습니다"
            ))
        
        # 특정 이메일의 로그 삭제
        await db_manager.execute_update(
            "DELETE FROM notification_logs WHERE user_email = ?",
            (email,)
        )
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"{email}의 {total_count}개 알림 로그가 삭제되었습니다"
        ))
        
    except Exception as e:
        logger.error(f"특정 이메일 알림 로그 삭제 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.post("/api/process-expired-users")
async def process_expired_users():
    """만료된 사용자 삭제 및 알림 발송"""
    try:
        results = await notification_service.send_deletion_notice_for_expired_users()
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"만료 사용자 처리 완료",
            data=results
        ))
        
    except Exception as e:
        logger.error(f"만료 사용자 처리 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=f"만료 사용자 처리 실패: {str(e)}"
        ), status_code=500)


@router.post("/api/approve-editor")
async def approve_editor_request(request: Request):
    """Editor 권한 요청 승인 및 알림 발송"""
    try:
        data = await request.json()
        user_email = data.get('user_email')
        property_id = data.get('property_id', '462884506')  # 기본값
        
        if not user_email:
            return JSONResponse(format_api_response(
                success=False,
                message="user_email이 필요합니다"
            ), status_code=400)
        
        # 1. 사용자 권한을 active로 변경하고 editor 권한 설정
        expiry_date = datetime.now() + timedelta(days=7)  # Editor 권한은 7일간 유효
        
        # 데이터베이스에서 사용자 정보 업데이트
        await db_manager.execute_update(
            """
            UPDATE user_registrations 
            SET status = 'active', 권한 = 'editor', 종료일 = ?, updated_at = CURRENT_TIMESTAMP
            WHERE 등록_계정 = ? AND property_id = ?
            """,
            (expiry_date.strftime('%Y-%m-%d'), user_email, property_id)
        )
        
        # 2. 프로퍼티 정보 조회
        property_info = await db_manager.execute_query(
            "SELECT property_display_name FROM ga4_properties WHERE property_id = ?",
            (property_id,)
        )
        property_name = property_info[0]['property_display_name'] if property_info else '알 수 없는 프로퍼티'
        
        # 3. 승인 알림 데이터 준비
        approval_data = {
            'user_email': user_email,
            'email': user_email,
            'property_name': property_name,
            'property_id': property_id,
            'role': 'editor',
            'expiry_date': expiry_date.isoformat(),
            'applicant': user_email,  # 신청자 정보
            'approved_at': datetime.now().isoformat()
        }
        
        # 4. Editor 승인 알림 발송
        approval_success = await notification_service.send_editor_approved_notification(approval_data)
        
        # 5. Welcome 알림도 발송 (새로운 권한이므로)
        welcome_success = await notification_service.send_welcome_notification(approval_data)
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"Editor 권한 승인 완료",
            data={
                'user_email': user_email,
                'property_name': property_name,
                'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                'approval_notification_sent': approval_success,
                'welcome_notification_sent': welcome_success
            }
        ))
        
    except Exception as e:
        logger.error(f"Editor 권한 승인 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=f"Editor 권한 승인 실패: {str(e)}"
        ), status_code=500)


@router.post("/api/test-editor-approval")
async def test_editor_approval(request: Request):
    """Editor 승인 프로세스 테스트 (실제 DB 변경 없이 메일만 발송)"""
    try:
        data = await request.json()
        user_email = data.get('user_email', 'test@example.com')
        
        from datetime import datetime, timedelta
        
        # 테스트 데이터 준비
        test_data = {
            'user_email': user_email,
            'email': user_email,
            'property_name': 'Amorepacific GA4 테스트',
            'property_id': '462884506',
            'role': 'editor',
            'expiry_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'applicant': user_email,
            'approved_at': datetime.now().isoformat()
        }
        
        # Editor 승인 알림 발송
        success = await notification_service.send_editor_approved_notification(test_data)
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"Editor 승인 테스트 메일 발송 {'성공' if success else '실패'}",
            data={
                'user_email': user_email,
                'notification_sent': success,
                'test_mode': True
            }
        ))
        
    except Exception as e:
        logger.error(f"Editor 승인 테스트 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=f"Editor 승인 테스트 실패: {str(e)}"
        ), status_code=500)


@router.get("/api/pending-editor-requests")
async def get_pending_editor_requests():
    """승인 대기 중인 Editor 권한 요청 조회"""
    try:
        pending_requests = await db_manager.execute_query(
            """
            SELECT ur.등록_계정 as user_email, ur.신청자 as applicant, 
                   p.property_display_name as property_name, ur.property_id,
                   ur.created_at, 'Editor 권한 신청' as reason
            FROM user_registrations ur
            JOIN ga4_properties p ON ur.property_id = p.property_id
            WHERE ur.status = 'pending_approval' AND ur.권한 = 'editor'
            ORDER BY ur.created_at DESC
            """
        )
        
        return JSONResponse(format_api_response(
            success=True,
            data={'requests': pending_requests, 'total': len(pending_requests)}
        ))
        
    except Exception as e:
        logger.error(f"승인 대기 Editor 요청 조회 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


# Admin 권한 관련 API
@router.get("/api/pending-admin-requests")
async def get_pending_admin_requests():
    """승인 대기 중인 Admin 권한 요청 조회"""
    try:
        pending_requests = await db_manager.execute_query(
            """
            SELECT ur.등록_계정 as user_email, ur.신청자 as applicant, 
                   p.property_display_name as property_name, ur.property_id,
                   ur.created_at, 'Admin 권한 신청' as reason
            FROM user_registrations ur
            JOIN ga4_properties p ON ur.property_id = p.property_id
            WHERE ur.status = 'pending_approval' AND ur.권한 = 'admin'
            ORDER BY ur.created_at DESC
            """
        )
        
        return JSONResponse(format_api_response(
            success=True,
            data={'requests': pending_requests, 'total': len(pending_requests)}
        ))
        
    except Exception as e:
        logger.error(f"승인 대기 Admin 요청 조회 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.post("/api/approve-admin")
async def approve_admin_request(request: Request):
    """Admin 권한 요청 승인 및 GA4 등록"""
    try:
        data = await request.json()
        user_email = data.get('user_email')
        property_id = data.get('property_id', '462884506')  # 기본값
        
        if not user_email:
            return JSONResponse(format_api_response(
                success=False,
                message="user_email이 필요합니다"
            ), status_code=400)
        
        # GA4UserManager 초기화 확인 및 수행
        if ga4_user_manager.client is None:
            try:
                await ga4_user_manager.initialize()
                logger.info("✅ GA4UserManager 초기화 완료")
            except Exception as init_error:
                logger.warning(f"⚠️ GA4UserManager 초기화 실패 (테스트 모드 사용): {init_error}")
        
        # 1. 등록 정보 조회
        registration = await db_manager.execute_query(
            """SELECT ur.*, p.property_id 
               FROM user_registrations ur
               JOIN ga4_properties p ON ur.property_id = p.property_id
               WHERE ur.등록_계정 = ? AND ur.property_id = ? AND ur.status = 'pending_approval' AND ur.권한 = 'admin'""",
            (user_email, property_id)
        )
        
        if not registration:
            return JSONResponse(format_api_response(
                success=False,
                message="승인 대기 중인 Admin 등록을 찾을 수 없습니다"
            ), status_code=404)
        
        reg = registration[0]
        
        # 2. GA4에 실제 사용자 등록
        success, message, user_link_name = await ga4_user_manager.register_user_to_property(
            property_id=property_id,
            email=user_email,
            role='admin'
        )
        
        if not success:
            return JSONResponse(format_api_response(
                success=False,
                message=f"GA4 등록 실패: {message}"
            ), status_code=500)
        
        # 3. 데이터베이스에서 사용자 정보 업데이트
        expiry_date = datetime.now() + timedelta(days=7)  # Admin 권한은 7일간 유효
        
        await db_manager.execute_update(
            """
            UPDATE user_registrations 
            SET status = 'active', ga4_registered = 1, user_link_name = ?, 종료일 = ?, updated_at = ?
            WHERE 등록_계정 = ? AND property_id = ? AND 권한 = 'admin'
            """,
            (user_link_name, expiry_date, datetime.now(), user_email, property_id)
        )
        
        # 4. 프로퍼티 정보 조회
        property_info = await db_manager.execute_query(
            "SELECT property_display_name FROM ga4_properties WHERE property_id = ?",
            (property_id,)
        )
        property_name = property_info[0]['property_display_name'] if property_info else '알 수 없는 프로퍼티'
        
        # 5. 승인 알림 데이터 준비
        approval_data = {
            'user_email': user_email,
            'email': user_email,
            'property_name': property_name,
            'property_id': property_id,
            'role': 'admin',
            'expiry_date': expiry_date.isoformat(),
            'applicant': user_email,  # 신청자 정보
            'approved_at': datetime.now().isoformat(),
            'ga4_registered': True,
            'user_link_name': user_link_name
        }
        
        # 6. Admin 승인 알림 발송 (우선순위 발송)
        approval_success = await notification_service.send_admin_approved_notification(approval_data)
        
        # 7. Welcome 알림도 발송 (새로운 권한이므로)
        welcome_success = await notification_service.send_welcome_notification(approval_data)
        
        logger.info(f"✅ Admin 권한 승인 완료: {user_email} -> {property_name} (GA4 등록: {user_link_name})")
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"Admin 권한 승인 및 GA4 등록 완료",
            data={
                'user_email': user_email,
                'property_name': property_name,
                'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                'ga4_registered': True,
                'user_link_name': user_link_name,
                'approval_notification_sent': approval_success,
                'welcome_notification_sent': welcome_success
            }
        ))
        
    except Exception as e:
        logger.error(f"Admin 권한 승인 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=f"Admin 권한 승인 실패: {str(e)}"
        ), status_code=500)


@router.post("/api/test-admin-approval")
async def test_admin_approval(request: Request):
    """Admin 승인 프로세스 테스트 (실제 DB 변경 없이 메일만 발송)"""
    try:
        data = await request.json()
        user_email = data.get('user_email', 'test@example.com')
        
        from datetime import datetime, timedelta
        
        # 테스트 데이터 준비
        test_data = {
            'user_email': user_email,
            'email': user_email,
            'property_name': 'Amorepacific GA4 테스트',
            'property_id': '462884506',
            'role': 'admin',
            'expiry_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'applicant': user_email,
            'approved_at': datetime.now().isoformat()
        }
        
        # Admin 승인 알림 발송
        success = await notification_service.send_admin_approved_notification(test_data)
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"Admin 승인 테스트 메일 발송 {'성공' if success else '실패'}",
            data={
                'user_email': user_email,
                'notification_sent': success,
                'test_mode': True
            }
        ))
        
    except Exception as e:
        logger.error(f"Admin 승인 테스트 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=f"Admin 승인 테스트 실패: {str(e)}"
        ), status_code=500)


@router.post("/api/process-admin-downgrade")
async def process_admin_downgrade():
    """Admin 권한 자동 다운그레이드 처리"""
    try:
        downgraded_count = await scheduler_service.process_admin_downgrade()
        
        return JSONResponse(format_api_response(
            success=True,
            message=f"Admin 권한 다운그레이드 완료: {downgraded_count}명 처리"
        ))
        
    except Exception as e:
        logger.error(f"Admin 권한 다운그레이드 중 오류: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=str(e)
        ))


@router.post("/api/test/verify-admin-registration")
async def verify_admin_registration(request: Request):
    """Admin 사용자의 실제 GA4 등록 상태 검증"""
    try:
        data = await request.json()
        user_email = data.get('user_email')
        property_id = data.get('property_id', '462884506')
        
        if not user_email:
            return JSONResponse(format_api_response(
                success=False,
                message="user_email이 필요합니다"
            ), status_code=400)
        
        # 1. 데이터베이스에서 사용자 조회
        db_user = await db_manager.execute_query(
            """SELECT id, 등록_계정, property_id, 권한, status, ga4_registered, user_link_name, 
                      created_at, 종료일 
               FROM user_registrations 
               WHERE 등록_계정 = ? AND property_id = ? AND 권한 = 'admin'
               ORDER BY created_at DESC LIMIT 1""",
            (user_email, property_id)
        )
        
        if not db_user:
            return JSONResponse(format_api_response(
                success=False,
                message=f"데이터베이스에서 {user_email}의 Admin 등록 정보를 찾을 수 없습니다"
            ), status_code=404)
        
        user_info = db_user[0]
        
        # 2. GA4UserManager를 통해 실제 등록 상태 확인
        ga4_manager = ga4_user_manager
        try:
            await ga4_manager.initialize()
            ga4_init_success = True
        except Exception as e:
            logger.warning(f"GA4 초기화 실패, 테스트 모드로 진행: {e}")
            ga4_init_success = False
        
        # 3. 프로퍼티에서 사용자 목록 조회
        actual_registration_status = "unknown"
        actual_roles = []
        ga4_error = None
        
        try:
            users = await ga4_manager.list_property_users(property_id)
            
            # 사용자 찾기
            found_user = None
            for user in users:
                if user_email.lower() in user.get('email', '').lower():
                    found_user = user
                    break
            
            if found_user:
                actual_registration_status = "registered"
                actual_roles = found_user.get('roles', [])
            else:
                actual_registration_status = "not_found"
        except Exception as e:
            ga4_error = str(e)
            if "401" in str(e) or "credential" in str(e).lower():
                actual_registration_status = "auth_error"
            else:
                actual_registration_status = "api_error"
        
        # 4. 결과 준비
        result = {
            "user_email": user_email,
            "property_id": property_id,
            "database_info": {
                "id": user_info['id'],
                "status": user_info['status'],
                "ga4_registered": bool(user_info['ga4_registered']),
                "user_link_name": user_info['user_link_name'],
                "created_at": user_info['created_at'],
                "expiry_date": user_info['종료일']
            },
            "ga4_api_info": {
                "initialization_success": ga4_init_success,
                "registration_status": actual_registration_status,
                "actual_roles": actual_roles,
                "error": ga4_error
            },
            "verification_result": {
                "database_says_registered": bool(user_info['ga4_registered']),
                "ga4_api_says_registered": actual_registration_status == "registered",
                "data_consistency": bool(user_info['ga4_registered']) == (actual_registration_status == "registered") 
                                   or actual_registration_status in ["auth_error", "api_error", "unknown"]
            }
        }
        
        # 5. 권한 레벨 분석
        if actual_roles:
            role_analysis = []
            for role in actual_roles:
                role_str = str(role).lower()
                if 'admin' in role_str:
                    role_analysis.append("Administrator")
                elif 'edit' in role_str:
                    role_analysis.append("Editor")
                elif 'analyz' in role_str:
                    role_analysis.append("Analyst")
                elif 'read' in role_str:
                    role_analysis.append("Viewer")
                else:
                    role_analysis.append(f"Unknown: {role}")
            result["verification_result"]["role_analysis"] = role_analysis
        
        return JSONResponse(format_api_response(
            success=True,
            message="Admin 등록 상태 검증 완료",
            data=result
        ))
        
    except Exception as e:
        logger.error(f"Admin 등록 검증 실패: {e}")
        return JSONResponse(format_api_response(
            success=False,
            message=f"검증 실패: {str(e)}"
        ), status_code=500)


@router.post("/api/test/simple-db-check")
async def simple_db_check(request: Request):
    """간단한 데이터베이스 조회 테스트"""
    try:
        data = await request.json()
        user_email = data.get('user_email', 'wonyoungseong@gmail.com')
        property_id = data.get('property_id', '462884506')
        
        logger.info(f"테스트 시작: {user_email}, {property_id}")
        
        # 데이터베이스에서 사용자 조회
        db_user = await db_manager.execute_query(
            """SELECT id, 등록_계정, property_id, 권한, status, ga4_registered, user_link_name
               FROM user_registrations 
               WHERE 등록_계정 = ? AND property_id = ? AND 권한 = 'admin'
               ORDER BY id DESC LIMIT 1""",
            (user_email, property_id)
        )
        
        logger.info(f"쿼리 결과: {db_user}")
        logger.info(f"결과 타입: {type(db_user)}")
        logger.info(f"결과 길이: {len(db_user) if db_user else 0}")
        
        if not db_user:
            return JSONResponse(format_api_response(
                success=False,
                message=f"사용자를 찾을 수 없음: {user_email}"
            ))
        
        user_info = db_user[0]
        logger.info(f"사용자 정보: {user_info}")
        
        return JSONResponse(format_api_response(
            success=True,
            message="조회 성공",
            data={
                "user_email": user_email,
                "property_id": property_id,
                "user_id": user_info['id'],
                "status": user_info['status'],
                "ga4_registered": bool(user_info['ga4_registered']),
                "user_link_name": user_info['user_link_name']
            }
        ))
        
    except Exception as e:
        logger.error(f"테스트 API 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return JSONResponse(format_api_response(
            success=False,
            message=f"오류: {str(e)}"
        ), status_code=500)


@router.get("/api/health")
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


@router.get("/api/system-status")
async def get_system_status():
    """시스템 전체 상태 조회"""
    try:
        # 데이터베이스 상태
        db_test = await db_manager.execute_query("SELECT 1 as test")
        db_stats = await db_manager.get_database_stats()
        
        # 스케줄러 상태
        scheduler_status = scheduler_service.get_scheduler_status()
        
        # 알림 서비스 상태
        notification_stats = await notification_service.get_notification_statistics()
        
        return format_api_response(
            success=True,
            data={
                "database": {
                    "status": "healthy" if db_test else "unhealthy",
                    "stats": db_stats
                },
                "scheduler": scheduler_status,
                "notifications": notification_stats,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"❌ 시스템 상태 조회 실패: {e}")
        return format_api_response(
            success=False,
            message=f"시스템 상태 조회 오류: {str(e)}"
        ) 