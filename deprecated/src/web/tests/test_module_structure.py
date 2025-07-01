"""
테스트 1: 모듈 구조 및 임포트 검증
============================

리팩토링된 모듈들이 정상적으로 임포트되고 구조화되었는지 테스트
"""

import pytest
import sys
from pathlib import Path

class TestModuleStructure:
    """모듈 구조 테스트 클래스"""

    def test_routers_import(self):
        """라우터 모듈들이 정상적으로 임포트되는지 테스트"""
        try:
            from src.web.routers import (
                dashboard_router,
                users_router,
                admin_router,
                api_router,
                test_router
            )
            assert dashboard_router is not None, "dashboard_router가 None입니다"
            assert users_router is not None, "users_router가 None입니다"
            assert admin_router is not None, "admin_router가 None입니다"
            assert api_router is not None, "api_router가 None입니다"
            assert test_router is not None, "test_router가 None입니다"
            print("✅ 모든 라우터 임포트 성공")
        except ImportError as e:
            pytest.fail(f"❌ 라우터 임포트 실패: {e}")

    def test_models_import(self):
        """모델 모듈들이 정상적으로 임포트되는지 테스트"""
        try:
            from src.web.models import (
                UserRegistrationRequest,
                AdminSettingsRequest,
                ApiResponse,
                DashboardData
            )
            assert UserRegistrationRequest is not None
            assert AdminSettingsRequest is not None
            assert ApiResponse is not None
            assert DashboardData is not None
            print("✅ 모든 모델 임포트 성공")
        except ImportError as e:
            pytest.fail(f"❌ 모델 임포트 실패: {e}")

    def test_utils_import(self):
        """유틸리티 모듈들이 정상적으로 임포트되는지 테스트"""
        try:
            from src.web.utils import (
                DictObj,
                get_dashboard_data,
                format_datetime,
                format_api_response
            )
            assert DictObj is not None
            assert get_dashboard_data is not None
            assert format_datetime is not None
            assert format_api_response is not None
            print("✅ 모든 유틸리티 임포트 성공")
        except ImportError as e:
            pytest.fail(f"❌ 유틸리티 임포트 실패: {e}")

    def test_file_structure(self):
        """파일 구조가 올바르게 생성되었는지 테스트"""
        base_path = Path("src/web")
        
        # 필수 디렉토리 존재 확인
        required_dirs = ["routers", "models", "utils", "templates", "static"]
        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"필수 디렉토리 {dir_name}이 존재하지 않습니다"
            assert dir_path.is_dir(), f"{dir_name}이 디렉토리가 아닙니다"
        
        # 필수 파일 존재 확인
        required_files = [
            "main.py",
            "routers/__init__.py",
            "routers/dashboard.py",
            "routers/users.py", 
            "routers/admin.py",
            "routers/api.py",
            "routers/test.py",
            "models/__init__.py",
            "models/requests.py",
            "models/responses.py",
            "utils/__init__.py",
            "utils/helpers.py",
            "utils/formatters.py"
        ]
        
        for file_path in required_files:
            full_path = base_path / file_path
            assert full_path.exists(), f"필수 파일 {file_path}가 존재하지 않습니다"
            assert full_path.is_file(), f"{file_path}가 파일이 아닙니다"
        
        print("✅ 파일 구조 검증 완료")

    def test_main_app_creation(self):
        """메인 앱이 정상적으로 생성되는지 테스트"""
        try:
            from src.web.main import app
            assert app is not None, "FastAPI 앱이 생성되지 않았습니다"
            assert hasattr(app, 'routes'), "앱에 라우트가 없습니다"
            assert len(app.routes) > 0, "등록된 라우트가 없습니다"
            print(f"✅ FastAPI 앱 생성 성공 (라우트 수: {len(app.routes)})")
        except ImportError as e:
            pytest.fail(f"❌ 메인 앱 임포트 실패: {e}")

    def test_backup_file_exists(self):
        """백업 파일이 존재하는지 테스트"""
        backup_path = Path("src/web/main_backup.py")
        assert backup_path.exists(), "백업 파일 main_backup.py가 존재하지 않습니다"
        
        # 백업 파일이 충분히 큰지 확인 (기존 코드가 들어있는지)
        backup_size = backup_path.stat().st_size
        assert backup_size > 50000, f"백업 파일이 너무 작습니다 ({backup_size} bytes)"
        print("✅ 백업 파일 검증 완료")


if __name__ == "__main__":
    # 단독 실행 시 테스트 실행
    test_module = TestModuleStructure()
    
    tests = [
        test_module.test_file_structure,
        test_module.test_backup_file_exists,
        test_module.test_routers_import,
        test_module.test_models_import,
        test_module.test_utils_import,
        test_module.test_main_app_creation
    ]
    
    print("🧪 TDD 테스트 1단계: 모듈 구조 검증 시작")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 테스트 결과: {passed}개 통과, {failed}개 실패")
    
    if failed == 0:
        print("🎉 모든 구조 테스트 통과!")
    else:
        print("⚠️ 일부 테스트 실패 - 코드를 수정해야 합니다.")
        sys.exit(1) 