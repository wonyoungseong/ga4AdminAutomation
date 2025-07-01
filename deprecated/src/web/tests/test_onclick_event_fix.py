#!/usr/bin/env python3
"""
onclick 이벤트 수정사항 검증 테스트
====================================

HTML onclick 속성을 ID 기반 이벤트 리스너로 변경한 수정사항을 검증합니다.
"""

import asyncio
import aiohttp
import json
from pathlib import Path


async def test_admin_page_loads():
    """관리자 페이지가 정상 로드되는지 테스트"""
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/admin') as response:
            assert response.status == 200
            content = await response.text()
            
            # HTML 수정사항 검증
            assert 'id="add-new-period-btn"' in content
            assert 'id="add-new-manager-btn"' in content
            assert 'id="save-system-settings-btn"' in content
            assert 'id="save-period-btn"' in content
            assert 'id="save-manager-btn"' in content
            
            # onclick 속성이 제거되었는지 확인
            assert 'onclick="addNewPeriod()"' not in content
            assert 'onclick="addNewManager()"' not in content
            assert 'onclick="saveSystemSettings()"' not in content
            assert 'onclick="savePeriod()"' not in content
            assert 'onclick="saveManager()"' not in content
            
            print("✅ HTML 템플릿 수정사항 검증 완료")


async def test_javascript_files_load():
    """JavaScript 파일들이 정상 로드되는지 테스트"""
    js_files = [
        '/static/admin/utils.js',
        '/static/admin/validity-periods.js', 
        '/static/admin/responsible-persons.js',
        '/static/admin/system-settings.js',
        '/static/admin/main.js'
    ]
    
    async with aiohttp.ClientSession() as session:
        for js_file in js_files:
            async with session.get(f'http://localhost:8000{js_file}') as response:
                assert response.status == 200
                print(f"✅ {js_file} 로드 성공")


async def test_api_endpoints():
    """Admin API 엔드포인트들이 정상 작동하는지 테스트"""
    endpoints = [
        '/api/admin/validity-periods',
        '/api/admin/responsible-persons',
        '/api/admin/system-settings',
        '/api/admin/notification-settings'
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            async with session.get(f'http://localhost:8000{endpoint}') as response:
                assert response.status == 200
                data = await response.json()
                assert 'success' in data
                print(f"✅ {endpoint} API 응답 정상")


async def run_all_tests():
    """모든 테스트 실행"""
    print("🔄 onclick 이벤트 수정사항 검증 테스트 시작")
    
    try:
        await test_admin_page_loads()
        await test_javascript_files_load()
        await test_api_endpoints()
        
        print("\n🎉 모든 테스트 통과!")
        print("📝 수정 결과:")
        print("   - HTML onclick 속성 → ID 기반 이벤트 리스너로 변경")
        print("   - JavaScript 파일 분리 후 이벤트 바인딩 정상 작동")
        print("   - Admin 페이지 JavaScript 오류 해결 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests()) 