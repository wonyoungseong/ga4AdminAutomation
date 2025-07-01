#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 알림 시스템 수정 테스트
========================

승인 대기 알림이 누락된 문제를 수정한 후 테스트
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_notification_system():
    """수정된 알림 시스템 테스트"""
    print("🧪 최종 알림 시스템 수정 테스트 시작")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # 1. Editor 권한 등록 테스트
        print("\n1️⃣ Editor 권한 등록 테스트")
        print("-" * 30)
        
        editor_data = {
            '신청자': '최종 테스트 - Editor',
            '등록_계정_목록': 'wonyoungseong@gmail.com',
            'property_ids': ['462884506'],
            '권한': 'editor'
        }
        
        try:
            async with session.post(f"{base_url}/api/register", data=editor_data) as response:
                result = await response.json()
                print(f"📝 Editor 등록 응답: {response.status}")
                print(f"📊 결과: {result}")
                
                if result.get('success'):
                    print("✅ Editor 권한 등록 성공")
                else:
                    print("❌ Editor 권한 등록 실패")
                    
        except Exception as e:
            print(f"❌ Editor 등록 테스트 실패: {e}")
        
        # 잠시 대기
        await asyncio.sleep(3)
        
        # 2. Admin 권한 등록 테스트
        print("\n2️⃣ Admin 권한 등록 테스트")
        print("-" * 30)
        
        admin_data = {
            '신청자': '최종 테스트 - Admin',
            '등록_계정_목록': 'wonyoungseong@gmail.com',
            'property_ids': ['462884506'],
            '권한': 'admin'
        }
        
        try:
            async with session.post(f"{base_url}/api/register", data=admin_data) as response:
                result = await response.json()
                print(f"📝 Admin 등록 응답: {response.status}")
                print(f"📊 결과: {result}")
                
                if result.get('success'):
                    print("✅ Admin 권한 등록 성공")
                else:
                    print("❌ Admin 권한 등록 실패")
                    
        except Exception as e:
            print(f"❌ Admin 등록 테스트 실패: {e}")
        
        # 잠시 대기
        await asyncio.sleep(3)
        
        # 3. 알림 로그 확인
        print("\n3️⃣ 알림 로그 확인")
        print("-" * 30)
        
        try:
            async with session.get(f"{base_url}/api/notification-logs") as response:
                logs_result = await response.json()
                
                if logs_result.get('success'):
                    logs = logs_result['data']['logs']
                    wonyoung_logs = [log for log in logs if log['user_email'] == 'wonyoungseong@gmail.com']
                    
                    print(f"📧 wonyoungseong@gmail.com 최근 알림 ({len(wonyoung_logs)}개):")
                    for i, log in enumerate(wonyoung_logs[:10], 1):
                        print(f"  {i}. {log['notification_type']:20} | {log['status']:6} | {log['sent_at']}")
                        if log.get('subject'):
                            print(f"     제목: {log['subject']}")
                    
                    # 승인 대기 알림이 있는지 확인
                    pending_logs = [log for log in wonyoung_logs if 'pending' in log['notification_type'].lower()]
                    if pending_logs:
                        print(f"✅ 승인 대기 알림 발송됨: {len(pending_logs)}개")
                    else:
                        print("❌ 승인 대기 알림이 발송되지 않음")
                    
                else:
                    print("❌ 알림 로그 조회 실패")
                    
        except Exception as e:
            print(f"❌ 알림 로그 확인 실패: {e}")
        
        # 4. 사용자 등록 상태 확인
        print("\n4️⃣ 사용자 등록 상태 확인")
        print("-" * 30)
        
        try:
            # 데이터베이스 직접 조회
            from src.infrastructure.database import db_manager
            
            registrations = await db_manager.execute_query('''
                SELECT id, 신청자, 권한, status, 신청일
                FROM user_registrations 
                WHERE 등록_계정 = 'wonyoungseong@gmail.com'
                ORDER BY 신청일 DESC
                LIMIT 5
            ''')
            
            print("📋 최근 등록 기록:")
            for reg in registrations:
                print(f"  ID:{reg['id']:3d} | {reg['신청자']:20} | {reg['권한']:8} | {reg['status']:15} | {reg['신청일']}")
            
        except Exception as e:
            print(f"❌ 등록 상태 확인 실패: {e}")
        
    print("\n" + "=" * 60)
    print("🎯 테스트 완료")
    print("📧 이메일함에서 다음 알림들을 확인해주세요:")
    print("  - Editor 권한 승인 대기 알림")
    print("  - Admin 권한 승인 대기 알림")
    print("  - 관리자 승인 요청 알림")

if __name__ == "__main__":
    asyncio.run(test_notification_system()) 