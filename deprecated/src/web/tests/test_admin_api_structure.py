"""
관리자 API 응답 구조 테스트
==========================

TDD 방식으로 관리자 설정 페이지의 API 응답 구조를 검증합니다.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.web.main import app

client = TestClient(app)


class TestAdminAPIStructure:
    """관리자 API 응답 구조 테스트"""
    
    def test_validity_periods_api_structure(self):
        """유효기간 설정 API 응답 구조 테스트"""
        response = client.get("/api/admin/validity-periods")
        
        # 기본 응답 구조 검증
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 기대하는 구조 검증
        assert "success" in data
        assert "data" in data
        assert "periods" in data["data"]
        assert isinstance(data["data"]["periods"], list)
        
        print(f"✅ 유효기간 API 응답: {data}")
    
    def test_responsible_persons_api_structure(self):
        """담당자 관리 API 응답 구조 테스트"""
        response = client.get("/api/admin/responsible-persons")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 기대하는 구조 검증
        assert "success" in data
        assert "data" in data
        assert "persons" in data["data"]
        assert isinstance(data["data"]["persons"], list)
        
        print(f"✅ 담당자 API 응답: {data}")
    
    def test_system_settings_api_structure(self):
        """시스템 설정 API 응답 구조 테스트"""
        response = client.get("/api/admin/system-settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 기대하는 구조 검증
        assert "success" in data
        assert "data" in data
        assert "settings" in data["data"]
        assert isinstance(data["data"]["settings"], dict)
        
        # 필수 설정 키들 확인
        settings = data["data"]["settings"]
        expected_keys = [
            "auto_approval_viewer", 
            "auto_approval_analyst", 
            "auto_approval_editor"
        ]
        
        for key in expected_keys:
            assert key in settings, f"Missing key: {key}"
        
        print(f"✅ 시스템 설정 API 응답: {data}")
    
    def test_notification_settings_api_structure(self):
        """알림 설정 API 응답 구조 테스트"""
        response = client.get("/api/admin/notification-settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 기대하는 구조 검증
        assert "success" in data
        assert "data" in data
        assert "settings" in data["data"]
        assert isinstance(data["data"]["settings"], list)
        
        print(f"✅ 알림 설정 API 응답: {data}")
    
    def test_properties_api_structure(self):
        """프로퍼티 API 응답 구조 테스트"""
        response = client.get("/api/properties")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 기대하는 구조 검증
        assert "success" in data
        
        # properties 키가 있는지 확인 (data 안에 있을 수도 있음)
        if "data" in data:
            assert "properties" in data["data"]
            assert isinstance(data["data"]["properties"], list)
        else:
            assert "properties" in data
            assert isinstance(data["properties"], list)
        
        print(f"✅ 프로퍼티 API 응답: {data}")
    
    def test_accounts_api_structure(self):
        """계정 API 응답 구조 테스트"""
        response = client.get("/api/accounts")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 기대하는 구조 검증
        assert "success" in data
        
        # accounts 키가 있는지 확인
        if "data" in data:
            assert "accounts" in data["data"]
            assert isinstance(data["data"]["accounts"], list)
        else:
            assert "accounts" in data
            assert isinstance(data["accounts"], list)
        
        print(f"✅ 계정 API 응답: {data}")


if __name__ == "__main__":
    # 개별 테스트 실행
    test_instance = TestAdminAPIStructure()
    
    print("🧪 관리자 API 구조 테스트 시작...")
    
    try:
        test_instance.test_validity_periods_api_structure()
        test_instance.test_responsible_persons_api_structure()  
        test_instance.test_system_settings_api_structure()
        test_instance.test_notification_settings_api_structure()
        test_instance.test_properties_api_structure()
        test_instance.test_accounts_api_structure()
        
        print("🎉 모든 테스트 통과!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc() 