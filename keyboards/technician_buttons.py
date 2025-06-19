from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from utils.i18n import i18n

def get_contact_keyboard(lang="uz"):
    """Kontakt ulashish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i18n.get_message(lang, "share_contact"), request_contact=True)]],
        resize_keyboard=True
    )
    return keyboard

def get_technician_main_menu_keyboard(lang="uz"):
    """Montajchi asosiy menyu klaviaturasi"""
    buttons = [
        i18n.get_message(lang, "new_tasks"),
        i18n.get_message(lang, "my_tasks"),
        i18n.get_message(lang, "reports"),
        i18n.get_message(lang, "change_language")
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text)] for text in buttons],
        resize_keyboard=True
    )
    return keyboard

def get_back_keyboard(lang="uz"):
    """Orqaga qaytish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n.get_message(lang, "back"))
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_language_keyboard():
    """Til tanlash klaviaturasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
        ]
    )
    return keyboard
