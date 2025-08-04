"""
GA4 API Client
==============

Google Analytics 4 Admin API를 사용한 실제 권한 관리 클라이언트
"""

import json
import logging
from typing import List, Dict, Optional, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GA4ApiClient:
    """Google Analytics 4 Admin API 클라이언트"""
    
    def __init__(self, service_account_path: str):
        """
        GA4 API 클라이언트 초기화
        
        Args:
            service_account_path: Service Account JSON 파일 경로
        """
        self.service_account_path = service_account_path
        self.credentials = None
        self.service = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Google Analytics Admin API 클라이언트 초기화"""
        try:
            # Service Account 인증 정보 로드
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=[
                    'https://www.googleapis.com/auth/analytics.readonly',
                    'https://www.googleapis.com/auth/analytics.manage.users',
                    'https://www.googleapis.com/auth/analytics.edit'
                ]
            )
            
            # Google Analytics Admin API 서비스 빌드
            self.service = build('analyticsadmin', 'v1beta', credentials=self.credentials)
            logger.info("GA4 API 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.error(f"GA4 API 클라이언트 초기화 실패: {str(e)}")
            raise
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        GA4 계정 목록 조회
        
        Returns:
            List[Dict]: GA4 계정 목록
        """
        try:
            request = self.service.accounts().list()
            response = request.execute()
            
            accounts = []
            if 'accounts' in response:
                for account in response['accounts']:
                    accounts.append({
                        'id': account.get('name', '').split('/')[-1],
                        'name': account.get('displayName', ''),
                        'resource_name': account.get('name', '')
                    })
            
            logger.info(f"GA4 계정 {len(accounts)}개 조회 완료")
            return accounts
            
        except HttpError as e:
            logger.error(f"GA4 계정 조회 실패: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"GA4 계정 조회 중 예상치 못한 오류: {str(e)}")
            return []
    
    async def get_properties(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        GA4 Property 목록 조회
        
        Args:
            account_id: 특정 계정의 Property만 조회 (optional)
        
        Returns:
            List[Dict]: GA4 Property 목록
        """
        try:
            filter_param = f"parent:accounts/{account_id}" if account_id else ""
            request = self.service.properties().list(filter=filter_param)
            response = request.execute()
            
            properties = []
            if 'properties' in response:
                for prop in response['properties']:
                    properties.append({
                        'id': prop.get('name', '').split('/')[-1],
                        'name': prop.get('displayName', ''),
                        'resource_name': prop.get('name', ''),
                        'account_id': prop.get('parent', '').split('/')[-1] if prop.get('parent') else '',
                        'create_time': prop.get('createTime', ''),
                        'currency_code': prop.get('currencyCode', ''),
                        'time_zone': prop.get('timeZone', ''),
                        'industry_category': prop.get('industryCategory', '')
                    })
            
            logger.info(f"GA4 Property {len(properties)}개 조회 완료")
            return properties
            
        except HttpError as e:
            logger.error(f"GA4 Property 조회 실패: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"GA4 Property 조회 중 예상치 못한 오류: {str(e)}")
            return []
    
    async def get_account_access_bindings(self, account_id: str) -> List[Dict[str, Any]]:
        """
        GA4 계정의 사용자 접근 권한 목록 조회
        
        Args:
            account_id: GA4 계정 ID
        
        Returns:
            List[Dict]: 사용자 접근 권한 목록
        """
        try:
            parent = f"accounts/{account_id}"
            request = self.service.accounts().accessBindings().list(parent=parent)
            response = request.execute()
            
            bindings = []
            if 'accessBindings' in response:
                for binding in response['accessBindings']:
                    bindings.append({
                        'name': binding.get('name', ''),
                        'user': binding.get('user', ''),
                        'roles': binding.get('roles', []),
                        'resource_name': binding.get('name', '')
                    })
            
            logger.info(f"GA4 계정 {account_id}의 접근 권한 {len(bindings)}개 조회 완료")
            return bindings
            
        except HttpError as e:
            logger.error(f"GA4 계정 접근 권한 조회 실패: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"GA4 계정 접근 권한 조회 중 예상치 못한 오류: {str(e)}")
            return []
    
    async def get_property_access_bindings(self, property_id: str) -> List[Dict[str, Any]]:
        """
        GA4 Property의 사용자 접근 권한 목록 조회
        
        Args:
            property_id: GA4 Property ID
        
        Returns:
            List[Dict]: 사용자 접근 권한 목록
        """
        try:
            parent = f"properties/{property_id}"
            request = self.service.properties().accessBindings().list(parent=parent)
            response = request.execute()
            
            bindings = []
            if 'accessBindings' in response:
                for binding in response['accessBindings']:
                    bindings.append({
                        'name': binding.get('name', ''),
                        'user': binding.get('user', ''),
                        'roles': binding.get('roles', []),
                        'resource_name': binding.get('name', '')
                    })
            
            logger.info(f"GA4 Property {property_id}의 접근 권한 {len(bindings)}개 조회 완료")
            return bindings
            
        except HttpError as e:
            logger.error(f"GA4 Property 접근 권한 조회 실패: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"GA4 Property 접근 권한 조회 중 예상치 못한 오류: {str(e)}")
            return []
    
    async def create_property_access_binding(
        self, 
        property_id: str, 
        user_email: str, 
        roles: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        GA4 Property에 사용자 접근 권한 부여
        
        Args:
            property_id: GA4 Property ID
            user_email: 사용자 이메일
            roles: 부여할 역할 목록 (예: ['predefinedRoles/read', 'predefinedRoles/collaborate'])
        
        Returns:
            Dict: 생성된 접근 권한 정보
        """
        try:
            parent = f"properties/{property_id}"
            access_binding = {
                'user': user_email,
                'roles': roles
            }
            
            request = self.service.properties().accessBindings().create(
                parent=parent,
                body=access_binding
            )
            response = request.execute()
            
            logger.info(f"GA4 Property {property_id}에 사용자 {user_email} 권한 부여 완료")
            return {
                'name': response.get('name', ''),
                'user': response.get('user', ''),
                'roles': response.get('roles', []),
                'resource_name': response.get('name', '')
            }
            
        except HttpError as e:
            logger.error(f"GA4 Property 권한 부여 실패: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"GA4 Property 권한 부여 중 예상치 못한 오류: {str(e)}")
            return None
    
    async def delete_property_access_binding(self, property_id: str, binding_name: str) -> bool:
        """
        GA4 Property의 사용자 접근 권한 철회
        
        Args:
            property_id: GA4 Property ID
            binding_name: 접근 권한 바인딩 이름
        
        Returns:
            bool: 성공 여부
        """
        try:
            request = self.service.properties().accessBindings().delete(name=binding_name)
            request.execute()
            
            logger.info(f"GA4 Property {property_id}의 접근 권한 {binding_name} 철회 완료")
            return True
            
        except HttpError as e:
            logger.error(f"GA4 Property 권한 철회 실패: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"GA4 Property 권한 철회 중 예상치 못한 오류: {str(e)}")
            return False
    
    async def update_property_access_binding(
        self, 
        binding_name: str, 
        roles: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        GA4 Property의 사용자 접근 권한 수정
        
        Args:
            binding_name: 접근 권한 바인딩 이름
            roles: 새로운 역할 목록
        
        Returns:
            Dict: 수정된 접근 권한 정보
        """
        try:
            access_binding = {
                'roles': roles
            }
            
            request = self.service.properties().accessBindings().patch(
                name=binding_name,
                updateMask='roles',
                body=access_binding
            )
            response = request.execute()
            
            logger.info(f"GA4 Property 접근 권한 {binding_name} 수정 완료")
            return {
                'name': response.get('name', ''),
                'user': response.get('user', ''),
                'roles': response.get('roles', []),
                'resource_name': response.get('name', '')
            }
            
        except HttpError as e:
            logger.error(f"GA4 Property 권한 수정 실패: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"GA4 Property 권한 수정 중 예상치 못한 오류: {str(e)}")
            return None

# GA4 역할 매핑
GA4_ROLES = {
    'viewer': ['predefinedRoles/read'],
    'analyst': ['predefinedRoles/read'],
    'marketer': ['predefinedRoles/collaborate'],
    'editor': ['predefinedRoles/edit'],
    'administrator': ['predefinedRoles/admin']
}

def map_permission_to_ga4_roles(permission_type: str) -> List[str]:
    """
    권한 타입을 GA4 역할로 매핑
    
    Args:
        permission_type: 권한 타입 (viewer, analyst, marketer, editor, administrator)
    
    Returns:
        List[str]: GA4 역할 목록
    """
    return GA4_ROLES.get(permission_type.lower(), ['predefinedRoles/read'])