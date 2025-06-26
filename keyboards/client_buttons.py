from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from utils.i18n import i18n
from typing import List, Dict, Any
import hashlib

def safe_callback_data(data: str, max_length: int = 64) -> str:
    """Create safe callback data within Telegram limits"""
    if len(data) <= max_length:
        return data
    
    # Create hash for long data
    hash_obj = hashlib.md5(data.encode())
    return f"hash_{hash_obj.hexdigest()[:50]}"

def get_contact_keyboard(lang="uz"):
    """Kontakt ulashish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i18n.get_message(lang, "share_contact"), request_contact=True)]],
        resize_keyboard=True
    )
    return keyboard

def get_main_menu_keyboard(lang="uz"):
    """Asosiy menyu klaviaturasi - 2 ustunli, 2 qatorli"""
    buttons = [
        [
            KeyboardButton(text=i18n.get_message(lang, "new_order")),
            KeyboardButton(text=i18n.get_message(lang, "my_orders"))
        ],
        [
            KeyboardButton(text=i18n.get_message(lang, "contact_operator")),
            KeyboardButton(text=i18n.get_message(lang, "change_language"))
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard

def get_back_keyboard(lang="uz"):
    """Foydalanuvchiga har doim faqat 'Asosiy menyu' tugmasini chiqaradi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get_message(lang, "main_menu"))]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_reply_keyboard(lang="uz"):
    """4 button keyboard for reply confirmation - 2 tilda"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n.get_message(lang, "confirm")),
                KeyboardButton(text=i18n.get_message(lang, "cancel"))
            ],
            [
                KeyboardButton(text=i18n.get_message(lang, "back")),
                KeyboardButton(text=i18n.get_message(lang, "main_menu"))
            ]
        ],
        resize_keyboard=True
    )

def get_language_keyboard():
    """Til tanlash klaviaturasi - har doim bir xil"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
        ]
    )
    return keyboard

def zayavka_type_keyboard(lang="uz"):
    """Zayavka turini tanlash klaviaturasi - 2 tilda"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get_message(lang, "person_physical"), callback_data="zayavka_type_b2b")],
            [InlineKeyboardButton(text=i18n.get_message(lang, "person_legal"), callback_data="zayavka_type_b2c")]
        ]
    )
    return keyboard

def media_attachment_keyboard(lang="uz"):
    """Media biriktirish klaviaturasi - 2 tilda"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.get_message(lang, "yes"), callback_data="attach_media_yes")],
        [InlineKeyboardButton(text=i18n.get_message(lang, "no"), callback_data="attach_media_no")]
    ])
    return keyboard

def geolocation_keyboard(lang="uz"):
    """Geolokatsiya klaviaturasi - 2 tilda"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.get_message(lang, "yes"), callback_data="send_location_yes")],
        [InlineKeyboardButton(text=i18n.get_message(lang, "no"), callback_data="send_location_no")]
    ])
    return keyboard

def confirmation_keyboard(lang="uz"):
    """Tasdiqlash klaviaturasi - 2 tilda"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=i18n.get_message(lang, "confirm"), callback_data="confirm_zayavka"),
            InlineKeyboardButton(text=i18n.get_message(lang, "resend"), callback_data="resend_zayavka")
        ]
    ])
    return keyboard
