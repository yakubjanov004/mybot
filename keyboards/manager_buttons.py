from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_manager_main_keyboard(lang='uz'):
    """Generate main keyboard for manager with locale support"""
    service_order_text = "🆕 Texnik xizmat" if lang == "uz" else "🆕 Техническая поддержка"
    connection_order_text = "🔌 Ulanish uchun ariza" if lang == "uz" else "🔌 Заявка на подключение"
    view_applications_text = "📋 Arizalarni ko'rish" if lang == "uz" else "📋 Просмотр заявок"
    filter_applications_text = "🔍 Filtrlar" if lang == "uz" else "🔍 Фильтры"
    change_status_text = "🔄 Status o'zgartirish" if lang == "uz" else "🔄 Изменить статус"
    generate_report_text = "📊 Hisobot yaratish" if lang == "uz" else "📊 Создать отчет"
    equipment_issuance_text = "📦 Jihozlar berish" if lang == "uz" else "📦 Выдача оборудования"
    ready_for_installation_text = "✅ O'rnatishga tayyor" if lang == "uz" else "✅ Готов к установке"
    staff_activity_text = "👥 Xodimlar faoliyati" if lang == "uz" else "👥 Активность сотрудников"
    notifications_text = "🔔 Bildirishnomalar" if lang == "uz" else "🔔 Уведомления"
    change_language_text = "🌐 Tilni o'zgartirish" if lang == "uz" else "🌐 Изменить язык"
    inbox_text = "📥 Kiruvchi xabarlar" if lang == "uz" else "📥 Входящие сообщения"
    
    keyboard = [
        [KeyboardButton(text=service_order_text),
         KeyboardButton(text=connection_order_text)],
        [KeyboardButton(text=view_applications_text)],
        [KeyboardButton(text=filter_applications_text),
         KeyboardButton(text=change_status_text)],
        [KeyboardButton(text=generate_report_text)],
        [KeyboardButton(text=equipment_issuance_text),
         KeyboardButton(text=ready_for_installation_text)],
        [KeyboardButton(text=staff_activity_text),
         KeyboardButton(text=notifications_text)],
        [KeyboardButton(text=inbox_text)],
        [KeyboardButton(text=change_language_text)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_status_keyboard(statuses: list, application_id: int, lang='uz') -> InlineKeyboardMarkup:
    """Get status selection keyboard with application_id in callback and locale support"""
    status_texts = {
        'new': '🆕 Yangi' if lang == "uz" else '🆕 Новый',
        'in_progress': '⏳ Jarayonda' if lang == "uz" else '⏳ В процессе',
        'completed': '✅ Bajarilgan' if lang == "uz" else '✅ Выполнено',
        'cancelled': '❌ Bekor qilingan' if lang == "uz" else '❌ Отменено',
        'pending': '⏸️ Kutilmoqda' if lang == "uz" else '⏸️ Ожидает',
        'rejected': '🚫 Rad etilgan' if lang == "uz" else '🚫 Отклонено'
    }

    
    buttons = []
    for status in statuses:
        buttons.append(
            InlineKeyboardButton(
                text=status_texts.get(status, status),
                callback_data=f"status_{status}_{application_id}"
            )
        )
    

    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[buttons[:-1], [buttons[-1]]]  # Last button on separate row
    )
    return keyboard

def get_report_type_keyboard(lang='uz'):
    """Generate inline keyboard for report type selection with locale support"""
    report_word_text = "📄 Word formatida" if lang == "uz" else "📄 В формате Word"
    report_pdf_text = "📄 PDF formatida" if lang == "uz" else "📄 В формате PDF"
    
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=report_word_text,
            callback_data="report_word"
        ),
        InlineKeyboardButton(
            text=report_pdf_text,
            callback_data="report_pdf"
        )
    )
    builder.adjust(2)  # 2 buttons in first row
    return builder.as_markup()

