-- Performance optimization indexes for existing tables
-- Migration: 007_performance_indexes_simple.sql

-- Create workflow tables first
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
    completion_rating INTEGER,
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

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(50),
    equipment_id INTEGER,
    quantity_used INTEGER NOT NULL DEFAULT 0,
    transaction_type VARCHAR(50) NOT NULL DEFAULT 'consume',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- Add performance indexes for existing tables
CREATE INDEX IF NOT EXISTS idx_users_role_active ON users(role) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_telegram_id_role ON users(telegram_id, role);
CREATE INDEX IF NOT EXISTS idx_zayavki_status_assigned ON zayavki(status, assigned_to);
CREATE INDEX IF NOT EXISTS idx_zayavki_created_priority ON zayavki(created_at DESC, priority);
CREATE INDEX IF NOT EXISTS idx_zayavki_user_status ON zayavki(user_id, status);
CREATE INDEX IF NOT EXISTS idx_zayavki_role_current_status ON zayavki(role_current, status);

-- Add performance indexes for new workflow tables
CREATE INDEX IF NOT EXISTS idx_service_requests_role_current ON service_requests(role_current);
CREATE INDEX IF NOT EXISTS idx_service_requests_status_role ON service_requests(current_status, role_current);
CREATE INDEX IF NOT EXISTS idx_service_requests_workflow_type ON service_requests(workflow_type);
CREATE INDEX IF NOT EXISTS idx_service_requests_client_id ON service_requests(client_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_created_at ON service_requests(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_state_transitions_request_id ON state_transitions(request_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_to_role ON state_transitions(to_role);
CREATE INDEX IF NOT EXISTS idx_state_transitions_created_at ON state_transitions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_inventory_transactions_request_id ON inventory_transactions(request_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_equipment_id ON inventory_transactions(equipment_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_created_at ON inventory_transactions(created_at DESC);

-- Enhanced indexes for materials and feedback
CREATE INDEX IF NOT EXISTS idx_materials_active_category ON materials(category, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_feedback_rating_created ON feedback(rating, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_help_requests_status_priority ON help_requests(status, priority, created_at DESC);