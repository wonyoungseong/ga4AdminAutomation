"""
Pytest configuration and fixtures for GA4 Admin Automation System tests
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.database import Base, get_db
from src.core.config import settings
from src.models.db_models import (
    User, Client, ServiceAccount, PermissionGrant, UserRole, UserStatus, 
    PermissionLevel, PermissionStatus, ClientAssignmentStatus, RegistrationStatus
)
from src.services.auth_service import AuthService
from src.main_enhanced import app


# Test database URL - use in-memory SQLite for fast tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as connection:
        session = AsyncSession(bind=connection, expire_on_commit=False)
        
        # Start a nested transaction
        nested = await connection.begin_nested()
        
        yield session
        
        # Rollback the nested transaction
        await nested.rollback()
        await session.close()


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for testing."""
    async def _get_db():
        yield db_session
    return _get_db


@pytest.fixture
def test_client(override_get_db):
    """Create a test client with overridden database dependency."""
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# User fixtures
@pytest.fixture
async def test_user_data() -> Dict[str, Any]:
    """Test user data for creating users."""
    return {
        "email": "testuser@example.com",
        "name": "Test User",
        "company": "Test Company",
        "password": "TestPassword123!",
        "role": UserRole.REQUESTER,
        "status": UserStatus.ACTIVE,
        "registration_status": RegistrationStatus.APPROVED,
    }


@pytest.fixture
async def test_admin_data() -> Dict[str, Any]:
    """Test admin user data."""
    return {
        "email": "admin@example.com",
        "name": "Admin User",
        "company": "Admin Company",
        "password": "AdminPassword123!",
        "role": UserRole.ADMIN,
        "status": UserStatus.ACTIVE,
        "registration_status": RegistrationStatus.APPROVED,
    }


@pytest.fixture
async def test_super_admin_data() -> Dict[str, Any]:
    """Test super admin user data."""
    return {
        "email": "superadmin@example.com",
        "name": "Super Admin User",
        "company": "Super Admin Company",
        "password": "SuperAdminPass123!",
        "role": UserRole.SUPER_ADMIN,
        "status": UserStatus.ACTIVE,
        "registration_status": RegistrationStatus.APPROVED,
    }


