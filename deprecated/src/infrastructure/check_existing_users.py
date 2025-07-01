#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현재 GA4 사용자 목록 확인
=======================

현재 GA4에 등록된 모든 사용자와 권한을 확인합니다.
"""

import json
import os
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient

def check_current_users():
    """현재 GA4 사용자 목록 조회"""
    print("🔍 현재 GA4 사용자 목록 확인")
    print("=" * 50)
    
    try:
        # 설정 로드
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # GA4 클라이언트 초기화
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'ga4-automatio-797ec352f393.json'
        client = AnalyticsAdminServiceClient()
        account_name = f"accounts/{config['account_id']}"
        
        # 사용자 목록 조회
        bindings = client.list_access_bindings(parent=account_name)
        
        print(f"📊 총 {len(list(bindings))} 개의 사용자가 등록되어 있습니다.\n")
        
        # 다시 조회 (iterator는 한 번만 사용 가능)
        bindings = client.list_access_bindings(parent=account_name)
        
        for i, binding in enumerate(bindings, 1):
            user_email = binding.user.replace("users/", "")
            roles = [role.split('/')[-1] for role in binding.roles]
            
            print(f"👤 사용자 {i}: {user_email}")
            print(f"   🎯 권한: {', '.join(roles)}")
            print(f"   📋 바인딩 ID: {binding.name}")
            print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_current_users()
