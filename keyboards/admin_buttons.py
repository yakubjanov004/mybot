from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# Zayavkalar bo'yicha asosiy reply menyu
def get_zayavka_main_keyboard(lang: str = "uz"):
    """Zayavkalar bo'yicha asosiy reply menyu - 2 tilda"""
    status_text = "📂 Holat bo'yicha" if lang == "uz" else "📂 По статусу"
    search_text = "🔍 Qidirish / Filtrlash" if lang == "uz" else "🔍 Поиск / Фильтр"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=status_text)
            ],
            [
                KeyboardButton(text=search_text)
            ],
            [
                KeyboardButton(text=back_text)
            ]
        ],
        resize_keyboard=True
    )

def get_zayavka_section_keyboard(lang: str = "uz"):
    """Zayavkalar bo'yicha section reply menyu - 2 tilda"""
    status_text = "📂 Holat bo'yicha" if lang == "uz" else "📂 По статусу"
    search_text = "🔍 Qidirish / Filtrlash" if lang == "uz" else "🔍 Поиск / Фильтр"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=search_text)
            ],
            [
                KeyboardButton(text=status_text)
            ],
            [
                KeyboardButton(text=back_text)
            ]
        ],
        resize_keyboard=True
    )

# Holat bo'yicha filtr tanlash menyusi
def get_zayavka_status_filter_keyboard(lang: str = "uz", page: int = 1, total_pages: int = 1):
    """Holat bo'yicha filtr tanlash menyusi - 2 tilda, chiroyli va qulay dizayn"""
    new_text = "🆕 Yangi" if lang == "uz" else "🆕 Новые"
    in_progress_text = "🔄 Jarayonda" if lang == "uz" else "🔄 В процессе"
    done_text = "✅ Yakunlangan" if lang == "uz" else "✅ Выполненные"
    rejected_text = "❌ Bekor qilingan" if lang == "uz" else "❌ Отменённые"
    prev_text = "Avvalgisi" if lang == "uz" else "Предыдущий"
    next_text = "Keyingisi" if lang == "uz" else "Следующий"
    
    statuses = [
        (new_text, "new"),
        (in_progress_text, "in_progress"),
        (done_text, "done"),
        (rejected_text, "rejected")
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Add status buttons in 2 columns
    for i in range(0, len(statuses), 2):
        row = []
        for j in range(2):
            if i + j < len(statuses):
                status_text, status_code = statuses[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=status_text,
                        callback_data=f"zayavka:status:{status_code}:{page}"
                    )
                )
        keyboard.inline_keyboard.append(row)
    
    # Add navigation buttons
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(
            text=prev_text,
            callback_data=f"zayavka:status:prev:{page}"
        ))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(
            text=next_text,
            callback_data=f"zayavka:status:next:{page}"
        ))
    if nav_row:
        keyboard.inline_keyboard.append(nav_row)
    
    return keyboard

# Qidirish / Filtrlash menyusi
def get_zayavka_filter_menu_keyboard(lang: str = "uz", page: int = 1, total_pages: int = 1, active_filter: str = None, admin: bool = False):
    """Qidirish / Filtrlash menyusi - 2 tilda, chiroyli va qulay dizayn"""
    username_text = "🔤 FIO / Username" if lang == "uz" else "🔤 ФИО / Username"
    id_text = "🔢 Zayavka ID" if lang == "uz" else "🔢 ID заявки"
    date_text = "📆 Sana oraliq" if lang == "uz" else "📆 Дата диапазон"
    category_text = "🏷 Kategoriya" if lang == "uz" else "🏷 Категория"
    technician_text = "👨‍🔧 Texnik" if lang == "uz" else "👨‍🔧 Техник"
    prev_text = "Avvalgisi" if lang == "uz" else "Предыдущий"
    next_text = "Keyingisi" if lang == "uz" else "Следующий"
    back_text = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    
    filters = [
        (username_text, "username"),
        (id_text, "id"),
        (date_text, "date"),
        (category_text, "category"),
        (technician_text, "technician")
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    if active_filter and active_filter in ["date", "category"]:
        # Show only the selected filter with pagination
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=date_text if active_filter == "date" else category_text,
                callback_data=f"zayavka:filter:{active_filter}:{page}"
            )
        ])
        if page > 1 or page < total_pages:
            nav_row = []
            if page > 1:
                nav_row.append(InlineKeyboardButton(
                    text=prev_text,
                    callback_data=f"zayavka:filter:prev:{page}"
                ))
            if page < total_pages:
                nav_row.append(InlineKeyboardButton(
                    text=next_text,
                    callback_data=f"zayavka:filter:next:{page}"
                ))
            if nav_row:
                keyboard.inline_keyboard.append(nav_row)
    else:
        # Show all filters without navigation
        for i in range(0, len(filters), 2):
            row = []
            for j in range(2):
                if i + j < len(filters):
                    filter_text, filter_code = filters[i + j]
                    row.append(
                        InlineKeyboardButton(
                            text=filter_text,
                            callback_data=f"zayavka:filter:{filter_code}:{page}"
                        )
                    )
            keyboard.inline_keyboard.append(row)
            InlineKeyboardButton(
                text="➡️ Keyingi" if lang == "uz" else "➡️ Следующая",
                callback_data=f"zayavka:filter:next:{page}"
            )
    
    # Add back button only if not admin
    if not admin:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=back_text,
                callback_data="zayavka:filter:back"
            )
        ])
    
    return keyboard

