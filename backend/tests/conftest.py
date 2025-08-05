"""
Simplified pytest configuration for basic testing
"""

import asyncio
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from src.core.database import Base
from src.models.db_models import (
    User, Client, ServiceAccount, PermissionGrant, UserRole, UserStatus, 
    PermissionLevel, PermissionStatus, RegistrationStatus
)
from src.services.auth_service import AuthService


# Test database URL - use in-memory SQLite for fast tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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


# Performance fixtures
@pytest.fixture
def performance_threshold():
    """Performance threshold in milliseconds."""
    return 200  # 200ms response time threshold


# Mock fixtures
@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    mock_instance = Mock()
    mock_instance.send_email = AsyncMock(return_value=True)
    mock_instance.send_notification = AsyncMock(return_value=True)
    return mock_instance


@pytest.fixture
def mock_google_api():
    """Mock Google API service for testing."""
    mock_instance = Mock()
    mock_instance.grant_permission = AsyncMock(return_value={"success": True})
    mock_instance.revoke_permission = AsyncMock(return_value={"success": True})
    mock_instance.list_properties = AsyncMock(return_value=[
        {"property_id": "properties/123456789", "name": "Test Property"}
    ])
    return mock_instance


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
    }