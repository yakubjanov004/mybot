import asyncio
import asyncpg
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os
import logging
from aiogram.client.default import DefaultBotProperties
from config import config
from utils.logger import logger

logging.basicConfig(level=logging.INFO)

load_dotenv()

# Initialize bot
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
bot.pool = None  # Initialize pool attribute
bot.zayavka_group_id = config.ZAYAVKA_GROUP_ID

async def create_db_pool():
    """Create database connection pool"""
    try:
        pool = await asyncpg.create_pool(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        bot.pool = pool
        logger.info("Database connection pool created with settings: host=%s, port=%s, db=%s, user=%s",
                   config.DB_HOST, config.DB_PORT, config.DB_NAME, config.DB_USER)
        return pool
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        raise

async def on_startup():
    bot.pool = await create_db_pool()
    
    # Create all tables if not exists
    async with bot.pool.acquire() as conn:
        # Users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                abonent_id VARCHAR(20),
                role VARCHAR(20) NOT NULL CHECK (role IN (
                    'abonent', 'client', 'manager', 'instander', 'callcenter', 'kontroler', 'sklad', 'admin'
                )),
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                phone_number TEXT
            )
        ''')

        # Materials table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                stock INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Zayavki table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS zayavki (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                description TEXT NOT NULL,
                address TEXT,
                media TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
                    'pending', 'assigned', 'in_progress', 'completed', 'cancelled'
                )),
                assigned_to INTEGER REFERENCES users(id),
                ready_to_install BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')

        # Solutions table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS solutions (
                id SERIAL PRIMARY KEY,
                zayavka_id INTEGER REFERENCES zayavki(id),
                instander_id INTEGER REFERENCES users(id),
                solution_text TEXT,
                media TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Feedback table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                zayavka_id INTEGER REFERENCES zayavki(id),
                user_id INTEGER REFERENCES users(id),
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Status logs table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS status_logs (
                id SERIAL PRIMARY KEY,
                zayavka_id INTEGER REFERENCES zayavki(id),
                changed_by INTEGER REFERENCES users(id),
                old_status VARCHAR(20),
                new_status VARCHAR(20),
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Issued items table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS issued_items (
                id SERIAL PRIMARY KEY,
                zayavka_id INTEGER REFERENCES zayavki(id),
                material_id INTEGER REFERENCES materials(id),
                quantity INTEGER NOT NULL,
                issued_by INTEGER REFERENCES users(id),
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Login logs table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                ip_address TEXT,
                user_agent TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Notifications table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                zayavka_id INTEGER REFERENCES zayavki(id),
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                channel VARCHAR(10) CHECK (channel IN ('telegram', 'email'))
            )
        ''')
    
    logging.info("Bot ishga tushdi!")