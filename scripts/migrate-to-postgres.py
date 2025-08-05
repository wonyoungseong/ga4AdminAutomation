#!/usr/bin/env python3
"""
Database migration script from SQLite to PostgreSQL
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import asyncpg
import aiosqlite

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path: str, postgres_url: str):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.postgres_sync_url = postgres_url.replace('+asyncpg', '')
        
        # Create engines
        self.sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
        self.postgres_sync_engine = create_engine(self.postgres_sync_url)
        self.postgres_async_engine = create_async_engine(postgres_url)
        
        # Create session makers
        self.postgres_async_session = async_sessionmaker(
            self.postgres_async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_sqlite_tables(self) -> List[str]:
        """Get list of tables from SQLite database"""
        async with aiosqlite.connect(self.sqlite_path) as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = await cursor.fetchall()
            return [table[0] for table in tables]
    
    async def get_table_schema(self, table_name: str) -> str:
        """Get table schema from SQLite"""
        async with aiosqlite.connect(self.sqlite_path) as conn:
            cursor = await conn.execute(
                f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            result = await cursor.fetchone()
            return result[0] if result else ""
    
    async def get_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all data from a SQLite table"""
        async with aiosqlite.connect(self.sqlite_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(f"SELECT * FROM {table_name}")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def create_postgres_tables(self):
        """Create tables in PostgreSQL using SQLAlchemy models"""
        logger.info("Creating PostgreSQL tables using SQLAlchemy models...")
        
        try:
            # Import models to register them
            from src.models.db_models import Base
            
            async with self.postgres_async_engine.begin() as conn:
                # Drop all tables (careful in production!)
                await conn.run_sync(Base.metadata.drop_all)
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("PostgreSQL tables created successfully")
        except Exception as e:
            logger.error(f"Error creating PostgreSQL tables: {e}")
            raise
    
    async def migrate_table_data(self, table_name: str, data: List[Dict[str, Any]]):
        """Migrate data from SQLite table to PostgreSQL"""
        if not data:
            logger.info(f"No data to migrate for table {table_name}")
            return
        
        logger.info(f"Migrating {len(data)} records from {table_name}")
        
        try:
            async with self.postgres_async_session() as session:
                # Get column names from first row
                columns = list(data[0].keys())
                
                # Prepare INSERT statement
                columns_sql = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])
                sql = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders})"
                
                # Insert data in batches
                batch_size = 100
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    
                    # Clean data for PostgreSQL compatibility
                    cleaned_batch = []
                    for row in batch:
                        cleaned_row = {}
                        for col, value in row.items():
                            # Handle SQLite-specific data types
                            if value is None:
                                cleaned_row[col] = None
                            elif isinstance(value, str) and value.lower() in ('true', 'false'):
                                # Convert string booleans to actual booleans
                                cleaned_row[col] = value.lower() == 'true'
                            else:
                                cleaned_row[col] = value
                        cleaned_batch.append(cleaned_row)
                    
                    # Execute batch insert
                    for row in cleaned_batch:
                        try:
                            await session.execute(text(sql), row)
                        except Exception as e:
                            logger.warning(f"Error inserting row in {table_name}: {e}")
                            logger.warning(f"Problematic row: {row}")
                            continue
                    
                    await session.commit()
                    logger.info(f"Migrated batch {i//batch_size + 1} for {table_name}")
                
        except Exception as e:
            logger.error(f"Error migrating data for table {table_name}: {e}")
            raise
    
    async def verify_migration(self):
        """Verify that data was migrated correctly"""
        logger.info("Verifying migration...")
        
        try:
            # Get table counts from both databases
            sqlite_counts = {}
            postgres_counts = {}
            
            # SQLite counts
            async with aiosqlite.connect(self.sqlite_path) as conn:
                tables = await self.get_sqlite_tables()
                for table in tables:
                    cursor = await conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = await cursor.fetchone()
                    sqlite_counts[table] = count[0]
            
            # PostgreSQL counts
            async with self.postgres_async_session() as session:
                for table in tables:
                    try:
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        postgres_counts[table] = count
                    except Exception as e:
                        logger.warning(f"Could not count records in {table}: {e}")
                        postgres_counts[table] = -1
            
            # Compare counts
            logger.info("Migration verification results:")
            all_match = True
            for table in tables:
                sqlite_count = sqlite_counts.get(table, 0)
                postgres_count = postgres_counts.get(table, 0)
                match = sqlite_count == postgres_count
                all_match = all_match and match
                
                status = "✓" if match else "✗"
                logger.info(f"{status} {table}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
            
            if all_match:
                logger.info("✓ Migration verification passed!")
            else:
                logger.warning("✗ Migration verification found discrepancies")
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")
    
    async def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting database migration from SQLite to PostgreSQL")
        
        try:
            # 1. Create PostgreSQL tables
            await self.create_postgres_tables()
            
            # 2. Get SQLite tables
            tables = await self.get_sqlite_tables()
            logger.info(f"Found {len(tables)} tables to migrate: {tables}")
            
            # 3. Migrate data for each table
            for table_name in tables:
                logger.info(f"Migrating table: {table_name}")
                data = await self.get_table_data(table_name)
                await self.migrate_table_data(table_name, data)
            
            # 4. Verify migration
            await self.verify_migration()
            
            logger.info("Database migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            await self.postgres_async_engine.dispose()

async def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate SQLite database to PostgreSQL')
    parser.add_argument('--sqlite-path', required=True, help='Path to SQLite database file')
    parser.add_argument('--postgres-url', required=True, help='PostgreSQL connection URL')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually doing it')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.sqlite_path):
        logger.error(f"SQLite database file not found: {args.sqlite_path}")
        return 1
    
    try:
        migrator = DatabaseMigrator(args.sqlite_path, args.postgres_url)
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual migration will be performed")
            tables = await migrator.get_sqlite_tables()
            logger.info(f"Would migrate {len(tables)} tables: {tables}")
            
            for table in tables:
                data = await migrator.get_table_data(table)
                logger.info(f"Table {table}: {len(data)} records")
        else:
            await migrator.run_migration()
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)