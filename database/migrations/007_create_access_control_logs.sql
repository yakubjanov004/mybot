-- Migration: Create access control logs table
-- Description: Creates table for logging access control attempts and audit trail

-- Create access_control_logs table
CREATE TABLE IF NOT EXISTS access_control_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(200) NOT NULL,
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    reason TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(100),
    
    -- Indexes for performance
    INDEX idx_access_logs_user_id (user_id),
    INDEX idx_access_logs_timestamp (timestamp),
    INDEX idx_access_logs_action (action),
    INDEX idx_access_logs_granted (granted),
    INDEX idx_access_logs_resource (resource)
);

-- Add foreign key constraint to users table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE access_control_logs 
        ADD CONSTRAINT fk_access_logs_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create partial index for failed access attempts (for security monitoring)
CREATE INDEX IF NOT EXISTS idx_access_logs_failed_attempts 
ON access_control_logs (user_id, timestamp) 
WHERE granted = FALSE;

-- Create index for resource-based queries
CREATE INDEX IF NOT EXISTS idx_access_logs_resource_granted 
ON access_control_logs (resource, granted, timestamp);

-- Add comment to table
COMMENT ON TABLE access_control_logs IS 'Audit trail for workflow access control attempts';
COMMENT ON COLUMN access_control_logs.user_id IS 'ID of user attempting access';
COMMENT ON COLUMN access_control_logs.action IS 'Action being attempted';
COMMENT ON COLUMN access_control_logs.resource IS 'Resource being accessed';
COMMENT ON COLUMN access_control_logs.granted IS 'Whether access was granted';
COMMENT ON COLUMN access_control_logs.reason IS 'Reason for access decision';
COMMENT ON COLUMN access_control_logs.timestamp IS 'When access attempt occurred';
COMMENT ON COLUMN access_control_logs.ip_address IS 'IP address of request (if available)';
COMMENT ON COLUMN access_control_logs.user_agent IS 'User agent string (if available)';
COMMENT ON COLUMN access_control_logs.session_id IS 'Session identifier (if available)';