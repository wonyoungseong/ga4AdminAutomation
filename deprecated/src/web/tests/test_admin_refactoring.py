"""
Admin 모듈 리팩토링 테스트
========================

TDD 방식으로 새로운 모듈 구조와 API 수정사항을 검증합니다.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

print("🧪 Admin 모듈 리팩토링 테스트 시작")

# 1. API 응답 구조 검증
print("\n1️⃣ API 응답 구조 수정 검증")
try:
    import requests
    
    # 유효기간 개별 조회 테스트
    response = requests.get("http://localhost:8000/api/admin/validity-periods")
    data = response.json()
    
    if data.get("success") and data.get("periods"):
        first_period_id = data["periods"][0]["id"]
        
        # 개별 조회 API 테스트
        detail_response = requests.get(f"http://localhost:8000/api/admin/validity-periods/{first_period_id}")
        detail_data = detail_response.json()
        
        print(f"   개별 조회 응답 구조: {list(detail_data.keys())}")
        
        if detail_data.get("success") and detail_data.get("period"):
            period = detail_data["period"]
            print(f"   ✅ 새로운 구조 확인: data.period.role = {period.get('role')}")
            print(f"   ✅ JavaScript 접근 가능: data.period.period_days = {period.get('period_days')}")
        else:
            print(f"   ❌ 응답 구조 문제: {detail_data}")
    
    # 담당자 개별 조회 테스트
    persons_response = requests.get("http://localhost:8000/api/admin/responsible-persons")
    persons_data = persons_response.json()
    
    if persons_data.get("success") and persons_data.get("persons"):
        first_person_id = persons_data["persons"][0]["id"]
        
        # 개별 조회 API 테스트
        person_detail_response = requests.get(f"http://localhost:8000/api/admin/responsible-persons/{first_person_id}")
        person_detail_data = person_detail_response.json()
        
        print(f"   담당자 개별 조회 구조: {list(person_detail_data.keys())}")
        
        if person_detail_data.get("success") and person_detail_data.get("person"):
            person = person_detail_data["person"]
            print(f"   ✅ 새로운 구조 확인: data.person.name = {person.get('name')}")
            print(f"   ✅ JavaScript 접근 가능: data.person.role = {person.get('role')}")
        else:
            print(f"   ❌ 담당자 응답 구조 문제: {person_detail_data}")
            
except Exception as e:
    print(f"   오류: {e}")

# 2. 파일 구조 검증
print("\n2️⃣ 리팩토링된 파일 구조 검증")

required_files = [
    "src/web/static/admin/utils.js",
    "src/web/static/admin/validity-periods.js", 
    "src/web/static/admin/responsible-persons.js",
    "src/web/static/admin/system-settings.js",
    "src/web/static/admin/main.js"
]

for file_path in required_files:
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"   ✅ {file_path} ({file_size} bytes)")
    else:
        print(f"   ❌ {file_path} 누락")

# 3. 모듈 분리 효과 검증
print("\n3️⃣ 모듈 분리 효과 분석")

original_file = "src/web/static/admin_config.js"
if os.path.exists(original_file):
    original_size = os.path.getsize(original_file)
    print(f"   기존 파일 크기: {original_size} bytes")
    
    total_new_size = sum(os.path.getsize(f) for f in required_files if os.path.exists(f))
    print(f"   새로운 파일들 총 크기: {total_new_size} bytes")
    
    if total_new_size > 0:
        improvement = ((original_size - total_new_size) / original_size) * 100
        print(f"   크기 변화: {improvement:.1f}% ({'감소' if improvement > 0 else '증가'})")
        
        print(f"\n   📊 분리 효과:")
        print(f"   - utils.js: 공통 기능 재사용")
        print(f"   - validity-periods.js: 유효기간 관리 전용")
        print(f"   - responsible-persons.js: 담당자 관리 전용") 
        print(f"   - system-settings.js: 시스템 설정 전용")
        print(f"   - main.js: 통합 관리자 (Facade 패턴)")

# 4. 웹 페이지 접근성 테스트
print("\n4️⃣ 웹 페이지 접근성 테스트")

try:
    admin_response = requests.get("http://localhost:8000/admin")
    print(f"   관리자 페이지 응답: {admin_response.status_code}")
    
    if admin_response.status_code == 200:
        # HTML 응답에서 새로운 스크립트 태그 확인
        html_content = admin_response.text
        script_includes = [
            "/static/admin/utils.js",
            "/static/admin/validity-periods.js", 
            "/static/admin/responsible-persons.js",
            "/static/admin/system-settings.js",
            "/static/admin/main.js"
        ]
        
        for script in script_includes:
            if script in html_content:
                print(f"   ✅ {script} 포함됨")
            else:
                print(f"   ❌ {script} 누락")
    
except Exception as e:
    print(f"   웹 페이지 테스트 오류: {e}")

print("\n🏁 Admin 모듈 리팩토링 테스트 완료!")
print("\n📝 예상 개선사항:")
print("   1. TypeError 오류 해결 (안전한 접근 패턴)")
print("   2. 모듈별 단일 책임 원칙 적용")
print("   3. 코드 재사용성 향상 (DRY 원칙)")
print("   4. 유지보수성 개선 (Clean Architecture)")
print("   5. 확장성 향상 (새로운 기능 추가 용이)") 