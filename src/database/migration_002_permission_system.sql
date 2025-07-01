-- Migration 002: 권한 관리 시스템 테이블 생성
-- 작성일: 2025-07-01
-- 설명: GA 권한 관리 자동화를 위한 핵심 테이블들을 생성합니다

-- 1. clients 테이블: 고객사 정보 관리
CREATE TABLE IF NOT EXISTS clients (
    client_id SERIAL PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL UNIQUE, -- 아모레퍼시픽 등 고객사명
    display_name VARCHAR(255) NOT NULL, -- 화면 표시용 이름
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. service_accounts 테이블: Google Service Account 정보
CREATE TABLE IF NOT EXISTS service_accounts (
    sa_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    sa_email VARCHAR(255) NOT NULL, -- Service Account 이메일
    sa_name VARCHAR(255) NOT NULL, -- Service Account 이름
    secret_reference VARCHAR(500), -- Secret Manager 등의 키 참조 (보안)
    ga_account_ids TEXT[], -- 접근 가능한 GA Account ID 배열
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(client_id, sa_email)
);

-- 3. permission_grants 테이블: GA 권한 부여 현황 (핵심 테이블)
CREATE TABLE IF NOT EXISTS permission_grants (
    grant_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id),
    sa_id INTEGER NOT NULL REFERENCES service_accounts(sa_id),
    ga_account_id VARCHAR(100) NOT NULL, -- GA 계정 ID
    ga_property_id VARCHAR(100) NOT NULL, -- GA 속성 ID
    target_email VARCHAR(255) NOT NULL, -- 권한을 받는 사용자 이메일
    target_name VARCHAR(255), -- 권한을 받는 사용자 이름
    requested_by INTEGER REFERENCES website_users(user_id), -- 신청한 사용자
    permission_level VARCHAR(20) NOT NULL CHECK (permission_level IN ('viewer', 'analyst', 'editor', 'administrator')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'approved', 'active', 'rejected', 'expired', 'revoked')),
    requested_duration_days INTEGER NOT NULL CHECK (requested_duration_days > 0),
    justification TEXT NOT NULL, -- 신청 사유
    
    -- 승인/거부 관련
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by INTEGER REFERENCES website_users(user_id),
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejected_by INTEGER REFERENCES website_users(user_id),
    rejected_reason TEXT,
    
    -- 만료 관리
    expires_at TIMESTAMP WITH TIME ZONE,
    auto_extend BOOLEAN DEFAULT false, -- viewer/analyst 자동 연장 여부
    
    -- 알림 관리 (중복 방지)
    last_notified_type VARCHAR(20) CHECK (last_notified_type IN ('welcome', 'expiry_30', 'expiry_7', 'expiry_1', 'expiry_today', 'expired')),
    last_notified_at TIMESTAMP WITH TIME ZONE,
    
    -- GA API 연동 정보
    ga_binding_name VARCHAR(500), -- GA API에서 반환하는 바인딩명 (삭제 시 사용)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. website_users 테이블 업데이트 (기존 테이블에 컬럼 추가)
-- role_expires_at 컬럼은 이미 존재하므로 추가 컬럼만 생성

-- 신청자 역할 상태 추가
DO $$
BEGIN
    -- status 컬럼이 없으면 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='website_users' AND column_name='status') THEN
        ALTER TABLE website_users ADD COLUMN status VARCHAR(20) DEFAULT 'active' 
            CHECK (status IN ('active', 'expired', 'suspended'));
    END IF;
    
    -- 신청자 역할의 마지막 알림 정보
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='website_users' AND column_name='last_role_notified_type') THEN
        ALTER TABLE website_users ADD COLUMN last_role_notified_type VARCHAR(20) 
            CHECK (last_role_notified_type IN ('role_expiry_30', 'role_expiry_7', 'role_expiry_1', 'role_expiry_today'));
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='website_users' AND column_name='last_role_notified_at') THEN
        ALTER TABLE website_users ADD COLUMN last_role_notified_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- 자동 갱신 여부 (requester 역할용)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='website_users' AND column_name='auto_renew_role') THEN
        ALTER TABLE website_users ADD COLUMN auto_renew_role BOOLEAN DEFAULT true;
    END IF;
END $$;

-- 5. audit_logs 테이블: 모든 권한 변경 이력 추적
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id SERIAL PRIMARY KEY,
    grant_id INTEGER REFERENCES permission_grants(grant_id),
    user_id INTEGER REFERENCES website_users(user_id),
    action VARCHAR(50) NOT NULL, -- 'create', 'approve', 'reject', 'renew', 'upgrade', 'revoke', 'expire'
    actor_email VARCHAR(255) NOT NULL, -- 실행한 사람
    target_email VARCHAR(255), -- 대상 사용자
    details JSONB, -- 변경 상세 정보 (이전 값, 새 값 등)
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET, -- 보안 감사용
    user_agent TEXT -- 보안 감사용
);

