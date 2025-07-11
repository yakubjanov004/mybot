from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.base_queries import get_user_lang
from utils.logger import setup_logger
from utils.role_router import get_role_router

logger = setup_logger('bot.manager.orders')

def get_manager_orders_router():
    router = get_role_router("manager")
    
    @router.message(F.text.in_(["📊 Hisobot yaratish", "📊 Создать отчет"]))
    async def manager_create_report(message: Message):
        """Manager create report"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "📊 Manager: Hisobot yaratish oynasi" if lang == 'uz' else "📊 Менеджер: Окно создания отчета"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_create_report: {e}")

    @router.message(F.text.in_(["📦 Jihozlar berish", "📦 Выдача оборудования"]))
    async def manager_give_equipment(message: Message):
        """Manager give equipment"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "📦 Manager: Jihozlar berish oynasi" if lang == 'uz' else "📦 Менеджер: Окно выдачи оборудования"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_give_equipment: {e}")

    @router.message(F.text.in_(["✅ O'rnatishga tayyor", "✅ Готов к установке"]))
    async def manager_ready_for_installation(message: Message):
        """Manager ready for installation"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "✅ Manager: O'rnatishga tayyor arizalar" if lang == 'uz' else "✅ Менеджер: Заявки готовые к установке"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_ready_for_installation: {e}")

    @router.message(F.text.in_(["🌐 Tilni o'zgartirish", "🌐 Изменить язык"]))
    async def manager_change_language(message: Message):
        """Manager change language"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "🌐 Manager: Tilni o'zgartirish" if lang == 'uz' else "🌐 Менеджер: Изменить язык"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_change_language: {e}")

    return router
