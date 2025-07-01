# GA 권한 관리 시스템 데이터베이스 스키마 설계

## 개요

Supabase (PostgreSQL)를 사용한 GA 권한 관리 시스템의 데이터베이스 스키마를 정의합니다.

## 핵심 설계 원칙

1. **정규화**: 데이터 중복 최소화 및 일관성 유지
2. **확장성**: 향후 기능 추가를 고려한 유연한 구조
3. **추적성**: 모든 변경사항에 대한 감사 로그 지원
4. **성능**: 자주 사용되는 쿼리 최적화를 위한 인덱스 설계

## 테이블 구조

### 1. website_users (웹사이트 사용자)

신청자와 Super Admin을 관리하는 테이블입니다.

```sql
CREATE TABLE website_users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    company VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('super_admin', 'requester')),
    role_expires_at TIMESTAMP WITH TIME ZONE,
    is_representative BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_website_users_email ON website_users(email);
CREATE INDEX idx_website_users_role ON website_users(role);
CREATE INDEX idx_website_users_expires_at ON website_users(role_expires_at);
```

**컬럼 설명:**
- `user_id`: 기본키
- `email`: 사용자 이메일 (고유)
- `user_name`: 사용자 이름
- `company`: 소속 회사
- `role`: 사용자 역할 ('super_admin', 'requester')
- `role_expires_at`: 역할 만료일 (requester의 경우 180일)
- `is_representative`: 대표 Super Admin 여부 (알림 발송용)

### 2. clients (고객사)

서비스 파트너가 관리하는 고객사 정보입니다.

```sql
CREATE TABLE clients (
    client_id SERIAL PRIMARY KEY,
    client_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_clients_name ON clients(client_name);
```

**컬럼 설명:**
- `client_id`: 기본키
- `client_name`: 고객사 이름 (예: '아모레퍼시픽')

### 3. service_accounts (Google Service Account)

Google Analytics 접근을 위한 Service Account 정보입니다.

```sql
CREATE TABLE service_accounts (
    sa_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    sa_email VARCHAR(255) NOT NULL,
    secret_name VARCHAR(100) NOT NULL, -- Secret Manager 참조명
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_service_accounts_client_id ON service_accounts(client_id);
CREATE INDEX idx_service_accounts_email ON service_accounts(sa_email);
```

**컬럼 설명:**
- `sa_id`: 기본키
- `client_id`: 소속 고객사 (외래키)
- `sa_email`: Service Account 이메일
- `secret_name`: Secret Manager에 저장된 키 참조명
- `display_name`: 화면 표시용 이름
- `is_active`: 활성 상태

### 4. permission_grants (GA 권한 부여 현황)

GA 속성에 대한 사용자 권한 현황을 관리하는 핵심 테이블입니다.

```sql
CREATE TABLE permission_grants (
    grant_id SERIAL PRIMARY KEY,
    ga_account_id VARCHAR(50) NOT NULL,
    ga_property_id VARCHAR(50) NOT NULL,
    target_email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('viewer', 'analyst', 'editor', 'administrator')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending_approval', 'active', 'expired', 'revoked', 'rejected')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    rejection_reason TEXT,
    last_notified_type VARCHAR(20) CHECK (last_notified_type IN ('welcome', 'expiry_30', 'expiry_7', 'expiry_1', 'expiry_today', 'expired')),
    last_notified_at TIMESTAMP WITH TIME ZONE,
    requested_by INTEGER NOT NULL REFERENCES website_users(user_id),
    approved_by INTEGER REFERENCES website_users(user_id),
    sa_id INTEGER NOT NULL REFERENCES service_accounts(sa_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_permission_grants_target_email ON permission_grants(target_email);
CREATE INDEX idx_permission_grants_status ON permission_grants(status);
CREATE INDEX idx_permission_grants_expires_at ON permission_grants(expires_at);
CREATE INDEX idx_permission_grants_ga_property ON permission_grants(ga_property_id);
CREATE INDEX idx_permission_grants_last_notified ON permission_grants(last_notified_type, last_notified_at);

-- 복합 인덱스 (중복 권한 방지)
CREATE UNIQUE INDEX idx_unique_active_permission 
ON permission_grants(target_email, ga_property_id, status) 
WHERE status = 'active';
```

