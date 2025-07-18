-- 019_inbox_system_schema.sql
-- Add inbox system schema with role tracking and message management

-- 1. Add role tracking column to zayavki table for inbox functionality
ALTER TABLE zayavki 
ADD COLUMN IF NOT EXISTS assigned_role VARCHAR(50) CHECK (assigned_role IN (
    'manager', 'junior_manager', 'technician', 'warehouse', 
    'call_center', 'call_center_supervisor', 'controller'
));

-- 2. Ensure service_requests has role_current column (should exist from previous migrations)
-- This is a safety check - the column should already exist
ALTER TABLE service_requests 
ADD COLUMN IF NOT EXISTS role_current VARCHAR(50) CHECK (role_current IN (
    'manager', 'junior_manager', 'technician', 'warehouse', 
    'call_center', 'call_center_supervisor', 'controller'
));

-- 3. Create inbox_messages table for application notifications and messages
CREATE TABLE IF NOT EXISTS inbox_messages (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(255) NOT NULL,
    application_type VARCHAR(50) NOT NULL CHECK (application_type IN ('zayavka', 'service_request')),
    assigned_role VARCHAR(50) NOT NULL CHECK (assigned_role IN (
        'manager', 'junior_manager', 'technician', 'warehouse', 
        'call_center', 'call_center_supervisor', 'controller'
    )),
    message_type VARCHAR(50) DEFAULT 'application' CHECK (message_type IN (
        'application', 'transfer', 'notification', 'reminder'
    )),
    title VARCHAR(255),
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure application exists in either zayavki or service_requests
    CONSTRAINT check_application_exists CHECK (
        (application_type = 'zayavka' AND application_id ~ '^[0-9]+$') OR
        (application_type = 'service_request' AND application_id ~ '^[a-f0-9-]{36}$')
    )
);

-- 4. Create application_transfers table for audit trail of role transfers
CREATE TABLE IF NOT EXISTS application_transfers (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(255) NOT NULL,
    application_type VARCHAR(50) NOT NULL CHECK (application_type IN ('zayavka', 'service_request')),
    from_role VARCHAR(50) CHECK (from_role IN (
        'manager', 'junior_manager', 'technician', 'warehouse', 
        'call_center', 'call_center_supervisor', 'controller'
    )),
    to_role VARCHAR(50) NOT NULL CHECK (to_role IN (
        'manager', 'junior_manager', 'technician', 'warehouse', 
        'call_center', 'call_center_supervisor', 'controller'
    )),
    transferred_by INTEGER NOT NULL REFERENCES users(id),
    transfer_reason VARCHAR(255),
    transfer_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure application exists in either zayavki or service_requests
    CONSTRAINT check_transfer_application_exists CHECK (
        (application_type = 'zayavka' AND application_id ~ '^[0-9]+$') OR
        (application_type = 'service_request' AND application_id ~ '^[a-f0-9-]{36}$')
    )
);

-- 5. Create indexes for efficient role-based queries
CREATE INDEX IF NOT EXISTS idx_zayavki_assigned_role ON zayavki(assigned_role) WHERE assigned_role IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_service_requests_role_current ON service_requests(role_current) WHERE role_current IS NOT NULL;

-- Inbox messages indexes
CREATE INDEX IF NOT EXISTS idx_inbox_messages_role_read ON inbox_messages(assigned_role, is_read);
CREATE INDEX IF NOT EXISTS idx_inbox_messages_created_desc ON inbox_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inbox_messages_application ON inbox_messages(application_id, application_type);
CREATE INDEX IF NOT EXISTS idx_inbox_messages_priority ON inbox_messages(priority, created_at DESC);

-- Application transfers indexes
CREATE INDEX IF NOT EXISTS idx_application_transfers_application ON application_transfers(application_id, application_type);
CREATE INDEX IF NOT EXISTS idx_application_transfers_from_role ON application_transfers(from_role, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_application_transfers_to_role ON application_transfers(to_role, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_application_transfers_transferred_by ON application_transfers(transferred_by, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_application_transfers_created_desc ON application_transfers(created_at DESC);

-- 6. Create trigger to automatically update updated_at timestamp for inbox_messages
CREATE OR REPLACE FUNCTION update_inbox_messages_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_inbox_messages_updated_at
    BEFORE UPDATE ON inbox_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_inbox_messages_updated_at();

-- 7. Add comments for documentation
COMMENT ON COLUMN zayavki.assigned_role IS 'Current role assigned to handle this zayavka for inbox system';
COMMENT ON COLUMN service_requests.role_current IS 'Current role assigned to handle this service request for inbox system';

COMMENT ON TABLE inbox_messages IS 'Messages and notifications for role-based inbox system';
COMMENT ON COLUMN inbox_messages.application_id IS 'ID of the application (zayavka.id or service_requests.id)';
COMMENT ON COLUMN inbox_messages.application_type IS 'Type of application: zayavka or service_request';
COMMENT ON COLUMN inbox_messages.assigned_role IS 'Role that should see this message in their inbox';
COMMENT ON COLUMN inbox_messages.message_type IS 'Type of message: application, transfer, notification, reminder';
COMMENT ON COLUMN inbox_messages.is_read IS 'Whether the message has been read by the assigned role';

COMMENT ON TABLE application_transfers IS 'Audit trail for application transfers between roles';
COMMENT ON COLUMN application_transfers.application_id IS 'ID of the transferred application';
COMMENT ON COLUMN application_transfers.application_type IS 'Type of application: zayavka or service_request';
COMMENT ON COLUMN application_transfers.from_role IS 'Role that transferred the application (NULL for initial assignment)';
COMMENT ON COLUMN application_transfers.to_role IS 'Role that received the application';
COMMENT ON COLUMN application_transfers.transferred_by IS 'User who performed the transfer';

-- END OF MIGRATION