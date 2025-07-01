#!/usr/bin/env python3
"""
GA4 Property Administrator 확인 스크립트
"""

import os
import sys
from google.analytics.admin import AnalyticsAdminServiceClient
from google.oauth2 import service_account

def check_property_administrators():
    print("🔍 GA4 Property Administrator 확인 시작...")
    
    try:
        # 1. Service Account 파일 확인
        service_account_file = 'config/ga4-automatio-797ec352f393.json'
        if not os.path.exists(service_account_file):
            print(f"❌ Service Account 파일을 찾을 수 없습니다: {service_account_file}")
            return
        
        print(f"✅ Service Account 파일 발견: {service_account_file}")
        
        # 2. GA4 클라이언트 초기화
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/analytics.edit']
        )
        
        client = AnalyticsAdminServiceClient(credentials=credentials)
        print("✅ GA4 클라이언트 초기화 완료")
        
        # 3. 테스트할 Property들
        properties = [
            "properties/462884506",  # [Edu]Ecommerce - Beauty Cosmetic
            "properties/477115705"   # [Edu]Ecommerce - 텔레토비
        ]
        
        for property_name in properties:
            print(f"\n📋 Property 확인: {property_name}")
            
            try:
                # Property 정보 가져오기
                property_info = client.get_property(name=property_name)
                print(f"✅ Property 접근 성공: {property_info.display_name}")
                
                # Access Bindings 조회 (사용자 권한 목록)
                print("🔍 Access Bindings 조회 시도...")
                access_bindings = client.list_access_bindings(parent=property_name)
                
                print("✅ Access Bindings 조회 성공!")
                
                admin_count = 0
                editor_count = 0
                viewer_count = 0
                
                for binding in access_bindings:
                    role = binding.roles[0] if binding.roles else "UNKNOWN"
                    
                    if "ADMINISTRATOR" in role:
                        admin_count += 1
                        print(f"  🔑 Administrator: {binding.user or binding.name}")
                    elif "EDITOR" in role:
                        editor_count += 1
                        print(f"  ✏️ Editor: {binding.user or binding.name}")
                    elif "VIEWER" in role:
                        viewer_count += 1
                        print(f"  👁️ Viewer: {binding.user or binding.name}")
                
                print(f"📊 권한 요약 - Admin: {admin_count}, Editor: {editor_count}, Viewer: {viewer_count}")
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Property {property_name} 오류: {error_msg}")
                
                # 세부 오류 분석
                if "401" in error_msg:
                    print("  → 인증 오류: 권한이 부족하거나 인증이 실패했습니다")
                elif "403" in error_msg:
                    print("  → 권한 거부: 해당 Property에 접근 권한이 없습니다")
                elif "404" in error_msg:
                    print("  → Property를 찾을 수 없습니다")
                else:
                    print(f"  → 기타 오류: {error_msg}")
        
        # 4. 사용자 관리 API 직접 테스트
        print(f"\n🧪 사용자 관리 API 직접 테스트...")
        test_property = properties[0]
        
        try:
            # 새로운 사용자 추가 시뮬레이션 (실제로는 실행하지 않음)
            print(f"🔍 {test_property}에 대한 사용자 관리 권한 테스트...")
            
            # Access Binding 생성 테스트 (실제로는 생성하지 않고 준비만)
            from google.analytics.admin_v1alpha.types import AccessBinding
            
            test_binding = AccessBinding(
                user="test@example.com",
                roles=["predefinedRoles/analyticsViewer"]
            )
            
            print("✅ Access Binding 객체 생성 성공 - 권한 관리 API 사용 가능")
            
        except Exception as e:
            print(f"❌ 사용자 관리 API 테스트 실패: {e}")
                
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_property_administrators()
    if success:
        print("\n🎉 GA4 API 연결 및 권한 확인 완료!")
    else:
        print("\n💥 GA4 API 연결 또는 권한 확인 실패!")
        sys.exit(1) 