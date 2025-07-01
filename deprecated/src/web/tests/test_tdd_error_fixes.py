"""
TDD 오류 수정 테스트
==================

유효기간 클릭 시 발생하는 오류들을 TDD 방식으로 해결합니다.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

print("🧪 TDD 수정 사항 검증")

# 1. 404 핸들러 수정 확인
print("\n1️⃣ 404 핸들러 수정 확인")
try:
    import requests
    response = requests.get("http://localhost:8000/nonexistent-path")
    print(f"   ✅ 404 응답 상태: {response.status_code}")
    data = response.json()
    print(f"   ✅ 응답 구조: {list(data.keys())}")
except Exception as e:
    print(f"   ❌ 404 테스트 오류: {e}")

# 2. 유효기간 상세 API 구조 확인 (존재하는 ID 2 사용)
print("\n2️⃣ 유효기간 상세 API 구조 확인 (ID=2)")
try:
    response = requests.get("http://localhost:8000/api/admin/validity-periods/2")
    print(f"   ✅ 상태: {response.status_code}")
    data = response.json()
    print(f"   ✅ 키들: {list(data.keys())}")
    
    # JavaScript에서 기대하는 필드들
    expected_fields = ['role', 'days', 'description', 'active']
    all_present = True
    for field in expected_fields:
        if field in data:
            print(f"   ✅ {field}: {data[field]}")
        else:
            print(f"   ❌ {field}: 누락")
            all_present = False
    
    if all_present:
        print("   🎉 모든 필드가 JavaScript 기대 구조와 일치!")
    
except Exception as e:
    print(f"   ❌ 유효기간 상세 API 오류: {e}")

# 3. 담당자 상세 API도 테스트 (ID=1 시도)
print("\n3️⃣ 담당자 상세 API 구조 확인")
try:
    # 먼저 담당자 목록 확인
    response = requests.get("http://localhost:8000/api/admin/responsible-persons")
    persons_data = response.json()
    
    if persons_data.get("persons") and len(persons_data["persons"]) > 0:
        person_id = persons_data["persons"][0]["id"]
        print(f"   📋 첫 번째 담당자 ID: {person_id}")
        
        response = requests.get(f"http://localhost:8000/api/admin/responsible-persons/{person_id}")
        print(f"   ✅ 상태: {response.status_code}")
        data = response.json()
        
        if "role" in data:
            print(f"   ✅ role 필드 존재: {data['role']}")
        else:
            print("   ❌ role 필드 누락")
            
    else:
        print("   ℹ️  담당자 데이터가 없음")
        
except Exception as e:
    print(f"   ❌ 담당자 API 오류: {e}")

print("\n🏁 TDD 검증 완료!") 