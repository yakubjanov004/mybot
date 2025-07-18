"""
Localization support for staff application creation feature.

This module provides comprehensive language support for all UI elements,
error messages, and notifications related to staff application creation.
"""

from typing import Dict, Any, Optional, Union
from enum import Enum
from utils.get_lang import LanguageText, get_text


class StaffApplicationTexts:
    """Localized texts for staff application creation"""
    
    # Main menu buttons
    CREATE_CONNECTION_REQUEST = LanguageText(
        "🔌 Ulanish arizasi yaratish",
        "🔌 Создать заявку на подключение"
    )
    
    CREATE_TECHNICAL_SERVICE = LanguageText(
        "🔧 Texnik xizmat yaratish", 
        "🔧 Создать техническую заявку"
    )
    
    # Client selection texts
    SELECT_CLIENT = LanguageText(
        "Mijozni tanlang",
        "Выберите клиента"
    )
    
    SEARCH_CLIENT = LanguageText(
        "🔍 Mijoz qidirish",
        "🔍 Поиск клиента"
    )
    
    SEARCH_BY_PHONE = LanguageText(
        "📞 Telefon raqami bo'yicha",
        "📞 По номеру телефона"
    )
    
    SEARCH_BY_NAME = LanguageText(
        "👤 Ism bo'yicha",
        "👤 По имени"
    )
    
    SEARCH_BY_ID = LanguageText(
        "🆔 ID bo'yicha",
        "🆔 По ID"
    )
    
    CREATE_NEW_CLIENT = LanguageText(
        "➕ Yangi mijoz yaratish",
        "➕ Создать нового клиента"
    )
    
    CLIENT_NOT_FOUND = LanguageText(
        "Mijoz topilmadi",
        "Клиент не найден"
    )
    
    MULTIPLE_CLIENTS_FOUND = LanguageText(
        "Bir nechta mijoz topildi",
        "Найдено несколько клиентов"
    )
    
    # Application type selection
    SELECT_APPLICATION_TYPE = LanguageText(
        "Ariza turini tanlang",
        "Выберите тип заявки"
    )
    
    CONNECTION_REQUEST = LanguageText(
        "🔌 Ulanish uchun ariza",
        "🔌 Заявка на подключение"
    )
    
    TECHNICAL_SERVICE = LanguageText(
        "🔧 Texnik xizmat",
        "🔧 Техническое обслуживание"
    )
    
    # Form field labels
    CLIENT_PHONE = LanguageText(
        "Mijoz telefon raqami",
        "Номер телефона клиента"
    )
    
    CLIENT_NAME = LanguageText(
        "Mijoz ismi",
        "Имя клиента"
    )
    
    CLIENT_ADDRESS = LanguageText(
        "Mijoz manzili",
        "Адрес клиента"
    )
    
    SERVICE_DESCRIPTION = LanguageText(
        "Xizmat tavsifi",
        "Описание услуги"
    )
    
    SERVICE_LOCATION = LanguageText(
        "Xizmat joylashuvi",
        "Местоположение услуги"
    )
    
    PRIORITY_LEVEL = LanguageText(
        "Muhimlik darajasi",
        "Уровень приоритета"
    )
    
    ADDITIONAL_NOTES = LanguageText(
        "Qo'shimcha izohlar",
        "Дополнительные заметки"
    )
    
    # Priority levels
    PRIORITY_LOW = LanguageText("Past", "Низкий")
    PRIORITY_MEDIUM = LanguageText("O'rta", "Средний")
    PRIORITY_HIGH = LanguageText("Yuqori", "Высокий")
    PRIORITY_URGENT = LanguageText("Shoshilinch", "Срочный")
    
    # Connection types
    CONNECTION_FIBER = LanguageText("Optik tola", "Оптоволокно")
    CONNECTION_CABLE = LanguageText("Kabel", "Кабель")
    CONNECTION_WIRELESS = LanguageText("Simsiz", "Беспроводной")
    CONNECTION_SATELLITE = LanguageText("Sun'iy yo'ldosh", "Спутниковый")
    
    # Technical service types
    TECH_REPAIR = LanguageText("Ta'mirlash", "Ремонт")
    TECH_MAINTENANCE = LanguageText("Profilaktika", "Профилактика")
    TECH_INSTALLATION = LanguageText("O'rnatish", "Установка")
    TECH_CONFIGURATION = LanguageText("Sozlash", "Настройка")
    
    # Confirmation texts
    CONFIRM_APPLICATION = LanguageText(
        "Arizani tasdiqlang",
        "Подтвердите заявку"
    )
    
    APPLICATION_PREVIEW = LanguageText(
        "Ariza ko'rib chiqish",
        "Предварительный просмотр заявки"
    )
    
    EDIT_APPLICATION = LanguageText(
        "✏️ Tahrirlash",
        "✏️ Редактировать"
    )
    
    SUBMIT_APPLICATION = LanguageText(
        "✅ Yuborish",
        "✅ Отправить"
    )
    
    CANCEL_APPLICATION = LanguageText(
        "❌ Bekor qilish",
        "❌ Отменить"
    )
    
    # Success messages
    APPLICATION_CREATED_SUCCESS = LanguageText(
        "✅ Ariza muvaffaqiyatli yaratildi!",
        "✅ Заявка успешно создана!"
    )
    
    CLIENT_NOTIFIED = LanguageText(
        "📱 Mijozga xabar yuborildi",
        "📱 Клиент уведомлен"
    )
    
    WORKFLOW_STARTED = LanguageText(
        "🔄 Ish jarayoni boshlandi",
        "🔄 Рабочий процесс запущен"
    )
    
    # Error messages
    PERMISSION_DENIED = LanguageText(
        "❌ Sizda bu amalni bajarish huquqi yo'q",
        "❌ У вас нет разрешения на это действие"
    )
    
    CLIENT_SELECTION_ERROR = LanguageText(
        "❌ Mijozni tanlashda xatolik",
        "❌ Ошибка при выборе клиента"
    )
    
    APPLICATION_CREATION_ERROR = LanguageText(
        "❌ Ariza yaratishda xatolik",
        "❌ Ошибка при создании заявки"
    )
    
    FORM_VALIDATION_ERROR = LanguageText(
        "❌ Forma ma'lumotlarida xatolik",
        "❌ Ошибка в данных формы"
    )
    
    NETWORK_ERROR = LanguageText(
        "❌ Tarmoq xatoligi",
        "❌ Сетевая ошибка"
    )
    
    DAILY_LIMIT_EXCEEDED = LanguageText(
        "❌ Kunlik limit oshib ketdi",
        "❌ Превышен дневной лимит"
    )
    
    # Role-specific messages
    MANAGER_PRIVILEGES = LanguageText(
        "👨‍💼 Menejer sifatida siz barcha turdagi arizalarni yarata olasiz",
        "👨‍💼 Как менеджер, вы можете создавать все типы заявок"
    )
    
    JUNIOR_MANAGER_LIMITATION = LanguageText(
        "👨‍💼 Kichik menejer sifatida siz faqat ulanish arizalarini yarata olasiz",
        "👨‍💼 Как младший менеджер, вы можете создавать только заявки на подключение"
    )
    
    CONTROLLER_PRIVILEGES = LanguageText(
        "🔍 Nazoratchi sifatida sizda kengaytirilgan huquqlar mavjud",
        "🔍 Как контролер, у вас есть расширенные права"
    )
    
    CALL_CENTER_NOTE = LanguageText(
        "📞 Qo'ng'iroq markazi operatori sifatida mijozlar bilan bog'lanishni unutmang",
        "📞 Как оператор колл-центра, не забудьте связаться с клиентами"
    )
    
    # Notification messages
    CLIENT_NOTIFICATION_TITLE = LanguageText(
        "🔔 Yangi ariza yaratildi",
        "🔔 Создана новая заявка"
    )
    
    CLIENT_NOTIFICATION_BODY = LanguageText(
        "Sizning nomingizdan yangi ariza yaratildi. Ariza ID: {application_id}",
        "От вашего имени создана новая заявка. ID заявки: {application_id}"
    )
    
    STAFF_CONFIRMATION_TITLE = LanguageText(
        "✅ Ariza tasdiqlandi",
        "✅ Заявка подтверждена"
    )
    
    STAFF_CONFIRMATION_BODY = LanguageText(
        "Siz yaratgan ariza muvaffaqiyatli yuborildi. Ariza ID: {application_id}",
        "Созданная вами заявка успешно отправлена. ID заявки: {application_id}"
    )
    
    # Input prompts
    ENTER_PHONE_NUMBER = LanguageText(
        "📞 Telefon raqamini kiriting:",
        "📞 Введите номер телефона:"
    )
    
    ENTER_CLIENT_NAME = LanguageText(
        "👤 Mijoz ismini kiriting:",
        "👤 Введите имя клиента:"
    )
    
    ENTER_CLIENT_ADDRESS = LanguageText(
        "🏠 Mijoz manzilini kiriting:",
        "🏠 Введите адрес клиента:"
    )
    
    ENTER_SERVICE_DESCRIPTION = LanguageText(
        "📝 Xizmat tavsifini kiriting:",
        "📝 Введите описание услуги:"
    )
    
    ENTER_SERVICE_LOCATION = LanguageText(
        "📍 Xizmat joylashuvini kiriting:",
        "📍 Введите местоположение услуги:"
    )
    
    ENTER_ADDITIONAL_NOTES = LanguageText(
        "📋 Qo'shimcha izohlar (ixtiyoriy):",
        "📋 Дополнительные заметки (необязательно):"
    )
    
    # Validation messages
    PHONE_REQUIRED = LanguageText(
        "Telefon raqami kiritilishi shart",
        "Номер телефона обязателен"
    )
    
    INVALID_PHONE_FORMAT = LanguageText(
        "Noto'g'ri telefon raqami formati",
        "Неверный формат номера телефона"
    )
    
    NAME_REQUIRED = LanguageText(
        "Mijoz ismi kiritilishi shart",
        "Имя клиента обязательно"
    )
    
    NAME_TOO_SHORT = LanguageText(
        "Ism juda qisqa (kamida 2 ta belgi)",
        "Имя слишком короткое (минимум 2 символа)"
    )
    
    ADDRESS_REQUIRED = LanguageText(
        "Manzil kiritilishi shart",
        "Адрес обязателен"
    )
    
    DESCRIPTION_REQUIRED = LanguageText(
        "Xizmat tavsifi kiritilishi shart",
        "Описание услуги обязательно"
    )
    
    DESCRIPTION_TOO_SHORT = LanguageText(
        "Tavsif juda qisqa (kamida 10 ta belgi)",
        "Описание слишком короткое (минимум 10 символов)"
    )
    
    LOCATION_REQUIRED = LanguageText(
        "Xizmat joylashuvi kiritilishi shart",
        "Местоположение услуги обязательно"
    )
    
    # Button texts
    BACK = LanguageText("◀️ Orqaga", "◀️ Назад")
    NEXT = LanguageText("Keyingi ▶️", "Далее ▶️")
    SKIP = LanguageText("O'tkazib yuborish", "Пропустить")
    RETRY = LanguageText("🔄 Qayta urinish", "🔄 Повторить")
    
    # Status texts
    SEARCHING = LanguageText("🔍 Qidirilmoqda...", "🔍 Поиск...")
    CREATING = LanguageText("⏳ Yaratilmoqda...", "⏳ Создание...")
    VALIDATING = LanguageText("✅ Tekshirilmoqda...", "✅ Проверка...")
    SUBMITTING = LanguageText("📤 Yuborilmoqda...", "📤 Отправка...")
    
    # Help texts
    PHONE_FORMAT_HELP = LanguageText(
        "Masalan: +998901234567 yoki 901234567",
        "Например: +998901234567 или 901234567"
    )
    
    NAME_FORMAT_HELP = LanguageText(
        "Ism va familiyani to'liq kiriting",
        "Введите полное имя и фамилию"
    )
    
    DESCRIPTION_HELP = LanguageText(
        "Muammo yoki xizmat haqida batafsil yozing",
        "Подробно опишите проблему или услугу"
    )


