"""
Client Data Verification and Editing Handlers
Provides functionality for staff to verify and edit client information during application creation
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from database.models import User
from states.staff_application_states import StaffApplicationStates
from keyboards.client_search_buttons import (
    get_client_edit_keyboard,
    get_client_language_selection_keyboard,
    get_client_details_keyboard,
    get_client_history_keyboard,
    get_validation_error_keyboard,
    format_client_display_text
)
from utils.client_selection import ClientValidator, ClientManager
from utils.get_lang import get_user_language
from database.base_queries import get_user_by_id, update_user_info
from database.client_queries import get_client_application_history

logger = logging.getLogger(__name__)
router = Router()

# Initialize client manager and validator
client_manager = ClientManager()
client_validator = ClientValidator()


@router.callback_query(F.data.startswith("client_edit_"))
async def handle_client_edit_request(callback: CallbackQuery, state: FSMContext):
    """Handle client edit request"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Fetch current client data
        client_data = await get_user_by_id(client_id)
        if not client_data:
            await callback.answer("Mijoz topilmadi" if lang == 'uz' else "Клиент не найден", show_alert=True)
            return
        
        # Show edit options
        if lang == 'uz':
            text = f"✏️ **Mijoz ma'lumotlarini tahrirlash**\n\n"
            text += format_client_display_text(client_data, lang)
            text += "\n\nQaysi ma'lumotni o'zgartirmoqchisiz?"
        else:
            text = f"✏️ **Редактирование данных клиента**\n\n"
            text += format_client_display_text(client_data, lang)
            text += "\n\nКакие данные хотите изменить?"
        
        keyboard = get_client_edit_keyboard(client_id, lang)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        
        # Store client data for editing
        await state.update_data({
            'editing_client_id': client_id,
            'editing_client_data': client_data,
            'original_client_data': client_data.copy()
        })
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error handling client edit request: {e}")
        await callback.answer("Tahrirlashda xatolik" if lang == 'uz' else "Ошибка редактирования", show_alert=True)


