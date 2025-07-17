-- Migration: Create pending_notifications table for Universal Notification System
-- This table tracks notifications sent to users for workflow assignments

CREATE TABLE IF NOT EXISTS pending_notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id VARCHAR(36) NOT NULL REFERENCES service_requests(id) ON DELETE CASCADE,
    workflow_type VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_handled BOOLEAN DEFAULT FALSE,
    handled_at TIMESTAMP NULL
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_pending_notifications_user_id ON pending_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_notifications_request_id ON pending_notifications(request_id);
CREATE INDEX IF NOT EXISTS idx_pending_notifications_role ON pending_notifications(role);
CREATE INDEX IF NOT EXISTS idx_pending_notifications_is_handled ON pending_notifications(is_handled);
CREATE INDEX IF NOT EXISTS idx_pending_notifications_created_at ON pending_notifications(created_at);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_pending_notifications_user_unhandled 
ON pending_notifications(user_id, is_handled) WHERE is_handled = FALSE;

-- Add comments for documentation
COMMENT ON TABLE pending_notifications IS 'Tracks workflow assignment notifications sent to users';
COMMENT ON COLUMN pending_notifications.id IS 'Unique notification identifier';
COMMENT ON COLUMN pending_notifications.user_id IS 'ID of user who received the notification';
COMMENT ON COLUMN pending_notifications.request_id IS 'ID of the service request being assigned';
COMMENT ON COLUMN pending_notifications.workflow_type IS 'Type of workflow (connection_request, technical_service, etc.)';
COMMENT ON COLUMN pending_notifications.role IS 'Role that received the notification';
COMMENT ON COLUMN pending_notifications.created_at IS 'When the notification was created';
COMMENT ON COLUMN pending_notifications.is_handled IS 'Whether the notification has been handled/viewed';
COMMENT ON COLUMN pending_notifications.handled_at IS 'When the notification was marked as handled';