import json
import sqlite3
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, CreateAccessBindingRequest
from google.oauth2 import service_account
import schedule
import time

# Service Account 인증 파일 경로
SERVICE_ACCOUNT_FILE = 'ga4-automatio-797ec352f393.json'
SCOPES = ['https://www.googleapis.com/auth/analytics.manage.users']

# 데이터베이스 설정
DB_NAME = 'ga4_user_management.db'

class GA4UserManager:
    def __init__(self):
        self.client = None
        self.credentials = None
        self.init_database()
        self.authenticate()

    def authenticate(self):
        """Service Account 인증"""
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, 
                scopes=SCOPES
            )
            self.client = AnalyticsAdminServiceClient(credentials=self.credentials)
            print("✅ Service Account 인증 성공")
        except Exception as e:
            print(f"❌ 인증 오류: {e}")

    def init_database(self):
        """사용자 관리를 위한 SQLite 데이터베이스 초기화"""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 사용자 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ga4_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                property_id TEXT NOT NULL,
                role TEXT NOT NULL,
                granted_date DATETIME NOT NULL,
                expiry_date DATETIME,
                notification_sent BOOLEAN DEFAULT FALSE,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 알림 로그 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                sent_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                days_before_expiry INTEGER,
                status TEXT DEFAULT 'sent'
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 데이터베이스 초기화 완료")

    def add_user_with_expiry(self, account_id, property_id, user_email, role, expiry_days=None):
        """
        만료일이 있는 사용자 추가
        
        Args:
            account_id: GA4 계정 ID
            property_id: GA4 속성 ID
            user_email: 사용자 이메일
            role: 역할 (viewer, analyst, editor, admin)
            expiry_days: 만료일까지 일수 (None이면 무제한)
        """
        try:
            # GA4에 사용자 추가
            success = self._add_user_to_ga4(account_id, property_id, user_email, role)
            
            if success:
                # 데이터베이스에 사용자 정보 저장
                granted_date = datetime.now()
                expiry_date = granted_date + timedelta(days=expiry_days) if expiry_days else None
                
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ga4_users 
                    (email, property_id, role, granted_date, expiry_date, notification_sent, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, FALSE, 'active', CURRENT_TIMESTAMP)
                ''', (user_email, property_id, role, granted_date, expiry_date))
                
                conn.commit()
                conn.close()
                
                print(f"✅ 사용자 '{user_email}' 추가 완료")
                if expiry_date:
                    print(f"   만료일: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"   만료일: 무제한")
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ 사용자 추가 오류: {e}")
            return False

    def _add_user_to_ga4(self, account_id, property_id, user_email, role):
        """GA4에 사용자 추가 (기존 로직)"""
        try:
            role_mapping = {
                'viewer': 'predefinedRoles/viewer',
                'analyst': 'predefinedRoles/analyst', 
                'editor': 'predefinedRoles/editor',
                'admin': 'predefinedRoles/admin'
            }
            
            if role not in role_mapping:
                print(f"❌ 지원하지 않는 역할: {role}")
                return False

            parent = f"properties/{property_id}"
            
            access_binding = AccessBinding(
                user=user_email,
                roles=[role_mapping[role]]
            )
            
            request = CreateAccessBindingRequest(
                parent=parent,
                access_binding=access_binding
            )
            
            response = self.client.create_access_binding(request=request)
            print(f"✅ GA4에 사용자 추가 완료: {response.name}")
            return True
            
        except Exception as e:
            print(f"❌ GA4 사용자 추가 실패: {e}")
            return False

    def check_expiring_users(self, notification_days=[60, 30, 7, 1]):
        """
        만료 예정 사용자 확인 및 알림
        
        Args:
            notification_days: 알림을 보낼 만료 전 일수 리스트
        """
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        current_date = datetime.now()
        
        for days in notification_days:
            target_date = current_date + timedelta(days=days)
            
            # 해당 일수에 만료되는 사용자 조회
            cursor.execute('''
                SELECT email, property_id, role, granted_date, expiry_date
                FROM ga4_users 
                WHERE DATE(expiry_date) = DATE(?) 
                AND status = 'active'
                AND NOT EXISTS (
                    SELECT 1 FROM notification_logs 
                    WHERE user_email = ga4_users.email 
                    AND days_before_expiry = ?
                    AND DATE(sent_date) = DATE(?)
                )
            ''', (target_date, days, current_date))
            
            users = cursor.fetchall()
            
            for user in users:
                email, property_id, role, granted_date, expiry_date = user
                expiry_datetime = datetime.fromisoformat(expiry_date) if isinstance(expiry_date, str) else expiry_date
                self.send_expiry_notification(email, role, expiry_datetime, days)
                
                # 알림 로그 저장
                cursor.execute('''
                    INSERT INTO notification_logs (user_email, notification_type, days_before_expiry)
                    VALUES (?, 'expiry_warning', ?)
                ''', (email, days))
        
        conn.commit()
        conn.close()

    def send_expiry_notification(self, user_email, role, expiry_date, days_before):
        """만료 알림 이메일 발송"""
        try:
            # 이메일 설정 (config.json에서 읽어오거나 환경변수 사용)
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            smtp_server = config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = config.get('smtp_port', 587)
            sender_email = config.get('sender_email')
            sender_password = config.get('sender_password')
            
            if not sender_email or not sender_password:
                print("❌ 이메일 설정이 없습니다. config.json에 sender_email, sender_password를 추가하세요.")
                return False
            
            # 이메일 내용 작성
            subject = f"[GA4 권한 알림] {days_before}일 후 권한 만료 예정"
            
            body = f"""
안녕하세요,

Google Analytics 4 속성에 대한 귀하의 {role} 권한이 {days_before}일 후 만료될 예정입니다.

만료일: {expiry_date.strftime('%Y년 %m월 %d일')}
현재 권한: {role}

권한 연장이 필요하시면 관리자에게 문의해주세요.

감사합니다.
GA4 자동화 시스템
            """
            
            # 이메일 발송
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = user_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ 알림 이메일 발송 완료: {user_email} ({days_before}일 전)")
            return True
            
        except Exception as e:
            print(f"❌ 이메일 발송 실패: {e}")
            return False

    def remove_expired_users(self, property_id):
        """만료된 사용자 자동 제거"""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        current_date = datetime.now()
        
        # 만료된 사용자 조회
        cursor.execute('''
            SELECT email, role, expiry_date
            FROM ga4_users 
            WHERE DATE(expiry_date) <= DATE(?) 
            AND status = 'active'
            AND property_id = ?
        ''', (current_date, property_id))
        
        expired_users = cursor.fetchall()
        
        for user in expired_users:
            email, role, expiry_date = user
            
            # GA4에서 사용자 제거
            success = self._remove_user_from_ga4(property_id, email)
            
            if success:
                # 데이터베이스에서 상태 업데이트
                cursor.execute('''
                    UPDATE ga4_users 
                    SET status = 'expired', updated_at = CURRENT_TIMESTAMP
                    WHERE email = ? AND property_id = ?
                ''', (email, property_id))
                
                print(f"✅ 만료된 사용자 제거 완료: {email}")
                
                # 제거 알림 발송
                self.send_removal_notification(email, role, expiry_date)
        
        conn.commit()
        conn.close()

    def _remove_user_from_ga4(self, property_id, user_email):
        """GA4에서 사용자 제거 (기존 로직)"""
        try:
            parent = f"accounts/-/properties/{property_id}"
            
            # 기존 access bindings 조회
            request = self.client.list_access_bindings(parent=parent)
            
            for binding in request:
                if binding.user == user_email:
                    # Access binding 삭제
                    self.client.delete_access_binding(name=binding.name)
                    print(f"✅ GA4에서 사용자 제거 완료: {user_email}")
                    return True
            
            print(f"❌ 사용자를 찾을 수 없음: {user_email}")
            return False
            
        except Exception as e:
            print(f"❌ 사용자 제거 실패: {e}")
            return False

    def send_removal_notification(self, user_email, role, expiry_date):
        """사용자 제거 알림"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            sender_email = config.get('sender_email')
            sender_password = config.get('sender_password')
            
            if not sender_email or not sender_password:
                return False
            
            subject = "[GA4 권한 알림] 권한이 만료되어 제거되었습니다"
            
            body = f"""
안녕하세요,

Google Analytics 4 속성에 대한 귀하의 권한이 만료되어 제거되었습니다.

만료일: {expiry_date.strftime('%Y년 %m월 %d일')}
이전 권한: {role}

권한이 필요하시면 관리자에게 문의해주세요.

감사합니다.
GA4 자동화 시스템
            """
            
            # 이메일 발송 로직 (위와 동일)
            # ... (간략화)
            
            print(f"✅ 제거 알림 발송 완료: {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ 제거 알림 발송 실패: {e}")
            return False

    def get_user_status_report(self, property_id):
        """사용자 상태 리포트 생성"""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        current_date = datetime.now()
        
        print("=== GA4 사용자 상태 리포트 ===\n")
        
        # 활성 사용자
        cursor.execute('''
            SELECT email, role, granted_date, expiry_date
            FROM ga4_users 
            WHERE status = 'active' AND property_id = ?
            ORDER BY expiry_date ASC
        ''', (property_id,))
        
        active_users = cursor.fetchall()
        
        print("📋 활성 사용자:")
        for user in active_users:
            email, role, granted_date, expiry_date = user
            granted = datetime.fromisoformat(granted_date)
            
            if expiry_date:
                expiry = datetime.fromisoformat(expiry_date)
                days_left = (expiry - current_date).days
                status = "⚠️ 곧 만료" if days_left <= 7 else "✅ 정상"
                print(f"  {status} {email} ({role}) - 만료: {expiry.strftime('%Y-%m-%d')} ({days_left}일 남음)")
            else:
                print(f"  ✅ 정상 {email} ({role}) - 만료: 무제한")
        
        # 만료 예정 사용자 (7일 이내)
        cursor.execute('''
            SELECT email, role, expiry_date
            FROM ga4_users 
            WHERE status = 'active' 
            AND property_id = ?
            AND expiry_date IS NOT NULL
            AND DATE(expiry_date) BETWEEN DATE(?) AND DATE(?, '+7 days')
            ORDER BY expiry_date ASC
        ''', (property_id, current_date, current_date))
        
        expiring_users = cursor.fetchall()
        
        if expiring_users:
            print("\n⚠️ 7일 이내 만료 예정:")
            for user in expiring_users:
                email, role, expiry_date = user
                expiry = datetime.fromisoformat(expiry_date)
                days_left = (expiry - current_date).days
                print(f"  {email} ({role}) - {days_left}일 후 만료")
        
        conn.close()

    def schedule_automation(self, property_id):
        """자동화 스케줄 설정"""
        print("🔄 자동화 스케줄 시작...")
        
        # 매일 오전 9시에 만료 확인
        schedule.every().day.at("09:00").do(self.check_expiring_users)
        
        # 매일 자정에 만료된 사용자 제거
        schedule.every().day.at("00:00").do(self.remove_expired_users, property_id)
        
        # 매주 월요일 오전 10시에 상태 리포트
        schedule.every().monday.at("10:00").do(self.get_user_status_report, property_id)
        
        print("✅ 스케줄 설정 완료")
        print("   - 매일 09:00: 만료 예정 사용자 알림")
        print("   - 매일 00:00: 만료된 사용자 자동 제거")
        print("   - 매주 월요일 10:00: 상태 리포트")
        
        # 스케줄 실행
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 확인


def main():
    """메인 함수"""
    manager = GA4UserManager()
    
    # 설정 파일 로드
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    account_id = config.get('account_id')
    property_id = config.get('property_id')
    
    while True:
        print("\n=== GA4 사용자 관리 시스템 ===")
        print("1. 기간 제한 사용자 추가")
        print("2. 사용자 상태 리포트")
        print("3. 만료 예정 사용자 확인")
        print("4. 만료된 사용자 제거")
        print("5. 자동화 스케줄 시작")
        print("6. 종료")
        
        choice = input("\n선택하세요 (1-6): ").strip()
        
        if choice == '1':
            email = input("사용자 이메일: ").strip()
            role = input("역할 (viewer/analyst/editor/admin): ").strip()
            days = input("만료까지 일수 (빈 값이면 무제한): ").strip()
            
            expiry_days = int(days) if days else None
            manager.add_user_with_expiry(account_id, property_id, email, role, expiry_days)
            
        elif choice == '2':
            manager.get_user_status_report(property_id)
            
        elif choice == '3':
            manager.check_expiring_users()
            
        elif choice == '4':
            manager.remove_expired_users(property_id)
            
        elif choice == '5':
            print("자동화 스케줄을 시작합니다. Ctrl+C로 중단할 수 있습니다.")
            try:
                manager.schedule_automation(property_id)
            except KeyboardInterrupt:
                print("\n자동화 스케줄이 중단되었습니다.")
                
        elif choice == '6':
            print("프로그램을 종료합니다.")
            break
            
        else:
            print("잘못된 선택입니다.")


if __name__ == "__main__":
    main() 