class StaffApplicationErrorMessages:
    """Localized error messages for staff application creation"""
    
    # Permission errors
    NO_CONNECTION_PERMISSION = LanguageText(
        "Sizda ulanish arizalarini yaratish huquqi yo'q",
        "У вас нет разрешения на создание заявок на подключение"
    )
    
    NO_TECHNICAL_PERMISSION = LanguageText(
        "Sizda texnik xizmat arizalarini yaratish huquqi yo'q",
        "У вас нет разрешения на создание заявок на техническое обслуживание"
    )
    
    NO_CLIENT_SELECTION_PERMISSION = LanguageText(
        "Sizda mijozlarni tanlash huquqi yo'q",
        "У вас нет разрешения на выбор клиентов"
    )
    
    NO_CLIENT_CREATION_PERMISSION = LanguageText(
        "Sizda yangi mijoz yaratish huquqi yo'q",
        "У вас нет разрешения на создание новых клиентов"
    )
    
    DAILY_LIMIT_EXCEEDED = LanguageText(
        "Bugun yaratish mumkin bo'lgan arizalar soni tugadi",
        "Превышен дневной лимит создания заявок"
    )
    
    # Validation errors
    INVALID_CLIENT_DATA = LanguageText(
        "Mijoz ma'lumotlari noto'g'ri",
        "Неверные данные клиента"
    )
    
    INVALID_APPLICATION_DATA = LanguageText(
        "Ariza ma'lumotlari noto'g'ri",
        "Неверные данные заявки"
    )
    
    CLIENT_ALREADY_EXISTS = LanguageText(
        "Bunday mijoz allaqachon mavjud",
        "Такой клиент уже существует"
    )
    
    DUPLICATE_APPLICATION = LanguageText(
        "Bunday ariza allaqachon mavjud",
        "Такая заявка уже существует"
    )
    
    # System errors
    DATABASE_ERROR = LanguageText(
        "Ma'lumotlar bazasi xatoligi",
        "Ошибка базы данных"
    )
    
    WORKFLOW_ERROR = LanguageText(
        "Ish jarayonini boshlashda xatolik",
        "Ошибка запуска рабочего процесса"
    )
    
    NOTIFICATION_ERROR = LanguageText(
        "Xabar yuborishda xatolik",
        "Ошибка отправки уведомления"
    )
    
    AUDIT_LOG_ERROR = LanguageText(
        "Audit yozuvini saqlashda xatolik",
        "Ошибка сохранения записи аудита"
    )
    
    # Network errors
    CONNECTION_TIMEOUT = LanguageText(
        "Ulanish vaqti tugadi",
        "Время подключения истекло"
    )
    
    SERVER_UNAVAILABLE = LanguageText(
        "Server mavjud emas",
        "Сервер недоступен"
    )
    
    # Input validation errors
    EMPTY_FIELD = LanguageText(
        "Bu maydon bo'sh bo'lishi mumkin emas",
        "Это поле не может быть пустым"
    )
    
    FIELD_TOO_LONG = LanguageText(
        "Bu maydon juda uzun",
        "Это поле слишком длинное"
    )
    
    FIELD_TOO_SHORT = LanguageText(
        "Bu maydon juda qisqa",
        "Это поле слишком короткое"
    )
    
    INVALID_FORMAT = LanguageText(
        "Noto'g'ri format",
        "Неверный формат"
    )
    
    INVALID_CHARACTERS = LanguageText(
        "Noto'g'ri belgilar",
        "Недопустимые символы"
    )


