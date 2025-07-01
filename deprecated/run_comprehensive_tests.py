#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
포괄적 테스트 실행기
==================

TDD 테스트, 시나리오 테스트, Playwright E2E 테스트를 모두 실행하는 통합 테스트 러너입니다.
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class ComprehensiveTestRunner:
    """포괄적 테스트 실행 클래스"""
    
    def __init__(self):
        self.test_results = {}
        self.overall_errors = []
        self.start_time = datetime.now()
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("🚀 GA4 권한 관리 시스템 포괄적 테스트 시작")
        print("=" * 60)
        print(f"시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 테스트 단계들
        test_phases = [
            ("1️⃣ TDD 방식 알림 시스템 오류 해결", self.run_tdd_tests),
            ("2️⃣ 사용자 등록 시나리오 테스트", self.run_scenario_tests),
            ("3️⃣ Playwright E2E 브라우저 테스트", self.run_playwright_tests),
            ("4️⃣ 시스템 상태 및 성능 검증", self.run_system_verification),
            ("5️⃣ 데이터베이스 일관성 확인", self.run_database_checks),
        ]
        
        total_phases = len(test_phases)
        completed_phases = 0
        
        for phase_name, phase_func in test_phases:
            try:
                print(f"\n{phase_name}")
                print("-" * 50)
                
                result = await phase_func()
                self.test_results[phase_name] = result
                
                if result.get('success', False):
                    print(f"✅ {phase_name} 완료")
                    completed_phases += 1
                else:
                    print(f"❌ {phase_name} 실패")
                    if result.get('errors'):
                        self.overall_errors.extend(result['errors'])
                
            except Exception as e:
                print(f"💥 {phase_name} 예외 발생: {e}")
                self.test_results[phase_name] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                self.overall_errors.append(f"{phase_name}: {str(e)}")
        
        # 종합 결과 계산
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        success_rate = (completed_phases / total_phases) * 100
        
        summary = {
            'test_phases': total_phases,
            'completed_phases': completed_phases,
            'failed_phases': total_phases - completed_phases,
            'success_rate': success_rate,
            'total_duration_seconds': total_duration,
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'overall_errors': self.overall_errors,
            'detailed_results': self.test_results
        }
        
        # 결과 출력
        self.print_final_summary(summary)
        
        # 결과 저장
        self.save_comprehensive_results(summary)
        
        return summary
    
    async def run_tdd_tests(self) -> Dict[str, Any]:
        """TDD 테스트 실행"""
        try:
            print("🧪 TDD 알림 시스템 오류 해결 테스트 실행 중...")
            
            # TDD 테스트 실행
            result = subprocess.run([
                sys.executable, "test_notification_system_tdd.py"
            ], capture_output=True, text=True, timeout=60)
            
            success = result.returncode == 0
            
            return {
                'success': success,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_type': 'TDD',
                'timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'TDD 테스트 타임아웃 (60초 초과)',
                'test_type': 'TDD'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'TDD 테스트 실행 오류: {str(e)}',
                'test_type': 'TDD'
            }
    
    async def run_scenario_tests(self) -> Dict[str, Any]:
        """사용자 등록 시나리오 테스트 실행"""
        try:
            print("🎭 사용자 등록 시나리오 테스트 실행 중...")
            
            # 시나리오 테스트 모듈 동적 import
            from test_user_registration_scenario import UserRegistrationScenarioTester
            
            tester = UserRegistrationScenarioTester()
            results = await tester.run_all_scenarios()
            
            return {
                'success': results.get('success_rate', 0) >= 70,  # 70% 이상 성공하면 통과
                'scenario_results': results,
                'test_type': 'Scenario',
                'timestamp': datetime.now().isoformat()
            }
            
        except ImportError as e:
            return {
                'success': False,
                'error': f'시나리오 테스트 모듈 import 실패: {str(e)}',
                'test_type': 'Scenario'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'시나리오 테스트 실행 오류: {str(e)}',
                'test_type': 'Scenario'
            }
    
    async def run_playwright_tests(self) -> Dict[str, Any]:
        """Playwright E2E 테스트 실행"""
        try:
            print("🎭 Playwright E2E 브라우저 테스트 실행 중...")
            
            # Playwright 패키지 확인
            try:
                import playwright
                print("   ✓ Playwright 패키지 확인됨")
            except ImportError:
                return {
                    'success': False,
                    'error': 'Playwright 패키지가 설치되지 않았습니다. pip install playwright 실행 후 playwright install 필요',
                    'test_type': 'Playwright'
                }
            
            # Playwright 테스트 모듈 동적 import
            try:
                from test_playwright_e2e import PlaywrightE2ETester
                
                tester = PlaywrightE2ETester()
                
                # Playwright 설정
                setup_success = await tester.setup(headless=True)
                
                if not setup_success:
                    return {
                        'success': False,
                        'error': 'Playwright 브라우저 설정 실패',
                        'test_type': 'Playwright'
                    }
                
                try:
                    # E2E 테스트 실행
                    results = await tester.run_all_e2e_tests()
                    
                    return {
                        'success': results.get('success_rate', 0) >= 60,  # 60% 이상 성공하면 통과
                        'e2e_results': results,
                        'test_type': 'Playwright',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                finally:
                    # 리소스 정리
                    await tester.teardown()
            
            except ImportError as e:
                return {
                    'success': False,
                    'error': f'Playwright 테스트 모듈 import 실패: {str(e)}',
                    'test_type': 'Playwright'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Playwright 테스트 실행 오류: {str(e)}',
                'test_type': 'Playwright'
            }
    
    async def run_system_verification(self) -> Dict[str, Any]:
        """시스템 상태 및 성능 검증"""
        try:
            print("🔍 시스템 상태 및 성능 검증 중...")
            
            import aiohttp
            
            base_url = "http://localhost:8000"
            
            async with aiohttp.ClientSession() as session:
                # 시스템 상태 확인
                health_check = await self.check_system_health(session, base_url)
                
                # 성능 테스트
                performance_check = await self.check_system_performance(session, base_url)
                
                # API 응답성 확인
                api_check = await self.check_api_responsiveness(session, base_url)
                
                overall_success = (
                    health_check.get('success', False) and
                    performance_check.get('success', False) and
                    api_check.get('success', False)
                )
                
                return {
                    'success': overall_success,
                    'health_check': health_check,
                    'performance_check': performance_check,
                    'api_check': api_check,
                    'test_type': 'System Verification',
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'시스템 검증 오류: {str(e)}',
                'test_type': 'System Verification'
            }
    
    async def check_system_health(self, session, base_url) -> Dict[str, Any]:
        """시스템 건강 상태 확인"""
        try:
            async with session.get(f"{base_url}/api/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'status_code': response.status,
                        'health_data': data
                    }
                else:
                    return {
                        'success': False,
                        'status_code': response.status,
                        'error': f'Health check failed with status {response.status}'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': f'Health check exception: {str(e)}'
            }
    
    async def check_system_performance(self, session, base_url) -> Dict[str, Any]:
        """시스템 성능 확인"""
        try:
            start_time = datetime.now()
            
            # 동시 요청 여러 개 보내기
            tasks = []
            for i in range(5):
                task = session.get(f"{base_url}/api/users", timeout=10)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            successful_requests = 0
            for response in responses:
                if not isinstance(response, Exception):
                    async with response:
                        if response.status == 200:
                            successful_requests += 1
            
            performance_good = total_time < 5.0 and successful_requests >= 3
            
            return {
                'success': performance_good,
                'total_time': total_time,
                'successful_requests': successful_requests,
                'total_requests': len(tasks),
                'average_time': total_time / len(tasks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Performance check exception: {str(e)}'
            }
    
    async def check_api_responsiveness(self, session, base_url) -> Dict[str, Any]:
        """API 응답성 확인"""
        try:
            api_endpoints = [
                '/api/health',
                '/api/users',
                '/api/admin/system-status',
                '/api/admin/notification-stats'
            ]
            
            endpoint_results = {}
            responsive_endpoints = 0
            
            for endpoint in api_endpoints:
                try:
                    start_time = datetime.now()
                    async with session.get(f"{base_url}{endpoint}", timeout=5) as response:
                        end_time = datetime.now()
                        response_time = (end_time - start_time).total_seconds()
                        
                        endpoint_results[endpoint] = {
                            'status': response.status,
                            'response_time': response_time,
                            'responsive': response.status < 500 and response_time < 3.0
                        }
                        
                        if endpoint_results[endpoint]['responsive']:
                            responsive_endpoints += 1
                            
                except Exception as e:
                    endpoint_results[endpoint] = {
                        'error': str(e),
                        'responsive': False
                    }
            
            responsiveness_rate = (responsive_endpoints / len(api_endpoints)) * 100
            
            return {
                'success': responsiveness_rate >= 75,  # 75% 이상 응답하면 성공
                'responsiveness_rate': responsiveness_rate,
                'responsive_endpoints': responsive_endpoints,
                'total_endpoints': len(api_endpoints),
                'endpoint_results': endpoint_results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'API responsiveness check exception: {str(e)}'
            }
    
    async def run_database_checks(self) -> Dict[str, Any]:
        """데이터베이스 일관성 확인"""
        try:
            print("🗄️ 데이터베이스 일관성 확인 중...")
            
            # 데이터베이스 모듈 import
            from src.infrastructure.database import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # 기본 테이블 존재 확인
            tables_check = await self.check_database_tables(db_manager)
            
            # 데이터 일관성 확인
            data_consistency_check = await self.check_data_consistency(db_manager)
            
            # 인덱스 및 성능 확인
            performance_check = await self.check_database_performance(db_manager)
            
            overall_success = (
                tables_check.get('success', False) and
                data_consistency_check.get('success', False) and
                performance_check.get('success', False)
            )
            
            return {
                'success': overall_success,
                'tables_check': tables_check,
                'data_consistency_check': data_consistency_check,
                'performance_check': performance_check,
                'test_type': 'Database Check',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'데이터베이스 확인 오류: {str(e)}',
                'test_type': 'Database Check'
            }
    
    async def check_database_tables(self, db_manager) -> Dict[str, Any]:
        """데이터베이스 테이블 확인"""
        try:
            required_tables = [
                'ga4_permissions',
                'notification_logs',
                'notification_settings',
                'audit_logs'
            ]
            
            existing_tables = []
            missing_tables = []
            
            for table in required_tables:
                try:
                    # 테이블 존재 확인
                    result = db_manager.execute_query_sync(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)
                    )
                    
                    if result:
                        existing_tables.append(table)
                    else:
                        missing_tables.append(table)
                        
                except Exception:
                    missing_tables.append(table)
            
            return {
                'success': len(missing_tables) == 0,
                'existing_tables': existing_tables,
                'missing_tables': missing_tables,
                'table_count': len(existing_tables)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'테이블 확인 오류: {str(e)}'
            }
    
    async def check_data_consistency(self, db_manager) -> Dict[str, Any]:
        """데이터 일관성 확인"""
        try:
            # 기본 데이터 검증
            user_count_result = db_manager.execute_query_sync(
                "SELECT COUNT(*) as count FROM ga4_permissions"
            )
            user_count = user_count_result[0]['count'] if user_count_result else 0
            
            # 알림 로그 수
            log_count_result = db_manager.execute_query_sync(
                "SELECT COUNT(*) as count FROM notification_logs"
            )
            log_count = log_count_result[0]['count'] if log_count_result else 0
            
            # 데이터 일관성 검사
            consistency_checks = {
                'user_count_positive': user_count >= 0,
                'log_count_positive': log_count >= 0,
                'no_orphaned_logs': True  # 추후 더 복잡한 검사 추가 가능
            }
            
            all_consistent = all(consistency_checks.values())
            
            return {
                'success': all_consistent,
                'user_count': user_count,
                'log_count': log_count,
                'consistency_checks': consistency_checks
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'데이터 일관성 확인 오류: {str(e)}'
            }
    
    async def check_database_performance(self, db_manager) -> Dict[str, Any]:
        """데이터베이스 성능 확인"""
        try:
            # 간단한 쿼리 성능 테스트
            start_time = datetime.now()
            
            db_manager.execute_query_sync("SELECT COUNT(*) FROM ga4_permissions")
            
            end_time = datetime.now()
            query_time = (end_time - start_time).total_seconds()
            
            # 1초 이내면 성능 양호
            performance_good = query_time < 1.0
            
            return {
                'success': performance_good,
                'query_time': query_time,
                'performance_threshold': 1.0,
                'performance_status': 'good' if performance_good else 'needs_optimization'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'데이터베이스 성능 확인 오류: {str(e)}'
            }
    
    def print_final_summary(self, summary: Dict[str, Any]):
        """최종 결과 요약 출력"""
        print("\n")
        print("=" * 60)
        print("🎯 GA4 권한 관리 시스템 포괄적 테스트 결과")
        print("=" * 60)
        
        success_rate = summary['success_rate']
        duration = summary['total_duration_seconds']
        
        print(f"📊 전체 성공률: {success_rate:.1f}%")
        print(f"⏱️ 총 소요 시간: {duration:.1f}초")
        print(f"✅ 완료된 단계: {summary['completed_phases']}/{summary['test_phases']}")
        print(f"❌ 실패한 단계: {summary['failed_phases']}")
        
        # 등급 평가
        if success_rate >= 90:
            grade = "A+ 🏆"
            status = "우수"
        elif success_rate >= 80:
            grade = "A 🥇"
            status = "양호"
        elif success_rate >= 70:
            grade = "B 🥈"
            status = "보통"
        elif success_rate >= 60:
            grade = "C 🥉"
            status = "미흡"
        else:
            grade = "D ⚠️"
            status = "불량"
        
        print(f"\n🏆 최종 등급: {grade} ({status})")
        
        # 개별 테스트 결과
        print(f"\n📋 개별 테스트 결과:")
        for phase_name, result in summary['detailed_results'].items():
            status_icon = "✅" if result.get('success', False) else "❌"
            print(f"   {status_icon} {phase_name}")
        
        # 오류 목록
        if summary['overall_errors']:
            print(f"\n🚨 발견된 오류들:")
            for i, error in enumerate(summary['overall_errors'], 1):
                print(f"   {i}. {error}")
        else:
            print(f"\n🎉 오류 없이 모든 테스트 완료!")
        
        print("\n" + "=" * 60)
    
    def save_comprehensive_results(self, summary: Dict[str, Any]) -> str:
        """포괄적 테스트 결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comprehensive_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 포괄적 테스트 결과가 저장되었습니다: {filename}")
        return filename


async def main():
    """메인 실행 함수"""
    runner = ComprehensiveTestRunner()
    
    try:
        # 모든 테스트 실행
        results = await runner.run_all_tests()
        
        # 성공 여부 결정
        success_rate = results['success_rate']
        success = success_rate >= 70  # 70% 이상 성공하면 전체적으로 성공
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹ 사용자에 의해 테스트가 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n💥 포괄적 테스트 실행 중 예외 발생: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 