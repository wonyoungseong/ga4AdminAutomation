-- Migration 005: Legacy Extensions for SQLite - GA4Property, UserPermission, NotificationLog, ReportDownloadLog
-- This migration extends the Backend to Legacy-level completeness

-- Create GA4 Properties table
CREATE TABLE IF NOT EXISTS ga4_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    
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
    auto_approval_enabled BOOLEAN DEFAULT 0,
    max_permission_duration_days INTEGER DEFAULT 90,
    
    -- Sync Management
    is_active BOOLEAN DEFAULT 1,
    sync_enabled BOOLEAN DEFAULT 1,
    last_synced_at DATETIME,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Create User Permissions table (direct mapping)
CREATE TABLE IF NOT EXISTS user_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Relationships
    user_id INTEGER NOT NULL,
    ga_property_id INTEGER NOT NULL,
    
    -- Permission Details
    target_email VARCHAR(255) NOT NULL,
    permission_level VARCHAR(20) NOT NULL, -- viewer, analyst, editor, admin
    
    -- Lifecycle Management
    status VARCHAR(20) DEFAULT 'approved', -- pending, approved, denied, expired, revoked
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    
    -- Extension Tracking
    extension_count INTEGER DEFAULT 0,
    original_expires_at DATETIME NOT NULL,
    
    -- Revocation Tracking
    revoked_at DATETIME,
    revoked_by_id INTEGER,
    revocation_reason TEXT,
    
    -- GA4 Integration
    google_permission_id VARCHAR(500), -- Google's permission ID
    synchronized_at DATETIME,
    sync_status VARCHAR(20) DEFAULT 'pending', -- pending, synced, failed
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ga_property_id) REFERENCES ga4_properties(id) ON DELETE CASCADE,
    FOREIGN KEY (revoked_by_id) REFERENCES users(id)
);

-- Create Notification Logs table
CREATE TABLE IF NOT EXISTS notification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Reference to audit log
    audit_log_id INTEGER,
    
    -- Notification Details
    channel VARCHAR(20) NOT NULL, -- email, slack
    recipient VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) NOT NULL,
    
    -- Message Content
    subject VARCHAR(255),
    message_body TEXT,
    template_data TEXT, -- JSON string
    
    -- Delivery Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed, retrying
    sent_at DATETIME,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (audit_log_id) REFERENCES audit_logs(id) ON DELETE CASCADE
);

-- Create Report Download Logs table
CREATE TABLE IF NOT EXISTS report_download_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- User Information
    admin_id INTEGER NOT NULL,
    
    -- Report Information
    report_type VARCHAR(50) NOT NULL, -- user_activity, permission_summary, audit_log, system_metrics, compliance_report
    report_id VARCHAR(255) NOT NULL,
    report_name VARCHAR(255),
    file_format VARCHAR(10) DEFAULT 'json', -- json, csv, excel
    
    -- Download Details
    downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45), -- IPv6 support
    user_agent TEXT,
    
    -- File Information
    file_size_bytes INTEGER,
    file_path VARCHAR(500),
    
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ga4_properties_client_id ON ga4_properties(client_id);
CREATE INDEX IF NOT EXISTS idx_ga4_properties_property_id ON ga4_properties(property_id);
CREATE INDEX IF NOT EXISTS idx_ga4_properties_active ON ga4_properties(is_active);
CREATE INDEX IF NOT EXISTS idx_ga4_properties_sync_needed ON ga4_properties(sync_enabled, last_synced_at);

CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_property_id ON user_permissions(ga_property_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_status ON user_permissions(status);
CREATE INDEX IF NOT EXISTS idx_user_permissions_expires_at ON user_permissions(expires_at);

CREATE INDEX IF NOT EXISTS idx_notification_logs_recipient ON notification_logs(recipient);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at ON notification_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_report_download_logs_admin_id ON report_download_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_report_download_logs_report_type ON report_download_logs(report_type);
CREATE INDEX IF NOT EXISTS idx_report_download_logs_downloaded_at ON report_download_logs(downloaded_at);

-- Create unique constraints
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_permissions_unique 
ON user_permissions(user_id, ga_property_id, target_email);