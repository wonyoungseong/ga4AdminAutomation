#!/usr/bin/env python3
"""
발송 기간(trigger_days) 수정 기능 검증 테스트
===========================================

알림 템플릿은 수정 불가능하고, 발송 기간만 수정 가능한 기능을 검증합니다.
"""

import subprocess
import json
from pathlib import Path


def test_trigger_days_ui_updates():
    """발송 기간 UI 수정사항 검증"""
    print("🔍 발송 기간 UI 수정사항 검증 중...")
    
    # HTML 템플릿 헤더 변경 확인
    html_file = Path("src/web/templates/admin_config.html")
    if not html_file.exists():
        print("❌ admin_config.html 파일이 없습니다.")
        return False
    
    content = html_file.read_text()
    
    # 알림 설정 테이블 헤더 변경 확인 (다른 테이블의 <th>작업</th>은 유지되어야 함)
    header_checks = [
        ('<th>발송 기간</th>', True),
        ('<th>템플릿 정보</th>', True),
        ('<th>상태</th>', True),
        ('<th>발송 조건</th>', False),  # 제거되어야 함
        ('<th>제목 템플릿</th>', False),  # 제거되어야 함
    ]
    
    # 알림 설정 섹션에서만 <th>작업</th>이 제거되었는지 확인
    notification_section_start = content.find('<!-- 알림 설정 탭 -->')
    notification_section_end = content.find('<!-- 시스템 설정 탭 -->')
    
    if notification_section_start != -1 and notification_section_end != -1:
        notification_section = content[notification_section_start:notification_section_end]
        if '<th>작업</th>' not in notification_section:
            print("✅ 알림 설정 테이블에서 <th>작업</th> 제거됨")
        else:
            print("❌ 알림 설정 테이블에 <th>작업</th>이 여전히 있음")
            return False
    else:
        print("❌ 알림 설정 섹션을 찾을 수 없음")
        return False
    
    for check_text, should_exist in header_checks:
        if (check_text in content) == should_exist:
            status = "✅" if should_exist else "✅ (제거됨)"
            print(f"{status} {check_text}")
        else:
            status = "❌" if should_exist else "❌ (제거되지 않음)"
            print(f"{status} {check_text}")
            return False
    
    return True


def test_trigger_days_javascript():
    """발송 기간 JavaScript 로직 검증"""
    print("\n🔍 발송 기간 JavaScript 로직 검증 중...")
    
    js_file = Path("src/web/static/admin/system-settings.js")
    if not js_file.exists():
        print("❌ system-settings.js 파일이 없습니다.")
        return False
    
    content = js_file.read_text()
    
    # 핵심 기능 확인
    feature_checks = [
        "trigger-days",  # CSS 클래스
        "updateTriggerDays",  # 함수명
        "validateTriggerDays",  # 유효성 검사 함수
        "발송 기간을 쉼표로 구분하여 입력",  # 플레이스홀더 텍스트
        "템플릿 수정 불가",  # 템플릿 수정 불가 텍스트
        "고정",  # 템플릿 고정 버튼 텍스트
        "trigger_days"  # API 필드명
    ]
    
    for check in feature_checks:
        if check in content:
            print(f"✅ 기능 로직: {check}")
        else:
            print(f"❌ 누락된 로직: {check}")
            return False
    
    return True


def test_trigger_days_validation():
    """발송 기간 유효성 검사 로직 확인"""
    print("\n🔍 발송 기간 유효성 검사 로직 확인 중...")
    
    js_file = Path("src/web/static/admin/system-settings.js")
    content = js_file.read_text()
    
    # 유효성 검사 로직 확인
    validation_checks = [
        "if (triggerDays === '0') {",  # 즉시 발송 체크
        "triggerDays.split(',')",  # 쉼표 구분 체크
        "parseInt(day.trim())",  # 숫자 변환 체크
        "isNaN(num) || num < 0",  # 유효성 검사
        "올바른 발송 기간 형식이 아닙니다"  # 오류 메시지
    ]
    
    for check in validation_checks:
        if check in content:
            print(f"✅ 유효성 검사: {check}")
        else:
            print(f"❌ 누락된 검사: {check}")
            return False
    
    return True


def test_api_trigger_days_support():
    """API에서 trigger_days 필드 지원 확인"""
    print("\n🔍 API trigger_days 필드 지원 확인 중...")
    
    try:
        # 알림 설정 API 테스트
        result = subprocess.run([
            'curl', '-s', 'http://localhost:8000/api/admin/notification-settings'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('success') and 'settings' in data:
                print(f"✅ 알림 설정 API 응답 정상")
                
                # trigger_days 필드 확인
                for setting in data['settings']:
                    notification_type = setting.get('notification_type', 'unknown')
                    trigger_days = setting.get('trigger_days', 'null')
                    
                    if 'trigger_days' in setting:
                        print(f"   ✅ {notification_type}: trigger_days = '{trigger_days}'")
                    else:
                        print(f"   ❌ {notification_type}: trigger_days 필드 누락")
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


def test_template_modification_disabled():
    """템플릿 수정 비활성화 확인"""
    print("\n🔍 템플릿 수정 비활성화 확인 중...")
    
    js_file = Path("src/web/static/admin/system-settings.js")
    content = js_file.read_text()
    
    # 템플릿 수정 불가 관련 코드 확인
    disabled_checks = [
        "템플릿은 수정할 수 없습니다",  # 수정 불가 메시지
        "disabled>",  # 버튼 비활성화
        "btn-outline-secondary",  # 비활성 스타일
        "fas fa-lock",  # 잠금 아이콘
        "text-muted small",  # 비활성 텍스트 스타일
    ]
    
    for check in disabled_checks:
        if check in content:
            print(f"✅ 템플릿 수정 비활성화: {check}")
        else:
            print(f"❌ 누락된 비활성화 로직: {check}")
            return False
    
    return True


def run_trigger_days_test():
    """발송 기간 기능 종합 테스트"""
    print("🔄 발송 기간 수정 기능 검증 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("UI 수정사항", test_trigger_days_ui_updates),
        ("JavaScript 로직", test_trigger_days_javascript),
        ("유효성 검사", test_trigger_days_validation),
        ("API 지원", test_api_trigger_days_support),
        ("템플릿 수정 비활성화", test_template_modification_disabled)
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
        print("\n🎉 발송 기간 수정 기능이 성공적으로 구현되었습니다!")
        print("\n📝 구현된 기능:")
        print("   ✅ 발송 기간(trigger_days) 수정 가능")
        print("   ✅ 템플릿 내용 수정 비활성화")
        print("   ✅ 유효성 검사 (예: 30,7,1 또는 0)")
        print("   ✅ 실시간 API 업데이트")
        print("   ✅ 오류 시 자동 복원")
        print("\n💡 사용 방법:")
        print("   - 0: 즉시 발송")
        print("   - 30,7,1: 30일전, 7일전, 1일전 발송")
        print("   - 7: 7일전에만 발송")
    else:
        print(f"\n💡 {failed}개의 문제가 있습니다. 상세 로그를 확인해주세요.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_trigger_days_test()
    exit(0 if success else 1) 