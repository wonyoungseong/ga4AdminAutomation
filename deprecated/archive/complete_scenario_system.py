#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 GA4 자동화 시나리오 시스템
================================

시나리오: 디지털 마케팅 회사의 GA4 사용자 권한 자동화 관리

워크플로우:
1. 신규 사용자 등록 (환영 이메일 발송)
2. 권한 만료일 추적 및 알림
3. 자동 권한 연장 또는 제거
4. 관리자 보고서 생성
5. 스케줄링 자동화

Author: GA4 자동화 팀
Date: 2025-01-22
"""

import json
import sqlite3
import os
import pickle
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Google APIs
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Email
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ga4_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """GA4 사용자 역할"""
    VIEWER = "predefinedRoles/read"
    ANALYST = "predefinedRoles/collaborate" 
    EDITOR = "predefinedRoles/edit"
    ADMIN = "predefinedRoles/manage"

class NotificationType(Enum):
    """알림 유형"""
    WELCOME = "welcome"
    EXPIRY_WARNING = "expiry_warning"
    EXPIRED = "expired"
    REMOVED = "removed"
    EXTENDED = "extended"
    ERROR = "error"

@dataclass
class User:
    """사용자 정보"""
    email: str
    role: UserRole
    added_date: datetime
    expiry_date: datetime
    department: str = ""
    notes: str = ""
    last_notification: Optional[datetime] = None

class GA4AutomationSystem:
    """완전한 GA4 자동화 시스템"""
    
    def __init__(self, config_file: str = "config.json"):
        """시스템 초기화"""
        self.config = self._load_config(config_file)
        self.db_path = "ga4_automation_system.db"
        self._init_database()
        self._init_ga4_client()
        self._init_gmail_client()
        
        logger.info("🚀 GA4 자동화 시스템이 시작되었습니다.")
    
    def _load_config(self, config_file: str) -> dict:
        """설정 파일 로드"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"❌ 설정 파일을 찾을 수 없습니다: {config_file}")
            raise
    
    def _init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                added_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                department TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                last_notification TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                sent_date TEXT NOT NULL,
                message TEXT,
                success INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                user_email TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ 데이터베이스가 초기화되었습니다.")
    
    def _init_ga4_client(self):
        """GA4 클라이언트 초기화"""
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'ga4-automatio-797ec352f393.json'
            self.ga4_client = AnalyticsAdminServiceClient()
            self.account_name = f"accounts/{self.config['account_id']}"
            self.property_name = f"properties/{self.config['property_id']}"
            logger.info("✅ GA4 클라이언트가 초기화되었습니다.")
        except Exception as e:
            logger.error(f"❌ GA4 클라이언트 초기화 실패: {e}")
            raise
    
    def _init_gmail_client(self):
        """Gmail 클라이언트 초기화"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/gmail.send']
            creds = None
            
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # OAuth 클라이언트 정보 생성
                    client_config = {
                        "installed": {
                            "client_id": self.config['gmail_oauth']['client_id'],
                            "client_secret": self.config['gmail_oauth']['client_secret'],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost"]
                        }
                    }
                    
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("✅ Gmail 클라이언트가 초기화되었습니다.")
        except Exception as e:
            logger.error(f"❌ Gmail 클라이언트 초기화 실패: {e}")
            raise

    # === 사용자 관리 메서드 ===
    
    def add_user(self, email: str, role: UserRole, department: str = "", 
                 expiry_days: int = 90, notes: str = "") -> bool:
        """사용자 추가"""
        try:
            logger.info(f"👤 사용자 추가 시작: {email}")
            
            # GA4에 사용자 추가
            access_binding = AccessBinding()
            access_binding.user = f"users/{email}"
            access_binding.roles = [role.value]
            
            request = self.ga4_client.create_access_binding(
                parent=self.account_name,
                access_binding=access_binding
            )
            
            # 데이터베이스에 저장
            added_date = datetime.now()
            expiry_date = added_date + timedelta(days=expiry_days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (email, role, added_date, expiry_date, department, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            ''', (
                email, role.name, added_date.isoformat(),
                expiry_date.isoformat(), department, notes
            ))
            
            conn.commit()
            conn.close()
            
            # 환영 이메일 발송
            self._send_welcome_email(email, role, expiry_date, department)
            
            # 로그 기록
            self._log_action("USER_ADDED", f"사용자 {email}을 {role.name} 권한으로 추가", email)
            
            logger.info(f"✅ 사용자 추가 완료: {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 사용자 추가 실패: {email} - {e}")
            self._log_action("ERROR", f"사용자 추가 실패: {e}", email)
            return False
    
    def remove_user(self, email: str, reason: str = "") -> bool:
        """사용자 제거"""
        try:
            logger.info(f"🗑️ 사용자 제거 시작: {email}")
            
            # GA4에서 사용자의 AccessBinding 찾기
            bindings = self.ga4_client.list_access_bindings(parent=self.account_name)
            
            for binding in bindings:
                if binding.user == f"users/{email}":
                    self.ga4_client.delete_access_binding(name=binding.name)
                    break
            
            # 데이터베이스 상태 업데이트
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET status = 'removed', updated_at = CURRENT_TIMESTAMP
                WHERE email = ?
            ''', (email,))
            
            conn.commit()
            conn.close()
            
            # 제거 알림 이메일
            self._send_removal_email(email, reason)
            
            # 로그 기록
            self._log_action("USER_REMOVED", f"사용자 {email} 제거 - {reason}", email)
            
            logger.info(f"✅ 사용자 제거 완료: {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 사용자 제거 실패: {email} - {e}")
            self._log_action("ERROR", f"사용자 제거 실패: {e}", email)
            return False
    
    def extend_user_access(self, email: str, additional_days: int = 90) -> bool:
        """사용자 권한 연장"""
        try:
            logger.info(f"📅 권한 연장 시작: {email}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT expiry_date FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            
            if result:
                current_expiry = datetime.fromisoformat(result[0])
                new_expiry = current_expiry + timedelta(days=additional_days)
                
                cursor.execute('''
                    UPDATE users SET expiry_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE email = ?
                ''', (new_expiry.isoformat(), email))
                
                conn.commit()
                conn.close()
                
                # 연장 알림 이메일
                self._send_extension_email(email, new_expiry, additional_days)
                
                # 로그 기록
                self._log_action("ACCESS_EXTENDED", 
                               f"사용자 {email} 권한을 {additional_days}일 연장", email)
                
                logger.info(f"✅ 권한 연장 완료: {email}")
                return True
            
            conn.close()
            return False
            
        except Exception as e:
            logger.error(f"❌ 권한 연장 실패: {email} - {e}")
            return False

    # === 이메일 알림 시스템 ===
    
    def _send_welcome_email(self, email: str, role: UserRole, expiry_date: datetime, department: str):
        """환영 이메일 발송"""
        subject = "🎉 GA4 분석 도구 접근 권한이 부여되었습니다"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">🎉 환영합니다!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">GA4 분석 도구 접근 권한이 부여되었습니다</p>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                    <h2 style="color: #2c3e50; margin-top: 0;">📋 권한 정보</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px 0; font-weight: bold;">이메일:</td><td>{email}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">권한 레벨:</td><td>{role.name}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">부서:</td><td>{department or '미지정'}</td></tr>
                        <tr><td style="padding: 8px 0; font-weight: bold;">만료일:</td><td>{expiry_date.strftime('%Y년 %m월 %d일')}</td></tr>
                    </table>
                </div>
                
                <div style="padding: 20px; background: #e8f5e8; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #27ae60; margin-top: 0;">🚀 시작하기</h3>
                    <p>1. <a href="https://analytics.google.com" style="color: #3498db;">Google Analytics 4</a>에 접속하세요</p>
                    <p>2. 부여된 권한으로 데이터 분석을 시작하세요</p>
                    <p>3. 질문이 있으시면 관리자에게 문의하세요</p>
                </div>
                
                <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                    <p>이 메시지는 GA4 자동화 시스템에서 발송되었습니다.</p>
                    <p>문의사항: {self.config['gmail_oauth']['sender_email']}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(email, subject, html_content, NotificationType.WELCOME)
    
    def _send_expiry_warning_email(self, email: str, expiry_date: datetime, days_left: int):
        """만료 경고 이메일 발송"""
        subject = f"⚠️ GA4 접근 권한 만료 알림 ({days_left}일 남음)"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #f39c12 0%, #e74c3c 100%); 
                           color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">⚠️ 권한 만료 알림</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">{days_left}일 후 접근 권한이 만료됩니다</p>
                </div>
                
                <div style="padding: 30px; background: #fff3cd; border-radius: 10px; margin: 20px 0; border-left: 5px solid #ffc107;">
                    <h2 style="color: #856404; margin-top: 0;">📅 만료 정보</h2>
                    <p><strong>이메일:</strong> {email}</p>
                    <p><strong>만료일:</strong> {expiry_date.strftime('%Y년 %m월 %d일')}</p>
                    <p><strong>남은 기간:</strong> {days_left}일</p>
                </div>
                
                <div style="padding: 20px; background: #d1ecf1; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #0c5460; margin-top: 0;">🔄 권한 연장 방법</h3>
                    <p>권한 연장이 필요하시면 관리자에게 연락해주세요:</p>
                    <p>📧 이메일: {self.config['gmail_oauth']['sender_email']}</p>
                </div>
                
                <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                    <p>이 메시지는 GA4 자동화 시스템에서 발송되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(email, subject, html_content, NotificationType.EXPIRY_WARNING)
    
    def _send_removal_email(self, email: str, reason: str):
        """제거 알림 이메일 발송"""
        subject = "🔒 GA4 접근 권한이 해제되었습니다"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%); 
                           color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">🔒 권한 해제 알림</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">GA4 접근 권한이 해제되었습니다</p>
                </div>
                
                <div style="padding: 30px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                    <p><strong>이메일:</strong> {email}</p>
                    <p><strong>해제일:</strong> {datetime.now().strftime('%Y년 %m월 %d일')}</p>
                    {f'<p><strong>사유:</strong> {reason}</p>' if reason else ''}
                </div>
                
                <div style="padding: 20px; background: #d4edda; border-radius: 10px; margin: 20px 0;">
                    <p>권한 재부여가 필요하시면 관리자에게 문의해주세요.</p>
                    <p>📧 이메일: {self.config['gmail_oauth']['sender_email']}</p>
                </div>
                
                <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                    <p>이 메시지는 GA4 자동화 시스템에서 발송되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(email, subject, html_content, NotificationType.REMOVED)
    
    def _send_extension_email(self, email: str, new_expiry: datetime, additional_days: int):
        """권한 연장 알림 이메일"""
        subject = "✅ GA4 접근 권한이 연장되었습니다"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); 
                           color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">✅ 권한 연장 완료</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">GA4 접근 권한이 연장되었습니다</p>
                </div>
                
                <div style="padding: 30px; background: #d4edda; border-radius: 10px; margin: 20px 0;">
                    <h2 style="color: #155724; margin-top: 0;">📅 연장 정보</h2>
                    <p><strong>이메일:</strong> {email}</p>
                    <p><strong>연장 기간:</strong> {additional_days}일</p>
                    <p><strong>새로운 만료일:</strong> {new_expiry.strftime('%Y년 %m월 %d일')}</p>
                </div>
                
                <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                    <p>이 메시지는 GA4 자동화 시스템에서 발송되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(email, subject, html_content, NotificationType.EXTENDED)
    
    def _send_email(self, to_email: str, subject: str, html_content: str, 
                   notification_type: NotificationType):
        """이메일 발송"""
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['from'] = self.config['gmail_oauth']['sender_email']
            message['subject'] = subject
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            send_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # 알림 기록 저장
            self._log_notification(to_email, notification_type, subject, True)
            
            logger.info(f"✅ 이메일 발송 성공: {to_email} - {notification_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 이메일 발송 실패: {to_email} - {e}")
            self._log_notification(to_email, notification_type, subject, False, str(e))
            return False

    # === 자동화 스케줄링 ===
    
    def check_expiring_users(self):
        """만료 예정 사용자 확인 및 알림"""
        logger.info("🔍 만료 예정 사용자를 확인합니다...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 설정된 경고 일수들
        warning_days = self.config.get('notification_settings', {}).get('expiry_warning_days', [30, 7, 1])
        
        for days in warning_days:
            target_date = (datetime.now() + timedelta(days=days)).date()
            
            cursor.execute('''
                SELECT email, expiry_date, last_notification 
                FROM users 
                WHERE status = 'active' 
                AND date(expiry_date) = ?
            ''', (target_date.isoformat(),))
            
            users = cursor.fetchall()
            
            for email, expiry_str, last_notification_str in users:
                expiry_date = datetime.fromisoformat(expiry_str)
                
                # 이미 알림을 보냈는지 확인
                should_send = True
                if last_notification_str:
                    last_notification = datetime.fromisoformat(last_notification_str)
                    if (datetime.now() - last_notification).days < 1:
                        should_send = False
                
                if should_send:
                    self._send_expiry_warning_email(email, expiry_date, days)
                    
                    # 마지막 알림 시간 업데이트
                    cursor.execute('''
                        UPDATE users SET last_notification = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE email = ?
                    ''', (datetime.now().isoformat(), email))
        
        conn.commit()
        conn.close()
    
    def remove_expired_users(self):
        """만료된 사용자 자동 제거"""
        logger.info("🗑️ 만료된 사용자를 확인합니다...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email FROM users 
            WHERE status = 'active' AND date(expiry_date) < date('now')
        ''')
        
        expired_users = cursor.fetchall()
        conn.close()
        
        for (email,) in expired_users:
            logger.info(f"⏰ 만료된 사용자 제거: {email}")
            self.remove_user(email, "권한 만료로 인한 자동 제거")
    
    def generate_daily_report(self):
        """일일 보고서 생성"""
        logger.info("📊 일일 보고서를 생성합니다...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 통계 수집
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
        active_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "removed"')
        removed_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE status = "active" AND date(expiry_date) <= date('now', '+7 days')
        ''')
        expiring_soon = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM notifications 
            WHERE date(sent_date) = date('now') AND success = 1
        ''')
        emails_sent_today = cursor.fetchone()[0]
        
        conn.close()
        
        # 관리자에게 보고서 이메일 발송
        admin_email = self.config.get('notification_settings', {}).get('admin_email')
        if admin_email:
            subject = f"📊 GA4 자동화 시스템 일일 보고서 - {datetime.now().strftime('%Y-%m-%d')}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); 
                               color: white; padding: 30px; border-radius: 10px; text-align: center;">
                        <h1 style="margin: 0; font-size: 28px;">📊 일일 보고서</h1>
                        <p style="margin: 10px 0 0 0; font-size: 18px;">{datetime.now().strftime('%Y년 %m월 %d일')}</p>
                    </div>
                    
                    <div style="padding: 30px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                        <h2 style="color: #2c3e50; margin-top: 0;">📈 사용자 통계</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 10px 0; font-weight: bold; border-bottom: 1px solid #ddd;">활성 사용자:</td><td style="border-bottom: 1px solid #ddd;">{active_users}명</td></tr>
                            <tr><td style="padding: 10px 0; font-weight: bold; border-bottom: 1px solid #ddd;">제거된 사용자:</td><td style="border-bottom: 1px solid #ddd;">{removed_users}명</td></tr>
                            <tr><td style="padding: 10px 0; font-weight: bold; border-bottom: 1px solid #ddd;">7일 내 만료 예정:</td><td style="border-bottom: 1px solid #ddd;">{expiring_soon}명</td></tr>
                            <tr><td style="padding: 10px 0; font-weight: bold;">오늘 발송된 이메일:</td><td>{emails_sent_today}건</td></tr>
                        </table>
                    </div>
                    
                    <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                        <p>GA4 자동화 시스템이 정상적으로 운영되고 있습니다.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            self._send_email(admin_email, subject, html_content, NotificationType.ERROR)
    
    def start_scheduler(self):
        """스케줄러 시작"""
        logger.info("⏰ 스케줄러를 시작합니다...")
        
        # 매일 오전 9시에 만료 사용자 확인
        schedule.every().day.at("09:00").do(self.check_expiring_users)
        
        # 매일 오전 10시에 만료된 사용자 제거
        schedule.every().day.at("10:00").do(self.remove_expired_users)
        
        # 매일 오후 6시에 일일 보고서 생성
        schedule.every().day.at("18:00").do(self.generate_daily_report)
        
        # 매시간마다 만료 확인 (급한 경우 대비)
        schedule.every().hour.do(self.check_expiring_users)
        
        logger.info("✅ 스케줄러가 설정되었습니다.")
        
        # 무한 루프로 스케줄 실행
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 확인

    # === 유틸리티 메서드 ===
    
    def _log_action(self, action: str, details: str, user_email: str = None):
        """시스템 로그 기록"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_logs (level, action, details, user_email)
            VALUES ('INFO', ?, ?, ?)
        ''', (action, details, user_email))
        
        conn.commit()
        conn.close()
    
    def _log_notification(self, user_email: str, notification_type: NotificationType, 
                         message: str, success: bool, error_message: str = None):
        """알림 로그 기록"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications 
            (user_email, notification_type, sent_date, message, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_email, notification_type.value, datetime.now().isoformat(),
            message, 1 if success else 0, error_message
        ))
        
        conn.commit()
        conn.close()
    
    def get_user_list(self) -> List[Dict]:
        """사용자 목록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, role, added_date, expiry_date, department, notes, status
            FROM users ORDER BY added_date DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'email': row[0],
                'role': row[1],
                'added_date': row[2],
                'expiry_date': row[3],
                'department': row[4],
                'notes': row[5],
                'status': row[6]
            })
        
        conn.close()
        return users
    
    def get_system_stats(self) -> Dict:
        """시스템 통계 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "active"')
        stats['active_users'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "removed"')
        stats['removed_users'] = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE status = "active" AND date(expiry_date) <= date('now', '+7 days')
        ''')
        stats['expiring_soon'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE success = 1')
        stats['total_emails_sent'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

def main():
    """메인 실행 함수"""
    print("🚀 GA4 완전 자동화 시스템")
    print("=" * 50)
    
    try:
        system = GA4AutomationSystem()
        
        while True:
            print("\n📋 메뉴를 선택하세요:")
            print("1. 사용자 추가")
            print("2. 사용자 제거")
            print("3. 권한 연장")
            print("4. 사용자 목록 조회")
            print("5. 시스템 통계")
            print("6. 만료 예정 사용자 확인")
            print("7. 스케줄러 시작")
            print("8. 테스트 이메일 발송")
            print("0. 종료")
            
            choice = input("\n선택: ").strip()
            
            if choice == "1":
                # 사용자 추가
                email = input("이메일: ").strip()
                print("역할 선택:")
                print("1. Viewer (조회만)")
                print("2. Analyst (분석)")
                print("3. Editor (편집)")
                print("4. Admin (관리)")
                
                role_choice = input("역할 번호: ").strip()
                role_map = {
                    "1": UserRole.VIEWER,
                    "2": UserRole.ANALYST,
                    "3": UserRole.EDITOR,
                    "4": UserRole.ADMIN
                }
                
                role = role_map.get(role_choice, UserRole.ANALYST)
                department = input("부서 (선택사항): ").strip()
                expiry_days = int(input("만료 일수 (기본 90일): ").strip() or "90")
                notes = input("메모 (선택사항): ").strip()
                
                if system.add_user(email, role, department, expiry_days, notes):
                    print(f"✅ 사용자 {email}이 성공적으로 추가되었습니다.")
                else:
                    print(f"❌ 사용자 추가에 실패했습니다.")
            
            elif choice == "2":
                # 사용자 제거
                email = input("제거할 사용자 이메일: ").strip()
                reason = input("제거 사유: ").strip()
                
                if system.remove_user(email, reason):
                    print(f"✅ 사용자 {email}이 성공적으로 제거되었습니다.")
                else:
                    print(f"❌ 사용자 제거에 실패했습니다.")
            
            elif choice == "3":
                # 권한 연장
                email = input("연장할 사용자 이메일: ").strip()
                days = int(input("연장할 일수 (기본 90일): ").strip() or "90")
                
                if system.extend_user_access(email, days):
                    print(f"✅ 사용자 {email}의 권한이 {days}일 연장되었습니다.")
                else:
                    print(f"❌ 권한 연장에 실패했습니다.")
            
            elif choice == "4":
                # 사용자 목록 조회
                users = system.get_user_list()
                print(f"\n📋 전체 사용자 목록 ({len(users)}명)")
                print("-" * 80)
                
                for user in users:
                    expiry_date = datetime.fromisoformat(user['expiry_date'])
                    days_left = (expiry_date - datetime.now()).days
                    status_icon = "✅" if user['status'] == 'active' else "❌"
                    
                    print(f"{status_icon} {user['email']}")
                    print(f"   역할: {user['role']} | 부서: {user['department'] or '미지정'}")
                    print(f"   만료: {expiry_date.strftime('%Y-%m-%d')} ({days_left}일 남음)")
                    print()
            
            elif choice == "5":
                # 시스템 통계
                stats = system.get_system_stats()
                print(f"\n📊 시스템 통계")
                print("-" * 30)
                print(f"활성 사용자: {stats['active_users']}명")
                print(f"제거된 사용자: {stats['removed_users']}명")
                print(f"7일 내 만료 예정: {stats['expiring_soon']}명")
                print(f"총 발송된 이메일: {stats['total_emails_sent']}건")
            
            elif choice == "6":
                # 만료 예정 사용자 확인
                print("🔍 만료 예정 사용자를 확인하고 알림을 발송합니다...")
                system.check_expiring_users()
                print("✅ 완료되었습니다.")
            
            elif choice == "7":
                # 스케줄러 시작
                print("⏰ 스케줄러를 시작합니다...")
                print("Ctrl+C로 중단할 수 있습니다.")
                try:
                    system.start_scheduler()
                except KeyboardInterrupt:
                    print("\n⏹️ 스케줄러가 중단되었습니다.")
            
            elif choice == "8":
                # 테스트 이메일 발송
                email = input("테스트 이메일을 받을 주소: ").strip()
                system._send_welcome_email(email, UserRole.ANALYST, 
                                         datetime.now() + timedelta(days=90), "테스트 부서")
                print("✅ 테스트 이메일이 발송되었습니다.")
            
            elif choice == "0":
                print("👋 시스템을 종료합니다.")
                break
            
            else:
                print("❌ 잘못된 선택입니다.")
    
    except KeyboardInterrupt:
        print("\n👋 시스템이 중단되었습니다.")
    except Exception as e:
        logger.error(f"❌ 시스템 오류: {e}")
        print(f"❌ 시스템 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main() 