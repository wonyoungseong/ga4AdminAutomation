"""
GA4 Admin Automation System - Main FastAPI Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import logging
from contextlib import asynccontextmanager
import os

from src.api.routers import auth, users, permissions, clients, notifications, audit, ga4, dashboard, ui_components
from src.core.config import settings
from src.core.database import init_db
from src.core.exceptions import AppException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler"""
    # Startup
    logger.info("Starting GA4 Admin Automation System...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GA4 Admin Automation System...")


# Create FastAPI application
app = FastAPI(
    title="GA4 Admin Automation System",
    description="Google Analytics Admin API를 활용한 현대적인 웹 기반 권한 관리 시스템",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/backend/templates/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="src/backend/templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
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
        "version": "2.0.0"
    }


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(permissions.router, prefix="/api/permissions", tags=["Permissions"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(ga4.router, prefix="/api/ga4", tags=["Google Analytics 4"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(ui_components.router, prefix="/api/ui", tags=["UI Components"])


# Web routes for serving HTML pages
@app.get("/dashboard")
async def dashboard_page(request: Request):
    """Serve dashboard HTML page"""
    # In a real implementation, you would get user data from session/JWT
    mock_user = {
        "id": 1,
        "email": "admin@example.com",
        "name": "Admin User",
        "role": "admin",
        "avatar_url": "https://www.gravatar.com/avatar/admin?s=100&d=identicon"
    }
    
    mock_role_config = {
        "name": "Admin",
        "icon": "Shield",
        "theme": {
            "primary": "#2563EB",
            "secondary": "#0EA5E9"
        }
    }
    
    mock_dashboard_stats = [
        {"label": "Total Users", "value": "150", "change": "+12%", "trend": "up", "icon": "users"},
        {"label": "Active Sessions", "value": "89", "change": "+5%", "trend": "up", "icon": "activity"},
        {"label": "Pending Requests", "value": "23", "change": "-8%", "trend": "down", "icon": "clock"},
        {"label": "System Health", "value": "99.9%", "change": "0%", "trend": "stable", "icon": "shield-check"}
    ]
    
    mock_notifications = {
        "unread_count": 3
    }
    
    mock_primary_widgets = [
        {
            "title": "Recent Users",
            "icon": "users",
            "type": "table",
            "headers": ["Name", "Email", "Role", "Status"],
            "data": [
                ["John Doe", "john@example.com", "Requester", "Active"],
                ["Jane Smith", "jane@example.com", "Viewer", "Active"]
            ],
            "action": "View All"
        }
    ]
    
    mock_sidebar_widgets = [
        {
            "title": "Recent Activity",
            "icon": "activity",
            "type": "activity",
            "data": [
                {
                    "message": "New user registered",
                    "icon": "user-plus",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "time_ago": "2 minutes ago"
                }
            ]
        }
    ]
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": mock_user,
            "role_config": mock_role_config,
            "dashboard_stats": mock_dashboard_stats,
            "notifications": mock_notifications,
            "primary_widgets": mock_primary_widgets,
            "sidebar_widgets": mock_sidebar_widgets
        }
    )


@app.get("/")
async def root(request: Request):
    """Redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")


@app.get("/demo")
async def demo_dashboard(request: Request):
    """Serve enhanced UI/UX demo dashboard"""
    return templates.TemplateResponse("demo-dashboard.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )