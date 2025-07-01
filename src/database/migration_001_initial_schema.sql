-- GA 권한 관리 시스템 초기 스키마 생성
-- Migration 001: Initial Schema
-- Created: 2025-07-01

-- ============================================================================
-- 1. website_users 테이블 생성
-- ============================================================================

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

-- website_users 인덱스
CREATE INDEX idx_website_users_email ON website_users(email);
CREATE INDEX idx_website_users_role ON website_users(role);
CREATE INDEX idx_website_users_expires_at ON website_users(role_expires_at);

-- website_users 트리거 (updated_at 자동 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_website_users_updated_at 
    BEFORE UPDATE ON website_users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 2. clients 테이블 생성
-- ============================================================================

CREATE TABLE clients (
    client_id SERIAL PRIMARY KEY,
    client_name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- clients 인덱스
CREATE INDEX idx_clients_name ON clients(client_name);

-- clients 트리거
CREATE TRIGGER update_clients_updated_at 
    BEFORE UPDATE ON clients 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 3. service_accounts 테이블 생성
-- ============================================================================

CREATE TABLE service_accounts (
    sa_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    sa_email VARCHAR(255) NOT NULL,
    secret_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- service_accounts 인덱스
CREATE INDEX idx_service_accounts_client_id ON service_accounts(client_id);
CREATE INDEX idx_service_accounts_email ON service_accounts(sa_email);
CREATE INDEX idx_service_accounts_active ON service_accounts(is_active);

-- service_accounts 트리거
CREATE TRIGGER update_service_accounts_updated_at 
    BEFORE UPDATE ON service_accounts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 4. permission_grants 테이블 생성
-- ============================================================================

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

-- permission_grants 인덱스
CREATE INDEX idx_permission_grants_target_email ON permission_grants(target_email);
CREATE INDEX idx_permission_grants_status ON permission_grants(status);
CREATE INDEX idx_permission_grants_expires_at ON permission_grants(expires_at);
CREATE INDEX idx_permission_grants_ga_property ON permission_grants(ga_property_id);
CREATE INDEX idx_permission_grants_last_notified ON permission_grants(last_notified_type, last_notified_at);
CREATE INDEX idx_permission_grants_requested_by ON permission_grants(requested_by);
CREATE INDEX idx_permission_grants_approved_by ON permission_grants(approved_by);

-- 복합 인덱스 (중복 활성 권한 방지)
CREATE UNIQUE INDEX idx_unique_active_permission 
ON permission_grants(target_email, ga_property_id, status) 
WHERE status = 'active';

-- permission_grants 트리거
CREATE TRIGGER update_permission_grants_updated_at 
    BEFORE UPDATE ON permission_grants 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5. audit_logs 테이블 생성
-- ============================================================================

CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    grant_id INTEGER NOT NULL REFERENCES permission_grants(grant_id) ON DELETE CASCADE,
    actor_email VARCHAR(255) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'approve', 'reject', 'renew', 'upgrade', 'revoke', 'expire')),
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- audit_logs 인덱스
CREATE INDEX idx_audit_logs_grant_id ON audit_logs(grant_id);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_email);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);

-- ============================================================================
-- 6. 권한 만료 기간 설정을 위한 함수
-- ============================================================================

CREATE OR REPLACE FUNCTION get_role_duration_days(role_name VARCHAR)
RETURNS INTEGER AS $$
BEGIN
    CASE role_name
        WHEN 'viewer' THEN RETURN 60;
        WHEN 'analyst' THEN RETURN 60;
        WHEN 'editor' THEN RETURN 7;
        WHEN 'administrator' THEN RETURN 90;
        ELSE RETURN 60; -- 기본값
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. 감사 로그 자동 생성 트리거
-- ============================================================================

