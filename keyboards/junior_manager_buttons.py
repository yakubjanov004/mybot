from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from utils.staff_application_localization import get_text, StaffApplicationTexts

def get_junior_manager_main_keyboard(lang='uz'):
    """Generate main keyboard for junior_manager with Inbox button"""
    # Staff application creation button (connection requests only) with proper localization
    create_connection_text = get_text(StaffApplicationTexts.CREATE_CONNECTION_REQUEST, lang)
    view_applications_text = "📋 Zayavkalarni ko'rish" if lang == "uz" else "📋 Просмотр заявок"
    filter_applications_text = "🔍 Zayavkani filtrlash" if lang == "uz" else "🔍 Фильтровать заявки"
    reports_text = "📊 Hisobotlar" if lang == "uz" else "📊 Отчеты"
    change_language_text = "🌐 Tilni o'zgartirish" if lang == "uz" else "🌐 Изменить язык"
    inbox_text = "📥 Inbox"

    keyboard = [
        [KeyboardButton(text=inbox_text)],
        [KeyboardButton(text=create_connection_text)],
        [KeyboardButton(text=view_applications_text)],
        [KeyboardButton(text=filter_applications_text)],
        [KeyboardButton(text=reports_text)],
        [KeyboardButton(text=change_language_text)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_order_filter_keyboard(lang='uz'):
    """Zayavkalarni filtrlash uchun tugmalar"""
    new_text = "🆕 Yangi zayavkalar" if lang == "uz" else "🆕 Новые заявки"
    assigned_text = "👨‍🔧 Tayinlangan zayavkalar" if lang == "uz" else "👨‍🔧 Назначенные заявки"
    in_progress_text = "⚡ Jarayonda" if lang == "uz" else "⚡ В процессе"
    completed_text = "✅ Bajarilgan" if lang == "uz" else "✅ Завершенные"
    cancelled_text = "❌ Bekor qilingan" if lang == "uz" else "❌ Отмененные"
    today_text = "📅 Bugungi" if lang == "uz" else "📅 Сегодня"
    yesterday_text = "📅 Kechagi" if lang == "uz" else "📅 Вчера"
    
    keyboard = [
        [InlineKeyboardButton(text=new_text, callback_data="filter_orders:new")],
        [InlineKeyboardButton(text=assigned_text, callback_data="filter_orders:assigned")],
        [InlineKeyboardButton(text=in_progress_text, callback_data="filter_orders:in_progress")],
        [InlineKeyboardButton(text=completed_text, callback_data="filter_orders:completed")],
        [InlineKeyboardButton(text=cancelled_text, callback_data="filter_orders:cancelled")],
        [InlineKeyboardButton(text=today_text, callback_data="filter_orders:today")],
        [InlineKeyboardButton(text=yesterday_text, callback_data="filter_orders:yesterday")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_order_action_keyboard(order_id, status, lang='uz'):
    """Zayavka uchun harakatlar tugmalari"""
    keyboard = []
    
    if status == 'new':
        assign_text = "👨‍🔧 Texnikka tayinlash" if lang == "uz" else "👨‍🔧 Назначить техника"
        keyboard.append([InlineKeyboardButton(text=assign_text, callback_data=f"assign_order:{order_id}")])
    
    if status in ['new', 'assigned', 'in_progress']:
        cancel_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отменить"
        keyboard.append([InlineKeyboardButton(text=cancel_text, callback_data=f"cancel_order:{order_id}")])
    
    if status == 'in_progress':
        complete_text = "✅ Bajarilgan deb belgilash" if lang == "uz" else "✅ Отметить как выполненную"
        keyboard.append([InlineKeyboardButton(text=complete_text, callback_data=f"complete_order:{order_id}")])
    
    back_text = "◀️ Orqaga" if lang == "uz" else "◀️ Назад"
    keyboard.append([InlineKeyboardButton(text=back_text, callback_data="back_to_orders")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_assign_order_keyboard(order_id, technicians, lang='uz'):
    """Zayavkani texnikka tayinlash uchun tugmalar"""
    keyboard = []
    
    for tech in technicians:
        keyboard.append([InlineKeyboardButton(
            text=f"👨‍🔧 {tech['name']} ({tech['phone']})",
            callback_data=f"assign_to_tech:{order_id}:{tech['id']}"
        )])
    
    cancel_text = "❌ Bekor qilish" if lang == "uz" else "❌ Отмена"
    keyboard.append([InlineKeyboardButton(text=cancel_text, callback_data="cancel_assign")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 

def get_junior_manager_inbox_actions(order_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Texnikka biriktirish", callback_data=f"action_assign_technician_zayavka_{order_id}"))
    keyboard.add(InlineKeyboardButton("Izoh qo'shish", callback_data=f"action_comment_zayavka_{order_id}"))
    keyboard.add(InlineKeyboardButton("Yakunlash", callback_data=f"action_complete_zayavka_{order_id}"))
    return keyboard

def get_application_keyboard(application_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_{application_id}")],
            [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{application_id}")]
        ]
    )
    return keyboard