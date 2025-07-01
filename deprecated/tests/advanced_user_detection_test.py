#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 사용자 감지 및 분석 테스트
============================

사용자가 GA4에 로그인했는데도 API에서 찾을 수 없는 이유를 분석합니다.
다양한 API 엔드포인트와 방법을 시도해봅니다.
"""

import json
import logging
import time
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, Account, Property
from google.oauth2 import service_account

class AdvancedUserDetectionTest:
    """고급 사용자 감지 테스트"""
    
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
    
    def test_all_accounts_access(self):
        """모든 계정에 대한 접근 테스트"""
        
        self.logger.info("🔍 모든 계정 접근 테스트")
        
        try:
            # 모든 계정 나열
            accounts = self.client.list_accounts()
            account_list = list(accounts)
            
            self.logger.info(f"📊 총 {len(account_list)}개의 계정 발견:")
            
            for i, account in enumerate(account_list, 1):
                self.logger.info(f"   {i}. {account.display_name}")
                self.logger.info(f"      - Account ID: {account.name}")
                self.logger.info(f"      - Region Code: {account.region_code}")
                
                # 각 계정의 사용자 확인
                try:
                    bindings = self.client.list_access_bindings(parent=account.name)
                    binding_list = list(bindings)
                    
                    self.logger.info(f"      - 사용자 수: {len(binding_list)}명")
                    
                    for binding in binding_list:
                        user_email = binding.user.replace("users/", "")
                        self.logger.info(f"        👤 {user_email}")
                        
                except Exception as e:
                    self.logger.error(f"      - 사용자 목록 조회 실패: {e}")
            
            return account_list
            
        except Exception as e:
            self.logger.error(f"❌ 계정 목록 조회 실패: {e}")
            return []
    
    def test_property_level_access(self):
        """Property 레벨 접근 테스트"""
        
        self.logger.info("🏢 Property 레벨 접근 테스트")
        
        account_name = f"accounts/{self.config['account_id']}"
        
        try:
            # Property 목록 조회
            properties = self.client.list_properties(filter=f"parent:{account_name}")
            property_list = list(properties)
            
            self.logger.info(f"📊 총 {len(property_list)}개의 Property 발견:")
            
            for i, property_obj in enumerate(property_list, 1):
                self.logger.info(f"   {i}. {property_obj.display_name}")
                self.logger.info(f"      - Property ID: {property_obj.name}")
                self.logger.info(f"      - Property Type: {property_obj.property_type}")
                
                # TODO: Property 레벨 사용자 권한은 GA4에서 지원하지 않을 수 있음
                
            return property_list
            
        except Exception as e:
            self.logger.error(f"❌ Property 목록 조회 실패: {e}")
            return []
    
    def test_user_registration_methods(self, email: str):
        """다양한 사용자 등록 방법 테스트"""
        
        self.logger.info(f"🧪 {email} 다양한 등록 방법 테스트")
        
        account_name = f"accounts/{self.config['account_id']}"
        
        # 방법 1: 기본 Viewer 권한
        self.logger.info("📝 방법 1: 기본 Viewer 권한")
        result1 = self._try_add_user(account_name, email, "predefinedRoles/read")
        
        # 방법 2: Editor 권한
        self.logger.info("📝 방법 2: Editor 권한")
        result2 = self._try_add_user(account_name, email, "predefinedRoles/edit")
        
        # 방법 3: Admin 권한
        self.logger.info("📝 방법 3: Admin 권한")  
        result3 = self._try_add_user(account_name, email, "predefinedRoles/admin")
        
        # 방법 4: 다른 형식의 사용자 ID 시도
        self.logger.info("📝 방법 4: 다른 형식의 사용자 ID")
        
        # Gmail 주소를 다양한 형식으로 시도
        email_variations = [
            email,
            email.lower(),
            email.upper(),
            email.replace('@gmail.com', '@googlemail.com')  # Gmail 별칭
        ]
        
        for variation in email_variations:
            self.logger.info(f"   시도: {variation}")
            result = self._try_add_user(account_name, variation, "predefinedRoles/read")
            if result:
                return True
        
        return False
    
    def _try_add_user(self, account_name: str, email: str, role: str) -> bool:
        """사용자 추가 시도"""
        try:
            access_binding = AccessBinding(
                user=f"users/{email}",
                roles=[role]
            )
            
            result = self.client.create_access_binding(
                parent=account_name,
                access_binding=access_binding
            )
            
            self.logger.info(f"   ✅ 성공! 바인딩 ID: {result.name}")
            
            # 즉시 삭제 (테스트용)
            try:
                self.client.delete_access_binding(name=result.name)
                self.logger.info(f"   🗑️ 테스트 권한 삭제 완료")
            except:
                self.logger.warning(f"   ⚠️ 테스트 권한 삭제 실패")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            if "404" in error_msg:
                self.logger.info(f"   ❌ 404: 사용자 찾을 수 없음")
            elif "403" in error_msg:
                self.logger.info(f"   ❌ 403: 권한 부족")
            elif "409" in error_msg:
                self.logger.info(f"   ❌ 409: 이미 존재함")
            else:
                self.logger.info(f"   ❌ 기타: {error_msg}")
            
            return False
    
    def test_user_sync_delay(self, email: str, max_attempts: int = 10):
        """사용자 동기화 지연 테스트"""
        
        self.logger.info(f"⏰ {email} 동기화 지연 테스트 (최대 {max_attempts}회)")
        
        account_name = f"accounts/{self.config['account_id']}"
        
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"시도 {attempt}/{max_attempts}")
            
            # 현재 사용자 목록 확인
            try:
                bindings = self.client.list_access_bindings(parent=account_name)
                
                found_user = False
                for binding in bindings:
                    user_email = binding.user.replace("users/", "")
                    if user_email.lower() == email.lower():
                        self.logger.info(f"✅ {email} 발견됨!")
                        return True
                
                self.logger.info(f"❌ {email} 아직 찾을 수 없음")
                
                # 직접 추가 시도
                result = self._try_add_user(account_name, email, "predefinedRoles/read")
                if result:
                    return True
                
                # 30초 대기
                if attempt < max_attempts:
                    self.logger.info("⏳ 30초 대기 중...")
                    time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"시도 {attempt} 실패: {e}")
        
        self.logger.error(f"❌ {max_attempts}번 시도 후에도 {email}을 찾을 수 없습니다")
        return False
    
    def test_google_account_types(self, email: str):
        """Google 계정 유형별 테스트"""
        
        self.logger.info(f"👤 {email} Google 계정 유형 분석")
        
        # Gmail 계정 여부 확인
        if '@gmail.com' in email.lower():
            self.logger.info("📧 Gmail 개인 계정으로 감지됨")
            
            # Gmail 계정 특별 처리
            self.logger.info("💡 Gmail 계정 특별 요구사항:")
            self.logger.info("   1. Google Analytics에 최소 1번 로그인")
            self.logger.info("   2. 해당 Analytics 속성에 직접 접근")
            self.logger.info("   3. '홈' 화면까지 완전히 로드")
            self.logger.info("   4. 브라우저 세션이 활성 상태여야 함")
            
        elif '@googlemail.com' in email.lower():
            self.logger.info("📧 GoogleMail 계정으로 감지됨")
            
        else:
            self.logger.info("🏢 조직 계정으로 감지됨")
            self.logger.info("💡 조직 계정은 추가 제약이 있을 수 있습니다")
    
    def comprehensive_analysis(self, target_email: str):
        """종합 분석"""
        
        self.logger.info("🔬 종합 분석 시작")
        self.logger.info("=" * 80)
        
        # 1. 모든 계정 접근 테스트
        self.logger.info("\n1️⃣ 모든 계정 접근 테스트")
        accounts = self.test_all_accounts_access()
        
        # 2. Property 레벨 접근 테스트
        self.logger.info("\n2️⃣ Property 레벨 접근 테스트")
        properties = self.test_property_level_access()
        
        # 3. Google 계정 유형 분석
        self.logger.info("\n3️⃣ Google 계정 유형 분석")
        self.test_google_account_types(target_email)
        
        # 4. 다양한 등록 방법 테스트
        self.logger.info("\n4️⃣ 다양한 등록 방법 테스트")
        success = self.test_user_registration_methods(target_email)
        
        if not success:
            # 5. 동기화 지연 테스트
            self.logger.info("\n5️⃣ 동기화 지연 테스트")
            self.test_user_sync_delay(target_email, max_attempts=3)
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🏁 종합 분석 완료")

def main():
    """메인 실행 함수"""
    
    test_system = AdvancedUserDetectionTest()
    
    print("🔬 고급 사용자 감지 및 분석 테스트")
    print("=" * 50)
    
    target_email = input("분석할 이메일 주소: ").strip()
    
    if not target_email:
        print("❌ 이메일 주소를 입력해주세요.")
        return
    
    # 종합 분석 실행
    test_system.comprehensive_analysis(target_email)

if __name__ == "__main__":
    main() 