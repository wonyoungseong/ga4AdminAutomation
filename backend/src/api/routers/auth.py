"""
Authentication API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ...core.database import get_db
from ...core.exceptions import AuthenticationError, ValidationError
from ...models.schemas import UserLogin, UserCreate, Token, UserResponse
from ...services.auth_service import AuthService
from ...services.user_service import UserService

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Register a new user"""
    try:
        user_service = UserService(db)
        user = await user_service.create_user(user_data)
        return user
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Authenticate user and return access token"""
    try:
        auth_service = AuthService(db)
        token = await auth_service.authenticate_user(login_data)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Refresh access token"""
    try:
        auth_service = AuthService(db)
        token = await auth_service.refresh_access_token(refresh_token)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )


@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: Annotated[dict, Depends(AuthService.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get current authenticated user"""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user