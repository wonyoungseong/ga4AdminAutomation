#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 실제 사용자 권한 부여 완전 테스트
===================================

실제 Google 계정으로 GA4 권한 부여/제거를 테스트하는 완전한 시스템

테스트 계정:
- wonyoungseong@gmail.com (Viewer 권한)
- wonyoung.seong@amorepacific.com (Viewer 권한)

보고서 수신:
- seongwonyoung0311@gmail.com

시나리오:
1. 현재 사용자 상태 확인
2. 테스트 계정들에 Viewer 권한 부여
3. 권한 부여 확인
4. 실패 케이스 테스트 (존재하지 않는 계정)
5. 권한 제거 테스트
6. 완전한 결과 보고서 이메일 발송

Author: GA4 자동화 팀
Date: 2025-01-22
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
        logging.FileHandler('wonyoung_complete_test.log', encoding='utf-8'),
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

class TestResult:
    """테스트 결과 클래스"""
    def __init__(self):
        self.steps = []
        self.success_count = 0
        self.failure_count = 0
        self.start_time = datetime.now()
        self.end_time = None
    
    def add_step(self, step_name: str, action: str, success: bool, details: str = ""):
        """테스트 단계 추가"""
        self.steps.append({
            'step': step_name,
            'action': action,
            'success': success,
            'details': details,
            'timestamp': datetime.now()
        })
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
    
    def finish(self):
        """테스트 완료"""
        self.end_time = datetime.now()
    
    def get_duration(self) -> float:
        """테스트 소요 시간 반환"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

class GA4CompleteTest:
    """GA4 완전한 권한 부여 테스트 시스템"""
    
    def __init__(self, config_file: str = "config.json"):
        """시스템 초기화"""
        self.config = self._load_config(config_file)
        self.db_path = "wonyoung_complete_test.db"
        self.test_result = TestResult()
        
        # 테스트 계정 설정
        self.test_accounts = [
            "wonyoungseong@gmail.com",
            "wonyoung.seong@amorepacific.com"
        ]
        self.test_role = UserRole.VIEWER
        self.report_email = "seongwonyoung0311@gmail.com"
        
        self._init_database()
        self._init_ga4_client()
        self._init_gmail_client()
        
        logger.info("🚀 GA4 완전한 권한 부여 테스트 시스템이 시작되었습니다.")
    
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
            CREATE TABLE IF NOT EXISTS test_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                step TEXT NOT NULL,
                action TEXT NOT NULL,
                success INTEGER NOT NULL,
                details TEXT,
                test_account TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ 테스트 데이터베이스가 초기화되었습니다.")
    
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

    def _log_to_db(self, step: str, action: str, success: bool, details: str = "", test_account: str = ""):
        """데이터베이스에 로그 기록"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_log (step, action, success, details, test_account)
            VALUES (?, ?, ?, ?, ?)
        ''', (step, action, 1 if success else 0, details, test_account))
        
        conn.commit()
        conn.close()

    def step1_check_current_users(self) -> Tuple[List[Dict], Dict]:
        """1단계: 현재 사용자 상태 확인"""
        print("\n" + "="*70)
        print("🔍 1단계: 현재 GA4 사용자 상태 확인")
        print("="*70)
        
        try:
            bindings = self.ga4_client.list_access_bindings(parent=self.account_name)
            
            current_users = []
            for binding in bindings:
                user_email = binding.user.replace("users/", "")
                roles = [role for role in binding.roles]
                current_users.append({"email": user_email, "roles": roles})
            
            print(f"📋 현재 등록된 사용자: {len(current_users)}명")
            
            # 테스트 계정 상태 확인
            test_account_status = {}
            for test_email in self.test_accounts:
                found = False
                for user in current_users:
                    if user['email'] == test_email:
                        found = True
                        test_account_status[test_email] = {
                            'exists': True,
                            'roles': user['roles']
                        }
                        print(f"  ✅ {test_email} - 이미 등록됨 (권한: {[r.split('/')[-1] for r in user['roles']]})")
                        break
                
                if not found:
                    test_account_status[test_email] = {'exists': False, 'roles': []}
                    print(f"  ⚪ {test_email} - 미등록")
            
            self.test_result.add_step(
                "STEP1", "현재 사용자 확인", True,
                f"총 {len(current_users)}명, 테스트 계정 상태: {test_account_status}"
            )
            
            self._log_to_db("STEP1", "현재 사용자 확인", True, f"총 {len(current_users)}명 확인")
            
            return current_users, test_account_status
            
        except Exception as e:
            error_msg = f"사용자 확인 실패: {e}"
            logger.error(f"❌ {error_msg}")
            self.test_result.add_step("STEP1", "현재 사용자 확인", False, error_msg)
            self._log_to_db("STEP1", "현재 사용자 확인", False, error_msg)
            return [], {}

    def step2_add_test_users(self, test_account_status: Dict) -> Dict:
        """2단계: 테스트 계정들에 Viewer 권한 부여"""
        print("\n" + "="*70)
        print("👥 2단계: 테스트 계정들에 Viewer 권한 부여")
        print("="*70)
        
        add_results = {}
        
        for test_email in self.test_accounts:
            print(f"\n🎯 {test_email} 권한 부여 시도...")
            
            try:
                # 이미 권한이 있는지 확인
                if test_account_status.get(test_email, {}).get('exists', False):
                    print(f"  ⚠️  이미 권한이 있는 사용자입니다. 기존 권한 유지.")
                    add_results[test_email] = {
                        'success': True,
                        'action': 'already_exists',
                        'message': '이미 권한 보유'
                    }
                    continue
                
                # 새로운 권한 부여
                access_binding = AccessBinding(
                    user=f"users/{test_email}",
                    roles=[self.test_role.value]
                )
                
                request = {
                    'parent': self.account_name,
                    'access_binding': access_binding
                }
                
                response = self.ga4_client.create_access_binding(request=request)
                
                print(f"  ✅ 권한 부여 성공!")
                print(f"     - 권한: Viewer")
                print(f"     - 바인딩 ID: {response.name}")
                
                add_results[test_email] = {
                    'success': True,
                    'action': 'added',
                    'message': '권한 부여 성공',
                    'binding_name': response.name
                }
                
                self.test_result.add_step(
                    "STEP2", f"{test_email} 권한 부여", True,
                    f"Viewer 권한 부여 성공"
                )
                
                self._log_to_db("STEP2", "권한 부여", True, "Viewer 권한 부여 성공", test_email)
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ 권한 부여 실패: {error_msg}")
                
                add_results[test_email] = {
                    'success': False,
                    'action': 'failed',
                    'message': error_msg
                }
                
                self.test_result.add_step(
                    "STEP2", f"{test_email} 권한 부여", False, error_msg
                )
                
                self._log_to_db("STEP2", "권한 부여", False, error_msg, test_email)
        
        return add_results

    def step3_verify_permissions(self) -> Dict:
        """3단계: 권한 부여 확인"""
        print("\n" + "="*70)
        print("🔍 3단계: 권한 부여 결과 확인")
        print("="*70)
        
        verification_results = {}
        
        try:
            bindings = self.ga4_client.list_access_bindings(parent=self.account_name)
            
            current_users = {}
            for binding in bindings:
                user_email = binding.user.replace("users/", "")
                roles = [role for role in binding.roles]
                current_users[user_email] = roles
            
            for test_email in self.test_accounts:
                print(f"\n🔍 {test_email} 권한 확인...")
                
                if test_email in current_users:
                    roles = current_users[test_email]
                    role_names = [role.split('/')[-1] for role in roles]
                    
                    print(f"  ✅ 권한 확인됨: {role_names}")
                    
                    verification_results[test_email] = {
                        'verified': True,
                        'roles': roles,
                        'role_names': role_names
                    }
                    
                    self.test_result.add_step(
                        "STEP3", f"{test_email} 권한 확인", True,
                        f"권한: {role_names}"
                    )
                    
                    self._log_to_db("STEP3", "권한 확인", True, f"권한: {role_names}", test_email)
                    
                else:
                    print(f"  ❌ 권한이 확인되지 않음")
                    
                    verification_results[test_email] = {
                        'verified': False,
                        'roles': [],
                        'role_names': []
                    }
                    
                    self.test_result.add_step(
                        "STEP3", f"{test_email} 권한 확인", False,
                        "권한이 확인되지 않음"
                    )
                    
                    self._log_to_db("STEP3", "권한 확인", False, "권한이 확인되지 않음", test_email)
        
        except Exception as e:
            error_msg = f"권한 확인 실패: {e}"
            logger.error(f"❌ {error_msg}")
            
            for test_email in self.test_accounts:
                verification_results[test_email] = {
                    'verified': False,
                    'error': error_msg
                }
                
                self.test_result.add_step(
                    "STEP3", f"{test_email} 권한 확인", False, error_msg
                )
        
        return verification_results

    def step4_test_failure_cases(self) -> Dict:
        """4단계: 실패 케이스 테스트 (존재하지 않는 계정)"""
        print("\n" + "="*70)
        print("🧪 4단계: 실패 케이스 테스트")
        print("="*70)
        
        # 존재하지 않는 가상의 이메일 주소들
        fake_emails = [
            "nonexistent.user.12345@gmail.com",
            "fake.test.account@example.com"
        ]
        
        failure_results = {}
        
        for fake_email in fake_emails:
            print(f"\n🎯 존재하지 않는 계정 테스트: {fake_email}")
            
            try:
                access_binding = AccessBinding(
                    user=f"users/{fake_email}",
                    roles=[self.test_role.value]
                )
                
                request = {
                    'parent': self.account_name,
                    'access_binding': access_binding
                }
                
                response = self.ga4_client.create_access_binding(request=request)
                
                # 이 경우는 예상하지 않은 성공
                print(f"  ⚠️  예상과 다르게 성공함: {response.name}")
                
                failure_results[fake_email] = {
                    'expected_failure': True,
                    'actual_result': 'success',
                    'message': '예상과 다르게 성공함'
                }
                
                self.test_result.add_step(
                    "STEP4", f"{fake_email} 실패 테스트", False,
                    "예상한 실패가 발생하지 않음"
                )
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ✅ 예상된 실패 발생: {error_msg}")
                
                failure_results[fake_email] = {
                    'expected_failure': True,
                    'actual_result': 'failed',
                    'message': error_msg
                }
                
                self.test_result.add_step(
                    "STEP4", f"{fake_email} 실패 테스트", True,
                    f"예상된 실패: {error_msg}"
                )
                
                self._log_to_db("STEP4", "실패 케이스 테스트", True, f"예상된 실패: {error_msg}", fake_email)
        
        return failure_results

    def step5_cleanup_test_users(self, verification_results: Dict) -> Dict:
        """5단계: 테스트 계정 권한 제거 (정리)"""
        print("\n" + "="*70)
        print("🧹 5단계: 테스트 계정 권한 제거 (정리)")
        print("="*70)
        
        cleanup_results = {}
        
        # 자동으로 제거 진행 (테스트이므로)
        print("테스트 완료 후 자동으로 권한을 제거합니다...")
        
        for test_email in self.test_accounts:
            if verification_results.get(test_email, {}).get('verified', False):
                print(f"\n🎯 {test_email} 권한 제거 중...")
                
                try:
                    # 해당 사용자의 바인딩 찾기
                    bindings = self.ga4_client.list_access_bindings(parent=self.account_name)
                    
                    for binding in bindings:
                        if binding.user == f"users/{test_email}":
                            # 바인딩 제거
                            self.ga4_client.delete_access_binding(name=binding.name)
                            
                            print(f"  ✅ 권한 제거 성공")
                            
                            cleanup_results[test_email] = {
                                'removed': True,
                                'message': '권한 제거 성공'
                            }
                            
                            self.test_result.add_step(
                                "STEP5", f"{test_email} 권한 제거", True,
                                "권한 제거 성공"
                            )
                            
                            self._log_to_db("STEP5", "권한 제거", True, "권한 제거 성공", test_email)
                            break
                    else:
                        print(f"  ⚠️  제거할 권한을 찾을 수 없음")
                        cleanup_results[test_email] = {
                            'removed': False,
                            'message': '제거할 권한을 찾을 수 없음'
                        }
                
                except Exception as e:
                    error_msg = f"권한 제거 실패: {e}"
                    print(f"  ❌ {error_msg}")
                    
                    cleanup_results[test_email] = {
                        'removed': False,
                        'message': error_msg
                    }
                    
                    self.test_result.add_step(
                        "STEP5", f"{test_email} 권한 제거", False, error_msg
                    )
                    
                    self._log_to_db("STEP5", "권한 제거", False, error_msg, test_email)
            else:
                print(f"  ⚪ {test_email} - 제거할 권한 없음")
                cleanup_results[test_email] = {
                    'removed': False,
                    'message': '제거할 권한 없음'
                }
        
        return cleanup_results

    def step6_send_complete_report(self, all_results: Dict):
        """6단계: 완전한 결과 보고서 이메일 발송"""
        print("\n" + "="*70)
        print("📧 6단계: 완전한 테스트 결과 보고서 발송")
        print("="*70)
        
        self.test_result.finish()
        
        try:
            subject = f"🎯 GA4 권한 부여 완전 테스트 결과 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 결과 요약
            total_tests = len(self.test_result.steps)
            success_rate = (self.test_result.success_count / total_tests * 100) if total_tests > 0 else 0
            
            # 테스트 결과 테이블 생성
            results_html = ""
            for step in self.test_result.steps:
                status_icon = "✅" if step['success'] else "❌"
                status_color = "#d4edda" if step['success'] else "#f8d7da"
                text_color = "#155724" if step['success'] else "#721c24"
                
                results_html += f"""
                <tr style="background: {status_color};">
                    <td style="padding: 10px; border: 1px solid #ddd; color: {text_color};">{step['step']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: {text_color};">{step['action']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: {text_color};">{status_icon}</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: {text_color};">{step['details']}</td>
                </tr>
                """
            
            # 계정별 결과 요약
            account_summary = ""
            for email in self.test_accounts:
                account_summary += f"""
                <div style="margin: 10px 0; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">📧 {email}</h4>
                """
                
                # 각 단계별 결과
                for result_key, result_data in all_results.items():
                    if email in result_data:
                        account_result = result_data[email]
                        if isinstance(account_result, dict):
                            if 'success' in account_result:
                                icon = "✅" if account_result['success'] else "❌"
                                account_summary += f"<p style='margin: 5px 0;'>{icon} {result_key}: {account_result.get('message', '')}</p>"
                            elif 'verified' in account_result:
                                icon = "✅" if account_result['verified'] else "❌"
                                roles = ', '.join(account_result.get('role_names', []))
                                account_summary += f"<p style='margin: 5px 0;'>{icon} 권한 확인: {roles or '없음'}</p>"
                
                account_summary += "</div>"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 900px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                               color: white; padding: 30px; border-radius: 10px; text-align: center;">
                        <h1 style="margin: 0; font-size: 32px;">🎯 GA4 권한 부여 완전 테스트 결과</h1>
                        <p style="margin: 10px 0 0 0; font-size: 18px;">실제 계정으로 수행한 완전한 권한 관리 테스트</p>
                    </div>
                    
                    <div style="padding: 30px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                        <h2 style="color: #2c3e50; margin-top: 0;">📊 테스트 결과 요약</h2>
                        <div style="display: flex; justify-content: space-around; text-align: center; flex-wrap: wrap;">
                            <div style="background: #d4edda; padding: 20px; border-radius: 10px; margin: 10px; min-width: 150px;">
                                <h3 style="color: #155724; margin: 0;">{self.test_result.success_count}</h3>
                                <p style="margin: 5px 0 0 0; color: #155724;">성공한 작업</p>
                            </div>
                            <div style="background: #f8d7da; padding: 20px; border-radius: 10px; margin: 10px; min-width: 150px;">
                                <h3 style="color: #721c24; margin: 0;">{self.test_result.failure_count}</h3>
                                <p style="margin: 5px 0 0 0; color: #721c24;">실패한 작업</p>
                            </div>
                            <div style="background: #d1ecf1; padding: 20px; border-radius: 10px; margin: 10px; min-width: 150px;">
                                <h3 style="color: #0c5460; margin: 0;">{success_rate:.1f}%</h3>
                                <p style="margin: 5px 0 0 0; color: #0c5460;">성공률</p>
                            </div>
                            <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin: 10px; min-width: 150px;">
                                <h3 style="color: #856404; margin: 0;">{self.test_result.get_duration():.1f}초</h3>
                                <p style="margin: 5px 0 0 0; color: #856404;">소요 시간</p>
                            </div>
                        </div>
                    </div>
                    
                    <div style="padding: 30px; background: #fff; border-radius: 10px; margin: 20px 0; border: 1px solid #ddd;">
                        <h2 style="color: #2c3e50; margin-top: 0;">👥 테스트 계정별 결과</h2>
                        {account_summary}
                    </div>
                    
                    <div style="padding: 30px; background: #fff; border-radius: 10px; margin: 20px 0; border: 1px solid #ddd;">
                        <h2 style="color: #2c3e50; margin-top: 0;">📋 상세 테스트 로그</h2>
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <thead>
                                <tr style="background: #f8f9fa;">
                                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">단계</th>
                                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">작업</th>
                                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">결과</th>
                                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">세부사항</th>
                                </tr>
                            </thead>
                            <tbody>
                                {results_html}
                            </tbody>
                        </table>
                    </div>
                    
                    <div style="padding: 20px; background: #e8f5e8; border-radius: 10px; margin: 20px 0;">
                        <h3 style="color: #27ae60; margin-top: 0;">🎯 테스트 시나리오</h3>
                        <ol style="line-height: 2;">
                            <li>현재 GA4 사용자 상태 확인</li>
                            <li>테스트 계정들에 Viewer 권한 부여</li>
                            <li>권한 부여 결과 검증</li>
                            <li>실패 케이스 테스트 (존재하지 않는 계정)</li>
                            <li>테스트 계정 권한 제거 (정리)</li>
                            <li>완전한 결과 보고서 발송</li>
                        </ol>
                    </div>
                    
                    <div style="padding: 20px; background: #fff3cd; border-radius: 10px; margin: 20px 0;">
                        <h3 style="color: #856404; margin-top: 0;">📝 테스트 정보</h3>
                        <p><strong>테스트 계정:</strong></p>
                        <ul>
                            <li>wonyoungseong@gmail.com</li>
                            <li>wonyoung.seong@amorepacific.com</li>
                        </ul>
                        <p><strong>부여 권한:</strong> Viewer (조회 권한)</p>
                        <p><strong>GA4 Property:</strong> {self.config['property_id']}</p>
                        <p><strong>테스트 시작:</strong> {self.test_result.start_time.strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
                        <p><strong>테스트 완료:</strong> {self.test_result.end_time.strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
                    </div>
                    
                    <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                        <p>이 보고서는 GA4 자동화 시스템에서 자동 생성되었습니다.</p>
                        <p>문의사항이 있으시면 시스템 관리자에게 연락해주세요.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            if self._send_email(self.report_email, subject, html_content):
                print(f"✅ 완전한 테스트 결과 보고서 발송 성공: {self.report_email}")
                self.test_result.add_step(
                    "STEP6", "결과 보고서 발송", True,
                    f"보고서 발송: {self.report_email}"
                )
                self._log_to_db("STEP6", "결과 보고서 발송", True, f"보고서 발송: {self.report_email}")
                return True
            else:
                print(f"❌ 보고서 발송 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 보고서 발송 실패: {e}")
            self.test_result.add_step("STEP6", "결과 보고서 발송", False, str(e))
            self._log_to_db("STEP6", "결과 보고서 발송", False, str(e))
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

    def run_complete_test(self):
        """완전한 테스트 실행"""
        print("🎬 GA4 권한 부여 완전 테스트 시작!")
        print("=" * 80)
        print(f"📧 테스트 계정: {', '.join(self.test_accounts)}")
        print(f"🎯 부여 권한: Viewer")
        print(f"📮 보고서 수신: {self.report_email}")
        print("=" * 80)
        
        all_results = {}
        
        try:
            # 1단계: 현재 사용자 확인
            current_users, test_account_status = self.step1_check_current_users()
            all_results['initial_status'] = test_account_status
            
            # 2단계: 테스트 계정들에 권한 부여
            add_results = self.step2_add_test_users(test_account_status)
            all_results['add_results'] = add_results
            
            # 3단계: 권한 부여 확인
            verification_results = self.step3_verify_permissions()
            all_results['verification_results'] = verification_results
            
            # 4단계: 실패 케이스 테스트
            failure_results = self.step4_test_failure_cases()
            all_results['failure_results'] = failure_results
            
            # 5단계: 테스트 계정 정리
            cleanup_results = self.step5_cleanup_test_users(verification_results)
            all_results['cleanup_results'] = cleanup_results
            
            # 6단계: 완전한 결과 보고서 발송
            self.step6_send_complete_report(all_results)
            
            # 최종 요약
            print("\n" + "="*80)
            print("🎉 완전한 테스트 완료!")
            print(f"⏱️  총 소요 시간: {self.test_result.get_duration():.1f}초")
            print(f"✅ 성공한 작업: {self.test_result.success_count}개")
            print(f"❌ 실패한 작업: {self.test_result.failure_count}개")
            print(f"📧 결과 보고서: {self.report_email}로 발송됨")
            print("="*80)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 테스트 실행 중 오류 발생: {e}")
            print(f"❌ 테스트 실행 중 오류가 발생했습니다: {e}")
            return False

def main():
    """메인 실행 함수"""
    print("🎯 GA4 실제 계정 권한 부여 완전 테스트")
    print("=" * 60)
    print("⚠️  주의: 이 테스트는 실제 GA4 계정에 권한을 부여/제거합니다.")
    print("⚠️  테스트 계정: wonyoungseong@gmail.com, wonyoung.seong@amorepacific.com")
    print("⚠️  보고서 수신: seongwonyoung0311@gmail.com")
    print("=" * 60)
    
    try:
        tester = GA4CompleteTest()
        
        print("\n🚀 완전한 테스트를 시작하시겠습니까?")
        print("1. 완전한 테스트 실행")
        print("0. 종료")
        
        choice = input("\n선택: ").strip()
        
        if choice == "1":
            tester.run_complete_test()
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