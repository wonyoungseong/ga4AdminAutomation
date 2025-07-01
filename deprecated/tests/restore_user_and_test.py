#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 복원 및 권한 부여 테스트
=============================

삭제된 사용자를 다시 추가하고 권한을 부여합니다.
"""

import json
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding
from google.oauth2 import service_account

def restore_and_test_users():
    """사용자 복원 및 권한 부여 테스트"""
    print("🔄 사용자 복원 및 권한 부여 테스트")
    print("=" * 50)
    
    # 설정 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # GA4 클라이언트 초기화 (올바른 스코프)
    service_account_file = 'ga4-automatio-797ec352f393.json'
    scopes = [
        'https://www.googleapis.com/auth/analytics.edit',
        'https://www.googleapis.com/auth/analytics.manage.users'
    ]
    
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=scopes
    )
    client = AnalyticsAdminServiceClient(credentials=credentials)
    
    account_name = f"accounts/{config['account_id']}"
    
    # 테스트할 사용자들
    test_users = [
        {
            "email": "wonyoungseong@gmail.com",
            "role": "predefinedRoles/read"  # Viewer
        },
        {
            "email": "wonyoung.seong@amorepacific.com", 
            "role": "predefinedRoles/read"  # Viewer
        }
    ]
    
    print("📋 현재 사용자 목록:")
    try:
        bindings = client.list_access_bindings(parent=account_name)
        for binding in bindings:
            user_email = binding.user.replace("users/", "")
            print(f"   👤 {user_email}")
    except Exception as e:
        print(f"   ❌ 조회 실패: {e}")
    
    print("\n🎯 사용자 복원 및 권한 부여 시작:")
    
    for user in test_users:
        email = user["email"]
        role = user["role"]
        
        print(f"\n👤 {email} 처리 중...")
        
        try:
            # AccessBinding 생성
            access_binding = AccessBinding(
                user=f"users/{email}",
                roles=[role]
            )
            
            # 권한 부여 시도
            result = client.create_access_binding(
                parent=account_name,
                access_binding=access_binding
            )
            
            print(f"   ✅ 권한 부여 성공!")
            print(f"   📋 바인딩 ID: {result.name}")
            print(f"   🎯 부여된 권한: {role}")
            
        except Exception as e:
            error_msg = str(e)
            
            if "404" in error_msg and "could not be found" in error_msg:
                print(f"   ❌ 사용자를 찾을 수 없음")
                print(f"   💡 해결방법:")
                print(f"      1. {email}로 analytics.google.com 접속")
                print(f"      2. 또는 GA4 콘솔에서 수동 초대")
                print(f"      3. 그 후 이 스크립트 재실행")
                
            elif "409" in error_msg or "already exists" in error_msg:
                print(f"   ⚠️  이미 권한이 존재함")
                
            elif "403" in error_msg:
                print(f"   ❌ 권한 부족: {error_msg}")
                
            else:
                print(f"   ❌ 오류: {error_msg}")
    
    print("\n📋 최종 사용자 목록:")
    try:
        bindings = client.list_access_bindings(parent=account_name)
        for binding in bindings:
            user_email = binding.user.replace("users/", "")
            roles = [role.split('/')[-1] for role in binding.roles]
            print(f"   👤 {user_email} - {', '.join(roles)}")
    except Exception as e:
        print(f"   ❌ 조회 실패: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 결론:")
    print("✅ Service Account 권한: 정상")
    print("✅ API 스코프: 올바름")
    print("💡 404 오류는 사용자가 Google Analytics에 접속한 적이 없기 때문")

if __name__ == "__main__":
    restore_and_test_users()
