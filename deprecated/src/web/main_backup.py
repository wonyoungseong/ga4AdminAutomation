#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 웹 애플리케이션
=================================

FastAPI 기반의 웹 인터페이스를 제공합니다.
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime, timedelta
import csv
import io
from fastapi.responses import StreamingResponse

from ..infrastructure.database import db_manager
from ..services.property_scanner_service import GA4PropertyScannerService
from ..services.ga4_user_manager import ga4_user_manager
from ..core.logger import get_ga4_logger
from ..services.notifications.notification_service import notification_service, NotificationService
from ..api.scheduler import scheduler_service, ga4_scheduler

# 로거 초기화
logger = get_ga4_logger()

# 전역 서비스 변수
property_scanner = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    global property_scanner
    
    # 시작 시 초기화
    try:
        # 데이터베이스 초기화
        await db_manager.initialize_database()
        
        # GA4 사용자 관리자 초기화
        await ga4_user_manager.initialize()
        
        # 프로퍼티 스캐너 초기화
        property_scanner = GA4PropertyScannerService()
        
        # 알림 서비스 초기화
        await notification_service.initialize()
        
        # 스케줄러 서비스 초기화 및 시작
        await scheduler_service.initialize()
        scheduler_service.start_scheduler()
        
        logger.info("✅ GA4 권한 관리 시스템이 성공적으로 시작되었습니다")
        
    except Exception as e:
        logger.error(f"❌ 시스템 시작 중 오류 발생: {e}")
        raise
    
    yield
    
    # 종료 시 정리
    try:
        # 스케줄러 중지
        scheduler_service.stop_scheduler()
        
        # 데이터베이스 연결 종료
        await db_manager.close()
        
        logger.info("✅ GA4 권한 관리 시스템이 정상적으로 종료되었습니다")
        
    except Exception as e:
        logger.error(f"❌ 시스템 종료 중 오류 발생: {e}")


class DictObj:
    """dict를 객체처럼 접근할 수 있도록 하는 클래스"""
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)
    
    def __getattr__(self, name):
        return None


