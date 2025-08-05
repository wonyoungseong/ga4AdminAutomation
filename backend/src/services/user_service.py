"""
User service
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..core.exceptions import ValidationError, NotFoundError, ConflictError
from ..models.db_models import User, UserRole, UserStatus
from ..models.schemas import UserCreate, UserUpdate, UserResponse
from ..services.auth_service import AuthService


class UserService:
    """User service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    async def create_user(self, user_data: UserCreate, is_admin_creation: bool = False) -> UserResponse:
        """Create a new user"""
        # Check if user with this email already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ConflictError("User with this email already exists")
        
        # Validate password strength
        if len(user_data.password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        # Create user
        hashed_password = AuthService.hash_password(user_data.password)
        
        # Determine user role and status based on registration context
        user_role = UserRole.REQUESTER  # Default role
        user_status = UserStatus.ACTIVE if is_admin_creation else UserStatus.INACTIVE  # Inactive for self-registration
        
        # If role is specified in user_data and it's admin creation, use that role
        if is_admin_creation and hasattr(user_data, 'role') and user_data.role:
            # Map frontend role names to backend enum values
            role_mapping = {
                "Super Admin": UserRole.SUPER_ADMIN,
                "Admin": UserRole.ADMIN,
                "Requester": UserRole.REQUESTER,
                "Viewer": UserRole.VIEWER
            }
            user_role = role_mapping.get(user_data.role, UserRole.REQUESTER)
        
        user = User(
            email=user_data.email,
            name=user_data.name,
            company=user_data.company,
            password_hash=hashed_password,
            role=user_role,
            status=user_status
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return UserResponse.model_validate(user)
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """Update user"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Update fields
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.company is not None:
            user.company = user_data.company
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.status is not None:
            user.status = user_data.status
        if user_data.is_representative is not None:
            user.is_representative = user_data.is_representative
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return UserResponse.model_validate(user)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        await self.db.delete(user)
        await self.db.commit()
        
        return True
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> List[UserResponse]:
        """List users with optional filters"""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return [UserResponse.model_validate(user) for user in users]
    
    async def count_users(
        self,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> int:
        """Count users with optional filters"""
        query = select(func.count(User.id))
        
        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Validate password strength
        if len(new_password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        # Update password
        user.password_hash = AuthService.hash_password(new_password)
        user.password_reset_count += 1
        
        await self.db.commit()
        
        return True