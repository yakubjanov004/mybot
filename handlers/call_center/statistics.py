from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.call_center_queries import get_statistics
from database.base_queries import get_user_by_telegram_id
from keyboards.call_center_buttons import call_center_statistics_menu, call_center_main_menu_reply
from states.call_center import CallCenterStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_call_center_statistics_router():
    router = get_role_router('call_center')

    @router.message(F.text == "📊 Statistikalar")
    async def handle_statistics(message: Message, state: FSMContext):
        """Handle statistics menu"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return

        lang = user.get('language', 'uz')
        await message.answer(
            "📊 Statistikalar menyu",
            reply_markup=call_center_statistics_menu(lang)
        )
        await state.set_state(CallCenterStates.statistics)

    @router.message(CallCenterStates.statistics, F.text == "📅 Bugungi ko'rsatkichlar")
    async def handle_daily_stats(message: Message, state: FSMContext):
        """Handle daily statistics"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizда ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return

        lang = user.get('language', 'uz')
        stats = await get_statistics('daily')
        
        if lang == 'uz':
            text = (
                "📊 Bugungi statistikalar\n\n"
                f"✅ Jarayondagi zayavkalar: {stats['active_orders']}\n"
                f"✅ Bajarilgan zayavkalar: {stats['completed_orders']}\n"
                f"✅ Bekor qilingan zayavkalar: {stats['cancelled_orders']}\n\n"
                f"📞 Qabul qilingan qo'ng'iroqlar: {stats['total_calls']}\n"
                f"📞 Qo'ng'iroqlar davri: {stats['avg_call_duration']}\n\n"
                f"🎯 Konversiya darajasi: {stats['conversion_rate']}%\n"
                f"🎯 Maksimal konversiya: {stats['max_conversion']}%\n"
                f"🎯 Minimal konversiya: {stats['min_conversion']}%\n\n"
                f"📊 Umumiy reyting: {stats['rating']}\n"
                f"📊 Maksimal reyting: {stats['max_rating']}\n"
                f"📊 Minimal reyting: {stats['min_rating']}"
            )
        else:
            text = (
                "📊 Статистика за сегодня\n\n"
                f"✅ Активные заявки: {stats['active_orders']}\n"
                f"✅ Выполненные заявки: {stats['completed_orders']}\n"
                f"✅ Отмененные заявки: {stats['cancelled_orders']}\n\n"
                f"📞 Принятые звонки: {stats['total_calls']}\n"
                f"📞 Длительность звонков: {stats['avg_call_duration']}\n\n"
                f"🎯 Коэффициент конверсии: {stats['conversion_rate']}%\n"
                f"🎯 Максимальный коэффициент: {stats['max_conversion']}%\n"
                f"🎯 Минимальный коэффициент: {stats['min_conversion']}%\n\n"
                f"📊 Общий рейтинг: {stats['rating']}\n"
                f"📊 Максимальный рейтинг: {stats['max_rating']}\n"
                f"📊 Минимальный рейтинг: {stats['min_rating']}"
            )

        await message.answer(
            text,
            reply_markup=call_center_statistics_menu(lang)
        )

    @router.message(CallCenterStates.statistics, F.text == "📊 Haftalik hisobot")
    async def handle_weekly_stats(message: Message, state: FSMContext):
        """Handle weekly statistics"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizда ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return

        lang = user.get('language', 'uz')
        stats = await get_statistics('weekly')
        
        if lang == 'uz':
            text = (
                "📊 Haftalik statistikalar\n\n"
                f"✅ Jarayondagi zayavkalar: {stats['active_orders']}\n"
                f"✅ Bajarilgan zayavkalar: {stats['completed_orders']}\n"
                f"✅ Bekor qilingan zayavkalar: {stats['cancelled_orders']}\n\n"
                f"📞 Qabul qilingan qo'ng'iroqlar: {stats['total_calls']}\n"
                f"📞 Qo'ng'iroqlar davri: {stats['avg_call_duration']}\n\n"
                f"🎯 Konversiya darajasi: {stats['conversion_rate']}%\n"
                f"🎯 Maksimal konversiya: {stats['max_conversion']}%\n"
                f"🎯 Minimal konversiya: {stats['min_conversion']}%\n\n"
                f"📊 Umumiy reyting: {stats['rating']}\n"
                f"📊 Maksimal reyting: {stats['max_rating']}\n"
                f"📊 Minimal reyting: {stats['min_rating']}"
            )
        else:
            text = (
                "📊 Статистика за неделю\n\n"
                f"✅ Активные заявки: {stats['active_orders']}\n"
                f"✅ Выполненные заявки: {stats['completed_orders']}\n"
                f"✅ Отмененные заявки: {stats['cancelled_orders']}\n\n"
                f"📞 Принятые звонки: {stats['total_calls']}\n"
                f"📞 Длительность звонков: {stats['avg_call_duration']}\n\n"
                f"🎯 Коэффициент конверсии: {stats['conversion_rate']}%\n"
                f"🎯 Максимальный коэффициент: {stats['max_conversion']}%\n"
                f"🎯 Минимальный коэффициент: {stats['min_conversion']}%\n\n"
                f"📊 Общий рейтинг: {stats['rating']}\n"
                f"📊 Максимальный рейтинг: {stats['max_rating']}\n"
                f"📊 Минимальный рейтинг: {stats['min_rating']}"
            )

        await message.answer(
            text,
            reply_markup=call_center_statistics_menu(lang)
        )

    @router.message(CallCenterStates.statistics, F.text == "📈 Oylik hisobot")
    async def handle_monthly_stats(message: Message, state: FSMContext):
        """Handle monthly statistics"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizда ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return

        lang = user.get('language', 'uz')
        stats = await get_statistics('monthly')
        
        if lang == 'uz':
            text = (
                "📊 Oylik statistikalar\n\n"
                f"✅ Jarayondagi zayavkalar: {stats['active_orders']}\n"
                f"✅ Bajarilgan zayavkalar: {stats['completed_orders']}\n"
                f"✅ Bekor qilingan zayavkalar: {stats['cancelled_orders']}\n\n"
                f"📞 Qabul qilingan qo'ng'iroqlar: {stats['total_calls']}\n"
                f"📞 Qo'ng'iroqlar davri: {stats['avg_call_duration']}\n\n"
                f"🎯 Konversiya darajasi: {stats['conversion_rate']}%\n"
                f"🎯 Maksimal konversiya: {stats['max_conversion']}%\n"
                f"🎯 Minimal konversiya: {stats['min_conversion']}%\n\n"
                f"📊 Umumiy reyting: {stats['rating']}\n"
                f"📊 Maksimal reyting: {stats['max_rating']}\n"
                f"📊 Minimal reyting: {stats['min_rating']}"
            )
        else:
            text = (
                "📊 Статистика за месяц\n\n"
                f"✅ Активные заявки: {stats['active_orders']}\n"
                f"✅ Выполненные заявки: {stats['completed_orders']}\n"
                f"✅ Отмененные заявки: {stats['cancelled_orders']}\n\n"
                f"📞 Принятые звонки: {stats['total_calls']}\n"
                f"📞 Длительность звонков: {stats['avg_call_duration']}\n\n"
                f"🎯 Коэффициент конверсии: {stats['conversion_rate']}%\n"
                f"🎯 Максимальный коэффициент: {stats['max_conversion']}%\n"
                f"🎯 Минимальный коэффициент: {stats['min_conversion']}%\n\n"
                f"📊 Общий рейтинг: {stats['rating']}\n"
                f"📊 Максимальный рейтинг: {stats['max_rating']}\n"
                f"📊 Минимальный рейтинг: {stats['min_rating']}"
            )

        await message.answer(
            text,
            reply_markup=call_center_statistics_menu(lang)
        )

    @router.message(CallCenterStates.statistics, F.text == "🎯 Mening samaradorligim")
    async def handle_performance(message: Message, state: FSMContext):
        """Handle personal performance statistics"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizда ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return

        lang = user.get('language', 'uz')
        stats = await get_statistics('performance', user_id=user['id'])
        
        if lang == 'uz':
            text = (
                "🎯 Mening samaradorligim\n\n"
                f"✅ Jarayondagi zayavkalar: {stats['active_orders']}\n"
                f"✅ Bajarilgan zayavkalar: {stats['completed_orders']}\n"
                f"✅ Bekor qilingan zayavkalar: {stats['cancelled_orders']}\n\n"
                f"📞 Qabul qilingan qo'ng'iroqlar: {stats['total_calls']}\n"
                f"📞 Qo'ng'iroqlar davri: {stats['avg_call_duration']}\n\n"
                f"🎯 Konversiya darajasi: {stats['conversion_rate']}%\n"
                f"🎯 Maksimal konversiya: {stats['max_conversion']}%\n"
                f"🎯 Minimal konversiya: {stats['min_conversion']}%\n\n"
                f"📊 Umumiy reyting: {stats['rating']}\n"
                f"📊 Maksimal reyting: {stats['max_rating']}\n"
                f"📊 Minimal reyting: {stats['min_rating']}"
            )
        else:
            text = (
                "🎯 Моя эффективность\n\n"
                f"✅ Активные заявки: {stats['active_orders']}\n"
                f"✅ Выполненные заявки: {stats['completed_orders']}\n"
                f"✅ Отмененные заявки: {stats['cancelled_orders']}\n\n"
                f"📞 Принятые звонки: {stats['total_calls']}\n"
                f"📞 Длительность звонков: {stats['avg_call_duration']}\n\n"
                f"🎯 Коэффициент конверсии: {stats['conversion_rate']}%\n"
                f"🎯 Максимальный коэффициент: {stats['max_conversion']}%\n"
                f"🎯 Минимальный коэффициент: {stats['min_conversion']}%\n\n"
                f"📊 Общий рейтинг: {stats['rating']}\n"
                f"📊 Максимальный рейтинг: {stats['max_rating']}\n"
                f"📊 Минимальный рейтинг: {stats['min_rating']}"
            )

        await message.answer(
            text,
            reply_markup=call_center_statistics_menu(lang)
        )

    @router.message(CallCenterStates.statistics, F.text == "📈 Konversiya darajasi")
    async def handle_conversion(message: Message, state: FSMContext):
        """Handle conversion statistics"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizда ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return

        lang = user.get('language', 'uz')
        stats = await get_statistics('conversion')
        
        if lang == 'uz':
            text = (
                "📈 Konversiya darajasi\n\n"
                f"🎯 Umumiy konversiya: {stats['conversion_rate']}%\n"
                f"🎯 Maksimal konversiya: {stats['max_conversion']}%\n"
                f"🎯 Minimal konversiya: {stats['min_conversion']}%\n\n"
                f"📊 Umumiy reyting: {stats['rating']}\n"
                f"📊 Maksimal reyting: {stats['max_rating']}\n"
                f"📊 Minimal reyting: {stats['min_rating']}"
            )
        else:
            text = (
                "📈 Коэффициент конверсии\n\n"
                f"🎯 Общий коэффициент: {stats['conversion_rate']}%\n"
                f"🎯 Максимальный коэффициент: {stats['max_conversion']}%\n"
                f"🎯 Минимальный коэффициент: {stats['min_conversion']}%\n\n"
                f"📊 Общий рейтинг: {stats['rating']}\n"
                f"📊 Максимальный рейтинг: {stats['max_rating']}\n"
                f"📊 Минимальный рейтинг: {stats['min_rating']}"
            )

        await message.answer(
            text,
            reply_markup=call_center_statistics_menu(lang)
        )

    @router.message(CallCenterStates.statistics, F.text == "🔄 Orqaga")
    async def handle_stats_back(message: Message, state: FSMContext):
        """Handle back from statistics"""
        await state.clear()
        await message.answer(
            "📊 Statistikalar menyu",
            reply_markup=call_center_main_menu_reply(message.from_user.language_code)
        )

    return router
