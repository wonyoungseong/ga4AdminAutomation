#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 GA4 권한 검증 스크립트
========================

웹에서 등록한 사용자가 실제 GA4에 반영되었는지 확인
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


class PermissionVerifier:
    """권한 검증 클래스"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        
    async def verify_permissions(self):
        """실제 권한 상태 검증"""
        self.logger.info("🔍 실제 GA4 권한 상태 검증 시작")
        
        try:
            # 1. 시스템 초기화
            await self._initialize_systems()
            
            # 2. 데이터베이스에서 등록 기록 확인
            await self._check_database_records()
            
            # 3. 실제 GA4에서 사용자 목록 확인
            await self._check_actual_ga4_users()
            
            # 4. 특정 사용자 검증
            await self._verify_specific_user("seongwonyoung0311@gmail.com")
            
        except Exception as e:
            self.logger.error(f"❌ 검증 중 오류: {e}")
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
    
    async def _check_database_records(self):
        """데이터베이스 등록 기록 확인"""
        self.logger.info("📊 데이터베이스 등록 기록 확인 중...")
        
        try:
            # 최근 등록 기록 조회
            recent_registrations = await db_manager.execute_query(
                """SELECT ur.*, p.property_display_name
                   FROM user_registrations ur
                   JOIN ga4_properties p ON ur.property_id = p.property_id
                   WHERE ur.등록_계정 = 'seongwonyoung0311@gmail.com'
                   ORDER BY ur.신청일 DESC"""
            )
            
            self.logger.info(f"📋 seongwonyoung0311@gmail.com 등록 기록: {len(recent_registrations)}건")
            
            for record in recent_registrations:
                self.logger.info(f"  - 프로퍼티: {record['property_display_name']}")
                self.logger.info(f"  - 권한: {record['권한']}")
                self.logger.info(f"  - 상태: {record['status']}")
                self.logger.info(f"  - GA4 등록됨: {'예' if record.get('ga4_registered', 0) else '아니오'}")
                self.logger.info(f"  - 바인딩 이름: {record.get('user_link_name', 'N/A')}")
                self.logger.info(f"  - 등록일: {record['신청일']}")
                self.logger.info("  ---")
                
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 기록 확인 실패: {e}")
    
    async def _check_actual_ga4_users(self):
        """실제 GA4에서 사용자 목록 확인"""
        self.logger.info("🔍 실제 GA4 사용자 목록 확인 중...")
        
        try:
            # 프로퍼티 목록 조회
            properties = await db_manager.execute_query(
                "SELECT * FROM ga4_properties WHERE 등록_가능여부 = 1 ORDER BY property_display_name"
            )
            
            for prop in properties:
                property_id = prop['property_id']
                property_name = prop['property_display_name']
                
                self.logger.info(f"📋 프로퍼티: {property_name} ({property_id})")
                
                # 실제 GA4에서 사용자 목록 조회
                users = await ga4_user_manager.list_property_users(property_id)
                
                self.logger.info(f"👥 현재 등록된 사용자: {len(users)}명")
                
                seongwonyoung_found = False
                for user in users:
                    email = user.get('email', 'Unknown')
                    roles = user.get('roles', [])
                    
                    if 'seongwonyoung0311@gmail.com' in email.lower():
                        seongwonyoung_found = True
                        self.logger.info(f"✅ 발견: {email} - 권한: {', '.join(roles)}")
                    else:
                        self.logger.info(f"  - {email}: {', '.join(roles)}")
                
                if not seongwonyoung_found:
                    self.logger.warning(f"⚠️ seongwonyoung0311@gmail.com이 {property_name}에서 발견되지 않음")
                
                self.logger.info("  ---")
                
        except Exception as e:
            self.logger.error(f"❌ GA4 사용자 목록 확인 실패: {e}")
    
    async def _verify_specific_user(self, email: str):
        """특정 사용자 검증"""
        self.logger.info(f"🎯 특정 사용자 검증: {email}")
        
        try:
            # 모든 프로퍼티에서 해당 사용자 검색
            properties = await db_manager.execute_query(
                "SELECT * FROM ga4_properties WHERE 등록_가능여부 = 1"
            )
            
            total_found = 0
            
            for prop in properties:
                property_id = prop['property_id']
                property_name = prop['property_display_name']
                
                users = await ga4_user_manager.list_property_users(property_id)
                
                for user in users:
                    if user.get('email', '').lower() == email.lower():
                        total_found += 1
                        self.logger.info(f"✅ {property_name}에서 발견:")
                        self.logger.info(f"   - 이메일: {user.get('email')}")
                        self.logger.info(f"   - 권한: {', '.join(user.get('roles', []))}")
                        self.logger.info(f"   - 바인딩: {user.get('name')}")
            
            if total_found == 0:
                self.logger.error(f"❌ {email}이 어떤 프로퍼티에서도 발견되지 않음")
                self.logger.info("🔍 가능한 원인:")
                self.logger.info("   1. 실제로 등록되지 않음")
                self.logger.info("   2. 등록 후 삭제됨")
                self.logger.info("   3. 다른 이메일로 등록됨")
                self.logger.info("   4. GA4 API 동기화 지연")
            else:
                self.logger.info(f"✅ 총 {total_found}개 프로퍼티에서 발견됨")
                
        except Exception as e:
            self.logger.error(f"❌ 특정 사용자 검증 실패: {e}")
    
    async def test_manual_registration(self, email: str, property_id: str):
        """수동 등록 테스트"""
        self.logger.info(f"🧪 수동 등록 테스트: {email} -> {property_id}")
        
        try:
            # 1. 등록 전 상태 확인
            self.logger.info("1️⃣ 등록 전 상태 확인")
            users_before = await ga4_user_manager.list_property_users(property_id)
            self.logger.info(f"등록 전 사용자 수: {len(users_before)}명")
            
            # 2. 실제 등록 시도
            self.logger.info("2️⃣ 실제 등록 시도")
            success, message, binding_name = await ga4_user_manager.register_user_to_property(
                property_id=property_id,
                email=email,
                role="viewer"
            )
            
            if success:
                self.logger.info(f"✅ 등록 성공: {message}")
                self.logger.info(f"📋 바인딩 이름: {binding_name}")
            else:
                self.logger.error(f"❌ 등록 실패: {message}")
                return
            
            # 3. 등록 후 상태 확인
            self.logger.info("3️⃣ 등록 후 상태 확인 (3초 대기 후)")
            await asyncio.sleep(3)
            
            users_after = await ga4_user_manager.list_property_users(property_id)
            self.logger.info(f"등록 후 사용자 수: {len(users_after)}명")
            
            # 4. 등록된 사용자 확인
            found = False
            for user in users_after:
                if user.get('email', '').lower() == email.lower():
                    found = True
                    self.logger.info(f"✅ 등록 확인: {user.get('email')} - {', '.join(user.get('roles', []))}")
                    break
            
            if not found:
                self.logger.error(f"❌ 등록 후에도 {email}을 찾을 수 없음")
            
        except Exception as e:
            self.logger.error(f"❌ 수동 등록 테스트 실패: {e}")


async def main():
    """메인 실행 함수"""
    verifier = PermissionVerifier()
    
    try:
        print("=" * 80)
        print("🔍 GA4 권한 검증 시작")
        print("=" * 80)
        
        # 1. 기본 검증
        await verifier.verify_permissions()
        
        print("\n" + "=" * 80)
        print("🧪 수동 등록 테스트")
        print("=" * 80)
        
        # 2. 수동 등록 테스트 (첫 번째 프로퍼티)
        properties = await db_manager.execute_query(
            "SELECT * FROM ga4_properties WHERE 등록_가능여부 = 1 LIMIT 1"
        )
        
        if properties:
            await verifier.test_manual_registration(
                "seongwonyoung0311@gmail.com",
                properties[0]['property_id']
            )
        
        print("\n" + "=" * 80)
        print("✅ 검증 완료")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 검증 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 