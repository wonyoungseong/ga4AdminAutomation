# GA4 권한 관리 시스템 설계 문서

**작성일**: 2025-01-21  
**프로젝트**: GA4 Admin Automation  
**아키텍처**: Clean Architecture + SOLID 원칙  

## 📋 요구사항 요약

### 핵심 기능
1. **GA4 계정/프로퍼티 자동 스캔** - Service Account 접근 가능한 모든 계정/프로퍼티
2. **웹 인터페이스 기반 사용자 등록** - 프로퍼티 선택 후 사용자 등록
3. **권한별 만료 관리** - Analyst(30일), Editor(7일) 자동 삭제
4. **이메일 알림 시스템** - 30/7/1일 전, 당일, 만료 후 알림
5. **연장 신청 처리** - 이메일 응답 기반 30일 연장

### 권한 정책
- **기본 권한**: Analyst (30일 만료)
- **특수 권한**: Editor (7일 만료, 수동 승인 필요)
- **연장**: 이메일 응답으로 30일 연장 가능

## 🏗️ 시스템 아키텍처

### Clean Architecture 레이어

```
┌─────────────────────────────────────┐
│         Presentation Layer          │  웹 인터페이스, API 엔드포인트
├─────────────────────────────────────┤
│         Application Layer           │  비즈니스 로직, 유스케이스
├─────────────────────────────────────┤
│           Domain Layer              │  엔티티, 도메인 서비스
├─────────────────────────────────────┤
│        Infrastructure Layer         │  데이터베이스, 외부 API
└─────────────────────────────────────┘
```

## 📊 데이터베이스 설계

### 1. GA4 계정 테이블 (ga4_accounts)
```sql
CREATE TABLE ga4_accounts (
    account_id TEXT PRIMARY KEY,
    account_display_name TEXT NOT NULL,
    최초_확인일 TIMESTAMP NOT NULL,
    최근_업데이트일 TIMESTAMP NOT NULL,
    삭제여부 BOOLEAN DEFAULT FALSE,
    현재_존재여부 BOOLEAN DEFAULT TRUE,
    service_account_access BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. GA4 프로퍼티 테이블 (ga4_properties)
```sql
CREATE TABLE ga4_properties (
    property_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    property_display_name TEXT NOT NULL,
    property_type TEXT,
    최초_확인일 TIMESTAMP NOT NULL,
    최근_업데이트일 TIMESTAMP NOT NULL,
    삭제여부 BOOLEAN DEFAULT FALSE,
    현재_존재여부 BOOLEAN DEFAULT TRUE,
    등록_가능여부 BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES ga4_accounts(account_id)
);
```

### 3. 사용자 등록 테이블 (user_registrations)
```sql
CREATE TABLE user_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    신청자 TEXT NOT NULL,
    등록_계정 TEXT NOT NULL,
    property_id TEXT NOT NULL,
    권한 TEXT NOT NULL CHECK (권한 IN ('analyst', 'editor')),
    신청일 TIMESTAMP NOT NULL,
    종료일 TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expired', 'deleted', 'pending_approval')),
    approval_required BOOLEAN DEFAULT FALSE,
    연장_횟수 INTEGER DEFAULT 0,
    최근_연장일 TIMESTAMP,
    binding_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES ga4_properties(property_id)
);
```

### 4. 알림 로그 테이블 (notification_logs)
```sql
CREATE TABLE notification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_registration_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('30_days', '7_days', '1_day', 'today', 'expired', 'extension_approved')),
    sent_to TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_subject TEXT,
    message_body TEXT,
    response_received BOOLEAN DEFAULT FALSE,
    response_content TEXT,
    FOREIGN KEY (user_registration_id) REFERENCES user_registrations(id)
);
```

### 5. 감사 로그 테이블 (audit_logs)
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    performed_by TEXT,
    action_details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    error_message TEXT
);
```

## 🎯 도메인 모델

### 1. GA4Account 엔티티
```python
@dataclass
class GA4Account:
    account_id: str
    display_name: str
    최초_확인일: datetime
    최근_업데이트일: datetime
    삭제여부: bool = False
    현재_존재여부: bool = True
    service_account_access: bool = True
```

### 2. GA4Property 엔티티
```python
@dataclass
class GA4Property:
    property_id: str
    account_id: str
    display_name: str
    property_type: str
    최초_확인일: datetime
    최근_업데이트일: datetime
    삭제여부: bool = False
    현재_존재여부: bool = True
    등록_가능여부: bool = True
```

### 3. UserRegistration 엔티티
```python
@dataclass
class UserRegistration:
    신청자: str
    등록_계정: str
    property_id: str
    권한: PermissionLevel
    신청일: datetime
    종료일: datetime
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    approval_required: bool = False
    연장_횟수: int = 0
    최근_연장일: Optional[datetime] = None
    binding_id: Optional[str] = None
```

## 🔧 핵심 서비스

### 1. GA4PropertyScannerService
```python
class GA4PropertyScannerService:
    """GA4 계정/프로퍼티 스캔 서비스"""
    
    async def scan_all_accounts_and_properties(self) -> ScanResult:
        """모든 접근 가능한 계정/프로퍼티 스캔"""
        
    async def update_property_dataset(self) -> None:
        """프로퍼티 데이터셋 업데이트"""
        
    async def check_property_accessibility(self, property_id: str) -> bool:
        """프로퍼티 접근 가능성 확인"""
```

