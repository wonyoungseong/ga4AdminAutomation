#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Email Test for wonyoungseong@gmail.com
==========================================

This module sends actual emails to wonyoungseong@gmail.com using SMTP
to test the complete notification system.

Author: GA4 Automation Team
Date: 2025-01-21
"""

import json
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional


class RealEmailTestWonyoung:
    """wonyoungseong@gmail.com 실제 이메일 테스트"""
    
    def __init__(self):
        """초기화"""
        self.target_user = "wonyoungseong@gmail.com"
        self.config = self._load_config()
        self.db_name = "real_email_test_wonyoung.db"
        self._setup_database()
        
    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ config.json 파일이 없습니다. SMTP 설정이 필요합니다.")
            return self._create_sample_config()
    
    def _create_sample_config(self) -> Dict:
        """샘플 설정 생성"""
        sample_config = {
            "smtp": {
                "server": "smtp.gmail.com",
                "port": 587,
                "username": "your_email@gmail.com",
                "password": "your_app_password",
                "use_tls": True
            },
            "email": {
                "from_name": "GA4 자동화 시스템",
                "from_email": "your_email@gmail.com"
            }
        }
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        
        print("📝 config.json 샘플 파일이 생성되었습니다.")
        print("   SMTP 설정을 업데이트한 후 다시 실행해주세요.")
        
        return sample_config
    
    def _setup_database(self):
        """데이터베이스 설정"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS real_email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                email_type TEXT NOT NULL,
                sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT FALSE,
                error_message TEXT,
                message_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _send_email(self, subject: str, html_content: str, text_content: str) -> Dict:
        """실제 이메일 발송"""
        try:
            # SMTP 설정 확인
            smtp_config = self.config.get('smtp', {})
            if not all(key in smtp_config for key in ['server', 'port', 'username', 'password']):
                return {
                    "success": False,
                    "error": "SMTP 설정이 완전하지 않습니다. config.json을 확인해주세요."
                }
            
            # 이메일 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config['email']['from_name']} <{self.config['email']['from_email']}>"
            msg['To'] = self.target_user
            
            # 텍스트 및 HTML 파트 추가
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            return {
                "success": True,
                "message_id": msg.get('Message-ID', 'unknown')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_welcome_email(self) -> Dict:
        """환영 메일 발송"""
        print("📧 환영 메일 발송 중...")
        
        subject = "🎉 GA4 접근 권한이 부여되었습니다!"
        
        # HTML 콘텐츠
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>GA4 환영 메일</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .info-box {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; 
                            border-left: 4px solid #667eea; }}
                .button {{ display: inline-block; background: #667eea; color: white; 
                          padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 환영합니다!</h1>
                    <p>GA4 접근 권한이 성공적으로 부여되었습니다</p>
                </div>
                <div class="content">
                    <p>안녕하세요 <strong>{self.target_user}</strong>님!</p>
                    
                    <p>Google Analytics 4(GA4) 접근 권한이 성공적으로 부여되었습니다. 
                    이제 웹사이트의 분석 데이터를 확인하실 수 있습니다.</p>
                    
                    <div class="info-box">
                        <h3>📊 권한 정보</h3>
                        <ul>
                            <li><strong>이메일:</strong> {self.target_user}</li>
                            <li><strong>역할:</strong> 뷰어 (Viewer)</li>
                            <li><strong>부여일:</strong> {datetime.now().strftime('%Y년 %m월 %d일')}</li>
                            <li><strong>만료일:</strong> {(datetime.now() + timedelta(days=30)).strftime('%Y년 %m월 %d일')}</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://analytics.google.com/analytics/web/" class="button">
                            🚀 GA4 대시보드 접속하기
                        </a>
                    </div>
                    
                    <div class="info-box">
                        <h3>📝 중요 안내사항</h3>
                        <ul>
                            <li>권한은 30일 후 자동으로 만료됩니다</li>
                            <li>만료 7일 전부터 알림 메일을 발송합니다</li>
                            <li>���장이 필요한 경우 관리자에게 문의해주세요</li>
                            <li>데이터 접근 시 개인정보보호 정책을 준수해주세요</li>
                        </ul>
                    </div>
                    
                    <p>궁금한 점이 있으시면 언제든지 문의해주세요.</p>
                    
                    <div class="footer">
                        <p>이 메일은 GA4 자동화 시스템에서 자동으로 발송되었습니다.</p>
                        <p>📧 문의: admin@company.com</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 텍스트 콘텐츠
        text_content = f"""
안녕하세요 {self.target_user}님!

GA4(Google Analytics 4) 접근 권한이 성공적으로 부여되었습니다.

권한 정보:
- 이메일: {self.target_user}
- 역할: 뷰어 (Viewer)
- 부여일: {datetime.now().strftime('%Y년 %m월 %d일')}
- 만료일: {(datetime.now() + timedelta(days=30)).strftime('%Y년 %m월 %d일')}

GA4 접속: https://analytics.google.com/analytics/web/

중요 안내사항:
- 권한은 30일 후 자동으로 만료됩니다
- 만료 7일 전부터 알림 메일을 발송합니다
- 연장이 필요한 경우 관리자에게 문의해주세요
- 데이터 접근 시 개인정보보호 정책을 준수해주세요

궁금한 점이 있으시면 언제든지 문의해주세요.

---
이 메일은 GA4 자동화 시스템에서 자동으로 발송되었습니다.
문의: admin@company.com
        """
        
        # 이메일 발송
        result = self._send_email(subject, html_content, text_content)
        
        # 로그 기록
        self._log_email(
            "welcome",
            subject,
            result["success"],
            result.get("error"),
            result.get("message_id")
        )
        
        if result["success"]:
            print(f"✅ 환영 메일 발송 성공: {self.target_user}")
            print(f"   📧 제목: {subject}")
        else:
            print(f"❌ 환영 메일 발송 실패: {result['error']}")
        
        return result
    
    def _log_email(self, email_type: str, subject: str, success: bool, 
                   error_message: Optional[str] = None, message_id: Optional[str] = None):
        """이메일 로그 기록"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO real_email_logs 
                (recipient, subject, email_type, success, error_message, message_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.target_user, subject, email_type, success, error_message, message_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 로그 기록 실패: {e}")


if __name__ == "__main__":
    # wonyoungseong@gmail.com 실제 이메일 테스트 실행
    email_test = RealEmailTestWonyoung()
    
    print("🔧 SMTP 설정을 확인하고 있습니다...")
    
    # SMTP 설정 확인
    smtp_config = email_test.config.get('smtp', {})
    if not all(key in smtp_config for key in ['server', 'port', 'username', 'password']):
        print("❌ SMTP 설정이 완전하지 않습니다.")
        print("   config.json 파일의 SMTP 설정을 업데이트해주세요.")
        print("   설정 예시:")
        print("   {")
        print("     \"smtp\": {")
        print("       \"server\": \"smtp.gmail.com\",")
        print("       \"port\": 587,")
        print("       \"username\": \"your_email@gmail.com\",")
        print("       \"password\": \"your_app_password\",")
        print("       \"use_tls\": true")
        print("     }")
        print("   }")
    else:
        print("✅ SMTP 설정이 확인되었습니다.")
        
        # 사용자 확인
        print(f"\n📧 {email_test.target_user}에게 실제 이메일을 발송합니다.")
        response = input("계속하시겠습니까? (y/N): ")
        
        if response.lower() in ['y', 'yes']:
            # 환영 메일 발송 테스트
            welcome_result = email_test.send_welcome_email()
            
            if welcome_result["success"]:
                print(f"\n✅ {email_test.target_user} 환영 메일 발송 완료!")
            else:
                print(f"\n❌ 환영 메일 발송 실패: {welcome_result['error']}")
        else:
            print("❌ 이메일 발송이 취소되었습니다.")