def get_equipment_keyboard(equipment_list, lang='uz'):
    """Generate inline keyboard for equipment selection with locale support"""
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    builder = InlineKeyboardBuilder()
    for equipment in equipment_list:
        builder.add(InlineKeyboardButton(
            text=f"📦 {equipment['name']}",
            callback_data=f"equipment_{equipment['id']}"
        ))
    
    # Add back button
    builder.add(InlineKeyboardButton(
        text=back_text,
        callback_data="back_to_equipment_menu"
    ))
    
    builder.adjust(1)  # One button per row
    return builder.as_markup()

def get_assign_technician_keyboard(application_id, technicians, lang='uz'):
    """Generate inline keyboard for assigning a technician to an application with locale support"""
    builder = InlineKeyboardBuilder()
    for tech in technicians:
        text = f"👨‍🔧 {tech['full_name']}"
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"manager_assign_zayavka_{application_id}_{tech['id']}"
        ))
    builder.adjust(1)  # One button per row
    return builder.as_markup()

def get_back_inline_keyboard(lang='uz'):
    """Generate inline keyboard with a single 'Back' button with locale support"""
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=back_text,
        callback_data="back_to_assign_technician"
    ))
    return builder.as_markup()

def get_manager_filter_reply_keyboard(lang='uz'):
    status_text = "🟢 Status bo'yicha" if lang == 'uz' else "🟢 По статусу"
    date_text = "📅 Sana bo'yicha" if lang == 'uz' else "📅 По дате"
    tech_text = "👨‍🔧 Texnik biriktirilganligi bo'yicha" if lang == 'uz' else "👨‍🔧 По назначению техника"
    back_text = "◀️ Orqaga" if lang == 'uz' else "◀️ Назад"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=status_text), KeyboardButton(text=date_text)],
            [KeyboardButton(text=tech_text), KeyboardButton(text=back_text)]
        ],
        resize_keyboard=True
    )

def get_status_filter_inline_keyboard(lang='uz'):
    new_text = "🆕 Yangi" if lang == 'uz' else "🆕 Новый"
    in_progress_text = "⏳ Jarayonda" if lang == 'uz' else "⏳ В процессе"
    completed_text = "✅ Yakunlangan" if lang == 'uz' else "✅ Завершено"
    cancelled_text = "❌ Bekor qilingan" if lang == 'uz' else "❌ Отменено"
    all_text = "📋 Barchasi" if lang == 'uz' else "📋 Все"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=new_text, callback_data='filter_status_new'),
                InlineKeyboardButton(text=in_progress_text, callback_data='filter_status_in_progress')
            ],
            [
                InlineKeyboardButton(text=completed_text, callback_data='filter_status_completed'),
                InlineKeyboardButton(text=cancelled_text, callback_data='filter_status_cancelled')
            ],
            [
                InlineKeyboardButton(text=all_text, callback_data='filter_status_all'),
            ]
        ]
    )

def get_date_filter_inline_keyboard(lang='uz'):
    today_text = "📅 Bugun" if lang == 'uz' else "📅 Сегодня"
    yesterday_text = "🗓️ Kecha" if lang == 'uz' else "🗓️ Вчера"
    week_text = "📆 Bu hafta" if lang == 'uz' else "📆 На этой неделе"
    month_text = "🗓️ Bu oy" if lang == 'uz' else "🗓️ В этом месяце"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=today_text, callback_data='filter_date_today'),
                InlineKeyboardButton(text=yesterday_text, callback_data='filter_date_yesterday')
            ],
            [
                InlineKeyboardButton(text=week_text, callback_data='filter_date_week'),
                InlineKeyboardButton(text=month_text, callback_data='filter_date_month')
            ]
        ]
    )

def get_tech_filter_inline_keyboard(lang='uz'):
    assigned_text = "👨‍🔧 Biriktirilgan" if lang == 'uz' else "👨‍🔧 Назначенные"
    unassigned_text = "🚫 Biriktirilmagan" if lang == 'uz' else "🚫 Не назначенные"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=assigned_text, callback_data='filter_tech_assigned'),
                InlineKeyboardButton(text=unassigned_text, callback_data='filter_tech_unassigned')
            ]
        ]
    )

