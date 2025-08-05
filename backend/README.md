# GA4 Admin Automation System - Backend

A modern FastAPI backend for Google Analytics 4 permission management with JWT authentication, SQLAlchemy 2.0, and comprehensive user management.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ (for production) or SQLite (for development)
- Redis 7+ (optional, for AI features)

### Installation

1. **Clone and navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
# Run migrations
alembic upgrade head
```

6. **Start development server**
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

7. **Access API documentation**
- Swagger UI: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

## 🏗️ Architecture

### Tech Stack

- **FastAPI 0.115.6**: Modern async web framework
- **SQLAlchemy 2.0**: Async ORM with type hints
- **Alembic**: Database migrations
- **JWT + bcrypt**: Authentication and password hashing
- **Pydantic 2.10**: Data validation and serialization
- **Uvicorn**: ASGI server with auto-reload

### Database Models

**Core Entities:**
- `User`: System users with role-based access
- `Client`: Customer companies
- `ServiceAccount`: Google service accounts
- `PermissionGrant`: GA4 permission assignments
- `AuditLog`: System activity tracking

**Enhanced Features:**
- `ClientAssignment`: User-client relationships
- `PropertyAccessRequest`: Permission request workflow
- `UserSession`: Session management with security tracking
- `PasswordResetToken`: Secure password reset flow

### API Structure

```
/api/
├── auth/          # Authentication (login, register, refresh)
├── users/         # User management
├── permissions/   # Permission management
├── clients/       # Client management
├── ga4/          # Google Analytics 4 integration
├── audit/        # Audit logging
├── notifications/ # Email notifications
├── dashboard/    # Dashboard data
└── health        # Health checks
```

## 🔧 Configuration

### Environment Variables

Key settings in `.env`:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./ga4_admin.db  # Development
# DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db  # Production

# Authentication
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# Features
ENABLE_REGISTRATION=true
ENABLE_PASSWORD_RESET=true
ENABLE_EMAIL_NOTIFICATIONS=false
```

### Database Configuration

**Development (SQLite):**
- Auto-created on first run
- File: `ga4_admin.db`
- Perfect for development and testing

**Production (PostgreSQL):**
- Update `DATABASE_URL` in `.env`
- Run migrations: `alembic upgrade head`
- Supports advanced features and concurrent users

## 🔐 Authentication

### JWT Token System

- **Access Token**: 24-hour expiry, contains user info
- **Refresh Token**: 30-day expiry, for token renewal
- **Stateless**: No server-side session storage

### User Registration Flow

1. User registers with email/password
2. Account created with `PENDING_VERIFICATION` status
3. Admin approval required (status → `APPROVED`)
4. User can login after approval

### API Usage Example

```python
import httpx

# Register user
async with httpx.AsyncClient() as client:
    response = await client.post("http://localhost:8001/api/auth/register", json={
        "email": "user@example.com",
        "name": "John Doe",
        "company": "Example Corp",
        "password": "securepassword123"
    })
    
    # Login
    response = await client.post("http://localhost:8001/api/auth/login", json={
        "email": "user@example.com",
        "password": "securepassword123"
    })
    
    tokens = response.json()
    access_token = tokens["access_token"]
    
    # Authenticated request
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("http://localhost:8001/api/users/me", headers=headers)
```

## 🧪 Testing

### Quick API Test

```bash
python test_api_quick.py
```

This tests:
- ✅ Health endpoint
- ✅ User registration
- ⚠️ User login (requires admin approval)
- ✅ API documentation
- ✅ OpenAPI spec (60 endpoints)

### API Endpoints

**Available endpoints:**
- 60 total endpoints across all routers
- Comprehensive CRUD operations
- Role-based access control
- Detailed API documentation

## 📊 Database Migrations

### Alembic Setup

```bash
# Generate new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Current Schema

- **Initial migration**: `9d1265301279_initial_database_schema.py`
- **Complete schema**: All 14+ tables with relationships
- **SQLite compatible**: Works with both SQLite and PostgreSQL

## 🛡️ Security Features

### Password Security
- **bcrypt hashing**: Industry-standard password hashing
- **Minimum length**: 8 characters (configurable)
- **Salt rounds**: Automatic with bcrypt

### Token Security
- **HMAC-based JWT**: Cryptographically signed tokens
- **Short-lived access tokens**: 24-hour expiry
- **Secure refresh flow**: Separate refresh tokens

### Input Validation
- **Pydantic models**: Comprehensive data validation
- **SQL injection protection**: SQLAlchemy ORM prevents injection
- **CORS configuration**: Configurable allowed origins

## 🚦 Health Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": 1754404100.123,
  "service": "ga4-admin-backend",
  "version": "2.0.0"
}
```

## 📈 Performance

### Async Architecture
- **Full async/await**: Non-blocking I/O operations
- **Connection pooling**: Efficient database connections
- **Lazy loading**: Optimized query patterns

### Production Optimizations
- **Database migrations**: Zero-downtime deployments
- **Connection limits**: Configurable pool settings
- **Logging**: Structured logging with levels

## 🐳 Deployment

### Docker Support

```bash
# Build image
docker build -t ga4-admin-backend .

# Run container
docker run -p 8000:8000 --env-file .env ga4-admin-backend
```

### Production Checklist

- [ ] Change `SECRET_KEY` to secure random value
- [ ] Use PostgreSQL for `DATABASE_URL`
- [ ] Set `DEBUG=false`
- [ ] Configure SMTP for email notifications
- [ ] Set up Redis for AI features (optional)
- [ ] Configure CORS for frontend domain
- [ ] Set up SSL/TLS termination
- [ ] Configure logging and monitoring

## 📚 API Documentation

- **Interactive docs**: http://localhost:8001/api/docs
- **OpenAPI spec**: http://localhost:8001/api/openapi.json
- **Alternative docs**: http://localhost:8001/api/redoc

## 🤝 Development

### Code Style
- **Type hints**: Full type coverage with mypy
- **Async patterns**: Proper async/await usage
- **Error handling**: Comprehensive exception handling
- **Documentation**: Docstrings for all public functions

### Adding New Features
1. Create Pydantic models in `models/schemas.py`
2. Add database models in `models/db_models.py`
3. Generate migration: `alembic revision --autogenerate`
4. Implement service logic in `services/`
5. Create API routes in `api/routers/`
6. Add tests and documentation

---

**Backend Developer**: Complete FastAPI setup with modern async architecture ✅  
**Status**: Phase 1 implementation completed and tested  
**Next**: Frontend integration and Google Analytics 4 API setup