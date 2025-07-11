from typing import Optional, Union
from aiogram.types import User, Message, CallbackQuery
from database.base_queries import get_user_by_telegram_id
from config import config
from utils.logger import setup_module_logger

logger = setup_module_logger("get_lang")

async def get_user_language(user: Union[User, int]) -> str:
    """Get user's preferred language"""
    try:
        # If user is an integer (telegram_id), get from database directly
        if isinstance(user, int):
            db_user = await get_user_by_telegram_id(user)
            return db_user.get('language', config.DEFAULT_LANGUAGE) if db_user else config.DEFAULT_LANGUAGE
        
        # If user is a User object
        if user.language_code:
            # Map Telegram language codes to our supported languages
            lang_map = {
                'uz': 'uz',
                'ru': 'ru', 
            }
            
            # Check for exact match first
            if user.language_code in lang_map:
                return lang_map[user.language_code]
            
            # Check for language prefix (e.g., 'ru-RU' -> 'ru')
            lang_prefix = user.language_code.split('-')[0]
            if lang_prefix in lang_map:
                return lang_map[lang_prefix]
        
        # Try to get from database first
        db_user = await get_user_by_telegram_id(user.id)
        if db_user and db_user.get('language'):
            return db_user['language']
        
        # Default language
        return config.DEFAULT_LANGUAGE
    except Exception as e:
        logger.error(f"Error getting user language: {str(e)}")
        return config.DEFAULT_LANGUAGE

async def get_language_from_message(message: Message) -> str:
    """Get language from message"""
    if message.from_user:
        return await get_user_language(message.from_user)
    return config.DEFAULT_LANGUAGE

async def get_language_from_callback(callback: CallbackQuery) -> str:
    """Get language from callback query"""
    if callback.from_user:
        return await get_user_language(callback.from_user)
    return config.DEFAULT_LANGUAGE

def get_language_flag(language: str) -> str:
    """Get flag emoji for language"""
    flags = {
        'uz': '🇺🇿',
        'ru': '🇷🇺'
    }
    return flags.get(language, '🌐')

def get_language_name(language: str, in_language: str = None) -> str:
    """Get language name"""
    names = {
        'uz': {
            'uz': "O'zbek",
            'ru': "Узбекский"
        },
        'ru': {
            'uz': "Rus",
            'ru': "Русский"
        }
    }
    
    if in_language and language in names and in_language in names[language]:
        return names[language][in_language]
    
    # Default names
    default_names = {
        'uz': "O'zbek",
        'ru': "Русский"
    }
    
    return default_names.get(language, language)

def is_supported_language(language: str) -> bool:
    """Check if language is supported"""
    return language in config.AVAILABLE_LANGUAGES

# Language-specific text helpers
class LanguageText:
    """Helper class for language-specific text"""
    
    def __init__(self, uz: str, ru: str):
        self.uz = uz
        self.ru = ru
    
    def get(self, language: str) -> str:
        """Get text in specified language"""
        if language == 'uz':
            return self.uz
        elif language == 'ru':
            return self.ru
        else:
            return self.ru  # Default to Russian
    
    def __str__(self) -> str:
        return f"LanguageText(uz='{self.uz}', ru='{self.ru}')"

