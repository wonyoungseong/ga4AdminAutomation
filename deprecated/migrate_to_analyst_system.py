#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 마이그레이션
==============================

viewer/editor 시스템에서 analyst/editor 시스템으로 마이그레이션
"""

import asyncio
import sys
import os
from datetime import datetime
import sqlite3

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from src.core.logger import get_ga4_logger
from src.infrastructure.database import db_manager

# 로거 초기화
logger = get_ga4_logger()


class SystemMigration:
    """시스템 마이그레이션 클래스"""
    
    def __init__(self):
        """초기화"""
        self.backup_file = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        self.migration_log = []
    
    async def run_migration(self):
        """전체 마이그레이션 실행"""
        logger.info("🚀 GA4 권한 관리 시스템 마이그레이션 시작")
        logger.info("📋 마이그레이션 내용:")
        logger.info("  - viewer → analyst 권한 변경")
        logger.info("  - 데이터베이스 스키마 업데이트")
        logger.info("  - 기존 데이터 보존")
        
        try:
            # 1. 데이터베이스 백업
            await self.backup_database()
            
            # 2. 스키마 검증
            await self.verify_current_schema()
            
            # 3. 권한 데이터 마이그레이션
            await self.migrate_permission_data()
            
            # 4. 스키마 업데이트
            await self.update_schema_constraints()
            
            # 5. 데이터 무결성 검증
            await self.verify_migration_integrity()
            
            # 6. 마이그레이션 로그 저장
            await self.save_migration_log()
            
            logger.info("✅ 마이그레이션 완료!")
            return True
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 실패: {str(e)}")
            await self.rollback_migration()
            return False
    
    async def backup_database(self):
        """데이터베이스 백업"""
        logger.info("💾 데이터베이스 백업 중...")
        
        try:
            # SQLite 데이터베이스 파일 복사
            import shutil
            db_path = "data/ga4_automation.db"
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, self.backup_file)
                logger.info(f"✅ 백업 완료: {self.backup_file}")
                self.migration_log.append(f"백업 생성: {self.backup_file}")
            else:
                logger.warning("⚠️ 기존 데이터베이스 파일이 없습니다. 새로 생성됩니다.")
                self.migration_log.append("새 데이터베이스 생성")
                
        except Exception as e:
            raise Exception(f"데이터베이스 백업 실패: {str(e)}")
    
    async def verify_current_schema(self):
        """현재 스키마 검증"""
        logger.info("🔍 현재 스키마 검증 중...")
        
        try:
            # 테이블 존재 확인
            tables = await db_manager.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            
            table_names = [table['name'] for table in tables]
            required_tables = ['user_registrations', 'ga4_accounts', 'ga4_properties', 
                             'notification_logs', 'audit_logs']
            
            for table in required_tables:
                if table not in table_names:
                    logger.warning(f"⚠️ 테이블 {table}이 존재하지 않습니다.")
            
            # user_registrations 테이블 구조 확인
            columns = await db_manager.execute_query(
                "PRAGMA table_info(user_registrations)"
            )
            
            column_names = [col['name'] for col in columns]
            logger.info(f"📋 현재 user_registrations 컬럼: {column_names}")
            
            self.migration_log.append(f"기존 테이블: {len(table_names)}개")
            self.migration_log.append(f"user_registrations 컬럼: {len(column_names)}개")
            
        except Exception as e:
            raise Exception(f"스키마 검증 실패: {str(e)}")
    
    async def migrate_permission_data(self):
        """권한 데이터 마이그레이션"""
        logger.info("🔄 권한 데이터 마이그레이션 중...")
        
        try:
            # 기존 viewer 권한을 analyst로 변경
            result = await db_manager.execute_update(
                "UPDATE user_registrations SET 권한 = 'analyst' WHERE 권한 = 'viewer'"
            )
            
            if result > 0:
                logger.info(f"✅ {result}개의 viewer 권한을 analyst로 변경")
                self.migration_log.append(f"권한 변경: viewer → analyst ({result}개)")
            else:
                logger.info("ℹ️ 변경할 viewer 권한이 없습니다.")
                self.migration_log.append("권한 변경: 변경할 데이터 없음")
            
            # 현재 권한 분포 확인
            permissions = await db_manager.execute_query(
                """SELECT 권한, COUNT(*) as count 
                   FROM user_registrations 
                   GROUP BY 권한"""
            )
            
            for perm in permissions:
                logger.info(f"📊 {perm['권한']}: {perm['count']}개")
                self.migration_log.append(f"현재 권한 분포 - {perm['권한']}: {perm['count']}개")
            
        except Exception as e:
            raise Exception(f"권한 데이터 마이그레이션 실패: {str(e)}")
    
    async def update_schema_constraints(self):
        """스키마 제약 조건 업데이트"""
        logger.info("🔧 스키마 제약 조건 업데이트 중...")
        
        try:
            # SQLite에서는 CHECK 제약 조건을 직접 수정할 수 없으므로
            # 테이블을 재생성해야 합니다.
            
            # 1. 임시 테이블 생성
            await db_manager.execute_update("""
                CREATE TABLE user_registrations_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    신청자 TEXT NOT NULL,
                    등록_계정 TEXT NOT NULL,
                    property_id TEXT NOT NULL,
                    property_name TEXT,
                    권한 TEXT NOT NULL DEFAULT 'analyst' CHECK (권한 IN ('analyst', 'editor')),
                    신청일 DATETIME DEFAULT CURRENT_TIMESTAMP,
                    종료일 DATETIME NOT NULL,
                    status TEXT DEFAULT 'active' CHECK (status IN ('pending_approval', 'active', 'expired', 'rejected', 'deleted')),
                    approval_required BOOLEAN DEFAULT 0,
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
            """)
            
            # 2. 기존 데이터 복사
            await db_manager.execute_update("""
                INSERT INTO user_registrations_new 
                SELECT * FROM user_registrations
            """)
            
            # 3. 기존 테이블 삭제 및 새 테이블 이름 변경
            await db_manager.execute_update("DROP TABLE user_registrations")
            await db_manager.execute_update("ALTER TABLE user_registrations_new RENAME TO user_registrations")
            
            logger.info("✅ 스키마 제약 조건 업데이트 완료")
            self.migration_log.append("스키마 업데이트: CHECK 제약 조건 변경 완료")
            
        except Exception as e:
            raise Exception(f"스키마 업데이트 실패: {str(e)}")
    
    async def verify_migration_integrity(self):
        """마이그레이션 무결성 검증"""
        logger.info("🔍 마이그레이션 무결성 검증 중...")
        
        try:
            # 1. 데이터 개수 확인
            total_registrations = await db_manager.execute_query(
                "SELECT COUNT(*) as count FROM user_registrations"
            )
            total_count = total_registrations[0]['count']
            
            # 2. 권한 분포 확인
            permissions = await db_manager.execute_query(
                """SELECT 권한, COUNT(*) as count 
                   FROM user_registrations 
                   GROUP BY 권한"""
            )
            
            # 3. viewer 권한이 남아있는지 확인
            viewer_count = await db_manager.execute_query(
                "SELECT COUNT(*) as count FROM user_registrations WHERE 권한 = 'viewer'"
            )
            
            if viewer_count[0]['count'] > 0:
                raise Exception(f"마이그레이션 후에도 viewer 권한이 {viewer_count[0]['count']}개 남아있습니다.")
            
            # 4. 잘못된 권한 확인
            invalid_permissions = await db_manager.execute_query(
                "SELECT COUNT(*) as count FROM user_registrations WHERE 권한 NOT IN ('analyst', 'editor')"
            )
            
            if invalid_permissions[0]['count'] > 0:
                raise Exception(f"잘못된 권한이 {invalid_permissions[0]['count']}개 발견되었습니다.")
            
            logger.info(f"✅ 무결성 검증 완료: 총 {total_count}개 등록")
            for perm in permissions:
                logger.info(f"   - {perm['권한']}: {perm['count']}개")
            
            self.migration_log.append(f"무결성 검증: 총 {total_count}개 등록 확인")
            
        except Exception as e:
            raise Exception(f"무결성 검증 실패: {str(e)}")
    
    async def save_migration_log(self):
        """마이그레이션 로그 저장"""
        log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("GA4 권한 관리 시스템 마이그레이션 로그\n")
                f.write("=" * 50 + "\n")
                f.write(f"마이그레이션 시간: {datetime.now().isoformat()}\n")
                f.write(f"백업 파일: {self.backup_file}\n")
                f.write("\n마이그레이션 상세 내역:\n")
                
                for i, log_entry in enumerate(self.migration_log, 1):
                    f.write(f"{i}. {log_entry}\n")
                
                f.write("\n마이그레이션 완료\n")
            
            logger.info(f"📄 마이그레이션 로그 저장: {log_file}")
            
        except Exception as e:
            logger.warning(f"⚠️ 로그 저장 실패: {str(e)}")
    
    async def rollback_migration(self):
        """마이그레이션 롤백"""
        logger.info("🔄 마이그레이션 롤백 중...")
        
        try:
            if os.path.exists(self.backup_file):
                # 백업 파일로 복원
                import shutil
                shutil.copy2(self.backup_file, "data/ga4_automation.db")
                logger.info("✅ 데이터베이스 롤백 완료")
            else:
                logger.warning("⚠️ 백업 파일이 없어 롤백할 수 없습니다.")
                
        except Exception as e:
            logger.error(f"❌ 롤백 실패: {str(e)}")


async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🎯 GA4 권한 관리 시스템 마이그레이션")
    print("=" * 60)
    print("📋 마이그레이션 내용:")
    print("  - viewer 권한 → analyst 권한 변경")
    print("  - 데이터베이스 스키마 업데이트")
    print("  - 기존 데이터 보존 및 백업")
    print("=" * 60)
    
    # 사용자 확인
    response = input("\n마이그레이션을 진행하시겠습니까? (y/N): ").strip().lower()
    
    if response != 'y':
        print("마이그레이션이 취소되었습니다.")
        return
    
    try:
        migration = SystemMigration()
        success = await migration.run_migration()
        
        if success:
            print("\n🎉 마이그레이션이 성공적으로 완료되었습니다!")
            print(f"📄 백업 파일: {migration.backup_file}")
            print("📄 마이그레이션 로그 파일이 생성되었습니다.")
            sys.exit(0)
        else:
            print("\n❌ 마이그레이션이 실패했습니다.")
            print("백업 파일을 확인하고 필요시 복원하세요.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 마이그레이션이 중단되었습니다.")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 마이그레이션 중 치명적 오류: {str(e)}")
        sys.exit(2)


if __name__ == "__main__":
    # 이벤트 루프 정책 설정 (Windows 호환성)
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main()) 