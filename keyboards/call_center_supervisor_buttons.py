from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_call_center_supervisor_main_menu(lang: str = 'uz') -> ReplyKeyboardMarkup:
    inbox = "📥 Inbox"
    orders = "📝 Buyurtmalar" if lang == 'uz' else "📝 Заказы"
    statistics = "📊 Statistikalar" if lang == 'uz' else "📊 Статистика"
    feedback = "⭐️ Fikr-mulohaza" if lang == 'uz' else "⭐️ Обратная связь"
    change_lang = "🌐 Tilni o'zgartirish" if lang == 'uz' else "🌐 Изменить язык"
    main_menu = "🏠 Bosh menyu" if lang == 'uz' else "🏠 Главное меню"
    keyboard = [
        [KeyboardButton(text=inbox)],
        [KeyboardButton(text=orders)],
        [KeyboardButton(text=statistics)],
        [KeyboardButton(text=feedback)],
        [KeyboardButton(text=change_lang)],
        [KeyboardButton(text=main_menu)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
