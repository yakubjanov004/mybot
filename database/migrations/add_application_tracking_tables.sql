-- Migration script for application tracking and reporting tables
-- Implements Requirements 6.1, 6.2, 6.3, 6.4 from multi-role application creation spec

-- Create staff application audit table (if not exists)
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

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_staff_audit_creator_id ON staff_application_audit(creator_id);
CREATE INDEX IF NOT EXISTS idx_staff_audit_creator_role ON staff_application_audit(creator_role);
CREATE INDEX IF NOT EXISTS idx_staff_audit_client_id ON staff_application_audit(client_id);
CREATE INDEX IF NOT EXISTS idx_staff_audit_application_type ON staff_application_audit(application_type);
CREATE INDEX IF NOT EXISTS idx_staff_audit_creation_timestamp ON staff_application_audit(creation_timestamp);
CREATE INDEX IF NOT EXISTS idx_staff_audit_application_id ON staff_application_audit(application_id);
CREATE INDEX IF NOT EXISTS idx_staff_audit_session_id ON staff_application_audit(session_id);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_staff_audit_creator_date ON staff_application_audit(creator_id, creation_timestamp);
CREATE INDEX IF NOT EXISTS idx_staff_audit_role_date ON staff_application_audit(creator_role, creation_timestamp);
CREATE INDEX IF NOT EXISTS idx_staff_audit_success_status ON staff_application_audit(client_notified, workflow_initiated);

-- Create application alerts table
CREATE TABLE IF NOT EXISTS application_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(255) UNIQUE NOT NULL,
    rule_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    channels JSONB DEFAULT '[]',
    recipients JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivery_status JSONB DEFAULT '{}',
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for application alerts
CREATE INDEX IF NOT EXISTS idx_alerts_alert_id ON application_alerts(alert_id);
CREATE INDEX IF NOT EXISTS idx_alerts_rule_id ON application_alerts(rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_alert_type ON application_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON application_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON application_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON application_alerts(acknowledged);

-- Create alert rules table
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    alert_type VARCHAR(100) NOT NULL,
    threshold_config JSONB DEFAULT '{}',
    frequency VARCHAR(50) NOT NULL CHECK (frequency IN ('real_time', 'hourly', 'daily', 'weekly')),
    channels JSONB DEFAULT '[]',
    recipients JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0
);

-- Create indexes for alert rules
CREATE INDEX IF NOT EXISTS idx_alert_rules_rule_id ON alert_rules(rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_rules_alert_type ON alert_rules(alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_rules_frequency ON alert_rules(frequency);
CREATE INDEX IF NOT EXISTS idx_alert_rules_is_active ON alert_rules(is_active);

-- Create application statistics cache table for performance
CREATE TABLE IF NOT EXISTS application_statistics_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    period_days INTEGER NOT NULL,
    source_filter VARCHAR(50),
    role_filter VARCHAR(50),
    statistics_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create index for statistics cache
CREATE INDEX IF NOT EXISTS idx_stats_cache_key ON application_statistics_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_stats_cache_expires ON application_statistics_cache(expires_at);

-- Create application tracking reports table
CREATE TABLE IF NOT EXISTS application_tracking_reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(255) UNIQUE NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    period VARCHAR(50) NOT NULL,
    format_type VARCHAR(20) NOT NULL,
    generated_by INTEGER,
    report_data JSONB NOT NULL,
    summary_data JSONB DEFAULT '{}',
    file_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for tracking reports
CREATE INDEX IF NOT EXISTS idx_reports_report_id ON application_tracking_reports(report_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON application_tracking_reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_generated_by ON application_tracking_reports(generated_by);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON application_tracking_reports(created_at);

-- Add staff creation tracking columns to service_requests table if they don't exist
DO $$ 
BEGIN
    -- Check and add created_by_staff column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'service_requests' AND column_name = 'created_by_staff') THEN
        ALTER TABLE service_requests ADD COLUMN created_by_staff BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Check and add staff_creator_id column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'service_requests' AND column_name = 'staff_creator_id') THEN
        ALTER TABLE service_requests ADD COLUMN staff_creator_id INTEGER;
    END IF;
    
    -- Check and add staff_creator_role column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'service_requests' AND column_name = 'staff_creator_role') THEN
        ALTER TABLE service_requests ADD COLUMN staff_creator_role VARCHAR(50);
    END IF;
    
    -- Check and add creation_source column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'service_requests' AND column_name = 'creation_source') THEN
        ALTER TABLE service_requests ADD COLUMN creation_source VARCHAR(50) DEFAULT 'client';
    END IF;
    
    -- Check and add client_notified_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'service_requests' AND column_name = 'client_notified_at') THEN
        ALTER TABLE service_requests ADD COLUMN client_notified_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Create indexes for service_requests staff tracking columns
