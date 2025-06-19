from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.i18n import get_text

def controllers_main_menu(language: str) -> InlineKeyboardMarkup:
    """Controllers main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("orders_control", language),
                callback_data="orders_control"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("technicians_control", language),
                callback_data="technicians_control"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("system_reports", language),
                callback_data="system_reports"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("quality_control", language),
                callback_data="quality_control"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def orders_control_menu(language: str) -> InlineKeyboardMarkup:
    """Orders control menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("priority_orders", language),
                callback_data="priority_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("delayed_orders", language),
                callback_data="delayed_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("assign_technicians", language),
                callback_data="assign_technicians"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("order_analytics", language),
                callback_data="order_analytics"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="controllers_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def technicians_menu(language: str) -> InlineKeyboardMarkup:
    """Technicians control menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("performance_report", language),
                callback_data="performance_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("workload_balance", language),
                callback_data="workload_balance"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("technician_ratings", language),
                callback_data="technician_ratings"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("schedule_management", language),
                callback_data="schedule_management"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="controllers_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def reports_menu(language: str) -> InlineKeyboardMarkup:
    """Reports menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("daily_report", language),
                callback_data="daily_report"
            ),
            InlineKeyboardButton(
                text=get_text("weekly_report", language),
                callback_data="weekly_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("monthly_report", language),
                callback_data="monthly_report"
            ),
            InlineKeyboardButton(
                text=get_text("custom_report", language),
                callback_data="custom_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("export_data", language),
                callback_data="export_data"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="controllers_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def order_priority_keyboard(language: str) -> InlineKeyboardMarkup:
    """Order priority selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"🔴 {get_text('high_priority', language)}",
                callback_data="set_priority_high"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🟡 {get_text('medium_priority', language)}",
                callback_data="set_priority_medium"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🟢 {get_text('normal_priority', language)}",
                callback_data="set_priority_normal"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="orders_control"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def technician_assignment_keyboard(language: str, technicians: list) -> InlineKeyboardMarkup:
    """Technician assignment keyboard"""
    keyboard = []
    
    for tech in technicians:
        keyboard.append([
            InlineKeyboardButton(
                text=f"👨‍🔧 {tech['full_name']} ({tech['active_orders']} заказов)",
                callback_data=f"assign_tech_{tech['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=get_text("back", language),
            callback_data="assign_technicians"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
