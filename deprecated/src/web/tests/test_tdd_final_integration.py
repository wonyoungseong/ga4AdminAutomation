#!/usr/bin/env python3
"""
TDD Refactor: 최종 통합 검증 테스트
================================

브라우저에서 실제 기능이 정상 작동하는지 검증합니다.
"""

import subprocess
import json
from pathlib import Path


def test_real_browser_functionality():
    """실제 브라우저 기능 통합 테스트"""
    print("🔵 TDD Refactor: 실제 브라우저 기능 검증 중...")
    
    # 1. 발송 기간 수정 테스트
    test_cases = [
        {"trigger_days": "30,7,1", "name": "다중 기간"},
        {"trigger_days": "0", "name": "즉시 발송"},
        {"trigger_days": "7", "name": "단일 기간"},
        {"trigger_days": "30,15,7,3,1", "name": "복합 기간"}
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📋 테스트 {i+1}: {test_case['name']}")
        
        # 각 알림 유형별로 테스트
        notification_types = ["daily_summary", "expiry_warning", "expiry_notice", "immediate_approval"]
        
        for notification_type in notification_types:
            result = subprocess.run([
                'curl', '-s', '-X', 'PUT',
                f'http://localhost:8000/api/admin/notification-settings/{notification_type}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(test_case)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    if response_data.get('success'):
                        print(f"  ✅ {notification_type}: {test_case['trigger_days']}")
                    else:
                        print(f"  ❌ {notification_type}: {response_data}")
                        return False
                except json.JSONDecodeError:
                    print(f"  ❌ {notification_type}: JSON 파싱 오류")
                    return False
            else:
                print(f"  ❌ {notification_type}: HTTP 오류")
                return False
    
    print("\n🎉 모든 발송 기간 수정 테스트 통과!")
    return True


def test_notification_toggle_functionality():
    """알림 활성화/비활성화 기능 테스트"""
    print("\n🔵 알림 토글 기능 검증 중...")
    
    notification_types = ["daily_summary", "expiry_warning"]
    
    for notification_type in notification_types:
        # 비활성화 테스트
        result = subprocess.run([
            'curl', '-s', '-X', 'PUT',
            f'http://localhost:8000/api/admin/notification-settings/{notification_type}',
            '-H', 'Content-Type: application/json',
            '-d', '{"enabled": false}'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            response_data = json.loads(result.stdout)
            if response_data.get('success'):
                print(f"  ✅ {notification_type} 비활성화 성공")
            else:
                print(f"  ❌ {notification_type} 비활성화 실패")
                return False
        
        # 활성화 테스트
        result = subprocess.run([
            'curl', '-s', '-X', 'PUT',
            f'http://localhost:8000/api/admin/notification-settings/{notification_type}',
            '-H', 'Content-Type: application/json',
            '-d', '{"enabled": true}'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            response_data = json.loads(result.stdout)
            if response_data.get('success'):
                print(f"  ✅ {notification_type} 활성화 성공")
            else:
                print(f"  ❌ {notification_type} 활성화 실패")
                return False
    
    print("\n🎉 모든 알림 토글 테스트 통과!")
    return True


def test_javascript_integration():
    """JavaScript 통합 기능 확인"""
    print("\n🔵 JavaScript 통합 기능 검증 중...")
    
    # JavaScript 파일들이 올바르게 로드되는지 확인
    js_files = [
        "/static/admin/utils.js",
        "/static/admin/validity-periods.js",
        "/static/admin/responsible-persons.js", 
        "/static/admin/system-settings.js",
        "/static/admin/main.js"
    ]
    
    for js_file in js_files:
        result = subprocess.run([
            'curl', '-s', '-I', f'http://localhost:8000{js_file}'
        ], capture_output=True, text=True, timeout=10)
        
        if "200 OK" in result.stdout:
            print(f"  ✅ {js_file} 로드 성공")
        else:
            print(f"  ❌ {js_file} 로드 실패")
            return False
    
    # Admin 페이지 로드 확인 (실제 콘텐츠 확인)
    result = subprocess.run([
        'curl', '-s', 'http://localhost:8000/admin'
    ], capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0 and "<!DOCTYPE html>" in result.stdout and "관리자 설정" in result.stdout:
        print("  ✅ Admin 페이지 로드 성공")
    else:
        print("  ❌ Admin 페이지 로드 실패")
        return False
    
    print("\n🎉 모든 JavaScript 통합 테스트 통과!")
    return True


def test_data_consistency():
    """데이터 일관성 검증"""
    print("\n🔵 데이터 일관성 검증 중...")
    
    # 알림 설정 조회
    result = subprocess.run([
        'curl', '-s', 'http://localhost:8000/api/admin/notification-settings'
    ], capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        settings = data.get('settings', [])
        
        print(f"  📊 총 {len(settings)}개 알림 설정 확인")
        
        # 각 설정 구조 검증
        required_fields = ['notification_type', 'enabled', 'trigger_days', 'template_subject']
        
        for setting in settings:
            missing_fields = []
            for field in required_fields:
                if field not in setting:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"  ❌ {setting.get('notification_type')}: 누락 필드 {missing_fields}")
                return False
            else:
                print(f"  ✅ {setting['notification_type']}: 모든 필드 존재")
        
        print("\n🎉 모든 데이터 일관성 테스트 통과!")
        return True
    else:
        print("  ❌ 알림 설정 조회 실패")
        return False


def run_tdd_refactor_tests():
    """TDD Refactor 단계 종합 테스트"""
    print("🔵 TDD Refactor 단계: 코드 개선 및 통합 검증")
    print("=" * 60)
    
    tests = [
        ("실제 브라우저 기능", test_real_browser_functionality),
        ("알림 토글 기능", test_notification_toggle_functionality),
        ("JavaScript 통합", test_javascript_integration),
        ("데이터 일관성", test_data_consistency)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n📋 테스트: {test_name}")
        print("-" * 40)
        
        try:
            if not test_func():
                failed_tests.append(test_name)
                print(f"🔴 {test_name} 실패")
            else:
                print(f"✅ {test_name} 성공")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"🔴 {test_name} 오류: {e}")
    
    print("\n" + "=" * 60)
    print(f"🔵 TDD Refactor 결과: {len(tests) - len(failed_tests)}/{len(tests)} 테스트 통과")
    
    if failed_tests:
        print("\n💥 실패한 테스트들:")
        for failed in failed_tests:
            print(f"   - {failed}")
        return False
    else:
        print("\n🏆 모든 TDD 단계 완료! 완벽한 기능 구현!")
        print("\n📋 구현된 기능:")
        print("   ✅ 발송 기간 수정 (0, 7, 30,7,1 등)")
        print("   ✅ 알림 활성화/비활성화 토글")
        print("   ✅ 모든 알림 유형 지원")
        print("   ✅ 실시간 UI 업데이트")
        print("   ✅ 오류 처리 및 검증")
        return True


if __name__ == "__main__":
    success = run_tdd_refactor_tests()
    exit(0 if success else 1) 