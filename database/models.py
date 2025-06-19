from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: int
    telegram_id: int
    full_name: Optional[str] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None
    role: str = 'client'
    abonent_id: Optional[str] = None
    language: str = 'uz'
    created_at: datetime = datetime.now()

@dataclass
class Zayavka:
    id: int
    user_id: int
    description: str
    media: Optional[str] = None
    status: str = 'pending'
    address: Optional[str] = None
    assigned_to: Optional[int] = None
    ready_to_install: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = datetime.now()

@dataclass
class Material:
    id: int
    name: str
    category: Optional[str] = None
    stock: int = 0
    created_at: datetime = datetime.now()

@dataclass
class Solution:
    id: int
    zayavka_id: int
    instander_id: int
    solution_text: str
    media: Optional[str] = None
    created_at: datetime = datetime.now()

@dataclass
class Feedback:
    id: int
    zayavka_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime = datetime.now()

@dataclass
class StatusLog:
    id: int
    zayavka_id: int
    old_status: str
    new_status: str
    changed_by: int
    changed_at: datetime = datetime.now()

@dataclass
class IssuedItem:
    id: int
    zayavka_id: int
    material_id: int
    quantity: int
    issued_by: int
    issued_at: datetime = datetime.now()

@dataclass
class LoginLog:
    id: int
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    logged_at: datetime = datetime.now()

@dataclass
class Notification:
    id: int
    user_id: int
    message: str
    zayavka_id: Optional[int] = None
    sent_at: datetime = datetime.now()
    channel: str = 'telegram'

# Ma'lumotlar bazasi jadvallarini yaratish uchun SQL so'rovlari
CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    language VARCHAR(2) DEFAULT 'uz',
    full_name TEXT,
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    notifications_enabled BOOLEAN DEFAULT TRUE,
    privacy_mode BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""" 