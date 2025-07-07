from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from database.admin_queries import get_admin_dashboard_stats, log_admin_action
from database.base_queries import get_user_lang
from keyboards.admin_buttons import get_admin_main_menu
from states.admin_states import AdminStates
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.logger import setup_logger
from utils.role_checks import admin_only

# Setup logger
logger = setup_logger('bot.admin.main_menu')

async def show_admin_main_menu(message, state):
    """Show admin main menu"""
    try:
        await cleanup_user_inline_messages(message.from_user.id)
        lang = await get_user_lang(message.from_user.id)
        stats = await get_admin_dashboard_stats()
        await log_admin_action(message.from_user.id, "admin_login")
        welcome_text = (
            f"🔧 <b>{'Admin Panel' if lang == 'uz' else 'Панель администратора'}</b>\n\n"
            f"📊 <b>{'Tizim holati' if lang == 'uz' else 'Состояние системы'}:</b>\n"
            f"👥 {'Jami foydalanuvchilar' if lang == 'uz' else 'Всего пользователей'}: <b>{stats.get('total_users', 0)}</b>\n"
            f"📋 {'Bugungi zayavkalar' if lang == 'uz' else 'Заявки сегодня'}: <b>{stats.get('today_orders', 0)}</b>\n"
            f"✅ {'Bugun bajarilgan' if lang == 'uz' else 'Выполнено сегодня'}: <b>{stats.get('today_completed', 0)}</b>\n"
            f"⏳ {'Kutilayotgan' if lang == 'uz' else 'Ожидающие'}: <b>{stats.get('pending_orders', 0)}</b>\n"
            f"👨‍🔧 {'Faol texniklar' if lang == 'uz' else 'Активные техники'}: <b>{stats.get('active_technicians', 0)}</b>\n\n"
            f"{'Kerakli bo\'limni tanlang:' if lang == 'uz' else 'Выберите нужный раздел:'}"
        )
        await message.answer(
            welcome_text,
            reply_markup=get_admin_main_menu(lang)
        )
        await state.set_state(AdminStates.main_menu)
        
        logger.info(f"Admin panel shown to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in admin_start: {e}")
        try:
            lang = await get_user_lang(message.from_user.id)
        except:
            lang = 'ru'
        error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await message.answer(error_text)

