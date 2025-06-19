-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    abonent_id VARCHAR(50),
    role VARCHAR(20) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    phone_number VARCHAR(20),
    language VARCHAR(10) DEFAULT 'uz'
);

-- Create zayavki table
CREATE TABLE IF NOT EXISTS zayavki (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    description TEXT,
    media TEXT,
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'pending', 'in_progress', 'completed', 'cancelled')),
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    zayavka_type VARCHAR(50),
    abonent_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
); 