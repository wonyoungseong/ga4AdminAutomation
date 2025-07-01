#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail SMTP SSL 연결 테스트 (포트 465)
"""

import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_smtp_ssl():
    """포트 465 SSL 연결 테스트"""
    print("🧪 Gmail SMTP SSL (포트 465) 테스트 시작...")
    
    try:
        # config.json 로드
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        smtp_settings = config.get('smtp_settings', {})
        
        # 설정 정보 출력
        print(f"📧 서버: smtp.gmail.com:465 (SSL)")
        print(f"👤 발송자: {smtp_settings['sender_email']}")
        print(f"🔑 비밀번호 길이: {len(smtp_settings['sender_password'])}자")
        
        # 테스트 이메일 생성
        subject = "🎉 [테스트] Gmail SMTP SSL 연결 성공!"
        
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
                    <h1>🚀 Gmail SMTP SSL 연결 성공!</h1>
                </div>
                
                <div class="content">
                    <div class="success">
                        <h3>✅ 포트 465 SSL 연결 성공!</h3>
                        <p>Gmail SMTP 서버와 SSL 연결이 정상적으로 작동합니다.</p>
                    </div>
                    
                    <ul>
                        <li><strong>연결 방식:</strong> SMTP_SSL (포트 465)</li>
                        <li><strong>서버:</strong> smtp.gmail.com</li>
                        <li><strong>테스트 시간:</strong> {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 이메일 메시지 생성
        message = MIMEMultipart('alternative')
        message['From'] = f"{smtp_settings.get('sender_name', 'GA4 자동화')} <{smtp_settings['sender_email']}>"
        message['To'] = smtp_settings['sender_email']
        message['Subject'] = subject
        
        # HTML 파트 추가
        html_part = MIMEText(html_body, 'html', 'utf-8')
        message.attach(html_part)
        
        # SSL 컨텍스트 생성
        context = ssl.create_default_context()
        
        # SMTP_SSL 서버 연결 (포트 465)
        print("🔐 Gmail SMTP SSL 서버 연결 중...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            print("🔑 Gmail 인증 중...")
            server.login(smtp_settings['sender_email'], smtp_settings['sender_password'])
            
            print("📤 이메일 발송 중...")
            server.send_message(message)
        
        print(f"✅ SSL 테스트 이메일 발송 성공!")
        print(f"   📬 수신자: {smtp_settings['sender_email']}")
        print(f"   📝 제목: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ SSL 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    test_smtp_ssl() 