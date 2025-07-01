#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Account를 활용한 API 사용자 등록 테스트
============================================

Google Analytics Admin API를 통해 Service Account 권한으로
직접 사용자를 등록하는 방법을 테스트합니다.
"""

import json
import logging
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding
from google.oauth2 import service_account

class ServiceAccountUserRegistrationTest:
    """Service Account 사용자 등록 테스트"""
    
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
        
        # 모든 필요한 스코프
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
    
    def test_direct_user_addition(self, email: str, role: str = "viewer"):
        """직접 사용자 추가 테스트"""
        
        self.logger.info(f"🧪 직접 사용자 추가 테스트 시작: {email}")
        
        account_name = f"accounts/{self.config['account_id']}"
        
        role_mapping = {
            'viewer': 'predefinedRoles/read',
            'editor': 'predefinedRoles/edit',
            'admin': 'predefinedRoles/admin'
        }
        
        ga4_role = role_mapping.get(role, 'predefinedRoles/read')
        
        try:
            # Access Binding 생성
            access_binding = AccessBinding(
                user=f"users/{email}",
                roles=[ga4_role]
            )
            
            self.logger.info(f"📝 Access Binding 생성 시도...")
            self.logger.info(f"   - Parent: {account_name}")
            self.logger.info(f"   - User: users/{email}")
            self.logger.info(f"   - Role: {ga4_role}")
            
            result = self.client.create_access_binding(
                parent=account_name,
                access_binding=access_binding
            )
            
            self.logger.info(f"✅ 성공! 바인딩 ID: {result.name}")
            return True, result.name
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ 실패: {error_msg}")
            
            # 에러 분석
            if "404" in error_msg:
                self.logger.info("💡 404 에러 분석:")
                self.logger.info("   - 사용자가 Google Analytics 시스템에 등록되지 않음")
                self.logger.info("   - 사용자가 해당 Google 계정으로 GA에 최소 1번 로그인 필요")
                
            elif "403" in error_msg:
                self.logger.info("💡 403 에러 분석:")
                self.logger.info("   - Service Account 권한 부족")
                self.logger.info("   - 해당 계정/속성에 대한 관리 권한 없음")
                
            elif "409" in error_msg:
                self.logger.info("💡 409 에러 분석:")
                self.logger.info("   - 사용자가 이미 존재함")
                
            return False, error_msg
    
    def test_current_users(self):
        """현재 등록된 사용자 목록 확인"""
        
        self.logger.info("👥 현재 등록된 사용자 목록 확인")
        
        account_name = f"accounts/{self.config['account_id']}"
        
        try:
            bindings = self.client.list_access_bindings(parent=account_name)
            binding_list = list(bindings)
            
            self.logger.info(f"📊 총 {len(binding_list)}명의 사용자 발견:")
            
            for i, binding in enumerate(binding_list, 1):
                user_email = binding.user.replace("users/", "")
                roles = list(binding.roles)
                
                self.logger.info(f"   {i}. {user_email}")
                self.logger.info(f"      - 권한: {roles}")
                self.logger.info(f"      - 바인딩 ID: {binding.name}")
            
            return binding_list
            
        except Exception as e:
            self.logger.error(f"❌ 사용자 목록 조회 실패: {e}")
            return []
    
    def test_service_account_permissions(self):
        """Service Account 권한 테스트"""
        
        self.logger.info("🔐 Service Account 권한 테스트")
        
        account_name = f"accounts/{self.config['account_id']}"
        property_name = f"properties/{self.config['property_id']}"
        
        # 1. Account 접근 테스트
        try:
            account = self.client.get_account(name=account_name)
            self.logger.info(f"✅ Account 접근 성공: {account.display_name}")
        except Exception as e:
            self.logger.error(f"❌ Account 접근 실패: {e}")
            return False
        
        # 2. Property 접근 테스트
        try:
            property_obj = self.client.get_property(name=property_name)
            self.logger.info(f"✅ Property 접근 성공: {property_obj.display_name}")
        except Exception as e:
            self.logger.error(f"❌ Property 접근 실패: {e}")
            return False
        
        # 3. Access Bindings 읽기 권한 테스트
        try:
            bindings = self.client.list_access_bindings(parent=account_name)
            binding_count = len(list(bindings))
            self.logger.info(f"✅ Access Bindings 읽기 성공: {binding_count}개")
        except Exception as e:
            self.logger.error(f"❌ Access Bindings 읽기 실패: {e}")
            return False
        
        self.logger.info("✅ Service Account 권한 테스트 완료")
        return True
    
    def run_comprehensive_test(self, test_email: str):
        """종합 테스트 실행"""
        
        self.logger.info("🚀 Service Account 사용자 등록 종합 테스트 시작")
        self.logger.info("=" * 60)
        
        # 1. Service Account 권한 확인
        self.logger.info("\n1️⃣ Service Account 권한 확인")
        if not self.test_service_account_permissions():
            self.logger.error("❌ Service Account 권한 부족으로 테스트 중단")
            return
        
        # 2. 현재 사용자 목록 확인
        self.logger.info("\n2️⃣ 현재 사용자 목록 확인")
        current_users = self.test_current_users()
        
        # 3. 테스트 이메일이 이미 존재하는지 확인
        self.logger.info(f"\n3️⃣ {test_email} 기존 등록 여부 확인")
        email_exists = any(
            binding.user.replace("users/", "").lower() == test_email.lower()
            for binding in current_users
        )
        
        if email_exists:
            self.logger.info(f"⚠️ {test_email}은 이미 등록되어 있습니다")
        else:
            self.logger.info(f"✅ {test_email}은 등록되지 않았습니다")
        
        # 4. 직접 사용자 추가 시도
        self.logger.info(f"\n4️⃣ {test_email} 직접 추가 시도")
        success, result = self.test_direct_user_addition(test_email, "viewer")
        
        if success:
            self.logger.info(f"🎉 사용자 추가 성공!")
            
            # 추가 후 목록 재확인
            self.logger.info("\n5️⃣ 추가 후 사용자 목록 재확인")
            self.test_current_users()
            
            # 테스트 권한 삭제 (선택사항)
            delete_choice = input("\n테스트 권한을 삭제하시겠습니까? (y/n): ").strip().lower()
            if delete_choice == 'y':
                try:
                    self.client.delete_access_binding(name=result)
                    self.logger.info("🗑️ 테스트 권한 삭제 완료")
                except Exception as e:
                    self.logger.error(f"❌ 테스트 권한 삭제 실패: {e}")
        else:
            self.logger.error(f"❌ 사용자 추가 실패: {result}")
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🏁 종합 테스트 완료")

def main():
    """메인 실행 함수"""
    
    test_system = ServiceAccountUserRegistrationTest()
    
    print("🧪 Service Account 사용자 등록 API 테스트")
    print("=" * 50)
    
    # 테스트할 이메일 입력
    test_email = input("테스트할 이메일 주소를 입력하세요: ").strip()
    
    if not test_email:
        print("❌ 이메일 주소를 입력해주세요.")
        return
    
    # 종합 테스트 실행
    test_system.run_comprehensive_test(test_email)

if __name__ == "__main__":
    main() 