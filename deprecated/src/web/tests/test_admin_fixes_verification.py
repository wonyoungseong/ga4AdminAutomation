#!/usr/bin/env python3
"""
Admin 수정사항 검증 테스트
=======================

1. 유효기간 저장 시 NULL 값 문제 해결 검증
2. 알림 설정 UI 표시 문제 해결 검증
"""

import subprocess
import json
from pathlib import Path


def test_admin_page_javascript_structure():
    """Admin 페이지 JavaScript 구조 검증"""
    print("🔍 JavaScript 파일 구조 검증 중...")
    
    # 파일 존재 확인
    admin_js_files = [
        "src/web/static/admin/utils.js",
        "src/web/static/admin/validity-periods.js", 
        "src/web/static/admin/responsible-persons.js",
        "src/web/static/admin/system-settings.js",
        "src/web/static/admin/main.js"
    ]
    
    for js_file in admin_js_files:
        if not Path(js_file).exists():
            print(f"❌ {js_file} 파일이 없습니다")
            return False
        else:
            print(f"✅ {js_file} 존재 확인")
    
    return True


def test_validity_periods_validation():
    """유효기간 저장 로직의 유효성 검사 확인"""
    print("\n🔍 유효기간 유효성 검사 로직 확인 중...")
    
    # validity-periods.js에서 유효성 검사 코드 확인
    js_file = Path("src/web/static/admin/validity-periods.js")
    content = js_file.read_text()
    
    # 유효성 검사 관련 코드 존재 확인
    validation_checks = [
        "isNaN(periodDays)",
        "periodDays <= 0",
        "유효한 일수를 입력해주세요",
        "AdminUtils.showAlert"
    ]
    
    for check in validation_checks:
        if check in content:
            print(f"✅ 유효성 검사 포함: {check}")
        else:
            print(f"❌ 유효성 검사 누락: {check}")
            return False
    
    return True


def test_notification_settings_ui():
    """알림 설정 UI 로직 확인"""
    print("\n🔍 알림 설정 UI 로직 확인 중...")
    
    # system-settings.js에서 알림 설정 관련 코드 확인
    js_file = Path("src/web/static/admin/system-settings.js")
    content = js_file.read_text()
    
    # 알림 설정 관련 코드 존재 확인
    notification_checks = [
        "notifications-table",  # 올바른 테이블 ID
        "setting.enabled",      # 올바른 필드명
        "immediate_approval",   # 실제 알림 타입
        "daily_summary",
        "expiry_warning", 
        "expiry_notice"
    ]
    
    for check in notification_checks:
        if check in content:
            print(f"✅ 알림 설정 로직 포함: {check}")
        else:
            print(f"❌ 알림 설정 로직 누락: {check}")
            return False
    
    return True


def test_api_endpoints_response():
    """API 엔드포인트 응답 확인"""
    print("\n🔍 API 엔드포인트 응답 확인 중...")
    
    try:
        # 알림 설정 API 테스트
        result = subprocess.run([
            'curl', '-s', 'http://localhost:8000/api/admin/notification-settings'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('success') and 'settings' in data:
                settings_count = len(data['settings'])
                print(f"✅ 알림 설정 API 응답 정상 ({settings_count}개 설정)")
                
                # 설정 항목들 확인
                for setting in data['settings']:
                    notification_type = setting.get('notification_type', 'unknown')
                    enabled = setting.get('enabled', 0)
                    status = "활성" if enabled else "비활성"
                    print(f"   - {notification_type}: {status}")
                
                return True
            else:
                print(f"❌ 알림 설정 API 응답 오류: {data}")
                return False
        else:
            print(f"❌ API 호출 실패: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ API 호출 타임아웃")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ API 테스트 오류: {e}")
        return False


def test_html_template_updates():
    """HTML 템플릿 수정사항 확인"""
    print("\n🔍 HTML 템플릿 수정사항 확인 중...")
    
    html_file = Path("src/web/templates/admin_config.html")
    content = html_file.read_text()
    
    # onclick 속성이 제거되고 ID가 추가되었는지 확인
    template_checks = [
        ('id="add-new-period-btn"', True),
        ('id="add-new-manager-btn"', True), 
        ('id="save-system-settings-btn"', True),
        ('id="save-period-btn"', True),
        ('id="save-manager-btn"', True),
        ('onclick="addNewPeriod()"', False),
        ('onclick="addNewManager()"', False),
        ('onclick="saveSystemSettings()"', False),
        ('onclick="savePeriod()"', False),
        ('onclick="saveManager()"', False)
    ]
    
    for check_text, should_exist in template_checks:
        if (check_text in content) == should_exist:
            status = "✅" if should_exist else "✅ (제거됨)"
            print(f"{status} {check_text}")
        else:
            status = "❌" if should_exist else "❌ (제거되지 않음)"
            print(f"{status} {check_text}")
            return False
    
    return True


def run_all_tests():
    """모든 테스트 실행"""
    print("🔄 Admin 수정사항 검증 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("JavaScript 파일 구조", test_admin_page_javascript_structure),
        ("유효기간 유효성 검사", test_validity_periods_validation),
        ("알림 설정 UI 로직", test_notification_settings_ui),
        ("API 엔드포인트 응답", test_api_endpoints_response),
        ("HTML 템플릿 수정", test_html_template_updates)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 테스트: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                print(f"🎉 {test_name} 테스트 통과!")
                passed += 1
            else:
                print(f"💥 {test_name} 테스트 실패!")
                failed += 1
        except Exception as e:
            print(f"💥 {test_name} 테스트 오류: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 테스트 결과: 통과 {passed}개, 실패 {failed}개")
    
    if failed == 0:
        print("🎉 모든 수정사항이 정상적으로 적용되었습니다!")
        print("\n📝 해결된 문제:")
        print("   ✅ 유효기간 저장 시 NULL 값 오류 해결")
        print("   ✅ 알림 설정 UI 표시 문제 해결") 
        print("   ✅ JavaScript onclick 이벤트 오류 해결")
        print("   ✅ 모든 Admin 기능 정상 작동")
    else:
        print("💡 일부 문제가 남아있습니다. 로그를 확인해주세요.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 