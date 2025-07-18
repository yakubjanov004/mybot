"""
Staff Application Confirmation Keyboards

This module provides keyboard layouts for staff application confirmation flows including:
- Application preview and confirmation screens
- Edit capabilities before final submission  
- Submission confirmation and success messages
- Error handling and retry mechanisms

Requirements: 1.5, 2.4, 3.4, 4.4
"""

from typing import Dict, Any, List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime


def get_application_preview_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get keyboard for application preview with edit and confirm options"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="app_preview_confirm")],
            [
                InlineKeyboardButton(text="📝 Tavsifni tahrirlash", callback_data="app_edit_description"),
                InlineKeyboardButton(text="📍 Manzilni tahrirlash", callback_data="app_edit_address")
            ],
            [
                InlineKeyboardButton(text="👤 Mijozni o'zgartirish", callback_data="app_edit_client"),
                InlineKeyboardButton(text="⚙️ Ma'lumotlarni tahrirlash", callback_data="app_edit_details")
            ],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="app_preview_confirm")],
            [
                InlineKeyboardButton(text="📝 Редактировать описание", callback_data="app_edit_description"),
                InlineKeyboardButton(text="📍 Редактировать адрес", callback_data="app_edit_address")
            ],
            [
                InlineKeyboardButton(text="👤 Изменить клиента", callback_data="app_edit_client"),
                InlineKeyboardButton(text="⚙️ Редактировать данные", callback_data="app_edit_details")
            ],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="app_cancel")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_application_edit_keyboard(edit_type: str, lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get keyboard for editing specific application fields"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="app_back_to_preview")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="◀️ Назад", callback_data="app_back_to_preview")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="app_cancel")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_submission_confirmation_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get keyboard for final submission confirmation"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="app_submit_confirm")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="app_back_to_preview")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="✅ Да, отправить", callback_data="app_submit_confirm")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="app_back_to_preview")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="app_cancel")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_submission_success_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get keyboard for successful submission with next action options"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="🆕 Yangi ariza yaratish", callback_data="app_success_create_another")],
            [InlineKeyboardButton(text="✅ Tugallash", callback_data="app_success_finish")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🆕 Создать новую заявку", callback_data="app_success_create_another")],
            [InlineKeyboardButton(text="✅ Завершить", callback_data="app_success_finish")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_error_retry_keyboard(error_type: str, lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get keyboard for error handling with retry options"""
    buttons = []
    
    if lang == 'uz':
        # Always show retry option
        buttons.append([InlineKeyboardButton(text="🔄 Qayta urinish", callback_data="app_error_retry")])
        
        # Show edit option for validation errors
        if error_type in ['validation_error', 'client_validation_error']:
            buttons.append([InlineKeyboardButton(text="📝 Tahrirlash", callback_data="app_error_edit")])
        
        # Always show cancel option
        buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_error_cancel")])
    else:
        # Always show retry option
        buttons.append([InlineKeyboardButton(text="🔄 Повторить", callback_data="app_error_retry")])
        
        # Show edit option for validation errors
        if error_type in ['validation_error', 'client_validation_error']:
            buttons.append([InlineKeyboardButton(text="📝 Редактировать", callback_data="app_error_edit")])
        
        # Always show cancel option
        buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="app_error_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_validation_error_keyboard(field_type: str, lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get keyboard for validation error handling"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="🔧 Tuzatish", callback_data="app_validation_fix")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="app_back_to_preview")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🔧 Исправить", callback_data="app_validation_fix")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="app_back_to_preview")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="app_cancel")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_application_preview_text(data: Dict[str, Any], lang: str = 'uz') -> str:
    """Format application preview text with all details"""
    try:
        if lang == 'uz':
            text = "📋 **Ariza ko'rib chiqish**\n\n"
            
            # Client information
            confirmed_client = data.get('confirmed_client', {})
            text += "👤 **Mijoz ma'lumotlari:**\n"
            text += f"📝 Ism: {confirmed_client.get('full_name', 'Kiritilmagan')}\n"
            text += f"📞 Telefon: {confirmed_client.get('phone_number', 'Kiritilmagan')}\n"
            if confirmed_client.get('address'):
                text += f"📍 Manzil: {confirmed_client['address']}\n"
            text += "\n"
            
            # Application information
            text += "📄 **Ariza ma'lumotlari:**\n"
            application_type = data.get('application_type', '')
            if application_type == 'connection_request':
                text += "🔌 Tur: Ulanish uchun ariza\n"
            elif application_type == 'technical_service':
                text += "🔧 Tur: Texnik xizmat\n"
            
            text += f"📝 Tavsif: {data.get('application_description', 'Kiritilmagan')}\n"
            text += f"📍 Manzil: {data.get('application_address', 'Kiritilmagan')}\n"
            
            # Application type specific details
            if application_type == 'connection_request':
                if data.get('connection_type'):
                    text += f"🔌 Ulanish turi: {data['connection_type']}\n"
                if data.get('tariff'):
                    text += f"💰 Tarif: {data['tariff']}\n"
            elif application_type == 'technical_service':
                if data.get('issue_type'):
                    text += f"⚠️ Muammo turi: {data['issue_type']}\n"
            
            # Additional information
            if data.get('priority'):
                priority_text = {
                    'low': 'Past',
                    'medium': 'O\'rta',
                    'high': 'Yuqori',
                    'urgent': 'Shoshilinch'
                }.get(data['priority'], data['priority'])
                text += f"⚡ Muhimlik: {priority_text}\n"
            
            if data.get('media_files'):
                text += f"📎 Media fayllar: {len(data['media_files'])} ta\n"
            
            if data.get('location_data'):
                text += "📍 Joylashuv: Qo'shilgan\n"
            
            text += "\n✅ **Barcha ma'lumotlar to'g'rimi? Yuborish uchun tasdiqlang.**"
            
        else:
            text = "📋 **Просмотр заявки**\n\n"
            
            # Client information
            confirmed_client = data.get('confirmed_client', {})
            text += "👤 **Данные клиента:**\n"
            text += f"📝 Имя: {confirmed_client.get('full_name', 'Не введено')}\n"
            text += f"📞 Телефон: {confirmed_client.get('phone_number', 'Не введен')}\n"
            if confirmed_client.get('address'):
                text += f"📍 Адрес: {confirmed_client['address']}\n"
            text += "\n"
            
            # Application information
            text += "📄 **Данные заявки:**\n"
            application_type = data.get('application_type', '')
            if application_type == 'connection_request':
                text += "🔌 Тип: Заявка на подключение\n"
            elif application_type == 'technical_service':
                text += "🔧 Тип: Техническое обслуживание\n"
            
            text += f"📝 Описание: {data.get('application_description', 'Не введено')}\n"
            text += f"📍 Адрес: {data.get('application_address', 'Не введен')}\n"
            
            # Application type specific details
            if application_type == 'connection_request':
                if data.get('connection_type'):
                    text += f"🔌 Тип подключения: {data['connection_type']}\n"
                if data.get('tariff'):
                    text += f"💰 Тариф: {data['tariff']}\n"
            elif application_type == 'technical_service':
                if data.get('issue_type'):
                    text += f"⚠️ Тип проблемы: {data['issue_type']}\n"
            
            # Additional information
            if data.get('priority'):
                priority_text = {
                    'low': 'Низкий',
                    'medium': 'Средний',
                    'high': 'Высокий',
                    'urgent': 'Срочный'
                }.get(data['priority'], data['priority'])
                text += f"⚡ Приоритет: {priority_text}\n"
            
            if data.get('media_files'):
                text += f"📎 Медиа файлы: {len(data['media_files'])} шт.\n"
            
            if data.get('location_data'):
                text += "📍 Местоположение: Добавлено\n"
            
            text += "\n✅ **Все данные корректны? Подтвердите для отправки.**"
        
        return text
        
    except Exception as e:
        return "Ariza ma'lumotlarini ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения данных заявки"


def format_submission_confirmation_text(data: Dict[str, Any], lang: str = 'uz') -> str:
    """Format final submission confirmation text"""
    try:
        if lang == 'uz':
            text = "⚠️ **Yakuniy tasdiqlash**\n\n"
            text += "Ariza yuborilgandan so'ng uni o'zgartirib bo'lmaydi.\n\n"
            
            # Brief summary
            confirmed_client = data.get('confirmed_client', {})
            application_type = data.get('application_type', '')
            
            text += "📋 **Qisqacha ma'lumot:**\n"
            text += f"👤 Mijoz: {confirmed_client.get('full_name', 'Unknown')}\n"
            
            if application_type == 'connection_request':
                text += "🔌 Tur: Ulanish uchun ariza\n"
            elif application_type == 'technical_service':
                text += "🔧 Tur: Texnik xizmat\n"
            
            text += f"📍 Manzil: {data.get('application_address', 'Kiritilmagan')}\n\n"
            
            text += "✅ **Arizani yuborishni tasdiqlaysizmi?**"
            
        else:
            text = "⚠️ **Окончательное подтверждение**\n\n"
            text += "После отправки заявки её нельзя будет изменить.\n\n"
            
            # Brief summary
            confirmed_client = data.get('confirmed_client', {})
            application_type = data.get('application_type', '')
            
            text += "📋 **Краткая информация:**\n"
            text += f"👤 Клиент: {confirmed_client.get('full_name', 'Unknown')}\n"
            
            if application_type == 'connection_request':
                text += "🔌 Тип: Заявка на подключение\n"
            elif application_type == 'technical_service':
                text += "🔧 Тип: Техническое обслуживание\n"
            
            text += f"📍 Адрес: {data.get('application_address', 'Не введен')}\n\n"
            
            text += "✅ **Подтвердить отправку заявки?**"
        
        return text
        
    except Exception as e:
        return "Tasdiqlash matnini ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения текста подтверждения"


def format_success_message_text(result: Dict[str, Any], lang: str = 'uz') -> str:
    """Format successful submission message"""
    try:
        application_id = result.get('application_id', 'Unknown')
        workflow_type = result.get('workflow_type', '')
        created_at = result.get('created_at', datetime.now())
        
        if lang == 'uz':
            text = "🎉 **Ariza muvaffaqiyatli yaratildi!**\n\n"
            text += f"📋 **Ariza ID:** `{application_id}`\n"
            text += f"📅 **Yaratilgan vaqt:** {created_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            if workflow_type == 'connection_request':
                text += "🔌 **Tur:** Ulanish uchun ariza\n"
            elif workflow_type == 'technical_service':
                text += "🔧 **Tur:** Texnik xizmat\n"
            
            text += "\n✅ Ariza ishlov berish uchun yuborildi.\n"
            text += "📱 Mijoz ariza haqida xabardor qilinadi.\n"
            text += "🔄 Ariza holati avtomatik ravishda kuzatiladi.\n\n"
            text += "**Keyingi qadamlar:**\n"
            text += "• Ariza tegishli xodimga tayinlanadi\n"
            text += "• Mijoz bilan bog'lanish amalga oshiriladi\n"
            text += "• Xizmat ko'rsatish jarayoni boshlanadi"
            
        else:
            text = "🎉 **Заявка успешно создана!**\n\n"
            text += f"📋 **ID заявки:** `{application_id}`\n"
            text += f"📅 **Время создания:** {created_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            if workflow_type == 'connection_request':
                text += "🔌 **Тип:** Заявка на подключение\n"
            elif workflow_type == 'technical_service':
                text += "🔧 **Тип:** Техническое обслуживание\n"
            
            text += "\n✅ Заявка отправлена на обработку.\n"
            text += "📱 Клиент будет уведомлен о заявке.\n"
            text += "🔄 Статус заявки отслеживается автоматически.\n\n"
            text += "**Следующие шаги:**\n"
            text += "• Заявка будет назначена соответствующему сотруднику\n"
            text += "• Будет осуществлен контакт с клиентом\n"
            text += "• Начнется процесс предоставления услуги"
        
        return text
        
    except Exception as e:
        return "Muvaffaqiyat xabarini ko'rsatishda xatolik" if lang == 'uz' else "Ошибка отображения сообщения об успехе"


def format_error_message_text(error_result: Dict[str, Any], lang: str = 'uz') -> str:
    """Format error message with details and suggestions"""
    try:
        error_type = error_result.get('error_type', 'unknown')
        error_message = error_result.get('error_message', 'Unknown error')
        error_details = error_result.get('error_details', {})
        
        if lang == 'uz':
            text = "❌ **Ariza yuborishda xatolik**\n\n"
            
            # Error type specific messages
            if error_type == 'validation_error':
                text += "⚠️ **Ma'lumotlar tekshiruvi xatosi**\n"
                text += "Ba'zi ma'lumotlar noto'g'ri yoki to'liq emas.\n\n"
                text += "**Xato tafsilotlari:**\n"
                if isinstance(error_details, dict):
                    for field, issue in error_details.items():
                        text += f"• {field}: {issue}\n"
                else:
                    text += f"• {error_message}\n"
                text += "\n🔧 Ma'lumotlarni tekshiring va qayta urinib ko'ring."
                
            elif error_type == 'client_validation_error':
                text += "👤 **Mijoz ma'lumotlari xatosi**\n"
                text += "Mijoz ma'lumotlarida muammo bor.\n\n"
                text += f"**Xato:** {error_message}\n\n"
                text += "🔧 Mijoz ma'lumotlarini tekshiring va tuzating."
                
            elif error_type == 'workflow_error':
                text += "🔄 **Ish jarayoni xatosi**\n"
                text += "Ariza ish jarayoniga qo'shishda muammo yuz berdi.\n\n"
                text += f"**Xato:** {error_message}\n\n"
                text += "🔄 Bir oz kutib qayta urinib ko'ring."
                
            elif error_type == 'permission_denied':
                text += "🚫 **Ruxsat rad etildi**\n"
                text += "Sizda bu amalni bajarish huquqi yo'q.\n\n"
                text += f"**Sabab:** {error_message}\n\n"
                text += "👨‍💼 Administrator bilan bog'laning."
                
            else:
                text += "🔧 **Tizim xatosi**\n"
                text += "Kutilmagan xatolik yuz berdi.\n\n"
                text += f"**Xato:** {error_message}\n\n"
                text += "🔄 Qayta urinib ko'ring yoki administrator bilan bog'laning."
            
        else:
            text = "❌ **Ошибка отправки заявки**\n\n"
            
            # Error type specific messages
            if error_type == 'validation_error':
                text += "⚠️ **Ошибка проверки данных**\n"
                text += "Некоторые данные неверны или неполны.\n\n"
                text += "**Детали ошибки:**\n"
                if isinstance(error_details, dict):
                    for field, issue in error_details.items():
                        text += f"• {field}: {issue}\n"
                else:
                    text += f"• {error_message}\n"
                text += "\n🔧 Проверьте данные и попробуйте снова."
                
            elif error_type == 'client_validation_error':
                text += "👤 **Ошибка данных клиента**\n"
                text += "Проблема с данными клиента.\n\n"
                text += f"**Ошибка:** {error_message}\n\n"
                text += "🔧 Проверьте и исправьте данные клиента."
                
            elif error_type == 'workflow_error':
                text += "🔄 **Ошибка рабочего процесса**\n"
                text += "Проблема при добавлении заявки в рабочий процесс.\n\n"
                text += f"**Ошибка:** {error_message}\n\n"
                text += "🔄 Подождите немного и попробуйте снова."
                
            elif error_type == 'permission_denied':
                text += "🚫 **Доступ запрещен**\n"
                text += "У вас нет прав для выполнения этого действия.\n\n"
                text += f"**Причина:** {error_message}\n\n"
                text += "👨‍💼 Обратитесь к администратору."
                
            else:
                text += "🔧 **Системная ошибка**\n"
                text += "Произошла неожиданная ошибка.\n\n"
                text += f"**Ошибка:** {error_message}\n\n"
                text += "🔄 Попробуйте снова или обратитесь к администратору."
        
        return text
        
    except Exception as e:
        return "Xato xabarini ko'rsatishda muammo" if lang == 'uz' else "Проблема отображения сообщения об ошибке"


# Additional utility keyboards
def get_application_type_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get keyboard for selecting application type"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="🔌 Ulanish uchun ariza", callback_data="app_type_connection")],
            [InlineKeyboardButton(text="🔧 Texnik xizmat", callback_data="app_type_technical")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="app_cancel")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🔌 Заявка на подключение", callback_data="app_type_connection")],
            [InlineKeyboardButton(text="🔧 Техническое обслуживание", callback_data="app_type_technical")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="app_cancel")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_preview_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get simple back to preview keyboard"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="app_back_to_preview")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="◀️ Назад", callback_data="app_back_to_preview")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Export all functions
__all__ = [
    'get_application_preview_keyboard',
    'get_application_edit_keyboard', 
    'get_submission_confirmation_keyboard',
    'get_submission_success_keyboard',
    'get_error_retry_keyboard',
    'get_validation_error_keyboard',
    'format_application_preview_text',
    'format_submission_confirmation_text',
    'format_success_message_text',
    'format_error_message_text',
    'get_application_type_keyboard',
    'get_back_to_preview_keyboard'
]