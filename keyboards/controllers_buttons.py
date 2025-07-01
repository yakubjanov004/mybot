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

def quality_control_menu(language: str) -> InlineKeyboardMarkup:
    """Quality control menu"""
    customer_feedback_text = "💬 Mijoz fikrlari" if language == "uz" else "💬 Отзывы клиентов"
    unresolved_issues_text = "⚠️ Hal etilmagan muammolar" if language == "uz" else "⚠️ Нерешенные проблемы"
    service_quality_text = "⭐ Xizmat sifatini baholash" if language == "uz" else "⭐ Оценка качества услуг"
    quality_trends_text = "📈 Sifat tendensiyalari" if language == "uz" else "📈 Тенденции качества"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=customer_feedback_text,
                callback_data="quality_customer_feedback"
            )
        ],
        [
            InlineKeyboardButton(
                text=unresolved_issues_text,
                callback_data="quality_unresolved_issues"
            )
        ],
        [
            InlineKeyboardButton(
                text=service_quality_text,
                callback_data="quality_service_assessment"
            )
        ],
        [
            InlineKeyboardButton(
                text=quality_trends_text,
                callback_data="quality_trends"
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

def feedback_filter_menu(language: str) -> InlineKeyboardMarkup:
    """Feedback filter menu"""
    all_feedback_text = "📋 Barcha fikrlar" if language == "uz" else "📋 Все отзывы"
    low_ratings_text = "⭐ Past baholar (1-2)" if language == "uz" else "⭐ Низкие оценки (1-2)"
    medium_ratings_text = "⭐⭐⭐ O'rta baholar (3)" if language == "uz" else "⭐⭐⭐ Средние оценки (3)"
    high_ratings_text = "⭐⭐⭐⭐⭐ Yuqori baholar (4-5)" if language == "uz" else "⭐⭐⭐⭐⭐ Высокие оценки (4-5)"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=all_feedback_text,
                callback_data="feedback_filter_all"
            )
        ],
        [
            InlineKeyboardButton(
                text=low_ratings_text,
                callback_data="feedback_filter_low"
            )
        ],
        [
            InlineKeyboardButton(
                text=medium_ratings_text,
                callback_data="feedback_filter_medium"
            )
        ],
        [
            InlineKeyboardButton(
                text=high_ratings_text,
                callback_data="feedback_filter_high"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="quality_control"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def quality_control_detailed_menu(language: str) -> InlineKeyboardMarkup:
    """Detailed quality control menu"""
    customer_feedback_text = "💬 Mijoz fikrlari" if language == "uz" else "💬 Отзывы клиентов"
    unresolved_issues_text = "⚠️ Hal etilmagan muammolar" if language == "uz" else "⚠️ Нерешенные проблемы"
    service_quality_text = "⭐ Xizmat sifatini baholash" if language == "uz" else "⭐ Оценка качества услуг"
    quality_trends_text = "📈 Sifat tendensiyalari" if language == "uz" else "📈 Тенденции качества"
    quality_reports_text = "📋 Sifat hisobotlari" if language == "uz" else "📋 Отчеты по качеству"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=customer_feedback_text,
                callback_data="quality_customer_feedback"
            )
        ],
        [
            InlineKeyboardButton(
                text=unresolved_issues_text,
                callback_data="quality_unresolved_issues"
            )
        ],
        [
            InlineKeyboardButton(
                text=service_quality_text,
                callback_data="quality_service_assessment"
            )
        ],
        [
            InlineKeyboardButton(
                text=quality_trends_text,
                callback_data="quality_trends"
            )
        ],
        [
            InlineKeyboardButton(
                text=quality_reports_text,
                callback_data="quality_reports"
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

def feedback_detailed_filter_menu(language: str) -> InlineKeyboardMarkup:
    """Detailed feedback filter menu"""
    all_feedback_text = "📋 Barcha fikrlar" if language == "uz" else "📋 Все отзывы"
    excellent_ratings_text = "⭐⭐⭐⭐⭐ A'lo (5)" if language == "uz" else "⭐⭐⭐⭐⭐ Отлично (5)"
    good_ratings_text = "⭐⭐⭐⭐ Yaxshi (4)" if language == "uz" else "⭐⭐⭐⭐ Хорошо (4)"
    average_ratings_text = "⭐⭐⭐ O'rta (3)" if language == "uz" else "⭐⭐⭐ Средне (3)"
    poor_ratings_text = "⭐⭐ Yomon (2)" if language == "uz" else "⭐⭐ Плохо (2)"
    terrible_ratings_text = "⭐ Juda yomon (1)" if language == "uz" else "⭐ Ужасно (1)"
    recent_feedback_text = "🕐 So'nggi fikrlar" if language == "uz" else "🕐 Последние отзывы"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=all_feedback_text,
                callback_data="feedback_filter_all"
            )
        ],
        [
            InlineKeyboardButton(
                text=excellent_ratings_text,
                callback_data="feedback_filter_5"
            )
        ],
        [
            InlineKeyboardButton(
                text=good_ratings_text,
                callback_data="feedback_filter_4"
            )
        ],
        [
            InlineKeyboardButton(
                text=average_ratings_text,
                callback_data="feedback_filter_3"
            )
        ],
        [
            InlineKeyboardButton(
                text=poor_ratings_text,
                callback_data="feedback_filter_2"
            )
        ],
        [
            InlineKeyboardButton(
                text=terrible_ratings_text,
                callback_data="feedback_filter_1"
            )
        ],
        [
            InlineKeyboardButton(
                text=recent_feedback_text,
                callback_data="feedback_filter_recent"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="quality_control"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
