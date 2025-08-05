"""
Clients API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Optional

from ...core.database import get_db
from ...core.rbac import Permission, require_permission, get_current_user_with_permissions
from ...models.schemas import ClientResponse, MessageResponse, ClientCreate, ClientUpdate
from ...services.client_service import ClientService

router = APIRouter()


@router.get("/", response_model=List[ClientResponse])
@require_permission(Permission.CLIENT_READ)
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """List clients with RBAC protection"""
    try:
        client_service = ClientService(db)
        clients = await client_service.list_clients(skip=skip, limit=limit)
        return clients
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.get("/{client_id}", response_model=ClientResponse)
@require_permission(Permission.CLIENT_READ)
async def get_client(
    client_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Get client by ID with RBAC protection"""
    try:
        client_service = ClientService(db)
        client = await client_service.get_client_by_id(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
        return client
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/", response_model=ClientResponse)
@require_permission(Permission.CLIENT_CREATE)
async def create_client(
    client_data: ClientCreate,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Create a new client (ADMIN+ only)"""
    try:
        client_service = ClientService(db)
        client = await client_service.create_client(client_data)
        return client
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.put("/{client_id}", response_model=ClientResponse)
@require_permission(Permission.CLIENT_UPDATE)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Update client information (ADMIN+ only)"""
    try:
        client_service = ClientService(db)
        client = await client_service.update_client(client_id, client_data)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client with ID {client_id} not found"
            )
        return client
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.delete("/{client_id}")
@require_permission(Permission.CLIENT_DELETE)
async def delete_client(
    client_id: int,
    current_user: dict = Depends(get_current_user_with_permissions),
    db: AsyncSession = Depends(get_db)
):
    """Delete client (SUPER_ADMIN only)"""
    try:
        client_service = ClientService(db)
        await client_service.delete_client(client_id)
        return {"message": f"Client {client_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )