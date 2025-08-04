#!/usr/bin/env python3
"""
RBAC 시스템 디버깅 스크립트
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """로그인 테스트"""
    print("=== 로그인 테스트 ===")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"email": "admin@example.com", "password": "admin123"}
    )
    
    print(f"로그인 응답 코드: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"토큰: {data.get('access_token', 'N/A')[:50]}...")
        print(f"사용자 정보: {data.get('user', 'N/A')}")
        return data.get('access_token')
    else:
        print(f"로그인 실패: {response.text}")
        return None

def test_user_info(token):
    """사용자 정보 조회 테스트"""
    print("\n=== 사용자 정보 조회 테스트 ===")
    
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"사용자 정보 응답 코드: {response.status_code}")
    if response.status_code == 200:
        print(f"사용자 정보: {response.json()}")
    else:
        print(f"사용자 정보 조회 실패: {response.text}")

def test_users_list(token):
    """사용자 목록 조회 테스트"""
    print("\n=== 사용자 목록 조회 테스트 ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"사용자 목록 응답 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"사용자 수: {len(users)}")
            for user in users:
                print(f"  - {user.get('name')} ({user.get('email')}) - {user.get('role')}")
        else:
            print(f"사용자 목록 조회 실패: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"요청 예외 발생: {e}")
    except Exception as e:
        print(f"기타 예외 발생: {e}")

def test_permissions_list(token):
    """권한 목록 조회 테스트"""
    print("\n=== 권한 목록 조회 테스트 ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/permissions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        print(f"권한 목록 응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            permissions = response.json()
            print(f"권한 요청 수: {len(permissions)}")
        else:
            print(f"권한 목록 조회 실패: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"요청 예외 발생: {e}")

def main():
    print("🔍 RBAC 시스템 디버깅 시작")
    
    # 1. 로그인
    token = test_login()
    if not token:
        print("로그인 실패로 테스트 중단")
        return
    
    # 2. 사용자 정보 조회
    test_user_info(token)
    
    # 3. 사용자 목록 조회
    test_users_list(token)
    
    # 4. 권한 목록 조회
    test_permissions_list(token)

if __name__ == "__main__":
    main()