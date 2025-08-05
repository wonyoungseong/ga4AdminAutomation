#!/usr/bin/env python3
"""
Create users using SQLAlchemy directly
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.db_models import User, UserRole, UserStatus, RegistrationStatus
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_users_with_sqlalchemy():
    """Create users using SQLAlchemy async session"""
    
    print("=== Creating Users with SQLAlchemy ===\n")
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Test users to create
    test_users_data = [
        {
            'email': 'admin@test.com',
            'password': 'admin123',
            'name': 'Test Admin',
            'role': UserRole.SUPER_ADMIN,
        },
        {
            'email': 'manager@test.com',
            'password': 'manager123',
            'name': 'Test Manager',
            'role': UserRole.ADMIN,
        },
        {
            'email': 'user@test.com',
            'password': 'user123',
            'name': 'Test User',
            'role': UserRole.REQUESTER,
        }
    ]
    
    async with async_session() as session:
        try:
            # Delete existing test users first
            print("Deleting existing test users...")
            from sqlalchemy import delete
            for user_data in test_users_data:
                await session.execute(delete(User).where(User.email == user_data['email']))
            
            await session.commit()
            print("Existing users deleted")
            
            # Create new users
            print("\nCreating new users...")
            for user_data in test_users_data:
                password_hash = pwd_context.hash(user_data['password'])
                
                user = User(
                    email=user_data['email'],
                    name=user_data['name'],
                    company='Test Company',
                    password_hash=password_hash,
                    role=user_data['role'],
                    status=UserStatus.ACTIVE,
                    is_representative=True,
                    registration_status=RegistrationStatus.APPROVED,
                    password_reset_count=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(user)
                print(f"Added user: {user_data['email']}")
            
            await session.commit()
            print("\n✅ All users created successfully with SQLAlchemy!")
            
            # Verify users
            print("\nVerifying users:")
            from sqlalchemy import select
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            for user in users:
                print(f"ID: {user.id}, Email: {user.email}, Role: {user.role}, Status: {user.status}")
                
                # Test password verification
                for user_data in test_users_data:
                    if user.email == user_data['email']:
                        is_valid = pwd_context.verify(user_data['password'], user.password_hash)
                        print(f"  Password verification: {is_valid}")
                        break
            
        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await session.close()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_users_with_sqlalchemy())