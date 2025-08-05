-- Migration 005: Enhanced User Registration System
-- This migration enhances the user registration system with improved relationships,
-- audit logging, and property access workflow

-- Add new enum types for enhanced status tracking
DO $$ BEGIN
    CREATE TYPE registration_status AS ENUM (
        'pending_verification',
        'verified',
        'approved',
        'rejected',
        'suspended'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE property_access_status AS ENUM (
        'requested',
        'approved',
        'denied',
        'revoked',
        'expired'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Enhance users table with registration tracking
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS registration_status registration_status DEFAULT 'pending_verification',
ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS verification_token_expires_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS approval_requested_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS approved_by_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS rejection_reason TEXT,
ADD COLUMN IF NOT EXISTS primary_client_id INTEGER REFERENCES clients(id),
ADD COLUMN IF NOT EXISTS department VARCHAR(100),
ADD COLUMN IF NOT EXISTS job_title VARCHAR(100),
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20);

-- Create indexes for new user fields
CREATE INDEX IF NOT EXISTS idx_users_registration_status ON users(registration_status);
CREATE INDEX IF NOT EXISTS idx_users_email_verified_at ON users(email_verified_at);
CREATE INDEX IF NOT EXISTS idx_users_primary_client_id ON users(primary_client_id);
CREATE INDEX IF NOT EXISTS idx_users_approved_by_id ON users(approved_by_id);

-- Create property access requests table (enhanced version of permission requests)
CREATE TABLE IF NOT EXISTS property_access_requests (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    ga4_property_id INTEGER REFERENCES ga4_properties(id),
    requested_property_id VARCHAR(50) NOT NULL, -- GA4 property ID string
    
    -- Request details
    status property_access_status NOT NULL DEFAULT 'requested',
    permission_level permission_level NOT NULL,
    target_email VARCHAR(255) NOT NULL,
    business_justification TEXT NOT NULL,
    requested_duration_days INTEGER NOT NULL DEFAULT 30 CHECK (requested_duration_days > 0 AND requested_duration_days <= 365),
    
    -- Auto-approval settings
    auto_approved BOOLEAN NOT NULL DEFAULT false,
    requires_approval_from_role user_role,
    
    -- Processing information
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_by_id INTEGER REFERENCES users(id),
    processing_notes TEXT,
    rejection_reason TEXT,
    
    -- Approval workflow
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by_id INTEGER REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Revocation tracking
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by_id INTEGER REFERENCES users(id),
    revocation_reason TEXT,
    
    -- Metadata
    priority_level VARCHAR(20) DEFAULT 'normal' CHECK (priority_level IN ('low', 'normal', 'high', 'urgent')),
    external_ticket_id VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for property access requests
CREATE INDEX IF NOT EXISTS idx_property_access_requests_user_id ON property_access_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_property_access_requests_client_id ON property_access_requests(client_id);
CREATE INDEX IF NOT EXISTS idx_property_access_requests_status ON property_access_requests(status);
CREATE INDEX IF NOT EXISTS idx_property_access_requests_ga4_property_id ON property_access_requests(ga4_property_id);
CREATE INDEX IF NOT EXISTS idx_property_access_requests_requested_property_id ON property_access_requests(requested_property_id);
CREATE INDEX IF NOT EXISTS idx_property_access_requests_processed_by_id ON property_access_requests(processed_by_id);
CREATE INDEX IF NOT EXISTS idx_property_access_requests_approved_by_id ON property_access_requests(approved_by_id);
CREATE INDEX IF NOT EXISTS idx_property_access_requests_created_at ON property_access_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_property_access_requests_priority_level ON property_access_requests(priority_level);

-- Create composite index for duplicate checking
CREATE UNIQUE INDEX IF NOT EXISTS idx_property_access_requests_active_unique 
ON property_access_requests(user_id, requested_property_id, target_email) 
WHERE status IN ('requested', 'approved');

-- Enhance client assignments with more detailed tracking
ALTER TABLE client_assignments 
ADD COLUMN IF NOT EXISTS assignment_type VARCHAR(20) DEFAULT 'manual' CHECK (assignment_type IN ('manual', 'auto', 'inherited')),
ADD COLUMN IF NOT EXISTS department VARCHAR(100),
ADD COLUMN IF NOT EXISTS access_level VARCHAR(20) DEFAULT 'standard' CHECK (access_level IN ('basic', 'standard', 'advanced', 'full')),
ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS deactivated_by_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS deactivation_reason TEXT;

-- Create indexes for enhanced client assignments
CREATE INDEX IF NOT EXISTS idx_client_assignments_assignment_type ON client_assignments(assignment_type);
CREATE INDEX IF NOT EXISTS idx_client_assignments_access_level ON client_assignments(access_level);
CREATE INDEX IF NOT EXISTS idx_client_assignments_last_activity_at ON client_assignments(last_activity_at);
CREATE INDEX IF NOT EXISTS idx_client_assignments_deactivated_by_id ON client_assignments(deactivated_by_id);

-- Create user activity log table for audit trail
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_user_id INTEGER REFERENCES users(id), -- For admin actions on other users
    client_id INTEGER REFERENCES clients(id),
    property_access_request_id INTEGER REFERENCES property_access_requests(id),
    
    -- Activity details
    activity_type VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Additional metadata
    details JSONB,
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    
    -- Timing
    duration_ms INTEGER, -- How long the action took
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for user activity logs
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_target_user_id ON user_activity_logs(target_user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_client_id ON user_activity_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_activity_type ON user_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_action ON user_activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_resource_type ON user_activity_logs(resource_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_success ON user_activity_logs(success);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_ip_address ON user_activity_logs(ip_address);

-- Create GIN index for JSONB details column
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_details ON user_activity_logs USING gin(details);

-- Create user session tracking table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session details
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255) UNIQUE,
    session_data JSONB,
    
    -- Security tracking
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    
    -- Session lifecycle
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Logout tracking
    logged_out_at TIMESTAMP WITH TIME ZONE,
    logout_reason VARCHAR(50), -- 'user_logout', 'timeout', 'admin_revoke', 'security'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for user sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token ON user_sessions(refresh_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity_at ON user_sessions(last_activity_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_address ON user_sessions(ip_address);

-- Create triggers for updating updated_at timestamps
CREATE OR REPLACE FUNCTION update_property_access_requests_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_user_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS trigger_property_access_requests_updated_at ON property_access_requests;
DROP TRIGGER IF EXISTS trigger_user_sessions_updated_at ON user_sessions;

-- Create new triggers
CREATE TRIGGER trigger_property_access_requests_updated_at
    BEFORE UPDATE ON property_access_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_property_access_requests_updated_at();

CREATE TRIGGER trigger_user_sessions_updated_at
    BEFORE UPDATE ON user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_user_sessions_updated_at();

-- Create function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE user_sessions 
    SET is_active = false, 
        logged_out_at = NOW(),
        logout_reason = 'timeout'
    WHERE is_active = true 
      AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to log user activity
CREATE OR REPLACE FUNCTION log_user_activity(
    p_user_id INTEGER,
    p_activity_type VARCHAR(50),
    p_action VARCHAR(100),
    p_resource_type VARCHAR(50) DEFAULT NULL,
    p_resource_id VARCHAR(100) DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_details JSONB DEFAULT NULL,
    p_success BOOLEAN DEFAULT true,
    p_error_message TEXT DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    log_id INTEGER;
BEGIN
    INSERT INTO user_activity_logs (
        user_id, activity_type, action, resource_type, resource_id,
        ip_address, user_agent, details, success, error_message
    ) VALUES (
        p_user_id, p_activity_type, p_action, p_resource_type, p_resource_id,
        p_ip_address, p_user_agent, p_details, p_success, p_error_message
    ) RETURNING id INTO log_id;
    
    RETURN log_id;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE property_access_requests IS 'Enhanced property access requests with comprehensive workflow tracking';
COMMENT ON TABLE user_activity_logs IS 'Comprehensive audit log for all user activities';
COMMENT ON TABLE user_sessions IS 'User session tracking with security features';

COMMENT ON COLUMN users.registration_status IS 'Current registration status of the user';
COMMENT ON COLUMN users.primary_client_id IS 'Primary client assignment for the user';
COMMENT ON COLUMN users.department IS 'User department for organizational tracking';

COMMENT ON COLUMN property_access_requests.priority_level IS 'Request priority for processing queue';
COMMENT ON COLUMN property_access_requests.external_ticket_id IS 'Reference to external ticketing system';

COMMENT ON COLUMN user_activity_logs.details IS 'JSONB field for additional context and metadata';
COMMENT ON COLUMN user_activity_logs.duration_ms IS 'Action execution time in milliseconds';

COMMENT ON COLUMN user_sessions.device_fingerprint IS 'Unique device identifier for security tracking';
COMMENT ON COLUMN user_sessions.session_data IS 'Additional session metadata and preferences';

-- Verify the migration
DO $$
BEGIN
    -- Check if new tables were created
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'property_access_requests') THEN
        RAISE NOTICE 'Migration 005: property_access_requests table created successfully';
    ELSE
        RAISE EXCEPTION 'Migration 005 failed: property_access_requests table not found';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_activity_logs') THEN
        RAISE NOTICE 'Migration 005: user_activity_logs table created successfully';
    ELSE
        RAISE EXCEPTION 'Migration 005 failed: user_activity_logs table not found';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_sessions') THEN
        RAISE NOTICE 'Migration 005: user_sessions table created successfully';
    ELSE
        RAISE EXCEPTION 'Migration 005 failed: user_sessions table not found';
    END IF;
    
    -- Check if new enums were created
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'registration_status') THEN
        RAISE NOTICE 'Migration 005: registration_status enum created successfully';
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'property_access_status') THEN
        RAISE NOTICE 'Migration 005: property_access_status enum created successfully';
    END IF;
    
    RAISE NOTICE 'Migration 005 completed successfully: Enhanced user registration system implemented';
END $$;