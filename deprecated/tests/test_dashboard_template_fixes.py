#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드 템플릿 오류 수정 테스트
============================

대시보드 템플릿에서 발생하는 오류들을 테스트하고 수정
"""

import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_dashboard_data_structure():
    """대시보드 데이터 구조 테스트"""
    try:
        from src.web.main import get_dashboard_data
        
        # 대시보드 데이터 가져오기
        dashboard_data = await get_dashboard_data()
        
        # 필요한 키들이 있는지 확인
        required_keys = [
            'properties', 'registrations', 'stats', 
            'notification_stats', 'recent_logs'
        ]
        
        for key in required_keys:
            assert key in dashboard_data, f"대시보드 데이터에 '{key}' 키가 없습니다"
        
        # properties 데이터 구조 확인
        if dashboard_data['properties']:
            for prop in dashboard_data['properties']:
                assert isinstance(prop, dict), "property는 dict 타입이어야 합니다"
                # 필요한 속성들이 있는지 확인
                required_prop_keys = ['property_id', 'property_display_name', 'last_updated']
                for prop_key in required_prop_keys:
                    if prop_key not in prop:
                        print(f"⚠️ property에 '{prop_key}' 키가 없습니다: {prop}")
        
        # registrations 데이터 구조 확인
        if dashboard_data['registrations']:
            for reg in dashboard_data['registrations']:
                assert isinstance(reg, dict), "registration은 dict 타입이어야 합니다"
                # 필요한 속성들이 있는지 확인
                required_reg_keys = ['등록_계정', 'property_display_name', 'status', 'created_at']
                for reg_key in required_reg_keys:
                    if reg_key not in reg:
                        print(f"⚠️ registration에 '{reg_key}' 키가 없습니다: {reg}")
        
        print("✅ 대시보드 데이터 구조 확인 완료")
        return True
        
    except Exception as e:
        print(f"❌ 대시보드 데이터 구조 확인 실패: {e}")
        return False


async def test_dashboard_template_rendering():
    """대시보드 템플릿 렌더링 테스트"""
    try:
        from fastapi.testclient import TestClient
        from src.web.main import app
        
        client = TestClient(app)
        
        # 대시보드 페이지 요청
        response = client.get("/")
        
        # 응답 상태 확인
        if response.status_code != 200:
            print(f"❌ 대시보드 페이지 응답 오류: {response.status_code}")
            print(f"응답 내용: {response.text[:500]}")
            return False
        
        # HTML 내용 확인
        html_content = response.text
        
        # 기본 HTML 구조 확인
        required_elements = [
            '<html', '<head>', '<body>', '</html>',
            'GA4 권한 관리 시스템', 'dashboard'
        ]
        
        for element in required_elements:
            if element not in html_content:
                print(f"❌ HTML에 '{element}' 요소가 없습니다")
                return False
        
        print("✅ 대시보드 템플릿 렌더링 확인 완료")
        return True
        
    except Exception as e:
        print(f"❌ 대시보드 템플릿 렌더링 확인 실패: {e}")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("🔧 대시보드 템플릿 오류 수정 테스트 시작...")
    
    # 비동기 테스트들
    test1 = asyncio.run(test_dashboard_data_structure())
    test2 = asyncio.run(test_dashboard_template_rendering())
    
    if all([test1, test2]):
        print("🎉 모든 테스트 통과!")
        return True
    else:
        print("❌ 일부 테스트 실패")
        return False


if __name__ == "__main__":
    run_all_tests() 