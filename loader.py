import asyncio

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from config import config
from aiogram.fsm.storage.memory import MemoryStorage
from utils.logger import setup_logger
from utils.inline_cleanup import InlineMessageManager
from config import ZAYAVKA_GROUP_ID
from utils.role_dispatcher import RoleAwareDispatcher, set_global_role_dispatcher
from database.base_queries import DatabaseManager

# Load environment variables
load_dotenv()

# Setup logger (nomi: bot, darajasi: INFO)
logger = setup_logger("bot")

# Initialize bot
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Initialize dispatcher
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
role_dispatcher = RoleAwareDispatcher(dp)
set_global_role_dispatcher(role_dispatcher)

# Initialize inline message manager
inline_message_manager = InlineMessageManager(bot)

# Initialize database manager va pool
bot.db_manager = DatabaseManager()
bot.db = None  # Pool obyektini saqlash uchun

async def create_db_pool():
    """Create and initialize database connection pool, set bot.db"""
    try:
        await bot.db_manager.init_pool()
        bot.db = bot.db_manager.get_pool()
        # Test connection
        async with bot.db.acquire() as conn:
            await conn.fetchval('SELECT 1')
        logger.info("Database connection pool created successfully")
        return bot.db
    except Exception as e:
        logger.error(f"Error creating database pool: {str(e)}", exc_info=True)
        raise

async def initialize_database():
    """Initialize database with required tables if needed (migration)"""
    pool = bot.db
    try:
        async with pool.acquire() as conn:
            # Check if tables exist
            tables_exist = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """)
            if not tables_exist:
                logger.info("Database tables not found, creating...")
                try:
                    with open('database/migrations/010_final_schema_update.sql', 'r', encoding='utf-8') as f:
                        migration_sql = f.read()
                    await conn.execute(migration_sql)
                    logger.info("Database tables created successfully")
                except FileNotFoundError:
                    logger.warning("Migration file not found, creating basic tables...")
                    await create_basic_tables(conn)
            else:
                logger.info("Database tables already exist")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        raise

async def create_basic_tables(conn):
    """Create basic tables if migration file is not available"""
    basic_schema = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        full_name TEXT,
        username TEXT,
        phone_number TEXT,
        role VARCHAR(20) NOT NULL DEFAULT 'client',
        language VARCHAR(2) NOT NULL DEFAULT 'uz',
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    -- Materials table
    CREATE TABLE IF NOT EXISTS materials (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        quantity INTEGER NOT NULL DEFAULT 0,
        unit VARCHAR(10) NOT NULL DEFAULT 'pcs',
        min_quantity INTEGER NOT NULL DEFAULT 5,
        price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    -- Zayavki table
    CREATE TABLE IF NOT EXISTS zayavki (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        description TEXT NOT NULL,
        address TEXT,
        media TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'new',
        assigned_to INTEGER REFERENCES users(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    -- Feedback table
    CREATE TABLE IF NOT EXISTS feedback (
        id SERIAL PRIMARY KEY,
        zayavka_id INTEGER REFERENCES zayavki(id),
        user_id INTEGER NOT NULL REFERENCES users(id),
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    -- Status logs table
    CREATE TABLE IF NOT EXISTS status_logs (
        id SERIAL PRIMARY KEY,
        zayavka_id INTEGER NOT NULL REFERENCES zayavki(id),
        old_status VARCHAR(20) NOT NULL,
        new_status VARCHAR(20) NOT NULL,
        changed_by INTEGER NOT NULL REFERENCES users(id),
        changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    -- Solutions table
    CREATE TABLE IF NOT EXISTS solutions (
        id SERIAL PRIMARY KEY,
        zayavka_id INTEGER NOT NULL REFERENCES zayavki(id),
        instander_id INTEGER NOT NULL REFERENCES users(id),
        solution_text TEXT NOT NULL,
        media TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    -- Create basic indexes
    CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
    CREATE INDEX IF NOT EXISTS idx_zayavki_user_id ON zayavki(user_id);
    CREATE INDEX IF NOT EXISTS idx_zayavki_status ON zayavki(status);
    """
    await conn.execute(basic_schema)
    logger.info("Basic database schema created")

async def on_startup():
    """Startup handler"""
    try:
        logger.info("Starting bot...")
        
        # Initialize database pool
        pool = await create_db_pool()
        bot.pool = pool
        
        # Initialize database tables
        await initialize_database()
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"Bot started successfully: @{bot_info.username}")
        
        # Notify admins
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id, 
                    "Бот запущен и готов к работе!"
                )
            except Exception as e:
                logger.warning(f"Failed to notify admin {admin_id}: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise

async def on_shutdown():
    try:
        logger.info("Bot shutdown initiated...")
        if inline_message_manager:
            await inline_message_manager.stop_auto_cleanup()
        if hasattr(bot, 'pool') and bot.pool:
            await bot.pool.close()
            logger.info("Database pool closed")
        if 'cache' in globals() and cache:
            await cache.close()
            logger.info("Cache closed")
        logger.info("Bot shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


__all__ = ['bot', 'dp', 'inline_message_manager', 'db', 'cache', 'ZAYAVKA_GROUP_ID']