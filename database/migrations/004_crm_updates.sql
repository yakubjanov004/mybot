-- CRM tizimi uchun yangi maydonlar va jadvallar

-- Zayavki jadvaliga yangi maydonlar qo'shish
ALTER TABLE zayavki ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 1; -- 1=past, 2=o'rta, 3=yuqori
ALTER TABLE zayavki ADD COLUMN IF NOT EXISTS estimated_time INTEGER; -- soatlarda
ALTER TABLE zayavki ADD COLUMN IF NOT EXISTS actual_time INTEGER; -- haqiqiy vaqt
ALTER TABLE zayavki ADD COLUMN IF NOT EXISTS completion_notes TEXT; -- yakunlash eslatmalari
ALTER TABLE zayavki ADD COLUMN IF NOT EXISTS created_by_role VARCHAR(20);

-- Zayavka statuslarini yangilash
DO $$ 
BEGIN
    -- Eski constraint ni o'chirish
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE table_name = 'zayavki' AND constraint_name = 'zayavki_status_check') THEN
        ALTER TABLE zayavki DROP CONSTRAINT zayavki_status_check;
    END IF;
    
    -- Yangi constraint qo'shish
    ALTER TABLE zayavki ADD CONSTRAINT zayavki_status_check 
        CHECK (status IN ('new', 'assigned', 'in_progress', 'completed', 'cancelled', 'transferred'));
END $$;

-- Technician workload jadvali (ish yukini kuzatish uchun)
CREATE TABLE IF NOT EXISTS technician_workload (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES users(id),
    active_tasks INTEGER DEFAULT 0,
    max_tasks INTEGER DEFAULT 5, -- maksimal vazifalar soni
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Zayavka transfer tarixi
CREATE TABLE IF NOT EXISTS zayavka_transfers (
    id SERIAL PRIMARY KEY,
    zayavka_id INTEGER REFERENCES zayavki(id),
    from_technician_id INTEGER REFERENCES users(id),
    to_technician_id INTEGER REFERENCES users(id),
    transferred_by INTEGER REFERENCES users(id), -- menejer
    reason TEXT,
    transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Technician performance jadvali
CREATE TABLE IF NOT EXISTS technician_performance (
    id SERIAL PRIMARY KEY,
    technician_id INTEGER REFERENCES users(id),
    completed_tasks INTEGER DEFAULT 0,
    average_completion_time DECIMAL(5,2), -- soatlarda
    rating DECIMAL(3,2) DEFAULT 5.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification queue jadvali
CREATE TABLE IF NOT EXISTS notification_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    zayavka_id INTEGER REFERENCES zayavki(id),
    notification_type VARCHAR(50), -- 'assignment', 'completion', 'transfer'
    sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexlar qo'shish
CREATE INDEX IF NOT EXISTS idx_zayavki_status ON zayavki(status);
CREATE INDEX IF NOT EXISTS idx_zayavki_assigned_to ON zayavki(assigned_to);
CREATE INDEX IF NOT EXISTS idx_notification_queue_sent ON notification_queue(sent);
CREATE INDEX IF NOT EXISTS idx_technician_workload_technician ON technician_workload(technician_id);
