#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotificationType enum 일원화 검증 테스트
======================================

데이터베이스와 enum 간의 일치성을 확인합니다.
"""

import sys
import os
import sqlite3

# 프로젝트 루트 추가
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from services.notifications.notification_types import NotificationType, NotificationMetadata


def test_enum_values():
    """NotificationType enum 값들 확인"""
    print("🔍 NotificationType enum 값들:")
    
    expected_values = [
        'welcome', '30_days', '7_days', '1_day', 'today', 'expired',
        'extension_approved', 'editor_auto_downgrade', 'admin_notification',
        'immediate_approval', 'daily_summary', 'test'
    ]
    
    actual_values = [nt.value for nt in NotificationType]
    
    print(f"  📝 정의된 enum 값들: {actual_values}")
    
    # 모든 expected 값이 있는지 확인
    missing = [v for v in expected_values if v not in actual_values]
    if missing:
        print(f"  ❌ 누락된 값들: {missing}")
        return False
    else:
        print(f"  ✅ 모든 예상 값들이 정의됨")
        return True


def test_database_type_mapping():
    """데이터베이스 타입 매핑 확인"""
    print("\n🔍 데이터베이스 타입 매핑:")
    
    mapping_tests = [
        (NotificationType.WELCOME, 'welcome'),
        (NotificationType.EXPIRY_WARNING_30, 'expiry_warning'),
        (NotificationType.EXPIRY_WARNING_7, 'expiry_warning'),
        (NotificationType.EXPIRY_WARNING_1, 'expiry_warning'),
        (NotificationType.EXPIRY_WARNING_TODAY, 'expiry_warning'),
        (NotificationType.EXPIRED, 'expiry_notice'),
        (NotificationType.ADMIN_NOTIFICATION, 'immediate_approval'),
        (NotificationType.IMMEDIATE_APPROVAL, 'immediate_approval'),
        (NotificationType.DAILY_SUMMARY, 'daily_summary'),
        (NotificationType.TEST, 'welcome')
    ]
    
    all_success = True
    
    for enum_type, expected_db_type in mapping_tests:
        actual_db_type = NotificationMetadata.get_database_type_mapping(enum_type)
        
        if actual_db_type == expected_db_type:
            print(f"  ✅ {enum_type.value} -> {actual_db_type}")
        else:
            print(f"  ❌ {enum_type.value} -> {actual_db_type} (예상: {expected_db_type})")
            all_success = False
    
    return all_success


def test_trigger_days_mapping():
    """발송 일수 매핑 확인"""
    print("\n🔍 발송 일수 매핑:")
    
    trigger_tests = [
        (NotificationType.EXPIRY_WARNING_30, 30),
        (NotificationType.EXPIRY_WARNING_7, 7),
        (NotificationType.EXPIRY_WARNING_1, 1),
        (NotificationType.EXPIRY_WARNING_TODAY, 0),
        (NotificationType.WELCOME, 0),
        (NotificationType.EXPIRED, 0),
        (NotificationType.TEST, 0)
    ]
    
    all_success = True
    
    for enum_type, expected_days in trigger_tests:
        actual_days = NotificationMetadata.get_trigger_days_for_type(enum_type)
        
        if actual_days == expected_days:
            print(f"  ✅ {enum_type.value} -> {actual_days}일")
        else:
            print(f"  ❌ {enum_type.value} -> {actual_days}일 (예상: {expected_days}일)")
            all_success = False
    
    return all_success


def test_database_schema_consistency():
    """데이터베이스 스키마와의 일치성 확인"""
    print("\n🔍 데이터베이스 스키마 일치성:")
    
    try:
        # 데이터베이스 연결
        db_path = os.path.join(project_root, 'data', 'ga4_permission_management.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # notification_settings 테이블의 타입들 확인
        cursor.execute("SELECT DISTINCT notification_type FROM notification_settings")
        db_settings_types = [row[0] for row in cursor.fetchall()]
        
        print(f"  📝 notification_settings 타입들: {db_settings_types}")
        
        # notification_logs CHECK 제약에서 허용하는 타입들 확인 (스키마에서 추출)
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='notification_logs'")
        schema = cursor.fetchone()[0]
        
        # CHECK 제약에서 허용하는 값들 파싱
        import re
        check_match = re.search(r"notification_type IN \('([^']+)'(?:, '([^']+)')*\)", schema)
        if check_match:
            # 모든 허용된 값들 추출
            allowed_values = re.findall(r"'([^']+)'", schema.split("notification_type IN")[1].split(")")[0])
            print(f"  📝 notification_logs 허용 타입들: {allowed_values}")
        else:
            print("  ⚠️ CHECK 제약을 파싱할 수 없음")
            allowed_values = []
        
        conn.close()
        
        # enum 값들이 데이터베이스에서 허용되는지 확인
        enum_values = [nt.value for nt in NotificationType]
        not_allowed = [v for v in enum_values if v not in allowed_values]
        
        if not_allowed:
            print(f"  ❌ 데이터베이스에서 허용되지 않는 enum 값들: {not_allowed}")
            return False
        else:
            print(f"  ✅ 모든 enum 값들이 데이터베이스에서 허용됨")
            return True
            
    except Exception as e:
        print(f"  ❌ 데이터베이스 확인 실패: {e}")
        return False


def test_wonyoungseong_email():
    """wonyoungseong@gmail.com 테스트 준비 확인"""
    print("\n🔍 테스트 이메일 준비:")
    
    test_email = 'wonyoungseong@gmail.com'
    
    # 테스트 알림 타입 확인
    test_type = NotificationType.TEST
    db_type = NotificationMetadata.get_database_type_mapping(test_type)
    trigger_days = NotificationMetadata.get_trigger_days_for_type(test_type)
    
    print(f"  📧 테스트 대상 이메일: {test_email}")
    print(f"  🧪 테스트 알림 타입: {test_type.value}")
    print(f"  🗃️ 데이터베이스 매핑: {db_type}")
    print(f"  📅 발송 일수: {trigger_days}")
    print(f"  ✅ 테스트 준비 완료")
    
    return True


def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🧪 NotificationType enum 일원화 검증 테스트")
    print("=" * 60)
    
    tests = [
        ("Enum 값 확인", test_enum_values),
        ("데이터베이스 타입 매핑", test_database_type_mapping),
        ("발송 일수 매핑", test_trigger_days_mapping),
        ("데이터베이스 스키마 일치성", test_database_schema_consistency),
        ("테스트 이메일 준비", test_wonyoungseong_email)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} 실행 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"  {status} {test_name}")
    
    success_rate = passed / total * 100
    print(f"\n🎯 성공률: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("🎉 모든 테스트 통과! NotificationType enum 일원화가 성공적으로 완료되었습니다.")
        return True
    else:
        print("⚠️ 일부 테스트 실패. 추가 수정이 필요합니다.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 