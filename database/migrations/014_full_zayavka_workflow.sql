-- 014_full_zayavka_workflow.sql
-- To‘liq zayavka workflow va rollar uchun migratsiya

-- 1. DROP TABLE (child -> parent tartibida)
DROP TABLE IF EXISTS issued_items CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS zayavka_status_history CASCADE;
DROP TABLE IF EXISTS zayavki CASCADE;
DROP TABLE IF EXISTS materials CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 2. CREATE TABLE (parent -> child tartibida)

-- users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    full_name TEXT,
    username TEXT,
    phone_number TEXT,
    role VARCHAR(30) NOT NULL CHECK (role IN (
        'admin',
        'call_center',            -- operator
        'call_center_supervisor', -- nazoratchi
        'technician',
        'manager',
        'junior_manager',
        'controller',
        'warehouse',
        'client',
        'blocked'
    )),
    abonent_id VARCHAR(50),
    language VARCHAR(2) NOT NULL DEFAULT 'uz' CHECK (language IN ('uz', 'ru')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- materials
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

-- zayavki
CREATE TABLE zayavki (
    id SERIAL PRIMARY KEY,
    public_id VARCHAR(20) UNIQUE,
    zayavka_type VARCHAR(10) NOT NULL CHECK (zayavka_type IN ('ul', 'tx')),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'new',
    role_current VARCHAR(30),
    current_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    abonent_id VARCHAR(50),
    phone_number TEXT,
    priority INTEGER NOT NULL DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_by_role VARCHAR(30),
    assigned_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- zayavka_status_history
CREATE TABLE zayavka_status_history (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER NOT NULL REFERENCES zayavki(id) ON DELETE CASCADE,
    old_status VARCHAR(30) NOT NULL,
    new_status VARCHAR(30) NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    changed_by_role VARCHAR(30),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    comment TEXT
);

-- feedback
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER NOT NULL REFERENCES zayavki(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER REFERENCES zayavki(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    recipient_role VARCHAR(30) NOT NULL,
    recipient_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    message_text TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    is_read BOOLEAN DEFAULT false,
    is_urgent BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- issued_items
CREATE TABLE issued_items (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER REFERENCES zayavki(id) ON DELETE CASCADE,
    material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    issued_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issued_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Triggers, Indexes, etc.
-- updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zayavki_updated_at BEFORE UPDATE ON zayavki
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_materials_updated_at BEFORE UPDATE ON materials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4. Indekslar
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_zayavki_status ON zayavki(status);
CREATE INDEX idx_zayavki_role_current ON zayavki(role_current);
CREATE INDEX idx_zayavka_status_history_zayavka_id ON zayavka_status_history(zayavka_id);
CREATE INDEX idx_messages_recipient_role ON messages(recipient_role);
CREATE INDEX idx_messages_recipient_user_id ON messages(recipient_user_id);
CREATE INDEX idx_materials_category ON materials(category);
CREATE INDEX idx_issued_items_zayavka_id ON issued_items(zayavka_id);
CREATE INDEX idx_issued_items_material_id ON issued_items(material_id);

-- END OF MIGRATION 