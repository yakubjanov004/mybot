from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from datetime import datetime, date, timedelta
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import get_staff_activity_keyboard, get_junior_manager_work_keyboard
from database.manager_queries import get_online_staff, get_staff_performance, get_staff_workload, get_staff_attendance
from database.base_queries import get_user_by_telegram_id
from database.base_queries import get_user_lang
from utils.logger import setup_logger
from utils.role_router import get_role_router
from loader import bot

def get_manager_staff_activity_router():
    logger = setup_logger('bot.manager.staff_activity')
    router = get_role_router("manager")

    @router.message(F.text.in_(['👥 Xodimlar faoliyati', '👥 Активность сотрудников']))
    async def show_staff_activity_menu(message: Message, state: FSMContext):
        """Show staff activity menu"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            lang = user.get('language', 'uz')
            activity_text = "👥 Xodimlar faoliyati:" if lang == 'uz' else "👥 Активность сотрудников:"
            
            await message.answer(
                activity_text,
                reply_markup=get_staff_activity_keyboard(lang)
            )
            
        except Exception as e:
            logger.error(f"Error in show_staff_activity_menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("staff_"))
    async def handle_staff_activity(callback: CallbackQuery, state: FSMContext):
        """Handle staff activity actions"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            action = callback.data.replace("staff_", "")
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            if action == "online":
                await show_online_staff(callback, lang)
            elif action == "performance":
                await show_staff_performance(callback, lang)
            elif action == "workload":
                await show_staff_workload(callback, lang)
            elif action == "attendance":
                await show_staff_attendance(callback, lang)
            elif action == "junior_work":
                await show_junior_manager_work(callback, lang)
            else:
                unknown_text = "Noma'lum amal" if lang == 'uz' else "Неизвестное действие"
                await callback.message.edit_text(unknown_text)
            
        except Exception as e:
            logger.error(f"Error in handle_staff_activity: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    async def show_online_staff(callback, lang):
        """Show currently online staff"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get staff who were active in the last 30 minutes
                online_staff = await conn.fetch(
                    '''SELECT u.*, 
                              EXTRACT(EPOCH FROM (NOW() - u.last_activity))/60 as minutes_ago
                     FROM users u
                     WHERE u.role IN ('technician', 'manager', 'call_center', 'warehouse', 'junior_manager')
                     AND u.last_activity > NOW() - INTERVAL '30 minutes'
                     ORDER BY u.last_activity DESC'''
                )
                
                if not online_staff:
                    no_online_text = "❌ Hozirda onlayn xodimlar yo'q." if lang == 'uz' else "❌ В данный момент нет сотрудников онлайн."
                    await callback.message.edit_text(no_online_text)
                    return
                
                role_emojis = {
                    'technician': '👨‍🔧',
                    'manager': '👨‍💼',
                    'call_center': '📞',
                    'warehouse': '📦',
                    'junior_manager': '👨‍💼'
                }
                
                if lang == 'uz':
                    online_text = "🟢 <b>Onlayn xodimlar:</b>\n\n"
                    
                    for staff in online_staff:
                        role_emoji = role_emojis.get(staff['role'], '👤')
                        minutes_ago = int(staff['minutes_ago']) if staff['minutes_ago'] else 0
                        
                        if minutes_ago < 5:
                            status = "🟢 Faol"
                        elif minutes_ago < 15:
                            status = f"🟡 {minutes_ago} daqiqa oldin"
                        else:
                            status = f"🟠 {minutes_ago} daqiqa oldin"
                        
                        online_text += (
                            f"{role_emoji} <b>{staff['full_name']}</b>\n"
                            f"   📞 {staff.get('phone_number', '-')}\n"
                            f"   💼 Lavozim: {staff['role']}\n"
                            f"   ⏰ Status: {status}\n\n"
                        )
                else:
                    online_text = "🟢 <b>Сотрудники онлайн:</b>\n\n"
                    
                    for staff in online_staff:
                        role_emoji = role_emojis.get(staff['role'], '👤')
                        minutes_ago = int(staff['minutes_ago']) if staff['minutes_ago'] else 0
                        
                        if minutes_ago < 5:
                            status = "🟢 Активен"
                        elif minutes_ago < 15:
                            status = f"🟡 {minutes_ago} мин назад"
                        else:
                            status = f"🟠 {minutes_ago} мин назад"
                        
                        online_text += (
                            f"{role_emoji} <b>{staff['full_name']}</b>\n"
                            f"   📞 {staff.get('phone_number', '-')}\n"
                            f"   💼 Должность: {staff['role']}\n"
                            f"   ⏰ Статус: {status}\n\n"
                        )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="staff_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(online_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_online_staff: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def show_staff_performance(callback, lang):
        """Show staff performance statistics"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get performance data for the last 30 days
                performance_data = await conn.fetch(
                    '''SELECT 
                           u.full_name, u.role, u.phone_number,
                           COUNT(CASE WHEN z.status = 'completed' AND z.completed_at > NOW() - INTERVAL '30 days' THEN 1 END) as completed_30d,
                           COUNT(CASE WHEN z.status = 'in_progress' THEN 1 END) as in_progress,
                           COUNT(CASE WHEN z.status = 'cancelled' AND z.updated_at > NOW() - INTERVAL '30 days' THEN 1 END) as cancelled_30d,
                           AVG(CASE WHEN z.status = 'completed' AND z.completed_at > NOW() - INTERVAL '30 days' 
                               THEN EXTRACT(EPOCH FROM (z.completed_at - z.created_at))/3600 END) as avg_completion_hours
                       FROM users u
                       LEFT JOIN zayavki z ON u.id = z.assigned_to
                       WHERE u.role IN ('technician', 'manager', 'call_center', 'junior_manager')
                       GROUP BY u.id, u.full_name, u.role, u.phone_number
                       ORDER BY completed_30d DESC, u.role'''
                )
                
                if not performance_data:
                    no_data_text = "❌ Ma'lumotlar topilmadi." if lang == 'uz' else "❌ Данные не найдены."
                    await callback.message.edit_text(no_data_text)
                    return
                
                role_emojis = {
                    'technician': '👨‍🔧',
                    'manager': '👨‍💼',
                    'call_center': '📞',
                    'junior_manager': '👨‍💼'
                }
                
                if lang == 'uz':
                    performance_text = "📊 <b>Xodimlar samaradorligi (30 kun):</b>\n\n"
                    
                    for staff in performance_data:
                        role_emoji = role_emojis.get(staff['role'], '👤')
                        avg_hours = round(staff['avg_completion_hours'] or 0, 1)
                        
                        performance_text += (
                            f"{role_emoji} <b>{staff['full_name']}</b>\n"
                            f"   📞 {staff.get('phone_number', '-')}\n"
                            f"   ✅ Bajarilgan: {staff['completed_30d']}\n"
                            f"   ⏳ Jarayonda: {staff['in_progress']}\n"
                            f"   ❌ Bekor qilingan: {staff['cancelled_30d']}\n"
                            f"   ⏱️ O'rtacha vaqt: {avg_hours} soat\n\n"
                        )
                else:
                    performance_text = "📊 <b>Производительность сотрудников (30 дней):</b>\n\n"
                    
                    for staff in performance_data:
                        role_emoji = role_emojis.get(staff['role'], '👤')
                        avg_hours = round(staff['avg_completion_hours'] or 0, 1)
                        
                        performance_text += (
                            f"{role_emoji} <b>{staff['full_name']}</b>\n"
                            f"   📞 {staff.get('phone_number', '-')}\n"
                            f"   ✅ Выполнено: {staff['completed_30d']}\n"
                            f"   ⏳ В процессе: {staff['in_progress']}\n"
                            f"   ❌ Отменено: {staff['cancelled_30d']}\n"
                            f"   ⏱️ Среднее время: {avg_hours} часов\n\n"
                        )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="staff_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(performance_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_staff_performance: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def show_staff_workload(callback, lang):
        """Show current staff workload"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get current workload for each staff member
                workload_data = await conn.fetch(
                    '''SELECT 
                           u.full_name, u.role, u.phone_number,
                           COUNT(CASE WHEN z.status IN ('new', 'confirmed', 'in_progress') THEN 1 END) as active_tasks,
                           COUNT(CASE WHEN z.status = 'new' THEN 1 END) as new_tasks,
                           COUNT(CASE WHEN z.status = 'in_progress' THEN 1 END) as in_progress_tasks
                       FROM users u
                       LEFT JOIN zayavki z ON u.id = z.assigned_to
                       WHERE u.role IN ('technician', 'manager', 'call_center', 'junior_manager')
                       GROUP BY u.id, u.full_name, u.role, u.phone_number
                       ORDER BY active_tasks DESC, u.role'''
                )
                
                if not workload_data:
                    no_data_text = "❌ Ma'lumotlar topilmadi." if lang == 'uz' else "❌ Данные не найдены."
                    await callback.message.edit_text(no_data_text)
                    return
                
                role_emojis = {
                    'technician': '👨‍🔧',
                    'manager': '👨‍💼',
                    'call_center': '📞',
                    'junior_manager': '👨‍💼'
                }
                
                if lang == 'uz':
                    workload_text = "📋 <b>Xodimlar ish yuki:</b>\n\n"
                    
                    for staff in workload_data:
                        role_emoji = role_emojis.get(staff['role'], '👤')
                        
                        # Determine workload level
                        active_tasks = staff['active_tasks']
                        if active_tasks == 0:
                            workload_emoji = "🟢"
                            workload_status = "Bo'sh"
                        elif active_tasks <= 3:
                            workload_emoji = "🟡"
                            workload_status = "Normal"
                        elif active_tasks <= 6:
                            workload_emoji = "🟠"
                            workload_status = "Yuklangan"
                        else:
                            workload_emoji = "🔴"
                            workload_status = "Juda yuklangan"
                        
                        workload_text += (
                            f"{role_emoji} <b>{staff['full_name']}</b>\n"
                            f"   📞 {staff.get('phone_number', '-')}\n"
                            f"   {workload_emoji} Status: {workload_status}\n"
                            f"   📋 Jami faol: {active_tasks}\n"
                            f"   🆕 Yangi: {staff['new_tasks']}\n"
                            f"   ⏳ Jarayonda: {staff['in_progress_tasks']}\n\n"
                        )
                else:
                    workload_text = "📋 <b>Рабочая нагрузка сотрудников:</b>\n\n"
                    
                    for staff in workload_data:
                        role_emoji = role_emojis.get(staff['role'], '👤')
                        
                        # Determine workload level
                        active_tasks = staff['active_tasks']
                        if active_tasks == 0:
                            workload_emoji = "🟢"
                            workload_status = "Свободен"
                        elif active_tasks <= 3:
                            workload_emoji = "🟡"
                            workload_status = "Нормально"
                        elif active_tasks <= 6:
                            workload_emoji = "🟠"
                            workload_status = "Загружен"
                        else:
                            workload_emoji = "🔴"
                            workload_status = "Перегружен"
                        
                        workload_text += (
                            f"{role_emoji} <b>{staff['full_name']}</b>\n"
                            f"   📞 {staff.get('phone_number', '-')}\n"
                            f"   {workload_emoji} Статус: {workload_status}\n"
                            f"   📋 Всего активных: {active_tasks}\n"
                            f"   🆕 Новых: {staff['new_tasks']}\n"
                            f"   ⏳ В процессе: {staff['in_progress_tasks']}\n\n"
                        )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="staff_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(workload_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_staff_workload: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def show_staff_attendance(callback, lang):
        """Show staff attendance for today"""
        try:
            conn = await bot.db.acquire()
            try:
                today = date.today()
                
                # Get staff attendance data
                attendance_data = await conn.fetch(
                    '''SELECT 
                           u.full_name, u.role, u.phone_number,
                           u.last_activity,
                           CASE WHEN u.last_activity::date = $1 THEN true ELSE false END as active_today
                       FROM users u
                       WHERE u.role IN ('technician', 'manager', 'call_center', 'warehouse', 'junior_manager')
                       ORDER BY u.role, u.full_name''',
                    today
                )
                
                if not attendance_data:
                    no_data_text = "❌ Ma'lumotlar topilmadi." if lang == 'uz' else "❌ Данные не найдены."
                    await callback.message.edit_text(no_data_text)
                    return
                
                role_emojis = {
                    'technician': '👨‍🔧',
                    'manager': '👨‍💼',
                    'call_center': '📞',
                    'warehouse': '📦',
                    'junior_manager': '👨‍💼'
                }
                
                active_count = sum(1 for staff in attendance_data if staff['active_today'])
                total_count = len(attendance_data)
                
                if lang == 'uz':
                    attendance_text = (
                        f"📅 <b>Bugungi davomat - {today.strftime('%d.%m.%Y')}</b>\n\n"
                        f"👥 Jami xodimlar: {total_count}\n"
                        f"✅ Faol: {active_count}\n"
                        f"❌ Faol emas: {total_count - active_count}\n\n"
                    )
                    
                    for staff in attendance_data:
                        role_emoji = role_emojis.get(staff['role'], '👤')
                        status_emoji = "✅" if staff['active_today'] else "❌"
                        
                        last_activity = ""
                        if staff['last_activity']:
                            if staff['active_today']:
                                last_activity = staff['last_activity'].strftime('%H:%M')
                            else:
                                last_activity = staff['last_activity'].strftime('%d.%m %H:%M')
                        else:
                            last_activity = "Hech qachon"
                        
                        attendance_text += (
                            f"{role_emoji} {status_emoji} <b>{staff['full_name']}</b>\n"
                            f"   📞 {staff.get('phone_number', '-')}\n"
                            f"   ⏰ Oxirgi faollik: {last_activity}\n\n"
                        )
                else:
                    attendance_text = (
                        f"📅 <b>Посещаемость сегодня - {today.strftime('%d.%m.%Y')}</b>\n\n"
                        f"👥 Всего сотрудников: {total_count}\n"
                        f"✅ Активных: {active_count}\n"
                        f"❌ Неактивных: {total_count - active_count}\n\n"
                    )
                    
                    for staff in attendance_data:
                        role_emoji = role_emojis.get(staff['role'], '👤')
                        status_emoji = "✅" if staff['active_today'] else "❌"
                        
                        last_activity = ""
                        if staff['last_activity']:
                            if staff['active_today']:
                                last_activity = staff['last_activity'].strftime('%H:%M')
                            else:
                                last_activity = staff['last_activity'].strftime('%d.%m %H:%M')
                        else:
                            last_activity = "Никогда"
                        
                        attendance_text += (
                            f"{role_emoji} {status_emoji} <b>{staff['full_name']}</b>\n"
                            f"   📞 {staff.get('phone_number', '-')}\n"
                            f"   ⏰ Последняя активность: {last_activity}\n\n"
                        )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="staff_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(attendance_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_staff_attendance: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def show_junior_manager_work(callback, lang):
        """Show junior manager work statistics"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get junior manager work data
                junior_data = await conn.fetch(
                    '''SELECT 
                           u.full_name, u.phone_number,
                           COUNT(CASE WHEN z.status = 'completed' AND z.completed_at > NOW() - INTERVAL '7 days' THEN 1 END) as completed_week,
                           COUNT(CASE WHEN z.status = 'in_progress' THEN 1 END) as in_progress,
                           COUNT(CASE WHEN z.status = 'new' THEN 1 END) as new_tasks,
                           AVG(CASE WHEN z.status = 'completed' AND z.completed_at > NOW() - INTERVAL '7 days' 
                               THEN EXTRACT(EPOCH FROM (z.completed_at - z.created_at))/3600 END) as avg_completion_hours
                       FROM users u
                       LEFT JOIN zayavki z ON u.id = z.assigned_by
                       WHERE u.role = 'junior_manager'
                       GROUP BY u.id, u.full_name, u.phone_number
                       ORDER BY completed_week DESC'''
                )
                
                if not junior_data:
                    no_data_text = "❌ Kichik menejerlar ishi topilmadi." if lang == 'uz' else "❌ Работа младших менеджеров не найдена."
                    await callback.message.edit_text(no_data_text)
                    return
                
                if lang == 'uz':
                    junior_text = "👨‍💼 <b>Kichik menejerlar ishi (7 kun):</b>\n\n"
                    
                    for junior in junior_data:
                        avg_hours = round(junior['avg_completion_hours'] or 0, 1)
                        
                        junior_text += (
                            f"👨‍💼 <b>{junior['full_name']}</b>\n"
                            f"   📞 {junior.get('phone_number', '-')}\n"
                            f"   ✅ Bajarilgan: {junior['completed_week']}\n"
                            f"   ⏳ Jarayonda: {junior['in_progress']}\n"
                            f"   🆕 Yangi: {junior['new_tasks']}\n"
                            f"   ⏱️ O'rtacha vaqt: {avg_hours} soat\n\n"
                        )
                else:
                    junior_text = "👨‍💼 <b>Работа младших менеджеров (7 дней):</b>\n\n"
                    
                    for junior in junior_data:
                        avg_hours = round(junior['avg_completion_hours'] or 0, 1)
                        
                        junior_text += (
                            f"👨‍💼 <b>{junior['full_name']}</b>\n"
                            f"   📞 {junior.get('phone_number', '-')}\n"
                            f"   ✅ Выполнено: {junior['completed_week']}\n"
                            f"   ⏳ В процессе: {junior['in_progress']}\n"
                            f"   🆕 Новых: {junior['new_tasks']}\n"
                            f"   ⏱️ Среднее время: {avg_hours} часов\n\n"
                        )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="staff_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(junior_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_junior_manager_work: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    @router.callback_query(F.data == "staff_menu")
    async def back_to_staff_menu(callback: CallbackQuery, state: FSMContext):
        """Return to staff activity menu"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            activity_text = "👥 Xodimlar faoliyati:" if lang == 'uz' else "👥 Активность сотрудников:"
            
            await callback.message.edit_text(
                activity_text,
                reply_markup=get_staff_activity_keyboard(lang)
            )
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in back_to_staff_menu: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    return router
