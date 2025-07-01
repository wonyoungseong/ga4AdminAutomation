#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 GA4 권한 관리 테스트
======================

실제 GA4 API를 통한 사용자 등록/삭제 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath('.'))

from src.core.logger import get_ga4_logger
from src.services.ga4_user_manager import ga4_user_manager
from src.infrastructure.database import db_manager
from src.services.property_scanner_service import GA4PropertyScannerService


class RealPermissionTester:
    """실제 권한 관리 테스트 클래스"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        self.test_results = []
        self.property_scanner = GA4PropertyScannerService()
        
        # 테스트 계정 정보
        self.existing_accounts = [
            "wonyoung.seong@concentrix.com",
            "wonyoung.seong@amorepacific.com"
        ]
        
        self.new_accounts = [
            "wonyoungseong@concentrix.com", 
            "wonyoungseong@amorepacific.com"
        ]
        
    async def run_comprehensive_test(self):
        """포괄적인 권한 관리 테스트 실행"""
        self.logger.info("🚀 실제 GA4 권한 관리 테스트 시작")
        
        try:
            # 1. 시스템 초기화
            await self._initialize_systems()
            
            # 2. 현재 프로퍼티 상태 확인
            await self._check_current_properties()
            
            # 3. 기존 사용자 권한 상태 확인
            await self._check_existing_users()
            
            # 4. 새 사용자 등록 테스트
            await self._test_new_user_registration()
            
            # 5. 사용자 제거 테스트
            await self._test_user_removal()
            
            # 6. 권한 변경 테스트
            await self._test_permission_changes()
            
            # 7. 에러 케이스 테스트
            await self._test_error_cases()
            
            # 8. 최종 상태 확인
            await self._final_status_check()
            
            # 9. 테스트 결과 출력
            self._print_test_results()
            
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
            
            self._add_result("시스템 초기화", True, "모든 시스템 정상 초기화")
            
        except Exception as e:
            self._add_result("시스템 초기화", False, f"초기화 실패: {e}")
            raise
    
    async def _check_current_properties(self):
        """현재 프로퍼티 상태 확인"""
        self.logger.info("🔍 현재 프로퍼티 상태 확인 중...")
        
        try:
            # 프로퍼티 스캔
            await self.property_scanner.scan_all_accounts_and_properties()
            
            # 데이터베이스에서 프로퍼티 목록 조회
            properties = await db_manager.execute_query(
                "SELECT * FROM ga4_properties WHERE 등록_가능여부 = 1 ORDER BY property_display_name"
            )
            
            self.logger.info(f"📊 발견된 프로퍼티: {len(properties)}개")
            
            for prop in properties:
                self.logger.info(f"  - {prop['property_display_name']} (ID: {prop['property_id']})")
            
            self._add_result("프로퍼티 스캔", True, f"{len(properties)}개 프로퍼티 발견")
            
            # 첫 번째 프로퍼티를 테스트용으로 사용
            if properties:
                self.test_property_id = properties[0]['property_id']
                self.test_property_name = properties[0]['property_display_name']
                self.logger.info(f"🎯 테스트 대상 프로퍼티: {self.test_property_name} ({self.test_property_id})")
            else:
                raise Exception("테스트할 프로퍼티가 없습니다")
                
        except Exception as e:
            self._add_result("프로퍼티 스캔", False, f"스캔 실패: {e}")
            raise
    
    async def _check_existing_users(self):
        """기존 사용자 권한 상태 확인"""
        self.logger.info("👥 기존 사용자 권한 상태 확인 중...")
        
        try:
            users = await ga4_user_manager.list_property_users(self.test_property_id)
            
            self.logger.info(f"📊 현재 등록된 사용자: {len(users)}명")
            
            existing_emails = []
            for user in users:
                email = user.get('email', 'Unknown')
                roles = user.get('roles', [])
                self.logger.info(f"  - {email}: {', '.join(roles)}")
                existing_emails.append(email)
            
            # 테스트 계정 중 이미 등록된 계정 확인
            already_registered = []
            for email in self.existing_accounts + self.new_accounts:
                if email in existing_emails:
                    already_registered.append(email)
            
            if already_registered:
                self.logger.info(f"⚠️ 이미 등록된 테스트 계정: {', '.join(already_registered)}")
            
            self._add_result("기존 사용자 확인", True, f"{len(users)}명 사용자 확인")
            
        except Exception as e:
            self._add_result("기존 사용자 확인", False, f"확인 실패: {e}")
            self.logger.error(f"❌ 기존 사용자 확인 실패: {e}")
    
    async def _test_new_user_registration(self):
        """새 사용자 등록 테스트"""
        self.logger.info("➕ 새 사용자 등록 테스트 시작...")
        
        # 각 테스트 계정에 대해 등록 테스트
        for email in self.new_accounts:
            await self._test_single_user_registration(email, "viewer")
            await asyncio.sleep(1)  # API 제한 고려
    
    async def _test_single_user_registration(self, email: str, role: str):
        """단일 사용자 등록 테스트"""
        try:
            self.logger.info(f"🔄 사용자 등록 테스트: {email} ({role})")
            
            success, message, binding_name = await ga4_user_manager.register_user_to_property(
                property_id=self.test_property_id,
                email=email,
                role=role
            )
            
            if success:
                self.logger.info(f"✅ 등록 성공: {email}")
                self._add_result(f"사용자 등록 ({email})", True, message)
                
                # 등록 후 확인
                await asyncio.sleep(2)
                users = await ga4_user_manager.list_property_users(self.test_property_id)
                user_found = any(u.get('email') == email for u in users)
                
                if user_found:
                    self.logger.info(f"✅ 등록 확인 완료: {email}")
                    self._add_result(f"등록 확인 ({email})", True, "사용자 목록에서 확인됨")
                else:
                    self.logger.warning(f"⚠️ 등록 확인 실패: {email}")
                    self._add_result(f"등록 확인 ({email})", False, "사용자 목록에서 확인되지 않음")
                
            else:
                self.logger.error(f"❌ 등록 실패: {email} - {message}")
                self._add_result(f"사용자 등록 ({email})", False, message)
                
        except Exception as e:
            self.logger.error(f"❌ 등록 테스트 오류: {email} - {e}")
            self._add_result(f"사용자 등록 ({email})", False, f"테스트 오류: {e}")
    
    async def _test_user_removal(self):
        """사용자 제거 테스트"""
        self.logger.info("➖ 사용자 제거 테스트 시작...")
        
        # 방금 등록한 사용자들 제거
        for email in self.new_accounts:
            await self._test_single_user_removal(email)
            await asyncio.sleep(1)  # API 제한 고려
    
    async def _test_single_user_removal(self, email: str):
        """단일 사용자 제거 테스트"""
        try:
            self.logger.info(f"🔄 사용자 제거 테스트: {email}")
            
            success, message = await ga4_user_manager.remove_user_from_property(
                property_id=self.test_property_id,
                email=email
            )
            
            if success:
                self.logger.info(f"✅ 제거 성공: {email}")
                self._add_result(f"사용자 제거 ({email})", True, message)
                
                # 제거 후 확인
                await asyncio.sleep(2)
                users = await ga4_user_manager.list_property_users(self.test_property_id)
                user_found = any(u.get('email') == email for u in users)
                
                if not user_found:
                    self.logger.info(f"✅ 제거 확인 완료: {email}")
                    self._add_result(f"제거 확인 ({email})", True, "사용자 목록에서 제거됨")
                else:
                    self.logger.warning(f"⚠️ 제거 확인 실패: {email}")
                    self._add_result(f"제거 확인 ({email})", False, "사용자가 여전히 목록에 있음")
                
            else:
                self.logger.error(f"❌ 제거 실패: {email} - {message}")
                self._add_result(f"사용자 제거 ({email})", False, message)
                
        except Exception as e:
            self.logger.error(f"❌ 제거 테스트 오류: {email} - {e}")
            self._add_result(f"사용자 제거 ({email})", False, f"테스트 오류: {e}")
    
    async def _test_permission_changes(self):
        """권한 변경 테스트"""
        self.logger.info("🔄 권한 변경 테스트 시작...")
        
        test_email = self.new_accounts[0]  # 첫 번째 계정으로 테스트
        
        try:
            # 1. viewer로 등록
            self.logger.info(f"1️⃣ {test_email}을 viewer로 등록")
            success, message, binding_name = await ga4_user_manager.register_user_to_property(
                self.test_property_id, test_email, "viewer"
            )
            
            if success:
                self._add_result("권한 변경 - viewer 등록", True, message)
                await asyncio.sleep(2)
                
                # 2. analyst로 변경 (기존 제거 후 재등록)
                self.logger.info(f"2️⃣ {test_email}을 analyst로 변경")
                
                # 기존 권한 제거
                await ga4_user_manager.remove_user_from_property(
                    self.test_property_id, test_email
                )
                await asyncio.sleep(2)
                
                # 새 권한으로 등록
                success2, message2, _ = await ga4_user_manager.register_user_to_property(
                    self.test_property_id, test_email, "analyst"
                )
                
                if success2:
                    self._add_result("권한 변경 - analyst 변경", True, message2)
                    
                    # 3. 최종 정리 - 제거
                    await asyncio.sleep(2)
                    await ga4_user_manager.remove_user_from_property(
                        self.test_property_id, test_email
                    )
                    self._add_result("권한 변경 - 정리", True, "테스트 완료 후 제거")
                    
                else:
                    self._add_result("권한 변경 - analyst 변경", False, message2)
            else:
                self._add_result("권한 변경 - viewer 등록", False, message)
                
        except Exception as e:
            self._add_result("권한 변경 테스트", False, f"테스트 오류: {e}")
    
    async def _test_error_cases(self):
        """에러 케이스 테스트"""
        self.logger.info("⚠️ 에러 케이스 테스트 시작...")
        
        try:
            # 1. 잘못된 이메일 주소
            self.logger.info("1️⃣ 잘못된 이메일 주소 테스트")
            success, message, _ = await ga4_user_manager.register_user_to_property(
                self.test_property_id, "invalid-email", "viewer"
            )
            
            if not success:
                self._add_result("에러 케이스 - 잘못된 이메일", True, "예상대로 실패")
            else:
                self._add_result("에러 케이스 - 잘못된 이메일", False, "예상과 다르게 성공")
            
            # 2. 존재하지 않는 프로퍼티
            self.logger.info("2️⃣ 존재하지 않는 프로퍼티 테스트")
            success, message, _ = await ga4_user_manager.register_user_to_property(
                "999999999", self.new_accounts[0], "viewer"
            )
            
            if not success:
                self._add_result("에러 케이스 - 잘못된 프로퍼티", True, "예상대로 실패")
            else:
                self._add_result("에러 케이스 - 잘못된 프로퍼티", False, "예상과 다르게 성공")
            
            # 3. 존재하지 않는 사용자 제거
            self.logger.info("3️⃣ 존재하지 않는 사용자 제거 테스트")
            success, message = await ga4_user_manager.remove_user_from_property(
                self.test_property_id, "nonexistent@example.com"
            )
            
            if not success:
                self._add_result("에러 케이스 - 존재하지 않는 사용자 제거", True, "예상대로 실패")
            else:
                self._add_result("에러 케이스 - 존재하지 않는 사용자 제거", False, "예상과 다르게 성공")
                
        except Exception as e:
            self._add_result("에러 케이스 테스트", False, f"테스트 오류: {e}")
    
    async def _final_status_check(self):
        """최종 상태 확인"""
        self.logger.info("🔍 최종 상태 확인 중...")
        
        try:
            users = await ga4_user_manager.list_property_users(self.test_property_id)
            
            self.logger.info(f"📊 최종 사용자 수: {len(users)}명")
            
            for user in users:
                email = user.get('email', 'Unknown')
                roles = user.get('roles', [])
                self.logger.info(f"  - {email}: {', '.join(roles)}")
            
            # 테스트 계정이 정리되었는지 확인
            test_accounts_remaining = []
            for email in self.new_accounts:
                if any(u.get('email') == email for u in users):
                    test_accounts_remaining.append(email)
            
            if test_accounts_remaining:
                self.logger.warning(f"⚠️ 정리되지 않은 테스트 계정: {', '.join(test_accounts_remaining)}")
                self._add_result("최종 정리 확인", False, f"정리되지 않은 계정: {len(test_accounts_remaining)}개")
            else:
                self.logger.info("✅ 모든 테스트 계정이 정리되었습니다")
                self._add_result("최종 정리 확인", True, "모든 테스트 계정 정리 완료")
                
        except Exception as e:
            self._add_result("최종 상태 확인", False, f"확인 실패: {e}")
    
    def _add_result(self, test_name: str, success: bool, message: str):
        """테스트 결과 추가"""
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now()
        })
    
    def _print_test_results(self):
        """테스트 결과 출력"""
        self.logger.info("\n" + "="*80)
        self.logger.info("📋 실제 GA4 권한 관리 테스트 결과")
        self.logger.info("="*80)
        
        success_count = 0
        total_count = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ 성공" if result['success'] else "❌ 실패"
            self.logger.info(f"{status} | {result['test_name']}: {result['message']}")
            if result['success']:
                success_count += 1
        
        self.logger.info("-"*80)
        self.logger.info(f"📊 전체 결과: {success_count}/{total_count} 성공 ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            self.logger.info("🎉 모든 테스트가 성공했습니다!")
        else:
            self.logger.warning(f"⚠️ {total_count - success_count}개 테스트가 실패했습니다.")
        
        self.logger.info("="*80)


async def main():
    """메인 실행 함수"""
    tester = RealPermissionTester()
    
    try:
        await tester.run_comprehensive_test()
        
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 