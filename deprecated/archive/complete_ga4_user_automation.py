#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 GA4 사용자 자동화 시스템
=============================

Google Analytics Admin API의 제약사항을 우회하여
완전한 사용자 권한 관리 자동화를 구현합니다.
"""

import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Google APIs
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding
from google.oauth2 import service_account

# Gmail for notifications
import base64
import pickle
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_ga4_automation.log', encoding='utf-8'),
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

class InvitationMethod(Enum):
    """초대 방법"""
    API_DIRECT = "api_direct"           # API 직접 추가
    EMAIL_INVITATION = "email_invite"   # 이메일 초대
    MANUAL_CONSOLE = "manual_console"   # 수동 콘솔 추가

class CompleteGA4UserAutomation:
    """완전한 GA4 사용자 자동화 시스템"""
    
    def __init__(self, config_file: str = "config.json"):
        """시스템 초기화"""
        self.config = self._load_config(config_file)
        self.db_path = "complete_ga4_automation.db"
        
        self._init_database()
        self._init_ga4_client()
        self._init_gmail_client()
        
        logger.info("🚀 완전한 GA4 사용자 자동화 시스템이 시작되었습니다.")
    
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
        
        # 사용자 관리 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_management (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                current_role TEXT,
                target_role TEXT,
                status TEXT DEFAULT 'pending',
                invitation_method TEXT,
                invited_at TEXT,
                accepted_at TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # 자동화 로그 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                email TEXT,
                action TEXT,
                method TEXT,
                result TEXT,
                error_details TEXT,
                retry_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ 완전한 자동화 데이터베이스가 초기화되었습니다.")
    
    def _init_ga4_client(self):
        """GA4 클라이언트 초기화"""
        try:
            service_account_file = 'ga4-automatio-797ec352f393.json'
            scopes = [
                'https://www.googleapis.com/auth/analytics.edit',
                'https://www.googleapis.com/auth/analytics.manage.users'
            ]
            
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=scopes
            )
            
            self.ga4_client = AnalyticsAdminServiceClient(credentials=credentials)
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
            self.gmail_service = None

    def get_current_users(self) -> Dict[str, List[str]]:
        """현재 GA4 사용자 목록 조회"""
        try:
            bindings = self.ga4_client.list_access_bindings(parent=self.account_name)
            
            current_users = {}
            for binding in bindings:
                user_email = binding.user.replace("users/", "")
                roles = [role for role in binding.roles]
                current_users[user_email] = roles
            
            return current_users
            
        except Exception as e:
            logger.error(f"❌ 현재 사용자 조회 실패: {e}")
            return {}

    def try_direct_api_addition(self, email: str, role: UserRole) -> Tuple[bool, str]:
        """API 직접 추가 시도"""
        try:
            access_binding = AccessBinding(
                user=f"users/{email}",
                roles=[role.value]
            )
            
            result = self.ga4_client.create_access_binding(
                parent=self.account_name,
                access_binding=access_binding
            )
            
            logger.info(f"✅ {email} API 직접 추가 성공")
            return True, f"성공: {result.name}"
            
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg and "could not be found" in error_msg:
                return False, "사용자가 Google Analytics에 접속한 적이 없음"
            elif "409" in error_msg or "already exists" in error_msg:
                return True, "이미 권한이 존재함"
            else:
                return False, f"API 오류: {error_msg}"

    def send_invitation_email(self, email: str, role: UserRole) -> Tuple[bool, str]:
        """이메일 초대 발송"""
        if not self.gmail_service:
            return False, "Gmail 서비스가 초기화되지 않음"
        
        try:
            # 초대 이메일 생성
            subject = f"[GA4 자동화] Google Analytics 권한 초대 - {email}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4285f4;">🎯 Google Analytics 4 권한 초대</h2>
                    
                    <p>안녕하세요,</p>
                    
                    <p><strong>{email}</strong> 계정에 Google Analytics 4 권한을 부여하기 위해 연락드립니다.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #1a73e8;">📋 권한 정보</h3>
                        <ul>
                            <li><strong>계정:</strong> BETC (Account ID: {self.config['account_id']})</li>
                            <li><strong>속성:</strong> [Edu]Ecommerce - Beauty Cosmetic</li>
                            <li><strong>권한 수준:</strong> {role.name} ({role.value})</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <h3 style="margin-top: 0; color: #856404;">⚠️ 중요: 초기 설정 필요</h3>
                        <p>API를 통한 자동 권한 관리를 위해 다음 단계를 완료해주세요:</p>
                        <ol>
                            <li><strong>Google Analytics 접속:</strong> <a href="https://analytics.google.com" target="_blank">analytics.google.com</a></li>
                            <li><strong>계정 로그인:</strong> {email}로 로그인</li>
                            <li><strong>초기 설정 완료:</strong> Google Analytics 시스템에 계정 등록</li>
                        </ol>
                    </div>
                    
                    <div style="background-color: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <h3 style="margin-top: 0; color: #155724;">✅ 완료 후 혜택</h3>
                        <ul>
                            <li>자동 권한 관리</li>
                            <li>권한 만료 알림</li>
                            <li>실시간 권한 변경</li>
                            <li>상세 활동 로그</li>
                        </ul>
                    </div>
                    
                    <p>위 단계를 완료하시면 자동으로 권한이 부여됩니다.</p>
                    
                    <p>문의사항이 있으시면 언제든 연락주세요.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px;">
                        이 메일은 GA4 자동화 시스템에서 발송되었습니다.<br>
                        발송일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            # 이메일 발송
            message = MIMEMultipart('alternative')
            message['to'] = email
            message['subject'] = subject
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            send_result = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"✅ {email}에게 초대 이메일 발송 성공")
            return True, f"이메일 발송 성공: {send_result['id']}"
            
        except Exception as e:
            logger.error(f"❌ {email} 이메일 발송 실패: {e}")
            return False, f"이메일 발송 실패: {e}"

    def add_user_with_smart_method(self, email: str, role: UserRole = UserRole.VIEWER) -> Dict:
        """지능형 사용자 추가 (여러 방법 시도)"""
        result = {
            'email': email,
            'target_role': role.name,
            'success': False,
            'method_used': None,
            'message': '',
            'attempts': []
        }
        
        # 1단계: API 직접 추가 시도
        logger.info(f"🎯 {email} - 1단계: API 직접 추가 시도")
        api_success, api_message = self.try_direct_api_addition(email, role)
        result['attempts'].append({
            'method': InvitationMethod.API_DIRECT.value,
            'success': api_success,
            'message': api_message
        })
        
        if api_success:
            result['success'] = True
            result['method_used'] = InvitationMethod.API_DIRECT.value
            result['message'] = api_message
            self._log_to_db(email, "add_user", InvitationMethod.API_DIRECT.value, "success", api_message)
            return result
        
        # 2단계: 이메일 초대 발송
        logger.info(f"🎯 {email} - 2단계: 이메일 초대 발송")
        email_success, email_message = self.send_invitation_email(email, role)
        result['attempts'].append({
            'method': InvitationMethod.EMAIL_INVITATION.value,
            'success': email_success,
            'message': email_message
        })
        
        if email_success:
            result['method_used'] = InvitationMethod.EMAIL_INVITATION.value
            result['message'] = f"초대 이메일 발송됨. 사용자가 로그인 후 자동 권한 부여 예정"
            
            # 데이터베이스에 대기 상태로 기록
            self._save_pending_user(email, role)
            self._log_to_db(email, "send_invitation", InvitationMethod.EMAIL_INVITATION.value, "success", email_message)
        else:
            result['message'] = f"모든 방법 실패. API: {api_message}, Email: {email_message}"
            self._log_to_db(email, "add_user", "all_methods", "failed", result['message'])
        
        return result

    def _save_pending_user(self, email: str, role: UserRole):
        """대기 중인 사용자 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_management 
            (email, target_role, status, invitation_method, invited_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, role.value, 'pending', InvitationMethod.EMAIL_INVITATION.value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def _log_to_db(self, email: str, action: str, method: str, result: str, details: str = ""):
        """데이터베이스에 로그 기록"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO automation_log 
            (email, action, method, result, error_details)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, action, method, result, details))
        
        conn.commit()
        conn.close()

    def check_pending_users_and_retry(self):
        """대기 중인 사용자들 재시도"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 5분 이상 대기 중인 사용자들 조회
        cutoff_time = (datetime.now() - timedelta(minutes=5)).isoformat()
        cursor.execute('''
            SELECT email, target_role FROM user_management 
            WHERE status = 'pending' AND invited_at < ?
        ''', (cutoff_time,))
        
        pending_users = cursor.fetchall()
        conn.close()
        
        for email, role_value in pending_users:
            role = UserRole(role_value)
            logger.info(f"🔄 대기 중인 사용자 재시도: {email}")
            
            api_success, api_message = self.try_direct_api_addition(email, role)
            if api_success:
                self._update_user_status(email, 'completed')
                logger.info(f"✅ {email} 재시도 성공!")

    def _update_user_status(self, email: str, status: str):
        """사용자 상태 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_management 
            SET status = ?, last_updated = ?
            WHERE email = ?
        ''', (status, datetime.now().isoformat(), email))
        
        conn.commit()
        conn.close()

    def bulk_add_users(self, users: List[Dict]) -> Dict:
        """대량 사용자 추가"""
        results = {
            'total': len(users),
            'successful': 0,
            'failed': 0,
            'pending': 0,
            'details': []
        }
        
        for user_info in users:
            email = user_info['email']
            role = UserRole(user_info.get('role', UserRole.VIEWER.value))
            
            result = self.add_user_with_smart_method(email, role)
            results['details'].append(result)
            
            if result['success']:
                results['successful'] += 1
            elif result['method_used'] == InvitationMethod.EMAIL_INVITATION.value:
                results['pending'] += 1
            else:
                results['failed'] += 1
        
        return results

def main():
    """메인 실행 함수"""
    print("🚀 완전한 GA4 사용자 자동화 시스템")
    print("=" * 60)
    
    # 시스템 초기화
    automation = CompleteGA4UserAutomation()
    
    # 테스트 사용자들
    test_users = [
        {
            "email": "wonyoungseong@gmail.com",
            "role": UserRole.VIEWER.value
        },
        {
            "email": "wonyoung.seong@amorepacific.com",
            "role": UserRole.VIEWER.value
        }
    ]
    
    print("🎯 지능형 사용자 추가 테스트 시작")
    print("-" * 40)
    
    # 대량 사용자 추가
    results = automation.bulk_add_users(test_users)
    
    print(f"\n📊 결과 요약:")
    print(f"   📈 총 처리: {results['total']}명")
    print(f"   ✅ 즉시 성공: {results['successful']}명")
    print(f"   ⏳ 초대 대기: {results['pending']}명")
    print(f"   ❌ 실패: {results['failed']}명")
    
    print(f"\n📋 상세 결과:")
    for detail in results['details']:
        print(f"   👤 {detail['email']}")
        print(f"      🎯 목표 권한: {detail['target_role']}")
        print(f"      📊 성공 여부: {'✅' if detail['success'] else '⏳' if detail['method_used'] else '❌'}")
        print(f"      🔧 사용 방법: {detail.get('method_used', 'None')}")
        print(f"      💬 메시지: {detail['message']}")
        print()

if __name__ == "__main__":
    main() 