@pytest.fixture
async def test_user(db_session: AsyncSession, test_user_data: Dict[str, Any]) -> User:
    """Create a test user in the database."""
    user = User(
        email=test_user_data["email"],
        name=test_user_data["name"],
        company=test_user_data["company"],
        password_hash=AuthService.hash_password(test_user_data["password"]),
        role=test_user_data["role"],
        status=test_user_data["status"],
        registration_status=test_user_data["registration_status"],
        email_verified_at=datetime.utcnow(),
        approved_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession, test_admin_data: Dict[str, Any]) -> User:
    """Create a test admin user in the database."""
    admin = User(
        email=test_admin_data["email"],
        name=test_admin_data["name"],
        company=test_admin_data["company"],
        password_hash=AuthService.hash_password(test_admin_data["password"]),
        role=test_admin_data["role"],
        status=test_admin_data["status"],
        registration_status=test_admin_data["registration_status"],
        email_verified_at=datetime.utcnow(),
        approved_at=datetime.utcnow(),
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_super_admin(db_session: AsyncSession, test_super_admin_data: Dict[str, Any]) -> User:
    """Create a test super admin user in the database."""
    super_admin = User(
        email=test_super_admin_data["email"],
        name=test_super_admin_data["name"],
        company=test_super_admin_data["company"],
        password_hash=AuthService.hash_password(test_super_admin_data["password"]),
        role=test_super_admin_data["role"],
        status=test_super_admin_data["status"],
        registration_status=test_super_admin_data["registration_status"],
        email_verified_at=datetime.utcnow(),
        approved_at=datetime.utcnow(),
    )
    db_session.add(super_admin)
    await db_session.commit()
    await db_session.refresh(super_admin)
    return super_admin


# Client fixtures
@pytest.fixture
async def test_client_data() -> Dict[str, Any]:
    """Test client data."""
    return {
        "name": "Test Client",
        "description": "Test client for testing purposes",
        "contact_email": "contact@testclient.com",
        "is_active": True,
    }


@pytest.fixture
async def test_client_entity(db_session: AsyncSession, test_client_data: Dict[str, Any]) -> Client:
    """Create a test client in the database."""
    client = Client(**test_client_data)
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client


# Service Account fixtures
@pytest.fixture
async def test_service_account_data(test_client_entity: Client) -> Dict[str, Any]:
    """Test service account data."""
    return {
        "client_id": test_client_entity.id,
        "email": "test-service@test-project.iam.gserviceaccount.com",
        "secret_name": "test-service-account-key",
        "display_name": "Test Service Account",
        "project_id": "test-project",
        "is_active": True,
        "health_status": "healthy",
    }


@pytest.fixture
async def test_service_account(db_session: AsyncSession, test_service_account_data: Dict[str, Any]) -> ServiceAccount:
    """Create a test service account in the database."""
    service_account = ServiceAccount(**test_service_account_data)
    db_session.add(service_account)
    await db_session.commit()
    await db_session.refresh(service_account)
    return service_account


# Authentication fixtures
@pytest.fixture
async def auth_headers(test_user: User) -> Dict[str, str]:
    """Create authentication headers for test user."""
    token_data = {"sub": test_user.email, "user_id": test_user.id, "role": test_user.role.value}
    access_token = AuthService.create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def admin_auth_headers(test_admin: User) -> Dict[str, str]:
    """Create authentication headers for admin user."""
    token_data = {"sub": test_admin.email, "user_id": test_admin.id, "role": test_admin.role.value}
    access_token = AuthService.create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def super_admin_auth_headers(test_super_admin: User) -> Dict[str, str]:
    """Create authentication headers for super admin user."""
    token_data = {"sub": test_super_admin.email, "user_id": test_super_admin.id, "role": test_super_admin.role.value}
    access_token = AuthService.create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


# Permission Grant fixtures
@pytest.fixture
async def test_permission_grant_data(
    test_user: User, 
    test_client_entity: Client, 
    test_service_account: ServiceAccount
) -> Dict[str, Any]:
    """Test permission grant data."""
    return {
        "user_id": test_user.id,
        "client_id": test_client_entity.id,
        "service_account_id": test_service_account.id,
        "ga_property_id": "properties/123456789",
        "target_email": "user@example.com",
        "permission_level": PermissionLevel.VIEWER,
        "status": PermissionStatus.APPROVED,
        "expires_at": datetime.utcnow() + timedelta(days=30),
        "reason": "Test permission grant",
    }


@pytest.fixture
async def test_permission_grant(
    db_session: AsyncSession, 
    test_permission_grant_data: Dict[str, Any]
) -> PermissionGrant:
    """Create a test permission grant in the database."""
    permission_grant = PermissionGrant(**test_permission_grant_data)
    db_session.add(permission_grant)
    await db_session.commit()
    await db_session.refresh(permission_grant)
    return permission_grant


# Mock fixtures
@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    with patch('src.services.email_service.EmailService') as mock:
        mock_instance = Mock()
        mock_instance.send_email = AsyncMock(return_value=True)
        mock_instance.send_notification = AsyncMock(return_value=True)
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_google_api():
    """Mock Google API service for testing."""
    with patch('src.services.google_api_service.GoogleAPIService') as mock:
        mock_instance = Mock()
        mock_instance.grant_permission = AsyncMock(return_value={"success": True})
        mock_instance.revoke_permission = AsyncMock(return_value={"success": True})
        mock_instance.list_properties = AsyncMock(return_value=[
            {"property_id": "properties/123456789", "name": "Test Property"}
        ])
        mock.return_value = mock_instance
        yield mock_instance


# Performance testing fixtures
@pytest.fixture
def performance_threshold():
    """Performance threshold in milliseconds."""
    return 200  # 200ms response time threshold


# Security testing fixtures
@pytest.fixture
def malicious_payloads():
    """Common malicious payloads for security testing."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users --",
            "admin'--",
            "admin' OR 1=1#",
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'><script>alert('xss')</script>",
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| whoami",
            "& dir",
            "`id`",
            "$(id)",
        ]
    }


@pytest.fixture
def brute_force_attempts():
    """Generate multiple login attempts for brute force testing."""
    return [
        {"email": "testuser@example.com", "password": f"wrongpass{i}"}
        for i in range(10)
    ]


# Test data factories
class UserFactory:
    """Factory for creating test users."""
    
    @staticmethod
    def create_user_data(
        email: str = None,
        name: str = None,
        role: UserRole = UserRole.REQUESTER,
        status: UserStatus = UserStatus.ACTIVE,
        **kwargs
    ) -> Dict[str, Any]:
        """Create user data with optional overrides."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        return {
            "email": email or f"user{unique_id}@example.com",
            "name": name or f"User {unique_id}",
            "company": "Test Company",
            "password": "TestPassword123!",
            "role": role,
            "status": status,
            "registration_status": RegistrationStatus.APPROVED,
            **kwargs
        }
    
    @staticmethod
    async def create_user(db_session: AsyncSession, **kwargs) -> User:
        """Create a user in the database."""
        user_data = UserFactory.create_user_data(**kwargs)
        password = user_data.pop("password")
        
        user = User(
            **user_data,
            password_hash=AuthService.hash_password(password),
            email_verified_at=datetime.utcnow(),
            approved_at=datetime.utcnow(),
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user


class ClientFactory:
    """Factory for creating test clients."""
    
    @staticmethod
    def create_client_data(name: str = None, **kwargs) -> Dict[str, Any]:
        """Create client data with optional overrides."""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        return {
            "name": name or f"Client {unique_id}",
            "description": f"Test client {unique_id}",
            "contact_email": f"contact{unique_id}@example.com",
            "is_active": True,
            **kwargs
        }
    
    @staticmethod
    async def create_client(db_session: AsyncSession, **kwargs) -> Client:
        """Create a client in the database."""
        client_data = ClientFactory.create_client_data(**kwargs)
        client = Client(**client_data)
        
        db_session.add(client)
        await db_session.commit()
        await db_session.refresh(client)
        return client


# Make factories available as fixtures
@pytest.fixture
def user_factory():
    """User factory fixture."""
    return UserFactory


@pytest.fixture
def client_factory():
    """Client factory fixture."""
    return ClientFactory


# Database utilities
@pytest.fixture
async def db_utils(db_session: AsyncSession):
    """Database utilities for tests."""
    class DatabaseUtils:
        def __init__(self, session: AsyncSession):
            self.session = session
        
        async def count_users(self) -> int:
            """Count users in database."""
            result = await self.session.execute(text("SELECT COUNT(*) FROM users"))
            return result.scalar()
        
        async def count_clients(self) -> int:
            """Count clients in database."""
            result = await self.session.execute(text("SELECT COUNT(*) FROM clients"))
            return result.scalar()
        
        async def clear_table(self, table_name: str):
            """Clear all data from a table."""
            await self.session.execute(text(f"DELETE FROM {table_name}"))
            await self.session.commit()
    
    return DatabaseUtils(db_session)