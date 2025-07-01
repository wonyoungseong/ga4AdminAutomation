#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 권한 관리 시스템 웹 서버 시작 스크립트
=========================================

웹 인터페이스를 시작하는 메인 스크립트입니다.
"""

import asyncio
import sys
import os
import uvicorn
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database import db_manager
from src.core.logger import get_ga4_logger


async def initialize_system():
    """시스템 초기화"""
    logger = get_ga4_logger()
    
    try:
        logger.info("🚀 GA4 권한 관리 시스템 초기화 시작")
        
        # 필수 디렉토리 생성
        directories = [
            "data",
            "logs", 
            "src/web/static",
            "src/web/templates",
            "backups"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 디렉토리 생성: {directory}")
        
        # 데이터베이스 초기화
        await db_manager.initialize_database()
        
        logger.info("✅ 시스템 초기화 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 시스템 초기화 실패: {e}")
        return False


def main():
    """메인 함수"""
    logger = get_ga4_logger()
    
    # 시스템 초기화
    init_success = asyncio.run(initialize_system())
    if not init_success:
        logger.error("❌ 시스템 초기화 실패로 인해 서버를 시작할 수 없습니다.")
        sys.exit(1)
    
    # 웹 서버 설정
    config = {
        "app": "src.web.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
        "log_level": "info",
        "access_log": True
    }
    
    logger.info("🌐 웹 서버 시작")
    logger.info(f"📍 접속 주소: http://localhost:{config['port']}")
    logger.info("🔧 개발 모드 (자동 재시작 활성화)")
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        logger.info("⏹️ 서버가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"❌ 서버 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 