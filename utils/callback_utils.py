import json
from typing import Dict, Any, Optional, Union
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.logger import setup_module_logger

logger = setup_module_logger("callback_utils")

class CallbackData:
    """Helper class for managing callback data"""
    
    def __init__(self, action: str, **kwargs):
        self.action = action
        self.data = kwargs
    
    def pack(self) -> str:
        """Pack callback data into string"""
        try:
            callback_dict = {
                'action': self.action,
                **self.data
            }
            
            # Ensure all values are JSON serializable
            for key, value in callback_dict.items():
                if not isinstance(value, (str, int, float, bool, type(None))):
                    callback_dict[key] = str(value)
            
            packed = json.dumps(callback_dict, separators=(',', ':'))
            
            # Telegram callback data limit is 64 bytes
            if len(packed.encode('utf-8')) > 64:
                logger.warning(f"Callback data too long: {len(packed)} chars")
                # Truncate or use alternative approach
                return self._pack_compact()
            
            return packed
            
        except Exception as e:
            logger.error(f"Error packing callback data: {str(e)}")
            return f"error:{self.action}"
    
    def _pack_compact(self) -> str:
        """Pack callback data in compact format"""
        # Use shorter format for large data
        parts = [self.action]
        
        for key, value in self.data.items():
            if isinstance(value, (int, str)) and len(str(value)) < 10:
                parts.append(f"{key[:2]}:{value}")
        
        return "|".join(parts)[:64]
    
    @classmethod
    def unpack(cls, callback_data: str) -> Optional['CallbackData']:
        """Unpack callback data from string"""
        try:
            if callback_data.startswith('error:'):
                action = callback_data.split(':', 1)[1]
                return cls(action)
            
            if '|' in callback_data:
                # Handle compact format
                return cls._unpack_compact(callback_data)
            
            data = json.loads(callback_data)
            action = data.pop('action', 'unknown')
            return cls(action, **data)
            
        except Exception as e:
            logger.error(f"Error unpacking callback data: {str(e)}")
            return None
    
    @classmethod
    def _unpack_compact(cls, callback_data: str) -> 'CallbackData':
        """Unpack compact format callback data"""
        parts = callback_data.split('|')
        action = parts[0]
        data = {}
        
        for part in parts[1:]:
            if ':' in part:
                key, value = part.split(':', 1)
                # Try to convert to int if possible
                try:
                    data[key] = int(value)
                except ValueError:
                    data[key] = value
        
        return cls(action, **data)
    
    def __str__(self) -> str:
        return f"CallbackData(action='{self.action}', data={self.data})"

# Predefined callback actions
class Actions:
    """Predefined callback actions"""
    
    # Navigation
    BACK = "back"
    CANCEL = "cancel"
    CONFIRM = "confirm"
    REFRESH = "refresh"
    
    # User management
    USER_PROFILE = "user_profile"
    USER_EDIT = "user_edit"
    USER_BLOCK = "user_block"
    USER_UNBLOCK = "user_unblock"
    USER_ROLE_CHANGE = "user_role_change"
    
    # Zayavka management
    ZAYAVKA_VIEW = "zayavka_view"
    ZAYAVKA_EDIT = "zayavka_edit"
    ZAYAVKA_ASSIGN = "zayavka_assign"
    ZAYAVKA_COMPLETE = "zayavka_complete"
    ZAYAVKA_CANCEL = "zayavka_cancel"
    ZAYAVKA_TRANSFER = "zayavka_transfer"
    
    # Technician actions
    TASK_ACCEPT = "task_accept"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_TRANSFER = "task_transfer"
    HELP_REQUEST = "help_request"
    
    # Warehouse actions
    MATERIAL_VIEW = "material_view"
    MATERIAL_EDIT = "material_edit"
    MATERIAL_ISSUE = "material_issue"
    INVENTORY_UPDATE = "inventory_update"
    
    # Admin actions
    ADMIN_USERS = "admin_users"
    ADMIN_STATS = "admin_stats"
    ADMIN_LOGS = "admin_logs"
    ADMIN_SETTINGS = "admin_settings"
    
    # Language selection
    LANG_SELECT = "lang_select"
    
    # Pagination
    PAGE_NEXT = "page_next"
    PAGE_PREV = "page_prev"
    PAGE_GOTO = "page_goto"

def create_callback_data(action: str, **kwargs) -> str:
    """Create callback data string"""
    return CallbackData(action, **kwargs).pack()

def parse_callback_data(callback_data: str) -> Optional[CallbackData]:
    """Parse callback data string"""
    return CallbackData.unpack(callback_data)

def create_inline_button(text: str, action: str, **kwargs) -> InlineKeyboardButton:
    """Create inline keyboard button with callback data"""
    callback_data = create_callback_data(action, **kwargs)
    return InlineKeyboardButton(text=text, callback_data=callback_data)

