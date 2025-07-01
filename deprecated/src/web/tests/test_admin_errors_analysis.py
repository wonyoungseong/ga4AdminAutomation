"""
Admin 정보 오류 분석 TDD 테스트
==============================

DevTools에서 발견된 오류들을 분석하고 해결방안을 제시합니다.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

print("🔍 Admin 정보 오류 분석 시작")

# 1. 유효기간 API 응답 구조 분석
print("\n1️⃣ 유효기간 API 응답 구조 분석")
try:
    import requests
    
    # 유효기간 목록 조회
    response = requests.get("http://localhost:8000/api/admin/validity-periods")
    data = response.json()
    
    print(f"   응답 상태: {response.status_code}")
    print(f"   응답 구조: {list(data.keys())}")
    
    if data.get("success") and data.get("periods"):
        periods = data["periods"]
        print(f"   유효기간 개수: {len(periods)}")
        
        if periods:
            first_period = periods[0]
            print(f"   첫 번째 유효기간 구조: {list(first_period.keys())}")
            print(f"   role 필드 존재: {'role' in first_period}")
            print(f"   실제 데이터: {first_period}")
            
            # 개별 유효기간 조회 테스트
            period_id = first_period.get('id')
            if period_id:
                detail_response = requests.get(f"http://localhost:8000/api/admin/validity-periods/{period_id}")
                detail_data = detail_response.json()
                print(f"   개별 조회 상태: {detail_response.status_code}")
                print(f"   개별 조회 구조: {list(detail_data.keys()) if detail_data else 'None'}")
                
                if detail_data.get("success"):
                    print("   ✅ 개별 조회 성공")
                    if 'period' in detail_data:
                        period_detail = detail_data['period']
                        print(f"   period 구조: {list(period_detail.keys()) if isinstance(period_detail, dict) else type(period_detail)}")
                else:
                    print(f"   ❌ 개별 조회 실패: {detail_data}")
    else:
        print("   ❌ 유효기간 데이터 없음")
        
except Exception as e:
    print(f"   오류: {e}")

# 2. 담당자 API 응답 구조 분석
print("\n2️⃣ 담당자 API 응답 구조 분석")
try:
    response = requests.get("http://localhost:8000/api/admin/responsible-persons")
    data = response.json()
    
    print(f"   응답 상태: {response.status_code}")
    print(f"   응답 구조: {list(data.keys())}")
    
    if data.get("success") and data.get("persons"):
        persons = data["persons"]
        print(f"   담당자 개수: {len(persons)}")
        
        if persons:
            first_person = persons[0]
            print(f"   첫 번째 담당자 구조: {list(first_person.keys())}")
            print(f"   name 필드 존재: {'name' in first_person}")
            print(f"   실제 데이터: {first_person}")
    else:
        print("   ❌ 담당자 데이터 없음")
        
except Exception as e:
    print(f"   오류: {e}")

# 3. JavaScript 오류 패턴 분석
print("\n3️⃣ JavaScript 오류 패턴 분석")

print("   발견된 오류들:")
print("   - TypeError: Cannot read properties of undefined (reading 'role')")
print("   - admin_config.js:108 (editPeriod 함수)")
print("   - admin_config.js:254 (editManager 함수)")

print("\n   예상 원인:")
print("   1. API 응답에서 data.period 또는 data.person이 undefined")
print("   2. 응답 구조가 JavaScript에서 기대하는 것과 다름")
print("   3. 오류 처리가 없어 undefined 접근 시 크래시")

print("\n   해결 방향:")
print("   1. API 응답 구조 통일")
print("   2. JavaScript에서 안전한 접근 패턴 적용")
print("   3. admin_config.js 파일을 기능별로 분리")

print("\n🏁 분석 완료!") 