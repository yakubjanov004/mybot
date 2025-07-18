"""
Staff Application Creation Confirmation Flow Handlers

This module implements confirmation flows for staff-created applications including:
- Application preview and confirmation screens
- Edit capabilities before final submission
- Submission confirmation and success messages
- Error handling and retry mechanisms

Requirements: 1.5, 2.4, 3.4, 4.4
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from database.models import ServiceRequest, WorkflowType, RequestStatus, Priority
from states.staff_application_states import StaffApplicationStates
from keyboards.staff_confirmation_buttons import (
    get_application_preview_keyboard,
    get_application_edit_keyboard,
    get_submission_confirmation_keyboard,
    get_submission_success_keyboard,
    get_error_retry_keyboard,
    get_validation_error_keyboard,
    format_application_preview_text,
    format_submission_confirmation_text,
    format_success_message_text,
    format_error_message_text
)
from handlers.staff_application_creation import RoleBasedApplicationHandler
from utils.get_lang import get_user_language
from utils.get_role import get_user_role
from utils.logger import setup_module_logger

logger = setup_module_logger("staff_application_confirmation")
router = Router()

# Initialize application handler
application_handler = RoleBasedApplicationHandler()


@router.message(StaffApplicationStates.reviewing_application_details)
async def handle_application_review_request(message: Message, state: FSMContext):
    """Handle request to review application details before submission"""
    try:
        user_id = message.from_user.id
        lang = await get_user_language(user_id)
        
        # Get application data from state
        data = await state.get_data()
        
        # Show application preview
        await show_application_preview(message, state, data, lang)
        
    except Exception as e:
        logger.error(f"Error handling application review request: {e}")
        await message.answer(
            "Ariza ko'rib chiqishda xatolik" if lang == 'uz' else "Ошибка просмотра заявки"
        )


async def show_application_preview(message: Message, state: FSMContext, data: Dict[str, Any], lang: str):
    """Show detailed application preview with edit options"""
    try:
        # Format application preview text
        preview_text = format_application_preview_text(data, lang)
        
        # Get preview keyboard with edit options
        keyboard = get_application_preview_keyboard(lang)
        
        await message.answer(
            preview_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(StaffApplicationStates.reviewing_application_details)
        
    except Exception as e:
        logger.error(f"Error showing application preview: {e}")
        await message.answer(
            "Ariza ko'rinishini ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения предварительного просмотра"
        )


@router.callback_query(F.data == "app_preview_confirm")
async def handle_application_confirmation(callback: CallbackQuery, state: FSMContext):
    """Handle application confirmation from preview"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        # Get application data
        data = await state.get_data()
        
        # Show final submission confirmation
        await show_submission_confirmation(callback, state, data, lang)
        
    except Exception as e:
        logger.error(f"Error handling application confirmation: {e}")
        await callback.answer(
            "Tasdiqlashda xatolik" if lang == 'uz' else "Ошибка подтверждения",
            show_alert=True
        )


async def show_submission_confirmation(callback: CallbackQuery, state: FSMContext, data: Dict[str, Any], lang: str):
    """Show final submission confirmation dialog"""
    try:
        # Format confirmation text
        confirmation_text = format_submission_confirmation_text(data, lang)
        
        # Get confirmation keyboard
        keyboard = get_submission_confirmation_keyboard(lang)
        
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(StaffApplicationStates.confirming_application_submission)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing submission confirmation: {e}")
        await callback.answer(
            "Tasdiqlash ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения подтверждения",
            show_alert=True
        )


