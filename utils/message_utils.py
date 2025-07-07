import re
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, User
from aiogram.utils.formatting import Text, Bold, Italic, Code, Pre, Underline
from utils.get_lang import get_user_language, LanguageText, get_text
from utils.logger import setup_module_logger

logger = setup_module_logger("message_utils")

class MessageFormatter:
    """Message formatting utilities"""
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape markdown special characters"""
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def format_user_mention(user: User) -> str:
        """Format user mention"""
        if user.username:
            return f"@{user.username}"
        else:
            full_name = f"{user.first_name}"
            if user.last_name:
                full_name += f" {user.last_name}"
            return f"[{full_name}](tg://user?id={user.id})"
    
    @staticmethod
    def format_datetime(dt: datetime, language: str = 'ru') -> str:
        """Format datetime for display"""
        if language == 'uz':
            months = [
                'yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun',
                'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr'
            ]
        else:
            months = [
                'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
            ]
        
        day = dt.day
        month = months[dt.month - 1]
        year = dt.year
        time = dt.strftime('%H:%M')
        
        return f"{day} {month} {year}, {time}"
    
    @staticmethod
    def format_duration(seconds: int, language: str = 'ru') -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            unit = "soniya" if language == 'uz' else "сек"
            return f"{seconds} {unit}"
        elif seconds < 3600:
            minutes = seconds // 60
            unit = "daqiqa" if language == 'uz' else "мин"
            return f"{minutes} {unit}"
        elif seconds < 86400:
            hours = seconds // 3600
            unit = "soat" if language == 'uz' else "ч"
            return f"{hours} {unit}"
        else:
            days = seconds // 86400
            unit = "kun" if language == 'uz' else "дн"
            return f"{days} {unit}"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """Format phone number"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Format based on length
        if len(digits) == 12 and digits.startswith('998'):
            # Uzbek number: +998 XX XXX XX XX
            return f"+{digits[:3]} {digits[3:5]} {digits[5:8]} {digits[8:10]} {digits[10:]}"
        elif len(digits) == 11 and digits.startswith('7'):
            # Russian number: +7 XXX XXX XX XX
            return f"+{digits[:1]} {digits[1:4]} {digits[4:7]} {digits[7:9]} {digits[9:]}"
        else:
            return phone
    
    @staticmethod
    def format_money(amount: float, currency: str = "UZS") -> str:
        """Format money amount"""
        if currency == "UZS":
            return f"{amount:,.0f} сум"
        elif currency == "USD":
            return f"${amount:,.2f}"
        elif currency == "RUB":
            return f"{amount:,.2f} ₽"
        else:
            return f"{amount:,.2f} {currency}"

class MessageBuilder:
    """Build formatted messages"""
    
    def __init__(self, language: str = 'ru'):
        self.language = language
        self.parts: List[str] = []
    
    def add_line(self, text: str = "") -> 'MessageBuilder':
        """Add line to message"""
        self.parts.append(text)
        return self
    
    def add_bold(self, text: str) -> 'MessageBuilder':
        """Add bold text"""
        self.parts.append(f"*{MessageFormatter.escape_markdown(text)}*")
        return self
    
    def add_italic(self, text: str) -> 'MessageBuilder':
        """Add italic text"""
        self.parts.append(f"_{MessageFormatter.escape_markdown(text)}_")
        return self
    
    def add_code(self, text: str) -> 'MessageBuilder':
        """Add code text"""
        self.parts.append(f"`{text}`")
        return self
    
    def add_field(self, label: str, value: str, bold_label: bool = True) -> 'MessageBuilder':
        """Add field with label and value"""
        if bold_label:
            self.parts.append(f"*{MessageFormatter.escape_markdown(label)}:* {MessageFormatter.escape_markdown(str(value))}")
        else:
            self.parts.append(f"{MessageFormatter.escape_markdown(label)}: {MessageFormatter.escape_markdown(str(value))}")
        return self
    
    def add_separator(self, char: str = "─", length: int = 20) -> 'MessageBuilder':
        """Add separator line"""
        self.parts.append(char * length)
        return self
    
    def add_header(self, text: str, level: int = 1) -> 'MessageBuilder':
        """Add header"""
        if level == 1:
            self.add_bold(text.upper())
        elif level == 2:
            self.add_bold(text)
        else:
            self.add_line(text)
        return self
    
    def add_list_item(self, text: str, bullet: str = "•") -> 'MessageBuilder':
        """Add list item"""
        self.parts.append(f"{bullet} {MessageFormatter.escape_markdown(text)}")
        return self
    
    def add_numbered_item(self, text: str, number: int) -> 'MessageBuilder':
        """Add numbered list item"""
        self.parts.append(f"{number}. {MessageFormatter.escape_markdown(text)}")
        return self
    
    def build(self) -> str:
        """Build final message"""
        return "\n".join(self.parts)
    
    def clear(self) -> 'MessageBuilder':
        """Clear message parts"""
        self.parts.clear()
        return self

