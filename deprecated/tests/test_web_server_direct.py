#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 서버 직접 테스트
================

웹 서버를 직접 실행하여 오류를 확인
"""

import sys
import os
import asyncio

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_web_server_startup():
    """웹 서버 시작 테스트"""
    try:
        print("🔧 웹 서버 시작 테스트 중...")
        
        # 필요한 모듈들 import
        from src.web.main import app
        from src.api.scheduler import scheduler_service, ga4_scheduler
        
        print("✅ 모든 모듈 import 성공")
        
        # 스케줄러 초기화
        await scheduler_service.initialize()
        print("✅ 스케줄러 초기화 성공")
        
        # FastAPI 앱 확인
        print(f"✅ FastAPI 앱: {app}")
        print(f"✅ 스케줄러 서비스: {scheduler_service}")
        
        print("🎉 웹 서버 시작 준비 완료")
        
    except Exception as e:
        print(f"❌ 웹 서버 시작 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(test_web_server_startup()) 