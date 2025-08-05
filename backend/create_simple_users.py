#!/usr/bin/env python3
"""
Create test users using direct SQL
"""

import sqlite3
import bcrypt
from datetime import datetime

def create_test_users():
    """Create test users directly in SQLite"""
    
    # Connect to database
    conn = sqlite3.connect('data/ga4_admin.db')
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            company VARCHAR(100),
            role VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
            is_representative BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP
        )
    """)
    
    test_users = [
        ("admin@example.com", "admin123", "Admin User", "Test Company", "SUPER_ADMIN", True),
        ("manager@example.com", "manager123", "Manager User", "Test Company", "ADMIN", True),
        ("user@example.com", "user123", "Regular User", "Test Company", "REQUESTER", False)
    ]
    
    for email, password, name, company, role, is_rep in test_users:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print(f"User already exists: {email}")
            continue
            
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, company, role, status, is_representative)
            VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
        """, (email, hashed_password, name, company, role, is_rep))
        
        print(f"Created user: {email} with role {role}")
    
    conn.commit()
    
    # Display all users
    cursor.execute("SELECT email, name, role, status FROM users")
    users = cursor.fetchall()
    print("\nAll users in database:")
    for user in users:
        print(f"  - {user[0]} ({user[1]}) - Role: {user[2]}, Status: {user[3]}")
    
    conn.close()
    print("\nTest users created successfully!")

if __name__ == "__main__":
    create_test_users()