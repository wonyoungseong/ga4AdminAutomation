"""
데이터 포맷터 함수
===============

데이터 형식 변환과 관련된 유틸리티 함수들을 제공합니다.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import csv
import io


def format_datetime(dt: Any) -> str:
    """datetime 객체를 문자열로 변환"""
    if dt is None:
        return ""
    
    if isinstance(dt, str):
        return dt
    
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return str(dt)


def format_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """사용자 데이터를 템플릿에 맞게 포맷"""
    return {
        'id': user_data.get('id', ''),
        'applicant': user_data.get('applicant', ''),
        'user_email': user_data.get('user_email', ''),
        'property_id': user_data.get('property_id', ''),
        'property_name': user_data.get('property_name', ''),
        'account_name': user_data.get('account_name', ''),
        'permission_level': user_data.get('permission_level', ''),
        'status': user_data.get('status', ''),
        'created_at': format_datetime(user_data.get('created_at')),
        'expiry_date': format_datetime(user_data.get('expiry_date')),
        'ga4_registered': bool(user_data.get('ga4_registered', False)),
        'extension_count': user_data.get('extension_count', 0)
    }


def format_csv_data(users: List[Dict[str, Any]]) -> str:
    """사용자 목록을 CSV 형식으로 변환"""
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
            user.get('id', ''),
            user.get('applicant', ''),
            user.get('user_email', ''),
            user.get('property_id', ''),
            user.get('property_name', ''),
            user.get('account_name', ''),
            user.get('permission_level', ''),
            user.get('status', ''),
            '등록됨' if user.get('ga4_registered') else '미등록',
            format_datetime(user.get('created_at')),
            format_datetime(user.get('expiry_date')),
            user.get('extension_count', 0)
        ]
        writer.writerow(row)
    
    csv_content = output.getvalue()
    output.close()
    
    return csv_content


def format_stats_data(stats: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """통계 데이터를 표준 형식으로 변환"""
    if not stats:
        return {
            'total_accounts': 0,
            'total_properties': 0,
            'active_users': 0,
            'expiring_soon': 0,
            'total_notifications': 0,
            'total_audit_logs': 0,
            'total_registrations': 0
        }
    
    return {
        'total_accounts': stats.get('total_accounts', 0),
        'total_properties': stats.get('total_properties', 0),
        'active_users': stats.get('active_users', 0),
        'expiring_soon': stats.get('expiring_soon', 0),
        'total_notifications': stats.get('total_notifications', 0),
        'total_audit_logs': stats.get('total_audit_logs', 0),
        'total_registrations': stats.get('total_registrations', 0)
    }


def format_api_response(success: bool, message: str = None, data: Any = None) -> Dict[str, Any]:
    """표준 API 응답 형식으로 변환"""
    response = {'success': success}
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    return response


def format_pagination_data(page: int, per_page: int, total: int) -> Dict[str, Any]:
    """페이지네이션 정보 포맷"""
    total_pages = (total + per_page - 1) // per_page
    
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    } 