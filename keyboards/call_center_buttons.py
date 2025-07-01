from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters.callback_data import CallbackData

def call_center_main_menu(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Call center main menu keyboard"""
    new_order = "🆕 Yangi buyurtma" if lang == 'uz' else "🆕 Новый заказ"
    search = "🔍 Mijoz qidirish" if lang == 'uz' else "🔍 Поиск клиента"
    stats = "📊 Statistika" if lang == 'uz' else "📊 Статистика"
    pending = "⏳ Kutilayotgan" if lang == 'uz' else "⏳ Ожидающие"
    feedback = "⭐️ Baholash" if lang == 'uz' else "⭐️ Оценка"
    chat = "💬 Chat" if lang == 'uz' else "💬 Чат"
    keyboard = [
        [InlineKeyboardButton(text=new_order, callback_data="new_order"),
         InlineKeyboardButton(text=search, callback_data="client_search")],
        [InlineKeyboardButton(text=feedback, callback_data="request_feedback"),
         InlineKeyboardButton(text=chat, callback_data="start_chat")],
        [InlineKeyboardButton(text=stats, callback_data="call_statistics"),
         InlineKeyboardButton(text=pending, callback_data="pending_calls")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def call_center_main_menu_reply(lang: str = 'uz') -> ReplyKeyboardMarkup:
    new_order = "🆕 Yangi buyurtma" if lang == 'uz' else "🆕 Новый заказ"
    search = "🔍 Mijoz qidirish" if lang == 'uz' else "🔍 Поиск клиента"
    stats = "📊 Statistika" if lang == 'uz' else "📊 Статистика"
    pending = "⏳ Kutilayotgan" if lang == 'uz' else "⏳ Ожидающие"
    feedback = "⭐️ Baholash" if lang == 'uz' else "⭐️ Оценка"
    chat = "💬 Chat" if lang == 'uz' else "💬 Чат"
    keyboard = [
        [KeyboardButton(text=new_order), KeyboardButton(text=search)],
        [KeyboardButton(text=feedback), KeyboardButton(text=chat)],
        [KeyboardButton(text=stats), KeyboardButton(text=pending)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def new_order_menu(lang: str = 'uz') -> InlineKeyboardMarkup:
    """New order menu keyboard"""
    back = "🔄 Orqaga" if lang == 'uz' else "🔄 Назад"
    keyboard = [
        [InlineKeyboardButton(text=back, callback_data="call_center_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def client_search_menu(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Client search menu keyboard"""
    back = "🔄 Orqaga" if lang == 'uz' else "🔄 Назад"
    keyboard = [
        [InlineKeyboardButton(text=back, callback_data="call_center_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def order_types_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Order types selection keyboard"""
    types = [
        ("🔧 Ta'mirlash", "repair"),
        ("🔌 O'rnatish", "installation"),
        ("🧰 Profilaktika", "maintenance"),
        ("📡 Sozlash", "setup"),
        ("❓ Konsultatsiya", "consultation")
    ]
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=f"service_type_{type_}") for text, type_ in types],
        [InlineKeyboardButton(text=("🔄 Orqaga" if lang == 'uz' else "🔄 Назад"), callback_data="call_center_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def call_status_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Call status keyboard"""
    priorities = [
        ("🔴 Yuqori", "high"),
        ("🟡 O'rta", "medium"),
        ("🟢 Past", "low")
    ]
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=f"priority_{priority}") for text, priority in priorities],
        [InlineKeyboardButton(text=("🔄 Orqaga" if lang == 'uz' else "🔄 Назад"), callback_data="call_center_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def callback_schedule_keyboard(language: str) -> InlineKeyboardMarkup:
    """Callback scheduling keyboard"""
    schedule_in_1_hour_text = "⏰ 1 soatdan keyin" if language == "uz" else "⏰ Через 1 час"
    schedule_in_2_hours_text = "⏰ 2 soatdan keyin" if language == "uz" else "⏰ Через 2 часа"
    schedule_tomorrow_text = "📅 Ertaga" if language == "uz" else "📅 Завтра"
    custom_time_text = "🕐 Maxsus vaqt" if language == "uz" else "🕐 Специальное время"
    back_text = "◀️ Orqaga" if language == "uz" else "◀️ Назад"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=schedule_in_1_hour_text,
                callback_data="callback_1h"
            )
        ],
        [
            InlineKeyboardButton(
                text=schedule_in_2_hours_text,
                callback_data="callback_2h"
            )
        ],
        [
            InlineKeyboardButton(
                text=schedule_tomorrow_text,
                callback_data="callback_tomorrow"
            )
        ],
        [
            InlineKeyboardButton(
                text=custom_time_text,
                callback_data="callback_custom"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="call_center_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def call_result_keyboard(language: str) -> InlineKeyboardMarkup:
    """Call result keyboard"""
    order_created_text = "✅ Buyurtma yaratildi" if language == "uz" else "✅ Заказ создан"
    callback_scheduled_text = "📞 Qayta qo'ng'iroq rejalashtirildi" if language == "uz" else "📞 Обратный звонок запланирован"
    information_provided_text = "ℹ️ Ma'lumot berildi" if language == "uz" else "ℹ️ Предоставлена информация"
    no_answer_text = "📵 Javob yo'q" if language == "uz" else "📵 Нет ответа"
    client_refused_text = "❌ Mijoz rad etdi" if language == "uz" else "❌ Клиент отказался"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=order_created_text,
                callback_data="call_result_order"
            )
        ],
        [
            InlineKeyboardButton(
                text=callback_scheduled_text,
                callback_data="call_result_callback"
            )
        ],
        [
            InlineKeyboardButton(
                text=information_provided_text,
                callback_data="call_result_info"
            )
        ],
        [
            InlineKeyboardButton(
                text=no_answer_text,
                callback_data="call_result_no_answer"
            )
        ],
        [
            InlineKeyboardButton(
                text=client_refused_text,
                callback_data="call_result_refused"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
