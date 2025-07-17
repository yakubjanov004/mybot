-- Performance optimization indexes for existing tables
-- Migration: 007_performance_indexes.sql

-- Create workflow tables first if they don't exist
CREATE TABLE IF NOT EXISTS service_requests (
    id VARCHAR(50) PRIMARY KEY,
    workflow_type VARCHAR(50) NOT NULL,
    client_id INTEGER,
    role_current VARCHAR(50),
    current_status VARCHAR(50) NOT NULL DEFAULT 'created',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    description TEXT,
    location TEXT,
    contact_info JSONB DEFAULT '{}',
    state_data JSONB DEFAULT '{}',
    equipment_used JSONB DEFAULT '[]',
    inventory_updated BOOLEAN DEFAULT FALSE,
    completion_rating INTEGER CHECK (completion_rating BETWEEN 1 AND 5),
    feedback_comments TEXT
);

CREATE TABLE IF NOT EXISTS state_transitions (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50) NOT NULL,
    from_role VARCHAR(50),
    to_role VARCHAR(50),
    action VARCHAR(100),
    actor_id INTEGER,
    transition_data JSONB DEFAULT '{}',
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Update existing notifications table to add missing columns if they don't exist
DO $$ 
BEGIN
    -- Add title column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='notifications' AND column_name='title') THEN
        ALTER TABLE notifications ADD COLUMN title TEXT;
    END IF;
    
    -- Add notification_type column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='notifications' AND column_name='notification_type') THEN
        ALTER TABLE notifications ADD COLUMN notification_type VARCHAR(50) DEFAULT 'info';
    END IF;
    
    -- Add related_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='notifications' AND column_name='related_id') THEN
        ALTER TABLE notifications ADD COLUMN related_id INTEGER;
    END IF;
    
    -- Add related_type column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='notifications' AND column_name='related_type') THEN
        ALTER TABLE notifications ADD COLUMN related_type VARCHAR(50);
    END IF;
    
    -- Add is_read column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='notifications' AND column_name='is_read') THEN
        ALTER TABLE notifications ADD COLUMN is_read BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add read_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='notifications' AND column_name='read_at') THEN
        ALTER TABLE notifications ADD COLUMN read_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Add created_at column if it doesn't exist (notifications table already has sent_at)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='notifications' AND column_name='created_at') THEN
        ALTER TABLE notifications ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50),
    equipment_id INTEGER,
    quantity_used INTEGER NOT NULL DEFAULT 0,
    transaction_type VARCHAR(50) NOT NULL DEFAULT 'consume',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- Indexes for existing tables optimization
CREATE INDEX IF NOT EXISTS idx_users_role_active 
ON users(role) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_users_telegram_id_role 
ON users(telegram_id, role);

CREATE INDEX IF NOT EXISTS idx_zayavki_status_assigned 
ON zayavki(status, assigned_to) 
WHERE status != 'closed';

CREATE INDEX IF NOT EXISTS idx_zayavki_created_priority 
ON zayavki(created_at DESC, priority);

CREATE INDEX IF NOT EXISTS idx_zayavki_user_status 
ON zayavki(user_id, status);

CREATE INDEX IF NOT EXISTS idx_zayavki_role_current_status 
ON zayavki(role_current, status);

-- Indexes for service_requests table
CREATE INDEX IF NOT EXISTS idx_service_requests_role_current 
ON service_requests(role_current ) 
WHERE current_status != 'completed';

CREATE INDEX IF NOT EXISTS idx_service_requests_status_role 
ON service_requests(current_status, role_current );

CREATE INDEX IF NOT EXISTS idx_service_requests_workflow_type 
ON service_requests(workflow_type);

CREATE INDEX IF NOT EXISTS idx_service_requests_client_id 
ON service_requests(client_id);

CREATE INDEX IF NOT EXISTS idx_service_requests_created_at 
ON service_requests(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_service_requests_priority_status 
ON service_requests(priority, current_status) 
WHERE current_status != 'completed';

-- Indexes for state_transitions table
CREATE INDEX IF NOT EXISTS idx_state_transitions_request_id 
ON state_transitions(request_id);

CREATE INDEX IF NOT EXISTS idx_state_transitions_to_role 
ON state_transitions(to_role);

CREATE INDEX IF NOT EXISTS idx_state_transitions_created_at 
ON state_transitions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_state_transitions_actor_id 
ON state_transitions(actor_id) 
WHERE actor_id IS NOT NULL;

-- Enhanced indexes for existing notifications table
CREATE INDEX IF NOT EXISTS idx_notifications_user_id_unread 
ON notifications(user_id) 
WHERE is_read = false;

CREATE INDEX IF NOT EXISTS idx_notifications_related_type_id 
ON notifications(related_type, related_id);

CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
ON notifications(created_at DESC);

-- Indexes for inventory_transactions table
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_request_id 
ON inventory_transactions(request_id) 
WHERE request_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_inventory_transactions_equipment_id 
ON inventory_transactions(equipment_id);

CREATE INDEX IF NOT EXISTS idx_inventory_transactions_created_at 
ON inventory_transactions(created_at DESC);

-- Composite indexes for complex queries
CREATE INDEX IF NOT EXISTS idx_service_requests_role_status_priority 
ON service_requests(role_current , current_status, priority);

CREATE INDEX IF NOT EXISTS idx_service_requests_workflow_status_created 
ON service_requests(workflow_type, current_status, created_at DESC);

-- Partial indexes for performance
CREATE INDEX IF NOT EXISTS idx_service_requests_active_by_role 
ON service_requests(role_current , created_at DESC) 
WHERE current_status IN ('created', 'in_progress', 'on_hold');

CREATE INDEX IF NOT EXISTS idx_notifications_pending_by_user 
ON notifications(user_id, created_at DESC) 
WHERE is_read = false;

-- Indexes for reporting and analytics
CREATE INDEX IF NOT EXISTS idx_state_transitions_action_date 
ON state_transitions(action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_service_requests_completion_stats 
ON service_requests(workflow_type, created_at, updated_at) 
WHERE current_status = 'completed';

-- Enhanced indexes for existing tables
CREATE INDEX IF NOT EXISTS idx_materials_active_category 
ON materials(category, is_active) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_materials_low_stock 
ON materials(name, quantity, min_quantity) 
WHERE quantity <= min_quantity;

CREATE INDEX IF NOT EXISTS idx_feedback_rating_created 
ON feedback(rating, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_help_requests_status_priority 
ON help_requests(status, priority, created_at DESC);

-- Add comments for documentation
COMMENT ON INDEX idx_service_requests_role_current IS 'Optimizes role-based request filtering for active requests';
COMMENT ON INDEX idx_service_requests_status_role IS 'Optimizes status and role combination queries';
COMMENT ON INDEX idx_notifications_user_id_unread IS 'Optimizes unread notification queries per user';
COMMENT ON INDEX idx_service_requests_active_by_role IS 'Partial index for active requests by role';
COMMENT ON INDEX idx_materials_low_stock IS 'Optimizes low stock material queries';
COMMENT ON INDEX idx_zayavki_role_current_status IS 'Optimizes workflow role and status queries';