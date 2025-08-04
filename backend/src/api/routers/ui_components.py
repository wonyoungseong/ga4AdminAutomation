"""
UI Components API - Provides reusable UI components and styling data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Dict, List, Any, Optional
from datetime import datetime

from ...core.database import get_db
from ...services.auth_service import AuthService

router = APIRouter()

# Icon mapping for different contexts
ICON_LIBRARY = {
    # Role icons
    "roles": {
        "super_admin": "Crown",
        "admin": "Shield",
        "requester": "UserPlus",
        "viewer": "Eye"
    },
    # Status icons
    "status": {
        "active": "CheckCircle",
        "inactive": "XCircle",
        "pending": "Clock",
        "approved": "Check",
        "rejected": "X",
        "blocked": "Ban"
    },
    # Action icons
    "actions": {
        "create": "Plus",
        "edit": "Edit",
        "delete": "Trash2",
        "view": "Eye",
        "download": "Download",
        "upload": "Upload",
        "refresh": "RefreshCw",
        "search": "Search",
        "filter": "Filter",
        "sort": "ArrowUpDown"
    },
    # Navigation icons
    "navigation": {
        "dashboard": "LayoutDashboard",
        "users": "Users",
        "permissions": "Lock",
        "clients": "Building",
        "analytics": "BarChart3",
        "settings": "Settings",
        "profile": "User",
        "logout": "LogOut"
    },
    # Notification icons
    "notifications": {
        "info": "Info",
        "success": "CheckCircle",
        "warning": "AlertTriangle",
        "error": "AlertCircle"
    },
    # Data visualization
    "charts": {
        "line": "TrendingUp",
        "bar": "BarChart3",
        "pie": "PieChart",
        "area": "Activity"
    }
}

# Color system for role-based theming
COLOR_SYSTEM = {
    "super_admin": {
        "50": "#FEF2F2",
        "100": "#FEE2E2",
        "200": "#FECACA",
        "300": "#FCA5A5",
        "400": "#F87171",
        "500": "#EF4444",
        "600": "#DC2626",  # Primary
        "700": "#B91C1C",
        "800": "#991B1B",
        "900": "#7F1D1D",
        "accent": "#F59E0B"  # Gold
    },
    "admin": {
        "50": "#EFF6FF",
        "100": "#DBEAFE",
        "200": "#BFDBFE",
        "300": "#93C5FD",
        "400": "#60A5FA",
        "500": "#3B82F6",
        "600": "#2563EB",  # Primary
        "700": "#1D4ED8",
        "800": "#1E40AF",
        "900": "#1E3A8A",
        "accent": "#0EA5E9"  # Sky
    },
    "requester": {
        "50": "#ECFDF5",
        "100": "#D1FAE5",
        "200": "#A7F3D0",
        "300": "#6EE7B7",
        "400": "#34D399",
        "500": "#10B981",
        "600": "#059669",  # Primary
        "700": "#047857",
        "800": "#065F46",
        "900": "#064E3B",
        "accent": "#0D9488"  # Teal
    },
    "viewer": {
        "50": "#FAF5FF",
        "100": "#F3E8FF",
        "200": "#E9D5FF",
        "300": "#D8B4FE",
        "400": "#C084FC",
        "500": "#A855F7",
        "600": "#9333EA",
        "700": "#7C3AED",  # Primary
        "800": "#6B21B6",
        "900": "#581C87",
        "accent": "#6B7280"  # Gray
    }
}

# Component templates for consistent UI
COMPONENT_TEMPLATES = {
    "card": {
        "base_classes": "bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700",
        "header_classes": "px-6 py-4 border-b border-gray-200 dark:border-gray-700",
        "content_classes": "px-6 py-4",
        "footer_classes": "px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700"
    },
    "button": {
        "primary": "inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2",
        "secondary": "inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2",
        "ghost": "inline-flex items-center px-4 py-2 text-sm font-medium rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2"
    },
    "input": {
        "base": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:border-transparent sm:text-sm",
        "error": "border-red-300 text-red-900 placeholder-red-300 focus:ring-red-500 focus:border-red-500",
        "success": "border-green-300 focus:ring-green-500 focus:border-green-500"
    },
    "badge": {
        "base": "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        "success": "bg-green-100 text-green-800",
        "warning": "bg-yellow-100 text-yellow-800",
        "error": "bg-red-100 text-red-800",
        "info": "bg-blue-100 text-blue-800",
        "neutral": "bg-gray-100 text-gray-800"
    },
    "skeleton": {
        "base": "animate-pulse bg-gray-200 dark:bg-gray-700 rounded",
        "text": "h-4 bg-gray-200 dark:bg-gray-700 rounded",
        "avatar": "h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-full",
        "button": "h-10 bg-gray-200 dark:bg-gray-700 rounded-md"
    }
}

# Empty state configurations
EMPTY_STATES = {
    "no_data": {
        "icon": "Database",
        "title": "No data available",
        "description": "There's no data to display right now.",
        "action": {
            "label": "Refresh",
            "icon": "RefreshCw"
        }
    },
    "no_permissions": {
        "icon": "Lock",
        "title": "No permissions found",
        "description": "You don't have any permissions assigned yet.",
        "action": {
            "label": "Request Access",
            "icon": "Plus"
        }
    },
    "no_requests": {
        "icon": "FileText",
        "title": "No requests",
        "description": "You haven't made any permission requests yet.",
        "action": {
            "label": "Create Request",
            "icon": "Plus"
        }
    },
    "no_users": {
        "icon": "Users",
        "title": "No users found",
        "description": "No users match your current filters.",
        "action": {
            "label": "Clear Filters",
            "icon": "X"
        }
    },
    "search_empty": {
        "icon": "Search",
        "title": "No results found",
        "description": "Try adjusting your search terms.",
        "action": {
            "label": "Clear Search",
            "icon": "X"
        }
    }
}

# Accessibility configurations
ACCESSIBILITY_CONFIG = {
    "focus_classes": "focus:outline-none focus:ring-2 focus:ring-offset-2",
    "sr_only": "sr-only",
    "skip_link": "sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 bg-blue-600 text-white p-2 rounded",
    "aria_labels": {
        "menu": "Main navigation",
        "search": "Search",
        "user_menu": "User account menu",
        "notifications": "Notifications",
        "close": "Close",
        "expand": "Expand",
        "collapse": "Collapse"
    },
    "keyboard_shortcuts": {
        "search": "Ctrl+K",
        "dashboard": "Alt+D",
        "profile": "Alt+P",
        "help": "?"
    }
}


@router.get("/icons")
async def get_icon_library(
    category: Optional[str] = Query(None, description="Icon category filter"),
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None
):
    """Get icon library for UI components"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    if category and category in ICON_LIBRARY:
        return {"category": category, "icons": ICON_LIBRARY[category]}
    
    return {"categories": list(ICON_LIBRARY.keys()), "icons": ICON_LIBRARY}


