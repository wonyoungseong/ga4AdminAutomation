#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 자동 스케줄링 서비스
===============================

자동화된 작업들을 스케줄링하여 실행하는 서비스
- 만료 알림 발송
- Editor 권한 자동 다운그레이드 (7일 후)
- 만료된 사용자 자동 삭제
- 시스템 상태 모니터링
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import schedule
import time
from threading import Thread

from ..core.logger import get_ga4_logger
from ..services.notifications.notification_service import notification_service
from ..services.ga4_user_manager import GA4UserManager
from ..infrastructure.database import DatabaseManager


class GA4Scheduler:
    """GA4 권한 관리 스케줄러"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        self.notification_service = notification_service
        self.ga4_user_manager = GA4UserManager()
        self.db_manager = DatabaseManager()
        self.is_running = False
        self.scheduler_thread = None
        
    async def initialize(self):
        """스케줄러 초기화"""
        try:
            self.logger.info("🔧 GA4 스케줄러 초기화 중...")
            
            # 데이터베이스 초기화
            await self.db_manager.initialize_database()
            
            # 알림 서비스 초기화
            await self.notification_service.initialize()
            
            # GA4 사용자 관리자 초기화
            await self.ga4_user_manager.initialize()
            
            # 스케줄 설정
            self._schedule_jobs()
            
            self.logger.info("✅ GA4 스케줄러 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"❌ GA4 스케줄러 초기화 실패: {e}")
            raise
        
    async def process_expiry_queue(self) -> Dict[str, int]:
        """만료된 사용자 권한 자동 삭제"""
        try:
            self.logger.info("🔄 만료 사용자 권한 삭제 프로세스 시작...")
            
            # 만료된 사용자 조회
            expired_users = await self.db_manager.execute_query(
                """SELECT ur.*, p.property_display_name as property_name, a.account_display_name as account_name
                   FROM user_registrations ur
                   JOIN ga4_properties p ON ur.property_id = p.property_id
                   JOIN ga4_accounts a ON p.account_id = a.account_id
                   WHERE ur.status = 'active' 
                   AND ur.종료일 <= datetime('now')
                   AND ur.ga4_registered = 1"""
            )
            
            results = {"removed": 0, "failed": 0, "notified": 0}
            
            for user in expired_users:
                try:
                    user_id = user.get('id')
                    user_email = user.get('등록_계정')
                    property_id = user.get('property_id')
                    user_link_name = user.get('user_link_name')
                    
                    # GA4에서 사용자 권한 삭제
                    if user_link_name:
                        success = await self.ga4_user_manager.remove_user_from_property(
                            property_id, user_link_name
                        )
                    else:
                        # user_link_name이 없는 경우 이메일로 찾아서 삭제
                        success = await self.ga4_user_manager.remove_user_by_email(
                            property_id, user_email
                        )
                    
                    if success:
                        # 데이터베이스 상태 업데이트
                        await self.db_manager.execute_update(
                            """UPDATE user_registrations 
                               SET status = 'expired', ga4_registered = 0, 
                                   updated_at = datetime('now')
                               WHERE id = ?""",
                            (user_id,)
                        )
                        
                        # 만료 알림 발송
                        user_data = {
                            'applicant': user.get('신청자', ''),
                            'user_email': user_email,
                            'property_name': user.get('property_name', ''),
                            'property_id': property_id,
                            'permission_level': user.get('권한', ''),
                            'created_at': str(user.get('신청일', '')),
                            'expiry_date': str(user.get('종료일', ''))
                        }
                        
                        notification_success = await self.notification_service.send_expired_notification(user_data)
                        
                        results["removed"] += 1
                        if notification_success:
                            results["notified"] += 1
                            
                        self.logger.info(f"✅ 만료 사용자 삭제 완료: {user_email}")
                        
                    else:
                        results["failed"] += 1
                        self.logger.error(f"❌ 만료 사용자 삭제 실패: {user_email}")
                    
                    # API 호출 제한을 위한 대기
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    results["failed"] += 1
                    self.logger.error(f"❌ 개별 만료 처리 실패: {user.get('등록_계정', 'Unknown')} - {e}")
            
            self.logger.info(f"✅ 만료 처리 완료 - 삭제: {results['removed']}, 실패: {results['failed']}, 알림: {results['notified']}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 만료 처리 실패: {e}")
            return {"removed": 0, "failed": 1, "notified": 0}
    
    async def process_editor_downgrade(self) -> Dict[str, int]:
        """Editor 권한 자동 다운그레이드 (7일 후)"""
        try:
            self.logger.info("⬇️ Editor 권한 다운그레이드 프로세스 시작...")
            
            # 7일 전에 등록된 Editor 권한 조회
            downgrade_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            editor_users = await self.db_manager.execute_query(
                """SELECT ur.*, p.property_display_name as property_name, a.account_display_name as account_name
                   FROM user_registrations ur
                   JOIN ga4_properties p ON ur.property_id = p.property_id
                   JOIN ga4_accounts a ON p.account_id = a.account_id
                   WHERE ur.status = 'active' 
                   AND ur.권한 = 'editor'
                   AND DATE(ur.신청일) <= ?
                   AND ur.ga4_registered = 1""",
                (downgrade_date,)
            )
            
            results = {"downgraded": 0, "failed": 0, "notified": 0}
            
            for user in editor_users:
                try:
                    user_id = user.get('id')
                    user_email = user.get('등록_계정')
                    property_id = user.get('property_id')
                    user_link_name = user.get('user_link_name')
                    
                    # GA4에서 권한을 Viewer로 변경
                    success = await self.ga4_user_manager.update_user_permission(
                        property_id, user_link_name, 'viewer'
                    )
                    
                    if success:
                        # 데이터베이스 권한 업데이트
                        await self.db_manager.execute_update(
                            """UPDATE user_registrations 
                               SET 권한 = 'viewer', updated_at = datetime('now')
                               WHERE id = ?""",
                            (user_id,)
                        )
                        
                        # 다운그레이드 알림 발송
                        user_data = {
                            'applicant': user.get('신청자', ''),
                            'user_email': user_email,
                            'property_name': user.get('property_name', ''),
                            'property_id': property_id,
                            'permission_level': 'editor',  # 이전 권한
                            'created_at': str(user.get('신청일', '')),
                            'expiry_date': str(user.get('종료일', ''))
                        }
                        
                        notification_success = await self.notification_service.send_editor_downgrade_notification(user_data)
                        
                        results["downgraded"] += 1
                        if notification_success:
                            results["notified"] += 1
                            
                        self.logger.info(f"✅ Editor 다운그레이드 완료: {user_email}")
                        
                    else:
                        results["failed"] += 1
                        self.logger.error(f"❌ Editor 다운그레이드 실패: {user_email}")
                    
                    # API 호출 제한을 위한 대기
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    results["failed"] += 1
                    self.logger.error(f"❌ 개별 다운그레이드 실패: {user.get('등록_계정', 'Unknown')} - {e}")
            
            self.logger.info(f"✅ Editor 다운그레이드 완료 - 변경: {results['downgraded']}, 실패: {results['failed']}, 알림: {results['notified']}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Editor 다운그레이드 실패: {e}")
            return {"downgraded": 0, "failed": 1, "notified": 0}
    
    async def process_admin_downgrade(self) -> int:
        """Admin 권한 자동 다운그레이드 (7일 후)"""
        try:
            self.logger.info("⬇️ Admin 권한 다운그레이드 프로세스 시작...")
            
            # 7일 전에 등록된 Admin 권한 조회
            downgrade_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            admin_users = await self.db_manager.execute_query(
                """SELECT ur.*, p.property_display_name as property_name, a.account_display_name as account_name
                   FROM user_registrations ur
                   JOIN ga4_properties p ON ur.property_id = p.property_id
                   JOIN ga4_accounts a ON p.account_id = a.account_id
                   WHERE ur.status = 'active' 
                   AND ur.권한 = 'admin'
                   AND DATE(ur.신청일) <= ?
                   AND ur.ga4_registered = 1""",
                (downgrade_date,)
            )
            
            downgraded_count = 0
            
            for user in admin_users:
                try:
                    user_id = user.get('id')
                    user_email = user.get('등록_계정')
                    property_id = user.get('property_id')
                    user_link_name = user.get('user_link_name')
                    
                    # GA4에서 권한을 Viewer로 변경
                    success = await self.ga4_user_manager.update_user_permission(
                        property_id, user_link_name, 'viewer'
                    )
                    
                    if success:
                        # 데이터베이스 권한 업데이트
                        await self.db_manager.execute_update(
                            """UPDATE user_registrations 
                               SET 권한 = 'viewer', updated_at = datetime('now')
                               WHERE id = ?""",
                            (user_id,)
                        )
                        
                        # Admin 다운그레이드는 높은 우선순위 admin 타입 알림으로 발송
                        await self.notification_service.send_admin_notification(
                            f"[중요] Admin 권한이 만료되어 Viewer로 변경되었습니다",
                            f"{user_email}님의 Admin 권한이 7일 유지기간 만료로 인해 Viewer 권한으로 변경되었습니다.",
                            f"프로퍼티: {user.get('property_name', '')}\n"
                            f"변경일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"새 권한: Viewer\n\n"
                            f"계속해서 고급 권한이 필요하시면 다시 신청해 주세요."
                        )
                        
                        downgraded_count += 1
                        self.logger.info(f"⬇️ Admin 다운그레이드 완료: {user_email} (Admin → Viewer)")
                        
                    else:
                        self.logger.error(f"❌ Admin 다운그레이드 실패: {user_email}")
                    
                    # API 호출 제한을 위한 대기
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"❌ 개별 Admin 다운그레이드 실패: {user.get('등록_계정', 'Unknown')} - {e}")
            
            self.logger.info(f"✅ Admin 다운그레이드 완료 - 처리: {downgraded_count}명")
            return downgraded_count
            
        except Exception as e:
            self.logger.error(f"❌ Admin 다운그레이드 실패: {e}")
            return 0
    
    async def daily_maintenance(self) -> Dict[str, Any]:
        """일일 유지보수 작업"""
        try:
            self.logger.info("🛠️ 일일 유지보수 작업 시작...")
            
            results = {
                "expiry_notifications": {"sent": 0, "failed": 0},
                "expiry_processing": {"removed": 0, "failed": 0, "notified": 0},
                "editor_downgrade": {"downgraded": 0, "failed": 0, "notified": 0},
                "admin_downgrade": {"downgraded": 0},
                "database_cleanup": {"cleaned": 0, "failed": 0}
            }
            
            # 1. 일일 알림 확인 및 발송
            expiry_results = await self.notification_service.check_and_send_expiry_notifications()
            results["expiry_notifications"] = expiry_results
            
            # 2. 만료된 사용자 권한 삭제
            expiry_processing = await self.process_expiry_queue()
            results["expiry_processing"] = expiry_processing
            
            # 3. Editor 권한 자동 다운그레이드
            editor_results = await self.process_editor_downgrade()
            results["editor_downgrade"] = editor_results
            
            # 4. Admin 권한 자동 다운그레이드
            admin_downgraded = await self.process_admin_downgrade()
            results["admin_downgrade"]["downgraded"] = admin_downgraded
            
            # 5. 데이터베이스 정리 (30일 이상 된 로그 삭제)
            try:
                deleted_logs = await self.db_manager.execute_update(
                    "DELETE FROM notification_logs WHERE sent_at < datetime('now', '-30 days')"
                )
                deleted_audits = await self.db_manager.execute_update(
                    "DELETE FROM audit_logs WHERE timestamp < datetime('now', '-90 days')"
                )
                results["database_cleanup"]["cleaned"] = (deleted_logs or 0) + (deleted_audits or 0)
                
            except Exception as e:
                self.logger.error(f"❌ 데이터베이스 정리 실패: {e}")
                results["database_cleanup"]["failed"] = 1
            
            self.logger.info("✅ 일일 유지보수 작업 완료")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 일일 유지보수 작업 실패: {e}")
            return {"error": str(e)}
    
    def _schedule_jobs(self):
        """스케줄 작업 설정"""
        # 기존 작업 정리
        schedule.clear()
        
        # 매일 오전 9시에 일일 알림 확인 및 발송
        schedule.every().day.at("09:00").do(self._run_async_job, self.notification_service.check_and_send_expiry_notifications)
        
        # 매일 새벽 2시에 일일 유지보수
        schedule.every().day.at("02:00").do(self._run_async_job, self.daily_maintenance)
        
        # 매시간 정각에 만료 처리
        schedule.every().hour.at(":00").do(self._run_async_job, self.process_expiry_queue)
        
        # 매일 오전 10시에 Editor 다운그레이드
        schedule.every().day.at("10:00").do(self._run_async_job, self.process_editor_downgrade)
        
        # 매일 오전 10시 5분에 Admin 다운그레이드 (Editor와 5분 차이로 실행)
        schedule.every().day.at("10:05").do(self._run_async_job, self.process_admin_downgrade)
        
        self.logger.info(f"✅ 스케줄 작업 설정 완료 (총 {len(schedule.jobs)}개 작업)")
    
    def _run_async_job(self, async_func):
        """비동기 함수를 동기 환경에서 실행"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(async_func())
            loop.close()
            return result
        except Exception as e:
            self.logger.error(f"❌ 스케줄 작업 실행 실패: {e}")
    
    async def send_daily_summary(self):
        """일일 요약 알림 발송"""
        try:
            self.logger.info("🔔 일일 요약 알림 발송 시작")
            success = await self.notification_service.send_daily_summary_notification()
            
            if success:
                self.logger.info("✅ 일일 요약 알림 발송 완료")
            else:
                self.logger.warning("⚠️ 일일 요약 알림 발송 실패 또는 발송할 내용 없음")
                
        except Exception as e:
            self.logger.error(f"❌ 일일 요약 알림 발송 중 오류: {e}")

    async def _run_scheduler(self):
        """스케줄러 백그라운드 실행"""
        try:
            while self.is_running:
                schedule.run_pending()
                await asyncio.sleep(60)  # 1분마다 체크
        except Exception as e:
            self.logger.error(f"❌ 스케줄러 실행 중 오류: {e}")
            self.is_running = False

    def start_scheduler(self):
        """스케줄러 시작"""
        try:
            # 기존 스케줄 설정
            schedule.every().hour.do(lambda: asyncio.create_task(self.check_and_send_notifications()))
            schedule.every().day.at("09:00").do(lambda: asyncio.create_task(self.check_and_send_daily_notifications()))
            
            # 일일 요약 알림 추가 (매일 오후 6시)
            schedule.every().day.at("18:00").do(lambda: asyncio.create_task(self.send_daily_summary()))
            
            self.is_running = True
            self.logger.info("⏰ 스케줄러가 시작되었습니다")
            self.logger.info("📅 스케줄 설정:")
            self.logger.info("  - 매시간: 만료 알림 체크")
            self.logger.info("  - 매일 09:00: 일일 알림 체크")
            self.logger.info("  - 매일 18:00: 일일 요약 알림")
            
            # 백그라운드에서 스케줄러 실행
            asyncio.create_task(self._run_scheduler())
            
        except Exception as e:
            self.logger.error(f"❌ 스케줄러 시작 실패: {e}")
            self.is_running = False
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        if not self.is_running:
            self.logger.warning("⚠️ 스케줄러가 실행 중이 아닙니다")
            return
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("⏹️ 스케줄러가 중지되었습니다")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """스케줄러 상태 조회"""
        return {
            "is_running": self.is_running,
            "scheduled_jobs": len(schedule.jobs),
            "next_run": str(schedule.next_run()) if schedule.jobs else None,
            "jobs": [
                {
                    "job": str(job.job_func),
                    "interval": str(job.interval),
                    "unit": job.unit,
                    "next_run": str(job.next_run)
                }
                for job in schedule.jobs
            ]
        }
    
    def get_status(self) -> Dict[str, Any]:
        """스케줄러 상태 조회 (별칭 메서드)"""
        return self.get_scheduler_status()
    
    async def run_manual_maintenance(self) -> Dict[str, Any]:
        """수동 유지보수 실행"""
        self.logger.info("🔧 수동 유지보수 작업 시작...")
        return await self.daily_maintenance()
    
    def start(self):
        """스케줄러 시작 (별칭 메서드)"""
        self.start_scheduler()
    
    def stop(self):
        """스케줄러 중지 (별칭 메서드)"""
        self.stop_scheduler()


# 글로벌 스케줄러 인스턴스
ga4_scheduler = GA4Scheduler()
scheduler_service = ga4_scheduler  # 별칭 