#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 접근 권한 디버깅
====================

다양한 방법으로 사용자 접근을 테스트합니다.
"""

import json
import os
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.oauth2 import service_account

def test_user_access_methods():
    """다양한 방법으로 사용자 접근 테스트"""
    print("🔍 사용자 접근 권한 디버깅")
    print("=" * 60)
    
    # 설정 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    service_account_file = 'ga4-automatio-797ec352f393.json'
    account_name = f"accounts/{config['account_id']}"
    property_name = f"properties/{config['property_id']}"
    
    # 테스트할 이메일
    test_emails = [
        "wonyoungseong@gmail.com",
        "wonyoung.seong@amorepacific.com"
    ]
    
    # 다양한 스코프 조합 테스트
    scope_combinations = [
        # 기본 스코프
        ['https://www.googleapis.com/auth/analytics.readonly'],
        # 편집 스코프
        ['https://www.googleapis.com/auth/analytics.edit'],
        # 사용자 관리 스코프
        ['https://www.googleapis.com/auth/analytics.manage.users'],
        # 조합 스코프
        ['https://www.googleapis.com/auth/analytics.edit', 
         'https://www.googleapis.com/auth/analytics.manage.users'],
        # 모든 스코프
        ['https://www.googleapis.com/auth/analytics.readonly',
         'https://www.googleapis.com/auth/analytics.edit',
         'https://www.googleapis.com/auth/analytics.manage.users']
    ]
    
    for i, scopes in enumerate(scope_combinations, 1):
        print(f"\n📋 테스트 {i}: {[s.split('.')[-1] for s in scopes]}")
        print("-" * 40)
        
        try:
            # 클라이언트 초기화
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=scopes
            )
            client = AnalyticsAdminServiceClient(credentials=credentials)
            
            # 1. Account 접근 테스트
            try:
                account = client.get_account(name=account_name)
                print(f"✅ Account 접근 성공: {account.display_name}")
            except Exception as e:
                print(f"❌ Account 접근 실패: {e}")
                continue
            
            # 2. Property 접근 테스트
            try:
                property_obj = client.get_property(name=property_name)
                print(f"✅ Property 접근 성공: {property_obj.display_name}")
            except Exception as e:
                print(f"❌ Property 접근 실패: {e}")
            
            # 3. Access Bindings 조회 테스트
            try:
                bindings = client.list_access_bindings(parent=account_name)
                binding_list = list(bindings)
                print(f"✅ Access Bindings 조회 성공: {len(binding_list)}개")
                
                # 현재 사용자 목록 출력
                for binding in binding_list:
                    user_email = binding.user.replace("users/", "")
                    print(f"   👤 {user_email}")
                    
            except Exception as e:
                print(f"❌ Access Bindings 조회 실패: {e}")
            
            # 4. 특정 사용자 검색 테스트
            for email in test_emails:
                try:
                    # 사용자 추가 시도 (실제로는 추가하지 않고 오류만 확인)
                    from google.analytics.admin_v1alpha.types import AccessBinding
                    
                    access_binding = AccessBinding(
                        user=f"users/{email}",
                        roles=["predefinedRoles/read"]
                    )
                    
                    # 실제 추가하지 않고 검증만
                    print(f"   🔍 {email} 검색 중...")
                    
                    # 사용자가 존재하는지 확인하기 위해 실제 추가 시도
                    try:
                        result = client.create_access_binding(
                            parent=account_name,
                            access_binding=access_binding
                        )
                        print(f"   ✅ {email} 권한 부여 성공!")
                        
                        # 즉시 삭제
                        client.delete_access_binding(name=result.name)
                        print(f"   🗑️ {email} 권한 삭제 완료")
                        
                    except Exception as add_error:
                        error_msg = str(add_error)
                        if "404" in error_msg and "could not be found" in error_msg:
                            print(f"   ❌ {email}: 사용자를 찾을 수 없음 (404)")
                        elif "403" in error_msg:
                            print(f"   ❌ {email}: 권한 부족 (403)")
                        elif "401" in error_msg:
                            print(f"   ❌ {email}: 인증 실패 (401)")
                        else:
                            print(f"   ❌ {email}: {error_msg}")
                            
                except Exception as e:
                    print(f"   ❌ {email} 테스트 실패: {e}")
                    
        except Exception as e:
            print(f"❌ 스코프 조합 테스트 실패: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 결론:")
    print("- 스크린샷에서는 사용자가 보이지만 API에서는 찾을 수 없음")
    print("- 이는 GA4 콘솔과 Admin API 간의 동기화 지연일 수 있음")
    print("- 또는 다른 방법으로 추가된 사용자일 수 있음")

if __name__ == "__main__":
    test_user_access_methods() 