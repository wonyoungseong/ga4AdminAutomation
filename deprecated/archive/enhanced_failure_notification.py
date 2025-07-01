#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Failure Notification System
====================================

This module provides specialized notification templates for different failure scenarios
in GA4 user registration process.

Author: GA4 Automation Team
Date: 2025-01-21
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from datetime import datetime
import json


class FailureNotificationTemplates:
    """실패 케이스별 알림 템플릿"""
    
    @staticmethod
    def get_user_notification_template(failure_type: str) -> Dict[str, str]:
        """
        사용자용 실패 알림 템플릿
        
        Args:
            failure_type: 실패 유형
            
        Returns:
            템플릿 딕셔너리 (subject, html_body, text_body)
        """
        templates = {
            "email_already_exists": {
                "subject": "GA4 접근 권한 - 이미 등록된 계정입니다",
                "html_body": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">✅ 이미 등록된 계정</h1>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                        <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                            <h2 style="color: #2c3e50; margin-top: 0;">안녕하세요!</h2>
                            
                            <p style="color: #34495e; line-height: 1.6; font-size: 16px;">
                                귀하의 계정은 <strong>이미 GA4에 등록되어 있습니다</strong>. 
                                중복 등록을 방지하여 기존 권한을 보호하고 있습니다.
                            </p>
                            
                            <div style="background: #e8f5e8; border-left: 4px solid #27ae60; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                <h3 style="color: #27ae60; margin: 0 0 10px 0;">✅ 다음 단계</h3>
                                <ul style="color: #2c3e50; margin: 0; padding-left: 20px;">
                                    <li>기존 GA4 권한을 확인해주세요</li>
                                    <li>GA4 대시보드에 접속하여 데이터를 확인해보세요</li>
                                    <li>권한 변경이 필요하면 관리자에게 문의해주세요</li>
                                </ul>
                            </div>
                            
                            <div style="text-align: center; margin: 25px 0;">
                                <a href="https://analytics.google.com/analytics/web/" 
                                   style="background: #3498db; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                                    GA4 접속하기
                                </a>
                            </div>
                            
                            <p style="color: #7f8c8d; font-size: 14px; margin-top: 25px;">
                                문의사항이 있으시면 언제든지 연락주세요.
                            </p>
                        </div>
                    </div>
                </div>
                """,
                "text_body": """
안녕하세요!

귀하의 계정은 이미 GA4에 등록되어 있습니다.
중복 등록을 방지하여 기존 권한을 보호하고 있습니다.

다음 단계:
- 기존 GA4 권한을 확인해주세요
- GA4 대시보드에 접속하여 데이터를 확인해보세요  
- 권한 변경이 필요하면 관리자에게 문의해주세요

GA4 접속: https://analytics.google.com/analytics/web/

문의사항이 있으시면 언제든지 연락주세요.
                """
            },