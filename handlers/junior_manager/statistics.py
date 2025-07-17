from aiogram import Router, F
from aiogram.types import Message
from database.base_queries import get_user_lang, get_user_by_telegram_id
from database.manager_queries import get_junior_manager_reports
from loader import get_pool
from states.junior_manager_states import JuniorManagerStatisticsStates

def get_junior_manager_statistics_router():
    router = Router()

    @router.message(F.text.in_(["📊 Hisobotlar", "📊 Отчеты"]))
    async def show_statistics(message: Message):
        lang = await get_user_lang(message.from_user.id)
        pool = await get_pool()
        report_data = await get_junior_manager_reports(pool)
        text = (
            f"📊 <b>Kichik menejer hisoboti</b>\n\n"
            f"📋 <b>Jami zayavkalar:</b> {report_data['total_orders']}\n"
            f"🆕 <b>Yangi zayavkalar:</b> {report_data['new_orders']}\n"
            f"👨‍🔧 <b>Tayinlangan zayavkalar:</b> {report_data['assigned_orders']}\n"
            f"⚡ <b>Jarayonda:</b> {report_data['in_progress_orders']}\n"
            f"✅ <b>Bajarilgan:</b> {report_data['completed_orders']}\n"
            f"❌ <b>Bekor qilingan:</b> {report_data['cancelled_orders']}\n\n"
            f"📅 <b>Bugun:</b> {report_data['today_orders']} ta zayavka\n"
            f"📅 <b>Kecha:</b> {report_data['yesterday_orders']} ta zayavka"
        )
        await message.answer(text, parse_mode='HTML')

    return router 