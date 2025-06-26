from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.i18n import i18n

def get_admin_main_menu(lang="uz"):
    """Admin asosiy menyu - 2 tilda"""
    statistics_text = "📊 Statistika" if lang == "uz" else "📊 Статистика"
    users_text = "👥 Foydalanuvchilar" if lang == "uz" else "👥 Пользователи"
    orders_text = "📝 Zayavkalar" if lang == "uz" else "📝 Заявки"
    settings_text = "⚙️ Sozlamalar" if lang == "uz" else "⚙️ Настройки"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=statistics_text),
                KeyboardButton(text=users_text)
            ],
            [
                KeyboardButton(text=orders_text),
                KeyboardButton(text=settings_text)
            ]
        ],
        resize_keyboard=True
    )

# Default admin menu (o'zbek tilida)
admin_main_menu = get_admin_main_menu("uz")

# Zayavka management keyboard
def get_zayavka_management_keyboard(lang="uz"):
    """Zayavka boshqaruv klaviaturasi - 2 tilda"""
    new_text = "🆕 Yangi zayavkalar" if lang == "uz" else "🆕 Новые заявки"
    progress_text = "⏳ Jarayonda" if lang == "uz" else "⏳ В процессе"
    completed_text = "✅ Bajarilgan" if lang == "uz" else "✅ Выполненные"
    cancelled_text = "❌ Bekor qilingan" if lang == "uz" else "❌ Отмененные"
    search_text = "🔍 Qidirish" if lang == "uz" else "🔍 Поиск"
    stats_text = "📊 Zayavka statistikasi" if lang == "uz" else "📊 Статистика заявок"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=new_text),
                KeyboardButton(text=progress_text)
            ],
            [
                KeyboardButton(text=completed_text),
                KeyboardButton(text=cancelled_text)
            ],
            [
                KeyboardButton(text=search_text),
                KeyboardButton(text=stats_text)
            ],
            [
                KeyboardButton(text=back_text)
            ]
        ],
        resize_keyboard=True
    )

zayavka_management_keyboard = get_zayavka_management_keyboard("uz")

# User management keyboard
def get_user_management_keyboard(lang="uz"):
    """Foydalanuvchi boshqaruv klaviaturasi - 2 tilda"""
    all_users_text = "👥 Barcha foydalanuvchilar" if lang == "uz" else "👥 Все пользователи"
    staff_text = "👤 Xodimlar" if lang == "uz" else "👤 Сотрудники"
    block_text = "🔒 Bloklash/Blokdan chiqarish" if lang == "uz" else "🔒 Блокировка/Разблокировка"
    role_text = "🔄 Rol o'zgartirish" if lang == "uz" else "🔄 Изменить роль"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=all_users_text),
                KeyboardButton(text=staff_text)
            ],
            [
                KeyboardButton(text=block_text),
                KeyboardButton(text=role_text)
            ],
            [
                KeyboardButton(text=back_text)
            ]
        ],
        resize_keyboard=True
    )

user_management_keyboard = get_user_management_keyboard("uz")

# Statistics keyboard
def get_statistics_keyboard(lang="uz"):
    """Statistika klaviaturasi - 2 tilda"""
    general_text = "📊 Umumiy statistika" if lang == "uz" else "📊 Общая статистика"
    orders_text = "📈 Zayavka statistikasi" if lang == "uz" else "📈 Статистика заявок"
    users_text = "👥 Foydalanuvchi aktivligi" if lang == "uz" else "👥 Активность пользователей"
    staff_text = "📋 Xodimlar statistikasi" if lang == "uz" else "📋 Статистика сотрудников"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=general_text),
                KeyboardButton(text=orders_text)
            ],
            [
                KeyboardButton(text=users_text),
                KeyboardButton(text=staff_text)
            ],
            [
                KeyboardButton(text=back_text)
            ]
        ],
        resize_keyboard=True
    )

statistics_keyboard = get_statistics_keyboard("uz")

# Settings keyboard
def get_settings_keyboard(lang="uz"):
    """Sozlamalar klaviaturasi - 2 tilda"""
    notifications_text = "🔔 Bildirishnomalar" if lang == "uz" else "🔔 Уведомления"
    language_text = "🌐 Til sozlamalari" if lang == "uz" else "🌐 Языковые настройки"
    templates_text = "📝 Xabar shablonlari" if lang == "uz" else "📝 Шаблоны сообщений"
    system_text = "⚙️ Tizim sozlamalari" if lang == "uz" else "⚙️ Системные настройки"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=notifications_text),
                KeyboardButton(text=language_text)
            ],
            [
                KeyboardButton(text=templates_text),
                KeyboardButton(text=system_text)
            ],
            [
                KeyboardButton(text=back_text)
            ]
        ],
        resize_keyboard=True
    )

settings_keyboard = get_settings_keyboard("uz")

