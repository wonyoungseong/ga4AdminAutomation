#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
알림 로거
========

알림 발송 로그 기록과 통계 조회를 담당하는 클래스입니다.
단일 책임 원칙(SRP)에 따라 로깅 관련 로직만 포함합니다.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from src.core.logger import get_ga4_logger
from src.infrastructure.database import db_manager
from .notification_types import NotificationType


class NotificationLogger:
    """알림 로깅 및 통계 관리 클래스
    
    알림 발송 기록, 실패 로그, 통계 조회 등
    모든 로깅 관련 기능을 담당합니다.
    """
    
    def __init__(self):
        self.logger = get_ga4_logger()
        self.db_manager = db_manager
    
    async def log_notification_sent(self, user_email: str, notification_type: NotificationType, 
                                  subject: str, status: str = "sent") -> None:
        """알림 발송 로그 기록"""
        try:
            await self.db_manager.execute_insert(
                """
                INSERT INTO notification_logs 
                (user_registration_id, user_email, notification_type, sent_to, message_subject, sent_at, status)
                VALUES (NULL, ?, ?, ?, ?, ?, ?)
                """,
                (user_email, notification_type.value, user_email, subject, datetime.now(), status)
            )
            self.logger.debug(f"✅ 알림 로그 기록 완료: {user_email} - {notification_type.value}")
            
        except Exception as e:
            self.logger.error(f"❌ 알림 로그 기록 실패: {e}")
    
    async def log_notification_failed(self, user_email: str, notification_type: NotificationType,
                                    subject: str, error_message: str) -> None:
        """알림 발송 실패 로그 기록"""
        try:
            await self.db_manager.execute_insert(
                """
                INSERT INTO notification_logs 
                (user_registration_id, user_email, notification_type, sent_to, message_subject, sent_at, status)
                VALUES (NULL, ?, ?, ?, ?, ?, 'failed')
                """,
                (user_email, notification_type.value, user_email, subject, datetime.now())
            )
            self.logger.warning(f"⚠️ 알림 실패 로그 기록: {user_email} - {error_message}")
            
        except Exception as e:
            self.logger.error(f"❌ 실패 로그 기록 실패: {e}")
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """알림 발송 통계 조회"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 총 발송 수
            total_sent_result = await self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM notification_logs WHERE status = 'sent'"
            )
            total_sent = total_sent_result[0]['count'] if total_sent_result else 0
            
            # 오늘 발송 수
            today_sent_result = await self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM notification_logs WHERE status = 'sent' AND DATE(sent_at) = ?",
                (current_date,)
            )
            today_sent = today_sent_result[0]['count'] if today_sent_result else 0
            
            # 실패 수
            failed_result = await self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM notification_logs WHERE status = 'failed'"
            )
            total_failed = failed_result[0]['count'] if failed_result else 0
            
            # 대기 중인 알림 (만료 예정 사용자)
            pending_result = await self.db_manager.execute_query(
                """
                SELECT COUNT(*) as count FROM user_registrations 
                WHERE status = 'active' AND 종료일 IS NOT NULL 
                AND DATE(종료일) <= DATE('now', '+30 days')
                """
            )
            pending_notifications = pending_result[0]['count'] if pending_result else 0
            
            # 마지막 발송 시간
            last_sent_result = await self.db_manager.execute_query(
                "SELECT MAX(sent_at) as last_sent FROM notification_logs WHERE status = 'sent'"
            )
            last_sent = last_sent_result[0]['last_sent'] if last_sent_result and last_sent_result[0]['last_sent'] else None
            
            if last_sent:
                last_sent = datetime.fromisoformat(last_sent).strftime('%m-%d %H:%M')
            
            return {
                'total_sent': total_sent,
                'total_failed': total_failed,
                'today_sent': today_sent,
                'pending_notifications': pending_notifications,
                'last_sent': last_sent or '없음',
                'success_rate': round((total_sent / (total_sent + total_failed) * 100), 2) if (total_sent + total_failed) > 0 else 100
            }
            
        except Exception as e:
            self.logger.error(f"❌ 알림 통계 조회 중 오류: {e}")
            return {
                'total_sent': 0,
                'total_failed': 0,
                'today_sent': 0,
                'pending_notifications': 0,
                'last_sent': '오류',
                'success_rate': 0
            }
    
    async def get_recent_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 알림 발송 기록 조회"""
        try:
            result = await self.db_manager.execute_query(
                """
                SELECT user_email, notification_type, message_subject, sent_at, status, error_message
                FROM notification_logs 
                ORDER BY sent_at DESC 
                LIMIT ?
                """,
                (limit,)
            )
            
            return result if result else []
            
        except Exception as e:
            self.logger.error(f"❌ 최근 알림 기록 조회 실패: {e}")
            return []
    
    async def get_notification_stats_by_type(self) -> Dict[str, Dict[str, int]]:
        """알림 타입별 통계 조회"""
        try:
            result = await self.db_manager.execute_query(
                """
                SELECT 
                    notification_type,
                    status,
                    COUNT(*) as count
                FROM notification_logs 
                GROUP BY notification_type, status
                ORDER BY notification_type, status
                """
            )
            
            stats_by_type = {}
            for row in result:
                notification_type = row['notification_type']
                status = row['status']
                count = row['count']
                
                if notification_type not in stats_by_type:
                    stats_by_type[notification_type] = {'sent': 0, 'failed': 0}
                
                stats_by_type[notification_type][status] = count
            
            return stats_by_type
            
        except Exception as e:
            self.logger.error(f"❌ 타입별 통계 조회 실패: {e}")
            return {}
    
    async def get_user_notification_history(self, user_email: str, limit: int = 20) -> List[Dict[str, Any]]:
        """특정 사용자의 알림 발송 기록 조회"""
        try:
            result = await self.db_manager.execute_query(
                """
                SELECT notification_type, message_subject, sent_at, status, error_message
                FROM notification_logs 
                WHERE user_email = ?
                ORDER BY sent_at DESC 
                LIMIT ?
                """,
                (user_email, limit)
            )
            
            return result if result else []
            
        except Exception as e:
            self.logger.error(f"❌ 사용자 알림 기록 조회 실패: {e}")
            return []
    
    async def check_notification_sent_today(self, user_email: str, notification_type: NotificationType) -> bool:
        """오늘 특정 알림이 이미 발송되었는지 확인"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            result = await self.db_manager.execute_query(
                """
                SELECT COUNT(*) as count FROM notification_logs 
                WHERE user_email = ? 
                AND notification_type = ?
                AND DATE(sent_at) = ?
                AND status = 'sent'
                """,
                (user_email, notification_type.value, current_date)
            )
            
            return result[0]['count'] > 0 if result else False
            
        except Exception as e:
            self.logger.error(f"❌ 알림 발송 여부 확인 실패: {e}")
            return False
    
    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """오래된 로그 정리"""
        try:
            cutoff_date = datetime.now().strftime('%Y-%m-%d')
            
            result = await self.db_manager.execute_query(
                """
                DELETE FROM notification_logs 
                WHERE sent_at < DATE('now', '-{} days')
                """.format(days_to_keep)
            )
            
            deleted_count = result if isinstance(result, int) else 0
            self.logger.info(f"🧹 오래된 알림 로그 정리 완료: {deleted_count}개 삭제")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ 로그 정리 실패: {e}")
            return 0
    
    async def get_failed_notifications_summary(self) -> Dict[str, Any]:
        """실패한 알림 요약 정보"""
        try:
            # 오늘 실패한 알림
            today_failed = await self.db_manager.execute_query(
                """
                SELECT notification_type, COUNT(*) as count, error_message
                FROM notification_logs 
                WHERE status = 'failed' 
                AND DATE(sent_at) = DATE('now')
                GROUP BY notification_type, error_message
                ORDER BY count DESC
                """
            )
            
            # 최다 실패 사유
            top_errors = await self.db_manager.execute_query(
                """
                SELECT error_message, COUNT(*) as count
                FROM notification_logs 
                WHERE status = 'failed' 
                AND sent_at >= DATE('now', '-7 days')
                GROUP BY error_message
                ORDER BY count DESC
                LIMIT 5
                """
            )
            
            return {
                'today_failed': today_failed if today_failed else [],
                'top_errors': top_errors if top_errors else []
            }
            
        except Exception as e:
            self.logger.error(f"❌ 실패 알림 요약 조회 실패: {e}")
            return {'today_failed': [], 'top_errors': []}
    
    async def log_notification(self, user_email: str, notification_type: str, 
                             property_name: str = None, sent_to: str = None, 
                             message_subject: str = "", message_body: str = "", 
                             status: str = "sent", error_message: str = None,
                             user_registration_id: int = None) -> bool:
        """통합 알림 로깅 메서드 (TDD 테스트 호환)
        
        Args:
            user_email: 사용자 이메일
            notification_type: 알림 타입 (문자열)
            property_name: 프로퍼티 이름
            sent_to: 발송 대상 이메일
            message_subject: 메시지 제목
            message_body: 메시지 본문
            status: 발송 상태 ('sent' 또는 'failed')
            error_message: 오류 메시지 (실패 시)
            
        Returns:
            bool: 로깅 성공 여부
        """
        try:
            # NotificationType enum으로 변환 시도
            from .notification_types import NotificationUnifiedManager
            notification_enum = NotificationUnifiedManager.from_string(notification_type)
            
            if notification_enum is None:
                # enum에 없는 경우 문자열 그대로 사용
                self.logger.warning(f"⚠️ 알 수 없는 알림 타입: {notification_type}")
            
            # 데이터베이스에 로그 기록
            await self.db_manager.execute_insert(
                """
                INSERT INTO notification_logs 
                (user_registration_id, user_email, notification_type, property_name, sent_to, 
                 message_subject, message_body, sent_at, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_registration_id,  # 등록 ID 추가
                    user_email, 
                    notification_type,  # 문자열 그대로 저장
                    property_name or '',
                    sent_to or user_email,
                    message_subject or '',
                    message_body or '',
                    datetime.now(),
                    status,
                    error_message
                )
            )
            
            if status == 'sent':
                self.logger.debug(f"✅ 알림 로그 기록 완료: {user_email} - {notification_type}")
            else:
                self.logger.warning(f"⚠️ 알림 실패 로그 기록: {user_email} - {notification_type} - {error_message}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 알림 로그 기록 실패: {user_email} - {notification_type} - {str(e)}")
            return False 