def get_pagination_inline_keyboard(page, total_pages, lang='uz', has_prev=True, has_next=True):
    prev_text = "Avvalgisi" if lang == 'uz' else "Предыдущая"
    next_text = "Keyingisi" if lang == 'uz' else "Следующая"
    back_text = "Orqaga" if lang == 'uz' else "Назад"
    buttons = []
    row = []
    if has_prev:
        row.append(InlineKeyboardButton(text=prev_text, callback_data=f'filter_page_prev_{page-1}'))
    if has_next:
        row.append(InlineKeyboardButton(text=next_text, callback_data=f'filter_page_next_{page+1}'))
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=back_text, callback_data='filter_back')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_filtered_applications_keyboard(applications: list, lang='uz') -> InlineKeyboardMarkup:
    """Show filtered applications with clear button"""
    clear_text = "🔄 Tozalash" if lang == "uz" else "🔄 Очистить"
    
    buttons = []
    for app in applications:
        status_emoji = {
            'new': '🆕',
            'in_progress': '⏳',
            'completed': '✅',
            'cancelled': '❌'
        }.get(app.get('status', 'new'), '📋')
        
        text = f"{status_emoji} ID: {app['id']} - {app.get('user_name', '-')}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"view_application_{app['id']}"
        )])
    
    # Add clear filter button
    buttons.append([InlineKeyboardButton(
        text=clear_text, 
        callback_data="filter_clear"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_filter_results_keyboard(page: int, total_pages: int, has_next: bool, has_prev: bool, lang='uz') -> InlineKeyboardMarkup:
    """Filtered results pagination keyboard with locale support"""
    prev_text = "◀️ Oldingi" if lang == "uz" else "◀️ Предыдущая"
    next_text = "Keyingi ▶️" if lang == "uz" else "Следующая ▶️"
    clear_text = "🔄 Tozalash" if lang == "uz" else "🔄 Очистить"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    buttons = []
    
    # Navigation buttons
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(text=prev_text, callback_data=f"filter_page_{page-1}"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text=next_text, callback_data=f"filter_page_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Page info
    if total_pages > 1:
        buttons.append([
            InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="filter_page_info")
        ])
    
    # Control buttons
    control_row = [
        InlineKeyboardButton(text=clear_text, callback_data="filter_clear"),
        InlineKeyboardButton(text=back_text, callback_data="back_to_main_menu")
    ]
    buttons.append(control_row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirmation_keyboard(action_type="confirm", lang='uz') -> InlineKeyboardMarkup:
    """Generate confirmation keyboard with locale support"""
    confirm_text = "✅ Tasdiqlash" if lang == "uz" else "✅ Подтвердить"
    cancel_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отменить"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=confirm_text, callback_data=f"confirm_{action_type}"),
            InlineKeyboardButton(text=cancel_text, callback_data=f"cancel_{action_type}")
        ]
    ])
    return keyboard

def get_application_actions_keyboard(application_id: int, lang='uz') -> InlineKeyboardMarkup:
    """Generate application action buttons with locale support"""
    change_status_text = "📊 Holatni o'zgartirish" if lang == "uz" else "📊 Изменить статус"
    assign_responsible_text = "👨‍🔧 Texnik biriktirish" if lang == "uz" else "👨‍🔧 Назначить техника"
    view_text = "👁️ Ko'rish" if lang == "uz" else "👁️ Просмотр"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=change_status_text, 
                callback_data=f"app_change_status_{application_id}"
            ),
            InlineKeyboardButton(
                text=assign_responsible_text, 
                callback_data=f"app_assign_tech_{application_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=view_text, 
                callback_data=f"app_view_details_{application_id}"
            ),
            InlineKeyboardButton(
                text=back_text, 
                callback_data="back_to_applications"
            )
        ]
    ])
    return keyboard

