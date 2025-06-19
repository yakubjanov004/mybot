import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from database.queries import create_tables, set_pool, add_missing_columns
from handlers.main import router as main_router
from config import BOT_TOKEN, ADMIN_IDS, ZAYAVKA_GROUP_ID
from utils.logger import setup_logger, logger
from loader import bot, create_db_pool
import asyncpg

# Load environment variables
load_dotenv()
setup_logger()

# Bot instance
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# Dispatcher
dp = Dispatcher(storage=MemoryStorage())

# Include main router which includes all other routers
dp.include_router(main_router)

async def on_startup():
    """Bot startup handler"""
    try:
        # Create database pool
        pool = await create_db_pool()
        set_pool(pool)
        
        # Create tables and add missing columns
        await create_tables(pool)
        await add_missing_columns()
        
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        raise

async def on_shutdown():
    """Bot shutdown handler"""
    try:
        if hasattr(bot, 'pool') and bot.pool:
            await bot.pool.close()
            logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.run_polling(bot)