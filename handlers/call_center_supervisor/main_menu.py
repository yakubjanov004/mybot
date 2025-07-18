"""
Call Center Supervisor Main Menu Handler

This module implements the main menu handler for Call Center Supervisor role,
including staff application creation functionality with appropriate permissions.
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Dict, Any, Optional

from database.base_queries import get_user_by_telegram_id, get_user_lang
from keyboards.call_center_supervisor_buttons import get_call_center_supervisor_main_menu
from states.call_center import CallCenterSupervisorStates
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.role_router import get_role_router

logger = setup_logger('bot.call_center_supervisor.main_menu')


def get_call_center_supervisor_main_menu_router():
    """Get router for call center supervisor main menu handlers"""
    router = get_role_router("call_center_supervisor")

    @router.message(F.text.in_(["📞 Call Center Supervisor", "📞 Супервайзер колл-центра", "📞 Call Center Nazoratchi"]))
    async def call_center_supervisor_start(message: Message, state: FSMContext):
        """Call center supervisor main menu"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            await state.clear()
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'call_center_supervisor':
                lang = user.get('language', 'uz') if user else 'uz'
                text = "Sizda call center supervisor huquqi yo'q." if lang == 'uz' else "У вас нет прав супервайзера колл-центра."
                await message.answer(text)
                return
            
            lang = user.get('language', 'uz')
            welcome_text = "📞 Call Center Supervisor paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель супервайзера колл-центра!"
            
            await message.answer(
                welcome_text,
                reply_markup=get_call_center_supervisor_main_menu(lang)
            )
            await state.set_state(CallCenterSupervisorStates.main_menu)
            
            logger.info(f"Call Center Supervisor {user['id']} accessed main menu")
            
        except Exception as e:
            logger.error(f"Error in call_center_supervisor_start: {str(e)}", exc_info=True)
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

    @router.message(F.text.in_(["🏠 Bosh menyu", "🏠 Главное меню"]))
    async def call_center_supervisor_main_menu_handler(message: Message, state: FSMContext):
        """Handle call center supervisor main menu button"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'call_center_supervisor':
                return
            
            lang = user.get('language', 'uz')
            main_menu_text = "Bosh menyu" if lang == 'uz' else "Главное меню"
            
            await message.answer(
                main_menu_text,
                reply_markup=get_call_center_supervisor_main_menu(lang)
            )
            if state is not None:
                await state.set_state(CallCenterSupervisorStates.main_menu)
            
        except Exception as e:
            logger.error(f"Error in call center supervisor main menu handler: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    # Staff application creation handlers
    @router.message(F.text.in_(["🔌 Ulanish arizasi yaratish", "🔌 Создать заявку на подключение"]))
    async def call_center_supervisor_create_connection_application(message: Message, state: FSMContext):
        """Handle call center supervisor creating connection application"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'call_center_supervisor':
                lang = user.get('language', 'uz') if user else 'uz'
                error_text = "Sizda call center supervisor huquqi yo'q." if lang == 'uz' else "У вас нет прав супервайзера колл-центра."
                await message.answer(error_text)
                return
            
            lang = user.get('language', 'uz')
            logger.info(f"Call Center Supervisor {user['id']} starting connection request creation")
            
            # Import the staff application creation handler
            from handlers.staff_application_creation import RoleBasedApplicationHandler
            app_handler = RoleBasedApplicationHandler()
            
            # Start application creation process
            result = await app_handler.start_application_creation(
                creator_role='call_center_supervisor',
                creator_id=user['id'],
                application_type='connection_request'
            )
            
            if not result['success']:
                error_msg = result.get('error_message', 'Unknown error')
                if result.get('error_type') == 'permission_denied':
                    error_text = (
                        f"Ruxsat rad etildi: {error_msg}" if lang == 'uz' 
                        else f"Доступ запрещен: {error_msg}"
                    )
                else:
                    error_text = (
                        f"Xatolik yuz berdi: {error_msg}" if lang == 'uz'
                        else f"Произошла ошибка: {error_msg}"
                    )
                await message.answer(error_text)
                return
            
            # Store creator context in FSM data
            from states.staff_application_states import StaffApplicationStates
            await state.update_data(
                creator_context=result['creator_context'],
                application_type='connection_request'
            )
            
            # Set initial state and prompt for client selection
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
            prompt_text = (
                "📞 Call Center Supervisor: Ulanish arizasi yaratish\n\n"
                "Supervisor sifatida mijoz uchun ariza yaratish.\n\n"
                "Mijozni qanday qidirishni xohlaysiz?\n\n"
                "📱 Telefon raqami bo'yicha\n"
                "👤 Ism bo'yicha\n"
                "🆔 Mijoz ID bo'yicha\n"
                "➕ Yangi mijoz yaratish"
            ) if lang == 'uz' else (
                "📞 Супервайзер колл-центра: Создание заявки на подключение\n\n"
                "Создание заявки для клиента в качестве супервайзера.\n\n"
                "Как вы хотите найти клиента?\n\n"
                "📱 По номеру телефона\n"
                "👤 По имени\n"
                "🆔 По ID клиента\n"
                "➕ Создать нового клиента"
            )
            
            # Create inline keyboard for client search options
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Telefon" if lang == 'uz' else "📱 Телефон",
                        callback_data="ccs_client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data="ccs_client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data="ccs_client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data="ccs_client_search_new"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data="ccs_cancel_application_creation"
                    )
                ]
            ])
            
            await message.answer(prompt_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in call_center_supervisor_create_connection_application: {e}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(["🔧 Texnik xizmat yaratish", "🔧 Создать техническую заявку"]))
    async def call_center_supervisor_create_technical_application(message: Message, state: FSMContext):
        """Handle call center supervisor creating technical service application"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'call_center_supervisor':
                lang = user.get('language', 'uz') if user else 'uz'
                error_text = "Sizda call center supervisor huquqi yo'q." if lang == 'uz' else "У вас нет прав супервайзера колл-центра."
                await message.answer(error_text)
                return
            
            lang = user.get('language', 'uz')
            logger.info(f"Call Center Supervisor {user['id']} starting technical service creation")
            
            # Import the staff application creation handler
            from handlers.staff_application_creation import RoleBasedApplicationHandler
            app_handler = RoleBasedApplicationHandler()
            
            # Start application creation process
            result = await app_handler.start_application_creation(
                creator_role='call_center_supervisor',
                creator_id=user['id'],
                application_type='technical_service'
            )
            
            if not result['success']:
                error_msg = result.get('error_message', 'Unknown error')
                if result.get('error_type') == 'permission_denied':
                    error_text = (
                        f"Ruxsat rad etildi: {error_msg}" if lang == 'uz' 
                        else f"Доступ запрещен: {error_msg}"
                    )
                else:
                    error_text = (
                        f"Xatolik yuz berdi: {error_msg}" if lang == 'uz'
                        else f"Произошла ошибка: {error_msg}"
                    )
                await message.answer(error_text)
                return
            
            # Store creator context in FSM data
            from states.staff_application_states import StaffApplicationStates
            await state.update_data(
                creator_context=result['creator_context'],
                application_type='technical_service'
            )
            
            # Set initial state and prompt for client selection
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
            prompt_text = (
                "📞 Call Center Supervisor: Texnik xizmat arizasi yaratish\n\n"
                "Supervisor sifatida mijoz uchun texnik xizmat arizasi yaratish.\n\n"
                "Mijozni qanday qidirishni xohlaysiz?\n\n"
                "📱 Telefon raqami bo'yicha\n"
                "👤 Ism bo'yicha\n"
                "🆔 Mijoz ID bo'yicha\n"
                "➕ Yangi mijoz yaratish"
            ) if lang == 'uz' else (
                "📞 Супервайзер колл-центра: Создание заявки на техническое обслуживание\n\n"
                "Создание заявки на техническое обслуживание для клиента в качестве супервайзера.\n\n"
                "Как вы хотите найти клиента?\n\n"
                "📱 По номеру телефона\n"
                "👤 По имени\n"
                "🆔 По ID клиента\n"
                "➕ Создать нового клиента"
            )
            
            # Create inline keyboard for client search options
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Telefon" if lang == 'uz' else "📱 Телефон",
                        callback_data="ccs_client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data="ccs_client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data="ccs_client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data="ccs_client_search_new"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data="ccs_cancel_application_creation"
                    )
                ]
            ])
            
            await message.answer(prompt_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in call_center_supervisor_create_technical_application: {e}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    return router