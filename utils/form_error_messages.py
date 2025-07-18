"""
Localized error messages for staff form validation.

This module provides consistent error messaging across all roles
in both Uzbek and Russian languages.
"""

from typing import Dict, Any, Optional
from enum import Enum
from utils.staff_application_localization import get_staff_application_error, StaffApplicationErrorMessages


class MessageType(Enum):
    """Types of validation messages"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class FormErrorMessages:
    """Centralized error message management with localization"""
    
    # Error message templates in multiple languages
    MESSAGES = {
        # Client data validation messages
        'required_field': {
            'uz': "'{field}' maydoni to'ldirilishi shart",
            'ru': "Поле '{field}' обязательно для заполнения",
            'en': "Field '{field}' is required"
        },
        'invalid_uzbek_phone': {
            'uz': "Noto'g'ri O'zbekiston telefon raqami formati",
            'ru': "Неверный формат узбекского номера телефона",
            'en': "Invalid Uzbek phone number format"
        },
        'phone_validation_error': {
            'uz': "Telefon raqamini tekshirishda xatolik",
            'ru': "Ошибка проверки номера телефона",
            'en': "Phone number validation failed"
        },
        'name_too_short': {
            'uz': "Ism kamida 2 ta belgidan iborat bo'lishi kerak",
            'ru': "Имя должно содержать не менее 2 символов",
            'en': "Name must be at least 2 characters long"
        },
        'name_too_long': {
            'uz': "Ism 100 ta belgidan oshmasligi kerak",
            'ru': "Имя не должно превышать 100 символов",
            'en': "Name must be no more than 100 characters long"
        },
        'invalid_name_characters': {
            'uz': "Ismda noto'g'ri belgilar mavjud",
            'ru': "Имя содержит недопустимые символы",
            'en': "Name contains invalid characters"
        },
        'name_single_word': {
            'uz': "Ism va familiyani to'liq kiriting",
            'ru': "Рекомендуется указать имя и фамилию",
            'en': "Consider providing both first and last name"
        },
        'name_too_many_parts': {
            'uz': "Ismda juda ko'p qismlar mavjud",
            'ru': "В имени слишком много частей",
            'en': "Name has too many parts"
        },
        'name_validation_error': {
            'uz': "Ismni tekshirishda xatolik",
            'ru': "Ошибка проверки имени",
            'en': "Name validation failed"
        },
        'address_too_short': {
            'uz': "Manzil kamida 5 ta belgidan iborat bo'lishi kerak",
            'ru': "Адрес должен содержать не менее 5 символов",
            'en': "Address must be at least 5 characters long"
        },
        'address_too_long': {
            'uz': "Manzil 500 ta belgidan oshmasligi kerak",
            'ru': "Адрес не должен превышать 500 символов",
            'en': "Address must be no more than 500 characters long"
        },
        'address_incomplete': {
            'uz': "Manzil to'liq emas",
            'ru': "Адрес кажется неполным",
            'en': "Address appears to be incomplete"
        },
        'address_validation_error': {
            'uz': "Manzilni tekshirishda xatolik",
            'ru': "Ошибка проверки адреса",
            'en': "Address validation failed"
        },
        'email_validation_error': {
            'uz': "Elektron pochtani tekshirishda xatolik",
            'ru': "Ошибка проверки электронной почты",
            'en': "Email validation failed"
        },
        'additional_info_too_long': {
            'uz': "Qo'shimcha ma'lumot 1000 ta belgidan oshmasligi kerak",
            'ru': "Дополнительная информация не должна превышать 1000 символов",
            'en': "Additional information must be no more than 1000 characters long"
        },
        'additional_info_validation_error': {
            'uz': "Qo'shimcha ma'lumotni tekshirishda xatolik",
            'ru': "Ошибка проверки дополнительной информации",
            'en': "Additional information validation failed"
        },
        
        # Application data validation messages
        'description_too_short': {
            'uz': "Tavsif kamida 10 ta belgidan iborat bo'lishi kerak",
            'ru': "Описание должно содержать не менее 10 символов",
            'en': "Description must be at least 10 characters long"
        },
        'description_too_long': {
            'uz': "Tavsif 2000 ta belgidan oshmasligi kerak",
            'ru': "Описание не должно превышать 2000 символов",
            'en': "Description must be no more than 2000 characters long"
        },
        'description_too_brief': {
            'uz': "Tavsifda ko'proq tafsilot berilishi kerak",
            'ru': "Описание должно содержать больше деталей",
            'en': "Description should provide more details"
        },
        'description_validation_error': {
            'uz': "Tavsifni tekshirishda xatolik",
            'ru': "Ошибка проверки описания",
            'en': "Description validation failed"
        },
        'location_too_short': {
            'uz': "Joylashuv kamida 5 ta belgidan iborat bo'lishi kerak",
            'ru': "Местоположение должно содержать не менее 5 символов",
            'en': "Location must be at least 5 characters long"
        },
        'location_too_long': {
            'uz': "Joylashuv 500 ta belgidan oshmasligi kerak",
            'ru': "Местоположение не должно превышать 500 символов",
            'en': "Location must be no more than 500 characters long"
        },
        'location_validation_error': {
            'uz': "Joylashuvni tekshirishda xatolik",
            'ru': "Ошибка проверки местоположения",
            'en': "Location validation failed"
        },
        'invalid_priority': {
            'uz': "Muhimlik darajasi: past, o'rta, yuqori, shoshilinch bo'lishi kerak",
            'ru': "Приоритет должен быть: низкий, средний, высокий, срочный",
            'en': "Priority must be one of: low, medium, high, urgent"
        },
        'priority_validation_error': {
            'uz': "Muhimlik darajasini tekshirishda xatolik",
            'ru': "Ошибка проверки приоритета",
            'en': "Priority validation failed"
        },
        'additional_notes_too_long': {
            'uz': "Qo'shimcha izohlar 1000 ta belgidan oshmasligi kerak",
            'ru': "Дополнительные заметки не должны превышать 1000 символов",
            'en': "Additional notes must be no more than 1000 characters long"
        },
        'additional_notes_validation_error': {
            'uz': "Qo'shimcha izohlarni tekshirishda xatolik",
            'ru': "Ошибка проверки дополнительных заметок",
            'en': "Additional notes validation failed"
        },
        
        # Technical service specific messages
        'invalid_issue_type': {
            'uz': "Noto'g'ri muammo turi tanlangan",
            'ru': "Выбран неверный тип проблемы",
            'en': "Invalid issue type selected"
        },
        'equipment_info_too_long': {
            'uz': "Uskunalar haqida ma'lumot 500 ta belgidan oshmasligi kerak",
            'ru': "Информация об оборудовании не должна превышать 500 символов",
            'en': "Equipment information must be no more than 500 characters long"
        },
        
        # Connection request specific messages
        'invalid_connection_type': {
            'uz': "Noto'g'ri ulanish turi tanlangan",
            'ru': "Выбран неверный тип подключения",
            'en': "Invalid connection type selected"
        },
        'invalid_speed_requirement': {
            'uz': "Tezlik talabi 1 dan 1000 Mbps gacha bo'lishi kerak",
            'ru': "Требование к скорости должно быть от 1 до 1000 Мбит/с",
            'en': "Speed requirement must be between 1 and 1000 Mbps"
        },
        'speed_requirement_not_number': {
            'uz': "Tezlik talabi raqam bo'lishi kerak",
            'ru': "Требование к скорости должно быть числом",
            'en': "Speed requirement must be a number"
        },
        
        # Permission error messages
        'no_client_selection_permission': {
            'uz': "Sizda mijozlarni tanlash huquqi yo'q",
            'ru': "У вас нет разрешения на выбор клиентов",
            'en': "You don't have permission to select clients"
        },
        'no_client_creation_permission': {
            'uz': "Sizda yangi mijoz yaratish huquqi yo'q",
            'ru': "У вас нет разрешения на создание новых клиентов",
            'en': "You don't have permission to create new clients"
        },
        'no_connection_creation_permission': {
            'uz': "Sizda ulanish so'rovlarini yaratish huquqi yo'q",
            'ru': "У вас нет разрешения на создание заявок на подключение",
            'en': "You don't have permission to create connection requests"
        },
        'no_technical_creation_permission': {
            'uz': "Sizda texnik xizmat so'rovlarini yaratish huquqi yo'q",
            'ru': "У вас нет разрешения на создание заявок на техническое обслуживание",
            'en': "You don't have permission to create technical service requests"
        },
        'no_direct_assignment_permission': {
            'uz': "Sizda to'g'ridan-to'g'ri texniklarga tayinlash huquqi yo'q",
            'ru': "У вас нет разрешения на прямое назначение техникам",
            'en': "You don't have permission to assign directly to technicians"
        },
        
        # Security error messages
        'security_threat_detected': {
            'uz': "Xavfsizlik tahdidi aniqlandi: {threat}",
            'ru': "Обнаружена угроза безопасности: {threat}",
            'en': "Security threat detected: {threat}"
        },
        'potential_xss_attack': {
            'uz': "Potentsial XSS hujumi aniqlandi",
            'ru': "Обнаружена потенциальная XSS-атака",
            'en': "Potential XSS attack detected"
        },
        'potential_sql_injection': {
            'uz': "Potentsial SQL in'ektsiya aniqlandi",
            'ru': "Обнаружена потенциальная SQL-инъекция",
            'en': "Potential SQL injection detected"
        },
        'input_too_long': {
            'uz': "Kiritilgan ma'lumot juda uzun (potentsial DoS)",
            'ru': "Введенные данные слишком длинные (потенциальный DoS)",
            'en': "Input too long (potential DoS)"
        },
        'suspicious_unicode_characters': {
            'uz': "Shubhali Unicode belgilar aniqlandi",
            'ru': "Обнаружены подозрительные Unicode символы",
            'en': "Suspicious Unicode characters detected"
        },
        
        # General messages
        'validation_error': {
            'uz': "Tekshirish xatoligi: {error}",
            'ru': "Ошибка проверки: {error}",
            'en': "Validation error: {error}"
        },
        'form_validation_error': {
            'uz': "Formani tekshirishda xatolik",
            'ru': "Ошибка проверки формы",
            'en': "Form validation error"
        },
        'unknown_form_step': {
            'uz': "Noma'lum forma qadami: {step}",
            'ru': "Неизвестный шаг формы: {step}",
            'en': "Unknown form step: {step}"
        },
        
        # Success messages
        'validation_successful': {
            'uz': "Tekshirish muvaffaqiyatli yakunlandi",
            'ru': "Проверка успешно завершена",
            'en': "Validation completed successfully"
        },
        'form_data_valid': {
            'uz': "Forma ma'lumotlari to'g'ri",
            'ru': "Данные формы корректны",
            'en': "Form data is valid"
        },
        
        # Warning messages
        'incomplete_information': {
            'uz': "Ma'lumot to'liq emas",
            'ru': "Информация неполная",
            'en': "Information is incomplete"
        },
        'consider_adding_details': {
            'uz': "Qo'shimcha tafsilotlar qo'shishni o'ylab ko'ring",
            'ru': "Рассмотрите возможность добавления дополнительных деталей",
            'en': "Consider adding more details"
        },
        
        # Role-specific messages
        'manager_validation_note': {
            'uz': "Menejer sifatida siz barcha turdagi arizalarni yarata olasiz",
            'ru': "Как менеджер, вы можете создавать все типы заявок",
            'en': "As a manager, you can create all types of applications"
        },
        'junior_manager_limitation': {
            'uz': "Kichik menejer sifatida siz faqat ulanish so'rovlarini yarata olasiz",
            'ru': "Как младший менеджер, вы можете создавать только заявки на подключение",
            'en': "As a junior manager, you can only create connection requests"
        },
        'call_center_note': {
            'uz': "Qo'ng'iroq markazi operatori sifatida mijozlar bilan bog'lanishni unutmang",
            'ru': "Как оператор колл-центра, не забудьте связаться с клиентами",
            'en': "As a call center operator, remember to contact clients"
        },
        'controller_privileges': {
            'uz': "Nazoratchi sifatida sizda kengaytirilgan huquqlar mavjud",
            'ru': "Как контролер, у вас есть расширенные права",
            'en': "As a controller, you have extended privileges"
        }
    }
    
    # Field name translations
    FIELD_NAMES = {
        'phone': {
            'uz': "Telefon raqami",
            'ru': "Номер телефона",
            'en': "Phone number"
        },
        'full_name': {
            'uz': "To'liq ism",
            'ru': "Полное имя",
            'en': "Full name"
        },
        'address': {
            'uz': "Manzil",
            'ru': "Адрес",
            'en': "Address"
        },
        'email': {
            'uz': "Elektron pochta",
            'ru': "Электронная почта",
            'en': "Email"
        },
        'additional_info': {
            'uz': "Qo'shimcha ma'lumot",
            'ru': "Дополнительная информация",
            'en': "Additional information"
        },
        'description': {
            'uz': "Tavsif",
            'ru': "Описание",
            'en': "Description"
        },
        'location': {
            'uz': "Joylashuv",
            'ru': "Местоположение",
            'en': "Location"
        },
        'priority': {
            'uz': "Muhimlik darajasi",
            'ru': "Приоритет",
            'en': "Priority"
        },
        'additional_notes': {
            'uz': "Qo'shimcha izohlar",
            'ru': "Дополнительные заметки",
            'en': "Additional notes"
        },
        'issue_type': {
            'uz': "Muammo turi",
            'ru': "Тип проблемы",
            'en': "Issue type"
        },
        'equipment_info': {
            'uz': "Uskunalar haqida ma'lumot",
            'ru': "Информация об оборудовании",
            'en': "Equipment information"
        },
        'connection_type': {
            'uz': "Ulanish turi",
            'ru': "Тип подключения",
            'en': "Connection type"
        },
        'speed_requirement': {
            'uz': "Tezlik talabi",
            'ru': "Требование к скорости",
            'en': "Speed requirement"
        }
    }
    
    # Priority level translations
    PRIORITY_LEVELS = {
        'low': {
            'uz': "Past",
            'ru': "Низкий",
            'en': "Low"
        },
        'medium': {
            'uz': "O'rta",
            'ru': "Средний",
            'en': "Medium"
        },
        'high': {
            'uz': "Yuqori",
            'ru': "Высокий",
            'en': "High"
        },
        'urgent': {
            'uz': "Shoshilinch",
            'ru': "Срочный",
            'en': "Urgent"
        }
    }
    
    # Issue type translations
    ISSUE_TYPES = {
        'internet_connection': {
            'uz': "Internet ulanishi",
            'ru': "Подключение к интернету",
            'en': "Internet connection"
        },
        'equipment_malfunction': {
            'uz': "Uskunaning buzilishi",
            'ru': "Неисправность оборудования",
            'en': "Equipment malfunction"
        },
        'signal_quality': {
            'uz': "Signal sifati",
            'ru': "Качество сигнала",
            'en': "Signal quality"
        },
        'billing_issue': {
            'uz': "Hisob-kitob masalasi",
            'ru': "Проблема с оплатой",
            'en': "Billing issue"
        },
        'installation_request': {
            'uz': "O'rnatish so'rovi",
            'ru': "Запрос на установку",
            'en': "Installation request"
        },
        'maintenance': {
            'uz': "Texnik xizmat",
            'ru': "Техническое обслуживание",
            'en': "Maintenance"
        },
        'other': {
            'uz': "Boshqa",
            'ru': "Другое",
            'en': "Other"
        }
    }
    
    # Connection type translations
    CONNECTION_TYPES = {
        'fiber': {
            'uz': "Optik tola",
            'ru': "Оптоволокно",
            'en': "Fiber"
        },
        'cable': {
            'uz': "Kabel",
            'ru': "Кабель",
            'en': "Cable"
        },
        'wireless': {
            'uz': "Simsiz",
            'ru': "Беспроводной",
            'en': "Wireless"
        },
        'satellite': {
            'uz': "Sun'iy yo'ldosh",
            'ru': "Спутниковый",
            'en': "Satellite"
        }
    }
    
    @classmethod
    def get_message(cls, message_key: str, language: str = 'uz', **kwargs) -> str:
        """
        Get localized message by key.
        
        Args:
            message_key: Key of the message
            language: Language code (uz, ru, en)
            **kwargs: Format parameters for the message
            
        Returns:
            Localized message string
        """
        if message_key not in cls.MESSAGES:
            return f"Unknown message: {message_key}"
        
        message_dict = cls.MESSAGES[message_key]
        
        # Get message in requested language, fallback to English
        message = message_dict.get(language, message_dict.get('en', message_key))
        
        # Format message with provided parameters
        try:
            return message.format(**kwargs)
        except KeyError as e:
            # If formatting fails, return message without formatting
            return message
    
    @classmethod
    def get_field_name(cls, field_key: str, language: str = 'uz') -> str:
        """
        Get localized field name.
        
        Args:
            field_key: Key of the field
            language: Language code (uz, ru, en)
            
        Returns:
            Localized field name
        """
        if field_key not in cls.FIELD_NAMES:
            return field_key
        
        field_dict = cls.FIELD_NAMES[field_key]
        return field_dict.get(language, field_dict.get('en', field_key))
    
    @classmethod
    def get_priority_name(cls, priority_key: str, language: str = 'uz') -> str:
        """
        Get localized priority name.
        
        Args:
            priority_key: Key of the priority level
            language: Language code (uz, ru, en)
            
        Returns:
            Localized priority name
        """
        if priority_key not in cls.PRIORITY_LEVELS:
            return priority_key
        
        priority_dict = cls.PRIORITY_LEVELS[priority_key]
        return priority_dict.get(language, priority_dict.get('en', priority_key))
    
    @classmethod
    def get_issue_type_name(cls, issue_key: str, language: str = 'uz') -> str:
        """
        Get localized issue type name.
        
        Args:
            issue_key: Key of the issue type
            language: Language code (uz, ru, en)
            
        Returns:
            Localized issue type name
        """
        if issue_key not in cls.ISSUE_TYPES:
            return issue_key
        
        issue_dict = cls.ISSUE_TYPES[issue_key]
        return issue_dict.get(language, issue_dict.get('en', issue_key))
    
    @classmethod
    def get_connection_type_name(cls, connection_key: str, language: str = 'uz') -> str:
        """
        Get localized connection type name.
        
        Args:
            connection_key: Key of the connection type
            language: Language code (uz, ru, en)
            
        Returns:
            Localized connection type name
        """
        if connection_key not in cls.CONNECTION_TYPES:
            return connection_key
        
        connection_dict = cls.CONNECTION_TYPES[connection_key]
        return connection_dict.get(language, connection_dict.get('en', connection_key))
    
    @classmethod
    def format_validation_errors(cls, errors: Dict[str, list], language: str = 'uz') -> Dict[str, list]:
        """
        Format validation errors with localized field names.
        
        Args:
            errors: Dictionary of field errors
            language: Language code (uz, ru, en)
            
        Returns:
            Dictionary with localized error messages
        """
        formatted_errors = {}
        
        for field, error_list in errors.items():
            # Get localized field name
            field_parts = field.split('.')
            if len(field_parts) > 1:
                # Handle nested fields like "client.phone"
                section = field_parts[0]
                field_name = field_parts[1]
                localized_field = cls.get_field_name(field_name, language)
                formatted_field = f"{section}.{localized_field}"
            else:
                formatted_field = cls.get_field_name(field, language)
            
            formatted_errors[formatted_field] = error_list
        
        return formatted_errors
    
    @classmethod
    def get_role_specific_message(cls, role: str, language: str = 'uz') -> Optional[str]:
        """
        Get role-specific validation message.
        
        Args:
            role: User role
            language: Language code (uz, ru, en)
            
        Returns:
            Role-specific message or None
        """
        role_message_map = {
            'manager': 'manager_validation_note',
            'junior_manager': 'junior_manager_limitation',
            'call_center': 'call_center_note',
            'controller': 'controller_privileges'
        }
        
        message_key = role_message_map.get(role)
        if message_key:
            return cls.get_message(message_key, language)
        
        return None
    
    @classmethod
    def create_error_response(cls, field: str, error_key: str, language: str = 'uz', 
                            message_type: MessageType = MessageType.ERROR, **kwargs) -> Dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            field: Field name where error occurred
            error_key: Error message key
            language: Language code (uz, ru, en)
            message_type: Type of message (error, warning, info, success)
            **kwargs: Additional parameters for message formatting
            
        Returns:
            Standardized error response dictionary
        """
        return {
            'field': field,
            'localized_field': cls.get_field_name(field, language),
            'message': cls.get_message(error_key, language, **kwargs),
            'message_type': message_type.value,
            'error_key': error_key,
            'language': language
        }
    
    @classmethod
    def get_validation_summary(cls, validation_result, language: str = 'uz') -> Dict[str, Any]:
        """
        Create validation summary with localized messages.
        
        Args:
            validation_result: ValidationResult object
            language: Language code (uz, ru, en)
            
        Returns:
            Dictionary with validation summary
        """
        summary = {
            'is_valid': validation_result.is_valid,
            'language': language,
            'error_count': len(validation_result.errors),
            'warning_count': len(validation_result.warnings),
            'errors': cls.format_validation_errors(validation_result.errors, language),
            'warnings': cls.format_validation_errors(validation_result.warnings, language)
        }
        
        if validation_result.is_valid:
            summary['message'] = cls.get_message('validation_successful', language)
        else:
            summary['message'] = cls.get_message('form_validation_error', language)
        
        return summary


