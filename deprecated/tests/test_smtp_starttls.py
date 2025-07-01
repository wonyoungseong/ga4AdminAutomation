#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail SMTP STARTTLS 연결 테스트 (포트 587)
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_smtp_starttls():
    """포트 587 STARTTLS 연결 테스트"""
    print("🧪 Gmail SMTP STARTTLS (포트 587) 테스트 시작...")
    
    try:
        # config.json 로드
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        smtp_settings = config.get('smtp_settings', {})
        
        # 설정 정보 출력
        print(f"📧 서버: smtp.gmail.com:587 (STARTTLS)")
        print(f"👤 발송자: {smtp_settings['sender_email']}")
        print(f"🔑 비밀번호: {smtp_settings['sender_password'][:4]}****{smtp_settings['sender_password'][-4:]}")
        
        # 테스트 이메일 생성
        subject = "🎉 [테스트] Gmail SMTP STARTTLS 연결 성공!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Malgun Gothic', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4285f4, #34a853); color: white; padding: 25px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 25px; background-color: #f8f9fa; border-radius: 0 0 10px 10px; }}
                .success {{ background-color: #d4edda; padding: 20px; border: 1px solid #c3e6cb; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Gmail SMTP STARTTLS 연결 성공!</h1>
                </div>
                
                <div class="content">
                    <div class="success">
                        <h3>✅ 포트 587 STARTTLS 연결 성공!</h3>
                        <p>Gmail SMTP 서버와 STARTTLS 연결이 정상적으로 작동합니다.</p>
                    </div>
                    
                    <ul>
                        <li><strong>연결 방식:</strong> SMTP + STARTTLS (포트 587)</li>
                        <li><strong>서버:</strong> smtp.gmail.com</li>
                        <li><strong>테스트 시간:</strong> {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</li>
                        <li><strong>앱 비밀번호:</strong> 정상 작동</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        Gmail SMTP STARTTLS 연결 성공!
        
        포트 587 STARTTLS 연결이 정상적으로 작동합니다.
        
        연결 정보:
        - 연결 방식: SMTP + STARTTLS (포트 587)
        - 서버: smtp.gmail.com
        - 테스트 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
        - 앱 비밀번호: 정상 작동
        """
        
        # 이메일 메시지 생성
        message = MIMEMultipart('alternative')
        message['From'] = f"{smtp_settings.get('sender_name', 'GA4 자동화')} <{smtp_settings['sender_email']}>"
        message['To'] = smtp_settings['sender_email']
        message['Subject'] = subject
        
        # 텍스트 및 HTML 파트 추가
        text_part = MIMEText(plain_body, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        
        message.attach(text_part)
        message.attach(html_part)
        
        # SMTP 서버 연결 (포트 587 + STARTTLS)
        print("🔐 Gmail SMTP 서버 연결 중...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            print("🔒 STARTTLS 보안 연결 활성화...")
            server.starttls()
            
            print("🔑 Gmail 인증 중...")
            server.login(smtp_settings['sender_email'], smtp_settings['sender_password'])
            
            print("📤 이메일 발송 중...")
            server.send_message(message)
        
        print(f"✅ STARTTLS 테스트 이메일 발송 성공!")
        print(f"   📬 수신자: {smtp_settings['sender_email']}")
        print(f"   📝 제목: {subject}")
        print(f"   ⏰ 발송 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🎉 Gmail SMTP 설정이 완료되었습니다!")
        return True
        
    except Exception as e:
        print(f"❌ STARTTLS 테스트 실패: {e}")
        
        # 상세 오류 진단
        if "Username and Password not accepted" in str(e):
            print("\n🔧 인증 문제 해결 방법:")
            print("   1. 새로운 앱 비밀번호 생성")
            print("   2. 2단계 인증 활성화 확인")
            print("   3. Gmail 계정 잠금 해제: https://accounts.google.com/DisplayUnlockCaptcha")
        elif "Connection unexpectedly closed" in str(e):
            print("\n🔧 연결 문제 해결 방법:")
            print("   1. 네트워크 방화벽 확인")
            print("   2. VPN 사용 시 비활성화 시도")
            print("   3. 다른 네트워크에서 테스트")
        elif "timed out" in str(e):
            print("\n🔧 타임아웃 문제 해결 방법:")
            print("   1. 인터넷 연결 상태 확인")
            print("   2. 잠시 후 다시 시도")
        
        return False

if __name__ == "__main__":
    test_smtp_starttls() 