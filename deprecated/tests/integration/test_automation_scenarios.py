#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 - 자동화 기능 테스트
=======================================

날짜를 조작하여 다양한 자동화 시나리오를 테스트합니다:
1. 만료 알림 테스트 (30일, 7일, 1일, 당일)
2. Editor 권한 자동 다운그레이드 테스트 (7일 후)
3. 만료 사용자 자동 삭제 테스트
4. 스케줄러 통합 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sqlite3

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath('.'))

from src.core.logger import get_ga4_logger
from src.infrastructure.database import db_manager
from src.services.notification_service import notification_service
from src.services.ga4_user_manager import ga4_user_manager
from src.api.scheduler import GA4SchedulerService


class AutomationTester:
    """자동화 기능 테스트 클래스"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        self.test_property_id = "462884506"  # 테스트용 프로퍼티
        self.test_emails = [
            "automation.test1@concentrix.com",
            "automation.test2@concentrix.com", 
            "automation.test3@concentrix.com"
        ]
        self.original_data = []  # 원본 데이터 백업용
        
    async def setup_test_data(self):
        """테스트 데이터 설정"""
        self.logger.info("🔧 테스트 데이터 설정 시작")
        
        # 기존 테스트 데이터 정리
        await self._cleanup_test_data()
        
        # 현재 시간 기준으로 다양한 시나리오 데이터 생성
        now = datetime.now()
        
        test_scenarios = [
            {
                "email": self.test_emails[0],
                "role": "viewer",
                "created_at": now - timedelta(days=35),  # 35일 전 생성 (만료 5일 지남)
                "expires_at": now - timedelta(days=5),   # 5일 전 만료
                "status": "active",
                "description": "만료된 사용자 (자동 삭제 대상)"
            },
            {
                "email": self.test_emails[1], 
                "role": "editor",
                "created_at": now - timedelta(days=8),   # 8일 전 생성
                "expires_at": now + timedelta(days=22),  # 22일 후 만료
                "status": "active",
                "description": "Editor 권한 다운그레이드 대상 (7일 경과)"
            },
            {
                "email": self.test_emails[2],
                "role": "viewer", 
                "created_at": now - timedelta(days=23),  # 23일 전 생성
                "expires_at": now + timedelta(days=7),   # 7일 후 만료
                "status": "active",
                "description": "7일 만료 알림 대상"
            }
        ]
        
        # 추가 시나리오 데이터
        additional_scenarios = [
            {
                "email": "test.30day@concentrix.com",
                "role": "viewer",
                "created_at": now,
                "expires_at": now + timedelta(days=30),  # 30일 후 만료
                "status": "active", 
                "description": "30일 만료 알림 대상"
            },
            {
                "email": "test.1day@concentrix.com",
                "role": "analyst",
                "created_at": now - timedelta(days=29),
                "expires_at": now + timedelta(days=1),   # 1일 후 만료
                "status": "active",
                "description": "1일 만료 알림 대상"
            },
            {
                "email": "test.today@concentrix.com", 
                "role": "viewer",
                "created_at": now - timedelta(days=30),
                "expires_at": now,                       # 오늘 만료
                "status": "active",
                "description": "당일 만료 알림 대상"
            }
        ]
        
        test_scenarios.extend(additional_scenarios)
        
        # 데이터베이스에 테스트 데이터 삽입
        for scenario in test_scenarios:
            await self._insert_test_registration(scenario)
            self.logger.info(f"📝 테스트 데이터 생성: {scenario['email']} - {scenario['description']}")
        
        self.logger.info(f"✅ {len(test_scenarios)}개 테스트 시나리오 데이터 생성 완료")
        
    async def _insert_test_registration(self, scenario: Dict[str, Any]):
        """테스트 등록 데이터 삽입"""
        query = """
        INSERT INTO user_registrations (
            신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status,
            ga4_registered, user_link_name, last_notification_sent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await db_manager.execute_insert(
            query,
            (
                "테스트시스템",  # 신청자
                scenario["email"],  # 등록_계정
                self.test_property_id,
                scenario["role"],  # 권한
                scenario["created_at"].strftime("%Y-%m-%d %H:%M:%S"),  # 신청일
                scenario["expires_at"].strftime("%Y-%m-%d %H:%M:%S"),  # 종료일
                scenario["status"],
                0,  # ga4_registered = False (테스트용)
                None,  # user_link_name
                None   # last_notification_sent
            )
        )
    
    async def test_expiry_notifications(self):
        """만료 알림 기능 테스트"""
        self.logger.info("📧 만료 알림 기능 테스트 시작")
        
        try:
            # 만료 알림 처리 실행
            result = await notification_service.process_expiry_notifications()
            
            self.logger.info("📊 만료 알림 처리 결과:")
            for notification_type, count in result.items():
                self.logger.info(f"   - {notification_type}: {count}건")
            
            # 알림 로그 확인
            await self._check_notification_logs()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 만료 알림 테스트 실패: {e}")
            return False
    
    async def test_editor_downgrade(self):
        """Editor 권한 다운그레이드 테스트"""
        self.logger.info("⬇️ Editor 권한 다운그레이드 테스트 시작")
        
        try:
            # Editor 권한 다운그레이드 처리 실행
            downgraded_count = await ga4_user_manager.process_editor_downgrade()
            
            self.logger.info(f"📊 다운그레이드 처리 결과: {downgraded_count}명")
            
            # 다운그레이드된 사용자 확인
            await self._check_downgraded_users()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Editor 다운그레이드 테스트 실패: {e}")
            return False
    
    async def test_expiration_cleanup(self):
        """만료 사용자 자동 삭제 테스트"""
        self.logger.info("🗑️ 만료 사용자 자동 삭제 테스트 시작")
        
        try:
            # 만료 사용자 삭제 처리 실행
            deleted_count = await ga4_user_manager.process_expiration_queue()
            
            self.logger.info(f"📊 삭제 처리 결과: {deleted_count}명")
            
            # 삭제된 사용자 확인
            await self._check_deleted_users()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 만료 사용자 삭제 테스트 실패: {e}")
            return False
    
    async def test_scheduler_integration(self):
        """스케줄러 통합 테스트"""
        self.logger.info("⏰ 스케줄러 통합 테스트 시작")
        
        try:
            scheduler = GA4SchedulerService()
            
            # 각 작업 개별 실행 테스트
            self.logger.info("🔄 개별 작업 실행 테스트")
            
            # 1. 만료 알림 확인
            await scheduler.check_expiry_warnings()
            self.logger.info("✅ 만료 알림 확인 작업 완료")
            
            # 2. Editor 다운그레이드
            downgraded_count = await scheduler.process_editor_downgrade()
            self.logger.info(f"✅ Editor 다운그레이드 작업 완료: {downgraded_count}명")
            
            # 3. 만료 사용자 삭제
            await scheduler.process_expired_users()
            self.logger.info("✅ 만료 사용자 삭제 작업 완료")
            
            # 4. 시스템 상태 체크
            await scheduler.health_check()
            self.logger.info("✅ 시스템 상태 체크 완료")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 스케줄러 통합 테스트 실패: {e}")
            return False
    
    async def _check_notification_logs(self):
        """알림 로그 확인"""
        query = """
        SELECT sent_to, notification_type, sent_at
        FROM notification_logs 
        WHERE sent_at >= datetime('now', '-1 hour')
        ORDER BY sent_at DESC
        """
        
        logs = await db_manager.execute_query(query)
        
        self.logger.info("📋 최근 알림 로그:")
        for log in logs:
            self.logger.info(f"   - {log['sent_to']}: {log['notification_type']} ({log['sent_at']})")
    
    async def _check_downgraded_users(self):
        """다운그레이드된 사용자 확인"""
        query = """
        SELECT 등록_계정, 권한, 신청일, 종료일
        FROM user_registrations 
        WHERE 등록_계정 LIKE '%test%' AND 권한 = 'viewer'
        AND 신청일 < datetime('now', '-7 days')
        """
        
        users = await db_manager.execute_query(query)
        
        self.logger.info("📋 다운그레이드된 사용자:")
        for user in users:
            self.logger.info(f"   - {user['등록_계정']}: {user['권한']} (생성: {user['신청일']})")
    
    async def _check_deleted_users(self):
        """삭제된 사용자 확인"""
        query = """
        SELECT 등록_계정, status, 종료일
        FROM user_registrations 
        WHERE 등록_계정 LIKE '%test%' AND status = 'expired'
        """
        
        users = await db_manager.execute_query(query)
        
        self.logger.info("📋 삭제 처리된 사용자:")
        for user in users:
            self.logger.info(f"   - {user['등록_계정']}: {user['status']} (만료: {user['종료일']})")
    
    async def _cleanup_test_data(self):
        """테스트 데이터 정리"""
        query = """
        DELETE FROM user_registrations 
        WHERE 등록_계정 LIKE '%test%' OR 등록_계정 LIKE '%automation%'
        """
        
        await db_manager.execute_update(query)
        
        # 알림 로그도 정리
        query = """
        DELETE FROM notification_logs 
        WHERE sent_to LIKE '%test%' OR sent_to LIKE '%automation%'
        """
        
        await db_manager.execute_update(query)
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        self.logger.info("🚀 GA4 권한 관리 시스템 자동화 기능 테스트 시작")
        self.logger.info("=" * 60)
        
        test_results = {}
        
        try:
            # 1. 테스트 데이터 설정
            await self.setup_test_data()
            
            # 2. 만료 알림 테스트
            test_results['expiry_notifications'] = await self.test_expiry_notifications()
            
            # 3. Editor 다운그레이드 테스트
            test_results['editor_downgrade'] = await self.test_editor_downgrade()
            
            # 4. 만료 사용자 삭제 테스트
            test_results['expiration_cleanup'] = await self.test_expiration_cleanup()
            
            # 5. 스케줄러 통합 테스트
            test_results['scheduler_integration'] = await self.test_scheduler_integration()
            
            # 결과 요약
            self.logger.info("=" * 60)
            self.logger.info("📊 테스트 결과 요약:")
            
            passed = 0
            total = len(test_results)
            
            for test_name, result in test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                self.logger.info(f"   - {test_name}: {status}")
                if result:
                    passed += 1
            
            self.logger.info(f"📈 전체 결과: {passed}/{total} 테스트 통과")
            
            if passed == total:
                self.logger.info("🎉 모든 자동화 기능 테스트 성공!")
            else:
                self.logger.warning(f"⚠️ {total - passed}개 테스트 실패")
            
        except Exception as e:
            self.logger.error(f"❌ 테스트 실행 중 오류 발생: {e}")
            
        finally:
            # 테스트 데이터 정리
            await self._cleanup_test_data()
            self.logger.info("🧹 테스트 데이터 정리 완료")


async def main():
    """메인 실행 함수"""
    tester = AutomationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 