# Admin asosiy menyu - 2 tilda
def get_admin_main_menu(lang="uz"):
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

def get_zayavka_management_keyboard(lang="uz"):
    """Zayavkalar boshqaruv uchun reply keyboard - 2 tilda"""
    new_text = "🆕 Yangi zayavkalar" if lang == "uz" else "🆕 Новые заявки"
    progress_text = "⏳ Kutilayotgan zayavkalar" if lang == "uz" else "⏳ Ожидающие заявки"
    completed_text = "✅ Bajarilgan zayavkalar" if lang == "uz" else "✅ Выполненные заявки"
    cancelled_text = "❌ Bekor qilingan zayavkalar" if lang == "uz" else "❌ Отменённые заявки"
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
    role_text = "🔄 Rolni o'zgartirish" if lang == "uz" else "🔄 Изменить роль"
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

# Language selection keyboard
def language_keyboard():
    """Til tanlash uchun inline klaviatura"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="lang_uz"),
                InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="lang_ru")
            ]
        ]
    )

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
    call_center_text = "Call Center" if lang == "uz" else "Колл-центр"
    tech_text = "Texnik" if lang == "uz" else "Техник"
    manager_text = "Menejer" if lang == "uz" else "Менеджер"
    controller_text = "Kontrolyor" if lang == "uz" else "Контроллер"
    warehouse_text = "Sklad" if lang == "uz" else "Склад"
    client_text = "Abonent" if lang == "uz" else "Абонент"
    blocked_text = "Bloklangan" if lang == "uz" else "Заблокирован"
    junior_manager_text = "Kichik menejer" if lang == "uz" else "Младший менеджер"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=admin_text, callback_data=f"set_role:admin:{telegram_id}"),
                InlineKeyboardButton(text=call_center_text, callback_data=f"set_role:call_center:{telegram_id}")
            ],
            [
                InlineKeyboardButton(text=tech_text, callback_data=f"set_role:technician:{telegram_id}"),
                InlineKeyboardButton(text=manager_text, callback_data=f"set_role:manager:{telegram_id}")
            ],
            [
                InlineKeyboardButton(text=junior_manager_text, callback_data=f"set_role:junior_manager:{telegram_id}"),
                InlineKeyboardButton(text=controller_text, callback_data=f"set_role:controller:{telegram_id}")
            ],
            [
                InlineKeyboardButton(text=warehouse_text, callback_data=f"set_role:warehouse:{telegram_id}")
            ],
            [
                InlineKeyboardButton(text=client_text, callback_data=f"set_role:client:{telegram_id}"),
                InlineKeyboardButton(text=blocked_text, callback_data=f"set_role:blocked:{telegram_id}")
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
                'call_center': 'колл-центр',
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

def get_orders_management_keyboard(lang="uz"):
    if lang == "uz":
        buttons = [
            [InlineKeyboardButton(text="🆕 Yangi zayavkalar", callback_data="show_new_orders")],
            [InlineKeyboardButton(text="⏳ Kutilayotgan zayavkalar", callback_data="show_pending_orders")],
            [InlineKeyboardButton(text="🔄 Jarayondagi zayavkalar", callback_data="show_in_progress_orders")],
            [InlineKeyboardButton(text="🚨 Tayinlanmagan zayavkalar", callback_data="show_unassigned_orders")],
            [InlineKeyboardButton(text="🔍 Zayavka qidirish", callback_data="search_orders")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🆕 Новые заявки", callback_data="show_new_orders")],
            [InlineKeyboardButton(text="⏳ Ожидающие заявки", callback_data="show_pending_orders")],
            [InlineKeyboardButton(text="🔄 Заявки в процессе", callback_data="show_in_progress_orders")],
            [InlineKeyboardButton(text="🚨 Неназначенные заявки", callback_data="show_unassigned_orders")],
            [InlineKeyboardButton(text="🔍 Поиск заявки", callback_data="search_orders")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_users_reply_keyboard(lang="uz"):
    """Admin foydalanuvchilar bo'limi uchun reply keyboard"""
    all_users_text = "👥 Barcha foydalanuvchilar" if lang == "uz" else "👥 Все пользователи"
    staff_text = "👤 Xodimlar" if lang == "uz" else "👤 Сотрудники"
    block_text = "🔒 Bloklash/Blokdan chiqarish" if lang == "uz" else "🔒 Блокировка/Разблокировка"
    role_text = "🔄 Rolni o'zgartirish" if lang == "uz" else "🔄 Изменить роль"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=all_users_text), KeyboardButton(text=staff_text)],
            [KeyboardButton(text=block_text), KeyboardButton(text=role_text)],
            [KeyboardButton(text=back_text)]
        ],
        resize_keyboard=True
    )

