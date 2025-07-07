from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from functools import wraps
import logging
from datetime import datetime, timedelta

from database.admin_queries import (
    is_admin, get_admin_dashboard_stats, get_performance_metrics,
    export_admin_data, log_admin_action
)
from database.base_queries import get_system_statistics, get_user_by_telegram_id, get_user_lang
from keyboards.admin_buttons import get_statistics_keyboard
from states.admin_states import AdminStates
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.logger import setup_logger
from utils.role_checks import admin_only

# Setup logger
logger = setup_logger('bot.admin.statistics')

def get_admin_statistics_router():
    router = Router()

    @router.message(F.text.in_(["📊 Statistika", "📊 Статистика"]))
    @admin_only
    async def statistics_menu(message: Message, state: FSMContext):
        """Statistics main menu"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            text = "Statistika bo'limini tanlang:" if lang == 'uz' else "Выберите раздел статистики:"
            
            await message.answer(
                text,
                reply_markup=get_statistics_keyboard(lang)
            )
            await state.set_state(AdminStates.statistics_menu)
            
        except Exception as e:
            logger.error(f"Error in statistics menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["📊 Umumiy statistika", "📊 Общая статистика"]))
    @admin_only
    async def general_statistics(message: Message):
        """Show general statistics"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get system statistics
            stats = await get_system_statistics()
            dashboard_stats = await get_admin_dashboard_stats()
            
            if lang == 'uz':
                text = (
                    f"📊 <b>Umumiy tizim statistikasi</b>\n\n"
                    f"👥 <b>Foydalanuvchilar:</b>\n"
                    f"• Jami: <b>{stats.get('active_clients', 0) + stats.get('active_technicians', 0)}</b>\n"
                    f"• Mijozlar: <b>{stats.get('active_clients', 0)}</b>\n"
                    f"• Texniklar: <b>{stats.get('active_technicians', 0)}</b>\n\n"
                    f"📋 <b>Zayavkalar:</b>\n"
                    f"• Jami: <b>{stats.get('total_orders', 0)}</b>\n"
                    f"• Bajarilgan: <b>{stats.get('completed_orders', 0)}</b>\n"
                    f"• Kutilayotgan: <b>{stats.get('pending_orders', 0)}</b>\n"
                    f"• Bugungi: <b>{dashboard_stats.get('today_orders', 0)}</b>\n\n"
                    f"💰 <b>Moliyaviy:</b>\n"
                    f"• Bugungi daromad: <b>{stats.get('revenue_today', 0):,} so'm</b>\n\n"
                    f"⏱ <b>Samaradorlik:</b>\n"
                    f"• O'rtacha bajarish vaqti: <b>{stats.get('avg_completion_time', 0)} soat</b>\n"
                    f"• Bajarish foizi: <b>{(stats.get('completed_orders', 0) / max(stats.get('total_orders', 1), 1) * 100):.1f}%</b>"
                )
            else:
                text = (
                    f"📊 <b>Общая статистика системы</b>\n\n"
                    f"👥 <b>Пользователи:</b>\n"
                    f"• Всего: <b>{stats.get('active_clients', 0) + stats.get('active_technicians', 0)}</b>\n"
                    f"• Клиенты: <b>{stats.get('active_clients', 0)}</b>\n"
                    f"• Техники: <b>{stats.get('active_technicians', 0)}</b>\n\n"
                    f"📋 <b>Заявки:</b>\n"
                    f"• Всего: <b>{stats.get('total_orders', 0)}</b>\n"
                    f"• Выполнено: <b>{stats.get('completed_orders', 0)}</b>\n"
                    f"• Ожидающие: <b>{stats.get('pending_orders', 0)}</b>\n"
                    f"• Сегодня: <b>{dashboard_stats.get('today_orders', 0)}</b>\n\n"
                    f"💰 <b>Финансы:</b>\n"
                    f"• Доход сегодня: <b>{stats.get('revenue_today', 0):,} сум</b>\n\n"
                    f"⏱ <b>Эффективность:</b>\n"
                    f"• Среднее время выполнения: <b>{stats.get('avg_completion_time', 0)} часов</b>\n"
                    f"• Процент выполнения: <b>{(stats.get('completed_orders', 0) / max(stats.get('total_orders', 1), 1) * 100):.1f}%</b>"
                )
            
            # Add refresh button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Yangilash" if lang == 'uz' else "🔄 Обновить",
                        callback_data="refresh_general_stats"
                    )
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing general statistics: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["📈 Samaradorlik hisoboti", "📈 Отчет эффективности"]))
    @admin_only
    async def performance_report(message: Message):
        """Show performance report"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get performance metrics for different periods
            daily_metrics = await get_performance_metrics('daily')
            weekly_metrics = await get_performance_metrics('weekly')
            monthly_metrics = await get_performance_metrics('monthly')
            
            if lang == 'uz':
                text = (
                    f"📈 <b>Samaradorlik hisoboti</b>\n\n"
                    f"📅 <b>Bugungi ko'rsatkichlar:</b>\n"
                    f"• Zayavkalar: <b>{daily_metrics.get('total_orders', 0)}</b>\n"
                    f"• Bajarilgan: <b>{daily_metrics.get('completed_orders', 0)}</b>\n"
                    f"• Bajarish foizi: <b>{daily_metrics.get('completion_rate', 0):.1f}%</b>\n"
                    f"• O'rtacha vaqt: <b>{daily_metrics.get('avg_completion_hours', 0):.1f} soat</b>\n\n"
                    f"📊 <b>Haftalik ko'rsatkichlar:</b>\n"
                    f"• Zayavkalar: <b>{weekly_metrics.get('total_orders', 0)}</b>\n"
                    f"• Bajarilgan: <b>{weekly_metrics.get('completed_orders', 0)}</b>\n"
                    f"• Bajarish foizi: <b>{weekly_metrics.get('completion_rate', 0):.1f}%</b>\n\n"
                    f"📈 <b>Oylik ko'rsatkichlar:</b>\n"
                    f"• Zayavkalar: <b>{monthly_metrics.get('total_orders', 0)}</b>\n"
                    f"• Bajarilgan: <b>{monthly_metrics.get('completed_orders', 0)}</b>\n"
                    f"• Bajarish foizi: <b>{monthly_metrics.get('completion_rate', 0):.1f}%</b>\n\n"
                    f"👥 <b>Foydalanuvchi faolligi:</b>\n"
                    f"• Faol foydalanuvchilar: <b>{daily_metrics.get('active_users', 0)}</b>\n"
                    f"• Jami amallar: <b>{daily_metrics.get('total_actions', 0)}</b>\n\n"
                    f"⚡ <b>Tizim yuki:</b>\n"
                    f"• Kutilayotgan: <b>{daily_metrics.get('pending_load', 0)}</b>\n"
                    f"• Jarayonda: <b>{daily_metrics.get('active_load', 0)}</b>"
                )
            else:
                text = (
                    f"📈 <b>Отчет эффективности</b>\n\n"
                    f"📅 <b>Показатели сегодня:</b>\n"
                    f"• Заявки: <b>{daily_metrics.get('total_orders', 0)}</b>\n"
                    f"• Выполнено: <b>{daily_metrics.get('completed_orders', 0)}</b>\n"
                    f"• Процент выполнения: <b>{daily_metrics.get('completion_rate', 0):.1f}%</b>\n"
                    f"• Среднее время: <b>{daily_metrics.get('avg_completion_hours', 0):.1f} часов</b>\n\n"
                    f"📊 <b>Недельные показатели:</b>\n"
                    f"• Заявки: <b>{weekly_metrics.get('total_orders', 0)}</b>\n"
                    f"• Выполнено: <b>{weekly_metrics.get('completed_orders', 0)}</b>\n"
                    f"• Процент выполнения: <b>{weekly_metrics.get('completion_rate', 0):.1f}%</b>\n\n"
                    f"📈 <b>Месячные показатели:</b>\n"
                    f"• Заявки: <b>{monthly_metrics.get('total_orders', 0)}</b>\n"
                    f"• Выполнено: <b>{monthly_metrics.get('completed_orders', 0)}</b>\n"
                    f"• Процент выполнения: <b>{monthly_metrics.get('completion_rate', 0):.1f}%</b>\n\n"
                    f"👥 <b>Активность пользователей:</b>\n"
                    f"• Активные пользователи: <b>{daily_metrics.get('active_users', 0)}</b>\n"
                    f"• Всего действий: <b>{daily_metrics.get('total_actions', 0)}</b>\n\n"
                    f"⚡ <b>Нагрузка системы:</b>\n"
                    f"• Ожидающие: <b>{daily_metrics.get('pending_load', 0)}</b>\n"
                    f"• В процессе: <b>{daily_metrics.get('active_load', 0)}</b>"
                )
            
            await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error showing performance report: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["📋 Xodimlar statistikasi", "📋 Статистика сотрудников"]))
    @admin_only
    async def staff_statistics(message: Message):
        """Show staff statistics"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get staff statistics from dashboard
            dashboard_stats = await get_admin_dashboard_stats()
            
            if lang == 'uz':
                text = (
                    f"📋 <b>Xodimlar statistikasi</b>\n\n"
                    f"👥 <b>Rollar bo'yicha taqsimot:</b>\n"
                )
                
                for role_stat in dashboard_stats.get('users_by_role', []):
                    role_name = {
                        'client': 'Mijozlar',
                        'technician': 'Texniklar',
                        'manager': 'Menejerlar',
                        'admin': 'Adminlar',
                        'call_center': 'Call Center',
                        'controller': 'Kontrolyorlar',
                        'warehouse': 'Sklad'
                    }.get(role_stat['role'], role_stat['role'])
                    text += f"• {role_name}: <b>{role_stat['count']}</b>\n"
                
                text += (
                    f"\n⚡ <b>Faol xodimlar:</b>\n"
                    f"• Texniklar: <b>{dashboard_stats.get('active_technicians', 0)}</b>\n"
                    f"• Menejerlar: <b>{dashboard_stats.get('active_managers', 0)}</b>\n\n"
                    f"📊 <b>Bugungi faollik:</b>\n"
                    f"• Bajarilgan vazifalar: <b>{dashboard_stats.get('today_completed', 0)}</b>\n"
                    f"• Jami zayavkalar: <b>{dashboard_stats.get('today_orders', 0)}</b>"
                )
            else:
                text = (
                    f"📋 <b>Статистика сотрудников</b>\n\n"
                    f"👥 <b>Распределение по ролям:</b>\n"
                )
                
                for role_stat in dashboard_stats.get('users_by_role', []):
                    role_name = {
                        'client': 'Клиенты',
                        'technician': 'Техники',
                        'manager': 'Менеджеры',
                        'admin': 'Администраторы',
                        'call_center': 'Колл-центр',
                        'controller': 'Контроллеры',
                        'warehouse': 'Склад'
                    }.get(role_stat['role'], role_stat['role'])
                    text += f"• {role_name}: <b>{role_stat['count']}</b>\n"
                
                text += (
                    f"\n⚡ <b>Активные сотрудники:</b>\n"
                    f"• Техники: <b>{dashboard_stats.get('active_technicians', 0)}</b>\n"
                    f"• Менеджеры: <b>{dashboard_stats.get('active_managers', 0)}</b>\n\n"
                    f"📊 <b>Активность сегодня:</b>\n"
                    f"• Выполненные задачи: <b>{dashboard_stats.get('today_completed', 0)}</b>\n"
                    f"• Всего заявок: <b>{dashboard_stats.get('today_orders', 0)}</b>"
                )
            
            await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error showing staff statistics: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["📊 Grafik va diagrammalar", "📊 Графики и диаграммы"]))
    @admin_only
    async def charts_and_graphs(message: Message):
        """Show charts and graphs menu"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            text = "Grafik turini tanlang:" if lang == 'uz' else "Выберите тип графика:"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📈 Zayavkalar dinamikasi" if lang == 'uz' else "📈 Динамика заявок",
                        callback_data="chart_orders_dynamic"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🥧 Status bo'yicha taqsimot" if lang == 'uz' else "🥧 Распределение по статусам",
                        callback_data="chart_status_distribution"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 Xodimlar samaradorligi" if lang == 'uz' else "👥 Эффективность сотрудников",
                        callback_data="chart_staff_performance"
                    )
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing charts menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["📤 Ma'lumotlarni eksport qilish", "�� Экспорт данных"]))
    @admin_only
    async def export_data_menu(message: Message):
        """Export data menu"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            text = "Eksport qilish uchun ma'lumot turini tanlang:" if lang == 'uz' else "Выберите тип данных для экспорта:"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👥 Foydalanuvchilar" if lang == 'uz' else "👥 Пользователи",
                        callback_data="export_users"
                    ),
                    InlineKeyboardButton(
                        text="📋 Zayavkalar" if lang == 'uz' else "📋 Заявки",
                        callback_data="export_orders"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Statistika" if lang == 'uz' else "📊 Статистика",
                        callback_data="export_statistics"
                    ),
                    InlineKeyboardButton(
                        text="📋 Loglar" if lang == 'uz' else "📋 Логи",
                        callback_data="export_logs"
                    )
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing export menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.callback_query(F.data == "refresh_general_stats")
    @admin_only
    async def refresh_general_stats(call: CallbackQuery):
        """Refresh general statistics"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            # Get fresh statistics
            stats = await get_system_statistics()
            dashboard_stats = await get_admin_dashboard_stats()
            
            if lang == 'uz':
                text = (
                    f"🔄 <b>Yangilangan umumiy statistika</b>\n\n"
                    f"👥 <b>Foydalanuvchilar:</b>\n"
                    f"• Jami: <b>{stats.get('active_clients', 0) + stats.get('active_technicians', 0)}</b>\n"
                    f"• Mijozlar: <b>{stats.get('active_clients', 0)}</b>\n"
                    f"• Texniklar: <b>{stats.get('active_technicians', 0)}</b>\n\n"
                    f"📋 <b>Zayavkalar:</b>\n"
                    f"• Jami: <b>{stats.get('total_orders', 0)}</b>\n"
                    f"• Bajarilgan: <b>{stats.get('completed_orders', 0)}</b>\n"
                    f"• Kutilayotgan: <b>{stats.get('pending_orders', 0)}</b>\n"
                    f"• Bugungi: <b>{dashboard_stats.get('today_orders', 0)}</b>\n\n"
                    f"⏱ <b>Samaradorlik:</b>\n"
                    f"• Bajarish foizi: <b>{(stats.get('completed_orders', 0) / max(stats.get('total_orders', 1), 1) * 100):.1f}%</b>\n\n"
                    f"🕐 Yangilangan: {datetime.now().strftime('%H:%M:%S')}"
                )
            else:
                text = (
                    f"🔄 <b>Обновленная общая статистика</b>\n\n"
                    f"👥 <b>Пользователи:</b>\n"
                    f"• Всего: <b>{stats.get('active_clients', 0) + stats.get('active_technicians', 0)}</b>\n"
                    f"• Клиенты: <b>{stats.get('active_clients', 0)}</b>\n"
                    f"• Техники: <b>{stats.get('active_technicians', 0)}</b>\n\n"
                    f"📋 <b>Заявки:</b>\n"
                    f"• Всего: <b>{stats.get('total_orders', 0)}</b>\n"
                    f"• Выполнено: <b>{stats.get('completed_orders', 0)}</b>\n"
                    f"• Ожидающие: <b>{stats.get('pending_orders', 0)}</b>\n"
                    f"• Сегодня: <b>{dashboard_stats.get('today_orders', 0)}</b>\n\n"
                    f"⏱ <b>Эффективность:</b>\n"
                    f"• Процент выполнения: <b>{(stats.get('completed_orders', 0) / max(stats.get('total_orders', 1), 1) * 100):.1f}%</b>\n\n"
                    f"🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Yangilash" if lang == 'uz' else "🔄 Обновить",
                        callback_data="refresh_general_stats"
                    )
                ]
            ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            await call.answer("Statistika yangilandi!" if lang == 'uz' else "Статистика обновлена!")
            
        except Exception as e:
            logger.error(f"Error refreshing general stats: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("export_"))
    @admin_only
    async def export_data(call: CallbackQuery):
        """Export data to CSV"""
        try:
            lang = await get_user_lang(call.from_user.id)
            export_type = call.data.split("_")[1]
            
            # Show processing message
            processing_text = "Ma'lumotlar tayyorlanmoqda..." if lang == 'uz' else "Подготовка данных..."
            await call.message.edit_text(processing_text)
            
            # Export data
            file_path = await export_admin_data(export_type)
            
            if file_path:
                # Log admin action
                await log_admin_action(call.from_user.id, "export_data", {"export_type": export_type})
                
                # Send file
                try:
                    with open(file_path, 'rb') as file:
                        await call.message.answer_document(
                            file,
                            caption=f"📤 {export_type.title()} ma'lumotlari eksport qilindi" if lang == 'uz' else f"📤 Данные {export_type} экспортированы"
                        )
                    
                    success_text = "✅ Eksport muvaffaqiyatli yakunlandi!" if lang == 'uz' else "✅ Экспорт успешно завершен!"
                    await call.message.edit_text(success_text)
                    
                    # Clean up file
                    import os
                    os.unlink(file_path)
                    
                except Exception as file_error:
                    logger.error(f"Error sending exported file: {file_error}")
                    error_text = "Faylni yuborishda xatolik." if lang == 'uz' else "Ошибка при отправке файла."
                    await call.message.edit_text(error_text)
            else:
                error_text = "Eksport qilishda xatolik." if lang == 'uz' else "Ошибка при экспорте."
                await call.message.edit_text(error_text)
            
            await call.answer()
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("chart_"))
    @admin_only
    async def show_chart(call: CallbackQuery):
        """Show chart (placeholder for future implementation)"""
        try:
            lang = await get_user_lang(call.from_user.id)
            chart_type = call.data.split("_", 1)[1]
            
            # For now, show text-based representation
            if chart_type == "orders_dynamic":
                # Get last 7 days data
                dashboard_stats = await get_admin_dashboard_stats()
                
                text = "📈 <b>Zayavkalar dinamikasi (oxirgi 7 kun)</b>\n\n" if lang == 'uz' else "�� <b>Динамика заявок (последние 7 дней)</b>\n\n"
                text += "Grafik funksiyasi tez orada qo'shiladi..." if lang == 'uz' else "Функция графиков будет добавлена в ближайшее время..."
                
            elif chart_type == "status_distribution":
                dashboard_stats = await get_admin_dashboard_stats()
                
                text = "🥧 <b>Status bo'yicha taqsimot</b>\n\n" if lang == 'uz' else "🥧 <b>Распределение по статусам</b>\n\n"
                
                for status_stat in dashboard_stats.get('orders_by_status', []):
                    status_name = {
                        'new': '🆕 Yangi' if lang == 'uz' else '🆕 Новые',
                        'pending': '⏳ Kutilmoqda' if lang == 'uz' else '⏳ Ожидающие',
                        'assigned': '👨‍🔧 Tayinlangan' if lang == 'uz' else '👨‍🔧 Назначенные',
                        'in_progress': '🔄 Jarayonda' if lang == 'uz' else '🔄 В процессе',
                        'completed': '✅ Bajarilgan' if lang == 'uz' else '✅ Выполненные',
                        'cancelled': '❌ Bekor qilingan' if lang == 'uz' else '❌ Отмененные'
                    }.get(status_stat['status'], status_stat['status'])
                    
                    # Simple text-based bar chart
                    bar_length = min(status_stat['count'] // 2, 20)
                    bar = "█" * bar_length
                    text += f"{status_name}: {bar} {status_stat['count']}\n"
            
            else:
                text = "Grafik funksiyasi ishlab chiqilmoqda..." if lang == 'uz' else "Функция графиков в разработке..."
            
            await call.message.edit_text(text)
            await call.answer()
            
        except Exception as e:
            logger.error(f"Error showing chart: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    return router
