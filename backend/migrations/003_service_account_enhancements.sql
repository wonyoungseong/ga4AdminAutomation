-- Migration 003: Service Account Enhancements
-- Enhances service account management with GA4 property relationships and health monitoring

-- Add new columns to service_accounts table
ALTER TABLE service_accounts 
ADD COLUMN IF NOT EXISTS project_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) DEFAULT 'unknown',
ADD COLUMN IF NOT EXISTS health_checked_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS key_version INTEGER DEFAULT 1;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_service_accounts_health_status ON service_accounts(health_status);
CREATE INDEX IF NOT EXISTS idx_service_accounts_client_active ON service_accounts(client_id, is_active);

-- Create service_account_properties table
CREATE TABLE IF NOT EXISTS service_account_properties (
    id SERIAL PRIMARY KEY,
    service_account_id INTEGER NOT NULL REFERENCES service_accounts(id) ON DELETE CASCADE,
    ga_property_id VARCHAR(50) NOT NULL,
    property_name VARCHAR(255),
    property_account_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_validated_at TIMESTAMP WITH TIME ZONE,
    validation_status VARCHAR(20) DEFAULT 'unknown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(service_account_id, ga_property_id)
);

-- Create indexes for service_account_properties
CREATE INDEX IF NOT EXISTS idx_sa_properties_service_account ON service_account_properties(service_account_id);
CREATE INDEX IF NOT EXISTS idx_sa_properties_ga_property ON service_account_properties(ga_property_id);
CREATE INDEX IF NOT EXISTS idx_sa_properties_active ON service_account_properties(is_active);
CREATE INDEX IF NOT EXISTS idx_sa_properties_validation ON service_account_properties(validation_status);

-- Create property_access_bindings table
CREATE TABLE IF NOT EXISTS property_access_bindings (
    id SERIAL PRIMARY KEY,
    service_account_id INTEGER NOT NULL REFERENCES service_accounts(id) ON DELETE CASCADE,
    ga_property_id VARCHAR(50) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    roles TEXT[], -- Array of GA4 roles
    binding_name VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    synchronized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(service_account_id, ga_property_id, user_email)
);

-- Create indexes for property_access_bindings
CREATE INDEX IF NOT EXISTS idx_pab_service_account ON property_access_bindings(service_account_id);
CREATE INDEX IF NOT EXISTS idx_pab_ga_property ON property_access_bindings(ga_property_id);
CREATE INDEX IF NOT EXISTS idx_pab_user_email ON property_access_bindings(user_email);
CREATE INDEX IF NOT EXISTS idx_pab_active ON property_access_bindings(is_active);
CREATE INDEX IF NOT EXISTS idx_pab_synchronized ON property_access_bindings(synchronized_at);

-- Add new columns to permission_grants table
ALTER TABLE permission_grants
ADD COLUMN IF NOT EXISTS binding_name VARCHAR(500),
ADD COLUMN IF NOT EXISTS synchronized_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'pending';

-- Create indexes for permission_grants new columns
CREATE INDEX IF NOT EXISTS idx_permission_grants_sync_status ON permission_grants(sync_status);
CREATE INDEX IF NOT EXISTS idx_permission_grants_synchronized ON permission_grants(synchronized_at);
CREATE INDEX IF NOT EXISTS idx_permission_grants_binding_name ON permission_grants(binding_name);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_permission_grants_user_client ON permission_grants(user_id, client_id);
CREATE INDEX IF NOT EXISTS idx_permission_grants_service_property ON permission_grants(service_account_id, ga_property_id);
CREATE INDEX IF NOT EXISTS idx_permission_grants_status_expires ON permission_grants(status, expires_at);

-- Update existing service accounts to have default health status
UPDATE service_accounts 
SET health_status = 'unknown' 
WHERE health_status IS NULL;

-- Update existing permission grants to have default sync status
UPDATE permission_grants 
SET sync_status = 'pending' 
WHERE sync_status IS NULL;

-- Add comments for documentation
COMMENT ON TABLE service_account_properties IS 'Tracks GA4 properties discovered and accessible by each service account';
COMMENT ON TABLE property_access_bindings IS 'Caches actual GA4 property access bindings for synchronization';

COMMENT ON COLUMN service_accounts.health_status IS 'Health status: healthy, unhealthy, warning, unknown';
COMMENT ON COLUMN service_accounts.health_checked_at IS 'Timestamp of last health check';
COMMENT ON COLUMN service_accounts.last_used_at IS 'Timestamp of last API usage';
COMMENT ON COLUMN service_accounts.key_version IS 'Version number for credential rotation tracking';

COMMENT ON COLUMN service_account_properties.validation_status IS 'Property validation status: valid, invalid, unknown';
COMMENT ON COLUMN service_account_properties.discovered_at IS 'When this property was first discovered';
COMMENT ON COLUMN service_account_properties.last_validated_at IS 'When this property was last validated';

COMMENT ON COLUMN property_access_bindings.roles IS 'JSON array of GA4 roles for this binding';
COMMENT ON COLUMN property_access_bindings.binding_name IS 'Google Analytics Admin API binding resource name';
COMMENT ON COLUMN property_access_bindings.synchronized_at IS 'When this binding was last synchronized with GA4';

COMMENT ON COLUMN permission_grants.binding_name IS 'Google Analytics Admin API binding resource name';
COMMENT ON COLUMN permission_grants.synchronized_at IS 'When this grant was last synchronized with GA4';
COMMENT ON COLUMN permission_grants.sync_status IS 'Synchronization status: pending, synced, failed';

-- Create triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to new tables
CREATE TRIGGER update_service_account_properties_updated_at 
    BEFORE UPDATE ON service_account_properties 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_property_access_bindings_updated_at 
    BEFORE UPDATE ON property_access_bindings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON service_account_properties TO ga4_admin_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON property_access_bindings TO ga4_admin_app;
-- GRANT USAGE ON SEQUENCE service_account_properties_id_seq TO ga4_admin_app;
-- GRANT USAGE ON SEQUENCE property_access_bindings_id_seq TO ga4_admin_app;