def get_admin_main_keyboard(lang="uz"):
    """Admin bosh menyu uchun reply keyboard"""
    return get_admin_main_menu(lang)

def get_stats_reply_keyboard(lang="uz"):
    """Admin statistika bo'limi uchun reply keyboard"""
    stats_text = "📊 Umumiy statistika" if lang == "uz" else "📊 Общая статистика"
    orders_text = "📈 Zayavka statistikasi" if lang == "uz" else "📈 Статистика заявок"
    users_text = "👥 Foydalanuvchi aktivligi" if lang == "uz" else "👥 Активность пользователей"
    staff_text = "📋 Xodimlar statistikasi" if lang == "uz" else "📋 Статистика сотрудников"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=stats_text), KeyboardButton(text=orders_text)],
            [KeyboardButton(text=users_text), KeyboardButton(text=staff_text)],
            [KeyboardButton(text=back_text)]
        ],
        resize_keyboard=True
    )

def get_zayavka_reply_keyboard(lang="uz"):
    """Admin zayavkalar bo'limi uchun reply keyboard"""
    new_text = "🆕 Yangi zayavkalar" if lang == "uz" else "🆕 Новые заявки"
    pending_text = "⏳ Kutilayotgan zayavkalar" if lang == "uz" else "⏳ Ожидающие заявки"
    in_progress_text = "🔄 Jarayondagi zayavkalar" if lang == "uz" else "🔄 Заявки в процессе"
    completed_text = "✅ Bajarilgan zayavkalar" if lang == "uz" else "✅ Выполненные заявки"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=new_text), KeyboardButton(text=pending_text)],
            [KeyboardButton(text=in_progress_text), KeyboardButton(text=completed_text)],
            [KeyboardButton(text=back_text)]
        ],
        resize_keyboard=True
    )

def get_settings_reply_keyboard(lang="uz"):
    """Admin sozlamalar bo'limi uchun reply keyboard"""
    notifications_text = "🔔 Bildirishnomalar" if lang == "uz" else "🔔 Уведомления"
    language_text = "🌐 Til sozlamalari" if lang == "uz" else "🌐 Языковые настройки"
    templates_text = "📝 Xabar shablonlari" if lang == "uz" else "📝 Шаблоны сообщений"
    system_text = "⚙️ Tizim sozlamalari" if lang == "uz" else "⚙️ Системные настройки"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=notifications_text), KeyboardButton(text=language_text)],
            [KeyboardButton(text=templates_text), KeyboardButton(text=system_text)],
            [KeyboardButton(text=back_text)]
        ],
        resize_keyboard=True
    )
