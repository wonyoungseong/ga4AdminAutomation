#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 기능 테스트
==================

새로 구현된 GA4 사용자 관리 기능들을 테스트합니다.
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database import db_manager
from src.services.ga4_user_manager import ga4_user_manager
from src.core.logger import get_ga4_logger

logger = get_ga4_logger()


async def test_phase2_features():
    """Phase 2 기능들 테스트"""
    
    print("🚀 Phase 2 기능 테스트 시작")
    print("=" * 50)
    
    try:
        # 1. 데이터베이스 초기화
        print("📊 1. 데이터베이스 초기화 테스트")
        await db_manager.initialize_database()
        print("✅ 데이터베이스 초기화 성공")
        
        # 2. GA4 사용자 관리자 초기화
        print("\n🔧 2. GA4 사용자 관리자 초기화 테스트")
        await ga4_user_manager.initialize()
        print("✅ GA4 사용자 관리자 초기화 성공")
        
        # 3. 등록 대기열 처리 테스트
        print("\n⏳ 3. 등록 대기열 처리 테스트")
        await ga4_user_manager.process_registration_queue()
        print("✅ 등록 대기열 처리 완료")
        
        # 4. 만료 처리 테스트
        print("\n📅 4. 만료 처리 테스트")
        await ga4_user_manager.process_expiration_queue()
        print("✅ 만료 처리 완료")
        
        # 5. 데이터베이스 통계 확인
        print("\n📈 5. 데이터베이스 통계 확인")
        stats = await db_manager.get_database_stats()
        print(f"   - GA4 계정: {stats.get('ga4_accounts', 0)}개")
        print(f"   - GA4 프로퍼티: {stats.get('ga4_properties', 0)}개")
        print(f"   - 사용자 등록: {stats.get('user_registrations', 0)}건")
        print(f"   - 알림 로그: {stats.get('notification_logs', 0)}건")
        print(f"   - 감사 로그: {stats.get('audit_logs', 0)}건")
        
        # 6. 프로퍼티별 사용자 조회 테스트 (첫 번째 프로퍼티가 있는 경우)
        print("\n👥 6. 프로퍼티 사용자 조회 테스트")
        properties = await db_manager.execute_query(
            "SELECT property_id FROM ga4_properties LIMIT 1"
        )
        
        if properties:
            property_id = properties[0]['property_id']
            users = await ga4_user_manager.list_property_users(property_id)
            print(f"   - 프로퍼티 {property_id}: {len(users)}명의 사용자")
            for user in users[:3]:  # 처음 3명만 표시
                print(f"     * {user.get('email', 'N/A')} ({', '.join(user.get('roles', []))})")
        else:
            print("   - 테스트할 프로퍼티가 없습니다")
        
        print("\n" + "=" * 50)
        print("🎉 Phase 2 기능 테스트 완료!")
        print("✅ 모든 핵심 기능이 정상적으로 작동합니다.")
        
        # 7. 웹 서버 상태 확인
        print("\n🌐 7. 웹 서버 상태 확인")
        import subprocess
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/api/stats"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("✅ 웹 서버가 정상적으로 실행 중입니다")
                print("📍 접속 주소: http://localhost:8000")
            else:
                print("⚠️ 웹 서버에 접속할 수 없습니다")
        except Exception as e:
            print(f"⚠️ 웹 서버 상태 확인 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        logger.error(f"Phase 2 테스트 실패: {e}")
        return False


async def main():
    """메인 함수"""
    success = await test_phase2_features()
    
    if success:
        print("\n🚀 다음 단계 안내:")
        print("1. 웹 브라우저에서 http://localhost:8000 접속")
        print("2. 대시보드에서 새로운 관리 버튼들 확인")
        print("3. 사용자 등록 페이지에서 실제 등록 테스트")
        print("4. 대기열 처리 버튼으로 GA4 실제 등록 테스트")
        
        print("\n📋 추가 개발 예정 기능:")
        print("- Gmail 알림 시스템")
        print("- 자동 스케줄링 시스템")
        print("- 고급 권한 관리")
        print("- 대시보드 UI 개선")
        
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 