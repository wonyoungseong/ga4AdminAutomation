#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 실제 API 테스트 러너
======================================
"""

import asyncio
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp

class GA4RealisticTestRunner:
    """실제 API 엔드포인트를 사용한 GA4 권한 관리 시스템 테스트"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
        
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n🚀 GA4 권한 관리 시스템 실제 API 테스트 시작")
        print("=" * 60)
        
        test_suites = [
            ("시스템 상태 확인", self.test_system_status),
            ("API 엔드포인트 테스트", self.test_api_endpoints),
            ("사용자 목록 조회", self.test_user_management),
            ("프로퍼티 및 계정 조회", self.test_property_account_management),
            ("알림 시스템 테스트", self.test_notification_system),
            ("스케줄러 테스트", self.test_scheduler_functions),
            ("성능 테스트", self.test_performance),
            ("관리자 기능 테스트", self.test_admin_functions)
        ]
        
        for suite_name, test_function in test_suites:
            try:
                print(f"\n📋 {suite_name} 실행 중...")
                results = await test_function()
                self.test_results[suite_name] = results
                success = self.evaluate_suite_success(results)
                print(f"{'✅' if success else '❌'} {suite_name} 완료")
            except Exception as e:
                error_msg = f"❌ {suite_name} 실패: {str(e)}"
                print(error_msg)
                self.test_results[suite_name] = {"error": error_msg, "traceback": traceback.format_exc()}
        
        await self.save_results_and_report()
        
    def evaluate_suite_success(self, results):
        """테스트 스위트 성공 여부 평가"""
        if isinstance(results, dict):
            if "error" in results:
                return False
            # 모든 하위 테스트 중 80% 이상 성공해야 성공으로 간주
            success_items = [item for item in results.values() 
                           if isinstance(item, dict) and item.get("success", False)]
            total_items = [item for item in results.values() 
                          if isinstance(item, dict) and "success" in item]
            
            if total_items:
                success_rate = len(success_items) / len(total_items)
                return success_rate >= 0.8
        return True
        
    async def test_system_status(self) -> Dict[str, Any]:
        """1. 시스템 상태 확인"""
        results = {}
        
        # 시스템 통계 확인
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stats") as response:
                    if response.status == 200:
                        data = await response.json()
                        results["system_stats"] = {
                            "success": True,
                            "data": data,
                            "response_code": response.status
                        }
                    else:
                        results["system_stats"] = {
                            "success": False,
                            "response_code": response.status
                        }
        except Exception as e:
            results["system_stats"] = {"success": False, "error": str(e)}
        
        # 대시보드 접근성 확인
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/dashboard") as response:
                    results["dashboard_access"] = {
                        "success": response.status == 200,
                        "response_code": response.status,
                        "content_type": response.headers.get('content-type', '')
                    }
        except Exception as e:
            results["dashboard_access"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """2. API 엔드포인트 테스트"""
        results = {}
        
        endpoints = [
            "/api/stats",
            "/api/users", 
            "/api/properties",
            "/api/accounts",
            "/api/notification-stats",
            "/api/scheduler-status"
        ]
        
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    start_time = datetime.now()
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        end_time = datetime.now()
                        response_time = (end_time - start_time).total_seconds()
                        
                        is_success = response.status == 200
                        data = None
                        if is_success:
                            try:
                                data = await response.json()
                            except:
                                pass
                        
                        results[endpoint] = {
                            "success": is_success,
                            "response_code": response.status,
                            "response_time": response_time,
                            "has_data": data is not None
                        }
            except Exception as e:
                results[endpoint] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_user_management(self) -> Dict[str, Any]:
        """3. 사용자 목록 조회 테스트"""
        results = {}
        
        # 전체 사용자 목록 조회
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/users") as response:
                    if response.status == 200:
                        data = await response.json()
                        user_count = len(data.get("data", {}).get("users", []))
                        results["user_list"] = {
                            "success": True,
                            "user_count": user_count,
                            "has_pagination": "pagination" in data.get("data", {})
                        }
                    else:
                        results["user_list"] = {
                            "success": False,
                            "response_code": response.status
                        }
        except Exception as e:
            results["user_list"] = {"success": False, "error": str(e)}
        
        # 필터링된 사용자 조회 (활성 사용자만)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/users?status=active&per_page=10") as response:
                    if response.status == 200:
                        data = await response.json()
                        results["filtered_users"] = {
                            "success": True,
                            "filtered_count": len(data.get("data", {}).get("users", []))
                        }
                    else:
                        results["filtered_users"] = {
                            "success": False,
                            "response_code": response.status
                        }
        except Exception as e:
            results["filtered_users"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_property_account_management(self) -> Dict[str, Any]:
        """4. 프로퍼티 및 계정 조회 테스트"""
        results = {}
        
        # 프로퍼티 목록 조회
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/properties") as response:
                    if response.status == 200:
                        data = await response.json()
                        properties = data.get("properties", [])
                        results["properties"] = {
                            "success": True,
                            "property_count": len(properties)
                        }
                    else:
                        results["properties"] = {
                            "success": False,
                            "response_code": response.status
                        }
        except Exception as e:
            results["properties"] = {"success": False, "error": str(e)}
        
        # 계정 목록 조회
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/accounts") as response:
                    if response.status == 200:
                        data = await response.json()
                        results["accounts"] = {
                            "success": True,
                            "has_data": data is not None
                        }
                    else:
                        results["accounts"] = {
                            "success": False,
                            "response_code": response.status
                        }
        except Exception as e:
            results["accounts"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_notification_system(self) -> Dict[str, Any]:
        """5. 알림 시스템 테스트"""
        results = {}
        
        # 알림 통계 조회
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/notification-stats") as response:
                    results["notification_stats"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["notification_stats"] = {"success": False, "error": str(e)}
        
        # 테스트 알림 발송
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/send-test-notification", json={
                    "email": "test@example.com",
                    "notification_type": "welcome"
                }) as response:
                    results["test_notification"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["test_notification"] = {"success": False, "error": str(e)}
        
        # 알림 로그 조회
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/notification-logs") as response:
                    results["notification_logs"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["notification_logs"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_scheduler_functions(self) -> Dict[str, Any]:
        """6. 스케줄러 테스트"""
        results = {}
        
        # 스케줄러 상태 확인
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/scheduler-status") as response:
                    results["scheduler_status"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["scheduler_status"] = {"success": False, "error": str(e)}
        
        # 만료 알림 처리
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/process-expiry-notifications") as response:
                    results["expiry_notifications"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["expiry_notifications"] = {"success": False, "error": str(e)}
        
        # 만료된 사용자 처리
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/process-expired-users") as response:
                    results["expired_users"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["expired_users"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_performance(self) -> Dict[str, Any]:
        """7. 성능 테스트"""
        results = {}
        
        # 동시 요청 테스트 (10개)
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for i in range(10):
                    task = session.get(f"{self.base_url}/api/stats")
                    tasks.append(task)
                
                start_time = datetime.now()
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = datetime.now()
                
                success_count = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
                total_time = (end_time - start_time).total_seconds()
                
                results["concurrent_requests"] = {
                    "success": success_count >= 8 and total_time < 5.0,
                    "total_requests": 10,
                    "successful_requests": success_count,
                    "total_time": total_time,
                    "avg_response_time": total_time / 10
                }
                
        except Exception as e:
            results["concurrent_requests"] = {"success": False, "error": str(e)}
        
        # 단일 요청 응답 시간 테스트
        try:
            async with aiohttp.ClientSession() as session:
                times = []
                for i in range(5):
                    start_time = datetime.now()
                    async with session.get(f"{self.base_url}/api/users") as response:
                        end_time = datetime.now()
                        if response.status == 200:
                            times.append((end_time - start_time).total_seconds())
                
                if times:
                    avg_time = sum(times) / len(times)
                    results["response_time"] = {
                        "success": avg_time < 1.0,
                        "average_time": avg_time,
                        "max_time": max(times),
                        "min_time": min(times)
                    }
                else:
                    results["response_time"] = {"success": False, "error": "모든 요청 실패"}
                    
        except Exception as e:
            results["response_time"] = {"success": False, "error": str(e)}
        
        return results
    
    async def test_admin_functions(self) -> Dict[str, Any]:
        """8. 관리자 기능 테스트"""
        results = {}
        
        # 프로퍼티 스캔
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/scan") as response:
                    results["property_scan"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["property_scan"] = {"success": False, "error": str(e)}
        
        # 등록 대기열 처리
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/process-queue") as response:
                    results["process_queue"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["process_queue"] = {"success": False, "error": str(e)}
        
        # 수동 유지보수
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/run-maintenance") as response:
                    results["maintenance"] = {
                        "success": response.status == 200,
                        "response_code": response.status
                    }
        except Exception as e:
            results["maintenance"] = {"success": False, "error": str(e)}
        
        return results
    
    async def save_results_and_report(self):
        """결과 저장 및 리포트 생성"""
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_realistic_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "test_results": self.test_results
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 테스트 결과 저장됨: {filename}")
        
        # 리포트 생성
        print("\n" + "=" * 60)
        print("📊 GA4 권한 관리 시스템 실제 API 테스트 결과")
        print("=" * 60)
        
        total_suites = len(self.test_results)
        successful_suites = 0
        
        for suite_name, results in self.test_results.items():
            success = self.evaluate_suite_success(results)
            if success:
                successful_suites += 1
                print(f"✅ {suite_name}: 성공")
            else:
                print(f"❌ {suite_name}: 실패")
                if "error" in results:
                    print(f"   오류: {results['error']}")
        
        print(f"\n📈 전체 결과: {successful_suites}/{total_suites} 테스트 스위트 성공")
        success_rate = (successful_suites / total_suites) * 100
        print(f"🎯 성공률: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 시스템이 완벽하게 작동하고 있습니다!")
        elif success_rate >= 80:
            print("✅ 시스템이 안정적으로 작동하고 있습니다!")
        elif success_rate >= 60:
            print("⚠️ 일부 기능에 개선이 필요합니다.")
        else:
            print("🚨 시스템에 중요한 문제가 있습니다.")
        
        # 상세 통계
        print(f"\n📊 상세 통계:")
        for suite_name, results in self.test_results.items():
            if isinstance(results, dict) and "error" not in results:
                success_items = [item for item in results.values() 
                               if isinstance(item, dict) and item.get("success", False)]
                total_items = [item for item in results.values() 
                              if isinstance(item, dict) and "success" in item]
                
                if total_items:
                    suite_rate = (len(success_items) / len(total_items)) * 100
                    print(f"   {suite_name}: {len(success_items)}/{len(total_items)} ({suite_rate:.1f}%)")

async def main():
    """테스트 실행"""
    runner = GA4RealisticTestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())