def create_zayavka_message(zayavka: Dict, language: str = 'ru') -> str:
    """Create formatted zayavka message"""
    builder = MessageBuilder(language)
    
    if language == 'uz':
        builder.add_header("📋 ZAYAVKA MA'LUMOTLARI")
        builder.add_line()
        builder.add_field("ID", f"#{zayavka['id']}")
        builder.add_field("Holat", zayavka.get('status', 'Noma\'lum'))
        builder.add_field("Yaratilgan", MessageFormatter.format_datetime(zayavka.get('created_at', datetime.now()), language))
        
        if zayavka.get('description'):
            builder.add_line()
            builder.add_bold("Tavsif:")
            builder.add_line(zayavka['description'])
        
        if zayavka.get('technician_name'):
            builder.add_line()
            builder.add_field("Texnik", zayavka['technician_name'])
        
        if zayavka.get('address'):
            builder.add_field("Manzil", zayavka['address'])
        
        if zayavka.get('phone'):
            builder.add_field("Telefon", MessageFormatter.format_phone_number(zayavka['phone']))
    
    else:
        builder.add_header("📋 ИНФОРМАЦИЯ О ЗАЯВКЕ")
        builder.add_line()
        builder.add_field("ID", f"#{zayavka['id']}")
        builder.add_field("Статус", zayavka.get('status', 'Неизвестно'))
        builder.add_field("Создана", MessageFormatter.format_datetime(zayavka.get('created_at', datetime.now()), language))
        
        if zayavka.get('description'):
            builder.add_line()
            builder.add_bold("Описание:")
            builder.add_line(zayavka['description'])
        
        if zayavka.get('technician_name'):
            builder.add_line()
            builder.add_field("Техник", zayavka['technician_name'])
        
        if zayavka.get('address'):
            builder.add_field("Адрес", zayavka['address'])
        
        if zayavka.get('phone'):
            builder.add_field("Телефон", MessageFormatter.format_phone_number(zayavka['phone']))
    
    return builder.build()

def create_user_profile_message(user_data: Dict, language: str = 'ru') -> str:
    """Create formatted user profile message"""
    builder = MessageBuilder(language)
    
    if language == 'uz':
        builder.add_header("👤 FOYDALANUVCHI PROFILI")
        builder.add_line()
        builder.add_field("ID", user_data.get('id', 'N/A'))
        builder.add_field("Ism", user_data.get('full_name', 'Noma\'lum'))
        builder.add_field("Telefon", MessageFormatter.format_phone_number(user_data.get('phone', '')))
        builder.add_field("Rol", user_data.get('role', 'mijoz'))
        builder.add_field("Til", user_data.get('language', 'uz'))
        
        if user_data.get('created_at'):
            builder.add_field("Ro'yxatdan o'tgan", 
                            MessageFormatter.format_datetime(user_data['created_at'], language))
    
    else:
        builder.add_header("👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ")
        builder.add_line()
        builder.add_field("ID", user_data.get('id', 'N/A'))
        builder.add_field("Имя", user_data.get('full_name', 'Неизвестно'))
        builder.add_field("Телефон", MessageFormatter.format_phone_number(user_data.get('phone', '')))
        builder.add_field("Роль", user_data.get('role', 'клиент'))
        builder.add_field("Язык", user_data.get('language', 'ru'))
        
        if user_data.get('created_at'):
            builder.add_field("Зарегистрирован", 
                            MessageFormatter.format_datetime(user_data['created_at'], language))
    
    return builder.build()