-- 6. system_configurations 테이블: 시스템 설정 관리
CREATE TABLE IF NOT EXISTS system_configurations (
    config_id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 기본 시스템 설정 삽입
INSERT INTO system_configurations (config_key, config_value, description) VALUES
('viewer_default_days', '60', 'Viewer 권한 기본 유효 기간 (일)'),
('analyst_default_days', '60', 'Analyst 권한 기본 유효 기간 (일)'),
('editor_default_days', '7', 'Editor 권한 기본 유효 기간 (일)'),
('administrator_default_days', '90', 'Administrator 권한 기본 유효 기간 (일)'),
('requester_role_days', '180', '신청자 역할 유효 기간 (일)'),
('notification_sender_email', 'seongwonyoung0311@gmail.com', '알림 발송자 이메일'),
('daily_report_enabled', 'true', '일일 리포트 발송 여부'),
('auto_cleanup_enabled', 'true', '자동 정리 기능 활성화 여부')
ON CONFLICT (config_key) DO NOTHING;

-- 7. 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_permission_grants_status ON permission_grants(status);
CREATE INDEX IF NOT EXISTS idx_permission_grants_expires_at ON permission_grants(expires_at);
CREATE INDEX IF NOT EXISTS idx_permission_grants_target_email ON permission_grants(target_email);
CREATE INDEX IF NOT EXISTS idx_permission_grants_property ON permission_grants(ga_property_id);
CREATE INDEX IF NOT EXISTS idx_website_users_role_expires ON website_users(role_expires_at) WHERE role = 'requester';
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_grant_id ON audit_logs(grant_id);

-- 8. 뷰 생성 (조회 편의성)

-- 활성 권한 요약 뷰
CREATE OR REPLACE VIEW active_permissions_summary AS
SELECT 
    pg.grant_id,
    c.client_name,
    sa.sa_email,
    pg.ga_property_id,
    pg.target_email,
    pg.target_name,
    pg.permission_level,
    pg.expires_at,
    EXTRACT(DAY FROM (pg.expires_at - NOW())) as days_until_expiry,
    wu.user_name as requested_by_name,
    pg.created_at
FROM permission_grants pg
JOIN clients c ON pg.client_id = c.client_id
JOIN service_accounts sa ON pg.sa_id = sa.sa_id
LEFT JOIN website_users wu ON pg.requested_by = wu.user_id
WHERE pg.status = 'active'
ORDER BY pg.expires_at ASC;

-- 승인 대기 요청 뷰
CREATE OR REPLACE VIEW pending_approval_requests AS
SELECT 
    pg.grant_id,
    c.client_name,
    pg.ga_property_id,
    pg.target_email,
    pg.target_name,
    pg.permission_level,
    pg.requested_duration_days,
    pg.justification,
    wu.user_name as requested_by_name,
    wu.email as requested_by_email,
    pg.created_at
FROM permission_grants pg
JOIN clients c ON pg.client_id = c.client_id
LEFT JOIN website_users wu ON pg.requested_by = wu.user_id
WHERE pg.status = 'pending'
ORDER BY pg.created_at ASC;

-- 만료 예정 권한 뷰 (30일 이내)
CREATE OR REPLACE VIEW expiring_permissions AS
SELECT 
    pg.grant_id,
    c.client_name,
    pg.ga_property_id,
    pg.target_email,
    pg.target_name,
    pg.permission_level,
    pg.expires_at,
    EXTRACT(DAY FROM (pg.expires_at - NOW())) as days_until_expiry,
    pg.last_notified_type,
    CASE 
        WHEN EXTRACT(DAY FROM (pg.expires_at - NOW())) <= 0 THEN 'expired'
        WHEN EXTRACT(DAY FROM (pg.expires_at - NOW())) <= 1 THEN 'expiry_today'
        WHEN EXTRACT(DAY FROM (pg.expires_at - NOW())) <= 7 THEN 'expiry_7'
        WHEN EXTRACT(DAY FROM (pg.expires_at - NOW())) <= 30 THEN 'expiry_30'
        ELSE 'not_expiring'
    END as notification_type
FROM permission_grants pg
JOIN clients c ON pg.client_id = c.client_id
WHERE pg.status = 'active' 
  AND pg.expires_at <= NOW() + INTERVAL '30 days'
ORDER BY pg.expires_at ASC;

-- 9. 트리거 생성 (자동 업데이트)

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 각 테이블에 updated_at 트리거 적용
DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_service_accounts_updated_at ON service_accounts;
CREATE TRIGGER update_service_accounts_updated_at BEFORE UPDATE ON service_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_permission_grants_updated_at ON permission_grants;
CREATE TRIGGER update_permission_grants_updated_at BEFORE UPDATE ON permission_grants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_configurations_updated_at ON system_configurations;
CREATE TRIGGER update_system_configurations_updated_at BEFORE UPDATE ON system_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 10. 권한 설정
-- RLS (Row Level Security) 설정은 추후 필요시 적용

-- 마이그레이션 완료 로그
INSERT INTO audit_logs (action, actor_email, details, timestamp) VALUES 
('migration_002', 'system', '{"description": "권한 관리 시스템 테이블 생성 완료"}', NOW());

COMMENT ON TABLE clients IS '고객사 정보 관리 테이블';
COMMENT ON TABLE service_accounts IS 'Google Service Account 정보 관리 테이블';
COMMENT ON TABLE permission_grants IS 'GA 권한 부여 현황 관리 핵심 테이블';
COMMENT ON TABLE audit_logs IS '모든 권한 변경 이력 추적 테이블';
COMMENT ON TABLE system_configurations IS '시스템 설정 관리 테이블'; 