from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.templates import get_template_text

async def get_manager_main_keyboard(lang='uz'):
    """Generate main keyboard for manager with locale support"""
    keyboard = [
        [KeyboardButton(text=await get_template_text(lang, 'manager', 'create_application')),
         KeyboardButton(text=await get_template_text(lang, 'manager', 'view_applications'))],
        [KeyboardButton(text=await get_template_text(lang, 'manager', 'filter_applications')),
         KeyboardButton(text=await get_template_text(lang, 'manager', 'change_status'))],
        [KeyboardButton(text=await get_template_text(lang, 'manager', 'assign_responsible')),
         KeyboardButton(text=await get_template_text(lang, 'manager', 'generate_report'))],
        [KeyboardButton(text=await get_template_text(lang, 'manager', 'equipment_issuance')),
         KeyboardButton(text=await get_template_text(lang, 'manager', 'ready_for_installation'))],
        [KeyboardButton(text=await get_template_text(lang, 'common', 'change_language'))]  # Changed from back to language
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_status_keyboard(statuses: list, locale: dict, application_id: int, lang='uz') -> InlineKeyboardMarkup:
    """Get status selection keyboard with application_id in callback and locale support"""
    buttons = []
    for status in statuses:
        buttons.append(
            InlineKeyboardButton(
                text=locale["statuses"].get(status, status),
                callback_data=f"status_{status}_{application_id}"
            )
        )
    
    # Add back button
    buttons.append(
        InlineKeyboardButton(
            text=locale["common"]["back"],
            callback_data="back_to_status_menu"
        )
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[buttons[:-1], [buttons[-1]]]  # Last button on separate row
    )
    return keyboard

def get_report_type_keyboard(locale, lang='uz'):
    """Generate inline keyboard for report type selection with locale support"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=locale["manager"]["report_word"],
            callback_data="report_word"
        ),
        InlineKeyboardButton(
            text=locale["manager"]["report_pdf"],
            callback_data="report_pdf"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text=locale["common"]["back"],
            callback_data="back_to_report_menu"
        )
    )
    builder.adjust(2, 1)  # 2 buttons in first row, 1 in second
    return builder.as_markup()

def get_equipment_keyboard(equipment_list, locale, lang='uz'):
    """Generate inline keyboard for equipment selection with locale support"""
    builder = InlineKeyboardBuilder()
    for equipment in equipment_list:
        builder.add(InlineKeyboardButton(
            text=f"📦 {equipment['name']}",
            callback_data=f"equipment_{equipment['id']}"
        ))
    
    # Add back button
    builder.add(InlineKeyboardButton(
        text=locale["common"]["back"],
        callback_data="back_to_equipment_menu"
    ))
    
    builder.adjust(1)  # One button per row
    return builder.as_markup()

def get_assign_technician_keyboard(application_id, technicians, locale, lang='uz'):
    """Generate inline keyboard for assigning a technician to an application with locale support"""
    builder = InlineKeyboardBuilder()
    
    for tech in technicians:
        text = f"👨‍🔧 {tech['full_name']}"
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"manager_assign_zayavka_{application_id}_{tech['id']}"
        ))
    
    # Add back button
    builder.add(InlineKeyboardButton(
        text=locale["common"]["back"],
        callback_data="back_to_assign_technician"
    ))
    
    builder.adjust(1)  # One button per row
    return builder.as_markup()

def get_back_inline_keyboard(locale, lang='uz'):
    """Generate inline keyboard with a single 'Back' button with locale support"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=locale["common"]["back"],
        callback_data="back_to_assign_technician"
    ))
    return builder.as_markup()

