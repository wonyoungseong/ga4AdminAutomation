"""
GA4 Admin Automation System - Main Application with Legacy Extensions
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from contextlib import asynccontextmanager
import os

# Core imports
from src.core.config import settings
from src.core.database import init_db
from src.core.exceptions import AppException

# Service imports - Legacy extensions included
from src.services.scheduler_service import scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler with Legacy services"""
    # Startup
    logger.info("Starting GA4 Admin Automation System (Legacy Complete)...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized successfully")
    
    # Start scheduler service (Legacy extension)
    await scheduler.start()
    logger.info("Background scheduler service started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GA4 Admin Automation System...")
    
    # Stop scheduler service
    await scheduler.stop()
    logger.info("Background scheduler service stopped")


# Create FastAPI application
app = FastAPI(
    title="GA4 Admin Automation System - Legacy Complete",
    description="Google Analytics Admin API를 활용한 현대적인 웹 기반 권한 관리 시스템 (Legacy 완전체)",
    version="2.0.0-legacy",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # Allow frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"]
)


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application-specific exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred"
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GA4 Admin Automation System",
        "version": "2.0.0-legacy",
        "features": [
            "Legacy Permission System",
            "Background Scheduler",
            "Notification System",
            "Report Generation",
            "User Permission Management",
            "GA4 Property Management"
        ]
    }


# Legacy Services Status endpoint
@app.get("/legacy-status", tags=["Legacy"])
async def legacy_status():
    """Get status of Legacy extension services"""
    try:
        scheduler_status = await scheduler.get_scheduler_status()
        
        return {
            "legacy_services": {
                "scheduler": scheduler_status,
                "services_available": [
                    "UserPermissionService",
                    "GA4PropertyService", 
                    "NotificationService",
                    "ReportService"
                ]
            },
            "database_extensions": [
                "ga4_properties",
                "user_permissions", 
                "notification_logs",
                "report_download_logs"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting legacy status: {e}")
        return {
            "error": "Failed to get legacy status",
            "message": str(e)
        }


# Basic API routes
@app.get("/api/test", tags=["Test"])
async def test_api():
    """Test API endpoint"""
    return {
        "message": "GA4 Admin Automation API is working!",
        "legacy_extensions": "Active"
    }


# Mock authentication for testing
from fastapi import Form

@app.post("/api/auth/login", tags=["Authentication"])
async def mock_login(username: str = Form(...), password: str = Form(...)):
    """Mock login endpoint for testing"""
    return {
        "access_token": "mock-jwt-token",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": username,
            "name": "Test User",
            "role": "admin"
        }
    }


@app.get("/api/users/me", tags=["Users"])
async def get_current_user():
    """Mock current user endpoint"""
    return {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "role": "admin",
        "status": "active"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main_legacy_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )