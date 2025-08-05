#!/usr/bin/env python3
"""
Simple script to create a test user for login testing
"""

import asyncio
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import AsyncSessionLocal, init_db
from src.models.db_models import User, UserRole, UserStatus, RegistrationStatus


def hash_password(password: str) -> str:
    """Simple SHA-256 hash for testing - in production use bcrypt"""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_test_user():
    """Create a simple test admin user"""
    
    # Initialize database
    await init_db()
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if user already exists
            existing_user = await db.execute(
                select(User).where(User.email == 'admin@test.com')
            )
            if existing_user.scalar_one_or_none():
                print("Test user already exists: admin@test.com")
                return
            
            # Create test admin user
            user = User(
                email='admin@test.com',
                name='Test Admin',
                company='Test Company',
                password_hash=hash_password('admin123'),
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                registration_status=RegistrationStatus.APPROVED,
                is_representative=True,
                email_verified_at=datetime.utcnow(),
                approved_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            db.add(user)
            await db.commit()
            
            print("Test user created successfully:")
            print(f"Email: {user.email}")
            print(f"Password: admin123")
            print(f"Role: {user.role}")
            print(f"Status: {user.status}")
            print(f"Registration Status: {user.registration_status}")
            
        except Exception as e:
            await db.rollback()
            print(f"Error creating test user: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    from sqlalchemy import select
    asyncio.run(create_test_user())