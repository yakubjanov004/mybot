from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.i18n import get_text

def call_center_main_menu(language: str) -> InlineKeyboardMarkup:
    """Call center main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("new_order", language),
                callback_data="new_order"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("client_search", language),
                callback_data="client_search"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("pending_calls", language),
                callback_data="pending_calls"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("call_statistics", language),
                callback_data="call_statistics"
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

def new_order_menu(language: str) -> InlineKeyboardMarkup:
    """New order creation menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("cancel", language),
                callback_data="call_center_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def client_search_menu(language: str) -> InlineKeyboardMarkup:
    """Client search menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("search_by_phone", language),
                callback_data="search_by_phone"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("search_by_name", language),
                callback_data="search_by_name"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="call_center_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def order_types_keyboard(language: str) -> InlineKeyboardMarkup:
    """Order types selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("repair_service", language),
                callback_data="service_type_repair"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("maintenance_service", language),
                callback_data="service_type_maintenance"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("installation_service", language),
                callback_data="service_type_installation"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("consultation_service", language),
                callback_data="service_type_consultation"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("emergency_service", language),
                callback_data="service_type_emergency"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="call_center_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def call_status_keyboard(language: str) -> InlineKeyboardMarkup:
    """Call status and priority keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"🔴 {get_text('urgent', language)}",
                callback_data="priority_urgent"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🟡 {get_text('high', language)}",
                callback_data="priority_high"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🟢 {get_text('normal', language)}",
                callback_data="priority_normal"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🔵 {get_text('low', language)}",
                callback_data="priority_low"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def callback_schedule_keyboard(language: str) -> InlineKeyboardMarkup:
    """Callback scheduling keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("schedule_in_1_hour", language),
                callback_data="callback_1h"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("schedule_in_2_hours", language),
                callback_data="callback_2h"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("schedule_tomorrow", language),
                callback_data="callback_tomorrow"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("custom_time", language),
                callback_data="callback_custom"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="call_center_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def call_result_keyboard(language: str) -> InlineKeyboardMarkup:
    """Call result keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("order_created", language),
                callback_data="call_result_order"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("callback_scheduled", language),
                callback_data="call_result_callback"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("information_provided", language),
                callback_data="call_result_info"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("no_answer", language),
                callback_data="call_result_no_answer"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("client_refused", language),
                callback_data="call_result_refused"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