def create_statistics_message(stats: Dict, language: str = 'ru') -> str:
    """Create formatted statistics message"""
    builder = MessageBuilder(language)
    
    if language == 'uz':
        builder.add_header("📊 STATISTIKA")
        builder.add_line()
        
        if 'total_zayavkas' in stats:
            builder.add_field("Jami zayavkalar", stats['total_zayavkas'])
        
        if 'completed_zayavkas' in stats:
            builder.add_field("Bajarilgan", stats['completed_zayavkas'])
        
        if 'pending_zayavkas' in stats:
            builder.add_field("Kutilayotgan", stats['pending_zayavkas'])
        
        if 'total_users' in stats:
            builder.add_line()
            builder.add_field("Jami foydalanuvchilar", stats['total_users'])
        
        if 'active_technicians' in stats:
            builder.add_field("Faol texniklar", stats['active_technicians'])
    
    else:
        builder.add_header("📊 СТАТИСТИКА")
        builder.add_line()
        
        if 'total_zayavkas' in stats:
            builder.add_field("Всего заявок", stats['total_zayavkas'])
        
        if 'completed_zayavkas' in stats:
            builder.add_field("Выполнено", stats['completed_zayavkas'])
        
        if 'pending_zayavkas' in stats:
            builder.add_field("В ожидании", stats['pending_zayavkas'])
        
        if 'total_users' in stats:
            builder.add_line()
            builder.add_field("Всего пользователей", stats['total_users'])
        
        if 'active_technicians' in stats:
            builder.add_field("Активных техников", stats['active_technicians'])
    
    return builder.build()

def create_error_message(error_type: str, language: str = 'ru') -> str:
    """Create formatted error message"""
    error_messages = {
        'access_denied': LanguageText("Ruxsat berilmagan", "Доступ запрещен"),
        'not_found': LanguageText("Topilmadi", "Не найдено"),
        'invalid_input': LanguageText("Noto'g'ri ma'lumot", "Неверные данные"),
        'server_error': LanguageText("Server xatosi", "Ошибка сервера"),
        'network_error': LanguageText("Tarmoq xatosi", "Ошибка сети"),
        'unknown_error': LanguageText("Noma'lum xato", "Неизвестная ошибка")
    }
    
    error_text = error_messages.get(error_type, error_messages['unknown_error'])
    return f"❌ {get_text(error_text, language)}"

def create_success_message(action: str, language: str = 'ru') -> str:
    """Create formatted success message"""
    success_messages = {
        'created': LanguageText("Muvaffaqiyatli yaratildi", "Успешно создано"),
        'updated': LanguageText("Muvaffaqiyatli yangilandi", "Успешно обновлено"),
        'deleted': LanguageText("Muvaffaqiyatli o'chirildi", "Успешно удалено"),
        'saved': LanguageText("Muvaffaqiyatli saqlandi", "Успешно сохранено"),
        'sent': LanguageText("Muvaffaqiyatli yuborildi", "Успешно отправлено"),
        'completed': LanguageText("Muvaffaqiyatli bajarildi", "Успешно выполнено")
    }
    
    success_text = success_messages.get(action, success_messages['completed'])
    return f"✅ {get_text(success_text, language)}"

