from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_technician_main_menu_keyboard(lang="uz"):
    """Technician main menu keyboard"""
    my_tasks_text = "📋 Vazifalarim" if lang == "uz" else "📋 Мои задачи"
    reports_text = "📊 Hisobotlar" if lang == "uz" else "📊 Отчеты"
    help_text = "🆘 Yordam" if lang == "uz" else "🆘 Помощь"
    change_language_text = "🌐 Tilni o'zgartirish" if lang == "uz" else "🌐 Изменить язык"
    
    keyboard = [
        [KeyboardButton(text=my_tasks_text), KeyboardButton(text=reports_text)],
        [KeyboardButton(text=help_text)],
        [KeyboardButton(text=change_language_text)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_technician_help_menu(language: str) -> ReplyKeyboardMarkup:
    """Technician help menu"""
    request_help_text = "🆘 Yordam so'rash" if language == "uz" else "🆘 Запросить помощь"
    send_location_text = "📍 Geolokatsiya yuborish" if language == "uz" else "📍 Отправить геолокацию"
    contact_manager_text = "👨‍💼 Menejer bilan bog'lanish" if language == "uz" else "👨‍💼 Связаться с менеджером"
    equipment_request_text = "🔧 Jihoz so'rash" if language == "uz" else "🔧 Запросить оборудование"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [KeyboardButton(text=request_help_text)],
        [KeyboardButton(text=send_location_text)],
        [KeyboardButton(text=contact_manager_text)],
        [KeyboardButton(text=equipment_request_text)],
        [KeyboardButton(text=back_text)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_help_request_types_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Help request types keyboard"""
    equipment_issue_text = "🔧 Jihoz muammosi" if language == "uz" else "🔧 Проблема с оборудованием"
    parts_needed_text = "🛠️ Qo'shimcha ehtiyot qism kerak" if language == "uz" else "🛠️ Нужны дополнительные запчасти"
    technical_question_text = "❓ Texnik savol" if language == "uz" else "❓ Технический вопрос"
    emergency_text = "🚨 Favqulodda holat" if language == "uz" else "🚨 Экстренная ситуация"
    client_issue_text = "👤 Mijoz bilan muammo" if language == "uz" else "👤 Проблема с клиентом"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [KeyboardButton(text=equipment_issue_text)],
        [KeyboardButton(text=parts_needed_text)],
        [KeyboardButton(text=technical_question_text)],
        [KeyboardButton(text=emergency_text)],
        [KeyboardButton(text=client_issue_text)],
        [KeyboardButton(text=back_text)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_back_technician_keyboard(lang="uz"):
    """Back to main menu keyboard for technician"""
    back_text = "🏠 Asosiy menyu" if lang == "uz" else "🏠 Главное меню"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=back_text)]],
        resize_keyboard=True
    )

def get_contact_keyboard(lang="uz"):
    """Contact sharing keyboard"""
    share_contact_text = "📱 Kontakt ulashish" if lang == "uz" else "📱 Поделиться контактом"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=share_contact_text, request_contact=True)]],
        resize_keyboard=True
    )
    return keyboard

def get_language_keyboard(role="technician"):
    """Language selection keyboard"""
    prefix = f"{role}_lang_" if role != "technician" else "tech_lang_"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data=f"{prefix}uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"{prefix}ru")]
        ]
    )
    return keyboard

def get_technician_selection_keyboard(technicians):
    """Keyboard for selecting technician for task transfer"""
    keyboard = []
    for tech in technicians:
        keyboard.append([
            InlineKeyboardButton(
                text=f"👨‍🔧 {tech['full_name']}",
                callback_data=f"transfer_to_tech_{tech['id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_task_action_keyboard(task_id, status, lang="uz") -> InlineKeyboardMarkup:
    """Task action keyboard"""
    buttons = []
    
    if status == 'assigned':
        accept_text = "✅ Qabul qilish" if lang == "uz" else "✅ Принять"
        transfer_text = "🔄 O'tkazish" if lang == "uz" else "🔄 Передать"
        buttons = [
            [InlineKeyboardButton(text=accept_text, callback_data=f"accept_task_{task_id}")],
            [InlineKeyboardButton(text=transfer_text, callback_data=f"transfer_task_{task_id}")]
        ]
    elif status == 'accepted':
        start_text = "▶️ Boshlash" if lang == "uz" else "▶️ Начать"
        transfer_text = "🔄 O'tkazish" if lang == "uz" else "🔄 Передать"
        buttons = [
            [InlineKeyboardButton(text=start_text, callback_data=f"start_task_{task_id}")],
            [InlineKeyboardButton(text=transfer_text, callback_data=f"transfer_task_{task_id}")]
        ]
    elif status == 'in_progress':
        complete_text = "✅ Yakunlash" if lang == "uz" else "✅ Завершить"
        buttons = [
            [InlineKeyboardButton(text=complete_text, callback_data=f"complete_task_{task_id}")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_equipment_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Equipment request keyboard for technician"""
    request_text = "🔧 Jihoz so'rang" if lang == "uz" else "🔧 Запросить оборудование"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=request_text,
                callback_data="tech_equipment_request"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="tech_back_to_help"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_completion_keyboard(task_id, lang="uz"):
    """Completion keyboard for task"""
    with_comment_text = "✅ Bajarildi (izoh bilan)" if lang == "uz" else "✅ Выполнено (с комментарием)"
    without_comment_text = "✅ Bajarildi" if lang == "uz" else "✅ Выполнено"
    
    keyboard = [
        [InlineKeyboardButton(text=with_comment_text, callback_data=f"complete_with_comment_{task_id}")],
        [InlineKeyboardButton(text=without_comment_text, callback_data=f"complete_without_comment_{task_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_reports_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Reports menu keyboard for technician"""
    stats_text = "📊 Statistikalarim" if lang == "uz" else "📊 Мои статистики"
    detailed_text = "📄 Batafsil" if lang == "uz" else "📄 Подробнее"
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=stats_text,
                callback_data="tech_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text=detailed_text,
                callback_data="tech_detailed_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="tech_back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
