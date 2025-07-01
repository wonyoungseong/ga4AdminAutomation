#!/usr/bin/env python3
"""
GA4 권한 관리 시스템 - Editor 승인 기능 UI 테스트
Playwright를 사용한 전체 플로우 테스트
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def test_editor_approval_flow():
    """Editor 권한 신청부터 승인까지 전체 플로우 테스트"""
    
    async with async_playwright() as p:
        # 브라우저 시작
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 GA4 권한 관리 시스템 접속...")
            await page.goto("http://localhost:8000")
            
            # 페이지 로드 대기
            await page.wait_for_load_state('networkidle')
            
            print("📷 메인 페이지 스크린샷 저장...")
            await page.screenshot(path='screenshots/01_main_page.png')
            
            # 1. Editor 권한 신청하기
            print("\n🔄 1단계: Editor 권한 신청")
            
            # 사용자 등록 페이지로 이동
            await page.click('a[href="/register"]')
            await page.wait_for_load_state('networkidle')
            
            print("📷 등록 페이지 스크린샷 저장...")
            await page.screenshot(path='screenshots/02_register_page.png')
            
            # 신청자 입력
            await page.fill('input[name="신청자"]', 'Playwright테스터')
            
            # 등록 계정 목록 입력
            await page.fill('textarea[name="등록_계정_목록"]', 'playwright_test@example.com')
            
            # Editor 권한 선택
            await page.check('input[type="radio"][name="권한"][value="editor"]')
            
            # 프로퍼티 선택 (첫 번째 프로퍼티)
            await page.check('input[type="checkbox"][name="property_ids"]:first-of-type')
            
            print("📷 신청서 작성 완료 스크린샷 저장...")
            await page.screenshot(path='screenshots/03_register_form_filled.png')
            
            # 신청 제출
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            print("📷 신청 완료 스크린샷 저장...")
            await page.screenshot(path='screenshots/04_register_success.png')
            
            # 2. 승인 대기 목록 확인
            print("\n🔄 2단계: 승인 대기 목록 확인")
            
            # 메인 페이지로 이동
            await page.goto("http://localhost:8000")
            await page.wait_for_load_state('networkidle')
            
            # Editor 승인 테스트 버튼 클릭
            try:
                await page.click('button:has-text("Editor 승인 테스트")')
                print("✅ Editor 승인 테스트 버튼 클릭 성공")
                
                # 모달이 열리는지 확인
                await page.wait_for_selector('#editorApprovalModal', state='visible', timeout=5000)
                print("✅ Editor 승인 모달 열림 확인")
                
                print("📷 Editor 승인 모달 스크린샷 저장...")
                await page.screenshot(path='screenshots/05_editor_approval_modal.png')
                
                # 승인 대기 목록 확인
                pending_list = await page.inner_text('#pendingEditorRequestsList')
                print(f"📋 승인 대기 목록:\n{pending_list}")
                
                # 승인 대기 목록에 우리가 신청한 요청이 있는지 확인
                if 'playwright_test@example.com' in pending_list:
                    print("✅ 신청한 Editor 요청이 승인 대기 목록에 표시됨")
                    
                    # 3. 실제 승인 처리
                    print("\n🔄 3단계: Editor 권한 승인 처리")
                    
                    # 승인 버튼 클릭
                    approve_button = page.locator('button:has-text("승인")')
                    if await approve_button.count() > 0:
                        await approve_button.first.click()
                        print("✅ 승인 버튼 클릭")
                        
                        # 승인 처리 대기
                        await page.wait_for_timeout(3000)
                        
                        print("📷 승인 처리 후 스크린샷 저장...")
                        await page.screenshot(path='screenshots/06_after_approval.png')
                        
                        # 승인 후 목록 다시 확인
                        await page.click('button:has-text("목록 새로고침")')
                        await page.wait_for_timeout(2000)
                        
                        updated_list = await page.inner_text('#pendingEditorRequestsList')
                        print(f"📋 승인 후 대기 목록:\n{updated_list}")
                        
                        if 'playwright_test@example.com' not in updated_list:
                            print("✅ 승인 처리 완료 - 대기 목록에서 제거됨")
                        else:
                            print("⚠️ 아직 승인 대기 목록에 남아있음")
                    else:
                        print("❌ 승인 버튼을 찾을 수 없음")
                        
                else:
                    print("❌ 신청한 요청이 승인 대기 목록에 없음")
                    print("💡 직접 테스트 승인 메일 발송해보기")
                    
                    # 테스트 메일 발송
                    await page.fill('input[type="email"]', 'playwright_test@example.com')
                    await page.click('button:has-text("승인 메일 발송")')
                    await page.wait_for_timeout(2000)
                    
                    print("📷 테스트 메일 발송 후 스크린샷 저장...")
                    await page.screenshot(path='screenshots/07_test_email_sent.png')
                
                # 모달 닫기
                await page.click('button:has-text("닫기")')
                
            except Exception as e:
                print(f"❌ Editor 승인 테스트 중 오류: {e}")
                await page.screenshot(path='screenshots/error_editor_approval.png')
            
            # 4. 최종 상태 확인
            print("\n🔄 4단계: 최종 상태 확인")
            
            # 사용자 목록 페이지로 이동
            await page.goto("http://localhost:8000/users")
            await page.wait_for_load_state('networkidle')
            
            print("📷 사용자 목록 페이지 스크린샷 저장...")
            await page.screenshot(path='screenshots/08_users_list.png')
            
            # 우리가 등록한 사용자가 있는지 확인
            page_content = await page.content()
            if 'playwright_test@example.com' in page_content:
                print("✅ 등록된 사용자를 사용자 목록에서 확인")
                
                # 사용자 상태 확인
                user_row = page.locator('tr:has-text("playwright_test@example.com")')
                if await user_row.count() > 0:
                    user_status = await user_row.locator('td').nth(4).inner_text()  # 상태 컬럼
                    print(f"📋 사용자 상태: {user_status}")
            else:
                print("❌ 등록된 사용자를 사용자 목록에서 찾을 수 없음")
            
            print("\n🎉 테스트 완료!")
            print("📁 스크린샷들이 screenshots/ 폴더에 저장되었습니다")
            
        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {e}")
            await page.screenshot(path='screenshots/error_general.png')
            
        finally:
            # 브라우저 닫기
            await browser.close()

async def main():
    """메인 함수"""
    print("🚀 GA4 Editor 승인 기능 UI 테스트 시작")
    print("=" * 50)
    
    # 스크린샷 디렉토리 생성
    import os
    os.makedirs('screenshots', exist_ok=True)
    
    # 테스트 실행
    await test_editor_approval_flow()

if __name__ == "__main__":
    asyncio.run(main()) 