def get_manager_language_keyboard(lang='uz') -> InlineKeyboardMarkup:
    """Language selection keyboard for manager"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="manager_lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="manager_lang_ru")
        ]
    ])
    return keyboard

def get_manager_back_keyboard(lang='uz'):
    """Manager uchun bosh menyuga qaytish klaviaturasi"""
    back_text = "🏠 Asosiy menyu" if lang == "uz" else "🏠 Главное меню"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=back_text)]],
        resize_keyboard=True
    )

def zayavka_type_keyboard(lang='uz'):
    """Zayavka turini tanlash klaviaturasi"""
    b2b_text = "🏢 B2B (Korxona)" if lang == "uz" else "🏢 B2B (Компания)"
    b2c_text = "👤 B2C (Shaxsiy)" if lang == "uz" else "👤 B2C (Личный)"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=b2b_text, callback_data="manager_zayavka_type_b2b"),
            InlineKeyboardButton(text=b2c_text, callback_data="manager_zayavka_type_b2c")
        ]
    ])
    return keyboard

def media_attachment_keyboard(lang='uz'):
    """Media biriktirish klaviaturasi"""
    yes_text = "✅ Ha" if lang == "uz" else "✅ Да"
    no_text = "❌ Yo'q" if lang == "uz" else "❌ Нет"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=yes_text, callback_data="manager_attach_media_yes"),
            InlineKeyboardButton(text=no_text, callback_data="manager_attach_media_no")
        ]
    ])
    return keyboard

def geolocation_keyboard(lang='uz'):
    """Geolokatsiya yuborish klaviaturasi"""
    yes_text = "📍 Ha, yuboraman" if lang == "uz" else "📍 Да, отправлю"
    no_text = "❌ Yo'q" if lang == "uz" else "❌ Нет"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=yes_text, callback_data="manager_send_location_yes"),
            InlineKeyboardButton(text=no_text, callback_data="manager_send_location_no")
        ]
    ])
    return keyboard

def confirmation_keyboard(lang="uz"):
    """Tasdiqlash klaviaturasi - 2 tilda"""
    confirm_text = "✅ Tasdiqlash" if lang == "uz" else "✅ Подтвердить"
    resend_text = "🔄 Qayta yuborish" if lang == "uz" else "🔄 Отправить заново"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=confirm_text, callback_data="manager_confirm_zayavka"),
            InlineKeyboardButton(text=resend_text, callback_data="manager_resend_zayavka")
        ]
    ])
    return keyboard

def get_reports_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Reports menu keyboard for manager"""
    daily_text = "📅 Kunninglik" if lang == "uz" else "📅 Ежедневный"
    monthly_text = "📅 Oylik" if lang == "uz" else "📅 Ежемесячный"
    custom_text = "📊 Maxsus" if lang == "uz" else "📊 Специальный"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=daily_text,
                callback_data="daily_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=monthly_text,
                callback_data="monthly_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=custom_text,
                callback_data="custom_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="manager_back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_notifications_keyboard(lang: str):
    """Notifications menu keyboard for manager"""
    builder = InlineKeyboardBuilder()
    
    # Add notification type buttons
    builder.add(
        InlineKeyboardButton(
            text="🔔 Yangi bildirishnomalar" if lang == "uz" else "🔔 Новые уведомления",
            callback_data="notifications_new"
        ),
        InlineKeyboardButton(
            text="✅ O'qilgan bildirishnomalar" if lang == "uz" else "✅ Прочитанные уведомления",
            callback_data="notifications_read"
        ),
        InlineKeyboardButton(
            text="🗑️ O'chirilgan bildirishnomalar" if lang == "uz" else "🗑️ Удаленные уведомления",
            callback_data="notifications_deleted"
        ),
        InlineKeyboardButton(
            text="⚙️ Sozlamalar" if lang == "uz" else "⚙️ Настройки",
            callback_data="notifications_settings"
        )
    )
    
    # Add back button
    builder.add(
        InlineKeyboardButton(
            text="🔙 Orqaga" if lang == "uz" else "🔙 Назад",
            callback_data="back_to_notifications_menu"
        )
    )
    
    # Adjust button layout
    builder.adjust(2, 2, 1)  # 2 buttons in first row, 2 in second, 1 in last
    return builder.as_markup()

