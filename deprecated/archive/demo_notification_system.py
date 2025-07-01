import json
import sqlite3
from datetime import datetime, timedelta
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, CreateAccessBindingRequest
from google.oauth2 import service_account

# Service Account 인증 파일 경로
SERVICE_ACCOUNT_FILE = 'ga4-automatio-797ec352f393.json'
SCOPES = ['https://www.googleapis.com/auth/analytics.manage.users']

# 데이터베이스 설정
DB_NAME = 'ga4_user_management.db'

class DemoNotificationSystem:
    def __init__(self):
        self.ga_client = None
        self.credentials = None
        self.config = self.load_config()
        self.init_database()
        self.authenticate()

    def load_config(self):
        """설정 파일 로드"""
        with open('config.json', 'r') as f:
            return json.load(f)

    def authenticate(self):
        """Service Account 인증"""
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, 
                scopes=SCOPES
            )
            
            # GA4 클라이언트
            self.ga_client = AnalyticsAdminServiceClient(credentials=self.credentials)
            
            print("✅ Service Account 인증 성공 (GA4)")
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
                status TEXT DEFAULT 'demo',
                message_subject TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 데이터베이스 초기화 완료")

    def demo_send_email(self, to_email, subject, html_body, plain_body=None):
        """데모용 이메일 발송 (실제 발송하지 않음)"""
        print(f"📧 [데모] 이메일 발송 시뮬레이션:")
        print(f"   받는 사람: {to_email}")
        print(f"   제목: {subject}")
        print(f"   내용 길이: {len(html_body)} 문자")
        print(f"   ✅ 발송 완료 (시뮬레이션)")
        return True

    def create_welcome_email_template(self, user_email, role, property_id, expiry_date):
        """사용자 등록 환영 이메일 템플릿"""
        expiry_str = expiry_date.strftime('%Y년 %m월 %d일') if expiry_date else '무제한'
        
        subject = "[GA4 권한 부여] Google Analytics 4 접근 권한이 부여되었습니다"
        
        html_body = f"""
        GA4 접근 권한 부여 알림
        
        안녕하세요, {user_email}님!
        
        Google Analytics 4 속성에 대한 접근 권한이 성공적으로 부여되었습니다.
        
        권한 정보:
        - 사용자 이메일: {user_email}
        - 권한 역할: {role}
        - 속성 ID: {property_id}
        - 권한 만료일: {expiry_str}
        - 부여일: {datetime.now().strftime('%Y년 %m월 %d일')}
        
        GA4 접속: https://analytics.google.com/analytics/web/
        """
        
        return subject, html_body, html_body

    def create_expiry_warning_email_template(self, user_email, role, expiry_date, days_left):
        """만료 경고 이메일 템플릿"""
        subject = f"[GA4 권한 알림] {days_left}일 후 권한 만료 예정 - 연장 신청 안내"
        
        html_body = f"""
        GA4 권한 만료 예정 알림
        
        안녕하세요, {user_email}님!
        
        Google Analytics 4 속성에 대한 귀하의 {role} 권한이 {days_left}일 후 만료될 예정입니다.
        
        만료 정보:
        - 만료일: {expiry_date.strftime('%Y년 %m월 %d일 %H:%M')}
        - 남은 기간: {days_left}일
        - 현재 역할: {role}
        
        권한 연장이 필요하시면 관리자에게 문의해주세요.
        """
        
        return subject, html_body, html_body

    def create_deletion_notice_email_template(self, user_email, role, expiry_date):
        """삭제 후 알림 이메일 템플릿"""
        subject = "[GA4 권한 알림] 권한이 만료되어 제거되었습니다"
        
        html_body = f"""
        GA4 권한 만료 및 제거 알림
        
        안녕하세요, {user_email}님!
        
        Google Analytics 4 속성에 대한 귀하의 접근 권한이 만료되어 자동으로 제거되었습니다.
        
        제거된 권한 정보:
        - 사용자 이메일: {user_email}
        - 이전 역할: {role}
        - 만료일: {expiry_date.strftime('%Y년 %m월 %d일')}
        - 제거일: {datetime.now().strftime('%Y년 %m월 %d일')}
        
        권한이 필요하시면 관리자에게 문의해주세요.
        """
        
        return subject, html_body, html_body

    def add_user_with_expiry_and_notification(self, account_id, property_id, user_email, role, expiry_days=None):
        """사용자 추가 및 환영 이메일 발송"""
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
                
                # 환영 이메일 발송 (데모)
                subject, html_body, plain_body = self.create_welcome_email_template(
                    user_email, role, property_id, expiry_date
                )
                
                email_sent = self.demo_send_email(user_email, subject, html_body, plain_body)
                
                if email_sent:
                    # 알림 로그 저장
                    self._log_notification(user_email, 'welcome', None, subject)
                
                print(f"✅ 사용자 '{user_email}' 추가 및 환영 이메일 발송 완료")
                if expiry_date:
                    print(f"   만료일: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"   만료일: 무제한")
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ 사용자 추가 및 알림 오류: {e}")
            return False

    def _add_user_to_ga4(self, account_id, property_id, user_email, role):
        """GA4에 사용자 추가"""
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
            
            response = self.ga_client.create_access_binding(request=request)
            print(f"✅ GA4에 사용자 추가 완료: {response.name}")
            return True
            
        except Exception as e:
            print(f"❌ GA4 사용자 추가 실패: {e}")
            return False

    def check_expiring_users_demo(self, notification_days=[7, 1]):
        """만료 예정 사용자 확인 및 데모 알림 발송"""
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
                    AND notification_type = 'expiry_warning'
                    AND days_before_expiry = ?
                    AND DATE(sent_date) = DATE(?)
                )
            ''', (target_date, days, current_date))
            
            users = cursor.fetchall()
            
            for user in users:
                email, property_id, role, granted_date, expiry_date = user
                expiry_datetime = datetime.fromisoformat(expiry_date) if isinstance(expiry_date, str) else expiry_date
                
                # 만료 경고 이메일 발송 (데모)
                subject, html_body, plain_body = self.create_expiry_warning_email_template(
                    email, role, expiry_datetime, days
                )
                
                email_sent = self.demo_send_email(email, subject, html_body, plain_body)
                
                if email_sent:
                    # 알림 로그 저장
                    self._log_notification(email, 'expiry_warning', days, subject)
                    print(f"✅ 만료 경고 이메일 발송: {email} ({days}일 전)")
        
        conn.commit()
        conn.close()

    def remove_expired_users_demo(self, property_id):
        """만료된 사용자 자동 제거 및 데모 알림"""
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
            expiry_datetime = datetime.fromisoformat(expiry_date) if isinstance(expiry_date, str) else expiry_date
            
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
                
                # 삭제 후 알림 발송 (데모)
                subject, html_body, plain_body = self.create_deletion_notice_email_template(
                    email, role, expiry_datetime
                )
                
                email_sent = self.demo_send_email(email, subject, html_body, plain_body)
                
                if email_sent:
                    # 알림 로그 저장
                    self._log_notification(email, 'deletion_notice', 0, subject)
                    print(f"✅ 삭제 알림 이메일 발송: {email}")
        
        conn.commit()
        conn.close()

    def _remove_user_from_ga4(self, property_id, user_email):
        """GA4에서 사용자 제거 (데모 - 실제 제거하지 않음)"""
        try:
            print(f"📧 [데모] GA4 사용자 제거 시뮬레이션:")
            print(f"   사용자: {user_email}")
            print(f"   속성 ID: {property_id}")
            print(f"   ✅ 제거 완료 (시뮬레이션)")
            return True
            
        except Exception as e:
            print(f"❌ 사용자 제거 실패: {e}")
            return False

    def _log_notification(self, user_email, notification_type, days_before_expiry, message_subject):
        """알림 로그 저장"""
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notification_logs 
                (user_email, notification_type, days_before_expiry, status, message_subject)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_email, notification_type, days_before_expiry, 'demo', message_subject))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ 알림 로그 저장 실패: {e}")

def demo_complete_scenario():
    """완전한 데모 시나리오"""
    
    # 설정 파일 로드
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    account_id = config.get('account_id')
    property_id = config.get('property_id')
    
    # 알림 시스템 초기화
    notification_system = DemoNotificationSystem()
    
    print("=== 📧 완전한 GA4 알림 시나리오 데모 ===\n")
    
    test_email = "wonyoungseong@gmail.com"
    test_role = "viewer"
    
    # === 시나리오 1: 사용자 등록 및 환영 메일 ===
    print("🎯 시나리오 1: 사용자 등록 및 환영 메일")
    print(f"   사용자: {test_email}")
    print(f"   역할: {test_role}")
    print(f"   만료 기간: 8일")
    print()
    
    # 사용자 추가 (8일 후 만료)
    success = notification_system.add_user_with_expiry_and_notification(
        account_id, property_id, test_email, test_role, 8
    )
    
    if not success:
        print("❌ 사용자 등록 실패")
        return
    
    print("✅ 사용자 등록 및 환영 메일 발송 완료\n")
    
    # === 시나리오 2: 7일 전 만료 경고 메일 시뮬레이션 ===
    print("🎯 시나리오 2: 7일 전 만료 경고 메일 시뮬레이션")
    
    # 데이터베이스에서 만료일을 7일 후로 설정
    conn = sqlite3.connect('ga4_user_management.db')
    cursor = conn.cursor()
    
    new_expiry = datetime.now() + timedelta(days=7)
    cursor.execute('''
        UPDATE ga4_users 
        SET expiry_date = ? 
        WHERE email = ? AND property_id = ?
    ''', (new_expiry, test_email, property_id))
    
    conn.commit()
    conn.close()
    
    print(f"   만료일을 {new_expiry.strftime('%Y-%m-%d %H:%M')}로 설정 (7일 후)")
    
    # 7일 전 경고 메일 발송
    notification_system.check_expiring_users_demo(notification_days=[7])
    print("✅ 7일 전 만료 경고 메일 발송 완료\n")
    
    # === 시나리오 3: 1일 전 최종 경고 메일 시뮬레이션 ===
    print("🎯 시나리오 3: 1일 전 최종 경고 메일 시뮬레이션")
    
    # 만료일을 1일 후로 설정
    conn = sqlite3.connect('ga4_user_management.db')
    cursor = conn.cursor()
    
    new_expiry = datetime.now() + timedelta(days=1)
    cursor.execute('''
        UPDATE ga4_users 
        SET expiry_date = ? 
        WHERE email = ? AND property_id = ?
    ''', (new_expiry, test_email, property_id))
    
    conn.commit()
    conn.close()
    
    print(f"   만료일을 {new_expiry.strftime('%Y-%m-%d %H:%M')}로 설정 (1일 후)")
    
    # 1일 전 최종 경고 메일 발송
    notification_system.check_expiring_users_demo(notification_days=[1])
    print("✅ 1일 전 최종 경고 메일 발송 완료\n")
    
    # === 시나리오 4: 만료 및 사용자 제거, 삭제 알림 메일 ===
    print("🎯 시나리오 4: 만료 및 사용자 제거, 삭제 알림 메일")
    
    # 만료일을 과거로 설정 (이미 만료됨)
    conn = sqlite3.connect('ga4_user_management.db')
    cursor = conn.cursor()
    
    expired_date = datetime.now() - timedelta(hours=1)  # 1시간 전에 만료
    cursor.execute('''
        UPDATE ga4_users 
        SET expiry_date = ? 
        WHERE email = ? AND property_id = ?
    ''', (expired_date, test_email, property_id))
    
    conn.commit()
    conn.close()
    
    print(f"   만료일을 {expired_date.strftime('%Y-%m-%d %H:%M')}로 설정 (이미 만료)")
    
    # 만료된 사용자 제거 및 알림
    notification_system.remove_expired_users_demo(property_id)
    print("✅ 만료된 사용자 제거 및 삭제 알림 메일 발송 완료\n")
    
    # === 최종 리포트 ===
    print("🎯 최종 알림 발송 리포트:")
    show_demo_report()

def show_demo_report():
    """데모 리포트 표시"""
    conn = sqlite3.connect('ga4_user_management.db')
    cursor = conn.cursor()
    
    # 오늘 발송된 모든 알림 조회
    cursor.execute('''
        SELECT user_email, notification_type, days_before_expiry, sent_date, message_subject
        FROM notification_logs 
        WHERE DATE(sent_date) = DATE('now')
        ORDER BY sent_date
    ''')
    
    notifications = cursor.fetchall()
    
    if notifications:
        print(f"\n📧 오늘 발송된 알림 ({len(notifications)}건):")
        for i, (email, notif_type, days, sent_date, subject) in enumerate(notifications, 1):
            type_name = {
                'welcome': '환영 메일',
                'expiry_warning': f'만료 경고 ({days}일 전)',
                'deletion_notice': '삭제 알림'
            }.get(notif_type, notif_type)
            
            sent_time = datetime.fromisoformat(sent_date).strftime('%H:%M:%S')
            print(f"  {i}. [{sent_time}] {type_name} → {email}")
            print(f"     제목: {subject}")
    else:
        print("\n📧 오늘 발송된 알림이 없습니다.")
    
    # 사용자 상태 확인
    cursor.execute('''
        SELECT email, role, status, granted_date, expiry_date
        FROM ga4_users 
        WHERE email = 'wonyoungseong@gmail.com'
    ''')
    
    user_info = cursor.fetchone()
    
    if user_info:
        email, role, status, granted_date, expiry_date = user_info
        print(f"\n👤 사용자 현재 상태:")
        print(f"   이메일: {email}")
        print(f"   역할: {role}")
        print(f"   상태: {status}")
        print(f"   부여일: {granted_date}")
        print(f"   만료일: {expiry_date}")
    
    conn.close()

if __name__ == "__main__":
    demo_complete_scenario() 