#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 Admin 권한 승인 플로우 TDD 테스트
================================

Playwright를 사용하여 Admin 권한 신청부터 승인까지의 전체 플로우를 테스트합니다.
"""

import asyncio
import sqlite3
import pytest
from playwright.async_api import async_playwright
from datetime import datetime
import os
import sys

# 경로 설정
sys.path.append('/Users/seong-won-yeong/Dev/ga4AdminAutomation')
from src.infrastructure.database import DatabaseManager

class TestAdminApprovalFlowTDD:
    """Admin 권한 승인 플로우 TDD 테스트 클래스"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.db_manager = DatabaseManager()
        self.test_email = "admin.test@example.com"
        self.test_applicant = "admin.tester@example.com"
        self.test_property_id = "462884506"  # 실제 존재하는 property_id 사용
        
    async def setup(self):
        """테스트 환경 설정"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        
        # 테스트 데이터 정리
        await self.cleanup_test_data()
        
    async def cleanup_test_data(self):
        """테스트 데이터 정리"""
        try:
            await self.db_manager.execute_update(
                "DELETE FROM user_registrations WHERE 등록_계정 = ? OR 신청자 = ?",
                (self.test_email, self.test_applicant)
            )
            await self.db_manager.execute_update(
                "DELETE FROM notification_logs WHERE user_email = ?",
                (self.test_email,)
            )
            print("✅ 테스트 데이터 정리 완료")
        except Exception as e:
            print(f"⚠️ 테스트 데이터 정리 실패: {e}")
    
    async def teardown(self):
        """테스트 환경 정리"""
        await self.cleanup_test_data()
        if self.browser:
            await self.browser.close()
            
    async def test_1_admin_registration_form_shows_admin_option(self):
        """테스트 1: 등록 폼에 Admin 옵션이 표시되는가?"""
        print("\n🧪 테스트 1: Admin 옵션 표시 확인")
        
        await self.page.goto("http://localhost:8001/register")
        await self.page.wait_for_load_state('networkidle')
        
        # Admin 권한 옵션이 있는지 확인
        admin_option = await self.page.locator('input[value="admin"]').count()
        assert admin_option > 0, "❌ Admin 권한 옵션이 등록 폼에 없습니다"
        
        # Admin 권한 설명이 있는지 확인 (실제 텍스트에 맞게 수정)
        admin_description = await self.page.get_by_text("최고 권한").count()
        assert admin_description > 0, "❌ Admin 권한 설명이 없습니다"
        
        print("✅ 테스트 1 통과: Admin 옵션이 폼에 정상 표시됨")
        
    async def test_2_admin_registration_creates_pending_status(self):
        """테스트 2: Admin 권한 신청시 pending_approval 상태로 DB에 저장되는가?"""
        print("\n🧪 테스트 2: Admin 권한 신청 → pending_approval 상태 확인")
        
        await self.page.goto("http://localhost:8001/register")
        await self.page.wait_for_load_state('networkidle')
        
        # 등록 폼 작성
        await self.page.fill('input[name="신청자"]', self.test_applicant)
        await self.page.fill('textarea[name="등록_계정_목록"]', self.test_email)
        await self.page.check('input[name="property_ids"][value="462884506"]')
        await self.page.check('input[value="admin"]')
        
        # 폼 제출
        await self.page.click('button[type="submit"]')
        
        # 페이지에서 응답 대기
        await self.page.wait_for_timeout(5000)
        
        # 성공/실패 메시지 확인
        try:
            success_alert = await self.page.locator('.alert-success').text_content()
            if success_alert:
                print(f"✅ 성공 메시지: {success_alert}")
        except:
            pass
            
        try:
            error_alert = await self.page.locator('.alert-danger').text_content()
            if error_alert:
                print(f"❌ 에러 메시지: {error_alert}")
        except:
            pass
        
        # DB에서 상태 확인
        registrations = await self.db_manager.execute_query(
            "SELECT * FROM user_registrations WHERE 등록_계정 = ? AND 권한 = 'admin'",
            (self.test_email,)
        )
        
        print(f"📊 DB 등록 수: {len(registrations)}")
        if len(registrations) > 0:
            print(f"📋 등록 정보: {registrations[0]}")
        
        assert len(registrations) > 0, "❌ Admin 권한 신청이 DB에 저장되지 않았습니다"
        
        registration = registrations[0]
        assert registration['status'] == 'pending_approval', f"❌ 예상: pending_approval, 실제: {registration['status']}"
        assert registration['approval_required'] == 1, "❌ approval_required가 1이 아닙니다"
        
        print("✅ 테스트 2 통과: Admin 권한이 pending_approval 상태로 저장됨")
        
    async def test_3_admin_registration_sends_notifications(self):
        """테스트 3: Admin 권한 신청시 알림이 발송되는가?"""
        print("\n🧪 테스트 3: Admin 권한 신청 알림 발송 확인")
        
        # 알림 로그 확인
        notifications = await self.db_manager.execute_query(
            "SELECT * FROM notification_logs WHERE user_email = ? ORDER BY sent_at DESC",
            (self.test_email,)
        )
        
        assert len(notifications) > 0, "❌ Admin 권한 신청 알림이 발송되지 않았습니다"
        
        # 승인 대기 알림 확인 (content 컬럼 사용)
        pending_notification = next(
            (n for n in notifications if 'admin' in n.get('content', '').lower() or 'admin' in n.get('message_body', '').lower()),
            None
        )
        
        assert pending_notification is not None, "❌ Admin 승인 대기 알림을 찾을 수 없습니다"
        
        print("✅ 테스트 3 통과: Admin 권한 신청 알림이 정상 발송됨")
        
    async def test_4_admin_pending_list_shows_request(self):
        """테스트 4: Admin 승인 대기 목록에 신청이 표시되는가?"""
        print("\n🧪 테스트 4: Admin 승인 대기 목록 표시 확인")
        
        await self.page.goto("http://localhost:8001/dashboard")
        await self.page.wait_for_load_state('networkidle')
        
        # Admin 승인 대기 목록 버튼 클릭
        await self.page.click('button:has-text("Admin 승인 대기 목록")')
        await self.page.wait_for_timeout(1000)
        
        # 모달이 열렸는지 확인
        modal = self.page.locator('#pendingAdminRequestsModal')
        await modal.wait_for(state='visible')
        
        # 목록에서 테스트 이메일 찾기
        admin_list_content = await self.page.locator('#pendingAdminRequestsList').text_content()
        assert self.test_email in admin_list_content, f"❌ Admin 승인 대기 목록에 {self.test_email}이 없습니다"
        
        print("✅ 테스트 4 통과: Admin 승인 대기 목록에 신청이 정상 표시됨")
        
    async def test_5_admin_approval_process_works(self):
        """테스트 5: Admin 권한 승인 프로세스가 정상 작동하는가?"""
        print("\n🧪 테스트 5: Admin 권한 승인 프로세스 확인")
        
        # 승인 버튼 클릭
        approve_button = self.page.locator(f'button:has-text("승인"):near(:text("{self.test_email}"))')
        await approve_button.click()
        await self.page.wait_for_timeout(2000)
        
        # DB에서 상태 변경 확인
        registrations = await self.db_manager.execute_query(
            "SELECT * FROM user_registrations WHERE 등록_계정 = ? AND 권한 = 'admin'",
            (self.test_email,)
        )
        
        assert len(registrations) > 0, "❌ Admin 권한 등록을 찾을 수 없습니다"
        
        registration = registrations[0]
        assert registration['status'] == 'active', f"❌ 예상: active, 실제: {registration['status']}"
        assert registration['ga4_registered'] == 1, "❌ GA4 등록 상태가 1이 아닙니다"
        
        print("✅ 테스트 5 통과: Admin 권한 승인이 정상 처리됨")
        
    async def test_6_admin_approval_sends_confirmation_email(self):
        """테스트 6: Admin 권한 승인시 확인 이메일이 발송되는가?"""
        print("\n🧪 테스트 6: Admin 권한 승인 확인 이메일 발송 확인")
        
        # 승인 완료 알림 확인
        notifications = await self.db_manager.execute_query(
            "SELECT * FROM notification_logs WHERE user_email = ? AND notification_type = 'admin_approved' ORDER BY sent_at DESC",
            (self.test_email,)
        )
        
        assert len(notifications) > 0, "❌ Admin 권한 승인 확인 이메일이 발송되지 않았습니다"
        
        notification = notifications[0]
        content_text = notification.get('content', '') + notification.get('message_body', '')
        assert 'admin' in content_text.lower(), "❌ 이메일 내용에 Admin 관련 내용이 없습니다"
        
        print("✅ 테스트 6 통과: Admin 권한 승인 확인 이메일이 정상 발송됨")
        
    async def test_7_users_list_shows_admin_user(self):
        """테스트 7: 사용자 목록에 Admin 사용자가 올바르게 표시되는가?"""
        print("\n🧪 테스트 7: 사용자 목록 Admin 사용자 표시 확인")
        
        await self.page.goto("http://localhost:8001/users")
        await self.page.wait_for_load_state('networkidle')
        
        # 사용자 목록에서 Admin 사용자 찾기
        user_row = self.page.locator(f'tr:has-text("{self.test_email}")')
        await user_row.wait_for(state='visible')
        
        # Admin 권한 표시 확인
        admin_badge = user_row.locator('.badge:has-text("Admin")')
        await admin_badge.wait_for(state='visible')
        
        # 배지 색상 확인 (bg-dark)
        badge_class = await admin_badge.get_attribute('class')
        assert 'bg-dark' in badge_class, f"❌ Admin 배지 색상이 올바르지 않습니다: {badge_class}"
        
        print("✅ 테스트 7 통과: 사용자 목록에 Admin 사용자가 올바르게 표시됨")
        
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 GA4 Admin 권한 승인 플로우 TDD 테스트 시작")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # 순차적으로 테스트 실행
            await self.test_1_admin_registration_form_shows_admin_option()
            await self.test_2_admin_registration_creates_pending_status()
            await self.test_3_admin_registration_sends_notifications()
            await self.test_4_admin_pending_list_shows_request()
            await self.test_5_admin_approval_process_works()
            await self.test_6_admin_approval_sends_confirmation_email()
            await self.test_7_users_list_shows_admin_user()
            
            print("\n🎉 모든 테스트 통과!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 테스트 실패: {e}")
            raise
        finally:
            await self.teardown()


async def main():
    """메인 실행 함수"""
    tester = TestAdminApprovalFlowTDD()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 