# FastAPI 앱 생성
app = FastAPI(
    title="GA4 권한 관리 시스템",
    description="GA4 계정 및 프로퍼티 권한을 관리하는 웹 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# 템플릿 설정
templates = Jinja2Templates(directory="src/web/templates")

# 정적 파일 설정
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")


async def get_dashboard_data():
    """대시보드 데이터 조회"""
    try:
        # 등록 가능한 프로퍼티 조회
        try:
            if property_scanner is not None:
                properties = await property_scanner.get_available_properties()
            else:
                logger.warning("⚠️ 프로퍼티 스캐너가 초기화되지 않음")
                properties = []
        except Exception as e:
            logger.warning(f"⚠️ 프로퍼티 스캔 서비스 오류: {e}")
            properties = []
        
        # 현재 등록된 사용자 현황
        registrations = await db_manager.execute_query(
            """SELECT ur.id, ur.신청자 as applicant, ur.등록_계정 as user_email, 
                      ur.property_id, ur.권한 as permission_level, ur.status,
                      ur.신청일 as created_at, ur.종료일 as expiry_date, ur.ga4_registered,
                      p.property_display_name as property_name, 
                      p.property_display_name as property_display_name,
                      a.account_display_name as account_name
               FROM user_registrations ur
               JOIN ga4_properties p ON ur.property_id = p.property_id
               JOIN ga4_accounts a ON p.account_id = a.account_id
               ORDER BY ur.신청일 DESC"""
        )
        
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
        
        # 알림 통계
        notification_stats = {"total_sent": 0, "today_sent": 0, "pending_notifications": 0, "last_sent": "없음"}
        
        # 최근 로그
        recent_logs = []
        
        return {
            "properties": properties,
            "registrations": registrations,
            "stats": stats,
            "notification_stats": notification_stats,
            "recent_logs": recent_logs
        }
        
    except Exception as e:
        logger.error(f"❌ 대시보드 데이터 조회 실패: {e}")
        return {
            "properties": [],
            "registrations": [],
            "stats": {},
            "notification_stats": {"total_sent": 0, "today_sent": 0, "pending_notifications": 0, "last_sent": "없음"},
            "recent_logs": []
        }


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """메인 대시보드"""
    try:
        # 등록 가능한 프로퍼티 조회
        try:
            if property_scanner is not None:
                properties = await property_scanner.get_available_properties()
            else:
                logger.warning("⚠️ 프로퍼티 스캐너가 초기화되지 않음")
                properties = []
        except Exception as e:
            logger.warning(f"⚠️ 프로퍼티 스캔 서비스 오류: {e}")
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
        
        # dict를 객체처럼 접근할 수 있도록 변환
        accounts = [DictObj({
            'account_id': acc.get('account_id', ''),
            'account_name': acc.get('account_name', ''),
            'display_name': acc.get('display_name', ''),
            'last_updated': str(acc.get('last_updated', '')) if acc.get('last_updated') else ''
        }) for acc in accounts_raw]
        
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
        
        all_properties = [DictObj({
            'property_id': prop.get('property_id', ''),
            'property_name': prop.get('property_name', ''),
            'account_name': prop.get('account_name', ''),
            'time_zone': prop.get('time_zone', 'Asia/Seoul'),
            'last_updated': str(prop.get('last_updated', '')) if prop.get('last_updated') else ''
        }) for prop in all_properties_raw]
        
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
        
        registrations = [DictObj({
            'id': reg.get('id', ''),
            'applicant': reg.get('applicant', ''),
            'user_email': reg.get('user_email', ''),
            'property_id': reg.get('property_id', ''),
            'property_name': reg.get('property_name', ''),
            'account_name': reg.get('account_name', ''),
            'permission_level': reg.get('permission_level', ''),
            'status': reg.get('status', ''),
            'created_at': str(reg.get('created_at', '')) if reg.get('created_at') else '',
            'expiry_date': str(reg.get('expiry_date', '')) if reg.get('expiry_date') else '',
            'ga4_registered': reg.get('ga4_registered', 0)
        }) for reg in registrations_raw]
        
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


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """사용자 등록 페이지"""
    try:
        # 등록 가능한 프로퍼티 목록
        properties = await property_scanner.get_available_properties()
        
        return templates.TemplateResponse("register.html", {
            "request": request,
            "properties": properties
        })
        
    except Exception as e:
        logger.error(f"❌ 등록 페이지 로딩 실패: {e}")
        raise HTTPException(status_code=500, detail="등록 페이지 로딩에 실패했습니다.")


@app.post("/api/register")
async def register_users(
    신청자: str = Form(...),
    등록_계정_목록: str = Form(...),  # 쉼표로 구분된 이메일 목록
    property_ids: List[str] = Form(...),
    권한: str = Form(...)
):
    """사용자 등록 API"""
    try:
        # 이메일 목록 파싱
        email_list = [email.strip() for email in 등록_계정_목록.split(',') if email.strip()]
        
        if not email_list:
            raise HTTPException(status_code=400, detail="등록할 이메일을 입력해주세요.")
        
        if not property_ids:
            raise HTTPException(status_code=400, detail="프로퍼티를 선택해주세요.")
        
        results = []
        
        for property_id in property_ids:
            for email in email_list:
                try:
                    # 만료일 계산 (Analyst: 30일, Editor: 7일)
                    종료일 = datetime.now() + timedelta(days=30 if 권한 == 'analyst' else 7)
                    
                    # 데이터베이스에 등록
                    registration_id = await db_manager.execute_insert(
                        """INSERT INTO user_registrations 
                           (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, approval_required, status, ga4_registered)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            신청자, email, property_id, 권한, datetime.now(), 종료일,
                            권한 == 'editor',  # Editor는 승인 필요
                            'pending_approval' if 권한 == 'editor' else 'active',
                            0  # 아직 GA4에 등록되지 않음
                        )
                    )
                    
                    # Editor가 아닌 경우 즉시 GA4에 등록 시도
                    if 권한 != 'editor':
                        try:
                            success, message, user_link_name = await ga4_user_manager.register_user_to_property(
                                property_id=property_id,
                                email=email,
                                role=권한
                            )
                            
                            if success:
                                # GA4 등록 성공 시 데이터베이스 업데이트
                                await db_manager.execute_update(
                                    """UPDATE user_registrations 
                                       SET ga4_registered = 1, user_link_name = ?, updated_at = ?
                                       WHERE id = ?""",
                                    (user_link_name, datetime.now(), registration_id)
                                )
                                logger.info(f"✅ GA4 등록 완료: {email} -> {property_id}")
                            else:
                                logger.warning(f"⚠️ GA4 등록 실패: {email} -> {message}")
                                
                        except Exception as ga4_error:
                            logger.error(f"❌ GA4 등록 중 오류: {email} -> {ga4_error}")
                    
                    results.append({
                        "email": email,
                        "property_id": property_id,
                        "status": "success",
                        "registration_id": registration_id
                    })
                    
                    logger.info(f"✅ 사용자 등록 성공: {email} -> {property_id} ({권한})")
                    
                except Exception as e:
                    logger.error(f"❌ 사용자 등록 실패 {email}: {e}")
                    results.append({
                        "email": email,
                        "property_id": property_id,
                        "status": "error",
                        "error": str(e)
                    })
        
        # 등록 성공 시 즉시 알림 발송
        if results[0]['status'] == 'success':
            try:
                await notification_service.send_immediate_approval_notification({
                    '신청자': 신청자,
                    '등록_계정': email_list[0],
                    'property_id': property_ids[0],
                    '권한': 권한,
                    '종료일': 종료일.strftime('%Y-%m-%d') if 종료일 else 'N/A',
                    'account_id': None  # 필요시 추가
                })
            except Exception as e:
                logger.warning(f"⚠️ 즉시 알림 발송 실패: {e}")
        
        return JSONResponse({
            "success": True,
            "message": f"{len([r for r in results if r['status'] == 'success'])}건 등록 완료",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"❌ 사용자 등록 API 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scan")
async def scan_properties():
    """프로퍼티 스캔 API"""
    try:
        logger.info("🔍 수동 프로퍼티 스캔 시작")
        
        if property_scanner is None:
            raise HTTPException(status_code=503, detail="프로퍼티 스캐너가 초기화되지 않았습니다")
        
        result = await property_scanner.scan_all_accounts_and_properties()
        
        return JSONResponse({
            "success": True,
            "message": "스캔이 완료되었습니다.",
            "result": {
                "accounts_found": result.accounts_found,
                "accounts_new": result.accounts_new,
                "accounts_updated": result.accounts_updated,
                "properties_found": result.properties_found,
                "properties_new": result.properties_new,
                "properties_updated": result.properties_updated,
                "scan_duration": result.scan_duration
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 프로퍼티 스캔 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties")
async def get_properties():
    """등록 가능한 프로퍼티 목록 API"""
    try:
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


@app.get("/api/stats")
async def get_stats():
    """시스템 통계 API"""
    try:
        stats = await db_manager.get_database_stats()
        
        return JSONResponse({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"❌ 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-queue")
async def process_registration_queue():
    """등록 대기열 처리 API"""
    try:
        logger.info("🔄 수동 등록 대기열 처리 시작")
        await ga4_user_manager.process_registration_queue()
        await ga4_user_manager.process_expiration_queue()
        
        return JSONResponse({
            "success": True,
            "message": "등록 대기열 처리 완료"
        })
        
    except Exception as e:
        logger.error(f"❌ 등록 대기열 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/approve/{registration_id}")
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
            
            return JSONResponse({
                "success": True,
                "message": "Editor 권한이 승인되었습니다"
            })
        else:
            raise HTTPException(status_code=500, detail=f"GA4 등록 실패: {message}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Editor 권한 승인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reject/{registration_id}")
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
        
        return JSONResponse({
            "success": True,
            "message": "Editor 권한 요청이 거부되었습니다"
        })
        
    except Exception as e:
        logger.error(f"❌ Editor 권한 거부 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extend/{registration_id}")
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
        
        return JSONResponse({
            "success": True,
            "message": f"권한이 {new_expiry.strftime('%Y-%m-%d')}까지 연장되었습니다"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 권한 연장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/registration/{registration_id}")
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
        
        return JSONResponse({
            "success": True,
            "message": "사용자 등록이 삭제되었습니다"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 사용자 등록 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/property/{property_id}/users")
async def get_property_users(property_id: str):
    """프로퍼티 사용자 목록 조회 API"""
    try:
        users = await ga4_user_manager.list_property_users(property_id)
        
        return JSONResponse({
            "success": True,
            "users": users,
            "count": len(users)
        })
        
    except Exception as e:
        logger.error(f"❌ 프로퍼티 사용자 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 새로운 알림 관련 API 엔드포인트들
@app.post("/api/send-test-notification")
async def send_test_notification(request: Request):
    """테스트 알림 발송"""
    try:
        data = await request.json()
        email = data.get("email")
        notification_type = data.get("type", "welcome")
        
        if not email:
            return {"success": False, "error": "이메일이 필요합니다"}
        
        # 테스트 알림 발송
        success = await notification_service.send_test_notification(
            email, notification_type
        )
        
        if success:
            return {"success": True, "message": f"테스트 알림이 {email}로 발송되었습니다"}
        else:
            return {"success": False, "error": "알림 발송에 실패했습니다"}
            
    except Exception as e:
        logger.error(f"테스트 알림 발송 중 오류: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/process-expiry-notifications")
async def process_expiry_notifications():
    """만료 알림 처리"""
    try:
        results = await notification_service.process_expiry_notifications()
        
        total_sent = sum(results.values())
        
        return {
            "success": True,
            "message": f"만료 알림 처리 완료: 총 {total_sent}개 발송",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"만료 알림 처리 중 오류: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/process-editor-downgrade")
async def process_editor_downgrade():
    """Editor 권한 자동 다운그레이드 처리"""
    try:
        downgraded_count = await scheduler_service.process_editor_downgrade()
        
        return {
            "success": True,
            "message": f"Editor 권한 다운그레이드 완료: {downgraded_count}명 처리"
        }
        
    except Exception as e:
        logger.error(f"Editor 권한 다운그레이드 중 오류: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/notification-stats")
async def get_notification_stats():
    """알림 통계 조회"""
    try:
        stats = await notification_service.get_notification_stats()
        return {"success": True, "data": stats}
        
    except Exception as e:
        logger.error(f"알림 통계 조회 중 오류: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/scheduler-status")
async def get_scheduler_status():
    """스케줄러 상태 조회"""
    try:
        status = scheduler_service.get_scheduler_status()
        return {"success": True, "data": status}
        
    except Exception as e:
        logger.error(f"스케줄러 상태 조회 중 오류: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/scheduler/start")
async def start_scheduler():
    """스케줄러 시작"""
    try:
        if not scheduler_service.is_running:
            scheduler_service.start_scheduler()
            return {"success": True, "message": "스케줄러가 시작되었습니다"}
        else:
            return {"success": True, "message": "스케줄러가 이미 실행 중입니다"}
            
    except Exception as e:
        logger.error(f"스케줄러 시작 중 오류: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """스케줄러 중지"""
    try:
        if scheduler_service.is_running:
            scheduler_service.stop_scheduler()
            return {"success": True, "message": "스케줄러가 중지되었습니다"}
        else:
            return {"success": True, "message": "스케줄러가 이미 중지되어 있습니다"}
            
    except Exception as e:
        logger.error(f"스케줄러 중지 중 오류: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/run-maintenance")
async def run_manual_maintenance():
    """수동 유지보수 실행"""
    try:
        result = await scheduler_service.run_manual_maintenance()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"❌ 유지보수 실행 실패: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/debug/stats")
async def debug_stats():
    """디버깅용 통계 엔드포인트"""
    try:
        stats = await db_manager.get_database_stats()
        
        return {
            "success": True,
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
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """테스트 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>통계 테스트</title>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>GA4 통계 테스트</h1>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5>API 응답</h5>
                            <pre id="api-response">로딩 중...</pre>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h5>통계 카드</h5>
                            <div class="card bg-primary text-white mb-2">
                                <div class="card-body">
                                    <h6>총 계정</h6>
                                    <h3 id="total-accounts">-</h3>
                                </div>
                            </div>
                            <div class="card bg-success text-white">
                                <div class="card-body">
                                    <h6>총 프로퍼티</h6>
                                    <h3 id="total-properties">-</h3>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <button class="btn btn-primary mt-3" onclick="refreshStats()">통계 새로고침</button>
        </div>
        
        <script>
        async function refreshStats() {
            try {
                console.log('📊 통계 새로고침 시작...');
                const response = await fetch('/api/stats');
                const result = await response.json();
                
                console.log('📊 API 응답:', result);
                document.getElementById('api-response').textContent = JSON.stringify(result, null, 2);
                
                if (result.success && result.stats) {
                    const stats = result.stats;
                    document.getElementById('total-accounts').textContent = stats.total_accounts || 0;
                    document.getElementById('total-properties').textContent = stats.total_properties || 0;
                    console.log('✅ 통계 업데이트 완료');
                } else {
                    console.error('❌ 통계 응답 오류:', result);
                }
            } catch (error) {
                console.error('❌ 통계 새로고침 오류:', error);
                document.getElementById('api-response').textContent = 'Error: ' + error.message;
            }
        }
        
        // 페이지 로드 시 자동 실행
        document.addEventListener('DOMContentLoaded', refreshStats);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/test-js")
async def test_js_page():
    """JavaScript 테스트 페이지"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JavaScript 테스트</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1>JavaScript 테스트 페이지</h1>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5>API 테스트</h5>
                        <button class="btn btn-primary" onclick="testStatsAPI()">통계 API 테스트</button>
                        <div id="api-result" class="mt-3"></div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5>통계 카드 테스트</h5>
                        <div id="test-stats">
                            <p>계정: <span id="accounts-display">로딩 중...</span>개</p>
                            <p>프로퍼티: <span id="properties-display">로딩 중...</span>개</p>
                            <p>활성 사용자: <span id="users-display">로딩 중...</span>명</p>
                        </div>
                        <button class="btn btn-success" onclick="updateTestStats()">통계 업데이트</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h5>콘솔 로그</h5>
                        <div id="console-log" style="background-color: #f8f9fa; padding: 10px; height: 300px; overflow-y: auto; font-family: monospace;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 콘솔 로그 캡처
        const originalLog = console.log;
        const originalError = console.error;
        const logDiv = document.getElementById('console-log');
        
        function addLogMessage(message, type = 'log') {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.innerHTML = `<span style="color: #666;">[${timestamp}]</span> <span style="color: ${type === 'error' ? 'red' : 'black'};">${message}</span>`;
            logDiv.appendChild(logEntry);
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        console.log = function(...args) {
            addLogMessage(args.join(' '), 'log');
            originalLog.apply(console, args);
        };
        
        console.error = function(...args) {
            addLogMessage(args.join(' '), 'error');
            originalError.apply(console, args);
        };
        
        // API 테스트 함수
        async function testStatsAPI() {
            console.log('📊 API 테스트 시작...');
            const resultDiv = document.getElementById('api-result');
            
            try {
                const response = await fetch('/api/stats');
                console.log('📊 응답 상태:', response.status, response.statusText);
                
                const data = await response.json();
                console.log('📊 응답 데이터:', JSON.stringify(data, null, 2));
                
                resultDiv.innerHTML = `
                    <div class="alert alert-success">
                        <h6>API 응답 성공</h6>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    </div>
                `;
                
                return data;
            } catch (error) {
                console.error('❌ API 테스트 실패:', error);
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <h6>API 응답 실패</h6>
                        <p>${error.message}</p>
                    </div>
                `;
                throw error;
            }
        }
        
        // 통계 업데이트 테스트
        async function updateTestStats() {
            console.log('📊 통계 업데이트 테스트 시작...');
            
            try {
                const data = await testStatsAPI();
                
                if (data.success && data.stats) {
                    const stats = data.stats;
                    
                    // DOM 요소 업데이트
                    const accountsDisplay = document.getElementById('accounts-display');
                    const propertiesDisplay = document.getElementById('properties-display');
                    const usersDisplay = document.getElementById('users-display');
                    
                    if (accountsDisplay) {
                        accountsDisplay.textContent = stats.total_accounts || 0;
                        console.log('✅ 계정 수 업데이트:', stats.total_accounts);
                    }
                    
                    if (propertiesDisplay) {
                        propertiesDisplay.textContent = stats.total_properties || 0;
                        console.log('✅ 프로퍼티 수 업데이트:', stats.total_properties);
                    }
                    
                    if (usersDisplay) {
                        usersDisplay.textContent = stats.active_users || 0;
                        console.log('✅ 활성 사용자 수 업데이트:', stats.active_users);
                    }
                    
                    console.log('✅ 모든 통계 업데이트 완료');
                } else {
                    console.error('❌ 통계 데이터 없음:', data);
                }
            } catch (error) {
                console.error('❌ 통계 업데이트 실패:', error);
            }
        }
        
        // 페이지 로드 시 초기 테스트
        document.addEventListener('DOMContentLoaded', function() {
            console.log('📄 테스트 페이지 로드 완료');
            updateTestStats();
        });
    </script>
</body>
</html>
    """)

@app.get("/debug-stats")
async def debug_stats_page(request: Request):
    """통계 데이터 디버깅 페이지"""
    return templates.TemplateResponse("debug_stats.html", {"request": request})

@app.route('/api/add_user', methods=['POST'])
async def add_user():
    """사용자 권한 추가 API"""
    try:
        data = await request.get_json()
        
        # 필수 필드 검증
        required_fields = ['email', 'property_id', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'필수 필드가 누락되었습니다: {field}'
                }), 400
        
        email = data['email'].strip()
        property_id = data['property_id'].strip()
        role = data['role'].strip().lower()
        requester = data.get('requester', 'admin')
        
        # 권한 레벨 검증
        if role not in ['analyst', 'editor']:
            return jsonify({
                'success': False,
                'message': '지원하지 않는 권한 레벨입니다. analyst 또는 editor만 가능합니다.'
            }), 400
        
        # 사용자 추가
        result = await user_manager.add_user_permission(
            user_email=email,
            property_id=property_id,
            role=role,
            requester=requester
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"사용자 추가 API 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'서버 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/trigger_scheduler', methods=['POST'])
async def trigger_scheduler():
    """스케줄러 수동 실행 API"""
    try:
        data = await request.get_json()
        task_type = data.get('task_type', 'all')
        
        results = {}
        
        if task_type in ['all', 'notifications']:
            # 알림 체크 및 발송
            notification_result = await notification_service.check_and_send_notifications()
            results['notifications'] = notification_result
        
        if task_type in ['all', 'expired']:
            # 만료된 권한 처리
            expired_result = await user_manager.process_expired_permissions()
            results['expired_permissions'] = expired_result
        
        if task_type in ['all', 'cleanup']:
            # 데이터베이스 정리
            cleanup_result = await db_manager.cleanup_old_logs()
            results['cleanup'] = cleanup_result
        
        return jsonify({
            'success': True,
            'message': f'{task_type} 작업이 수동으로 실행되었습니다.',
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"스케줄러 수동 실행 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'스케줄러 실행 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/dashboard')
async def dashboard():
    """대시보드 페이지"""
    try:
        # 시스템 통계 조회
        stats = await get_system_stats()
        
        # 최근 등록 사용자 조회
        recent_users = await db_manager.execute_query(
            """SELECT ur.*, p.property_display_name
               FROM user_registrations ur
               LEFT JOIN ga4_properties p ON ur.property_id = p.property_id
               ORDER BY ur.created_at DESC
               LIMIT 10"""
        )
        
        # 만료 예정 사용자 조회 (7일 이내)
        expiring_users = await db_manager.execute_query(
            """SELECT ur.*, p.property_display_name,
                      CAST((julianday(ur.종료일) - julianday('now')) AS INTEGER) as days_left
               FROM user_registrations ur
               LEFT JOIN ga4_properties p ON ur.property_id = p.property_id
               WHERE ur.status = 'active'
               AND ur.종료일 > datetime('now')
               AND ur.종료일 <= datetime('now', '+7 days')
               ORDER BY ur.종료일 ASC"""
        )
        
        # 승인 대기 사용자 조회
        pending_approvals = await db_manager.execute_query(
            """SELECT ur.*, p.property_display_name
               FROM user_registrations ur
               LEFT JOIN ga4_properties p ON ur.property_id = p.property_id
               WHERE ur.status = 'pending_approval'
               ORDER BY ur.created_at ASC"""
        )
        
        return render_template('dashboard.html', 
                             stats=stats,
                             recent_users=recent_users,
                             expiring_users=expiring_users,
                             pending_approvals=pending_approvals)
        
    except Exception as e:
        logger.error(f"대시보드 로딩 오류: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.get("/admin", response_class=HTMLResponse)
async def admin_config():
    """관리자 설정 페이지"""
    try:
        with open("src/web/templates/admin_config.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"❌ 관리자 설정 페이지 로드 실패: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다")

# 관리자 API 엔드포인트들

@app.get("/api/admin/validity-periods")
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

@app.get("/api/admin/validity-periods/{period_id}")
async def get_validity_period(period_id: int):
    """특정 유효기간 설정 조회"""
    try:
        period = await db_manager.execute_query(
            "SELECT * FROM validity_periods WHERE id = ?", (period_id,)
        )
        if not period:
            raise HTTPException(status_code=404, detail="유효기간 설정을 찾을 수 없습니다")
        
        return JSONResponse({
            "success": True,
            "period": period[0]
        })
    except Exception as e:
        logger.error(f"❌ 유효기간 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/validity-periods")
async def create_validity_period(request: Request):
    """유효기간 설정 생성"""
    try:
        data = await request.json()
        
        # 중복 체크
        existing = await db_manager.execute_query(
            "SELECT id FROM validity_periods WHERE role = ?", (data['role'],)
        )
        if existing:
            return JSONResponse({
                "success": False,
                "message": f"{data['role']} 권한의 유효기간이 이미 설정되어 있습니다."
            })
        
        await db_manager.execute_insert(
            """INSERT INTO validity_periods (role, period_days, description, is_active)
               VALUES (?, ?, ?, ?)""",
            (data['role'], data['period_days'], data.get('description'), data.get('is_active', True))
        )
        
        return JSONResponse({
            "success": True,
            "message": "유효기간 설정이 생성되었습니다."
        })
    except Exception as e:
        logger.error(f"❌ 유효기간 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/validity-periods/{period_id}")
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
        
        return JSONResponse({
            "success": True,
            "message": "유효기간 설정이 수정되었습니다."
        })
    except Exception as e:
        logger.error(f"❌ 유효기간 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/validity-periods/{period_id}")
async def delete_validity_period(period_id: int):
    """유효기간 설정 삭제"""
    try:
        await db_manager.execute_update(
            "DELETE FROM validity_periods WHERE id = ?", (period_id,)
        )
        
        return JSONResponse({
            "success": True,
            "message": "유효기간 설정이 삭제되었습니다."
        })
    except Exception as e:
        logger.error(f"❌ 유효기간 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/responsible-persons")
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

@app.get("/api/admin/responsible-persons/{person_id}")
async def get_responsible_person(person_id: int):
    """특정 담당자 조회"""
    try:
        person = await db_manager.execute_query(
            "SELECT * FROM responsible_persons WHERE id = ?", (person_id,)
        )
        if not person:
            raise HTTPException(status_code=404, detail="담당자를 찾을 수 없습니다")
        
        return JSONResponse({
            "success": True,
            "person": person[0]
        })
    except Exception as e:
        logger.error(f"❌ 담당자 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/responsible-persons")
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
        
        return JSONResponse({
            "success": True,
            "message": "담당자가 생성되었습니다."
        })
    except Exception as e:
        logger.error(f"❌ 담당자 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/responsible-persons/{person_id}")
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
        
        return JSONResponse({
            "success": True,
            "message": "담당자 정보가 수정되었습니다."
        })
    except Exception as e:
        logger.error(f"❌ 담당자 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/responsible-persons/{person_id}")
async def delete_responsible_person(person_id: int):
    """담당자 삭제"""
    try:
        await db_manager.execute_update(
            "DELETE FROM responsible_persons WHERE id = ?", (person_id,)
        )
        
        return JSONResponse({
            "success": True,
            "message": "담당자가 삭제되었습니다."
        })
    except Exception as e:
        logger.error(f"❌ 담당자 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/notification-settings")
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

@app.put("/api/admin/notification-settings/{notification_type}")
async def update_notification_setting(notification_type: str, request: Request):
    """알림 설정 수정"""
    try:
        data = await request.json()
        
        await db_manager.execute_update(
            """UPDATE notification_settings 
               SET enabled = ?, updated_at = CURRENT_TIMESTAMP
               WHERE notification_type = ?""",
            (data['enabled'], notification_type)
        )
        
        return JSONResponse({
            "success": True,
            "message": "알림 설정이 수정되었습니다."
        })
    except Exception as e:
        logger.error(f"❌ 알림 설정 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/system-settings")
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

@app.put("/api/admin/system-settings")
async def update_system_settings(request: Request):
    """시스템 설정 수정"""
    try:
        data = await request.json()
        
        # 각 설정을 개별적으로 업데이트
        for key, value in data.items():
            await db_manager.execute_update(
                """UPDATE admin_settings 
                   SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE setting_key = ?""",
                (str(value), key)
            )
        
        return JSONResponse({
            "success": True,
            "message": "시스템 설정이 저장되었습니다."
        })
    except Exception as e:
        logger.error(f"❌ 시스템 설정 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users", response_class=HTMLResponse)
async def users_list_page(request: Request):
    """사용자 목록 페이지"""
    try:
        return templates.TemplateResponse("users_list.html", {
            "request": request
        })
    except Exception as e:
        logger.error(f"❌ 사용자 목록 페이지 로드 실패: {e}")
        raise HTTPException(status_code=500, detail="페이지를 불러올 수 없습니다")

@app.get("/api/users")
async def get_users_list(
    status: Optional[str] = None,
    role: Optional[str] = None,
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
        
        # 필터 조건 추가
        if status:
            conditions.append("ur.status = ?")
            params.append(status)
            
        if role:
            conditions.append("ur.권한 = ?")
            params.append(role)
            
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
        users = await db_manager.execute_query(paginated_query, params)
        
        # 페이지네이션 정보
        total_pages = (total + per_page - 1) // per_page
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages
        }
        
        return {
            "success": True,
            "users": users,
            "pagination": pagination
        }
        
    except Exception as e:
        logger.error(f"❌ 사용자 목록 조회 실패: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/users/export")
async def export_users_csv(
    status: Optional[str] = None,
    role: Optional[str] = None,
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
            
        if role:
            conditions.append("ur.권한 = ?")
            params.append(role)
            
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
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 헤더 작성
        headers = [
            'ID', '신청자', '사용자 이메일', '프로퍼티 ID', '프로퍼티명', 
            '계정명', '권한', '상태', 'GA4 등록', '신청일', '종료일', '연장 횟수'
        ]
        writer.writerow(headers)
        
        # 데이터 작성
        for user in users:
            row = [
                user['id'],
                user['applicant'],
                user['user_email'],
                user['property_id'],
                user['property_name'] or '',
                user['account_name'] or '',
                user['permission_level'],
                user['status'],
                '등록됨' if user['ga4_registered'] else '미등록',
                user['created_at'],
                user['expiry_date'] or '',
                user['extension_count'] or 0
            ]
            writer.writerow(row)
        
        # CSV 내용 가져오기
        csv_content = output.getvalue()
        output.close()
        
        # 파일명 생성 (현재 날짜 포함)
        from datetime import datetime
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

@app.get("/api/accounts")
async def get_accounts():
    """계정 목록 조회 API"""
    try:
        accounts = await db_manager.execute_query(
            """SELECT account_id as id, account_display_name as name 
               FROM ga4_accounts 
               WHERE 삭제여부 = 0
               ORDER BY account_display_name"""
        )
        
        return {
            "success": True,
            "accounts": accounts or []
        }
        
    except Exception as e:
        logger.error(f"❌ 계정 목록 조회 실패: {e}")
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "src.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 