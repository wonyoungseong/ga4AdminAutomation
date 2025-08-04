"""
Enhanced GA4 Admin Automation System with Client Assignment Access Control
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .core.config import settings
from .core.database import init_db, close_db, get_db
from .core.exceptions import AppException
from .models.db_models import ClientAssignmentStatus
from .api.routers import (
    client_assignments,
    clients_enhanced,
    permissions_enhanced,
    permission_requests,
    service_accounts
)

# Import existing routers (assuming they exist)
try:
    from .api.routers import auth, users, audit_logs
except ImportError:
    # Create placeholder routers if they don't exist
    from fastapi import APIRouter
    auth = APIRouter(prefix="/auth", tags=["Authentication"])
    users = APIRouter(prefix="/users", tags=["Users"])
    audit_logs = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting GA4 Admin Automation System...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down GA4 Admin Automation System...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enhanced GA4 Admin Automation System with Client Assignment Access Control",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": getattr(exc, 'error_code', 'UNKNOWN_ERROR'),
                "details": exc.details
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "details": {}
            }
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs" if settings.DEBUG else "Contact administrator for API documentation"
    }


# Include API routers
app.include_router(auth, prefix="/api")
app.include_router(users, prefix="/api")
app.include_router(clients_enhanced.router, prefix="/api")
app.include_router(client_assignments.router, prefix="/api")
app.include_router(permissions_enhanced.router, prefix="/api")
app.include_router(permission_requests.router, prefix="/api")
app.include_router(service_accounts.router, prefix="/api")
app.include_router(audit_logs, prefix="/api")


# Additional endpoints for system administration
@app.get("/api/system/info", tags=["System"])
async def system_info():
    """Get system information"""
    from .core.auth_dependencies import get_current_user, require_roles
    from .models.db_models import UserRole
    
    # This would normally be protected by authentication
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "features": [
            "Client Assignment System",
            "Role-Based Access Control",
            "Enhanced Permission Management",
            "Comprehensive Audit Logging",
            "Client-Level Access Control"
        ],
        "roles": [role.value for role in UserRole],
        "assignment_statuses": [status.value for status in ClientAssignmentStatus]
    }


@app.get("/api/system/stats", tags=["System"])
async def system_stats(db: AsyncSession = Depends(get_db)):
    """Get system statistics (admin only)"""
    from sqlalchemy import select, func
    from .models.db_models import User, Client, ClientAssignment, PermissionGrant
    
    # This would normally be protected by admin authentication
    try:
        # Count statistics
        user_count = await db.scalar(select(func.count(User.id)))
        client_count = await db.scalar(select(func.count(Client.id)))
        assignment_count = await db.scalar(select(func.count(ClientAssignment.id)))
        permission_count = await db.scalar(select(func.count(PermissionGrant.id)))
        
        # Active assignments
        active_assignments = await db.scalar(
            select(func.count(ClientAssignment.id)).where(
                ClientAssignment.status == ClientAssignmentStatus.ACTIVE
            )
        )
        
        return {
            "users": user_count or 0,
            "clients": client_count or 0,
            "total_assignments": assignment_count or 0,
            "active_assignments": active_assignments or 0,
            "permission_grants": permission_count or 0
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            "users": 0,
            "clients": 0,
            "total_assignments": 0,
            "active_assignments": 0,
            "permission_grants": 0,
            "error": "Could not retrieve statistics"
        }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    uvicorn.run(
        "main_enhanced:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )