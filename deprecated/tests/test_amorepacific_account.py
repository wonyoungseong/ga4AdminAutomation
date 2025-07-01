#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amorepacific 계정 테스트
======================

wonyoung.seong@amorepacific.com 계정으로 완전 자동화 시스템을 테스트합니다.
"""

import json
from datetime import datetime
from complete_ga4_user_automation import CompleteGA4UserAutomation, UserRole

def test_amorepacific_account():
    """Amorepacific 계정 테스트"""
    print("🎯 Amorepacific 계정 테스트")
    print("=" * 60)
    
    # 테스트 대상 계정
    test_email = "wonyoung.seong@amorepacific.com"
    target_role = UserRole.VIEWER
    
    print(f"📧 테스트 계정: {test_email}")
    print(f"🎯 목표 권한: {target_role.name} ({target_role.value})")
    print(f"🕐 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        # 자동화 시스템 초기화
        print("🚀 자동화 시스템 초기화 중...")
        automation = CompleteGA4UserAutomation()
        print("✅ 시스템 초기화 완료")
        
        # 현재 사용자 목록 확인
        print("\n📋 현재 GA4 사용자 목록:")
        current_users = automation.get_current_users()
        for email, roles in current_users.items():
            print(f"   👤 {email}: {roles}")
        
        # 지능형 사용자 추가 시도
        print(f"\n🎯 {test_email} 지능형 추가 시도:")
        print("-" * 40)
        
        result = automation.add_user_with_smart_method(test_email, target_role)
        
        # 결과 출력
        print(f"\n📊 테스트 결과:")
        print(f"   📧 계정: {result['email']}")
        print(f"   🎯 목표 권한: {result['target_role']}")
        print(f"   ✅ 성공 여부: {'성공' if result['success'] else '대기 중' if result.get('method_used') else '실패'}")
        print(f"   🔧 사용된 방법: {result.get('method_used', 'None')}")
        print(f"   💬 메시지: {result['message']}")
        
        # 시도한 방법들 상세 출력
        print(f"\n🔍 시도한 방법들:")
        for i, attempt in enumerate(result['attempts'], 1):
            status = "✅ 성공" if attempt['success'] else "❌ 실패"
            print(f"   {i}. {attempt['method']}: {status}")
            print(f"      💬 {attempt['message']}")
        
        # 최종 사용자 목록 재확인
        print(f"\n📋 최종 GA4 사용자 목록:")
        final_users = automation.get_current_users()
        for email, roles in final_users.items():
            print(f"   👤 {email}: {roles}")
        
        # 결론 및 다음 단계
        print(f"\n" + "=" * 60)
        print(f"🎉 테스트 완료 요약:")
        
        if result['success']:
            print(f"✅ {test_email} 즉시 권한 부여 성공!")
            print(f"🎯 부여된 권한: {target_role.name}")
        elif result.get('method_used') == 'email_invite':
            print(f"📧 {test_email}에게 초대 이메일 발송 완료")
            print(f"⏳ 사용자 로그인 후 자동 권한 부여 예정")
            print(f"🔄 스케줄러가 5분마다 자동 확인 중...")
            print(f"\n💡 다음 단계:")
            print(f"   1. {test_email}로 이메일 확인")
            print(f"   2. analytics.google.com 접속")
            print(f"   3. 5분 후 자동 권한 부여 완료")
        else:
            print(f"❌ {test_email} 처리 실패")
            print(f"💬 오류: {result['message']}")
        
        print(f"🕐 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def check_pending_status():
    """대기 중인 사용자 상태 확인"""
    print("\n🔍 대기 중인 사용자 상태 확인")
    print("-" * 40)
    
    try:
        automation = CompleteGA4UserAutomation()
        
        # 대기 중인 사용자 재시도
        automation.check_pending_users_and_retry()
        
        # 최종 상태 확인
        current_users = automation.get_current_users()
        print(f"\n📋 현재 GA4 사용자 목록:")
        for email, roles in current_users.items():
            print(f"   👤 {email}: {roles}")
            
    except Exception as e:
        print(f"❌ 상태 확인 중 오류: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 Amorepacific 계정 완전 자동화 테스트")
    print("=" * 60)
    
    while True:
        print("\n📋 테스트 메뉴:")
        print("1. 🎯 Amorepacific 계정 지능형 추가 테스트")
        print("2. 🔍 대기 중인 사용자 상태 확인")
        print("3. 📊 현재 사용자 목록 조회")
        print("0. 🚪 종료")
        
        choice = input("\n선택하세요 (0-3): ").strip()
        
        if choice == '1':
            test_amorepacific_account()
        elif choice == '2':
            check_pending_status()
        elif choice == '3':
            automation = CompleteGA4UserAutomation()
            current_users = automation.get_current_users()
            print(f"\n📋 현재 GA4 사용자 목록:")
            for email, roles in current_users.items():
                print(f"   👤 {email}: {roles}")
        elif choice == '0':
            print("👋 테스트를 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다. 다시 선택해주세요.")

if __name__ == "__main__":
    main() 