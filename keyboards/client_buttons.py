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

def get_language_selection_keyboard():
    """Til tanlash uchun inline keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="select_lang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="select_lang_ru")]
        ]
    )
    return keyboard

def get_contact_keyboard(lang="uz"):
    """Kontakt ulashish klaviaturasi"""
    share_contact_text = "📱 Kontakt ulashish" if lang == "uz" else "📱 Поделиться контактом"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=share_contact_text, request_contact=True)]],
        resize_keyboard=True
    )
    return keyboard

def get_main_menu_keyboard(lang="uz"):
    """Asosiy menyu klaviaturasi - 2 ustunli, 3 qatorli"""
    service_order_text = "🆕 Texnik xizmat" if lang == "uz" else "🆕 Техническая поддержка"
    connection_order_text = "🔌 Ulanish uchun ariza" if lang == "uz" else "🔌 Заявка на подключение"
    my_orders_text = "📋 Mening buyurtmalarim" if lang == "uz" else "📋 Мои заказы"
    contact_operator_text = "📞 Operator bilan bog'lanish" if lang == "uz" else "📞 Связаться с оператором"
    change_language_text = "🌐 Til o'zgartirish" if lang == "uz" else "🌐 Изменить язык"
    profile_text = "👤 Profil" if lang == "uz" else "👤 Профиль"
    help_text = "❓ Yordam" if lang == "uz" else "❓ Помощь"
    
    buttons = [
        [
            KeyboardButton(text=service_order_text),
            KeyboardButton(text=connection_order_text)
        ],
        [
            KeyboardButton(text=my_orders_text)
        ],
        [
            KeyboardButton(text=contact_operator_text),
            KeyboardButton(text=profile_text)
        ],
        [
            KeyboardButton(text=help_text),
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

def get_client_profile_menu(lang="uz"):
    """Client profile menu"""
    view_info_text = "👁️ Ma'lumotlarni ko'rish" if lang == "uz" else "👁️ Просмотр информации"
    view_orders_text = "🔄 Mening arizalarim" if lang == "uz" else "🔄 Мои заявки"
    edit_profile_text = "✏️ Ma'lumotlarni o'zgartirish" if lang == "uz" else "✏️ Редактировать информацию"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=view_info_text,
                callback_data="client_view_info"
            ),
            InlineKeyboardButton(
                text=view_orders_text,
                callback_data="client_order_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text=edit_profile_text,
                callback_data="client_edit_profile"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_to_profile_menu(lang="uz"):
    """Back button for profile menu"""
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=back_text, callback_data="client_profile_back")]]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_client_help_menu(lang="uz"):
    """Client help menu"""
    faq_text = "❓ Tez-tez so'raladigan savollar" if lang == "uz" else "❓ Часто задаваемые вопросы"
    contact_support_text = "📞 Qo'llab-quvvatlash xizmati" if lang == "uz" else "📞 Служба поддержки"
    how_to_order_text = "📝 Qanday buyurtma berish" if lang == "uz" else "📝 Как сделать заказ"
    track_order_text = "📍 Buyurtmani kuzatish" if lang == "uz" else "📍 Отслеживание заказа"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=faq_text,
                callback_data="client_faq"
            )
        ],
        [
            InlineKeyboardButton(
                text=how_to_order_text,
                callback_data="client_how_to_order"
            )
        ],
        [
            InlineKeyboardButton(
                text=track_order_text,
                callback_data="client_track_order"
            )
        ],
        [
            InlineKeyboardButton(
                text=contact_support_text,
                callback_data="client_contact_support"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_client_help_back_inline(lang="uz"):
    """Faqat orqaga tugmasi uchun inline keyboard"""
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    keyboard = [
        [InlineKeyboardButton(
            text=back_text,
            callback_data="client_back_help"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_client_profile_edit_menu(lang="uz"):
    """Client profile edit menu"""
    edit_name_text = "✏️ Ism o'zgartirish" if lang == "uz" else "✏️ Изменить имя"
    edit_address_text = "📍 Manzil o'zgartirish" if lang == "uz" else "📍 Изменить адрес"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=edit_name_text,
                callback_data="client_edit_name"
            )
        ],
        [
            InlineKeyboardButton(
                text=edit_address_text,
                callback_data="client_edit_address"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Orqaga" if lang == "uz" else "◀️ Назад",
                callback_data="client_profile_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_edit_keyboard(lang="uz"):
    """Cancel edit keyboard"""
    cancel_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отменить"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=cancel_text, callback_data="client_profile_back")]]
    )
    return keyboard