def get_staff_activity_menu(lang='uz'):
    """Staff activity monitoring menu"""
    technician_performance_text = "👨‍🔧 Texniklar samaradorligi" if lang == "uz" else "👨‍🔧 Производительность техников"
    daily_activity_text = "📅 Kunlik faollik" if lang == "uz" else "📅 Ежедневная активность"
    weekly_summary_text = "📊 Haftalik xulosalar" if lang == "uz" else "📊 Недельная сводка"
    individual_reports_text = "👤 Shaxsiy hisobotlar" if lang == "uz" else "👤 Индивидуальные отчеты"
    team_comparison_text = "⚖️ Jamoa taqqoslash" if lang == "uz" else "⚖️ Сравнение команды"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=technician_performance_text,
                callback_data="staff_technician_performance"
            )
        ],
        [
            InlineKeyboardButton(
                text=daily_activity_text,
                callback_data="staff_daily_activity"
            )
        ],
        [
            InlineKeyboardButton(
                text=weekly_summary_text,
                callback_data="staff_weekly_summary"
            )
        ],
        [
            InlineKeyboardButton(
                text=individual_reports_text,
                callback_data="staff_individual_reports"
            )
        ],
        [
            InlineKeyboardButton(
                text=team_comparison_text,
                callback_data="staff_team_comparison"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_notifications_settings_menu(lang='uz'):
    """Notifications settings menu"""
    new_orders_text = "🆕 Yangi buyurtmalar" if lang == "uz" else "🆕 Новые заказы"
    status_changes_text = "🔄 Status o'zgarishlari" if lang == "uz" else "🔄 Изменения статуса"
    urgent_issues_text = "🚨 Shoshilinch masalalar" if lang == "uz" else "🚨 Срочные вопросы"
    daily_summary_text = "📊 Kunlik xulosalar" if lang == "uz" else "📊 Ежедневная сводка"
    system_alerts_text = "⚠️ Tizim ogohlantirishlari" if lang == "uz" else "⚠️ Системные предупреждения"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=new_orders_text,
                callback_data="notif_new_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=status_changes_text,
                callback_data="notif_status_changes"
            )
        ],
        [
            InlineKeyboardButton(
                text=urgent_issues_text,
                callback_data="notif_urgent_issues"
            )
        ],
        [
            InlineKeyboardButton(
                text=daily_summary_text,
                callback_data="notif_daily_summary"
            )
        ],
        [
            InlineKeyboardButton(
                text=system_alerts_text,
                callback_data="notif_system_alerts"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="manager_back_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_manager_view_applications_keyboard(lang='uz'):
    view_all_text = "📋 Hammasini ko'rish" if lang == 'uz' else "📋 Посмотреть все"
    by_id_text = "🔎 ID bo'yicha ko'rish" if lang == 'uz' else "🔎 По ID"
    back_text = "◀️ Orqaga" if lang == 'uz' else "◀️ Назад"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=view_all_text)],
            [KeyboardButton(text=by_id_text)],
            [KeyboardButton(text=back_text)]
        ],
        resize_keyboard=True
    )

