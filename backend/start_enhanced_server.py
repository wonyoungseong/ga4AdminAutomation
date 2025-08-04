#!/usr/bin/env python3
"""
Enhanced GA4 Admin Automation Server Startup Script
Demonstrates the comprehensive client assignment and access control system
"""

import asyncio
import sys
import uvicorn
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.config import settings
from src.core.database import init_db
from src.models.db_models import (
    User, Client, ClientAssignment, UserRole, 
    UserStatus, ClientAssignmentStatus
)


async def create_demo_data():
    """Create demonstration data for the enhanced system"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.core.database import AsyncSessionLocal
    from datetime import datetime, timedelta
    import hashlib
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if demo data already exists
            from sqlalchemy import select
            result = await db.execute(select(User).limit(1))
            if result.scalar_one_or_none():
                print("Demo data already exists, skipping creation...")
                return
            
            print("Creating demo data...")
            
            # Create users
            users_data = [
                {
                    "email": "superadmin@ga4admin.com",
                    "name": "Super Administrator",
                    "company": "GA4 Admin Corp",
                    "role": UserRole.SUPER_ADMIN,
                    "password": "superadmin123"
                },
                {
                    "email": "admin@ga4admin.com", 
                    "name": "System Administrator",
                    "company": "GA4 Admin Corp",
                    "role": UserRole.ADMIN,
                    "password": "admin123"
                },
                {
                    "email": "manager@client1.com",
                    "name": "Client Manager",
                    "company": "Client One Corp",
                    "role": UserRole.REQUESTER,
                    "password": "manager123"
                },
                {
                    "email": "analyst@client1.com",
                    "name": "Data Analyst",
                    "company": "Client One Corp", 
                    "role": UserRole.VIEWER,
                    "password": "analyst123"
                },
                {
                    "email": "user@client2.com",
                    "name": "Marketing User",
                    "company": "Client Two Inc",
                    "role": UserRole.REQUESTER,
                    "password": "user123"
                }
            ]
            
            created_users = {}
            for user_data in users_data:
                password_hash = hashlib.sha256(user_data["password"].encode()).hexdigest()
                user = User(
                    email=user_data["email"],
                    name=user_data["name"],
                    company=user_data["company"],
                    role=user_data["role"],
                    status=UserStatus.ACTIVE,
                    password_hash=password_hash
                )
                db.add(user)
                created_users[user_data["email"]] = user
            
            # Create clients
            clients_data = [
                {
                    "name": "ABC Marketing Solutions",
                    "description": "Digital marketing agency specializing in e-commerce",
                    "contact_email": "contact@abcmarketing.com"
                },
                {
                    "name": "XYZ E-commerce Platform", 
                    "description": "Online retail platform with multiple brands",
                    "contact_email": "admin@xyzplatform.com"
                },
                {
                    "name": "TechStart Analytics",
                    "description": "B2B SaaS analytics startup",
                    "contact_email": "hello@techstart.io"
                }
            ]
            
            created_clients = {}
            for client_data in clients_data:
                client = Client(
                    name=client_data["name"],
                    description=client_data["description"],
                    contact_email=client_data["contact_email"]
                )
                db.add(client)
                created_clients[client_data["name"]] = client
            
            await db.commit()
            
            # Refresh to get IDs
            for user in created_users.values():
                await db.refresh(user)
            for client in created_clients.values():
                await db.refresh(client)
            
            # Create client assignments
            assignments_data = [
                {
                    "user_email": "manager@client1.com",
                    "client_name": "ABC Marketing Solutions",
                    "assigned_by_email": "admin@ga4admin.com",
                    "notes": "Primary client manager"
                },
                {
                    "user_email": "analyst@client1.com",
                    "client_name": "ABC Marketing Solutions", 
                    "assigned_by_email": "admin@ga4admin.com",
                    "notes": "Analytics and reporting"
                },
                {
                    "user_email": "user@client2.com",
                    "client_name": "XYZ E-commerce Platform",
                    "assigned_by_email": "admin@ga4admin.com", 
                    "notes": "Marketing campaign management"
                },
                {
                    "user_email": "manager@client1.com",
                    "client_name": "TechStart Analytics",
                    "assigned_by_email": "admin@ga4admin.com",
                    "notes": "Consulting services"
                }
            ]
            
            for assignment_data in assignments_data:
                user = created_users[assignment_data["user_email"]]
                client = created_clients[assignment_data["client_name"]]
                assigned_by = created_users[assignment_data["assigned_by_email"]]
                
                assignment = ClientAssignment(
                    user_id=user.id,
                    client_id=client.id,
                    assigned_by_id=assigned_by.id,
                    status=ClientAssignmentStatus.ACTIVE,
                    notes=assignment_data["notes"],
                    expires_at=datetime.utcnow() + timedelta(days=365)  # 1 year expiry
                )
                db.add(assignment)
            
            await db.commit()
            
            print("✅ Demo data created successfully!")
            print("\n📋 Demo Accounts:")
            print("=" * 60)
            for user_data in users_data:
                print(f"🔑 {user_data['role'].value}:")
                print(f"   Email: {user_data['email']}")
                print(f"   Password: {user_data['password']}")
                print(f"   Name: {user_data['name']}")
                print()
            
            print("🏢 Demo Clients:")
            print("=" * 60)
            for client_data in clients_data:
                print(f"📊 {client_data['name']}")
                print(f"   Description: {client_data['description']}")
                print(f"   Contact: {client_data['contact_email']}")
                print()
            
            print("🔗 Client Assignments Created:")
            print("=" * 60)
            for assignment_data in assignments_data:
                print(f"👤 {assignment_data['user_email']} → 🏢 {assignment_data['client_name']}")
                print(f"   Notes: {assignment_data['notes']}")
                print()
            
        except Exception as e:
            print(f"❌ Error creating demo data: {e}")
            await db.rollback()
            raise


def print_system_info():
    """Print system information and features"""
    print("🚀 GA4 Admin Automation System - Enhanced Edition")
    print("=" * 60)
    print(f"📱 Version: {settings.APP_VERSION}")
    print(f"🌐 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔍 ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    print()
    
    print("✨ Enhanced Features:")
    print("=" * 60)
    print("🔐 Comprehensive Client Assignment System")
    print("   • Multi-level role-based access control")
    print("   • Client-user assignment management") 
    print("   • Automatic access filtering")
    print()
    print("👥 Enhanced User Management")
    print("   • Role hierarchy: Super Admin > Admin > Requester > Viewer")
    print("   • Client-specific access permissions")
    print("   • Assignment-based data filtering")
    print()
    print("🏢 Advanced Client Management")
    print("   • Client-user relationship tracking")
    print("   • Assignment metadata and expiration")
    print("   • Bulk assignment operations")
    print()
    print("🛡️ Security & Access Control")
    print("   • Client-level permission isolation")
    print("   • Role-based API endpoint protection")
    print("   • Comprehensive audit logging")
    print()
    print("📊 Permission Management")
    print("   • Client-aware permission requests")
    print("   • Assignment-based permission filtering")
    print("   • Enhanced approval workflows")
    print()


async def main():
    """Main startup function"""
    print_system_info()
    
    print("🔧 Initializing system...")
    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized")
        
        # Create demo data
        await create_demo_data()
        
        print("\n🎯 Key API Endpoints:")
        print("=" * 60)
        print("🔗 Client Assignments:")
        print("   GET    /api/client-assignments/")
        print("   POST   /api/client-assignments/")
        print("   POST   /api/client-assignments/bulk")
        print()
        print("🏢 Enhanced Clients:")
        print("   GET    /api/clients/")
        print("   GET    /api/clients/{client_id}")
        print("   GET    /api/clients/my/accessible")
        print()
        print("🔐 Enhanced Permissions:")
        print("   GET    /api/permissions/")
        print("   GET    /api/permissions/my/requests")
        print("   GET    /api/permissions/pending/review")
        print()
        print("🎮 Access Control:")
        print("   GET    /api/client-assignments/my/accessible-clients")
        print("   POST   /api/client-assignments/validate-access/{client_id}")
        print()
        
        print("🚀 Starting server...")
        print("   Press Ctrl+C to stop the server")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run initialization
    asyncio.run(main())
    
    # Start the server
    uvicorn.run(
        "src.main_enhanced:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )