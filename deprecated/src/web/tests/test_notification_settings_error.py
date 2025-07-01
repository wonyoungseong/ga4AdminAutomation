#!/usr/bin/env python3
"""
TDD Red: 알림 설정 수정 오류 분석 테스트
=====================================

현재 발생하고 있는 500 Internal Server Error를 파악하고 수정합니다.
"""

import subprocess
import json
from pathlib import Path


def test_notification_settings_api_error():
    """현재 발생하는 알림 설정 API 오류 테스트 (TDD Red)"""
    print("🔴 TDD Red: 알림 설정 API 오류 분석 중...")
    
    try:
        # 1. 현재 알림 설정 조회
        result = subprocess.run([
            'curl', '-s', 'http://localhost:8000/api/admin/notification-settings'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ 알림 설정 조회 실패: {result.stderr}")
            return False
        
        data = json.loads(result.stdout)
        if not data.get('success'):
            print(f"❌ API 응답 오류: {data}")
            return False
        
        print(f"✅ 알림 설정 조회 성공: {len(data['settings'])}개 설정")
        
        # 2. 발송 기간 수정 테스트 (현재 실패하는 요청)
        test_notification_type = data['settings'][0]['notification_type']
        
        print(f"🧪 테스트 대상: {test_notification_type}")
        
        # trigger_days 수정 시도
        update_result = subprocess.run([
            'curl', '-s', '-X', 'PUT',
            f'http://localhost:8000/api/admin/notification-settings/{test_notification_type}',
            '-H', 'Content-Type: application/json',
            '-d', '{"trigger_days": "7,1"}'
        ], capture_output=True, text=True, timeout=10)
        
        print(f"📊 응답 코드: {update_result.returncode}")
        print(f"📊 응답 내용: {update_result.stdout}")
        
        if update_result.returncode == 0:
            try:
                response_data = json.loads(update_result.stdout)
                if response_data.get('success'):
                    print("✅ 발송 기간 수정 성공")
                    return True
                else:
                    print(f"❌ 발송 기간 수정 실패: {response_data}")
                    return False
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 오류: {e}")
                print(f"응답 내용: {update_result.stdout}")
                return False
        else:
            print(f"❌ HTTP 요청 실패: {update_result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        return False


def test_backend_api_implementation():
    """백엔드 API 구현 상태 확인"""
    print("\n🔍 백엔드 API 구현 상태 확인 중...")
    
    # 1. API 라우터 파일 확인
    admin_router_file = Path("src/web/routers/admin.py")
    if not admin_router_file.exists():
        print("❌ admin.py 라우터 파일이 없습니다.")
        return False
    
    content = admin_router_file.read_text()
    
    # 2. PUT 메소드 구현 확인
    put_checks = [
        "@router.put(\"/api/admin/notification-settings/{notification_type}\")",
        "async def update_notification_setting",
        "notification_type: str",
        "trigger_days"
    ]
    
    missing_implementations = []
    for check in put_checks:
        if check not in content:
            missing_implementations.append(check)
    
    if missing_implementations:
        print("❌ 누락된 API 구현:")
        for missing in missing_implementations:
            print(f"   - {missing}")
        return False
    else:
        print("✅ PUT API 엔드포인트 구현 확인됨")
    
    # 3. 오류 처리 로직 확인
    error_handling_checks = [
        "try:",
        "except",
        "HTTPException"
    ]
    
    for check in error_handling_checks:
        if check in content:
            print(f"✅ 오류 처리: {check}")
        else:
            print(f"⚠️  오류 처리 누락: {check}")
    
    return True


def test_database_notification_settings_table():
    """데이터베이스 알림 설정 테이블 구조 확인"""
    print("\n🔍 데이터베이스 테이블 구조 확인 중...")
    
    # SQLite 스키마 확인
    try:
        result = subprocess.run([
            'sqlite3', 'data/ga4_permission_management.db',
            '.schema notification_settings'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ notification_settings 테이블 존재:")
            print(result.stdout)
            
            # trigger_days 컬럼 확인
            if 'trigger_days' in result.stdout:
                print("✅ trigger_days 컬럼 확인됨")
            else:
                print("❌ trigger_days 컬럼 누락")
                return False
                
            return True
        else:
            print("❌ notification_settings 테이블이 없거나 접근 불가")
            return False
            
    except Exception as e:
        print(f"❌ 데이터베이스 확인 오류: {e}")
        return False


def run_tdd_red_analysis():
    """TDD Red 단계: 실패 원인 분석"""
    print("🔴 TDD Red 단계: 현재 실패 상황 분석")
    print("=" * 50)
    
    tests = [
        ("알림 설정 API 오류", test_notification_settings_api_error),
        ("백엔드 API 구현", test_backend_api_implementation),
        ("데이터베이스 테이블", test_database_notification_settings_table)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n📋 테스트: {test_name}")
        print("-" * 30)
        
        try:
            if not test_func():
                failed_tests.append(test_name)
                print(f"🔴 {test_name} 실패 확인")
            else:
                print(f"✅ {test_name} 정상")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"🔴 {test_name} 오류: {e}")
    
    print("\n" + "=" * 50)
    print(f"🔴 TDD Red 결과: {len(failed_tests)}개 실패 항목 발견")
    
    if failed_tests:
        print("\n💥 실패한 테스트들:")
        for failed in failed_tests:
            print(f"   - {failed}")
        print("\n🔧 다음 단계: TDD Green (문제 해결)")
    else:
        print("\n🎉 모든 테스트 통과! 문제가 해결되었습니다.")
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_tdd_red_analysis()
    exit(0 if success else 1) 