@router.callback_query(F.data.startswith("client_edit_name_"))
async def handle_edit_client_name(callback: CallbackQuery, state: FSMContext):
    """Handle client name editing"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Set editing state
        await state.update_data({
            'editing_field': 'name',
            'editing_client_id': client_id
        })
        
        prompt_text = "👤 **Yangi ismni kiriting:**\n\nTo'liq ism va familiyani yozing" if lang == 'uz' else "👤 **Введите новое имя:**\n\nПолное имя и фамилию"
        
        await callback.message.edit_text(prompt_text, parse_mode="Markdown")
        await callback.message.answer("Yangi ismni yozing:" if lang == 'uz' else "Напишите новое имя:")
        
        await state.set_state(StaffApplicationStates.handling_validation_error)  # Reuse state for editing
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error starting name edit: {e}")
        await callback.answer("Xatolik" if lang == 'uz' else "Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("client_edit_phone_"))
async def handle_edit_client_phone(callback: CallbackQuery, state: FSMContext):
    """Handle client phone editing"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Set editing state
        await state.update_data({
            'editing_field': 'phone',
            'editing_client_id': client_id
        })
        
        prompt_text = "📞 **Yangi telefon raqamini kiriting:**\n\nMisol: +998901234567" if lang == 'uz' else "📞 **Введите новый номер телефона:**\n\nПример: +998901234567"
        
        await callback.message.edit_text(prompt_text, parse_mode="Markdown")
        await callback.message.answer("Yangi telefon raqamini yozing:" if lang == 'uz' else "Напишите новый номер телефона:")
        
        await state.set_state(StaffApplicationStates.handling_validation_error)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error starting phone edit: {e}")
        await callback.answer("Xatolik" if lang == 'uz' else "Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("client_edit_address_"))
async def handle_edit_client_address(callback: CallbackQuery, state: FSMContext):
    """Handle client address editing"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Set editing state
        await state.update_data({
            'editing_field': 'address',
            'editing_client_id': client_id
        })
        
        prompt_text = "📍 **Yangi manzilni kiriting:**\n\n(Bo'sh qoldirish uchun 'skip' yozing)" if lang == 'uz' else "📍 **Введите новый адрес:**\n\n(Напишите 'skip' чтобы оставить пустым)"
        
        await callback.message.edit_text(prompt_text, parse_mode="Markdown")
        await callback.message.answer("Yangi manzilni yozing:" if lang == 'uz' else "Напишите новый адрес:")
        
        await state.set_state(StaffApplicationStates.handling_validation_error)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error starting address edit: {e}")
        await callback.answer("Xatolik" if lang == 'uz' else "Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("client_edit_language_"))
async def handle_edit_client_language(callback: CallbackQuery, state: FSMContext):
    """Handle client language editing"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        text = "🌐 **Mijoz tilini tanlang:**" if lang == 'uz' else "🌐 **Выберите язык клиента:**"
        keyboard = get_client_language_selection_keyboard(client_id, lang)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing language selection: {e}")
        await callback.answer("Xatolik" if lang == 'uz' else "Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("client_set_lang_"))
async def handle_set_client_language(callback: CallbackQuery, state: FSMContext):
    """Handle setting client language"""
    try:
        parts = callback.data.split("_")
        new_language = parts[3]  # uz or ru
        client_id = int(parts[4])
        
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Update client language
        success = await update_user_info(client_id, {'language': new_language})
        
        if success:
            # Update editing client data
            editing_client_data = data.get('editing_client_data', {})
            editing_client_data['language'] = new_language
            await state.update_data({'editing_client_data': editing_client_data})
            
            lang_name = "O'zbek" if new_language == 'uz' else "Rus"
            success_text = f"✅ Mijoz tili {lang_name} ga o'zgartirildi" if lang == 'uz' else f"✅ Язык клиента изменен на {lang_name}"
            await callback.answer(success_text)
            
            # Return to edit menu
            await show_client_edit_menu(callback.message, state, client_id)
        else:
            await callback.answer("Tilni o'zgartirishda xatolik" if lang == 'uz' else "Ошибка изменения языка", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error setting client language: {e}")
        await callback.answer("Xatolik" if lang == 'uz' else "Ошибка", show_alert=True)


@router.message(StaffApplicationStates.handling_validation_error)
async def handle_client_field_edit_input(message: Message, state: FSMContext):
    """Handle input for client field editing"""
    try:
        input_text = message.text.strip()
        data = await state.get_data()
        lang = data.get('language', 'uz')
        editing_field = data.get('editing_field')
        client_id = data.get('editing_client_id')
        
        if not editing_field or not client_id:
            await message.answer("Tahrirlash ma'lumotlari topilmadi" if lang == 'uz' else "Данные редактирования не найдены")
            return
        
        # Validate input based on field type
        validation_error = None
        update_data = {}
        
        if editing_field == 'name':
            if not client_validator.validate_full_name(input_text):
                validation_error = "Ism noto'g'ri. 2-100 ta belgi, faqat harflar" if lang == 'uz' else "Неверное имя. 2-100 символов, только буквы"
            else:
                update_data['full_name'] = input_text
                
        elif editing_field == 'phone':
            if not client_validator.validate_phone_number(input_text):
                validation_error = "Telefon raqami noto'g'ri" if lang == 'uz' else "Неверный номер телефона"
            else:
                # Check if phone already exists for another client
                normalized_phone = client_validator.normalize_phone_number(input_text)
                existing_client = await client_manager.search_client('phone', normalized_phone)
                
                if existing_client.found and existing_client.client and existing_client.client.get('id') != client_id:
                    validation_error = "Bu telefon raqami boshqa mijozda mavjud" if lang == 'uz' else "Этот номер уже используется другим клиентом"
                else:
                    update_data['phone_number'] = normalized_phone
                    
        elif editing_field == 'address':
            if input_text.lower() in ['skip', 'o\'tkazish', 'пропустить']:
                update_data['address'] = None
            else:
                if len(input_text) > 500:  # Address length limit
                    validation_error = "Manzil juda uzun (maksimal 500 belgi)" if lang == 'uz' else "Адрес слишком длинный (максимум 500 символов)"
                else:
                    update_data['address'] = input_text
        
        if validation_error:
            keyboard = get_validation_error_keyboard(editing_field, lang)
            await message.answer(validation_error, reply_markup=keyboard)
            return
        
        # Update client data
        success = await update_user_info(client_id, update_data)
        
        if success:
            # Update editing client data
            editing_client_data = data.get('editing_client_data', {})
            editing_client_data.update(update_data)
            await state.update_data({'editing_client_data': editing_client_data})
            
            field_name = {
                'name': 'ism' if lang == 'uz' else 'имя',
                'phone': 'telefon' if lang == 'uz' else 'телефон',
                'address': 'manzil' if lang == 'uz' else 'адрес'
            }.get(editing_field, editing_field)
            
            success_text = f"✅ Mijoz {field_name}i yangilandi" if lang == 'uz' else f"✅ {field_name.capitalize()} клиента обновлен"
            await message.answer(success_text)
            
            # Return to edit menu
            await show_client_edit_menu(message, state, client_id)
        else:
            await message.answer("Ma'lumotlarni yangilashda xatolik" if lang == 'uz' else "Ошибка обновления данных")
        
    except Exception as e:
        logger.error(f"Error handling client field edit: {e}")
        await message.answer("Tahrirlashda xatolik" if lang == 'uz' else "Ошибка редактирования")


@router.callback_query(F.data.startswith("client_save_changes_"))
async def handle_save_client_changes(callback: CallbackQuery, state: FSMContext):
    """Handle saving all client changes"""
    try:
        client_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Get updated client data
        updated_client = await get_user_by_id(client_id)
        if not updated_client:
            await callback.answer("Mijoz topilmadi" if lang == 'uz' else "Клиент не найден", show_alert=True)
            return
        
        # Show confirmation of saved changes
        success_text = "✅ Barcha o'zgarishlar saqlandi" if lang == 'uz' else "✅ Все изменения сохранены"
        await callback.answer(success_text)
        
        # Return to client details view
        await show_client_details(callback.message, state, client_id)
        
    except Exception as e:
        logger.error(f"Error saving client changes: {e}")
        await callback.answer("Saqlashda xatolik" if lang == 'uz' else "Ошибка сохранения", show_alert=True)


@router.callback_query(F.data.startswith("client_history_"))
async def handle_client_history_request(callback: CallbackQuery, state: FSMContext):
    """Handle client application history request"""
    try:
        parts = callback.data.split("_")
        client_id = int(parts[2])
        
        # Check if this is a pagination request
        page = 1
        if len(parts) > 3 and parts[3] == "page":
            page = int(parts[4])
        
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Fetch client application history
        applications, total_count = await get_client_application_history(client_id, page=page, limit=5)
        total_pages = (total_count + 4) // 5  # Ceiling division
        
        # Format history text
        if lang == 'uz':
            text = f"📋 **Mijoz arizalari tarixi**\n\n"
            if applications:
                for i, app in enumerate(applications, 1):
                    status_emoji = {
                        'new': '🆕',
                        'in_progress': '⏳',
                        'completed': '✅',
                        'cancelled': '❌'
                    }.get(app.get('status', 'new'), '📋')
                    
                    created_date = app.get('created_at', datetime.now()).strftime('%d.%m.%Y')
                    text += f"{status_emoji} **#{app.get('id', 'N/A')}** - {app.get('description', 'Tavsif yo\'q')[:50]}...\n"
                    text += f"   📅 {created_date}\n\n"
            else:
                text += "Hech qanday ariza topilmadi"
        else:
            text = f"📋 **История заявок клиента**\n\n"
            if applications:
                for i, app in enumerate(applications, 1):
                    status_emoji = {
                        'new': '🆕',
                        'in_progress': '⏳',
                        'completed': '✅',
                        'cancelled': '❌'
                    }.get(app.get('status', 'new'), '📋')
                    
                    created_date = app.get('created_at', datetime.now()).strftime('%d.%m.%Y')
                    text += f"{status_emoji} **#{app.get('id', 'N/A')}** - {app.get('description', 'Нет описания')[:50]}...\n"
                    text += f"   📅 {created_date}\n\n"
            else:
                text += "Заявки не найдены"
        
        keyboard = get_client_history_keyboard(client_id, page, total_pages, lang)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing client history: {e}")
        await callback.answer("Tarix ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения истории", show_alert=True)


@router.callback_query(F.data == "client_history_page_info")
async def handle_history_page_info(callback: CallbackQuery, state: FSMContext):
    """Handle history page info callback (no action needed)"""
    await callback.answer()


# Helper functions
async def show_client_edit_menu(message: Message, state: FSMContext, client_id: int):
    """Show client edit menu with updated data"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Fetch updated client data
        client_data = await get_user_by_id(client_id)
        if not client_data:
            await message.answer("Mijoz topilmadi" if lang == 'uz' else "Клиент не найден")
            return
        
        # Show edit menu
        if lang == 'uz':
            text = f"✏️ **Mijoz ma'lumotlarini tahrirlash**\n\n"
            text += format_client_display_text(client_data, lang)
            text += "\n\nQaysi ma'lumotni o'zgartirmoqchisiz?"
        else:
            text = f"✏️ **Редактирование данных клиента**\n\n"
            text += format_client_display_text(client_data, lang)
            text += "\n\nКакие данные хотите изменить?"
        
        keyboard = get_client_edit_keyboard(client_id, lang)
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
        # Update stored client data
        await state.update_data({'editing_client_data': client_data})
        
    except Exception as e:
        logger.error(f"Error showing client edit menu: {e}")
        await message.answer("Tahrirlash menyusini ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения меню редактирования")


async def show_client_details(message: Message, state: FSMContext, client_id: int):
    """Show detailed client information"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Fetch client data
        client_data = await get_user_by_id(client_id)
        if not client_data:
            await message.answer("Mijoz topilmadi" if lang == 'uz' else "Клиент не найден")
            return
        
        # Format client details
        client_text = format_client_display_text(client_data, lang)
        
        # Add additional details
        if client_data.get('created_at'):
            created_date = client_data['created_at'].strftime('%d.%m.%Y %H:%M')
            if lang == 'uz':
                client_text += f"\n📅 **Ro'yxatdan o'tgan:** {created_date}"
            else:
                client_text += f"\n📅 **Зарегистрирован:** {created_date}"
        
        if client_data.get('last_activity'):
            last_activity = client_data['last_activity'].strftime('%d.%m.%Y %H:%M')
            if lang == 'uz':
                client_text += f"\n🕐 **So'nggi faollik:** {last_activity}"
            else:
                client_text += f"\n🕐 **Последняя активность:** {last_activity}"
        
        keyboard = get_client_details_keyboard(client_id, lang)
        await message.answer(client_text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error showing client details: {e}")
        await message.answer("Mijoz ma'lumotlarini ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения данных клиента")


# Validation retry handlers
@router.callback_query(F.data.startswith("client_retry_input_"))
async def handle_retry_input(callback: CallbackQuery, state: FSMContext):
    """Handle retry input for validation errors"""
    try:
        field = callback.data.split("_")[-1]
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        # Set up retry based on field
        if field == 'name':
            prompt_text = "👤 **Ismni qayta kiriting:**" if lang == 'uz' else "👤 **Введите имя заново:**"
        elif field == 'phone':
            prompt_text = "📞 **Telefon raqamini qayta kiriting:**" if lang == 'uz' else "📞 **Введите телефон заново:**"
        elif field == 'address':
            prompt_text = "📍 **Manzilni qayta kiriting:**" if lang == 'uz' else "📍 **Введите адрес заново:**"
        else:
            prompt_text = "Ma'lumotni qayta kiriting:" if lang == 'uz' else "Введите данные заново:"
        
        await callback.message.edit_text(prompt_text, parse_mode="Markdown")
        await callback.message.answer("Yangi ma'lumotni yozing:" if lang == 'uz' else "Напишите новые данные:")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error handling retry input: {e}")
        await callback.answer("Xatolik" if lang == 'uz' else "Ошибка", show_alert=True)


@router.callback_query(F.data == "client_cancel_creation")
async def handle_cancel_client_creation(callback: CallbackQuery, state: FSMContext):
    """Handle canceling client creation"""
    try:
        data = await state.get_data()
        lang = data.get('language', 'uz')
        
        cancel_text = "❌ Mijoz yaratish bekor qilindi" if lang == 'uz' else "❌ Создание клиента отменено"
        await callback.answer(cancel_text)
        
        # Return to search method selection
        from handlers.client_search_ui import back_to_search_method
        await back_to_search_method(callback.message, state)
        
    except Exception as e:
        logger.error(f"Error canceling client creation: {e}")
        await callback.answer("Xatolik" if lang == 'uz' else "Ошибка", show_alert=True)


# Export router
__all__ = ['router']