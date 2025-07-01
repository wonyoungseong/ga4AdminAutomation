#!/usr/bin/env python3
"""
사용자 등록 디버깅 시스템
======================

wonyoungseong@gmail.com 등록 프로세스를 상세히 추적하여
저장/조회/표시 과정에서 발생하는 문제를 진단합니다.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
import sqlite3
from pathlib import Path

# 로그 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_user_registration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UserRegistrationDebugger:
    """사용자 등록 디버깅 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_email = "wonyoungseong@gmail.com"
        self.test_data = {
            "신청자": "디버깅 테스트",
            "등록_계정_목록": self.test_email,
            "property_ids": ["462884506"],  # 기본 프로퍼티
            "권한": "viewer"
        }
        
    async def debug_full_registration_process(self):
        """전체 등록 프로세스 디버깅"""
        logger.info("🔍 === 사용자 등록 프로세스 디버깅 시작 ===")
        
        try:
            # 1. 사전 상태 확인
            await self._check_pre_registration_state()
            
            # 2. 등록 요청 실행
            registration_result = await self._execute_registration()
            
            # 3. 등록 후 상태 확인
            await self._check_post_registration_state()
            
            # 4. 사용자 목록 조회 테스트
            await self._test_user_list_retrieval()
            
            # 5. 데이터베이스 직접 확인
            await self._check_database_directly()
            
            # 6. 최종 진단
            await self._final_diagnosis()
            
        except Exception as e:
            logger.error(f"❌ 디버깅 프로세스 실패: {e}")
            
    async def _check_pre_registration_state(self):
        """등록 전 상태 확인"""
        logger.info("📋 1. 등록 전 상태 확인")
        
        # 기존 등록 확인
        existing_users = await self._get_users_from_api()
        existing_count = len(existing_users)
        logger.info(f"   📊 기존 등록 사용자 수: {existing_count}")
        
        # 테스트 이메일 기존 등록 확인
        existing_test_user = [u for u in existing_users if u.get('user_email') == self.test_email]
        if existing_test_user:
            logger.warning(f"   ⚠️ 테스트 이메일 기존 등록 발견: {existing_test_user}")
        else:
            logger.info(f"   ✅ 테스트 이메일 신규 등록 가능")
            
        # 서버 상태 확인
        server_status = await self._check_server_status()
        logger.info(f"   🖥️ 서버 상태: {server_status}")
        
    async def _execute_registration(self) -> Dict[str, Any]:
        """등록 요청 실행 및 상세 로그"""
        logger.info("📝 2. 사용자 등록 요청 실행")
        
        try:
            async with aiohttp.ClientSession() as session:
                # FormData 생성
                form_data = aiohttp.FormData()
                form_data.add_field('신청자', self.test_data['신청자'])
                form_data.add_field('등록_계정_목록', self.test_data['등록_계정_목록'])
                for prop_id in self.test_data['property_ids']:
                    form_data.add_field('property_ids', prop_id)
                form_data.add_field('권한', self.test_data['권한'])
                
                logger.info(f"   📤 요청 데이터: {self.test_data}")
                logger.info(f"   🌐 요청 URL: {self.base_url}/api/register")
                
                async with session.post(
                    f"{self.base_url}/api/register",
                    data=form_data
                ) as response:
                    status_code = response.status
                    response_text = await response.text()
                    
                    logger.info(f"   📊 응답 상태 코드: {status_code}")
                    logger.info(f"   📄 응답 헤더: {dict(response.headers)}")
                    
                    try:
                        response_data = json.loads(response_text)
                        logger.info(f"   📋 응답 데이터: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                    except json.JSONDecodeError:
                        logger.warning(f"   ⚠️ JSON 파싱 실패, 원본 응답: {response_text}")
                        response_data = {"raw_response": response_text}
                    
                    if status_code == 200:
                        logger.info("   ✅ 등록 요청 성공")
                    else:
                        logger.error(f"   ❌ 등록 요청 실패: {status_code}")
                        
                    return response_data
                    
        except Exception as e:
            logger.error(f"   ❌ 등록 요청 중 오류: {e}")
            return {"error": str(e)}
            
    async def _check_post_registration_state(self):
        """등록 후 상태 확인"""
        logger.info("🔍 3. 등록 후 상태 확인")
        
        # 잠시 대기 (비동기 처리 고려)
        await asyncio.sleep(2)
        
        # 사용자 목록 다시 조회
        users_after = await self._get_users_from_api()
        users_count_after = len(users_after)
        logger.info(f"   📊 등록 후 사용자 수: {users_count_after}")
        
        # 테스트 이메일 등록 확인
        test_user_registered = [u for u in users_after if u.get('user_email') == self.test_email]
        if test_user_registered:
            logger.info(f"   ✅ 테스트 사용자 등록 확인됨: {test_user_registered[0]}")
            return True
        else:
            logger.error(f"   ❌ 테스트 사용자 등록 확인 안됨")
            return False
            
    async def _test_user_list_retrieval(self):
        """사용자 목록 조회 테스트"""
        logger.info("📋 4. 사용자 목록 조회 테스트")
        
        # 다양한 방법으로 사용자 목록 조회
        await self._test_api_users_endpoint()
        await self._test_dashboard_data()
        await self._test_filtered_search()
        
    async def _test_api_users_endpoint(self):
        """API 사용자 엔드포인트 테스트"""
        logger.info("   🔗 /api/users 엔드포인트 테스트")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/users") as response:
                    status_code = response.status
                    response_data = await response.json()
                    
                    logger.info(f"      📊 상태 코드: {status_code}")
                    logger.info(f"      📄 응답 구조: {list(response_data.keys())}")
                    
                    if response_data.get('success'):
                        users = response_data.get('data', {}).get('users', [])
                        logger.info(f"      👥 조회된 사용자 수: {len(users)}")
                        
                        # 테스트 이메일 검색
                        test_user = [u for u in users if u.get('user_email') == self.test_email]
                        if test_user:
                            logger.info(f"      ✅ 테스트 사용자 발견: {test_user[0]}")
                        else:
                            logger.warning(f"      ⚠️ 테스트 사용자 미발견")
                            
                    else:
                        logger.error(f"      ❌ API 호출 실패: {response_data}")
                        
        except Exception as e:
            logger.error(f"      ❌ API 테스트 오류: {e}")
            
    async def _test_dashboard_data(self):
        """대시보드 데이터 테스트"""
        logger.info("   🏠 대시보드 데이터 테스트")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        html_content = await response.text()
                        if self.test_email in html_content:
                            logger.info(f"      ✅ 대시보드에서 테스트 사용자 발견")
                        else:
                            logger.warning(f"      ⚠️ 대시보드에서 테스트 사용자 미발견")
                    else:
                        logger.error(f"      ❌ 대시보드 로드 실패: {response.status}")
                        
        except Exception as e:
            logger.error(f"      ❌ 대시보드 테스트 오류: {e}")
            
    async def _test_filtered_search(self):
        """필터링 검색 테스트"""
        logger.info("   🔍 필터링 검색 테스트")
        
        search_params = [
            {"search": self.test_email},
            {"search": "wonyoungseong"},
            {"status": "active"},
            {"permission": "viewer"}
        ]
        
        for params in search_params:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}/api/users?" + "&".join([f"{k}={v}" for k, v in params.items()])
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            users = data.get('data', {}).get('users', [])
                            logger.info(f"      🔍 검색 '{params}': {len(users)}명 발견")
                            
                            test_user = [u for u in users if u.get('user_email') == self.test_email]
                            if test_user:
                                logger.info(f"         ✅ 테스트 사용자 포함됨")
                                
            except Exception as e:
                logger.error(f"      ❌ 검색 테스트 오류 '{params}': {e}")
                
    async def _check_database_directly(self):
        """데이터베이스 직접 확인"""
        logger.info("🗄️ 5. 데이터베이스 직접 확인")
        
        db_paths = [
            "ga4_admin.db",
            "src/infrastructure/ga4_admin.db",
            "data/ga4_admin.db"
        ]
        
        for db_path in db_paths:
            if Path(db_path).exists():
                logger.info(f"   📁 데이터베이스 파일 발견: {db_path}")
                await self._query_database_directly(db_path)
                break
        else:
            logger.warning("   ⚠️ 데이터베이스 파일을 찾을 수 없습니다")
            
    async def _query_database_directly(self, db_path: str):
        """데이터베이스 직접 쿼리"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"   📋 테이블 목록: {tables}")
            
            # user_registrations 테이블 확인
            if 'user_registrations' in tables:
                # 전체 등록 수
                cursor.execute("SELECT COUNT(*) FROM user_registrations")
                total_count = cursor.fetchone()[0]
                logger.info(f"   📊 전체 등록 수: {total_count}")
                
                # 테스트 이메일 검색
                cursor.execute(
                    "SELECT * FROM user_registrations WHERE 등록_계정 = ?",
                    (self.test_email,)
                )
                test_records = cursor.fetchall()
                
                if test_records:
                    logger.info(f"   ✅ 테스트 이메일 DB 레코드 발견: {len(test_records)}개")
                    for record in test_records:
                        record_dict = dict(record)
                        logger.info(f"      📝 레코드: {record_dict}")
                else:
                    logger.error(f"   ❌ 테스트 이메일 DB 레코드 미발견")
                    
                # 최근 등록 확인
                cursor.execute(
                    "SELECT * FROM user_registrations ORDER BY created_at DESC LIMIT 5"
                )
                recent_records = cursor.fetchall()
                logger.info(f"   📅 최근 등록 5건:")
                for record in recent_records:
                    record_dict = dict(record)
                    logger.info(f"      - {record_dict.get('등록_계정')} ({record_dict.get('created_at')})")
                    
            conn.close()
            
        except Exception as e:
            logger.error(f"   ❌ 데이터베이스 쿼리 오류: {e}")
            
    async def _final_diagnosis(self):
        """최종 진단"""
        logger.info("🏁 6. 최종 진단")
        
        # 모든 테스트 결과 종합
        final_check = await self._get_users_from_api()
        test_user_final = [u for u in final_check if u.get('user_email') == self.test_email]
        
        if test_user_final:
            logger.info("   ✅ 최종 결과: 사용자 등록 및 조회 성공")
            logger.info(f"   📋 등록된 사용자 정보: {test_user_final[0]}")
        else:
            logger.error("   ❌ 최종 결과: 사용자 등록 실패 또는 조회 문제")
            logger.info("   🔧 가능한 원인:")
            logger.info("      1. 등록 API 오류")
            logger.info("      2. 데이터베이스 저장 실패")
            logger.info("      3. 조회 API 오류")
            logger.info("      4. 캐싱 문제")
            logger.info("      5. 트랜잭션 롤백")
            
    async def _get_users_from_api(self) -> List[Dict[str, Any]]:
        """API에서 사용자 목록 조회"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/users") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('users', [])
                    else:
                        logger.error(f"사용자 목록 조회 실패: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"사용자 목록 조회 오류: {e}")
            return []
            
    async def _check_server_status(self) -> str:
        """서버 상태 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/health") as response:
                    if response.status == 200:
                        return "정상"
                    else:
                        return f"오류 ({response.status})"
        except Exception as e:
            return f"연결 실패 ({e})"

async def main():
    """메인 실행 함수"""
    debugger = UserRegistrationDebugger()
    await debugger.debug_full_registration_process()

if __name__ == "__main__":
    asyncio.run(main()) 