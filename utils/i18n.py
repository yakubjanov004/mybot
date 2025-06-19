import json
from pathlib import Path
from typing import Dict, Any
import os

class I18n:
    def __init__(self):
        self.locales_dir = Path(__file__).parent.parent / "locales"
        self.messages: Dict[str, Dict[str, Any]] = {}
        self.keyboards: Dict[str, Dict[str, Any]] = {}
        self.load_translations()

    def load_translations(self):
        """Barcha tillardagi tarjimalarni yuklash"""
        for lang in ["uz", "ru"]:
            # Xabarlarni yuklash
            messages_file = self.locales_dir / lang / "messages.json"
            if messages_file.exists():
                with open(messages_file, "r", encoding="utf-8") as f:
                    self.messages[lang] = json.load(f)

            # Klaviaturalarni yuklash
            keyboards_file = self.locales_dir / lang / "keyboards.json"
            if keyboards_file.exists():
                with open(keyboards_file, "r", encoding="utf-8") as f:
                    self.keyboards[lang] = json.load(f)

    def get_message(self, lang: str, key: str, **kwargs) -> str:
        """Xabarni olish"""
        try:
            # Try to get the message from the specified language
            message = self.messages[lang]
            for k in key.split('.'):
                message = message[k]
            
            if kwargs:
                message = message.format(**kwargs)
            return message
        except (KeyError, TypeError):
            # If not found in specified language, try default language (uz)
            if lang != 'uz':
                try:
                    message = self.messages['uz']
                    for k in key.split('.'):
                        message = message[k]
                    
                    if kwargs:
                        message = message.format(**kwargs)
                    return message
                except (KeyError, TypeError):
                    pass
            
            # If still not found, return a default message
            if key == 'admin.welcome':
                return "Admin paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель администратора!"
            elif key == 'admin.main_menu':
                return "Admin panel" if lang == 'uz' else "Панель администратора"
            return f"Missing translation: {key}"

    def get_keyboard(self, lang: str, keyboard_type: str) -> Dict[str, Any]:
        """Klaviaturani olish"""
        try:
            return self.keyboards[lang][keyboard_type]
        except KeyError:
            return {}

i18n = I18n()

def get_locale(language_code: str = None) -> Dict[str, Any]:
    """Get locale dictionary based on language code"""
    if not language_code or language_code not in ['uz', 'ru']:
        language_code = 'uz'
    
    # Get the absolute path to the locales directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_file = os.path.join(current_dir, 'locales', language_code, 'messages.json')
    
    try:
        with open(locale_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading locale file {locale_file}: {str(e)}")
        # Return empty dict as fallback
        return {} 