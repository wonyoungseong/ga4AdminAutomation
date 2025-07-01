#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 완전 자동화 시스템 (Property 레벨)
====================================

Property 레벨에서 작동하는 완전 자동화 시스템입니다.
이제 API만으로 사용자 권한 관리가 가능합니다!
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, CreateAccessBindingRequest
from google.oauth2 import service_account

from .interfaces import IAnalyticsClient, IDatabase, ILogger, IConfigManager
from .logger import get_ga4_logger

class GA4AutomationSystem:
    """GA4 완전 자동화 시스템 (의존성 주입 적용)"""
    
    def __init__(self, 
                 db_name: str = "working_ga4_automation.db",
                 analytics_client: Optional[IAnalyticsClient] = None,
                 config_manager: Optional[IConfigManager] = None,
                 logger: Optional[ILogger] = None):
        """
        의존성 주입을 통한 초기화
        
        Args:
            db_name: 데이터베이스 파일명
            analytics_client: Analytics 클라이언트 (주입 가능)
            config_manager: 설정 관리자 (주입 가능)
            logger: 로거 (주입 가능)
        """
        self.db_name = db_name
        self.config = self._load_config() if config_manager is None else config_manager
        self.logger = get_ga4_logger() if logger is None else logger
        self.client = self._init_client() if analytics_client is None else analytics_client
        self._init_database()
    
    async def initialize(self):
        """비동기 초기화 (호환성을 위한 메서드)"""
        # 이미 __init__에서 초기화가 완료되므로 추가 작업 없음
        self.logger.info("✅ GA4AutomationSystem 초기화 완료")
        return True
    
    def _load_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    

    
    def _init_client(self):
        """Service Account 클라이언트 초기화"""
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
        self.logger.info("✅ Service Account 클라이언트 초기화 완료")
        return client
    
    def _init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                binding_id TEXT,
                added_date TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT,
                timestamp TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("✅ 데이터베이스 초기화 완료")
    
    def add_user(self, email: str, role: str = "analyst") -> bool:
        """사용자 추가 (Property 레벨)"""
        
        self.logger.info(f"🔄 사용자 추가 시작: {email} ({role})")
        
        # Property 경로 (성공하는 방식)
        parent = f"properties/{self.config['property_id']}"
        
        # 역할 매핑
        role_mapping = {
            'analyst': 'predefinedRoles/analyst',
            'editor': 'predefinedRoles/editor', 
            'admin': 'predefinedRoles/admin',
            'viewer': 'predefinedRoles/viewer'
        }
        
        predefined_role = role_mapping.get(role.lower(), 'predefinedRoles/analyst')
        
        try:
            # AccessBinding 생성 (성공하는 방식)
            access_binding = AccessBinding(
                user=email,  # users/ 접두사 없이
                roles=[predefined_role]
            )
            
            # CreateAccessBindingRequest 생성
            request = CreateAccessBindingRequest(
                parent=parent,
                access_binding=access_binding
            )
            
            # API 호출
            response = self.client.create_access_binding(request=request)
            
            # 데이터베이스에 기록
            self._record_user_to_db(email, role, response.name)
            self._record_operation("add_user", email, role, True, f"Binding ID: {response.name}")
            
            self.logger.info(f"✅ 사용자 추가 성공: {email}")
            self.logger.info(f"   - 바인딩 ID: {response.name}")
            self.logger.info(f"   - 권한: {predefined_role}")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            self._record_operation("add_user", email, role, False, error_msg)
            
            self.logger.error(f"❌ 사용자 추가 실패: {email}")
            self.logger.error(f"   - 오류: {error_msg}")
            
            # 에러 분석
            if "409" in error_msg or "ALREADY_EXISTS" in error_msg:
                self.logger.info("💡 이미 존재하는 사용자입니다. 권한 업데이트를 시도합니다.")
                return self.update_user_role(email, role)
            
            return False
    
    def remove_user(self, email: str) -> bool:
        """사용자 제거"""
        
        self.logger.info(f"🔄 사용자 제거 시작: {email}")
        
        try:
            # 데이터베이스에서 바인딩 ID 조회
            binding_id = self._get_user_binding_id(email)
            
            if not binding_id:
                # 실시간으로 바인딩 ID 찾기
                binding_id = self._find_user_binding_id(email)
                
                if not binding_id:
                    self.logger.error(f"❌ 사용자를 찾을 수 없음: {email}")
                    self._record_operation("remove_user", email, None, False, "User not found")
                    return False
            
            # 바인딩 삭제
            self.client.delete_access_binding(name=binding_id)
            
            # 데이터베이스 업데이트
            self._update_user_status(email, "removed")
            self._record_operation("remove_user", email, None, True, f"Removed binding: {binding_id}")
            
            self.logger.info(f"✅ 사용자 제거 성공: {email}")
            self.logger.info(f"   - 삭제된 바인딩: {binding_id}")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            self._record_operation("remove_user", email, None, False, error_msg)
            
            self.logger.error(f"❌ 사용자 제거 실패: {email}")
            self.logger.error(f"   - 오류: {error_msg}")
            
            return False
    
    def update_user_role(self, email: str, new_role: str) -> bool:
        """사용자 권한 업데이트"""
        
        self.logger.info(f"🔄 권한 업데이트 시작: {email} → {new_role}")
        
        # 기존 사용자 제거 후 새 권한으로 추가
        if self.remove_user(email):
            if self.add_user(email, new_role):
                self.logger.info(f"✅ 권한 업데이트 성공: {email} → {new_role}")
                return True
        
        self.logger.error(f"❌ 권한 업데이트 실패: {email}")
        return False
    
    def list_users(self) -> List[Dict]:
        """현재 사용자 목록 조회"""
        
        self.logger.info("👥 사용자 목록 조회")
        
        parent = f"properties/{self.config['property_id']}"
        users = []
        
        try:
            response = self.client.list_access_bindings(parent=parent)
            
            for binding in response:
                user_info = {
                    'email': binding.user,
                    'roles': list(binding.roles),
                    'binding_id': binding.name
                }
                users.append(user_info)
                
                self.logger.info(f"   - {binding.user}: {', '.join(binding.roles)}")
            
            self.logger.info(f"📊 총 {len(users)}명의 사용자")
            return users
            
        except Exception as e:
            self.logger.error(f"❌ 사용자 목록 조회 실패: {e}")
            return []
    
    def batch_add_users(self, user_list: List[Dict]) -> Dict:
        """일괄 사용자 추가"""
        
        self.logger.info(f"🔄 일괄 사용자 추가 시작: {len(user_list)}명")
        
        results = {
            'success': [],
            'failed': [],
            'total': len(user_list)
        }
        
        for user_info in user_list:
            email = user_info['email']
            role = user_info.get('role', 'analyst')
            
            if self.add_user(email, role):
                results['success'].append(email)
            else:
                results['failed'].append(email)
        
        self.logger.info(f"📊 일괄 추가 완료:")
        self.logger.info(f"   - 성공: {len(results['success'])}명")
        self.logger.info(f"   - 실패: {len(results['failed'])}명")
        
        return results
    
    def get_user_history(self, email: str) -> List[Dict]:
        """사용자 작업 이력 조회"""
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT operation_type, role, timestamp, success, details
            FROM operations
            WHERE email = ?
            ORDER BY timestamp DESC
        ''', (email,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'operation': row[0],
                'role': row[1],
                'timestamp': row[2],
                'success': bool(row[3]),
                'details': row[4]
            })
        
        conn.close()
        return history
    
    def _record_user_to_db(self, email: str, role: str, binding_id: str):
        """데이터베이스에 사용자 기록"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (email, role, binding_id, added_date, status)
            VALUES (?, ?, ?, ?, 'active')
        ''', (email, role, binding_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def _record_operation(self, operation_type: str, email: str, role: str, success: bool, details: str):
        """작업 이력 기록"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO operations (operation_type, email, role, timestamp, success, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (operation_type, email, role, datetime.now().isoformat(), success, details))
        
        conn.commit()
        conn.close()
    
    def _get_user_binding_id(self, email: str) -> Optional[str]:
        """데이터베이스에서 바인딩 ID 조회"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT binding_id FROM users WHERE email = ? AND status = 'active'
        ''', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def _find_user_binding_id(self, email: str) -> Optional[str]:
        """실시간으로 사용자 바인딩 ID 찾기"""
        parent = f"properties/{self.config['property_id']}"
        
        try:
            if self.client is None:
                self.logger.error("클라이언트가 초기화되지 않았습니다")
                return None
                
            response = self.client.list_access_bindings(parent=parent)
            
            for binding in response:
                if binding.user == email:
                    return binding.name
            
            return None
            
        except Exception as e:
            self.logger.error(f"바인딩 ID 검색 실패: {e}")
            return None
    
    def _update_user_status(self, email: str, status: str):
        """사용자 상태 업데이트"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET status = ? WHERE email = ?
        ''', (status, email))
        
        conn.commit()
        conn.close()

