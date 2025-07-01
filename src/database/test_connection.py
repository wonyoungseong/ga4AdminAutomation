#!/usr/bin/env python3
"""
Supabase 연결 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def load_environment():
    """환경 변수 로드"""
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ 환경 변수가 설정되지 않았습니다.")
        print("SUPABASE_URL과 SUPABASE_ANON_KEY를 .env 파일에 설정해주세요.")
        return None, None
    
    return supabase_url, supabase_key

def test_connection(supabase: Client):
    """기본 연결 테스트"""
    try:
        # 간단한 쿼리로 연결 테스트
        result = supabase.table("website_users").select("count", count="exact").execute()
        print("✅ Supabase 연결 성공!")
        print(f"   website_users 테이블 레코드 수: {result.count}")
        return True
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False

def test_tables(supabase: Client):
    """테이블 존재 확인"""
    tables_to_check = [
        "website_users",
        "clients", 
        "service_accounts",
        "permission_grants",
        "audit_logs"
    ]
    
    print("\n📋 테이블 존재 확인:")
    for table_name in tables_to_check:
        try:
            result = supabase.table(table_name).select("count", count="exact").execute()
            print(f"   ✅ {table_name}: 존재함 (레코드 수: {result.count})")
        except Exception as e:
            print(f"   ❌ {table_name}: 없음 또는 오류 - {e}")

def main():
    """메인 함수"""
    print("🔄 Supabase 연결 테스트 시작...")
    
    # 환경 변수 로드
    supabase_url, supabase_key = load_environment()
    if not supabase_url or not supabase_key:
        sys.exit(1)
    
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase 클라이언트 생성 성공!")
    except Exception as e:
        print(f"❌ Supabase 클라이언트 생성 실패: {e}")
        sys.exit(1)
    
    # 연결 테스트
    if not test_connection(supabase):
        print("\n💡 힌트:")
        print("   1. .env 파일의 SUPABASE_URL과 SUPABASE_ANON_KEY 확인")
        print("   2. Supabase 프로젝트에 데이터베이스 스키마가 적용되었는지 확인")
        print("   3. 네트워크 연결 상태 확인")
        sys.exit(1)
    
    # 테이블 확인
    test_tables(supabase)
    
    print("\n🎉 모든 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main() 