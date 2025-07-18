from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_call_center_supervisor_main_menu(lang: str = 'uz') -> ReplyKeyboardMarkup:
    inbox = "📥 Inbox"
    orders = "📝 Buyurtmalar" if lang == 'uz' else "📝 Заказы"
    # Staff application creation buttons
    create_connection = "🔌 Ulanish arizasi yaratish" if lang == 'uz' else "🔌 Создать заявку на подключение"
    create_technical = "🔧 Texnik xizmat yaratish" if lang == 'uz' else "🔧 Создать техническую заявку"
    statistics = "📊 Statistikalar" if lang == 'uz' else "📊 Статистика"
    feedback = "⭐️ Fikr-mulohaza" if lang == 'uz' else "⭐️ Обратная связь"
    change_lang = "🌐 Tilni o'zgartirish" if lang == 'uz' else "🌐 Изменить язык"
    main_menu = "🏠 Bosh menyu" if lang == 'uz' else "🏠 Главное меню"
    keyboard = [
        [KeyboardButton(text=inbox)],
        [KeyboardButton(text=orders)],
        [KeyboardButton(text=create_connection), KeyboardButton(text=create_technical)],
        [KeyboardButton(text=statistics)],
        [KeyboardButton(text=feedback)],
        [KeyboardButton(text=change_lang)],
        [KeyboardButton(text=main_menu)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
