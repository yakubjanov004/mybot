-- Migration: Add error recovery and monitoring tables
-- Description: Creates tables for comprehensive error handling and recovery system
-- Requirements: Task 12 - Create comprehensive error handling and recovery

-- Error records table for tracking all system errors
CREATE TABLE IF NOT EXISTS error_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    stack_trace TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- Indexes for error records
CREATE INDEX IF NOT EXISTS idx_error_records_category ON error_records(category);
CREATE INDEX IF NOT EXISTS idx_error_records_severity ON error_records(severity);
CREATE INDEX IF NOT EXISTS idx_error_records_occurred_at ON error_records(occurred_at);
CREATE INDEX IF NOT EXISTS idx_error_records_resolved_at ON error_records(resolved_at);

-- Transaction log table for tracking transactional operations
CREATE TABLE IF NOT EXISTS transaction_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL,
    operation_type VARCHAR(100) NOT NULL,
    operation_data JSONB DEFAULT '{}',
    rollback_data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, rolled_back, failed
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Indexes for transaction log
CREATE INDEX IF NOT EXISTS idx_transaction_log_transaction_id ON transaction_log(transaction_id);
CREATE INDEX IF NOT EXISTS idx_transaction_log_status ON transaction_log(status);
CREATE INDEX IF NOT EXISTS idx_transaction_log_started_at ON transaction_log(started_at);

-- Notification retry queue table
CREATE TABLE IF NOT EXISTS notification_retry_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(50) NOT NULL,
    request_id UUID NOT NULL,
    workflow_type VARCHAR(100) NOT NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 5,
    next_retry_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' -- pending, completed, failed
);

-- Indexes for notification retry queue
CREATE INDEX IF NOT EXISTS idx_notification_retry_queue_next_retry_at ON notification_retry_queue(next_retry_at);
CREATE INDEX IF NOT EXISTS idx_notification_retry_queue_status ON notification_retry_queue(status);
CREATE INDEX IF NOT EXISTS idx_notification_retry_queue_request_id ON notification_retry_queue(request_id);

-- Inventory reconciliation log table
CREATE TABLE IF NOT EXISTS inventory_reconciliation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reconciliation_type VARCHAR(50) NOT NULL,
    material_id INTEGER REFERENCES materials(id),
    request_id UUID,
    discrepancy_details JSONB DEFAULT '{}',
    resolution_action VARCHAR(100),
    before_quantity INTEGER,
    after_quantity INTEGER,
    performed_by INTEGER REFERENCES users(id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed', -- completed, failed, pending
    notes TEXT
);

-- Indexes for inventory reconciliation log
CREATE INDEX IF NOT EXISTS idx_inventory_reconciliation_log_material_id ON inventory_reconciliation_log(material_id);
CREATE INDEX IF NOT EXISTS idx_inventory_reconciliation_log_request_id ON inventory_reconciliation_log(request_id);
CREATE INDEX IF NOT EXISTS idx_inventory_reconciliation_log_performed_at ON inventory_reconciliation_log(performed_at);

-- Workflow recovery log table
CREATE TABLE IF NOT EXISTS workflow_recovery_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    recovery_action VARCHAR(100) NOT NULL,
    recovery_data JSONB DEFAULT '{}',
    performed_by INTEGER NOT NULL REFERENCES users(id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    previous_state JSONB DEFAULT '{}',
    new_state JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    notes TEXT
);

-- Indexes for workflow recovery log
CREATE INDEX IF NOT EXISTS idx_workflow_recovery_log_request_id ON workflow_recovery_log(request_id);
CREATE INDEX IF NOT EXISTS idx_workflow_recovery_log_performed_at ON workflow_recovery_log(performed_at);
CREATE INDEX IF NOT EXISTS idx_workflow_recovery_log_performed_by ON workflow_recovery_log(performed_by);

-- System health monitoring table
CREATE TABLE IF NOT EXISTS system_health_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    active_requests INTEGER DEFAULT 0,
    pending_notifications INTEGER DEFAULT 0,
    active_transactions INTEGER DEFAULT 0,
    error_count_24h INTEGER DEFAULT 0,
    inventory_discrepancies INTEGER DEFAULT 0,
    stuck_workflows INTEGER DEFAULT 0,
    system_status VARCHAR(20) DEFAULT 'healthy', -- healthy, degraded, critical
    metrics JSONB DEFAULT '{}',
    notes TEXT
);

