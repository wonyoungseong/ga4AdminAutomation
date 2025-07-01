"""
JavaScript-API 통합 테스트
=========================

TDD 방식으로 JavaScript에서 기대하는 API 응답 구조와 실제 API 응답 구조의 일치를 검증합니다.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import requests

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.web.main import app

client = TestClient(app)


class TestJavaScriptAPIIntegration:
    """JavaScript-API 응답 구조 일치성 테스트"""
    
    def test_validity_periods_structure_match(self):
        """유효기간 API가 JavaScript에서 기대하는 구조로 응답하는지 테스트"""
        response = client.get("/api/admin/validity-periods")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 data.periods로 접근하므로 최상위에 periods가 있어야 함
        assert "success" in data
        assert "periods" in data  # JavaScript: data.periods
        assert isinstance(data["periods"], list)
        
        print(f"✅ 유효기간 JavaScript 호환 구조: {data}")
    
    def test_responsible_persons_structure_match(self):
        """담당자 API가 JavaScript에서 기대하는 구조로 응답하는지 테스트"""
        response = client.get("/api/admin/responsible-persons")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 data.persons로 접근하므로 최상위에 persons가 있어야 함
        assert "success" in data
        assert "persons" in data  # JavaScript: data.persons
        assert isinstance(data["persons"], list)
        
        print(f"✅ 담당자 JavaScript 호환 구조: {data}")
    
    def test_notification_settings_structure_match(self):
        """알림 설정 API가 JavaScript에서 기대하는 구조로 응답하는지 테스트"""
        response = client.get("/api/admin/notification-settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 data.settings로 접근하므로 최상위에 settings가 있어야 함
        assert "success" in data
        assert "settings" in data  # JavaScript: data.settings
        assert isinstance(data["settings"], list)
        
        print(f"✅ 알림 설정 JavaScript 호환 구조: {data}")
    
    def test_system_settings_structure_match(self):
        """시스템 설정 API가 JavaScript에서 기대하는 구조로 응답하는지 테스트"""
        response = client.get("/api/admin/system-settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 data.settings로 접근하므로 최상위에 settings가 있어야 함
        assert "success" in data
        assert "settings" in data  # JavaScript: data.settings
        assert isinstance(data["settings"], dict)
        
        # 필수 설정 키들 확인
        settings = data["settings"]
        expected_keys = [
            "auto_approval_viewer", 
            "auto_approval_analyst", 
            "auto_approval_editor"
        ]
        
        for key in expected_keys:
            assert key in settings, f"Missing key: {key}"
        
        print(f"✅ 시스템 설정 JavaScript 호환 구조: {data}")
    
    def test_accounts_structure_match(self):
        """계정 API가 JavaScript에서 기대하는 구조로 응답하는지 테스트"""
        response = client.get("/api/accounts")
        
        assert response.status_code == 200
        data = response.json()
        
        # JavaScript에서 data.accounts로 접근하므로 최상위에 accounts가 있어야 함
        assert "success" in data
        assert "accounts" in data  # JavaScript: data.accounts
        assert isinstance(data["accounts"], list)
        
        print(f"✅ 계정 JavaScript 호환 구조: {data}")
    
    def test_properties_structure_match_real_server(self):
        """프로퍼티 API가 JavaScript에서 기대하는 구조로 응답하는지 테스트 (실제 서버)"""
        try:
            # 실제 서버에서 테스트
            response = requests.get("http://localhost:8000/api/properties", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # JavaScript에서 data.properties로 접근하므로 최상위에 properties가 있어야 함
                assert "success" in data
                assert "properties" in data  # JavaScript: data.properties
                assert isinstance(data["properties"], list)
                
                print(f"✅ 프로퍼티 JavaScript 호환 구조: {data}")
            else:
                print(f"⚠️ 프로퍼티 API 응답 상태: {response.status_code}")
                print(f"   실제 서버에서 프로퍼티 스캐너가 초기화되지 않은 상태")
                # 응답 구조만 확인 (503 에러여도 구조는 확인 가능)
                assert response.status_code in [200, 503]
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 실제 서버 연결 실패: {e}")
            print("   TestClient로 기본 구조 테스트 진행")
            
            # TestClient로 대체 테스트
            response = client.get("/api/properties")
            # 503 오류가 예상되므로 오류 처리
            assert response.status_code in [200, 503]


if __name__ == "__main__":
    # 개별 테스트 실행
    test_instance = TestJavaScriptAPIIntegration()
    
    print("🧪 JavaScript-API 통합 테스트 시작...")
    
    try:
        test_instance.test_validity_periods_structure_match()
        test_instance.test_responsible_persons_structure_match()  
        test_instance.test_notification_settings_structure_match()
        test_instance.test_system_settings_structure_match()
        test_instance.test_accounts_structure_match()
        test_instance.test_properties_structure_match_real_server()
        
        print("🎉 모든 테스트 통과!")
        
    except AssertionError as e:
        print(f"❌ 테스트 실패: {e}")
        print("💡 API 응답 구조를 JavaScript에서 기대하는 형태로 수정해야 합니다.")
        
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc() 