# Convenience functions for external use
def get_localized_error(error_key: str, language: str = 'uz', **kwargs) -> str:
    """Get localized error message"""
    return FormErrorMessages.get_message(error_key, language, **kwargs)


def get_localized_field_name(field_key: str, language: str = 'uz') -> str:
    """Get localized field name"""
    return FormErrorMessages.get_field_name(field_key, language)


def format_field_error(field: str, error_key: str, language: str = 'uz', **kwargs) -> str:
    """Format field error with localized field name and message"""
    field_name = FormErrorMessages.get_field_name(field, language)
    error_message = FormErrorMessages.get_message(error_key, language, field=field_name, **kwargs)
    return error_message


def create_validation_response(validation_result, language: str = 'uz') -> Dict[str, Any]:
    """Create comprehensive validation response with localization"""
    return FormErrorMessages.get_validation_summary(validation_result, language)


# Export commonly used message keys
class ErrorKeys:
    """Common error message keys"""
    REQUIRED_FIELD = 'required_field'
    INVALID_PHONE = 'invalid_uzbek_phone'
    NAME_TOO_SHORT = 'name_too_short'
    NAME_TOO_LONG = 'name_too_long'
    DESCRIPTION_TOO_SHORT = 'description_too_short'
    DESCRIPTION_TOO_LONG = 'description_too_long'
    LOCATION_TOO_SHORT = 'location_too_short'
    SECURITY_THREAT = 'security_threat_detected'
    NO_PERMISSION = 'no_client_selection_permission'
    VALIDATION_ERROR = 'validation_error'


class WarningKeys:
    """Common warning message keys"""
    INCOMPLETE_INFO = 'incomplete_information'
    NAME_SINGLE_WORD = 'name_single_word'
    DESCRIPTION_BRIEF = 'description_too_brief'
    ADDRESS_INCOMPLETE = 'address_incomplete'


class SuccessKeys:
    """Common success message keys"""
    VALIDATION_SUCCESSFUL = 'validation_successful'
    FORM_DATA_VALID = 'form_data_valid'