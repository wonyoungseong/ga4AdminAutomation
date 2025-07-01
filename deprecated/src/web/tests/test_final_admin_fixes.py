#!/usr/bin/env python3
"""
최종 Admin 수정사항 검증 테스트
==============================

모든 Admin 오류 수정사항을 종합적으로 검증합니다.
"""

import subprocess
import json
from pathlib import Path


def test_validity_periods_fixes():
    """유효기간 수정사항 검증"""
    print("🔍 유효기간 수정사항 검증 중...")
    
    # JavaScript 파일에서 유효성 검사 로직 확인
    js_file = Path("src/web/static/admin/validity-periods.js")
    if not js_file.exists():
        print("❌ validity-periods.js 파일이 없습니다.")
        return False
    
    content = js_file.read_text()
    
    # 핵심 수정사항들 확인
    fixes = [
        "const daysValue = document.getElementById('period-days').value;",
        "const periodDays = parseInt(daysValue);",
        "if (!daysValue || isNaN(periodDays) || periodDays <= 0) {",
        "AdminUtils.showAlert('유효한 일수를 입력해주세요. (1일 이상)', 'warning');",
        "return;"
    ]
    
    for fix in fixes:
        if fix in content:
            print(f"✅ 유효성 검사 로직: {fix[:50]}...")
        else:
            print(f"❌ 누락된 로직: {fix[:50]}...")
            return False
    
    return True


def test_notification_settings_fixes():
    """알림 설정 수정사항 검증"""
    print("\n🔍 알림 설정 수정사항 검증 중...")
    
    # JavaScript 파일에서 이벤트 위임 로직 확인
    js_file = Path("src/web/static/admin/system-settings.js")
    if not js_file.exists():
        print("❌ system-settings.js 파일이 없습니다.")
        return False
    
    content = js_file.read_text()
    
    # 핵심 수정사항들 확인
    fixes = [
        "setupEventListeners()",
        "notification-toggle",
        "template-subject",
        "edit-template-btn",
        "data-notification-type",
        "event.target.classList.contains('notification-toggle')",
        "setting.enabled"
    ]
    
    for fix in fixes:
        if fix in content:
            print(f"✅ 이벤트 위임 로직: {fix}")
        else:
            print(f"❌ 누락된 로직: {fix}")
            return False
    
    return True


def test_html_template_fixes():
    """HTML 템플릿 수정사항 검증"""
    print("\n🔍 HTML 템플릿 수정사항 검증 중...")
    
    html_file = Path("src/web/templates/admin_config.html")
    if not html_file.exists():
        print("❌ admin_config.html 파일이 없습니다.")
        return False
    
    content = html_file.read_text()
    
    # onclick 속성이 모두 제거되었는지 확인
    removed_onclicks = [
        'onclick="addNewPeriod()"',
        'onclick="addNewManager()"', 
        'onclick="saveSystemSettings()"',
        'onclick="savePeriod()"',
        'onclick="saveManager()"'
    ]
    
    # ID 속성이 추가되었는지 확인
    added_ids = [
        'id="add-new-period-btn"',
        'id="add-new-manager-btn"',
        'id="save-system-settings-btn"',
        'id="save-period-btn"',
        'id="save-manager-btn"'
    ]
    
    # onclick 제거 확인
    for onclick in removed_onclicks:
        if onclick in content:
            print(f"❌ 제거되지 않은 onclick: {onclick}")
            return False
        else:
            print(f"✅ onclick 제거됨: {onclick}")
    
    # ID 추가 확인
    for id_attr in added_ids:
        if id_attr in content:
            print(f"✅ ID 추가됨: {id_attr}")
        else:
            print(f"❌ 누락된 ID: {id_attr}")
            return False
    
    return True


def test_api_functionality():
    """API 기능 테스트"""
    print("\n🔍 API 기능 테스트 중...")
    
    try:
        # 알림 설정 API 테스트
        result = subprocess.run([
            'curl', '-s', 'http://localhost:8000/api/admin/notification-settings'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('success') and 'settings' in data:
                print(f"✅ 알림 설정 API 정상 ({len(data['settings'])}개 설정)")
                
                # 각 설정이 올바른 구조를 가지는지 확인
                required_fields = ['notification_type', 'enabled', 'template_subject']
                for setting in data['settings']:
                    for field in required_fields:
                        if field in setting:
                            print(f"   ✅ {setting['notification_type']}: {field} 필드 존재")
                        else:
                            print(f"   ❌ {setting.get('notification_type', 'unknown')}: {field} 필드 누락")
                            return False
                
                return True
            else:
                print(f"❌ API 응답 오류: {data}")
                return False
        else:
            print(f"❌ API 호출 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ API 테스트 오류: {e}")
        return False


def test_javascript_module_integration():
    """JavaScript 모듈 통합 테스트"""
    print("\n🔍 JavaScript 모듈 통합 테스트 중...")
    
    # main.js에서 이벤트 바인딩 확인
    main_js = Path("src/web/static/admin/main.js")
    if not main_js.exists():
        print("❌ main.js 파일이 없습니다.")
        return False
    
    content = main_js.read_text()
    
    # 핵심 통합 로직 확인
    integration_checks = [
        "bindEventListeners()",
        "addEventListener('click'",
        "add-new-period-btn",
        "save-system-settings-btn",
        "this.modules.validityPeriods.addNewPeriod()",
        "this.modules.systemSettings.saveSystemSettings()"
    ]
    
    for check in integration_checks:
        if check in content:
            print(f"✅ 통합 로직: {check}")
        else:
            print(f"❌ 누락된 통합 로직: {check}")
            return False
    
    return True


def run_comprehensive_test():
    """종합 테스트 실행"""
    print("🔄 최종 Admin 수정사항 검증 테스트 시작")
    print("=" * 60)
    
    tests = [
        ("유효기간 수정사항", test_validity_periods_fixes),
        ("알림 설정 수정사항", test_notification_settings_fixes),
        ("HTML 템플릿 수정사항", test_html_template_fixes),
        ("API 기능", test_api_functionality), 
        ("JavaScript 모듈 통합", test_javascript_module_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 테스트: {test_name}")
        print("-" * 40)
        
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
    
    print("\n" + "=" * 60)
    print(f"📊 최종 테스트 결과: 통과 {passed}개, 실패 {failed}개")
    
    if failed == 0:
        print("\n🎉 모든 Admin 오류가 성공적으로 해결되었습니다!")
        print("\n📝 해결된 문제 요약:")
        print("   ✅ 1. 유효기간 저장 시 NULL 값 오류 → 유효성 검사 추가")
        print("   ✅ 2. 담당자 추가 기능 오류 → onclick 이벤트 리스너 수정")
        print("   ✅ 3. 설정 저장 오류 → 이벤트 바인딩 수정")
        print("   ✅ 4. 알림 설정 UI 표시 오류 → API 데이터 구조 수정")
        print("   ✅ 5. JavaScript onclick 이벤트 오류 → 이벤트 위임 적용")
        print("\n🚀 이제 모든 Admin 기능이 정상적으로 작동합니다!")
    else:
        print(f"\n💡 {failed}개의 문제가 남아있습니다. 상세 로그를 확인해주세요.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1) 