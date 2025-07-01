#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새로운 앱 비밀번호 즉시 테스트
"""

import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def quick_test():
    """새로운 앱 비밀번호 즉시 테스트"""
    print("🧪 새로운 앱 비밀번호 테스트 시작...")
    
    # 새로운 설정
    email = "wonyoungseong@gmail.com"
    password = "opqerlhnfmpgcgen"  # 공백 제거된 새 비밀번호
    
    print(f"📧 이메일: {email}")
    print(f"🔑 비밀번호: {password[:4]}****{password[-4:]}")
    print(f"🌐 서버: smtp.gmail.com:587")
    
    try:
        # 간단한 테스트 이메일
        msg = MIMEText(f"""
🎉 새로운 앱 비밀번호 테스트 성공!

테스트 정보:
- 앱 비밀번호: {password[:4]}****{password[-4:]}
- 테스트 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
- 연결 방식: STARTTLS (포트 587)

GA4 자동화 시스템이 정상적으로 작동합니다! ✅
        """)
        
        msg['Subject'] = "🎉 [성공] GA4 Gmail SMTP 연결 완료!"
        msg['From'] = email
        msg['To'] = email
        
        print("\n🔐 SMTP 서버 연결 중...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            print("🔒 STARTTLS 활성화...")
            server.starttls()
            
            print("🔑 새로운 앱 비밀번호로 로그인...")
            server.login(email, password)
            
            print("📤 테스트 이메일 발송...")
            server.send_message(msg)
        
        print("✅ 성공! 새로운 앱 비밀번호가 정상 작동합니다!")
        print(f"   📬 {email}에서 이메일을 확인해보세요.")
        print(f"   ⏰ 발송 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🎉 Gmail SMTP 설정이 완료되었습니다!")
        print("   이제 GA4 자동화 시스템에서 이메일을 발송할 수 있습니다.")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        
        if "Username and Password not accepted" in str(e):
            print("\n💡 추가 시도 방법:")
            print("   1. 5분 정도 기다린 후 다시 시도")
            print("   2. Gmail 계정 잠금 해제: https://accounts.google.com/DisplayUnlockCaptcha")
            print("   3. 또 다른 새로운 앱 비밀번호 생성")
        
        return False

if __name__ == "__main__":
    quick_test() 