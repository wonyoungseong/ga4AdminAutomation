#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GA4 자동화 스케줄러 시스템
========================

대기 중인 사용자들을 주기적으로 확인하고 자동으로 권한을 부여합니다.
"""

import json
import schedule
import time
import sqlite3
from datetime import datetime, timedelta
from smtp_notification_system import SMTPNotificationSystem
from complete_ga4_user_automation import CompleteGA4UserAutomation, UserRole

class GA4AutomationScheduler:
    """GA4 자동화 스케줄러"""
    
    def __init__(self):
        self.config = self.load_config()
        self.notification_system = SMTPNotificationSystem()
        self.property_id = self.config.get('property_id')
        self.automation = CompleteGA4UserAutomation()
        self.db_path = "complete_ga4_automation.db"
    
    def load_config(self):
        """설정 파일 로드"""
        with open('config.json', 'r') as f:
            return json.load(f)
    
    def daily_expiry_check(self):
        """매일 만료 예정 사용자 확인 및 알림 발송"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📅 일일 만료 확인 시작")
        
        # 7일, 3일, 1일 전 알림
        self.notification_system.check_expiring_users_with_smtp(
            notification_days=[7, 3, 1]
        )
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ 일일 만료 확인 완료")
    
    def daily_user_cleanup(self):
        """매일 만료된 사용자 제거"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🗑️  만료 사용자 정리 시작")
        
        self.notification_system.remove_expired_users_with_notification(
            self.property_id
        )
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ 만료 사용자 정리 완료")
    
    def weekly_report(self):
        """주간 리포트 생성"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📊 주간 리포트 생성 시작")
        
        # 주간 리포트 로직 (필요시 구현)
        print("주간 사용자 관리 리포트를 생성합니다...")
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ 주간 리포트 생성 완료")
    
    def setup_schedule(self):
        """스케줄 설정"""
        # 매일 오전 9시에 만료 확인 및 알림
        schedule.every().day.at("09:00").do(self.daily_expiry_check)
        
        # 매일 자정에 만료된 사용자 정리
        schedule.every().day.at("00:00").do(self.daily_user_cleanup)
        
        # 매주 월요일 오전 10시에 주간 리포트
        schedule.every().monday.at("10:00").do(self.weekly_report)
        
        print("✅ 스케줄 설정 완료:")
        print("   - 매일 09:00: 만료 예정 사용자 알림")
        print("   - 매일 00:00: 만료된 사용자 제거")
        print("   - 매주 월요일 10:00: 주간 리포트")
    
    def run_scheduler(self):
        """스케줄러 실행"""
        self.setup_schedule()
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 GA4 자동화 스케줄러 시작")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 확인
    
    def check_and_retry_pending_users(self):
        """대기 중인 사용자들 확인 및 재시도"""
        print(f"🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 대기 사용자 확인 시작")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 5분 이상 대기 중인 사용자들 조회
        cursor.execute('''
            SELECT email, target_role, invited_at FROM user_management 
            WHERE status = 'pending' AND invited_at < ?
        ''', ((datetime.now() - timedelta(minutes=5)).isoformat(),))
        
        pending_users = cursor.fetchall()
        conn.close()
        
        if not pending_users:
            print("   ✅ 대기 중인 사용자가 없습니다.")
            return
        
        print(f"   📋 대기 중인 사용자 {len(pending_users)}명 발견")
        
        successful_count = 0
        for email, role_value, invited_at in pending_users:
            try:
                role = UserRole(role_value)
                print(f"   🎯 {email} 재시도 중...")
                
                api_success, api_message = self.automation.try_direct_api_addition(email, role)
                
                if api_success:
                    self._update_user_status(email, 'completed')
                    successful_count += 1
                    print(f"   ✅ {email} 권한 부여 성공!")
                    
                    # 성공 알림 이메일 발송
                    self._send_success_notification(email, role)
                else:
                    print(f"   ⏳ {email} 여전히 대기 중: {api_message}")
                    
            except Exception as e:
                print(f"   ❌ {email} 처리 중 오류: {e}")
        
        print(f"   📊 재시도 결과: {successful_count}/{len(pending_users)} 성공")
        print("-" * 50)
    
    def _update_user_status(self, email: str, status: str):
        """사용자 상태 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_management 
            SET status = ?, accepted_at = ?, last_updated = ?
            WHERE email = ?
        ''', (status, datetime.now().isoformat(), datetime.now().isoformat(), email))
        
        conn.commit()
        conn.close()
    
    def _send_success_notification(self, email: str, role: UserRole):
        """성공 알림 이메일 발송"""
        try:
            subject = f"[GA4 자동화] 권한 부여 완료 - {email}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #28a745;">✅ Google Analytics 4 권한 부여 완료</h2>
                    
                    <p>안녕하세요,</p>
                    
                    <p><strong>{email}</strong> 계정에 Google Analytics 4 권한이 성공적으로 부여되었습니다!</p>
                    
                    <div style="background-color: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                        <h3 style="margin-top: 0; color: #155724;">🎉 권한 부여 완료</h3>
                        <ul>
                            <li><strong>계정:</strong> BETC</li>
                            <li><strong>속성:</strong> [Edu]Ecommerce - Beauty Cosmetic</li>
                            <li><strong>권한 수준:</strong> {role.name}</li>
                            <li><strong>완료 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #1a73e8;">🚀 이제 사용 가능한 기능</h3>
                        <ul>
                            <li>Google Analytics 4 데이터 조회</li>
                            <li>리포트 및 분석 기능</li>
                            <li>대시보드 생성 및 공유</li>
                            <li>자동화된 권한 관리</li>
                        </ul>
                    </div>
                    
                    <p>이제 <a href="https://analytics.google.com" target="_blank">Google Analytics</a>에 접속하여 모든 기능을 사용하실 수 있습니다.</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px;">
                        이 메일은 GA4 자동화 시스템에서 발송되었습니다.<br>
                        발송일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            success, message = self.automation.send_invitation_email(email, role)
            if success:
                print(f"   📧 {email}에게 완료 알림 발송 성공")
            else:
                print(f"   ❌ {email} 완료 알림 발송 실패: {message}")
                
        except Exception as e:
            print(f"   ❌ {email} 완료 알림 처리 중 오류: {e}")
    
    def cleanup_old_logs(self):
        """오래된 로그 정리"""
        print(f"🧹 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 로그 정리 시작")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 30일 이상 된 로그 삭제
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        cursor.execute('DELETE FROM automation_log WHERE timestamp < ?', (cutoff_date,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {deleted_count}개의 오래된 로그 삭제 완료")

def manual_test_mode():
    """수동 테스트 모드"""
    scheduler = GA4AutomationScheduler()
    
    print("=== 🧪 수동 테스트 모드 ===\n")
    
    while True:
        print("\\n선택하세요:")
        print("1. 만료 예정 사용자 확인 및 알림")
        print("2. 만료된 사용자 정리")
        print("3. 주간 리포트 생성")
        print("4. 스케줄러 시작")
        print("5. 종료")
        
        choice = input("\\n선택 (1-5): ").strip()
        
        if choice == '1':
            scheduler.daily_expiry_check()
        elif choice == '2':
            scheduler.daily_user_cleanup()
        elif choice == '3':
            scheduler.weekly_report()
        elif choice == '4':
            print("스케줄러를 시작합니다. (Ctrl+C로 중단)")
            try:
                scheduler.run_scheduler()
            except KeyboardInterrupt:
                print("\\n스케줄러가 중단되었습니다.")
        elif choice == '5':
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")

def main():
    """메인 실행 함수"""
    scheduler = GA4AutomationScheduler()
    
    try:
        scheduler.run_scheduler()
    except KeyboardInterrupt:
        print("\n🛑 스케줄러가 중단되었습니다.")
    except Exception as e:
        print(f"❌ 스케줄러 오류: {e}")

if __name__ == "__main__":
    print("GA4 자동화 스케줄러")
    print("\\n실행 모드를 선택하세요:")
    print("1. 자동 스케줄 모드")
    print("2. 수동 테스트 모드")
    
    mode = input("\\n선택 (1-2): ").strip()
    
    if mode == '1':
        main()
    elif mode == '2':
        manual_test_mode()
    else:
        print("잘못된 선택입니다.") 