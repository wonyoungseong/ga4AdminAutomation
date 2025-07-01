#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 알림 모듈
===================

Clean Architecture 기반으로 구조화된 알림 시스템
- 단일 책임 원칙 (SRP) 적용
- 개방-폐쇄 원칙 (OCP) 지원
- 의존성 역전 원칙 (DIP) 준수
"""

# 핵심 타입 정의만 import (다른 모듈의 의존성 문제 방지)
from .notification_types import NotificationType, NotificationMetadata

# 다른 import들은 필요할 때 직접 import 하도록 주석 처리
# from .notification_service import NotificationService, notification_service
# from .email_templates import EmailTemplateManager
# from .notification_handlers import (
#     WelcomeNotificationHandler,
#     ExpiryWarningHandler,
#     DeletionNoticeHandler,
#     AdminNotificationHandler,
#     EditorDowngradeHandler
# )
# from .notification_logger import NotificationLogger
# from .notification_config import NotificationConfigManager

__all__ = [
    'NotificationType',
    'NotificationMetadata'
]

__version__ = "2.0.0"
__author__ = "GA4 권한 관리 시스템" 