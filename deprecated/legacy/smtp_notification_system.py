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

class SMTPNotificationSystem:
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
                status TEXT DEFAULT 'sent',
                message_subject TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 데이터베이스 초기화 완료")

    def send_smtp_email(self, to_email, subject, html_body, plain_body=None):
        """SMTP를 사용한 이메일 발송"""
        try:
            sender_email = self.config.get('sender_email')
            sender_password = self.config.get('sender_password')
            smtp_server = self.config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.config.get('smtp_port', 587)
            
            # 이메일 메시지 생성
            message = MIMEMultipart('alternative')
            message['From'] = sender_email
            message['To'] = to_email
            message['Subject'] = subject
            
            # 텍스트 버전 추가
            if plain_body:
                text_part = MIMEText(plain_body, 'plain', 'utf-8')
                message.attach(text_part)
            
            # HTML 버전 추가
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)
            
            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
            
            print(f"✅ SMTP로 이메일 발송 완료: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ SMTP 발송 실패: {e}")
            return False

    def create_welcome_email_template(self, user_email, role, property_id, expiry_date):
        """사용자 등록 환영 이메일 템플릿"""
        expiry_str = expiry_date.strftime('%Y년 %m월 %d일') if expiry_date else '무제한'
        
        subject = "[GA4 권한 부여] Google Analytics 4 접근 권한이 부여되었습니다"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4285f4; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .highlight {{ background-color: #e8f0fe; padding: 15px; border-left: 4px solid #4285f4; margin: 15px 0; }}
                .button {{ background-color: #4285f4; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 GA4 접근 권한 부여</h1>
                </div>
                
                <div class="content">
                    <h2>안녕하세요, {user_email}님!</h2>
                    
                    <p>Google Analytics 4 속성에 대한 접근 권한이 성공적으로 부여되었습니다.</p>
                    
                    <div class="highlight">
                        <h3>📊 권한 정보</h3>
                        <ul>
                            <li><strong>사용자 이메일:</strong> {user_email}</li>
                            <li><strong>권한 역할:</strong> {role}</li>
                            <li><strong>속성 ID:</strong> {property_id}</li>
                            <li><strong>권한 만료일:</strong> {expiry_str}</li>
                            <li><strong>부여일:</strong> {datetime.now().strftime('%Y년 %m월 %d일')}</li>
                        </ul>
                    </div>
                    
                    <h3>🚀 시작하기</h3>
                    <p>이제 Google Analytics 4에 접속하여 데이터를 분석할 수 있습니다.</p>
                    
                    <a href="https://analytics.google.com/analytics/web/" class="button">GA4 접속하기</a>
                    
                    {"<div style='background-color: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; border-radius: 5px; margin: 15px 0;'><strong>⚠️ 중요:</strong> 권한이 " + expiry_str + "에 만료됩니다. 연장이 필요한 경우 관리자에게 문의해주세요.</div>" if expiry_date else ""}
                </div>
                
                <div class="footer">
                    <p>이 메일은 GA4 자동화 시스템에서 발송되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
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
        
        return subject, html_body, plain_body

    def create_expiry_warning_email_template(self, user_email, role, expiry_date, days_left):
        """만료 경고 이메일 템플릿"""
        subject = f"[GA4 권한 알림] {days_left}일 후 권한 만료 예정 - 연장 신청 안내"
        
        urgency_color = "#ff6b6b" if days_left <= 3 else "#ffa726" if days_left <= 7 else "#42a5f5"
        urgency_icon = "🚨" if days_left <= 3 else "⚠️" if days_left <= 7 else "📅"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {urgency_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .warning {{ background-color: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; border-radius: 5px; margin: 15px 0; }}
                .urgent {{ background-color: #f8d7da; padding: 15px; border: 1px solid #f5c6cb; border-radius: 5px; margin: 15px 0; }}
                .button {{ background-color: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
                .countdown {{ font-size: 24px; font-weight: bold; color: {urgency_color}; text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{urgency_icon} GA4 권한 만료 예정</h1>
                </div>
                
                <div class="content">
                    <h2>안녕하세요, {user_email}님!</h2>
                    
                    <div class="countdown">
                        {days_left}일 후 권한 만료
                    </div>
                    
                    <p>Google Analytics 4 속성에 대한 귀하의 <strong>{role}</strong> 권한이 곧 만료될 예정입니다.</p>
                    
                    <div class="{'urgent' if days_left <= 3 else 'warning'}">
                        <h3>📋 만료 정보</h3>
                        <ul>
                            <li><strong>만료일:</strong> {expiry_date.strftime('%Y년 %m월 %d일 %H:%M')}</li>
                            <li><strong>남은 기간:</strong> {days_left}일</li>
                            <li><strong>현재 역할:</strong> {role}</li>
                        </ul>
                    </div>
                    
                    <h3>🔄 권한 연장 신청</h3>
                    <p>계속해서 GA4에 접근하시려면 권한 연장을 신청해주세요.</p>
                </div>
                
                <div class="footer">
                    <p>이 메일은 GA4 자동화 시스템에서 발송되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
        GA4 권한 만료 예정 알림
        
        안녕하세요, {user_email}님!
        
        Google Analytics 4 속성에 대한 귀하의 {role} 권한이 {days_left}일 후 만료될 예정입니다.
        
        만료 정보:
        - 만료일: {expiry_date.strftime('%Y년 %m월 %d일 %H:%M')}
        - 남은 기간: {days_left}일
        - 현재 역할: {role}
        
        권한 연장이 필요하시면 관리자에게 문의해주세요.
        """
        
        return subject, html_body, plain_body

    def create_deletion_notice_email_template(self, user_email, role, expiry_date):
        """삭제 후 알림 이메일 템플릿"""
        subject = "[GA4 권한 알림] 권한이 만료되어 제거되었습니다"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .notice {{ background-color: #f8d7da; padding: 15px; border: 1px solid #f5c6cb; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 GA4 권한 만료 및 제거</h1>
                </div>
                
                <div class="content">
                    <h2>안녕하세요, {user_email}님!</h2>
                    
                    <p>Google Analytics 4 속성에 대한 귀하의 접근 권한이 만료되어 자동으로 제거되었습니다.</p>
                    
                    <div class="notice">
                        <h3>📋 제거된 권한 정보</h3>
                        <ul>
                            <li><strong>사용자 이메일:</strong> {user_email}</li>
                            <li><strong>이전 역할:</strong> {role}</li>
                            <li><strong>만료일:</strong> {expiry_date.strftime('%Y년 %m월 %d일')}</li>
                            <li><strong>제거일:</strong> {datetime.now().strftime('%Y년 %m월 %d일')}</li>
                        </ul>
                    </div>
                    
                    <p>권한이 필요하시면 관리자에게 문의해주세요.</p>
                </div>
                
                <div class="footer">
                    <p>이 메일은 GA4 자동화 시스템에서 발송되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_body = f"""
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
        
        return subject, html_body, plain_body

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
                
                # 환영 이메일 발송
                subject, html_body, plain_body = self.create_welcome_email_template(
                    user_email, role, property_id, expiry_date
                )
                
                email_sent = self.send_smtp_email(user_email, subject, html_body, plain_body)
                
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

    def check_expiring_users_with_smtp(self, notification_days=[7, 1]):
        """만료 예정 사용자 확인 및 SMTP로 알림 발송"""
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
                
                # 만료 경고 이메일 발송
                subject, html_body, plain_body = self.create_expiry_warning_email_template(
                    email, role, expiry_datetime, days
                )
                
                email_sent = self.send_smtp_email(email, subject, html_body, plain_body)
                
                if email_sent:
                    # 알림 로그 저장
                    self._log_notification(email, 'expiry_warning', days, subject)
                    print(f"✅ 만료 경고 이메일 발송: {email} ({days}일 전)")
        
        conn.commit()
        conn.close()

    def remove_expired_users_with_notification(self, property_id):
        """만료된 사용자 자동 제거 및 알림"""
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
                
                # 삭제 후 알림 발송
                subject, html_body, plain_body = self.create_deletion_notice_email_template(
                    email, role, expiry_datetime
                )
                
                email_sent = self.send_smtp_email(email, subject, html_body, plain_body)
                
                if email_sent:
                    # 알림 로그 저장
                    self._log_notification(email, 'deletion_notice', 0, subject)
                    print(f"✅ 삭제 알림 이메일 발송: {email}")
        
        conn.commit()
        conn.close()

    def _remove_user_from_ga4(self, property_id, user_email):
        """GA4에서 사용자 제거"""
        try:
            parent = f"accounts/-/properties/{property_id}"
            
            # 기존 access bindings 조회
            request = self.ga_client.list_access_bindings(parent=parent)
            
            for binding in request:
                if binding.user == user_email:
                    # Access binding 삭제
                    self.ga_client.delete_access_binding(name=binding.name)
                    print(f"✅ GA4에서 사용자 제거 완료: {user_email}")
                    return True
            
            print(f"❌ 사용자를 찾을 수 없음: {user_email}")
            return False
            
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
                (user_email, notification_type, days_before_expiry, message_subject)
                VALUES (?, ?, ?, ?)
            ''', (user_email, notification_type, days_before_expiry, message_subject))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ 알림 로그 저장 실패: {e}")

def test_smtp_notification_scenario():
    """wonyoungseong@gmail.com 사용자 시나리오 테스트"""
    
    # 설정 파일 로드
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    account_id = config.get('account_id')
    property_id = config.get('property_id')
    
    # 알림 시스템 초기화
    notification_system = SMTPNotificationSystem()
    
    print("=== 📧 SMTP 알림 시나리오 테스트 ===\n")
    
    # 1. 사용자 등록 및 환영 메일
    test_email = "wonyoungseong@gmail.com"
    test_role = "viewer"
    test_expiry_days = 8  # 8일 후 만료 (7일 경고 + 1일 최종 경고)
    
    print(f"1. 사용자 등록 및 환영 메일 발송: {test_email}")
    success = notification_system.add_user_with_expiry_and_notification(
        account_id, property_id, test_email, test_role, test_expiry_days
    )
    
    if success:
        print("✅ 등록 및 환영 메일 발송 완료\n")
        
        # 2. 7일 전 만료 경고 메일 (시뮬레이션)
        print("2. 만료 경고 메일 발송 테스트 (7일 전):")
        notification_system.check_expiring_users_with_smtp(notification_days=[7])
        
        # 3. 1일 전 최종 경고 메일 (시뮬레이션)
        print("\n3. 최종 경고 메일 발송 테스트 (1일 전):")
        notification_system.check_expiring_users_with_smtp(notification_days=[1])
        
    else:
        print("❌ 사용자 등록 실패")

if __name__ == "__main__":
    test_smtp_notification_scenario() 