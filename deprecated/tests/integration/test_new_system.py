#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 테스트 스크립트
==================================

새로 구축한 시스템의 기본 기능을 테스트합니다.
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database import db_manager
from src.services.property_scanner_service import GA4PropertyScannerService
from src.core.logger import get_ga4_logger


async def test_database():
    """데이터베이스 기능 테스트"""
    logger = get_ga4_logger()
    logger.info("🧪 데이터베이스 테스트 시작")
    
    try:
        # 데이터베이스 초기화
        await db_manager.initialize_database()
        logger.info("✅ 데이터베이스 초기화 완료")
        
        # 통계 조회 테스트
        stats = await db_manager.get_database_stats()
        logger.info(f"📊 데이터베이스 통계: {stats}")
        
        # 테스트 데이터 삽입
        test_account_id = "test_account_123"
        await db_manager.execute_insert(
            """INSERT OR REPLACE INTO ga4_accounts 
               (account_id, account_display_name, 최초_확인일, 최근_업데이트일)
               VALUES (?, ?, datetime('now'), datetime('now'))""",
            (test_account_id, "테스트 계정")
        )
        logger.info("✅ 테스트 계정 데이터 삽입 완료")
        
        # 데이터 조회 테스트
        accounts = await db_manager.execute_query(
            "SELECT * FROM ga4_accounts WHERE account_id = ?",
            (test_account_id,)
        )
        logger.info(f"📋 조회된 계정: {accounts}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 테스트 실패: {e}")
        return False


async def test_property_scanner():
    """프로퍼티 스캐너 테스트"""
    logger = get_ga4_logger()
    logger.info("🧪 프로퍼티 스캐너 테스트 시작")
    
    try:
        # 스캐너 초기화
        scanner = GA4PropertyScannerService()
        logger.info("✅ 프로퍼티 스캐너 초기화 완료")
        
        # 등록 가능한 프로퍼티 조회 (DB에서)
        properties = await scanner.get_available_properties()
        logger.info(f"📋 등록 가능한 프로퍼티: {len(properties)}개")
        
        for prop in properties:
            logger.info(f"  - {prop.get('property_display_name', 'Unknown')} (ID: {prop.get('property_id', 'Unknown')})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 프로퍼티 스캐너 테스트 실패: {e}")
        return False


async def test_ga4_api_connection():
    """GA4 API 연결 테스트"""
    logger = get_ga4_logger()
    logger.info("🧪 GA4 API 연결 테스트 시작")
    
    try:
        scanner = GA4PropertyScannerService()
        
        # 실제 GA4 API 스캔 시도
        logger.info("🔍 GA4 계정/프로퍼티 스캔 시작...")
        result = await scanner.scan_all_accounts_and_properties()
        
        logger.info("✅ GA4 API 연결 및 스캔 완료")
        logger.info(f"📊 스캔 결과:")
        logger.info(f"  - 계정: {result.accounts_found}개 발견, {result.accounts_new}개 신규")
        logger.info(f"  - 프로퍼티: {result.properties_found}개 발견, {result.properties_new}개 신규")
        logger.info(f"  - 소요시간: {result.scan_duration:.2f}초")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ GA4 API 연결 테스트 실패: {e}")
        logger.error("   - Service Account 파일이 올바른 위치에 있는지 확인하세요.")
        logger.error("   - config/ga4-automatio-797ec352f393.json")
        return False


async def test_web_dependencies():
    """웹 의존성 테스트"""
    logger = get_ga4_logger()
    logger.info("🧪 웹 의존성 테스트 시작")
    
    try:
        # FastAPI import 테스트
        from fastapi import FastAPI
        logger.info("✅ FastAPI 임포트 성공")
        
        # Jinja2 import 테스트
        from jinja2 import Template
        logger.info("✅ Jinja2 임포트 성공")
        
        # 웹 모듈 import 테스트
        from src.web.main import app
        logger.info("✅ 웹 애플리케이션 임포트 성공")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 웹 의존성 테스트 실패: {e}")
        logger.error("   - requirements.txt의 패키지들이 설치되었는지 확인하세요.")
        return False


async def main():
    """메인 테스트 함수"""
    logger = get_ga4_logger()
    logger.info("🚀 GA4 권한 관리 시스템 종합 테스트 시작")
    logger.info("=" * 60)
    
    test_results = {}
    
    # 1. 데이터베이스 테스트
    test_results['database'] = await test_database()
    logger.info("")
    
    # 2. 웹 의존성 테스트
    test_results['web_dependencies'] = await test_web_dependencies()
    logger.info("")
    
    # 3. 프로퍼티 스캐너 테스트
    test_results['property_scanner'] = await test_property_scanner()
    logger.info("")
    
    # 4. GA4 API 연결 테스트 (선택적)
    try_api_test = input("GA4 API 연결 테스트를 수행하시겠습니까? (y/N): ").lower().strip()
    if try_api_test == 'y':
        test_results['ga4_api'] = await test_ga4_api_connection()
    else:
        test_results['ga4_api'] = None
        logger.info("⏭️ GA4 API 테스트 건너뜀")
    
    # 결과 요약
    logger.info("")
    logger.info("=" * 60)
    logger.info("📋 테스트 결과 요약")
    logger.info("=" * 60)
    
    passed = 0
    total = 0
    
    for test_name, result in test_results.items():
        if result is None:
            status = "⏭️ 건너뜀"
        elif result:
            status = "✅ 통과"
            passed += 1
            total += 1
        else:
            status = "❌ 실패"
            total += 1
        
        logger.info(f"{test_name:20}: {status}")
    
    logger.info("")
    logger.info(f"총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100 if total > 0 else 0:.1f}%)")
    
    if passed == total and total > 0:
        logger.info("🎉 모든 테스트가 성공했습니다!")
        logger.info("💡 이제 다음 명령으로 웹 서버를 시작할 수 있습니다:")
        logger.info("   python start_web_server.py")
    else:
        logger.info("⚠️ 일부 테스트가 실패했습니다. 문제를 해결한 후 다시 시도하세요.")


if __name__ == "__main__":
    asyncio.run(main()) 