# Common text constants
class CommonTexts:
    """Common text constants in multiple languages"""
    
    YES = LanguageText("Ha", "Да")
    NO = LanguageText("Yo'q", "Нет")
    CANCEL = LanguageText("Bekor qilish", "Отмена")
    BACK = LanguageText("Orqaga", "Назад")
    NEXT = LanguageText("Keyingi", "Далее")
    SAVE = LanguageText("Saqlash", "Сохранить")
    DELETE = LanguageText("O'chirish", "Удалить")
    EDIT = LanguageText("Tahrirlash", "Редактировать")
    VIEW = LanguageText("Ko'rish", "Просмотр")
    CONFIRM = LanguageText("Tasdiqlash", "Подтвердить")
    
    # Status texts
    NEW = LanguageText("Yangi", "Новая")
    PENDING = LanguageText("Kutilmoqda", "В ожидании")
    ASSIGNED = LanguageText("Tayinlangan", "Назначена")
    IN_PROGRESS = LanguageText("Bajarilmoqda", "В работе")
    COMPLETED = LanguageText("Bajarildi", "Завершена")
    CANCELLED = LanguageText("Bekor qilindi", "Отменена")
    
    # Role texts
    CLIENT = LanguageText("Mijoz", "Клиент")
    TECHNICIAN = LanguageText("Texnik", "Техник")
    MANAGER = LanguageText("Menejer", "Менеджер")
    ADMIN = LanguageText("Admin", "Админ")
    CALL_CENTER = LanguageText("Call-markaz", "Call-центр")
    WAREHOUSE = LanguageText("Ombor", "Склад")
    CONTROLLER = LanguageText("Nazoratchi", "Контролер")
    
    # Error messages
    ERROR_OCCURRED = LanguageText("Xatolik yuz berdi", "Произошла ошибка")
    ACCESS_DENIED = LanguageText("Ruxsat berilmagan", "Доступ запрещен")
    NOT_FOUND = LanguageText("Topilmadi", "Не найдено")
    INVALID_INPUT = LanguageText("Noto'g'ri ma'lumot", "Неверные данные")
    
    # Success messages
    SUCCESS = LanguageText("Muvaffaqiyatli", "Успешно")
    SAVED = LanguageText("Saqlandi", "Сохранено")
    DELETED = LanguageText("O'chirildi", "Удалено")
    UPDATED = LanguageText("Yangilandi", "Обновлено")

def get_text(text: LanguageText, language: str) -> str:
    """Get text in specified language"""
    return text.get(language)

async def get_localized_text(text: LanguageText, user: User) -> str:
    """Get localized text for user"""
    language = await get_user_language(user)
    return text.get(language)

# Text formatting helpers
def format_status_text(status: str, language: str) -> str:
    """Format status text with emoji"""
    status_map = {
        'new': ('🆕', CommonTexts.NEW),
        'pending': ('⏳', CommonTexts.PENDING),
        'assigned': ('👨‍🔧', CommonTexts.ASSIGNED),
        'in_progress': ('🔄', CommonTexts.IN_PROGRESS),
        'completed': ('✅', CommonTexts.COMPLETED),
        'cancelled': ('❌', CommonTexts.CANCELLED)
    }
    
    if status in status_map:
        emoji, text = status_map[status]
        return f"{emoji} {text.get(language)}"
    
    return status

def format_role_text(role: str, language: str) -> str:
    """Format role text with emoji"""
    role_map = {
        'client': ('👤', CommonTexts.CLIENT),
        'technician': ('🔧', CommonTexts.TECHNICIAN),
        'manager': ('👨‍💼', CommonTexts.MANAGER),
        'admin': ('👑', CommonTexts.ADMIN),
        'call_center': ('📞', CommonTexts.CALL_CENTER),
        'warehouse': ('📦', CommonTexts.WAREHOUSE),
        'controller': ('🔍', CommonTexts.CONTROLLER)
    }
    
    if role in role_map:
        emoji, text = role_map[role]
        return f"{emoji} {text.get(language)}"
    
    return role

# Language detection helpers
def detect_language_from_text(text: str) -> str:
    """Simple language detection from text"""
    # Simple heuristic based on character frequency
    cyrillic_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    latin_chars = sum(1 for c in text if c.isalpha() and c.isascii())
    
    if cyrillic_chars > latin_chars:
        return 'ru'
    elif latin_chars > 0:
        return 'uz'
    
    return config.DEFAULT_LANGUAGE

def get_keyboard_language_text(language: str) -> dict:
    """Get keyboard text for language"""
    texts = {
        'uz': {
            'main_menu': "🏠 Asosiy menyu",
            'my_requests': "📋 Mening so'rovlarim",
            'new_request': "➕ Yangi so'rov",
            'profile': "👤 Profil",
            'settings': "⚙️ Sozlamalar",
            'help': "❓ Yordam",
            'language': "🌐 Til",
            'contact': "📞 Aloqa"
        },
        'ru': {
            'main_menu': "🏠 Главное меню",
            'my_requests': "📋 Мои заявки",
            'new_request': "➕ Новая заявка",
            'profile': "👤 Профиль",
            'settings': "⚙️ Настройки",
            'help': "❓ Помощь",
            'language': "🌐 Язык",
            'contact': "📞 Контакты"
        }
    }
    
    return texts.get(language, texts['ru'])

from typing import Union

async def get_user_lang(user: Union[User, int]) -> str:
    try:
        return await get_user_language(user)
    except Exception as e:
        logger.error(f"Error getting user language: {str(e)}")
        return config.DEFAULT_LANGUAGE