CREATE OR REPLACE FUNCTION log_permission_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (grant_id, actor_email, action, details)
        VALUES (NEW.grant_id, 
                (SELECT email FROM website_users WHERE user_id = NEW.requested_by),
                'create',
                jsonb_build_object(
                    'target_email', NEW.target_email,
                    'role', NEW.role,
                    'ga_property_id', NEW.ga_property_id,
                    'expires_at', NEW.expires_at
                ));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- 상태 변경 시 로그 생성
        IF OLD.status != NEW.status THEN
            INSERT INTO audit_logs (grant_id, actor_email, action, details)
            VALUES (NEW.grant_id,
                    COALESCE(
                        (SELECT email FROM website_users WHERE user_id = NEW.approved_by),
                        'system'
                    ),
                    CASE NEW.status
                        WHEN 'active' THEN 'approve'
                        WHEN 'rejected' THEN 'reject'
                        WHEN 'expired' THEN 'expire'
                        WHEN 'revoked' THEN 'revoke'
                        ELSE 'update'
                    END,
                    jsonb_build_object(
                        'old_status', OLD.status,
                        'new_status', NEW.status,
                        'rejection_reason', NEW.rejection_reason
                    ));
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER permission_grants_audit_trigger
    AFTER INSERT OR UPDATE ON permission_grants
    FOR EACH ROW EXECUTE FUNCTION log_permission_changes();

-- ============================================================================
-- 8. 초기 데이터 삽입
-- ============================================================================

-- 첫 번째 Super Admin 생성 (대표자)
INSERT INTO website_users (email, user_name, company, role, is_representative) 
VALUES ('seongwonyoung0311@gmail.com', '영성원', 'GA 서비스 파트너', 'super_admin', TRUE);

-- 테스트용 고객사 생성
INSERT INTO clients (client_name) VALUES ('아모레퍼시픽');
INSERT INTO clients (client_name) VALUES ('테스트 고객사');

-- ============================================================================
-- 9. 유용한 뷰 생성
-- ============================================================================

-- 활성 권한 뷰
CREATE VIEW active_permissions AS
SELECT 
    pg.grant_id,
    pg.target_email,
    pg.role,
    pg.ga_account_id,
    pg.ga_property_id,
    pg.expires_at,
    c.client_name,
    sa.display_name as service_account_name,
    wu.user_name as requested_by_name
FROM permission_grants pg
JOIN service_accounts sa ON pg.sa_id = sa.sa_id
JOIN clients c ON sa.client_id = c.client_id
JOIN website_users wu ON pg.requested_by = wu.user_id
WHERE pg.status = 'active';

-- 만료 예정 권한 뷰 (30일 이내)
CREATE VIEW expiring_permissions AS
SELECT 
    pg.*,
    c.client_name,
    sa.display_name as service_account_name
FROM permission_grants pg
JOIN service_accounts sa ON pg.sa_id = sa.sa_id
JOIN clients c ON sa.client_id = c.client_id
WHERE pg.status = 'active'
AND pg.expires_at <= CURRENT_DATE + INTERVAL '30 days'
ORDER BY pg.expires_at;

-- 승인 대기 권한 뷰
CREATE VIEW pending_approvals AS
SELECT 
    pg.*,
    c.client_name,
    sa.display_name as service_account_name,
    wu.user_name as requested_by_name,
    wu.email as requested_by_email
FROM permission_grants pg
JOIN service_accounts sa ON pg.sa_id = sa.sa_id
JOIN clients c ON sa.client_id = c.client_id
JOIN website_users wu ON pg.requested_by = wu.user_id
WHERE pg.status = 'pending_approval'
ORDER BY pg.created_at;

-- ============================================================================
-- 10. 권한 확인
-- ============================================================================

-- 생성된 테이블 확인
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- 생성된 뷰 확인
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public'
ORDER BY table_name;

COMMENT ON TABLE website_users IS 'GA 권한 관리 시스템 사용자 (Super Admin, Requester)';
COMMENT ON TABLE clients IS '서비스 파트너가 관리하는 고객사 정보';
COMMENT ON TABLE service_accounts IS 'Google Analytics 접근용 Service Account 정보';
COMMENT ON TABLE permission_grants IS 'GA 속성에 대한 사용자 권한 부여 현황';
COMMENT ON TABLE audit_logs IS '모든 권한 변경 이력 감사 로그'; 