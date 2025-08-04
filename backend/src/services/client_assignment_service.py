"""
Client Assignment Service
Handles client-user assignment operations with access control
"""

from datetime import datetime
from typing import List, Optional, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from ..models.db_models import (
    User, Client, ClientAssignment, AuditLog,
    UserRole, ClientAssignmentStatus
)
from ..models.schemas import (
    ClientAssignmentCreate, ClientAssignmentUpdate, ClientAssignmentBulkCreate,
    ClientAssignmentResponse, AccessControlSummary
)
from ..core.exceptions import PermissionDeniedError, NotFoundError, ValidationError


class ClientAssignmentService:
    """Service for managing client assignments and access control"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_assignment(
        self,
        assignment_data: ClientAssignmentCreate,
        assigned_by_id: int
    ) -> ClientAssignmentResponse:
        """Create a new client assignment"""
        
        # Validate user and client exist
        user = await self._get_user_by_id(assignment_data.user_id)
        client = await self._get_client_by_id(assignment_data.client_id)
        assigned_by = await self._get_user_by_id(assigned_by_id)
        
        # Check for existing assignment
        existing = await self._get_existing_assignment(
            assignment_data.user_id, 
            assignment_data.client_id
        )
        if existing:
            raise ValidationError("User is already assigned to this client")
        
        # Create assignment
        assignment = ClientAssignment(
            user_id=assignment_data.user_id,
            client_id=assignment_data.client_id,
            assigned_by_id=assigned_by_id,
            status=assignment_data.status,
            expires_at=assignment_data.expires_at,
            notes=assignment_data.notes
        )
        
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        
        # Load relationships
        await self._load_assignment_relationships(assignment)
        
        # Create audit log
        await self._create_audit_log(
            action="create_client_assignment",
            actor_id=assigned_by_id,
            resource_type="client_assignment",
            resource_id=str(assignment.id),
            details=f"Assigned user {user.email} to client {client.name}"
        )
        
        return ClientAssignmentResponse.model_validate(assignment)
    
    async def bulk_create_assignments(
        self,
        bulk_data: ClientAssignmentBulkCreate,
        assigned_by_id: int
    ) -> List[ClientAssignmentResponse]:
        """Create multiple client assignments"""
        
        # Validate all users and clients exist
        users = await self._get_users_by_ids(bulk_data.user_ids)
        clients = await self._get_clients_by_ids(bulk_data.client_ids)
        assigned_by = await self._get_user_by_id(assigned_by_id)
        
        if len(users) != len(bulk_data.user_ids):
            raise NotFoundError("One or more users not found")
        if len(clients) != len(bulk_data.client_ids):
            raise NotFoundError("One or more clients not found")
        
        # Check for existing assignments
        existing_assignments = await self._get_existing_assignments_bulk(
            bulk_data.user_ids, bulk_data.client_ids
        )
        
        assignments = []
        created_assignments = []
        
        for user_id in bulk_data.user_ids:
            for client_id in bulk_data.client_ids:
                # Skip if assignment already exists
                if (user_id, client_id) in existing_assignments:
                    continue
                
                assignment = ClientAssignment(
                    user_id=user_id,
                    client_id=client_id,
                    assigned_by_id=assigned_by_id,
                    status=bulk_data.status,
                    expires_at=bulk_data.expires_at,
                    notes=bulk_data.notes
                )
                assignments.append(assignment)
        
        if assignments:
            self.db.add_all(assignments)
            await self.db.commit()
            
            # Load relationships and convert to response objects
            for assignment in assignments:
                await self.db.refresh(assignment)
                await self._load_assignment_relationships(assignment)
                created_assignments.append(ClientAssignmentResponse.model_validate(assignment))
            
            # Create audit log
            await self._create_audit_log(
                action="bulk_create_client_assignments",
                actor_id=assigned_by_id,
                resource_type="client_assignment",
                details=f"Bulk assigned {len(assignments)} client assignments"
            )
        
        return created_assignments
    
    async def update_assignment(
        self,
        assignment_id: int,
        update_data: ClientAssignmentUpdate,
        updated_by_id: int
    ) -> ClientAssignmentResponse:
        """Update a client assignment"""
        
        assignment = await self._get_assignment_by_id(assignment_id)
        updated_by = await self._get_user_by_id(updated_by_id)
        
        # Track changes for audit log
        changes = []
        
        if update_data.status is not None and update_data.status != assignment.status:
            changes.append(f"status: {assignment.status.value} → {update_data.status.value}")
            assignment.status = update_data.status
        
        if update_data.expires_at is not None and update_data.expires_at != assignment.expires_at:
            changes.append(f"expires_at: {assignment.expires_at} → {update_data.expires_at}")
            assignment.expires_at = update_data.expires_at
        
        if update_data.notes is not None and update_data.notes != assignment.notes:
            changes.append(f"notes updated")
            assignment.notes = update_data.notes
        
        if changes:
            assignment.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(assignment)
            
            # Load relationships
            await self._load_assignment_relationships(assignment)
            
            # Create audit log
            await self._create_audit_log(
                action="update_client_assignment",
                actor_id=updated_by_id,
                resource_type="client_assignment",
                resource_id=str(assignment_id),
                details=f"Updated assignment: {', '.join(changes)}"
            )
        
        return ClientAssignmentResponse.model_validate(assignment)
    
    async def delete_assignment(
        self,
        assignment_id: int,
        deleted_by_id: int
    ) -> bool:
        """Delete a client assignment"""
        
        assignment = await self._get_assignment_by_id(assignment_id)
        deleted_by = await self._get_user_by_id(deleted_by_id)
        
        # Load relationships for audit log
        await self._load_assignment_relationships(assignment)
        user_email = assignment.user.email
        client_name = assignment.client.name
        
        # Delete assignment
        await self.db.delete(assignment)
        await self.db.commit()
        
        # Create audit log
        await self._create_audit_log(
            action="delete_client_assignment",
            actor_id=deleted_by_id,
            resource_type="client_assignment",
            resource_id=str(assignment_id),
            details=f"Removed assignment: {user_email} from {client_name}"
        )
        
        return True
    
    async def get_user_assignments(
        self,
        user_id: int,
        include_inactive: bool = False
    ) -> List[ClientAssignmentResponse]:
        """Get all client assignments for a user"""
        
        query = select(ClientAssignment).where(ClientAssignment.user_id == user_id)
        
        if not include_inactive:
            query = query.where(ClientAssignment.status == ClientAssignmentStatus.ACTIVE)
        
        query = query.options(
            selectinload(ClientAssignment.client),
            selectinload(ClientAssignment.assigned_by)
        )
        
        result = await self.db.execute(query)
        assignments = result.scalars().all()
        
        return [ClientAssignmentResponse.model_validate(a) for a in assignments]
    
    async def get_client_assignments(
        self,
        client_id: int,
        include_inactive: bool = False
    ) -> List[ClientAssignmentResponse]:
        """Get all user assignments for a client"""
        
        query = select(ClientAssignment).where(ClientAssignment.client_id == client_id)
        
        if not include_inactive:
            query = query.where(ClientAssignment.status == ClientAssignmentStatus.ACTIVE)
        
        query = query.options(
            selectinload(ClientAssignment.user),
            selectinload(ClientAssignment.assigned_by)
        )
        
        result = await self.db.execute(query)
        assignments = result.scalars().all()
        
        return [ClientAssignmentResponse.model_validate(a) for a in assignments]
    
    async def get_user_accessible_clients(
        self,
        user_id: int,
        user_role: UserRole
    ) -> List[int]:
        """Get list of client IDs accessible to a user based on role and assignments"""
        
        # Super Admins can access all active clients
        if user_role == UserRole.SUPER_ADMIN:
            query = select(Client.id).where(Client.is_active == True)
            result = await self.db.execute(query)
            return [row[0] for row in result.fetchall()]
        
        # Admins can access all clients they manage (assigned clients + all if they manage system)
        elif user_role == UserRole.ADMIN:
            # For now, admins can see all active clients
            # This can be customized based on business rules
            query = select(Client.id).where(Client.is_active == True)
            result = await self.db.execute(query)
            return [row[0] for row in result.fetchall()]
        
        # Requesters and Viewers only see assigned clients
        else:
            query = select(ClientAssignment.client_id).where(
                and_(
                    ClientAssignment.user_id == user_id,
                    ClientAssignment.status == ClientAssignmentStatus.ACTIVE
                )
            )
            result = await self.db.execute(query)
            return [row[0] for row in result.fetchall()]
    
    async def check_user_client_access(
        self,
        user_id: int,
        client_id: int,
        user_role: UserRole
    ) -> bool:
        """Check if a user has access to a specific client"""
        
        # Super Admins have access to all active clients
        if user_role == UserRole.SUPER_ADMIN:
            query = select(Client).where(
                and_(Client.id == client_id, Client.is_active == True)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        
        # Admins have access to all active clients (can be customized)
        elif user_role == UserRole.ADMIN:
            query = select(Client).where(
                and_(Client.id == client_id, Client.is_active == True)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        
        # Requesters and Viewers need specific assignment
        else:
            query = select(ClientAssignment).where(
                and_(
                    ClientAssignment.user_id == user_id,
                    ClientAssignment.client_id == client_id,
                    ClientAssignment.status == ClientAssignmentStatus.ACTIVE
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
    
    async def get_access_control_summary(
        self,
        user_id: int,
        user_role: UserRole
    ) -> AccessControlSummary:
        """Get comprehensive access control summary for a user"""
        
        accessible_clients = await self.get_user_accessible_clients(user_id, user_role)
        
        # Get assignment-based access
        query = select(ClientAssignment.client_id).where(
            and_(
                ClientAssignment.user_id == user_id,
                ClientAssignment.status == ClientAssignmentStatus.ACTIVE
            )
        )
        result = await self.db.execute(query)
        assignment_based = [row[0] for row in result.fetchall()]
        
        return AccessControlSummary(
            user_id=user_id,
            accessible_client_ids=accessible_clients,
            role_based_access=user_role in [UserRole.SUPER_ADMIN, UserRole.ADMIN],
            assignment_based_access=assignment_based
        )
    
    # Private helper methods
    
    async def _get_user_by_id(self, user_id: int) -> User:
        """Get user by ID or raise NotFoundError"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        return user
    
    async def _get_client_by_id(self, client_id: int) -> Client:
        """Get client by ID or raise NotFoundError"""
        query = select(Client).where(Client.id == client_id)
        result = await self.db.execute(query)
        client = result.scalar_one_or_none()
        if not client:
            raise NotFoundError(f"Client with ID {client_id} not found")
        return client
    
    async def _get_users_by_ids(self, user_ids: List[int]) -> List[User]:
        """Get multiple users by IDs"""
        query = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _get_clients_by_ids(self, client_ids: List[int]) -> List[Client]:
        """Get multiple clients by IDs"""
        query = select(Client).where(Client.id.in_(client_ids))
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _get_assignment_by_id(self, assignment_id: int) -> ClientAssignment:
        """Get assignment by ID or raise NotFoundError"""
        query = select(ClientAssignment).where(ClientAssignment.id == assignment_id)
        result = await self.db.execute(query)
        assignment = result.scalar_one_or_none()
        if not assignment:
            raise NotFoundError(f"Client assignment with ID {assignment_id} not found")
        return assignment
    
    async def _get_existing_assignment(
        self,
        user_id: int,
        client_id: int
    ) -> Optional[ClientAssignment]:
        """Check if assignment already exists"""
        query = select(ClientAssignment).where(
            and_(
                ClientAssignment.user_id == user_id,
                ClientAssignment.client_id == client_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_existing_assignments_bulk(
        self,
        user_ids: List[int],
        client_ids: List[int]
    ) -> set:
        """Get existing assignments for bulk operations"""
        query = select(ClientAssignment.user_id, ClientAssignment.client_id).where(
            and_(
                ClientAssignment.user_id.in_(user_ids),
                ClientAssignment.client_id.in_(client_ids)
            )
        )
        result = await self.db.execute(query)
        return {(user_id, client_id) for user_id, client_id in result.fetchall()}
    
    async def _load_assignment_relationships(self, assignment: ClientAssignment) -> None:
        """Load user, client, and assigned_by relationships"""
        await self.db.refresh(
            assignment,
            ["user", "client", "assigned_by"]
        )
    
    async def _create_audit_log(
        self,
        action: str,
        actor_id: int,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[str] = None
    ) -> None:
        """Create an audit log entry"""
        audit_log = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        self.db.add(audit_log)
        # Note: Don't commit here, let the calling method handle it