def get_staff_activity_keyboard(lang='uz'):
    """Xodimlar faoliyati uchun keyboard"""
    online_text = "🟢 Onlayn xodimlar" if lang == "uz" else "🟢 Сотрудники онлайн"
    performance_text = "📊 Samaradorlik" if lang == "uz" else "📊 Производительность"
    workload_text = "📋 Ish yuki" if lang == "uz" else "📋 Рабочая нагрузка"
    attendance_text = "📅 Davomat" if lang == "uz" else "📅 Посещаемость"
    junior_work_text = "👨‍💼 Kichik menejerlar ishi" if lang == "uz" else "👨‍💼 Работа младших менеджеров"
    back_text = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=online_text,
                callback_data="staff_online"
            )
        ],
        [
            InlineKeyboardButton(
                text=performance_text,
                callback_data="staff_performance"
            )
        ],
        [
            InlineKeyboardButton(
                text=workload_text,
                callback_data="staff_workload"
            )
        ],
        [
            InlineKeyboardButton(
                text=attendance_text,
                callback_data="staff_attendance"
            )
        ],
        [
            InlineKeyboardButton(
                text=junior_work_text,
                callback_data="staff_junior_work"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="staff_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_inbox_keyboard(lang='uz'):
    """Kiruvchi xabarlar uchun keyboard"""
    new_messages_text = "🆕 Yangi xabarlar" if lang == "uz" else "🆕 Новые сообщения"
    read_messages_text = "✅ O'qilgan xabarlar" if lang == "uz" else "✅ Прочитанные сообщения"
    urgent_messages_text = "🚨 Shoshilinch xabarlar" if lang == "uz" else "🚨 Срочные сообщения"
    client_messages_text = "👤 Mijoz xabarlari" if lang == "uz" else "👤 Сообщения клиентов"
    system_messages_text = "⚙️ Tizim xabarlari" if lang == "uz" else "⚙️ Системные сообщения"
    back_text = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=new_messages_text,
                callback_data="inbox_new"
            )
        ],
        [
            InlineKeyboardButton(
                text=read_messages_text,
                callback_data="inbox_read"
            )
        ],
        [
            InlineKeyboardButton(
                text=urgent_messages_text,
                callback_data="inbox_urgent"
            )
        ],
        [
            InlineKeyboardButton(
                text=client_messages_text,
                callback_data="inbox_client"
            )
        ],
        [
            InlineKeyboardButton(
                text=system_messages_text,
                callback_data="inbox_system"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="inbox_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_junior_manager_work_keyboard(lang='uz'):
    """Kichik menejerlar ishi uchun keyboard"""
    today_work_text = "📅 Bugungi ishlar" if lang == "uz" else "📅 Работа сегодня"
    week_work_text = "📊 Haftalik ishlar" if lang == "uz" else "📊 Работа за неделю"
    assignments_text = "👨‍🔧 Texnik biriktirishlar" if lang == "uz" else "👨‍🔧 Назначения техников"
    performance_text = "📈 Samaradorlik" if lang == "uz" else "📈 Производительность"
    back_text = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=today_work_text,
                callback_data="junior_today"
            )
        ],
        [
            InlineKeyboardButton(
                text=week_work_text,
                callback_data="junior_week"
            )
        ],
        [
            InlineKeyboardButton(
                text=assignments_text,
                callback_data="junior_assignments"
            )
        ],
        [
            InlineKeyboardButton(
                text=performance_text,
                callback_data="junior_performance"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="junior_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_message_detail_keyboard(message_id: int, lang='uz'):
    """Xabar tafsilotlari uchun keyboard"""
    reply_text = "💬 Javob berish" if lang == "uz" else "💬 Ответить"
    forward_text = "📤 O'tkazish" if lang == "uz" else "📤 Переслать"
    mark_read_text = "✅ O'qilgan deb belgilash" if lang == "uz" else "✅ Отметить как прочитанное"
    delete_text = "🗑️ O'chirish" if lang == "uz" else "🗑️ Удалить"
    back_text = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=reply_text,
                callback_data=f"message_reply_{message_id}"
            ),
            InlineKeyboardButton(
                text=forward_text,
                callback_data=f"message_forward_{message_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=mark_read_text,
                callback_data=f"message_read_{message_id}"
            ),
            InlineKeyboardButton(
                text=delete_text,
                callback_data=f"message_delete_{message_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="message_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)