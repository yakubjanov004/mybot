import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

from config import config
from loader import bot, inline_message_manager
from utils.logger import setup_logging
from utils.cache_manager import cache_maintenance
from utils.rate_limiter import cleanup_expired_limits
from middlewares.logger_middleware import LoggerMiddleware
from middlewares.error_handler import ErrorHandlerMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Logda aiohttp va asyncio xatolarini yashirish
logging.getLogger("aiohttp.client").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp.connector").setLevel(logging.CRITICAL)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

async def on_startup(dp: Dispatcher):
    """Bot startup handler"""
    try:
        logger.info("Starting bot...")
        
        # Initialize database pool with proper parameters
        import asyncpg
        try:
            # Validate database URL
            if not config.DATABASE_URL:
                raise ValueError("DATABASE_URL is not set in environment variables")
            
            # Parse the database URL
            from urllib.parse import urlparse
            parsed_url = urlparse(config.DATABASE_URL)
            
            if not parsed_url.scheme.startswith('postgres'):
                raise ValueError(f"Invalid database URL scheme: {parsed_url.scheme}")
            
            # Create connection pool with retry logic
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Add more detailed connection parameters for diagnostics
                    bot.db = await asyncpg.create_pool(
                        config.DATABASE_URL,
                        min_size=1,
                        max_size=10,
                        timeout=30,
                        command_timeout=30,
                        max_inactive_connection_lifetime=300,  # 5 minutes
                        statement_cache_size=1000,
                        max_cached_statement_lifetime=300,  # 5 minutes
                        max_cacheable_statement_size=100000  # 100KB
                    )
                    
                    # Test the connection
                    async with bot.db.acquire() as conn:
                        await conn.execute("SELECT 1")
                    
                    logger.info("Database connection pool initialized successfully")
                    break
                except asyncpg.exceptions.InterfaceError as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                        logger.error(f"Database URL: {config.DATABASE_URL}")
                        raise
                    logger.warning(f"Database connection failed, retrying in {retry_delay} seconds... ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                except asyncpg.exceptions.PostgresError as e:
                    logger.error(f"Postgres error: {str(e)}")
                    logger.error(f"Postgres error code: {e.sqlstate}")
                    raise
                except Exception as e:
                    logger.error(f"Database connection failed: {str(e)}")
                    logger.error(f"Type of error: {type(e).__name__}")
                    logger.error(f"Full error details: {str(e)}")
                    raise
        except ValueError as e:
            logger.error(f"Configuration error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
        
        # Initialize inline cleanup
        inline_message_manager.start_auto_cleanup()
        
        # Start background tasks
        asyncio.create_task(cache_maintenance())
        asyncio.create_task(cleanup_expired_limits())
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"Bot started successfully: @{bot_info.username}")
        
        # Notify admins
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"Bot started successfully.\n\n"
                    f"Bot Info:\n"
                    f"- Username: @{bot_info.username}\n"
                    f"- ID: {bot_info.id}\n"
                    f"- First Name: {bot_info.first_name}\n"
                    f"- Can Join Groups: {bot_info.can_join_groups}\n"
                    f"- Can Read All Group Messages: {bot_info.can_read_all_group_messages}\n"
                    f"- Supports Inline Queries: {bot_info.supports_inline_queries}"
                )
            except Exception as e:
                logger.warning(f"Failed to notify admin {admin_id}: {str(e)}")
        
        # Register handlers
        from handlers import setup_handlers
        setup_handlers(dp)
        
        # Setup middlewares
        setup_middlewares(dp)
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

async def on_shutdown(dp: Dispatcher):
    """Bot shutdown handler"""
    try:
        # Close database connection pool
        if hasattr(bot, 'db'):
            await bot.db.close()
            logger.info("Database connection pool closed successfully")
        
        # Notify admins
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id, 
                    "Bot stopped for maintenance"
                )
            except Exception as e:
                logger.warning(f"Failed to notify admin {admin_id}: {str(e)}")
        
        # Stop inline cleanup
        await inline_message_manager.stop_auto_cleanup()
        
        # --- Bot sessiyasini to‘g‘ri yopish ---
        try:
            await bot.session.close()
        except Exception as e:
            logger.warning(f"Bot session close error: {e}")
        # -------------------------------------
        
        logger.info("Bot shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

def setup_middlewares(dp: Dispatcher):
    # Register global middlewares for messages
    dp.message.middleware(LoggerMiddleware())
    dp.message.middleware(ErrorHandlerMiddleware())
    # Register global middlewares for callback queries
    dp.callback_query.middleware(LoggerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())

async def main():
    """Main function"""
    try:
        # Create dispatcher
        dp = Dispatcher(storage=MemoryStorage())
        
        # Register startup and shutdown handlers
        from functools import partial
        dp.startup.register(partial(on_startup, dp))
        dp.shutdown.register(partial(on_shutdown, dp))
        
        # Setup middlewares
        setup_middlewares(dp)
        
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
    finally:
        await on_shutdown(dp)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        sys.exit(1)
