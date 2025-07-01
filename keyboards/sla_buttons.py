from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

sla_cb = CallbackData('sla', 'action', 'period', 'type')

def get_sla_period_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for selecting SLA monitoring period
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    periods = [
        ("📅 Bugun", "today"),
        ("📅 Bu hafta", "week"),
        ("📅 Bu oy", "month"),
        ("📊 Barchasi", "all")
    ]
    
    buttons = []
    for text, period in periods:
        buttons.append(
            InlineKeyboardButton(
                text=text,
                callback_data=sla_cb.new(
                    action='period',
                    period=period,
                    type='all'
                )
            )
        )
    
    keyboard.add(*buttons)
    return keyboard

def get_sla_type_keyboard(period: str) -> InlineKeyboardMarkup:
    """
    Keyboard for selecting SLA statistics type
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    types = [
        ("⏱ Bajarilish vaqti", "completion_time"),
        ("📊 Bajarilgan/Bajarilmagan", "completion_rate"),
        ("⚠️ Kechiktirilgan", "delayed"),
        ("📈 Tendensiya", "trend")
    ]
    
    for text, type_ in types:
        keyboard.add(
            InlineKeyboardButton(
                text=text,
                callback_data=sla_cb.new(
                    action='type',
                    period=period,
                    type=type_
                )
            )
        )
    
    keyboard.add(
        InlineKeyboardButton(
            text="🔄 Qaytish",
            callback_data=sla_cb.new(
                action='back',
                period='0',
                type='0'
            )
        )
    )
    
    return keyboard

def get_sla_export_keyboard(period: str, type_: str) -> InlineKeyboardMarkup:
    """
    Keyboard for exporting SLA statistics
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            text="📥 Excel formatida yuklash",
            callback_data=sla_cb.new(
                action='export_excel',
                period=period,
                type=type_
            )
        ),
        InlineKeyboardButton(
            text="📊 PDF hisobot",
            callback_data=sla_cb.new(
                action='export_pdf',
                period=period,
                type=type_
            )
        )
    )
    
    keyboard.add(
        InlineKeyboardButton(
            text="🔄 Qaytish",
            callback_data=sla_cb.new(
                action='back_type',
                period=period,
                type='0'
            )
        )
    )
    
    return keyboard 