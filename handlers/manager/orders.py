from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.base_queries import get_user_lang
from utils.logger import setup_logger
from utils.role_router import get_role_router

logger = setup_logger('bot.manager.orders')

def get_manager_orders_router():
    router = get_role_router("manager")
    
    @router.message(F.text.in_(["📝 Ariza yaratish", "📝 Создать заявку"]))
    async def manager_create_order(message: Message):
        """Manager create order"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "📝 Manager: Ariza yaratish oynasi" if lang == 'uz' else "📝 Менеджер: Окно создания заявки"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_create_order: {e}")

    @router.message(F.text.in_(["📋 Arizalarni ko'rish", "📋 Просмотр заявок"]))
    async def manager_orders_list(message: Message):
        """Manager orders list"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "📋 Manager: Mening arizalarim ro'yxati" if lang == 'uz' else "📋 Менеджер: Список моих заявок"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_orders_list: {e}")


    @router.message(F.text.in_(["🔄 Status o'zgartirish", "🔄 Изменить статус"]))
    async def manager_change_status(message: Message):
        """Manager change order status"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "🔄 Manager: Ariza statusini o'zgartirish" if lang == 'uz' else "🔄 Менеджер: Изменение статуса заявки"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_change_status: {e}")

    @router.message(F.text.in_(["👨‍🔧 Texnik biriktirish", "👨‍🔧 Назначить техника"]))
    async def manager_assign_technician(message: Message):
        """Manager assign technician"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "👨‍🔧 Manager: Texnik biriktirish oynasi" if lang == 'uz' else "👨‍🔧 Менеджер: Окно назначения техника"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_assign_technician: {e}")

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

    @router.message(F.text.in_(["👥 Xodimlar faoliyati", "👥 Активность сотрудников"]))
    async def manager_staff_activity(message: Message):
        """Manager staff activity"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "👥 Manager: Xodimlar faoliyati oynasi" if lang == 'uz' else "👥 Менеджер: Окно активности сотрудников"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_staff_activity: {e}")

    @router.message(F.text.in_(["🔔 Bildirishnomalar", "🔔 Уведомления"]))
    async def manager_notifications(message: Message):
        """Manager notifications"""
        try:
            lang = await get_user_lang(message.from_user.id)
            text = "🔔 Manager: Bildirishnomalar oynasi" if lang == 'uz' else "🔔 Менеджер: Окно уведомлений"
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error in manager_notifications: {e}")

    return router
