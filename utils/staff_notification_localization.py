"""
Localization support for staff application creation notifications.

This module provides localized notification templates and messages
for all staff application creation workflows.
"""

from typing import Dict, Any, Optional
from utils.get_lang import LanguageText, get_text


class StaffNotificationTexts:
    """Localized notification texts for staff application creation"""
    
    # Client notification templates
    CLIENT_APPLICATION_CREATED_TITLE = LanguageText(
        "🔔 Yangi ariza yaratildi",
        "🔔 Создана новая заявка"
    )
    
    CLIENT_CONNECTION_REQUEST_BODY = LanguageText(
        "Sizning nomingizdan ulanish uchun ariza yaratildi.\n\n"
        "📋 Ariza ID: {application_id}\n"
        "👨‍💼 Yaratuvchi: {creator_name} ({creator_role})\n"
        "📅 Sana: {created_date}\n"
        "📍 Manzil: {location}\n\n"
        "Ariza holati haqida xabar beramiz.",
        
        "От вашего имени создана заявка на подключение.\n\n"
        "📋 ID заявки: {application_id}\n"
        "👨‍💼 Создатель: {creator_name} ({creator_role})\n"
        "📅 Дата: {created_date}\n"
        "📍 Адрес: {location}\n\n"
        "Мы уведомим вас о статусе заявки."
    )
    
    CLIENT_TECHNICAL_SERVICE_BODY = LanguageText(
        "Sizning nomingizdan texnik xizmat uchun ariza yaratildi.\n\n"
        "📋 Ariza ID: {application_id}\n"
        "👨‍💼 Yaratuvchi: {creator_name} ({creator_role})\n"
        "📅 Sana: {created_date}\n"
        "🔧 Xizmat turi: {service_type}\n"
        "📍 Manzil: {location}\n\n"
        "Ariza holati haqida xabar beramiz.",
        
        "От вашего имени создана заявка на техническое обслуживание.\n\n"
        "📋 ID заявки: {application_id}\n"
        "👨‍💼 Создатель: {creator_name} ({creator_role})\n"
        "📅 Дата: {created_date}\n"
        "🔧 Тип услуги: {service_type}\n"
        "📍 Адрес: {location}\n\n"
        "Мы уведомим вас о статусе заявки."
    )
    
    # Staff confirmation notifications
    STAFF_CONFIRMATION_TITLE = LanguageText(
        "✅ Ariza muvaffaqiyatli yaratildi",
        "✅ Заявка успешно создана"
    )
    
    STAFF_CONFIRMATION_BODY = LanguageText(
        "Siz yaratgan ariza tizimga kiritildi.\n\n"
        "📋 Ariza ID: {application_id}\n"
        "👤 Mijoz: {client_name}\n"
        "📞 Telefon: {client_phone}\n"
        "🔄 Holat: Yangi\n"
        "📅 Yaratilgan: {created_date}\n\n"
        "Mijozga xabar yuborildi.",
        
        "Созданная вами заявка внесена в систему.\n\n"
        "📋 ID заявки: {application_id}\n"
        "👤 Клиент: {client_name}\n"
        "📞 Телефон: {client_phone}\n"
        "🔄 Статус: Новая\n"
        "📅 Создана: {created_date}\n\n"
        "Клиент уведомлен."
    )
    
    # Workflow participant notifications
    WORKFLOW_ASSIGNMENT_TITLE = LanguageText(
        "📋 Yangi ariza tayinlandi",
        "📋 Назначена новая заявка"
    )
    
    WORKFLOW_CONNECTION_ASSIGNMENT_BODY = LanguageText(
        "Sizga yangi ulanish arizasi tayinlandi.\n\n"
        "📋 Ariza ID: {application_id}\n"
        "👤 Mijoz: {client_name}\n"
        "📞 Telefon: {client_phone}\n"
        "📍 Manzil: {location}\n"
        "👨‍💼 Yaratuvchi: {creator_name} ({creator_role})\n"
        "⚡ Muhimlik: {priority}\n\n"
        "Iltimos, arizani ko'rib chiqing.",
        
        "Вам назначена новая заявка на подключение.\n\n"
        "📋 ID заявки: {application_id}\n"
        "👤 Клиент: {client_name}\n"
        "📞 Телефон: {client_phone}\n"
        "📍 Адрес: {location}\n"
        "👨‍💼 Создатель: {creator_name} ({creator_role})\n"
        "⚡ Приоритет: {priority}\n\n"
        "Пожалуйста, рассмотрите заявку."
    )
    
    WORKFLOW_TECHNICAL_ASSIGNMENT_BODY = LanguageText(
        "Sizga yangi texnik xizmat arizasi tayinlandi.\n\n"
        "📋 Ariza ID: {application_id}\n"
        "👤 Mijoz: {client_name}\n"
        "📞 Telefon: {client_phone}\n"
        "🔧 Xizmat turi: {service_type}\n"
        "📍 Manzil: {location}\n"
        "👨‍💼 Yaratuvchi: {creator_name} ({creator_role})\n"
        "⚡ Muhimlik: {priority}\n\n"
        "Iltimos, arizani ko'rib chiqing.",
        
        "Вам назначена новая заявка на техническое обслуживание.\n\n"
        "📋 ID заявки: {application_id}\n"
        "👤 Клиент: {client_name}\n"
        "📞 Телефон: {client_phone}\n"
        "🔧 Тип услуги: {service_type}\n"
        "📍 Адрес: {location}\n"
        "👨‍💼 Создатель: {creator_name} ({creator_role})\n"
        "⚡ Приоритет: {priority}\n\n"
        "Пожалуйста, рассмотрите заявку."
    )
    
    # Error notifications
    ERROR_NOTIFICATION_TITLE = LanguageText(
        "❌ Ariza yaratishda xatolik",
        "❌ Ошибка создания заявки"
    )
    
    PERMISSION_ERROR_BODY = LanguageText(
        "Sizda bu turdagi ariza yaratish huquqi yo'q.\n\n"
        "🔒 Ruxsat berilmagan harakat\n"
        "👤 Sizning rolingiz: {user_role}\n"
        "📋 So'ralgan harakat: {requested_action}\n\n"
        "Administrator bilan bog'laning.",
        
        "У вас нет разрешения на создание заявок этого типа.\n\n"
        "🔒 Действие запрещено\n"
        "👤 Ваша роль: {user_role}\n"
        "📋 Запрошенное действие: {requested_action}\n\n"
        "Обратитесь к администратору."
    )
    
    DAILY_LIMIT_ERROR_BODY = LanguageText(
        "Bugun yaratish mumkin bo'lgan arizalar soni tugadi.\n\n"
        "📊 Kunlik limit: {daily_limit}\n"
        "✅ Yaratilgan: {created_today}\n"
        "⏰ Keyingi imkoniyat: ertaga\n\n"
        "Shoshilinch holatlar uchun rahbaringiz bilan bog'laning.",
        
        "Превышен дневной лимит создания заявок.\n\n"
        "📊 Дневной лимит: {daily_limit}\n"
        "✅ Создано: {created_today}\n"
        "⏰ Следующая возможность: завтра\n\n"
        "Для срочных случаев обратитесь к руководителю."
    )
    
    # System notifications
    SYSTEM_NOTIFICATION_TITLE = LanguageText(
        "🔔 Tizim xabari",
        "🔔 Системное уведомление"
    )
    
    AUDIT_LOG_CREATED_BODY = LanguageText(
        "Ariza yaratish jarayoni audit yozuviga kiritildi.\n\n"
        "📋 Ariza ID: {application_id}\n"
        "👨‍💼 Yaratuvchi: {creator_name}\n"
        "📅 Sana: {created_date}\n"
        "🔍 Audit ID: {audit_id}\n\n"
        "Barcha harakatlar nazorat ostida.",
        
        "Процесс создания заявки записан в журнал аудита.\n\n"
        "📋 ID заявки: {application_id}\n"
        "👨‍💼 Создатель: {creator_name}\n"
        "📅 Дата: {created_date}\n"
        "🔍 ID аудита: {audit_id}\n\n"
        "Все действия контролируются."
    )
    
    # Role-specific notification additions
    MANAGER_NOTIFICATION_SUFFIX = LanguageText(
        "\n\n👨‍💼 Menejer huquqlari bilan yaratildi",
        "\n\n👨‍💼 Создано с правами менеджера"
    )
    
    JUNIOR_MANAGER_NOTIFICATION_SUFFIX = LanguageText(
        "\n\n👨‍💼 Kichik menejer tomonidan yaratildi",
        "\n\n👨‍💼 Создано младшим менеджером"
    )
    
    CONTROLLER_NOTIFICATION_SUFFIX = LanguageText(
        "\n\n🔍 Nazoratchi tomonidan yaratildi",
        "\n\n🔍 Создано контролером"
    )
    
    CALL_CENTER_NOTIFICATION_SUFFIX = LanguageText(
        "\n\n📞 Call-markaz operatori tomonidan yaratildi",
        "\n\n📞 Создано оператором колл-центра"
    )