# Inline keyboards
def users_list_keyboard(users: list, lang="uz"):
    """Foydalanuvchilar ro'yxati klaviaturasi"""
    buttons = []
    for user in users:
        buttons.append([InlineKeyboardButton(text=user['full_name'], callback_data=f"manage_user_{user['telegram_id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def roles_keyboard(telegram_id: int, lang="uz"):
    """Rollar klaviaturasi - 2 tilda"""
    admin_text = "Admin" if lang == "uz" else "Админ"
    operator_text = "Operator" if lang == "uz" else "Оператор"
    tech_text = "Texnik" if lang == "uz" else "Техник"
    manager_text = "Menejer" if lang == "uz" else "Менеджер"
    controller_text = "Kontrolyor" if lang == "uz" else "Контроллер"
    warehouse_text = "Sklad" if lang == "uz" else "Склад"
    client_text = "Abonent" if lang == "uz" else "Абонент"
    blocked_text = "Bloklangan" if lang == "uz" else "Заблокирован"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=admin_text, callback_data=f"set_role_{telegram_id}_admin"),
                InlineKeyboardButton(text=operator_text, callback_data=f"set_role_{telegram_id}_operator")
            ],
            [
                InlineKeyboardButton(text=tech_text, callback_data=f"set_role_{telegram_id}_technician"),
                InlineKeyboardButton(text=manager_text, callback_data=f"set_role_{telegram_id}_manager")
            ],
            [
                InlineKeyboardButton(text=controller_text, callback_data=f"set_role_{telegram_id}_controller"),
                InlineKeyboardButton(text=warehouse_text, callback_data=f"set_role_{telegram_id}_warehouse")
            ],
            [
                InlineKeyboardButton(text=client_text, callback_data=f"set_role_{telegram_id}_client"),
                InlineKeyboardButton(text=blocked_text, callback_data=f"set_role_{telegram_id}_blocked")
            ]
        ]
    )
    return keyboard

def search_user_method_keyboard(lang="uz"):
    """Foydalanuvchi qidirish usuli klaviaturasi - 2 tilda"""
    telegram_text = "Telegram ID orqali" if lang == "uz" else "По Telegram ID"
    phone_text = "Telefon raqami orqali" if lang == "uz" else "По номеру телефона"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=telegram_text, callback_data="search_by_telegram_id"),
                InlineKeyboardButton(text=phone_text, callback_data="search_by_phone")
            ]
        ]
    )
    return keyboard

def zayavka_status_keyboard(zayavka_id: int, lang="uz") -> InlineKeyboardMarkup:
    """Zayavka statusini o'zgartirish uchun klaviatura - 2 tilda"""
    progress_text = "⏳ Jarayonda" if lang == "uz" else "⏳ В процессе"
    completed_text = "✅ Bajarildi" if lang == "uz" else "✅ Выполнено"
    cancelled_text = "❌ Bekor qilindi" if lang == "uz" else "❌ Отменено"
    
    buttons = [
        [
            InlineKeyboardButton(text=progress_text, callback_data=f"admin_status_{zayavka_id}_in_progress"),
            InlineKeyboardButton(text=completed_text, callback_data=f"admin_status_{zayavka_id}_completed"),
            InlineKeyboardButton(text=cancelled_text, callback_data=f"admin_status_{zayavka_id}_cancelled"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def assign_zayavka_keyboard(zayavka_id: int, staff_members: list, lang="uz"):
    """Zayavka biriktirish klaviaturasi"""
    buttons = []
    for staff in staff_members:
        role_text = staff['role']
        if lang == "ru":
            role_translations = {
                'technician': 'техник',
                'manager': 'менеджер',
                'operator': 'оператор',
                'admin': 'админ'
            }
            role_text = role_translations.get(staff['role'], staff['role'])
        
        buttons.append([InlineKeyboardButton(
            text=f"{staff['full_name']} ({role_text})",
            callback_data=f"assign_{zayavka_id}_{staff['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def zayavka_filter_keyboard(lang="uz"):
    """Zayavka filtrlash klaviaturasi - 2 tilda"""
    new_text = "🆕 Yangi" if lang == "uz" else "🆕 Новые"
    progress_text = "⏳ Jarayonda" if lang == "uz" else "⏳ В процессе"
    completed_text = "✅ Bajarilgan" if lang == "uz" else "✅ Выполненные"
    cancelled_text = "❌ Bekor qilingan" if lang == "uz" else "❌ Отмененные"
    today_text = "📅 Bugun" if lang == "uz" else "📅 Сегодня"
    yesterday_text = "📅 Kecha" if lang == "uz" else "📅 Вчера"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=new_text, callback_data="filter_new"),
            InlineKeyboardButton(text=progress_text, callback_data="filter_in_progress")
        ],
        [
            InlineKeyboardButton(text=completed_text, callback_data="filter_completed"),
            InlineKeyboardButton(text=cancelled_text, callback_data="filter_cancelled")
        ],
        [
            InlineKeyboardButton(text=today_text, callback_data="filter_today"),
            InlineKeyboardButton(text=yesterday_text, callback_data="filter_yesterday")
        ]
    ])