async def send_formatted_message(message_or_callback: Union[Message, CallbackQuery], 
                               text: str, 
                               reply_markup: Optional[InlineKeyboardMarkup] = None,
                               parse_mode: str = "MarkdownV2") -> Message:
    """Send formatted message with error handling"""
    try:
        if isinstance(message_or_callback, CallbackQuery):
            if message_or_callback.message:
                return await message_or_callback.message.edit_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                return await message_or_callback.bot.send_message(
                    chat_id=message_or_callback.from_user.id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        else:
            return await message_or_callback.answer(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    
    except Exception as e:
        logger.error(f"Error sending formatted message: {str(e)}")
        # Fallback without formatting
        try:
            if isinstance(message_or_callback, CallbackQuery):
                if message_or_callback.message:
                    return await message_or_callback.message.edit_text(
                        text=text,
                        reply_markup=reply_markup
                    )
                else:
                    return await message_or_callback.bot.send_message(
                        chat_id=message_or_callback.from_user.id,
                        text=text,
                        reply_markup=reply_markup
                    )
            else:
                return await message_or_callback.answer(
                    text=text,
                    reply_markup=reply_markup
                )
        except Exception as e2:
            logger.error(f"Error sending fallback message: {str(e2)}")
            raise

def validate_message_length(text: str, max_length: int = 4096) -> bool:
    """Validate message length"""
    return len(text.encode('utf-8')) <= max_length

def split_long_message(text: str, max_length: int = 4096) -> List[str]:
    """Split long message into chunks"""
    if len(text.encode('utf-8')) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len((current_chunk + '\n' + line).encode('utf-8')) > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                # Single line is too long, split by words
                words = line.split(' ')
                for word in words:
                    if len((current_chunk + ' ' + word).encode('utf-8')) > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = word
                        else:
                            # Single word is too long, truncate
                            chunks.append(word[:max_length])
                    else:
                        current_chunk += ' ' + word if current_chunk else word
        else:
            current_chunk += '\n' + line if current_chunk else line
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# Template system
class MessageTemplate:
    """Message template system"""
    
    def __init__(self, template: str):
        self.template = template
    
    def render(self, **kwargs) -> str:
        """Render template with variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing template variable: {str(e)}")
            return self.template
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return self.template

# Common templates
TEMPLATES = {
    'zayavka_created': {
        'uz': MessageTemplate("✅ Zayavka #{id} muvaffaqiyatli yaratildi!\n\nHolat: {status}\nVaqt: {created_at}"),
        'ru': MessageTemplate("✅ Заявка #{id} успешно создана!\n\nСтатус: {status}\nВремя: {created_at}")
    },
    'zayavka_assigned': {
        'uz': MessageTemplate("👨‍🔧 Zayavka #{id} texnikka tayinlandi\n\nTexnik: {technician_name}\nVaqt: {assigned_at}"),
        'ru': MessageTemplate("👨‍🔧 Заявка #{id} назначена технику\n\nТехник: {technician_name}\nВремя: {assigned_at}")
    },
    'task_completed': {
        'uz': MessageTemplate("✅ Vazifa #{id} bajarildi!\n\nTexnik: {technician_name}\nVaqt: {completed_at}"),
        'ru': MessageTemplate("✅ Задача #{id} выполнена!\n\nТехник: {technician_name}\nВремя: {completed_at}")
    }
}

def render_template(template_name: str, language: str, **kwargs) -> str:
    """Render message template"""
    if template_name in TEMPLATES and language in TEMPLATES[template_name]:
        return TEMPLATES[template_name][language].render(**kwargs)
    
    logger.warning(f"Template not found: {template_name} ({language})")
    return f"Template {template_name} not found"

# Message queue for bulk operations
class MessageQueue:
    """Queue for bulk message operations"""
    
    def __init__(self):
        self.queue: List[Dict] = []
    
    def add_message(self, chat_id: int, text: str, **kwargs):
        """Add message to queue"""
        self.queue.append({
            'chat_id': chat_id,
            'text': text,
            **kwargs
        })
    
    async def send_all(self, bot, delay: float = 0.1) -> List[Message]:
        """Send all queued messages"""
        sent_messages = []
        
        for msg_data in self.queue:
            try:
                message = await bot.send_message(**msg_data)
                sent_messages.append(message)
                
                if delay > 0:
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error sending queued message: {str(e)}")
        
        self.queue.clear()
        return sent_messages
    
    def clear(self):
        """Clear message queue"""
        self.queue.clear()
    
    def size(self) -> int:
        """Get queue size"""
        return len(self.queue)

def get_main_menu_keyboard(lang: str, role: str):
    """Return the main menu keyboard for the given role and language."""
    if role == "admin":
        from keyboards.admin_buttons import get_admin_main_menu
        return get_admin_main_menu(lang)
    elif role == "manager":
        from keyboards.manager_buttons import get_manager_main_keyboard
        return get_manager_main_keyboard(lang)
    elif role == "technician":
        from keyboards.technician_buttons import get_technician_main_menu_keyboard
        return get_technician_main_menu_keyboard(lang)
    elif role == "call_center":
        from keyboards.call_center_buttons import call_center_main_menu_reply
        return call_center_main_menu_reply(lang)
    elif role == "warehouse":
        from keyboards.warehouse_buttons import warehouse_main_menu
        return warehouse_main_menu(lang)
    else:
        from keyboards.client_buttons import get_main_menu_keyboard
        return get_main_menu_keyboard(lang)
