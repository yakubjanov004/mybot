from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_manager_main_keyboard(lang='uz'):
    """Generate main keyboard for manager with locale support"""
    create_application_text = "📝 Ariza yaratish" if lang == "uz" else "📝 Создать заявку"
    view_applications_text = "📋 Arizalarni ko'rish" if lang == "uz" else "📋 Просмотр заявок"
    filter_applications_text = "🔍 Filtrlar" if lang == "uz" else "🔍 Фильтры"
    change_status_text = "🔄 Status o'zgartirish" if lang == "uz" else "🔄 Изменить статус"
    assign_responsible_text = "👨‍🔧 Texnik biriktirish" if lang == "uz" else "👨‍🔧 Назначить техника"
    generate_report_text = "📊 Hisobot yaratish" if lang == "uz" else "📊 Создать отчет"
    equipment_issuance_text = "📦 Jihozlar berish" if lang == "uz" else "📦 Выдача оборудования"
    ready_for_installation_text = "✅ O'rnatishga tayyor" if lang == "uz" else "✅ Готов к установке"
    change_language_text = "🌐 Tilni o'zgartirish" if lang == "uz" else "🌐 Изменить язык"
    main_menu_text = "🏠 Asosiy menyu" if lang == "uz" else "🏠 Главное меню"
    
    keyboard = [
        [KeyboardButton(text=create_application_text),
         KeyboardButton(text=view_applications_text)],
        [KeyboardButton(text=filter_applications_text),
         KeyboardButton(text=change_status_text)],
        [KeyboardButton(text=assign_responsible_text),
         KeyboardButton(text=generate_report_text)],
        [KeyboardButton(text=equipment_issuance_text),
         KeyboardButton(text=ready_for_installation_text)],
        [KeyboardButton(text=change_language_text)]
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
    
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    buttons = []
    for status in statuses:
        buttons.append(
            InlineKeyboardButton(
                text=status_texts.get(status, status),
                callback_data=f"status_{status}_{application_id}"
            )
        )
    
    # Add back button
    buttons.append(
        InlineKeyboardButton(
            text=back_text,
            callback_data="back_to_status_menu"
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

def get_filter_keyboard(lang='uz', show_clear=False) -> InlineKeyboardMarkup:
    """Application filter keyboard with locale support"""
    new_text = "🆕 Yangi" if lang == "uz" else "🆕 Новый"
    in_progress_text = "⏳ Jarayonda" if lang == "uz" else "⏳ В процессе"
    completed_text = "✅ Bajarilgan" if lang == "uz" else "✅ Выполнено"
    cancelled_text = "❌ Bekor qilingan" if lang == "uz" else "❌ Отменено"
    all_statuses_text = "📋 Barchasi" if lang == "uz" else "📋 Все"
    today_text = "📅 Bugun" if lang == "uz" else "📅 Сегодня"
    yesterday_text = "📅 Kecha" if lang == "uz" else "📅 Вчера"
    this_week_text = "📅 Bu hafta" if lang == "uz" else "📅 На этой неделе"
    this_month_text = "📅 Bu oy" if lang == "uz" else "📅 В этом месяце"
    unassigned_text = "👨‍🔧 Biriktirilmagan" if lang == "uz" else "👨‍🔧 Не назначен"
    assigned_text = "👨‍🔧 Biriktirilgan" if lang == "uz" else "👨‍🔧 Назначен"
    clear_filter_text = "🔄 Filterni tozalash" if lang == "uz" else "🔄 Очистить фильтр"
    
    buttons = [
        [
            InlineKeyboardButton(text=new_text, callback_data="filter_status_new"),
            InlineKeyboardButton(text=in_progress_text, callback_data="filter_status_in_progress"),
            InlineKeyboardButton(text=completed_text, callback_data="filter_status_completed")
        ],
        [
            InlineKeyboardButton(text=cancelled_text, callback_data="filter_status_cancelled"),
            InlineKeyboardButton(text=all_statuses_text, callback_data="filter_status_all")
        ],
        [
            InlineKeyboardButton(text=today_text, callback_data="filter_date_today"),
            InlineKeyboardButton(text=yesterday_text, callback_data="filter_date_yesterday")
        ],
        [
            InlineKeyboardButton(text=this_week_text, callback_data="filter_date_week"),
            InlineKeyboardButton(text=this_month_text, callback_data="filter_date_month")
        ],
        [
            InlineKeyboardButton(text=unassigned_text, callback_data="filter_tech_unassigned"),
            InlineKeyboardButton(text=assigned_text, callback_data="filter_tech_assigned")
        ]
    ]
    
    if show_clear:
        buttons.append([
            InlineKeyboardButton(text=clear_filter_text, callback_data="filter_clear")
        ])
    
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
