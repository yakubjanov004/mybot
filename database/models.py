from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class UserRole(Enum):
    CLIENT = "client"
    TECHNICIAN = "technician"
    MANAGER = "manager"
    ADMIN = "admin"
    CALL_CENTER = "call_center"
    WAREHOUSE = "warehouse"
    CONTROLLER = "controller"
    BLOCKED = "blocked"

class ZayavkaStatus(Enum):
    NEW = "new"
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class User:
    id: Optional[int] = None
    telegram_id: Optional[int] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = UserRole.CLIENT.value
    language: str = "ru"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'language': self.language,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_activity': self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(**data)

@dataclass
class Zayavka:
    id: Optional[int] = None
    user_id: Optional[int] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    status: str = ZayavkaStatus.NEW.value
    priority: str = Priority.MEDIUM.value
    technician_id: Optional[int] = None
    assigned_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    notes: Optional[str] = None
    client_feedback: Optional[str] = None
    rating: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description,
            'address': self.address,
            'phone': self.phone,
            'status': self.status,
            'priority': self.priority,
            'technician_id': self.technician_id,
            'assigned_by': self.assigned_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'assigned_at': self.assigned_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'cancelled_at': self.cancelled_at,
            'estimated_completion': self.estimated_completion,
            'actual_completion': self.actual_completion,
            'notes': self.notes,
            'client_feedback': self.client_feedback,
            'rating': self.rating
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Zayavka':
        return cls(**data)

@dataclass
class Material:
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    quantity_in_stock: int = 0
    min_quantity: int = 0
    price: float = 0.0
    supplier: Optional[str] = None
    location: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'unit': self.unit,
            'quantity_in_stock': self.quantity_in_stock,
            'min_quantity': self.min_quantity,
            'price': self.price,
            'supplier': self.supplier,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Material':
        return cls(**data)

@dataclass
class MaterialUsage:
    id: Optional[int] = None
    zayavka_id: Optional[int] = None
    material_id: Optional[int] = None
    quantity_used: int = 0
    issued_by: Optional[int] = None
    issued_to: Optional[int] = None
    issued_at: Optional[datetime] = None
    returned_quantity: int = 0
    returned_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'zayavka_id': self.zayavka_id,
            'material_id': self.material_id,
            'quantity_used': self.quantity_used,
            'issued_by': self.issued_by,
            'issued_to': self.issued_to,
            'issued_at': self.issued_at,
            'returned_quantity': self.returned_quantity,
            'returned_at': self.returned_at,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialUsage':
        return cls(**data)

@dataclass
class TechnicianTask:
    id: Optional[int] = None
    technician_id: Optional[int] = None
    zayavka_id: Optional[int] = None
    assigned_by: Optional[int] = None
    assigned_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "assigned"
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    time_spent_minutes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'technician_id': self.technician_id,
            'zayavka_id': self.zayavka_id,
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at,
            'accepted_at': self.accepted_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'status': self.status,
            'notes': self.notes,
            'completion_notes': self.completion_notes,
            'time_spent_minutes': self.time_spent_minutes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TechnicianTask':
        return cls(**data)

@dataclass
class Feedback:
    id: Optional[int] = None
    zayavka_id: Optional[int] = None
    user_id: Optional[int] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
    technician_rating: Optional[int] = None
    service_rating: Optional[int] = None
    speed_rating: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'zayavka_id': self.zayavka_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'technician_rating': self.technician_rating,
            'service_rating': self.service_rating,
            'speed_rating': self.speed_rating,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feedback':
        return cls(**data)

@dataclass
class ChatMessage:
    id: Optional[int] = None
    chat_id: Optional[int] = None
    user_id: Optional[int] = None
    message: Optional[str] = None
    message_type: str = "text"
    file_path: Optional[str] = None
    is_from_support: bool = False
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'message': self.message,
            'message_type': self.message_type,
            'file_path': self.file_path,
            'is_from_support': self.is_from_support,
            'created_at': self.created_at,
            'read_at': self.read_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        return cls(**data)

@dataclass
class SupportChat:
    id: Optional[int] = None
    user_id: Optional[int] = None
    zayavka_id: Optional[int] = None
    support_user_id: Optional[int] = None
    status: str = "open"
    subject: Optional[str] = None
    priority: str = Priority.MEDIUM.value
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'zayavka_id': self.zayavka_id,
            'support_user_id': self.support_user_id,
            'status': self.status,
            'subject': self.subject,
            'priority': self.priority,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'closed_at': self.closed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SupportChat':
        return cls(**data)

