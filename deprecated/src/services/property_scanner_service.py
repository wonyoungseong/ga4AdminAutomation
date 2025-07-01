#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 Property Scanner Service
============================

GA4 계정과 프로퍼티를 스캔하고 데이터베이스를 업데이트하는 서비스입니다.
"""

from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import ListAccountsRequest, ListPropertiesRequest
from google.oauth2 import service_account

from ..domain.entities import GA4Account, GA4Property, AuditLog
from ..infrastructure.database import db_manager
from ..core.logger import get_ga4_logger


@dataclass
class ScanResult:
    """스캔 결과"""
    accounts_found: int
    accounts_new: int
    accounts_updated: int
    properties_found: int
    properties_new: int
    properties_updated: int
    scan_duration: float
    errors: List[str]


class GA4PropertyScannerService:
    """GA4 프로퍼티 스캔 서비스"""
    
    def __init__(self):
        self.logger = get_ga4_logger()
        self.client = self._init_ga4_client()
    
    async def initialize(self):
        """비동기 초기화 (호환성을 위한 메서드)"""
        # 이미 __init__에서 초기화가 완료되므로 추가 작업 없음
        self.logger.info("✅ GA4PropertyScannerService 초기화 완료")
        return True
    
    def _init_ga4_client(self) -> AnalyticsAdminServiceClient:
        """GA4 클라이언트 초기화"""
        try:
            service_account_file = 'config/ga4-automatio-797ec352f393.json'
            scopes = [
                'https://www.googleapis.com/auth/analytics.edit',
                'https://www.googleapis.com/auth/analytics.manage.users',
                'https://www.googleapis.com/auth/analytics.readonly'
            ]
            
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=scopes
            )
            
            client = AnalyticsAdminServiceClient(credentials=credentials)
            self.logger.info("✅ GA4 클라이언트 초기화 완료")
            return client
            
        except Exception as e:
            self.logger.error(f"❌ GA4 클라이언트 초기화 실패: {e}")
            raise
    
    async def scan_all_accounts_and_properties(self) -> ScanResult:
        """모든 접근 가능한 계정과 프로퍼티 스캔"""
        start_time = datetime.now()
        errors = []
        
        self.logger.info("🔍 GA4 계정/프로퍼티 스캔 시작")
        
        try:
            # 1. 계정 스캔
            accounts_result = await self._scan_accounts()
            
            # 2. 프로퍼티 스캔
            properties_result = await self._scan_properties()
            
            # 3. 스캔 결과 생성
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            result = ScanResult(
                accounts_found=accounts_result['found'],
                accounts_new=accounts_result['new'],
                accounts_updated=accounts_result['updated'],
                properties_found=properties_result['found'],
                properties_new=properties_result['new'],
                properties_updated=properties_result['updated'],
                scan_duration=scan_duration,
                errors=errors
            )
            
            # 4. 감사 로그 기록
            await self._log_scan_result(result)
            
            self.logger.info(f"✅ 스캔 완료 - 계정: {result.accounts_found}개, 프로퍼티: {result.properties_found}개")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 스캔 실패: {e}")
            errors.append(str(e))
            
            # 실패 감사 로그
            await self._log_audit(
                "SCAN_FAILED", "SYSTEM", "ALL", 
                f"전체 스캔 실패: {e}", False, str(e)
            )
            
            raise
    
    async def _scan_accounts(self) -> Dict[str, int]:
        """GA4 계정 스캔"""
        found = new = updated = 0
        
        try:
            # GA4 API로 계정 목록 조회
            request = ListAccountsRequest()
            accounts_page = self.client.list_accounts(request=request)
            
            for account in accounts_page:
                found += 1
                account_id = account.name.split('/')[-1]  # accounts/123456 -> 123456
                
                # 기존 계정 확인
                existing = await self._get_existing_account(account_id)
                
                if existing:
                    # 기존 계정 업데이트
                    if await self._update_account(account_id, account.display_name):
                        updated += 1
                else:
                    # 새 계정 추가
                    if await self._create_account(account_id, account.display_name):
                        new += 1
            
            self.logger.info(f"📊 계정 스캔 결과 - 발견: {found}, 신규: {new}, 업데이트: {updated}")
            return {'found': found, 'new': new, 'updated': updated}
            
        except Exception as e:
            self.logger.error(f"❌ 계정 스캔 실패: {e}")
            raise
    
    async def _scan_properties(self) -> Dict[str, int]:
        """GA4 프로퍼티 스캔"""
        found = new = updated = 0
        
        try:
            # 모든 계정의 프로퍼티 스캔
            accounts = await self._get_all_accounts()
            
            for account in accounts:
                account_id = account['account_id']
                
                # 계정 ID가 숫자가 아닌 경우 스킵 (테스트 계정)
                if not account_id.isdigit():
                    self.logger.debug(f"⚠️ 테스트 계정 스킵: {account_id}")
                    continue
                
                account_name = f"accounts/{account_id}"
                
                try:
                    # 해당 계정의 프로퍼티 목록 조회
                    request = ListPropertiesRequest(filter=f"parent:{account_name}")
                    properties_page = self.client.list_properties(request=request)
                    
                    for property_obj in properties_page:
                        found += 1
                        property_id = property_obj.name.split('/')[-1]  # properties/123456 -> 123456
                        
                        # 기존 프로퍼티 확인
                        existing = await self._get_existing_property(property_id)
                        
                        if existing:
                            # 기존 프로퍼티 업데이트
                            if await self._update_property(property_id, property_obj):
                                updated += 1
                        else:
                            # 새 프로퍼티 추가
                            if await self._create_property(property_id, account['account_id'], property_obj):
                                new += 1
                
                except Exception as e:
                    self.logger.warning(f"⚠️ 계정 {account['account_id']} 프로퍼티 스캔 실패: {e}")
                    continue
            
            self.logger.info(f"📊 프로퍼티 스캔 결과 - 발견: {found}, 신규: {new}, 업데이트: {updated}")
            return {'found': found, 'new': new, 'updated': updated}
            
        except Exception as e:
            self.logger.error(f"❌ 프로퍼티 스캔 실패: {e}")
            raise
    
    async def _get_existing_account(self, account_id: str) -> Optional[Dict]:
        """기존 계정 조회"""
        result = await db_manager.execute_query(
            "SELECT * FROM ga4_accounts WHERE account_id = ?",
            (account_id,)
        )
        return result[0] if result else None
    
    async def _get_existing_property(self, property_id: str) -> Optional[Dict]:
        """기존 프로퍼티 조회"""
        result = await db_manager.execute_query(
            "SELECT * FROM ga4_properties WHERE property_id = ?",
            (property_id,)
        )
        return result[0] if result else None
    
    async def _get_all_accounts(self) -> List[Dict]:
        """모든 계정 조회"""
        return await db_manager.execute_query(
            "SELECT * FROM ga4_accounts WHERE 현재_존재여부 = TRUE"
        )
    
    async def _create_account(self, account_id: str, display_name: str) -> bool:
        """새 계정 생성"""
        try:
            now = datetime.now()
            await db_manager.execute_insert(
                """INSERT INTO ga4_accounts 
                   (account_id, account_display_name, 최초_확인일, 최근_업데이트일, 
                    삭제여부, 현재_존재여부, service_account_access)
                   VALUES (?, ?, ?, ?, FALSE, TRUE, TRUE)""",
                (account_id, display_name, now, now)
            )
            
            await self._log_audit(
                "ACCOUNT_CREATED", "ACCOUNT", account_id,
                f"새 계정 추가: {display_name}", True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 계정 생성 실패 {account_id}: {e}")
            return False
    
    async def _update_account(self, account_id: str, display_name: str) -> bool:
        """계정 정보 업데이트"""
        try:
            now = datetime.now()
            rowcount = await db_manager.execute_update(
                """UPDATE ga4_accounts 
                   SET account_display_name = ?, 최근_업데이트일 = ?, 
                       현재_존재여부 = TRUE, updated_at = ?
                   WHERE account_id = ?""",
                (display_name, now, now, account_id)
            )
            
            if rowcount > 0:
                await self._log_audit(
                    "ACCOUNT_UPDATED", "ACCOUNT", account_id,
                    f"계정 정보 업데이트: {display_name}", True
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 계정 업데이트 실패 {account_id}: {e}")
            return False
    
    async def _create_property(self, property_id: str, account_id: str, property_obj) -> bool:
        """새 프로퍼티 생성"""
        try:
            now = datetime.now()
            await db_manager.execute_insert(
                """INSERT INTO ga4_properties 
                   (property_id, account_id, property_display_name, property_type,
                    최초_확인일, 최근_업데이트일, 삭제여부, 현재_존재여부, 등록_가능여부)
                   VALUES (?, ?, ?, ?, ?, ?, FALSE, TRUE, TRUE)""",
                (property_id, account_id, property_obj.display_name, 
                 str(property_obj.property_type), now, now)
            )
            
            await self._log_audit(
                "PROPERTY_CREATED", "PROPERTY", property_id,
                f"새 프로퍼티 추가: {property_obj.display_name}", True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 프로퍼티 생성 실패 {property_id}: {e}")
            return False
    
    async def _update_property(self, property_id: str, property_obj) -> bool:
        """프로퍼티 정보 업데이트"""
        try:
            now = datetime.now()
            rowcount = await db_manager.execute_update(
                """UPDATE ga4_properties 
                   SET property_display_name = ?, property_type = ?, 최근_업데이트일 = ?,
                       현재_존재여부 = TRUE, updated_at = ?
                   WHERE property_id = ?""",
                (property_obj.display_name, str(property_obj.property_type), 
                 now, now, property_id)
            )
            
            if rowcount > 0:
                await self._log_audit(
                    "PROPERTY_UPDATED", "PROPERTY", property_id,
                    f"프로퍼티 정보 업데이트: {property_obj.display_name}", True
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 프로퍼티 업데이트 실패 {property_id}: {e}")
            return False
    
    async def get_available_properties(self) -> List[Dict]:
        """등록 가능한 프로퍼티 목록 조회"""
        return await db_manager.execute_query(
            """SELECT p.*, a.account_display_name,
                      p.최근_업데이트일 as last_updated
               FROM ga4_properties p
               JOIN ga4_accounts a ON p.account_id = a.account_id
               WHERE p.등록_가능여부 = TRUE 
               AND p.현재_존재여부 = TRUE 
               AND a.현재_존재여부 = TRUE
               ORDER BY a.account_display_name, p.property_display_name"""
        )
    
    async def check_property_accessibility(self, property_id: str) -> bool:
        """프로퍼티 접근 가능성 확인"""
        try:
            # GA4 API로 직접 접근 테스트
            property_name = f"properties/{property_id}"
            property_obj = self.client.get_property(name=property_name)
            
            # 접근 가능하면 True
            await self._log_audit(
                "PROPERTY_ACCESS_CHECK", "PROPERTY", property_id,
                "프로퍼티 접근 확인 성공", True
            )
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ 프로퍼티 {property_id} 접근 불가: {e}")
            
            await self._log_audit(
                "PROPERTY_ACCESS_CHECK", "PROPERTY", property_id,
                "프로퍼티 접근 확인 실패", False, str(e)
            )
            return False
    
    async def _log_scan_result(self, result: ScanResult) -> None:
        """스캔 결과 감사 로그"""
        details = f"계정: {result.accounts_found}개 발견, {result.accounts_new}개 신규, {result.accounts_updated}개 업데이트 | " \
                 f"프로퍼티: {result.properties_found}개 발견, {result.properties_new}개 신규, {result.properties_updated}개 업데이트 | " \
                 f"소요시간: {result.scan_duration:.2f}초"
        
        await self._log_audit(
            "SCAN_COMPLETED", "SYSTEM", "ALL",
            details, True
        )
    
    async def _log_audit(self, action_type: str, target_type: str, target_id: str,
                        action_details: str, success: bool, error_message: str = None) -> None:
        """감사 로그 기록"""
        try:
            await db_manager.execute_insert(
                """INSERT INTO audit_logs 
                   (action_type, target_type, target_id, action_details, success, error_message, performed_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (action_type, target_type, target_id, action_details, success, error_message, "SYSTEM")
            )
        except Exception as e:
            self.logger.error(f"❌ 감사 로그 기록 실패: {e}") 