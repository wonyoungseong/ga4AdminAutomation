"""
애플리케이션 설정 관리
환경 변수를 로드하고 설정을 중앙화합니다.
"""

import os
from typing import List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # Pydantic v2 설정
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # 추가 환경변수 무시
    )
    
    # 애플리케이션 기본 설정
    app_name: str = "GA4 Admin Automation"
    app_version: str = "0.1.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API 설정
    api_v1_prefix: str = "/api/v1"
    
    # CORS 설정
    allowed_origins: List[str] = [
        "http://localhost:3000",  # React 개발 서버
        "http://localhost:8080",  # Vue 개발 서버
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    # Supabase 설정
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # 보안 설정
    secret_key: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "jwt-fallback-secret-key-change-in-production")
    
    # 서버 설정
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))


# 전역 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스를 반환하는 의존성 함수"""
    return settings 