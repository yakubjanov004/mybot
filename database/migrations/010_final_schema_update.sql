-- Final comprehensive schema update
-- This migration ensures all tables are properly structured with constraints and indexes

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS material_receipts CASCADE;
DROP TABLE IF EXISTS equipment_requests CASCADE;
DROP TABLE IF EXISTS technician_locations CASCADE;
DROP TABLE IF EXISTS notification_templates CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS help_requests CASCADE;
DROP TABLE IF EXISTS call_logs CASCADE;
DROP TABLE IF EXISTS issued_items CASCADE;
DROP TABLE IF EXISTS status_logs CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS solutions CASCADE;
DROP TABLE IF EXISTS zayavki CASCADE;
DROP TABLE IF EXISTS materials CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table with all necessary fields
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    full_name TEXT,
    username TEXT,
    phone_number TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'client' CHECK (role IN (
        'admin', 'call_center', 'technician', 'manager', 'controller', 
        'warehouse', 'client', 'blocked'
    )),
    abonent_id VARCHAR(50),
    language VARCHAR(2) NOT NULL DEFAULT 'uz' CHECK (language IN ('uz', 'ru')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    address TEXT,
    permissions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create materials table
CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    unit VARCHAR(10) NOT NULL DEFAULT 'pcs',
    min_quantity INTEGER NOT NULL DEFAULT 5 CHECK (min_quantity >= 0),
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00 CHECK (price >= 0),
    description TEXT,
    supplier TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create zayavki table
CREATE TABLE zayavki (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    media TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN (
        'new', 'pending', 'assigned', 'in_progress', 'completed', 'cancelled', 'transferred'
    )),
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    zayavka_type VARCHAR(20),
    abonent_id VARCHAR(50),
    phone_number TEXT,
    priority INTEGER NOT NULL DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    estimated_time INTEGER, -- in minutes
    actual_time INTEGER, -- in minutes
    completion_notes TEXT,
    created_by_role VARCHAR(20),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ready_to_install BOOLEAN NOT NULL DEFAULT false,
    assigned_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create solutions table
CREATE TABLE solutions (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER NOT NULL REFERENCES zayavki(id) ON DELETE CASCADE,
    instander_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    solution_text TEXT NOT NULL,
    media TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create feedback table
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER REFERENCES zayavki(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create status_logs table
CREATE TABLE status_logs (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER NOT NULL REFERENCES zayavki(id) ON DELETE CASCADE,
    old_status VARCHAR(20) NOT NULL,
    new_status VARCHAR(20) NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create issued_items table
CREATE TABLE issued_items (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER REFERENCES zayavki(id) ON DELETE CASCADE,
    material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    issued_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issued_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create call_logs table
CREATE TABLE call_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    phone_number TEXT NOT NULL,
    duration INTEGER NOT NULL DEFAULT 0 CHECK (duration >= 0), -- in seconds
    result VARCHAR(50) NOT NULL,
    notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create help_requests table
CREATE TABLE help_requests (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    help_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'assigned', 'in_progress', 'resolved', 'cancelled'
    )),
    priority VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolution TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Create chat_sessions table
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    operator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed', 'transferred')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- Create chat_messages table
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text' CHECK (message_type IN (
        'text', 'image', 'document', 'location', 'contact'
    )),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create system_settings table
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create notification_templates table
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    template_type VARCHAR(50) NOT NULL,
    language VARCHAR(2) NOT NULL CHECK (language IN ('uz', 'ru')),
    content TEXT NOT NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_type, language)
);

-- Create technician_locations table
CREATE TABLE technician_locations (
    technician_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create equipment_requests table
CREATE TABLE equipment_requests (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    equipment_type VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'issued', 'rejected'
    )),
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create material_receipts table
CREATE TABLE material_receipts (
    id SERIAL PRIMARY KEY,
    material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    received_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    supplier TEXT,
    notes TEXT,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_zayavki_user_id ON zayavki(user_id);
CREATE INDEX idx_zayavki_status ON zayavki(status);
CREATE INDEX idx_zayavki_assigned_to ON zayavki(assigned_to);
CREATE INDEX idx_zayavki_created_at ON zayavki(created_at);
CREATE INDEX idx_zayavki_location ON zayavki(latitude, longitude);
CREATE INDEX idx_solutions_zayavka_id ON solutions(zayavka_id);
CREATE INDEX idx_feedback_zayavka_id ON feedback(zayavka_id);
CREATE INDEX idx_status_logs_zayavka_id ON status_logs(zayavka_id);
CREATE INDEX idx_issued_items_zayavka_id ON issued_items(zayavka_id);
CREATE INDEX idx_issued_items_material_id ON issued_items(material_id);
CREATE INDEX idx_call_logs_user_id ON call_logs(user_id);
CREATE INDEX idx_call_logs_created_by ON call_logs(created_by);
CREATE INDEX idx_help_requests_technician_id ON help_requests(technician_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_materials_category ON materials(category);
CREATE INDEX idx_materials_low_stock ON materials(quantity, min_quantity) WHERE quantity <= min_quantity;

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('bot_version', '2.0.0', 'Current bot version'),
('maintenance_mode', 'false', 'Maintenance mode flag'),
('max_zayavkas_per_day', '10', 'Maximum zayavkas per user per day'),
('default_language', 'uz', 'Default system language'),
('notification_enabled', 'true', 'Global notification flag');

-- Insert default notification templates
INSERT INTO notification_templates (template_type, language, content) VALUES
('zayavka_created', 'uz', 'Sizning zayavkangiz #{id} yaratildi va ko''rib chiqilmoqda.'),
('zayavka_created', 'ru', 'Ваша заявка #{id} создана и рассматривается.'),
('zayavka_assigned', 'uz', 'Sizning zayavkangiz #{id} texnikka tayinlandi.'),
('zayavka_assigned', 'ru', 'Ваша заявка #{id} назначена технику.'),
('zayavka_completed', 'uz', 'Sizning zayavkangiz #{id} bajarildi.'),
('zayavka_completed', 'ru', 'Ваша заявка #{id} выполнена.');

-- Create triggers for updated_at fields
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_materials_updated_at BEFORE UPDATE ON materials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zayavki_updated_at BEFORE UPDATE ON zayavki
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_help_requests_updated_at BEFORE UPDATE ON help_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_requests_updated_at BEFORE UPDATE ON equipment_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_bot_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_bot_user;