@router.callback_query(F.data == "app_submit_confirm")
async def handle_final_submission(callback: CallbackQuery, state: FSMContext):
    """Handle final application submission"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        user_role = await get_user_role(user_id)
        
        # Show processing message
        processing_text = "⏳ Ariza yuborilmoqda..." if lang == 'uz' else "⏳ Отправка заявки..."
        await callback.message.edit_text(processing_text)
        await callback.answer()
        
        # Set processing state
        await state.set_state(StaffApplicationStates.processing_submission)
        
        # Get application data
        data = await state.get_data()
        
        # Prepare application data for submission
        application_data = await prepare_application_for_submission(data, user_id, user_role)
        
        # Create creator context
        creator_context = {
            'creator_id': user_id,
            'creator_role': user_role,
            'application_type': data.get('application_type'),
            'session_id': data.get('session_id'),
            'started_at': data.get('started_at', datetime.now())
        }
        
        # Submit application
        result = await application_handler.validate_and_submit(application_data, creator_context)
        
        if result['success']:
            # Show success message
            await show_submission_success(callback.message, state, result, lang)
        else:
            # Show error message with retry options
            await show_submission_error(callback.message, state, result, lang)
        
    except Exception as e:
        logger.error(f"Error handling final submission: {e}")
        await callback.message.edit_text(
            "Yuborishda xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка при отправке"
        )
        await show_submission_error(callback.message, state, {'error_type': 'system_error', 'error_message': str(e)}, lang)


async def prepare_application_for_submission(data: Dict[str, Any], user_id: int, user_role: str) -> Dict[str, Any]:
    """Prepare application data for submission"""
    try:
        # Get client data
        confirmed_client = data.get('confirmed_client', {})
        client_data = {
            'phone': confirmed_client.get('phone_number', ''),
            'full_name': confirmed_client.get('full_name', ''),
            'address': confirmed_client.get('address', ''),
            'additional_info': ''
        }
        
        # Get application data
        application_data = {
            'description': data.get('application_description', ''),
            'location': data.get('application_address', ''),
            'priority': data.get('priority', Priority.MEDIUM.value),
            'additional_notes': data.get('additional_notes', '')
        }
        
        # Add application type specific data
        application_type = data.get('application_type')
        if application_type == 'technical_service':
            application_data['issue_type'] = data.get('issue_type', '')
        elif application_type == 'connection_request':
            application_data['connection_type'] = data.get('connection_type', '')
            application_data['tariff'] = data.get('tariff', '')
        
        # Add media and location if available
        if data.get('media_files'):
            application_data['media_files'] = data['media_files']
        if data.get('location_data'):
            application_data['location_data'] = data['location_data']
        
        return {
            'client_data': client_data,
            'application_data': application_data
        }
        
    except Exception as e:
        logger.error(f"Error preparing application for submission: {e}")
        raise


async def show_submission_success(message: Message, state: FSMContext, result: Dict[str, Any], lang: str):
    """Show successful submission message"""
    try:
        # Format success message
        success_text = format_success_message_text(result, lang)
        
        # Get success keyboard
        keyboard = get_submission_success_keyboard(lang)
        
        await message.edit_text(
            success_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(StaffApplicationStates.application_submitted)
        
        # Log successful submission
        logger.info(f"Application submitted successfully: {result.get('application_id')}")
        
    except Exception as e:
        logger.error(f"Error showing submission success: {e}")
        await message.edit_text(
            "Ariza muvaffaqiyatli yuborildi!" if lang == 'uz' else "Заявка успешно отправлена!"
        )


async def show_submission_error(message: Message, state: FSMContext, error_result: Dict[str, Any], lang: str):
    """Show submission error with retry options"""
    try:
        # Format error message
        error_text = format_error_message_text(error_result, lang)
        
        # Get error keyboard with retry options
        keyboard = get_error_retry_keyboard(error_result.get('error_type', 'unknown'), lang)
        
        await message.edit_text(
            error_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(StaffApplicationStates.handling_submission_error)
        
        # Log submission error
        logger.error(f"Application submission failed: {error_result}")
        
    except Exception as e:
        logger.error(f"Error showing submission error: {e}")
        await message.edit_text(
            "Yuborishda xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка при отправке"
        )


# Edit handlers
@router.callback_query(F.data.startswith("app_edit_"))
async def handle_application_edit(callback: CallbackQuery, state: FSMContext):
    """Handle application edit requests"""
    try:
        edit_field = callback.data.split("_")[-1]  # description, address, client, etc.
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        # Route to appropriate edit handler
        if edit_field == "description":
            await edit_application_description(callback, state, lang)
        elif edit_field == "address":
            await edit_application_address(callback, state, lang)
        elif edit_field == "client":
            await edit_client_selection(callback, state, lang)
        elif edit_field == "details":
            await edit_application_details(callback, state, lang)
        else:
            await callback.answer(
                "Noma'lum tahrirlash turi" if lang == 'uz' else "Неизвестный тип редактирования",
                show_alert=True
            )
        
    except Exception as e:
        logger.error(f"Error handling application edit: {e}")
        await callback.answer(
            "Tahrirlashda xatolik" if lang == 'uz' else "Ошибка редактирования",
            show_alert=True
        )


async def edit_application_description(callback: CallbackQuery, state: FSMContext, lang: str):
    """Handle editing application description"""
    try:
        edit_text = (
            "📝 **Ariza tavsifini tahrirlash**\n\n"
            "Yangi tavsifni kiriting:"
        ) if lang == 'uz' else (
            "📝 **Редактирование описания заявки**\n\n"
            "Введите новое описание:"
        )
        
        keyboard = get_application_edit_keyboard('description', lang)
        
        await callback.message.edit_text(
            edit_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(StaffApplicationStates.entering_application_description)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error editing application description: {e}")
        await callback.answer(
            "Tavsifni tahrirlashda xatolik" if lang == 'uz' else "Ошибка редактирования описания",
            show_alert=True
        )


async def edit_application_address(callback: CallbackQuery, state: FSMContext, lang: str):
    """Handle editing application address"""
    try:
        edit_text = (
            "📍 **Ariza manzilini tahrirlash**\n\n"
            "Yangi manzilni kiriting:"
        ) if lang == 'uz' else (
            "📍 **Редактирование адреса заявки**\n\n"
            "Введите новый адрес:"
        )
        
        keyboard = get_application_edit_keyboard('address', lang)
        
        await callback.message.edit_text(
            edit_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(StaffApplicationStates.entering_application_address)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error editing application address: {e}")
        await callback.answer(
            "Manzilni tahrirlashda xatolik" if lang == 'uz' else "Ошибка редактирования адреса",
            show_alert=True
        )


async def edit_client_selection(callback: CallbackQuery, state: FSMContext, lang: str):
    """Handle editing client selection"""
    try:
        edit_text = (
            "👤 **Mijozni tahrirlash**\n\n"
            "Boshqa mijozni tanlash uchun qidirish usulini tanlang:"
        ) if lang == 'uz' else (
            "👤 **Редактирование клиента**\n\n"
            "Выберите способ поиска для выбора другого клиента:"
        )
        
        # Import client search keyboard
        from keyboards.client_search_buttons import get_client_search_method_keyboard
        keyboard = get_client_search_method_keyboard(lang)
        
        await callback.message.edit_text(
            edit_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(StaffApplicationStates.selecting_client_search_method)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error editing client selection: {e}")
        await callback.answer(
            "Mijozni tahrirlashda xatolik" if lang == 'uz' else "Ошибка редактирования клиента",
            show_alert=True
        )


async def edit_application_details(callback: CallbackQuery, state: FSMContext, lang: str):
    """Handle editing application-specific details"""
    try:
        data = await state.get_data()
        application_type = data.get('application_type')
        
        if application_type == 'connection_request':
            edit_text = (
                "🔌 **Ulanish ma'lumotlarini tahrirlash**\n\n"
                "Ulanish turini qayta tanlang:"
            ) if lang == 'uz' else (
                "🔌 **Редактирование данных подключения**\n\n"
                "Выберите тип подключения заново:"
            )
            await state.set_state(StaffApplicationStates.selecting_connection_type)
        elif application_type == 'technical_service':
            edit_text = (
                "🔧 **Texnik xizmat ma'lumotlarini tahrirlash**\n\n"
                "Muammo turini qayta tanlang:"
            ) if lang == 'uz' else (
                "🔧 **Редактирование данных технического сервиса**\n\n"
                "Выберите тип проблемы заново:"
            )
            await state.set_state(StaffApplicationStates.selecting_issue_type)
        else:
            await callback.answer(
                "Noma'lum ariza turi" if lang == 'uz' else "Неизвестный тип заявки",
                show_alert=True
            )
            return
        
        keyboard = get_application_edit_keyboard('details', lang)
        
        await callback.message.edit_text(
            edit_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error editing application details: {e}")
        await callback.answer(
            "Ma'lumotlarni tahrirlashda xatolik" if lang == 'uz' else "Ошибка редактирования данных",
            show_alert=True
        )


# Error handling and retry mechanisms
@router.callback_query(F.data == "app_error_retry")
async def handle_error_retry(callback: CallbackQuery, state: FSMContext):
    """Handle retry after submission error"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        # Show processing message
        processing_text = "🔄 Qayta urinilmoqda..." if lang == 'uz' else "🔄 Повторная попытка..."
        await callback.message.edit_text(processing_text)
        await callback.answer()
        
        # Retry submission
        await handle_final_submission(callback, state)
        
    except Exception as e:
        logger.error(f"Error handling retry: {e}")
        await callback.answer(
            "Qayta urinishda xatolik" if lang == 'uz' else "Ошибка повторной попытки",
            show_alert=True
        )