def get_filter_keyboard(locale, lang='uz', show_clear=False) -> InlineKeyboardMarkup:
    """Application filter keyboard with locale support"""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🆕 {locale['statuses'].get('new', 'Yangi')}",
                callback_data="filter_status_new"
            ),
            InlineKeyboardButton(
                text=f"⏳ {locale['statuses'].get('in_progress', 'Jarayonda')}",
                callback_data="filter_status_in_progress"
            ),
            InlineKeyboardButton(
                text=f"✅ {locale['statuses'].get('completed', 'Bajarilgan')}",
                callback_data="filter_status_completed"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"❌ {locale['statuses'].get('cancelled', 'Bekor qilingan')}",
                callback_data="filter_status_cancelled"
            ),
            InlineKeyboardButton(
                text=f"📋 {locale['manager'].get('all_statuses', 'Barchasi')}",
                callback_data="filter_status_all"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📅 {locale['manager'].get('today', 'Bugun')}",
                callback_data="filter_date_today"
            ),
            InlineKeyboardButton(
                text=f"📅 {locale['manager'].get('yesterday', 'Kecha')}",
                callback_data="filter_date_yesterday"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📅 {locale['manager'].get('this_week', 'Bu hafta')}",
                callback_data="filter_date_week"
            ),
            InlineKeyboardButton(
                text=f"📅 {locale['manager'].get('this_month', 'Bu oy')}",
                callback_data="filter_date_month"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"👨‍🔧 {locale['manager'].get('unassigned', 'Biriktirilmagan')}",
                callback_data="filter_tech_unassigned"
            ),
            InlineKeyboardButton(
                text=f"👨‍🔧 {locale['manager'].get('assigned', 'Biriktirilgan')}",
                callback_data="filter_tech_assigned"
            )
        ]
    ]
    
    if show_clear:
        buttons.append([
            InlineKeyboardButton(
                text=f"🔄 {locale['manager'].get('clear_filter', 'Filterni tozalash')}",
                callback_data="filter_clear"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_filtered_applications_keyboard(applications: list, locale: dict, lang='uz') -> InlineKeyboardMarkup:
    """Show filtered applications with clear button"""
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
        text=f"🔄 {locale['common']['clear']}", 
        callback_data="filter_clear"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_filter_results_keyboard(page: int, total_pages: int, has_next: bool, has_prev: bool, locale, lang='uz') -> InlineKeyboardMarkup:
    """Filtered results pagination keyboard with locale support"""
    buttons = []
    
    # Navigation buttons
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(text=f"◀️ {locale['common']['prev']}", callback_data=f"filter_page_{page-1}"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text=f"{locale['common']['next']} ▶️", callback_data=f"filter_page_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Page info
    if total_pages > 1:
        buttons.append([
            InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="filter_page_info")
        ])
    
    # Control buttons
    control_row = [
        InlineKeyboardButton(text=locale["common"]["clear"], callback_data="filter_clear"),
        InlineKeyboardButton(text=locale["common"]["back"], callback_data="back_to_main_menu")
    ]
    buttons.append(control_row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def manager_main_menu(locale, lang='uz') -> InlineKeyboardMarkup:
    """Manager main menu inline keyboard with locale support"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=locale["manager"]["view_applications"], callback_data="view_applications"),
            InlineKeyboardButton(text=locale["manager"]["filter_applications"], callback_data="filter_applications")
        ],
        [
            InlineKeyboardButton(text=locale["manager"]["generate_report"], callback_data="generate_report"),
            InlineKeyboardButton(text=locale["manager"]["assign_responsible"], callback_data="assign_technician")
        ],
        [
            InlineKeyboardButton(text=locale["manager"]["equipment_issuance"], callback_data="equipment_issuance"),
            InlineKeyboardButton(text=locale["manager"]["ready_for_installation"], callback_data="ready_for_installation")
        ],
        [
            InlineKeyboardButton(text=locale["manager"]["change_status"], callback_data="change_status"),
            InlineKeyboardButton(text=locale["manager"]["create_application"], callback_data="create_application")
        ]
    ])
    return keyboard

def get_confirmation_keyboard(locale, action_type="confirm", lang='uz') -> InlineKeyboardMarkup:
    """Generate confirmation keyboard with locale support"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=locale["common"]["confirm"], callback_data=f"confirm_{action_type}"),
            InlineKeyboardButton(text=locale["common"]["cancel"], callback_data=f"cancel_{action_type}")
        ]
    ])
    return keyboard

def get_application_actions_keyboard(application_id: int, locale, lang='uz') -> InlineKeyboardMarkup:
    """Generate application action buttons with locale support"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"📊 {locale['manager']['change_status']}", 
                callback_data=f"app_change_status_{application_id}"
            ),
            InlineKeyboardButton(
                text=f"👤 {locale['manager']['assign_responsible']}", 
                callback_data=f"app_assign_tech_{application_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"👁️ {locale['common']['view']}", 
                callback_data=f"app_view_details_{application_id}"
            ),
            InlineKeyboardButton(
                text=locale["common"]["back"], 
                callback_data="back_to_applications"
            )
        ]
    ])
    return keyboard

def get_manager_language_keyboard(locale, lang='uz') -> InlineKeyboardMarkup:
    """Language selection keyboard for manager"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="manager_lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="manager_lang_ru")
        ]
    ])
    return keyboard

async def get_manager_back_keyboard(lang='uz'):
    """Manager uchun faqat 'Bosh menyu' tugmasi chiqadi"""
    main_menu_text = await get_template_text(lang, 'manager', 'main_menu')
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=main_menu_text)]],
        resize_keyboard=True
    )
    return keyboard
