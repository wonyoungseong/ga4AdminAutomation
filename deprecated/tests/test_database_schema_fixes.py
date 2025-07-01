#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 스키마 수정 테스트
============================

데이터베이스 스키마 문제를 테스트하고 수정
"""

import pytest
import sys
import os
import asyncio
import aiosqlite

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_and_fix_database_schema():
    """데이터베이스 스키마를 테스트하고 수정"""
    try:
        from src.infrastructure.database import DatabaseManager
        
        db_manager = DatabaseManager()
        await db_manager.initialize_database()
        
        async with aiosqlite.connect(db_manager.db_path) as db:
            # 1. user_registrations 테이블에 expiry_date 컬럼 추가
            try:
                await db.execute("ALTER TABLE user_registrations ADD COLUMN expiry_date TEXT")
                print("✅ user_registrations에 expiry_date 컬럼 추가")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("ℹ️ expiry_date 컬럼이 이미 존재합니다")
                else:
                    print(f"⚠️ expiry_date 컬럼 추가 실패: {e}")
            
            # 2. notification_logs 테이블 구조 확인 및 수정
            cursor = await db.execute("PRAGMA table_info(notification_logs)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # 필요한 컬럼들이 없으면 추가
            required_columns = {
                'user_email': 'TEXT NOT NULL DEFAULT ""',
                'notification_type': 'TEXT NOT NULL DEFAULT "test"',
                'sent_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in column_names:
                    try:
                        await db.execute(f"ALTER TABLE notification_logs ADD COLUMN {col_name} {col_type}")
                        print(f"✅ notification_logs에 {col_name} 컬럼 추가")
                    except Exception as e:
                        print(f"⚠️ {col_name} 컬럼 추가 실패: {e}")
            
            # 3. 기존 데이터에서 expiry_date 값 설정 (종료일 -> expiry_date)
            await db.execute("""
                UPDATE user_registrations 
                SET expiry_date = 종료일 
                WHERE expiry_date IS NULL AND 종료일 IS NOT NULL
            """)
            
            await db.commit()
            print("✅ 데이터베이스 스키마 수정 완료")
            
    except Exception as e:
        print(f"❌ 데이터베이스 스키마 수정 실패: {e}")
        raise


async def test_notification_service_columns():
    """알림 서비스에서 사용하는 컬럼들 테스트"""
    try:
        from src.infrastructure.database import DatabaseManager
        
        db_manager = DatabaseManager()
        await db_manager.initialize_database()
        
        # 테스트 데이터 삽입
        test_data = {
            'user_email': 'test@example.com',
            'notification_type': 'test',
            'property_id': 'test_property',
            'sent_to': 'test@example.com',
            'message_subject': 'Test Subject',
            'message_body': 'Test Body'
        }
        
        insert_query = """
            INSERT INTO notification_logs (user_email, notification_type, property_id, sent_to, message_subject, message_body)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        await db_manager.execute_insert(
            insert_query,
            (test_data['user_email'], test_data['notification_type'], test_data['property_id'],
             test_data['sent_to'], test_data['message_subject'], test_data['message_body'])
        )
        
        print("✅ notification_logs 테이블 삽입 테스트 성공")
        
    except Exception as e:
        print(f"❌ notification_logs 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    print("🔧 데이터베이스 스키마 수정 시작")
    
    asyncio.run(test_and_fix_database_schema())
    asyncio.run(test_notification_service_columns())
    
    print("✅ 데이터베이스 스키마 수정 완료") 