#!/usr/bin/env python3
"""
Simple authentication debug without async
"""

import sqlite3
from passlib.context import CryptContext
import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_auth_issue():
    """Test authentication step by step"""
    
    print("=== Simple Authentication Debug ===\n")
    
    # Get users from database
    conn = sqlite3.connect('ga4_admin.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, password_hash, role, status, registration_status 
        FROM users 
        WHERE email IN ('admin@test.com', 'manager@test.com', 'user@test.com') 
        ORDER BY id
    """)
    users = cursor.fetchall()
    
    test_credentials = {
        'admin@test.com': 'admin123',
        'manager@test.com': 'manager123', 
        'user@test.com': 'user123'
    }
    
    print("Database Status Check:")
    for user_id, email, password_hash, role, status, reg_status in users:
        print(f"\nUser ID: {user_id}")
        print(f"Email: {email}")
        print(f"Role: {role}")
        print(f"Status: {status}")
        print(f"Registration Status: {reg_status}")
        print(f"Hash Preview: {password_hash[:50]}...")
        
        if email in test_credentials:
            test_password = test_credentials[email]
            
            # Test with passlib (same as AuthService)
            passlib_result = pwd_context.verify(test_password, password_hash)
            print(f"Passlib verify (AuthService method): {passlib_result}")
            
            # Test with bcrypt directly
            try:
                bcrypt_result = bcrypt.checkpw(test_password.encode('utf-8'), password_hash.encode('utf-8'))
                print(f"Bcrypt verify (direct): {bcrypt_result}")
            except Exception as e:
                print(f"Bcrypt error: {e}")
            
            # Check if status would pass AuthService checks
            is_status_active = (status == 'ACTIVE')
            print(f"Status check (status == 'ACTIVE'): {is_status_active}")
            
            # Overall authentication prediction
            auth_should_succeed = passlib_result and is_status_active
            print(f"Authentication should succeed: {auth_should_succeed}")
            
            if not auth_should_succeed:
                if not passlib_result:
                    print("❌ ISSUE: Password verification fails")
                if not is_status_active:
                    print("❌ ISSUE: User status is not ACTIVE")
        
        print("-" * 60)
    
    conn.close()

if __name__ == "__main__":
    test_auth_issue()