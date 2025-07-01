-- Create feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    operator_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_rating CHECK (rating >= 1 AND rating <= 5)
);

-- Create chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    operator_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('active', 'closed'))
);

-- Create chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL REFERENCES chat_sessions(id),
    sender_id INTEGER NOT NULL REFERENCES users(id),
    message_text TEXT NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_message_type CHECK (message_type IN ('text', 'file', 'image'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_feedback_client ON feedback(client_id);
CREATE INDEX IF NOT EXISTS idx_feedback_operator ON feedback(operator_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_client ON chat_sessions(client_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_operator ON chat_sessions(operator_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_chat ON chat_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender ON chat_messages(sender_id);

-- Add permissions
GRANT SELECT, INSERT, UPDATE ON feedback TO call_center;
GRANT SELECT, INSERT, UPDATE ON chat_sessions TO call_center;
GRANT SELECT, INSERT ON chat_messages TO call_center;

GRANT USAGE, SELECT ON SEQUENCE feedback_id_seq TO call_center;
GRANT USAGE, SELECT ON SEQUENCE chat_sessions_id_seq TO call_center;
GRANT USAGE, SELECT ON SEQUENCE chat_messages_id_seq TO call_center; 