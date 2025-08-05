#!/usr/bin/env python3
"""
Debug authentication issue step by step
"""

import asyncio
import sqlite3
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.db_models import User, UserStatus, UserRole
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def debug_authentication():
    """Debug authentication step by step"""
    
    print("=== Authentication Debug Analysis ===\n")
    
    # Test password verification first
    print("1. Testing password hashes directly from database...")
    conn = sqlite3.connect('ga4_admin.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email, password_hash FROM users WHERE email IN ('admin@test.com', 'manager@test.com', 'user@test.com') ORDER BY id")
    users = cursor.fetchall()
    
    test_passwords = {
        'admin@test.com': 'admin123',
        'manager@test.com': 'manager123', 
        'user@test.com': 'user123'
    }
    
    for user_id, email, password_hash in users:
        if email in test_passwords:
            test_password = test_passwords[email]
            is_valid = pwd_context.verify(test_password, password_hash)
            print(f"   {email}: {test_password} -> {is_valid}")
    
    conn.close()
    
    print("\n2. Testing database connection and user retrieval...")
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        from sqlalchemy.orm import sessionmaker
        async_session = sessionmaker(
            conn, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            for email in ['admin@test.com', 'manager@test.com', 'user@test.com']:
                print(f"\n   Testing user: {email}")
                
                # Get user from database
                result = await session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                
                if user:
                    print(f"   ✓ User found: {user.id}")
                    print(f"   ✓ Email: {user.email}")
                    print(f"   ✓ Role: {user.role}")
                    print(f"   ✓ Status: {user.status}")
                    print(f"   ✓ Registration Status: {user.registration_status}")
                    print(f"   ✓ Password hash: {user.password_hash[:20]}...")
                    
                    # Test password verification
                    test_password = test_passwords.get(email)
                    if test_password:
                        is_valid = pwd_context.verify(test_password, user.password_hash)
                        print(f"   ✓ Password verification: {is_valid}")
                        
                        # Check if user is active
                        is_active = user.status == UserStatus.ACTIVE
                        print(f"   ✓ Is Active: {is_active}")
                        
                        if not is_valid:
                            print(f"   ❌ PASSWORD VERIFICATION FAILED!")
                        elif not is_active:
                            print(f"   ❌ USER NOT ACTIVE!")
                        else:
                            print(f"   ✅ Authentication should succeed")
                    
                else:
                    print(f"   ❌ User not found!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_authentication())