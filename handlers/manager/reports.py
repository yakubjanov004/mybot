from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from datetime import datetime, date, timedelta
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import get_reports_keyboard
from database.base_queries import get_reports
from database.base_queries import get_user_by_telegram_id
from database.base_queries import get_user_lang
from utils.logger import setup_logger

def get_manager_reports_router():
    logger = setup_logger('bot.manager.reports')
    router = Router()

    @router.message(F.text.in_(['📊 Hisobotlar', '📊 Отчеты']))
    async def show_reports_menu(message: Message, state: FSMContext):
        """Show reports menu"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            lang = user.get('language', 'uz')
            reports_text = "📊 Hisobot turini tanlang:" if lang == 'uz' else "📊 Выберите тип отчета:"
            
            await message.answer(
                reports_text,
                reply_markup=get_reports_keyboard(lang)
            )
            
        except Exception as e:
            logger.error(f"Error in show_reports_menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("report_"))
    async def generate_report(callback: CallbackQuery, state: FSMContext):
        """Generate different types of reports"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            report_type = callback.data.replace("report_", "")
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            conn = await bot.db.acquire()
            try:
                if report_type == "daily":
                    await generate_daily_report(callback, conn, lang)
                elif report_type == "weekly":
                    await generate_weekly_report(callback, conn, lang)
                elif report_type == "monthly":
                    await generate_monthly_report(callback, conn, lang)
                elif report_type == "technician":
                    await generate_technician_report(callback, conn, lang)
                elif report_type == "status":
                    await generate_status_report(callback, conn, lang)
                else:
                    unknown_text = "Noma'lum hisobot turi" if lang == 'uz' else "Неизвестный тип отчета"
                    await callback.message.edit_text(unknown_text)
                    
            finally:
                await conn.release()
            
        except Exception as e:
            logger.error(f"Error in generate_report: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    async def generate_daily_report(callback, conn, lang):
        """Generate daily report"""
        today = date.today()
        
        # Get today's statistics
        total_today = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE DATE(created_at) = $1',
            today
        )
        
        completed_today = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE DATE(completed_at) = $1',
            today
        )
        
        in_progress_today = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE status = $1 AND DATE(created_at) = $2',
            'in_progress', today
        )
        
        new_today = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE status = $1 AND DATE(created_at) = $2',
            'new', today
        )
        
        if lang == 'uz':
            report_text = (
                f"📊 <b>Kunlik hisobot - {today.strftime('%d.%m.%Y')}</b>\n\n"
                f"📋 <b>Jami arizalar:</b> {total_today}\n"
                f"🆕 <b>Yangi:</b> {new_today}\n"
                f"⏳ <b>Jarayonda:</b> {in_progress_today}\n"
                f"✅ <b>Bajarilgan:</b> {completed_today}\n\n"
                f"📈 <b>Bajarish foizi:</b> {round((completed_today / total_today * 100) if total_today > 0 else 0, 1)}%"
            )
        else:
            report_text = (
                f"📊 <b>Дневной отчет - {today.strftime('%d.%m.%Y')}</b>\n\n"
                f"📋 <b>Всего заявок:</b> {total_today}\n"
                f"🆕 <b>Новых:</b> {new_today}\n"
                f"⏳ <b>В процессе:</b> {in_progress_today}\n"
                f"✅ <b>Выполнено:</b> {completed_today}\n\n"
                f"📈 <b>Процент выполнения:</b> {round((completed_today / total_today * 100) if total_today > 0 else 0, 1)}%"
            )
        
        await callback.message.edit_text(report_text, parse_mode='HTML')

    async def generate_weekly_report(callback, conn, lang):
        """Generate weekly report"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = today
        
        # Get week's statistics
        total_week = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE DATE(created_at) BETWEEN $1 AND $2',
            week_start, week_end
        )
        
        completed_week = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE DATE(completed_at) BETWEEN $1 AND $2',
            week_start, week_end
        )
        
        # Get daily breakdown
        daily_stats = await conn.fetch(
            '''SELECT DATE(created_at) as day, COUNT(*) as count 
               FROM zayavki 
               WHERE DATE(created_at) BETWEEN $1 AND $2 
               GROUP BY DATE(created_at) 
               ORDER BY day''',
            week_start, week_end
        )
        
        if lang == 'uz':
            report_text = (
                f"📊 <b>Haftalik hisobot</b>\n"
                f"📅 {week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}\n\n"
                f"📋 <b>Jami arizalar:</b> {total_week}\n"
                f"✅ <b>Bajarilgan:</b> {completed_week}\n"
                f"📈 <b>Bajarish foizi:</b> {round((completed_week / total_week * 100) if total_week > 0 else 0, 1)}%\n\n"
                f"📅 <b>Kunlik taqsimot:</b>\n"
            )
            
            days_uz = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
            for i in range(7):
                day_date = week_start + timedelta(days=i)
                day_count = 0
                for stat in daily_stats:
                    if stat['day'] == day_date:
                        day_count = stat['count']
                        break
                report_text += f"• {days_uz[i]} ({day_date.strftime('%d.%m')}): {day_count}\n"
        else:
            report_text = (
                f"📊 <b>Недельный отчет</b>\n"
                f"📅 {week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}\n\n"
                f"📋 <b>Всего заявок:</b> {total_week}\n"
                f"✅ <b>Выполнено:</b> {completed_week}\n"
                f"📈 <b>Процент выполнения:</b> {round((completed_week / total_week * 100) if total_week > 0 else 0, 1)}%\n\n"
                f"📅 <b>Распределение по дням:</b>\n"
            )
            
            days_ru = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            for i in range(7):
                day_date = week_start + timedelta(days=i)
                day_count = 0
                for stat in daily_stats:
                    if stat['day'] == day_date:
                        day_count = stat['count']
                        break
                report_text += f"• {days_ru[i]} ({day_date.strftime('%d.%m')}): {day_count}\n"
        
        await callback.message.edit_text(report_text, parse_mode='HTML')

    async def generate_monthly_report(callback, conn, lang):
        """Generate monthly report"""
        today = date.today()
        month_start = today.replace(day=1)
        month_end = today
        
        # Get month's statistics
        total_month = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE DATE(created_at) BETWEEN $1 AND $2',
            month_start, month_end
        )
        
        completed_month = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE DATE(completed_at) BETWEEN $1 AND $2',
            month_start, month_end
        )
        
        cancelled_month = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE status = $1 AND DATE(created_at) BETWEEN $2 AND $3',
            'cancelled', month_start, month_end
        )
        
        in_progress_month = await conn.fetchval(
            'SELECT COUNT(*) FROM zayavki WHERE status = $1 AND DATE(created_at) BETWEEN $2 AND $3',
            'in_progress', month_start, month_end
        )
        
        # Get technician performance
        tech_stats = await conn.fetch(
            '''SELECT u.full_name, COUNT(z.id) as completed_count
               FROM users u
               LEFT JOIN zayavki z ON u.id = z.assigned_to AND z.status = 'completed' 
               AND DATE(z.completed_at) BETWEEN $1 AND $2
               WHERE u.role = 'technician'
               GROUP BY u.id, u.full_name
               ORDER BY completed_count DESC
               LIMIT 5''',
            month_start, month_end
        )
        
        month_name = {
            1: {'uz': 'Yanvar', 'ru': 'Январь'},
            2: {'uz': 'Fevral', 'ru': 'Февраль'},
            3: {'uz': 'Mart', 'ru': 'Март'},
            4: {'uz': 'Aprel', 'ru': 'Апрель'},
            5: {'uz': 'May', 'ru': 'Май'},
            6: {'uz': 'Iyun', 'ru': 'Июнь'},
            7: {'uz': 'Iyul', 'ru': 'Июль'},
            8: {'uz': 'Avgust', 'ru': 'Август'},
            9: {'uz': 'Sentyabr', 'ru': 'Сентябрь'},
            10: {'uz': 'Oktyabr', 'ru': 'Октябрь'},
            11: {'uz': 'Noyabr', 'ru': 'Ноябрь'},
            12: {'uz': 'Dekabr', 'ru': 'Декабрь'}
        }.get(today.month, {'uz': 'Noma\'lum', 'ru': 'Неизвестно'})
        
        if lang == 'uz':
            report_text = (
                f"📊 <b>Oylik hisobot - {month_name['uz']} {today.year}</b>\n\n"
                f"📋 <b>Jami arizalar:</b> {total_month}\n"
                f"✅ <b>Bajarilgan:</b> {completed_month}\n"
                f"⏳ <b>Jarayonda:</b> {in_progress_month}\n"
                f"❌ <b>Bekor qilingan:</b> {cancelled_month}\n"
                f"📈 <b>Bajarish foizi:</b> {round((completed_month / total_month * 100) if total_month > 0 else 0, 1)}%\n\n"
                f"🏆 <b>Eng faol texniklar:</b>\n"
            )
            
            for i, tech in enumerate(tech_stats, 1):
                report_text += f"{i}. {tech['full_name']}: {tech['completed_count']} ta\n"
        else:
            report_text = (
                f"📊 <b>Месячный отчет - {month_name['ru']} {today.year}</b>\n\n"
                f"📋 <b>Всего заявок:</b> {total_month}\n"
                f"✅ <b>Выполнено:</b> {completed_month}\n"
                f"⏳ <b>В процессе:</b> {in_progress_month}\n"
                f"❌ <b>Отменено:</b> {cancelled_month}\n"
                f"📈 <b>Процент выполнения:</b> {round((completed_month / total_month * 100) if total_month > 0 else 0, 1)}%\n\n"
                f"🏆 <b>Самые активные техники:</b>\n"
            )
            
            for i, tech in enumerate(tech_stats, 1):
                report_text += f"{i}. {tech['full_name']}: {tech['completed_count']} шт\n"
        
        await callback.message.edit_text(report_text, parse_mode='HTML')

    async def generate_technician_report(callback, conn, lang):
        """Generate technician performance report"""
        # Get all technicians with their statistics
        tech_stats = await conn.fetch(
            '''SELECT 
                   u.id, u.full_name, u.phone_number,
                   COUNT(CASE WHEN z.status = 'completed' THEN 1 END) as completed,
                   COUNT(CASE WHEN z.status = 'in_progress' THEN 1 END) as in_progress,
                   COUNT(CASE WHEN z.status = 'cancelled' THEN 1 END) as cancelled,
                   COUNT(z.id) as total_assigned
               FROM users u
               LEFT JOIN zayavki z ON u.id = z.assigned_to
               WHERE u.role = 'technician'
               GROUP BY u.id, u.full_name, u.phone_number
               ORDER BY completed DESC, total_assigned DESC'''
        )
        
        if lang == 'uz':
            report_text = "👨‍🔧 <b>Texniklar bo'yicha hisobot:</b>\n\n"
            
            for i, tech in enumerate(tech_stats, 1):
                efficiency = round((tech['completed'] / tech['total_assigned'] * 100) if tech['total_assigned'] > 0 else 0, 1)
                report_text += (
                    f"{i}. <b>{tech['full_name']}</b>\n"
                    f"   📞 {tech['phone_number'] or 'Telefon yo\'q'}\n"
                    f"   📋 Jami: {tech['total_assigned']}\n"
                    f"   ✅ Bajarilgan: {tech['completed']}\n"
                    f"   ⏳ Jarayonda: {tech['in_progress']}\n"
                    f"   ❌ Bekor qilingan: {tech['cancelled']}\n"
                    f"   📈 Samaradorlik: {efficiency}%\n\n"
                )
        else:
            report_text = "👨‍🔧 <b>Отчет по техникам:</b>\n\n"
            
            for i, tech in enumerate(tech_stats, 1):
                efficiency = round((tech['completed'] / tech['total_assigned'] * 100) if tech['total_assigned'] > 0 else 0, 1)
                report_text += (
                    f"{i}. <b>{tech['full_name']}</b>\n"
                    f"   📞 {tech['phone_number'] or 'Нет телефона'}\n"
                    f"   📋 Всего: {tech['total_assigned']}\n"
                    f"   ✅ Выполнено: {tech['completed']}\n"
                    f"   ⏳ В процессе: {tech['in_progress']}\n"
                    f"   ❌ Отменено: {tech['cancelled']}\n"
                    f"   📈 Эффективность: {efficiency}%\n\n"
                )
        
        await callback.message.edit_text(report_text, parse_mode='HTML')

    async def generate_status_report(callback, conn, lang):
        """Generate status distribution report"""
        # Get status statistics
        status_stats = await conn.fetch(
            '''SELECT status, COUNT(*) as count
               FROM zayavki
               GROUP BY status
               ORDER BY count DESC'''
        )
        
        total_applications = sum(stat['count'] for stat in status_stats)
        
        status_emojis = {
            'new': '🆕',
            'confirmed': '✅',
            'in_progress': '⏳',
            'completed': '🏁',
            'cancelled': '❌'
        }
        
        if lang == 'uz':
            status_labels = {
                'new': 'Yangi',
                'confirmed': 'Tasdiqlangan',
                'in_progress': 'Jarayonda',
                'completed': 'Bajarilgan',
                'cancelled': 'Bekor qilingan'
            }
            
            report_text = (
                f"📊 <b>Status bo'yicha hisobot:</b>\n\n"
                f"📋 <b>Jami arizalar:</b> {total_applications}\n\n"
            )
            
            for stat in status_stats:
                status = stat['status']
                count = stat['count']
                percentage = round((count / total_applications * 100) if total_applications > 0 else 0, 1)
                emoji = status_emojis.get(status, '📋')
                label = status_labels.get(status, status)
                
                report_text += f"{emoji} <b>{label}:</b> {count} ({percentage}%)\n"
        else:
            status_labels = {
                'new': 'Новые',
                'confirmed': 'Подтвержденные',
                'in_progress': 'В процессе',
                'completed': 'Выполненные',
                'cancelled': 'Отмененные'
            }
            
            report_text = (
                f"📊 <b>Отчет по статусам:</b>\n\n"
                f"📋 <b>Всего заявок:</b> {total_applications}\n\n"
            )
            
            for stat in status_stats:
                status = stat['status']
                count = stat['count']
                percentage = round((count / total_applications * 100) if total_applications > 0 else 0, 1)
                emoji = status_emojis.get(status, '📋')
                label = status_labels.get(status, status)
                
                report_text += f"{emoji} <b>{label}:</b> {count} ({percentage}%)\n"
        
        await callback.message.edit_text(report_text, parse_mode='HTML')

    return router
