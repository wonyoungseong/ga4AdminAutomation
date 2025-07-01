#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMTP 연결 디버깅 스크립트
========================

Gmail SMTP 연결 문제를 진단합니다.
"""

import json
import smtplib
import socket
from email.mime.text import MIMEText

def debug_smtp_connection():
    """SMTP 연결 상세 진단"""
    print("🔍 SMTP 연결 디버깅 시작...\n")
    
    try:
        # config.json 로드
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        smtp_settings = config.get('smtp_settings', {})
        
        # 1. 설정 정보 출력
        print("📋 현재 SMTP 설정 정보")
        for key, value in smtp_settings.items():
            print(f"{key}: {value}")
        
        # 2. SMTP 연결 테스트
        print("\n🔍 SMTP 연결 테스트 시작...")
        
        smtp_server = smtp_settings.get('smtp_server')
        smtp_port = smtp_settings.get('smtp_port')
        use_tls = smtp_settings.get('use_tls')
        sender_email = smtp_settings.get('sender_email')
        sender_password = smtp_settings.get('sender_password')
        sender_name = smtp_settings.get('sender_name')
        timeout = smtp_settings.get('timeout')
        
        if not smtp_server or not smtp_port or not use_tls or not sender_email or not sender_password or not sender_name or not timeout:
            print("❌ 필수 설정 정보가 누락되었습니다. 설정을 확인하고 다시 시도해주세요.")
            return
        
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(sender_email, sender_password)
                print("✅ SMTP 연결 성공")
        except Exception as e:
            print(f"❌ SMTP 연결 실패: {e}")
    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")

if __name__ == "__main__":
    debug_smtp_connection() 