def interactive_menu():
    """대화형 메뉴"""
    
    system = GA4AutomationSystem()
    
    while True:
        print("\n" + "="*60)
        print("🚀 GA4 완전 자동화 시스템 (Property 레벨)")
        print("="*60)
        print("1. 사용자 추가")
        print("2. 사용자 제거")
        print("3. 권한 변경")
        print("4. 사용자 목록 조회")
        print("5. 일괄 사용자 추가")
        print("6. 사용자 이력 조회")
        print("7. 종료")
        print("="*60)
        
        choice = input("선택하세요 (1-7): ").strip()
        
        if choice == '1':
            email = input("이메일 주소: ").strip()
            role = input("권한 (analyst/editor/admin/viewer) [analyst]: ").strip() or "analyst"
            
            if system.add_user(email, role):
                print(f"✅ {email} 사용자 추가 완료!")
            else:
                print(f"❌ {email} 사용자 추가 실패!")
        
        elif choice == '2':
            email = input("제거할 이메일 주소: ").strip()
            
            if system.remove_user(email):
                print(f"✅ {email} 사용자 제거 완료!")
            else:
                print(f"❌ {email} 사용자 제거 실패!")
        
        elif choice == '3':
            email = input("이메일 주소: ").strip()
            new_role = input("새 권한 (analyst/editor/admin/viewer): ").strip()
            
            if system.update_user_role(email, new_role):
                print(f"✅ {email} 권한 변경 완료!")
            else:
                print(f"❌ {email} 권한 변경 실패!")
        
        elif choice == '4':
            users = system.list_users()
            if users:
                print(f"\n👥 현재 사용자 목록 ({len(users)}명):")
                for i, user in enumerate(users, 1):
                    print(f"   {i}. {user['email']}")
                    print(f"      권한: {', '.join(user['roles'])}")
            else:
                print("사용자가 없습니다.")
        
        elif choice == '5':
            print("일괄 사용자 추가 (이메일:권한 형식, 빈 줄로 종료)")
            user_list = []
            
            while True:
                line = input("이메일:권한 (예: user@example.com:analyst): ").strip()
                if not line:
                    break
                
                if ':' in line:
                    email, role = line.split(':', 1)
                    user_list.append({'email': email.strip(), 'role': role.strip()})
                else:
                    user_list.append({'email': line.strip(), 'role': 'analyst'})
            
            if user_list:
                results = system.batch_add_users(user_list)
                print(f"\n📊 일괄 추가 결과:")
                print(f"   - 성공: {len(results['success'])}명")
                print(f"   - 실패: {len(results['failed'])}명")
                
                if results['failed']:
                    print(f"   - 실패한 사용자: {', '.join(results['failed'])}")
        
        elif choice == '6':
            email = input("이력을 조회할 이메일 주소: ").strip()
            history = system.get_user_history(email)
            
            if history:
                print(f"\n📋 {email} 작업 이력:")
                for i, record in enumerate(history, 1):
                    status = "✅" if record['success'] else "❌"
                    print(f"   {i}. {status} {record['operation']} ({record['timestamp']})")
                    if record['role']:
                        print(f"      권한: {record['role']}")
                    print(f"      세부사항: {record['details']}")
            else:
                print(f"❌ {email}의 이력이 없습니다.")
        
        elif choice == '7':
            print("👋 시스템을 종료합니다.")
            break
        
        else:
            print("❌ 잘못된 선택입니다.")

def main():
    """메인 함수"""
    interactive_menu()

if __name__ == "__main__":
    main() 