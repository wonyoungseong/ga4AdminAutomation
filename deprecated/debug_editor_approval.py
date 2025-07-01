import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.notifications.notification_service import NotificationService
from services.notifications.notification_types import NotificationType
from datetime import datetime, timedelta

async def test_editor_approval_notification():
    """Editor 승인 알림 직접 테스트"""
    print("🧪 Editor 승인 알림 테스트 시작...")
    
    try:
        # NotificationService 초기화
        notification_service = NotificationService()
        
        # 테스트 데이터 준비
        test_data = {
            'user_email': 'debug_test@example.com',
            'email': 'debug_test@example.com',
            'property_name': 'Amorepacific GA4 테스트',
            'property_id': '462884506',
            'role': 'editor',
            'expiry_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'applicant': 'debug_test@example.com',
            'approved_at': datetime.now().isoformat()
        }
        
        print(f"📧 테스트 이메일: {test_data['user_email']}")
        print(f"📅 만료일: {test_data['expiry_date']}")
        
        # 1. 템플릿 생성 테스트
        print("\n🔄 1. 템플릿 생성 테스트...")
        try:
            print(f"📋 알림 타입: {NotificationType.EDITOR_APPROVED}")
            print(f"📋 데이터: {test_data}")
            
            subject, text_content, html_content = notification_service._generate_rich_email_content(
                NotificationType.EDITOR_APPROVED, test_data
            )
            
            print(f"📋 반환값: subject={bool(subject)}, text={bool(text_content)}, html={bool(html_content)}")
            
            if subject and html_content:
                print(f"✅ 템플릿 생성 성공")
                print(f"📬 제목: {subject[:50]}...")
                print(f"📄 HTML 길이: {len(html_content)} 문자")
            else:
                print(f"❌ 템플릿 생성 실패")
                print(f"  - subject: {subject}")
                print(f"  - html_content: {html_content}")
                return False
                
        except Exception as e:
            print(f"❌ 템플릿 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 2. Gmail 서비스 초기화 확인
        print("\n🔄 2. Gmail 서비스 확인...")
        try:
            email_service = notification_service.email_service
            print(f"✅ Gmail 서비스 객체: {type(email_service).__name__}")
        except Exception as e:
            print(f"❌ Gmail 서비스 오류: {e}")
            return False
        
        # 3. 실제 알림 발송 테스트
        print("\n🔄 3. Editor 승인 알림 발송 테스트...")
        success = await notification_service.send_editor_approved_notification(test_data)
        
        if success:
            print("✅ Editor 승인 알림 발송 성공!")
        else:
            print("❌ Editor 승인 알림 발송 실패")
        
        # 4. Welcome 알림도 테스트
        print("\n🔄 4. Welcome 알림 발송 테스트...")
        welcome_success = await notification_service.send_welcome_notification(test_data)
        
        if welcome_success:
            print("✅ Welcome 알림 발송 성공!")
        else:
            print("❌ Welcome 알림 발송 실패")
        
        return success and welcome_success
        
    except Exception as e:
        print(f"❌ 전체 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_editor_approval_notification())
    print(f"\n🎯 최종 결과: {'성공' if result else '실패'}") 