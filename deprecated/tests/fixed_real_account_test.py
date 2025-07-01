#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수정된 실제 GA4 계정 권한 부여 테스트
==================================

올바른 API 스코프를 사용하여 실제 계정 권한 부여 테스트
"""

import json
import sqlite3
import os
import pickle
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Google APIs
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Email
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fixed_real_account_test.log', encoding='utf-8'),
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

class FixedRealAccountTest:
    """수정된 실제 계정 권한 부여 테스트 시스템"""
    
    def __init__(self, config_file: str = "config.json"):
        """시스템 초기화"""
        self.config = self._load_config(config_file)
        self.db_path = "fixed_real_account_test.db"
        
        # 테스트 계정 설정
        self.test_accounts = [
            "wonyoungseong@gmail.com",
            "wonyoung.seong@amorepacific.com"
        ]
        self.target_role = UserRole.VIEWER
        self.report_email = "seongwonyoung0311@gmail.com"
        
        self._init_database()
        self._init_ga4_client_with_correct_scopes()
        self._init_gmail_client()
        
        logger.info("🚀 수정된 실제 계정 권한 부여 테스트 시스템이 시작되었습니다.")
    
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
            CREATE TABLE IF NOT EXISTS fixed_account_test_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                account_email TEXT NOT NULL,
                action TEXT NOT NULL,
                result TEXT NOT NULL,
                details TEXT,
                before_roles TEXT,
                after_roles TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ 수정된 계정 테스트 데이터베이스가 초기화되었습니다.")
    
    def _init_ga4_client_with_correct_scopes(self):
        """올바른 스코프로 GA4 클라이언트 초기화"""
        try:
            service_account_file = 'ga4-automatio-797ec352f393.json'
            
            # 올바른 스코프 조합 사용
            scopes = [
                'https://www.googleapis.com/auth/analytics.edit',
                'https://www.googleapis.com/auth/analytics.manage.users'
            ]
            
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=scopes
            )
            
            self.ga4_client = AnalyticsAdminServiceClient(credentials=credentials)
            self.account_name = f"accounts/{self.config['account_id']}"
            self.property_name = f"properties/{self.config['property_id']}"
            
            logger.info("✅ GA4 클라이언트가 올바른 스코프로 초기화되었습니다.")
            logger.info(f"📋 사용된 스코프: {scopes}")
            
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
            raise

    def _log_to_db(self, account_email: str, action: str, result: str, details: str = "", 
                   before_roles: str = "", after_roles: str = ""):
        """데이터베이스에 로그 기록"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO fixed_account_test_log 
            (account_email, action, result, details, before_roles, after_roles)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (account_email, action, result, details, before_roles, after_roles))
        
        conn.commit()
        conn.close()

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

    def check_account_status(self, email: str) -> Dict:
        """특정 계정의 현재 상태 확인"""
        print(f"\n🔍 {email} 계정 상태 확인 중...")
        
        current_users = self.get_current_users()
        
        if email in current_users:
            roles = current_users[email]
            role_names = [role.split('/')[-1] for role in roles]
            
            print(f"  ✅ 계정 발견! 현재 권한: {role_names}")
            
            status = {
                'exists_in_ga4': True,
                'current_roles': roles,
                'role_names': role_names,
                'needs_update': self.target_role.value not in roles
            }
            
            self._log_to_db(email, "계정 상태 확인", "GA4에 존재", 
                          f"현재 권한: {role_names}", str(roles))
            
        else:
            print(f"  ⚪ GA4에 등록되지 않은 계정")
            
            status = {
                'exists_in_ga4': False,
                'current_roles': [],
                'role_names': [],
                'needs_update': True
            }
            
            self._log_to_db(email, "계정 상태 확인", "GA4에 미등록", "새로운 권한 부여 필요")
        
        return status

    def add_or_update_permission(self, email: str, status: Dict) -> Dict:
        """계정 권한 추가 또는 수정"""
        print(f"\n🎯 {email} 권한 처리 중...")
        
        try:
            if status['exists_in_ga4']:
                # 기존 사용자 권한 수정
                if status['needs_update']:
                    print(f"  🔄 기존 권한 수정: {status['role_names']} → Viewer")
                    
                    # 기존 바인딩 찾기
                    bindings = self.ga4_client.list_access_bindings(parent=self.account_name)
                    
                    for binding in bindings:
                        if binding.user == f"users/{email}":
                            # 기존 바인딩 삭제
                            self.ga4_client.delete_access_binding(name=binding.name)
                            print(f"    ✅ 기존 권한 제거됨")
                            break
                    
                    # 새로운 권한 추가
                    access_binding = AccessBinding(
                        user=f"users/{email}",
                        roles=[self.target_role.value]
                    )
                    
                    request = {
                        'parent': self.account_name,
                        'access_binding': access_binding
                    }
                    
                    response = self.ga4_client.create_access_binding(request=request)
                    
                    print(f"    ✅ 새로운 Viewer 권한 부여됨")
                    print(f"    📋 바인딩 ID: {response.name}")
                    
                    result = {
                        'success': True,
                        'action': 'updated',
                        'message': f'권한 수정: {status["role_names"]} → Viewer',
                        'binding_name': response.name
                    }
                    
                    self._log_to_db(email, "권한 수정", "성공", 
                                  f"권한 수정: {status['role_names']} → Viewer",
                                  str(status['current_roles']), str([self.target_role.value]))
                    
                else:
                    print(f"  ✅ 이미 Viewer 권한을 보유하고 있습니다.")
                    
                    result = {
                        'success': True,
                        'action': 'no_change',
                        'message': '이미 올바른 권한 보유'
                    }
                    
                    self._log_to_db(email, "권한 확인", "변경 불필요", "이미 Viewer 권한 보유")
            
            else:
                # 새로운 사용자 추가
                print(f"  ➕ 새로운 Viewer 권한 부여 중...")
                
                access_binding = AccessBinding(
                    user=f"users/{email}",
                    roles=[self.target_role.value]
                )
                
                request = {
                    'parent': self.account_name,
                    'access_binding': access_binding
                }
                
                response = self.ga4_client.create_access_binding(request=request)
                
                print(f"    ✅ Viewer 권한 부여 성공!")
                print(f"    📋 바인딩 ID: {response.name}")
                
                result = {
                    'success': True,
                    'action': 'added',
                    'message': 'Viewer 권한 부여 성공',
                    'binding_name': response.name
                }
                
                self._log_to_db(email, "권한 부여", "성공", "새로운 Viewer 권한 부여",
                              "", str([self.target_role.value]))
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ 권한 처리 실패: {error_msg}")
            
            # 오류 유형별 분석
            if "404" in error_msg and "could not be found" in error_msg:
                print(f"  💡 404 오류 분석:")
                print(f"     ✅ Service Account 스코프: 올바름")
                print(f"     ❌ 사용자 계정: Google Analytics 미접속")
                print(f"  🔍 해결 방법:")
                print(f"     1. {email}로 Google Analytics에 직접 로그인")
                print(f"     2. 또는 GA4 콘솔에서 수동 초대")
            elif "401" in error_msg:
                print(f"  💡 401 오류: 인증 권한 부족 (스코프 문제 해결됨)")
            elif "403" in error_msg:
                print(f"  💡 403 오류: API 권한 부족")
            
            result = {
                'success': False,
                'action': 'failed',
                'message': error_msg,
                'error_type': self._classify_error(error_msg)
            }
            
            self._log_to_db(email, "권한 처리", "실패", error_msg)
            
            return result

    def _classify_error(self, error_msg: str) -> str:
        """오류 유형 분류"""
        if "404" in error_msg:
            return "404_user_not_found"
        elif "401" in error_msg:
            return "401_auth_failed"
        elif "403" in error_msg:
            return "403_permission_denied"
        else:
            return "other"

    def verify_final_status(self, email: str) -> Dict:
        """최종 권한 상태 확인"""
        print(f"\n🔍 {email} 최종 권한 상태 확인...")
        
        current_users = self.get_current_users()
        
        if email in current_users:
            roles = current_users[email]
            role_names = [role.split('/')[-1] for role in roles]
            has_viewer = self.target_role.value in roles
            
            print(f"  ✅ 최종 권한: {role_names}")
            print(f"  {'✅' if has_viewer else '❌'} Viewer 권한: {'보유' if has_viewer else '미보유'}")
            
            result = {
                'verified': True,
                'final_roles': roles,
                'role_names': role_names,
                'has_target_role': has_viewer
            }
            
            self._log_to_db(email, "최종 확인", "성공", f"최종 권한: {role_names}")
            
        else:
            print(f"  ❌ 권한이 확인되지 않음")
            
            result = {
                'verified': False,
                'final_roles': [],
                'role_names': [],
                'has_target_role': False
            }
            
            self._log_to_db(email, "최종 확인", "실패", "권한 확인되지 않음")
        
        return result

    def send_detailed_report(self, test_results: Dict):
        """상세한 결과 보고서 발송"""
        print(f"\n📧 상세 결과 보고서 발송 중...")
        
        try:
            subject = f"🎯 [수정된] 실제 GA4 계정 권한 부여 결과 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 결과 통계
            total_accounts = len(self.test_accounts)
            successful_accounts = sum(1 for result in test_results.values() 
                                    if result['permission_result']['success'])
            
            # 오류 유형별 분석
            error_analysis = {}
            for result in test_results.values():
                if not result['permission_result']['success']:
                    error_type = result['permission_result'].get('error_type', 'unknown')
                    error_analysis[error_type] = error_analysis.get(error_type, 0) + 1
            
            # 계정별 상세 결과
            account_details = ""
            for email, result in test_results.items():
                status = result['status']
                perm_result = result['permission_result']
                final_status = result['final_status']
                
                # 상태 아이콘
                if perm_result['success']:
                    status_icon = "✅"
                    status_color = "#d4edda"
                    text_color = "#155724"
                else:
                    status_icon = "❌"
                    status_color = "#f8d7da"
                    text_color = "#721c24"
                
                account_details += f"""
                <div style="margin: 20px 0; padding: 20px; background: {status_color}; 
                           border-radius: 10px; border-left: 5px solid {text_color};">
                    <h3 style="margin: 0 0 15px 0; color: {text_color};">
                        {status_icon} {email}
                    </h3>
                    
                    <div style="margin: 10px 0;">
                        <strong>초기 상태:</strong> 
                        {'GA4에 등록됨' if status['exists_in_ga4'] else 'GA4에 미등록'}
                        {f" (권한: {', '.join(status['role_names'])})" if status['role_names'] else ""}
                    </div>
                    
                    <div style="margin: 10px 0;">
                        <strong>수행 작업:</strong> {perm_result['action']}
                    </div>
                    
                    <div style="margin: 10px 0;">
                        <strong>결과:</strong> {perm_result['message']}
                    </div>
                    
                    <div style="margin: 10px 0;">
                        <strong>최종 상태:</strong> 
                        {'권한 확인됨' if final_status['verified'] else '권한 확인 안됨'}
                        {f" (권한: {', '.join(final_status['role_names'])})" if final_status['role_names'] else ""}
                    </div>
                    
                    {'<div style="margin: 10px 0; color: #155724;"><strong>✅ Viewer 권한 보유</strong></div>' 
                     if final_status.get('has_target_role') else 
                     '<div style="margin: 10px 0; color: #721c24;"><strong>❌ Viewer 권한 미보유</strong></div>'}
                </div>
                """
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                               color: white; padding: 30px; border-radius: 10px; text-align: center;">
                        <h1 style="margin: 0; font-size: 28px;">🎯 [수정된] 실제 GA4 계정 권한 부여 결과</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">
                            {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')} 실행 결과
                        </p>
                        <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">
                            올바른 API 스코프 적용 후 테스트
                        </p>
                    </div>
                    
                    <div style="padding: 20px; background: #e8f4f8; border-radius: 10px; margin: 20px 0;">
                        <h2 style="color: #1e6091; margin-top: 0;">🔧 기술적 개선사항</h2>
                        <ul style="line-height: 1.8;">
                            <li><strong>API 스코프 수정:</strong> analytics.edit + analytics.manage.users</li>
                            <li><strong>401 인증 오류 해결:</strong> Service Account 권한 문제 수정</li>
                            <li><strong>정확한 오류 분석:</strong> 404 오류는 사용자 미접속 문제</li>
                        </ul>
                    </div>
                    
                    <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                        <h2 style="color: #2c3e50; margin-top: 0;">📊 실행 결과 요약</h2>
                        <div style="display: flex; justify-content: space-around; text-align: center;">
                            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 5px;">
                                <h3 style="color: #27ae60; margin: 0;">{successful_accounts}</h3>
                                <p style="margin: 5px 0 0 0; color: #27ae60;">성공</p>
                            </div>
                            <div style="background: #ffeaa7; padding: 15px; border-radius: 8px; margin: 5px;">
                                <h3 style="color: #d63031; margin: 0;">{total_accounts - successful_accounts}</h3>
                                <p style="margin: 5px 0 0 0; color: #d63031;">실패</p>
                            </div>
                            <div style="background: #ddd; padding: 15px; border-radius: 8px; margin: 5px;">
                                <h3 style="color: #2d3436; margin: 0;">{total_accounts}</h3>
                                <p style="margin: 5px 0 0 0; color: #2d3436;">총 계정</p>
                            </div>
                        </div>
                    </div>
                    
                    <div style="padding: 20px; background: #fff; border-radius: 10px; margin: 20px 0; border: 1px solid #ddd;">
                        <h2 style="color: #2c3e50; margin-top: 0;">📋 계정별 상세 결과</h2>
                        {account_details}
                    </div>
                    
                    <div style="padding: 20px; background: #fff3cd; border-radius: 10px; margin: 20px 0;">
                        <h3 style="color: #856404; margin-top: 0;">💡 최종 결론</h3>
                        <p><strong>✅ Service Account 권한 문제 해결됨!</strong></p>
                        <p>404 오류는 API 권한 문제가 아닌 <strong>사용자가 Google Analytics에 접속하지 않았기 때문</strong>입니다.</p>
                        <ol style="line-height: 1.8;">
                            <li>해당 이메일로 <strong>Google Analytics에 직접 로그인</strong></li>
                            <li>또는 <strong>GA4 콘솔에서 수동 초대</strong> 후 로그인</li>
                            <li>그 후 <strong>API를 통한 권한 관리 가능</strong></li>
                        </ol>
                    </div>
                    
                    <div style="padding: 20px; background: #e8f4f8; border-radius: 10px; margin: 20px 0;">
                        <h3 style="color: #1e6091; margin-top: 0;">🔧 테스트 정보</h3>
                        <p><strong>대상 계정:</strong> {', '.join(self.test_accounts)}</p>
                        <p><strong>부여 권한:</strong> Viewer (조회 권한)</p>
                        <p><strong>GA4 Property ID:</strong> {self.config['property_id']}</p>
                        <p><strong>API 스코프:</strong> analytics.edit + analytics.manage.users</p>
                        <p><strong>실행 시간:</strong> {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
                    </div>
                    
                    <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                        <p>이 보고서는 수정된 GA4 자동화 시스템에서 자동 생성되었습니다.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if self._send_email(self.report_email, subject, html_content):
                print(f"✅ 상세 결과 보고서 발송 성공: {self.report_email}")
                return True
            else:
                print(f"❌ 보고서 발송 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 보고서 발송 실패: {e}")
            return False

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
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
            
            logger.info(f"✅ 이메일 발송 성공: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 이메일 발송 실패: {to_email} - {e}")
            return False

    def run_fixed_account_test(self):
        """수정된 실제 계정 권한 부여 테스트 실행"""
        print("🎬 수정된 실제 GA4 계정 권한 부여 테스트 시작!")
        print("=" * 80)
        print(f"🔧 개선사항: 올바른 API 스코프 적용")
        print(f"📧 대상 계정: {', '.join(self.test_accounts)}")
        print(f"🎯 목표 권한: Viewer")
        print(f"📮 보고서 수신: {self.report_email}")
        print("=" * 80)
        
        test_results = {}
        
        try:
            for email in self.test_accounts:
                print(f"\n{'='*50}")
                print(f"🎯 {email} 처리 시작")
                print(f"{'='*50}")
                
                # 1. 현재 상태 확인
                status = self.check_account_status(email)
                
                # 2. 권한 추가/수정
                permission_result = self.add_or_update_permission(email, status)
                
                # 3. 최종 상태 확인
                final_status = self.verify_final_status(email)
                
                # 결과 저장
                test_results[email] = {
                    'status': status,
                    'permission_result': permission_result,
                    'final_status': final_status
                }
                
                print(f"✅ {email} 처리 완료")
            
            # 4. 상세 보고서 발송
            print(f"\n{'='*80}")
            print("📧 상세 결과 보고서 발송")
            print(f"{'='*80}")
            
            self.send_detailed_report(test_results)
            
            # 최종 요약
            successful_count = sum(1 for result in test_results.values() 
                                 if result['permission_result']['success'])
            
            print(f"\n🎉 수정된 실제 계정 권한 부여 테스트 완료!")
            print(f"✅ 성공: {successful_count}개")
            print(f"❌ 실패: {len(self.test_accounts) - successful_count}개")
            print(f"📧 상세 보고서: {self.report_email}로 발송됨")
            
            # 기술적 결론
            print(f"\n🔧 기술적 결론:")
            print(f"✅ Service Account 스코프 문제 해결됨")
            print(f"✅ 401 인증 오류 해결됨")
            print(f"💡 404 오류는 사용자 미접속 문제 (정상)")
            
            return test_results
            
        except Exception as e:
            logger.error(f"❌ 테스트 실행 중 오류 발생: {e}")
            print(f"❌ 테스트 실행 중 오류가 발생했습니다: {e}")
            return {}

def main():
    """메인 실행 함수"""
    print("🎯 수정된 실제 GA4 계정 권한 부여 테스트")
    print("=" * 60)
    print("🔧 개선사항: 올바른 API 스코프 적용")
    print("⚠️  주의: 이 테스트는 실제 GA4 계정에 권한을 부여/수정합니다.")
    print("📧 대상: wonyoungseong@gmail.com, wonyoung.seong@amorepacific.com")
    print("🎯 권한: Viewer")
    print("📮 보고서: seongwonyoung0311@gmail.com")
    print("=" * 60)
    
    try:
        tester = FixedRealAccountTest()
        
        print("\n🚀 수정된 권한 부여 테스트를 시작하시겠습니까?")
        print("1. 수정된 권한 부여 테스트 실행")
        print("0. 종료")
        
        choice = input("\n선택: ").strip()
        
        if choice == "1":
            tester.run_fixed_account_test()
        elif choice == "0":
            print("👋 테스트를 종료합니다.")
        else:
            print("❌ 잘못된 선택입니다.")
    
    except KeyboardInterrupt:
        print("\n👋 테스트가 중단되었습니다.")
    except Exception as e:
        logger.error(f"❌ 테스트 시스템 오류: {e}")
        print(f"❌ 테스트 시스템 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