**컬럼 설명:**
- `grant_id`: 기본키
- `ga_account_id`: GA 계정 ID
- `ga_property_id`: GA 속성 ID
- `target_email`: 권한을 받을 사용자 이메일
- `role`: 권한 역할 ('viewer', 'analyst', 'editor', 'administrator')
- `status`: 권한 상태 ('pending_approval', 'active', 'expired', 'revoked', 'rejected')
- `expires_at`: 권한 만료일
- `rejection_reason`: 거절 사유 (거절 시에만)
- `last_notified_type`: 마지막 발송된 알림 유형 (중복 방지용)
- `last_notified_at`: 마지막 알림 발송 시간
- `requested_by`: 요청자 (외래키)
- `approved_by`: 승인자 (외래키, 수동 승인인 경우)
- `sa_id`: 사용된 Service Account (외래키)

### 5. audit_logs (감사 로그)

모든 권한 변경 이력을 추적하는 테이블입니다.

```sql
CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    grant_id INTEGER NOT NULL REFERENCES permission_grants(grant_id) ON DELETE CASCADE,
    actor_email VARCHAR(255) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'approve', 'reject', 'renew', 'upgrade', 'revoke', 'expire')),
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_audit_logs_grant_id ON audit_logs(grant_id);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_email);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

**컬럼 설명:**
- `log_id`: 기본키
- `grant_id`: 관련된 권한 (외래키)
- `actor_email`: 행위를 수행한 사용자 이메일
- `action`: 수행된 액션 ('create', 'approve', 'reject', 'renew', 'upgrade', 'revoke', 'expire')
- `details`: 변경 상세 정보 (JSON 형태)
- `timestamp`: 액션 수행 시간

## 권한 만료 기간 설정

권한별 기본 만료 기간:

- **Viewer**: 60일
- **Analyst**: 60일  
- **Editor**: 7일
- **Administrator**: 90일
- **Requester 역할**: 180일

## 알림 발송 로직

`permission_grants.last_notified_type` 컬럼을 사용하여 중복 알림 방지:

1. **환영 알림**: 권한 부여 시 'welcome' 기록
2. **만료 예정 알림**: 
   - 30일 전: 'expiry_30' 기록
   - 7일 전: 'expiry_7' 기록  
   - 1일 전: 'expiry_1' 기록
   - 당일: 'expiry_today' 기록
3. **만료 확인**: 권한 삭제 시 'expired' 기록

## 보안 고려사항

1. **Service Account 키**: 실제 JSON 키는 데이터베이스에 저장하지 않고 Secret Manager 참조명만 저장
2. **이메일 검증**: 이메일 형식 검증 및 도메인 제한 가능
3. **권한 최소화**: 각 역할별 최소 필요 권한만 부여
4. **감사 로그**: 모든 변경사항 추적으로 보안 사고 시 추적 가능

## 쿼리 최적화

1. **만료 예정 권한 조회**:
```sql
SELECT * FROM permission_grants 
WHERE status = 'active' 
AND expires_at <= CURRENT_DATE + INTERVAL '30 days'
AND (last_notified_type IS NULL OR last_notified_type != 'expiry_30');
```

2. **사용자별 활성 권한 조회**:
```sql
SELECT * FROM permission_grants 
WHERE target_email = $1 
AND status = 'active'
ORDER BY expires_at;
```

## 다음 단계

1. **Supabase 설정**: 데이터베이스 인스턴스 생성
2. **마이그레이션 스크립트**: DDL 스크립트 작성
3. **초기 데이터**: Super Admin 및 테스트 데이터 생성
4. **백엔드 연동**: Python SQLAlchemy ORM 모델 정의 