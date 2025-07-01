from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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
    share_contact_text = "📱 Kontakt ulashish" if lang == "uz" else "📱 Поделиться контактом"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=share_contact_text, request_contact=True)]],
        resize_keyboard=True
    )
    return keyboard

def get_main_menu_keyboard(lang="uz"):
    """Asosiy menyu klaviaturasi - 2 ustunli, 2 qatorli"""
    new_order_text = "🆕 Yangi buyurtma" if lang == "uz" else "🆕 Новый заказ"
    my_orders_text = "📋 Mening buyurtmalarim" if lang == "uz" else "📋 Мои заказы"
    contact_operator_text = "📞 Operator bilan bog'lanish" if lang == "uz" else "📞 Связаться с оператором"
    change_language_text = "🌐 Til o'zgartirish" if lang == "uz" else "🌐 Изменить язык"
    
    buttons = [
        [
            KeyboardButton(text=new_order_text),
            KeyboardButton(text=my_orders_text)
        ],
        [
            KeyboardButton(text=contact_operator_text),
            KeyboardButton(text=change_language_text)
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard

def get_back_keyboard(lang="uz"):
    """Foydalanuvchiga har doim faqat 'Asosiy menyu' tugmasini chiqaradi"""
    main_menu_text = "🏠 Asosiy menyu" if lang == "uz" else "🏠 Главное меню"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=main_menu_text)]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_reply_keyboard(lang="uz"):
    """4 button keyboard for reply confirmation - 2 tilda"""
    confirm_text = "✅ Tasdiqlash" if lang == "uz" else "✅ Подтвердить"
    cancel_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отменить"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    main_menu_text = "🏠 Asosiy menyu" if lang == "uz" else "🏠 Главное меню"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=confirm_text),
                KeyboardButton(text=cancel_text)
            ],
            [
                KeyboardButton(text=back_text),
                KeyboardButton(text=main_menu_text)
            ]
        ],
        resize_keyboard=True
    )

def get_language_keyboard(role="client"):
    """Til tanlash klaviaturasi - role asosida callback data"""
    prefix = f"{role}_lang_" if role != "client" else "client_lang_"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data=f"{prefix}uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"{prefix}ru")]
        ]
    )
    return keyboard

def zayavka_type_keyboard(lang="uz"):
    """Zayavka turini tanlash klaviaturasi - 2 tilda"""
    person_physical_text = "👤 Jismoniy shaxs" if lang == "uz" else "👤 Физическое лицо"
    person_legal_text = "🏢 Yuridik shaxs" if lang == "uz" else "🏢 Юридическое лицо"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=person_physical_text, callback_data="zayavka_type_b2b")],
            [InlineKeyboardButton(text=person_legal_text, callback_data="zayavka_type_b2c")]
        ]
    )
    return keyboard

def media_attachment_keyboard(lang="uz"):
    """Media biriktirish klaviaturasi - 2 tilda"""
    yes_text = "✅ Ha" if lang == "uz" else "✅ Да"
    no_text = "❌ Yo'q" if lang == "uz" else "❌ Нет"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=yes_text, callback_data="attach_media_yes")],
        [InlineKeyboardButton(text=no_text, callback_data="attach_media_no")]
    ])
    return keyboard

def geolocation_keyboard(lang="uz"):
    """Geolokatsiya klaviaturasi - 2 tilda"""
    yes_text = "✅ Ha" if lang == "uz" else "✅ Да"
    no_text = "❌ Yo'q" if lang == "uz" else "❌ Нет"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=yes_text, callback_data="send_location_yes")],
        [InlineKeyboardButton(text=no_text, callback_data="send_location_no")]
    ])
    return keyboard

def confirmation_keyboard(lang="uz"):
    """Tasdiqlash klaviaturasi - 2 tilda"""
    confirm_text = "✅ Tasdiqlash" if lang == "uz" else "✅ Подтвердить"
    resend_text = "🔄 Qayta yuborish" if lang == "uz" else "🔄 Отправить заново"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=confirm_text, callback_data="confirm_zayavka"),
            InlineKeyboardButton(text=resend_text, callback_data="resend_zayavka")
        ]
    ])
    return keyboard
