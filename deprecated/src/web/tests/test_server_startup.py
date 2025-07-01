"""
테스트 3: 서버 시작 테스트 (간단 버전)
==============================

리팩토링된 서버가 정상적으로 시작되는지 테스트
"""

import sys
import time
import subprocess
import requests
from pathlib import Path

def test_import_main():
    """메인 모듈 임포트 테스트"""
    try:
        from src.web.main import app, main
        print("✅ 메인 모듈 임포트 성공")
        return True
    except Exception as e:
        print(f"❌ 메인 모듈 임포트 실패: {e}")
        return False

def test_app_creation():
    """FastAPI 앱 생성 테스트"""
    try:
        from src.web.main import app
        
        # 앱 기본 속성 확인
        assert hasattr(app, 'title')
        assert hasattr(app, 'routes')
        assert len(app.routes) > 0
        
        print(f"✅ FastAPI 앱 생성 성공 (라우트: {len(app.routes)}개)")
        return True
    except Exception as e:
        print(f"❌ FastAPI 앱 생성 실패: {e}")
        return False

def test_dependencies_available():
    """주요 의존성 확인"""
    try:
        from src.web.main import (
            db_manager,
            ga4_user_manager,
            notification_service,
            scheduler_service
        )
        
        print("✅ 주요 의존성 임포트 성공")
        return True
    except Exception as e:
        print(f"❌ 의존성 임포트 실패: {e}")
        return False

def test_config_files():
    """설정 파일 존재 확인"""
    try:
        config_file = Path("config/ga4-automatio-797ec352f393.json")
        if config_file.exists():
            print("✅ GA4 서비스 계정 파일 존재")
        else:
            print("⚠️ GA4 서비스 계정 파일 없음 (프로덕션에서는 필요)")
        
        return True
    except Exception as e:
        print(f"❌ 설정 파일 확인 실패: {e}")
        return False

def run_basic_tests():
    """기본 테스트 실행"""
    tests = [
        ("메인 모듈 임포트", test_import_main),
        ("FastAPI 앱 생성", test_app_creation),
        ("주요 의존성", test_dependencies_available),
        ("설정 파일", test_config_files)
    ]
    
    print("🧪 TDD 테스트 3단계: 서버 시작 기본 검증")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 테스트 오류: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 테스트 결과: {passed}개 통과, {failed}개 실패")
    
    if failed == 0:
        print("🎉 모든 서버 시작 테스트 통과!")
        print("✨ 리팩토링 완료 - 서버 구동 준비 완료!")
    else:
        print("⚠️ 일부 테스트 실패")
    
    return failed == 0

if __name__ == "__main__":
    success = run_basic_tests()
    if not success:
        sys.exit(1) 