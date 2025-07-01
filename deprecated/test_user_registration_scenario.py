#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 등록 과정 시나리오 테스트
==============================

실제 사용자 등록 과정에서 발생할 수 있는 모든 오류를 시나리오별로 테스트합니다.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import aiohttp

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class UserRegistrationScenarioTester:
    """사용자 등록 시나리오 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.errors_found = []
    
    async def run_all_scenarios(self) -> Dict[str, Any]:
        """모든 시나리오 실행"""
        print("\n🎭 사용자 등록 시나리오 테스트 시작\n")
        
        scenarios = [
            ("시나리오 1: 정상적인 Analyst 등록", self.scenario_normal_analyst_registration),
            ("시나리오 2: Editor 권한 신청", self.scenario_editor_permission_request),
            ("시나리오 3: Admin 권한 신청", self.scenario_admin_permission_request),
            ("시나리오 4: 중복 등록 시도", self.scenario_duplicate_registration),
            ("시나리오 5: 잘못된 이메일 형식", self.scenario_invalid_email_format),
            ("시나리오 6: 누락된 필드", self.scenario_missing_required_fields),
            ("시나리오 7: 권한 승인 과정", self.scenario_permission_approval_process),
            ("시나리오 8: 알림 발송 확인", self.scenario_notification_verification),
            ("시나리오 9: 데이터베이스 일관성 확인", self.scenario_database_consistency_check),
            ("시나리오 10: 시스템 부하 상황", self.scenario_system_load_test),
        ]
        
        passed = 0
        failed = 0
        
        for scenario_name, scenario_func in scenarios:
            try:
                print(f"🔄 실행 중: {scenario_name}")
                result = await scenario_func()
                
                if result.get('success', False):
                    print(f"✅ 성공: {scenario_name}")
                    passed += 1
                else:
                    print(f"❌ 실패: {scenario_name}")
                    print(f"   오류: {result.get('error', '알 수 없는 오류')}")
                    failed += 1
                    
                    if result.get('errors'):
                        self.errors_found.extend(result['errors'])
                
                self.test_results.append({
                    'scenario': scenario_name,
                    'success': result.get('success', False),
                    'error': result.get('error'),
                    'details': result.get('details', {}),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"💥 예외 발생: {scenario_name} - {e}")
                failed += 1
                self.errors_found.append(f"{scenario_name}: {str(e)}")
                
                self.test_results.append({
                    'scenario': scenario_name,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            
            print()  # 줄바꿈
        
        # 종합 결과
        total_scenarios = len(scenarios)
        success_rate = (passed / total_scenarios) * 100 if total_scenarios > 0 else 0
        
        summary = {
            'total_scenarios': total_scenarios,
            'passed': passed,
            'failed': failed,
            'success_rate': success_rate,
            'errors_found': self.errors_found,
            'detailed_results': self.test_results,
            'test_timestamp': datetime.now().isoformat()
        }
        
        print(f"📊 시나리오 테스트 결과:")
        print(f"   총 시나리오: {total_scenarios}개")
        print(f"   성공: {passed}개")
        print(f"   실패: {failed}개")
        print(f"   성공률: {success_rate:.1f}%")
        
        if self.errors_found:
            print(f"\n🚨 발견된 오류들:")
            for i, error in enumerate(self.errors_found, 1):
                print(f"   {i}. {error}")
        
        return summary
    
    async def scenario_normal_analyst_registration(self) -> Dict[str, Any]:
        """시나리오 1: 정상적인 Analyst 등록"""
        test_email = f"analyst_test_{datetime.now().strftime('%H%M%S')}@example.com"
        
        registration_data = {
            "등록_계정": test_email,
            "프로퍼티명": "Test Property Analytics",
            "role": "Analyst",
            "applicant": "자동 테스트",
            "status": "active"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 등록 요청
                async with session.post(
                    f"{self.base_url}/api/register",
                    json=registration_data
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"등록 요청 실패: HTTP {response.status}",
                            'details': {'status_code': response.status}
                        }
                    
                    result = await response.json()
                    
                    if not result.get('success', False):
                        return {
                            'success': False,
                            'error': f"등록 처리 실패: {result.get('message', '알 수 없음')}",
                            'details': result
                        }
                    
                    # 등록 후 데이터베이스 확인
                    async with session.get(
                        f"{self.base_url}/api/users",
                        params={"email": test_email}
                    ) as verify_response:
                        
                        if verify_response.status == 200:
                            verify_result = await verify_response.json()
                            
                            # 사용자가 실제로 등록되었는지 확인
                            users = verify_result.get('users', [])
                            registered_user = next(
                                (u for u in users if u.get('등록_계정') == test_email), 
                                None
                            )
                            
                            if registered_user:
                                return {
                                    'success': True,
                                    'details': {
                                        'registered_user': registered_user,
                                        'registration_response': result
                                    }
                                }
                            else:
                                return {
                                    'success': False,
                                    'error': "등록 후 사용자 조회 실패",
                                    'details': {'users_found': len(users)}
                                }
                        else:
                            return {
                                'success': False,
                                'error': f"사용자 조회 실패: HTTP {verify_response.status}",
                                'details': {'verify_status': verify_response.status}
                            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"시나리오 실행 중 예외: {str(e)}",
                'details': {'exception_type': type(e).__name__}
            }
    
    async def scenario_editor_permission_request(self) -> Dict[str, Any]:
        """시나리오 2: Editor 권한 신청"""
        test_email = f"editor_test_{datetime.now().strftime('%H%M%S')}@example.com"
        
        # 먼저 Analyst로 등록
        analyst_data = {
            "등록_계정": test_email,
            "프로퍼티명": "Test Property Editor",
            "role": "Analyst",
            "applicant": "Editor 테스트",
            "status": "active"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1단계: Analyst 등록
                async with session.post(
                    f"{self.base_url}/api/register",
                    json=analyst_data
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"초기 Analyst 등록 실패: HTTP {response.status}"
                        }
                
                # 2단계: Editor 권한 요청
                editor_request_data = {
                    "user_email": test_email,
                    "role": "editor",
                    "property_name": "Test Property Editor",
                    "reason": "자동 테스트를 위한 Editor 권한 요청"
                }
                
                async with session.post(
                    f"{self.base_url}/api/request-permission",
                    json=editor_request_data
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"Editor 권한 요청 실패: HTTP {response.status}",
                            'details': {'status_code': response.status}
                        }
                    
                    result = await response.json()
                    
                    return {
                        'success': result.get('success', False),
                        'error': result.get('message') if not result.get('success') else None,
                        'details': result
                    }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Editor 권한 신청 시나리오 예외: {str(e)}"
            }
    
    async def scenario_admin_permission_request(self) -> Dict[str, Any]:
        """시나리오 3: Admin 권한 신청"""
        test_email = f"admin_test_{datetime.now().strftime('%H%M%S')}@example.com"
        
        # 먼저 Editor로 등록 (Admin은 보통 Editor에서 승격)
        editor_data = {
            "등록_계정": test_email,
            "프로퍼티명": "Test Property Admin",
            "role": "Editor",
            "applicant": "Admin 테스트",
            "status": "active"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1단계: Editor 등록
                async with session.post(
                    f"{self.base_url}/api/register",
                    json=editor_data
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"초기 Editor 등록 실패: HTTP {response.status}"
                        }
                
                # 2단계: Admin 권한 요청
                admin_request_data = {
                    "user_email": test_email,
                    "role": "admin",
                    "property_name": "Test Property Admin",
                    "reason": "자동 테스트를 위한 Admin 권한 요청"
                }
                
                async with session.post(
                    f"{self.base_url}/api/request-permission",
                    json=admin_request_data
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"Admin 권한 요청 실패: HTTP {response.status}",
                            'details': {'status_code': response.status}
                        }
                    
                    result = await response.json()
                    
                    return {
                        'success': result.get('success', False),
                        'error': result.get('message') if not result.get('success') else None,
                        'details': result
                    }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Admin 권한 신청 시나리오 예외: {str(e)}"
            }
    
    async def scenario_duplicate_registration(self) -> Dict[str, Any]:
        """시나리오 4: 중복 등록 시도"""
        test_email = f"duplicate_test_{datetime.now().strftime('%H%M%S')}@example.com"
        
        registration_data = {
            "등록_계정": test_email,
            "프로퍼티명": "Duplicate Test Property",
            "role": "Analyst",
            "applicant": "중복 테스트",
            "status": "active"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 첫 번째 등록
                async with session.post(
                    f"{self.base_url}/api/register",
                    json=registration_data
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"첫 번째 등록 실패: HTTP {response.status}"
                        }
                
                # 두 번째 등록 시도 (중복)
                async with session.post(
                    f"{self.base_url}/api/register",
                    json=registration_data
                ) as response:
                    
                    result = await response.json()
                    
                    # 중복 등록은 실패해야 함
                    if response.status == 400 or not result.get('success', True):
                        return {
                            'success': True,  # 중복 방지가 제대로 작동함
                            'details': {
                                'duplicate_prevented': True,
                                'response': result
                            }
                        }
                    else:
                        return {
                            'success': False,
                            'error': "중복 등록이 방지되지 않음",
                            'details': result
                        }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"중복 등록 시나리오 예외: {str(e)}"
            }
    
    async def scenario_invalid_email_format(self) -> Dict[str, Any]:
        """시나리오 5: 잘못된 이메일 형식"""
        invalid_emails = [
            "invalid-email",
            "no-at-symbol.com",
            "@missing-local.com",
            "missing-domain@.com",
            "spaces in@email.com"
        ]
        
        errors_caught = 0
        total_tests = len(invalid_emails)
        
        try:
            async with aiohttp.ClientSession() as session:
                for invalid_email in invalid_emails:
                    registration_data = {
                        "등록_계정": invalid_email,
                        "프로퍼티명": "Invalid Email Test",
                        "role": "Analyst",
                        "applicant": "이메일 검증 테스트",
                        "status": "active"
                    }
                    
                    async with session.post(
                        f"{self.base_url}/api/register",
                        json=registration_data
                    ) as response:
                        
                        result = await response.json()
                        
                        # 잘못된 이메일은 거부되어야 함
                        if response.status == 400 or not result.get('success', True):
                            errors_caught += 1
                
                return {
                    'success': errors_caught == total_tests,
                    'details': {
                        'total_invalid_emails': total_tests,
                        'errors_caught': errors_caught,
                        'validation_rate': (errors_caught / total_tests) * 100
                    }
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"이메일 형식 검증 시나리오 예외: {str(e)}"
            }
    
    async def scenario_missing_required_fields(self) -> Dict[str, Any]:
        """시나리오 6: 누락된 필드"""
        test_cases = [
            {"프로퍼티명": "Missing Email Test", "role": "Analyst"},  # 이메일 누락
            {"등록_계정": "missing_property@test.com", "role": "Analyst"},  # 프로퍼티명 누락
            {"등록_계정": "missing_role@test.com", "프로퍼티명": "Missing Role Test"},  # role 누락
            {}  # 모든 필드 누락
        ]
        
        errors_caught = 0
        total_tests = len(test_cases)
        
        try:
            async with aiohttp.ClientSession() as session:
                for test_data in test_cases:
                    async with session.post(
                        f"{self.base_url}/api/register",
                        json=test_data
                    ) as response:
                        
                        result = await response.json()
                        
                        # 필수 필드가 누락된 요청은 거부되어야 함
                        if response.status == 400 or not result.get('success', True):
                            errors_caught += 1
                
                return {
                    'success': errors_caught == total_tests,
                    'details': {
                        'total_test_cases': total_tests,
                        'validation_errors_caught': errors_caught,
                        'validation_success_rate': (errors_caught / total_tests) * 100
                    }
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"필수 필드 검증 시나리오 예외: {str(e)}"
            }
    
    async def scenario_permission_approval_process(self) -> Dict[str, Any]:
        """시나리오 7: 권한 승인 과정"""
        test_email = f"approval_test_{datetime.now().strftime('%H%M%S')}@example.com"
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. pending_approval 상태의 사용자 생성
                registration_data = {
                    "등록_계정": test_email,
                    "프로퍼티명": "Approval Test Property",
                    "role": "Editor",
                    "applicant": "승인 테스트",
                    "status": "pending_approval"
                }
                
                async with session.post(
                    f"{self.base_url}/api/register",
                    json=registration_data
                ) as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"pending_approval 사용자 등록 실패: HTTP {response.status}"
                        }
                
                # 2. 승인 처리 확인
                async with session.post(
                    f"{self.base_url}/api/admin/approve-user",
                    json={"user_email": test_email, "action": "approve"}
                ) as response:
                    
                    result = await response.json()
                    
                    return {
                        'success': result.get('success', False),
                        'details': {
                            'approval_response': result,
                            'approval_status': response.status
                        }
                    }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"권한 승인 과정 시나리오 예외: {str(e)}"
            }
    
    async def scenario_notification_verification(self) -> Dict[str, Any]:
        """시나리오 8: 알림 발송 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                # 알림 통계 확인
                async with session.get(f"{self.base_url}/api/admin/notification-stats") as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"알림 통계 조회 실패: HTTP {response.status}"
                        }
                    
                    stats = await response.json()
                    
                    # 테스트 알림 발송
                    test_notification_data = {
                        "email": "test@example.com",
                        "notification_type": "welcome"
                    }
                    
                    async with session.post(
                        f"{self.base_url}/api/admin/send-test-notification",
                        json=test_notification_data
                    ) as notify_response:
                        
                        notify_result = await notify_response.json()
                        
                        return {
                            'success': notify_result.get('success', False),
                            'details': {
                                'notification_stats': stats,
                                'test_notification_result': notify_result
                            }
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"알림 확인 시나리오 예외: {str(e)}"
            }
    
    async def scenario_database_consistency_check(self) -> Dict[str, Any]:
        """시나리오 9: 데이터베이스 일관성 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                # 시스템 상태 확인
                async with session.get(f"{self.base_url}/api/admin/system-status") as response:
                    
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f"시스템 상태 조회 실패: HTTP {response.status}"
                        }
                    
                    status = await response.json()
                    
                    # 기본적인 일관성 검사
                    db_health = status.get('database', {}).get('status') == 'healthy'
                    user_count = status.get('statistics', {}).get('total_users', 0)
                    
                    return {
                        'success': db_health and user_count >= 0,
                        'details': {
                            'system_status': status,
                            'database_healthy': db_health,
                            'user_count': user_count
                        }
                    }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"데이터베이스 일관성 확인 시나리오 예외: {str(e)}"
            }
    
    async def scenario_system_load_test(self) -> Dict[str, Any]:
        """시나리오 10: 시스템 부하 상황"""
        concurrent_requests = 5
        test_emails = [
            f"load_test_{i}_{datetime.now().strftime('%H%M%S')}@example.com"
            for i in range(concurrent_requests)
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                
                for i, email in enumerate(test_emails):
                    registration_data = {
                        "등록_계정": email,
                        "프로퍼티명": f"Load Test Property {i+1}",
                        "role": "Analyst",
                        "applicant": f"부하 테스트 {i+1}",
                        "status": "active"
                    }
                    
                    task = session.post(
                        f"{self.base_url}/api/register",
                        json=registration_data
                    )
                    tasks.append(task)
                
                # 동시 요청 실행
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                successful_requests = 0
                failed_requests = 0
                
                for response in responses:
                    if isinstance(response, Exception):
                        failed_requests += 1
                    else:
                        async with response:
                            if response.status == 200:
                                result = await response.json()
                                if result.get('success', False):
                                    successful_requests += 1
                                else:
                                    failed_requests += 1
                            else:
                                failed_requests += 1
                
                success_rate = (successful_requests / concurrent_requests) * 100
                
                return {
                    'success': success_rate >= 80,  # 80% 이상 성공하면 통과
                    'details': {
                        'concurrent_requests': concurrent_requests,
                        'successful_requests': successful_requests,
                        'failed_requests': failed_requests,
                        'success_rate': success_rate
                    }
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"시스템 부하 테스트 시나리오 예외: {str(e)}"
            }
    
    def save_results(self, filename: str = None) -> str:
        """테스트 결과를 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"user_registration_scenario_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'test_results': self.test_results,
                'errors_found': self.errors_found,
                'summary': {
                    'total_scenarios': len(self.test_results),
                    'passed': sum(1 for r in self.test_results if r['success']),
                    'failed': sum(1 for r in self.test_results if not r['success']),
                    'test_completed_at': datetime.now().isoformat()
                }
            }, f, indent=2, ensure_ascii=False)
        
        return filename


async def main():
    """메인 실행 함수"""
    tester = UserRegistrationScenarioTester()
    
    try:
        # 시나리오 테스트 실행
        results = await tester.run_all_scenarios()
        
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
            print(f"\n🎉 모든 시나리오가 성공적으로 완료되었습니다!")
            return True
        
    except KeyboardInterrupt:
        print("\n⏹ 사용자에 의해 테스트가 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n💥 테스트 실행 중 예외 발생: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 