class StaffNotificationFormatter:
    """Formatter for staff application creation notifications"""
    
    @staticmethod
    def format_client_notification(
        application_data: Dict[str, Any],
        creator_data: Dict[str, Any],
        language: str = 'uz'
    ) -> Dict[str, str]:
        """Format client notification message"""
        
        app_type = application_data.get('application_type', '')
        
        # Select appropriate template based on application type
        if app_type == 'connection':
            title = get_text(StaffNotificationTexts.CLIENT_APPLICATION_CREATED_TITLE, language)
            body_template = get_text(StaffNotificationTexts.CLIENT_CONNECTION_REQUEST_BODY, language)
        elif app_type == 'technical':
            title = get_text(StaffNotificationTexts.CLIENT_APPLICATION_CREATED_TITLE, language)
            body_template = get_text(StaffNotificationTexts.CLIENT_TECHNICAL_SERVICE_BODY, language)
        else:
            title = get_text(StaffNotificationTexts.CLIENT_APPLICATION_CREATED_TITLE, language)
            body_template = get_text(StaffNotificationTexts.CLIENT_CONNECTION_REQUEST_BODY, language)
        
        # Format the message body
        body = body_template.format(
            application_id=application_data.get('id', 'N/A'),
            creator_name=creator_data.get('full_name', 'N/A'),
            creator_role=StaffNotificationFormatter._get_role_display_name(
                creator_data.get('role', ''), language
            ),
            created_date=application_data.get('created_at', 'N/A'),
            location=application_data.get('location', 'N/A'),
            service_type=application_data.get('service_type', 'N/A')
        )
        
        # Add role-specific suffix
        role_suffix = StaffNotificationFormatter._get_role_suffix(
            creator_data.get('role', ''), language
        )
        if role_suffix:
            body += role_suffix
        
        return {
            'title': title,
            'body': body
        }
    
    @staticmethod
    def format_staff_confirmation(
        application_data: Dict[str, Any],
        client_data: Dict[str, Any],
        language: str = 'uz'
    ) -> Dict[str, str]:
        """Format staff confirmation notification"""
        
        title = get_text(StaffNotificationTexts.STAFF_CONFIRMATION_TITLE, language)
        body_template = get_text(StaffNotificationTexts.STAFF_CONFIRMATION_BODY, language)
        
        body = body_template.format(
            application_id=application_data.get('id', 'N/A'),
            client_name=client_data.get('full_name', 'N/A'),
            client_phone=client_data.get('phone', 'N/A'),
            created_date=application_data.get('created_at', 'N/A')
        )
        
        return {
            'title': title,
            'body': body
        }
    
    @staticmethod
    def format_workflow_assignment(
        application_data: Dict[str, Any],
        client_data: Dict[str, Any],
        creator_data: Dict[str, Any],
        language: str = 'uz'
    ) -> Dict[str, str]:
        """Format workflow assignment notification"""
        
        app_type = application_data.get('application_type', '')
        
        title = get_text(StaffNotificationTexts.WORKFLOW_ASSIGNMENT_TITLE, language)
        
        if app_type == 'connection':
            body_template = get_text(StaffNotificationTexts.WORKFLOW_CONNECTION_ASSIGNMENT_BODY, language)
        elif app_type == 'technical':
            body_template = get_text(StaffNotificationTexts.WORKFLOW_TECHNICAL_ASSIGNMENT_BODY, language)
        else:
            body_template = get_text(StaffNotificationTexts.WORKFLOW_CONNECTION_ASSIGNMENT_BODY, language)
        
        body = body_template.format(
            application_id=application_data.get('id', 'N/A'),
            client_name=client_data.get('full_name', 'N/A'),
            client_phone=client_data.get('phone', 'N/A'),
            location=application_data.get('location', 'N/A'),
            creator_name=creator_data.get('full_name', 'N/A'),
            creator_role=StaffNotificationFormatter._get_role_display_name(
                creator_data.get('role', ''), language
            ),
            priority=StaffNotificationFormatter._get_priority_display_name(
                application_data.get('priority', 'medium'), language
            ),
            service_type=application_data.get('service_type', 'N/A')
        )
        
        return {
            'title': title,
            'body': body
        }
    
    @staticmethod
    def format_error_notification(
        error_type: str,
        error_data: Dict[str, Any],
        language: str = 'uz'
    ) -> Dict[str, str]:
        """Format error notification message"""
        
        title = get_text(StaffNotificationTexts.ERROR_NOTIFICATION_TITLE, language)
        
        if error_type == 'permission_denied':
            body_template = get_text(StaffNotificationTexts.PERMISSION_ERROR_BODY, language)
            body = body_template.format(
                user_role=StaffNotificationFormatter._get_role_display_name(
                    error_data.get('user_role', ''), language
                ),
                requested_action=error_data.get('requested_action', 'N/A')
            )
        elif error_type == 'daily_limit_exceeded':
            body_template = get_text(StaffNotificationTexts.DAILY_LIMIT_ERROR_BODY, language)
            body = body_template.format(
                daily_limit=error_data.get('daily_limit', 'N/A'),
                created_today=error_data.get('created_today', 'N/A')
            )
        else:
            body = f"Xatolik turi: {error_type}" if language == 'uz' else f"Тип ошибки: {error_type}"
        
        return {
            'title': title,
            'body': body
        }
    
    @staticmethod
    def format_audit_notification(
        application_data: Dict[str, Any],
        creator_data: Dict[str, Any],
        audit_data: Dict[str, Any],
        language: str = 'uz'
    ) -> Dict[str, str]:
        """Format audit log notification"""
        
        title = get_text(StaffNotificationTexts.SYSTEM_NOTIFICATION_TITLE, language)
        body_template = get_text(StaffNotificationTexts.AUDIT_LOG_CREATED_BODY, language)
        
        body = body_template.format(
            application_id=application_data.get('id', 'N/A'),
            creator_name=creator_data.get('full_name', 'N/A'),
            created_date=application_data.get('created_at', 'N/A'),
            audit_id=audit_data.get('id', 'N/A')
        )
        
        return {
            'title': title,
            'body': body
        }
    
    @staticmethod
    def _get_role_display_name(role: str, language: str) -> str:
        """Get localized role display name"""
        role_names = {
            'manager': {
                'uz': 'Menejer',
                'ru': 'Менеджер'
            },
            'junior_manager': {
                'uz': 'Kichik menejer',
                'ru': 'Младший менеджер'
            },
            'controller': {
                'uz': 'Nazoratchi',
                'ru': 'Контролер'
            },
            'call_center': {
                'uz': 'Call-markaz operatori',
                'ru': 'Оператор колл-центра'
            }
        }
        
        if role in role_names and language in role_names[role]:
            return role_names[role][language]
        
        return role
    
    @staticmethod
    def _get_priority_display_name(priority: str, language: str) -> str:
        """Get localized priority display name"""
        priority_names = {
            'low': {
                'uz': 'Past',
                'ru': 'Низкий'
            },
            'medium': {
                'uz': "O'rta",
                'ru': 'Средний'
            },
            'high': {
                'uz': 'Yuqori',
                'ru': 'Высокий'
            },
            'urgent': {
                'uz': 'Shoshilinch',
                'ru': 'Срочный'
            }
        }
        
        if priority in priority_names and language in priority_names[priority]:
            return priority_names[priority][language]
        
        return priority
    
    @staticmethod
    def _get_role_suffix(role: str, language: str) -> Optional[str]:
        """Get role-specific notification suffix"""
        role_suffixes = {
            'manager': StaffNotificationTexts.MANAGER_NOTIFICATION_SUFFIX,
            'junior_manager': StaffNotificationTexts.JUNIOR_MANAGER_NOTIFICATION_SUFFIX,
            'controller': StaffNotificationTexts.CONTROLLER_NOTIFICATION_SUFFIX,
            'call_center': StaffNotificationTexts.CALL_CENTER_NOTIFICATION_SUFFIX
        }
        
        if role in role_suffixes:
            return get_text(role_suffixes[role], language)
        
        return None


