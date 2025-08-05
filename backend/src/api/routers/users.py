"""
Users API routes with RBAC protection
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional, List

from ...core.database import get_db
from ...core.rbac import (
    Permission, require_permission, get_current_user_with_permissions
)
from ...core.exceptions import AppException
from ...models.schemas import UserResponse, UserUpdate, UserCreate, PaginatedResponse
from ...models.db_models import User, UserRole, UserStatus
from ...services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
@require_permission(Permission.USER_READ)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    status: Optional[UserStatus] = Query(None, description="Filter by user status"),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    List users with optional filters.
    
    Required permissions: USER_READ (ADMIN+ only)
    """
    try:
        user_service = UserService(db)
        users = await user_service.list_users(
            skip=skip,
            limit=limit,
            role=role,
            status=status
        )
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/", response_model=UserResponse)
@require_permission(Permission.USER_CREATE)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user (admin only).
    
    Required permissions: USER_CREATE (ADMIN+ only)
    """
    try:
        user_service = UserService(db)
        user = await user_service.create_user(user_data, is_admin_creation=True)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
@require_permission(Permission.USER_READ, resource_ownership=True, allow_self_access=True)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID.
    
    Required permissions: USER_READ (ADMIN+ for others, own profile allowed)
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
@require_permission(Permission.USER_UPDATE, resource_ownership=True, allow_self_access=True)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user information.
    
    Required permissions: USER_UPDATE (ADMIN+ for others, own profile allowed)
    """
    try:
        user_service = UserService(db)
        user = await user_service.update_user(user_id, user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.delete("/{user_id}")
@require_permission(Permission.USER_DELETE)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (SUPER_ADMIN only).
    
    Required permissions: USER_DELETE (SUPER_ADMIN only)
    """
    try:
        # Prevent self-deletion
        if current_user["user_id"] == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        user_service = UserService(db)
        await user_service.delete_user(user_id)
        return {"message": f"User {user_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )