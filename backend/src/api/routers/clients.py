"""
Clients API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List

from ...core.database import get_db
from ...models.schemas import ClientResponse, MessageResponse
from ...services.auth_service import AuthService

router = APIRouter()


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """List clients"""
    # TODO: Implement clients listing
    return []


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: Annotated[dict, Depends(AuthService.get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Get client by ID"""
    # TODO: Implement get client
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Client not found"
    )