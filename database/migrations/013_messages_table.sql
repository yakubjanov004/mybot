-- Messages jadvalini yaratish
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    recipient_role VARCHAR(50) NOT NULL,
    message_text TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    is_read BOOLEAN DEFAULT false,
    is_urgent BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexlar qo'shish
CREATE INDEX IF NOT EXISTS idx_messages_recipient_role ON messages(recipient_role);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_is_read ON messages(is_read);
CREATE INDEX IF NOT EXISTS idx_messages_is_urgent ON messages(is_urgent);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_messages_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_messages_updated_at();

-- Test ma'lumotlari qo'shish (ixtiyoriy)
INSERT INTO messages (sender_id, recipient_role, message_text, is_urgent) VALUES
(NULL, 'manager', 'Tizim yangilandi va barcha funksiyalar ishlayapti', false),
(NULL, 'manager', 'Yangi mijoz ro\'yxatdan o\'tdi', false),
(NULL, 'manager', 'Texnik xizmat so\'rovi keldi', true); 