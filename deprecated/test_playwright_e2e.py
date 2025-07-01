#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright End-to-End 테스트
===========================

실제 브라우저 환경에서 사용자 등록 과정을 테스트합니다.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class PlaywrightE2ETester:
    """Playwright End-to-End 테스터"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.errors_found = []
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup(self, headless: bool = True) -> bool:
        """브라우저 설정"""
        try:
            self.playwright = await async_playwright().start()
            
            # Chromium 브라우저 시작
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 브라우저 컨텍스트 생성
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # 새 페이지 생성
            self.page = await self.context.new_page()
            
            # 콘솔 로그 캡처
            self.page.on('console', self._handle_console_log)
            self.page.on('pageerror', self._handle_page_error)
            
            print("✅ Playwright 브라우저 설정 완료")
            return True
            
        except Exception as e:
            print(f"❌ Playwright 설정 실패: {e}")
            return False
    
    async def teardown(self):
        """리소스 정리"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            print("✅ Playwright 리소스 정리 완료")
        except Exception as e:
            print(f"⚠️ 리소스 정리 중 오류: {e}")
    
    def _handle_console_log(self, msg):
        """브라우저 콘솔 로그 처리"""
        if msg.type in ['error', 'warning']:
            self.errors_found.append(f"Console {msg.type}: {msg.text}")
    
    def _handle_page_error(self, error):
        """페이지 오류 처리"""
        self.errors_found.append(f"Page error: {error}")
    
    async def run_all_e2e_tests(self) -> Dict[str, Any]:
        """모든 E2E 테스트 실행"""
        print("\n🎭 Playwright End-to-End 테스트 시작\n")
        
        tests = [
            ("E2E 1: 홈페이지 접근 및 기본 UI 확인", self.test_homepage_access),
            ("E2E 2: 사용자 등록 폼 작동 확인", self.test_registration_form),
            ("E2E 3: 관리자 페이지 접근", self.test_admin_page_access),
            ("E2E 4: API 엔드포인트 응답 확인", self.test_api_endpoints),
            ("E2E 5: 실시간 알림 기능", self.test_real_time_notifications),
            ("E2E 6: 모바일 반응형 디자인", self.test_mobile_responsive),
            ("E2E 7: 성능 및 로딩 시간", self.test_performance),
            ("E2E 8: 접근성 (Accessibility) 확인", self.test_accessibility),
            ("E2E 9: 보안 헤더 및 HTTPS", self.test_security_headers),
            ("E2E 10: 브라우저 호환성", self.test_browser_compatibility),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"🔄 실행 중: {test_name}")
                result = await test_func()
                
                if result.get('success', False):
                    print(f"✅ 성공: {test_name}")
                    passed += 1
                else:
                    print(f"❌ 실패: {test_name}")
                    print(f"   오류: {result.get('error', '알 수 없는 오류')}")
                    failed += 1
                    
                    if result.get('errors'):
                        self.errors_found.extend(result['errors'])
                
                self.test_results.append({
                    'test': test_name,
                    'success': result.get('success', False),
                    'error': result.get('error'),
                    'details': result.get('details', {}),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"💥 예외 발생: {test_name} - {e}")
                failed += 1
                self.errors_found.append(f"{test_name}: {str(e)}")
                
                self.test_results.append({
                    'test': test_name,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            
            print()  # 줄바꿈
        
        # 종합 결과
        total_tests = len(tests)
        success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
        
        summary = {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'success_rate': success_rate,
            'errors_found': self.errors_found,
            'detailed_results': self.test_results,
            'test_timestamp': datetime.now().isoformat()
        }
        
        print(f"📊 E2E 테스트 결과:")
        print(f"   총 테스트: {total_tests}개")
        print(f"   성공: {passed}개")
        print(f"   실패: {failed}개")
        print(f"   성공률: {success_rate:.1f}%")
        
        if self.errors_found:
            print(f"\n🚨 발견된 오류들:")
            for i, error in enumerate(self.errors_found, 1):
                print(f"   {i}. {error}")
        
        return summary
    
    async def test_homepage_access(self) -> Dict[str, Any]:
        """E2E 1: 홈페이지 접근 및 기본 UI 확인"""
        try:
            # 홈페이지 접근
            response = await self.page.goto(self.base_url, wait_until='networkidle')
            
            if response.status != 200:
                return {
                    'success': False,
                    'error': f"홈페이지 접근 실패: HTTP {response.status}"
                }
            
            # 기본 요소들 확인
            title = await self.page.title()
            
            # 페이지 제목 확인
            if not title or title.strip() == "":
                return {
                    'success': False,
                    'error': "페이지 제목이 비어있음"
                }
            
            # 주요 네비게이션 요소 확인
            nav_elements = [
                'nav', 'header', 'main', 'footer'
            ]
            
            missing_elements = []
            for element in nav_elements:
                try:
                    await self.page.wait_for_selector(element, timeout=3000)
                except:
                    missing_elements.append(element)
            
            # 스크린샷 저장
            screenshot_path = f"homepage_screenshot_{datetime.now().strftime('%H%M%S')}.png"
            await self.page.screenshot(path=screenshot_path)
            
            return {
                'success': len(missing_elements) == 0,
                'error': f"누락된 요소들: {missing_elements}" if missing_elements else None,
                'details': {
                    'page_title': title,
                    'missing_elements': missing_elements,
                    'screenshot': screenshot_path,
                    'url': self.page.url
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"홈페이지 접근 테스트 예외: {str(e)}"
            }
    
    async def test_registration_form(self) -> Dict[str, Any]:
        """E2E 2: 사용자 등록 폼 작동 확인"""
        try:
            # 등록 페이지로 이동
            await self.page.goto(f"{self.base_url}/register", wait_until='networkidle')
            
            # 폼 요소들 확인
            form_elements = [
                'input[type="email"]',
                'input[name="property_name"]',
                'select[name="role"]',
                'button[type="submit"]'
            ]
            
            missing_form_elements = []
            for element in form_elements:
                try:
                    await self.page.wait_for_selector(element, timeout=3000)
                except:
                    missing_form_elements.append(element)
            
            # 폼 작성 및 제출 테스트
            test_email = f"playwright_test_{datetime.now().strftime('%H%M%S')}@example.com"
            
            try:
                # 이메일 입력
                email_input = await self.page.query_selector('input[type="email"]')
                if email_input:
                    await email_input.fill(test_email)
                
                # 프로퍼티명 입력
                property_input = await self.page.query_selector('input[name="property_name"]')
                if property_input:
                    await property_input.fill("Playwright Test Property")
                
                # 역할 선택
                role_select = await self.page.query_selector('select[name="role"]')
                if role_select:
                    await role_select.select_option("analyst")
                
                # 폼 제출
                submit_button = await self.page.query_selector('button[type="submit"]')
                if submit_button:
                    await submit_button.click()
                    
                    # 제출 후 응답 대기
                    await self.page.wait_for_timeout(2000)
                
                form_submission_success = True
                
            except Exception as form_error:
                form_submission_success = False
                missing_form_elements.append(f"Form submission error: {form_error}")
            
            return {
                'success': len(missing_form_elements) == 0 and form_submission_success,
                'error': f"폼 문제: {missing_form_elements}" if missing_form_elements else None,
                'details': {
                    'missing_form_elements': missing_form_elements,
                    'form_submission_success': form_submission_success,
                    'test_email': test_email
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"등록 폼 테스트 예외: {str(e)}"
            }
    
    async def test_admin_page_access(self) -> Dict[str, Any]:
        """E2E 3: 관리자 페이지 접근"""
        try:
            # 관리자 페이지 접근
            response = await self.page.goto(f"{self.base_url}/admin", wait_until='networkidle')
            
            # 관리자 페이지는 인증이 필요할 수 있으므로 403/401도 정상으로 처리
            acceptable_status = [200, 401, 403, 302]
            
            if response.status not in acceptable_status:
                return {
                    'success': False,
                    'error': f"관리자 페이지 접근 실패: HTTP {response.status}"
                }
            
            # 인증이 필요한 경우 로그인 폼 확인
            if response.status in [401, 403]:
                # 로그인 관련 요소 확인
                login_elements = ['input[type="password"]', 'input[name="username"]', 'button[type="submit"]']
                login_form_present = False
                
                for element in login_elements:
                    try:
                        await self.page.wait_for_selector(element, timeout=1000)
                        login_form_present = True
                        break
                    except:
                        continue
                
                return {
                    'success': True,  # 인증이 필요한 것은 정상
                    'details': {
                        'status_code': response.status,
                        'login_form_present': login_form_present,
                        'requires_authentication': True
                    }
                }
            
            # 200 응답인 경우 관리자 기능 확인
            admin_elements = [
                'table',  # 사용자 목록
                'button',  # 관리 버튼들
                'nav'  # 네비게이션
            ]
            
            present_elements = []
            for element in admin_elements:
                try:
                    await self.page.wait_for_selector(element, timeout=1000)
                    present_elements.append(element)
                except:
                    continue
            
            return {
                'success': True,
                'details': {
                    'status_code': response.status,
                    'admin_elements_present': present_elements,
                    'page_accessible': True
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"관리자 페이지 접근 테스트 예외: {str(e)}"
            }
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """E2E 4: API 엔드포인트 응답 확인"""
        try:
            api_endpoints = [
                '/api/health',
                '/api/users',
                '/api/system-status',
                '/api/admin/notification-stats'
            ]
            
            endpoint_results = {}
            
            for endpoint in api_endpoints:
                try:
                    response = await self.page.goto(f"{self.base_url}{endpoint}", wait_until='networkidle')
                    
                    # JSON 응답 확인
                    try:
                        content = await self.page.content()
                        # JSON 형태인지 간단히 확인
                        if content.strip().startswith('{') or content.strip().startswith('['):
                            is_json = True
                        else:
                            is_json = False
                    except:
                        is_json = False
                    
                    endpoint_results[endpoint] = {
                        'status': response.status,
                        'accessible': response.status < 500,
                        'is_json': is_json
                    }
                    
                except Exception as e:
                    endpoint_results[endpoint] = {
                        'status': None,
                        'accessible': False,
                        'error': str(e)
                    }
            
            # 성공 기준: 대부분의 엔드포인트가 접근 가능
            accessible_count = sum(1 for result in endpoint_results.values() if result.get('accessible', False))
            success_rate = (accessible_count / len(api_endpoints)) * 100
            
            return {
                'success': success_rate >= 75,  # 75% 이상 접근 가능하면 성공
                'details': {
                    'endpoint_results': endpoint_results,
                    'accessible_endpoints': accessible_count,
                    'total_endpoints': len(api_endpoints),
                    'success_rate': success_rate
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"API 엔드포인트 테스트 예외: {str(e)}"
            }
    
    async def test_real_time_notifications(self) -> Dict[str, Any]:
        """E2E 5: 실시간 알림 기능"""
        try:
            # 알림 관련 페이지로 이동
            await self.page.goto(f"{self.base_url}/admin", wait_until='networkidle')
            
            # 알림 관련 요소 확인
            notification_elements = []
            
            # 알림 관련 가능한 셀렉터들
            selectors = [
                '.notification',
                '.alert',
                '.toast',
                '[data-notification]',
                '.message'
            ]
            
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        notification_elements.extend([selector] * len(elements))
                except:
                    continue
            
            # JavaScript 알림 함수 확인
            js_notification_support = await self.page.evaluate("""
                () => {
                    return {
                        'Notification' in window,
                        'serviceWorker' in navigator,
                        'PushManager' in window
                    }
                }
            """)
            
            return {
                'success': len(notification_elements) > 0 or any(js_notification_support.values()),
                'details': {
                    'notification_elements_found': len(notification_elements),
                    'js_notification_support': js_notification_support,
                    'notification_selectors': list(set(notification_elements))
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"실시간 알림 테스트 예외: {str(e)}"
            }
    
    async def test_mobile_responsive(self) -> Dict[str, Any]:
        """E2E 6: 모바일 반응형 디자인"""
        try:
            # 모바일 뷰포트로 변경
            await self.page.set_viewport_size({'width': 375, 'height': 667})  # iPhone SE 크기
            
            # 홈페이지 다시 로드
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            # 모바일에서 주요 요소들이 제대로 표시되는지 확인
            mobile_elements = [
                'nav', 'main', 'header'
            ]
            
            visible_elements = []
            for element in mobile_elements:
                try:
                    locator = self.page.locator(element)
                    if await locator.is_visible():
                        visible_elements.append(element)
                except:
                    continue
            
            # 가로 스크롤이 없는지 확인
            scroll_width = await self.page.evaluate("document.documentElement.scrollWidth")
            client_width = await self.page.evaluate("document.documentElement.clientWidth")
            no_horizontal_scroll = scroll_width <= client_width + 5  # 5px 여유
            
            # 모바일 스크린샷 저장
            mobile_screenshot = f"mobile_screenshot_{datetime.now().strftime('%H%M%S')}.png"
            await self.page.screenshot(path=mobile_screenshot)
            
            # 원래 뷰포트로 복원
            await self.page.set_viewport_size({'width': 1920, 'height': 1080})
            
            return {
                'success': len(visible_elements) >= 2 and no_horizontal_scroll,
                'details': {
                    'visible_elements': visible_elements,
                    'no_horizontal_scroll': no_horizontal_scroll,
                    'scroll_width': scroll_width,
                    'client_width': client_width,
                    'mobile_screenshot': mobile_screenshot
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"모바일 반응형 테스트 예외: {str(e)}"
            }
    
    async def test_performance(self) -> Dict[str, Any]:
        """E2E 7: 성능 및 로딩 시간"""
        try:
            # 페이지 로딩 시간 측정
            start_time = datetime.now()
            
            response = await self.page.goto(self.base_url, wait_until='networkidle')
            
            end_time = datetime.now()
            loading_time = (end_time - start_time).total_seconds()
            
            # 리소스 로딩 정보
            performance_data = await self.page.evaluate("""
                () => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    return {
                        'domContentLoaded': perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
                        'loadComplete': perf.loadEventEnd - perf.loadEventStart,
                        'firstPaint': performance.getEntriesByType('paint')[0]?.startTime || 0
                    }
                }
            """)
            
            # 성능 기준 (3초 이내)
            performance_good = loading_time < 3.0
            
            return {
                'success': performance_good,
                'details': {
                    'loading_time_seconds': loading_time,
                    'performance_data': performance_data,
                    'response_status': response.status,
                    'performance_threshold_met': performance_good
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"성능 테스트 예외: {str(e)}"
            }
    
    async def test_accessibility(self) -> Dict[str, Any]:
        """E2E 8: 접근성 (Accessibility) 확인"""
        try:
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            # 기본적인 접근성 요소들 확인
            accessibility_checks = await self.page.evaluate("""
                () => {
                    const checks = {
                        'hasTitle': !!document.title,
                        'hasLang': !!document.documentElement.lang,
                        'hasMainLandmark': !!document.querySelector('main'),
                        'hasHeadings': !!document.querySelector('h1, h2, h3, h4, h5, h6'),
                        'hasAltTexts': Array.from(document.images).every(img => img.alt !== undefined),
                        'hasLabels': Array.from(document.querySelectorAll('input')).every(
                            input => input.labels?.length > 0 || input.getAttribute('aria-label')
                        )
                    };
                    
                    const score = Object.values(checks).filter(Boolean).length;
                    const total = Object.keys(checks).length;
                    
                    return {
                        checks: checks,
                        score: score,
                        total: total,
                        percentage: (score / total) * 100
                    };
                }
            """)
            
            # 70% 이상 통과하면 성공
            accessibility_good = accessibility_checks['percentage'] >= 70
            
            return {
                'success': accessibility_good,
                'details': accessibility_checks
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"접근성 테스트 예외: {str(e)}"
            }
    
    async def test_security_headers(self) -> Dict[str, Any]:
        """E2E 9: 보안 헤더 및 HTTPS"""
        try:
            response = await self.page.goto(self.base_url, wait_until='networkidle')
            
            # 응답 헤더 확인
            headers = response.headers
            
            security_headers = {
                'x-frame-options': headers.get('x-frame-options'),
                'x-content-type-options': headers.get('x-content-type-options'),
                'x-xss-protection': headers.get('x-xss-protection'),
                'content-security-policy': headers.get('content-security-policy'),
                'strict-transport-security': headers.get('strict-transport-security')
            }
            
            # HTTPS 확인
            is_https = self.page.url.startswith('https://')
            
            # 보안 헤더 점수 계산
            present_headers = sum(1 for value in security_headers.values() if value)
            security_score = (present_headers / len(security_headers)) * 100
            
            return {
                'success': security_score >= 30,  # 30% 이상의 보안 헤더가 있으면 통과
                'details': {
                    'security_headers': security_headers,
                    'is_https': is_https,
                    'security_score': security_score,
                    'headers_present': present_headers,
                    'total_headers_checked': len(security_headers)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"보안 헤더 테스트 예외: {str(e)}"
            }
    
    async def test_browser_compatibility(self) -> Dict[str, Any]:
        """E2E 10: 브라우저 호환성"""
        try:
            # JavaScript 기능 확인
            js_features = await self.page.evaluate("""
                () => {
                    return {
                        'ES6_support': typeof Promise !== 'undefined',
                        'Fetch_API': typeof fetch !== 'undefined',
                        'LocalStorage': typeof localStorage !== 'undefined',
                        'JSON_support': typeof JSON !== 'undefined',
                        'querySelector': typeof document.querySelector !== 'undefined',
                        'addEventListener': typeof document.addEventListener !== 'undefined'
                    }
                }
            """)
            
            # CSS 기능 확인
            css_features = await self.page.evaluate("""
                () => {
                    const testDiv = document.createElement('div');
                    document.body.appendChild(testDiv);
                    
                    const features = {
                        'flexbox': CSS.supports('display', 'flex'),
                        'grid': CSS.supports('display', 'grid'),
                        'transforms': CSS.supports('transform', 'translateX(10px)'),
                        'transitions': CSS.supports('transition', 'opacity 1s')
                    };
                    
                    document.body.removeChild(testDiv);
                    return features;
                }
            """)
            
            # 호환성 점수 계산
            js_supported = sum(js_features.values())
            css_supported = sum(css_features.values())
            total_features = len(js_features) + len(css_features)
            supported_features = js_supported + css_supported
            
            compatibility_score = (supported_features / total_features) * 100
            
            return {
                'success': compatibility_score >= 80,  # 80% 이상 지원하면 성공
                'details': {
                    'js_features': js_features,
                    'css_features': css_features,
                    'compatibility_score': compatibility_score,
                    'supported_features': supported_features,
                    'total_features': total_features
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"브라우저 호환성 테스트 예외: {str(e)}"
            }
    
    def save_results(self, filename: str = None) -> str:
        """테스트 결과를 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"playwright_e2e_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'test_results': self.test_results,
                'errors_found': self.errors_found,
                'summary': {
                    'total_tests': len(self.test_results),
                    'passed': sum(1 for r in self.test_results if r['success']),
                    'failed': sum(1 for r in self.test_results if not r['success']),
                    'test_completed_at': datetime.now().isoformat()
                }
            }, f, indent=2, ensure_ascii=False)
        
        return filename


async def main():
    """메인 실행 함수"""
    tester = PlaywrightE2ETester()
    
    try:
        # Playwright 설정
        setup_success = await tester.setup(headless=True)  # headless=False로 하면 브라우저가 보임
        
        if not setup_success:
            print("❌ Playwright 설정 실패")
            return False
        
        # E2E 테스트 실행
        results = await tester.run_all_e2e_tests()
        
        # 결과 저장
        result_file = tester.save_results()
        print(f"\n💾 테스트 결과가 저장되었습니다: {result_file}")
        
        # 최종 평가
        success_rate = results['success_rate']
        
        if success_rate >= 90:
            grade = "A+ (우수)"
        elif success_rate >= 80:
            grade = "A (양호)"
        elif success_rate >= 70:
            grade = "B (보통)"
        elif success_rate >= 60:
            grade = "C (미흡)"
        else:
            grade = "D (불량)"
        
        print(f"\n🎯 최종 평가: {grade}")
        print(f"   성공률: {success_rate:.1f}%")
        
        if results['errors_found']:
            print(f"\n🔧 해결해야 할 오류: {len(results['errors_found'])}개")
            return False
        else:
            print(f"\n🎉 모든 E2E 테스트가 성공적으로 완료되었습니다!")
            return True
        
    except KeyboardInterrupt:
        print("\n⏹ 사용자에 의해 테스트가 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n💥 테스트 실행 중 예외 발생: {e}")
        return False
    finally:
        # 리소스 정리
        await tester.teardown()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 