#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 사용자 관리 종합 시나리오 테스트
=================================

사용자 등록 → 권한 상향 → 삭제 → 결과 리포트 발송까지의 전체 워크플로우를 테스트합니다.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.ga4_automation import GA4AutomationSystem
from src.core.email_validator import SmartEmailValidationSystem
from src.core.logger import get_logger

class GA4UserManagementScenario:
    """GA4 사용자 관리 종합 시나리오 테스트"""
    
    def __init__(self):
        self.logger = get_logger("USER_SCENARIO", "user_management_scenario.log")
        self.ga4_system = GA4AutomationSystem()
        self.email_validator = SmartEmailValidationSystem()
        self.test_results = []
        
        # 테스트 대상 이메일 목록
        self.test_emails = [
            "wonyoungseong@gmail.com",
            "wonyoung.seong@amorepacific.com", 
            "wonyoung.seong@concentrix.com",
            "wonyoungseong@concentrix.com"  # 이 계정은 존재하지 않음
        ]
        
        # 리포트 수신자
        self.report_recipient = "seongwonyoung0311@gmail.com"
    
    def run_complete_scenario(self):
        """전체 시나리오 실행"""
        self.logger.info("🚀 GA4 사용자 관리 종합 시나리오 테스트 시작")
        self.logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # 1단계: 이메일 검증
            validation_results = self._validate_all_emails()
            
            # 2단계: 유효한 계정만 필터링
            valid_emails = self._filter_valid_emails(validation_results)
            
            # 3단계: 사용자 등록
            registration_results = self._register_users(valid_emails)
            
            # 4단계: 권한 상향 (Analyst → Editor)
            upgrade_results = self._upgrade_user_permissions(valid_emails)
            
            # 5단계: 일부 사용자 삭제
            deletion_results = self._delete_users(valid_emails[:2])  # 처음 2명만 삭제
            
            # 6단계: 결과 리포트 생성 및 발송
            report_sent = self._send_comprehensive_report(
                validation_results, registration_results, 
                upgrade_results, deletion_results
            )
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info("✅ 종합 시나리오 테스트 완료")
            self.logger.info(f"⏱️ 총 소요 시간: {duration.total_seconds():.2f}초")
            
            return {
                'success': True,
                'duration': duration.total_seconds(),
                'validation_results': validation_results,
                'registration_results': registration_results,
                'upgrade_results': upgrade_results,
                'deletion_results': deletion_results,
                'report_sent': report_sent
            }
            
        except Exception as e:
            self.logger.error(f"❌ 시나리오 테스트 실패: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_all_emails(self) -> Dict:
        """모든 이메일 검증"""
        self.logger.info("📋 1단계: 이메일 검증 시작")
        
        validation_results = {}
        
        for email in self.test_emails:
            self.logger.info(f"🔍 검증 중: {email}")
            result = self.email_validator.validate_email_with_ga4(email)
            validation_results[email] = result
            
            status = "✅" if result['valid'] else "❌"
            self.logger.info(f"{status} {email}: {result['status']}")
        
        valid_count = sum(1 for r in validation_results.values() if r['valid'])
        self.logger.info(f"📊 검증 완료: {valid_count}/{len(self.test_emails)}개 유효")
        
        return validation_results
    
    def _filter_valid_emails(self, validation_results: Dict) -> List[str]:
        """유효한 이메일만 필터링"""
        valid_emails = [
            email for email, result in validation_results.items() 
            if result['valid'] and result['can_register']
        ]
        
        self.logger.info(f"✅ 등록 가능한 이메일: {len(valid_emails)}개")
        for email in valid_emails:
            self.logger.info(f"   - {email}")
        
        return valid_emails
    
    def _register_users(self, emails: List[str]) -> Dict:
        """사용자 등록"""
        self.logger.info("👥 2단계: 사용자 등록 시작")
        
        registration_results = {}
        
        for email in emails:
            self.logger.info(f"📝 등록 중: {email}")
            
            try:
                # Analyst 권한으로 등록
                result = self.ga4_system.add_user(
                    email=email,
                    role='predefinedRoles/analyst'
                )
                
                registration_results[email] = {
                    'success': True,
                    'role': 'analyst',
                    'message': '등록 성공'
                }
                
                self.logger.info(f"✅ {email} - Analyst 권한으로 등록 완료")
                
                # 잠시 대기 (API 제한 방지)
                time.sleep(1)
                
            except Exception as e:
                registration_results[email] = {
                    'success': False,
                    'error': str(e),
                    'message': '등록 실패'
                }
                
                self.logger.error(f"❌ {email} - 등록 실패: {str(e)}")
        
        success_count = sum(1 for r in registration_results.values() if r['success'])
        self.logger.info(f"📊 등록 완료: {success_count}/{len(emails)}개 성공")
        
        return registration_results
    
    def _upgrade_user_permissions(self, emails: List[str]) -> Dict:
        """권한 상향 (Analyst → Editor)"""
        self.logger.info("⬆️ 3단계: 권한 상향 시작")
        
        upgrade_results = {}
        
        for email in emails:
            self.logger.info(f"🔧 권한 상향 중: {email}")
            
            try:
                # 기존 권한 제거
                self.ga4_system.remove_user(email)
                time.sleep(1)
                
                # Editor 권한으로 재등록
                result = self.ga4_system.add_user(
                    email=email,
                    role='predefinedRoles/editor'
                )
                
                upgrade_results[email] = {
                    'success': True,
                    'old_role': 'analyst',
                    'new_role': 'editor',
                    'message': '권한 상향 성공'
                }
                
                self.logger.info(f"✅ {email} - Editor 권한으로 상향 완료")
                
                time.sleep(1)
                
            except Exception as e:
                upgrade_results[email] = {
                    'success': False,
                    'error': str(e),
                    'message': '권한 상향 실패'
                }
                
                self.logger.error(f"❌ {email} - 권한 상향 실패: {str(e)}")
        
        success_count = sum(1 for r in upgrade_results.values() if r['success'])
        self.logger.info(f"📊 권한 상향 완료: {success_count}/{len(emails)}개 성공")
        
        return upgrade_results
    
    def _delete_users(self, emails: List[str]) -> Dict:
        """사용자 삭제"""
        self.logger.info("🗑️ 4단계: 사용자 삭제 시작")
        
        deletion_results = {}
        
        for email in emails:
            self.logger.info(f"🗑️ 삭제 중: {email}")
            
            try:
                result = self.ga4_system.remove_user(email)
                
                deletion_results[email] = {
                    'success': True,
                    'message': '삭제 성공'
                }
                
                self.logger.info(f"✅ {email} - 삭제 완료")
                
                time.sleep(1)
                
            except Exception as e:
                deletion_results[email] = {
                    'success': False,
                    'error': str(e),
                    'message': '삭제 실패'
                }
                
                self.logger.error(f"❌ {email} - 삭제 실패: {str(e)}")
        
        success_count = sum(1 for r in deletion_results.values() if r['success'])
        self.logger.info(f"📊 삭제 완료: {success_count}/{len(emails)}개 성공")
        
        return deletion_results
    
    def _send_comprehensive_report(self, validation_results, registration_results, 
                                 upgrade_results, deletion_results) -> bool:
        """종합 결과 리포트 발송"""
        self.logger.info("📧 5단계: 결과 리포트 발송 시작")
        
        try:
            # 리포트 내용 생성
            report_content = self._generate_report_content(
                validation_results, registration_results,
                upgrade_results, deletion_results
            )
            
            # 이메일 발송
            success = self.email_validator.gmail_sender.send_email(
                recipient_email=self.report_recipient,
                subject="🔔 GA4 사용자 관리 시나리오 테스트 결과 리포트",
                text_content=report_content['text'],
                html_content=report_content['html']
            )
            
            if success:
                self.logger.info(f"✅ 결과 리포트 발송 성공: {self.report_recipient}")
            else:
                self.logger.error(f"❌ 결과 리포트 발송 실패: {self.report_recipient}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 리포트 발송 중 오류: {str(e)}")
            return False
    
    def _generate_report_content(self, validation_results, registration_results,
                               upgrade_results, deletion_results) -> Dict:
        """리포트 내용 생성"""
        
        # 통계 계산
        total_emails = len(self.test_emails)
        valid_emails = sum(1 for r in validation_results.values() if r['valid'])
        registered_users = sum(1 for r in registration_results.values() if r['success'])
        upgraded_users = sum(1 for r in upgrade_results.values() if r['success'])
        deleted_users = sum(1 for r in deletion_results.values() if r['success'])
        
        # 텍스트 버전
        text_content = f"""
GA4 사용자 관리 시나리오 테스트 결과 리포트
========================================

테스트 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 전체 통계:
- 검증 대상 이메일: {total_emails}개
- 유효한 계정: {valid_emails}개
- 등록 성공: {registered_users}개
- 권한 상향 성공: {upgraded_users}개
- 삭제 성공: {deleted_users}개

📋 상세 결과:

1. 이메일 검증 결과:
"""
        
        for email, result in validation_results.items():
            status = "✅ 유효" if result['valid'] else "❌ 무효"
            text_content += f"   - {email}: {status} ({result['status']})\n"
        
        text_content += "\n2. 사용자 등록 결과:\n"
        for email, result in registration_results.items():
            status = "✅ 성공" if result['success'] else "❌ 실패"
            text_content += f"   - {email}: {status}\n"
        
        text_content += "\n3. 권한 상향 결과:\n"
        for email, result in upgrade_results.items():
            status = "✅ 성공" if result['success'] else "❌ 실패"
            text_content += f"   - {email}: {status}\n"
        
        text_content += "\n4. 사용자 삭제 결과:\n"
        for email, result in deletion_results.items():
            status = "✅ 성공" if result['success'] else "❌ 실패"
            text_content += f"   - {email}: {status}\n"
        
        text_content += f"""
이 리포트는 GA4 자동화 시스템에서 자동으로 생성되었습니다.
시스템 버전: v2.0 (개선된 로깅 및 의존성 주입 적용)
"""
        
        # HTML 버전 (간단하게)
        html_content = text_content.replace('\n', '<br>').replace('   ', '&nbsp;&nbsp;&nbsp;')
        html_content = f"<html><body><pre>{html_content}</pre></body></html>"
        
        return {
            'text': text_content,
            'html': html_content
        }

def main():
    """메인 실행 함수"""
    print("🚀 GA4 사용자 관리 종합 시나리오 테스트 시작")
    print("=" * 60)
    
    scenario = GA4UserManagementScenario()
    results = scenario.run_complete_scenario()
    
    if results['success']:
        print("\n✅ 시나리오 테스트 성공!")
        print(f"⏱️ 총 소요 시간: {results['duration']:.2f}초")
        print(f"📧 리포트 발송: {'성공' if results['report_sent'] else '실패'}")
    else:
        print(f"\n❌ 시나리오 테스트 실패: {results['error']}")
    
    return results['success']

if __name__ == "__main__":
    main() 