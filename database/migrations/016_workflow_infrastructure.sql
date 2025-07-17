-- 016_workflow_infrastructure.sql
-- Create tables for enhanced workflow system

-- 1. Service Requests table
CREATE TABLE IF NOT EXISTS service_requests (
    id VARCHAR(36) PRIMARY KEY,
    workflow_type VARCHAR(50) NOT NULL CHECK (workflow_type IN ('connection_request', 'technical_service', 'call_center_direct')),
    client_id INTEGER REFERENCES users(id),
    role_current VARCHAR(50) NOT NULL CHECK (role_current IN (
        'admin', 'call_center', 'call_center_supervisor', 'technician', 
        'manager', 'junior_manager', 'controller', 'warehouse', 'client', 'blocked'
    )),
    current_status VARCHAR(50) NOT NULL CHECK (current_status IN ('created', 'in_progress', 'completed', 'cancelled', 'on_hold')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    
    -- Request details
    description TEXT,
    location TEXT,
    contact_info JSONB DEFAULT '{}',
    
    -- Workflow state
    state_data JSONB DEFAULT '{}',
    
    -- Equipment tracking
    equipment_used JSONB DEFAULT '[]',
    inventory_updated BOOLEAN DEFAULT FALSE,
    
    -- Quality tracking
    completion_rating INTEGER CHECK (completion_rating >= 1 AND completion_rating <= 5),
    feedback_comments TEXT
);

-- 2. State Transitions table
CREATE TABLE IF NOT EXISTS state_transitions (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(36) NOT NULL REFERENCES service_requests(id) ON DELETE CASCADE,
    from_role VARCHAR(50),
    to_role VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    actor_id INTEGER REFERENCES users(id),
    transition_data JSONB DEFAULT '{}',
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Workflow Notifications table (enhanced from existing notifications)
CREATE TABLE IF NOT EXISTS workflow_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_id VARCHAR(36) NOT NULL REFERENCES service_requests(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL DEFAULT 'assignment',
    title VARCHAR(255),
    message TEXT,
    is_handled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    handled_at TIMESTAMP WITH TIME ZONE
);

-- 4. Inventory Transactions table (for equipment tracking)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(36) REFERENCES service_requests(id) ON DELETE CASCADE,
    material_id INTEGER REFERENCES materials(id),
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('reserve', 'consume', 'return')),
    quantity INTEGER NOT NULL,
    performed_by INTEGER REFERENCES users(id),
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_service_requests_client_id ON service_requests(client_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_role_current ON service_requests(role_current );
CREATE INDEX IF NOT EXISTS idx_service_requests_current_status ON service_requests(current_status);
CREATE INDEX IF NOT EXISTS idx_service_requests_workflow_type ON service_requests(workflow_type);
CREATE INDEX IF NOT EXISTS idx_service_requests_created_at ON service_requests(created_at);

CREATE INDEX IF NOT EXISTS idx_state_transitions_request_id ON state_transitions(request_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_created_at ON state_transitions(created_at);

CREATE INDEX IF NOT EXISTS idx_workflow_notifications_user_id ON workflow_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_notifications_request_id ON workflow_notifications(request_id);
CREATE INDEX IF NOT EXISTS idx_workflow_notifications_is_handled ON workflow_notifications(is_handled);

CREATE INDEX IF NOT EXISTS idx_inventory_transactions_request_id ON inventory_transactions(request_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_material_id ON inventory_transactions(material_id);

-- Add trigger to update updated_at timestamp on service_requests
CREATE OR REPLACE FUNCTION update_service_request_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_service_request_updated_at
    BEFORE UPDATE ON service_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_service_request_updated_at();

-- END OF MIGRATION