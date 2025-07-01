#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네트워크 연결 진단 스크립트
"""

import socket
import smtplib
import ssl

def test_network_connectivity():
    """네트워크 연결 상태 진단"""
    print("🌐 네트워크 연결 진단 시작...\n")
    
    # 1. 기본 연결 테스트
    print("1️⃣ Gmail SMTP 서버 연결 테스트")
    
    servers_to_test = [
        ("smtp.gmail.com", 587, "STARTTLS"),
        ("smtp.gmail.com", 465, "SSL"),
        ("smtp.gmail.com", 25, "Plain")
    ]
    
    for server, port, method in servers_to_test:
        try:
            print(f"   테스트: {server}:{port} ({method})")
            sock = socket.create_connection((server, port), timeout=10)
            sock.close()
            print(f"   ✅ {server}:{port} 연결 성공")
        except Exception as e:
            print(f"   ❌ {server}:{port} 연결 실패: {e}")
    
    print("\n2️⃣ SMTP 프로토콜 테스트")
    
    # 2. SMTP 프로토콜 레벨 테스트
    try:
        print("   SMTP 서버 응답 확인...")
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        print(f"   서버 응답: {server.noop()}")
        
        print("   STARTTLS 지원 확인...")
        server.starttls()
        print("   ✅ STARTTLS 지원됨")
        
        server.quit()
        print("   ✅ SMTP 프로토콜 테스트 성공")
        
    except Exception as e:
        print(f"   ❌ SMTP 프로토콜 테스트 실패: {e}")
    
    print("\n3️⃣ SSL/TLS 인증서 확인")
    
    # 3. SSL 인증서 확인
    try:
        context = ssl.create_default_context()
        with socket.create_connection(('smtp.gmail.com', 465), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname='smtp.gmail.com') as ssock:
                print(f"   ✅ SSL 인증서 검증 성공")
                print(f"   인증서 버전: {ssock.version()}")
    except Exception as e:
        print(f"   ❌ SSL 인증서 확인 실패: {e}")
    
    print("\n4️⃣ DNS 해상도 확인")
    
    # 4. DNS 확인
    try:
        import socket
        ip = socket.gethostbyname('smtp.gmail.com')
        print(f"   ✅ DNS 해상도 성공: smtp.gmail.com → {ip}")
    except Exception as e:
        print(f"   ❌ DNS 해상도 실패: {e}")

if __name__ == "__main__":
    test_network_connectivity() 