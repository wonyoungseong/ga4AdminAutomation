#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMTP 연결 테스트
===============

Gmail SMTP를 사용한 이메일 발송 테스트
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_smtp_connection():
    """SMTP 연결 및 이메일 발송 테스트"""
    print("🧪 SMTP 연결 테스트 시작...")
    
    try:
        # config.json 로드
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        smtp_settings = config.get('smtp_settings', {})
        
        print(f"📧 SMTP 서버: {smtp_settings['smtp_server']}:{smtp_settings['smtp_port']}")
        print(f"👤 발송자: {smtp_settings['sender_email']}")
        
        # 테스트 이메일 생성
        subject = "🎉 [테스트] GA4 SMTP 연동 성공!"
        
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
                .info {{ background-color: #e8f0fe; padding: 15px; border-left: 4px solid #4285f4; margin: 15px 0; }}
                .highlight {{ color: #1a73e8; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 GA4 자동화 시스템</h1>
                    <p>SMTP 연동 테스트 성공!</p>
                </div>
                
                <div class="content">
                    <div class="success">
                        <h3>✅ 연결 성공!</h3>
                        <p>Gmail SMTP를 통한 이메일 발송이 정상적으로 작동합니다.</p>
                    </div>
                    
                    <div class="info">
                        <h3>📋 테스트 정보</h3>
                        <ul>
                            <li><strong>SMTP 서버:</strong> {smtp_settings['smtp_server']}</li>
                            <li><strong>포트:</strong> {smtp_settings['smtp_port']}</li>
                            <li><strong>발송자:</strong> {smtp_settings['sender_email']}</li>
                            <li><strong>테스트 시간:</strong> {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}</li>
                            <li><strong>TLS 사용:</strong> {'예' if smtp_settings.get('use_tls') else '아니오'}</li>
                        </ul>
                    </div>
                    
                    <h3>🎯 다음 단계</h3>
                    <p>이제 GA4 사용자 관리 시스템에서 다음과 같은 이메일을 자동으로 발송할 수 있습니다:</p>
                    <ul>
                        <li>🎉 <span class="highlight">환영 이메일</span> - 새 사용자 등록 시</li>
                        <li>⚠️ <span class="highlight">만료 경고</span> - 권한 만료 30일, 7일, 1일 전</li>
                        <li>🚫 <span class="highlight">삭제 알림</span> - 권한 만료 후 제거</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        GA4 자동화 시스템 - SMTP 연동 테스트 성공!
        
        ✅ 연결 성공!
        Gmail SMTP를 통한 이메일 발송이 정상적으로 작동합니다.
        
        📋 테스트 정보:
        - SMTP 서버: {smtp_settings['smtp_server']}
        - 포트: {smtp_settings['smtp_port']}
        - 발송자: {smtp_settings['sender_email']}
        - 테스트 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
        - TLS 사용: {'예' if smtp_settings.get('use_tls') else '아니오'}
        
        🎯 다음 단계:
        이제 GA4 사용자 관리 시스템에서 자동 이메일 발송이 가능합니다.
        """
        
        # 이메일 메시지 생성
        message = MIMEMultipart('alternative')
        message['From'] = f"{smtp_settings.get('sender_name', 'GA4 자동화')} <{smtp_settings['sender_email']}>"
        message['To'] = smtp_settings['sender_email']  # 자기 자신에게 테스트
        message['Subject'] = subject
        
        # 텍스트 및 HTML 파트 추가
        text_part = MIMEText(plain_body, 'plain', 'utf-8')
        html_part = MIMEText(html_body, 'html', 'utf-8')
        
        message.attach(text_part)
        message.attach(html_part)
        
        # SMTP 서버 연결 및 발송
        print("🔐 SMTP 서버 연결 중...")
        with smtplib.SMTP(smtp_settings['smtp_server'], smtp_settings['smtp_port']) as server:
            if smtp_settings.get('use_tls', True):
                print("🔒 TLS 보안 연결 활성화...")
                server.starttls()
            
            print("🔑 Gmail 인증 중...")
            server.login(smtp_settings['sender_email'], smtp_settings['sender_password'])
            
            print("📤 이메일 발송 중...")
            server.send_message(message)
        
        print(f"✅ 테스트 이메일 발송 성공!")
        print(f"   📬 수신자: {smtp_settings['sender_email']}")
        print(f"   📝 제목: {subject}")
        print(f"   ⏰ 발송 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🎉 SMTP 설정이 완료되었습니다!")
        print("   이제 GA4 자동화 시스템에서 이메일 알림을 사용할 수 있습니다.")
        
        return True
        
    except Exception as e:
        print(f"❌ SMTP 테스트 실패: {e}")
        print("\n🔧 문제 해결 방법:")
        print("   1. Gmail 앱 비밀번호가 정확한지 확인")
        print("   2. config.json의 SMTP 설정 확인")
        print("   3. 네트워크 연결 상태 확인")
        return False

if __name__ == "__main__":
    test_smtp_connection() 