#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail OAuth 2.0 테스트
==================

Gmail API를 사용한 OAuth 2.0 인증 및 이메일 발송 테스트

Requirements:
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Usage:
    python gmail_oauth_test.py
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

# Gmail API 스코프
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    """Gmail OAuth 2.0 인증"""
    print("🔐 Gmail OAuth 2.0 인증 시작...")
    
    creds = None
    
    # token.pickle 파일이 있다면 로드
    if os.path.exists('token.pickle'):
        print("📁 기존 토큰 파일 발견, 로드 중...")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # 유효한 자격 증명이 없다면 인증 플로우 실행
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 토큰 갱신 중...")
            creds.refresh(Request())
        else:
            print("🆕 새로운 OAuth 인증 플로우 시작...")
            
            # config.json에서 OAuth 설정 로드
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            gmail_oauth = config.get('gmail_oauth', {})
            
            # OAuth 클라이언트 설정
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
            
            print("🌐 브라우저에서 Google 인증을 진행해주세요...")
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
            
            print("✅ OAuth 인증 완료!")
        
        # 자격 증명 저장
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            print("💾 토큰 파일 저장 완료")
    else:
        print("✅ 기존 토큰이 유효합니다")
    
    return creds

def create_test_email():
    """테스트 이메일 생성"""
    # config.json 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    gmail_oauth = config.get('gmail_oauth', {})
    sender_email = gmail_oauth.get('sender_email')
    sender_name = gmail_oauth.get('sender_name', 'GA4 자동화 시스템')
    
    # HTML 이메일 생성
    message = MIMEMultipart('alternative')
    message['to'] = sender_email
    message['from'] = f"{sender_name} <{sender_email}>"
    message['subject'] = '🎉 Gmail OAuth 2.0 테스트 성공!'
    
    # 텍스트 버전
    text_content = """
Gmail OAuth 2.0 인증이 성공적으로 완료되었습니다!

✅ OAuth 2.0 인증 완료
✅ Gmail API 연결 성공
✅ 이메일 발송 테스트 완료

이제 GA4 자동화 시스템에서 안전하게 이메일을 발송할 수 있습니다.

발송 시간: {}
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # HTML 버전
    html_content = """
    <html>
      <body>
        <h2>🎉 Gmail OAuth 2.0 테스트 성공!</h2>
        <p>Gmail OAuth 2.0 인증이 성공적으로 완료되었습니다!</p>
        
        <h3>✅ 완료된 작업:</h3>
        <ul>
          <li>OAuth 2.0 인증 완료</li>
          <li>Gmail API 연결 성공</li>
          <li>이메일 발송 테스트 완료</li>
        </ul>
        
        <p><strong>이제 GA4 자동화 시스템에서 안전하게 이메일을 발송할 수 있습니다.</strong></p>
        
        <hr>
        <p><small>발송 시간: {}</small></p>
      </body>
    </html>
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 텍스트와 HTML 파트 추가
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    html_part = MIMEText(html_content, 'html', 'utf-8')
    
    message.attach(text_part)
    message.attach(html_part)
    
    return message

def send_test_email():
    """테스트 이메일 발송"""
    try:
        # Gmail 인증
        creds = authenticate_gmail()
        
        print("📧 Gmail API 서비스 생성 중...")
        service = build('gmail', 'v1', credentials=creds)
        
        print("✉️ 테스트 이메일 생성 중...")
        message = create_test_email()
        
        # 이메일 인코딩
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        print("📤 테스트 이메일 발송 중...")
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"✅ 테스트 이메일 발송 성공!")
        print(f"📬 메시지 ID: {result['id']}")
        print(f"📧 수신자: {message['to']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail OAuth 2.0 테스트 실패: {str(e)}")
        print(f"🔍 오류 세부사항: {type(e).__name__}")
        return False

def check_requirements():
    """필수 패키지 확인"""
    required_packages = [
        'google-auth',
        'google-auth-oauthlib', 
        'google-auth-httplib2',
        'google-api-python-client'
    ]
    
    print("📦 필수 패키지 확인 중...")
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'google-auth':
                import google.auth
            elif package == 'google-auth-oauthlib':
                import google_auth_oauthlib
            elif package == 'google-auth-httplib2':
                import google.auth.transport.requests
            elif package == 'google-api-python-client':
                import googleapiclient
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 다음 패키지가 누락되었습니다:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n다음 명령어로 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 모든 필수 패키지가 설치되어 있습니다.")
    return True

if __name__ == "__main__":
    print("🧪 Gmail OAuth 2.0 테스트 시작...")
    print("=" * 50)
    
    # 필수 패키지 확인
    if not check_requirements():
        exit(1)
    
    # config.json 파일 확인
    if not os.path.exists('config.json'):
        print("❌ config.json 파일이 없습니다.")
        exit(1)
    
    print()
    success = send_test_email()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Gmail OAuth 2.0 설정이 완료되었습니다!")
        print("✅ 이제 GA4 자동화 시스템에서 이메일을 발송할 수 있습니다.")
        print("📁 token.pickle 파일이 생성되어 향후 인증이 자동화됩니다.")
    else:
        print("❌ Gmail OAuth 2.0 설정에 문제가 있습니다.")
        print("�� 설정을 다시 확인해주세요.") 