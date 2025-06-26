-- ========== 1. Users (Foydalanuvchilar) ==========
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    phone_number VARCHAR(20),
    abonent_id VARCHAR(50),
    role VARCHAR(20) NOT NULL DEFAULT 'client' CHECK (role IN (
        'admin', 'technician', 'client', 'blocked',
        'call_center', 'manager', 'controller', 'warehouse'
    )),
    language VARCHAR(2) DEFAULT 'uz',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_role ON users(role);

-- ========== 2. Materials (Jihozlar) ==========
CREATE TABLE IF NOT EXISTS materials (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    stock INTEGER DEFAULT 0 CHECK (stock >= 0),
    ready_to_install BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_materials_category ON materials(category);

-- ========== 3. Zayavki (Murojaatlar) ==========
CREATE TABLE IF NOT EXISTS zayavki (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    media TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN (
        'new', 'pending', 'in_progress', 'completed', 'cancelled'
    )),
    address TEXT,
    location TEXT,
    zayavka_type VARCHAR(50),
    abonent_id VARCHAR(50),
    assigned_to BIGINT REFERENCES users(id) ON DELETE SET NULL,
    ready_to_install BOOLEAN DEFAULT FALSE,
    created_by_role VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_zayavki_user_id ON zayavki(user_id);
CREATE INDEX idx_zayavki_status ON zayavki(status);
CREATE INDEX idx_zayavki_assigned_to ON zayavki(assigned_to);
CREATE INDEX idx_zayavki_created_at ON zayavki(created_at DESC);

-- ========== 4. Solutions (Zayavka yechimlari) ==========
CREATE TABLE IF NOT EXISTS solutions (
    id SERIAL PRIMARY KEY,
    zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
    instander_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    solution_text TEXT NOT NULL,
    media TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_solutions_zayavka_id ON solutions(zayavka_id);

-- ========== 5. Feedback (Foydalanuvchi baholari) ==========
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_zayavka_id ON feedback(zayavka_id);

-- ========== 6. Status Logs (Status o'zgarish tarixi) ==========
CREATE TABLE IF NOT EXISTS status_logs (
    id SERIAL PRIMARY KEY,
    zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
    changed_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_status_logs_zayavka_id ON status_logs(zayavka_id);

-- ========== 7. Issued Items (Berilgan jihozlar) ==========
CREATE TABLE IF NOT EXISTS issued_items (
    id SERIAL PRIMARY KEY,
    zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
    material_id INTEGER REFERENCES materials(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    issued_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_issued_items_zayavka_id ON issued_items(zayavka_id);
CREATE INDEX idx_issued_items_material_id ON issued_items(material_id);

-- ========== 8. Login Logs (Kirish loglari) ==========
CREATE TABLE IF NOT EXISTS login_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    ip_address TEXT,
    user_agent TEXT,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_login_logs_user_id ON login_logs(user_id);
CREATE INDEX idx_login_logs_logged_at ON login_logs(logged_at DESC);

-- ========== 9. Notifications (Xabarlar) ==========
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    channel VARCHAR(10) CHECK (channel IN ('telegram', 'email')),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_zayavka_id ON notifications(zayavka_id);
