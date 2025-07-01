#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 사용자 권한 변경 테스트
===========================

이미 GA4에 등록된 사용자의 권한을 변경하는 테스트
"""

import json
import os
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding

def test_permission_change():
    """기존 사용자 권한 변경 테스트"""
    print("🔄 기존 사용자 권한 변경 테스트")
    print("=" * 50)
    
    try:
        # 설정 로드
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # GA4 클라이언트 초기화
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'ga4-automatio-797ec352f393.json'
        client = AnalyticsAdminServiceClient()
        account_name = f"accounts/{config['account_id']}"
        
        # 테스트할 사용자
        test_email = "seongwonyoung0311@gmail.com"
        
        print(f"�� 테스트 대상: {test_email}")
        print(f"🔄 Admin → Viewer → Admin 순서로 권한 변경 테스트\n")
        
        # 1. 현재 상태 확인
        print("1️⃣ 현재 권한 상태 확인...")
        bindings = client.list_access_bindings(parent=account_name)
        current_binding = None
        
        for binding in bindings:
            if binding.user == f"users/{test_email}":
                current_binding = binding
                roles = [role.split('/')[-1] for role in binding.roles]
                print(f"   현재 권한: {', '.join(roles)}")
                break
        
        if not current_binding:
            print(f"   ❌ {test_email} 사용자를 찾을 수 없습니다.")
            return
        
        # 2. Viewer 권한으로 변경
        print("\n2️⃣ Viewer 권한으로 변경...")
        
        # 기존 바인딩 삭제
        client.delete_access_binding(name=current_binding.name)
        print("   ✅ 기존 Admin 권한 제거됨")
        
        # 새로운 Viewer 권한 추가
        new_binding = AccessBinding(
            user=f"users/{test_email}",
            roles=["predefinedRoles/read"]
        )
        
        response = client.create_access_binding(
            parent=account_name,
            access_binding=new_binding
        )
        print("   ✅ Viewer 권한 부여됨")
        print(f"   📋 새 바인딩 ID: {response.name}")
        
        # 3. 권한 확인
        print("\n3️⃣ 변경된 권한 확인...")
        bindings = client.list_access_bindings(parent=account_name)
        
        for binding in bindings:
            if binding.user == f"users/{test_email}":
                roles = [role.split('/')[-1] for role in binding.roles]
                print(f"   현재 권한: {', '.join(roles)}")
                break
        
        # 4. 다시 Admin 권한으로 복구
        print("\n4️⃣ Admin 권한으로 복구...")
        
        # Viewer 권한 삭제
        client.delete_access_binding(name=response.name)
        print("   ✅ Viewer 권한 제거됨")
        
        # Admin 권한 복구
        admin_binding = AccessBinding(
            user=f"users/{test_email}",
            roles=["predefinedRoles/manage"]
        )
        
        final_response = client.create_access_binding(
            parent=account_name,
            access_binding=admin_binding
        )
        print("   ✅ Admin 권한 복구됨")
        print(f"   📋 최종 바인딩 ID: {final_response.name}")
        
        # 5. 최종 확인
        print("\n5️⃣ 최종 권한 상태 확인...")
        bindings = client.list_access_bindings(parent=account_name)
        
        for binding in bindings:
            if binding.user == f"users/{test_email}":
                roles = [role.split('/')[-1] for role in binding.roles]
                print(f"   최종 권한: {', '.join(roles)}")
                break
        
        print("\n🎉 권한 변경 테스트 완료!")
        print("✅ 시스템이 정상적으로 작동합니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_permission_change()
