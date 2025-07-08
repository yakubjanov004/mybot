from aiogram import F
from aiogram.types import Message
from database.base_queries import get_user_lang
from utils.logger import setup_logger
from utils.role_router import get_role_router

logger = setup_logger('bot.manager.statistics')

def get_manager_statistics_router():
    router = get_role_router("manager")
    
    @router.message(F.text.in_(["📈 Umumiy statistika", "📈 Общая статистика"]))
    async def manager_general_stats(message: Message):
        """Manager general statistics"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "📈 Manager: Umumiy statistika paneli" if lang == 'uz' else "📈 Менеджер: Панель общей статистики"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_general_stats: {e}")
    
    @router.message(F.text.in_(["👨‍🔧 Texnik statistikasi", "👨‍🔧 Статистика техников"]))
    async def manager_technician_stats(message: Message):
        """Manager technician statistics"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "👨‍🔧 Manager: Texniklar statistikasi" if lang == 'uz' else "👨‍🔧 Менеджер: Статистика техников"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_technician_stats: {e}")
    
    @router.message(F.text.in_(["📊 Ariza statistikasi", "📊 Статистика заявок"]))
    async def manager_order_stats(message: Message):
        """Manager order statistics"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "📊 Manager: Arizalar bo'yicha statistika" if lang == 'uz' else "📊 Менеджер: Статистика по заявкам"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_order_stats: {e}")
    
    @router.message(F.text.in_(["📋 Hisobot yaratish", "📋 Создать отчет"]))
    async def manager_create_report(message: Message):
        """Manager create report"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "📋 Manager: Hisobot yaratish vositasi" if lang == 'uz' else "📋 Менеджер: Инструмент создания отчетов"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_create_report: {e}")
    
    return router
