#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Infrastructure
=======================

SQLite 데이터베이스 스키마와 초기화 코드를 제공합니다.
"""

import sqlite3
import aiosqlite
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..core.logger import get_ga4_logger


class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "data/ga4_permission_management.db"):
        self.db_path = db_path
        self.logger = get_ga4_logger()
        
        # 데이터 디렉토리 생성
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize_database(self) -> None:
        """데이터베이스 초기화"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await self._create_tables(db)
                await self._create_indexes(db)
                await self._migrate_database(db)
                await self._insert_default_admin_settings()
                await db.commit()
                
            self.logger.info("✅ 데이터베이스 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
            raise
    
    async def close(self) -> None:
        """데이터베이스 연결 종료"""
        # SQLite는 자동으로 연결이 닫히므로 특별한 작업 불필요
        pass
    
    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        """테이블 생성"""
        
        # 1. GA4 계정 테이블
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ga4_accounts (
                account_id TEXT PRIMARY KEY,
                account_display_name TEXT NOT NULL,
                최초_확인일 TIMESTAMP NOT NULL,
                최근_업데이트일 TIMESTAMP NOT NULL,
                삭제여부 BOOLEAN DEFAULT FALSE,
                현재_존재여부 BOOLEAN DEFAULT TRUE,
                service_account_access BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. GA4 프로퍼티 테이블
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ga4_properties (
                property_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                property_display_name TEXT NOT NULL,
                property_type TEXT,
                최초_확인일 TIMESTAMP NOT NULL,
                최근_업데이트일 TIMESTAMP NOT NULL,
                삭제여부 BOOLEAN DEFAULT FALSE,
                현재_존재여부 BOOLEAN DEFAULT TRUE,
                등록_가능여부 BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES ga4_accounts(account_id)
            )
        ''')
        
        # 3. 사용자 등록 테이블
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                신청자 TEXT NOT NULL,
                등록_계정 TEXT NOT NULL,
                property_id TEXT NOT NULL,
                property_name TEXT,
                권한 TEXT NOT NULL DEFAULT 'analyst' CHECK (권한 IN ('analyst', 'editor', 'admin')),
                신청일 DATETIME DEFAULT CURRENT_TIMESTAMP,
                종료일 DATETIME NOT NULL,
                status TEXT DEFAULT 'pending_approval' CHECK (status IN ('pending_approval', 'active', 'expired', 'rejected', 'deleted')),
                approval_required BOOLEAN DEFAULT 1,
                연장_횟수 INTEGER DEFAULT 0,
                최근_연장일 DATETIME,
                binding_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ga4_registered BOOLEAN DEFAULT 0,
                user_link_name TEXT,
                last_notification_sent DATETIME,
                expiry_date DATETIME,
                FOREIGN KEY (property_id) REFERENCES ga4_properties(property_id)
            )
        ''')
        
        # 4. 알림 로그 테이블
        await db.execute('''
            CREATE TABLE IF NOT EXISTS notification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_registration_id INTEGER,
                user_email TEXT NOT NULL,
                notification_type TEXT NOT NULL CHECK (notification_type IN ('30_days', '7_days', '1_day', 'today', 'expired', 'extension_approved', 'welcome', 'test', 'editor_auto_downgrade', 'admin_notification', 'expiry_warning_30', 'expiry_warning_7', 'expiry_warning_1', 'expiry_warning_today', 'deletion_notice', 'admin_approved', 'editor_approved', 'admin_downgrade', 'immediate_approval', 'daily_summary')),
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
        ''')
        
        # 5. 감사 로그 테이블
        await db.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                user_email TEXT,
                property_id TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT DEFAULT 'user_action',
                target_type TEXT,
                target_id TEXT,
                performed_by TEXT,
                action_details TEXT,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        ''')
        
        # 6. 시스템 설정 테이블
        await db.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 관리자 설정 테이블
        await self.execute_update("""
            CREATE TABLE IF NOT EXISTS admin_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 유효기간 설정 테이블
        await self.execute_update("""
            CREATE TABLE IF NOT EXISTS validity_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                period_days INTEGER NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 담당자 관리 테이블
        await self.execute_update("""
            CREATE TABLE IF NOT EXISTS responsible_persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id TEXT,
                account_id TEXT,
                email TEXT NOT NULL,
                name TEXT,
                role TEXT DEFAULT 'manager',
                is_active INTEGER DEFAULT 1,
                notification_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 알림 설정 테이블
        await self.execute_update("""
            CREATE TABLE IF NOT EXISTS notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT UNIQUE NOT NULL,
                enabled INTEGER DEFAULT 1,
                trigger_days TEXT,
                template_subject TEXT,
                template_body TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _create_indexes(self, db: aiosqlite.Connection) -> None:
        """인덱스 생성"""
        
        # 성능 최적화를 위한 인덱스들
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_properties_account_id ON ga4_properties(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_properties_등록가능 ON ga4_properties(등록_가능여부)",
            "CREATE INDEX IF NOT EXISTS idx_registrations_property_id ON user_registrations(property_id)",
            "CREATE INDEX IF NOT EXISTS idx_registrations_status ON user_registrations(status)",
            "CREATE INDEX IF NOT EXISTS idx_registrations_종료일 ON user_registrations(종료일)",
            "CREATE INDEX IF NOT EXISTS idx_registrations_등록계정 ON user_registrations(등록_계정)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_registration_id ON notification_logs(user_registration_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notification_logs(notification_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs(target_type, target_id)"
        ]
        
        for index_sql in indexes:
            await db.execute(index_sql)
    
    async def _migrate_database(self, db: aiosqlite.Connection) -> None:
        """데이터베이스 마이그레이션"""
        try:
            # user_registrations 테이블에 새로운 컬럼 추가
            await self._add_column_if_not_exists(db, 'user_registrations', 'property_name', 'TEXT')
            await self._add_column_if_not_exists(db, 'user_registrations', 'ga4_registered', 'BOOLEAN DEFAULT 0')
            await self._add_column_if_not_exists(db, 'user_registrations', 'user_link_name', 'TEXT')
            await self._add_column_if_not_exists(db, 'user_registrations', 'last_notification_sent', 'DATETIME')
            await self._add_column_if_not_exists(db, 'user_registrations', 'expiry_date', 'DATETIME')
            
            # notification_logs 테이블에 새로운 컬럼 추가
            await self._add_column_if_not_exists(db, 'notification_logs', 'user_email', 'TEXT')
            await self._add_column_if_not_exists(db, 'notification_logs', 'property_id', 'TEXT')
            await self._add_column_if_not_exists(db, 'notification_logs', 'status', 'TEXT DEFAULT "sent"')
            
            # notification_logs 테이블의 CHECK 제약 조건 업데이트
            await self._update_notification_logs_constraints(db)
            
            # audit_logs 테이블 스키마 업데이트 (기존 컬럼과 호환성 유지)
            await self._add_column_if_not_exists(db, 'audit_logs', 'action', 'TEXT')
            await self._add_column_if_not_exists(db, 'audit_logs', 'user_email', 'TEXT')
            await self._add_column_if_not_exists(db, 'audit_logs', 'property_id', 'TEXT')
            await self._add_column_if_not_exists(db, 'audit_logs', 'details', 'TEXT')
            # created_at 컬럼은 기본값이 함수라서 SQLite에서 추가할 수 없음
            
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 마이그레이션 실패: {e}")
            
    async def _update_notification_logs_constraints(self, db: aiosqlite.Connection) -> None:
        """notification_logs 테이블의 CHECK 제약 조건 업데이트"""
        try:
            # 기존 테이블 구조 확인
            cursor = await db.execute("PRAGMA table_info(notification_logs)")
            columns = await cursor.fetchall()
            
            # 기존 데이터가 있는지 확인
            cursor = await db.execute("SELECT COUNT(*) FROM notification_logs")
            count_result = await cursor.fetchone()
            has_data = count_result[0] > 0 if count_result else False
            
            if has_data:
                # 기존 데이터가 있으면 임시 테이블 생성 후 데이터 이동
                await db.execute('''
                    CREATE TABLE notification_logs_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_registration_id INTEGER,
                        user_email TEXT NOT NULL,
                        notification_type TEXT NOT NULL CHECK (notification_type IN ('30_days', '7_days', '1_day', 'today', 'expired', 'extension_approved', 'welcome', 'test', 'editor_auto_downgrade', 'admin_notification', 'expiry_warning_30', 'expiry_warning_7', 'expiry_warning_1', 'expiry_warning_today', 'deletion_notice', 'admin_approved', 'editor_approved', 'admin_downgrade', 'immediate_approval', 'daily_summary')),
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
                ''')
                
                # 기존 데이터를 새 테이블로 복사 (알림 타입 변환)
                await db.execute('''
                    INSERT INTO notification_logs_new 
                    SELECT id, user_registration_id, user_email,
                           CASE 
                               WHEN notification_type = 'expiry_warning_30' THEN '30_days'
                               WHEN notification_type = 'expiry_warning_7' THEN '7_days'
                               WHEN notification_type = 'expiry_warning_1' THEN '1_day'
                               WHEN notification_type = 'expiry_warning_today' THEN 'today'
                               WHEN notification_type = 'deletion_notice' THEN 'expired'
                               ELSE notification_type
                           END as notification_type,
                           property_id, sent_to, sent_at, message_subject, message_body, 
                           status, response_received, response_content
                    FROM notification_logs
                ''')
                
                # 기존 테이블 삭제 후 새 테이블로 교체
                await db.execute('DROP TABLE notification_logs')
                await db.execute('ALTER TABLE notification_logs_new RENAME TO notification_logs')
                
                self.logger.info("✅ notification_logs 테이블 제약 조건 업데이트 완료")
                
        except Exception as e:
            self.logger.error(f"❌ notification_logs 테이블 제약 조건 업데이트 실패: {e}")
            # 실패 시 새 테이블이 생성되었다면 정리
            try:
                await db.execute('DROP TABLE IF EXISTS notification_logs_new')
            except:
                pass
    
    async def _add_column_if_not_exists(self, db: aiosqlite.Connection, table: str, column: str, column_type: str):
        """컬럼이 존재하지 않으면 추가"""
        try:
            # 테이블 스키마 확인
            cursor = await db.execute(f"PRAGMA table_info({table})")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if column not in column_names:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                self.logger.info(f"✅ 컬럼 추가: {table}.{column}")
                
        except Exception as e:
            self.logger.warning(f"⚠️ 컬럼 추가 실패 {table}.{column}: {e}")
    
    async def get_connection(self) -> aiosqlite.Connection:
        """데이터베이스 연결 반환"""
        return await aiosqlite.connect(self.db_path)
    
    async def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """쿼리 실행 및 결과 반환"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    def execute_query_sync(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """쿼리 실행 및 결과 반환 (동기 버전)"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                cursor = db.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"❌ 동기 쿼리 실행 실패: {e}")
            return []
    
    async def execute_update(self, query: str, params: tuple = ()) -> int:
        """업데이트 쿼리 실행"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.rowcount
    
    def execute_update_sync(self, query: str, params: tuple = ()) -> int:
        """업데이트 쿼리 실행 (동기 버전)"""
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.execute(query, params)
                db.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"❌ 동기 업데이트 실행 실패: {e}")
            return 0
    
    async def execute_insert(self, query: str, params: tuple = ()) -> int:
        """삽입 쿼리 실행 및 ID 반환"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.lastrowid
    
    async def backup_database(self, backup_path: str) -> bool:
        """데이터베이스 백업"""
        try:
            # 백업 디렉토리 생성
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            async with aiosqlite.connect(self.db_path) as source:
                async with aiosqlite.connect(backup_path) as backup:
                    await source.backup(backup)
            
            self.logger.info(f"✅ 데이터베이스 백업 완료: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 백업 실패: {e}")
            return False
    
    async def get_database_stats(self) -> Dict[str, int]:
        """데이터베이스 통계 정보 (대시보드 형식)"""
        # 기본 테이블 카운트
        tables = [
            "ga4_accounts",
            "ga4_properties", 
            "user_registrations",
            "notification_logs",
            "audit_logs"
        ]
        
        table_stats = {}
        for table in tables:
            result = await self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            table_stats[table] = result[0]['count'] if result else 0
        
        # 활성 사용자 수 (status = 'active' AND ga4_registered = 1)
        active_users_result = await self.execute_query(
            "SELECT COUNT(*) as count FROM user_registrations WHERE status = 'active' AND ga4_registered = 1"
        )
        active_users = active_users_result[0]['count'] if active_users_result else 0
        
        # 만료 예정 사용자 수 (30일 이내, GA4에 실제 등록된 사용자만)
        expiring_soon_result = await self.execute_query(
            """SELECT COUNT(*) as count FROM user_registrations 
               WHERE status = 'active' 
               AND ga4_registered = 1
               AND 종료일 <= datetime('now', '+30 days')"""
        )
        expiring_soon = expiring_soon_result[0]['count'] if expiring_soon_result else 0
        
        # 대시보드에 필요한 형식으로 반환
        return {
            'total_accounts': table_stats.get('ga4_accounts', 0),
            'total_properties': table_stats.get('ga4_properties', 0),
            'active_users': active_users,
            'expiring_soon': expiring_soon,
            'total_notifications': table_stats.get('notification_logs', 0),
            'total_audit_logs': table_stats.get('audit_logs', 0),
            'total_registrations': table_stats.get('user_registrations', 0)
        }

    async def _insert_default_admin_settings(self):
        """기본 관리자 설정 데이터 삽입"""
        try:
            # 기본 유효기간 설정
            default_periods = [
                ('analyst', 30, 'Analyst 권한 기본 유효기간'),
                ('editor', 7, 'Editor 권한 기본 유효기간'),
                ('viewer', 180, 'Viewer 권한 기본 유효기간')
            ]
            
            for role, days, desc in default_periods:
                existing = await self.execute_query(
                    "SELECT id FROM validity_periods WHERE role = ?", (role,)
                )
                if not existing:
                    await self.execute_insert(
                        """INSERT INTO validity_periods (role, period_days, description)
                           VALUES (?, ?, ?)""",
                        (role, days, desc)
                    )
            
            # 기본 알림 설정
            default_notifications = [
                ('immediate_approval', 1, '30,7,1', 'GA4 권한 신청 알림', '새로운 권한 신청이 있습니다.'),
                ('daily_summary', 1, '1', 'GA4 권한 신청 일일 요약', '오늘의 권한 신청 요약입니다.'),
                ('expiry_warning', 1, '30,7,1', 'GA4 권한 만료 경고', '권한이 곧 만료됩니다.'),
                ('expiry_notice', 1, '0', 'GA4 권한 만료 안내', '권한이 만료되었습니다.')
            ]
            
            for noti_type, enabled, trigger_days, subject, body in default_notifications:
                existing = await self.execute_query(
                    "SELECT id FROM notification_settings WHERE notification_type = ?", (noti_type,)
                )
                if not existing:
                    await self.execute_insert(
                        """INSERT INTO notification_settings (notification_type, enabled, trigger_days, template_subject, template_body)
                           VALUES (?, ?, ?, ?, ?)""",
                        (noti_type, enabled, trigger_days, subject, body)
                    )
            
            # 기본 시스템 설정
            default_settings = [
                ('auto_approval_analyst', 'true', 'Analyst 권한 자동 승인 여부'),
                ('auto_approval_viewer', 'true', 'Viewer 권한 자동 승인 여부'),
                ('auto_approval_editor', 'false', 'Editor 권한 자동 승인 여부'),
                ('notification_batch_size', '50', '알림 일괄 처리 크기'),
                ('max_extension_count', '3', '최대 연장 횟수'),
                ('system_email', 'ga4-admin@company.com', '시스템 발송 이메일')
            ]
            
            for key, value, desc in default_settings:
                existing = await self.execute_query(
                    "SELECT id FROM admin_settings WHERE setting_key = ?", (key,)
                )
                if not existing:
                    await self.execute_insert(
                        """INSERT INTO admin_settings (setting_key, setting_value, description)
                           VALUES (?, ?, ?)""",
                        (key, value, desc)
                    )
            
            self.logger.info("✅ 기본 관리자 설정 데이터 삽입 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 기본 설정 삽입 실패: {e}")

    async def get_admin_setting(self, setting_key: str) -> str:
        """관리자 설정 값 조회"""
        try:
            result = await self.execute_query(
                "SELECT setting_value FROM admin_settings WHERE setting_key = ?",
                (setting_key,)
            )
            return result[0]['setting_value'] if result else None
        except Exception as e:
            self.logger.error(f"❌ 설정 조회 실패: {e}")
            return None

    async def update_admin_setting(self, setting_key: str, setting_value: str) -> bool:
        """관리자 설정 값 업데이트"""
        try:
            await self.execute_update(
                """UPDATE admin_settings 
                   SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE setting_key = ?""",
                (setting_value, setting_key)
            )
            return True
        except Exception as e:
            self.logger.error(f"❌ 설정 업데이트 실패: {e}")
            return False

    async def get_validity_period(self, role: str) -> int:
        """역할별 유효기간 조회"""
        try:
            result = await self.execute_query(
                "SELECT period_days FROM validity_periods WHERE role = ? AND is_active = 1",
                (role,)
            )
            return result[0]['period_days'] if result else 30  # 기본값 30일
        except Exception as e:
            self.logger.error(f"❌ 유효기간 조회 실패: {e}")
            return 30

    async def get_responsible_persons(self, property_id: str = None, account_id: str = None) -> List[Dict]:
        """담당자 목록 조회"""
        try:
            if property_id:
                query = """SELECT * FROM responsible_persons 
                          WHERE (property_id = ? OR property_id IS NULL) 
                          AND is_active = 1 AND notification_enabled = 1"""
                params = (property_id,)
            elif account_id:
                query = """SELECT * FROM responsible_persons 
                          WHERE (account_id = ? OR account_id IS NULL) 
                          AND is_active = 1 AND notification_enabled = 1"""
                params = (account_id,)
            else:
                query = "SELECT * FROM responsible_persons WHERE is_active = 1"
                params = ()
            
            result = await self.execute_query(query, params)
            return result or []
        except Exception as e:
            self.logger.error(f"❌ 담당자 조회 실패: {e}")
            return []

    async def update_notification_types_constraint(self):
        """notification_logs 테이블의 CHECK 제약조건 업데이트"""
        try:
            # 새로운 notification_type들을 포함한 완전한 목록
            new_notification_types = [
                '30_days', '7_days', '1_day', 'today', 'expired', 
                'extension_approved', 'welcome', 'test', 'editor_auto_downgrade',
                'admin_notification', 'expiry_warning_30', 'expiry_warning_7', 
                'expiry_warning_1', 'expiry_warning_today', 'deletion_notice',
                'admin_approved', 'editor_approved', 'admin_downgrade', 
                'immediate_approval', 'daily_summary', 'pending_approval',
                'editor_downgrade', 'user_pending_approval'
            ]
            
            # 기존 테이블 백업
            await self.execute_update("""
                CREATE TABLE notification_logs_backup AS 
                SELECT * FROM notification_logs
            """)
            
            # 기존 테이블 삭제
            await self.execute_update("DROP TABLE notification_logs")
            
            # 새로운 제약조건으로 테이블 재생성 (현재 스키마 12개 컬럼에 맞춤)
            constraint_values = "', '".join(new_notification_types)
            await self.execute_update(f"""
                CREATE TABLE notification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_registration_id INTEGER,
                    user_email TEXT NOT NULL,
                    notification_type TEXT NOT NULL CHECK (notification_type IN ('{constraint_values}')),
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
            
            # 백업 데이터 복원 (현재 스키마 12개 컬럼에 맞춰서)
            await self.execute_update("""
                INSERT INTO notification_logs (id, user_registration_id, user_email, notification_type, 
                                             property_id, sent_to, sent_at, message_subject, message_body, 
                                             status, response_received, response_content)
                SELECT id, user_registration_id, user_email, notification_type, 
                       property_id, sent_to, sent_at, message_subject, message_body, 
                       status, response_received, response_content
                FROM notification_logs_backup
            """)
            
            # 백업 테이블 삭제
            await self.execute_update("DROP TABLE notification_logs_backup")
            
            # 인덱스 재생성
            await self.execute_update("CREATE INDEX IF NOT EXISTS idx_notification_logs_type ON notification_logs(notification_type)")
            await self.execute_update("CREATE INDEX IF NOT EXISTS idx_notification_logs_recipient ON notification_logs(user_email)")
            await self.execute_update("CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status)")
            await self.execute_update("CREATE INDEX IF NOT EXISTS idx_notification_logs_sent_at ON notification_logs(sent_at)")
            
            self.logger.info("✅ notification_logs 테이블 제약조건 업데이트 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ notification_logs 테이블 제약조건 업데이트 실패: {e}")
            # 실패 시 백업에서 복원 시도
            try:
                await self.execute_update("DROP TABLE notification_logs")
                await self.execute_update("ALTER TABLE notification_logs_backup RENAME TO notification_logs")
            except:
                pass
            return False


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager() 