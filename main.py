import asyncio
import sys
from aiogram import Dispatcher
from config import config
from loader import bot, dp, inline_message_manager, create_db_pool, initialize_database, on_startup, on_shutdown
from utils.logger import setup_logger
from utils.cache_manager import cache_maintenance
from utils.rate_limiter import cleanup_expired_limits
from middlewares.logger_middleware import LoggerMiddleware
from middlewares.error_handler import ErrorHandlerMiddleware
from middlewares.enhanced_role_filter import EnhancedRoleFilterMiddleware

# Yagona logger (bot, INFO)
logger = setup_logger("bot")

# Logda aiohttp va asyncio xatolarini yashirish
import logging
logging.getLogger("aiohttp.client").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp.connector").setLevel(logging.CRITICAL)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

def setup_middlewares(dp: Dispatcher):
    dp.message.middleware(LoggerMiddleware())
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.message.middleware(EnhancedRoleFilterMiddleware())
    dp.callback_query.middleware(LoggerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(EnhancedRoleFilterMiddleware())

def setup_handlers(dp: Dispatcher):
    from handlers import setup_handlers as _setup_handlers
    _setup_handlers(dp)

def main():
    try:
        # Startup va shutdown handlerlarini ro'yxatdan o'tkazish
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        # Handlers va middlewares
        setup_handlers(dp)
        setup_middlewares(dp)
        # Polling
        asyncio.run(dp.start_polling(bot))
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
