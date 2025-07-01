#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스마트 이메일 검증 및 자동 발송 시스템
====================================

GA4 API의 404 오류를 활용하여 이메일 유효성을 검증하고,
검증 결과에 따라 적절한 이메일을 자동으로 발송하는 시스템입니다.
"""

import json
import smtplib
import base64
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, CreateAccessBindingRequest
from google.oauth2 import service_account
from .gmail_service import GmailOAuthSender
from .logger import get_email_logger

class SmartEmailValidationSystem:
    """스마트 이메일 검증 및 자동 발송 시스템 (개선된 로깅)"""
    
    def __init__(self):
        self.config = self._load_config()
        self.logger = get_email_logger()
        self._init_ga4_client()
        self._init_gmail_client()
        self.validation_results = {}
    
    def _load_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    

    
    def _init_ga4_client(self):
        service_account_file = 'config/ga4-automatio-797ec352f393.json'
        
        scopes = [
            'https://www.googleapis.com/auth/analytics.edit',
            'https://www.googleapis.com/auth/analytics.manage.users'
        ]
        
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        
        self.ga4_client = AnalyticsAdminServiceClient(credentials=credentials)
        self.logger.info("✅ GA4 클라이언트 초기화 완료")
    
    def _init_gmail_client(self):
        """Gmail OAuth 클라이언트 초기화"""
        try:
            self.gmail_sender = GmailOAuthSender()
            # 인증 시도
            if self.gmail_sender.authenticate():
                self.gmail_available = True
                self.logger.info("✅ Gmail OAuth 클라이언트 초기화 완료")
            else:
                self.gmail_available = False
                self.logger.warning("⚠️ Gmail OAuth 인증 실패")
        except Exception as e:
            self.gmail_available = False
            self.logger.warning(f"⚠️ Gmail OAuth 초기화 실패: {e}")
    
    def validate_email_with_ga4(self, email: str) -> Dict:
        """GA4 API를 사용한 이메일 검증"""
        
        self.logger.info(f"🔍 이메일 검증 시작: {email}")
        
        parent = f"properties/{self.config['property_id']}"
        
        try:
            # 테스트용 권한 부여 시도 (실제로는 부여되지 않도록 즉시 제거)
            access_binding = AccessBinding(
                user=email,
                roles=['predefinedRoles/analyst']
            )
            
            request = CreateAccessBindingRequest(
                parent=parent,
                access_binding=access_binding
            )
            
            response = self.ga4_client.create_access_binding(request=request)
            
            # 성공한 경우 즉시 제거
            self.ga4_client.delete_access_binding(name=response.name)
            
            result = {
                'email': email,
                'valid': True,
                'status': 'VALID_GOOGLE_ACCOUNT',
                'message': '유효한 Google 계정입니다',
                'error_code': None,
                'can_register': True,
                'recommendation': 'GA4 등록 가능'
            }
            
            self.logger.info(f"✅ {email} - 유효한 Google 계정")
            
        except Exception as e:
            error_msg = str(e)
            
            if "404" in error_msg and "could not be found" in error_msg:
                result = {
                    'email': email,
                    'valid': False,
                    'status': 'ACCOUNT_NOT_FOUND',
                    'message': 'Google 시스템에서 계정을 찾을 수 없음',
                    'error_code': '404',
                    'can_register': False,
                    'recommendation': '계정 확인 필요'
                }
                self.logger.info(f"❌ {email} - 계정을 찾을 수 없음 (404)")
                
            elif "400" in error_msg and "User not allowed" in error_msg:
                result = {
                    'email': email,
                    'valid': True,
                    'status': 'ACCOUNT_RESTRICTED',
                    'message': '계정이 존재하지만 정책상 제한됨',
                    'error_code': '400',
                    'can_register': False,
                    'recommendation': '관리자 문의 필요'
                }
                self.logger.info(f"⚠️ {email} - 정책상 제한된 계정 (400)")
                
            elif "403" in error_msg:
                result = {
                    'email': email,
                    'valid': True,
                    'status': 'PERMISSION_DENIED',
                    'message': '계정이 존재하지만 권한 부족',
                    'error_code': '403',
                    'can_register': False,
                    'recommendation': '권한 설정 확인 필요'
                }
                self.logger.info(f"⚠️ {email} - 권한 부족 (403)")
                
            else:
                result = {
                    'email': email,
                    'valid': False,
                    'status': 'UNKNOWN_ERROR',
                    'message': f'알 수 없는 오류: {error_msg[:100]}',
                    'error_code': 'UNKNOWN',
                    'can_register': False,
                    'recommendation': '수동 확인 필요'
                }
                self.logger.error(f"❓ {email} - 알 수 없는 오류: {error_msg}")
        
        self.validation_results[email] = result
        return result
    
    def batch_validate_emails(self, email_list: List[str]) -> Dict[str, Dict]:
        """이메일 목록 일괄 검증"""
        
        self.logger.info(f"📋 일괄 검증 시작: {len(email_list)}개 이메일")
        
        results = {}
        
        for i, email in enumerate(email_list, 1):
            self.logger.info(f"[{i}/{len(email_list)}] 검증 중: {email}")
            
            result = self.validate_email_with_ga4(email)
            results[email] = result
            
            # 진행 상황 표시
            if i % 5 == 0 or i == len(email_list):
                self.logger.info(f"📊 진행률: {i}/{len(email_list)} ({i/len(email_list)*100:.1f}%)")
        
        self.logger.info(f"✅ 일괄 검증 완료: {len(email_list)}개 이메일")
        
        return results
    
    def send_validation_results_email(self, results: Dict[str, Dict], 
                                    recipient_email: str) -> bool:
        """검증 결과 이메일 발송"""
        
        self.logger.info(f"📧 검증 결과 이메일 발송: {recipient_email}")
        
        # 통계 계산
        total_count = len(results)
        valid_count = sum(1 for r in results.values() if r['valid'])
        invalid_count = total_count - valid_count
        registerable_count = sum(1 for r in results.values() if r['can_register'])
        
        # 상태별 분류
        status_groups = {}
        for email, result in results.items():
            status = result['status']
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(email)
        
        # 이메일 내용 생성
        subject = f"📊 이메일 검증 결과 - {total_count}개 계정 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        
        # 상태별 상세 내용
        status_details = ""
        status_colors = {
            'VALID_GOOGLE_ACCOUNT': '#d4edda',
            'ACCOUNT_NOT_FOUND': '#f8d7da', 
            'ACCOUNT_RESTRICTED': '#fff3cd',
            'PERMISSION_DENIED': '#ffeaa7',
            'UNKNOWN_ERROR': '#e2e3e5'
        }
        
        status_names = {
            'VALID_GOOGLE_ACCOUNT': '✅ 유효한 Google 계정',
            'ACCOUNT_NOT_FOUND': '❌ 계정을 찾을 수 없음',
            'ACCOUNT_RESTRICTED': '⚠️ 정책상 제한된 계정',
            'PERMISSION_DENIED': '🔒 권한 부족',
            'UNKNOWN_ERROR': '❓ 알 수 없는 오류'
        }
        
        for status, emails in status_groups.items():
            color = status_colors.get(status, '#f8f9fa')
            name = status_names.get(status, status)
            
            status_details += f"""
            <div style="margin: 15px 0; padding: 15px; background: {color}; 
                       border-radius: 8px; border-left: 4px solid #007bff;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{name} ({len(emails)}개)</h4>
                <div style="font-size: 14px; line-height: 1.4;">
                    {', '.join(emails)}
                </div>
            </div>
            """
        
        # 추천 사항
        recommendations = ""
        if status_groups.get('ACCOUNT_NOT_FOUND'):
            recommendations += """
            <div style="margin: 10px 0; padding: 15px; background: #f8d7da; border-radius: 8px;">
                <h4 style="margin: 0 0 10px 0; color: #721c24;">❌ 계정을 찾을 수 없는 경우</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>이메일 주소 오타 확인</li>
                    <li>Google 계정 존재 여부 확인</li>
                    <li>계정이 비활성화되었는지 확인</li>
                    <li>조직 정책으로 인한 제한 확인</li>
                </ul>
            </div>
            """
        
        if status_groups.get('ACCOUNT_RESTRICTED'):
            recommendations += """
            <div style="margin: 10px 0; padding: 15px; background: #fff3cd; border-radius: 8px;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">⚠️ 정책상 제한된 계정</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>조직 관리자에게 문의</li>
                    <li>외부 공유 정책 확인</li>
                    <li>개인 Gmail 계정 사용 고려</li>
                </ul>
            </div>
            """
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">📊 이메일 검증 결과</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">
                        {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')} 검증 완료
                    </p>
                </div>
                
                <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                    <h2 style="color: #2c3e50; margin-top: 0;">📈 검증 결과 요약</h2>
                    <div style="display: flex; justify-content: space-around; text-align: center; flex-wrap: wrap;">
                        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 5px; min-width: 120px;">
                            <h3 style="color: #27ae60; margin: 0; font-size: 24px;">{total_count}</h3>
                            <p style="margin: 5px 0 0 0; color: #27ae60;">총 검증</p>
                        </div>
                        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 5px; min-width: 120px;">
                            <h3 style="color: #27ae60; margin: 0; font-size: 24px;">{valid_count}</h3>
                            <p style="margin: 5px 0 0 0; color: #27ae60;">유효한 계정</p>
                        </div>
                        <div style="background: #ffeaa7; padding: 15px; border-radius: 8px; margin: 5px; min-width: 120px;">
                            <h3 style="color: #d63031; margin: 0; font-size: 24px;">{invalid_count}</h3>
                            <p style="margin: 5px 0 0 0; color: #d63031;">무효한 계정</p>
                        </div>
                        <div style="background: #a8e6cf; padding: 15px; border-radius: 8px; margin: 5px; min-width: 120px;">
                            <h3 style="color: #00b894; margin: 0; font-size: 24px;">{registerable_count}</h3>
                            <p style="margin: 5px 0 0 0; color: #00b894;">등록 가능</p>
                        </div>
                    </div>
                </div>
                
                <div style="padding: 20px; background: #fff; border-radius: 10px; margin: 20px 0; border: 1px solid #ddd;">
                    <h2 style="color: #2c3e50; margin-top: 0;">📋 상태별 상세 결과</h2>
                    {status_details}
                </div>
                
                {f'<div style="padding: 20px; background: #fff; border-radius: 10px; margin: 20px 0;">{recommendations}</div>' if recommendations else ''}
                
                <div style="padding: 20px; background: #e8f4f8; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #1e6091; margin-top: 0;">🔧 검증 정보</h3>
                    <p><strong>검증 방법:</strong> GA4 API 404 오류 활용</p>
                    <p><strong>검증 시간:</strong> {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
                    <p><strong>GA4 Property ID:</strong> {self.config['property_id']}</p>
                </div>
                
                <div style="text-align: center; padding: 20px; color: #7f8c8d;">
                    <p>이 보고서는 스마트 이메일 검증 시스템에서 자동 생성되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(recipient_email, subject, html_content)
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """이메일 발송 (Gmail API 우선, SMTP 대체)"""
        
        # Gmail API 시도
        if self.gmail_available:
            return self._send_email_via_gmail_api(to_email, subject, html_content)
        
        # SMTP 대체
        return self._send_email_via_smtp(to_email, subject, html_content)
    
    def _send_email_via_gmail_api(self, to_email: str, subject: str, html_content: str) -> bool:
        """Gmail OAuth를 사용한 이메일 발송"""
        try:
            # 텍스트 버전도 생성 (HTML에서 태그 제거)
            import re
            text_content = re.sub(r'<[^>]+>', '', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Gmail OAuth 발송
            success = self.gmail_sender.send_email(
                recipient_email=to_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
            
            if success:
                self.logger.info(f"✅ Gmail OAuth로 이메일 발송 성공: {to_email}")
                return True
            else:
                self.logger.error(f"❌ Gmail OAuth 이메일 발송 실패: {to_email}")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Gmail OAuth 이메일 발송 실패: {to_email} - {e}")
            return False
    
    def _send_email_via_smtp(self, to_email: str, subject: str, html_content: str) -> bool:
        """SMTP를 사용한 이메일 발송"""
        try:
            smtp_config = self.config.get('smtp_settings', {})
            
            if not all(key in smtp_config for key in ['smtp_server', 'smtp_port', 'sender_email', 'sender_password']):
                self.logger.error("SMTP 설정이 완전하지 않습니다")
                return False
            
            # 이메일 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"GA4 자동화 시스템 <{smtp_config['sender_email']}>"
            msg['To'] = to_email
            
            # HTML 파트 추가
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                
                server.login(smtp_config['sender_email'], smtp_config['sender_password'])
                server.send_message(msg)
            
            self.logger.info(f"✅ SMTP로 이메일 발송 성공: {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ SMTP 이메일 발송 실패: {to_email} - {e}")
            return False

def main():
    """메인 함수"""
    
    print("🚀 스마트 이메일 검증 및 자동 발송 시스템")
    print("=" * 60)
    print("GA4 API의 404 오류를 활용한 이메일 유효성 검증")
    print()
    
    system = SmartEmailValidationSystem()
    
    while True:
        print("\n📋 메뉴:")
        print("1. 단일 이메일 검증")
        print("2. 이메일 목록 일괄 검증")
        print("3. 검증 결과 이메일 발송")
        print("4. 종료")
        
        choice = input("\n선택: ").strip()
        
        if choice == '1':
            email = input("검증할 이메일 주소: ").strip()
            if email:
                result = system.validate_email_with_ga4(email)
                print(f"\n📊 검증 결과:")
                print(f"  이메일: {result['email']}")
                print(f"  상태: {result['status']}")
                print(f"  메시지: {result['message']}")
                print(f"  등록 가능: {'예' if result['can_register'] else '아니오'}")
                print(f"  권장사항: {result['recommendation']}")
        
        elif choice == '2':
            emails_input = input("이메일 주소들 (쉼표로 구분): ").strip()
            if emails_input:
                email_list = [email.strip() for email in emails_input.split(',')]
                results = system.batch_validate_emails(email_list)
                
                print(f"\n📊 일괄 검증 완료:")
                for email, result in results.items():
                    status_icon = "✅" if result['can_register'] else "❌"
                    print(f"  {status_icon} {email}: {result['status']}")
        
        elif choice == '3':
            if hasattr(system, 'validation_results') and system.validation_results:
                recipient = input("결과를 받을 이메일 주소: ").strip()
                if recipient:
                    success = system.send_validation_results_email(
                        system.validation_results, recipient
                    )
                    if success:
                        print("✅ 검증 결과 이메일 발송 완료")
                    else:
                        print("❌ 이메일 발송 실패")
            else:
                print("❌ 먼저 이메일 검증을 수행해주세요")
        
        elif choice == '4':
            print("👋 시스템을 종료합니다.")
            break
        
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main() 