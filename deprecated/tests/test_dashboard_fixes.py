#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드 오류 수정 테스트
=======================

대시보드에서 발생하는 오류들을 테스트하고 수정
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_scheduler_initialize_method_exists():
    """GA4Scheduler에 initialize 메서드가 있는지 테스트"""
    try:
        from src.api.scheduler import GA4Scheduler
        
        scheduler = GA4Scheduler()
        
        # initialize 메서드가 있는지 확인
        assert hasattr(scheduler, 'initialize'), "GA4Scheduler에 initialize 메서드가 없습니다"
        
        # 메서드가 호출 가능한지 확인
        assert callable(getattr(scheduler, 'initialize')), "initialize가 호출 가능하지 않습니다"
        
        print("✅ GA4Scheduler.initialize 메서드 존재 확인")
        
    except Exception as e:
        pytest.fail(f"❌ GA4Scheduler.initialize 테스트 실패: {e}")


def test_database_manager_close_method():
    """DatabaseManager에 close 메서드가 있는지 테스트"""
    try:
        from src.infrastructure.database import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # close 메서드가 있는지 확인
        assert hasattr(db_manager, 'close'), "DatabaseManager에 close 메서드가 없습니다"
        
        print("✅ DatabaseManager.close 메서드 존재 확인")
        
    except Exception as e:
        pytest.fail(f"❌ DatabaseManager.close 테스트 실패: {e}")


def test_notification_service_database_columns():
    """알림 서비스에서 사용하는 데이터베이스 컬럼들이 존재하는지 테스트"""
    try:
        from src.infrastructure.database import DatabaseManager
        import aiosqlite
        
        async def check_columns():
            db_manager = DatabaseManager()
            await db_manager.initialize_database()
            
            # notification_logs 테이블의 컬럼 확인
            async with aiosqlite.connect(db_manager.db_path) as db:
                cursor = await db.execute("PRAGMA table_info(notification_logs)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                required_columns = ['user_email', 'notification_type', 'sent_at']
                for col in required_columns:
                    assert col in column_names, f"notification_logs 테이블에 {col} 컬럼이 없습니다"
                
                # user_registrations 테이블의 컬럼 확인
                cursor = await db.execute("PRAGMA table_info(user_registrations)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # expiry_date 컬럼이 있는지 확인
                assert 'expiry_date' in column_names, "user_registrations 테이블에 expiry_date 컬럼이 없습니다"
        
        asyncio.run(check_columns())
        print("✅ 데이터베이스 컬럼 존재 확인")
        
    except Exception as e:
        pytest.fail(f"❌ 데이터베이스 컬럼 테스트 실패: {e}")


if __name__ == "__main__":
    print("🧪 대시보드 오류 수정 테스트 시작")
    
    test_scheduler_initialize_method_exists()
    test_database_manager_close_method()
    test_notification_service_database_columns()
    
    print("✅ 모든 테스트 완료") 