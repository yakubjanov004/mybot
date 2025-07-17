from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any
from utils.logger import logger

def get_technicians_keyboard(technicians: List[Dict[str, Any]], lang: str) -> InlineKeyboardMarkup:
    """Create keyboard for technicians list"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for tech in technicians:
        status = "🟢" if tech['is_active'] else "🔴"
        button_text = f"{status} {tech['full_name']}"
        callback_data = f"technician:view:{tech['id']}"
        keyboard.add(
            InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )
        )
    
    return keyboard

def get_technician_details_keyboard(technician_id: int, lang: str) -> InlineKeyboardMarkup:
    """Create keyboard for technician details"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Status toggle button
    status_text = {
        'uz': "Statusni o'zgartirish",
        'ru': "Изменить статус"
    }[lang]
    
    keyboard.add(
        InlineKeyboardButton(
            text=status_text,
            callback_data=f"technician:status:{technician_id}"
        )
    )
    
    # Back button
    back_text = {
        'uz': "⬅️ Orqaga",
        'ru': "⬅️ Назад"
    }[lang]
    
    keyboard.add(
        InlineKeyboardButton(
            text=back_text,
            callback_data="back_to_technicians"
        )
    )
    
    return keyboard

def get_application_keyboard(app_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for an application"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👁️ Ko'rish", callback_data=f"view_app_{app_id}"),
                InlineKeyboardButton(text="👨‍🔧 Texnikga yuborish", callback_data=f"assign_tech_{app_id}")
            ]
        ]
    )
    return keyboard

def technical_service_assignment_keyboard(request_id: str, technicians: List[Dict[str, Any]], lang: str) -> InlineKeyboardMarkup:
    """Create keyboard for technical service assignment to technicians"""
    keyboard = []
    
    for tech in technicians:
        status_emoji = "🟢" if tech.get('is_active', True) else "🔴"
        button_text = f"{status_emoji} {tech['full_name']}"
        callback_data = f"assign_technical_to_technician_{tech['id']}_{request_id}"
        
        keyboard.append([InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        )])
    
    # Add back button
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    keyboard.append([InlineKeyboardButton(
        text=back_text,
        callback_data="back_to_technical_requests"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
