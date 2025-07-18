"""
Client Search and Selection UI Keyboards
Provides keyboard interfaces for staff members to search, select, and create clients
"""

from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any, Optional


def get_client_search_method_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for selecting client search method
    
    Args:
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with search method options
    """
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(
                text="📞 Telefon raqami bo'yicha", 
                callback_data="client_search_phone"
            )],
            [InlineKeyboardButton(
                text="👤 Ism bo'yicha", 
                callback_data="client_search_name"
            )],
            [InlineKeyboardButton(
                text="🆔 ID raqami bo'yicha", 
                callback_data="client_search_id"
            )],
            [InlineKeyboardButton(
                text="➕ Yangi mijoz yaratish", 
                callback_data="client_create_new"
            )],
            [InlineKeyboardButton(
                text="◀️ Orqaga", 
                callback_data="staff_app_back_to_type_selection"
            )]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(
                text="📞 По номеру телефона", 
                callback_data="client_search_phone"
            )],
            [InlineKeyboardButton(
                text="👤 По имени", 
                callback_data="client_search_name"
            )],
            [InlineKeyboardButton(
                text="🆔 По ID", 
                callback_data="client_search_id"
            )],
            [InlineKeyboardButton(
                text="➕ Создать нового клиента", 
                callback_data="client_create_new"
            )],
            [InlineKeyboardButton(
                text="◀️ Назад", 
                callback_data="staff_app_back_to_type_selection"
            )]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_client_search_input_keyboard(search_method: str, lang: str = 'uz') -> ReplyKeyboardMarkup:
    """
    Keyboard for client search input with cancel option
    
    Args:
        search_method: Type of search ('phone', 'name', 'id')
        lang: Language code ('uz' or 'ru')
        
    Returns:
        ReplyKeyboardMarkup with cancel button
    """
    if lang == 'uz':
        cancel_text = "❌ Bekor qilish"
        back_text = "◀️ Orqaga"
    else:
        cancel_text = "❌ Отменить"
        back_text = "◀️ Назад"
    
    keyboard = [
        [KeyboardButton(text=cancel_text)],
        [KeyboardButton(text=back_text)]
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_client_selection_keyboard(clients: List[Dict[str, Any]], lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for selecting from multiple found clients
    
    Args:
        clients: List of client dictionaries
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with client selection options
    """
    builder = InlineKeyboardBuilder()
    
    # Add client selection buttons (limit to 8 for UI clarity)
    for i, client in enumerate(clients[:8]):
        client_name = client.get('full_name', 'Unknown')
        client_phone = client.get('phone_number', 'No phone')
        client_id = client.get('id', 'Unknown')
        
        # Truncate long names for button display
        display_name = client_name[:20] + "..." if len(client_name) > 20 else client_name
        button_text = f"👤 {display_name} - {client_phone}"
        
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"client_select_{client_id}"
        ))
    
    # Add "Create new client" option if search didn't find exact match
    if lang == 'uz':
        builder.add(InlineKeyboardButton(
            text="➕ Yangi mijoz yaratish",
            callback_data="client_create_new"
        ))
        builder.add(InlineKeyboardButton(
            text="🔍 Qayta qidirish",
            callback_data="client_search_again"
        ))
        builder.add(InlineKeyboardButton(
            text="◀️ Orqaga",
            callback_data="staff_app_back_to_search_method"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="➕ Создать нового клиента",
            callback_data="client_create_new"
        ))
        builder.add(InlineKeyboardButton(
            text="🔍 Поиск заново",
            callback_data="client_search_again"
        ))
        builder.add(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="staff_app_back_to_search_method"
        ))
    
    # Adjust layout: 1 client per row, then control buttons
    builder.adjust(1)
    
    return builder.as_markup()


