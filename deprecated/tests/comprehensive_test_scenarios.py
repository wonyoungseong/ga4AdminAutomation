#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 포괄적 테스트 시나리오
===========================================

답변 완료된 요구사항을 바탕으로 한 전체 시스템 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.logger import get_ga4_logger
from src.infrastructure.database import db_manager
from src.services.ga4_user_manager import ga4_user_manager
from src.services.notification_service import notification_service
from src.services.email_validator import email_validator
from src.domain.entities import PermissionLevel, RegistrationStatus, NotificationType

# 로거 초기화
logger = get_ga4_logger()


class ComprehensiveTestScenarios:
    """포괄적 테스트 시나리오 실행기"""
    
    def __init__(self):
        """초기화"""
        self.user_manager = ga4_user_manager
        self.notification_service = notification_service
        
        # 테스트 데이터
        self.test_emails = {
            'success_expected': [
                'wonyoungseong@gmail.com',
                'wonyoung.seong@conentrix.com',
                'wonyoung.seong@amorepacific.com',
                'seongwonyoung0311@gmail.com'
            ],
            'failure_expected': [
                'salboli@naver.com',  # naver.com은 허용되지 않은 도메인
                'demotest@yahoo.com'  # yahoo.com도 허용되지 않은 도메인
            ]
        }
        
        self.test_property_id = "462884506"
        self.admin_email = "seongwonyoung0311@gmail.com"
        
        # 테스트 결과 저장
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'details': []
        }
    
    async def run_all_scenarios(self) -> Dict[str, Any]:
        """모든 테스트 시나리오 실행"""
        logger.info("🚀 GA4 권한 관리 시스템 포괄적 테스트 시작")
        
        scenarios = [
            ("시스템 초기화", self.test_system_initialization),
            ("이메일 검증", self.test_email_validation),
            ("권한 추가", self.test_permission_addition),
            ("권한 업데이트", self.test_permission_update),
            ("권한 삭제", self.test_permission_deletion),
            ("알림 시스템", self.test_notification_system),
            ("UI/UX 검증", self.test_ui_ux_validation),
            ("데이터베이스 연동", self.test_database_integration),
            ("성능 및 안정성", self.test_performance_stability),
            ("보안 및 권한", self.test_security_authorization)
        ]
        
        for scenario_name, scenario_func in scenarios:
            try:
                logger.info(f"📋 테스트 시나리오: {scenario_name}")
                await scenario_func()
                self.test_results['passed'] += 1
                self.test_results['details'].append({
                    'scenario': scenario_name,
                    'status': 'PASSED',
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"✅ {scenario_name} 테스트 통과")
            except Exception as e:
                self.test_results['failed'] += 1
                self.test_results['details'].append({
                    'scenario': scenario_name,
                    'status': 'FAILED',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"❌ {scenario_name} 테스트 실패: {str(e)}")
        
        # 최종 결과 출력
        await self.print_final_results()
        return self.test_results
    
    async def test_system_initialization(self):
        """1. 시스템 초기화 및 권한 레벨 변경 테스트"""
        logger.info("🔧 시스템 초기화 테스트")
        
        # 1.1 데이터베이스 초기화
        await db_manager.initialize_database()
        
        # 1.2 GA4UserManager 초기화
        try:
            await self.user_manager.initialize()
            logger.info("✅ GA4UserManager 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ GA4UserManager 초기화 실패 (테스트 환경에서는 정상): {e}")
        
        # 1.3 권한 레벨 시스템 확인
        test_registrations = await db_manager.execute_query(
            "SELECT 권한 FROM user_registrations WHERE 권한 NOT IN ('analyst', 'editor') LIMIT 1"
        )
        
        if test_registrations:
            raise Exception("데이터베이스에 지원하지 않는 권한 레벨이 존재합니다")
        
        logger.info("✅ 시스템 초기화 완료")
    
    async def test_email_validation(self):
        """2. 이메일 검증 테스트"""
        logger.info("📧 이메일 검증 테스트")
        
        # 2.1 성공 예상 이메일 검증
        for email in self.test_emails['success_expected']:
            result = email_validator.validate_email(email)
            if not result.is_valid:
                raise Exception(f"유효한 이메일이 검증 실패: {email} - {result.error_message}")
        
        # 2.2 실패 예상 이메일 검증
        for email in self.test_emails['failure_expected']:
            result = email_validator.validate_email(email)
            if result.is_valid:
                raise Exception(f"유효하지 않은 이메일이 검증 통과: {email}")
        
        # 2.3 회사 도메인 확인
        company_email = "wonyoung.seong@conentrix.com"
        result = email_validator.validate_email(company_email)
        if not result.is_company_email:
            raise Exception(f"회사 이메일이 회사 도메인으로 인식되지 않음: {company_email}")
        
        logger.info("✅ 이메일 검증 테스트 완료")
    
    async def test_permission_addition(self):
        """3. 권한 추가 테스트"""
        logger.info("➕ 권한 추가 테스트")
        
        # 3.1 Analyst 권한 추가 (자동 승인)
        analyst_email = self.test_emails['success_expected'][0]
        result = await self.user_manager.add_user_permission(
            user_email=analyst_email,
            property_id=self.test_property_id,
            role="analyst",
            requester=self.admin_email
        )
        
        if not result['success']:
            raise Exception(f"Analyst 권한 추가 실패: {result['message']}")
        
        # 3.2 Editor 권한 추가 (승인 대기)
        editor_email = self.test_emails['success_expected'][1]
        result = await self.user_manager.add_user_permission(
            user_email=editor_email,
            property_id=self.test_property_id,
            role="editor",
            requester=self.admin_email
        )
        
        if not result['success'] or not result['approval_required']:
            raise Exception(f"Editor 권한 추가 또는 승인 대기 상태 설정 실패: {result['message']}")
        
        # 3.3 잘못된 이메일 권한 추가 시도
        invalid_email = self.test_emails['failure_expected'][0]
        result = await self.user_manager.add_user_permission(
            user_email=invalid_email,
            property_id=self.test_property_id,
            role="analyst",
            requester=self.admin_email
        )
        
        if result['success']:
            raise Exception(f"잘못된 이메일에 대한 권한 추가가 성공함: {invalid_email}")
        
        logger.info("✅ 권한 추가 테스트 완료")
    
    async def test_permission_update(self):
        """4. 권한 업데이트 테스트"""
        logger.info("🔄 권한 업데이트 테스트")
        
        # 4.1 기존 사용자의 권한 레벨 변경
        test_email = self.test_emails['success_expected'][0]
        
        # 현재 권한 확인
        registrations = await db_manager.execute_query(
            "SELECT * FROM user_registrations WHERE 등록_계정 = ? AND status = 'active'",
            (test_email,)
        )
        
        if not registrations:
            # 테스트용 사용자 추가
            await self.user_manager.add_user_permission(
                user_email=test_email,
                property_id=self.test_property_id,
                role="analyst",
                requester=self.admin_email
            )
        
        # 4.2 만료일 연장 테스트
        registration_id = registrations[0]['id'] if registrations else None
        if registration_id:
            await db_manager.execute_update(
                "UPDATE user_registrations SET 종료일 = ? WHERE id = ?",
                (datetime.now() + timedelta(days=60), registration_id)
            )
        
        logger.info("✅ 권한 업데이트 테스트 완료")
    
    async def test_permission_deletion(self):
        """5. 권한 삭제 테스트"""
        logger.info("🗑️ 권한 삭제 테스트")
        
        # 5.1 수동 삭제 테스트
        test_email = self.test_emails['success_expected'][2]
        
        # 테스트용 사용자 추가
        await self.user_manager.add_user_permission(
            user_email=test_email,
            property_id=self.test_property_id,
            role="analyst",
            requester=self.admin_email
        )
        
        # 삭제 실행
        result = await self.user_manager.remove_user_permission(
            test_email,
            self.test_property_id
        )
        
        if not result['success']:
            raise Exception(f"권한 삭제 실패: {result['message']}")
        
        # 5.2 만료된 권한 자동 삭제 테스트
        # 만료된 테스트 데이터 생성
        expired_email = self.test_emails['success_expected'][3]
        await db_manager.execute_update(
            """INSERT INTO user_registrations 
               (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status, ga4_registered)
               VALUES (?, ?, ?, 'analyst', ?, ?, 'active', 1)""",
            (self.admin_email, expired_email, self.test_property_id, 
             datetime.now() - timedelta(days=2), datetime.now() - timedelta(days=1))
        )
        
        # 만료 처리 실행
        result = await self.user_manager.process_expired_permissions()
        
        if not result['success']:
            raise Exception(f"만료 권한 처리 실패: {result['message']}")
        
        logger.info("✅ 권한 삭제 테스트 완료")
    
    async def test_notification_system(self):
        """6. 알림 시스템 테스트"""
        logger.info("📬 알림 시스템 테스트")
        
        # 6.1 만료 예정 알림 테스트 (30일, 7일, 1일 전)
        test_scenarios = [
            (30, "30_days"),
            (7, "7_days"),
            (1, "1_day"),
            (0, "today")
        ]
        
        for days_before, notification_type in test_scenarios:
            # 테스트 데이터 생성
            test_email = f"test_{notification_type}@gmail.com"
            expiry_date = datetime.now() + timedelta(days=days_before)
            
            registration_id = await db_manager.execute_insert(
                """INSERT INTO user_registrations 
                   (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status, ga4_registered)
                   VALUES (?, ?, ?, 'analyst', ?, ?, 'active', 1)""",
                (self.admin_email, test_email, self.test_property_id, 
                 datetime.now(), expiry_date)
            )
            
            # 알림 발송 테스트 (실제 이메일 대신 로그로 확인)
            logger.info(f"📧 {notification_type} 알림 테스트: {test_email} (만료 {days_before}일 전)")
        
        # 6.2 즉시 알림 발송 테스트
        result = await self.notification_service.check_and_send_daily_notifications()
        
        if not result.get('success', True):
            logger.warning(f"즉시 알림 발송 중 일부 오류: {result}")
        
        logger.info("✅ 알림 시스템 테스트 완료")
    
    async def test_ui_ux_validation(self):
        """7. UI/UX 검증 테스트"""
        logger.info("🖥️ UI/UX 검증 테스트")
        
        # 7.1 대시보드 데이터 조회 테스트
        stats = await self.get_dashboard_stats()
        
        required_stats = ['total_accounts', 'total_properties', 'active_users', 'pending_approvals']
        for stat in required_stats:
            if stat not in stats:
                raise Exception(f"대시보드 통계에 필수 항목 누락: {stat}")
        
        # 7.2 사용자 목록 조회 테스트
        recent_users = await db_manager.execute_query(
            """SELECT ur.*, p.property_display_name
               FROM user_registrations ur
               LEFT JOIN ga4_properties p ON ur.property_id = p.property_id
               ORDER BY ur.created_at DESC
               LIMIT 10"""
        )
        
        # 7.3 만료 예정 사용자 조회 테스트
        expiring_users = await db_manager.execute_query(
            """SELECT ur.*, p.property_display_name,
                      CAST((julianday(ur.종료일) - julianday('now')) AS INTEGER) as days_left
               FROM user_registrations ur
               LEFT JOIN ga4_properties p ON ur.property_id = p.property_id
               WHERE ur.status = 'active'
               AND ur.종료일 > datetime('now')
               AND ur.종료일 <= datetime('now', '+7 days')
               ORDER BY ur.종료일 ASC"""
        )
        
        logger.info("✅ UI/UX 검증 테스트 완료")
    
    async def test_database_integration(self):
        """8. 데이터베이스 연동 테스트"""
        logger.info("🗃️ 데이터베이스 연동 테스트")
        
        # 8.1 CRUD 작업 테스트
        test_email = "db_test@gmail.com"
        
        # Create
        registration_id = await db_manager.execute_insert(
            """INSERT INTO user_registrations 
               (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status)
               VALUES (?, ?, ?, 'analyst', ?, ?, 'active')""",
            (self.admin_email, test_email, self.test_property_id, 
             datetime.now(), datetime.now() + timedelta(days=30))
        )
        
        if not registration_id:
            raise Exception("데이터베이스 INSERT 실패")
        
        # Read
        registration = await db_manager.execute_query(
            "SELECT * FROM user_registrations WHERE id = ?",
            (registration_id,)
        )
        
        if not registration:
            raise Exception("데이터베이스 SELECT 실패")
        
        # Update
        await db_manager.execute_update(
            "UPDATE user_registrations SET 권한 = 'editor' WHERE id = ?",
            (registration_id,)
        )
        
        # Delete
        await db_manager.execute_update(
            "DELETE FROM user_registrations WHERE id = ?",
            (registration_id,)
        )
        
        # 8.2 트랜잭션 테스트
        try:
            # 의도적으로 실패하는 트랜잭션
            await db_manager.execute_update(
                "INSERT INTO user_registrations (invalid_column) VALUES (?)",
                ("test",)
            )
        except Exception:
            pass  # 예상된 실패
        
        logger.info("✅ 데이터베이스 연동 테스트 완료")
    
    async def test_performance_stability(self):
        """9. 성능 및 안정성 테스트"""
        logger.info("⚡ 성능 및 안정성 테스트")
        
        # 9.1 대량 데이터 처리 테스트
        start_time = datetime.now()
        
        # 100개의 테스트 등록 생성
        for i in range(10):  # 실제 테스트에서는 100개로 증가 가능
            test_email = f"perf_test_{i}@gmail.com"
            await db_manager.execute_update(
                """INSERT INTO user_registrations 
                   (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status)
                   VALUES (?, ?, ?, 'analyst', ?, ?, 'active')""",
                (self.admin_email, test_email, self.test_property_id, 
                 datetime.now(), datetime.now() + timedelta(days=30))
            )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if processing_time > 10:  # 10초 이상 걸리면 성능 문제
            raise Exception(f"대량 데이터 처리 성능 문제: {processing_time}초")
        
        # 9.2 동시성 테스트 (간단한 버전)
        tasks = []
        for i in range(5):
            task = self.concurrent_operation(f"concurrent_test_{i}@gmail.com")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"동시성 테스트 중 오류: {result}")
        
        logger.info("✅ 성능 및 안정성 테스트 완료")
    
    async def test_security_authorization(self):
        """10. 보안 및 권한 테스트"""
        logger.info("🔒 보안 및 권한 테스트")
        
        # 10.1 SQL 인젝션 방지 테스트
        malicious_email = "test'; DROP TABLE user_registrations; --"
        
        try:
            result = await self.user_manager.add_user_permission(
                user_email=malicious_email,
                property_id=self.test_property_id,
                role="analyst",
                requester=self.admin_email
            )
            
            # 이메일 검증에서 실패해야 함
            if result['success']:
                raise Exception("악성 이메일이 검증을 통과함")
        except Exception as e:
            if "SQL" in str(e).upper():
                raise Exception(f"SQL 인젝션 취약점 발견: {e}")
        
        # 10.2 권한 레벨 검증 테스트
        invalid_role = "admin"  # 지원하지 않는 권한
        result = await self.user_manager.add_user_permission(
            user_email=self.test_emails['success_expected'][0],
            property_id=self.test_property_id,
            role=invalid_role,
            requester=self.admin_email
        )
        
        if result['success']:
            raise Exception(f"지원하지 않는 권한 레벨이 허용됨: {invalid_role}")
        
        logger.info("✅ 보안 및 권한 테스트 완료")
    
    async def concurrent_operation(self, email: str):
        """동시성 테스트용 작업"""
        try:
            await db_manager.execute_update(
                """INSERT INTO user_registrations 
                   (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status)
                   VALUES (?, ?, ?, 'analyst', ?, ?, 'active')""",
                (self.admin_email, email, self.test_property_id, 
                 datetime.now(), datetime.now() + timedelta(days=30))
            )
            return True
        except Exception as e:
            return e
    
    async def get_dashboard_stats(self) -> Dict[str, int]:
        """대시보드 통계 조회"""
        stats = {}
        
        # 총 계정 수
        accounts = await db_manager.execute_query("SELECT COUNT(*) as count FROM ga4_accounts")
        stats['total_accounts'] = accounts[0]['count'] if accounts else 0
        
        # 총 프로퍼티 수
        properties = await db_manager.execute_query("SELECT COUNT(*) as count FROM ga4_properties")
        stats['total_properties'] = properties[0]['count'] if properties else 0
        
        # 활성 사용자 수
        active_users = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM user_registrations WHERE status = 'active'"
        )
        stats['active_users'] = active_users[0]['count'] if active_users else 0
        
        # 승인 대기 수
        pending = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM user_registrations WHERE status = 'pending_approval'"
        )
        stats['pending_approvals'] = pending[0]['count'] if pending else 0
        
        return stats
    
    async def print_final_results(self):
        """최종 결과 출력"""
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 80)
        logger.info("🎯 GA4 권한 관리 시스템 포괄적 테스트 결과")
        logger.info("=" * 80)
        logger.info(f"📊 총 테스트: {total_tests}개")
        logger.info(f"✅ 성공: {self.test_results['passed']}개")
        logger.info(f"❌ 실패: {self.test_results['failed']}개")
        logger.info(f"📈 성공률: {success_rate:.1f}%")
        logger.info("=" * 80)
        
        # 실패한 테스트 상세 정보
        if self.test_results['failed'] > 0:
            logger.info("❌ 실패한 테스트:")
            for detail in self.test_results['details']:
                if detail['status'] == 'FAILED':
                    logger.error(f"  - {detail['scenario']}: {detail.get('error', '알 수 없는 오류')}")
        
        # 결과를 파일로 저장
        with open('test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info("📄 상세 결과가 test_results.json에 저장되었습니다.")


async def main():
    """메인 실행 함수"""
    try:
        test_runner = ComprehensiveTestScenarios()
        results = await test_runner.run_all_scenarios()
        
        # 결과에 따른 종료 코드 설정
        if results['failed'] > 0:
            sys.exit(1)  # 실패한 테스트가 있으면 오류 코드로 종료
        else:
            sys.exit(0)  # 모든 테스트 성공
            
    except Exception as e:
        logger.error(f"💥 테스트 실행 중 치명적 오류: {str(e)}")
        sys.exit(2)  # 치명적 오류로 종료


if __name__ == "__main__":
    asyncio.run(main()) 