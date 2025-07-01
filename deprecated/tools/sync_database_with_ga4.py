#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스와 GA4 동기화 스크립트
==============================

데이터베이스의 ga4_registered 플래그를 실제 GA4 상태와 동기화
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


class DatabaseSynchronizer:
    """데이터베이스 동기화 클래스"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        
    async def sync_database_with_ga4(self):
        """데이터베이스를 실제 GA4 상태와 동기화"""
        self.logger.info("🔄 데이터베이스와 GA4 동기화 시작")
        
        try:
            # 1. 시스템 초기화
            await self._initialize_systems()
            
            # 2. 활성 등록 기록 조회
            await self._sync_active_registrations()
            
            # 3. 동기화 결과 확인
            await self._verify_sync_results()
            
        except Exception as e:
            self.logger.error(f"❌ 동기화 중 오류: {e}")
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
    
    async def _sync_active_registrations(self):
        """활성 등록 기록 동기화"""
        self.logger.info("🔄 활성 등록 기록 동기화 중...")
        
        try:
            # 활성 상태인 모든 등록 기록 조회
            active_registrations = await db_manager.execute_query(
                """SELECT ur.*, p.property_display_name
                   FROM user_registrations ur
                   JOIN ga4_properties p ON ur.property_id = p.property_id
                   WHERE ur.status = 'active'
                   ORDER BY ur.신청일 DESC"""
            )
            
            self.logger.info(f"📋 동기화 대상: {len(active_registrations)}건")
            
            sync_count = 0
            update_count = 0
            
            for registration in active_registrations:
                try:
                    email = registration['등록_계정']
                    property_id = registration['property_id']
                    property_name = registration['property_display_name']
                    registration_id = registration['id']
                    current_ga4_registered = registration.get('ga4_registered', 0)
                    
                    self.logger.info(f"🔍 확인 중: {email} -> {property_name}")
                    
                    # 실제 GA4에서 사용자 확인
                    users = await ga4_user_manager.list_property_users(property_id)
                    
                    # 해당 사용자가 GA4에 등록되어 있는지 확인
                    user_found = False
                    user_binding_name = None
                    
                    for user in users:
                        if user.get('email', '').lower() == email.lower():
                            user_found = True
                            user_binding_name = user.get('name')
                            break
                    
                    # 데이터베이스 상태와 실제 GA4 상태 비교
                    if user_found and current_ga4_registered == 0:
                        # GA4에는 있지만 데이터베이스에는 등록되지 않음으로 표시
                        await db_manager.execute_query(
                            """UPDATE user_registrations 
                               SET ga4_registered = 1, user_link_name = ?, updated_at = ?
                               WHERE id = ?""",
                            (user_binding_name, datetime.now(), registration_id)
                        )
                        self.logger.info(f"✅ 동기화 완료: {email} -> {property_name} (GA4에 등록됨)")
                        update_count += 1
                        
                    elif not user_found and current_ga4_registered == 1:
                        # GA4에는 없지만 데이터베이스에는 등록됨으로 표시
                        await db_manager.execute_query(
                            """UPDATE user_registrations 
                               SET ga4_registered = 0, user_link_name = NULL, updated_at = ?
                               WHERE id = ?""",
                            (datetime.now(), registration_id)
                        )
                        self.logger.warning(f"⚠️ 동기화 완료: {email} -> {property_name} (GA4에서 제거됨)")
                        update_count += 1
                        
                    elif user_found and current_ga4_registered == 1:
                        # 이미 동기화됨
                        self.logger.info(f"✓ 이미 동기화됨: {email} -> {property_name}")
                        
                    else:
                        # GA4에도 없고 데이터베이스에도 등록되지 않음으로 표시
                        self.logger.info(f"- 등록 필요: {email} -> {property_name}")
                    
                    sync_count += 1
                    
                    # API 제한을 위한 대기
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"❌ 동기화 실패 {email}: {e}")
            
            self.logger.info(f"✅ 동기화 완료: {sync_count}건 확인, {update_count}건 업데이트")
            
        except Exception as e:
            self.logger.error(f"❌ 활성 등록 기록 동기화 실패: {e}")
    
    async def _verify_sync_results(self):
        """동기화 결과 확인"""
        self.logger.info("🔍 동기화 결과 확인 중...")
        
        try:
            # 동기화 후 통계
            stats = await db_manager.execute_query(
                """SELECT 
                   COUNT(*) as total,
                   SUM(CASE WHEN ga4_registered = 1 THEN 1 ELSE 0 END) as ga4_registered,
                   SUM(CASE WHEN ga4_registered = 0 THEN 1 ELSE 0 END) as not_registered
                   FROM user_registrations 
                   WHERE status = 'active'"""
            )
            
            if stats:
                stat = stats[0]
                self.logger.info("📊 동기화 후 통계:")
                self.logger.info(f"  - 총 활성 등록: {stat['total']}건")
                self.logger.info(f"  - GA4 등록됨: {stat['ga4_registered']}건")
                self.logger.info(f"  - GA4 미등록: {stat['not_registered']}건")
            
            # seongwonyoung0311@gmail.com 상태 확인
            seongwonyoung_records = await db_manager.execute_query(
                """SELECT ur.*, p.property_display_name
                   FROM user_registrations ur
                   JOIN ga4_properties p ON ur.property_id = p.property_id
                   WHERE ur.등록_계정 = 'seongwonyoung0311@gmail.com'
                   AND ur.status = 'active'"""
            )
            
            self.logger.info("🎯 seongwonyoung0311@gmail.com 동기화 결과:")
            for record in seongwonyoung_records:
                ga4_status = "등록됨" if record.get('ga4_registered', 0) else "미등록"
                self.logger.info(f"  - {record['property_display_name']}: {ga4_status}")
                
        except Exception as e:
            self.logger.error(f"❌ 동기화 결과 확인 실패: {e}")


async def main():
    """메인 실행 함수"""
    synchronizer = DatabaseSynchronizer()
    
    try:
        print("=" * 80)
        print("🔄 데이터베이스와 GA4 동기화 시작")
        print("=" * 80)
        
        await synchronizer.sync_database_with_ga4()
        
        print("\n" + "=" * 80)
        print("✅ 동기화 완료")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 동기화 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 