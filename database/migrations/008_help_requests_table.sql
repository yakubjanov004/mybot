-- Create help_requests table for technician help functionality
CREATE TABLE IF NOT EXISTS help_requests (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    help_type VARCHAR(50) NOT NULL, -- 'equipment', 'parts', 'question', 'emergency'
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'resolved', 'closed'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'emergency'
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolution TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_help_requests_technician ON help_requests(technician_id);
CREATE INDEX IF NOT EXISTS idx_help_requests_status ON help_requests(status);
CREATE INDEX IF NOT EXISTS idx_help_requests_priority ON help_requests(priority);

-- Create inventory_movements table for tracking warehouse operations
CREATE TABLE IF NOT EXISTS inventory_movements (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
    movement_type VARCHAR(20) NOT NULL, -- 'in', 'out', 'adjustment'
    quantity INTEGER NOT NULL,
    reason VARCHAR(100),
    order_id INTEGER REFERENCES zayavka(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for inventory movements
CREATE INDEX IF NOT EXISTS idx_inventory_movements_material ON inventory_movements(material_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_date ON inventory_movements(created_at);
