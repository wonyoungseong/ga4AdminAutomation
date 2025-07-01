#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail OAuth 2.0 설정 가이드
=========================
"""

def create_oauth_setup_guide():
    """OAuth 2.0 설정 단계별 가이드"""
    print("📋 Gmail OAuth 2.0 설정 가이드 (2025년 최신)")
    print("="*60)
    
    print("\n🔧 1단계: Google Cloud Console 설정")
    print("   https://console.cloud.google.com/")
    print("   → 새 프로젝트 생성: 'GA4-Gmail-OAuth'")
    
    print("\n📚 2단계: Gmail API 활성화")
    print("   → API 및 서비스 → 라이브러리")
    print("   → 'Gmail API' 검색 → 사용 설정")
    
    print("\n🔐 3단계: OAuth 동의 화면 설정")
    print("   → OAuth 동의 화면 → 외부 → 만들기")
    print("   → 앱 이름: 'GA4 이메일 시스템'")
    print("   → 범위 추가: https://www.googleapis.com/auth/gmail.send")
    
    print("\n🗝️ 4단계: 사용자 인증 정보 생성")
    print("   → 사용자 인증 정보 → OAuth 클라이언트 ID")
    print("   → 애플리케이션 유형: 데스크톱 애플리케이션")
    print("   → JSON 파일 다운로드 → 'gmail_credentials.json'으로 저장")
    
    print("\n📦 5단계: 패키지 설치")
    print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

def create_oauth_email_sender():
    """OAuth 2.0 이메일 발송 클래스"""
    code = '''
import base64
import json
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("❌ 필요한 패키지를 설치해주세요:")
    print("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)

class GmailOAuth2Sender:
    """Gmail OAuth 2.0 이메일 발송 클래스"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self, credentials_file='gmail_credentials.json', token_file='gmail_token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """OAuth 2.0 인증"""
        creds = None
        
        # 기존 토큰 파일 확인
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # 토큰이 없거나 만료된 경우
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 토큰 갱신 중...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ {self.credentials_file} 파일이 없습니다.")
                    print("Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 JSON 파일을 다운로드하세요.")
                    return False
                
                print("🔐 OAuth 2.0 인증 시작...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 토큰 저장
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Gmail 서비스 빌드
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail OAuth 2.0 인증 성공")
        return True
    
    def send_email(self, to_email, subject, html_body, plain_body=None):
        """OAuth 2.0로 이메일 발송"""
        try:
            # 설정에서 발송자 정보 읽기
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            sender_email = config.get('smtp_settings', {}).get('sender_email', 'wonyoungseong@gmail.com')
            
            # 이메일 메시지 생성
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['from'] = sender_email
            message['subject'] = subject
            
            # 텍스트 및 HTML 파트 추가
            if plain_body:
                text_part = MIMEText(plain_body, 'plain', 'utf-8')
                message.attach(text_part)
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # base64 인코딩
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Gmail API로 전송
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            message_id = send_result.get('id')
            print(f"✅ OAuth 2.0로 이메일 발송 성공: {message_id}")
            return message_id
            
        except Exception as e:
            print(f"❌ OAuth 2.0 이메일 발송 실패: {e}")
            return None

def test_oauth_email():
    """OAuth 2.0 이메일 테스트"""
    print("🧪 Gmail OAuth 2.0 이메일 테스트 시작...")
    
    sender = GmailOAuth2Sender()
    if not sender.service:
        return False
    
    # 테스트 이메일 내용
    subject = "🎉 [테스트] Gmail OAuth 2.0 연동 성공!"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #4285f4;">🚀 Gmail OAuth 2.0 연동 성공!</h2>
        <p>SMTP 앱 비밀번호 대신 <strong>OAuth 2.0</strong>으로 이메일 발송이 성공했습니다.</p>
        
        <h3>✅ 장점:</h3>
        <ul>
            <li>보안성 향상 (Google 권장 방식)</li>
            <li>앱 비밀번호 불필요</li>
            <li>토큰 자동 갱신</li>
            <li>더 안정적인 연결</li>
        </ul>
        
        <p><strong>테스트 시간:</strong> {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</p>
        
        <hr>
        <p style="font-size: 12px; color: #666;">GA4 자동화 시스템에서 발송</p>
    </body>
    </html>
    """
    
    plain_body = f"""
    Gmail OAuth 2.0 연동 성공!
    
    SMTP 앱 비밀번호 대신 OAuth 2.0으로 이메일 발송이 성공했습니다.
    
    장점:
    - 보안성 향상 (Google 권장 방식)
    - 앱 비밀번호 불필요
    - 토큰 자동 갱신
    - 더 안정적인 연결
    
    테스트 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
    """
    
    # 이메일 발송
    result = sender.send_email(
        to_email="wonyoungseong@gmail.com",
        subject=subject,
        html_body=html_body,
        plain_body=plain_body
    )
    
    return result is not None

if __name__ == "__main__":
    test_oauth_email()
'''
    
    print("\n📄 gmail_oauth2_sender.py 파일 내용:")
    print(code)

if __name__ == "__main__":
    create_oauth_setup_guide()
    print("\n" + "="*60)
    create_oauth_email_sender() 