def get_staff_application_text(text_key: str, language: str = 'uz') -> str:
    """
    Get localized text for staff application creation.
    
    Args:
        text_key: Key of the text (attribute name from StaffApplicationTexts)
        language: Language code ('uz' or 'ru')
        
    Returns:
        Localized text string
    """
    if hasattr(StaffApplicationTexts, text_key):
        text_obj = getattr(StaffApplicationTexts, text_key)
        if isinstance(text_obj, LanguageText):
            return get_text(text_obj, language)
    
    return text_key


def get_staff_application_error(error_key: str, language: str = 'uz') -> str:
    """
    Get localized error message for staff application creation.
    
    Args:
        error_key: Key of the error message
        language: Language code ('uz' or 'ru')
        
    Returns:
        Localized error message
    """
    if hasattr(StaffApplicationErrorMessages, error_key):
        error_obj = getattr(StaffApplicationErrorMessages, error_key)
        if isinstance(error_obj, LanguageText):
            return get_text(error_obj, language)
    
    return error_key


def format_application_summary(application_data: Dict[str, Any], language: str = 'uz') -> str:
    """
    Format application summary with localized labels.
    
    Args:
        application_data: Application data dictionary
        language: Language code ('uz' or 'ru')
        
    Returns:
        Formatted application summary
    """
    summary_lines = []
    
    # Application type
    app_type = application_data.get('application_type', '')
    if app_type == 'connection':
        type_text = get_text(StaffApplicationTexts.CONNECTION_REQUEST, language)
    elif app_type == 'technical':
        type_text = get_text(StaffApplicationTexts.TECHNICAL_SERVICE, language)
    else:
        type_text = app_type
    
    summary_lines.append(f"📋 {type_text}")
    
    # Client information
    client_name = application_data.get('client_name', '')
    if client_name:
        client_label = get_text(StaffApplicationTexts.CLIENT_NAME, language)
        summary_lines.append(f"👤 {client_label}: {client_name}")
    
    client_phone = application_data.get('client_phone', '')
    if client_phone:
        phone_label = get_text(StaffApplicationTexts.CLIENT_PHONE, language)
        summary_lines.append(f"📞 {phone_label}: {client_phone}")
    
    # Service details
    description = application_data.get('description', '')
    if description:
        desc_label = get_text(StaffApplicationTexts.SERVICE_DESCRIPTION, language)
        summary_lines.append(f"📝 {desc_label}: {description[:100]}...")
    
    location = application_data.get('location', '')
    if location:
        location_label = get_text(StaffApplicationTexts.SERVICE_LOCATION, language)
        summary_lines.append(f"📍 {location_label}: {location}")
    
    # Priority
    priority = application_data.get('priority', '')
    if priority:
        priority_label = get_text(StaffApplicationTexts.PRIORITY_LEVEL, language)
        priority_text = get_priority_text(priority, language)
        summary_lines.append(f"⚡ {priority_label}: {priority_text}")
    
    return '\n'.join(summary_lines)