### 2. UserRegistrationService
```python
class UserRegistrationService:
    """사용자 등록 관리 서비스"""
    
    async def register_user(self, registration_request: UserRegistrationRequest) -> UserRegistration:
        """사용자 등록 처리"""
        
    async def approve_editor_request(self, registration_id: int) -> bool:
        """Editor 권한 수동 승인"""
        
    async def extend_user_permission(self, registration_id: int, extension_days: int = 30) -> bool:
        """권한 연장 처리"""
```

### 3. ExpiryNotificationService
```python
class ExpiryNotificationService:
    """만료 알림 서비스"""
    
    async def check_and_send_expiry_notifications(self) -> NotificationSummary:
        """만료 알림 확인 및 발송"""
        
    async def process_extension_email_responses(self) -> List[ExtensionRequest]:
        """연장 신청 이메일 응답 처리"""
        
    async def send_daily_admin_summary(self) -> bool:
        """관리자 일일 요약 발송"""
```

### 4. AutoDeletionService
```python
class AutoDeletionService:
    """자동 삭제 서비스"""
    
    async def delete_expired_users(self) -> DeletionSummary:
        """만료된 사용자 자동 삭제"""
        
    async def send_deletion_notifications(self, deleted_users: List[UserRegistration]) -> None:
        """삭제 알림 발송"""
```

## 🌐 웹 인터페이스 설계

### 1. 메인 대시보드
- 등록 가능한 프로퍼티 목록 (체크박스 선택)
- 현재 등록된 사용자 현황
- 만료 예정 사용자 알림

### 2. 사용자 등록 페이지
- 프로퍼티 선택 (다중 선택 가능)
- 사용자 이메일 입력 (쉼표 구분 또는 CSV 업로드)
- 권한 선택 (Analyst 기본, Editor 수동 승인)
- 신청자 정보 입력

### 3. 관리 페이지
- Editor 권한 승인 대기 목록
- 연장 신청 처리
- 사용자 검색 및 관리

## ⏰ 스케줄링 시스템

### 일일 스케줄 (매일 오전 9시)
```python
schedule.every().day.at("09:00").do(daily_tasks)

async def daily_tasks():
    # 1. GA4 프로퍼티 스캔 및 업데이트
    await property_scanner.scan_all_accounts_and_properties()
    
    # 2. 만료 알림 확인 및 발송
    notification_summary = await notification_service.check_and_send_expiry_notifications()
    
    # 3. 만료된 사용자 자동 삭제
    deletion_summary = await auto_deletion_service.delete_expired_users()
    
    # 4. 관리자 일일 요약 발송
    await notification_service.send_daily_admin_summary()
    
    # 5. 데이터베이스 백업 (주 1회)
    if datetime.now().weekday() == 0:  # 월요일
        await backup_service.create_weekly_backup()
```

## 📧 알림 시스템

### 알림 유형별 템플릿

#### 1. 만료 예정 알림 (30/7/1일 전)
```
제목: [GA4 권한] {property_name} 권한이 {days}일 후 만료됩니다
내용: 
- 권한 정보: {권한} 권한
- 만료일: {종료일}
- 연장 신청: 이 이메일에 "연장"이라고 답장해 주세요
```

#### 2. 당일 만료 알림
```
제목: [GA4 권한] {property_name} 권한이 오늘 만료됩니다
내용: 긴급 - 오늘 자정에 권한이 자동 삭제됩니다
```

#### 3. 관리자 일일 요약
```
제목: [GA4 관리] 일일 권한 관리 요약 - {date}
내용:
- 오늘 처리 대상: {count}건
- 신규 등록: {new_registrations}건
- 만료 삭제: {deletions}건
- 연장 처리: {extensions}건
```

## 🔐 보안 고려사항

1. **Service Account 키 보안**: config/ 폴더에 안전하게 저장
2. **이메일 인증**: OAuth2 토큰 기반 Gmail API 사용
3. **입력 검증**: 이메일 형식, 권한 레벨 검증
4. **감사 로그**: 모든 권한 변경 작업 기록
5. **백업**: 주간 자동 백업으로 데이터 보호

## 📈 확장성 고려사항

1. **다중 Service Account 지원**: 향후 여러 Service Account 관리
2. **권한 레벨 확장**: Admin, Viewer 권한 추가 가능
3. **알림 채널 확장**: Slack, Teams 등 추가 알림 채널
4. **API 제공**: 외부 시스템 연동을 위한 REST API
5. **대시보드 확장**: 상세 분석 및 리포팅 기능

## 🚀 개발 단계

### Phase 1: 기반 시스템 구축
1. 데이터베이스 스키마 생성
2. GA4 프로퍼티 스캔 서비스 개발
3. 기본 웹 인터페이스 구축

### Phase 2: 사용자 관리 기능
1. 사용자 등록 시스템 개발
2. 권한 관리 로직 구현
3. 수동 승인 워크플로우

### Phase 3: 알림 및 자동화
1. 만료 알림 시스템 구현
2. 자동 삭제 기능 개발
3. 스케줄링 시스템 구축

### Phase 4: 고도화
1. 연장 신청 처리 자동화
2. 관리자 대시보드 고도화
3. 리포팅 및 분석 기능

이 설계를 바탕으로 체계적인 개발을 진행하겠습니다! 