def get_client_confirmation_keyboard(client_data: Dict[str, Any], lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for confirming selected client
    
    Args:
        client_data: Selected client data
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with confirmation options
    """
    client_id = client_data.get('id', 0)
    
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"client_confirm_{client_id}"
            )],
            [InlineKeyboardButton(
                text="✏️ Ma'lumotlarni ko'rish",
                callback_data=f"client_view_details_{client_id}"
            )],
            [InlineKeyboardButton(
                text="🔍 Boshqa mijoz tanlash",
                callback_data="client_search_again"
            )],
            [InlineKeyboardButton(
                text="◀️ Orqaga",
                callback_data="staff_app_back_to_search_method"
            )]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"client_confirm_{client_id}"
            )],
            [InlineKeyboardButton(
                text="✏️ Просмотр данных",
                callback_data=f"client_view_details_{client_id}"
            )],
            [InlineKeyboardButton(
                text="🔍 Выбрать другого клиента",
                callback_data="client_search_again"
            )],
            [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="staff_app_back_to_search_method"
            )]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_new_client_form_keyboard(step: str, lang: str = 'uz') -> ReplyKeyboardMarkup:
    """
    Keyboard for new client creation form steps
    
    Args:
        step: Current form step ('name', 'phone', 'address')
        lang: Language code ('uz' or 'ru')
        
    Returns:
        ReplyKeyboardMarkup with appropriate options for the step
    """
    if lang == 'uz':
        skip_text = "⏭️ O'tkazib yuborish"
        cancel_text = "❌ Bekor qilish"
        back_text = "◀️ Orqaga"
    else:
        skip_text = "⏭️ Пропустить"
        cancel_text = "❌ Отменить"
        back_text = "◀️ Назад"
    
    keyboard = []
    
    # Address step can be skipped
    if step == 'address':
        keyboard.append([KeyboardButton(text=skip_text)])
    
    keyboard.extend([
        [KeyboardButton(text=cancel_text)],
        [KeyboardButton(text=back_text)]
    ])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_new_client_confirmation_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for confirming new client creation
    
    Args:
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with confirmation options
    """
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(
                text="✅ Mijozni yaratish",
                callback_data="new_client_confirm_create"
            )],
            [InlineKeyboardButton(
                text="✏️ Ismni o'zgartirish",
                callback_data="new_client_edit_name"
            )],
            [InlineKeyboardButton(
                text="📞 Telefonni o'zgartirish",
                callback_data="new_client_edit_phone"
            )],
            [InlineKeyboardButton(
                text="📍 Manzilni o'zgartirish",
                callback_data="new_client_edit_address"
            )],
            [InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="new_client_cancel"
            )]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(
                text="✅ Создать клиента",
                callback_data="new_client_confirm_create"
            )],
            [InlineKeyboardButton(
                text="✏️ Изменить имя",
                callback_data="new_client_edit_name"
            )],
            [InlineKeyboardButton(
                text="📞 Изменить телефон",
                callback_data="new_client_edit_phone"
            )],
            [InlineKeyboardButton(
                text="📍 Изменить адрес",
                callback_data="new_client_edit_address"
            )],
            [InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="new_client_cancel"
            )]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_client_details_keyboard(client_id: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for viewing and editing client details
    
    Args:
        client_id: Client database ID
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with client detail options
    """
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(
                text="✅ Bu mijozni tanlash",
                callback_data=f"client_confirm_{client_id}"
            )],
            [InlineKeyboardButton(
                text="✏️ Ma'lumotlarni yangilash",
                callback_data=f"client_edit_{client_id}"
            )],
            [InlineKeyboardButton(
                text="📋 Arizalar tarixi",
                callback_data=f"client_history_{client_id}"
            )],
            [InlineKeyboardButton(
                text="🔍 Boshqa mijoz qidirish",
                callback_data="client_search_again"
            )],
            [InlineKeyboardButton(
                text="◀️ Orqaga",
                callback_data="staff_app_back_to_search_method"
            )]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(
                text="✅ Выбрать этого клиента",
                callback_data=f"client_confirm_{client_id}"
            )],
            [InlineKeyboardButton(
                text="✏️ Обновить данные",
                callback_data=f"client_edit_{client_id}"
            )],
            [InlineKeyboardButton(
                text="📋 История заявок",
                callback_data=f"client_history_{client_id}"
            )],
            [InlineKeyboardButton(
                text="🔍 Найти другого клиента",
                callback_data="client_search_again"
            )],
            [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="staff_app_back_to_search_method"
            )]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_client_edit_keyboard(client_id: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for editing client information
    
    Args:
        client_id: Client database ID
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with edit options
    """
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(
                text="✏️ Ismni o'zgartirish",
                callback_data=f"client_edit_name_{client_id}"
            )],
            [InlineKeyboardButton(
                text="📞 Telefonni o'zgartirish",
                callback_data=f"client_edit_phone_{client_id}"
            )],
            [InlineKeyboardButton(
                text="📍 Manzilni o'zgartirish",
                callback_data=f"client_edit_address_{client_id}"
            )],
            [InlineKeyboardButton(
                text="🌐 Tilni o'zgartirish",
                callback_data=f"client_edit_language_{client_id}"
            )],
            [InlineKeyboardButton(
                text="✅ O'zgarishlarni saqlash",
                callback_data=f"client_save_changes_{client_id}"
            )],
            [InlineKeyboardButton(
                text="◀️ Orqaga",
                callback_data=f"client_view_details_{client_id}"
            )]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(
                text="✏️ Изменить имя",
                callback_data=f"client_edit_name_{client_id}"
            )],
            [InlineKeyboardButton(
                text="📞 Изменить телефон",
                callback_data=f"client_edit_phone_{client_id}"
            )],
            [InlineKeyboardButton(
                text="📍 Изменить адрес",
                callback_data=f"client_edit_address_{client_id}"
            )],
            [InlineKeyboardButton(
                text="🌐 Изменить язык",
                callback_data=f"client_edit_language_{client_id}"
            )],
            [InlineKeyboardButton(
                text="✅ Сохранить изменения",
                callback_data=f"client_save_changes_{client_id}"
            )],
            [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"client_view_details_{client_id}"
            )]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_client_language_selection_keyboard(client_id: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for selecting client language
    
    Args:
        client_id: Client database ID
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with language options
    """
    buttons = [
        [InlineKeyboardButton(
            text="🇺🇿 O'zbek tili",
            callback_data=f"client_set_lang_uz_{client_id}"
        )],
        [InlineKeyboardButton(
            text="🇷🇺 Русский язык",
            callback_data=f"client_set_lang_ru_{client_id}"
        )],
        [InlineKeyboardButton(
            text="◀️ Orqaga" if lang == 'uz' else "◀️ Назад",
            callback_data=f"client_edit_{client_id}"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_search_error_keyboard(error_type: str, lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for handling search errors
    
    Args:
        error_type: Type of error ('not_found', 'invalid_input', 'multiple_found', 'database_error')
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with error handling options
    """
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(
                text="🔍 Qayta qidirish",
                callback_data="client_search_again"
            )],
            [InlineKeyboardButton(
                text="➕ Yangi mijoz yaratish",
                callback_data="client_create_new"
            )],
            [InlineKeyboardButton(
                text="◀️ Orqaga",
                callback_data="staff_app_back_to_search_method"
            )]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(
                text="🔍 Поиск заново",
                callback_data="client_search_again"
            )],
            [InlineKeyboardButton(
                text="➕ Создать нового клиента",
                callback_data="client_create_new"
            )],
            [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="staff_app_back_to_search_method"
            )]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_client_history_keyboard(client_id: int, page: int = 1, total_pages: int = 1, lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for client application history with pagination
    
    Args:
        client_id: Client database ID
        page: Current page number
        total_pages: Total number of pages
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with history navigation
    """
    builder = InlineKeyboardBuilder()
    
    # Pagination buttons
    if page > 1:
        prev_text = "◀️ Oldingi" if lang == 'uz' else "◀️ Предыдущая"
        builder.add(InlineKeyboardButton(
            text=prev_text,
            callback_data=f"client_history_{client_id}_page_{page-1}"
        ))
    
    if page < total_pages:
        next_text = "Keyingi ▶️" if lang == 'uz' else "Следующая ▶️"
        builder.add(InlineKeyboardButton(
            text=next_text,
            callback_data=f"client_history_{client_id}_page_{page+1}"
        ))
    
    # Page info
    if total_pages > 1:
        builder.add(InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data=f"client_history_page_info"
        ))
    
    # Control buttons
    if lang == 'uz':
        builder.add(InlineKeyboardButton(
            text="✅ Bu mijozni tanlash",
            callback_data=f"client_confirm_{client_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="◀️ Orqaga",
            callback_data=f"client_view_details_{client_id}"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="✅ Выбрать этого клиента",
            callback_data=f"client_confirm_{client_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"client_view_details_{client_id}"
        ))
    
    # Adjust layout
    builder.adjust(2, 1, 2)  # 2 nav buttons, 1 page info, 2 control buttons
    
    return builder.as_markup()


def get_validation_error_keyboard(error_field: str, lang: str = 'uz') -> InlineKeyboardMarkup:
    """
    Keyboard for handling validation errors
    
    Args:
        error_field: Field that failed validation ('name', 'phone', 'address')
        lang: Language code ('uz' or 'ru')
        
    Returns:
        InlineKeyboardMarkup with error handling options
    """
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(
                text="✏️ Qayta kiritish",
                callback_data=f"client_retry_input_{error_field}"
            )],
            [InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="client_cancel_creation"
            )],
            [InlineKeyboardButton(
                text="◀️ Orqaga",
                callback_data="staff_app_back_to_search_method"
            )]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(
                text="✏️ Ввести заново",
                callback_data=f"client_retry_input_{error_field}"
            )],
            [InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="client_cancel_creation"
            )],
            [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="staff_app_back_to_search_method"
            )]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Utility functions for keyboard generation
def format_client_display_text(client_data: Dict[str, Any], lang: str = 'uz') -> str:
    """
    Format client data for display in keyboards and messages
    
    Args:
        client_data: Client information dictionary
        lang: Language code ('uz' or 'ru')
        
    Returns:
        Formatted client display text
    """
    name = client_data.get('full_name', 'Unknown')
    phone = client_data.get('phone_number', 'No phone')
    client_id = client_data.get('id', 'Unknown')
    address = client_data.get('address', '')
    language = client_data.get('language', 'uz')
    
    if lang == 'uz':
        text = f"👤 **Mijoz ma'lumotlari:**\n\n"
        text += f"📝 **Ism:** {name}\n"
        text += f"📞 **Telefon:** {phone}\n"
        text += f"🆔 **ID:** {client_id}\n"
        if address:
            text += f"📍 **Manzil:** {address}\n"
        text += f"🌐 **Til:** {'O\'zbek' if language == 'uz' else 'Rus'}\n"
    else:
        text = f"👤 **Данные клиента:**\n\n"
        text += f"📝 **Имя:** {name}\n"
        text += f"📞 **Телефон:** {phone}\n"
        text += f"🆔 **ID:** {client_id}\n"
        if address:
            text += f"📍 **Адрес:** {address}\n"
        text += f"🌐 **Язык:** {'Узбекский' if language == 'uz' else 'Русский'}\n"
    
    return text


def get_search_prompt_text(search_method: str, lang: str = 'uz') -> str:
    """
    Get prompt text for different search methods
    
    Args:
        search_method: Type of search ('phone', 'name', 'id')
        lang: Language code ('uz' or 'ru')
        
    Returns:
        Prompt text for the search method
    """
    prompts = {
        'uz': {
            'phone': "📞 **Mijoz telefon raqamini kiriting:**\n\nMisol: +998901234567 yoki 901234567",
            'name': "👤 **Mijoz ismini kiriting:**\n\nTo'liq ism yoki ism qismini yozing",
            'id': "🆔 **Mijoz ID raqamini kiriting:**\n\nFaqat raqamlarni kiriting"
        },
        'ru': {
            'phone': "📞 **Введите номер телефона клиента:**\n\nПример: +998901234567 или 901234567",
            'name': "👤 **Введите имя клиента:**\n\nПолное имя или часть имени",
            'id': "🆔 **Введите ID клиента:**\n\nТолько цифры"
        }
    }
    
    return prompts.get(lang, {}).get(search_method, "Enter search criteria")


def get_new_client_form_prompt(step: str, lang: str = 'uz') -> str:
    """
    Get prompt text for new client form steps
    
    Args:
        step: Form step ('name', 'phone', 'address')
        lang: Language code ('uz' or 'ru')
        
    Returns:
        Prompt text for the form step
    """
    prompts = {
        'uz': {
            'name': "👤 **Yangi mijoz ismini kiriting:**\n\nTo'liq ism va familiyani yozing",
            'phone': "📞 **Mijoz telefon raqamini kiriting:**\n\nMisol: +998901234567 yoki 901234567",
            'address': "📍 **Mijoz manzilini kiriting:**\n\n(Ixtiyoriy - o'tkazib yuborishingiz mumkin)"
        },
        'ru': {
            'name': "👤 **Введите имя нового клиента:**\n\nПолное имя и фамилию",
            'phone': "📞 **Введите номер телефона клиента:**\n\nПример: +998901234567 или 901234567",
            'address': "📍 **Введите адрес клиента:**\n\n(Необязательно - можно пропустить)"
        }
    }
    
    return prompts.get(lang, {}).get(step, "Enter information")


# Export all keyboard functions
__all__ = [
    'get_client_search_method_keyboard',
    'get_client_search_input_keyboard',
    'get_client_selection_keyboard',
    'get_client_confirmation_keyboard',
    'get_new_client_form_keyboard',
    'get_new_client_confirmation_keyboard',
    'get_client_details_keyboard',
    'get_client_edit_keyboard',
    'get_client_language_selection_keyboard',
    'get_search_error_keyboard',
    'get_client_history_keyboard',
    'get_validation_error_keyboard',
    'format_client_display_text',
    'get_search_prompt_text',
    'get_new_client_form_prompt'
]