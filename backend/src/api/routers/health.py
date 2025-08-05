"""
Health check endpoints for monitoring and load balancing
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio
import logging
import time
from typing import Dict, Any

from ...core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    Returns 200 if service is healthy
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "ga4-admin-backend",
        "version": "2.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check including database connectivity
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "ga4-admin-backend",
        "version": "2.0.0",
        "checks": {}
    }
    
    # Database connectivity check
    try:
        start_time = time.time()
        result = await db.execute(text("SELECT 1"))
        db_response_time = (time.time() - start_time) * 1000  # ms
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_response_time, 2)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Memory usage check (basic)
    try:
        import psutil
        memory_percent = psutil.virtual_memory().percent
        health_status["checks"]["memory"] = {
            "status": "healthy" if memory_percent < 90 else "warning",
            "usage_percent": memory_percent
        }
    except ImportError:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "error": "psutil not available"
        }
    
    return health_status

@router.get("/health/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes
    Ensures service is ready to accept traffic
    """
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": time.time()
            }
        )

@router.get("/health/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes
    Simple check to ensure the service is alive
    """
    return {
        "status": "alive",
        "timestamp": time.time()
    }