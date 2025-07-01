#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 권한 및 스코프 확인
=====================

Service Account의 API 권한과 필요한 스코프를 확인합니다.
"""

import json
import os
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.oauth2 import service_account

def check_api_scopes():
    """API 권한 및 스코프 확인"""
    print("🔍 API 권한 및 스코프 확인")
    print("=" * 50)
    
    try:
        # 1. 현재 사용 중인 스코프 확인
        print("1️⃣ 현재 스코프 설정 확인...")
        
        service_account_file = 'ga4-automatio-797ec352f393.json'
        
        # 다양한 스코프로 테스트
        scopes_to_test = [
            ['https://www.googleapis.com/auth/analytics.edit'],
            ['https://www.googleapis.com/auth/analytics.manage.users'],
            ['https://www.googleapis.com/auth/analytics.manage.users.readonly'],
            ['https://www.googleapis.com/auth/analytics.edit', 
             'https://www.googleapis.com/auth/analytics.manage.users'],
            ['https://www.googleapis.com/auth/analytics.readonly'],
        ]
        
        scope_names = [
            "analytics.edit",
            "analytics.manage.users", 
            "analytics.manage.users.readonly",
            "edit + manage.users",
            "analytics.readonly"
        ]
        
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        account_name = f"accounts/{config['account_id']}"
        
        for i, (scopes, name) in enumerate(zip(scopes_to_test, scope_names)):
            print(f"\n2️⃣ 스코프 테스트 {i+1}: {name}")
            print(f"   📋 스코프: {scopes}")
            
            try:
                # 해당 스코프로 credentials 생성
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_file,
                    scopes=scopes
                )
                
                client = AnalyticsAdminServiceClient(credentials=credentials)
                
                # Account 접근 테스트
                try:
                    account = client.get_account(name=account_name)
                    print(f"   ✅ Account 접근: 성공")
                except Exception as e:
                    print(f"   ❌ Account 접근: 실패 - {str(e)[:100]}...")
                    continue
                
                # Access Bindings 조회 테스트
                try:
                    bindings = client.list_access_bindings(parent=account_name)
                    binding_count = len(list(bindings))
                    print(f"   ✅ Access Bindings 조회: 성공 ({binding_count}개)")
                    
                    # 실제 바인딩 생성 테스트 (테스트용 더미 이메일)
                    print(f"   🧪 권한 부여 테스트 중...")
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"   ❌ Access Bindings 조회: 실패 - {error_msg[:100]}...")
                    
                    if "401" in error_msg:
                        print(f"      💡 401 오류: 인증 권한 부족")
                    elif "403" in error_msg:
                        print(f"      💡 403 오류: API 권한 부족")
                    continue
                
            except Exception as e:
                print(f"   ❌ 클라이언트 초기화 실패: {str(e)[:100]}...")
        
        # 3. Service Account 파일의 권한 정보 확인
        print(f"\n3️⃣ Service Account 파일 권한 정보 확인...")
        
        with open(service_account_file, 'r', encoding='utf-8') as f:
            sa_info = json.load(f)
        
        print(f"   📧 Service Account: {sa_info.get('client_email')}")
        print(f"   🆔 Project ID: {sa_info.get('project_id')}")
        print(f"   🔑 Key Type: {sa_info.get('type')}")
        
        # 4. Google Cloud Console에서 확인해야 할 사항들
        print(f"\n4️⃣ Google Cloud Console 확인 사항")
        print(f"=" * 50)
        print(f"🔍 다음 사항들을 Google Cloud Console에서 확인해주세요:")
        print(f"")
        print(f"1. Service Account 권한:")
        print(f"   - IAM & Admin > Service Accounts")
        print(f"   - {sa_info.get('client_email')} 선택")
        print(f"   - 'Analytics Admin' 또는 'Analytics Editor' 역할 필요")
        print(f"")
        print(f"2. API 활성화 확인:")
        print(f"   - APIs & Services > Library")
        print(f"   - 'Google Analytics Admin API' 검색 및 활성화 확인")
        print(f"")
        print(f"3. Service Account 키 권한:")
        print(f"   - Service Account에 'Analytics Admin' 역할 부여")
        print(f"   - 또는 'Analytics Editor' + 'Analytics User Management' 권한")
        print(f"")
        print(f"4. GA4 Property에서 Service Account 확인:")
        print(f"   - GA4 > Admin > Property Access Management")
        print(f"   - {sa_info.get('client_email')} 사용자가 관리자 권한으로 등록되어 있는지 확인")
        
        # 5. 권장 해결 방법
        print(f"\n5️⃣ 권장 해결 방법")
        print(f"=" * 50)
        print(f"💡 다음 순서로 문제를 해결해보세요:")
        print(f"")
        print(f"1단계: Google Cloud Console")
        print(f"   → IAM & Admin → Service Accounts")
        print(f"   → {sa_info.get('client_email')} 선택")
        print(f"   → 'Analytics Admin' 역할 추가")
        print(f"")
        print(f"2단계: GA4 Console")
        print(f"   → Admin → Property Access Management")
        print(f"   → Add users → {sa_info.get('client_email')}")
        print(f"   → Administrator 권한으로 추가")
        print(f"")
        print(f"3단계: API 재테스트")
        print(f"   → 위 설정 완료 후 다시 테스트")
        
    except Exception as e:
        print(f"❌ 확인 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_api_scopes()
