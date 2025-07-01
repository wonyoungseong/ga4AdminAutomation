import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.notifications.email_templates import EmailTemplateManager
from datetime import datetime, timedelta

def test_editor_approved_template():
    """Editor 승인 템플릿 직접 테스트"""
    print("🧪 Editor 승인 템플릿 직접 테스트...")
    
    try:
        # 테스트 데이터
        user_email = 'template_test@example.com'
        property_name = 'Amorepacific GA4 테스트'
        property_id = '462884506'
        expiry_date = datetime.now() + timedelta(days=7)
        applicant = 'template_test@example.com'
        
        print(f"📧 사용자: {user_email}")
        print(f"🏢 프로퍼티: {property_name}")
        print(f"📅 만료일: {expiry_date}")
        print(f"👤 신청자: {applicant}")
        
        # 템플릿 생성
        print("\n🔄 템플릿 생성 중...")
        subject, text_content, html_content = EmailTemplateManager.create_editor_approved_email(
            user_email=user_email,
            property_name=property_name,
            property_id=property_id,
            expiry_date=expiry_date,
            applicant=applicant
        )
        
        if subject and text_content and html_content:
            print("✅ 템플릿 생성 성공!")
            print(f"📬 제목: {subject}")
            print(f"📄 텍스트 길이: {len(text_content)} 문자")
            print(f"📄 HTML 길이: {len(html_content)} 문자")
            
            # HTML 일부 출력
            print(f"\n📋 HTML 미리보기 (첫 200자):")
            print(html_content[:200] + "...")
            
            return True
        else:
            print("❌ 템플릿 생성 실패")
            print(f"  - subject: {bool(subject)}")
            print(f"  - text_content: {bool(text_content)}")  
            print(f"  - html_content: {bool(html_content)}")
            return False
            
    except Exception as e:
        print(f"❌ 템플릿 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_editor_approved_template()
    print(f"\n🎯 템플릿 테스트 결과: {'성공' if result else '실패'}") 