@router.callback_query(F.data == "app_error_edit")
async def handle_error_edit(callback: CallbackQuery, state: FSMContext):
    """Handle edit request after submission error"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        # Get application data and show preview for editing
        data = await state.get_data()
        await show_application_preview(callback.message, state, data, lang)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error handling error edit: {e}")
        await callback.answer(
            "Tahrirlashga o'tishda xatolik" if lang == 'uz' else "Ошибка перехода к редактированию",
            show_alert=True
        )


@router.callback_query(F.data == "app_error_cancel")
async def handle_error_cancel(callback: CallbackQuery, state: FSMContext):
    """Handle cancellation after submission error"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        cancel_text = (
            "❌ **Ariza yaratish bekor qilindi**\n\n"
            "Yangi ariza yaratish uchun menyudan tanlang."
        ) if lang == 'uz' else (
            "❌ **Создание заявки отменено**\n\n"
            "Для создания новой заявки выберите из меню."
        )
        
        await callback.message.edit_text(
            cancel_text,
            parse_mode="Markdown"
        )
        
        # Clear state
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error handling error cancel: {e}")
        await callback.answer(
            "Bekor qilishda xatolik" if lang == 'uz' else "Ошибка отмены",
            show_alert=True
        )


# Success flow handlers
@router.callback_query(F.data == "app_success_create_another")
async def handle_create_another_application(callback: CallbackQuery, state: FSMContext):
    """Handle creating another application after successful submission"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        # Clear current state
        await state.clear()
        
        # Start new application creation
        start_text = (
            "🆕 **Yangi ariza yaratish**\n\n"
            "Ariza turini tanlang:"
        ) if lang == 'uz' else (
            "🆕 **Создание новой заявки**\n\n"
            "Выберите тип заявки:"
        )
        
        # Import application type keyboard
        from keyboards.staff_application_buttons import get_application_type_keyboard
        keyboard = get_application_type_keyboard(lang)
        
        await callback.message.edit_text(
            start_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(StaffApplicationStates.selecting_application_type)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error creating another application: {e}")
        await callback.answer(
            "Yangi ariza yaratishda xatolik" if lang == 'uz' else "Ошибка создания новой заявки",
            show_alert=True
        )


@router.callback_query(F.data == "app_success_finish")
async def handle_finish_application_creation(callback: CallbackQuery, state: FSMContext):
    """Handle finishing application creation process"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        finish_text = (
            "✅ **Ariza yaratish tugallandi**\n\n"
            "Rahmat! Ariza muvaffaqiyatli yaratildi va ishlov berishga yuborildi."
        ) if lang == 'uz' else (
            "✅ **Создание заявки завершено**\n\n"
            "Спасибо! Заявка успешно создана и отправлена на обработку."
        )
        
        await callback.message.edit_text(
            finish_text,
            parse_mode="Markdown"
        )
        
        # Clear state
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error finishing application creation: {e}")
        await callback.answer(
            "Tugatishda xatolik" if lang == 'uz' else "Ошибка завершения",
            show_alert=True
        )


