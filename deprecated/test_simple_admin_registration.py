#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 Admin 등록 테스트
"""

import asyncio
import sys
import requests
sys.path.append('/Users/seong-won-yeong/Dev/ga4AdminAutomation')
from src.infrastructure.database import DatabaseManager

async def test_simple_admin_registration():
    """간단한 Admin 등록 테스트"""
    db_manager = DatabaseManager()
    
    # 테스트 데이터 정리
    await db_manager.execute_update(
        "DELETE FROM user_registrations WHERE 등록_계정 = 'simple.test@example.com'"
    )
    await db_manager.execute_update(
        "DELETE FROM notification_logs WHERE user_email = 'simple.test@example.com'"
    )
    
    print("🧪 테스트 시작: requests로 Admin 등록 요청")
    
    # requests로 등록 요청
    data = {
        '신청자': 'simple.tester@example.com',
        '등록_계정_목록': 'simple.test@example.com',
        'property_ids': '462884506',
        '권한': 'admin'
    }
    
    try:
        response = requests.post(
            'http://localhost:8001/api/register',
            data=data
        )
        print(f"📋 응답 상태: {response.status_code}")
        print(f"📋 응답 내용: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 요청 에러: {e}")
        return
    
    # 잠시 대기
    await asyncio.sleep(3)
    
    # DB 확인
    registrations = await db_manager.execute_query(
        "SELECT * FROM user_registrations WHERE 등록_계정 = 'simple.test@example.com'"
    )
    print(f"📊 등록 레코드 수: {len(registrations)}")
    if registrations:
        print(f"📋 등록 정보: {registrations[0]}")
    
    # 알림 로그 확인
    notifications = await db_manager.execute_query(
        "SELECT * FROM notification_logs WHERE user_email = 'simple.test@example.com'"
    )
    print(f"📧 알림 로그 수: {len(notifications)}")
    if notifications:
        for n in notifications:
            print(f"📧 알림: {n}")
    
    # 최근 모든 알림 확인
    recent_notifications = await db_manager.execute_query(
        "SELECT * FROM notification_logs ORDER BY sent_at DESC LIMIT 5"
    )
    print(f"📧 최근 알림 5개:")
    for n in recent_notifications:
        print(f"📧 {n['user_email']}: {n['notification_type']} at {n['sent_at']}")

if __name__ == "__main__":
    asyncio.run(test_simple_admin_registration()) 