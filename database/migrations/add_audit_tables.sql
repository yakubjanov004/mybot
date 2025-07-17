-- Migration script to add audit logging tables for staff application creation
-- Implements Requirements 6.1, 6.2 from multi-role application creation spec

-- Create staff_application_audit table
CREATE TABLE IF NOT EXISTS staff_application_audit (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(255),
    creator_id INTEGER,
    creator_role VARCHAR(50),
    client_id INTEGER,
    application_type VARCHAR(100),
    creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    client_notified BOOLEAN DEFAULT FALSE,
    client_notified_at TIMESTAMP WITH TIME ZONE,
    workflow_initiated BOOLEAN DEFAULT FALSE,
    workflow_initiated_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create client_selection_data table
CREATE TABLE IF NOT EXISTS client_selection_data (
    id SERIAL PRIMARY KEY,
    search_method VARCHAR(20) NOT NULL DEFAULT 'phone',
    search_value VARCHAR(255),
    client_id INTEGER,
    new_client_data JSONB DEFAULT '{}',
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_staff_audit_application_id ON staff_application_audit(application_id);
CREATE INDEX IF NOT EXISTS idx_staff_audit_creator_id ON staff_application_audit(creator_id);
CREATE INDEX IF NOT EXISTS idx_staff_audit_creator_role ON staff_application_audit(creator_role);
CREATE INDEX IF NOT EXISTS idx_staff_audit_client_id ON staff_application_audit(client_id);
CREATE INDEX IF NOT EXISTS idx_staff_audit_application_type ON staff_application_audit(application_type);
CREATE INDEX IF NOT EXISTS idx_staff_audit_creation_timestamp ON staff_application_audit(creation_timestamp);
CREATE INDEX IF NOT EXISTS idx_staff_audit_session_id ON staff_application_audit(session_id);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_staff_audit_creator_timestamp ON staff_application_audit(creator_id, creation_timestamp);
CREATE INDEX IF NOT EXISTS idx_staff_audit_role_timestamp ON staff_application_audit(creator_role, creation_timestamp);
CREATE INDEX IF NOT EXISTS idx_staff_audit_type_timestamp ON staff_application_audit(application_type, creation_timestamp);

-- Index for client selection data
CREATE INDEX IF NOT EXISTS idx_client_selection_method ON client_selection_data(search_method);
CREATE INDEX IF NOT EXISTS idx_client_selection_client_id ON client_selection_data(client_id);
CREATE INDEX IF NOT EXISTS idx_client_selection_created_at ON client_selection_data(created_at);

-- Add foreign key constraints if users table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        -- Add foreign key for creator_id
        ALTER TABLE staff_application_audit 
        ADD CONSTRAINT fk_staff_audit_creator 
        FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL;
        
        -- Add foreign key for client_id
        ALTER TABLE staff_application_audit 
        ADD CONSTRAINT fk_staff_audit_client 
        FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE SET NULL;
        
        -- Add foreign key for client selection data
        ALTER TABLE client_selection_data 
        ADD CONSTRAINT fk_client_selection_client 
        FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN duplicate_object THEN
        -- Foreign keys already exist, ignore
        NULL;
END $$;

-- Add foreign key constraint for service_requests if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'service_requests') THEN
        ALTER TABLE staff_application_audit 
        ADD CONSTRAINT fk_staff_audit_application 
        FOREIGN KEY (application_id) REFERENCES service_requests(id) ON DELETE CASCADE;
    END IF;
EXCEPTION
    WHEN duplicate_object THEN
        -- Foreign key already exists, ignore
        NULL;
END $$;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to audit table
DROP TRIGGER IF EXISTS update_staff_audit_updated_at ON staff_application_audit;
CREATE TRIGGER update_staff_audit_updated_at
    BEFORE UPDATE ON staff_application_audit
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to client selection table
DROP TRIGGER IF EXISTS update_client_selection_updated_at ON client_selection_data;
CREATE TRIGGER update_client_selection_updated_at
    BEFORE UPDATE ON client_selection_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add check constraints for data validation
ALTER TABLE staff_application_audit 
ADD CONSTRAINT chk_creator_role 
CHECK (creator_role IN ('manager', 'junior_manager', 'controller', 'call_center', 'admin'));

ALTER TABLE staff_application_audit 
ADD CONSTRAINT chk_application_type 
CHECK (application_type IN ('connection_request', 'technical_service'));

ALTER TABLE client_selection_data 
ADD CONSTRAINT chk_search_method 
CHECK (search_method IN ('phone', 'name', 'id', 'new'));

-- Create view for audit summary
CREATE OR REPLACE VIEW staff_audit_summary AS
SELECT 
    creator_role,
    application_type,
    DATE(creation_timestamp) as audit_date,
    COUNT(*) as total_applications,
    COUNT(CASE WHEN client_notified THEN 1 END) as notified_applications,
    COUNT(CASE WHEN workflow_initiated THEN 1 END) as workflow_applications,
    COUNT(CASE WHEN client_notified AND workflow_initiated THEN 1 END) as successful_applications,
    ROUND(
        COUNT(CASE WHEN client_notified AND workflow_initiated THEN 1 END)::numeric / 
        COUNT(*)::numeric * 100, 2
    ) as success_rate
FROM staff_application_audit
WHERE creation_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY creator_role, application_type, DATE(creation_timestamp)
ORDER BY audit_date DESC, creator_role, application_type;

-- Create view for creator performance
CREATE OR REPLACE VIEW creator_performance_summary AS
SELECT 
    creator_id,
    creator_role,
    COUNT(*) as total_applications,
    COUNT(CASE WHEN client_notified THEN 1 END) as notified_applications,
    COUNT(CASE WHEN workflow_initiated THEN 1 END) as workflow_applications,
    COUNT(CASE WHEN client_notified AND workflow_initiated THEN 1 END) as successful_applications,
    ROUND(
        COUNT(CASE WHEN client_notified AND workflow_initiated THEN 1 END)::numeric / 
        COUNT(*)::numeric * 100, 2
    ) as success_rate,
    COUNT(CASE WHEN metadata->>'event_type' = 'error_occurred' THEN 1 END) as error_count,
    MIN(creation_timestamp) as first_application,
    MAX(creation_timestamp) as last_application
FROM staff_application_audit
WHERE creation_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY creator_id, creator_role
ORDER BY total_applications DESC;

-- Create view for daily audit statistics
CREATE OR REPLACE VIEW daily_audit_stats AS
SELECT 
    DATE(creation_timestamp) as audit_date,
    COUNT(*) as total_applications,
    COUNT(DISTINCT creator_id) as active_creators,
    COUNT(DISTINCT client_id) as affected_clients,
    COUNT(CASE WHEN application_type = 'connection_request' THEN 1 END) as connection_requests,
    COUNT(CASE WHEN application_type = 'technical_service' THEN 1 END) as technical_services,
    COUNT(CASE WHEN client_notified AND workflow_initiated THEN 1 END) as successful_applications,
    ROUND(
        COUNT(CASE WHEN client_notified AND workflow_initiated THEN 1 END)::numeric / 
        COUNT(*)::numeric * 100, 2
    ) as daily_success_rate
FROM staff_application_audit
WHERE creation_timestamp >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(creation_timestamp)
ORDER BY audit_date DESC;

-- Grant permissions (adjust as needed for your user roles)
-- GRANT SELECT, INSERT, UPDATE ON staff_application_audit TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON client_selection_data TO app_user;
-- GRANT SELECT ON staff_audit_summary TO app_user;
-- GRANT SELECT ON creator_performance_summary TO app_user;
-- GRANT SELECT ON daily_audit_stats TO app_user;

-- Add comments for documentation
COMMENT ON TABLE staff_application_audit IS 'Audit log for staff-created applications';
COMMENT ON COLUMN staff_application_audit.application_id IS 'ID of the created application';
COMMENT ON COLUMN staff_application_audit.creator_id IS 'ID of staff member who created the application';
COMMENT ON COLUMN staff_application_audit.creator_role IS 'Role of the staff member';
COMMENT ON COLUMN staff_application_audit.client_id IS 'ID of the client for whom application was created';
COMMENT ON COLUMN staff_application_audit.application_type IS 'Type of application (connection_request, technical_service)';
COMMENT ON COLUMN staff_application_audit.metadata IS 'Additional audit data in JSON format';
COMMENT ON COLUMN staff_application_audit.session_id IS 'Session ID for tracking related audit events';

COMMENT ON TABLE client_selection_data IS 'Data about client selection during staff application creation';
COMMENT ON COLUMN client_selection_data.search_method IS 'Method used to search/select client';
COMMENT ON COLUMN client_selection_data.search_value IS 'Value used for client search';
COMMENT ON COLUMN client_selection_data.new_client_data IS 'Data for newly created clients';

COMMENT ON VIEW staff_audit_summary IS 'Summary of staff application creation by role, type, and date';
COMMENT ON VIEW creator_performance_summary IS 'Performance metrics for individual creators';
COMMENT ON VIEW daily_audit_stats IS 'Daily statistics for audit activities';

-- Insert initial test data (optional, for development)
-- INSERT INTO staff_application_audit (
--     application_id, creator_id, creator_role, client_id, application_type,
--     client_notified, workflow_initiated, metadata
-- ) VALUES (
--     'test-app-001', 1, 'manager', 100, 'connection_request',
--     true, true, '{"event_type": "application_submitted", "test": true}'
-- );

-- Verify tables were created
SELECT 
    table_name, 
    table_type
FROM information_schema.tables 
WHERE table_name IN ('staff_application_audit', 'client_selection_data')
ORDER BY table_name;