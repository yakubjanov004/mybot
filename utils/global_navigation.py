from typing import Dict, List, Optional, Callable
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.get_lang import get_user_language, get_keyboard_language_text
from utils.get_role import get_user_role
from utils.callback_utils import create_inline_button, Actions
from utils.logger import setup_module_logger

logger = setup_module_logger("global_navigation")

class NavigationManager:
    """Manages global navigation across the bot"""
    
    def __init__(self):
        self._menu_builders: Dict[str, Callable] = {}
        self._breadcrumbs: Dict[int, List[str]] = {}  # user_id -> breadcrumb list
    
    def register_menu_builder(self, role: str, builder: Callable):
        """Register menu builder for specific role"""
        self._menu_builders[role] = builder
    
    async def get_main_menu(self, user, language: str = None) -> ReplyKeyboardMarkup:
        """Get main menu for user based on role"""
        try:
            if not language:
                language = await get_user_language(user)
            
            user_role = await get_user_role(user)
            
            # Get role-specific menu builder
            if user_role in self._menu_builders:
                return await self._menu_builders[user_role](language)
            
            # Default client menu
            return await self._build_client_menu(language)
            
        except Exception as e:
            logger.error(f"Error getting main menu: {str(e)}")
            return await self._build_client_menu(language or 'ru')
    
    async def _build_client_menu(self, language: str) -> ReplyKeyboardMarkup:
        """Build client main menu"""
        texts = get_keyboard_language_text(language)
        
        keyboard = [
            [KeyboardButton(text=texts['new_request'])],
            [KeyboardButton(text=texts['my_requests'])],
            [
                KeyboardButton(text=texts['profile']),
                KeyboardButton(text=texts['help'])
            ],
            [
                KeyboardButton(text=texts['language']),
                KeyboardButton(text=texts['contact'])
            ]
        ]
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    async def _build_admin_menu(self, language: str) -> ReplyKeyboardMarkup:
        """Build admin main menu"""
        if language == 'uz':
            keyboard = [
                [KeyboardButton(text="👥 Foydalanuvchilar")],
                [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📋 Zayavkalar")],
                [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="📝 Loglar")],
                [KeyboardButton(text="🌐 Til"), KeyboardButton(text="❓ Yordam")]
            ]
        else:
            keyboard = [
                [KeyboardButton(text="👥 Пользователи")],
                [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📋 Заявки")],
                [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="📝 Логи")],
                [KeyboardButton(text="🌐 Язык"), KeyboardButton(text="❓ Помощь")]
            ]
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    async def _build_technician_menu(self, language: str) -> ReplyKeyboardMarkup:
        """Build technician main menu"""
        if language == 'uz':
            keyboard = [
                [KeyboardButton(text="📋 Mening vazifalarim")],
                [KeyboardButton(text="✅ Bajarilgan"), KeyboardButton(text="🔄 Jarayonda")],
                [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🆘 Yordam so'rash")],
                [KeyboardButton(text="👤 Profil"), KeyboardButton(text="🌐 Til")]
            ]
        else:
            keyboard = [
                [KeyboardButton(text="📋 Мои задачи")],
                [KeyboardButton(text="✅ Выполненные"), KeyboardButton(text="🔄 В работе")],
                [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🆘 Запрос помощи")],
                [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🌐 Язык")]
            ]
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    async def _build_manager_menu(self, language: str) -> ReplyKeyboardMarkup:
        """Build manager main menu"""
        if language == 'uz':
            keyboard = [
                [KeyboardButton(text="📋 Barcha zayavkalar")],
                [KeyboardButton(text="👨‍🔧 Texniklar"), KeyboardButton(text="📊 Hisobotlar")],
                [KeyboardButton(text="⚡ Tayinlash"), KeyboardButton(text="📈 Statistika")],
                [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="🌐 Til")]
            ]
        else:
            keyboard = [
                [KeyboardButton(text="📋 Все заявки")],
                [KeyboardButton(text="👨‍🔧 Техники"), KeyboardButton(text="📊 Отчеты")],
                [KeyboardButton(text="⚡ Назначение"), KeyboardButton(text="📈 Статистика")],
                [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🌐 Язык")]
            ]
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    async def _build_warehouse_menu(self, language: str) -> ReplyKeyboardMarkup:
        """Build warehouse main menu"""
        if language == 'uz':
            keyboard = [
                [KeyboardButton(text="📦 Ombor")],
                [KeyboardButton(text="📥 Qabul qilish"), KeyboardButton(text="📤 Berish")],
                [KeyboardButton(text="📊 Hisobot"), KeyboardButton(text="⚠️ Kam qolgan")],
                [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="🌐 Til")]
            ]
        else:
            keyboard = [
                [KeyboardButton(text="📦 Склад")],
                [KeyboardButton(text="📥 Приход"), KeyboardButton(text="📤 Выдача")],
                [KeyboardButton(text="📊 Отчет"), KeyboardButton(text="⚠️ Мало на складе")],
                [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🌐 Язык")]
            ]
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    async def _build_call_center_menu(self, language: str) -> ReplyKeyboardMarkup:
        """Build call center main menu"""
        if language == 'uz':
            keyboard = [
                [KeyboardButton(text="📞 Qo'ng'iroqlar")],
                [KeyboardButton(text="👤 Mijoz qidirish"), KeyboardButton(text="➕ Yangi zayavka")],
                [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📋 Qayta qo'ng'iroq")],
                [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="🌐 Til")]
            ]
        else:
            keyboard = [
                [KeyboardButton(text="📞 Звонки")],
                [KeyboardButton(text="👤 Поиск клиента"), KeyboardButton(text="➕ Новая заявка")],
                [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📋 Перезвонить")],
                [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🌐 Язык")]
            ]
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    def add_breadcrumb(self, user_id: int, item: str):
        """Add breadcrumb for user navigation"""
        if user_id not in self._breadcrumbs:
            self._breadcrumbs[user_id] = []
        
        self._breadcrumbs[user_id].append(item)
        
        # Limit breadcrumb depth
        if len(self._breadcrumbs[user_id]) > 10:
            self._breadcrumbs[user_id] = self._breadcrumbs[user_id][-10:]
    
    def get_breadcrumbs(self, user_id: int) -> List[str]:
        """Get breadcrumbs for user"""
        return self._breadcrumbs.get(user_id, [])
    
    def clear_breadcrumbs(self, user_id: int):
        """Clear breadcrumbs for user"""
        if user_id in self._breadcrumbs:
            del self._breadcrumbs[user_id]
    
    def pop_breadcrumb(self, user_id: int) -> Optional[str]:
        """Remove and return last breadcrumb"""
        if user_id in self._breadcrumbs and self._breadcrumbs[user_id]:
            return self._breadcrumbs[user_id].pop()
        return None

# Global navigation manager instance
nav_manager = NavigationManager()

# Register menu builders
nav_manager.register_menu_builder('admin', nav_manager._build_admin_menu)
nav_manager.register_menu_builder('technician', nav_manager._build_technician_menu)
nav_manager.register_menu_builder('manager', nav_manager._build_manager_menu)
nav_manager.register_menu_builder('warehouse', nav_manager._build_warehouse_menu)
nav_manager.register_menu_builder('call_center', nav_manager._build_call_center_menu)
nav_manager.register_menu_builder('client', nav_manager._build_client_menu)

# Utility functions
async def get_main_menu_keyboard(user) -> ReplyKeyboardMarkup:
    """Get main menu keyboard for user"""
    return await nav_manager.get_main_menu(user)

def create_back_to_menu_keyboard(language: str = 'ru') -> InlineKeyboardMarkup:
    """Create back to main menu keyboard"""
    text = "🏠 Главное меню" if language == 'ru' else "🏠 Asosiy menyu"
    keyboard = [[create_inline_button(text, Actions.BACK, target="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_navigation_keyboard(current_page: int, total_pages: int, 
                             action_prefix: str, **extra_data) -> InlineKeyboardMarkup:
    """Create navigation keyboard with page controls"""
    keyboard = []
    
    # Navigation row
    nav_row = []
    
    if current_page > 1:
        nav_row.append(create_inline_button(
            "⬅️", f"{action_prefix}_page", 
            page=current_page - 1, **extra_data
        ))
    
    nav_row.append(InlineKeyboardButton(
        text=f"{current_page}/{total_pages}",
        callback_data="noop"
    ))
    
    if current_page < total_pages:
        nav_row.append(create_inline_button(
            "➡️", f"{action_prefix}_page",
            page=current_page + 1, **extra_data
        ))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Back button
    keyboard.append([create_inline_button("⬅️ Назад", Actions.BACK)])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_action_keyboard(actions: List[Dict], language: str = 'ru') -> InlineKeyboardMarkup:
    """Create keyboard with action buttons"""
    keyboard = []
    
    for action in actions:
        button = create_inline_button(
            action['text'],
            action['action'],
            **action.get('data', {})
        )
        keyboard.append([button])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_yes_no_keyboard(yes_action: str, no_action: str = Actions.CANCEL,
                          language: str = 'ru', **extra_data) -> InlineKeyboardMarkup:
    """Create yes/no confirmation keyboard"""
    if language == 'uz':
        yes_text, no_text = "✅ Ha", "❌ Yo'q"
    else:
        yes_text, no_text = "✅ Да", "❌ Нет"
    
    keyboard = [
        [
            create_inline_button(yes_text, yes_action, **extra_data),
            create_inline_button(no_text, no_action, **extra_data)
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_role_specific_keyboard(user, context: str, language: str = None) -> Optional[InlineKeyboardMarkup]:
    """Get role-specific keyboard for context"""
    try:
        if not language:
            language = await get_user_language(user)
        
        user_role = await get_user_role(user)
        
        # Define role-specific keyboards for different contexts
        keyboards = {
            'zayavka_actions': {
                'admin': _create_admin_zayavka_keyboard,
                'manager': _create_manager_zayavka_keyboard,
                'technician': _create_technician_zayavka_keyboard,
                'client': _create_client_zayavka_keyboard
            }
        }
        
        if context in keyboards and user_role in keyboards[context]:
            return keyboards[context][user_role](language)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting role-specific keyboard: {str(e)}")
        return None

def _create_admin_zayavka_keyboard(language: str) -> InlineKeyboardMarkup:
    """Create admin zayavka action keyboard"""
    if language == 'uz':
        buttons = [
            [create_inline_button("👁 Ko'rish", Actions.ZAYAVKA_VIEW)],
            [create_inline_button("✏️ Tahrirlash", Actions.ZAYAVKA_EDIT)],
            [create_inline_button("👨‍🔧 Tayinlash", Actions.ZAYAVKA_ASSIGN)],
            [create_inline_button("❌ O'chirish", "zayavka_delete")]
        ]
    else:
        buttons = [
            [create_inline_button("👁 Просмотр", Actions.ZAYAVKA_VIEW)],
            [create_inline_button("✏️ Редактировать", Actions.ZAYAVKA_EDIT)],
            [create_inline_button("👨‍🔧 Назначить", Actions.ZAYAVKA_ASSIGN)],
            [create_inline_button("❌ Удалить", "zayavka_delete")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _create_manager_zayavka_keyboard(language: str) -> InlineKeyboardMarkup:
    """Create manager zayavka action keyboard"""
    if language == 'uz':
        buttons = [
            [create_inline_button("👁 Ko'rish", Actions.ZAYAVKA_VIEW)],
            [create_inline_button("👨‍🔧 Tayinlash", Actions.ZAYAVKA_ASSIGN)],
            [create_inline_button("🔄 O'tkazish", Actions.ZAYAVKA_TRANSFER)]
        ]
    else:
        buttons = [
            [create_inline_button("👁 Просмотр", Actions.ZAYAVKA_VIEW)],
            [create_inline_button("👨‍🔧 Назнач.", Actions.ZAYAVKA_ASSIGN)],
            [create_inline_button("🔄 Передать", Actions.ZAYAVKA_TRANSFER)]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _create_technician_zayavka_keyboard(language: str) -> InlineKeyboardMarkup:
    """Create technician zayavka action keyboard"""
    if language == 'uz':
        buttons = [
            [create_inline_button("👁 Ko'rish", Actions.ZAYAVKA_VIEW)],
            [create_inline_button("▶️ Boshlash", Actions.TASK_START)],
            [create_inline_button("✅ Tugatish", Actions.TASK_COMPLETE)]
        ]
    else:
        buttons = [
            [create_inline_button("👁 Просмотр", Actions.ZAYAVKA_VIEW)],
            [create_inline_button("▶️ Начать", Actions.TASK_START)],
            [create_inline_button("✅ Завершить", Actions.TASK_COMPLETE)]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _create_client_zayavka_keyboard(language: str) -> InlineKeyboardMarkup:
    """Create client zayavka action keyboard"""
    if language == 'uz':
        buttons = [
            [create_inline_button("👁 Ko'rish", Actions.ZAYAVKA_VIEW)],
            [create_inline_button("❌ Bekor qilish", Actions.ZAYAVKA_CANCEL)]
        ]
    else:
        buttons = [
            [create_inline_button("👁 Просмотр", Actions.ZAYAVKA_VIEW)],
            [create_inline_button("❌ Отменить", Actions.ZAYAVKA_CANCEL)]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Breadcrumb utilities
def add_breadcrumb(user_id: int, item: str):
    """Add breadcrumb for navigation"""
    nav_manager.add_breadcrumb(user_id, item)

def get_breadcrumb_text(user_id: int, language: str = 'ru') -> str:
    """Get breadcrumb text for display"""
    breadcrumbs = nav_manager.get_breadcrumbs(user_id)
    if not breadcrumbs:
        return ""
    
    separator = " → " if language == 'ru' else " → "
    return separator.join(breadcrumbs[-3:])  # Show last 3 levels

def clear_navigation(user_id: int):
    """Clear user navigation history"""
    nav_manager.clear_breadcrumbs(user_id)
