from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import get_call_center_stats, get_operator_performance
from keyboards.call_center_buttons import call_center_detailed_statistics_menu
from states.call_center import CallCenterStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_call_center_statistics_router():
    router = get_role_router("call_center")

    @router.message(F.text.in_(["📊 Statistika", "📊 Статистика"]))
    async def call_center_statistics_handler(message: Message, state: FSMContext):
        """Handle call center statistics"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        lang = user.get('language', 'uz')
        stats_text = "📊 Statistika bo'limi" if lang == 'uz' else "📊 Раздел статистики"
        await message.answer(
            stats_text,
            reply_markup=call_center_detailed_statistics_menu(lang)
        )

    @router.callback_query(F.data == "call_statistics")
    async def call_statistics_menu(callback: CallbackQuery, state: FSMContext):
        """Show call center statistics menu"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        stats_text = "📊 Statistika bo'limi" if lang == 'uz' else "📊 Раздел статистики"
        await callback.message.edit_text(
            stats_text,
            reply_markup=call_center_detailed_statistics_menu(lang)
        )

    @router.callback_query(F.data.startswith("cc_stats_"))
    async def handle_call_center_statistics(callback: CallbackQuery, state: FSMContext):
        """Handle call center statistics requests"""
        stats_type = callback.data.split("_")[2]
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        try:
            if stats_type == "daily":
                stats = await get_call_center_stats(user['id'], period='daily')
                title = "📅 Bugungi ko'rsatkichlar" if lang == 'uz' else "📅 Сегодняшние показатели"
            elif stats_type == "weekly":
                stats = await get_call_center_stats(user['id'], period='weekly')
                title = "📊 Haftalik hisobot" if lang == 'uz' else "📊 Недельный отчет"
            elif stats_type == "monthly":
                stats = await get_call_center_stats(user['id'], period='monthly')
                title = "📈 Oylik hisobot" if lang == 'uz' else "📈 Месячный отчет"
            elif stats_type == "performance":
                stats = await get_operator_performance(user['id'], period='monthly')
                title = "🎯 Mening samaradorligim" if lang == 'uz' else "🎯 Моя эффективность"
            elif stats_type == "conversion":
                stats = await get_call_center_stats(user['id'], period='conversion')
                title = "📈 Konversiya darajasi" if lang == 'uz' else "📈 Коэффициент конверсии"
            
            # Format statistics text
            calls_text = "Qo'ng'iroqlar" if lang == 'uz' else "Звонки"
            orders_text = "Buyurtmalar" if lang == 'uz' else "Заказы"
            conversion_text = "Konversiya" if lang == 'uz' else "Конверсия"
            avg_time_text = "O'rtacha vaqt" if lang == 'uz' else "Среднее время"
            success_rate_text = "Muvaffaqiyat darajasi" if lang == 'uz' else "Процент успеха"
            
            text = f"{title}\n\n"
            text += f"📞 {calls_text}: {stats.get('calls', 0)}\n"
            text += f"📋 {orders_text}: {stats.get('orders', 0)}\n"
            text += f"🎯 {conversion_text}: {stats.get('conversion_rate', 0)}%\n"
            text += f"⏱️ {avg_time_text}: {stats.get('avg_call_time', 0)} daqiqa\n"
            text += f"✅ {success_rate_text}: {stats.get('success_rate', 0)}%\n"
            
            if stats_type == "performance":
                rating_text = "Reyting" if lang == 'uz' else "Рейтинг"
                feedback_text = "Fikr-mulohazalar" if lang == 'uz' else "Отзывы"
                text += f"⭐ {rating_text}: {stats.get('rating', 0)}/5\n"
                text += f"💬 {feedback_text}: {stats.get('feedback_count', 0)}\n"
            
            await callback.message.edit_text(text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in call center statistics: {str(e)}")
            error_text = "Statistikani olishda xatolik yuz berdi" if lang == 'uz' else "Ошибка при получении статистики"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data.startswith("stats_"))
    async def handle_statistics_requests(callback: CallbackQuery, state: FSMContext):
        """Handle different statistics requests (legacy support)"""
        stats_type = callback.data.split("_")[1]
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        try:
            if stats_type == "daily":
                stats = await get_call_center_stats(user['id'], period='daily')
                title = "Bugungi ko'rsatkichlar" if lang == 'uz' else "Сегодняшние показатели"
            elif stats_type == "weekly":
                stats = await get_call_center_stats(user['id'], period='weekly')
                title = "Haftalik hisobot" if lang == 'uz' else "Недельный отчет"
            elif stats_type == "monthly":
                stats = await get_call_center_stats(user['id'], period='monthly')
                title = "Oylik hisobot" if lang == 'uz' else "Месячный отчет"
            elif stats_type == "performance":
                stats = await get_call_center_stats(user['id'], period='performance')
                title = "Mening samaradorligim" if lang == 'uz' else "Моя эффективность"
            
            # Format statistics text
            calls_text = "Qo'ng'iroqlar" if lang == 'uz' else "Звонки"
            orders_text = "Buyurtmalar" if lang == 'uz' else "Заказы"
            conversion_text = "Konversiya" if lang == 'uz' else "Конверсия"
            
            text = f"📊 {title}\n\n"
            text += f"📞 {calls_text}: {stats.get('calls', 0)}\n"
            text += f"📋 {orders_text}: {stats.get('orders', 0)}\n"
            text += f"🎯 {conversion_text}: {stats.get('conversion_rate', 0)}%\n"
            
            await callback.message.edit_text(text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in statistics: {str(e)}")
            error_text = "Statistikani olishda xatolik yuz berdi" if lang == 'uz' else "Ошибка при получении статистики"
            await callback.message.edit_text(error_text)
            await callback.answer()

    return router
