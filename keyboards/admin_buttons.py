from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Reply keyboards
admin_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="👥 Foydalanuvchilar")
        ],
        [
            KeyboardButton(text="📝 Zayavkalar"),
            KeyboardButton(text="⚙️ Sozlamalar")
        ]
    ],
    resize_keyboard=True
)

# Zayavka management keyboard
zayavka_management_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🆕 Yangi zayavkalar"),
            KeyboardButton(text="⏳ Jarayonda")
        ],
        [
            KeyboardButton(text="✅ Bajarilgan"),
            KeyboardButton(text="❌ Bekor qilingan")
        ],
        [
            KeyboardButton(text="🔍 Qidirish"),
            KeyboardButton(text="📊 Zayavka statistikasi")
        ],
        [
            KeyboardButton(text="◀️ Orqaga")
        ]
    ],
    resize_keyboard=True
)

# User management keyboard
user_management_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👥 Barcha foydalanuvchilar"),
            KeyboardButton(text="👤 Xodimlar")
        ],
        [
            KeyboardButton(text="🔒 Bloklash/Blokdan chiqarish"),
            KeyboardButton(text="🔄 Rol o'zgartirish")
        ],
        [
            KeyboardButton(text="◀️ Orqaga")
        ]
    ],
    resize_keyboard=True
)

# Statistics keyboard
statistics_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Umumiy statistika"),
            KeyboardButton(text="📈 Zayavka statistikasi")
        ],
        [
            KeyboardButton(text="👥 Foydalanuvchi aktivligi"),
            KeyboardButton(text="📋 Xodimlar statistikasi")
        ],
        [
            KeyboardButton(text="◀️ Orqaga")
        ]
    ],
    resize_keyboard=True
)

# Settings keyboard
settings_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔔 Bildirishnomalar"),
            KeyboardButton(text="🌐 Til sozlamalari")
        ],
        [
            KeyboardButton(text="📝 Xabar shablonlari"),
            KeyboardButton(text="⚙️ Tizim sozlamalari")
        ],
        [
            KeyboardButton(text="◀️ Orqaga")
        ]
    ],
    resize_keyboard=True
)

# Inline keyboards
def users_list_keyboard(users: list):
    buttons = []
    for user in users:
        buttons.append([InlineKeyboardButton(text=user['full_name'], callback_data=f"manage_user_{user['telegram_id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def roles_keyboard(telegram_id: int):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Admin", callback_data=f"set_role_{telegram_id}_admin"),
                InlineKeyboardButton(text="Operator", callback_data=f"set_role_{telegram_id}_operator")
            ],
            [
                InlineKeyboardButton(text="Texnik", callback_data=f"set_role_{telegram_id}_technician"),
                InlineKeyboardButton(text="Menejer", callback_data=f"set_role_{telegram_id}_manager")
            ],
            [
                InlineKeyboardButton(text="Kontrolyor", callback_data=f"set_role_{telegram_id}_controller"),
                InlineKeyboardButton(text="Sklad", callback_data=f"set_role_{telegram_id}_warehouse")
            ],
            [
                InlineKeyboardButton(text="Abonent", callback_data=f"set_role_{telegram_id}_client"),
                InlineKeyboardButton(text="Bloklangan", callback_data=f"set_role_{telegram_id}_blocked")
            ]
        ]
    )
    return keyboard

def search_user_method_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Telegram ID orqali", callback_data="search_by_telegram_id"),
                InlineKeyboardButton(text="Telefon raqami orqali", callback_data="search_by_phone")
            ]
        ]
    )
    return keyboard

def zayavka_status_keyboard(zayavka_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏳ Jarayonda", callback_data=f"status_{zayavka_id}_in_progress"),
            InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"status_{zayavka_id}_completed")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"status_{zayavka_id}_cancelled"),
            InlineKeyboardButton(text="📝 Izoh qo'shish", callback_data=f"comment_{zayavka_id}")
        ]
    ])

def assign_zayavka_keyboard(zayavka_id: int, staff_members: list):
    buttons = []
    for staff in staff_members:
        buttons.append([InlineKeyboardButton(
            text=f"{staff['full_name']} ({staff['role']})",
            callback_data=f"assign_{zayavka_id}_{staff['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def zayavka_filter_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🆕 Yangi", callback_data="filter_new"),
            InlineKeyboardButton(text="⏳ Jarayonda", callback_data="filter_in_progress")
        ],
        [
            InlineKeyboardButton(text="✅ Bajarilgan", callback_data="filter_completed"),
            InlineKeyboardButton(text="❌ Bekor qilingan", callback_data="filter_cancelled")
        ],
        [
            InlineKeyboardButton(text="📅 Bugun", callback_data="filter_today"),
            InlineKeyboardButton(text="📅 Kecha", callback_data="filter_yesterday")
        ]
    ]) 