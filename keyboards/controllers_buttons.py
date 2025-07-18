from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.staff_application_localization import get_text, StaffApplicationTexts

def controllers_main_menu(lang='uz'):
    """Controllers asosiy menyu"""
    # Use proper localization for staff application creation buttons
    create_connection_text = get_text(StaffApplicationTexts.CREATE_CONNECTION_REQUEST, lang)
    create_technical_text = get_text(StaffApplicationTexts.CREATE_TECHNICAL_SERVICE, lang)
    
    if lang == 'uz':
        keyboard = [
            [KeyboardButton(text="📋 Buyurtmalar nazorati"), KeyboardButton(text="👨‍🔧 Texniklar nazorati")],
            [KeyboardButton(text=create_connection_text), KeyboardButton(text=create_technical_text)],
            [KeyboardButton(text="🎯 Sifat nazorati"), KeyboardButton(text="📊 Hisobotlar")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🌐 Til o'zgartirish")],
            [KeyboardButton(text="📥 Inbox")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📋 Контроль заказов"), KeyboardButton(text="👨‍🔧 Контроль техников")],
            [KeyboardButton(text=create_connection_text), KeyboardButton(text=create_technical_text)],
            [KeyboardButton(text="🎯 Контроль качества"), KeyboardButton(text="📊 Отчеты")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="�� Изменить язык")],
            [KeyboardButton(text="📥 Inbox")],
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def orders_control_menu(lang='uz'):
    """Buyurtmalar nazorati menyusi"""
    if lang == 'uz':
        keyboard = [
            [KeyboardButton(text="🆕 Yangi buyurtmalar"), KeyboardButton(text="⏳ Kutilayotgan")],
            [KeyboardButton(text="🔴 Muammoli buyurtmalar"), KeyboardButton(text="📊 Buyurtmalar hisoboti")],
            [KeyboardButton(text="🏠 Bosh menyu")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="🆕 Новые заказы"), KeyboardButton(text="⏳ Ожидающие")],
            [KeyboardButton(text="🔴 Проблемные заказы"), KeyboardButton(text="📊 Отчет по заказам")],
            [KeyboardButton(text="🏠 Главное меню")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def technicians_menu(lang='uz'):
    """Texniklar menyusi"""
    if lang == 'uz':
        keyboard = [
            [KeyboardButton(text="📋 Texniklar ro'yxati"), KeyboardButton(text="📊 Texniklar samaradorligi")],
            [KeyboardButton(text="🎯 Vazifa tayinlash"), KeyboardButton(text="📈 Texniklar hisoboti")],
            [KeyboardButton(text="🏠 Bosh menyu")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📋 Список техников"), KeyboardButton(text="📊 Эффективность техников")],
            [KeyboardButton(text="🎯 Назначение задач"), KeyboardButton(text="📈 Отчет по техникам")],
            [KeyboardButton(text="🏠 Главное меню")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def quality_control_menu(lang='uz'):
    """Sifat nazorati menyusi"""
    if lang == 'uz':
        keyboard = [
            [KeyboardButton(text="💬 Mijoz fikrlari"), KeyboardButton(text="⚠️ Muammoli holatlar")],
            [KeyboardButton(text="📊 Sifat baholash"), KeyboardButton(text="📈 Sifat tendensiyalari")],
            [KeyboardButton(text="📋 Sifat hisoboti"), KeyboardButton(text="🏠 Bosh menyu")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="💬 Отзывы клиентов"), KeyboardButton(text="⚠️ Проблемные ситуации")],
            [KeyboardButton(text="📊 Оценка качества"), KeyboardButton(text="📈 Тенденции качества")],
            [KeyboardButton(text="📋 Отчет по качеству"), KeyboardButton(text="🏠 Главное меню")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def reports_menu(lang='uz'):
    """Hisobotlar menyusi"""
    if lang == 'uz':
        keyboard = [
            [KeyboardButton(text="📈 Tizim hisoboti"), KeyboardButton(text="👨‍🔧 Texniklar hisoboti")],
            [KeyboardButton(text="⭐ Sifat hisoboti"), KeyboardButton(text="📅 Kunlik hisobot")],
            [KeyboardButton(text="📊 Haftalik hisobot"), KeyboardButton(text="🏠 Bosh menyu")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="📈 Системный отчет"), KeyboardButton(text="👨‍🔧 Отчет по техникам")],
            [KeyboardButton(text="⭐ Отчет по качеству"), KeyboardButton(text="📅 Ежедневный отчет")],
            [KeyboardButton(text="�� Еженедельный отчет"), KeyboardButton(text="🏠 Главное меню")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def language_keyboard():
    """Til tanlash klaviaturasi"""
    keyboard = [
        [KeyboardButton(text="🇺🇿 O'zbek tili"), KeyboardButton(text="🇷🇺 Русский язык")],
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def order_priority_keyboard(lang='uz'):
    """Buyurtma ustuvorligi klaviaturasi"""
    if lang == 'uz':
        keyboard = [
            [InlineKeyboardButton(text="🔴 Yuqori", callback_data="set_priority_high")],
            [InlineKeyboardButton(text="🟡 O'rta", callback_data="set_priority_medium")],
            [InlineKeyboardButton(text="🟢 Past", callback_data="set_priority_low")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="controllers_back")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="🔴 Высокий", callback_data="set_priority_high")],
            [InlineKeyboardButton(text="🟡 Средний", callback_data="set_priority_medium")],
            [InlineKeyboardButton(text="🟢 Низкий", callback_data="set_priority_low")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="controllers_back")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def technician_assignment_keyboard(lang='uz', technicians=None):
    """Texnik tayinlash klaviaturasi"""
    keyboard = []
    
    if technicians:
        for tech in technicians[:10]:  # Maksimal 10 ta texnik
            button_text = f"👨‍🔧 {tech['full_name']} ({tech.get('active_tasks', 0)})"
            keyboard.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"assign_tech_{tech['id']}"
            )])
    
    back_text = "◀️ Orqaga" if lang == 'uz' else "◀️ Назад"
    keyboard.append([InlineKeyboardButton(text=back_text, callback_data="controllers_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_to_controllers_menu(lang='uz'):
    """Controllers menyusiga qaytish"""
    if lang == 'uz':
        keyboard = [
            [KeyboardButton(text="🏠 Bosh menyu")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="🏠 Главное меню")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def quality_control_detailed_menu(lang='uz'):
    """Batafsil sifat nazorati menyusi"""
    if lang == 'uz':
        keyboard = [
            [InlineKeyboardButton(text="💬 Mijoz fikrlari", callback_data="quality_customer_feedback")],
            [InlineKeyboardButton(text="⚠️ Hal etilmagan muammolar", callback_data="quality_unresolved_issues")],
            [InlineKeyboardButton(text="📊 Xizmat sifatini baholash", callback_data="quality_service_assessment")],
            [InlineKeyboardButton(text="📈 Sifat tendensiyalari", callback_data="quality_trends")],
            [InlineKeyboardButton(text="📋 Sifat hisoboti", callback_data="quality_reports")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="controllers_back")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="💬 Отзывы клиентов", callback_data="quality_customer_feedback")],
            [InlineKeyboardButton(text="⚠️ Нерешенные проблемы", callback_data="quality_unresolved_issues")],
            [InlineKeyboardButton(text="📊 Оценка качества услуг", callback_data="quality_service_assessment")],
            [InlineKeyboardButton(text="📈 Тенденции качества", callback_data="quality_trends")],
            [InlineKeyboardButton(text="📋 Отчет по качеству", callback_data="quality_reports")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="controllers_back")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def feedback_detailed_filter_menu(lang='uz'):
    """Fikrlarni filtrlash menyusi"""
    if lang == 'uz':
        keyboard = [
            [InlineKeyboardButton(text="⭐⭐⭐⭐⭐ (5)", callback_data="feedback_filter_5")],
            [InlineKeyboardButton(text="⭐⭐⭐⭐ (4)", callback_data="feedback_filter_4")],
            [InlineKeyboardButton(text="⭐⭐⭐ (3)", callback_data="feedback_filter_3")],
            [InlineKeyboardButton(text="⭐⭐ (2)", callback_data="feedback_filter_2")],
            [InlineKeyboardButton(text="⭐ (1)", callback_data="feedback_filter_1")],
            [InlineKeyboardButton(text="📋 Barcha fikrlar", callback_data="feedback_filter_all")],
            [InlineKeyboardButton(text="🕒 So'nggi fikrlar", callback_data="feedback_filter_recent")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="quality_control")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(text="⭐⭐⭐⭐⭐ (5)", callback_data="feedback_filter_5")],
            [InlineKeyboardButton(text="⭐⭐⭐⭐ (4)", callback_data="feedback_filter_4")],
            [InlineKeyboardButton(text="⭐⭐⭐ (3)", callback_data="feedback_filter_3")],
            [InlineKeyboardButton(text="⭐⭐ (2)", callback_data="feedback_filter_2")],
            [InlineKeyboardButton(text="⭐ (1)", callback_data="feedback_filter_1")],
            [InlineKeyboardButton(text="📋 Все отзывы", callback_data="feedback_filter_all")],
            [InlineKeyboardButton(text="🕒 Последние отзывы", callback_data="feedback_filter_recent")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="quality_control")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def technical_service_assignment_keyboard(request_id, technicians=None, lang='uz'):
    """Technical service assignment keyboard"""
    keyboard = []
    
    if technicians:
        for tech in technicians[:10]:  # Maximum 10 technicians
            button_text = f"👨‍🔧 {tech['full_name']}"
            if tech.get('active_tasks'):
                button_text += f" ({tech['active_tasks']})"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"assign_technical_to_technician_{tech['id']}_{request_id}"
            )])
    
    back_text = "◀️ Orqaga" if lang == 'uz' else "◀️ Назад"
    keyboard.append([InlineKeyboardButton(text=back_text, callback_data="controllers_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
