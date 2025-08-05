-- Migration 006: RBAC System Implementation
-- Adds comprehensive Role-Based Access Control with permissions and role assignments

-- Create new enum types for RBAC
DO $$ BEGIN
    -- Permission enumeration
    CREATE TYPE permission_enum AS ENUM (
        -- User Management
        'user:create', 'user:read', 'user:update', 'user:delete', 'user:approve', 'user:assign_role',
        -- Client Management  
        'client:create', 'client:read', 'client:update', 'client:delete', 'client:assign_user',
        -- GA4 Property Management
        'ga4_property:create', 'ga4_property:read', 'ga4_property:update', 'ga4_property:delete',
        -- Permission Management
        'permission:create', 'permission:read', 'permission:update', 'permission:delete', 
        'permission:approve', 'permission:revoke',
        -- Service Account Management
        'service_account:create', 'service_account:read', 'service_account:update', 'service_account:delete',
        -- Audit and Reporting
        'audit:read', 'audit:export', 'report:generate', 'report:download',
        -- System Administration
        'system:config', 'system:health', 'system:backup'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    -- Permission scope enumeration
    CREATE TYPE permission_scope_enum AS ENUM ('system', 'client', 'own', 'assigned');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    -- Permission context enumeration
    CREATE TYPE permission_context_enum AS ENUM ('all', 'assigned_clients', 'own_data', 'same_client');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Update existing user_role enum to include new roles
DO $$ BEGIN
    -- Add new role values to existing enum
    ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'Manager';
    ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'User';
    ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'Client';
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Role-Permission mapping table
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role user_role_enum NOT NULL,
    permission permission_enum NOT NULL,
    scope permission_scope_enum DEFAULT 'system' NOT NULL,
    context permission_context_enum DEFAULT 'all' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Prevent duplicate role-permission combinations
    UNIQUE(role, permission, scope, context)
);

-- User role assignments (beyond primary role)
CREATE TABLE IF NOT EXISTS user_role_assignments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role user_role_enum NOT NULL,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE, -- NULL for system-wide roles
    scope permission_scope_enum DEFAULT 'system' NOT NULL,
    
    -- Lifecycle management
    is_active BOOLEAN DEFAULT true NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    assigned_by_id INTEGER NOT NULL REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Revocation tracking  
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by_id INTEGER REFERENCES users(id),
    revocation_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Prevent duplicate assignments
    UNIQUE(user_id, role, client_id)
);

