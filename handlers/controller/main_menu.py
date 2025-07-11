from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from filters.role_filter import RoleFilter
from utils.role_router import get_role_router
from database.base_queries import get_user_by_telegram_id, get_system_statistics
from keyboards.controllers_buttons import controllers_main_menu
from states.controllers_states import ControllerMainMenuStates
from utils.logger import logger

def get_controller_main_menu_router():
    router = get_role_router("controller")

    @router.message(F.text.in_(["🎛️ Controller", "🎛️ Контроллер", "🎛️ Nazoratchi"]))
    async def controllers_start(message: Message, state: FSMContext):
        """Controllers panel asosiy menyu"""
        await state.clear()
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        await state.set_state(ControllerMainMenuStates.main_menu)
        lang = user.get('language', 'uz')
        stats = await get_system_statistics()
        if lang == 'uz':
            welcome_text = (
                "🎛️ <b>Nazoratchi paneli</b>\n\n"
                "📊 <b>Tizim holati:</b>\n"
                f"• Jami buyurtmalar: {stats.get('total_orders', 0)}\n"
                f"• Bajarilgan: {stats.get('completed_orders', 0)}\n"
                f"• Kutilayotgan: {stats.get('pending_orders', 0)}\n"
                f"• Faol mijozlar: {stats.get('active_clients', 0)}\n"
                f"• Faol texniklar: {stats.get('active_technicians', 0)}\n\n"
                "Kerakli bo'limni tanlang:"
            )
        else:
            welcome_text = (
                "🎛️ <b>Панель контроллера</b>\n\n"
                "📊 <b>Состояние системы:</b>\n"
                f"• Всего заказов: {stats.get('total_orders', 0)}\n"
                f"• Завершено: {stats.get('completed_orders', 0)}\n"
                f"• Ожидает: {stats.get('pending_orders', 0)}\n"
                f"• Активные клиенты: {stats.get('active_clients', 0)}\n"
                f"• Активные техники: {stats.get('active_technicians', 0)}\n\n"
                "Выберите нужный раздел:"
            )
        await message.answer(
            welcome_text,
            reply_markup=controllers_main_menu(lang),
            parse_mode='HTML'
        )

    @router.message(F.text.in_(["🏠 Bosh menyu", "🏠 Главное меню"]))
    async def back_to_main_menu(message: Message, state: FSMContext):
        """Bosh menyuga qaytish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        await controllers_start(message, state)

    @router.message(F.text.in_(["📊 Statistika", "📊 Статистика"]))
    async def show_statistics(message: Message, state: FSMContext):
        """Tizim statistikasini ko'rsatish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        lang = user.get('language', 'uz')
        stats = await get_system_statistics()
        try:
            if lang == 'uz':
                text = (
                    "📊 <b>Tizim statistikasi</b>\n"
                    "📈 <b>Buyurtmalar:</b>\n"
                    f"• Jami: {stats.get('total_orders', 0)}\n"
                    f"• Bajarilgan: {stats.get('completed_orders', 0)}\n"
                    f"• Kutilayotgan: {stats.get('pending_orders', 0)}\n\n"
                    "👥 <b>Foydalanuvchilar:</b>\n"
                    f"• Faol mijozlar: {stats.get('active_clients', 0)}\n"
                    f"• Faol texniklar: {stats.get('active_technicians', 0)}\n\n"
                    "💰 <b>Moliyaviy:</b>\n"
                    f"• Bugungi tushum: {stats.get('revenue_today', 0):,} so'm\n"
                    f"• O'rtacha bajarish vaqti: {stats.get('avg_completion_time', 0)} soat"
                )
            else:
                text = (
                    "📊 <b>Статистика системы</b>\n\n"
                    "📈 <b>Заказы:</b>\n"
                    f"• Всего: {stats.get('total_orders', 0)}\n"
                    f"• Завершено: {stats.get('completed_orders', 0)}\n"
                    f"• Ожидает: {stats.get('pending_orders', 0)}\n\n"
                    "👥 <b>Пользователи:</b>\n"
                    f"• Активные клиенты: {stats.get('active_clients', 0)}\n"
                    f"• Активные техники: {stats.get('active_technicians', 0)}\n\n"
                    "💰 <b>Финансы:</b>\n"
                    f"• Доход сегодня: {stats.get('revenue_today', 0):,} сум\n"
                    f"• Среднее время выполнения: {stats.get('avg_completion_time', 0)} ч"
                )
            await message.answer(text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error showing statistics: {e}")
            error_text = "Statistikani olishda xatolik yuz berdi" if lang == 'uz' else "Ошибка при получении статистики"
            await message.answer(error_text)

    return router
