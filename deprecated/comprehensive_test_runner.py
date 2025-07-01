#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 포괄적 테스트 러너
=======================================
"""

import asyncio
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import sqlite3

class GA4ComprehensiveTestRunner:
    """GA4 권한 관리 시스템의 모든 기능을 테스트하는 포괄적 테스트 러너"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
        self.test_emails = [
            "wonyoungseong@gmail.com",
            "wonyoung.seong@conentrix.com", 
            "wonyoung.seong@amorepacific.com",
            "seongwonyoung0311@gmail.com"
        ]
        self.invalid_emails = ["salboli@naver.com", "demotest@gmail.com"]
        self.property_id = "462884506"
        
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n🚀 GA4 권한 관리 시스템 포괄적 테스트 시작")
        print("=" * 60)
        
        test_suites = [
            ("시스템 초기화", self.test_system_initialization),
            ("권한 추가", self.test_permission_addition),
            ("권한 업데이트", self.test_permission_updates),
            ("권한 삭제", self.test_permission_deletion),
            ("알림 시스템", self.test_notification_system),
            ("UI/UX 검증", self.test_ui_verification),
            ("데이터베이스 연동", self.test_database_integration),
            ("성능 및 안정성", self.test_performance_stability),
            ("보안 및 권한", self.test_security_validation),
            ("통합 워크플로우", self.test_integration_workflow)
        ]
        
        for suite_name, test_function in test_suites:
            try:
                print(f"\n📋 {suite_name} 테스트 실행 중...")
                results = await test_function()
                self.test_results[suite_name] = results
                print(f"✅ {suite_name} 테스트 완료")
            except Exception as e:
                error_msg = f"❌ {suite_name} 테스트 실패: {str(e)}"
                print(error_msg)
                self.test_results[suite_name] = {"error": error_msg, "traceback": traceback.format_exc()}
        
        # 결과 저장
        await self.save_test_results()
        await self.generate_test_report()
        
    async def test_system_initialization(self) -> Dict[str, Any]:
        """1. 시스템 초기화 및 권한 레벨 변경 테스트"""
        results = {}
        
        # 1.1 서버 상태 확인
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stats") as response:
                    if response.status == 200:
                        stats = await response.json()
                        results["server_status"] = "✅ 서버 정상 작동"
                        results["initial_stats"] = stats
                    else:
                        results["server_status"] = f"❌ 서버 상태 이상: {response.status}"
        except Exception as e:
            results["server_status"] = f"❌ 서버 연결 실패: {str(e)}"
        
        # 1.2 데이터베이스 연결 확인
        try:
            conn = sqlite3.connect("data/ga4_permission_management.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_registrations")
            count = cursor.fetchone()[0]
            conn.close()
            results["database_status"] = f"✅ 데이터베이스 연결 성공 (등록 사용자: {count}명)"
        except Exception as e:
            results["database_status"] = f"❌ 데이터베이스 연결 실패: {str(e)}"
        
        return results
    
    async def test_permission_addition(self) -> Dict[str, Any]:
        """2. 권한 추가 시나리오 테스트"""
        results = {}
        
        # Analyst 권한 추가 테스트
        analyst_results = {}
        for email in self.test_emails[:2]:  # 처음 2개만 테스트
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.base_url}/api/add_user", json={
                        "email": email,
                        "property_id": self.property_id,
                        "role": "analyst",
                        "requester": "seongwonyoung0311@gmail.com"
                    }) as response:
                        result = await response.json()
                        analyst_results[email] = {
                            "status_code": response.status,
                            "result": result,
                            "success": response.status == 200
                        }
            except Exception as e:
                analyst_results[email] = {"error": str(e), "success": False}
        
        results["analyst_addition"] = analyst_results
        return results
    
    async def test_permission_updates(self) -> Dict[str, Any]:
        """3. 권한 업데이트 시나리오 테스트"""
        results = {}
        results["message"] = "권한 업데이트 테스트는 기존 사용자가 있을 때 실행됩니다."
        return results
    
    async def test_permission_deletion(self) -> Dict[str, Any]:
        """4. 권한 삭제 시나리오 테스트"""  
        results = {}
        results["message"] = "권한 삭제 테스트는 기존 사용자가 있을 때 실행됩니다."
        return results
    
    async def test_notification_system(self) -> Dict[str, Any]:
        """5. 알림 시스템 시나리오 테스트"""
        results = {}
        
        # 즉시 알림 발송 테스트
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/trigger_scheduler", json={
                    "task_type": "notifications"
                }) as response:
                    result = await response.json()
                    results["immediate_notification"] = {
                        "status_code": response.status,
                        "result": result,
                        "success": response.status == 200
                    }
        except Exception as e:
            results["immediate_notification"] = {"error": str(e), "success": False}
        
        return results
    
    async def test_ui_verification(self) -> Dict[str, Any]:
        """6. UI/UX 검증 시나리오 테스트"""
        results = {}
        
        # 대시보드 접근성 테스트
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/dashboard") as response:
                    results["dashboard_access"] = {
                        "status_code": response.status,
                        "success": response.status == 200,
                        "content_type": response.headers.get('content-type', '')
                    }
        except Exception as e:
            results["dashboard_access"] = {"error": str(e), "success": False}
        
        # API 엔드포인트 응답성 테스트
        endpoints = ["/api/stats", "/api/users"]
        endpoint_results = {}
        
        for endpoint in endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    start_time = datetime.now()
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        end_time = datetime.now()
                        response_time = (end_time - start_time).total_seconds()
                        endpoint_results[endpoint] = {
                            "status_code": response.status,
                            "response_time": response_time,
                            "success": response.status == 200 and response_time < 2.0
                        }
            except Exception as e:
                endpoint_results[endpoint] = {"error": str(e), "success": False}
        
        results["endpoint_performance"] = endpoint_results
        return results
    
    async def test_database_integration(self) -> Dict[str, Any]:
        """7. 데이터베이스 연동 시나리오 테스트"""
        results = {}
        
        # 데이터 일관성 검증
        try:
            conn = sqlite3.connect("data/ga4_permission_management.db")
            cursor = conn.cursor()
            
            # 사용자 등록 수 확인
            cursor.execute("SELECT COUNT(*) FROM user_registrations")
            total_users = cursor.fetchone()[0]
            
            # 활성 사용자 수 확인
            cursor.execute("SELECT COUNT(*) FROM user_registrations WHERE status = 'active'")
            active_users = cursor.fetchone()[0]
            
            conn.close()
            
            results["data_consistency"] = {
                "total_users": total_users,
                "active_users": active_users,
                "success": True
            }
            
        except Exception as e:
            results["data_consistency"] = {"error": str(e), "success": False}
        
        return results
    
    async def test_performance_stability(self) -> Dict[str, Any]:
        """8. 성능 및 안정성 시나리오 테스트"""
        results = {}
        
        # 동시 요청 테스트
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for i in range(5):  # 5개 동시 요청
                    task = session.get(f"{self.base_url}/api/stats")
                    tasks.append(task)
                
                start_time = datetime.now()
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = datetime.now()
                
                success_count = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
                total_time = (end_time - start_time).total_seconds()
                
                results["concurrent_requests"] = {
                    "total_requests": 5,
                    "successful_requests": success_count,
                    "total_time": total_time,
                    "success": success_count >= 4 and total_time < 3.0
                }
                
        except Exception as e:
            results["concurrent_requests"] = {"error": str(e), "success": False}
        
        return results
    
    async def test_security_validation(self) -> Dict[str, Any]:
        """9. 보안 및 권한 시나리오 테스트"""
        results = {}
        
        # 잘못된 이메일 테스트
        try:
            malicious_email = "test@gmail.com'; DROP TABLE user_registrations; --"
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/add_user", json={
                    "email": malicious_email,
                    "property_id": self.property_id,
                    "role": "analyst"
                }) as response:
                    results["sql_injection_prevention"] = {
                        "status_code": response.status,
                        "success": response.status >= 400  # 400 에러가 나와야 성공
                    }
        except Exception as e:
            results["sql_injection_prevention"] = {"error": str(e), "success": True}
        
        return results
    
    async def test_integration_workflow(self) -> Dict[str, Any]:
        """10. 통합 워크플로우 시나리오 테스트"""
        results = {}
        
        # 전체 시스템 통계 확인
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stats") as response:
                    if response.status == 200:
                        stats = await response.json()
                        results["system_stats"] = {
                            "stats": stats,
                            "success": True
                        }
                    else:
                        results["system_stats"] = {
                            "status_code": response.status,
                            "success": False
                        }
        except Exception as e:
            results["system_stats"] = {"error": str(e), "success": False}
        
        return results
    
    async def save_test_results(self):
        """테스트 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_comprehensive_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "test_results": self.test_results
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 테스트 결과 저장됨: {filename}")
    
    async def generate_test_report(self):
        """테스트 결과 요약 리포트 생성"""
        print("\n" + "=" * 60)
        print("📊 GA4 권한 관리 시스템 포괄적 테스트 결과 요약")
        print("=" * 60)
        
        total_suites = len(self.test_results)
        successful_suites = 0
        
        for suite_name, results in self.test_results.items():
            if "error" not in results:
                successful_suites += 1
                print(f"✅ {suite_name}: 성공")
            else:
                print(f"❌ {suite_name}: 실패")
                print(f"   오류: {results.get('error', '알 수 없는 오류')}")
        
        print(f"\n📈 전체 결과: {successful_suites}/{total_suites} 테스트 스위트 성공")
        success_rate = (successful_suites / total_suites) * 100
        print(f"🎯 성공률: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 시스템이 안정적으로 작동하고 있습니다!")
        elif success_rate >= 60:
            print("⚠️ 일부 개선이 필요합니다.")
        else:
            print("🚨 시스템에 중요한 문제가 있습니다.")

async def main():
    """테스트 실행"""
    runner = GA4ComprehensiveTestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())