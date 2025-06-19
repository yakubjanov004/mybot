from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from utils.i18n import get_text

def warehouse_main_menu(language: str) -> InlineKeyboardMarkup:
    """Warehouse main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("inventory_management", language),
                callback_data="warehouse_inventory"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("orders_management", language),
                callback_data="warehouse_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("warehouse_statistics", language),
                callback_data="warehouse_stats"
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

def inventory_menu(language: str) -> InlineKeyboardMarkup:
    """Inventory management menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("add_item", language),
                callback_data="add_inventory_item"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("update_item", language),
                callback_data="update_inventory_item"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("low_stock_report", language),
                callback_data="low_stock_report"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="warehouse_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def orders_menu(language: str) -> InlineKeyboardMarkup:
    """Orders management menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("pending_orders", language),
                callback_data="pending_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("in_progress_orders", language),
                callback_data="in_progress_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("completed_orders", language),
                callback_data="completed_orders"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="warehouse_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def order_status_keyboard(language: str, current_status: str) -> InlineKeyboardMarkup:
    """Order status update keyboard"""
    keyboard = []
    
    if current_status == 'confirmed':
        keyboard.append([
            InlineKeyboardButton(
                text=get_text("start_processing", language),
                callback_data="update_order_status_in_progress"
            )
        ])
    
    if current_status == 'in_progress':
        keyboard.extend([
            [
                InlineKeyboardButton(
                    text=get_text("parts_ready", language),
                    callback_data="update_order_status_parts_ready"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text("ready_for_technician", language),
                    callback_data="update_order_status_ready_for_tech"
                )
            ]
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=get_text("back", language),
            callback_data="warehouse_orders"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def inventory_actions_keyboard(language: str) -> InlineKeyboardMarkup:
    """Inventory item actions keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("update_quantity", language),
                callback_data="update_quantity"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("set_min_quantity", language),
                callback_data="set_min_quantity"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("delete_item", language),
                callback_data="delete_item"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("back", language),
                callback_data="warehouse_inventory"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
