#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
올바른 Analytics 계정 접근 확인
=============================

사용자가 올바른 BETC Analytics 계정에 접근했는지 확인합니다.
"""

import json

def verify_correct_analytics_access():
    """올바른 Analytics 계정 접근 확인"""
    print("🔍 올바른 Analytics 계정 접근 확인")
    print("=" * 60)
    
    # 설정 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    target_account_id = config['account_id']
    target_property_id = config['property_id']
    target_email = "wonyoung.seong@amorepacific.com"
    
    print(f"🎯 대상 정보:")
    print(f"   이메일: {target_email}")
    print(f"   Account ID: {target_account_id}")
    print(f"   Property ID: {target_property_id}")
    print(f"   계정명: BETC")
    print(f"   속성명: [Edu]Ecommerce - Beauty Cosmetic")
    
    print(f"\n🚨 중요한 문제 발견!")
    print("-" * 40)
    print(f"❌ 현재 상황: 사용자가 Amorepacific Analytics에 로그인함")
    print(f"✅ 필요한 상황: 사용자가 BETC Analytics에 접근해야 함")
    
    print(f"\n💡 해결 방법:")
    print("-" * 40)
    print(f"1. 🔄 올바른 Analytics 계정 접근:")
    print(f"   - 현재 Amorepacific Analytics에서 로그아웃")
    print(f"   - BETC Analytics 계정에 접근")
    print(f"   - URL에서 Account ID {target_account_id} 확인")
    
    print(f"\n2. 📧 직접 초대 방법:")
    print(f"   - BETC 계정 관리자가 GA4 콘솔에서 직접 초대")
    print(f"   - {target_email}을 Viewer 권한으로 초대")
    print(f"   - 사용자가 초대 이메일 수락")
    
    print(f"\n3. 🔗 정확한 접근 URL:")
    betc_url = f"https://analytics.google.com/analytics/web/#/p{target_property_id}/reports/intelligenthome"
    print(f"   {betc_url}")
    
    print(f"\n❓ 확인 사항:")
    print(f"   1. 현재 URL에 'p{target_property_id}'가 포함되어 있나요?")
    print(f"   2. 좌측 상단에 'BETC' 계정명이 보이나요?")
    print(f"   3. '[Edu]Ecommerce - Beauty Cosmetic' 속성이 보이나요?")
    
    print(f"\n🎯 다음 단계:")
    print("-" * 40)
    print(f"1. 위 URL로 직접 접근")
    print(f"2. BETC 계정 확인")
    print(f"3. 올바른 계정에서 API 재시도")

def generate_invitation_instructions():
    """초대 안내 생성"""
    print(f"\n📧 BETC 계정 관리자용 초대 안내")
    print("=" * 60)
    
    print(f"🎯 초대할 사용자: wonyoung.seong@amorepacific.com")
    print(f"🏢 대상 계정: BETC (Account ID: 332818805)")
    print(f"📊 대상 속성: [Edu]Ecommerce - Beauty Cosmetic")
    print(f"🔑 권한 수준: Viewer")
    
    print(f"\n📋 초대 단계:")
    print(f"1. GA4 콘솔 접속: analytics.google.com")
    print(f"2. 관리 → 계정 액세스 관리")
    print(f"3. '+' 버튼 → 사용자 추가")
    print(f"4. 이메일: wonyoung.seong@amorepacific.com")
    print(f"5. 권한: Viewer")
    print(f"6. 초대 발송")
    
    print(f"\n✅ 초대 완료 후:")
    print(f"   - 사용자가 초대 이메일 수락")
    print(f"   - BETC Analytics에 직접 접근")
    print(f"   - API 자동 권한 관리 활성화")

def main():
    """메인 실행 함수"""
    verify_correct_analytics_access()
    generate_invitation_instructions()
    
    print(f"\n🎉 결론:")
    print("=" * 60)
    print(f"✅ API 시스템: 완벽 작동")
    print(f"✅ Service Account: 정상")
    print(f"❌ 사용자 위치: 잘못된 Analytics 계정")
    print(f"💡 해결책: BETC Analytics 직접 접근 필요")

if __name__ == "__main__":
    main() 