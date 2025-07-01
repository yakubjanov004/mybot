-- Additional tables for new functionality

-- Call logs table for call center
CREATE TABLE IF NOT EXISTS call_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    phone_number VARCHAR(20) NOT NULL,
    duration INTEGER DEFAULT 0, -- in seconds
    result VARCHAR(50) NOT NULL, -- 'order_created', 'callback_requested', 'no_answer', etc.
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Support tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    media JSONB,
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'in_progress', 'resolved', 'closed'
    assigned_to INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Assignment logs table
CREATE TABLE IF NOT EXISTS assignment_logs (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES zayavki(id),
    technician_id INTEGER REFERENCES users(id),
    assigned_by INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Notification settings table
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    new_orders BOOLEAN DEFAULT true,
    status_changes BOOLEAN DEFAULT true,
    urgent_issues BOOLEAN DEFAULT true,
    daily_summary BOOLEAN DEFAULT false,
    system_alerts BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Task transfer requests table
CREATE TABLE IF NOT EXISTS task_transfer_requests (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER REFERENCES zayavki(id),
    from_technician_id INTEGER REFERENCES users(id),
    to_technician_id INTEGER REFERENCES users(id),
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processed_by INTEGER REFERENCES users(id)
);

-- Equipment table (if not exists)
CREATE TABLE IF NOT EXISTS equipment (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    status VARCHAR(50) DEFAULT 'available', -- 'available', 'in_use', 'maintenance', 'ready'
    assigned_to INTEGER REFERENCES users(id),
    location VARCHAR(255),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materials table (if not exists)
CREATE TABLE IF NOT EXISTS materials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 0,
    unit VARCHAR(20) DEFAULT 'pcs',
    min_quantity INTEGER DEFAULT 5,
    price DECIMAL(10,2) DEFAULT 0,
    category VARCHAR(100) DEFAULT 'general',
    description TEXT,
    supplier VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory transactions table
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES materials(id),
    transaction_type VARCHAR(20) NOT NULL, -- 'in', 'out', 'adjustment'
    quantity INTEGER NOT NULL,
    reference_id INTEGER, -- can reference zayavki.id or other tables
    reference_type VARCHAR(50), -- 'order', 'adjustment', 'return', etc.
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50), -- 'user', 'order', 'material', etc.
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    metric_type VARCHAR(50) NOT NULL, -- 'orders_completed', 'avg_response_time', etc.
    metric_value DECIMAL(10,2) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_call_logs_user_id ON call_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_created_at ON call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_assignment_logs_order_id ON assignment_logs(order_id);
CREATE INDEX IF NOT EXISTS idx_assignment_logs_technician_id ON assignment_logs(technician_id);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_material_id ON inventory_transactions(material_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_user_id ON performance_metrics(user_id);

-- Add some sample data for testing
INSERT INTO materials (name, quantity, unit, min_quantity, price, category, description) VALUES
('Ethernet Cable Cat6', 100, 'meters', 20, 5000, 'cables', 'High-quality Cat6 ethernet cable'),
('Router TP-Link', 15, 'pcs', 5, 250000, 'equipment', 'Wireless router for home use'),
('Fiber Optic Cable', 500, 'meters', 50, 15000, 'cables', 'Single-mode fiber optic cable'),
('Network Switch 8-port', 10, 'pcs', 3, 180000, 'equipment', '8-port gigabit network switch'),
('Coaxial Cable RG6', 200, 'meters', 30, 3000, 'cables', 'RG6 coaxial cable for TV/Internet')
ON CONFLICT DO NOTHING;

INSERT INTO equipment (name, type, model, status, description) VALUES
('Installation Kit #1', 'tools', 'Standard', 'available', 'Basic installation tools'),
('Testing Equipment #1', 'testing', 'Advanced', 'available', 'Network testing and diagnostics'),
('Ladder 3m', 'tools', 'Standard', 'available', '3 meter extension ladder'),
('Drill Set', 'tools', 'Professional', 'available', 'Professional drill set with bits'),
('Cable Tester', 'testing', 'Digital', 'available', 'Digital cable testing device')
ON CONFLICT DO NOTHING;
