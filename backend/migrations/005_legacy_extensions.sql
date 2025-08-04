-- Migration 005: Legacy Extensions - GA4Property, UserPermission, NotificationLog, ReportDownloadLog
-- This migration extends the Backend to Legacy-level completeness

-- Add new enum types
DO $$ BEGIN
    CREATE TYPE notification_channel AS ENUM ('email', 'slack');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed', 'retrying');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE report_type AS ENUM ('user_activity', 'permission_summary', 'audit_log', 'system_metrics', 'compliance_report');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create GA4 Properties table
CREATE TABLE IF NOT EXISTS ga4_properties (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- GA4 Property Information
    property_id VARCHAR(50) UNIQUE NOT NULL, -- properties/123456789
    property_name VARCHAR(255) NOT NULL,
    account_id VARCHAR(50) NOT NULL, -- accounts/123456
    account_name VARCHAR(255) NOT NULL,
    
    -- Property Settings
    website_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'Asia/Seoul',
    currency_code VARCHAR(3) DEFAULT 'KRW',
    
    -- Auto-approval Settings
    auto_approval_enabled BOOLEAN DEFAULT FALSE,
    max_permission_duration_days INTEGER DEFAULT 90,
    
    -- Sync Management
    is_active BOOLEAN DEFAULT TRUE,
    sync_enabled BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Create User Permissions table (direct mapping)
CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ga_property_id INTEGER NOT NULL REFERENCES ga4_properties(id) ON DELETE CASCADE,
    
    -- Permission Details
    target_email VARCHAR(255) NOT NULL,
    permission_level permission_level NOT NULL,
    
    -- Lifecycle Management
    status permission_status DEFAULT 'approved',
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Extension Tracking
    extension_count INTEGER DEFAULT 0,
    original_expires_at TIMESTAMPTZ NOT NULL,
    
    -- Revocation Tracking
    revoked_at TIMESTAMPTZ,
    revoked_by_id INTEGER REFERENCES users(id),
    revocation_reason TEXT,
    
    -- GA4 Integration
    google_permission_id VARCHAR(500), -- Google's permission ID
    synchronized_at TIMESTAMPTZ,
    sync_status VARCHAR(20) DEFAULT 'pending', -- pending, synced, failed
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add extension tracking fields to permission_grants
ALTER TABLE permission_grants 
ADD COLUMN IF NOT EXISTS extension_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS original_expires_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS revoked_by_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS revocation_reason TEXT;

-- Create Notification Logs table
CREATE TABLE IF NOT EXISTS notification_logs (
    id SERIAL PRIMARY KEY,
    
    -- Reference to audit log
    audit_log_id INTEGER REFERENCES audit_logs(id) ON DELETE CASCADE,
    
    -- Notification Details
    channel notification_channel NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    
    -- Message Content
    subject VARCHAR(255),
    message_body TEXT,
    template_data TEXT, -- JSON string
    
    -- Delivery Status
    status notification_status DEFAULT 'pending',
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create Report Download Logs table
CREATE TABLE IF NOT EXISTS report_download_logs (
    id SERIAL PRIMARY KEY,
    
    -- User Information
    admin_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Report Information
    report_type report_type NOT NULL,
    report_id VARCHAR(255) NOT NULL,
    report_name VARCHAR(255),
    file_format VARCHAR(10) DEFAULT 'json', -- json, csv, excel
    
    -- Download Details
    downloaded_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address VARCHAR(45), -- IPv6 support
    user_agent TEXT,
    
    -- File Information
    file_size_bytes INTEGER,
    file_path VARCHAR(500)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ga4_properties_client_id ON ga4_properties(client_id);
CREATE INDEX IF NOT EXISTS idx_ga4_properties_property_id ON ga4_properties(property_id);
CREATE INDEX IF NOT EXISTS idx_ga4_properties_active ON ga4_properties(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_ga4_properties_sync_needed ON ga4_properties(sync_enabled, last_synced_at) WHERE sync_enabled = TRUE;

CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_property_id ON user_permissions(ga_property_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_status ON user_permissions(status);
CREATE INDEX IF NOT EXISTS idx_user_permissions_expires_at ON user_permissions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_permissions_active ON user_permissions(status, expires_at) WHERE status = 'approved';

CREATE INDEX IF NOT EXISTS idx_notification_logs_recipient ON notification_logs(recipient);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at ON notification_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_report_download_logs_admin_id ON report_download_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_report_download_logs_report_type ON report_download_logs(report_type);
CREATE INDEX IF NOT EXISTS idx_report_download_logs_downloaded_at ON report_download_logs(downloaded_at);

-- Create unique constraints
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_permissions_unique 
ON user_permissions(user_id, ga_property_id, target_email) 
WHERE status = 'approved';

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to ga4_properties
DROP TRIGGER IF EXISTS update_ga4_properties_updated_at ON ga4_properties;
CREATE TRIGGER update_ga4_properties_updated_at
    BEFORE UPDATE ON ga4_properties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply updated_at trigger to user_permissions
DROP TRIGGER IF EXISTS update_user_permissions_updated_at ON user_permissions;
CREATE TRIGGER update_user_permissions_updated_at
    BEFORE UPDATE ON user_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO ga4_properties (client_id, property_id, property_name, account_id, account_name, auto_approval_enabled)
SELECT 
    c.id,
    'properties/' || (random() * 1000000000)::bigint,
    c.name || ' Analytics Property',
    'accounts/' || (random() * 100000000)::bigint,
    c.name || ' Analytics Account',
    TRUE
FROM clients c
WHERE NOT EXISTS (
    SELECT 1 FROM ga4_properties WHERE client_id = c.id
)
LIMIT 5;

-- Comments for documentation
COMMENT ON TABLE ga4_properties IS 'GA4 Property independent entity - Legacy compatible';
COMMENT ON TABLE user_permissions IS 'User-Property direct permission mapping - Legacy style';
COMMENT ON TABLE notification_logs IS 'Notification log table - Legacy compatible';
COMMENT ON TABLE report_download_logs IS 'Report download log - Legacy compatible';

COMMENT ON COLUMN ga4_properties.auto_approval_enabled IS 'Whether Viewer/Analyst permissions can be auto-approved';
COMMENT ON COLUMN ga4_properties.max_permission_duration_days IS 'Maximum permission duration in days';
COMMENT ON COLUMN ga4_properties.sync_enabled IS 'Whether GA4 sync is enabled for this property';

COMMENT ON COLUMN user_permissions.extension_count IS 'Number of times permission has been extended';
COMMENT ON COLUMN user_permissions.original_expires_at IS 'Original expiry date before any extensions';
COMMENT ON COLUMN user_permissions.sync_status IS 'GA4 synchronization status: pending, synced, failed';