@dataclass
class HelpRequest:
    id: Optional[int] = None
    technician_id: Optional[int] = None
    zayavka_id: Optional[int] = None
    request_type: str = "general"
    description: Optional[str] = None
    status: str = "pending"
    assigned_to: Optional[int] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'technician_id': self.technician_id,
            'zayavka_id': self.zayavka_id,
            'request_type': self.request_type,
            'description': self.description,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at,
            'resolved_at': self.resolved_at,
            'resolution_notes': self.resolution_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HelpRequest':
        return cls(**data)

@dataclass
class Equipment:
    id: Optional[int] = None
    name: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    category: Optional[str] = None
    status: str = "available"
    assigned_to: Optional[int] = None
    location: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_until: Optional[datetime] = None
    maintenance_schedule: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'serial_number': self.serial_number,
            'category': self.category,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'location': self.location,
            'purchase_date': self.purchase_date,
            'warranty_until': self.warranty_until,
            'maintenance_schedule': self.maintenance_schedule,
            'last_maintenance': self.last_maintenance,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Equipment':
        return cls(**data)

@dataclass
class Notification:
    id: Optional[int] = None
    user_id: Optional[int] = None
    title: Optional[str] = None
    message: Optional[str] = None
    notification_type: str = "info"
    related_id: Optional[int] = None
    related_type: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'is_read': self.is_read,
            'created_at': self.created_at,
            'read_at': self.read_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        return cls(**data)

# Utility functions for models
def get_status_display(status: str, language: str = 'ru') -> str:
    """Get display text for status"""
    status_map = {
        'new': {'uz': 'Yangi', 'ru': 'Новая'},
        'pending': {'uz': 'Kutilmoqda', 'ru': 'В ожидании'},
        'assigned': {'uz': 'Tayinlangan', 'ru': 'Назначена'},
        'in_progress': {'uz': 'Bajarilmoqda', 'ru': 'В работе'},
        'completed': {'uz': 'Bajarildi', 'ru': 'Завершена'},
        'cancelled': {'uz': 'Bekor qilindi', 'ru': 'Отменена'}
    }
    
    return status_map.get(status, {}).get(language, status)

def get_priority_display(priority: str, language: str = 'ru') -> str:
    """Get display text for priority"""
    priority_map = {
        'low': {'uz': 'Past', 'ru': 'Низкий'},
        'medium': {'uz': "O'rta", 'ru': 'Средний'},
        'high': {'uz': 'Yuqori', 'ru': 'Высокий'},
        'urgent': {'uz': 'Shoshilinch', 'ru': 'Срочный'}
    }
    
    return priority_map.get(priority, {}).get(language, priority)

def get_role_display(role: str, language: str = 'ru') -> str:
    """Get display text for role"""
    role_map = {
        'client': {'uz': 'Mijoz', 'ru': 'Клиент'},
        'technician': {'uz': 'Texnik', 'ru': 'Техник'},
        'manager': {'uz': 'Menejer', 'ru': 'Менеджер'},
        'admin': {'uz': 'Administrator', 'ru': 'Администратор'},
        'call_center': {'uz': 'Call-markaz', 'ru': 'Call-центр'},
        'warehouse': {'uz': 'Ombor', 'ru': 'Склад'},
        'controller': {'uz': 'Nazoratchi', 'ru': 'Контролер'},
        'blocked': {'uz': 'Bloklangan', 'ru': 'Заблокирован'}
    }
    
    return role_map.get(role, {}).get(language, role)

# Model collections for easier management
class Models:
    """Collection of all models"""
    User = User
    Zayavka = Zayavka
    Material = Material
    MaterialUsage = MaterialUsage
    TechnicianTask = TechnicianTask
    Feedback = Feedback
    ChatMessage = ChatMessage
    SupportChat = SupportChat
    HelpRequest = HelpRequest
    Equipment = Equipment
    Notification = Notification

# Constants
class ModelConstants:
    """Model-related constants"""
    
    USER_ROLES = [role.value for role in UserRole]
    ZAYAVKA_STATUSES = [status.value for status in ZayavkaStatus]
    PRIORITIES = [priority.value for priority in Priority]
    
    DEFAULT_LANGUAGE = "ru"
    DEFAULT_ROLE = UserRole.CLIENT.value
    DEFAULT_STATUS = ZayavkaStatus.NEW.value
    DEFAULT_PRIORITY = Priority.MEDIUM.value
    
    # Validation constants
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_PHONE_LENGTH = 20
    MAX_ADDRESS_LENGTH = 500
    
    # Rating constants
    MIN_RATING = 1
    MAX_RATING = 5
