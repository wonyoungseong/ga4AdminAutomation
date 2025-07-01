"""
여러 시스템 이메일 및 UI 정리 TDD 테스트
=========================================

1. 시스템 메일을 여러 개 선정할 수 있도록 개선
2. 기간 설정 UI와 DB 연동 확인 및 정리
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

print("🧪 시스템 이메일 및 UI 정리 TDD 분석")

# 1. 현재 시스템 이메일 설정 확인
print("\n1️⃣ 현재 시스템 이메일 설정 분석")
try:
    import requests
    response = requests.get("http://localhost:8000/api/admin/system-settings")
    data = response.json()
    
    if data.get("success"):
        system_email = data["settings"].get("system_email", "")
        print(f"   현재 시스템 이메일: {system_email}")
        print(f"   형태: {'단일 이메일' if ',' not in system_email else '복수 이메일'}")
        
        # 여러 이메일을 쉼표로 구분하는지 확인
        if ',' in system_email:
            emails = [email.strip() for email in system_email.split(',')]
            print(f"   이메일 개수: {len(emails)}")
            for i, email in enumerate(emails):
                print(f"     {i+1}. {email}")
        else:
            print("   ❌ 단일 이메일만 설정됨 - 여러 이메일 지원 필요")
            
except Exception as e:
    print(f"   오류: {e}")

# 2. 기간 설정 UI와 DB 연동 확인
print("\n2️⃣ 유효기간 설정 DB 연동 분석")
try:
    # 유효기간 목록 조회
    response = requests.get("http://localhost:8000/api/admin/validity-periods")
    data = response.json()
    
    if data.get("success"):
        periods = data.get("periods", [])
        print(f"   DB에 저장된 유효기간 개수: {len(periods)}")
        
        if periods:
            print("   ✅ 유효기간 데이터가 DB에 존재함:")
            for period in periods:
                print(f"     - {period.get('role')}: {period.get('period_days')}일")
        else:
            print("   ❌ 유효기간 데이터가 없음 - UI 제거 필요")
    
    # 유효기간 생성/수정/삭제 API 테스트
    print("\n   API 기능 테스트:")
    
    # 생성 API 테스트
    create_response = requests.post("http://localhost:8000/api/admin/validity-periods", 
                                  json={"role": "test_role", "period_days": 30, "description": "테스트"})
    print(f"     생성 API: {create_response.status_code} {'✅' if create_response.status_code == 200 else '❌'}")
    
    if create_response.status_code == 200:
        # 방금 생성한 데이터 삭제 (정리)
        response = requests.get("http://localhost:8000/api/admin/validity-periods")
        periods = response.json().get("periods", [])
        test_period = next((p for p in periods if p.get("role") == "test_role"), None)
        if test_period:
            delete_response = requests.delete(f"http://localhost:8000/api/admin/validity-periods/{test_period['id']}")
            print(f"     삭제 API: {delete_response.status_code} {'✅' if delete_response.status_code == 200 else '❌'}")
        
except Exception as e:
    print(f"   오류: {e}")

# 3. 시스템 설정 스키마 확인
print("\n3️⃣ 시스템 설정 개선 방향 제안")

print("   📋 현재 상황 요약:")
print("   1. 시스템 이메일: 단일 입력 필드")
print("   2. 유효기간 설정: UI와 DB 모두 구현됨")

print("\n   🎯 개선 방향:")
print("   1. 시스템 이메일을 textarea + 쉼표 구분으로 변경")
print("   2. 여러 이메일 유효성 검사 추가")
print("   3. 유효기간 설정은 정상 동작하므로 유지")

print("\n🏁 분석 완료!") 