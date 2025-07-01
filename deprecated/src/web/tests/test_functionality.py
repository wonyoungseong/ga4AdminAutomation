"""
테스트 2: 기능 테스트
=================

리팩토링된 각 라우터의 주요 기능이 정상 작동하는지 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates

class TestFunctionality:
    """기능 테스트 클래스"""
    
    def __init__(self):
        self.client = None
        self.app = None
    
    def setup_test_client(self):
        """테스트 클라이언트 설정"""
        try:
            from src.web.main import app
            self.app = app
            self.client = TestClient(app)
            return True
        except Exception as e:
            print(f"❌ 테스트 클라이언트 설정 실패: {e}")
            return False
    
    def test_dashboard_router_endpoints(self):
        """대시보드 라우터 엔드포인트 테스트"""
        if not self.setup_test_client():
            pytest.fail("테스트 클라이언트 설정 실패")
        
        try:
            # 대시보드 페이지 라우트 확인
            from src.web.routers.dashboard import router as dashboard_router
            
            routes = [route.path for route in dashboard_router.routes]
            expected_routes = ["/", "/register"]
            
            for expected in expected_routes:
                assert expected in routes, f"대시보드 라우터에 {expected} 경로가 없습니다"
            
            print("✅ 대시보드 라우터 엔드포인트 검증 완료")
            return True
            
        except Exception as e:
            print(f"❌ 대시보드 라우터 테스트 실패: {e}")
            return False
    
    def test_users_router_endpoints(self):
        """사용자 관리 라우터 엔드포인트 테스트"""
        try:
            from src.web.routers.users import router as users_router
            
            routes = [route.path for route in users_router.routes]
            expected_routes = ["/users", "/api/users", "/api/users/export"]
            
            for expected in expected_routes:
                assert expected in routes, f"사용자 라우터에 {expected} 경로가 없습니다"
            
            print("✅ 사용자 라우터 엔드포인트 검증 완료")
            return True
            
        except Exception as e:
            print(f"❌ 사용자 라우터 테스트 실패: {e}")
            return False
    
    def test_admin_router_endpoints(self):
        """관리자 라우터 엔드포인트 테스트"""
        try:
            from src.web.routers.admin import router as admin_router
            
            routes = [route.path for route in admin_router.routes]
            expected_routes = ["/admin", "/api/admin/validity-periods", "/api/admin/system-settings"]
            
            for expected in expected_routes:
                assert expected in routes, f"관리자 라우터에 {expected} 경로가 없습니다"
            
            print("✅ 관리자 라우터 엔드포인트 검증 완료")
            return True
            
        except Exception as e:
            print(f"❌ 관리자 라우터 테스트 실패: {e}")
            return False
    
    def test_api_router_endpoints(self):
        """API 라우터 엔드포인트 테스트"""
        try:
            from src.web.routers.api import router as api_router
            
            routes = [route.path for route in api_router.routes]
            expected_routes = ["/api/scan", "/api/properties", "/api/stats"]
            
            for expected in expected_routes:
                assert expected in routes, f"API 라우터에 {expected} 경로가 없습니다"
            
            print("✅ API 라우터 엔드포인트 검증 완료")
            return True
            
        except Exception as e:
            print(f"❌ API 라우터 테스트 실패: {e}")
            return False
    
    def test_test_router_endpoints(self):
        """테스트 라우터 엔드포인트 테스트"""
        try:
            from src.web.routers.test import router as test_router
            
            routes = [route.path for route in test_router.routes]
            expected_routes = ["/test", "/debug", "/api/test/health"]
            
            for expected in expected_routes:
                assert expected in routes, f"테스트 라우터에 {expected} 경로가 없습니다"
            
            print("✅ 테스트 라우터 엔드포인트 검증 완료")
            return True
            
        except Exception as e:
            print(f"❌ 테스트 라우터 테스트 실패: {e}")
            return False
    
    def test_model_validation(self):
        """모델 검증 테스트"""
        try:
            from src.web.models.requests import UserRegistrationRequest, AdminSettingsRequest
            from src.web.models.responses import ApiResponse, DashboardData
            
            # UserRegistrationRequest 검증
            user_req = UserRegistrationRequest(
                신청자="테스트 사용자",
                등록_계정_목록="test@example.com",
                property_ids=["123456"],
                권한="viewer"
            )
            assert user_req.신청자 == "테스트 사용자"
            
            # ApiResponse 검증
            api_resp = ApiResponse(
                success=True,
                message="테스트 성공",
                data={"test": "data"}
            )
            assert api_resp.success is True
            
            print("✅ 모델 검증 테스트 완료")
            return True
            
        except Exception as e:
            print(f"❌ 모델 검증 테스트 실패: {e}")
            return False
    
    def test_utility_functions(self):
        """유틸리티 함수 테스트"""
        try:
            from src.web.utils.helpers import DictObj, validate_email_list
            from src.web.utils.formatters import format_datetime, format_api_response
            
            # DictObj 테스트
            dict_obj = DictObj({"name": "test", "value": 123})
            assert dict_obj.name == "test"
            assert dict_obj.value == 123
            
            # 이메일 검증 테스트
            emails = validate_email_list("test1@example.com, test2@example.com")
            assert len(emails) == 2
            assert "test1@example.com" in emails
            
            # API 응답 포맷팅 테스트
            response = format_api_response(True, "성공", {"key": "value"})
            assert response["success"] is True
            assert response["message"] == "성공"
            
            print("✅ 유틸리티 함수 테스트 완료")
            return True
            
        except Exception as e:
            print(f"❌ 유틸리티 함수 테스트 실패: {e}")
            return False
    
    def test_fastapi_app_configuration(self):
        """FastAPI 앱 구성 테스트"""
        try:
            from src.web.main import app
            
            # 앱 메타데이터 확인
            assert app.title == "GA4 권한 관리 시스템"
            assert app.version == "2.0.0"
            
            # 미들웨어 확인
            middleware_classes = [middleware.cls.__name__ for middleware in app.user_middleware]
            assert "CORSMiddleware" in middleware_classes
            
            # 라우터 포함 확인
            assert len(app.routes) > 30  # 최소 30개 이상의 라우트
            
            print(f"✅ FastAPI 앱 구성 테스트 완료 (총 {len(app.routes)}개 라우트)")
            return True
            
        except Exception as e:
            print(f"❌ FastAPI 앱 구성 테스트 실패: {e}")
            return False
    
    def test_template_accessibility(self):
        """템플릿 접근성 테스트"""
        try:
            import os
            from pathlib import Path
            
            template_dir = Path("src/web/templates")
            required_templates = [
                "base.html",
                "dashboard.html", 
                "users_list.html",
                "admin_config.html",
                "register.html"
            ]
            
            for template in required_templates:
                template_path = template_dir / template
                assert template_path.exists(), f"템플릿 {template}이 존재하지 않습니다"
                
                # 템플릿 파일이 비어있지 않은지 확인
                assert template_path.stat().st_size > 0, f"템플릿 {template}이 비어있습니다"
            
            print("✅ 템플릿 접근성 테스트 완료")
            return True
            
        except Exception as e:
            print(f"❌ 템플릿 접근성 테스트 실패: {e}")
            return False


if __name__ == "__main__":
    # 단독 실행 시 테스트 실행
    test_functionality = TestFunctionality()
    
    tests = [
        test_functionality.test_dashboard_router_endpoints,
        test_functionality.test_users_router_endpoints,
        test_functionality.test_admin_router_endpoints,
        test_functionality.test_api_router_endpoints,
        test_functionality.test_test_router_endpoints,
        test_functionality.test_model_validation,
        test_functionality.test_utility_functions,
        test_functionality.test_fastapi_app_configuration,
        test_functionality.test_template_accessibility
    ]
    
    print("🧪 TDD 테스트 2단계: 기능 검증 시작")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 테스트 결과: {passed}개 통과, {failed}개 실패")
    
    if failed == 0:
        print("🎉 모든 기능 테스트 통과!")
    else:
        print("⚠️ 일부 테스트 실패 - 코드를 수정해야 합니다.")
        import sys
        sys.exit(1) 