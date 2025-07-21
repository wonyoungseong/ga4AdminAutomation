"""
User Management Service
=======================

사용자 권한 관리 및 시스템 권한 상향 서비스
- 등록된 사용자 목록 조회
- 시스템 권한 및 GA4 권한 상향/변경
- 권한 변경 로그 및 감사 추적
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..models import db_models as models, schemas
from ..models.domain_models import RoleType, UserStatus
from ..core.permission_cache import permission_cache

logger = logging.getLogger(__name__)


class UserManagementService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_admin_info(self, current_admin):
        """Admin 정보 추출 (딕셔너리 또는 모델 객체 처리)"""
        if isinstance(current_admin, dict):
            # JWT 토큰에서 온 딕셔너리인 경우, 데이터베이스에서 실제 Admin 정보 조회
            user_id = current_admin.get('user_id')
            if user_id:
                admin_query = select(models.Admin).filter(models.Admin.id == user_id)
                admin_result = await self.db.execute(admin_query)
                admin_obj = admin_result.scalar_one_or_none()
                
                if admin_obj:
                    return {
                        'is_super_admin': admin_obj.is_super_admin,
                        'client_id': admin_obj.client_id,
                        'email': admin_obj.email,
                        'user_id': str(admin_obj.id)
                    }
            
            # fallback to token data
            return {
                'is_super_admin': current_admin.get('role') == 'SUPER_ADMIN',
                'client_id': current_admin.get('client_id'),
                'email': current_admin.get('email'),
                'user_id': current_admin.get('user_id')
            }
        else:
            return {
                'is_super_admin': getattr(current_admin, 'is_super_admin', False),
                'client_id': getattr(current_admin, 'client_id', None),
                'email': getattr(current_admin, 'email', ''),
                'user_id': str(getattr(current_admin, 'id', ''))
            }

    async def get_registered_users(
        self, 
        current_admin,  # Dict[str, Any] 또는 models.Admin
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        user_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> schemas.UserListResponseDto:
        """
        등록된 사용자 목록 조회 (권한 관리용)
        
        Args:
            current_admin: 현재 관리자
            page: 페이지 번호
            per_page: 페이지당 항목 수
            search: 검색 키워드 (이름, 이메일)
            user_type: 사용자 유형 필터 ('admin', 'requester')
            status_filter: 상태 필터 ('active', 'pending', 'inactive')
        """
        try:
            # Admin 정보 추출
            admin_info = await self._get_admin_info(current_admin)
            
            users = []
            
            # 1. 승인된 Requester 조회
            if user_type is None or user_type == 'requester':
                requester_query = select(models.Requester).filter(
                    models.Requester.status == UserStatus.ACTIVE
                )
                
                # 검색 조건 추가
                if search:
                    requester_query = requester_query.filter(
                        or_(
                            models.Requester.name.ilike(f"%{search}%"),
                            models.Requester.email.ilike(f"%{search}%")
                        )
                    )
                
                # Admin이 super_admin이 아닌 경우 클라이언트 필터링
                if not admin_info['is_super_admin']:
                    if admin_info['client_id']:
                        # 클라이언트가 할당된 일반 Admin은 해당 클라이언트만
                        requester_query = requester_query.filter(
                            models.Requester.client_id == admin_info['client_id']
                        )
                    else:
                        # 클라이언트가 할당되지 않은 일반 Admin은 아무것도 볼 수 없음
                        requester_query = requester_query.filter(
                            models.Requester.id == None  # 항상 false인 조건
                        )
                
                requester_result = await self.db.execute(requester_query)
                requesters = requester_result.scalars().all()
                
                # Requester 데이터 변환
                for requester in requesters:
                    # Client 정보 조회
                    client = None
                    if requester.client_id:
                        client_query = select(models.Client).filter(
                            models.Client.id == requester.client_id
                        )
                        client_result = await self.db.execute(client_query)
                        client = client_result.scalar_one_or_none()
                    
                    # 역할에 따라 user_type과 system_role 결정
                    role_str = requester.role.value if hasattr(requester.role, 'value') else str(requester.role)
                    
                    # user_type은 항상 "requester" (테이블 기준)
                    user_type = "requester"
                    
                    # 캐시에서 권한 정보 확인
                    cached_perms = permission_cache.get_permissions(str(requester.id))
                    
                    if cached_perms:
                        # 캐시된 권한 사용
                        system_role, ga4_role = cached_perms
                        if not ga4_role:  # GA4 권한이 캐시에 없으면 기본값 사용
                            ga4_role = "administrator" if system_role in ["admin", "super_admin"] else role_str.lower()
                        # Handle legacy 'admin' GA4 role from cache
                        if ga4_role == "admin":
                            ga4_role = "administrator"
                    else:
                        # 캐시가 없으면 DB 값으로 결정
                        # 시스템 권한과 GA4 권한 분리
                        # ADMIN/SUPER_ADMIN은 시스템 권한, 나머지는 GA4 권한
                        role_str_upper = role_str.upper()
                        if role_str_upper == 'SUPER_ADMIN':
                            system_role = "super_admin"
                            ga4_role = "administrator"  # 기본 GA4 권한
                        elif role_str_upper == 'ADMIN':
                            system_role = "admin"
                            ga4_role = "administrator"  # 기본 GA4 권한
                        else:
                            system_role = "requester"
                            ga4_role = role_str.lower()
                            # Handle legacy 'admin' GA4 role
                            if ga4_role == "admin":
                                ga4_role = "administrator"
                    
                    user_data = schemas.RegisteredUserResponseDto(
                        id=str(requester.id),
                        name=requester.name,
                        email=requester.email,
                        department=requester.department or "",
                        user_type=user_type,
                        system_role=system_role,
                        ga4_role=ga4_role,
                        client_id=str(requester.client_id) if requester.client_id else None,
                        client_name=client.name if client else None,
                        service_account_id=str(requester.service_account_id) if requester.service_account_id else None,
                        status=requester.status.value if hasattr(requester.status, 'value') else str(requester.status),
                        last_login=requester.last_login,
                        created_at=requester.created_at,
                        updated_at=requester.updated_at
                    )
                    users.append(user_data)
            
            # 2. Admin 사용자 조회 (super_admin만 조회 가능)
            if (user_type is None or user_type == 'admin') and admin_info['is_super_admin']:
                admin_query = select(models.Admin).filter(
                    models.Admin.status == UserStatus.ACTIVE
                )
                
                # 검색 조건 추가
                if search:
                    admin_query = admin_query.filter(
                        or_(
                            models.Admin.name.ilike(f"%{search}%"),
                            models.Admin.email.ilike(f"%{search}%")
                        )
                    )
                
                admin_result = await self.db.execute(admin_query)
                admins = admin_result.scalars().all()
                
                # Admin 데이터 변환
                for admin in admins:
                    # Client 정보 조회
                    client = None
                    if admin.client_id:
                        client_query = select(models.Client).filter(
                            models.Client.id == admin.client_id
                        )
                        client_result = await self.db.execute(client_query)
                        client = client_result.scalar_one_or_none()
                    
                    system_role = "super_admin" if admin.is_super_admin else "admin"
                    
                    # Admin 사용자도 GA4 권한을 가질 수 있음
                    # Admin 테이블의 role 필드가 GA4 권한을 저장
                    ga4_role = None
                    if admin.role:
                        role_str = admin.role.value if hasattr(admin.role, 'value') else str(admin.role)
                        # Admin 테이블의 사용자는 role 필드에 GA4 권한 저장
                        # ADMIN/SUPER_ADMIN이 저장되어 있으면 기본값 사용
                        if role_str in ['ADMIN', 'SUPER_ADMIN']:
                            ga4_role = "administrator"  # 기본 GA4 권한
                        else:
                            ga4_role = role_str.lower()
                            # Handle legacy 'admin' GA4 role
                            if ga4_role == "admin":
                                ga4_role = "administrator"
                    
                    user_data = schemas.RegisteredUserResponseDto(
                        id=str(admin.id),
                        name=admin.name,
                        email=admin.email,
                        department=admin.department or "",
                        user_type="admin",
                        system_role=system_role,
                        ga4_role=ga4_role,
                        client_id=str(admin.client_id) if admin.client_id else None,
                        client_name=client.name if client else None,
                        service_account_id=None,
                        status=admin.status.value if hasattr(admin.status, 'value') else str(admin.status),
                        last_login=admin.last_login,
                        created_at=admin.created_at,
                        updated_at=admin.updated_at
                    )
                    users.append(user_data)
            
            # 페이지네이션 처리
            total = len(users)
            offset = (page - 1) * per_page
            paginated_users = users[offset:offset + per_page]
            total_pages = (total + per_page - 1) // per_page
            
            logger.info(f"사용자 목록 조회 완료: {total}명, 페이지 {page}/{total_pages}")
            
            return schemas.UserListResponseDto(
                users=paginated_users,
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"사용자 목록 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}"
            )

    async def update_user_permissions(
        self,
        current_admin,  # Dict[str, Any] 또는 models.Admin
        update_data: schemas.UserPermissionUpdateDto
    ) -> schemas.UserPermissionUpdateResponseDto:
        """
        사용자 권한 상향/변경
        
        Args:
            current_admin: 현재 관리자
            update_data: 권한 변경 요청 데이터
        """
        try:
            # Admin 정보 추출
            admin_info = await self._get_admin_info(current_admin)
            
            # 1. 대상 사용자 조회
            target_user = await self._get_target_user(update_data.user_id, update_data.user_type)
            if not target_user:
                # Enhanced error logging for debugging
                logger.error(f"User not found: user_id={update_data.user_id} (type: {type(update_data.user_id)}, len: {len(update_data.user_id)}), user_type={update_data.user_type}")
                logger.error(f"Request data: {update_data.model_dump()}")
                
                # Check if it's a UUID format issue
                if len(update_data.user_id) != 36 or update_data.user_id.count('-') != 4:
                    logger.error(f"Invalid UUID format detected: {update_data.user_id}")
                
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"대상 사용자를 찾을 수 없습니다 (ID: {update_data.user_id[:8]}...)"
                )
            
            # 2. 권한 변경 유효성 검사 (클라이언트 접근 권한 포함)
            if not self._validate_permission_update(admin_info, update_data, target_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="권한 변경 권한이 없습니다"
                )
            
            # 3. 이전 권한 저장
            old_system_role = None
            old_ga4_role = None
            
            # Check if user is from Admin table or Requester table
            if hasattr(target_user, 'is_super_admin'):
                # User is from Admin table
                old_system_role = "super_admin" if target_user.is_super_admin else "admin"
                # Admin 테이블 사용자의 GA4 권한
                if target_user.role:
                    role_str = target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)
                    if role_str not in ['ADMIN', 'SUPER_ADMIN']:
                        old_ga4_role = role_str.lower()
                    else:
                        old_ga4_role = "administrator"
            else:
                # User is from Requester table
                role_str = target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)
                
                # 캐시에서 권한 확인
                cached_perms = permission_cache.get_permissions(str(target_user.id))
                if cached_perms:
                    old_system_role, old_ga4_role = cached_perms
                else:
                    # 캐시가 없으면 role 필드로 판단
                    # Note: role_str might be lowercase from enum
                    role_str_upper = role_str.upper()
                    if role_str_upper == 'SUPER_ADMIN':
                        old_system_role = "super_admin"
                        old_ga4_role = "administrator"
                    elif role_str_upper == 'ADMIN':
                        old_system_role = "admin"
                        old_ga4_role = "administrator"
                    else:
                        old_system_role = "requester"
                        old_ga4_role = role_str.lower()
            
            # 4. 권한 업데이트 실행
            new_system_role = update_data.system_role or old_system_role
            new_ga4_role = update_data.ga4_role or old_ga4_role
            
            await self._apply_permission_update(target_user, update_data, admin_info)
            
            # 5. 감사 로그 기록
            await self._create_audit_log(
                admin_info, target_user, update_data,
                old_system_role, new_system_role,
                old_ga4_role, new_ga4_role
            )
            
            # 6. 변경사항 커밋
            logger.info(f"About to commit changes for {target_user.email}")
            logger.info(f"Session dirty before commit: {list(self.db.dirty)}")
            logger.info(f"Session new before commit: {list(self.db.new)}")
            
            try:
                await self.db.commit()
                logger.info(f"Commit successful for {target_user.email}")
                
                await self.db.refresh(target_user)
                logger.info(f"Refresh successful for {target_user.email}")
                
                # Verify the change
                final_role = target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)
                logger.info(f"사용자 권한 변경 완료: {target_user.email} by {admin_info['email']}, final role: {final_role}")
            except Exception as commit_error:
                logger.error(f"Error during commit: {commit_error}")
                raise
            
            return schemas.UserPermissionUpdateResponseDto(
                success=True,
                message="사용자 권한이 성공적으로 변경되었습니다",
                user_id=update_data.user_id,
                old_system_role=old_system_role,
                new_system_role=new_system_role,
                old_ga4_role=old_ga4_role,
                new_ga4_role=new_ga4_role,
                updated_by=admin_info['email'],
                updated_at=datetime.utcnow()
            )
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"사용자 권한 변경 실패: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"사용자 권한 변경 중 오류가 발생했습니다: {str(e)}"
            )

    def _validate_permission_update(
        self, 
        admin_info: dict, 
        update_data: schemas.UserPermissionUpdateDto,
        target_user
    ) -> bool:
        """권한 변경 유효성 검사"""
        
        # super_admin은 모든 권한 변경 가능
        if admin_info['is_super_admin']:
            return True
        
        # 일반 admin은 자신이 속한 클라이언트의 사용자만 관리 가능
        if not admin_info['client_id']:
            return False
        
        # 대상 사용자의 클라이언트 ID 확인
        target_client_id = getattr(target_user, 'client_id', None)
        if target_client_id != admin_info['client_id']:
            return False
        
        # 일반 admin이 가능한 작업:
        # 1. requester를 admin으로 승격
        if (update_data.user_type == "requester" and 
            update_data.system_role == "admin"):
            return True
        
        # 2. requester의 GA4 권한 변경
        if (update_data.user_type == "requester" and 
            update_data.ga4_role):
            return True
        
        # 3. admin 사용자의 권한 변경 (일반 admin도 같은 클라이언트의 admin 권한 변경 가능)
        if update_data.user_type == "admin":
            # 단, super_admin으로의 승격은 불가
            if update_data.system_role != "super_admin":
                return True
        
        # 그 외의 경우는 권한 없음
        return False

    async def _get_target_user(
        self, 
        user_id: str, 
        user_type: str
    ) -> Optional[models.Admin | models.Requester]:
        """대상 사용자 조회"""
        
        # First, try to find in the Admin table
        admin_query = select(models.Admin).filter(models.Admin.id == user_id)
        admin_result = await self.db.execute(admin_query)
        admin_user = admin_result.scalar_one_or_none()
        
        if admin_user:
            return admin_user
        
        # If not found in Admin table, try Requester table
        # This handles the case where a user with ADMIN/SUPER_ADMIN role is still in requesters table
        requester_query = select(models.Requester).filter(models.Requester.id == user_id)
        requester_result = await self.db.execute(requester_query)
        requester_user = requester_result.scalar_one_or_none()
        
        if requester_user:
            # Log if we found an admin-type user in the requesters table
            if user_type == "admin":
                role_str = requester_user.role.value if hasattr(requester_user.role, 'value') else str(requester_user.role)
                if role_str in ['ADMIN', 'SUPER_ADMIN']:
                    logger.info(f"Found admin-type user in requesters table: {requester_user.email} with role {role_str}")
            return requester_user
        
        return None

    async def _apply_permission_update(
        self,
        target_user: models.Admin | models.Requester,
        update_data: schemas.UserPermissionUpdateDto,
        admin_info: dict
    ):
        """권한 업데이트 실행"""
        
        target_user.updated_at = datetime.utcnow()
        
        # Check if target_user is from Admin table or Requester table
        is_admin_table = isinstance(target_user, models.Admin)
        
        # Debug logging
        logger.info(f"_apply_permission_update called for {target_user.email}")
        logger.info(f"  is_admin_table: {is_admin_table}")
        logger.info(f"  update_data.user_type: {update_data.user_type}")
        logger.info(f"  update_data.system_role: {update_data.system_role}")
        logger.info(f"  current role: {target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)}")
        
        # Ensure the user object is part of the session
        if target_user not in self.db:
            logger.info(f"Adding {target_user.email} to session")
            self.db.add(target_user)
        
        if update_data.user_type == "admin" and is_admin_table:
            # Admin 권한 변경 (Admin 테이블의 사용자)
            if update_data.system_role:
                if update_data.system_role == "super_admin":
                    target_user.is_super_admin = True
                elif update_data.system_role == "admin":
                    target_user.is_super_admin = False
                elif update_data.system_role == "requester":
                    # Admin → Requester 강등 처리
                    from .admin_demotion_service import AdminDemotionService
                    demotion_service = AdminDemotionService(self.db)
                    
                    # Get actor information
                    actor_id = admin_info.get('user_id') if admin_info else None
                    
                    # Preserve current GA4 role if exists
                    result = await demotion_service.demote_admin_to_requester(
                        admin_id=str(target_user.id),
                        client_id=target_user.client_id,
                        preserve_ga4_role=True,
                        reason=update_data.reason or "Permission update",
                        actor_id=actor_id,
                        actor_type="admin"
                    )
                    
                    if not result["success"]:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=result.get("error", "Failed to demote admin")
                        )
                    
                    # The demotion service handles everything including deletion
                    # The commit will be handled by the main function
            
            # Admin의 GA4 권한 변경 - Super Admin도 GA4 권한 설정 가능
            # Admin 테이블의 사용자는 role 필드를 GA4 권한 저장에 사용
            if update_data.ga4_role:
                # GA4 권한으로 설정 (viewer, analyst, marketer, editor, administrator)
                ga4_role_value = update_data.ga4_role.lower()
                # RoleType enum은 소문자로 정의되어 있음
                if ga4_role_value == "administrator":
                    target_user.role = RoleType.ADMINISTRATOR
                else:
                    target_user.role = RoleType(ga4_role_value)
        elif update_data.user_type == "admin" and not is_admin_table:
            # Requester 테이블에 있는 Admin 타입 사용자 처리
            current_role_str = target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)
            
            if update_data.system_role:
                # 시스템 권한 변경
                if update_data.system_role == "super_admin":
                    target_user.role = RoleType.SUPER_ADMIN
                elif update_data.system_role == "admin":
                    target_user.role = RoleType.ADMIN
                elif update_data.system_role == "requester":
                    # Admin을 다시 Requester로 강등
                    # 기존 GA4 권한이 있으면 그것으로, 없으면 viewer로
                    cached_perms = permission_cache.get_permissions(str(target_user.id))
                    if cached_perms and cached_perms[1]:
                        ga4_role = cached_perms[1]
                        # Handle legacy 'admin' GA4 role
                        if ga4_role == "admin":
                            ga4_role = "administrator"
                        target_user.role = RoleType(ga4_role.upper()) if ga4_role != "administrator" else RoleType.VIEWER
                    else:
                        # GA4 role이 지정되었으면 사용, 아니면 viewer
                        ga4_role = update_data.ga4_role if update_data.ga4_role else "viewer"
                        # Handle legacy 'admin' GA4 role
                        if ga4_role == "admin":
                            ga4_role = "administrator"
                        
                        if ga4_role == "administrator":
                            target_user.role = RoleType.ADMINISTRATOR
                        else:
                            target_user.role = RoleType(ga4_role.upper())
                        
                        # Ensure the object is marked as modified
                        self.db.add(target_user)
                        
                    # 캐시 삭제
                    permission_cache.clear_user(str(target_user.id))
                    
                    # Explicitly flush
                    await self.db.flush()
                    logger.info(f"Flushed Admin->Requester change for {target_user.email} in requesters table")
            
            # GA4 권한 변경 요청 처리
            if update_data.ga4_role:
                # 현재 시스템 권한 확인
                if update_data.system_role:
                    system_role = update_data.system_role
                elif current_role_str == 'SUPER_ADMIN':
                    system_role = "super_admin"
                elif current_role_str == 'ADMIN':
                    system_role = "admin"
                else:
                    system_role = "requester"
                
                # 캐시에 GA4 권한 저장
                permission_cache.set_permissions(
                    str(target_user.id),
                    system_role,
                    update_data.ga4_role
                )
                logger.info(f"Cached GA4 role for admin user in requesters table: {target_user.email} -> {update_data.ga4_role}")
        else:
            # Requester 권한 변경
            if update_data.system_role in ["admin", "super_admin"]:
                # Admin으로 승격 시 기존 GA4 권한 유지
                # 변경 전의 role 확인
                old_role_str = target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)
                current_ga4_role = None
                
                # 캐시에서 확인
                cached_perms = permission_cache.get_permissions(str(target_user.id))
                if cached_perms:
                    _, current_ga4_role = cached_perms
                elif old_role_str.upper() not in ['ADMIN', 'SUPER_ADMIN']:
                    # 캐시가 없고 현재 role이 GA4 권한인 경우
                    current_ga4_role = old_role_str.lower()
                
                # Requester를 Admin으로 승격
                if update_data.system_role == "super_admin":
                    target_user.role = RoleType.SUPER_ADMIN
                else:
                    target_user.role = RoleType.ADMIN
                
                # GA4 권한 결정: 명시적으로 지정되었으면 그것을, 아니면 현재 권한 유지
                ga4_role_to_cache = update_data.ga4_role if update_data.ga4_role else (current_ga4_role or "administrator")
                
                permission_cache.set_permissions(
                    str(target_user.id),
                    update_data.system_role,
                    ga4_role_to_cache
                )
                
                if update_data.ga4_role:
                    logger.info(f"Cached GA4 role for admin user: {target_user.email} -> {update_data.ga4_role}")
            elif update_data.system_role == "requester":
                # Admin/Super Admin을 Requester로 강등 (Requester 테이블에 있는 경우)
                old_role_str = target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)
                
                # 현재 ADMIN 또는 SUPER_ADMIN 역할인 경우만 처리
                # Note: role_str might be lowercase from enum
                if old_role_str.upper() in ['ADMIN', 'SUPER_ADMIN']:
                    # GA4 권한 결정
                    if update_data.ga4_role:
                        ga4_role = update_data.ga4_role
                    else:
                        # 캐시에서 GA4 권한 확인
                        cached_perms = permission_cache.get_permissions(str(target_user.id))
                        if cached_perms and cached_perms[1]:
                            ga4_role = cached_perms[1]
                        else:
                            ga4_role = "viewer"  # 기본값
                    
                    # Handle legacy 'admin' GA4 role
                    if ga4_role == "admin":
                        ga4_role = "administrator"
                    
                    # GA4 권한으로 role 설정
                    if ga4_role == "administrator":
                        target_user.role = RoleType.ADMINISTRATOR
                    else:
                        target_user.role = RoleType(ga4_role.upper())
                    
                    # Ensure the object is marked as modified
                    self.db.add(target_user)
                    
                    # 캐시 삭제
                    permission_cache.clear_user(str(target_user.id))
                    
                    logger.info(f"Demoted {target_user.email} from {old_role_str} to Requester with GA4 role: {ga4_role}")
                    logger.info(f"New role value: {target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)}")
                    
                    # Explicitly flush changes
                    await self.db.flush()
                    logger.info(f"Flushed changes for {target_user.email}")
            elif update_data.ga4_role:
                # GA4 권한만 변경
                # RoleType enum은 소문자로 정의되어 있음 (administrator 제외)
                ga4_role_value = update_data.ga4_role.lower()
                if ga4_role_value == "administrator":
                    target_user.role = RoleType.ADMINISTRATOR
                else:
                    target_user.role = RoleType(ga4_role_value)
                
                # 현재 시스템 권한 확인
                current_role_str = target_user.role.value if hasattr(target_user.role, 'value') else str(target_user.role)
                if current_role_str in ['ADMIN', 'SUPER_ADMIN']:
                    # Admin/Super Admin 사용자의 GA4 권한 변경 시 캐시 업데이트
                    system_role = "super_admin" if current_role_str == 'SUPER_ADMIN' else "admin"
                    permission_cache.set_permissions(
                        str(target_user.id),
                        system_role,
                        update_data.ga4_role
                    )

    async def _promote_requester_to_admin(self, requester: models.Requester, is_super_admin: bool = False):
        """Requester를 Admin으로 승격 - 단순히 Requester 레코드 수정"""
        
        # Requester 테이블에서 직접 Admin 권한 부여
        # 별도 Admin 테이블로 이동하지 않고 기존 레코드 업데이트
        
        # Admin으로 승격 시 기존 GA4 권한은 유지하되, 
        # ADMIN/SUPER_ADMIN role은 시스템 권한으로만 사용
        current_ga4_role = requester.role
        
        # 시스템 권한 표시를 위한 필드가 필요할 수 있음
        # 현재는 role 필드를 시스템/GA4 권한 모두에 사용
        
        # 필요한 경우 추가 필드 업데이트
        requester.updated_at = datetime.utcnow()

    async def _create_audit_log(
        self,
        admin_info: dict,
        target_user: models.Admin | models.Requester,
        update_data: schemas.UserPermissionUpdateDto,
        old_system_role: str,
        new_system_role: str,
        old_ga4_role: Optional[str],
        new_ga4_role: Optional[str]
    ):
        """감사 로그 생성"""
        
        audit_log = models.AuditLog(
            event_type="USER_PERMISSION_UPDATE",
            target_id=str(target_user.id),
            target_type=update_data.user_type,
            actor_id=admin_info['user_id'],
            actor_type="admin",
            detail=f"권한 변경: {target_user.email}, 사유: {update_data.reason}",
            old_value=f"system:{old_system_role}, ga4:{old_ga4_role}",
            new_value=f"system:{new_system_role}, ga4:{new_ga4_role}",
            created_at=datetime.utcnow()
        )
        
        self.db.add(audit_log)