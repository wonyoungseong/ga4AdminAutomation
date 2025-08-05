#!/usr/bin/env python3
"""
Create test user for main.py backend
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import AsyncSessionLocal
from src.models.db_models import User, UserRole, UserStatus, RegistrationStatus
from src.core.config import settings
import bcrypt
from datetime import datetime

async def create_test_users():
    """Create test users for development"""
    
    # Get database session
    async with AsyncSessionLocal() as db:
        try:
            # Test users data
            test_users = [
                {
                    'email': 'admin@test.com',
                    'name': 'System Admin',
                    'password': 'admin123',
                    'company': 'Test Company',
                    'role': UserRole.SUPER_ADMIN
                },
                {
                    'email': 'manager@test.com', 
                    'name': 'Manager User',
                    'password': 'manager123',
                    'company': 'Test Company',
                    'role': UserRole.ADMIN
                },
                {
                    'email': 'user@test.com',
                    'name': 'Regular User',
                    'password': 'user123',
                    'company': 'Test Company',
                    'role': UserRole.REQUESTER
                }
            ]
            
            created_users = []
            
            for user_data in test_users:
                # Check if user already exists
                result = await db.execute(select(User).where(User.email == user_data['email']))
                existing_user = result.scalar_one_or_none()
                if existing_user:
                    print(f"User {user_data['email']} already exists")
                    continue
                
                # Hash password
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), salt).decode('utf-8')
                
                # Create user
                user = User(
                    email=user_data['email'],
                    name=user_data['name'],
                    password_hash=password_hash,
                    company=user_data['company'],
                    role=user_data['role'],
                    status=UserStatus.ACTIVE,
                    email_verified_at=datetime.utcnow(),
                    registration_status=RegistrationStatus.APPROVED,
                    approved_at=datetime.utcnow()
                )
                
                db.add(user)
                created_users.append(user_data['email'])
            
            await db.commit()
            print(f"Successfully created {len(created_users)} test users:")
            for email in created_users:
                print(f"  - {email}")
                
        except Exception as e:
            await db.rollback()
            print(f"Error creating test users: {e}")
            raise
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(create_test_users())