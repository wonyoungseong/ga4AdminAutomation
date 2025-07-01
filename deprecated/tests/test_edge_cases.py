#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 자동화 시스템 오류 메시지 및 예외 상황 QA 테스트
==============================================

오류 메시지가 예상대로 나오는지, 시스템이 예외 상황을 적절히 처리하는지 테스트합니다.
"""

import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Tuple
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, CreateAccessBindingRequest
from google.oauth2 import service_account

class ErrorMessageQATest:
    """오류 메시지 및 예외 상황 QA 테스트"""
    
    def __init__(self):
        self.config = self._load_config()
        self._setup_logging()
        self._init_client()
        self.test_results = []
    
    def _load_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _setup_logging(self):
        log_formatter = logging.Formatter(
            '%(asctime)s - ERROR_QA - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler('error_qa_test.log', encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        
        self.logger = logging.getLogger('ERROR_QA')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _init_client(self):
        """Service Account 클라이언트 초기화"""
        service_account_file = 'ga4-automatio-797ec352f393.json'
        
        scopes = [
            'https://www.googleapis.com/auth/analytics.edit',
            'https://www.googleapis.com/auth/analytics.manage.users',
            'https://www.googleapis.com/auth/analytics.readonly'
        ]
        
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        
        self.client = AnalyticsAdminServiceClient(credentials=credentials)
        self.logger.info("✅ 오류 테스트용 클라이언트 초기화 완료")
    
    def add_test_result(self, test_name: str, expected_error: str, actual_error: str, 
                       passed: bool, details: str = ""):
        """테스트 결과 기록"""
        result = {
            'test_name': test_name,
            'expected_error': expected_error,
            'actual_error': actual_error,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        self.logger.info(f"{status} | {test_name}")
        self.logger.info(f"    Expected Error: {expected_error}")
        self.logger.info(f"    Actual Error: {actual_error}")
        if details:
            self.logger.info(f"    Details: {details}")
    
    def test_404_error_messages(self):
        """404 오류 메시지 테스트"""
        
        self.logger.info("🧪 404 오류 메시지 테스트 시작")
        self.logger.info("=" * 60)
        
        test_cases = [
            {
                'email': 'nonexistent@invalid-domain.com',
                'description': '존재하지 않는 도메인',
                'expected_keyword': '404'
            },
            {
                'email': 'fake.user@gmail.com',
                'description': '존재하지 않는 Gmail 사용자',
                'expected_keyword': 'could not be found'
            },
            {
                'email': 'invalid@',
                'description': '잘못된 이메일 형식',
                'expected_keyword': '404'
            },
            {
                'email': '@invalid.com',
                'description': '@ 앞부분 누락',
                'expected_keyword': '404'
            }
        ]
        
        for case in test_cases:
            self.logger.info(f"테스트: {case['description']} - {case['email']}")
            
            try:
                success, error_msg = self._add_user_test(case['email'], "analyst")
                
                # 실패해야 하고, 예상 키워드가 포함되어야 함
                has_expected_keyword = case['expected_keyword'].lower() in error_msg.lower()
                test_passed = not success and has_expected_keyword
                
                self.add_test_result(
                    f"404 오류 - {case['description']}",
                    f"실패 및 '{case['expected_keyword']}' 포함",
                    f"실패: {not success}, 키워드 포함: {has_expected_keyword}",
                    test_passed,
                    f"오류 메시지: {error_msg[:100]}..."
                )
                
            except Exception as e:
                # 예외가 발생해도 적절한 오류 메시지가 있어야 함
                error_msg = str(e)
                has_expected_keyword = case['expected_keyword'].lower() in error_msg.lower()
                
                self.add_test_result(
                    f"404 오류 (예외) - {case['description']}",
                    f"예외 발생 및 '{case['expected_keyword']}' 포함",
                    f"예외: {type(e).__name__}, 키워드 포함: {has_expected_keyword}",
                    has_expected_keyword,
                    f"예외 메시지: {error_msg[:100]}..."
                )
    
    def test_permission_error_simulation(self):
        """권한 오류 시뮬레이션 테스트"""
        
        self.logger.info("🧪 권한 오류 시뮬레이션 테스트 시작")
        self.logger.info("=" * 60)
        
        # 잘못된 Property ID로 테스트
        original_property_id = self.config['property_id']
        
        try:
            # 존재하지 않는 Property ID로 변경
            self.config['property_id'] = '999999999'
            
            success, error_msg = self._add_user_test("wonyoungseong@gmail.com", "analyst")
            
            # 권한 관련 오류 키워드 확인
            permission_keywords = ['permission', 'denied', 'not found', '403', '404']
            has_permission_error = any(keyword in error_msg.lower() for keyword in permission_keywords)
            
            self.add_test_result(
                "잘못된 Property ID 오류",
                "권한 또는 404 오류",
                f"실패: {not success}, 권한 오류: {has_permission_error}",
                not success and has_permission_error,
                f"오류 메시지: {error_msg}"
            )
            
        finally:
            # 원래 Property ID 복원
            self.config['property_id'] = original_property_id
    
    def test_network_timeout_simulation(self):
        """네트워크 타임아웃 시뮬레이션 테스트"""
        
        self.logger.info("🧪 네트워크 및 연결 안정성 테스트 시작")
        self.logger.info("=" * 60)
        
        # 빠른 연속 요청으로 API 제한 테스트
        rapid_requests = []
        
        for i in range(5):
            start_time = time.time()
            try:
                success, error_msg = self._add_user_test("wonyoungseong@gmail.com", "analyst")
                end_time = time.time()
                
                rapid_requests.append({
                    'request_num': i + 1,
                    'success': success,
                    'response_time': end_time - start_time,
                    'error': error_msg if not success else None
                })
                
                # 추가 성공 시 즉시 제거
                if success:
                    self._remove_user_test("wonyoungseong@gmail.com")
                
            except Exception as e:
                end_time = time.time()
                rapid_requests.append({
                    'request_num': i + 1,
                    'success': False,
                    'response_time': end_time - start_time,
                    'error': str(e)
                })
        
        # 결과 분석
        avg_response_time = sum(req['response_time'] for req in rapid_requests) / len(rapid_requests)
        success_count = sum(1 for req in rapid_requests if req['success'])
        
        # 적어도 일부는 성공하고, 평균 응답 시간이 합리적이어야 함
        reasonable_performance = avg_response_time < 10.0  # 10초 이내
        some_success = success_count > 0
        
        self.add_test_result(
            "연속 요청 안정성",
            "일부 성공 및 합리적 응답 시간",
            f"성공: {success_count}/5, 평균 응답시간: {avg_response_time:.2f}초",
            reasonable_performance and some_success,
            f"상세: {rapid_requests}"
        )
    
    def test_data_validation_errors(self):
        """데이터 유효성 검사 오류 테스트"""
        
        self.logger.info("🧪 데이터 유효성 검사 오류 테스트 시작")
        self.logger.info("=" * 60)
        
        validation_test_cases = [
            {
                'email': None,
                'role': 'analyst',
                'description': 'None 이메일',
                'expected_error': 'TypeError'
            },
            {
                'email': 'valid@gmail.com',
                'role': None,
                'description': 'None 권한',
                'expected_error': '기본값 처리'
            },
            {
                'email': 123,
                'role': 'analyst',
                'description': '숫자 이메일',
                'expected_error': 'TypeError'
            },
            {
                'email': 'test@gmail.com',
                'role': 123,
                'description': '숫자 권한',
                'expected_error': '기본값 처리'
            }
        ]
        
        for case in validation_test_cases:
            self.logger.info(f"테스트: {case['description']}")
            
            try:
                success, error_msg = self._add_user_test(case['email'], case['role'])
                
                if case['expected_error'] == '기본값 처리':
                    # 기본값으로 처리되어 성공하거나 적절한 오류
                    test_passed = True  # 크래시하지 않으면 성공
                else:
                    # 특정 오류 타입이 예상됨
                    test_passed = not success
                
                self.add_test_result(
                    f"데이터 유효성 - {case['description']}",
                    case['expected_error'],
                    f"성공: {success}, 오류: {error_msg[:50] if error_msg else 'None'}",
                    test_passed,
                    f"입력: email={case['email']}, role={case['role']}"
                )
                
            except Exception as e:
                # 예외 발생 - 예상된 경우
                expected_exception = case['expected_error'] in str(type(e).__name__)
                
                self.add_test_result(
                    f"데이터 유효성 (예외) - {case['description']}",
                    case['expected_error'],
                    f"예외: {type(e).__name__}",
                    expected_exception,
                    f"예외 메시지: {str(e)[:100]}"
                )
    
    def test_error_message_clarity(self):
        """오류 메시지 명확성 테스트"""
        
        self.logger.info("🧪 오류 메시지 명확성 테스트 시작")
        self.logger.info("=" * 60)
        
        # 실제로 실패할 것으로 예상되는 케이스들
        error_clarity_cases = [
            {
                'email': 'definitely.nonexistent.user@gmail.com',
                'description': '명확히 존재하지 않는 사용자',
                'required_info': ['404', 'not found', 'email']
            },
            {
                'email': 'test@nonexistent-domain-12345.com',
                'description': '존재하지 않는 도메인',
                'required_info': ['404', 'not found']
            }
        ]
        
        for case in error_clarity_cases:
            self.logger.info(f"테스트: {case['description']}")
            
            success, error_msg = self._add_user_test(case['email'], "analyst")
            
            # 오류 메시지에 필요한 정보가 포함되어 있는지 확인
            info_present = []
            for info in case['required_info']:
                if info.lower() in error_msg.lower():
                    info_present.append(info)
            
            clarity_score = len(info_present) / len(case['required_info'])
            test_passed = not success and clarity_score >= 0.5  # 50% 이상의 정보 포함
            
            self.add_test_result(
                f"오류 메시지 명확성 - {case['description']}",
                f"실패 및 필요 정보 포함 ({case['required_info']})",
                f"실패: {not success}, 정보 포함률: {clarity_score:.1%}",
                test_passed,
                f"포함된 정보: {info_present}, 오류: {error_msg}"
            )
    
    def test_system_recovery(self):
        """시스템 복구 능력 테스트"""
        
        self.logger.info("🧪 시스템 복구 능력 테스트 시작")
        self.logger.info("=" * 60)
        
        # 1. 실패 후 정상 작업 가능 여부
        self.logger.info("1. 실패 후 정상 작업 복구 테스트")
        
        # 의도적으로 실패시키기
        fail_success, fail_error = self._add_user_test("nonexistent@invalid.com", "analyst")
        
        # 이후 정상 작업 시도
        normal_success, normal_error = self._add_user_test("wonyoungseong@gmail.com", "analyst")
        
        recovery_success = not fail_success and normal_success
        
        self.add_test_result(
            "실패 후 정상 작업 복구",
            "실패 후 정상 작업 성공",
            f"실패: {not fail_success}, 복구 성공: {normal_success}",
            recovery_success,
            f"실패 오류: {fail_error}, 복구 결과: {normal_error}"
        )
        
        # 정상 작업 정리
        if normal_success:
            self._remove_user_test("wonyoungseong@gmail.com")
    
    def _add_user_test(self, email, role) -> Tuple[bool, str]:
        """사용자 추가 테스트 헬퍼"""
        if email is None or not isinstance(email, str):
            return False, f"Invalid email type: {type(email)}"
        
        if role is None:
            role = "analyst"  # 기본값 처리
        elif not isinstance(role, str):
            role = "analyst"  # 기본값 처리
        
        parent = f"properties/{self.config['property_id']}"
        
        role_mapping = {
            'analyst': 'predefinedRoles/analyst',
            'editor': 'predefinedRoles/editor', 
            'admin': 'predefinedRoles/admin',
            'viewer': 'predefinedRoles/viewer'
        }
        
        predefined_role = role_mapping.get(role.lower(), 'predefinedRoles/analyst')
        
        try:
            access_binding = AccessBinding(
                user=email,
                roles=[predefined_role]
            )
            
            request = CreateAccessBindingRequest(
                parent=parent,
                access_binding=access_binding
            )
            
            response = self.client.create_access_binding(request=request)
            return True, response.name
            
        except Exception as e:
            return False, str(e)
    
    def _remove_user_test(self, email: str) -> bool:
        """사용자 제거 테스트 헬퍼"""
        try:
            binding_id = self._find_user_binding_id(email)
            
            if not binding_id:
                return False
            
            self.client.delete_access_binding(name=binding_id)
            return True
            
        except Exception as e:
            self.logger.error(f"사용자 제거 실패: {email} - {str(e)}")
            return False
    
    def _find_user_binding_id(self, email: str) -> str:
        """사용자 바인딩 ID 찾기"""
        parent = f"properties/{self.config['property_id']}"
        
        try:
            response = self.client.list_access_bindings(parent=parent)
            
            for binding in response:
                if binding.user == email:
                    return binding.name
            
            return None
            
        except Exception as e:
            self.logger.error(f"바인딩 ID 검색 실패: {str(e)}")
            return None
    
    def generate_error_report(self):
        """오류 테스트 보고서 생성"""
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("📊 GA4 자동화 시스템 오류 메시지 QA 보고서")
        self.logger.info("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.logger.info(f"📈 오류 처리 테스트 결과:")
        self.logger.info(f"   총 테스트: {total_tests}개")
        self.logger.info(f"   성공: {passed_tests}개")
        self.logger.info(f"   실패: {failed_tests}개")
        self.logger.info(f"   성공률: {success_rate:.1f}%")
        
        if failed_tests > 0:
            self.logger.info(f"\n❌ 실패한 오류 처리 테스트:")
            for result in self.test_results:
                if not result['passed']:
                    self.logger.info(f"   - {result['test_name']}")
                    self.logger.info(f"     예상: {result['expected_error']}")
                    self.logger.info(f"     실제: {result['actual_error']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate
        }
    
    def run_all_error_tests(self):
        """모든 오류 테스트 실행"""
        
        self.logger.info("🚀 GA4 자동화 시스템 오류 메시지 QA 테스트 시작")
        self.logger.info("=" * 80)
        
        start_time = time.time()
        
        try:
            # 404 오류 메시지 테스트
            self.test_404_error_messages()
            
            # 권한 오류 시뮬레이션
            self.test_permission_error_simulation()
            
            # 네트워크 타임아웃 시뮬레이션
            self.test_network_timeout_simulation()
            
            # 데이터 유효성 검사 오류
            self.test_data_validation_errors()
            
            # 오류 메시지 명확성
            self.test_error_message_clarity()
            
            # 시스템 복구 능력
            self.test_system_recovery()
            
        except Exception as e:
            self.logger.error(f"오류 테스트 실행 중 예외 발생: {str(e)}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        self.logger.info(f"\n⏱️ 총 오류 테스트 시간: {total_time:.2f}초")
        
        # 보고서 생성
        report = self.generate_error_report()
        
        return report

def main():
    """메인 함수"""
    
    error_qa = ErrorMessageQATest()
    
    print("🧪 GA4 자동화 시스템 오류 메시지 QA 테스트를 시작합니다...")
    print("테스트 결과는 error_qa_test.log 파일에 저장됩니다.")
    
    report = error_qa.run_all_error_tests()
    
    print(f"\n📊 오류 테스트 완료!")
    print(f"성공률: {report['success_rate']:.1f}% ({report['passed_tests']}/{report['total_tests']})")
    
    if report['failed_tests'] > 0:
        print(f"⚠️ {report['failed_tests']}개의 오류 처리 테스트가 실패했습니다.")
    else:
        print("🎉 모든 오류 처리 테스트가 성공했습니다!")

if __name__ == "__main__":
    main() 