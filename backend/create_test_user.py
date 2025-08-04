#!/usr/bin/env python3
"""
Create test users for GA4 Admin System
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add src to path
sys.path.append('/Users/seong-won-yeong/Dev/ga4AdminAutomation/backend')

from src.core.database import AsyncSessionLocal, engine, Base
from src.models.db_models import User, UserRole, UserStatus, Client, ServiceAccount
from src.services.auth_service import AuthService


async def create_test_data():
    """Create test users and data"""
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Check if admin user already exists
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("✅ Admin user already exists!")
        else:
            # Create admin user
            admin_user = User(
                email="admin@example.com",
                name="System Admin",
                company="GA4 Admin Company",
                password_hash=AuthService.hash_password("admin123"),
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                is_representative=True
            )
            session.add(admin_user)
            print("✅ Created admin user: admin@example.com / admin123")
        
        # Check if requester user already exists
        result = await session.execute(select(User).where(User.email == "user@example.com"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("✅ Test user already exists!")
        else:
            # Create test requester user
            test_user = User(
                email="user@example.com",
                name="Test User",
                company="Test Company",
                password_hash=AuthService.hash_password("user123"),
                role=UserRole.REQUESTER,
                status=UserStatus.ACTIVE
            )
            session.add(test_user)
            print("✅ Created test user: user@example.com / user123")
        
        # Check if client already exists
        result = await session.execute(select(Client).where(Client.name == "Test Client"))
        existing_client = result.scalar_one_or_none()
        
        if existing_client:
            print("✅ Test client already exists!")
        else:
            # Create test client
            test_client = Client(
                name="Test Client",
                description="Test client for GA4 integration",
                contact_email="client@example.com"
            )
            session.add(test_client)
            await session.flush()  # Get the ID
            
            # Create test service account
            test_service_account = ServiceAccount(
                client_id=test_client.id,
                email="test-service@ga4-project.iam.gserviceaccount.com",
                secret_name="ga4-test-service-account",
                display_name="Test Service Account"
            )
            session.add(test_service_account)
            print("✅ Created test client and service account")
        
        await session.commit()
        print("\n🎉 Test data created successfully!")
        
        print("\n📋 테스트 계정 정보:")
        print("=" * 50)
        print("🔑 관리자 계정:")
        print("   이메일: admin@example.com")
        print("   비밀번호: admin123")
        print("   역할: Super Admin")
        print()
        print("👤 일반 사용자 계정:")
        print("   이메일: user@example.com")
        print("   비밀번호: user123")
        print("   역할: Requester")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(create_test_data())