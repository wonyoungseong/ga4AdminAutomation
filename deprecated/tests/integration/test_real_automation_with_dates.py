#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 - 실제 권한 등록/삭제 자동화 테스트
====================================================

실제 GA4 계정을 사용하여 날짜를 조작한 자동화 시나리오를 테스트합니다:
1. 실제 사용자를 GA4에 등록
2. 데이터베이스 날짜를 조작하여 만료 상황 시뮬레이션
3. 자동화 프로세스 실행하여 실제 권한 삭제 확인
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath('.'))

from src.core.logger import get_ga4_logger
from src.infrastructure.database import db_manager
from src.services.notification_service import notification_service
from src.services.ga4_user_manager import ga4_user_manager
from src.api.scheduler import GA4SchedulerService


class RealAutomationTester:
    """실제 권한 등록/삭제 자동화 테스트 클래스"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        self.test_property_id = "462884506"  # [Edu]Ecommerce - Beauty Cosmetic
        self.test_user = "wonyoung.seong@concentrix.com"  # 실제 존재하는 계정
        self.registration_id = None
        
    async def setup_real_test_user(self):
        """실제 테스트 사용자를 GA4에 등록"""
        self.logger.info(f"👤 실제 테스트 사용자 설정: {self.test_user}")
        
        try:
            # 1. 기존 등록 정보 정리
            await self._cleanup_test_user()
            
            # 2. GA4에 실제 사용자 등록
            success, message, binding_name = await ga4_user_manager.register_user_to_property(
                property_id=self.test_property_id,
                email=self.test_user,
                role="viewer"
            )
            
            if not success:
                raise Exception(f"GA4 사용자 등록 실패: {message}")
            
            self.logger.info(f"✅ GA4 사용자 등록 성공: {self.test_user}")
            
            # 3. 데이터베이스에 등록 정보 저장 (과거 날짜로 조작)
            past_date = datetime.now() - timedelta(days=10)  # 10일 전 등록으로 설정
            expiry_date = datetime.now() - timedelta(days=2)  # 2일 전 만료로 설정
            
            query = """
            INSERT INTO user_registrations (
                신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status,
                ga4_registered, user_link_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.registration_id = await db_manager.execute_insert(
                query,
                (
                    "자동화테스트",  # 신청자
                    self.test_user,  # 등록_계정
                    self.test_property_id,
                    "viewer",  # 권한
                    past_date.strftime("%Y-%m-%d %H:%M:%S"),  # 신청일 (과거)
                    expiry_date.strftime("%Y-%m-%d %H:%M:%S"),  # 종료일 (과거 = 만료됨)
                    "active",
                    1,  # ga4_registered = True (실제 등록됨)
                    binding_name  # user_link_name
                )
            )
            
            self.logger.info(f"✅ 데이터베이스 등록 완료 (만료된 상태로 설정)")
            self.logger.info(f"   - 등록일: {past_date.strftime('%Y-%m-%d %H:%M')}")
            self.logger.info(f"   - 만료일: {expiry_date.strftime('%Y-%m-%d %H:%M')} (이미 만료됨)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 실제 테스트 사용자 설정 실패: {e}")
            return False
    
    async def test_automatic_expiry_deletion(self):
        """자동 만료 삭제 테스트"""
        self.logger.info("🗑️ 자동 만료 삭제 테스트 시작")
        
        try:
            # 1. 현재 GA4 사용자 수 확인
            initial_count = await self._count_ga4_users()
            self.logger.info(f"📊 삭제 전 GA4 사용자 수: {initial_count}명")
            
            # 2. 만료 사용자 자동 삭제 실행
            scheduler = GA4SchedulerService()
            await scheduler.process_expired_users()
            
            # 3. 삭제 후 GA4 사용자 수 확인
            final_count = await self._count_ga4_users()
            self.logger.info(f"📊 삭제 후 GA4 사용자 수: {final_count}명")
            
            # 4. 결과 확인
            if final_count < initial_count:
                self.logger.info(f"✅ 자동 삭제 성공: {initial_count - final_count}명 삭제됨")
                
                # 5. 데이터베이스 상태 확인
                await self._check_database_status()
                
                return True
            else:
                self.logger.warning(f"⚠️ GA4 사용자 수 변화 없음 (삭제되지 않음)")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 자동 만료 삭제 테스트 실패: {e}")
            return False
    
    async def test_editor_downgrade_scenario(self):
        """Editor 권한 다운그레이드 시나리오 테스트"""
        self.logger.info("⬇️ Editor 권한 다운그레이드 시나리오 테스트")
        
        try:
            # 1. 새로운 Editor 사용자 등록
            editor_email = "wonyoung.seong@amorepacific.com"  # 다른 실제 계정
            
            # 기존 등록 정리
            await self._cleanup_specific_user(editor_email)
            
            # GA4에 Editor 권한으로 등록
            success, message, binding_name = await ga4_user_manager.register_user_to_property(
                property_id=self.test_property_id,
                email=editor_email,
                role="editor"
            )
            
            if not success:
                raise Exception(f"Editor 등록 실패: {message}")
            
            self.logger.info(f"✅ Editor 권한 등록 성공: {editor_email}")
            
            # 2. 데이터베이스에 8일 전 등록으로 설정
            old_date = datetime.now() - timedelta(days=8)  # 8일 전 등록
            future_expiry = datetime.now() + timedelta(days=22)  # 22일 후 만료
            
            query = """
            INSERT INTO user_registrations (
                신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status,
                ga4_registered, user_link_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await db_manager.execute_insert(
                query,
                (
                    "자동화테스트",
                    editor_email,
                    self.test_property_id,
                    "editor",
                    old_date.strftime("%Y-%m-%d %H:%M:%S"),
                    future_expiry.strftime("%Y-%m-%d %H:%M:%S"),
                    "active",
                    1,
                    binding_name
                )
            )
            
            self.logger.info(f"✅ Editor 사용자 데이터베이스 등록 완료 (8일 전 등록으로 설정)")
            
            # 3. 현재 GA4에서 권한 확인
            current_role = await self._check_user_role(editor_email)
            self.logger.info(f"📊 다운그레이드 전 권한: {current_role}")
            
            # 4. Editor 다운그레이드 실행
            scheduler = GA4SchedulerService()
            downgraded_count = await scheduler.process_editor_downgrade()
            
            self.logger.info(f"📊 다운그레이드 처리 결과: {downgraded_count}명")
            
            # 5. 다운그레이드 후 권한 확인
            new_role = await self._check_user_role(editor_email)
            self.logger.info(f"📊 다운그레이드 후 권한: {new_role}")
            
            # 6. 결과 검증
            if current_role == "editor" and new_role == "viewer":
                self.logger.info("✅ Editor → Viewer 다운그레이드 성공!")
                
                # 정리: 테스트 사용자 삭제
                await ga4_user_manager.remove_user_from_property(
                    property_id=self.test_property_id,
                    email=editor_email,
                    binding_name=binding_name
                )
                await self._cleanup_specific_user(editor_email)
                
                return True
            else:
                self.logger.warning(f"⚠️ 다운그레이드 실패 또는 미실행: {current_role} → {new_role}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Editor 다운그레이드 테스트 실패: {e}")
            return False
    
    async def _count_ga4_users(self) -> int:
        """GA4 프로퍼티의 현재 사용자 수 확인"""
        try:
            # GA4 API를 통해 현재 AccessBinding 수 조회
            from google.analytics.admin_v1alpha.types import ListAccessBindingsRequest
            
            request = ListAccessBindingsRequest(
                parent=f"properties/{self.test_property_id}"
            )
            
            response = ga4_user_manager.ga4_core.client.list_access_bindings(request=request)
            
            count = 0
            for binding in response:
                count += 1
            
            return count
            
        except Exception as e:
            self.logger.error(f"❌ GA4 사용자 수 확인 실패: {e}")
            return 0
    
    async def _check_user_role(self, email: str) -> str:
        """특정 사용자의 GA4 권한 확인"""
        try:
            from google.analytics.admin_v1alpha.types import ListAccessBindingsRequest
            
            request = ListAccessBindingsRequest(
                parent=f"properties/{self.test_property_id}"
            )
            
            response = ga4_user_manager.ga4_core.client.list_access_bindings(request=request)
            
            for binding in response:
                if binding.user == f"users/{email}":
                    for role in binding.roles:
                        if "predefinedRoles/read" in role:
                            return "viewer"
                        elif "predefinedRoles/edit" in role:
                            return "editor"
                        elif "predefinedRoles/collaborate" in role:
                            return "analyst"
            
            return "없음"
            
        except Exception as e:
            self.logger.error(f"❌ 사용자 권한 확인 실패: {e}")
            return "오류"
    
    async def _check_database_status(self):
        """데이터베이스 상태 확인"""
        query = """
        SELECT 등록_계정, status, ga4_registered, 종료일
        FROM user_registrations 
        WHERE 등록_계정 = ?
        """
        
        result = await db_manager.execute_query(query, (self.test_user,))
        
        if result:
            user = result[0]
            self.logger.info("📋 데이터베이스 상태:")
            self.logger.info(f"   - 계정: {user['등록_계정']}")
            self.logger.info(f"   - 상태: {user['status']}")
            self.logger.info(f"   - GA4 등록: {user['ga4_registered']}")
            self.logger.info(f"   - 만료일: {user['종료일']}")
        else:
            self.logger.info("📋 데이터베이스에서 사용자 정보를 찾을 수 없습니다")
    
    async def _cleanup_test_user(self):
        """테스트 사용자 정리"""
        await self._cleanup_specific_user(self.test_user)
    
    async def _cleanup_specific_user(self, email: str):
        """특정 사용자 정리"""
        # 데이터베이스에서 삭제
        query = "DELETE FROM user_registrations WHERE 등록_계정 = ?"
        await db_manager.execute_update(query, (email,))
        
        # 알림 로그에서도 삭제
        query = "DELETE FROM notification_logs WHERE sent_to = ?"
        await db_manager.execute_update(query, (email,))
    
    async def run_real_automation_test(self):
        """실제 자동화 테스트 실행"""
        self.logger.info("🚀 실제 GA4 권한 자동화 테스트 시작")
        self.logger.info("=" * 60)
        
        test_results = {}
        
        try:
            # 1. 실제 테스트 사용자 설정
            setup_success = await self.setup_real_test_user()
            if not setup_success:
                self.logger.error("❌ 테스트 사용자 설정 실패로 테스트 중단")
                return
            
            # 2. 자동 만료 삭제 테스트
            test_results['expiry_deletion'] = await self.test_automatic_expiry_deletion()
            
            # 3. Editor 다운그레이드 테스트
            test_results['editor_downgrade'] = await self.test_editor_downgrade_scenario()
            
            # 결과 요약
            self.logger.info("=" * 60)
            self.logger.info("📊 실제 자동화 테스트 결과:")
            
            passed = 0
            total = len(test_results)
            
            for test_name, result in test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                self.logger.info(f"   - {test_name}: {status}")
                if result:
                    passed += 1
            
            self.logger.info(f"📈 전체 결과: {passed}/{total} 테스트 통과")
            
            if passed == total:
                self.logger.info("🎉 모든 실제 자동화 테스트 성공!")
            else:
                self.logger.warning(f"⚠️ {total - passed}개 테스트 실패")
            
        except Exception as e:
            self.logger.error(f"❌ 실제 자동화 테스트 실행 중 오류: {e}")
            
        finally:
            # 테스트 데이터 정리
            await self._cleanup_test_user()
            self.logger.info("🧹 테스트 데이터 정리 완료")


async def main():
    """메인 실행 함수"""
    tester = RealAutomationTester()
    await tester.run_real_automation_test()


if __name__ == "__main__":
    asyncio.run(main()) 