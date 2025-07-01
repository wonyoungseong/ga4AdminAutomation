#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
존재하는 사용자 권한 관리 테스트
==============================

실제 존재하는 계정으로 GA4 권한 등록/삭제 테스트
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath('.'))

from src.core.logger import get_ga4_logger
from src.services.ga4_user_manager import ga4_user_manager
from src.infrastructure.database import db_manager


class ExistingUserTester:
    """존재하는 사용자 권한 테스트 클래스"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        
        # 존재하는 테스트 계정
        self.existing_accounts = [
            "wonyoung.seong@concentrix.com",
            "wonyoung.seong@amorepacific.com"
        ]
        
    async def test_existing_users(self):
        """존재하는 사용자 권한 테스트"""
        self.logger.info("🚀 존재하는 사용자 권한 관리 테스트 시작")
        
        try:
            # 1. 시스템 초기화
            await self._initialize_systems()
            
            # 2. 테스트 프로퍼티 설정
            await self._setup_test_property()
            
            # 3. 현재 사용자 목록 확인
            await self._check_current_users()
            
            # 4. 존재하는 사용자 등록 테스트
            await self._test_existing_user_registration()
            
            # 5. 등록 확인
            await self._verify_registration()
            
            # 6. 사용자 제거 테스트
            await self._test_user_removal()
            
            # 7. 제거 확인
            await self._verify_removal()
            
        except Exception as e:
            self.logger.error(f"❌ 테스트 실행 중 오류: {e}")
            raise
    
    async def _initialize_systems(self):
        """시스템 초기화"""
        self.logger.info("📋 시스템 초기화 중...")
        
        try:
            # 데이터베이스 초기화
            await db_manager.initialize_database()
            
            # GA4 사용자 관리자 초기화
            await ga4_user_manager.initialize()
            
            self.logger.info("✅ 시스템 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 초기화 실패: {e}")
            raise
    
    async def _setup_test_property(self):
        """테스트 프로퍼티 설정"""
        self.logger.info("🔍 테스트 프로퍼티 설정 중...")
        
        try:
            # 데이터베이스에서 프로퍼티 목록 조회
            properties = await db_manager.execute_query(
                "SELECT * FROM ga4_properties WHERE 등록_가능여부 = 1 ORDER BY property_display_name"
            )
            
            if properties:
                self.test_property_id = properties[0]['property_id']
                self.test_property_name = properties[0]['property_display_name']
                self.logger.info(f"🎯 테스트 대상 프로퍼티: {self.test_property_name} ({self.test_property_id})")
            else:
                raise Exception("테스트할 프로퍼티가 없습니다")
                
        except Exception as e:
            self.logger.error(f"❌ 프로퍼티 설정 실패: {e}")
            raise
    
    async def _check_current_users(self):
        """현재 사용자 목록 확인"""
        self.logger.info("👥 현재 사용자 권한 상태 확인 중...")
        
        try:
            users = await ga4_user_manager.list_property_users(self.test_property_id)
            
            self.logger.info(f"📊 현재 등록된 사용자: {len(users)}명")
            
            for user in users:
                email = user.get('email', 'Unknown')
                roles = user.get('roles', [])
                self.logger.info(f"  - {email}: {', '.join(roles)}")
                
        except Exception as e:
            self.logger.error(f"❌ 사용자 목록 확인 실패: {e}")
    
    async def _test_existing_user_registration(self):
        """존재하는 사용자 등록 테스트"""
        self.logger.info("➕ 존재하는 사용자 등록 테스트 시작...")
        
        for email in self.existing_accounts:
            await self._test_single_registration(email)
            await asyncio.sleep(2)  # API 제한 고려
    
    async def _test_single_registration(self, email: str):
        """단일 사용자 등록 테스트"""
        try:
            self.logger.info(f"🔄 사용자 등록 테스트: {email}")
            
            success, message, binding_name = await ga4_user_manager.register_user_to_property(
                property_id=self.test_property_id,
                email=email,
                role="viewer"
            )
            
            if success:
                self.logger.info(f"✅ 등록 성공: {email}")
                self.logger.info(f"📋 바인딩 이름: {binding_name}")
            else:
                self.logger.error(f"❌ 등록 실패: {email} - {message}")
                
        except Exception as e:
            self.logger.error(f"❌ 등록 테스트 오류: {email} - {e}")
    
    async def _verify_registration(self):
        """등록 확인"""
        self.logger.info("🔍 등록 확인 중...")
        
        try:
            await asyncio.sleep(3)  # API 반영 대기
            
            users = await ga4_user_manager.list_property_users(self.test_property_id)
            
            self.logger.info(f"📊 등록 후 사용자 수: {len(users)}명")
            
            registered_emails = []
            for user in users:
                email = user.get('email', 'Unknown')
                roles = user.get('roles', [])
                self.logger.info(f"  - {email}: {', '.join(roles)}")
                registered_emails.append(email)
            
            # 테스트 계정이 등록되었는지 확인
            for email in self.existing_accounts:
                if email in registered_emails:
                    self.logger.info(f"✅ 등록 확인됨: {email}")
                else:
                    self.logger.warning(f"⚠️ 등록 확인되지 않음: {email}")
                    
        except Exception as e:
            self.logger.error(f"❌ 등록 확인 실패: {e}")
    
    async def _test_user_removal(self):
        """사용자 제거 테스트"""
        self.logger.info("➖ 사용자 제거 테스트 시작...")
        
        for email in self.existing_accounts:
            await self._test_single_removal(email)
            await asyncio.sleep(2)  # API 제한 고려
    
    async def _test_single_removal(self, email: str):
        """단일 사용자 제거 테스트"""
        try:
            self.logger.info(f"🔄 사용자 제거 테스트: {email}")
            
            success, message = await ga4_user_manager.remove_user_from_property(
                property_id=self.test_property_id,
                email=email
            )
            
            if success:
                self.logger.info(f"✅ 제거 성공: {email}")
            else:
                self.logger.error(f"❌ 제거 실패: {email} - {message}")
                
        except Exception as e:
            self.logger.error(f"❌ 제거 테스트 오류: {email} - {e}")
    
    async def _verify_removal(self):
        """제거 확인"""
        self.logger.info("🔍 제거 확인 중...")
        
        try:
            await asyncio.sleep(3)  # API 반영 대기
            
            users = await ga4_user_manager.list_property_users(self.test_property_id)
            
            self.logger.info(f"📊 제거 후 사용자 수: {len(users)}명")
            
            remaining_emails = []
            for user in users:
                email = user.get('email', 'Unknown')
                roles = user.get('roles', [])
                self.logger.info(f"  - {email}: {', '.join(roles)}")
                remaining_emails.append(email)
            
            # 테스트 계정이 제거되었는지 확인
            for email in self.existing_accounts:
                if email not in remaining_emails:
                    self.logger.info(f"✅ 제거 확인됨: {email}")
                else:
                    self.logger.warning(f"⚠️ 제거 확인되지 않음: {email}")
                    
        except Exception as e:
            self.logger.error(f"❌ 제거 확인 실패: {e}")


async def main():
    """메인 실행 함수"""
    tester = ExistingUserTester()
    
    try:
        await tester.test_existing_users()
        
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 