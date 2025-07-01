#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property 레벨 사용자 등록 테스트
==============================

이전에 성공했던 방식으로 Property 레벨에서 사용자 등록을 시도합니다.
"""

import json
import logging
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, CreateAccessBindingRequest
from google.oauth2 import service_account

class PropertyLevelAccessTest:
    """Property 레벨 접근 테스트"""
    
    def __init__(self):
        self.config = self._load_config()
        self._setup_logging()
        self._init_client()
    
    def _load_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _init_client(self):
        """Service Account 클라이언트 초기화"""
        service_account_file = 'ga4-automatio-797ec352f393.json'
        
        scopes = [
            'https://www.googleapis.com/auth/analytics.edit',
            'https://www.googleapis.com/auth/analytics.manage.users',
            'https://www.googleapis.com/auth/analytics.readonly'
        ]
        
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        
        self.client = AnalyticsAdminServiceClient(credentials=credentials)
        self.logger.info("✅ Service Account 클라이언트 초기화 완료")
    
    def test_property_level_user_addition(self, email: str, role: str = "analyst"):
        """Property 레벨에서 사용자 추가 테스트 (이전 성공 방식)"""
        
        self.logger.info(f"🧪 Property 레벨 사용자 추가 테스트: {email}")
        
        # Property 경로 (이전 성공 방식)
        parent = f"properties/{self.config['property_id']}"
        
        # 역할 매핑 (이전 성공 방식)
        role_mapping = {
            'analyst': 'predefinedRoles/analyst',
            'editor': 'predefinedRoles/editor', 
            'admin': 'predefinedRoles/admin',
            'viewer': 'predefinedRoles/viewer'
        }
        
        predefined_role = role_mapping.get(role.lower(), 'predefinedRoles/analyst')
        
        try:
            self.logger.info(f"📝 요청 준비:")
            self.logger.info(f"   - Parent: {parent}")
            self.logger.info(f"   - User: {email}")  # users/ 접두사 없이
            self.logger.info(f"   - Role: {predefined_role}")
            
            # AccessBinding 생성 (이전 성공 방식)
            access_binding = AccessBinding(
                user=email,  # users/ 접두사 없이
                roles=[predefined_role]
            )
            
            # CreateAccessBindingRequest 생성 (이전 성공 방식)
            request = CreateAccessBindingRequest(
                parent=parent,
                access_binding=access_binding
            )
            
            # API 호출
            response = self.client.create_access_binding(request=request)
            
            self.logger.info(f"✅ 사용자 추가 성공!")
            self.logger.info(f"응답: {response}")
            return True, response.name
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ 실패: {error_msg}")
            
            # 에러 분석
            if "404" in error_msg or "NOT_FOUND" in error_msg:
                self.logger.info("💡 404 에러 분석:")
                self.logger.info("   - 사용자가 Google Analytics 시스템에 등록되지 않음")
                self.logger.info("   - 또는 Property ID가 잘못됨")
                
            elif "403" in error_msg or "PERMISSION_DENIED" in error_msg:
                self.logger.info("💡 403 에러 분석:")
                self.logger.info("   - Service Account 권한 부족")
                
            elif "409" in error_msg or "ALREADY_EXISTS" in error_msg:
                self.logger.info("💡 409 에러 분석:")
                self.logger.info("   - 사용자가 이미 존재함")
                
            return False, error_msg
    
    def test_account_vs_property_level(self, email: str):
        """Account 레벨 vs Property 레벨 비교 테스트"""
        
        self.logger.info(f"🔄 Account vs Property 레벨 비교 테스트: {email}")
        
        # 1. Account 레벨 시도 (현재 실패 방식)
        self.logger.info("\n1️⃣ Account 레벨 시도 (현재 방식)")
        account_parent = f"accounts/{self.config['account_id']}"
        
        try:
            access_binding = AccessBinding(
                user=f"users/{email}",  # users/ 접두사 포함
                roles=["predefinedRoles/read"]
            )
            
            response = self.client.create_access_binding(
                parent=account_parent,
                access_binding=access_binding
            )
            
            self.logger.info(f"✅ Account 레벨 성공!")
            return True, "account_level"
            
        except Exception as e:
            self.logger.error(f"❌ Account 레벨 실패: {e}")
        
        # 2. Property 레벨 시도 (이전 성공 방식)
        self.logger.info("\n2️⃣ Property 레벨 시도 (이전 성공 방식)")
        success, result = self.test_property_level_user_addition(email, "analyst")
        
        if success:
            return True, "property_level"
        else:
            return False, result
    
    def list_property_users(self):
        """Property 레벨 사용자 목록 조회"""
        
        self.logger.info("👥 Property 레벨 사용자 목록 조회")
        
        parent = f"properties/{self.config['property_id']}"
        
        try:
            # Property 레벨에서 access bindings 조회
            response = self.client.list_access_bindings(parent=parent)
            binding_list = list(response)
            
            self.logger.info(f"📊 Property 레벨에서 {len(binding_list)}명의 사용자 발견:")
            
            for i, binding in enumerate(binding_list, 1):
                user_email = binding.user
                roles = list(binding.roles)
                
                self.logger.info(f"   {i}. {user_email}")
                self.logger.info(f"      - 권한: {roles}")
                self.logger.info(f"      - 바인딩 ID: {binding.name}")
            
            return binding_list
            
        except Exception as e:
            self.logger.error(f"❌ Property 사용자 목록 조회 실패: {e}")
            return []
    
    def comprehensive_test(self, test_email: str):
        """종합 테스트"""
        
        self.logger.info("🚀 Property 레벨 종합 테스트 시작")
        self.logger.info("=" * 60)
        
        # 1. Property 레벨 사용자 목록 확인
        self.logger.info("\n1️⃣ Property 레벨 사용자 목록 확인")
        property_users = self.list_property_users()
        
        # 2. Account vs Property 레벨 비교
        self.logger.info(f"\n2️⃣ {test_email} Account vs Property 레벨 비교")
        success, method = self.test_account_vs_property_level(test_email)
        
        if success:
            self.logger.info(f"🎉 성공! 방법: {method}")
            
            # 성공 후 목록 재확인
            self.logger.info("\n3️⃣ 추가 후 사용자 목록 재확인")
            if method == "property_level":
                self.list_property_users()
            else:
                # Account 레벨에서 확인
                account_parent = f"accounts/{self.config['account_id']}"
                try:
                    bindings = self.client.list_access_bindings(parent=account_parent)
                    for binding in bindings:
                        self.logger.info(f"Account 사용자: {binding.user}")
                except Exception as e:
                    self.logger.error(f"Account 사용자 조회 실패: {e}")
            
            # 테스트 권한 삭제 여부 확인
            delete_choice = input("\n테스트 권한을 삭제하시겠습니까? (y/n): ").strip().lower()
            if delete_choice == 'y':
                self._cleanup_test_user(test_email, method)
        else:
            self.logger.error(f"❌ 모든 방법 실패: {method}")
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🏁 종합 테스트 완료")
    
    def _cleanup_test_user(self, email: str, method: str):
        """테스트 사용자 정리"""
        try:
            if method == "property_level":
                parent = f"properties/{self.config['property_id']}"
            else:
                parent = f"accounts/{self.config['account_id']}"
            
            # 사용자 바인딩 찾기
            bindings = self.client.list_access_bindings(parent=parent)
            
            for binding in bindings:
                user_in_binding = binding.user
                if method == "property_level":
                    target_user = email
                else:
                    target_user = f"users/{email}"
                
                if user_in_binding == target_user:
                    self.client.delete_access_binding(name=binding.name)
                    self.logger.info(f"🗑️ 테스트 권한 삭제 완료: {binding.name}")
                    return
            
            self.logger.warning(f"⚠️ 삭제할 사용자를 찾을 수 없음: {email}")
            
        except Exception as e:
            self.logger.error(f"❌ 테스트 권한 삭제 실패: {e}")

def main():
    """메인 실행 함수"""
    
    test_system = PropertyLevelAccessTest()
    
    print("🧪 Property 레벨 사용자 등록 테스트")
    print("=" * 50)
    
    test_email = input("테스트할 이메일 주소: ").strip()
    
    if not test_email:
        print("❌ 이메일 주소를 입력해주세요.")
        return
    
    # 종합 테스트 실행
    test_system.comprehensive_test(test_email)

if __name__ == "__main__":
    main() 