def create_url_button(text: str, url: str) -> InlineKeyboardButton:
    """Create inline keyboard button with URL"""
    return InlineKeyboardButton(text=text, url=url)

def create_pagination_keyboard(current_page: int, total_pages: int, 
                             action_prefix: str = "page", **extra_data) -> InlineKeyboardMarkup:
    """Create pagination keyboard"""
    keyboard = []
    
    # Navigation buttons
    nav_buttons = []
    
    if current_page > 1:
        nav_buttons.append(create_inline_button(
            "⬅️ Назад", Actions.PAGE_PREV, 
            page=current_page - 1, **extra_data
        ))
    
    # Page info
    nav_buttons.append(InlineKeyboardButton(
        text=f"{current_page}/{total_pages}",
        callback_data="noop"
    ))
    
    if current_page < total_pages:
        nav_buttons.append(create_inline_button(
            "Вперед ➡️", Actions.PAGE_NEXT,
            page=current_page + 1, **extra_data
        ))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_confirmation_keyboard(confirm_action: str, cancel_action: str = Actions.CANCEL,
                               **extra_data) -> InlineKeyboardMarkup:
    """Create confirmation keyboard"""
    keyboard = [
        [
            create_inline_button("✅ Подтвердить", confirm_action, **extra_data),
            create_inline_button("❌ Отмена", cancel_action, **extra_data)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_back_keyboard(action: str = Actions.BACK, **extra_data) -> InlineKeyboardMarkup:
    """Create simple back keyboard"""
    keyboard = [[create_inline_button("⬅️ Назад", action, **extra_data)]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_language_keyboard() -> InlineKeyboardMarkup:
    """Create language selection keyboard"""
    keyboard = [
        [
            create_inline_button("🇺🇿 O'zbek", Actions.LANG_SELECT, lang="uz"),
            create_inline_button("🇷🇺 Русский", Actions.LANG_SELECT, lang="ru")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_role_selection_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Create role selection keyboard for admin"""
    roles = [
        ("👤 Клиент", "client"),
        ("🔧 Техник", "technician"),
        ("📞 Call-центр", "call_center"),
        ("👨‍💼 Менеджер", "manager"),
        ("📦 Склад", "warehouse"),
        ("🔍 Контролер", "controller"),
        ("👑 Админ", "admin")
    ]
    
    keyboard = []
    for text, role in roles:
        keyboard.append([create_inline_button(
            text, Actions.USER_ROLE_CHANGE, 
            user_id=user_id, role=role
        )])
    
    keyboard.append([create_inline_button("⬅️ Назад", Actions.BACK)])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_status_keyboard(zayavka_id: int) -> InlineKeyboardMarkup:
    """Create status change keyboard"""
    statuses = [
        ("🆕 Новая", "new"),
        ("⏳ В ожидании", "pending"),
        ("👨‍🔧 Назначена", "assigned"),
        ("🔄 В работе", "in_progress"),
        ("✅ Завершена", "completed"),
        ("❌ Отменена", "cancelled")
    ]
    
    keyboard = []
    for text, status in statuses:
        keyboard.append([create_inline_button(
            text, "status_change",
            zayavka_id=zayavka_id, status=status
        )])
    
    keyboard.append([create_inline_button("⬅️ Назад", Actions.BACK)])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Utility functions for callback handling
async def handle_callback_error(callback_query, error_message: str = "Произошла ошибка"):
    """Handle callback query errors"""
    try:
        await callback_query.answer(error_message, show_alert=True)
    except Exception as e:
        logger.error(f"Error handling callback error: {str(e)}")

async def answer_callback_query(callback_query, text: str = None, show_alert: bool = False):
    """Answer callback query with error handling"""
    try:
        await callback_query.answer(text, show_alert=show_alert)
    except Exception as e:
        logger.error(f"Error answering callback query: {str(e)}")

def validate_callback_data(callback_data: CallbackData, required_fields: list) -> bool:
    """Validate callback data has required fields"""
    if not callback_data:
        return False
    
    for field in required_fields:
        if field not in callback_data.data:
            logger.warning(f"Missing required field in callback data: {field}")
            return False
    
    return True

# Callback data builders for specific use cases
class CallbackBuilders:
    """Callback data builders for common use cases"""
    
    @staticmethod
    def user_action(action: str, user_id: int, **kwargs) -> str:
        """Build user action callback"""
        return create_callback_data(action, user_id=user_id, **kwargs)
    
    @staticmethod
    def zayavka_action(action: str, zayavka_id: int, **kwargs) -> str:
        """Build zayavka action callback"""
        return create_callback_data(action, zayavka_id=zayavka_id, **kwargs)
    
    @staticmethod
    def material_action(action: str, material_id: int, **kwargs) -> str:
        """Build material action callback"""
        return create_callback_data(action, material_id=material_id, **kwargs)
    
    @staticmethod
    def pagination(action: str, page: int, **kwargs) -> str:
        """Build pagination callback"""
        return create_callback_data(action, page=page, **kwargs)
