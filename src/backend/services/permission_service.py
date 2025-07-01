"""
권한 관리 서비스
==============

권한 신청, 승인, 만료 관리 등의 비즈니스 로직을 담당
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status

from src.backend.core.database import get_db, DatabaseService
from src.backend.services.ga4_service import get_ga4_service, GA4Service
from src.backend.models.permission_models import (
    PermissionLevel, PermissionStatus, PermissionRequest,
    PermissionRequestResponse, PermissionApprovalRequest,
    PermissionExtensionRequest, ExpiringPermission
)

logger = logging.getLogger(__name__)


class PermissionService:
    """권한 관리 서비스 클래스"""
    
    def __init__(self):
        """PermissionService 초기화"""
        self.db = get_db()
        self.ga4_service = get_ga4_service()
        logger.info("✅ PermissionService 초기화 완료")
    
    async def submit_permission_request(
        self, 
        user_id: int, 
        request: PermissionRequest
    ) -> PermissionRequestResponse:
        """
        권한 신청 제출
        
        Args:
            user_id: 신청자 사용자 ID
            request: 권한 신청 정보
            
        Returns:
            PermissionRequestResponse: 생성된 권한 신청 정보
        """
        try:
            # 1. 사용자 정보 조회
            user_data = await self._get_user_info(user_id)
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다"
                )
            
            # 2. 중복 신청 확인 (같은 속성에 대한 활성/대기 중인 신청)
            existing_request = await self._check_existing_request(
                user_id, request.property_id
            )
            if existing_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="해당 속성에 대해 이미 활성화되었거나 승인 대기 중인 신청이 있습니다"
                )
            
            # 3. 권한 신청 데이터베이스 저장
            grant_data = {
                "user_id": user_id,
                "property_id": request.property_id,
                "permission_level": request.permission_level.value,
                "requested_duration_days": request.requested_duration_days,
                "justification": request.justification,
                "status": PermissionStatus.PENDING.value,
                "requested_at": datetime.utcnow(),
                "client_id": user_data.get("client_id")  # 사용자의 고객사 ID
            }
            
            grant_id = await self._create_permission_grant(grant_data)
            
            # 4. 자동 승인 가능 여부 확인 및 처리
            if self._is_auto_approvable(request.permission_level):
                await self._auto_approve_request(grant_id, request)
                final_status = PermissionStatus.ACTIVE
                approved_at = datetime.utcnow()
                expires_at = approved_at + timedelta(days=request.requested_duration_days)
            else:
                final_status = PermissionStatus.PENDING
                approved_at = None
                expires_at = None
            
            # 5. 응답 데이터 구성
            response = PermissionRequestResponse(
                grant_id=grant_id,
                user_id=user_id,
                user_email=user_data["email"],
                user_name=user_data["user_name"],
                property_id=request.property_id,
                permission_level=request.permission_level,
                requested_duration_days=request.requested_duration_days,
                justification=request.justification,
                status=final_status,
                requested_at=grant_data["requested_at"],
                approved_at=approved_at,
                expires_at=expires_at
            )
            
            logger.info(f"✅ 권한 신청 완료 - Grant ID: {grant_id}, 상태: {final_status}")
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"권한 신청 처리 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="권한 신청 처리 중 오류가 발생했습니다"
            )
    
    async def approve_permission_request(
        self, 
        approval: PermissionApprovalRequest, 
        admin_user_id: int
    ) -> Dict[str, Any]:
        """
        권한 신청 승인/거부 처리
        
        Args:
            approval: 승인/거부 요청 정보
            admin_user_id: 승인 처리하는 관리자 사용자 ID
            
        Returns:
            Dict: 처리 결과
        """
        try:
            # 1. 권한 신청 정보 조회
            grant_info = await self._get_permission_grant(approval.grant_id)
            if not grant_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="권한 신청을 찾을 수 없습니다"
                )
            
            if grant_info["status"] != PermissionStatus.PENDING.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="승인 대기 중인 신청만 처리할 수 있습니다"
                )
            
            current_time = datetime.utcnow()
            
            if approval.action == "approve":
                # 승인 처리
                duration_days = approval.custom_duration_days or grant_info["requested_duration_days"]
                expires_at = current_time + timedelta(days=duration_days)
                
                # GA4에 권한 부여
                success = await self._grant_ga4_permission(
                    grant_info["property_id"],
                    grant_info["user_email"],
                    grant_info["permission_level"]
                )
                
                if success:
                    # 데이터베이스 업데이트
                    await self._update_permission_grant(approval.grant_id, {
                        "status": PermissionStatus.ACTIVE.value,
                        "approved_at": current_time,
                        "expires_at": expires_at,
                        "admin_notes": approval.admin_notes,
                        "approved_by": admin_user_id
                    })
                    
                    logger.info(f"✅ 권한 신청 승인 완료 - Grant ID: {approval.grant_id}")
                    return {
                        "success": True,
                        "message": f"권한 신청 {approval.grant_id}이 승인되었습니다",
                        "grant_id": approval.grant_id,
                        "expires_at": expires_at.isoformat()
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="GA4 권한 부여에 실패했습니다"
                    )
                    
            elif approval.action == "reject":
                # 거부 처리
                await self._update_permission_grant(approval.grant_id, {
                    "status": PermissionStatus.REJECTED.value,
                    "rejected_at": current_time,
                    "rejected_reason": approval.admin_notes,
                    "rejected_by": admin_user_id
                })
                
                logger.info(f"✅ 권한 신청 거부 완료 - Grant ID: {approval.grant_id}")
                return {
                    "success": True,
                    "message": f"권한 신청 {approval.grant_id}이 거부되었습니다",
                    "grant_id": approval.grant_id,
                    "reason": approval.admin_notes
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"권한 승인 처리 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="권한 승인 처리 중 오류가 발생했습니다"
            )
    
    async def get_pending_requests(self, skip: int = 0, limit: int = 100) -> List[PermissionRequestResponse]:
        """승인 대기 중인 권한 신청 목록 조회"""
        try:
            response = self.db.client.table("permission_grants").select("""
                *,
                website_users!inner (
                    email,
                    user_name
                )
            """).eq("status", "pending").range(skip, skip + limit - 1).execute()
            
            results = []
            for grant_data in response.data:
                # 사용자 정보 평면화
                user_info = grant_data["website_users"]
                
                # datetime 문자열을 파싱
                requested_at = datetime.fromisoformat(grant_data["requested_at"].replace("Z", "+00:00"))
                
                request_response = PermissionRequestResponse(
                    grant_id=grant_data["grant_id"],
                    user_id=grant_data["user_id"],
                    user_email=user_info["email"],
                    user_name=user_info["user_name"],
                    property_id=grant_data["property_id"],
                    permission_level=PermissionLevel(grant_data["permission_level"]),
                    requested_duration_days=grant_data["requested_duration_days"],
                    justification=grant_data["justification"],
                    status=PermissionStatus(grant_data["status"]),
                    requested_at=requested_at,
                    approved_at=None,
                    expires_at=None,
                    admin_notes=grant_data.get("admin_notes"),
                    rejected_reason=grant_data.get("rejected_reason")
                )
                results.append(request_response)
            
            return results
            
        except Exception as e:
            logger.error(f"승인 대기 목록 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="승인 대기 목록 조회 중 오류가 발생했습니다"
            )
    
    async def get_expiring_permissions(self, days: int = 30) -> List[ExpiringPermission]:
        """만료 예정 권한 목록 조회"""
        try:
            # 현재 시간부터 지정된 일수 이내에 만료 예정인 권한 조회
            expiry_threshold = (datetime.utcnow() + timedelta(days=days)).isoformat()
            
            response = self.db.client.table("permission_grants").select("""
                *,
                website_users!inner (
                    email,
                    user_name
                )
            """).eq("status", "active").lte("expires_at", expiry_threshold).execute()
            
            results = []
            for grant_data in response.data:
                user_info = grant_data["website_users"]
                expires_at = datetime.fromisoformat(grant_data["expires_at"].replace("Z", "+00:00"))
                days_until_expiry = (expires_at - datetime.utcnow()).days
                
                expiring_permission = ExpiringPermission(
                    grant_id=grant_data["grant_id"],
                    user_email=user_info["email"],
                    user_name=user_info["user_name"],
                    property_id=grant_data["property_id"],
                    permission_level=PermissionLevel(grant_data["permission_level"]),
                    expires_at=expires_at,
                    days_until_expiry=max(0, days_until_expiry)  # 음수가 되지 않도록
                )
                results.append(expiring_permission)
            
            return results
            
        except Exception as e:
            logger.error(f"만료 예정 권한 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="만료 예정 권한 조회 중 오류가 발생했습니다"
            )
    
    async def get_permission_stats(self) -> Dict[str, Any]:
        """권한 통계 정보 조회"""
        try:
            # 전체 권한 수
            total_response = self.db.client.table("permission_grants").select("grant_id", count="exact").execute()
            
            # 활성 권한 수
            active_response = self.db.client.table("permission_grants").select("grant_id", count="exact").eq("status", "active").execute()
            
            # 승인 대기 권한 수
            pending_response = self.db.client.table("permission_grants").select("grant_id", count="exact").eq("status", "pending").execute()
            
            # 만료 예정 권한 수 (30일 이내)
            expiry_threshold = (datetime.utcnow() + timedelta(days=30)).isoformat()
            expiring_response = self.db.client.table("permission_grants").select("grant_id", count="exact").eq("status", "active").lte("expires_at", expiry_threshold).execute()
            
            # 권한 수준별 통계
            level_stats = {}
            for level in ["viewer", "analyst", "editor", "administrator"]:
                level_response = self.db.client.table("permission_grants").select("grant_id", count="exact").eq("permission_level", level).execute()
                level_stats[level] = level_response.count
            
            # 상태별 통계
            status_stats = {}
            for status_name in ["pending", "active", "rejected", "expired", "revoked"]:
                status_response = self.db.client.table("permission_grants").select("grant_id", count="exact").eq("status", status_name).execute()
                status_stats[status_name] = status_response.count
            
            return {
                "total_active": active_response.count,
                "pending_approvals": pending_response.count,
                "expiring_soon": expiring_response.count,
                "by_permission_level": level_stats,
                "by_status": status_stats
            }
            
        except Exception as e:
            logger.error(f"권한 통계 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="권한 통계 조회 중 오류가 발생했습니다"
            )

    async def get_active_permissions(
        self, 
        user_id: Optional[int] = None, 
        property_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[PermissionRequestResponse]:
        """활성 권한 목록 조회"""
        try:
            query = self.db.client.table("permission_grants").select("""
                *,
                website_users!inner (
                    email,
                    user_name
                )
            """).eq("status", "active")
            
            # 필터 조건 적용
            if user_id:
                query = query.eq("user_id", user_id)
            if property_id:
                query = query.eq("property_id", property_id)
            
            response = query.range(skip, skip + limit - 1).execute()
            
            results = []
            for grant_data in response.data:
                user_info = grant_data["website_users"]
                
                # datetime 문자열 파싱
                requested_at = datetime.fromisoformat(grant_data["requested_at"].replace("Z", "+00:00"))
                approved_at = None
                expires_at = None
                
                if grant_data.get("approved_at"):
                    approved_at = datetime.fromisoformat(grant_data["approved_at"].replace("Z", "+00:00"))
                if grant_data.get("expires_at"):
                    expires_at = datetime.fromisoformat(grant_data["expires_at"].replace("Z", "+00:00"))
                
                request_response = PermissionRequestResponse(
                    grant_id=grant_data["grant_id"],
                    user_id=grant_data["user_id"],
                    user_email=user_info["email"],
                    user_name=user_info["user_name"],
                    property_id=grant_data["property_id"],
                    permission_level=PermissionLevel(grant_data["permission_level"]),
                    requested_duration_days=grant_data["requested_duration_days"],
                    justification=grant_data["justification"],
                    status=PermissionStatus(grant_data["status"]),
                    requested_at=requested_at,
                    approved_at=approved_at,
                    expires_at=expires_at,
                    admin_notes=grant_data.get("admin_notes"),
                    rejected_reason=grant_data.get("rejected_reason")
                )
                results.append(request_response)
            
            return results
            
        except Exception as e:
            logger.error(f"활성 권한 목록 조회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="활성 권한 목록 조회 중 오류가 발생했습니다"
            )

    async def revoke_permission(self, grant_id: int, reason: Optional[str] = None, admin_user_id: int = None) -> Dict[str, Any]:
        """권한 철회"""
        try:
            # 권한 정보 조회
            grant_info = await self._get_permission_grant(grant_id)
            if not grant_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="권한을 찾을 수 없습니다"
                )
            
            if grant_info["status"] != PermissionStatus.ACTIVE.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="활성 상태인 권한만 철회할 수 있습니다"
                )
            
            # GA4에서 권한 제거
            success = await self._revoke_ga4_permission(
                grant_info["property_id"],
                grant_info["user_email"],
                grant_info["permission_level"]
            )
            
            current_time = datetime.utcnow()
            
            if success:
                # 데이터베이스 업데이트
                await self._update_permission_grant(grant_id, {
                    "status": PermissionStatus.REVOKED.value,
                    "revoked_at": current_time,
                    "revoked_reason": reason,
                    "revoked_by": admin_user_id
                })
                
                logger.info(f"✅ 권한 철회 완료 - Grant ID: {grant_id}")
                return {
                    "success": True,
                    "message": f"권한 {grant_id}이 철회되었습니다",
                    "grant_id": grant_id,
                    "revoked_at": current_time.isoformat(),
                    "reason": reason
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GA4 권한 제거에 실패했습니다"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"권한 철회 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="권한 철회 처리 중 오류가 발생했습니다"
            )

    # Private helper methods
    
    async def _get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 정보 조회"""
        try:
            response = self.db.client.table("website_users").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"사용자 정보 조회 실패: {e}")
            return None
    
    async def _check_existing_request(self, user_id: int, property_id: str) -> bool:
        """중복 신청 확인"""
        try:
            response = self.db.client.table("permission_grants").select("grant_id").eq("user_id", user_id).eq("property_id", property_id).in_("status", ["pending", "active"]).execute()
            
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"중복 신청 확인 실패: {e}")
            return False
    
    async def _create_permission_grant(self, grant_data: Dict[str, Any]) -> int:
        """권한 신청 데이터베이스 저장"""
        try:
            # Supabase에서 datetime을 ISO 문자열로 변환
            if "requested_at" in grant_data:
                grant_data["requested_at"] = grant_data["requested_at"].isoformat()
            
            response = self.db.client.table("permission_grants").insert(grant_data).execute()
            
            if response.data:
                return response.data[0]["grant_id"]
            else:
                raise Exception("권한 신청 저장 실패")
        except Exception as e:
            logger.error(f"권한 신청 저장 실패: {e}")
            raise
    
    def _is_auto_approvable(self, permission_level: PermissionLevel) -> bool:
        """자동 승인 가능 여부 확인"""
        return permission_level in [PermissionLevel.VIEWER, PermissionLevel.ANALYST]
    
    async def _auto_approve_request(self, grant_id: int, request: PermissionRequest):
        """자동 승인 처리"""
        try:
            current_time = datetime.utcnow()
            expires_at = current_time + timedelta(days=request.requested_duration_days)
            
            # 권한 정보 조회 (사용자 정보 포함)
            grant_info = await self._get_permission_grant(grant_id)
            if not grant_info:
                logger.error(f"자동 승인 실패: 권한 신청 {grant_id}을 찾을 수 없음")
                return
            
            # GA4에 권한 부여
            success = await self._grant_ga4_permission(
                request.property_id,
                grant_info["user_email"],
                request.permission_level.value
            )
            
            if success:
                # 데이터베이스 업데이트
                await self._update_permission_grant(grant_id, {
                    "status": PermissionStatus.ACTIVE.value,
                    "approved_at": current_time,
                    "expires_at": expires_at,
                    "admin_notes": "자동 승인됨"
                })
                logger.info(f"✅ 자동 승인 완료 - Grant ID: {grant_id}, 권한: {request.permission_level.value}")
            else:
                logger.error(f"GA4 권한 부여 실패 - Grant ID: {grant_id}")
                # 실패 시 상태를 rejected로 변경
                await self._update_permission_grant(grant_id, {
                    "status": PermissionStatus.REJECTED.value,
                    "rejected_at": current_time,
                    "rejected_reason": "GA4 권한 부여 실패"
                })
                
        except Exception as e:
            logger.error(f"자동 승인 처리 실패: {e}")
            raise
    
    async def _grant_ga4_permission(self, property_id: str, email: str, role: str) -> bool:
        """GA4에 권한 부여"""
        try:
            success, message, _ = await self.ga4_service.register_user_to_property(
                property_id=property_id,
                email=email,
                role=role
            )
            if success:
                logger.info(f"GA4 권한 부여 성공: {email} -> {property_id} ({role})")
            else:
                logger.error(f"GA4 권한 부여 실패: {message}")
            return success
        except Exception as e:
            logger.error(f"GA4 권한 부여 오류: {e}")
            return False
    
    async def _get_permission_grant(self, grant_id: int) -> Optional[Dict[str, Any]]:
        """권한 신청 정보 조회"""
        try:
            # permission_grants와 website_users를 조인해서 정보 조회
            response = self.db.client.table("permission_grants").select("""
                *,
                website_users!inner (
                    email,
                    user_name
                )
            """).eq("grant_id", grant_id).execute()
            
            if response.data:
                grant_data = response.data[0]
                # 중첩된 사용자 정보를 평면화
                if "website_users" in grant_data:
                    user_info = grant_data["website_users"]
                    grant_data["user_email"] = user_info["email"]
                    grant_data["user_name"] = user_info["user_name"]
                    del grant_data["website_users"]
                
                return grant_data
            return None
        except Exception as e:
            logger.error(f"권한 신청 정보 조회 실패: {e}")
            return None
    
    async def _update_permission_grant(self, grant_id: int, update_data: Dict[str, Any]):
        """권한 신청 정보 업데이트"""
        try:
            # datetime 객체들을 ISO 문자열로 변환
            for key, value in update_data.items():
                if isinstance(value, datetime):
                    update_data[key] = value.isoformat()
            
            response = self.db.client.table("permission_grants").update(update_data).eq("grant_id", grant_id).execute()
            
            if not response.data:
                raise Exception(f"권한 신청 {grant_id} 업데이트 실패")
                
        except Exception as e:
            logger.error(f"권한 신청 업데이트 실패: {e}")
            raise

    async def _revoke_ga4_permission(self, property_id: str, email: str, role: str) -> bool:
        """GA4에서 권한 제거"""
        try:
            success, message, _ = await self.ga4_service.remove_user_from_property(
                property_id=property_id,
                email=email
            )
            if success:
                logger.info(f"GA4 권한 제거 성공: {email} -> {property_id}")
            else:
                logger.error(f"GA4 권한 제거 실패: {message}")
            return success
        except Exception as e:
            logger.error(f"GA4 권한 제거 오류: {e}")
            return False


# 전역 권한 서비스 인스턴스
_permission_service = None

def get_permission_service() -> PermissionService:
    """권한 서비스 싱글톤 인스턴스 반환"""
    global _permission_service
    if _permission_service is None:
        _permission_service = PermissionService()
    return _permission_service 