# Validation error handlers
@router.callback_query(F.data == "app_validation_fix")
async def handle_validation_error_fix(callback: CallbackQuery, state: FSMContext):
    """Handle fixing validation errors"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        # Get application data and show preview for fixing
        data = await state.get_data()
        await show_application_preview(callback.message, state, data, lang)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error handling validation fix: {e}")
        await callback.answer(
            "Xatolarni tuzatishda xatolik" if lang == 'uz' else "Ошибка исправления ошибок",
            show_alert=True
        )


# Cancel handlers
@router.callback_query(F.data == "app_cancel")
async def handle_application_cancel(callback: CallbackQuery, state: FSMContext):
    """Handle application creation cancellation"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        cancel_text = (
            "❌ **Ariza yaratish bekor qilindi**\n\n"
            "Barcha kiritilgan ma'lumotlar o'chirildi."
        ) if lang == 'uz' else (
            "❌ **Создание заявки отменено**\n\n"
            "Все введенные данные удалены."
        )
        
        await callback.message.edit_text(
            cancel_text,
            parse_mode="Markdown"
        )
        
        # Clear state
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error handling application cancel: {e}")
        await callback.answer(
            "Bekor qilishda xatolik" if lang == 'uz' else "Ошибка отмены",
            show_alert=True
        )


# Back to preview handler
@router.callback_query(F.data == "app_back_to_preview")
async def handle_back_to_preview(callback: CallbackQuery, state: FSMContext):
    """Handle going back to application preview"""
    try:
        user_id = callback.from_user.id
        lang = await get_user_language(user_id)
        
        # Get application data and show preview
        data = await state.get_data()
        await show_application_preview(callback.message, state, data, lang)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error going back to preview: {e}")
        await callback.answer(
            "Orqaga qaytishda xatolik" if lang == 'uz' else "Ошибка возврата назад",
            show_alert=True
        )


# Export router
__all__ = ['router']