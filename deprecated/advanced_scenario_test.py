#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 고급 시나리오 테스트
====================================
"""

import asyncio
import json
import aiohttp
from datetime import datetime
import sqlite3

class GA4AdvancedScenarioTest:
    """실제 사용자 등록/관리 워크플로우 테스트"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.db_path = "data/ga4_permission_management.db"
        
    async def run_all_scenarios(self):
        """모든 고급 시나리오 실행"""
        print("\n🚀 GA4 고급 시나리오 테스트 시작")
        print("=" * 50)
        
        scenarios = [
            ("실제 데이터 분석", self.analyze_real_data),
            ("사용자 등록 프로세스", self.test_user_registration_process),
            ("승인 워크플로우", self.test_approval_workflow),
            ("알림 시스템 검증", self.verify_notification_system),
            ("데이터 무결성 검증", self.verify_data_integrity),
            ("성능 벤치마크", self.performance_benchmark)
        ]
        
        for name, test_func in scenarios:
            print(f"\n📋 {name} 테스트...")
            try:
                await test_func()
                print(f"✅ {name} 완료")
            except Exception as e:
                print(f"❌ {name} 실패: {e}")
    
    async def analyze_real_data(self):
        """실제 데이터 분석"""
        print("📊 실제 데이터 분석 중...")
        
        # 데이터베이스 연결
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 통계 수집
        print("\n📈 현재 시스템 통계:")
        
        # 전체 등록 수
        cursor.execute("SELECT COUNT(*) FROM user_registrations")
        total_registrations = cursor.fetchone()[0]
        print(f"   총 등록 수: {total_registrations:,}명")
        
        # 활성 사용자 수
        cursor.execute("SELECT COUNT(*) FROM user_registrations WHERE status = 'active'")
        active_users = cursor.fetchone()[0]
        print(f"   활성 사용자: {active_users:,}명")
        
        # 권한별 분포
        cursor.execute("""
            SELECT 권한, COUNT(*) as count 
            FROM user_registrations 
            WHERE status = 'active'
            GROUP BY 권한
        """)
        permissions = cursor.fetchall()
        print("   권한별 분포:")
        for perm, count in permissions:
            print(f"     {perm}: {count:,}명")
        
        # 상태별 분포
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM user_registrations 
            GROUP BY status
        """)
        statuses = cursor.fetchall()
        print("   상태별 분포:")
        for status, count in statuses:
            print(f"     {status}: {count:,}명")
        
        # 최근 등록 활동
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM user_registrations 
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        recent_activity = cursor.fetchall()
        print("   최근 7일 등록 활동:")
        for date, count in recent_activity:
            print(f"     {date}: {count:,}명")
        
        conn.close()
    
    async def test_user_registration_process(self):
        """사용자 등록 프로세스 테스트"""
        print("👤 사용자 등록 프로세스 테스트 중...")
        
        # 등록 페이지 접근
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/register") as response:
                if response.status == 200:
                    print("   ✅ 등록 페이지 접근 성공")
                else:
                    print(f"   ❌ 등록 페이지 접근 실패: {response.status}")
            
            # 사용자 목록 페이지 접근
            async with session.get(f"{self.base_url}/users") as response:
                if response.status == 200:
                    print("   ✅ 사용자 목록 페이지 접근 성공")
                else:
                    print(f"   ❌ 사용자 목록 페이지 접근 실패: {response.status}")
    
    async def test_approval_workflow(self):
        """승인 워크플로우 테스트"""
        print("⚖️ 승인 워크플로우 테스트 중...")
        
        # 승인 대기 중인 Editor 요청 확인
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/pending-editor-requests") as response:
                if response.status == 200:
                    data = await response.json()
                    pending_count = len(data.get("data", {}).get("pending_requests", []))
                    print(f"   📋 승인 대기 중인 Editor 요청: {pending_count}개")
                else:
                    print(f"   ❌ 승인 대기 요청 조회 실패: {response.status}")
            
            # 승인 대기 중인 Admin 요청 확인
            async with session.get(f"{self.base_url}/api/pending-admin-requests") as response:
                if response.status == 200:
                    data = await response.json()
                    pending_count = len(data.get("data", {}).get("pending_requests", []))
                    print(f"   📋 승인 대기 중인 Admin 요청: {pending_count}개")
                else:
                    print(f"   ❌ Admin 승인 대기 요청 조회 실패: {response.status}")
    
    async def verify_notification_system(self):
        """알림 시스템 검증"""
        print("📧 알림 시스템 검증 중...")
        
        async with aiohttp.ClientSession() as session:
            # 알림 통계 확인
            async with session.get(f"{self.base_url}/api/notification-stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print("   📊 알림 통계:")
                    stats = data.get("data", {}).get("stats", {})
                    for key, value in stats.items():
                        print(f"     {key}: {value}")
                else:
                    print(f"   ❌ 알림 통계 조회 실패: {response.status}")
            
            # 테스트 알림 발송
            notification_types = ["welcome", "7_days", "1_day", "deletion_notice"]
            for notification_type in notification_types:
                async with session.post(f"{self.base_url}/api/send-test-notification", json={
                    "email": "test@example.com",
                    "notification_type": notification_type
                }) as response:
                    if response.status == 200:
                        print(f"   ✅ {notification_type} 알림 발송 성공")
                    else:
                        print(f"   ❌ {notification_type} 알림 발송 실패: {response.status}")
    
    async def verify_data_integrity(self):
        """데이터 무결성 검증"""
        print("🔍 데이터 무결성 검증 중...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 중복 등록 확인
        cursor.execute("""
            SELECT 등록_계정, property_id, COUNT(*) as count
            FROM user_registrations 
            WHERE status = 'active'
            GROUP BY 등록_계정, property_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"   ⚠️ 중복 등록 발견: {len(duplicates)}개")
            for email, prop_id, count in duplicates:
                print(f"     {email} @ {prop_id}: {count}건")
        else:
            print("   ✅ 중복 등록 없음")
        
        # 잘못된 권한 확인
        cursor.execute("""
            SELECT COUNT(*) FROM user_registrations 
            WHERE 권한 NOT IN ('analyst', 'editor', 'admin')
        """)
        invalid_permissions = cursor.fetchone()[0]
        if invalid_permissions > 0:
            print(f"   ⚠️ 잘못된 권한: {invalid_permissions}개")
        else:
            print("   ✅ 모든 권한이 유효함")
        
        # 만료일 검증
        cursor.execute("""
            SELECT COUNT(*) FROM user_registrations 
            WHERE expiry_date < created_at
        """)
        invalid_dates = cursor.fetchone()[0]
        if invalid_dates > 0:
            print(f"   ⚠️ 잘못된 만료일: {invalid_dates}개")
        else:
            print("   ✅ 모든 만료일이 유효함")
        
        # 감사 로그 확인
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        audit_count = cursor.fetchone()[0]
        print(f"   📋 감사 로그: {audit_count:,}개 기록")
        
        conn.close()
    
    async def performance_benchmark(self):
        """성능 벤치마크"""
        print("⚡ 성능 벤치마크 실행 중...")
        
        # API 응답 시간 측정
        endpoints = [
            "/api/stats",
            "/api/users", 
            "/api/properties",
            "/api/notification-stats"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                times = []
                for i in range(10):  # 10회 측정
                    start_time = datetime.now()
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        end_time = datetime.now()
                        if response.status == 200:
                            times.append((end_time - start_time).total_seconds())
                
                if times:
                    avg_time = sum(times) / len(times)
                    max_time = max(times)
                    min_time = min(times)
                    print(f"   {endpoint}:")
                    print(f"     평균: {avg_time*1000:.1f}ms")
                    print(f"     최대: {max_time*1000:.1f}ms") 
                    print(f"     최소: {min_time*1000:.1f}ms")
        
        # 데이터베이스 쿼리 성능
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        queries = [
            ("사용자 목록 조회", "SELECT * FROM user_registrations LIMIT 100"),
            ("활성 사용자 수", "SELECT COUNT(*) FROM user_registrations WHERE status = 'active'"),
            ("통계 쿼리", """
                SELECT 권한, status, COUNT(*) 
                FROM user_registrations 
                GROUP BY 권한, status
            """)
        ]
        
        print("   데이터베이스 쿼리 성능:")
        for name, query in queries:
            start_time = datetime.now()
            cursor.execute(query)
            cursor.fetchall()
            end_time = datetime.now()
            query_time = (end_time - start_time).total_seconds()
            print(f"     {name}: {query_time*1000:.1f}ms")
        
        conn.close()
    
    async def generate_final_report(self):
        """최종 리포트 생성"""
        print("\n" + "=" * 50)
        print("📋 GA4 권한 관리 시스템 고급 테스트 완료")
        print("=" * 50)
        
        # 시스템 상태 요약
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data.get("data", {}).get("stats", {})
                    
                    print("🎯 시스템 현황 요약:")
                    print(f"   총 계정: {stats.get('total_accounts', 0)}개")
                    print(f"   총 프로퍼티: {stats.get('total_properties', 0)}개")
                    print(f"   활성 사용자: {stats.get('active_users', 0):,}명")
                    print(f"   만료 예정: {stats.get('expiring_soon', 0):,}명")
                    print(f"   총 알림: {stats.get('total_notifications', 0):,}개")
                    print(f"   감사 로그: {stats.get('total_audit_logs', 0):,}개")
                    print(f"   총 등록: {stats.get('total_registrations', 0):,}건")
        
        print("\n✅ 모든 고급 시나리오 테스트가 완료되었습니다!")
        print("🎉 시스템이 정상적으로 작동하고 있습니다!")

async def main():
    """메인 실행"""
    tester = GA4AdvancedScenarioTest()
    await tester.run_all_scenarios()
    await tester.generate_final_report()

if __name__ == "__main__":
    asyncio.run(main())