def get_priority_text(priority: str, language: str = 'uz') -> str:
    """Get localized priority text"""
    priority_map = {
        'low': StaffApplicationTexts.PRIORITY_LOW,
        'medium': StaffApplicationTexts.PRIORITY_MEDIUM,
        'high': StaffApplicationTexts.PRIORITY_HIGH,
        'urgent': StaffApplicationTexts.PRIORITY_URGENT
    }
    
    if priority in priority_map:
        return get_text(priority_map[priority], language)
    
    return priority


def get_connection_type_text(connection_type: str, language: str = 'uz') -> str:
    """Get localized connection type text"""
    type_map = {
        'fiber': StaffApplicationTexts.CONNECTION_FIBER,
        'cable': StaffApplicationTexts.CONNECTION_CABLE,
        'wireless': StaffApplicationTexts.CONNECTION_WIRELESS,
        'satellite': StaffApplicationTexts.CONNECTION_SATELLITE
    }
    
    if connection_type in type_map:
        return get_text(type_map[connection_type], language)
    
    return connection_type


def get_technical_service_type_text(service_type: str, language: str = 'uz') -> str:
    """Get localized technical service type text"""
    type_map = {
        'repair': StaffApplicationTexts.TECH_REPAIR,
        'maintenance': StaffApplicationTexts.TECH_MAINTENANCE,
        'installation': StaffApplicationTexts.TECH_INSTALLATION,
        'configuration': StaffApplicationTexts.TECH_CONFIGURATION
    }
    
    if service_type in type_map:
        return get_text(type_map[service_type], language)
    
    return service_type


