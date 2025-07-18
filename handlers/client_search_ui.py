"""
Client Search and Selection UI Handlers
Handles user interactions for client search, selection, and creation during staff application creation
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from database.models import ClientSelectionData, User
from states.staff_application_states import StaffApplicationStates
from keyboards.client_search_buttons import (
    get_client_search_method_keyboard,
    get_client_search_input_keyboard,
    get_client_selection_keyboard,
    get_client_confirmation_keyboard,
    get_new_client_form_keyboard,
    get_new_client_confirmation_keyboard,
    get_client_details_keyboard,
    get_client_edit_keyboard,
    get_client_language_selection_keyboard,
    get_search_error_keyboard,
    get_client_history_keyboard,
    get_validation_error_keyboard,
    format_client_display_text,
    get_search_prompt_text,
    get_new_client_form_prompt
)
from utils.client_selection import (
    ClientManager,
    ClientValidationError,
    ClientSelectionError,
    ClientSearchResult
)
from utils.get_lang import get_user_language
from utils.get_role import get_user_role
from utils.role_permissions import check_staff_application_permission
from database.base_queries import get_user_by_id, update_user_info

logger = logging.getLogger(__name__)
router = Router()

# Initialize client manager
client_manager = ClientManager()


@router.callback_query(F.data == "staff_app_select_client")
async def start_client_selection(callback: CallbackQuery, state: FSMContext):
    """Start client selection process for staff application creation"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        user_role = await get_user_role(user_id)
        
        # Check if user has permission to create applications
        if not await check_staff_application_permission(user_role, "create_application"):
            error_text = "Sizda ariza yaratish huquqi yo'q" if lang == 'uz' else "У вас нет прав на создание заявок"
            await callback.answer(error_text, show_alert=True)
            return
        
        # Show client search method selection
        if lang == 'uz':
            text = "👥 **Mijozni tanlash**\n\nMijozni qanday qidirishni xohlaysiz?"
        else:
            text = "👥 **Выбор клиента**\n\nКак вы хотите найти клиента?"
        
        keyboard = get_client_search_method_keyboard(lang)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.set_state(StaffApplicationStates.selecting_client_search_method)
        
        # Store user context
        await state.update_data({
            'staff_user_id': user_id,
            'staff_role': user_role,
            'language': lang
        })
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error starting client selection: {e}")
        await callback.answer("Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("client_search_"))
async def handle_search_method_selection(callback: CallbackQuery, state: FSMContext):
    """Handle client search method selection"""
    try:
        search_method = callback.data.split("_")[-1]  # phone, name, id
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        if search_method in ['phone', 'name', 'id']:
            # Set up search input state
            prompt_text = get_search_prompt_text(search_method, lang)
            keyboard = get_client_search_input_keyboard(search_method, lang)
            
            await callback.message.edit_text(prompt_text, parse_mode="Markdown")
            await callback.message.answer("Qidirish uchun ma'lumot kiriting:" if lang == 'uz' else "Введите данные для поиска:", reply_markup=keyboard)
            
            # Set appropriate state based on search method
            if search_method == 'phone':
                await state.set_state(StaffApplicationStates.entering_client_phone)
            elif search_method == 'name':
                await state.set_state(StaffApplicationStates.entering_client_name)
            elif search_method == 'id':
                await state.set_state(StaffApplicationStates.entering_client_id)
            
            # Store search method
            await state.update_data({'search_method': search_method})
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error handling search method selection: {e}")
        await callback.answer("Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "client_create_new")
async def start_new_client_creation(callback: CallbackQuery, state: FSMContext):
    """Start new client creation process"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Start new client creation
        prompt_text = get_new_client_form_prompt('name', lang)
        keyboard = get_new_client_form_keyboard('name', lang)
        
        await callback.message.edit_text(prompt_text, parse_mode="Markdown")
        await callback.message.answer("Mijoz ismini kiriting:" if lang == 'uz' else "Введите имя клиента:", reply_markup=keyboard)
        
        await state.set_state(StaffApplicationStates.entering_new_client_name)
        
        # Initialize new client data
        await state.update_data({
            'new_client_data': {},
            'creating_new_client': True
        })
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error starting new client creation: {e}")
        await callback.answer("Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка", show_alert=True)


@router.message(StaffApplicationStates.entering_client_phone)
async def handle_phone_search_input(message: Message, state: FSMContext):
    """Handle phone number search input"""
    try:
        phone_input = message.text.strip()
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Check for cancel/back commands
        if phone_input in ["❌ Bekor qilish", "❌ Отменить"]:
            await cancel_client_selection(message, state)
            return
        elif phone_input in ["◀️ Orqaga", "◀️ Назад"]:
            await back_to_search_method(message, state)
            return
        
        # Perform phone search
        await message.answer("🔍 Qidirilmoqda..." if lang == 'uz' else "🔍 Поиск...")
        
        search_result = await client_manager.search_client('phone', phone_input)
        await handle_search_result(message, state, search_result, 'phone', phone_input)
        
    except Exception as e:
        logger.error(f"Error handling phone search: {e}")
        await message.answer("Qidirish xatosi" if lang == 'uz' else "Ошибка поиска")


@router.message(StaffApplicationStates.entering_client_name)
async def handle_name_search_input(message: Message, state: FSMContext):
    """Handle name search input"""
    try:
        name_input = message.text.strip()
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Check for cancel/back commands
        if name_input in ["❌ Bekor qilish", "❌ Отменить"]:
            await cancel_client_selection(message, state)
            return
        elif name_input in ["◀️ Orqaga", "◀️ Назад"]:
            await back_to_search_method(message, state)
            return
        
        # Validate name input
        if len(name_input) < 2:
            error_text = "Ism kamida 2 ta belgidan iborat bo'lishi kerak" if lang == 'uz' else "Имя должно содержать минимум 2 символа"
            await message.answer(error_text)
            return
        
        # Perform name search
        await message.answer("🔍 Qidirilmoqda..." if lang == 'uz' else "🔍 Поиск...")
        
        search_result = await client_manager.search_client('name', name_input)
        await handle_search_result(message, state, search_result, 'name', name_input)
        
    except Exception as e:
        logger.error(f"Error handling name search: {e}")
        await message.answer("Qidirish xatosi" if lang == 'uz' else "Ошибка поиска")


@router.message(StaffApplicationStates.entering_client_id)
async def handle_id_search_input(message: Message, state: FSMContext):
    """Handle ID search input"""
    try:
        id_input = message.text.strip()
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Check for cancel/back commands
        if id_input in ["❌ Bekor qilish", "❌ Отменить"]:
            await cancel_client_selection(message, state)
            return
        elif id_input in ["◀️ Orqaga", "◀️ Назад"]:
            await back_to_search_method(message, state)
            return
        
        # Validate ID input
        try:
            client_id = int(id_input)
            if client_id <= 0:
                raise ValueError("Invalid ID")
        except ValueError:
            error_text = "ID raqami noto'g'ri. Faqat musbat raqamlar kiriting" if lang == 'uz' else "Неверный ID. Введите только положительные числа"
            await message.answer(error_text)
            return
        
        # Perform ID search
        await message.answer("🔍 Qidirilmoqda..." if lang == 'uz' else "🔍 Поиск...")
        
        search_result = await client_manager.search_client('id', str(client_id))
        await handle_search_result(message, state, search_result, 'id', str(client_id))
        
    except Exception as e:
        logger.error(f"Error handling ID search: {e}")
        await message.answer("Qidirish xatosi" if lang == 'uz' else "Ошибка поиска")


async def handle_search_result(message: Message, state: FSMContext, search_result: ClientSearchResult, search_method: str, search_value: str):
    """Handle search result and display appropriate response"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        if search_result.error:
            # Handle search error
            error_text = f"Qidirish xatosi: {search_result.error}" if lang == 'uz' else f"Ошибка поиска: {search_result.error}"
            keyboard = get_search_error_keyboard('database_error', lang)
            await message.answer(error_text, reply_markup=keyboard)
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
        elif not search_result.found:
            # No clients found
            not_found_text = "Mijoz topilmadi" if lang == 'uz' else "Клиент не найден"
            keyboard = get_search_error_keyboard('not_found', lang)
            await message.answer(not_found_text, reply_markup=keyboard)
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
        elif search_result.multiple_matches:
            # Multiple clients found
            header_text = "Bir nechta mijoz topildi. Birini tanlang:" if lang == 'uz' else "Найдено несколько клиентов. Выберите одного:"
            keyboard = get_client_selection_keyboard(search_result.multiple_matches, lang)
            await message.answer(header_text, reply_markup=keyboard)
            await state.set_state(StaffApplicationStates.selecting_client_from_results)
            
            # Store search results
            await state.update_data({
                'search_results': search_result.multiple_matches,
                'search_method': search_method,
                'search_value': search_value
            })
            
        elif search_result.client:
            # Single client found
            client_text = format_client_display_text(search_result.client, lang)
            confirm_text = "\n\n✅ Bu mijozni tanlaysizmi?" if lang == 'uz' else "\n\n✅ Выбрать этого клиента?"
            
            keyboard = get_client_confirmation_keyboard(search_result.client, lang)
            await message.answer(client_text + confirm_text, reply_markup=keyboard, parse_mode="Markdown")
            await state.set_state(StaffApplicationStates.confirming_client_selection)
            
            # Store selected client
            await state.update_data({
                'selected_client': search_result.client,
                'search_method': search_method,
                'search_value': search_value
            })
        
    except Exception as e:
        logger.error(f"Error handling search result: {e}")
        await message.answer("Natijalarni ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения результатов")


@router.callback_query(F.data.startswith("client_select_"))
async def handle_client_selection_from_results(callback: CallbackQuery, state: FSMContext):
    """Handle client selection from multiple search results"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        search_results = data.get('search_results', [])
        
        # Find selected client in search results
        selected_client = None
        for client in search_results:
            if client.get('id') == client_id:
                selected_client = client
                break
        
        if not selected_client:
            await callback.answer("Mijoz topilmadi" if lang == 'uz' else "Клиент не найден", show_alert=True)
            return
        
        # Show client confirmation
        client_text = format_client_display_text(selected_client, lang)
        confirm_text = "\n\n✅ Bu mijozni tanlaysizmi?" if lang == 'uz' else "\n\n✅ Выбрать этого клиента?"
        
        keyboard = get_client_confirmation_keyboard(selected_client, lang)
        await callback.message.edit_text(client_text + confirm_text, reply_markup=keyboard, parse_mode="Markdown")
        await state.set_state(StaffApplicationStates.confirming_client_selection)
        
        # Store selected client
        await state.update_data({'selected_client': selected_client})
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error handling client selection: {e}")
        await callback.answer("Tanlashda xatolik" if lang == 'uz' else "Ошибка выбора", show_alert=True)


@router.callback_query(F.data.startswith("client_confirm_"))
async def handle_client_confirmation(callback: CallbackQuery, state: FSMContext):
    """Handle client selection confirmation"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Get client data (either from selected_client or fetch from database)
        selected_client = data.get('selected_client')
        if not selected_client or selected_client.get('id') != client_id:
            # Fetch client from database
            selected_client = await get_user_by_id(client_id)
            if not selected_client:
                await callback.answer("Mijoz topilmadi" if lang == 'uz' else "Клиент не найден", show_alert=True)
                return
        
        # Store confirmed client selection
        await state.update_data({
            'confirmed_client': selected_client,
            'client_selection_completed': True
        })
        
        # Move to next step (application form)
        success_text = f"✅ Mijoz tanlandi: {selected_client.get('full_name', 'Unknown')}" if lang == 'uz' else f"✅ Клиент выбран: {selected_client.get('full_name', 'Unknown')}"
        await callback.answer(success_text)
        
        # Proceed to application description entry
        await proceed_to_application_form(callback.message, state)
        
    except Exception as e:
        logger.error(f"Error confirming client selection: {e}")
        await callback.answer("Tasdiqlashda xatolik" if lang == 'uz' else "Ошибка подтверждения", show_alert=True)


@router.callback_query(F.data.startswith("client_view_details_"))
async def handle_view_client_details(callback: CallbackQuery, state: FSMContext):
    """Handle viewing detailed client information"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Fetch detailed client information
        client_data = await get_user_by_id(client_id)
        if not client_data:
            await callback.answer("Mijoz topilmadi" if lang == 'uz' else "Клиент не найден", show_alert=True)
            return
        
        # Format detailed client information
        client_text = format_client_display_text(client_data, lang)
        
        # Add additional details if available
        if client_data.get('created_at'):
            created_date = client_data['created_at'].strftime('%d.%m.%Y')
            if lang == 'uz':
                client_text += f"\n📅 **Ro'yxatdan o'tgan:** {created_date}"
            else:
                client_text += f"\n📅 **Зарегистрирован:** {created_date}"
        
        keyboard = get_client_details_keyboard(client_id, lang)
        await callback.message.edit_text(client_text, reply_markup=keyboard, parse_mode="Markdown")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error viewing client details: {e}")
        await callback.answer("Ma'lumotlarni ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения данных", show_alert=True)


# New client creation handlers
@router.message(StaffApplicationStates.entering_new_client_name)
async def handle_new_client_name_input(message: Message, state: FSMContext):
    """Handle new client name input"""
    try:
        name_input = message.text.strip()
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Check for cancel/back commands
        if name_input in ["❌ Bekor qilish", "❌ Отменить"]:
            await cancel_client_selection(message, state)
            return
        elif name_input in ["◀️ Orqaga", "◀️ Назад"]:
            await back_to_search_method(message, state)
            return
        
        # Validate name
        from utils.client_selection import ClientValidator
        if not ClientValidator.validate_full_name(name_input):
            error_text = "Ism noto'g'ri. 2-100 ta belgi, faqat harflar" if lang == 'uz' else "Неверное имя. 2-100 символов, только буквы"
            keyboard = get_validation_error_keyboard('name', lang)
            await message.answer(error_text, reply_markup=keyboard)
            return
        
        # Store name and proceed to phone input
        new_client_data = data.get('new_client_data', {})
        new_client_data['full_name'] = name_input
        await state.update_data({'new_client_data': new_client_data})
        
        # Ask for phone number
        prompt_text = get_new_client_form_prompt('phone', lang)
        keyboard = get_new_client_form_keyboard('phone', lang)
        
        await message.answer(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
        await state.set_state(StaffApplicationStates.entering_new_client_phone)
        
    except Exception as e:
        logger.error(f"Error handling new client name: {e}")
        await message.answer("Ism kiritishda xatolik" if lang == 'uz' else "Ошибка ввода имени")


@router.message(StaffApplicationStates.entering_new_client_phone)
async def handle_new_client_phone_input(message: Message, state: FSMContext):
    """Handle new client phone input"""
    try:
        phone_input = message.text.strip()
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Check for cancel/back commands
        if phone_input in ["❌ Bekor qilish", "❌ Отменить"]:
            await cancel_client_selection(message, state)
            return
        elif phone_input in ["◀️ Orqaga", "◀️ Назад"]:
            # Go back to name input
            prompt_text = get_new_client_form_prompt('name', lang)
            keyboard = get_new_client_form_keyboard('name', lang)
            await message.answer(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
            await state.set_state(StaffApplicationStates.entering_new_client_name)
            return
        
        # Validate phone
        from utils.client_selection import ClientValidator
        if not ClientValidator.validate_phone_number(phone_input):
            error_text = "Telefon raqami noto'g'ri. O'zbekiston raqamini kiriting" if lang == 'uz' else "Неверный номер телефона. Введите узбекский номер"
            keyboard = get_validation_error_keyboard('phone', lang)
            await message.answer(error_text, reply_markup=keyboard)
            return
        
        # Normalize phone and check if client already exists
        normalized_phone = ClientValidator.normalize_phone_number(phone_input)
        existing_client = await client_manager.search_client('phone', normalized_phone)
        
        if existing_client.found:
            error_text = "Bu telefon raqami bilan mijoz allaqachon mavjud" if lang == 'uz' else "Клиент с этим номером уже существует"
            keyboard = get_validation_error_keyboard('phone', lang)
            await message.answer(error_text, reply_markup=keyboard)
            return
        
        # Store phone and proceed to address input
        new_client_data = data.get('new_client_data', {})
        new_client_data['phone_number'] = normalized_phone
        await state.update_data({'new_client_data': new_client_data})
        
        # Ask for address (optional)
        prompt_text = get_new_client_form_prompt('address', lang)
        keyboard = get_new_client_form_keyboard('address', lang)
        
        await message.answer(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
        await state.set_state(StaffApplicationStates.entering_new_client_address)
        
    except Exception as e:
        logger.error(f"Error handling new client phone: {e}")
        await message.answer("Telefon kiritishda xatolik" if lang == 'uz' else "Ошибка ввода телефона")


@router.message(StaffApplicationStates.entering_new_client_address)
async def handle_new_client_address_input(message: Message, state: FSMContext):
    """Handle new client address input"""
    try:
        address_input = message.text.strip()
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Check for commands
        if address_input in ["❌ Bekor qilish", "❌ Отменить"]:
            await cancel_client_selection(message, state)
            return
        elif address_input in ["◀️ Orqaga", "◀️ Назад"]:
            # Go back to phone input
            prompt_text = get_new_client_form_prompt('phone', lang)
            keyboard = get_new_client_form_keyboard('phone', lang)
            await message.answer(prompt_text, reply_markup=keyboard, parse_mode="Markdown")
            await state.set_state(StaffApplicationStates.entering_new_client_phone)
            return
        elif address_input in ["⏭️ O'tkazib yuborish", "⏭️ Пропустить"]:
            address_input = ""  # Skip address
        
        # Store address (can be empty)
        new_client_data = data.get('new_client_data', {})
        if address_input:
            new_client_data['address'] = address_input
        new_client_data['language'] = lang  # Set client language same as staff language
        
        await state.update_data({'new_client_data': new_client_data})
        
        # Show confirmation
        await show_new_client_confirmation(message, state)
        
    except Exception as e:
        logger.error(f"Error handling new client address: {e}")
        await message.answer("Manzil kiritishda xatolik" if lang == 'uz' else "Ошибка ввода адреса")


async def show_new_client_confirmation(message: Message, state: FSMContext):
    """Show new client confirmation with all entered data"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        new_client_data = data.get('new_client_data', {})
        
        # Format confirmation text
        if lang == 'uz':
            text = "👤 **Yangi mijoz ma'lumotlari:**\n\n"
            text += f"📝 **Ism:** {new_client_data.get('full_name', 'Kiritilmagan')}\n"
            text += f"📞 **Telefon:** {new_client_data.get('phone_number', 'Kiritilmagan')}\n"
            if new_client_data.get('address'):
                text += f"📍 **Manzil:** {new_client_data['address']}\n"
            text += f"🌐 **Til:** O'zbek\n\n"
            text += "✅ Mijozni yaratishni tasdiqlaysizmi?"
        else:
            text = "👤 **Данные нового клиента:**\n\n"
            text += f"📝 **Имя:** {new_client_data.get('full_name', 'Не введено')}\n"
            text += f"📞 **Телефон:** {new_client_data.get('phone_number', 'Не введен')}\n"
            if new_client_data.get('address'):
                text += f"📍 **Адрес:** {new_client_data['address']}\n"
            text += f"🌐 **Язык:** Русский\n\n"
            text += "✅ Подтвердить создание клиента?"
        
        keyboard = get_new_client_confirmation_keyboard(lang)
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.set_state(StaffApplicationStates.confirming_new_client)
        
    except Exception as e:
        logger.error(f"Error showing new client confirmation: {e}")
        await message.answer("Tasdiqlash ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения подтверждения")


@router.callback_query(F.data == "new_client_confirm_create")
async def handle_new_client_creation_confirmation(callback: CallbackQuery, state: FSMContext):
    """Handle new client creation confirmation"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        new_client_data = data.get('new_client_data', {})
        
        # Create new client
        await callback.answer("Mijoz yaratilmoqda..." if lang == 'uz' else "Создание клиента...")
        
        success, client_id, errors = await client_manager.create_new_client(new_client_data)
        
        if success and client_id:
            # Fetch created client data
            created_client = await get_user_by_id(client_id)
            
            # Store confirmed client
            await state.update_data({
                'confirmed_client': created_client,
                'client_selection_completed': True,
                'created_new_client': True
            })
            
            success_text = f"✅ Yangi mijoz yaratildi: {created_client.get('full_name', 'Unknown')}" if lang == 'uz' else f"✅ Новый клиент создан: {created_client.get('full_name', 'Unknown')}"
            await callback.answer(success_text)
            
            # Proceed to application form
            await proceed_to_application_form(callback.message, state)
            
        else:
            # Handle creation errors
            error_text = "Mijoz yaratishda xatolik:\n" + "\n".join(errors) if lang == 'uz' else "Ошибка создания клиента:\n" + "\n".join(errors)
            keyboard = get_validation_error_keyboard('creation', lang)
            await callback.message.edit_text(error_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error creating new client: {e}")
        await callback.answer("Yaratishda xatolik" if lang == 'uz' else "Ошибка создания", show_alert=True)


async def proceed_to_application_form(message: Message, state: FSMContext):
    """Proceed to application form after client selection is complete"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        confirmed_client = data.get('confirmed_client')
        
        if not confirmed_client:
            error_text = "Mijoz ma'lumotlari topilmadi" if lang == 'uz' else "Данные клиента не найдены"
            await message.answer(error_text)
            return
        
        # Clear reply keyboard and show application form start
        from aiogram.types import ReplyKeyboardRemove
        
        if lang == 'uz':
            text = f"👤 **Tanlangan mijoz:** {confirmed_client.get('full_name', 'Unknown')}\n\n"
            text += "📝 **Ariza tavsifini kiriting:**\n\nMuammo yoki xizmat haqida batafsil yozing."
        else:
            text = f"👤 **Выбранный клиент:** {confirmed_client.get('full_name', 'Unknown')}\n\n"
            text += "📝 **Введите описание заявки:**\n\nПодробно опишите проблему или услугу."
        
        await message.answer(text, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
        await state.set_state(StaffApplicationStates.entering_application_description)
        
    except Exception as e:
        logger.error(f"Error proceeding to application form: {e}")
        await message.answer("Ariza formasiga o'tishda xatolik" if lang == 'uz' else "Ошибка перехода к форме заявки")


# Helper functions
async def cancel_client_selection(message: Message, state: FSMContext):
    """Cancel client selection and return to main menu"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        cancel_text = "❌ Mijoz tanlash bekor qilindi" if lang == 'uz' else "❌ Выбор клиента отменен"
        await message.answer(cancel_text, reply_markup=ReplyKeyboardRemove())
        
        # Clear state and return to main menu
        await state.clear()
        
        # TODO: Return to staff main menu based on role
        
    except Exception as e:
        logger.error(f"Error canceling client selection: {e}")


async def back_to_search_method(message: Message, state: FSMContext):
    """Go back to search method selection"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        text = "👥 **Mijozni tanlash**\n\nMijozni qanday qidirishni xohlaysiz?" if lang == 'uz' else "👥 **Выбор клиента**\n\nКак вы хотите найти клиента?"
        keyboard = get_client_search_method_keyboard(lang)
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        await state.set_state(StaffApplicationStates.selecting_client_search_method)
        
    except Exception as e:
        logger.error(f"Error going back to search method: {e}")


# Navigation callback handlers
@router.callback_query(F.data == "client_search_again")
async def handle_search_again(callback: CallbackQuery, state: FSMContext):
    """Handle search again request"""
    await back_to_search_method(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "staff_app_back_to_search_method")
async def handle_back_to_search_method(callback: CallbackQuery, state: FSMContext):
    """Handle back to search method callback"""
    await back_to_search_method(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "staff_app_back_to_type_selection")
async def handle_back_to_type_selection(callback: CallbackQuery, state: FSMContext):
    """Handle back to application type selection"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # TODO: Return to application type selection
        # This should be implemented in the main staff application handler
        
        await callback.answer("Ariza turi tanloviga qaytish" if lang == 'uz' else "Возврат к выбору типа заявки")
        
    except Exception as e:
        logger.error(f"Error going back to type selection: {e}")
        await callback.answer("Xatolik" if lang == 'uz' else "Ошибка", show_alert=True)


# Export router
__all__ = ['router']