-- User permission overrides (individual grants/denials)
CREATE TABLE IF NOT EXISTS user_permission_overrides (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission permission_enum NOT NULL,
    
    -- Override type
    is_granted BOOLEAN NOT NULL, -- true = grant, false = deny
    scope permission_scope_enum DEFAULT 'system' NOT NULL,
    context permission_context_enum DEFAULT 'all' NOT NULL,
    
    -- Context-specific overrides
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    resource_id VARCHAR(100), -- Specific resource identifier
    
    -- Lifecycle management
    is_active BOOLEAN DEFAULT true NOT NULL,
    granted_by_id INTEGER NOT NULL REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Index for efficient permission lookups
    UNIQUE(user_id, permission, client_id, resource_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role);
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON role_permissions(permission);
CREATE INDEX IF NOT EXISTS idx_role_permissions_active ON role_permissions(is_active);

CREATE INDEX IF NOT EXISTS idx_user_role_assignments_user ON user_role_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_role_assignments_role ON user_role_assignments(role);
CREATE INDEX IF NOT EXISTS idx_user_role_assignments_client ON user_role_assignments(client_id);
CREATE INDEX IF NOT EXISTS idx_user_role_assignments_active ON user_role_assignments(is_active);

CREATE INDEX IF NOT EXISTS idx_user_permission_overrides_user ON user_permission_overrides(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permission_overrides_permission ON user_permission_overrides(permission);
CREATE INDEX IF NOT EXISTS idx_user_permission_overrides_client ON user_permission_overrides(client_id);
CREATE INDEX IF NOT EXISTS idx_user_permission_overrides_active ON user_permission_overrides(is_active);

-- Insert default role-permission mappings
INSERT INTO role_permissions (role, permission, scope, context) VALUES
-- SUPER_ADMIN: All permissions
('Super Admin', 'user:create', 'system', 'all'),
('Super Admin', 'user:read', 'system', 'all'),
('Super Admin', 'user:update', 'system', 'all'),
('Super Admin', 'user:delete', 'system', 'all'),
('Super Admin', 'user:approve', 'system', 'all'),
('Super Admin', 'user:assign_role', 'system', 'all'),
('Super Admin', 'client:create', 'system', 'all'),
('Super Admin', 'client:read', 'system', 'all'),
('Super Admin', 'client:update', 'system', 'all'),
('Super Admin', 'client:delete', 'system', 'all'),
('Super Admin', 'client:assign_user', 'system', 'all'),
('Super Admin', 'ga4_property:create', 'system', 'all'),
('Super Admin', 'ga4_property:read', 'system', 'all'),
('Super Admin', 'ga4_property:update', 'system', 'all'),
('Super Admin', 'ga4_property:delete', 'system', 'all'),
('Super Admin', 'permission:create', 'system', 'all'),
('Super Admin', 'permission:read', 'system', 'all'),
('Super Admin', 'permission:update', 'system', 'all'),
('Super Admin', 'permission:delete', 'system', 'all'),
('Super Admin', 'permission:approve', 'system', 'all'),
('Super Admin', 'permission:revoke', 'system', 'all'),
('Super Admin', 'service_account:create', 'system', 'all'),
('Super Admin', 'service_account:read', 'system', 'all'),
('Super Admin', 'service_account:update', 'system', 'all'),
('Super Admin', 'service_account:delete', 'system', 'all'),
('Super Admin', 'audit:read', 'system', 'all'),
('Super Admin', 'audit:export', 'system', 'all'),
('Super Admin', 'report:generate', 'system', 'all'),
('Super Admin', 'report:download', 'system', 'all'),
('Super Admin', 'system:config', 'system', 'all'),
('Super Admin', 'system:health', 'system', 'all'),
('Super Admin', 'system:backup', 'system', 'all'),

-- ADMIN: Full operations except system administration
('Admin', 'user:create', 'system', 'all'),
('Admin', 'user:read', 'system', 'all'),
('Admin', 'user:update', 'system', 'all'),
('Admin', 'user:delete', 'system', 'all'),
('Admin', 'user:approve', 'system', 'all'),
('Admin', 'user:assign_role', 'system', 'all'),
('Admin', 'client:create', 'system', 'all'),
('Admin', 'client:read', 'system', 'all'),
('Admin', 'client:update', 'system', 'all'),
('Admin', 'client:delete', 'system', 'all'),
('Admin', 'client:assign_user', 'system', 'all'),
('Admin', 'ga4_property:create', 'system', 'all'),
('Admin', 'ga4_property:read', 'system', 'all'),
('Admin', 'ga4_property:update', 'system', 'all'),
('Admin', 'ga4_property:delete', 'system', 'all'),
('Admin', 'permission:create', 'system', 'all'),
('Admin', 'permission:read', 'system', 'all'),
('Admin', 'permission:update', 'system', 'all'),
('Admin', 'permission:delete', 'system', 'all'),
('Admin', 'permission:approve', 'system', 'all'),
('Admin', 'permission:revoke', 'system', 'all'),
('Admin', 'service_account:create', 'system', 'all'),
('Admin', 'service_account:read', 'system', 'all'),
('Admin', 'service_account:update', 'system', 'all'),
('Admin', 'service_account:delete', 'system', 'all'),
('Admin', 'audit:read', 'system', 'all'),
('Admin', 'audit:export', 'system', 'all'),
('Admin', 'report:generate', 'system', 'all'),
('Admin', 'report:download', 'system', 'all'),
('Admin', 'system:health', 'system', 'all'),

-- MANAGER: Client-specific management
('Manager', 'user:read', 'client', 'assigned_clients'),
('Manager', 'user:update', 'client', 'assigned_clients'),
('Manager', 'user:assign_role', 'client', 'assigned_clients'),
('Manager', 'client:read', 'client', 'assigned_clients'),
('Manager', 'client:update', 'client', 'assigned_clients'),
('Manager', 'client:assign_user', 'client', 'assigned_clients'),
('Manager', 'ga4_property:create', 'client', 'assigned_clients'),
('Manager', 'ga4_property:read', 'client', 'assigned_clients'),
('Manager', 'ga4_property:update', 'client', 'assigned_clients'),
('Manager', 'ga4_property:delete', 'client', 'assigned_clients'),
('Manager', 'permission:create', 'client', 'assigned_clients'),
('Manager', 'permission:read', 'client', 'assigned_clients'),
('Manager', 'permission:update', 'client', 'assigned_clients'),
('Manager', 'permission:approve', 'client', 'assigned_clients'),
('Manager', 'permission:revoke', 'client', 'assigned_clients'),
('Manager', 'service_account:read', 'client', 'assigned_clients'),
('Manager', 'service_account:update', 'client', 'assigned_clients'),
('Manager', 'audit:read', 'client', 'assigned_clients'),
('Manager', 'report:generate', 'client', 'assigned_clients'),

-- USER: Standard operations within assigned clients
('User', 'user:read', 'client', 'same_client'),
('User', 'client:read', 'client', 'assigned_clients'),
('User', 'ga4_property:read', 'client', 'assigned_clients'),
('User', 'permission:create', 'client', 'assigned_clients'),
('User', 'permission:read', 'client', 'assigned_clients'),
('User', 'service_account:read', 'client', 'assigned_clients'),
('User', 'audit:read', 'client', 'assigned_clients'),

-- CLIENT: Limited read-only access to own data
('Client', 'user:read', 'own', 'own_data'),
('Client', 'client:read', 'own', 'own_data'),
('Client', 'ga4_property:read', 'own', 'own_data'),
('Client', 'permission:read', 'own', 'own_data'),
('Client', 'audit:read', 'own', 'own_data'),

-- VIEWER: Read-only access (legacy compatibility)
('Viewer', 'user:read', 'system', 'all'),
('Viewer', 'client:read', 'system', 'all'),
('Viewer', 'ga4_property:read', 'system', 'all'),
('Viewer', 'permission:read', 'system', 'all'),
('Viewer', 'service_account:read', 'system', 'all'),
('Viewer', 'audit:read', 'system', 'all'),

-- REQUESTER: Can request permissions (legacy compatibility)
('Requester', 'user:read', 'client', 'same_client'),
('Requester', 'client:read', 'client', 'assigned_clients'),
('Requester', 'ga4_property:read', 'client', 'assigned_clients'),
('Requester', 'permission:create', 'client', 'assigned_clients'),
('Requester', 'permission:read', 'client', 'assigned_clients'),
('Requester', 'service_account:read', 'client', 'assigned_clients')

ON CONFLICT (role, permission, scope, context) DO NOTHING;

-- Update updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_role_permissions_updated_at ON role_permissions;
CREATE TRIGGER update_role_permissions_updated_at
    BEFORE UPDATE ON role_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_role_assignments_updated_at ON user_role_assignments;
CREATE TRIGGER update_user_role_assignments_updated_at
    BEFORE UPDATE ON user_role_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_permission_overrides_updated_at ON user_permission_overrides;
CREATE TRIGGER update_user_permission_overrides_updated_at
    BEFORE UPDATE ON user_permission_overrides
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for easier permission queries
CREATE OR REPLACE VIEW user_effective_permissions AS
SELECT DISTINCT
    u.id as user_id,
    u.email,
    u.role as primary_role,
    rp.permission,
    rp.scope,
    rp.context,
    COALESCE(ura.client_id, NULL) as client_id,
    'role' as permission_source,
    COALESCE(ura.role, u.role) as source_role
FROM users u
LEFT JOIN user_role_assignments ura ON u.id = ura.user_id 
    AND ura.is_active = true 
    AND (ura.expires_at IS NULL OR ura.expires_at > CURRENT_TIMESTAMP)
    AND ura.revoked_at IS NULL
JOIN role_permissions rp ON rp.role = COALESCE(ura.role, u.role)
    AND rp.is_active = true
WHERE u.status = 'active'

UNION ALL

SELECT DISTINCT
    upo.user_id,
    u.email,
    u.role as primary_role,
    upo.permission,
    upo.scope,
    upo.context,
    upo.client_id,
    CASE WHEN upo.is_granted THEN 'override_grant' ELSE 'override_deny' END as permission_source,
    NULL as source_role
FROM user_permission_overrides upo
JOIN users u ON u.id = upo.user_id
WHERE upo.is_active = true
    AND (upo.expires_at IS NULL OR upo.expires_at > CURRENT_TIMESTAMP)
    AND u.status = 'active';

-- Grant permissions on new tables
GRANT SELECT, INSERT, UPDATE, DELETE ON role_permissions TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_role_assignments TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_permission_overrides TO postgres;
GRANT SELECT ON user_effective_permissions TO postgres;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE role_permissions_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE user_role_assignments_id_seq TO postgres;
GRANT USAGE, SELECT ON SEQUENCE user_permission_overrides_id_seq TO postgres;

-- Migration completed successfully
SELECT 'RBAC System Migration 006 completed successfully' as status;