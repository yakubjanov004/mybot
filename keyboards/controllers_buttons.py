from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def controllers_main_menu(language: str) -> ReplyKeyboardMarkup:
    orders_control_text = "📋 Buyurtmalarni nazorat qilish" if language == "uz" else "📋 Контроль заказов"
    technicians_control_text = "👨‍🔧 Texniklarni nazorat qilish" if language == "uz" else "👨‍🔧 Контроль техников"
    system_reports_text = "📊 Tizim hisobotlari" if language == "uz" else "📊 Системные отчеты"
    quality_control_text = "✅ Sifat nazorati" if language == "uz" else "✅ Контроль качества"
    change_language_text = "🌐 Tilni o'zgartirish" if language == "uz" else "🌐 Изменить язык"
    keyboard = [
        [KeyboardButton(text=orders_control_text), KeyboardButton(text=technicians_control_text)],
        [KeyboardButton(text=system_reports_text), KeyboardButton(text=quality_control_text)],
        [KeyboardButton(text=change_language_text)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def orders_control_menu(language: str) -> InlineKeyboardMarkup:
    """Orders control menu"""
    priority_orders_text = "🔴 Ustuvor buyurtmalar" if language == "uz" else "🔴 Приоритетные заказы"
    delayed_orders_text = "⏰ Kechiktirilgan buyurtmalar" if language == "uz" else "⏰ Просроченные заказы"
    assign_technicians_text = "👨‍🔧 Texniklarni tayinlash" if language == "uz" else "👨‍🔧 Назначить техников"
    order_analytics_text = "📈 Buyurtma tahlili" if language == "uz" else "📈 Аналитика заказов"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=priority_orders_text,
                callback_data="priority_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=delayed_orders_text,
                callback_data="delayed_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=assign_technicians_text,
                callback_data="assign_technicians"
            )
        ],
        [
            InlineKeyboardButton(
                text=order_analytics_text,
                callback_data="order_analytics"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="controllers_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def technicians_menu(language: str) -> InlineKeyboardMarkup:
    """Technicians control menu"""
    performance_report_text = "📊 Samaradorlik hisoboti" if language == "uz" else "📊 Отчет о производительности"
    workload_balance_text = "⚖️ Ish yukini taqsimlash" if language == "uz" else "⚖️ Балансировка нагрузки"
    technician_ratings_text = "⭐ Texniklar reytingi" if language == "uz" else "⭐ Рейтинг техников"
    schedule_management_text = "📅 Jadval boshqaruvi" if language == "uz" else "📅 Управление расписанием"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=performance_report_text,
                callback_data="performance_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=workload_balance_text,
                callback_data="workload_balance"
            )
        ],
        [
            InlineKeyboardButton(
                text=technician_ratings_text,
                callback_data="technician_ratings"
            )
        ],
        [
            InlineKeyboardButton(
                text=schedule_management_text,
                callback_data="schedule_management"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="controllers_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def reports_menu(language: str) -> InlineKeyboardMarkup:
    """Reports menu"""
    daily_report_text = "📅 Kunlik hisobot" if language == "uz" else "📅 Ежедневный отчет"
    weekly_report_text = "📅 Haftalik hisobot" if language == "uz" else "📅 Еженедельный отчет"
    monthly_report_text = "📅 Oylik hisobot" if language == "uz" else "📅 Ежемесячный отчет"
    custom_report_text = "📊 Maxsus hisobot" if language == "uz" else "📊 Специальный отчет"
    export_data_text = "📤 Ma'lumotlarni eksport qilish" if language == "uz" else "📤 Экспорт данных"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=daily_report_text,
                callback_data="daily_report"
            ),
            InlineKeyboardButton(
                text=weekly_report_text,
                callback_data="weekly_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=monthly_report_text,
                callback_data="monthly_report"
            ),
            InlineKeyboardButton(
                text=custom_report_text,
                callback_data="custom_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=export_data_text,
                callback_data="export_data"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="controllers_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def order_priority_keyboard(language: str) -> InlineKeyboardMarkup:
    """Order priority selection keyboard"""
    high_priority_text = "Yuqori ustuvorlik" if language == "uz" else "Высокий приоритет"
    medium_priority_text = "O'rtacha ustuvorlik" if language == "uz" else "Средний приоритет"
    normal_priority_text = "Oddiy ustuvorlik" if language == "uz" else "Обычный приоритет"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"🔴 {high_priority_text}",
                callback_data="set_priority_high"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🟡 {medium_priority_text}",
                callback_data="set_priority_medium"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🟢 {normal_priority_text}",
                callback_data="set_priority_normal"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="orders_control"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def technician_assignment_keyboard(language: str, technicians: list) -> InlineKeyboardMarkup:
    """Technician assignment keyboard"""
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    orders_word = "buyurtma" if language == "uz" else "заказов"
    
    keyboard = []
    
    for tech in technicians:
        keyboard.append([
            InlineKeyboardButton(
                text=f"👨‍🔧 {tech['full_name']} ({tech['active_orders']} {orders_word})",
                callback_data=f"assign_tech_{tech['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=back_text,
            callback_data="assign_technicians"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
