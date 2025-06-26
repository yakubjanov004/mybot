from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from utils.i18n import i18n

def get_contact_keyboard(lang="uz"):
    """Kontakt ulashish klaviaturasi - 2 tilda"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i18n.get_message(lang, "share_contact"), request_contact=True)]],
        resize_keyboard=True
    )
    return keyboard

def get_technician_main_menu_keyboard(lang="uz"):
    """Montajchi asosiy menyu klaviaturasi - 2 tilda"""
    buttons = [
        [KeyboardButton(text=i18n.get_message(lang, "my_tasks"))],
        [KeyboardButton(text=i18n.get_message(lang, "reports"))],
        [KeyboardButton(text=i18n.get_message(lang, "change_language"))]
    ]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard

def get_back_technician_keyboard(lang="uz"):
    """Orqaga qaytish klaviaturasi - 2 tilda"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get_message(lang, "back"))]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_language_keyboard():
    """Til tanlash klaviaturasi - har doim bir xil"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
        ]
    )
    return keyboard

def get_task_action_keyboard(zayavka_id: int, status: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """Task action keyboard with validation and status - 2 tilda"""
    if not isinstance(zayavka_id, int) or zayavka_id <= 0:
        raise ValueError("Invalid zayavka_id")
    
    # Tugmalar matnlari til bo'yicha
    accept_text = "✅ Qabul qilish" if lang == "uz" else "✅ Принять"
    start_text = "▶️ Boshlash" if lang == "uz" else "▶️ Начать"
    complete_text = "✅ Yakunlash" if lang == "uz" else "✅ Завершить"
    transfer_text = "🔄 O'tkazish so'rovi" if lang == "uz" else "🔄 Запрос передачи"
    
    if status == 'assigned':
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=accept_text, callback_data=f"accept_task_{zayavka_id}"),
                InlineKeyboardButton(text=transfer_text, callback_data=f"transfer_task_{zayavka_id}")
            ]
        ])
    elif status == 'accepted':
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=start_text, callback_data=f"start_task_{zayavka_id}"),
                InlineKeyboardButton(text=transfer_text, callback_data=f"transfer_task_{zayavka_id}")
            ]
        ])
    elif status == 'in_progress':
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=complete_text, callback_data=f"complete_task_{zayavka_id}"),
                InlineKeyboardButton(text=transfer_text, callback_data=f"transfer_task_{zayavka_id}")
            ]
        ])
    else:
        return None

def get_completion_keyboard(zayavka_id, lang="uz"):
    """Yakunlash klaviaturasi - 2 tilda"""
    complete_text = "✅ Yakunlash" if lang == "uz" else "✅ Завершить"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=complete_text, callback_data=f"complete_with_comment_{zayavka_id}")
        ]
    ])

def get_technician_selection_keyboard(technicians: list, lang: str = "uz") -> InlineKeyboardMarkup:
    """Technician selection keyboard with safe callback data - 2 tilda"""
    buttons = []
    task_word = "vazifa" if lang == "uz" else "задач"
    
    for tech in technicians:
        active_tasks = tech.get('active_tasks', 0)
        text = f"👨‍🔧 {tech['full_name']} ({active_tasks} {task_word})"
        callback_data = f"select_tech_{tech['id']}"  
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        )])
    
    cancel_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отмена"
    buttons.append([InlineKeyboardButton(
        text=cancel_text,
        callback_data="cancel_assignment"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
