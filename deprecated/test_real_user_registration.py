#!/usr/bin/env python3
"""
실제 사용자 등록 테스트
====================

wonyoungseong@gmail.com 등록 프로세스를 실시간으로 테스트하고
서버 로그를 확인합니다.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_user_registration():
    """실제 사용자 등록 테스트"""
    
    print(f"\n🔍 === 실제 사용자 등록 테스트 시작 ({datetime.now()}) ===")
    
    # 테스트 데이터
    test_data = {
        '신청자': '실시간 디버깅 테스트',
        '등록_계정_목록': 'wonyoungseong@gmail.com',
        'property_ids': ['462884506'],  # Beauty Cosmetic 
        '권한': 'viewer'
    }
    
    print(f"📤 등록 요청 데이터:")
    for key, value in test_data.items():
        print(f"   - {key}: {value}")
    
    async with aiohttp.ClientSession() as session:
        try:
            print(f"\n🌐 등록 요청 전송 중...")
            
            # FormData로 전송
            form_data = aiohttp.FormData()
            for key, value in test_data.items():
                if isinstance(value, list):
                    for item in value:
                        form_data.add_field(key, item)
                else:
                    form_data.add_field(key, value)
            
            async with session.post(
                'http://localhost:8000/api/register',
                data=form_data
            ) as response:
                print(f"📊 응답 상태: {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    print(f"📋 응답 데이터:")
                    print(json.dumps(response_data, indent=2, ensure_ascii=False))
                    
                    # 결과 분석
                    if response_data.get('success'):
                        results = response_data.get('data', {}).get('results', [])
                        for result in results:
                            print(f"\n✅ 처리 결과:")
                            print(f"   - 이메일: {result.get('email')}")
                            print(f"   - 프로퍼티: {result.get('property_id')}")
                            print(f"   - 상태: {result.get('status')}")
                            print(f"   - 메시지: {result.get('message', 'N/A')}")
                            print(f"   - 등록 ID: {result.get('registration_id', 'N/A')}")
                    else:
                        print(f"❌ 등록 실패: {response_data.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP 오류: {response.status}")
                    print(f"   응답: {error_text}")
                    
        except Exception as e:
            print(f"❌ 요청 실패: {e}")
    
    print(f"\n🔍 === 테스트 완료 ({datetime.now()}) ===")

if __name__ == "__main__":
    asyncio.run(test_user_registration()) 