CREATE TABLE IF NOT EXISTS admin_action_logs (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    performed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
); 