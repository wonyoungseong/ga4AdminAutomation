#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 Phase 2 테스트
===================

기본 기능들만 테스트하는 간단한 스크립트입니다.
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database import db_manager
from src.core.logger import get_ga4_logger

logger = get_ga4_logger()


async def simple_test():
    """간단한 기능 테스트"""
    
    print("🚀 간단한 Phase 2 테스트 시작")
    print("=" * 40)
    
    try:
        # 1. 데이터베이스 초기화
        print("📊 1. 데이터베이스 초기화")
        await db_manager.initialize_database()
        print("✅ 성공")
        
        # 2. 데이터베이스 통계
        print("\n📈 2. 데이터베이스 통계")
        stats = await db_manager.get_database_stats()
        for table, count in stats.items():
            print(f"   - {table}: {count}건")
        
        # 3. GA4 사용자 관리자 import 테스트
        print("\n🔧 3. GA4 사용자 관리자 import 테스트")
        try:
            from src.services.ga4_user_manager import ga4_user_manager
            print("✅ import 성공")
        except Exception as e:
            print(f"❌ import 실패: {e}")
            return False
        
        # 4. 웹 서버 상태 확인
        print("\n🌐 4. 웹 서버 상태 확인")
        import subprocess
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8000"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0 and result.stdout == "200":
                print("✅ 웹 서버 정상 작동")
                print("📍 접속 주소: http://localhost:8000")
            else:
                print("⚠️ 웹 서버 상태 확인 불가")
        except Exception as e:
            print(f"⚠️ 웹 서버 상태 확인 실패: {e}")
        
        print("\n" + "=" * 40)
        print("🎉 간단한 테스트 완료!")
        
        print("\n🚀 다음 단계:")
        print("1. 웹 브라우저에서 http://localhost:8000 접속")
        print("2. 대시보드 확인")
        print("3. 사용자 등록 테스트")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        logger.error(f"간단한 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(simple_test())
    sys.exit(0 if success else 1) 