def create_client_notification(
    application_data: Dict[str, Any],
    creator_data: Dict[str, Any],
    language: str = 'uz'
) -> Dict[str, str]:
    """Create client notification for staff-created application"""
    return StaffNotificationFormatter.format_client_notification(
        application_data, creator_data, language
    )


def create_staff_confirmation(
    application_data: Dict[str, Any],
    client_data: Dict[str, Any],
    language: str = 'uz'
) -> Dict[str, str]:
    """Create staff confirmation notification"""
    return StaffNotificationFormatter.format_staff_confirmation(
        application_data, client_data, language
    )


def create_workflow_assignment_notification(
    application_data: Dict[str, Any],
    client_data: Dict[str, Any],
    creator_data: Dict[str, Any],
    language: str = 'uz'
) -> Dict[str, str]:
    """Create workflow assignment notification"""
    return StaffNotificationFormatter.format_workflow_assignment(
        application_data, client_data, creator_data, language
    )


def create_error_notification(
    error_type: str,
    error_data: Dict[str, Any],
    language: str = 'uz'
) -> Dict[str, str]:
    """Create error notification"""
    return StaffNotificationFormatter.format_error_notification(
        error_type, error_data, language
    )


def create_audit_notification(
    application_data: Dict[str, Any],
    creator_data: Dict[str, Any],
    audit_data: Dict[str, Any],
    language: str = 'uz'
) -> Dict[str, str]:
    """Create audit log notification"""
    return StaffNotificationFormatter.format_audit_notification(
        application_data, creator_data, audit_data, language
    )