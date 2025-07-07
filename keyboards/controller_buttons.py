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