-- Index for system health snapshots
CREATE INDEX IF NOT EXISTS idx_system_health_snapshots_snapshot_time ON system_health_snapshots(snapshot_time);
CREATE INDEX IF NOT EXISTS idx_system_health_snapshots_system_status ON system_health_snapshots(system_status);

-- Add inventory_transactions table if it doesn't exist (for inventory reconciliation)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    request_id UUID,
    material_id INTEGER REFERENCES materials(id),
    transaction_type VARCHAR(20) NOT NULL, -- consume, reserve, return, adjustment
    quantity INTEGER NOT NULL,
    performed_by INTEGER REFERENCES users(id),
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Indexes for inventory transactions
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_request_id ON inventory_transactions(request_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_material_id ON inventory_transactions(material_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_transaction_date ON inventory_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_transaction_type ON inventory_transactions(transaction_type);

-- Add pending_notifications table if it doesn't exist (for notification system)
CREATE TABLE IF NOT EXISTS pending_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id),
    request_id UUID NOT NULL,
    workflow_type VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_handled BOOLEAN DEFAULT false,
    handled_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for pending notifications
CREATE INDEX IF NOT EXISTS idx_pending_notifications_user_id ON pending_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_notifications_request_id ON pending_notifications(request_id);
CREATE INDEX IF NOT EXISTS idx_pending_notifications_is_handled ON pending_notifications(is_handled);

-- Function to clean up old error records (older than 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_error_records()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM error_records 
    WHERE occurred_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
    AND resolved_at IS NOT NULL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old transaction logs (older than 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_transaction_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM transaction_log 
    WHERE started_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
    AND status IN ('completed', 'rolled_back');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old system health snapshots (keep only last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_health_snapshots()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM system_health_snapshots 
    WHERE snapshot_time < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get system health summary
CREATE OR REPLACE FUNCTION get_system_health_summary()
RETURNS TABLE (
    active_requests BIGINT,
    pending_notifications BIGINT,
    recent_errors BIGINT,
    inventory_discrepancies BIGINT,
    stuck_workflows BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM service_requests WHERE current_status != 'completed') as active_requests,
        (SELECT COUNT(*) FROM pending_notifications WHERE is_handled = false) as pending_notifications,
        (SELECT COUNT(*) FROM error_records WHERE occurred_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours') as recent_errors,
        (SELECT COUNT(*) FROM materials WHERE quantity_in_stock < 0) as inventory_discrepancies,
        (SELECT COUNT(*) FROM service_requests 
         WHERE current_status != 'completed' 
         AND updated_at < CURRENT_TIMESTAMP - INTERVAL '24 hours') as stuck_workflows;
END;
$$ LANGUAGE plpgsql;

-- Insert initial system health snapshot
INSERT INTO system_health_snapshots (
    active_requests, pending_notifications, error_count_24h, 
    inventory_discrepancies, stuck_workflows, system_status, notes
) 
SELECT 
    active_requests, pending_notifications, recent_errors,
    inventory_discrepancies, stuck_workflows,
    CASE 
        WHEN recent_errors > 50 OR stuck_workflows > 10 THEN 'critical'
        WHEN recent_errors > 20 OR stuck_workflows > 5 THEN 'degraded'
        ELSE 'healthy'
    END as system_status,
    'Initial system health snapshot after error recovery migration'
FROM get_system_health_summary();

-- Add comments to tables
COMMENT ON TABLE error_records IS 'Comprehensive error tracking and categorization';
COMMENT ON TABLE transaction_log IS 'Transactional operation logging for rollback support';
COMMENT ON TABLE notification_retry_queue IS 'Notification retry queue with exponential backoff';
COMMENT ON TABLE inventory_reconciliation_log IS 'Inventory discrepancy detection and resolution log';
COMMENT ON TABLE workflow_recovery_log IS 'Workflow recovery actions and admin interventions';
COMMENT ON TABLE system_health_snapshots IS 'System health monitoring and alerting';
COMMENT ON TABLE inventory_transactions IS 'Inventory transaction audit trail';
COMMENT ON TABLE pending_notifications IS 'Pending notification tracking system';