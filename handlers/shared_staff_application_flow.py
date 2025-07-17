"""
Shared Staff Application Creation Flow Handler

This module contains shared handlers for application creation flow that are
common across all staff roles (Manager, Junior Manager, Controller, Call Center).
These handlers manage the application form filling, confirmation, and submission process.
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Dict, Any, Optional

from database.base_queries import get_user_by_telegram_id, get_user_lang
from handlers.staff_application_creation import RoleBasedApplicationHandler
from states.staff_application_states import StaffApplicationStates
from utils.logger import setup_module_logger
from utils.inline_cleanup import cleanup_user_inline_messages

logger = setup_module_logger("shared_staff_application_flow")


def get_shared_staff_application_flow_router():
    """Get router for shared staff application creation flow handlers"""
    router = Router()
    
    # Initialize the role-based application handler
    app_handler = RoleBasedApplicationHandler()
    
    # Client confirmation handlers (shared across all roles)
    @router.callback_query(F.data.in_([
        "confirm_client_selection", "jm_confirm_client_selection", 
        "ctrl_confirm_client_selection", "cc_confirm_client_selection"
    ]))
    async def confirm_client_selection(callback: CallbackQuery, state: FSMContext):
        """Handle client selection confirmation for all roles"""
        try:
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            
            # Get FSM data
            data = await state.get_data()
            selected_client = data.get('selected_client')
            application_type = data.get('application_type')
            
            if not selected_client or not application_type:
                error_text = "Ma'lumotlar topilmadi" if lang == 'uz' else "Данные не найдены"
                await callback.answer(error_text, show_alert=True)
                return
            
            # Move to application description entry
            await state.set_state(StaffApplicationStates.entering_application_description)
            
            # Create prompt based on application type
            if application_type == 'connection_request':
                prompt_text = (
                    f"🔌 Ulanish arizasi - {selected_client['full_name']}\n\n"
                    f"Ariza tavsifini kiriting:\n\n"
                    f"Masalan:\n"
                    f"• Internet ulanishini o'rnatish\n"
                    f"• Yangi tarif rejasiga o'tish\n"
                    f"• Qo'shimcha xizmatlar ulash\n\n"
                    f"Batafsil tavsif yozing:"
                ) if lang == 'uz' else (
                    f"🔌 Заявка на подключение - {selected_client['full_name']}\n\n"
                    f"Введите описание заявки:\n\n"
                    f"Например:\n"
                    f"• Установка интернет-подключения\n"
                    f"• Переход на новый тарифный план\n"
                    f"• Подключение дополнительных услуг\n\n"
                    f"Напишите подробное описание:"
                )
            else:  # technical_service
                prompt_text = (
                    f"🔧 Texnik xizmat arizasi - {selected_client['full_name']}\n\n"
                    f"Texnik muammo tavsifini kiriting:\n\n"
                    f"Masalan:\n"
                    f"• Internet aloqasi uziladi\n"
                    f"• Sekin internet tezligi\n"
                    f"• Jihozlar ishlamayapti\n"
                    f"• Kabel shikastlangan\n\n"
                    f"Muammo haqida batafsil yozing:"
                ) if lang == 'uz' else (
                    f"🔧 Заявка на техническое обслуживание - {selected_client['full_name']}\n\n"
                    f"Введите описание технической проблемы:\n\n"
                    f"Например:\n"
                    f"• Пропадает интернет-соединение\n"
                    f"• Медленная скорость интернета\n"
                    f"• Не работает оборудование\n"
                    f"• Поврежден кабель\n\n"
                    f"Опишите проблему подробно:"
                )
            
            await callback.message.edit_text(prompt_text, reply_markup=None)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in confirm_client_selection: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    @router.callback_query(F.data.in_([
        "search_another_client", "jm_search_another_client", 
        "ctrl_search_another_client", "cc_search_another_client"
    ]))
    async def search_another_client(callback: CallbackQuery, state: FSMContext):
        """Handle search another client for all roles"""
        try:
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            
            # Reset to client search method selection
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
            prompt_text = (
                "🔍 Boshqa mijoz qidirish\n\n"
                "Mijozni qanday qidirishni xohlaysiz?"
            ) if lang == 'uz' else (
                "🔍 Поиск другого клиента\n\n"
                "Как вы хотите найти клиента?"
            )
            
            # Create role-specific callback prefixes
            role = user['role']
            prefix_map = {
                'manager': '',
                'junior_manager': 'jm_',
                'controller': 'ctrl_',
                'call_center': 'cc_'
            }
            prefix = prefix_map.get(role, '')
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Telefon" if lang == 'uz' else "📱 Телефон",
                        callback_data=f"{prefix}client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data=f"{prefix}client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data=f"{prefix}client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data=f"{prefix}client_search_new"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data=f"{prefix}cancel_application_creation"
                    )
                ]
            ])
            
            await callback.message.edit_text(prompt_text, reply_markup=keyboard)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in search_another_client: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    # Application description handler
    @router.message(StaffApplicationStates.entering_application_description)
    async def handle_application_description(message: Message, state: FSMContext):
        """Handle application description input for all roles"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                return
            
            lang = user.get('language', 'uz')
            description = message.text.strip()
            
            # Validate description
            if len(description) < 10:
                error_text = (
                    "❌ Tavsif juda qisqa. Kamida 10 ta belgi bo'lishi kerak.\n"
                    "Iltimos, batafsil tavsif yozing."
                ) if lang == 'uz' else (
                    "❌ Описание слишком короткое. Должно быть минимум 10 символов.\n"
                    "Пожалуйста, напишите подробное описание."
                )
                await message.answer(error_text)
                return
            
            if len(description) > 1000:
                error_text = (
                    "❌ Tavsif juda uzun. Maksimal 1000 ta belgi bo'lishi kerak."
                ) if lang == 'uz' else (
                    "❌ Описание слишком длинное. Максимум 1000 символов."
                )
                await message.answer(error_text)
                return
            
            # Store description and move to address entry
            await state.update_data(application_description=description)
            await state.set_state(StaffApplicationStates.entering_application_address)
            
            # Get client info for context
            data = await state.get_data()
            selected_client = data.get('selected_client', {})
            
            address_prompt = (
                f"📍 Xizmat manzilini kiriting:\n\n"
                f"Mijoz: {selected_client.get('full_name', 'Noma\'lum')}\n"
                f"Tavsif: {description[:50]}{'...' if len(description) > 50 else ''}\n\n"
                f"Xizmat ko'rsatiladigan aniq manzilni kiriting:\n"
                f"(Ko'cha, uy raqami, kvartira va boshqa ma'lumotlar)"
            ) if lang == 'uz' else (
                f"📍 Введите адрес обслуживания:\n\n"
                f"Клиент: {selected_client.get('full_name', 'Неизвестно')}\n"
                f"Описание: {description[:50]}{'...' if len(description) > 50 else ''}\n\n"
                f"Введите точный адрес обслуживания:\n"
                f"(Улица, номер дома, квартира и другие данные)"
            )
            
            await message.answer(address_prompt)
            
        except Exception as e:
            logger.error(f"Error in handle_application_description: {e}", exc_info=True)
    
    # Application address handler
    @router.message(StaffApplicationStates.entering_application_address)
    async def handle_application_address(message: Message, state: FSMContext):
        """Handle application address input for all roles"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                return
            
            lang = user.get('language', 'uz')
            address = message.text.strip()
            
            # Validate address
            if len(address) < 5:
                error_text = (
                    "❌ Manzil juda qisqa. Kamida 5 ta belgi bo'lishi kerak.\n"
                    "Iltimos, to'liq manzilni kiriting."
                ) if lang == 'uz' else (
                    "❌ Адрес слишком короткий. Должно быть минимум 5 символов.\n"
                    "Пожалуйста, введите полный адрес."
                )
                await message.answer(error_text)
                return
            
            # Store address and move to confirmation
            await state.update_data(application_address=address)
            await state.set_state(StaffApplicationStates.reviewing_application_details)
            
            # Get all data for review
            data = await state.get_data()
            selected_client = data.get('selected_client', {})
            application_type = data.get('application_type', '')
            description = data.get('application_description', '')
            creator_context = data.get('creator_context', {})
            
            # Create application type display
            app_type_display = (
                "🔌 Ulanish arizasi" if application_type == 'connection_request' 
                else "🔧 Texnik xizmat arizasi"
            ) if lang == 'uz' else (
                "🔌 Заявка на подключение" if application_type == 'connection_request' 
                else "🔧 Заявка на техническое обслуживание"
            )
            
            # Create review text
            review_text = (
                f"📋 Ariza ma'lumotlarini ko'rib chiqing:\n\n"
                f"📝 Turi: {app_type_display}\n"
                f"👤 Mijoz: {selected_client.get('full_name', 'Noma\'lum')}\n"
                f"📱 Telefon: {selected_client.get('phone', 'Noma\'lum')}\n"
                f"📍 Manzil: {address}\n"
                f"📄 Tavsif: {description}\n"
                f"👨‍💼 Yaratuvchi: {creator_context.get('creator_role', 'Noma\'lum').title()}\n\n"
                f"Ma'lumotlar to'g'rimi?"
            ) if lang == 'uz' else (
                f"📋 Просмотрите данные заявки:\n\n"
                f"📝 Тип: {app_type_display}\n"
                f"👤 Клиент: {selected_client.get('full_name', 'Неизвестно')}\n"
                f"📱 Телефон: {selected_client.get('phone', 'Неизвестно')}\n"
                f"📍 Адрес: {address}\n"
                f"📄 Описание: {description}\n"
                f"👨‍💼 Создатель: {creator_context.get('creator_role', 'Неизвестно').title()}\n\n"
                f"Данные корректны?"
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Ha, yuborish" if lang == 'uz' else "✅ Да, отправить",
                        callback_data="submit_application"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ Tavsifni o'zgartirish" if lang == 'uz' else "✏️ Изменить описание",
                        callback_data="edit_description"
                    ),
                    InlineKeyboardButton(
                        text="📍 Manzilni o'zgartirish" if lang == 'uz' else "📍 Изменить адрес",
                        callback_data="edit_address"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👤 Mijozni o'zgartirish" if lang == 'uz' else "👤 Изменить клиента",
                        callback_data="edit_client"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data="cancel_application_final"
                    )
                ]
            ])
            
            await message.answer(review_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in handle_application_address: {e}", exc_info=True)
    
    # Application submission handler
    @router.callback_query(F.data == "submit_application")
    async def submit_application(callback: CallbackQuery, state: FSMContext):
        """Handle application submission for all roles"""
        try:
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            
            # Get all data
            data = await state.get_data()
            selected_client = data.get('selected_client', {})
            application_type = data.get('application_type', '')
            description = data.get('application_description', '')
            address = data.get('application_address', '')
            creator_context = data.get('creator_context', {})
            
            # Set processing state
            await state.set_state(StaffApplicationStates.processing_submission)
            
            processing_text = (
                "⏳ Ariza yuborilmoqda...\n\n"
                "Iltimos, kuting."
            ) if lang == 'uz' else (
                "⏳ Отправка заявки...\n\n"
                "Пожалуйста, подождите."
            )
            
            await callback.message.edit_text(processing_text, reply_markup=None)
            
            # Prepare application data
            application_data = {
                'client_data': {
                    'phone': selected_client.get('phone', ''),
                    'full_name': selected_client.get('full_name', ''),
                    'address': selected_client.get('address', ''),
                    'additional_info': ''
                },
                'application_data': {
                    'description': description,
                    'location': address,
                    'priority': 'medium',
                    'additional_notes': f"Created by {creator_context.get('creator_role', 'staff')}"
                }
            }
            
            # Process and submit application
            form_result = await app_handler.process_application_form(application_data, creator_context)
            
            if not form_result['success']:
                error_text = (
                    f"❌ Ariza yaratishda xatolik:\n{form_result.get('error_message', 'Noma\'lum xatolik')}"
                ) if lang == 'uz' else (
                    f"❌ Ошибка при создании заявки:\n{form_result.get('error_message', 'Неизвестная ошибка')}"
                )
                await callback.message.edit_text(error_text)
                return
            
            # Submit application
            submit_result = await app_handler.validate_and_submit(
                form_result['processed_data'], creator_context
            )
            
            if submit_result['success']:
                await state.set_state(StaffApplicationStates.application_submitted)
                
                success_text = (
                    f"✅ Ariza muvaffaqiyatli yaratildi!\n\n"
                    f"📋 Ariza ID: {submit_result['application_id']}\n"
                    f"👤 Mijoz: {selected_client.get('full_name', '')}\n"
                    f"📱 Telefon: {selected_client.get('phone', '')}\n"
                    f"📍 Manzil: {address}\n\n"
                    f"Mijozga bildirishnoma yuborildi.\n"
                    f"Ariza ish jarayoniga kiritildi."
                ) if lang == 'uz' else (
                    f"✅ Заявка успешно создана!\n\n"
                    f"📋 ID заявки: {submit_result['application_id']}\n"
                    f"👤 Клиент: {selected_client.get('full_name', '')}\n"
                    f"📱 Телефон: {selected_client.get('phone', '')}\n"
                    f"📍 Адрес: {address}\n\n"
                    f"Клиенту отправлено уведомление.\n"
                    f"Заявка передана в работу."
                )
                
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🆕 Yangi ariza yaratish" if lang == 'uz' else "🆕 Создать новую заявку",
                            callback_data="create_another_application"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🏠 Asosiy menyu" if lang == 'uz' else "🏠 Главное меню",
                            callback_data="return_to_main_menu"
                        )
                    ]
                ])
                
                await callback.message.edit_text(success_text, reply_markup=keyboard)
                
            else:
                error_text = (
                    f"❌ Ariza yuborishda xatolik:\n{submit_result.get('error_message', 'Noma\'lum xatolik')}"
                ) if lang == 'uz' else (
                    f"❌ Ошибка при отправке заявки:\n{submit_result.get('error_message', 'Неизвестная ошибка')}"
                )
                await callback.message.edit_text(error_text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in submit_application: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    # Edit handlers
    @router.callback_query(F.data == "edit_description")
    async def edit_description(callback: CallbackQuery, state: FSMContext):
        """Handle edit description request"""
        try:
            await state.set_state(StaffApplicationStates.entering_application_description)
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz') if user else 'uz'
            
            edit_text = (
                "✏️ Ariza tavsifini qayta kiriting:"
            ) if lang == 'uz' else (
                "✏️ Введите описание заявки заново:"
            )
            
            await callback.message.edit_text(edit_text, reply_markup=None)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in edit_description: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    @router.callback_query(F.data == "edit_address")
    async def edit_address(callback: CallbackQuery, state: FSMContext):
        """Handle edit address request"""
        try:
            await state.set_state(StaffApplicationStates.entering_application_address)
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz') if user else 'uz'
            
            edit_text = (
                "📍 Xizmat manzilini qayta kiriting:"
            ) if lang == 'uz' else (
                "📍 Введите адрес обслуживания заново:"
            )
            
            await callback.message.edit_text(edit_text, reply_markup=None)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in edit_address: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    @router.callback_query(F.data == "edit_client")
    async def edit_client(callback: CallbackQuery, state: FSMContext):
        """Handle edit client request"""
        try:
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz') if user else 'uz'
            
            # Get role-specific prefix
            role = user['role'] if user else 'manager'
            prefix_map = {
                'manager': '',
                'junior_manager': 'jm_',
                'controller': 'ctrl_',
                'call_center': 'cc_'
            }
            prefix = prefix_map.get(role, '')
            
            edit_text = (
                "👤 Boshqa mijozni tanlang:"
            ) if lang == 'uz' else (
                "👤 Выберите другого клиента:"
            )
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Telefon" if lang == 'uz' else "📱 Телефон",
                        callback_data=f"{prefix}client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data=f"{prefix}client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data=f"{prefix}client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data=f"{prefix}client_search_new"
                    )
                ]
            ])
            
            await callback.message.edit_text(edit_text, reply_markup=keyboard)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in edit_client: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    # Final handlers
    @router.callback_query(F.data == "create_another_application")
    async def create_another_application(callback: CallbackQuery, state: FSMContext):
        """Handle create another application request"""
        try:
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            
            # Clear state and start over
            await state.clear()
            
            restart_text = (
                "🆕 Yangi ariza yaratish\n\n"
                "Qaysi turdagi ariza yaratmoqchisiz?"
            ) if lang == 'uz' else (
                "🆕 Создание новой заявки\n\n"
                "Какой тип заявки вы хотите создать?"
            )
            
            # Get role-specific prefix
            role = user['role']
            prefix_map = {
                'manager': '',
                'junior_manager': 'jm_',
                'controller': 'ctrl_',
                'call_center': 'cc_'
            }
            prefix = prefix_map.get(role, '')
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            buttons = [
                [
                    InlineKeyboardButton(
                        text="🔌 Ulanish arizasi" if lang == 'uz' else "🔌 Заявка на подключение",
                        callback_data=f"{prefix}start_connection_request"
                    )
                ]
            ]
            
            # Add technical service button for roles that can create it
            if role in ['manager', 'controller', 'call_center']:
                buttons.append([
                    InlineKeyboardButton(
                        text="🔧 Texnik xizmat" if lang == 'uz' else "🔧 Техническое обслуживание",
                        callback_data=f"{prefix}start_technical_service"
                    )
                ])
            
            buttons.append([
                InlineKeyboardButton(
                    text="🏠 Asosiy menyu" if lang == 'uz' else "🏠 Главное меню",
                    callback_data="return_to_main_menu"
                )
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await callback.message.edit_text(restart_text, reply_markup=keyboard)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in create_another_application: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    @router.callback_query(F.data.in_(["cancel_application_final", "return_to_main_menu"]))
    async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
        """Handle return to main menu"""
        try:
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            await state.clear()
            
            return_text = (
                "🏠 Asosiy menyuga qaytdingiz."
            ) if lang == 'uz' else (
                "🏠 Вы вернулись в главное меню."
            )
            
            await callback.message.edit_text(return_text, reply_markup=None)
            
            # Send appropriate main menu based on role
            role = user['role']
            if role == 'manager':
                from keyboards.manager_buttons import get_manager_main_keyboard
                keyboard = get_manager_main_keyboard(lang)
            elif role == 'junior_manager':
                from keyboards.junior_manager_buttons import get_junior_manager_main_keyboard
                keyboard = get_junior_manager_main_keyboard(lang)
            elif role == 'controller':
                from keyboards.controllers_buttons import controllers_main_menu
                keyboard = controllers_main_menu(lang)
            elif role == 'call_center':
                from keyboards.call_center_buttons import call_center_main_menu_reply
                keyboard = call_center_main_menu_reply(lang)
            else:
                keyboard = None
            
            if keyboard:
                main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
                await callback.message.answer(main_menu_text, reply_markup=keyboard)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in return_to_main_menu: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)
    
    return router