@router.get("/colors/{role}")
async def get_role_colors(
    role: str,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None
):
    """Get color system for specific role"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    if role not in COLOR_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Color system not found for role: {role}"
        )
    
    return {
        "role": role,
        "colors": COLOR_SYSTEM[role],
        "css_variables": generate_css_variables(role)
    }


@router.get("/components")
async def get_component_templates(
    component_type: Optional[str] = Query(None, description="Component type filter"),
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None
):
    """Get component templates for consistent styling"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    if component_type and component_type in COMPONENT_TEMPLATES:
        return {
            "component_type": component_type,
            "template": COMPONENT_TEMPLATES[component_type]
        }
    
    return {"templates": COMPONENT_TEMPLATES}


@router.get("/empty-states")
async def get_empty_states(
    state_type: Optional[str] = Query(None, description="Empty state type"),
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None
):
    """Get empty state configurations"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    if state_type and state_type in EMPTY_STATES:
        return {
            "state_type": state_type,
            "config": EMPTY_STATES[state_type]
        }
    
    return {"empty_states": EMPTY_STATES}


@router.get("/accessibility")
async def get_accessibility_config(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None
):
    """Get accessibility configuration"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return ACCESSIBILITY_CONFIG


@router.get("/mobile-breakpoints")
async def get_mobile_breakpoints(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None
):
    """Get mobile responsive breakpoints"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {
        "breakpoints": {
            "sm": "640px",
            "md": "768px",
            "lg": "1024px",
            "xl": "1280px",
            "2xl": "1536px"
        },
        "mobile_first": True,
        "touch_targets": {
            "minimum_size": "44px",
            "recommended_size": "48px",
            "spacing": "8px"
        },
        "mobile_navigation": {
            "drawer_width": "280px",
            "header_height": "56px",
            "bottom_nav_height": "64px"
        }
    }


@router.post("/theme/generate")
async def generate_custom_theme(
    role: str,
    overrides: Dict[str, Any] = {},
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None
):
    """Generate custom theme for role with overrides"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Check if user has permission to generate themes
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to generate themes"
        )
    
    if role not in COLOR_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Base theme not found for role: {role}"
        )
    
    base_theme = COLOR_SYSTEM[role].copy()
    base_theme.update(overrides)
    
    return {
        "role": role,
        "theme": base_theme,
        "css_variables": generate_css_variables(role, base_theme),
        "tailwind_config": generate_tailwind_config(role, base_theme),
        "generated_at": datetime.now().isoformat()
    }


# Helper Functions
def generate_css_variables(role: str, colors: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Generate CSS custom properties for role colors"""
    color_map = colors or COLOR_SYSTEM.get(role, {})
    css_vars = {}
    
    for shade, color in color_map.items():
        if shade == "accent":
            css_vars[f"--color-{role}-accent"] = color
        else:
            css_vars[f"--color-{role}-{shade}"] = color
    
    return css_vars


def generate_tailwind_config(role: str, colors: Dict[str, str]) -> Dict[str, Any]:
    """Generate Tailwind CSS configuration for role theme"""
    return {
        "theme": {
            "extend": {
                "colors": {
                    role: colors
                },
                "animation": {
                    "fade-in": "fadeIn 0.5s ease-in-out",
                    "slide-up": "slideUp 0.3s ease-out",
                    "bounce-gentle": "bounceGentle 2s infinite"
                },
                "keyframes": {
                    "fadeIn": {
                        "0%": {"opacity": "0"},
                        "100%": {"opacity": "1"}
                    },
                    "slideUp": {
                        "0%": {"transform": "translateY(10px)", "opacity": "0"},
                        "100%": {"transform": "translateY(0)", "opacity": "1"}
                    },
                    "bounceGentle": {
                        "0%, 20%, 50%, 80%, 100%": {"transform": "translateY(0)"},
                        "40%": {"transform": "translateY(-4px)"},
                        "60%": {"transform": "translateY(-2px)"}
                    }
                }
            }
        }
    }
