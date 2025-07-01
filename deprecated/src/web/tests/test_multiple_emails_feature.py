"""
여러 시스템 이메일 기능 테스트
============================

TDD 방식으로 여러 이메일 처리 기능을 검증합니다.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

print("🧪 여러 시스템 이메일 기능 테스트")

# 1. 여러 이메일 저장 테스트
print("\n1️⃣ 여러 이메일 저장 테스트")
try:
    import requests
    
    # 여러 이메일을 쉼표로 구분하여 저장
    test_emails = "admin1@test.com, admin2@test.com, admin3@test.com"
    
    settings_data = {
        "auto_approval_viewer": "true",
        "auto_approval_analyst": "true", 
        "auto_approval_editor": "false",
        "notification_batch_size": "50",
        "max_extension_count": "3",
        "system_email": test_emails
    }
    
    response = requests.put("http://localhost:8000/api/admin/system-settings", 
                           json=settings_data)
    
    if response.status_code == 200:
        print(f"   ✅ 여러 이메일 저장 성공: {test_emails}")
        
        # 저장된 데이터 확인
        get_response = requests.get("http://localhost:8000/api/admin/system-settings")
        if get_response.status_code == 200:
            data = get_response.json()
            saved_email = data["settings"]["system_email"]
            print(f"   ✅ 저장 확인: {saved_email}")
            
            # 이메일 개수 확인
            email_count = len([email.strip() for email in saved_email.split(',') if email.strip()])
            print(f"   ✅ 저장된 이메일 개수: {email_count}개")
            
    else:
        print(f"   ❌ 저장 실패: {response.status_code}")
        
except Exception as e:
    print(f"   오류: {e}")

# 2. 줄바꿈으로 구분된 이메일 테스트
print("\n2️⃣ 줄바꿈 구분 이메일 처리 테스트")
try:
    # 줄바꿈으로 구분된 이메일 (JavaScript에서 처리될 형태)
    newline_emails = "manager1@company.com\nmanager2@company.com\nmanager3@company.com"
    
    # JavaScript의 processMultipleEmails 함수와 동일한 로직
    import re
    emails = re.split(r'[\n,]', newline_emails)
    emails = [email.strip() for email in emails if email.strip()]
    
    print(f"   입력: {repr(newline_emails)}")
    print(f"   ✅ 파싱된 이메일 개수: {len(emails)}개")
    
    for i, email in enumerate(emails):
        print(f"     {i+1}. {email}")
        
    # 이메일 유효성 검사
    import re
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    valid_emails = [email for email in emails if re.match(email_regex, email)]
    
    print(f"   ✅ 유효한 이메일 개수: {len(valid_emails)}개")
    
except Exception as e:
    print(f"   오류: {e}")

# 3. 중복 이메일 제거 테스트
print("\n3️⃣ 중복 이메일 제거 테스트")
try:
    duplicate_emails = "test@example.com, test@example.com, unique@example.com"
    emails = [email.strip() for email in duplicate_emails.split(',') if email.strip()]
    unique_emails = list(set(emails))  # 중복 제거
    
    print(f"   입력: {duplicate_emails}")
    print(f"   ✅ 중복 제거 전: {len(emails)}개")
    print(f"   ✅ 중복 제거 후: {len(unique_emails)}개")
    
except Exception as e:
    print(f"   오류: {e}")

# 4. 원래 이메일로 복원 (정리)
print("\n4️⃣ 원래 설정으로 복원")
try:
    original_settings = {
        "auto_approval_viewer": "true",
        "auto_approval_analyst": "true", 
        "auto_approval_editor": "false",
        "notification_batch_size": "50",
        "max_extension_count": "3",
        "system_email": "wonyoungseong@gmail.com"
    }
    
    response = requests.put("http://localhost:8000/api/admin/system-settings", 
                           json=original_settings)
    
    if response.status_code == 200:
        print("   ✅ 원래 설정으로 복원 완료")
    else:
        print(f"   ❌ 복원 실패: {response.status_code}")
        
except Exception as e:
    print(f"   오류: {e}")

print("\n🏁 여러 이메일 기능 테스트 완료!") 