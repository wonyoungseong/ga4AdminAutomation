#!/usr/bin/env python3
"""
Start the GA4 Admin Backend Server
"""

import sys
import os
import asyncio
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import engine, Base, AsyncSessionLocal
from src.models.db_models import User, UserRole, UserStatus
from src.services.auth_service import AuthService


async def init_database():
    """Initialize database and create test users"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Check if admin exists
        result = await session.execute(text("SELECT COUNT(*) FROM users WHERE email = 'admin@example.com'"))
        count = result.scalar()
        
        if count == 0:
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
            
            # Create test user
            test_user = User(
                email="user@example.com",
                name="Test User",
                company="Test Company",
                password_hash=AuthService.hash_password("user123"),
                role=UserRole.REQUESTER,
                status=UserStatus.ACTIVE
            )
            session.add(test_user)
            
            await session.commit()
            print("✅ Test users created successfully!")


async def main():
    """Main function to start the server"""
    print("🚀 Initializing database...")
    await init_database()
    
    print("🚀 Starting GA4 Admin Backend Server...")
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
    print("\n🌐 Backend URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🎨 Frontend URL: http://localhost:3000")
    print()
    
    # Start the server
    import uvicorn
    from main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    asyncio.run(main())