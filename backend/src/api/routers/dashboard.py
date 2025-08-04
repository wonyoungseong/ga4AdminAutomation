"""
Role-based Dashboard API with Enhanced UI/UX Support
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Dict, List, Any
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.exceptions import AuthorizationError
from ...models.schemas import UserResponse
from ...models.db_models import UserRole, UserStatus
from ...services.auth_service import AuthService
from ...services.user_service import UserService
from ...services.permission_service import PermissionService

router = APIRouter()

# Role-based UI/UX Configuration
ROLE_THEMES = {
    "super_admin": {
        "name": "Super Admin",
        "theme": {
            "primary": "#DC2626",      # Red-600
            "secondary": "#F59E0B",    # Amber-500
            "accent": "#7C2D12",       # Red-900
            "background": "#1F2937",   # Gray-800
            "surface": "#374151",     # Gray-700
            "text": "#F9FAFB",        # Gray-50
            "textSecondary": "#D1D5DB" # Gray-300
        },
        "icon": "Crown",
        "gradient": "from-red-900 via-red-700 to-amber-600",
        "permissions": ["all"]
    },
    "admin": {
        "name": "Admin",
        "theme": {
            "primary": "#2563EB",      # Blue-600
            "secondary": "#1E40AF",    # Blue-700
            "accent": "#1E3A8A",       # Blue-800
            "background": "#F8FAFC",   # Slate-50
            "surface": "#FFFFFF",     # White
            "text": "#0F172A",        # Slate-900
            "textSecondary": "#475569" # Slate-600
        },
        "icon": "Shield",
        "gradient": "from-blue-800 via-blue-600 to-blue-500",
        "permissions": ["user_management", "client_management", "permissions"]
    },
    "requester": {
        "name": "Requester",
        "theme": {
            "primary": "#059669",      # Emerald-600
            "secondary": "#0D9488",    # Teal-600
            "accent": "#047857",       # Emerald-700
            "background": "#F0FDF4",   # Green-50
            "surface": "#FFFFFF",     # White
            "text": "#064E3B",        # Emerald-900
            "textSecondary": "#065F46" # Emerald-800
        },
        "icon": "UserPlus",
        "gradient": "from-emerald-700 via-emerald-600 to-teal-600",
        "permissions": ["request_permissions", "view_own_requests"]
    },
    "viewer": {
        "name": "Viewer",
        "theme": {
            "primary": "#7C3AED",      # Violet-600
            "secondary": "#6B7280",    # Gray-500
            "accent": "#5B21B6",       # Violet-800
            "background": "#FAFAFA",   # Gray-50
            "surface": "#FFFFFF",     # White
            "text": "#374151",        # Gray-700
            "textSecondary": "#6B7280" # Gray-500
        },
        "icon": "Eye",
        "gradient": "from-violet-800 via-violet-600 to-gray-500",
        "permissions": ["view_only"]
    }
}

# Dashboard Widget Configuration
WIDGET_CONFIG = {
    "super_admin": [
        "system_overview", "user_stats", "permission_analytics", 
        "security_alerts", "audit_logs", "performance_metrics"
    ],
    "admin": [
        "user_management", "permission_requests", "client_overview", 
        "recent_activities", "approval_queue"
    ],
    "requester": [
        "my_requests", "request_status", "available_clients", 
        "quick_request", "request_history"
    ],
    "viewer": [
        "assigned_properties", "access_overview", "recent_changes"
    ]
}


@router.get("/config", response_model=Dict[str, Any])
async def get_dashboard_config(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Get role-based dashboard configuration"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ROLE_THEMES:
        user_role = "viewer"
    
    config = ROLE_THEMES[user_role].copy()
    config["widgets"] =  get_widgets_for_role(user_role)
    config["user_info"] = {
        "id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "name": current_user.get("name", current_user.get("email")),
        "role": user_role,
        "avatar": generate_avatar_url(current_user.get("email"))
    }
    
    return config


@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Get role-based dashboard statistics"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_role = current_user.get("role", "viewer").lower()
    user_id = current_user.get("user_id")
    
    try:
        user_service = UserService(db)
        permission_service = PermissionService(db)
        
        if user_role in ["super_admin", "admin"]:
            stats = await get_admin_stats(user_service, permission_service)
        elif user_role == "requester":
            stats = await get_requester_stats(user_service, permission_service, user_id)
        else:  # viewer
            stats = await get_viewer_stats(user_service, permission_service, user_id)
        
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )


@router.get("/widgets/{widget_type}", response_model=Dict[str, Any])
async def get_widget_data(
    widget_type: str,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Get data for specific dashboard widget"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_role = current_user.get("role", "viewer").lower()
    user_id = current_user.get("user_id")
    
    # Check if user has permission to access this widget
    allowed_widgets = WIDGET_CONFIG.get(user_role, [])
    if widget_type not in allowed_widgets:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access this widget"
        )
    
    try:
        widget_data = await get_widget_data_by_type(
            widget_type, user_role, user_id, db
        )
        return widget_data
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch widget data: {str(e)}"
        )


@router.get("/notifications", response_model=Dict[str, Any])
async def get_role_notifications(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Get role-based notifications with UI styling"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_role = current_user.get("role", "viewer").lower()
    user_id = current_user.get("user_id")
    
    try:
        notifications = await get_notifications_for_role(
            user_role, user_id, db
        )
        return {
            "notifications": notifications,
            "unread_count": len([n for n in notifications if not n.get("read", False)]),
            "priority_count": len([n for n in notifications if n.get("priority") == "high"])
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notifications: {str(e)}"
        )


# Helper Functions
def get_widgets_for_role(role: str) -> List[Dict[str, Any]]:
    """Get widget configuration for specific role"""
    widget_types = WIDGET_CONFIG.get(role, [])
    
    widget_definitions = {
        "system_overview": {
            "id": "system_overview",
            "title": "System Overview",
            "type": "stats_grid",
            "icon": "Activity",
            "size": "large",
            "priority": 1
        },
        "user_stats": {
            "id": "user_stats",
            "title": "User Statistics",
            "type": "chart",
            "icon": "Users",
            "size": "medium",
            "priority": 2
        },
        "permission_analytics": {
            "id": "permission_analytics",
            "title": "Permission Analytics",
            "type": "chart",
            "icon": "BarChart3",
            "size": "large",
            "priority": 3
        },
        "security_alerts": {
            "id": "security_alerts",
            "title": "Security Alerts",
            "type": "alert_list",
            "icon": "AlertTriangle",
            "size": "medium",
            "priority": 4
        },
        "user_management": {
            "id": "user_management",
            "title": "User Management",
            "type": "table",
            "icon": "UserCog",
            "size": "large",
            "priority": 1
        },
        "permission_requests": {
            "id": "permission_requests",
            "title": "Permission Requests",
            "type": "list",
            "icon": "FileText",
            "size": "medium",
            "priority": 2
        },
        "my_requests": {
            "id": "my_requests",
            "title": "My Requests",
            "type": "timeline",
            "icon": "Clock",
            "size": "large",
            "priority": 1
        },
        "request_status": {
            "id": "request_status",
            "title": "Request Status",
            "type": "progress",
            "icon": "TrendingUp",
            "size": "medium",
            "priority": 2
        },
        "assigned_properties": {
            "id": "assigned_properties",
            "title": "Assigned Properties",
            "type": "card_grid",
            "icon": "Building",
            "size": "large",
            "priority": 1
        }
    }
    
    return [
        widget_definitions.get(widget_type, {
            "id": widget_type,
            "title": widget_type.replace("_", " ").title(),
            "type": "generic",
            "icon": "Square",
            "size": "medium",
            "priority": 99
        })
        for widget_type in widget_types
    ]


def generate_avatar_url(email: str) -> str:
    """Generate avatar URL for user"""
    import hashlib
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s=100&d=identicon"


async def get_admin_stats(user_service: UserService, permission_service: PermissionService) -> Dict[str, Any]:
    """Get statistics for admin users"""
    # Mock data - replace with actual service calls
    return {
        "total_users": 150,
        "active_users": 142,
        "pending_requests": 23,
        "total_clients": 45,
        "recent_activities": [
            {
                "id": 1,
                "type": "user_created",
                "message": "New user registered: john@example.com",
                "timestamp": datetime.now().isoformat(),
                "severity": "info"
            },
            {
                "id": 2,
                "type": "permission_granted",
                "message": "Permission granted for GA4 Property",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "severity": "success"
            }
        ],
        "charts": {
            "user_growth": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "data": [10, 25, 45, 78, 120, 150]
            },
            "permission_requests": {
                "labels": ["Pending", "Approved", "Rejected"],
                "data": [23, 145, 12]
            }
        }
    }


async def get_requester_stats(user_service: UserService, permission_service: PermissionService, user_id: int) -> Dict[str, Any]:
    """Get statistics for requester users"""
    # Mock data - replace with actual service calls
    return {
        "my_requests_count": 8,
        "pending_requests": 3,
        "approved_requests": 4,
        "rejected_requests": 1,
        "available_clients": 12,
        "recent_requests": [
            {
                "id": 1,
                "client_name": "Acme Corp",
                "property_name": "Website Analytics",
                "status": "pending",
                "requested_at": datetime.now().isoformat(),
                "permission_type": "viewer"
            },
            {
                "id": 2,
                "client_name": "Tech Startup",
                "property_name": "Mobile App Analytics",
                "status": "approved",
                "requested_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "permission_type": "editor"
            }
        ],
        "request_timeline": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "data": [1, 2, 1, 3, 0, 1]
        }
    }


async def get_viewer_stats(user_service: UserService, permission_service: PermissionService, user_id: int) -> Dict[str, Any]:
    """Get statistics for viewer users"""
    # Mock data - replace with actual service calls
    return {
        "assigned_properties": 5,
        "active_permissions": 3,
        "recent_access": [
            {
                "property_name": "E-commerce Analytics",
                "client_name": "Online Store",
                "last_accessed": datetime.now().isoformat(),
                "permission_type": "viewer"
            },
            {
                "property_name": "Blog Analytics",
                "client_name": "Content Site",
                "last_accessed": (datetime.now() - timedelta(hours=5)).isoformat(),
                "permission_type": "viewer"
            }
        ]
    }


async def get_widget_data_by_type(widget_type: str, user_role: str, user_id: int, db: AsyncSession) -> Dict[str, Any]:
    """Get specific widget data based on type"""
    # Mock implementation - replace with actual data fetching
    widget_data_map = {
        "system_overview": {
            "metrics": [
                {"label": "Total Users", "value": 150, "change": "+12%", "trend": "up"},
                {"label": "Active Sessions", "value": 89, "change": "+5%", "trend": "up"},
                {"label": "Pending Requests", "value": 23, "change": "-8%", "trend": "down"},
                {"label": "System Health", "value": "99.9%", "change": "0%", "trend": "stable"}
            ]
        },
        "my_requests": {
            "requests": [
                {
                    "id": 1,
                    "title": "Access to Marketing Analytics",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "client": "Acme Corp",
                    "priority": "high"
                },
                {
                    "id": 2,
                    "title": "Viewer Access to Sales Data",
                    "status": "approved",
                    "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                    "client": "Tech Startup",
                    "priority": "medium"
                }
            ]
        }
    }
    
    return widget_data_map.get(widget_type, {"message": "Widget data not available"})


async def get_notifications_for_role(user_role: str, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """Get role-specific notifications"""
    # Mock implementation - replace with actual notification service
    base_notifications = [
        {
            "id": 1,
            "title": "Welcome to the Dashboard",
            "message": "Your account has been set up successfully.",
            "type": "info",
            "priority": "low",
            "read": False,
            "created_at": datetime.now().isoformat(),
            "icon": "Info"
        }
    ]
    
    role_specific = {
        "super_admin": [
            {
                "id": 2,
                "title": "System Alert",
                "message": "High CPU usage detected on server.",
                "type": "warning",
                "priority": "high",
                "read": False,
                "created_at": datetime.now().isoformat(),
                "icon": "AlertTriangle"
            }
        ],
        "admin": [
            {
                "id": 3,
                "title": "Pending Approval",
                "message": "5 permission requests awaiting approval.",
                "type": "info",
                "priority": "medium",
                "read": False,
                "created_at": datetime.now().isoformat(),
                "icon": "Clock"
            }
        ],
        "requester": [
            {
                "id": 4,
                "title": "Request Approved",
                "message": "Your request for Analytics access has been approved.",
                "type": "success",
                "priority": "medium",
                "read": False,
                "created_at": datetime.now().isoformat(),
                "icon": "CheckCircle"
            }
        ]
    }
    
    return base_notifications + role_specific.get(user_role, [])
