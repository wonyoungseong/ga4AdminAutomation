#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 스키마 마이그레이션
=============================

기존 데이터베이스를 새로운 스키마로 업데이트합니다.
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.database import DatabaseManager
from src.core.logger import get_ga4_logger

async def migrate_notification_table_constraints(db_manager):
    """notification_logs 테이블 제약조건 업데이트"""
    logger = get_ga4_logger()
    
    try:
        logger.info("🔧 notification_logs 테이블 제약조건 업데이트 시작")
        
        # 기존 데이터 백업
        existing_data = await db_manager.execute_query("SELECT * FROM notification_logs")
        
        # 임시 테이블 생성
        await db_manager.execute_update("""
            CREATE TABLE notification_logs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_registration_id INTEGER,
                user_email TEXT NOT NULL,
                notification_type TEXT NOT NULL CHECK (notification_type IN ('30_days', '7_days', '1_day', 'today', 'expired', 'extension_approved', 'welcome', 'test')),
                property_id TEXT,
                sent_to TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_subject TEXT,
                message_body TEXT,
                status TEXT DEFAULT 'sent' CHECK (status IN ('sent', 'failed', 'pending')),
                response_received BOOLEAN DEFAULT FALSE,
                response_content TEXT,
                FOREIGN KEY (user_registration_id) REFERENCES user_registrations(id)
            )
        """)
        
        # 기존 데이터를 새 테이블로 복사
        if existing_data:
            for row in existing_data:
                # 누락된 컬럼에 기본값 설정
                user_email = row.get('user_email', row.get('sent_to', ''))
                property_id = row.get('property_id', '')
                status = row.get('status', 'sent')
                
                await db_manager.execute_update("""
                    INSERT INTO notification_logs_new 
                    (id, user_registration_id, user_email, notification_type, property_id, sent_to, sent_at, message_subject, message_body, status, response_received, response_content)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['id'],
                    row.get('user_registration_id'),
                    user_email,
                    row['notification_type'],
                    property_id,
                    row['sent_to'],
                    row['sent_at'],
                    row.get('message_subject'),
                    row.get('message_body'),
                    status,
                    row.get('response_received', False),
                    row.get('response_content')
                ))
        
        # 기존 테이블 삭제하고 새 테이블로 이름 변경
        await db_manager.execute_update("DROP TABLE notification_logs")
        await db_manager.execute_update("ALTER TABLE notification_logs_new RENAME TO notification_logs")
        
        logger.info("✅ notification_logs 테이블 제약조건 업데이트 완료")
        
    except Exception as e:
        logger.error(f"❌ notification_logs 테이블 업데이트 실패: {e}")
        raise

async def migrate_database():
    """데이터베이스 마이그레이션 실행"""
    logger = get_ga4_logger()
    
    logger.info("🔄 데이터베이스 스키마 마이그레이션 시작")
    
    try:
        # 기존 데이터베이스 백업
        db_manager = DatabaseManager()
        backup_path = f"backups/ga4_permission_management_backup_{asyncio.get_event_loop().time():.0f}.db"
        
        logger.info(f"📦 데이터베이스 백업 생성: {backup_path}")
        await db_manager.backup_database(backup_path)
        
        # 기본 마이그레이션 실행
        logger.info("🔧 기본 스키마 마이그레이션 실행")
        await db_manager.initialize_database()
        
        # notification_logs 테이블 제약조건 업데이트
        await migrate_notification_table_constraints(db_manager)
        
        # 마이그레이션 검증
        logger.info("🔍 마이그레이션 검증")
        
        # 테이블 스키마 확인
        audit_logs_schema = await db_manager.execute_query("PRAGMA table_info(audit_logs)")
        notification_logs_schema = await db_manager.execute_query("PRAGMA table_info(notification_logs)")
        
        # audit_logs 검증
        audit_columns = [row['name'] for row in audit_logs_schema]
        required_audit_columns = ['id', 'timestamp', 'action', 'user_email', 'property_id', 'details', 'created_at']
        missing_audit = [col for col in required_audit_columns if col not in audit_columns]
        
        if missing_audit:
            logger.error(f"❌ audit_logs 테이블에 누락된 컬럼: {missing_audit}")
        else:
            logger.info("✅ audit_logs 테이블 스키마 검증 완료")
        
        # notification_logs 검증
        notification_columns = [row['name'] for row in notification_logs_schema]
        required_notification_columns = ['id', 'user_email', 'notification_type', 'property_id', 'status', 'sent_at']
        missing_notification = [col for col in required_notification_columns if col not in notification_columns]
        
        if missing_notification:
            logger.error(f"❌ notification_logs 테이블에 누락된 컬럼: {missing_notification}")
        else:
            logger.info("✅ notification_logs 테이블 스키마 검증 완료")
        
        # 통계 정보 출력
        stats = await db_manager.get_database_stats()
        logger.info("📊 데이터베이스 통계:")
        for key, value in stats.items():
            logger.info(f"   - {key}: {value}")
        
        logger.info("🎉 데이터베이스 스키마 마이그레이션 완료")
        
    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_database()) 