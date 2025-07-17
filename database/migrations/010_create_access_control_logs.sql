-- Migration: Create access control logs table
-- Description: Creates table for logging access control attempts and audit trail

-- Create access control logs table
CREATE TABLE IF NOT EXISTS access_control_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(200) NOT NULL,
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Add foreign key constraint to users table
    CONSTRAINT fk_access_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_control_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_control_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_access_logs_granted ON access_control_logs(granted);
CREATE INDEX IF NOT EXISTS idx_access_logs_action ON access_control_logs(action);
CREATE INDEX IF NOT EXISTS idx_access_logs_resource ON access_control_logs(resource);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_access_logs_user_action ON access_control_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_access_logs_user_granted ON access_control_logs(user_id, granted);
CREATE INDEX IF NOT EXISTS idx_access_logs_action_granted ON access_control_logs(action, granted);

-- Add comment to table
COMMENT ON TABLE access_control_logs IS 'Audit trail for access control decisions and attempts';
COMMENT ON COLUMN access_control_logs.user_id IS 'ID of user attempting access';
COMMENT ON COLUMN access_control_logs.action IS 'Action being attempted';
COMMENT ON COLUMN access_control_logs.resource IS 'Resource being accessed';
COMMENT ON COLUMN access_control_logs.granted IS 'Whether access was granted';
COMMENT ON COLUMN access_control_logs.reason IS 'Reason for access decision';
COMMENT ON COLUMN access_control_logs.created_at IS 'Timestamp of access attempt';