def get_admin_main_menu_router():
    router = Router()

    @router.message(F.text.in_(["/start", "/admin"]))
    @admin_only
    async def admin_start(message: Message, state: FSMContext):
        await show_admin_main_menu(message, state)

    async def show_admin_main_menu(message: Message, state: FSMContext):
        """Show admin main menu"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            stats = await get_admin_dashboard_stats()
            await log_admin_action(message.from_user.id, "admin_login")
            welcome_text = (
                f"🔧 <b>{'Admin Panel' if lang == 'uz' else 'Панель администратора'}</b>\n\n"
                f"📊 <b>{'Tizim holati' if lang == 'uz' else 'Состояние системы'}:</b>\n"
                f"👥 {'Jami foydalanuvchilar' if lang == 'uz' else 'Всего пользователей'}: <b>{stats.get('total_users', 0)}</b>\n"
                f"📋 {'Bugungi zayavkalar' if lang == 'uz' else 'Заявки сегодня'}: <b>{stats.get('today_orders', 0)}</b>\n"
                f"✅ {'Bugun bajarilgan' if lang == 'uz' else 'Выполнено сегодня'}: <b>{stats.get('today_completed', 0)}</b>\n"
                f"⏳ {'Kutilayotgan' if lang == 'uz' else 'Ожидающие'}: <b>{stats.get('pending_orders', 0)}</b>\n"
                f"👨‍🔧 {'Faol texniklar' if lang == 'uz' else 'Активные техники'}: <b>{stats.get('active_technicians', 0)}</b>\n\n"
                f"{'Kerakli bo\'limni tanlang:' if lang == 'uz' else 'Выберите нужный раздел:'}"
            )
            await message.answer(
                welcome_text,
                reply_markup=get_admin_main_menu(lang)
            )
            await state.set_state(AdminStates.main_menu)
            
            logger.info(f"Admin panel shown to user {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"Error in admin_start: {e}")
            try:
                lang = await get_user_lang(message.from_user.id)
            except:
                lang = 'ru'
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(['🏠 Bosh sahifa', '🏠 Главная']))
    @admin_only
    async def admin_home(message: Message, state: FSMContext):
        """Return to admin home"""
        await admin_start(message, state)

    @router.message(F.text.in_(['📊 Statistika', '📊 Статистика']))
    @admin_only
    async def admin_dashboard(message: Message):
        """Show admin dashboard"""
        try:
            logger.info(f"Admin dashboard requested by user {message.from_user.id}")
            
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get detailed dashboard stats
            try:
                stats = await get_admin_dashboard_stats()
            except Exception as e:
                logger.error(f"Error getting dashboard stats: {e}")
                stats = {'users_by_role': [], 'orders_by_status': []}
            
            if lang == 'uz':
                dashboard_text = f"📊 <b>Admin Dashboard</b>\n\n👥 <b>Foydalanuvchilar:</b>\n"
                
                for role_stat in stats.get('users_by_role', []):
                    role_name = {
                        'client': 'Mijozlar',
                        'technician': 'Texniklar', 
                        'manager': 'Menejerlar',
                        'admin': 'Adminlar',
                        'call_center': 'Call Center',
                        'controller': 'Kontrolyorlar',
                        'warehouse': 'Sklad'
                    }.get(role_stat['role'], role_stat['role'])
                    dashboard_text += f"• {role_name}: <b>{role_stat['count']}</b>\n"
                
                dashboard_text += f"\n📋 <b>Zayavkalar:</b>\n"
                for status_stat in stats.get('orders_by_status', []):
                    status_name = {
                        'new': '🆕 Yangi',
                        'pending': '⏳ Kutilmoqda',
                        'assigned': '👨‍🔧 Tayinlangan',
                        'in_progress': '🔄 Jarayonda',
                        'completed': '✅ Bajarilgan',
                        'cancelled': '❌ Bekor qilingan'
                    }.get(status_stat['status'], status_stat['status'])
                    dashboard_text += f"• {status_name}: <b>{status_stat['count']}</b>\n"
            else:
                dashboard_text = f"📊 <b>Панель администратора</b>\n\n👥 <b>Пользователи:</b>\n"
                
                for role_stat in stats.get('users_by_role', []):
                    role_name = {
                        'client': 'Клиенты',
                        'technician': 'Техники',
                        'manager': 'Менеджеры', 
                        'admin': 'Администраторы',
                        'call_center': 'Колл-центр',
                        'controller': 'Контроллеры',
                        'warehouse': 'Склад'
                    }.get(role_stat['role'], role_stat['role'])
                    dashboard_text += f"• {role_name}: <b>{role_stat['count']}</b>\n"
                
                dashboard_text += f"\n📋 <b>Заявки:</b>\n"
                for status_stat in stats.get('orders_by_status', []):
                    status_name = {
                        'new': '🆕 Новые',
                        'pending': '⏳ Ожидающие',
                        'assigned': '👨‍🔧 Назначенные',
                        'in_progress': '🔄 В процессе',
                        'completed': '✅ Выполненные',
                        'cancelled': '❌ Отмененные'
                    }.get(status_stat['status'], status_stat['status'])
                    dashboard_text += f"• {status_name}: <b>{status_stat['count']}</b>\n"
            
            await message.answer(dashboard_text)
            logger.info(f"Admin dashboard shown to user {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"Error showing admin dashboard: {e}")
            try:
                lang = await get_user_lang(message.from_user.id)
            except:
                lang = 'ru'
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(['ℹ️ Yordam', 'ℹ️ Помощь']))
    @admin_only
    async def admin_help(message: Message):
        """Show admin help"""
        try:
            logger.info(f"Admin help requested by user {message.from_user.id}")
            
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            if lang == 'uz':
                help_text = (
                    f"ℹ️ <b>Admin Panel Yordami</b>\n\n"
                    f"📋 <b>Asosiy funksiyalar:</b>\n"
                    f"• 👥 Foydalanuvchilar - foydalanuvchilarni boshqarish\n"
                    f"• 📝 Zayavkalar - zayavkalarni ko'rish va boshqarish\n"
                    f"• 📊 Statistika - tizim statistikasini ko'rish\n"
                    f"• ⚙️ Sozlamalar - tizim sozlamalarini o'zgartirish\n\n"
                    f"🔧 <b>Foydalanuvchi boshqaruvi:</b>\n"
                    f"• Rol o'zgartirish\n"
                    f"• Bloklash/blokdan chiqarish\n"
                    f"• Qidirish (ID, telefon, ism bo'yicha)\n\n"
                    f"📋 <b>Zayavka boshqaruvi:</b>\n"
                    f"• Status o'zgartirish\n"
                    f"• Texnik tayinlash\n"
                    f"• Filtrlash va qidirish\n\n"
                    f"📞 <b>Yordam uchun:</b> @support"
                )
            else:
                help_text = (
                    f"ℹ️ <b>Помощь по панели администратора</b>\n\n"
                    f"📋 <b>Основные функции:</b>\n"
                    f"• 👥 Пользователи - управление пользователями\n"
                    f"• 📝 Заявки - просмотр и управление заявками\n"
                    f"• 📊 Статистика - просмотр статистики системы\n"
                    f"• ⚙️ Настройки - изменение настроек системы\n\n"
                    f"🔧 <b>Управление пользователями:</b>\n"
                    f"• Изменение роли\n"
                    f"• Блокировка/разблокировка\n"
                    f"• Поиск (по ID, телефону, имени)\n\n"
                    f"📋 <b>Управление заявками:</b>\n"
                    f"• Изменение статуса\n"
                    f"• Назначение техника\n"
                    f"• Фильтрация и поиск\n\n"
                    f"📞 <b>Для помощи:</b> @support"
                )
            
            await message.answer(help_text)
            logger.info(f"Admin help shown to user {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"Error showing admin help: {e}")
            try:
                lang = await get_user_lang(message.from_user.id)
            except:
                lang = 'ru'
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    # Test handler without decorator
    @router.message(F.text == '/test_admin')
    async def test_admin(message: Message):
        """Test admin access without decorator"""
        try:
            from config import config
            user_id = message.from_user.id
            
            if config.is_admin(user_id):
                await message.answer("✅ Admin access confirmed!")
            else:
                await message.answer(f"❌ Not admin. Your ID: {user_id}")
                
        except Exception as e:
            await message.answer(f"Error: {str(e)}")

    return router