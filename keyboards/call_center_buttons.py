from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters.callback_data import CallbackData

def call_center_main_menu_reply(lang: str = 'uz') -> ReplyKeyboardMarkup:
    new_order = "🆕 Yangi buyurtma" if lang == 'uz' else "🆕 Новый заказ"
    search = "🔍 Mijoz qidirish" if lang == 'uz' else "🔍 Поиск клиента"
    # Staff application creation buttons
    create_connection = "🔌 Ulanish arizasi yaratish" if lang == 'uz' else "🔌 Создать заявку на подключение"
    create_technical = "🔧 Texnik xizmat yaratish" if lang == 'uz' else "🔧 Создать техническую заявку"
    stats = "📊 Statistikalar" if lang == 'uz' else "📊 Статистика"
    pending = "⏳ Kutilayotgan" if lang == 'uz' else "⏳ Ожидающие"
    feedback = "⭐️ Baholash" if lang == 'uz' else "⭐️ Оценка"
    chat = "💬 Chat" if lang == 'uz' else "💬 Чат"
    change_lang = "🌐 Tilni o'zgartirish" if lang == 'uz' else "🌐 Изменить язык"
    inbox = "📥 Inbox"

    keyboard = [
        [KeyboardButton(text=new_order), KeyboardButton(text=search)],
        [KeyboardButton(text=create_connection), KeyboardButton(text=create_technical)],
        [KeyboardButton(text=feedback), KeyboardButton(text=chat)],
        [KeyboardButton(text=stats), KeyboardButton(text=pending)],
        [KeyboardButton(text=inbox)],
        [KeyboardButton(text=change_lang)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def new_order_reply_menu(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """New order reply keyboard (only back button)"""
    back = "🔄 Orqaga" if lang == 'uz' else "🔄 Назад"
    keyboard = [
        [KeyboardButton(text=back)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def client_search_menu(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Client search menu keyboard with search methods"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔤 " + ("Ism bo'yicha qidirish" if lang == 'uz' else "Поиск по имени")
                ),
                KeyboardButton(
                    text="📞 " + ("Telefon raqami bo'yicha" if lang == 'uz' else "По номеру телефона")
                )
            ],
            [
                KeyboardButton(
                    text="🆔 " + ("ID raqami bo'yicha" if lang == 'uz' else "По ID")
                )
            ],
            [
                KeyboardButton(
                    text="🔙 " + ("Orqaga" if lang == 'uz' else "Назад")
                )
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_client_actions_reply(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Reply keyboard for client actions"""
    order = "📄 Buyurtma yaratish" if lang == 'uz' else "📄 Создать заказ"
    call = "📞 Qo'ng'iroq qilish" if lang == 'uz' else "📞 Позвонить"
    chat = "💬 Chat o'chirish" if lang == 'uz' else "💬 Начать чат"
    details = "🔍 To'liq ma'lumot" if lang == 'uz' else "🔍 Полная информация"
    back = "🔙 Ortga" if lang == 'uz' else "🔙 Назад"

    keyboard = [
        [KeyboardButton(text=order), KeyboardButton(text=call)],
        [KeyboardButton(text=chat), KeyboardButton(text=details)],
        [KeyboardButton(text=back)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def order_types_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Order types selection keyboard with workflow routing"""
    if lang == 'uz':
        types = [
            ("🔌 O'rnatish (Ulanish)", "installation"),
            ("📡 Sozlash (Ulanish)", "setup"),
            ("🔧 Ta'mirlash (Texnik)", "repair"),
            ("🧰 Profilaktika (Texnik)", "maintenance"),
            ("❓ Konsultatsiya (To'g'ridan-to'g'ri)", "consultation")
        ]
    else:
        types = [
            ("🔌 Установка (Подключение)", "installation"),
            ("📡 Настройка (Подключение)", "setup"),
            ("🔧 Ремонт (Техническая)", "repair"),
            ("🧰 Профилактика (Техническая)", "maintenance"),
            ("❓ Консультация (Прямая)", "consultation")
        ]
    
    keyboard = []
    for text, type_ in types:
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"service_type_{type_}")])
    
    keyboard.append([InlineKeyboardButton(text=("🔄 Orqaga" if lang == 'uz' else "🔄 Назад"), callback_data="call_center_back")])
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



def call_center_statistics_menu(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Call center statistics menu"""
    daily_stats = "📅 Bugungi ko'rsatkichlar" if lang == 'uz' else "📅 Сегодняшние показатели"
    weekly_stats = "📊 Haftalik hisobot" if lang == 'uz' else "📊 Недельный отчет"
    monthly_stats = "📈 Oylik hisobot" if lang == 'uz' else "📈 Месячный отчет"
    performance = "🎯 Mening samaradorligim" if lang == 'uz' else "🎯 Моя эффективность"
    conversion = "📈 Konversiya darajasi" if lang == 'uz' else "📈 Коэффициент конверсии"
    back = "🔄 Orqaga" if lang == 'uz' else "🔄 Назад"
    
    keyboard = [
        [KeyboardButton(text=daily_stats),
         KeyboardButton(text=weekly_stats)],
        [KeyboardButton(text=monthly_stats),
         KeyboardButton(text=performance)],
        [KeyboardButton(text=conversion)],
        [KeyboardButton(text=back)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def call_center_supervisor_main_menu(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Call center supervisor main menu"""
    assign_requests = "📋 So'rovlarni tayinlash" if lang == 'uz' else "📋 Назначить запросы"
    pending_assignments = "⏳ Kutilayotgan tayinlashlar" if lang == 'uz' else "⏳ Ожидающие назначения"
    team_performance = "📊 Jamoa samaradorligi" if lang == 'uz' else "📊 Производительность команды"
    back = "🔄 Orqaga" if lang == 'uz' else "🔄 Назад"
    
    keyboard = [
        [KeyboardButton(text=assign_requests), KeyboardButton(text=pending_assignments)],
        [KeyboardButton(text=team_performance)],
        [KeyboardButton(text=back)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def call_center_operator_selection_keyboard(operators: list, lang: str = 'uz') -> InlineKeyboardMarkup:
    """Keyboard for selecting call center operator"""
    keyboard = []
    
    for operator in operators:
        operator_name = operator.get('full_name', f"Operator {operator['id']}")
        keyboard.append([
            InlineKeyboardButton(
                text=f"👤 {operator_name}",
                callback_data=f"assign_cc_operator_{operator['id']}"
            )
        ])
    
    back_text = "🔄 Orqaga" if lang == 'uz' else "🔄 Назад"
    keyboard.append([InlineKeyboardButton(text=back_text, callback_data="cc_supervisor_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def remote_resolution_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Keyboard for remote resolution actions"""
    resolve_text = "✅ Masofadan hal qilish" if lang == 'uz' else "✅ Решить удаленно"
    escalate_text = "⬆️ Yuqoriga ko'tarish" if lang == 'uz' else "⬆️ Эскалировать"
    back_text = "🔄 Orqaga" if lang == 'uz' else "🔄 Назад"
    
    keyboard = [
        [InlineKeyboardButton(text=resolve_text, callback_data="resolve_remotely")],
        [InlineKeyboardButton(text=escalate_text, callback_data="escalate_request")],
        [InlineKeyboardButton(text=back_text, callback_data="cc_operator_back")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def rating_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Rating keyboard for client feedback"""
    rating_text = "Xizmatni baholang" if lang == 'uz' else "Оцените услугу"
    
    keyboard = []
    for i in range(1, 6):
        star_text = "⭐" * i
        keyboard.append([
            InlineKeyboardButton(
                text=f"{star_text} ({i})",
                callback_data=f"rate_service_{i}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)