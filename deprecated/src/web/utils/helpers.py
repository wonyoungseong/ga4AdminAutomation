"""
웹 애플리케이션 헬퍼 함수
======================

공통으로 사용되는 유틸리티 함수들을 제공합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

from src.infrastructure.database import db_manager
from ...core.logger import get_ga4_logger

logger = get_ga4_logger()


class DictObj:
    """dict를 객체처럼 접근할 수 있도록 하는 클래스"""
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)
    
    def __getattr__(self, name):
        return None


def get_property_scanner():
    """프로퍼티 스캐너 인스턴스 반환"""
    # 전역 변수에서 가져오기 (임시 처리)
    import sys
    if hasattr(sys.modules.get('src.web.main'), 'property_scanner'):
        return sys.modules['src.web.main'].property_scanner
    return None


async def get_dashboard_data() -> Dict[str, Any]:
    """대시보드 데이터 조회"""
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
        
        return {
            "properties": properties,
            "registrations": registrations,
            "stats": stats,
            "notification_stats": {"total_sent": 0, "today_sent": 0, "pending_notifications": 0, "last_sent": "없음"},
            "recent_logs": []
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


def validate_email_list(email_string: str) -> List[str]:
    """이메일 목록 문자열을 검증하고 파싱"""
    email_list = [email.strip() for email in email_string.split(',') if email.strip()]
    
    # 이메일 형식 검증
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    valid_emails = []
    
    for email in email_list:
        if email_pattern.match(email):
            valid_emails.append(email)
        else:
            logger.warning(f"⚠️ 잘못된 이메일 형식: {email}")
    
    return valid_emails


def calculate_expiry_date(permission_level: str) -> datetime:
    """권한 레벨에 따른 만료일 계산"""
    if permission_level == 'analyst':
        return datetime.now() + timedelta(days=30)
    elif permission_level == 'editor':
        return datetime.now() + timedelta(days=7)
    else:  # viewer
        return datetime.now() + timedelta(days=14)


def format_registration_data(registrations_raw: List[Dict]) -> List[DictObj]:
    """등록 데이터를 DictObj로 변환"""
    return [DictObj({
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


def format_properties_data(properties_raw: List[Dict]) -> List[DictObj]:
    """프로퍼티 데이터를 DictObj로 변환"""
    return [DictObj({
        'property_id': prop.get('property_id', ''),
        'property_name': prop.get('property_name', ''),
        'account_name': prop.get('account_name', ''),
        'time_zone': prop.get('time_zone', 'Asia/Seoul'),
        'last_updated': str(prop.get('last_updated', '')) if prop.get('last_updated') else ''
    }) for prop in properties_raw]


def format_accounts_data(accounts_raw: List[Dict]) -> List[DictObj]:
    """계정 데이터를 DictObj로 변환"""
    return [DictObj({
        'account_id': acc.get('account_id', ''),
        'account_name': acc.get('account_name', ''),
        'display_name': acc.get('display_name', ''),
        'last_updated': str(acc.get('last_updated', '')) if acc.get('last_updated') else ''
    }) for acc in accounts_raw] 