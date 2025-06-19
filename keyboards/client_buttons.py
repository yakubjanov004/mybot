from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from utils.i18n import i18n

def get_contact_keyboard(lang="uz"):
    """Kontakt ulashish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i18n.get_message(lang, "share_contact"), request_contact=True)]],
        resize_keyboard=True
    )
    return keyboard

def get_main_menu_keyboard(lang="uz"):
    """Asosiy menyu klaviaturasi"""
    buttons = [
        i18n.get_message(lang, "new_order"),
        i18n.get_message(lang, "my_orders"),
        i18n.get_message(lang, "contact_operator"),
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

def get_reply_keyboard(lang="uz"):
    """4 button keyboard for reply confirmation"""
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
    """Til tanlash klaviaturasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
        ]
    )
    return keyboard

def zayavka_type_keyboard():
    """Zayavka turini tanlash klaviaturasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="B2B", callback_data="zayavka_type_b2b")],
            [InlineKeyboardButton(text="B2C", callback_data="zayavka_type_b2c")]
        ]
    )
    return keyboard

def media_attachment_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ha", callback_data="attach_media_yes")],
        [InlineKeyboardButton(text="Yo'q", callback_data="attach_media_no")]
    ])
    return keyboard

def geolocation_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ha", callback_data="send_location_yes")],
        [InlineKeyboardButton(text="Yo'q", callback_data="send_location_no")]
    ])
    return keyboard

def confirmation_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlayman", callback_data="confirm_zayavka"),
            InlineKeyboardButton(text="🔄 Qayta yuborish", callback_data="resend_zayavka")
        ]
    ])
    return keyboard

def get_technician_selection_keyboard(technicians):
    """Technician tanlash klaviaturasi"""
    buttons = []
    for tech in technicians:
        active_tasks = tech.get('active_tasks', 0)
        text = f"👨‍🔧 {tech['full_name']} ({active_tasks} vazifa)"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"select_tech_{tech['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="❌ Bekor qilish",
        callback_data="cancel_assignment"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_task_action_keyboard(zayavka_id):
    """Vazifa amal klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="▶️ Boshlash", callback_data=f"start_task_{zayavka_id}"),
            InlineKeyboardButton(text="✅ Yakunlash", callback_data=f"complete_task_{zayavka_id}")
        ],
        [
            InlineKeyboardButton(text="🔄 O'tkazish so'rovi", callback_data=f"transfer_task_{zayavka_id}")
        ]
    ])

def get_completion_keyboard(zayavka_id):
    """Yakunlash klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Izohsiz yakunlash", callback_data=f"complete_no_comment_{zayavka_id}"),
            InlineKeyboardButton(text="📝 Izoh bilan yakunlash", callback_data=f"complete_with_comment_{zayavka_id}")
        ]
    ])
