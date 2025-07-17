"""
Call Center Staff Application Creation Handler

This module implements application creation handlers for Call Center role,
allowing call center operators to create both connection requests and technical service
applications on behalf of clients during phone calls.
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Dict, Any, Optional

from database.base_queries import get_user_by_telegram_id, get_user_lang
from handlers.staff_application_creation import RoleBasedApplicationHandler
from states.staff_application_states import StaffApplicationStates
from keyboards.call_center_buttons import call_center_main_menu_reply
from utils.logger import setup_module_logger
from utils.role_router import get_role_router
from utils.inline_cleanup import cleanup_user_inline_messages

logger = setup_module_logger("call_center.staff_application_creation")


def get_call_center_staff_application_router():
    """Get router for call center staff application creation handlers"""
    router = get_role_router("call_center")
    
    # Initialize the role-based application handler
    app_handler = RoleBasedApplicationHandler()
    
    @router.message(F.text.in_(["🔌 Ulanish arizasi yaratish", "🔌 Создать заявку на подключение"]))
    async def call_center_create_connection_request(message: Message, state: FSMContext):
        """Handle call center creating connection request for client"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'call_center':
                lang = user.get('language', 'uz') if user else 'uz'
                error_text = "Sizda call center huquqi yo'q." if lang == 'uz' else "У вас нет прав call-центра."
                await message.answer(error_text)
                return
            
            lang = user.get('language', 'uz')
            logger.info(f"Call Center {user['id']} starting connection request creation")
            
            # Start application creation process
            result = await app_handler.start_application_creation(
                creator_role='call_center',
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
            await state.update_data(
                creator_context=result['creator_context'],
                application_type='connection_request'
            )
            
            # Set initial state and prompt for client selection
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
            prompt_text = (
                "📞 Call Center: Ulanish arizasi yaratish\n\n"
                "Mijoz bilan telefon orqali gaplashayotgan vaqtda ariza yaratish.\n\n"
                "Mijozni qanday qidirishni xohlaysiz?\n\n"
                "📱 Telefon raqami bo'yicha\n"
                "👤 Ism bo'yicha\n"
                "🆔 Mijoz ID bo'yicha\n"
                "➕ Yangi mijoz yaratish"
            ) if lang == 'uz' else (
                "📞 Call-центр: Создание заявки на подключение\n\n"
                "Создание заявки во время разговора с клиентом по телефону.\n\n"
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
                        callback_data="cc_client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data="cc_client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data="cc_client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data="cc_client_search_new"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data="cc_cancel_application_creation"
                    )
                ]
            ])
            
            await message.answer(prompt_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in call_center_create_connection_request: {e}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
    
    @router.message(F.text.in_(["🔧 Texnik xizmat yaratish", "🔧 Создать техническую заявку"]))
    async def call_center_create_technical_service(message: Message, state: FSMContext):
        """Handle call center creating technical service request for client"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'call_center':
                lang = user.get('language', 'uz') if user else 'uz'
                error_text = "Sizda call center huquqi yo'q." if lang == 'uz' else "У вас нет прав call-центра."
                await message.answer(error_text)
                return
            
            lang = user.get('language', 'uz')
            logger.info(f"Call Center {user['id']} starting technical service creation")
            
            # Start application creation process
            result = await app_handler.start_application_creation(
                creator_role='call_center',
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
            await state.update_data(
                creator_context=result['creator_context'],
                application_type='technical_service'
            )
            
            # Set initial state and prompt for client selection
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
            prompt_text = (
                "📞 Call Center: Texnik xizmat arizasi yaratish\n\n"
                "Mijoz bilan telefon orqali gaplashayotgan vaqtda texnik muammo uchun ariza yaratish.\n\n"
                "Mijozni qanday qidirishni xohlaysiz?\n\n"
                "📱 Telefon raqami bo'yicha\n"
                "👤 Ism bo'yicha\n"
                "🆔 Mijoz ID bo'yicha\n"
                "➕ Yangi mijoz yaratish"
            ) if lang == 'uz' else (
                "📞 Call-центр: Создание заявки на техническое обслуживание\n\n"
                "Создание заявки на техническую проблему во время разговора с клиентом.\n\n"
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
                        callback_data="cc_client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data="cc_client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data="cc_client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data="cc_client_search_new"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data="cc_cancel_application_creation"
                    )
                ]
            ])
            
            await message.answer(prompt_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in call_center_create_technical_service: {e}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
    
    @router.callback_query(F.data.startswith("cc_client_search_"))
    async def handle_call_center_client_search_method(callback: CallbackQuery, state: FSMContext):
        """Handle client search method selection for call center"""
        try:
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != 'call_center':
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            search_method = callback.data.split("_")[-1]  # phone, name, id, new
            
            # Update FSM data with search method
            await state.update_data(client_search_method=search_method)
            
            if search_method == "phone":
                await state.set_state(StaffApplicationStates.entering_client_phone)
                prompt_text = (
                    "📱 Mijoz telefon raqamini kiriting:\n\n"
                    "Masalan: +998901234567\n\n"
                    "💡 Maslahat: Mijoz bilan gaplashayotgan bo'lsangiz, "
                    "uning telefon raqamini so'rang."
                ) if lang == 'uz' else (
                    "📱 Введите номер телефона клиента:\n\n"
                    "Например: +998901234567\n\n"
                    "💡 Совет: Если вы разговариваете с клиентом, "
                    "попросите его номер телефона."
                )
                
            elif search_method == "name":
                await state.set_state(StaffApplicationStates.entering_client_name)
                prompt_text = (
                    "👤 Mijoz ismini kiriting:\n\n"
                    "To'liq ism va familiyani kiriting\n\n"
                    "💡 Maslahat: Mijozdan to'liq ismini so'rang."
                ) if lang == 'uz' else (
                    "👤 Введите имя клиента:\n\n"
                    "Введите полное имя и фамилию\n\n"
                    "💡 Совет: Попросите у клиента полное имя."
                )
                
            elif search_method == "id":
                await state.set_state(StaffApplicationStates.entering_client_id)
                prompt_text = (
                    "🆔 Mijoz ID raqamini kiriting:\n\n"
                    "💡 Maslahat: Agar mijozda ID raqami bo'lsa, uni so'rang."
                ) if lang == 'uz' else (
                    "🆔 Введите ID клиента:\n\n"
                    "💡 Совет: Если у клиента есть ID номер, попросите его."
                )
                
            elif search_method == "new":
                await state.set_state(StaffApplicationStates.creating_new_client)
                prompt_text = (
                    "➕ Yangi mijoz yaratish\n\n"
                    "Yangi mijoz ma'lumotlarini kiritishni boshlaymiz.\n"
                    "Mijoz bilan gaplashib, uning ma'lumotlarini oling.\n\n"
                    "Birinchi navbatda, mijoz ismini kiriting:"
                ) if lang == 'uz' else (
                    "➕ Создание нового клиента\n\n"
                    "Начинаем ввод данных нового клиента.\n"
                    "Поговорите с клиентом и получите его данные.\n\n"
                    "Сначала введите имя клиента:"
                )
                await state.set_state(StaffApplicationStates.entering_new_client_name)
            
            await callback.message.edit_text(prompt_text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in handle_call_center_client_search_method: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    @router.callback_query(F.data == "cc_cancel_application_creation")
    async def call_center_cancel_application_creation(callback: CallbackQuery, state: FSMContext):
        """Cancel application creation and return to main menu for call center"""
        try:
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != 'call_center':
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            await state.clear()
            
            cancel_text = (
                "❌ Ariza yaratish bekor qilindi.\n\n"
                "Asosiy menyuga qaytdingiz.\n\n"
                "💡 Mijoz bilan gaplashishni davom ettiring."
            ) if lang == 'uz' else (
                "❌ Создание заявки отменено.\n\n"
                "Вы вернулись в главное меню.\n\n"
                "💡 Продолжайте разговор с клиентом."
            )
            
            await callback.message.edit_text(
                cancel_text,
                reply_markup=None
            )
            
            # Send main menu
            main_menu_text = "Call Center - Asosiy menyu" if lang == 'uz' else "Call-центр - Главное меню"
            await callback.message.answer(
                main_menu_text,
                reply_markup=call_center_main_menu_reply(lang)
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in call_center_cancel_application_creation: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    # Client search input handlers for call center
    @router.message(StaffApplicationStates.entering_client_phone)
    async def handle_call_center_client_phone_input(message: Message, state: FSMContext):
        """Handle client phone number input for call center"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'call_center':
                return
            
            lang = user.get('language', 'uz')
            phone = message.text.strip()
            
            # Basic phone validation
            if not phone.startswith('+') or len(phone) < 10:
                error_text = (
                    "❌ Telefon raqami noto'g'ri formatda.\n"
                    "Iltimos, +998901234567 formatida kiriting.\n\n"
                    "💡 Mijozdan to'g'ri formatda raqam so'rang."
                ) if lang == 'uz' else (
                    "❌ Неверный формат номера телефона.\n"
                    "Пожалуйста, введите в формате +998901234567.\n\n"
                    "💡 Попросите у клиента номер в правильном формате."
                )
                await message.answer(error_text)
                return
            
            # Store phone and search for client
            await state.update_data(client_phone=phone)
            await state.set_state(StaffApplicationStates.searching_client)
            
            search_text = (
                f"🔍 Telefon raqami {phone} bo'yicha mijozni qidiryapman...\n\n"
                f"💡 Mijoz bilan gaplashishni davom ettiring."
            ) if lang == 'uz' else (
                f"🔍 Поиск клиента по номеру {phone}...\n\n"
                f"💡 Продолжайте разговор с клиентом."
            )
            
            search_msg = await message.answer(search_text)
            
            # For demo purposes, simulate found client
            await _simulate_call_center_client_found(message, state, search_msg, phone, lang)
            
        except Exception as e:
            logger.error(f"Error in handle_call_center_client_phone_input: {e}", exc_info=True)
    
    @router.message(StaffApplicationStates.entering_client_name)
    async def handle_call_center_client_name_input(message: Message, state: FSMContext):
        """Handle client name input for call center"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'call_center':
                return
            
            lang = user.get('language', 'uz')
            name = message.text.strip()
            
            # Basic name validation
            if len(name) < 2:
                error_text = (
                    "❌ Ism juda qisqa. Kamida 2 ta harf bo'lishi kerak.\n\n"
                    "💡 Mijozdan to'liq ismini so'rang."
                ) if lang == 'uz' else (
                    "❌ Имя слишком короткое. Должно быть минимум 2 символа.\n\n"
                    "💡 Попросите у клиента полное имя."
                )
                await message.answer(error_text)
                return
            
            # Store name and search for client
            await state.update_data(client_name=name)
            await state.set_state(StaffApplicationStates.searching_client)
            
            search_text = (
                f"🔍 '{name}' ismli mijozni qidiryapman...\n\n"
                f"💡 Mijoz bilan gaplashishni davom ettiring."
            ) if lang == 'uz' else (
                f"🔍 Поиск клиента с именем '{name}'...\n\n"
                f"💡 Продолжайте разговор с клиентом."
            )
            
            search_msg = await message.answer(search_text)
            
            # For demo purposes, simulate found client
            await _simulate_call_center_client_found(message, state, search_msg, name, lang)
            
        except Exception as e:
            logger.error(f"Error in handle_call_center_client_name_input: {e}", exc_info=True)
    
    @router.message(StaffApplicationStates.entering_client_id)
    async def handle_call_center_client_id_input(message: Message, state: FSMContext):
        """Handle client ID input for call center"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'call_center':
                return
            
            lang = user.get('language', 'uz')
            client_id_str = message.text.strip()
            
            # Validate ID is numeric
            try:
                client_id = int(client_id_str)
            except ValueError:
                error_text = (
                    "❌ ID raqam bo'lishi kerak. Masalan: 12345\n\n"
                    "💡 Mijozdan ID raqamini aniq so'rang."
                ) if lang == 'uz' else (
                    "❌ ID должен быть числом. Например: 12345\n\n"
                    "💡 Попросите у клиента точный ID номер."
                )
                await message.answer(error_text)
                return
            
            # Store ID and search for client
            await state.update_data(client_id=client_id)
            await state.set_state(StaffApplicationStates.searching_client)
            
            search_text = (
                f"🔍 ID {client_id} bo'yicha mijozni qidiryapman...\n\n"
                f"💡 Mijoz bilan gaplashishni davom ettiring."
            ) if lang == 'uz' else (
                f"🔍 Поиск клиента с ID {client_id}...\n\n"
                f"💡 Продолжайте разговор с клиентом."
            )
            
            search_msg = await message.answer(search_text)
            
            # For demo purposes, simulate found client
            await _simulate_call_center_client_found(message, state, search_msg, str(client_id), lang)
            
        except Exception as e:
            logger.error(f"Error in handle_call_center_client_id_input: {e}", exc_info=True)
    
    return router


async def _simulate_call_center_client_found(message: Message, state: FSMContext, search_msg: Message, 
                                           search_value: str, lang: str):
    """
    Simulate client found for call center demo purposes.
    In production, this would be replaced with actual database search logic.
    """
    import asyncio
    
    # Simulate search delay
    await asyncio.sleep(1)
    
    # For demo, create a mock client
    mock_client = {
        'id': 12345,
        'full_name': 'Bobur Toshmatov',
        'phone': '+998901234567',
        'address': 'Toshkent, Shayxontohur tumani'
    }
    
    # Store found client
    await state.update_data(selected_client=mock_client)
    await state.set_state(StaffApplicationStates.confirming_client_selection)
    
    # Update search message with found client
    found_text = (
        f"✅ Mijoz topildi!\n\n"
        f"👤 Ism: {mock_client['full_name']}\n"
        f"📱 Telefon: {mock_client['phone']}\n"
        f"📍 Manzil: {mock_client['address']}\n\n"
        f"Bu mijoz uchun ariza yaratishni xohlaysizmi?\n\n"
        f"💡 Mijoz bilan ma'lumotlarni tasdiqlang."
    ) if lang == 'uz' else (
        f"✅ Клиент найден!\n\n"
        f"👤 Имя: {mock_client['full_name']}\n"
        f"📱 Телефон: {mock_client['phone']}\n"
        f"📍 Адрес: {mock_client['address']}\n\n"
        f"Хотите создать заявку для этого клиента?\n\n"
        f"💡 Подтвердите данные с клиентом."
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Ha, davom etish" if lang == 'uz' else "✅ Да, продолжить",
                callback_data="cc_confirm_client_selection"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Boshqa mijoz qidirish" if lang == 'uz' else "🔍 Найти другого клиента",
                callback_data="cc_search_another_client"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                callback_data="cc_cancel_application_creation"
            )
        ]
    ])
    
    await search_msg.edit_text(found_text, reply_markup=keyboard)