#!/usr/bin/env python3
"""
Recreate test users with fresh password hashes
"""

import sqlite3
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def recreate_test_users():
    """Recreate test users with fresh hashes"""
    
    print("=== Recreating Test Users ===\n")
    
    # Test users to create
    test_users = [
        {
            'email': 'admin@test.com',
            'password': 'admin123',
            'name': 'Test Admin',
            'role': 'Super Admin',
            'status': 'active',
            'registration_status': 'approved',
            'company': 'Test Company'
        },
        {
            'email': 'manager@test.com',
            'password': 'manager123',
            'name': 'Test Manager',
            'role': 'Admin',
            'status': 'active',
            'registration_status': 'approved',
            'company': 'Test Company'
        },
        {
            'email': 'user@test.com',
            'password': 'user123',
            'name': 'Test User',
            'role': 'Requester',
            'status': 'active',
            'registration_status': 'approved',
            'company': 'Test Company'
        }
    ]
    
    conn = sqlite3.connect('ga4_admin.db')
    cursor = conn.cursor()
    
    # Delete existing test users
    print("Deleting existing test users...")
    cursor.execute("DELETE FROM users WHERE email IN ('admin@test.com', 'manager@test.com', 'user@test.com')")
    
    # Create fresh users
    print("Creating fresh test users...")
    for user in test_users:
        password_hash = pwd_context.hash(user['password'])
        
        cursor.execute("""
            INSERT INTO users (
                email, name, company, password_hash, role, status, 
                is_representative, registration_status, 
                password_reset_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user['email'],
            user['name'],
            user['company'],
            password_hash,
            user['role'],
            user['status'],
            True,  # is_representative
            user['registration_status'],
            0,  # password_reset_count
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        print(f"Created user: {user['email']} with hash: {password_hash[:30]}...")
        
        # Verify the hash immediately
        verify_result = pwd_context.verify(user['password'], password_hash)
        print(f"Verification test: {verify_result}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ All test users recreated successfully!")
    
    # Verify in database
    print("\nVerifying users in database:")
    conn = sqlite3.connect('ga4_admin.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, role, status, registration_status FROM users WHERE email IN ('admin@test.com', 'manager@test.com', 'user@test.com') ORDER BY id")
    users = cursor.fetchall()
    
    for user in users:
        print(f"ID: {user[0]}, Email: {user[1]}, Role: {user[2]}, Status: {user[3]}, Registration: {user[4]}")
    
    conn.close()

if __name__ == "__main__":
    recreate_test_users()