import asyncio
import os
from dotenv import load_dotenv
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database.queries import create_tables, set_pool, add_missing_columns
from handlers.main import router as main_router
from handlers.language import router as language_router
from config import config
from utils.logger import setup_logger, logger
from loader import bot, create_db_pool
from utils import global_navigation
import signal
import sys
import logging

# Load environment variables
load_dotenv()

# Validate configuration
try:
    config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)

# Setup logger
setup_logger(level=getattr(logging, config.LOG_LEVEL.upper()))

# Dispatcher with memory storage
dp = Dispatcher(storage=MemoryStorage())

# Include routers - language router should be first to handle language changes
dp.include_router(language_router)  # Til o'zgartirish uchun birinchi bo'lib qo'shamiz

# Include main router which includes all other routers
dp.include_router(main_router)

# Include global navigation router for handling back buttons
dp.include_router(global_navigation.router)

async def on_startup():
    """Enhanced bot startup handler"""
    try:
        logger.info("Starting bot initialization...")
        # Create database pool with configuration
        pool = await create_db_pool()
        set_pool(pool)
        bot.pool = pool
        # Initialize database
        await create_tables(pool)
        await add_missing_columns(pool)
        # Test database connection
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}", exc_info=True)
        raise

async def on_shutdown():
    """Enhanced bot shutdown handler"""
    try:
        logger.info("Shutting down bot...")
        if hasattr(bot, 'pool') and bot.pool:
            await bot.pool.close()
            logger.info("Database connection pool closed")
        logger.info("Bot shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)

def signal_handler(signum, frame):
    """Handle system signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    try:
        logger.info("Starting bot polling...")
        dp.run_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {str(e)}", exc_info=True)
    finally:
        logger.info("Bot polling stopped")