def get_role_specific_message(role: str, language: str = 'uz') -> Optional[str]:
    """Get role-specific message for staff application creation"""
    role_messages = {
        'manager': StaffApplicationTexts.MANAGER_PRIVILEGES,
        'junior_manager': StaffApplicationTexts.JUNIOR_MANAGER_LIMITATION,
        'controller': StaffApplicationTexts.CONTROLLER_PRIVILEGES,
        'call_center': StaffApplicationTexts.CALL_CENTER_NOTE
    }
    
    if role in role_messages:
        return get_text(role_messages[role], language)
    
    return None


def create_localized_keyboard_text(base_text: str, language: str = 'uz') -> str:
    """
    Create localized keyboard button text.
    
    Args:
        base_text: Base text key or direct text
        language: Language code
        
    Returns:
        Localized button text
    """
    # Try to get from StaffApplicationTexts first
    text = get_staff_application_text(base_text, language)
    if text != base_text:
        return text
    
    # If not found, return the base text
    return base_text


def validate_language_consistency(texts: Dict[str, Any], language: str = 'uz') -> bool:
    """
    Validate that all texts are consistently localized.
    
    Args:
        texts: Dictionary of texts to validate
        language: Target language
        
    Returns:
        True if all texts are properly localized
    """
    for key, value in texts.items():
        if isinstance(value, str):
            # Check if text contains mixed languages (basic heuristic)
            if language == 'uz' and any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in value):
                return False  # Uzbek text shouldn't contain Cyrillic
            elif language == 'ru' and not any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in value):
                # Russian text should contain some Cyrillic (unless it's symbols/numbers only)
                if any(c.isalpha() for c in value):
                    return False
    
    return True


# Export commonly used text keys for convenience
class TextKeys:
    """Common text keys for staff application creation"""
    CREATE_CONNECTION_REQUEST = 'CREATE_CONNECTION_REQUEST'
    CREATE_TECHNICAL_SERVICE = 'CREATE_TECHNICAL_SERVICE'
    SELECT_CLIENT = 'SELECT_CLIENT'
    SEARCH_CLIENT = 'SEARCH_CLIENT'
    APPLICATION_CREATED_SUCCESS = 'APPLICATION_CREATED_SUCCESS'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    FORM_VALIDATION_ERROR = 'FORM_VALIDATION_ERROR'


class ErrorKeys:
    """Common error keys for staff application creation"""
    NO_CONNECTION_PERMISSION = 'NO_CONNECTION_PERMISSION'
    NO_TECHNICAL_PERMISSION = 'NO_TECHNICAL_PERMISSION'
    INVALID_CLIENT_DATA = 'INVALID_CLIENT_DATA'
    DATABASE_ERROR = 'DATABASE_ERROR'
    WORKFLOW_ERROR = 'WORKFLOW_ERROR'