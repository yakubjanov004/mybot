-- 018_staff_creation_tracking.sql
-- Add staff creation tracking fields and audit tables

-- 1. Add staff creation tracking fields to service_requests table
ALTER TABLE service_requests 
ADD COLUMN IF NOT EXISTS created_by_staff BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS staff_creator_id INTEGER REFERENCES users(id),
ADD COLUMN IF NOT EXISTS staff_creator_role VARCHAR(50) CHECK (staff_creator_role IN (
    'admin', 'call_center', 'call_center_supervisor', 'technician', 
    'manager', 'junior_manager', 'controller', 'warehouse', 'client', 'blocked'
)),
ADD COLUMN IF NOT EXISTS creation_source VARCHAR(50) DEFAULT 'client' CHECK (creation_source IN (
    'client', 'manager', 'junior_manager', 'controller', 'call_center'
)),
ADD COLUMN IF NOT EXISTS client_notified_at TIMESTAMP WITH TIME ZONE;

-- 2. Create client_selection_data table for temporary client selection during staff application creation
CREATE TABLE IF NOT EXISTS client_selection_data (
    id SERIAL PRIMARY KEY,
    search_method VARCHAR(20) NOT NULL DEFAULT 'phone' CHECK (search_method IN ('phone', 'name', 'id', 'new')),
    search_value VARCHAR(255),
    client_id INTEGER REFERENCES users(id),
    new_client_data JSONB DEFAULT '{}',
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create staff_application_audit table for comprehensive audit trail
CREATE TABLE IF NOT EXISTS staff_application_audit (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(36) REFERENCES service_requests(id) ON DELETE CASCADE,
    creator_id INTEGER NOT NULL REFERENCES users(id),
    creator_role VARCHAR(50) NOT NULL CHECK (creator_role IN (
        'admin', 'call_center', 'call_center_supervisor', 'technician', 
        'manager', 'junior_manager', 'controller', 'warehouse', 'client', 'blocked'
    )),
    client_id INTEGER REFERENCES users(id),
    application_type VARCHAR(50) CHECK (application_type IN ('connection_request', 'technical_service')),
    creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    client_notified BOOLEAN DEFAULT FALSE,
    client_notified_at TIMESTAMP WITH TIME ZONE,
    workflow_initiated BOOLEAN DEFAULT FALSE,
    workflow_initiated_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    -- Additional audit fields
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_service_requests_created_by_staff ON service_requests(created_by_staff);
CREATE INDEX IF NOT EXISTS idx_service_requests_staff_creator_id ON service_requests(staff_creator_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_creation_source ON service_requests(creation_source);

CREATE INDEX IF NOT EXISTS idx_client_selection_data_search_method ON client_selection_data(search_method);
CREATE INDEX IF NOT EXISTS idx_client_selection_data_client_id ON client_selection_data(client_id);
CREATE INDEX IF NOT EXISTS idx_client_selection_data_created_at ON client_selection_data(created_at);

CREATE INDEX IF NOT EXISTS idx_staff_application_audit_application_id ON staff_application_audit(application_id);
CREATE INDEX IF NOT EXISTS idx_staff_application_audit_creator_id ON staff_application_audit(creator_id);
CREATE INDEX IF NOT EXISTS idx_staff_application_audit_client_id ON staff_application_audit(client_id);
CREATE INDEX IF NOT EXISTS idx_staff_application_audit_creation_timestamp ON staff_application_audit(creation_timestamp);

-- Add comments for documentation
COMMENT ON COLUMN service_requests.created_by_staff IS 'Flag indicating if this request was created by staff on behalf of a client';
COMMENT ON COLUMN service_requests.staff_creator_id IS 'ID of the staff member who created this request';
COMMENT ON COLUMN service_requests.staff_creator_role IS 'Role of the staff member who created this request';
COMMENT ON COLUMN service_requests.creation_source IS 'Source of request creation (client, manager, junior_manager, controller, call_center)';
COMMENT ON COLUMN service_requests.client_notified_at IS 'Timestamp when client was notified about staff-created request';

COMMENT ON TABLE client_selection_data IS 'Temporary data for client selection during staff application creation';
COMMENT ON TABLE staff_application_audit IS 'Comprehensive audit trail for staff-created applications';

-- END OF MIGRATION