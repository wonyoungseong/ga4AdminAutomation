#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 자동화 시스템 메인 실행 파일
==============================

Usage:
    python main.py --validate-email user@example.com
    python main.py --add-user user@example.com --role analyst
    python main.py --run-qa-test
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core import SmartEmailValidationSystem, GmailOAuthSender
from src.core.logger import setup_logging, get_logger

def validate_email_command(email: str):
    """이메일 검증 명령"""
    print(f"🔍 이메일 검증 시작: {email}")
    
    validator = SmartEmailValidationSystem()
    result = validator.validate_email_with_ga4(email)
    
    print(f"📧 결과: {result['status']}")
    print(f"💬 메시지: {result['message']}")
    
    return result['status'] == 'VALID_GOOGLE_ACCOUNT'

def run_qa_test_command():
    """QA 테스트 실행 명령"""
    print("🧪 QA 테스트 시작...")
    
    # 여러 이메일로 테스트
    test_emails = [
        'seongwonyoung0311@gmail.com',
        'definitely.does.not.exist@invalid-domain.com',
        'test@naver.com'
    ]
    
    validator = SmartEmailValidationSystem()
    results = {}
    
    for email in test_emails:
        print(f"  테스트 중: {email}")
        result = validator.validate_email_with_ga4(email)
        results[email] = result
        print(f"    → {result['status']}")
    
    # 결과 이메일 발송
    print("📧 결과 이메일 발송 중...")
    success = validator.send_validation_results_email(
        results, 
        'wonyoungseong@gmail.com'
    )
    
    if success:
        print("✅ QA 테스트 완료 및 결과 이메일 발송 성공")
    else:
        print("❌ 결과 이메일 발송 실패")
    
    return success

def main():
    """메인 함수"""
    setup_logging()
    logger = get_logger("MAIN")
    
    parser = argparse.ArgumentParser(
        description='GA4 자동화 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py --validate-email user@example.com
  python main.py --run-qa-test
        """
    )
    
    parser.add_argument(
        '--validate-email',
        help='이메일 주소 검증'
    )
    
    parser.add_argument(
        '--run-qa-test',
        action='store_true',
        help='QA 테스트 실행'
    )
    
    args = parser.parse_args()
    
    if args.validate_email:
        success = validate_email_command(args.validate_email)
        sys.exit(0 if success else 1)
    
    elif args.run_qa_test:
        success = run_qa_test_command()
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main() 