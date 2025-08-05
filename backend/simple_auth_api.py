#!/usr/bin/env python3
"""
Simple authentication API for testing
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
import uvicorn

app = FastAPI(title="Simple Auth API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT settings
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict

def get_password_hash(password: str) -> str:
    """Hash password"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/api/auth/create-test-user")
async def create_test_user():
    """Create test users for development"""
    try:
        conn = sqlite3.connect('data/ga4_admin.db')
        cursor = conn.cursor()
        
        # Create users table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                company TEXT,
                role TEXT DEFAULT 'requester',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Test users data
        test_users = [
            {
                'email': 'admin@test.com',
                'name': 'System Admin',
                'password': 'admin123',
                'company': 'Test Company',
                'role': 'super_admin'
            },
            {
                'email': 'manager@test.com', 
                'name': 'Manager User',
                'password': 'manager123',
                'company': 'Test Company',
                'role': 'manager'
            },
            {
                'email': 'user@test.com',
                'name': 'Regular User', 
                'password': 'user123',
                'company': 'Test Company',
                'role': 'requester'
            }
        ]
        
        created_users = []
        for user in test_users:
            try:
                hashed_password = get_password_hash(user['password'])
                cursor.execute(
                    "INSERT INTO users (email, name, password_hash, company, role, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (user['email'], user['name'], hashed_password, user['company'], user['role'], 'active')
                )
                created_users.append({
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role'],
                    'password': user['password']  # Include for testing only
                })
            except sqlite3.IntegrityError:
                # User already exists, skip
                pass
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Test users created successfully",
            "users": created_users
        }
        
    except Exception as e:
        return {"error": f"Failed to create test users: {str(e)}"}

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Simple login endpoint"""
    try:
        # Connect to database
        conn = sqlite3.connect('data/ga4_admin.db')
        cursor = conn.cursor()
        
        # Get user by email
        cursor.execute(
            "SELECT id, email, password_hash, name, company, role, status FROM users WHERE email = ?",
            (login_data.email,)
        )
        user_row = cursor.fetchone()
        conn.close()
        
        if not user_row:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user_id, email, password_hash, name, company, role, status = user_row
        
        # Verify password
        if not verify_password(login_data.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is active
        if status != 'active':
            raise HTTPException(status_code=401, detail="Account is not active")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email, "user_id": user_id, "role": role},
            expires_delta=access_token_expires
        )
        
        # Create refresh token (longer expiry)
        refresh_token_expires = timedelta(days=7)
        refresh_token = create_access_token(
            data={"sub": email, "user_id": user_id, "role": role, "type": "refresh"},
            expires_delta=refresh_token_expires
        )
        
        # Prepare user info
        user_info = {
            "id": user_id,
            "email": email,
            "name": name,
            "company": company,
            "role": role,
            "status": status
        }
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/auth/me")
async def get_current_user(authorization: str = Header(None)):
    """Get current user info"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not email or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Connect to database and find user
        conn = sqlite3.connect('data/ga4_admin.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, email, name, company, role, status FROM users WHERE email = ? AND id = ?",
            (email, user_id)
        )
        user_row = cursor.fetchone()
        conn.close()
        
        if not user_row:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_id, email, name, company, role, status = user_row
        
        return {
            "id": user_id,
            "email": email,
            "name": name,
            "company": company,
            "role": role,
            "status": status
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Mock data for testing
MOCK_USERS = [
    {"id": 1, "email": "admin@example.com", "name": "Admin User", "company": "Test Company", "role": "SUPER_ADMIN", "status": "ACTIVE"},
    {"id": 2, "email": "manager@example.com", "name": "Manager User", "company": "Test Company", "role": "ADMIN", "status": "ACTIVE"},
    {"id": 3, "email": "user@example.com", "name": "Regular User", "company": "Test Company", "role": "REQUESTER", "status": "ACTIVE"}
]

MOCK_SERVICE_ACCOUNTS = [
    {"id": 1, "name": "GA4 Analytics Service", "email": "ga4-service@test.iam.gserviceaccount.com", "status": "ACTIVE", "created_at": "2024-01-01T00:00:00Z"},
    {"id": 2, "name": "Data Export Service", "email": "data-export@test.iam.gserviceaccount.com", "status": "ACTIVE", "created_at": "2024-01-01T00:00:00Z"}
]

MOCK_CLIENTS = [
    {"id": 1, "name": "Client A", "domain": "client-a.com", "status": "ACTIVE", "created_at": "2024-01-01T00:00:00Z"},
    {"id": 2, "name": "Client B", "domain": "client-b.com", "status": "ACTIVE", "created_at": "2024-01-01T00:00:00Z"}
]

MOCK_PERMISSIONS = [
    {"id": 1, "user_id": 1, "ga4_property_id": "GA4-123456", "level": "ADMIN", "status": "ACTIVE", "expires_at": "2024-12-31T23:59:59Z"},
    {"id": 2, "user_id": 2, "ga4_property_id": "GA4-123456", "level": "EDITOR", "status": "ACTIVE", "expires_at": "2024-12-31T23:59:59Z"}
]

MOCK_GA4_PROPERTIES = [
    {"id": "GA4-123456", "name": "Test Property", "display_name": "Test Website Analytics", "status": "ACTIVE"},
    {"id": "GA4-789012", "name": "Demo Property", "display_name": "Demo Site Analytics", "status": "ACTIVE"}
]

@app.get("/api/users")
async def get_users(page: int = 1, limit: int = 10):
    """Get users with pagination"""
    start = (page - 1) * limit
    end = start + limit
    users = MOCK_USERS[start:end]
    return {
        "users": users,
        "total": len(MOCK_USERS),
        "page": page,
        "limit": limit,
        "total_pages": (len(MOCK_USERS) + limit - 1) // limit
    }

@app.get("/api/service-accounts")
async def get_service_accounts(page: int = 1, limit: int = 10):
    """Get service accounts with pagination"""
    start = (page - 1) * limit
    end = start + limit
    accounts = MOCK_SERVICE_ACCOUNTS[start:end]
    return {
        "service_accounts": accounts,
        "total": len(MOCK_SERVICE_ACCOUNTS),
        "page": page,
        "limit": limit,
        "total_pages": (len(MOCK_SERVICE_ACCOUNTS) + limit - 1) // limit
    }

@app.get("/api/clients")
async def get_clients(page: int = 1, limit: int = 10):
    """Get clients with pagination"""
    start = (page - 1) * limit
    end = start + limit
    clients = MOCK_CLIENTS[start:end]
    return {
        "clients": clients,
        "total": len(MOCK_CLIENTS),
        "page": page,
        "limit": limit,
        "total_pages": (len(MOCK_CLIENTS) + limit - 1) // limit
    }

@app.get("/api/permissions")
async def get_permissions():
    """Get permissions"""
    return {
        "permissions": MOCK_PERMISSIONS,
        "total": len(MOCK_PERMISSIONS)
    }

@app.get("/api/ga4-properties")
async def get_ga4_properties(page: int = 1, limit: int = 100):
    """Get GA4 properties"""
    start = (page - 1) * limit
    end = start + limit
    properties = MOCK_GA4_PROPERTIES[start:end]
    return {
        "properties": properties,
        "total": len(MOCK_GA4_PROPERTIES),
        "page": page,
        "limit": limit,
        "total_pages": (len(MOCK_GA4_PROPERTIES) + limit - 1) // limit
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    return {
        "total_users": len(MOCK_USERS),
        "total_service_accounts": len(MOCK_SERVICE_ACCOUNTS), 
        "total_clients": len(MOCK_CLIENTS),
        "total_properties": len(MOCK_GA4_PROPERTIES),
        "active_permissions": len([p for p in MOCK_PERMISSIONS if p["status"] == "ACTIVE"]),
        "recent_activities": [
            {
                "id": 1,
                "action": "User Login",
                "user": "admin@test.com",
                "timestamp": "2024-01-01T10:00:00Z",
                "details": "Successful login"
            },
            {
                "id": 2, 
                "action": "Permission Grant",
                "user": "manager@test.com",
                "timestamp": "2024-01-01T09:30:00Z",
                "details": "Granted GA4 access to user@test.com"
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Simple Auth API is running"}

if __name__ == "__main__":
    uvicorn.run(
        "simple_auth_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )