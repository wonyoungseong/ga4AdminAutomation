#!/usr/bin/env python3
"""
GA4 권한 관리 시스템 - 템플릿 시스템 테스트
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.notifications.notification_service import NotificationService
from src.services.notifications.notification_types import NotificationType

async def test_template_system():
    """템플릿 시스템 테스트"""
    print("🧪 GA4 템플릿 시스템 테스트 시작")
    print("=" * 60)
    
    # 알림 서비스 초기화
    notification_service = NotificationService()
    
    # 테스트 데이터
    test_data = {
        'user_email': 'wonyoungseong@gmail.com',
        'email': 'wonyoungseong@gmail.com',
        'property_name': '[Edu]Ecommerce - Beauty Cosmetic',
        'property_id': '123456789',
        'role': 'editor',
        'expiry_date': datetime.now() + timedelta(days=7),
        'applicant': 'wonyoungseong@gmail.com',
        'test_type': 'template_test'
    }
    
    # 테스트할 알림 타입들
    test_types = [
        NotificationType.WELCOME,
        NotificationType.PENDING_APPROVAL,
        NotificationType.EDITOR_APPROVED,
        NotificationType.ADMIN_APPROVED,
        NotificationType.EXTENSION_APPROVED,
        NotificationType.TEST,
        NotificationType.EXPIRY_WARNING_7,
        NotificationType.EXPIRED
    ]
    
    success_count = 0
    total_count = len(test_types)
    
    for notification_type in test_types:
        try:
            print(f"\n🔄 테스트 중: {notification_type.value}")
            
            # 템플릿 생성 테스트
            subject, html_body, text_body = notification_service._generate_rich_email_content(
                notification_type, test_data
            )
            
            print(f"✅ 제목: {subject[:50]}...")
            print(f"✅ HTML 길이: {len(html_body)} 문자")
            print(f"✅ 텍스트 길이: {len(text_body)} 문자")
            
            # 기본 검증
            assert subject and len(subject) > 0, "제목이 비어있음"
            assert html_body and len(html_body) > 0, "HTML 내용이 비어있음"
            assert text_body and len(text_body) > 0, "텍스트 내용이 비어있음"
            
            success_count += 1
            print(f"✅ {notification_type.value} 템플릿 생성 성공")
            
        except Exception as e:
            print(f"❌ {notification_type.value} 템플릿 생성 실패: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 템플릿 테스트 결과: {success_count}/{total_count} 성공")
    
    if success_count == total_count:
        print("🎉 모든 템플릿이 정상적으로 작동합니다!")
        
        # 실제 이메일 발송 테스트
        print("\n📧 실제 이메일 발송 테스트 시작...")
        
        test_result = await notification_service.send_test_notification(
            email='wonyoungseong@gmail.com',
            notification_type='test'
        )
        
        if test_result:
            print("✅ 테스트 이메일 발송 성공!")
        else:
            print("❌ 테스트 이메일 발송 실패")
            
    else:
        print(f"⚠️ {total_count - success_count}개 템플릿에 문제가 있습니다.")
    
    print("\n🏁 템플릿 시스템 테스트 완료")

if __name__ == "__main__":
    asyncio.run(test_template_system()) 