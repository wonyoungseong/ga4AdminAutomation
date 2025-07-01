"""
웹 애플리케이션 라우터 패키지
==========================

기능별로 분리된 FastAPI 라우터들을 제공합니다.
"""

from .dashboard import router as dashboard_router
from .users import router as users_router
from .admin import router as admin_router
from .api import router as api_router
from .test import router as test_router

__all__ = [
    'dashboard_router',
    'users_router', 
    'admin_router',
    'api_router',
    'test_router',
] 