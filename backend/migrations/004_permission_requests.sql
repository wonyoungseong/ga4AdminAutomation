-- Migration 004: Add Permission Request System
-- This migration adds the permission request workflow system

-- Add new enum type for permission request status
DO $$ BEGIN
    CREATE TYPE permission_request_status AS ENUM (
        'pending',
        'auto_approved', 
        'approved',
        'rejected',
        'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create permission_requests table
CREATE TABLE IF NOT EXISTS permission_requests (
    id SERIAL PRIMARY KEY,
    
    -- Foreign keys
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    
    -- GA4 specific fields
    ga_property_id VARCHAR(50) NOT NULL,
    target_email VARCHAR(255) NOT NULL,
    permission_level permission_level NOT NULL,
    
    -- Request details
    status permission_request_status NOT NULL DEFAULT 'pending',
    business_justification TEXT,
    requested_duration_days INTEGER CHECK (requested_duration_days > 0 AND requested_duration_days <= 365),
    
    -- Auto-approval tracking
    auto_approved BOOLEAN NOT NULL DEFAULT false,
    requires_approval_from_role user_role,
    
    -- Processing details
    processed_at TIMESTAMP WITH TIME ZONE,
    processed_by_id INTEGER REFERENCES users(id),
    processing_notes TEXT,
    
    -- Link to created permission grant
    permission_grant_id INTEGER REFERENCES permission_grants(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for permission_requests
CREATE INDEX IF NOT EXISTS idx_permission_requests_user_id ON permission_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_permission_requests_client_id ON permission_requests(client_id);
CREATE INDEX IF NOT EXISTS idx_permission_requests_status ON permission_requests(status);
CREATE INDEX IF NOT EXISTS idx_permission_requests_ga_property_id ON permission_requests(ga_property_id);
CREATE INDEX IF NOT EXISTS idx_permission_requests_target_email ON permission_requests(target_email);
CREATE INDEX IF NOT EXISTS idx_permission_requests_processed_by_id ON permission_requests(processed_by_id);
CREATE INDEX IF NOT EXISTS idx_permission_requests_created_at ON permission_requests(created_at DESC);

-- Create composite index for duplicate checking
CREATE UNIQUE INDEX IF NOT EXISTS idx_permission_requests_active_unique 
ON permission_requests(user_id, ga_property_id, target_email) 
WHERE status IN ('pending', 'auto_approved');

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_permission_requests_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_permission_requests_updated_at ON permission_requests;
CREATE TRIGGER trigger_permission_requests_updated_at
    BEFORE UPDATE ON permission_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_permission_requests_updated_at();

-- Add comments for documentation
COMMENT ON TABLE permission_requests IS 'Permission requests for GA4 property access before they become grants';
COMMENT ON COLUMN permission_requests.user_id IS 'User who submitted the request';
COMMENT ON COLUMN permission_requests.client_id IS 'Client the user is requesting access for';
COMMENT ON COLUMN permission_requests.ga_property_id IS 'GA4 Property ID being requested';
COMMENT ON COLUMN permission_requests.target_email IS 'Email address to grant permission to';
COMMENT ON COLUMN permission_requests.permission_level IS 'Requested permission level';
COMMENT ON COLUMN permission_requests.status IS 'Current status of the request';
COMMENT ON COLUMN permission_requests.business_justification IS 'Business reason for the access request';
COMMENT ON COLUMN permission_requests.requested_duration_days IS 'Requested access duration in days';
COMMENT ON COLUMN permission_requests.auto_approved IS 'Whether the request was automatically approved';
COMMENT ON COLUMN permission_requests.requires_approval_from_role IS 'Minimum role required to approve this request';
COMMENT ON COLUMN permission_requests.processed_at IS 'When the request was processed (approved/rejected)';
COMMENT ON COLUMN permission_requests.processed_by_id IS 'User who processed the request';
COMMENT ON COLUMN permission_requests.processing_notes IS 'Notes from the approver/rejecter';
COMMENT ON COLUMN permission_requests.permission_grant_id IS 'Linked permission grant if approved';

-- Create some sample data (optional, for testing)
-- Uncomment the following section if you want test data

/*
-- Insert sample permission requests (only if tables exist and have data)
DO $$
DECLARE
    test_user_id INTEGER;
    test_client_id INTEGER;
BEGIN
    -- Check if we have test data
    SELECT id INTO test_user_id FROM users WHERE email = 'test@example.com' LIMIT 1;
    SELECT id INTO test_client_id FROM clients WHERE name LIKE '%Test%' LIMIT 1;
    
    IF test_user_id IS NOT NULL AND test_client_id IS NOT NULL THEN
        -- Insert a pending request
        INSERT INTO permission_requests (
            user_id, client_id, ga_property_id, target_email, 
            permission_level, status, business_justification, 
            requested_duration_days, auto_approved, requires_approval_from_role
        ) VALUES (
            test_user_id, test_client_id, 'GA4-TEST-12345', 'test@example.com',
            'viewer', 'pending', 'Need access for monthly reporting', 
            30, false, 'Admin'
        );
        
        -- Insert an auto-approved request
        INSERT INTO permission_requests (
            user_id, client_id, ga_property_id, target_email, 
            permission_level, status, business_justification, 
            requested_duration_days, auto_approved, requires_approval_from_role,
            processed_at
        ) VALUES (
            test_user_id, test_client_id, 'GA4-TEST-67890', 'test@example.com',
            'analyst', 'auto_approved', 'Regular analytics work', 
            30, true, null, NOW()
        );
    END IF;
END $$;
*/

-- Verify the migration
DO $$
BEGIN
    -- Check if the table was created successfully
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'permission_requests') THEN
        RAISE NOTICE 'Migration 004 completed successfully: permission_requests table created';
    ELSE
        RAISE EXCEPTION 'Migration 004 failed: permission_requests table not found';
    END IF;
    
    -- Check if the enum was created
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'permission_request_status') THEN
        RAISE NOTICE 'Migration 004: permission_request_status enum created successfully';
    ELSE
        RAISE EXCEPTION 'Migration 004 failed: permission_request_status enum not found';
    END IF;
    
    -- Check key indexes
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'permission_requests' AND indexname = 'idx_permission_requests_active_unique') THEN
        RAISE NOTICE 'Migration 004: Unique constraint index created successfully';
    ELSE
        RAISE WARNING 'Migration 004: Unique constraint index may not have been created properly';
    END IF;
END $$;