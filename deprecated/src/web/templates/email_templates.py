"""
이메일 템플릿 시스템

GA4 권한 관리 시스템의 다양한 이메일 템플릿을 제공합니다.
"""

from typing import Dict, Any, Tuple
from datetime import datetime, timedelta


class EmailTemplates:
    """이메일 템플릿 클래스"""
    
    @staticmethod
    def get_base_template() -> str:
        """기본 HTML 템플릿"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GA4 권한 관리 시스템</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
            font-size: 24px;
        }
        .content {
            margin-bottom: 30px;
        }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .alert-info { background-color: #d1ecf1; border-left: 4px solid #17a2b8; }
        .alert-warning { background-color: #fff3cd; border-left: 4px solid #ffc107; }
        .alert-danger { background-color: #f8d7da; border-left: 4px solid #dc3545; }
        .alert-success { background-color: #d4edda; border-left: 4px solid #28a745; }
        .property-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .footer {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 14px;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 5px;
        }
        .btn-danger { background-color: #dc3545; }
        .btn-warning { background-color: #ffc107; color: #212529; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 GA4 권한 관리 시스템</h1>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>이 메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.</p>
            <p>문의사항이 있으시면 관리자에게 연락해주세요.</p>
        </div>
    </div>
</body>
</html>
        """
    
    @staticmethod
    def welcome_email(data: Dict[str, Any]) -> Dict[str, str]:
        """환영 이메일 템플릿"""
        content = f"""
        <div class="alert alert-success">
            <h3>🎉 GA4 권한 등록 완료!</h3>
            <p><strong>{data['applicant']}</strong>님의 GA4 권한이 성공적으로 등록되었습니다.</p>
        </div>
        
        <div class="property-info">
            <h4>📊 등록 정보</h4>
            <ul>
                <li><strong>계정:</strong> {data['user_email']}</li>
                <li><strong>프로퍼티:</strong> {data['property_name']}</li>
                <li><strong>권한 레벨:</strong> {data['permission_level']}</li>
                <li><strong>등록일:</strong> {data['created_at']}</li>
                <li><strong>만료일:</strong> {data['expiry_date']}</li>
            </ul>
        </div>
        
        <div class="alert alert-info">
            <h4>📋 주의사항</h4>
            <ul>
                <li>GA4 계정에 로그인하여 권한이 정상적으로 부여되었는지 확인해주세요.</li>
                <li>권한은 만료일까지 유효하며, 연장이 필요한 경우 관리자에게 문의해주세요.</li>
                <li>Editor 권한의 경우 7일 후 자동으로 Viewer 권한으로 변경됩니다.</li>
            </ul>
        </div>
        """
        
        html_content = EmailTemplates.get_base_template().format(content=content)
        
        return {
            "subject": f"[GA4] 권한 등록 완료 - {data['property_name']}",
            "html": html_content,
            "text": f"""
GA4 권한 등록 완료

{data['applicant']}님의 GA4 권한이 성공적으로 등록되었습니다.

등록 정보:
- 계정: {data['user_email']}
- 프로퍼티: {data['property_name']}
- 권한 레벨: {data['permission_level']}
- 등록일: {data['created_at']}
- 만료일: {data['expiry_date']}

주의사항:
- GA4 계정에 로그인하여 권한을 확인해주세요.
- 권한은 만료일까지 유효합니다.
- Editor 권한은 7일 후 자동으로 Viewer 권한으로 변경됩니다.
            """
        }
    
    @staticmethod
    def expiry_warning_email(data: Dict[str, Any], days_left: int) -> Dict[str, str]:
        """만료 경고 이메일 템플릿"""
        urgency_class = "alert-danger" if days_left <= 1 else "alert-warning"
        urgency_emoji = "🚨" if days_left <= 1 else "⚠️"
        
        content = f"""
        <div class="alert {urgency_class}">
            <h3>{urgency_emoji} GA4 권한 만료 알림</h3>
            <p><strong>{data['applicant']}</strong>님의 GA4 권한이 <strong>{days_left}일 후</strong> 만료됩니다.</p>
        </div>
        
        <div class="property-info">
            <h4>📊 권한 정보</h4>
            <ul>
                <li><strong>계정:</strong> {data['user_email']}</li>
                <li><strong>프로퍼티:</strong> {data['property_name']}</li>
                <li><strong>권한 레벨:</strong> {data['permission_level']}</li>
                <li><strong>만료일:</strong> {data['expiry_date']}</li>
            </ul>
        </div>
        
        <div class="alert alert-info">
            <h4>🔄 권한 연장 방법</h4>
            <p>권한 연장이 필요한 경우 관리자에게 연락하거나 새로운 권한 신청을 해주세요.</p>
            <p>연장하지 않으면 만료일 이후 자동으로 권한이 삭제됩니다.</p>
        </div>
        """
        
        html_content = EmailTemplates.get_base_template().format(content=content)
        
        return {
            "subject": f"[GA4] 권한 만료 알림 ({days_left}일 후) - {data['property_name']}",
            "html": html_content,
            "text": f"""
GA4 권한 만료 알림

{data['applicant']}님의 GA4 권한이 {days_left}일 후 만료됩니다.

권한 정보:
- 계정: {data['user_email']}
- 프로퍼티: {data['property_name']}
- 권한 레벨: {data['permission_level']}
- 만료일: {data['expiry_date']}

권한 연장이 필요한 경우 관리자에게 연락해주세요.
연장하지 않으면 만료일 이후 자동으로 권한이 삭제됩니다.
            """
        }
    
    @staticmethod
    def expired_email(data: Dict[str, Any]) -> Dict[str, str]:
        """만료 후 삭제 알림 이메일 템플릿"""
        content = f"""
        <div class="alert alert-danger">
            <h3>🔒 GA4 권한 삭제 완료</h3>
            <p><strong>{data['applicant']}</strong>님의 GA4 권한이 만료되어 삭제되었습니다.</p>
        </div>
        
        <div class="property-info">
            <h4>📊 삭제된 권한 정보</h4>
            <ul>
                <li><strong>계정:</strong> {data['user_email']}</li>
                <li><strong>프로퍼티:</strong> {data['property_name']}</li>
                <li><strong>권한 레벨:</strong> {data['permission_level']}</li>
                <li><strong>만료일:</strong> {data['expiry_date']}</li>
                <li><strong>삭제일:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
        </div>
        
        <div class="alert alert-info">
            <h4>🔄 권한 재신청</h4>
            <p>다시 권한이 필요한 경우 새로운 권한 신청을 해주세요.</p>
            <p>관리자에게 연락하시거나 권한 관리 시스템을 통해 신청할 수 있습니다.</p>
        </div>
        """
        
        html_content = EmailTemplates.get_base_template().format(content=content)
        
        return {
            "subject": f"[GA4] 권한 삭제 완료 - {data['property_name']}",
            "html": html_content,
            "text": f"""
GA4 권한 삭제 완료

{data['applicant']}님의 GA4 권한이 만료되어 삭제되었습니다.

삭제된 권한 정보:
- 계정: {data['user_email']}
- 프로퍼티: {data['property_name']}
- 권한 레벨: {data['permission_level']}
- 만료일: {data['expiry_date']}
- 삭제일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

다시 권한이 필요한 경우 새로운 권한 신청을 해주세요.
            """
        }
    
    @staticmethod
    def editor_downgrade_email(data: Dict[str, Any]) -> Dict[str, str]:
        """Editor 권한 다운그레이드 알림 템플릿"""
        content = f"""
        <div class="alert alert-warning">
            <h3>⬇️ Editor 권한 자동 변경</h3>
            <p><strong>{data['applicant']}</strong>님의 Editor 권한이 Viewer 권한으로 자동 변경되었습니다.</p>
        </div>
        
        <div class="property-info">
            <h4>📊 권한 변경 정보</h4>
            <ul>
                <li><strong>계정:</strong> {data['user_email']}</li>
                <li><strong>프로퍼티:</strong> {data['property_name']}</li>
                <li><strong>이전 권한:</strong> Editor</li>
                <li><strong>현재 권한:</strong> Viewer</li>
                <li><strong>변경일:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
        </div>
        
        <div class="alert alert-info">
            <h4>📋 변경 사유</h4>
            <p>보안 정책에 따라 Editor 권한은 7일 후 자동으로 Viewer 권한으로 변경됩니다.</p>
            <p>계속해서 Editor 권한이 필요한 경우 관리자에게 연락하여 재신청해주세요.</p>
        </div>
        """
        
        html_content = EmailTemplates.get_base_template().format(content=content)
        
        return {
            "subject": f"[GA4] Editor 권한 자동 변경 - {data['property_name']}",
            "html": html_content,
            "text": f"""
Editor 권한 자동 변경

{data['applicant']}님의 Editor 권한이 Viewer 권한으로 자동 변경되었습니다.

권한 변경 정보:
- 계정: {data['user_email']}
- 프로퍼티: {data['property_name']}
- 이전 권한: Editor
- 현재 권한: Viewer
- 변경일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

보안 정책에 따라 Editor 권한은 7일 후 자동으로 Viewer 권한으로 변경됩니다.
계속해서 Editor 권한이 필요한 경우 관리자에게 연락하여 재신청해주세요.
            """
        }
    
    @staticmethod
    def approval_request_email(data: Dict[str, Any]) -> Dict[str, str]:
        """Editor 권한 승인 요청 이메일 (관리자용)"""
        content = f"""
        <div class="alert alert-warning">
            <h3>👤 Editor 권한 승인 요청</h3>
            <p>새로운 Editor 권한 신청이 승인 대기 중입니다.</p>
        </div>
        
        <div class="property-info">
            <h4>📊 신청 정보</h4>
            <ul>
                <li><strong>신청자:</strong> {data['applicant']}</li>
                <li><strong>계정:</strong> {data['user_email']}</li>
                <li><strong>프로퍼티:</strong> {data['property_name']}</li>
                <li><strong>요청 권한:</strong> Editor</li>
                <li><strong>신청일:</strong> {data['created_at']}</li>
                <li><strong>만료 예정일:</strong> {data['expiry_date']}</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="#" class="btn">승인</a>
            <a href="#" class="btn btn-danger">거부</a>
        </div>
        
        <div class="alert alert-info">
            <h4>📋 승인 시 주의사항</h4>
            <ul>
                <li>Editor 권한은 7일 후 자동으로 Viewer 권한으로 변경됩니다.</li>
                <li>승인 후 사용자에게 자동으로 알림이 발송됩니다.</li>
                <li>권한 남용 방지를 위해 신중하게 검토해주세요.</li>
            </ul>
        </div>
        """
        
        html_content = EmailTemplates.get_base_template().format(content=content)
        
        return {
            "subject": f"[GA4 관리자] Editor 권한 승인 요청 - {data['applicant']}",
            "html": html_content,
            "text": f"""
Editor 권한 승인 요청

새로운 Editor 권한 신청이 승인 대기 중입니다.

신청 정보:
- 신청자: {data['applicant']}
- 계정: {data['user_email']}
- 프로퍼티: {data['property_name']}
- 요청 권한: Editor
- 신청일: {data['created_at']}
- 만료 예정일: {data['expiry_date']}

관리자 대시보드에서 승인 또는 거부 처리를 해주세요.
            """
        }
    
    @staticmethod
    def create_expiry_warning_email(user_email: str = "test@example.com", 
                                  property_name: str = "Test Property", 
                                  property_id: str = "123456789", 
                                  role: str = "Analyst", 
                                  expiry_date: datetime = None, 
                                  days_left: int = 7) -> Tuple[str, str, str]:
        """만료 경고 이메일 생성 (NotificationService 호환)"""
        # expiry_date가 None이면 기본값 설정
        if expiry_date is None:
            from datetime import timedelta
            expiry_date = datetime.now() + timedelta(days=days_left)
            
        urgency_icon = "🚨" if days_left <= 1 else "⚠️"
        urgency_color = "#dc3545" if days_left <= 1 else "#ffc107"
        
        subject = f"{urgency_icon} [GA4 권한 알림] {days_left}일 후 만료 예정 - {property_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: {urgency_color}; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">{urgency_icon} GA4 권한 만료 알림</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{days_left}일 후 권한이 만료됩니다</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid {urgency_color}; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 15px 0; color: {urgency_color};">📊 권한 정보</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; width: 30%;">사용자:</td>
                                <td style="padding: 8px 0;">{user_email}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">프로퍼티:</td>
                                <td style="padding: 8px 0;">{property_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">현재 권한:</td>
                                <td style="padding: 8px 0;">{role}</td>
                            </tr>
                            <tr style="color: {urgency_color}; font-weight: bold;">
                                <td style="padding: 8px 0;">만료일:</td>
                                <td style="padding: 8px 0;">{expiry_date.strftime('%Y년 %m월 %d일 %H시 %M분')}</td>
                            </tr>
                            <tr style="color: {urgency_color}; font-weight: bold; font-size: 16px;">
                                <td style="padding: 8px 0;">남은 시간:</td>
                                <td style="padding: 8px 0;">{days_left}일</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #1565c0;">🔗 GA4 접속</h3>
                        <p style="margin: 0 0 15px 0;">현재 권한으로 GA4에 접속하여 작업을 계속하세요:</p>
                        <a href="https://analytics.google.com/analytics/web/#/p{property_id}/reports/intelligenthome"
                           style="background: #2196f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            📈 GA4 접속하기
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                    <p style="text-align: center; color: #6c757d; font-size: 14px; margin: 0;">
                        이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다<br>
                        발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
{urgency_icon} GA4 권한 만료 알림

{days_left}일 후 GA4 권한이 만료됩니다!

권한 정보:
- 사용자: {user_email}
- 프로퍼티: {property_name}
- 현재 권한: {role}
- 만료일: {expiry_date.strftime('%Y년 %m월 %d일 %H시 %M분')}
- 남은 시간: {days_left}일

권한 연장 방법:
1. 관리자에게 권한 연장을 요청하세요
2. 업무 필요성과 연장 기간을 명시하세요
3. 승인 후 자동으로 권한이 연장됩니다

GA4 접속: https://analytics.google.com/analytics/web/#/p{property_id}/reports/intelligenthome

이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다.
        """
        
        return subject, text_content, html_content
    
    @staticmethod
    def create_admin_notification_email(subject: str = "🔧 GA4 시스템 알림", message: str = "시스템 알림", details: str = None) -> Tuple[str, str, str]:
        """관리자 알림 이메일 생성 (NotificationService 호환)"""
        details_section = ""
        if details:
            details_section = f"""
            <div style="background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #495057;">📋 상세 정보</h3>
                <pre style="margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 14px;">{details}</pre>
            </div>
            """
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #343a40; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">🔧 시스템 관리자 알림</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">GA4 권한 관리 시스템에서 중요한 알림이 있습니다</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; margin-bottom: 20px;">
                        <h2 style="margin: 0 0 15px 0; color: #007bff;">📢 알림 내용</h2>
                        <p style="margin: 0; font-size: 16px; font-weight: bold;">{message}</p>
                    </div>
                    {details_section}
                    
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                    <p style="text-align: center; color: #6c757d; font-size: 14px; margin: 0;">
                        이 이메일은 GA4 권한 관리 시스템에서 자동으로 발송되었습니다<br>
                        발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        details_text = f'상세 정보:\n{details}\n' if details else ''
        text_content = f"""
시스템 관리자 알림

알림 내용: {message}

{details_text}

발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
GA4 권한 관리 시스템 자동 알림
        """
        
        return subject, text_content, html_content
    
    @staticmethod
    def create_welcome_email(data: Dict[str, Any]) -> Tuple[str, str, str]:
        """환영 이메일 생성 (NotificationService 호환)"""
        user_email = data.get('user_email', '')
        property_name = data.get('property_name', 'Unknown')
        applicant = data.get('applicant', user_email)
        permission_level = data.get('permission_level', 'analyst')
        created_at = data.get('created_at', datetime.now().strftime('%Y-%m-%d'))
        expiry_date = data.get('expiry_date', '')
        
        subject = f"[GA4] 권한 등록 완료 - {property_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #28a745; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">🎉 GA4 권한 등록 완료!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">GA4 권한이 성공적으로 등록되었습니다</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                        <h2 style="margin: 0 0 15px 0; color: #28a745;">📊 등록 정보</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 8px 0; font-weight: bold; width: 30%;">신청자:</td><td>{applicant}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold;">계정:</td><td>{user_email}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold;">프로퍼티:</td><td>{property_name}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold;">권한 레벨:</td><td>{permission_level}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold;">등록일:</td><td>{created_at}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold;">만료일:</td><td>{expiry_date}</td></tr>
                        </table>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
GA4 권한 등록 완료

{applicant}님의 GA4 권한이 성공적으로 등록되었습니다.

등록 정보:
- 신청자: {applicant}
- 계정: {user_email}
- 프로퍼티: {property_name}
- 권한 레벨: {permission_level}
- 등록일: {created_at}
- 만료일: {expiry_date}

GA4 계정에 로그인하여 권한을 확인해주세요.
        """
        
        return subject, html_content, text_content
    
    @staticmethod
    def create_deletion_notice_email(data: Dict[str, Any]) -> Tuple[str, str, str]:
        """삭제 알림 이메일 생성 (NotificationService 호환)"""
        user_email = data.get('user_email', '')
        property_name = data.get('property_name', 'Unknown')
        applicant = data.get('applicant', user_email)
        permission_level = data.get('permission_level', 'analyst')
        
        subject = f"[GA4] 권한 만료 및 삭제 - {property_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #dc3545; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">🚨 GA4 권한 만료 및 삭제</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">GA4 권한이 만료되어 삭제되었습니다</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545;">
                        <h2 style="margin: 0 0 15px 0; color: #dc3545;">📊 삭제된 권한 정보</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 8px 0; font-weight: bold; width: 30%;">신청자:</td><td>{applicant}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold;">계정:</td><td>{user_email}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold;">프로퍼티:</td><td>{property_name}</td></tr>
                            <tr><td style="padding: 8px 0; font-weight: bold;">권한 레벨:</td><td>{permission_level}</td></tr>
                        </table>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
GA4 권한 만료 및 삭제

{applicant}님의 GA4 권한이 만료되어 삭제되었습니다.

삭제된 권한 정보:
- 신청자: {applicant}
- 계정: {user_email}
- 프로퍼티: {property_name}
- 권한 레벨: {permission_level}

재신청이 필요한 경우 관리자에게 연락해주세요.
        """
        
        return subject, html_content, text_content
    
    @staticmethod
    def create_extension_approved_email(data: Dict[str, Any]) -> Tuple[str, str, str]:
        """연장 승인 이메일 생성"""
        user_email = data.get('user_email', '')
        property_name = data.get('property_name', 'Unknown')
        applicant = data.get('applicant', user_email)
        
        subject = f"[GA4] 권한 연장 승인 - {property_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #28a745; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">✅ GA4 권한 연장 승인</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                        <h2 style="margin: 0 0 15px 0; color: #28a745;">📊 연장된 권한 정보</h2>
                        <p>{applicant}님의 GA4 권한 연장이 승인되었습니다.</p>
                        <p>계정: {user_email}<br>프로퍼티: {property_name}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"GA4 권한 연장 승인\n\n{applicant}님의 GA4 권한 연장이 승인되었습니다.\n계정: {user_email}\n프로퍼티: {property_name}"
        
        return subject, html_content, text_content
    
    @staticmethod
    def create_editor_approved_email(data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Editor 권한 승인 이메일 생성"""
        user_email = data.get('user_email', '')
        property_name = data.get('property_name', 'Unknown')
        applicant = data.get('applicant', user_email)
        
        subject = f"[GA4] Editor 권한 승인 - {property_name}"
        html_content = f"<p>{applicant}님의 Editor 권한이 승인되었습니다.</p><p>계정: {user_email}<br>프로퍼티: {property_name}</p>"
        text_content = f"Editor 권한 승인\n\n{applicant}님의 Editor 권한이 승인되었습니다.\n계정: {user_email}\n프로퍼티: {property_name}"
        
        return subject, html_content, text_content
    
    @staticmethod
    def create_admin_approved_email(data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Admin 권한 승인 이메일 생성"""
        user_email = data.get('user_email', '')
        property_name = data.get('property_name', 'Unknown')
        applicant = data.get('applicant', user_email)
        
        subject = f"[GA4] Admin 권한 승인 - {property_name}"
        html_content = f"<p>{applicant}님의 Admin 권한이 승인되었습니다.</p><p>계정: {user_email}<br>프로퍼티: {property_name}</p>"
        text_content = f"Admin 권한 승인\n\n{applicant}님의 Admin 권한이 승인되었습니다.\n계정: {user_email}\n프로퍼티: {property_name}"
        
        return subject, html_content, text_content
    
    @staticmethod
    def create_editor_downgrade_email(data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Editor 자동 다운그레이드 이메일 생성"""
        user_email = data.get('user_email', '')
        property_name = data.get('property_name', 'Unknown')
        applicant = data.get('applicant', user_email)
        
        subject = f"[GA4] Editor 권한 자동 변경 - {property_name}"
        html_content = f"<p>{applicant}님의 Editor 권한이 Viewer 권한으로 자동 변경되었습니다.</p><p>계정: {user_email}<br>프로퍼티: {property_name}</p>"
        text_content = f"Editor 권한 자동 변경\n\n{applicant}님의 Editor 권한이 Viewer 권한으로 자동 변경되었습니다.\n계정: {user_email}\n프로퍼티: {property_name}"
        
        return subject, html_content, text_content
    
    @staticmethod
    def create_test_email(data: Dict[str, Any]) -> Tuple[str, str, str]:
        """테스트 이메일 생성"""
        user_email = data.get('user_email', '')
        test_timestamp = data.get('test_timestamp', datetime.now().isoformat())
        notification_type = data.get('notification_type', 'test')
        
        subject = f"[GA4] 테스트 알림 - {notification_type}"
        html_content = f"<p>GA4 권한 관리 시스템 테스트 알림입니다.</p><p>대상 이메일: {user_email}<br>알림 타입: {notification_type}<br>발송 시간: {test_timestamp}</p>"
        text_content = f"GA4 권한 관리 시스템 테스트 알림\n\n대상 이메일: {user_email}\n알림 타입: {notification_type}\n발송 시간: {test_timestamp}"
        
        return subject, html_content, text_content 