"""
Google Analytics Admin API service
"""

import json
import logging
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..core.config import settings
from ..core.exceptions import GoogleAPIError
from ..models.db_models import PermissionLevel

logger = logging.getLogger(__name__)


class GoogleAnalyticsService:
    """Google Analytics Admin API service"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Analytics Admin API service"""
        try:
            if settings.GOOGLE_SERVICE_ACCOUNT_FILE:
                # Use service account credentials
                self.credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                    scopes=['https://www.googleapis.com/auth/analytics.manage.users']
                )
            else:
                logger.warning("No Google service account file configured")
                return
            
            # Build the Analytics Admin API service
            self.service = build('analyticsadmin', 'v1beta', credentials=self.credentials)
            logger.info("Google Analytics Admin API service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Analytics service: {e}")
            raise GoogleAPIError(f"Failed to initialize Google Analytics service: {e}")
    
    def _convert_permission_level(self, permission_level: PermissionLevel) -> str:
        """Convert internal permission level to GA4 permission level"""
        permission_mapping = {
            PermissionLevel.VIEWER: "predefinedRoles/analyticsViewer",
            PermissionLevel.ANALYST: "predefinedRoles/analyticsAnalyst", 
            PermissionLevel.MARKETER: "predefinedRoles/analyticsMarketer",
            PermissionLevel.EDITOR: "predefinedRoles/analyticsEditor",
            PermissionLevel.ADMINISTRATOR: "predefinedRoles/analyticsAdmin"
        }
        return permission_mapping.get(permission_level, "predefinedRoles/analyticsViewer")
    
    async def list_accounts(self) -> List[Dict[str, Any]]:
        """List all Google Analytics accounts"""
        if not self.service:
            raise GoogleAPIError("Google Analytics service not initialized")
        
        try:
            request = self.service.accounts().list()
            response = request.execute()
            
            accounts = []
            for account in response.get('accounts', []):
                accounts.append({
                    'name': account.get('name'),
                    'displayName': account.get('displayName'),
                    'regionCode': account.get('regionCode'),
                    'createTime': account.get('createTime'),
                    'updateTime': account.get('updateTime')
                })
            
            return accounts
            
        except HttpError as e:
            logger.error(f"Failed to list GA4 accounts: {e}")
            raise GoogleAPIError(f"Failed to list GA4 accounts: {e}")
    
    async def list_properties(self, account_name: str) -> List[Dict[str, Any]]:
        """List properties for a specific account"""
        if not self.service:
            raise GoogleAPIError("Google Analytics service not initialized")
        
        try:
            request = self.service.properties().list(
                filter=f"parent:{account_name}"
            )
            response = request.execute()
            
            properties = []
            for property_data in response.get('properties', []):
                properties.append({
                    'name': property_data.get('name'),
                    'displayName': property_data.get('displayName'),
                    'propertyType': property_data.get('propertyType'),
                    'createTime': property_data.get('createTime'),
                    'updateTime': property_data.get('updateTime'),
                    'industryCategory': property_data.get('industryCategory'),
                    'timeZone': property_data.get('timeZone'),
                    'currencyCode': property_data.get('currencyCode')
                })
            
            return properties
            
        except HttpError as e:
            logger.error(f"Failed to list GA4 properties: {e}")
            raise GoogleAPIError(f"Failed to list GA4 properties: {e}")
    
    async def get_property_users(self, property_name: str) -> List[Dict[str, Any]]:
        """Get users for a specific property"""
        if not self.service:
            raise GoogleAPIError("Google Analytics service not initialized")
        
        try:
            request = self.service.properties().userLinks().list(
                parent=property_name
            )
            response = request.execute()
            
            users = []
            for user_link in response.get('userLinks', []):
                users.append({
                    'name': user_link.get('name'),
                    'emailAddress': user_link.get('emailAddress'),
                    'directRoles': user_link.get('directRoles', []),
                    'directGroupMemberships': user_link.get('directGroupMemberships', [])
                })
            
            return users
            
        except HttpError as e:
            logger.error(f"Failed to get property users: {e}")
            raise GoogleAPIError(f"Failed to get property users: {e}")
    
    async def grant_property_access(
        self,
        property_name: str,
        email_address: str,
        permission_level: PermissionLevel
    ) -> Dict[str, Any]:
        """Grant access to a GA4 property"""
        if not self.service:
            raise GoogleAPIError("Google Analytics service not initialized")
        
        try:
            role = self._convert_permission_level(permission_level)
            
            user_link = {
                'emailAddress': email_address,
                'directRoles': [role]
            }
            
            request = self.service.properties().userLinks().create(
                parent=property_name,
                body=user_link
            )
            response = request.execute()
            
            logger.info(f"Granted {permission_level.value} access to {email_address} for property {property_name}")
            
            return {
                'name': response.get('name'),
                'emailAddress': response.get('emailAddress'),
                'directRoles': response.get('directRoles', []),
                'status': 'granted'
            }
            
        except HttpError as e:
            logger.error(f"Failed to grant property access: {e}")
            raise GoogleAPIError(f"Failed to grant property access: {e}")
    
    async def revoke_property_access(
        self,
        property_name: str,
        email_address: str
    ) -> bool:
        """Revoke access from a GA4 property"""
        if not self.service:
            raise GoogleAPIError("Google Analytics service not initialized")
        
        try:
            # First, get the current user links to find the specific one
            users = await self.get_property_users(property_name)
            user_link_name = None
            
            for user in users:
                if user.get('emailAddress') == email_address:
                    user_link_name = user.get('name')
                    break
            
            if not user_link_name:
                logger.warning(f"User {email_address} not found in property {property_name}")
                return False
            
            # Delete the user link
            request = self.service.properties().userLinks().delete(
                name=user_link_name
            )
            request.execute()
            
            logger.info(f"Revoked access for {email_address} from property {property_name}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to revoke property access: {e}")
            raise GoogleAPIError(f"Failed to revoke property access: {e}")
    
    async def update_property_access(
        self,
        property_name: str,
        email_address: str,
        new_permission_level: PermissionLevel
    ) -> Dict[str, Any]:
        """Update user access level for a GA4 property"""
        if not self.service:
            raise GoogleAPIError("Google Analytics service not initialized")
        
        try:
            # First, get the current user link
            users = await self.get_property_users(property_name)
            user_link_name = None
            
            for user in users:
                if user.get('emailAddress') == email_address:
                    user_link_name = user.get('name')
                    break
            
            if not user_link_name:
                # User doesn't exist, create new access
                return await self.grant_property_access(property_name, email_address, new_permission_level)
            
            # Update existing user link
            new_role = self._convert_permission_level(new_permission_level)
            
            user_link = {
                'emailAddress': email_address,
                'directRoles': [new_role]
            }
            
            request = self.service.properties().userLinks().patch(
                name=user_link_name,
                body=user_link
            )
            response = request.execute()
            
            logger.info(f"Updated {email_address} access to {new_permission_level.value} for property {property_name}")
            
            return {
                'name': response.get('name'),
                'emailAddress': response.get('emailAddress'),
                'directRoles': response.get('directRoles', []),
                'status': 'updated'
            }
            
        except HttpError as e:
            logger.error(f"Failed to update property access: {e}")
            raise GoogleAPIError(f"Failed to update property access: {e}")
    
    async def validate_property_access(self, property_name: str) -> bool:
        """Validate if the service account has access to manage the property"""
        if not self.service:
            raise GoogleAPIError("Google Analytics service not initialized")
        
        try:
            # Try to list users for the property
            await self.get_property_users(property_name)
            return True
            
        except GoogleAPIError:
            return False
        except Exception as e:
            logger.error(f"Failed to validate property access: {e}")
            return False