CREATE INDEX IF NOT EXISTS idx_service_requests_created_by_staff ON service_requests(created_by_staff);
CREATE INDEX IF NOT EXISTS idx_service_requests_staff_creator_id ON service_requests(staff_creator_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_staff_creator_role ON service_requests(staff_creator_role);
CREATE INDEX IF NOT EXISTS idx_service_requests_creation_source ON service_requests(creation_source);
CREATE INDEX IF NOT EXISTS idx_service_requests_created_at ON service_requests(created_at);

-- Create composite indexes for common tracking queries
CREATE INDEX IF NOT EXISTS idx_service_requests_staff_date ON service_requests(created_by_staff, created_at);
CREATE INDEX IF NOT EXISTS idx_service_requests_source_date ON service_requests(creation_source, created_at);
CREATE INDEX IF NOT EXISTS idx_service_requests_creator_date ON service_requests(staff_creator_id, created_at) WHERE staff_creator_id IS NOT NULL;

-- Create client selection data table for staff application creation
CREATE TABLE IF NOT EXISTS client_selection_data (
    id SERIAL PRIMARY KEY,
    search_method VARCHAR(20) NOT NULL CHECK (search_method IN ('phone', 'name', 'id', 'new')),
    search_value VARCHAR(255),
    client_id INTEGER,
    new_client_data JSONB DEFAULT '{}',
    verified BOOLEAN DEFAULT FALSE,
    created_by INTEGER NOT NULL,
    session_id VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for client selection data
CREATE INDEX IF NOT EXISTS idx_client_selection_method ON client_selection_data(search_method);
CREATE INDEX IF NOT EXISTS idx_client_selection_client_id ON client_selection_data(client_id);
CREATE INDEX IF NOT EXISTS idx_client_selection_created_by ON client_selection_data(created_by);
CREATE INDEX IF NOT EXISTS idx_client_selection_session ON client_selection_data(session_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
DROP TRIGGER IF EXISTS update_staff_audit_updated_at ON staff_application_audit;
CREATE TRIGGER update_staff_audit_updated_at 
    BEFORE UPDATE ON staff_application_audit 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_alert_rules_updated_at ON alert_rules;
CREATE TRIGGER update_alert_rules_updated_at 
    BEFORE UPDATE ON alert_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for application tracking summary
CREATE OR REPLACE VIEW application_tracking_summary AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_applications,
    COUNT(CASE WHEN created_by_staff = true THEN 1 END) as staff_created,
    COUNT(CASE WHEN created_by_staff = false THEN 1 END) as client_created,
    ROUND(COUNT(CASE WHEN created_by_staff = true THEN 1 END) * 100.0 / COUNT(*), 2) as staff_percentage,
    COUNT(CASE WHEN current_status = 'completed' THEN 1 END) as completed_applications,
    ROUND(COUNT(CASE WHEN current_status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
FROM service_requests 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Create view for role performance summary
CREATE OR REPLACE VIEW role_performance_summary AS
SELECT 
    staff_creator_role as role,
    COUNT(*) as total_applications,
    COUNT(CASE WHEN current_status = 'completed' THEN 1 END) as completed_applications,
    ROUND(COUNT(CASE WHEN current_status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate,
    COUNT(CASE WHEN current_status IN ('cancelled', 'failed') THEN 1 END) as failed_applications,
    ROUND(COUNT(CASE WHEN current_status IN ('cancelled', 'failed') THEN 1 END) * 100.0 / COUNT(*), 2) as error_rate,
    ROUND(COUNT(*) / EXTRACT(days FROM (MAX(created_at) - MIN(created_at) + INTERVAL '1 day')), 2) as avg_per_day
FROM service_requests 
WHERE created_by_staff = true 
    AND staff_creator_role IS NOT NULL
    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY staff_creator_role
ORDER BY total_applications DESC;

-- Create view for recent alerts summary
CREATE OR REPLACE VIEW recent_alerts_summary AS
SELECT 
    alert_type,
    severity,
    COUNT(*) as alert_count,
    MAX(created_at) as last_alert,
    COUNT(CASE WHEN acknowledged = false THEN 1 END) as unacknowledged_count
FROM application_alerts 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY alert_type, severity
ORDER BY alert_count DESC, last_alert DESC;

-- Insert default alert rules
INSERT INTO alert_rules (rule_id, name, description, alert_type, threshold_config, frequency, channels, recipients, is_active)
VALUES 
    ('high_staff_creation_rate', 'High Staff Creation Rate', 'Alert when staff creation rate exceeds normal levels', 'high_staff_creation_rate', 
     '{"staff_percentage_threshold": 70, "baseline_comparison": true, "minimum_applications": 10}', 'hourly', 
     '["telegram", "database"]', '[]', true),
    
    ('low_client_creation_rate', 'Low Client Self-Service Rate', 'Alert when client self-service rate drops significantly', 'low_client_creation_rate', 
     '{"client_percentage_threshold": 30, "baseline_comparison": true, "drop_percentage": 20}', 'hourly', 
     '["telegram", "database"]', '[]', true),
    
    ('success_rate_drop', 'Success Rate Drop', 'Alert when application success rate drops below acceptable levels', 'success_rate_drop', 
     '{"success_rate_threshold": 80, "drop_percentage": 15, "baseline_comparison": true}', 'hourly', 
     '["telegram", "database"]', '[]', true),
    
    ('error_spike', 'Error Rate Spike', 'Alert when error rate spikes above normal levels', 'error_spike', 
     '{"error_rate_threshold": 10, "spike_percentage": 5, "baseline_comparison": true}', 'hourly', 
     '["telegram", "database"]', '[]', true),
    
    ('unusual_role_activity', 'Unusual Role Activity', 'Alert when specific roles show unusual activity patterns', 'unusual_role_activity', 
     '{"activity_multiplier": 3, "minimum_baseline": 1, "roles_to_monitor": ["manager", "junior_manager", "controller", "call_center"]}', 'daily', 
     '["telegram", "database"]', '[]', true)
ON CONFLICT (rule_id) DO NOTHING;

-- Create function to clean up old cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM application_statistics_cache WHERE expires_at < CURRENT_TIMESTAMP;
    DELETE FROM application_tracking_reports WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create function to get application statistics
CREATE OR REPLACE FUNCTION get_application_stats(days_back INTEGER DEFAULT 30, source_filter TEXT DEFAULT 'all')
RETURNS TABLE (
    total_applications BIGINT,
    client_created BIGINT,
    staff_created BIGINT,
    staff_percentage NUMERIC,
    success_rate NUMERIC,
    error_rate NUMERIC,
    avg_per_day NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_applications,
        COUNT(CASE WHEN created_by_staff = false THEN 1 END) as client_created,
        COUNT(CASE WHEN created_by_staff = true THEN 1 END) as staff_created,
        ROUND(COUNT(CASE WHEN created_by_staff = true THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as staff_percentage,
        ROUND(COUNT(CASE WHEN current_status = 'completed' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as success_rate,
        ROUND(COUNT(CASE WHEN current_status IN ('cancelled', 'failed') THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as error_rate,
        ROUND(COUNT(*) * 1.0 / NULLIF(days_back, 0), 2) as avg_per_day
    FROM service_requests 
    WHERE created_at >= CURRENT_TIMESTAMP - (days_back || ' days')::INTERVAL
        AND (source_filter = 'all' OR 
             (source_filter = 'client' AND created_by_staff = false) OR
             (source_filter = 'staff' AND created_by_staff = true));
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions (adjust as needed for your user roles)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Create comments for documentation
COMMENT ON TABLE staff_application_audit IS 'Audit trail for staff-created applications';
COMMENT ON TABLE application_alerts IS 'System alerts for unusual application creation patterns';
COMMENT ON TABLE alert_rules IS 'Configuration for automated alert rules';
COMMENT ON TABLE application_statistics_cache IS 'Performance cache for application statistics';
COMMENT ON TABLE application_tracking_reports IS 'Generated tracking and reporting data';
COMMENT ON TABLE client_selection_data IS 'Client selection data during staff application creation';

COMMENT ON VIEW application_tracking_summary IS 'Daily summary of application creation statistics';
COMMENT ON VIEW role_performance_summary IS 'Performance summary by staff role';
COMMENT ON VIEW recent_alerts_summary IS 'Summary of recent system alerts';

-- Migration completed successfully
SELECT 'Application tracking and reporting tables created successfully' as migration_status;