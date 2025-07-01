#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
상세 진단 시스템
===============

사용자가 로그인했는데도 API에서 찾을 수 없는 정확한 원인을 파악합니다.
"""

import json
import time
from datetime import datetime
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding
from google.oauth2 import service_account
from complete_ga4_user_automation import CompleteGA4UserAutomation, UserRole

class DetailedDiagnosis:
    """상세 진단 시스템"""
    
    def __init__(self):
        self.config = self._load_config()
        self.automation = CompleteGA4UserAutomation()
        self._init_clients()
    
    def _load_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _init_clients(self):
        """다양한 스코프로 클라이언트 초기화"""
        service_account_file = 'ga4-automatio-797ec352f393.json'
        
        # 다양한 스코프 조합
        self.scope_combinations = {
            'readonly': ['https://www.googleapis.com/auth/analytics.readonly'],
            'edit': ['https://www.googleapis.com/auth/analytics.edit'],
            'manage_users': ['https://www.googleapis.com/auth/analytics.manage.users'],
            'edit_and_users': [
                'https://www.googleapis.com/auth/analytics.edit',
                'https://www.googleapis.com/auth/analytics.manage.users'
            ],
            'all_scopes': [
                'https://www.googleapis.com/auth/analytics.readonly',
                'https://www.googleapis.com/auth/analytics.edit',
                'https://www.googleapis.com/auth/analytics.manage.users'
            ]
        }
        
        self.clients = {}
        for name, scopes in self.scope_combinations.items():
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_file, scopes=scopes
                )
                self.clients[name] = AnalyticsAdminServiceClient(credentials=credentials)
                print(f"✅ {name} 클라이언트 초기화 성공")
            except Exception as e:
                print(f"❌ {name} 클라이언트 초기화 실패: {e}")
    
    def comprehensive_diagnosis(self, target_email: str):
        """포괄적 진단"""
        print(f"🔍 {target_email} 포괄적 진단 시작")
        print("=" * 80)
        
        account_name = f"accounts/{self.config['account_id']}"
        property_name = f"properties/{self.config['property_id']}"
        
        # 1. 각 스코프별 사용자 목록 조회
        print("1️⃣ 스코프별 사용자 목록 조회")
        print("-" * 50)
        
        all_users_found = {}
        
        for scope_name, client in self.clients.items():
            print(f"\n📋 {scope_name} 스코프로 조회:")
            try:
                # Account 접근 테스트
                account = client.get_account(name=account_name)
                print(f"   ✅ Account 접근: {account.display_name}")
                
                # Property 접근 테스트  
                property_obj = client.get_property(name=property_name)
                print(f"   ✅ Property 접근: {property_obj.display_name}")
                
                # Access Bindings 조회
                try:
                    bindings = client.list_access_bindings(parent=account_name)
                    binding_list = list(bindings)
                    print(f"   ✅ Access Bindings 조회: {len(binding_list)}개")
                    
                    users_in_scope = []
                    for binding in binding_list:
                        user_email = binding.user.replace("users/", "")
                        roles = [role for role in binding.roles]
                        users_in_scope.append({
                            'email': user_email,
                            'roles': roles,
                            'binding_id': binding.name
                        })
                        print(f"      👤 {user_email}: {roles}")
                        
                        # 대상 이메일 확인
                        if user_email.lower() == target_email.lower():
                            print(f"      🎯 대상 이메일 발견!")
                    
                    all_users_found[scope_name] = users_in_scope
                    
                except Exception as e:
                    print(f"   ❌ Access Bindings 조회 실패: {e}")
                    all_users_found[scope_name] = None
                    
            except Exception as e:
                print(f"   ❌ {scope_name} 전체 실패: {e}")
                all_users_found[scope_name] = None
        
        # 2. 대상 이메일 직접 추가 시도
        print(f"\n2️⃣ {target_email} 직접 추가 시도")
        print("-" * 50)
        
        for scope_name, client in self.clients.items():
            if all_users_found.get(scope_name) is not None:
                print(f"\n🎯 {scope_name} 스코프로 추가 시도:")
                
                try:
                    access_binding = AccessBinding(
                        user=f"users/{target_email}",
                        roles=["predefinedRoles/read"]
                    )
                    
                    result = client.create_access_binding(
                        parent=account_name,
                        access_binding=access_binding
                    )
                    
                    print(f"   ✅ 성공! 바인딩 ID: {result.name}")
                    
                    # 즉시 삭제 (테스트용)
                    try:
                        client.delete_access_binding(name=result.name)
                        print(f"   🗑️ 테스트 권한 삭제 완료")
                    except:
                        print(f"   ⚠️ 테스트 권한 삭제 실패 (수동 삭제 필요)")
                    
                    return True, f"{scope_name} 스코프로 성공"
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"   ❌ 실패: {error_msg}")
                    
                    if "404" in error_msg:
                        print(f"      💡 404 오류: 사용자가 Google Analytics 시스템에 등록되지 않음")
                    elif "403" in error_msg:
                        print(f"      💡 403 오류: 권한 부족")
                    elif "409" in error_msg:
                        print(f"      💡 409 오류: 이미 존재함")
                    else:
                        print(f"      💡 기타 오류: {error_msg}")
        
        # 3. 계정 동기화 상태 확인
        print(f"\n3️⃣ 계정 동기화 상태 확인")
        print("-" * 50)
        
        # 여러 번 시도하여 동기화 지연 확인
        for attempt in range(1, 4):
            print(f"\n시도 {attempt}/3:")
            time.sleep(2)  # 2초 대기
            
            try:
                client = self.clients['edit_and_users']
                bindings = client.list_access_bindings(parent=account_name)
                
                found_target = False
                for binding in bindings:
                    user_email = binding.user.replace("users/", "")
                    if user_email.lower() == target_email.lower():
                        print(f"   ✅ {target_email} 발견!")
                        found_target = True
                        break
                
                if not found_target:
                    print(f"   ❌ {target_email} 여전히 찾을 수 없음")
                else:
                    break
                    
            except Exception as e:
                print(f"   ❌ 조회 실패: {e}")
        
        # 4. 결론 및 권장사항
        print(f"\n4️⃣ 진단 결론 및 권장사항")
        print("-" * 50)
        
        # 사용자가 발견된 스코프 확인
        found_in_scopes = []
        for scope_name, users in all_users_found.items():
            if users:
                for user in users:
                    if user['email'].lower() == target_email.lower():
                        found_in_scopes.append(scope_name)
        
        if found_in_scopes:
            print(f"✅ {target_email}이 다음 스코프에서 발견됨: {found_in_scopes}")
            print(f"💡 권한은 이미 존재하지만 API 호출에 문제가 있을 수 있음")
        else:
            print(f"❌ {target_email}이 어떤 스코프에서도 발견되지 않음")
            print(f"💡 가능한 원인들:")
            print(f"   1. Google Analytics 로그인은 했지만 해당 Property에 접근하지 않음")
            print(f"   2. 다른 Google Analytics 계정에 로그인함")
            print(f"   3. Property ID나 Account ID가 다름")
            print(f"   4. Google Analytics와 Admin API 간 동기화 지연")
            print(f"   5. 사용자가 다른 조직의 Analytics에 로그인함")
        
        return False, "진단 완료"
    
    def verify_account_property_access(self, target_email: str):
        """계정/속성 접근 권한 확인"""
        print(f"\n🔍 {target_email} 계정/속성 접근 권한 확인")
        print("-" * 50)
        
        account_id = self.config['account_id']
        property_id = self.config['property_id']
        
        print(f"📋 확인 대상:")
        print(f"   Account ID: {account_id}")
        print(f"   Property ID: {property_id}")
        print(f"   Target Email: {target_email}")
        
        # 사용자에게 확인 요청
        print(f"\n❓ 사용자 확인 사항:")
        print(f"   1. {target_email}로 로그인했나요?")
        print(f"   2. 'BETC' 계정이 보이나요?")
        print(f"   3. '[Edu]Ecommerce - Beauty Cosmetic' 속성이 보이나요?")
        print(f"   4. 현재 화면에서 Account ID {account_id}가 URL에 있나요?")
        
        return True

def main():
    """메인 실행 함수"""
    print("🔍 상세 진단 시스템")
    print("=" * 60)
    
    target_email = "wonyoung.seong@amorepacific.com"
    
    diagnosis = DetailedDiagnosis()
    
    print(f"🎯 대상 이메일: {target_email}")
    print(f"🕐 진단 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 포괄적 진단 실행
    success, message = diagnosis.comprehensive_diagnosis(target_email)
    
    # 계정/속성 접근 확인
    diagnosis.verify_account_property_access(target_email)
    
    print(f"\n🎉 진단 완료: {message}")
    print(f"🕐 진단 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 