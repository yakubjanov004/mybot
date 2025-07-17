"""
Workflow System Keyboards
Provides keyboard layouts for workflow-specific actions across all roles
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict, Any, Optional
from database.models import UserRole, WorkflowType, WorkflowAction, Priority


def workflow_request_type_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Keyboard for selecting workflow request type"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="🔌 Ulanish so'rovi", callback_data="workflow_type_connection_request")],
            [InlineKeyboardButton(text="🔧 Texnik xizmat", callback_data="workflow_type_technical_service")],
            [InlineKeyboardButton(text="📞 Call-markaz xizmati", callback_data="workflow_type_call_center_direct")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🔌 Запрос подключения", callback_data="workflow_type_connection_request")],
            [InlineKeyboardButton(text="🔧 Техническое обслуживание", callback_data="workflow_type_technical_service")],
            [InlineKeyboardButton(text="📞 Сервис call-центра", callback_data="workflow_type_call_center_direct")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workflow_priority_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Keyboard for selecting request priority"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="🟢 Past", callback_data="priority_low")],
            [InlineKeyboardButton(text="🟡 O'rta", callback_data="priority_medium")],
            [InlineKeyboardButton(text="🟠 Yuqori", callback_data="priority_high")],
            [InlineKeyboardButton(text="🔴 Shoshilinch", callback_data="priority_urgent")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🟢 Низкий", callback_data="priority_low")],
            [InlineKeyboardButton(text="🟡 Средний", callback_data="priority_medium")],
            [InlineKeyboardButton(text="🟠 Высокий", callback_data="priority_high")],
            [InlineKeyboardButton(text="🔴 Срочный", callback_data="priority_urgent")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workflow_action_keyboard(role: str, available_actions: List[str], lang: str = 'ru') -> InlineKeyboardMarkup:
    """Generate keyboard based on available workflow actions for role"""
    buttons = []
    
    # Action text mappings
    action_texts = {
        'uz': {
            WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value: "👤 Kichik menejerga tayinlash",
            WorkflowAction.CALL_CLIENT.value: "📞 Mijozga qo'ng'iroq qilish",
            WorkflowAction.FORWARD_TO_CONTROLLER.value: "➡️ Nazoratchiga yuborish",
            WorkflowAction.ASSIGN_TO_TECHNICIAN.value: "🔧 Texnikga tayinlash",
            WorkflowAction.START_INSTALLATION.value: "🚀 O'rnatishni boshlash",
            WorkflowAction.DOCUMENT_EQUIPMENT.value: "📝 Jihozlarni hujjatlash",
            WorkflowAction.UPDATE_INVENTORY.value: "📦 Inventarni yangilash",
            WorkflowAction.START_DIAGNOSTICS.value: "🔍 Diagnostikani boshlash",
            WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value: "🤔 Ombor ishtirokini hal qilish",
            WorkflowAction.RESOLVE_WITHOUT_WAREHOUSE.value: "✅ Omborsiz hal qilish",
            WorkflowAction.REQUEST_WAREHOUSE_SUPPORT.value: "📦 Ombor yordamini so'rash",
            WorkflowAction.PREPARE_EQUIPMENT.value: "🛠️ Jihozlarni tayyorlash",
            WorkflowAction.CONFIRM_EQUIPMENT_READY.value: "✅ Jihozlar tayyorligini tasdiqlash",
            WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value: "🏁 Texnik xizmatni yakunlash",
            WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value: "📞 Operatorga tayinlash",
            WorkflowAction.RESOLVE_REMOTELY.value: "💻 Masofadan hal qilish",
            WorkflowAction.CLOSE_REQUEST.value: "🔒 So'rovni yopish",
            WorkflowAction.ADD_COMMENTS.value: "💬 Izoh qo'shish",
            WorkflowAction.CANCEL_REQUEST.value: "❌ So'rovni bekor qilish"
        },
        'ru': {
            WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value: "👤 Назначить младшему менеджеру",
            WorkflowAction.CALL_CLIENT.value: "📞 Позвонить клиенту",
            WorkflowAction.FORWARD_TO_CONTROLLER.value: "➡️ Переслать контролеру",
            WorkflowAction.ASSIGN_TO_TECHNICIAN.value: "🔧 Назначить технику",
            WorkflowAction.START_INSTALLATION.value: "🚀 Начать установку",
            WorkflowAction.DOCUMENT_EQUIPMENT.value: "📝 Документировать оборудование",
            WorkflowAction.UPDATE_INVENTORY.value: "📦 Обновить инвентарь",
            WorkflowAction.START_DIAGNOSTICS.value: "🔍 Начать диагностику",
            WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value: "🤔 Решить участие склада",
            WorkflowAction.RESOLVE_WITHOUT_WAREHOUSE.value: "✅ Решить без склада",
            WorkflowAction.REQUEST_WAREHOUSE_SUPPORT.value: "📦 Запросить поддержку склада",
            WorkflowAction.PREPARE_EQUIPMENT.value: "🛠️ Подготовить оборудование",
            WorkflowAction.CONFIRM_EQUIPMENT_READY.value: "✅ Подтвердить готовность оборудования",
            WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value: "🏁 Завершить техническое обслуживание",
            WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value: "📞 Назначить оператору",
            WorkflowAction.RESOLVE_REMOTELY.value: "💻 Решить удаленно",
            WorkflowAction.CLOSE_REQUEST.value: "🔒 Закрыть запрос",
            WorkflowAction.ADD_COMMENTS.value: "💬 Добавить комментарий",
            WorkflowAction.CANCEL_REQUEST.value: "❌ Отменить запрос"
        }
    }
    
    # Generate buttons for available actions
    for action in available_actions:
        text = action_texts.get(lang, {}).get(action, action)
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"workflow_action_{action}"
        )])
    
    # Add common actions
    if lang == 'uz':
        buttons.append([InlineKeyboardButton(text="💬 Izoh qo'shish", callback_data="workflow_action_add_comments")])
        buttons.append([InlineKeyboardButton(text="🔄 Yangilash", callback_data="workflow_refresh")])
    else:
        buttons.append([InlineKeyboardButton(text="💬 Добавить комментарий", callback_data="workflow_action_add_comments")])
        buttons.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="workflow_refresh")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_selection_keyboard(users: List[Dict[str, Any]], action: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Generate keyboard for selecting users (technicians, managers, etc.)"""
    buttons = []
    
    for user in users:
        name = user.get('full_name', f"User {user['id']}")
        buttons.append([InlineKeyboardButton(
            text=f"👤 {name}",
            callback_data=f"select_user_{action}_{user['id']}"
        )])
    
    # Add back button
    back_text = "⬅️ Orqaga" if lang == 'uz' else "⬅️ Назад"
    buttons.append([InlineKeyboardButton(text=back_text, callback_data="workflow_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workflow_request_details_keyboard(request_id: str, role_current : str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Generate keyboard for viewing request details"""
    buttons = []
    
    if lang == 'uz':
        buttons.extend([
            [InlineKeyboardButton(text="📋 Tafsilotlar", callback_data=f"view_request_details_{request_id}")],
            [InlineKeyboardButton(text="📜 Tarix", callback_data=f"view_request_history_{request_id}")],
            [InlineKeyboardButton(text="🔧 Amallar", callback_data=f"workflow_actions_{request_id}")],
            [InlineKeyboardButton(text="💬 Izoh qo'shish", callback_data=f"add_comment_{request_id}")],
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"refresh_request_{request_id}")]
        ])
    else:
        buttons.extend([
            [InlineKeyboardButton(text="📋 Детали", callback_data=f"view_request_details_{request_id}")],
            [InlineKeyboardButton(text="📜 История", callback_data=f"view_request_history_{request_id}")],
            [InlineKeyboardButton(text="🔧 Действия", callback_data=f"workflow_actions_{request_id}")],
            [InlineKeyboardButton(text="💬 Добавить комментарий", callback_data=f"add_comment_{request_id}")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_request_{request_id}")]
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def equipment_selection_keyboard(materials: List[Dict[str, Any]], lang: str = 'ru') -> InlineKeyboardMarkup:
    """Generate keyboard for selecting equipment/materials"""
    buttons = []
    
    for material in materials:
        name = material.get('name', f"Material {material['id']}")
        stock = material.get('quantity_in_stock', 0)
        unit = material.get('unit', 'pcs')
        
        text = f"📦 {name} ({stock} {unit})"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"select_material_{material['id']}"
        )])
    
    # Add control buttons
    if lang == 'uz':
        buttons.extend([
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_equipment_selection")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_equipment_selection")]
        ])
    else:
        buttons.extend([
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_equipment_selection")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_equipment_selection")]
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rating_keyboard(request_id: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Generate keyboard for service rating"""
    buttons = []
    
    # Star rating buttons
    for i in range(1, 6):
        stars = "⭐" * i
        buttons.append([InlineKeyboardButton(
            text=f"{stars} ({i})",
            callback_data=f"rate_service_{request_id}_{i}"
        )])
    
    # Skip rating option
    skip_text = "⏭️ O'tkazib yuborish" if lang == 'uz' else "⏭️ Пропустить"
    buttons.append([InlineKeyboardButton(text=skip_text, callback_data=f"skip_rating_{request_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workflow_navigation_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Main navigation keyboard for workflow system"""
    if lang == 'uz':
        buttons = [
            [KeyboardButton(text="📋 Mening topshiriqlarim")],
            [KeyboardButton(text="➕ Yangi so'rov"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🔔 Bildirishnomalar"), KeyboardButton(text="⚙️ Sozlamalar")],
            [KeyboardButton(text="🏠 Bosh menyu")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="📋 Мои задания")],
            [KeyboardButton(text="➕ Новый запрос"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔔 Уведомления"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🏠 Главное меню")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def confirmation_keyboard(action: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Generate confirmation keyboard for actions"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="✅ Ha", callback_data=f"confirm_{action}")],
            [InlineKeyboardButton(text="❌ Yo'q", callback_data=f"cancel_{action}")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}")],
            [InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def warehouse_decision_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Keyboard for technician to decide warehouse involvement"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="📦 Ombor kerak", callback_data="warehouse_needed")],
            [InlineKeyboardButton(text="🚫 Ombor kerak emas", callback_data="warehouse_not_needed")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="📦 Нужен склад", callback_data="warehouse_needed")],
            [InlineKeyboardButton(text="🚫 Склад не нужен", callback_data="warehouse_not_needed")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workflow_status_keyboard(request_id: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Generate keyboard for workflow status actions"""
    if lang == 'uz':
        buttons = [
            [InlineKeyboardButton(text="📋 Tafsilotlar", callback_data=f"status_details_{request_id}")],
            [InlineKeyboardButton(text="📜 Tarix", callback_data=f"status_history_{request_id}")],
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"status_refresh_{request_id}")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="📋 Детали", callback_data=f"status_details_{request_id}")],
            [InlineKeyboardButton(text="📜 История", callback_data=f"status_history_{request_id}")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"status_refresh_{request_id}")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Helper functions for dynamic keyboard generation

def get_role_specific_actions(role: str, workflow_type: str) -> List[str]:
    """Get available actions for specific role and workflow type"""
    role_actions = {
        UserRole.MANAGER.value: {
            WorkflowType.CONNECTION_REQUEST.value: [
                WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value
            ]
        },
        UserRole.JUNIOR_MANAGER.value: {
            WorkflowType.CONNECTION_REQUEST.value: [
                WorkflowAction.CALL_CLIENT.value,
                WorkflowAction.FORWARD_TO_CONTROLLER.value
            ]
        },
        UserRole.CONTROLLER.value: {
            WorkflowType.CONNECTION_REQUEST.value: [
                WorkflowAction.ASSIGN_TO_TECHNICIAN.value
            ],
            WorkflowType.TECHNICAL_SERVICE.value: [
                WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value
            ]
        },
        UserRole.TECHNICIAN.value: {
            WorkflowType.CONNECTION_REQUEST.value: [
                WorkflowAction.START_INSTALLATION.value,
                WorkflowAction.DOCUMENT_EQUIPMENT.value
            ],
            WorkflowType.TECHNICAL_SERVICE.value: [
                WorkflowAction.START_DIAGNOSTICS.value,
                WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value,
                WorkflowAction.RESOLVE_WITHOUT_WAREHOUSE.value,
                WorkflowAction.REQUEST_WAREHOUSE_SUPPORT.value,
                WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value
            ]
        },
        UserRole.WAREHOUSE.value: {
            WorkflowType.CONNECTION_REQUEST.value: [
                WorkflowAction.UPDATE_INVENTORY.value,
                WorkflowAction.CLOSE_REQUEST.value
            ],
            WorkflowType.TECHNICAL_SERVICE.value: [
                WorkflowAction.PREPARE_EQUIPMENT.value,
                WorkflowAction.CONFIRM_EQUIPMENT_READY.value,
                WorkflowAction.UPDATE_INVENTORY.value
            ]
        },
        UserRole.CALL_CENTER_SUPERVISOR.value: {
            WorkflowType.CALL_CENTER_DIRECT.value: [
                WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value
            ]
        },
        UserRole.CALL_CENTER.value: {
            WorkflowType.CALL_CENTER_DIRECT.value: [
                WorkflowAction.RESOLVE_REMOTELY.value
            ]
        }
    }
    
    return role_actions.get(role, {}).get(workflow_type, [])


def create_dynamic_workflow_keyboard(role: str, workflow_type: str, request_id: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Create dynamic keyboard based on role and workflow type"""
    available_actions = get_role_specific_actions(role, workflow_type)
    
    if not available_actions:
        # Return basic keyboard if no specific actions
        return workflow_request_details_keyboard(request_id, role, lang)
    
    return workflow_action_keyboard(role, available_actions, lang)