#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Account 권한 및 설정 진단
===============================

Service Account의 권한과 설정을 상세히 진단합니다.
"""

import json
import os
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding
from google.oauth2 import service_account

def diagnose_service_account():
    """Service Account 권한 및 설정 진단"""
    print("🔍 Service Account 권한 및 설정 진단")
    print("=" * 60)
    
    try:
        # 1. 설정 파일 확인
        print("1️⃣ 설정 파일 확인...")
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"   ✅ Account ID: {config['account_id']}")
        print(f"   ✅ Property ID: {config['property_id']}")
        
        # 2. Service Account 파일 확인
        print("\n2️⃣ Service Account 파일 확인...")
        service_account_file = 'config/ga4-automatio-797ec352f393.json'
        
        if os.path.exists(service_account_file):
            with open(service_account_file, 'r', encoding='utf-8') as f:
                sa_info = json.load(f)
            
            print(f"   ✅ Service Account 파일 존재")
            print(f"   📧 Service Account Email: {sa_info.get('client_email', 'N/A')}")
            print(f"   🆔 Project ID: {sa_info.get('project_id', 'N/A')}")
            print(f"   �� Private Key ID: {sa_info.get('private_key_id', 'N/A')[:20]}...")
        else:
            print(f"   ❌ Service Account 파일을 찾을 수 없습니다: {service_account_file}")
            return
        
        # 3. GA4 클라이언트 초기화 및 권한 확인
        print("\n3️⃣ GA4 클라이언트 초기화 및 권한 확인...")
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_file
        
        # 직접 credentials 로드해서 확인
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/analytics.edit']
        )
        
        client = AnalyticsAdminServiceClient(credentials=credentials)
        print(f"   ✅ GA4 클라이언트 초기화 성공")
        
        # 4. Account 접근 권한 확인
        print("\n4️⃣ Account 접근 권한 확인...")
        account_name = f"accounts/{config['account_id']}"
        
        try:
            # Account 정보 조회 시도
            account = client.get_account(name=account_name)
            print(f"   ✅ Account 접근 성공: {account.display_name}")
            print(f"   🌍 Account Region: {account.region_code}")
        except Exception as e:
            print(f"   ❌ Account 접근 실패: {e}")
            return
        
        # 5. Property 접근 권한 확인
        print("\n5️⃣ Property 접근 권한 확인...")
        property_name = f"properties/{config['property_id']}"
        
        try:
            # Property 정보 조회 시도
            property_info = client.get_property(name=property_name)
            print(f"   ✅ Property 접근 성공: {property_info.display_name}")
            print(f"   🏢 Property Type: {property_info.property_type}")
        except Exception as e:
            print(f"   ❌ Property 접근 실패: {e}")
            return
        
        # 6. 현재 Access Bindings 확인
        print("\n6️⃣ 현재 Access Bindings 확인...")
        try:
            bindings = client.list_access_bindings(parent=account_name)
            binding_count = 0
            
            for binding in bindings:
                binding_count += 1
                user_email = binding.user.replace("users/", "")
                roles = [role.split('/')[-1] for role in binding.roles]
                print(f"   👤 사용자 {binding_count}: {user_email}")
                print(f"      🎯 권한: {', '.join(roles)}")
                print(f"      📋 바인딩 ID: {binding.name}")
            
            print(f"   📊 총 {binding_count}개의 사용자 바인딩 발견")
            
        except Exception as e:
            print(f"   ❌ Access Bindings 조회 실패: {e}")
            return
        
        # 7. 테스트 계정 직접 추가 시도
        print("\n7️⃣ 테스트 계정 직접 추가 시도...")
        test_emails = ["wonyoungseong@gmail.com", "wonyoung.seong@amorepacific.com"]
        
        for test_email in test_emails:
            print(f"\n   🎯 테스트 대상: {test_email}")
            
            try:
                # Viewer 권한으로 추가 시도
                access_binding = AccessBinding(
                    user=f"users/{test_email}",
                    roles=["predefinedRoles/read"]
                )
                
                response = client.create_access_binding(
                    parent=account_name,
                    access_binding=access_binding
                )
                
                print(f"      ✅ 권한 부여 성공!")
                print(f"      📋 바인딩 ID: {response.name}")
                
                # 성공하면 바로 제거 (테스트 목적)
                try:
                    client.delete_access_binding(name=response.name)
                    print(f"      🗑️ 테스트 권한 제거 완료")
                except:
                    print(f"      ⚠️ 테스트 권한 제거 실패 (수동 제거 필요)")
                
            except Exception as e:
                error_msg = str(e)
                print(f"      ❌ 권한 부여 실패: {error_msg}")
                
                # 오류 유형별 분석
                if "404" in error_msg and "could not be found" in error_msg:
                    print(f"      💡 404 오류 - 사용자가 Google Analytics에 접속한 적이 없음")
                elif "403" in error_msg:
                    print(f"      💡 403 오류 - Service Account 권한 부족")
                elif "400" in error_msg:
                    print(f"      💡 400 오류 - 잘못된 요청 형식")
                else:
                    print(f"      💡 기타 오류 - 추가 조사 필요")
        
        # 8. Service Account 자체 권한 확인
        print(f"\n8️⃣ Service Account 자체 권한 확인...")
        sa_email = sa_info.get('client_email', '')
        
        bindings = client.list_access_bindings(parent=account_name)
        sa_found = False
        
        for binding in bindings:
            user_email = binding.user.replace("users/", "")
            if user_email == sa_email:
                sa_found = True
                roles = [role.split('/')[-1] for role in binding.roles]
                print(f"   ✅ Service Account 권한 발견: {', '.join(roles)}")
                
                if 'manage' in roles or 'admin' in roles:
                    print(f"   ✅ 충분한 관리자 권한 보유")
                else:
                    print(f"   ⚠️ 제한된 권한 - 사용자 관리에 부족할 수 있음")
                break
        
        if not sa_found:
            print(f"   ❌ Service Account가 GA4에 등록되지 않음")
            print(f"   💡 GA4 콘솔에서 Service Account를 수동으로 추가해야 함")
        
        # 9. 진단 결과 요약
        print(f"\n📋 진단 결과 요약")
        print(f"=" * 60)
        print(f"✅ Service Account 파일: 정상")
        print(f"✅ GA4 클라이언트 초기화: 정상")
        print(f"✅ Account 접근: 정상")
        print(f"✅ Property 접근: 정상")
        print(f"✅ Access Bindings 조회: 정상")
        print(f"{'✅' if sa_found else '❌'} Service Account 권한: {'정상' if sa_found else '문제'}")
        
        print(f"\n💡 권장사항:")
        if sa_found:
            print(f"   - Service Account 권한은 정상입니다")
            print(f"   - 테스트 계정들이 Google Analytics에 직접 로그인 필요")
            print(f"   - 또는 GA4 콘솔에서 수동 초대 후 API 사용")
        else:
            print(f"   - Service Account를 GA4에 관리자 권한으로 추가 필요")
            print(f"   - 그 후 테스트 계정 추가 재시도")
        
    except Exception as e:
        print(f"❌ 진단 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_service_account()
