#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
알림 설정 관리자
==============

GA4 권한 관리 시스템의 알림 설정을 관리하는 서비스
"""

import json
from typing import Dict, List, Optional, Any
from src.core.logger import get_ga4_logger
from src.infrastructure.database import db_manager
from .notification_types import NotificationType, NotificationUnifiedManager

logger = get_ga4_logger()


class NotificationConfigManager:
    """알림 설정 관리 클래스"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    async def initialize_notification_settings(self):
        """알림 설정 초기화"""
        try:
            logger.info("🔧 알림 설정 초기화 시작")
            
            # 기본 알림 설정들
            default_settings = [
                ('welcome', 1, '', '권한 부여 완료 알림', '권한이 성공적으로 부여되었습니다.'),
                ('30_days', 1, '30', '30일 만료 경고', '권한이 30일 후 만료됩니다.'),
                ('7_days', 1, '7', '7일 만료 경고', '권한이 7일 후 만료됩니다.'),
                ('1_day', 1, '1', '1일 만료 경고', '권한이 내일 만료됩니다.'),
                ('today', 1, '0', '당일 만료 경고', '권한이 오늘 만료됩니다.'),
                ('expired', 1, '', '만료 알림', '권한이 만료되었습니다.'),
                ('extension_approved', 1, '', '연장 승인 알림', '권한 연장이 승인되었습니다.'),
                ('admin_notification', 1, '', '관리자 알림', '관리자 검토가 필요합니다.'),
                ('test', 1, '', '테스트 알림', '시스템 테스트 알림입니다.'),
            ]
            
            for notification_type, enabled, trigger_days, subject, body in default_settings:
                # 기존 설정이 있는지 확인
                existing = await self.db_manager.execute_query(
                    "SELECT id FROM notification_settings WHERE notification_type = ?", 
                    (notification_type,)
                )
                
                if not existing:
                    await self.db_manager.execute_insert(
                        """INSERT INTO notification_settings 
                           (notification_type, enabled, trigger_days, template_subject, template_body)
                           VALUES (?, ?, ?, ?, ?)""",
                        (notification_type, enabled, trigger_days, subject, body)
                    )
                    logger.info(f"✅ 알림 설정 추가: {notification_type}")
            
            logger.info("✅ 알림 설정 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ 알림 설정 초기화 실패: {e}")
            raise
    
    def is_notification_enabled(self, notification_type: NotificationType) -> bool:
        """알림 활성화 여부 확인 (단순화된 버전)
        
        Args:
            notification_type: NotificationType enum 값
            
        Returns:
            bool: 활성화 여부
        """
        try:
            # enum 값을 직접 사용 (매핑 없음)
            enum_value = NotificationUnifiedManager.get_database_value(notification_type)
            
            # notification_settings에서 직접 조회
            query = """
            SELECT enabled, trigger_days 
            FROM notification_settings 
            WHERE notification_type = ?
            """
            
            result = self.db_manager.execute_query_sync(query, (enum_value,))
            
            if not result:
                logger.warning(f"🚨 알림 설정을 찾을 수 없음: {enum_value}")
                return True  # 기본값: 활성화
            
            enabled = bool(result[0]['enabled'])
            
            if not enabled:
                logger.info(f"⏹ 알림 비활성화됨: {enum_value}")
                return False
            
            # 만료 경고 알림의 경우 trigger_days 확인
            if NotificationUnifiedManager.is_expiry_warning(notification_type):
                trigger_days = result[0].get('trigger_days', '')
                target_days = NotificationUnifiedManager.get_trigger_days(notification_type)
                
                if trigger_days:
                    trigger_days_list = [int(d.strip()) for d in trigger_days.split(',') if d.strip().isdigit()]
                    if target_days not in trigger_days_list:
                        logger.info(f"⏭ {enum_value} 알림 일수({target_days}일)가 설정에 없음: {trigger_days}")
                        return False
            
            logger.info(f"✅ 알림 활성화됨: {enum_value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 알림 설정 확인 실패: {notification_type.value} - {e}")
            return True  # 오류 시 기본값: 활성화
    
    def get_notification_settings(self, notification_type: NotificationType) -> Optional[Dict[str, Any]]:
        """알림 설정 조회 (단순화된 버전)
        
        Args:
            notification_type: NotificationType enum 값
            
        Returns:
            dict: 알림 설정 정보
        """
        try:
            # enum 값을 직접 사용
            enum_value = NotificationUnifiedManager.get_database_value(notification_type)
            
            query = """
            SELECT * FROM notification_settings 
            WHERE notification_type = ?
            """
            
            result = self.db_manager.execute_query_sync(query, (enum_value,))
            
            if result:
                settings = dict(result[0])
                logger.info(f"✅ 알림 설정 조회 성공: {enum_value}")
                return settings
            else:
                logger.warning(f"⚠ 알림 설정이 없음: {enum_value}")
                return None
            
        except Exception as e:
            logger.error(f"❌ 알림 설정 조회 실패: {notification_type.value} - {e}")
            return None
    
    def get_admin_emails_for_notification(self, notification_type: NotificationType) -> List[str]:
        """관리자 이메일 목록 조회 (단순화된 버전)
        
        Args:
            notification_type: NotificationType enum 값
            
        Returns:
            list: 관리자 이메일 목록
        """
        try:
            # 기본 관리자 이메일 반환 (admin_notifications 테이블 사용하지 않음)
            default_admin = "wonyoungseong@gmail.com"
            logger.info(f"📧 기본 관리자 이메일 사용: {default_admin}")
            return [default_admin]
            
        except Exception as e:
            logger.error(f"❌ 관리자 이메일 조회 실패: {notification_type.value} - {e}")
            return ["wonyoungseong@gmail.com"]  # 기본값
    
    async def get_trigger_days(self, notification_category: str) -> str:
        """발송 일수 설정 조회 (비동기 버전)
        
        Args:
            notification_category: 알림 카테고리 (예: 'expiry_warning')
            
        Returns:
            str: 발송 일수 설정 (예: '30,7,1,0')
        """
        try:
            query = """
            SELECT trigger_days 
            FROM notification_settings 
            WHERE notification_type = ? AND enabled = 1
            """
            
            result = await self.db_manager.execute_query(query, (notification_category,))
            
            if result and result[0]['trigger_days']:
                trigger_days = result[0]['trigger_days']
                logger.info(f"✅ trigger_days 조회 성공: {notification_category} -> {trigger_days}")
                return trigger_days
            else:
                logger.warning(f"⚠ trigger_days 설정이 없음: {notification_category}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ trigger_days 조회 실패: {notification_category} - {e}")
            return ""
    
    async def parse_trigger_days(self, trigger_days_str: str) -> List[int]:
        """발송 일수 문자열 파싱
        
        Args:
            trigger_days_str: 발송 일수 문자열 (예: '30,7,1,0')
            
        Returns:
            list: 발송 일수 목록
        """
        try:
            if not trigger_days_str:
                return []
            
            trigger_days = [int(d.strip()) for d in trigger_days_str.split(',') if d.strip().isdigit()]
            logger.info(f"✅ trigger_days 파싱 성공: {trigger_days_str} -> {trigger_days}")
            return trigger_days
            
        except Exception as e:
            logger.error(f"❌ trigger_days 파싱 실패: {trigger_days_str} - {e}")
            return [] 