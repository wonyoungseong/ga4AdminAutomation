#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail OAuth 2.0 이메일 발송 시스템
==============================

GA4 자동화 시스템용 Gmail OAuth 2.0 이메일 발송 클래스

Usage:
    from gmail_oauth_sender import GmailOAuthSender
    
    sender = GmailOAuthSender()
    sender.send_user_notification(
        recipient_email="user@example.com",
        user_name="홍길동",
        action="added",
        role="Analyst",
        property_id="123456789"
    )
"""

import json
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from datetime import datetime
from .logger import get_gmail_logger

# Gmail API 스코프
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailOAuthSender:
    def __init__(self, config_file='config.json'):
        """Gmail OAuth 2.0 이메일 발송 클래스 초기화 (개선된 로깅)"""
        self.config_file = config_file
        self.config = self.load_config()
        self.service = None
        self.logger = get_gmail_logger()
        
    def load_config(self):
        """설정 파일 로드"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"설정 파일 로드 실패: {str(e)}")
    
    def authenticate(self):
        """Gmail OAuth 2.0 인증"""
        try:
            creds = None
            
            # 기존 토큰 로드
            if os.path.exists('config/token.pickle'):
                with open('config/token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            # 토큰 유효성 확인 및 갱신
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("토큰 갱신 중...")
                    creds.refresh(Request())
                else:
                    self.logger.info("새로운 OAuth 인증 필요")
                    gmail_oauth = self.config.get('gmail_oauth', {})
                    
                    client_config = {
                        "installed": {
                            "client_id": gmail_oauth.get('client_id'),
                            "client_secret": gmail_oauth.get('client_secret'),
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": ["http://localhost"]
                        }
                    }
                    
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # 토큰 저장
                with open('config/token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            # Gmail 서비스 생성
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail OAuth 인증 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"Gmail OAuth 인증 실패: {str(e)}")
            return False
    
    def create_email_message(self, recipient_email, subject, text_content, html_content=None):
        """이메일 메시지 생성"""
        gmail_oauth = self.config.get('gmail_oauth', {})
        sender_email = gmail_oauth.get('sender_email')
        sender_name = gmail_oauth.get('sender_name', 'GA4 자동화 시스템')
        
        if html_content:
            message = MIMEMultipart('alternative')
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(text_part)
            message.attach(html_part)
        else:
            message = MIMEText(text_content, 'plain', 'utf-8')
        
        message['to'] = recipient_email
        message['from'] = f"{sender_name} <{sender_email}>"
        message['subject'] = subject
        
        return message
    
    def send_email(self, recipient_email, subject, text_content, html_content=None):
        """이메일 발송"""
        try:
            # 인증 확인
            if not self.service:
                if not self.authenticate():
                    return False
            
            # 이메일 메시지 생성
            message = self.create_email_message(recipient_email, subject, text_content, html_content)
            
            # 이메일 인코딩 및 발송
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.logger.info(f"이메일 발송 성공: {recipient_email} (메시지 ID: {result['id']})")
            return True
            
        except Exception as e:
            self.logger.error(f"이메일 발송 실패: {str(e)}")
            return False
    
    async def send_rich_email(self, recipient_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """리치 HTML 이메일 발송 (NotificationService 호환)
        
        Args:
            recipient_email: 수신자 이메일
            subject: 제목
            text_content: 텍스트 내용
            html_content: HTML 내용
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # 인증 확인
            if not self.service:
                if not self.authenticate():
                    self.logger.error(f"Gmail 인증 실패: {recipient_email}")
                    return False
            
            # 멀티파트 메시지 생성
            message = MIMEMultipart('alternative')
            
            # 발송자 정보 설정
            gmail_oauth = self.config.get('gmail_oauth', {})
            sender_email = gmail_oauth.get('sender_email')
            sender_name = gmail_oauth.get('sender_name', 'GA4 자동화 시스템')
            
            message['to'] = recipient_email
            message['from'] = f"{sender_name} <{sender_email}>"
            message['subject'] = subject
            
            # 텍스트 및 HTML 파트 추가
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # 이메일 인코딩 및 발송
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            message_id = result.get('id')
            self.logger.info(f"리치 이메일 발송 성공: {recipient_email} (ID: {message_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"리치 이메일 발송 실패: {recipient_email} - {str(e)}")
            return False
    
    def send_user_notification(self, recipient_email, user_name, action, role, property_id):
        """GA4 사용자 관리 알림 이메일 발송"""
        action_text = {
            'added': '추가',
            'removed': '제거', 
            'updated': '업데이트'
        }
        
        action_korean = action_text.get(action, action)
        
        subject = f"🔔 GA4 사용자 {action_korean} 알림"
        
        # 텍스트 버전
        text_content = f"""
GA4 사용자 {action_korean} 알림
===================

사용자 정보:
- 이메일: {recipient_email}
- 이름: {user_name}
- 역할: {role}
- 속성 ID: {property_id}

작업: {action_korean}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

이 이메일은 GA4 자동화 시스템에서 자동으로 발송되었습니다.
"""
        
        # HTML 버전
        html_content = f"""
        <html>
          <body>
            <h2>🔔 GA4 사용자 {action_korean} 알림</h2>
            
            <h3>👤 사용자 정보:</h3>
            <ul>
              <li><strong>이메일:</strong> {recipient_email}</li>
              <li><strong>이름:</strong> {user_name}</li>
              <li><strong>역할:</strong> {role}</li>
              <li><strong>속성 ID:</strong> {property_id}</li>
            </ul>
            
            <h3>📋 작업 내용:</h3>
            <p><strong>{action_korean}</strong> 작업이 완료되었습니다.</p>
            
            <hr>
            <p><small>작업 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
            <p><small>이 이메일은 GA4 자동화 시스템에서 자동으로 발송되었습니다.</small></p>
          </body>
        </html>
        """
        
        return self.send_email(recipient_email, subject, text_content, html_content)
    
    def send_admin_notification(self, message, details=None):
        """관리자 알림 이메일 발송"""
        notification_settings = self.config.get('notification_settings', {})
        admin_email = notification_settings.get('admin_email')
        
        if not admin_email:
            self.logger.warning("관리자 이메일이 설정되지 않았습니다.")
            return False
        
        subject = "🚨 GA4 자동화 시스템 알림"
        
        text_content = f"""
GA4 자동화 시스템 알림
==================

메시지: {message}

세부사항:
{details if details else '없음'}

시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        html_content = f"""
        <html>
          <body>
            <h2>🚨 GA4 자동화 시스템 알림</h2>
            
            <h3>📢 메시지:</h3>
            <p>{message}</p>
            
            <h3>📋 세부사항:</h3>
            <pre>{details if details else '없음'}</pre>
            
            <hr>
            <p><small>시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
          </body>
        </html>
        """
        
        return self.send_email(admin_email, subject, text_content, html_content)

# 사용 예시
if __name__ == "__main__":
    sender = GmailOAuthSender()
    
    # 테스트 이메일 발송
    success = sender.send_user_notification(
        recipient_email="wonyoungseong@gmail.com",
        user_name="테스트 사용자",
        action="added",
        role="Analyst", 
        property_id="462884506"
    )
    
    if success:
        print("✅ 테스트 알림 이메일 발송 성공!")
    else:
        print("❌ 테스트 알림 이메일 발송 실패!") 