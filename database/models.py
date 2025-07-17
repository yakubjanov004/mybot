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
    JUNIOR_MANAGER = "junior_manager"
    CALL_CENTER_SUPERVISOR = "call_center_supervisor"

class ZayavkaStatus(Enum):
    # General Statuses
    NEW = "new"
    CANCELLED = "cancelled"
    CLOSED = "closed" # Final status after feedback

    # Manager Flow
    PENDING_JUNIOR_MANAGER = "pending_junior_manager"
    ASSIGNED_TO_JUNIOR_MANAGER = "assigned_to_junior_manager"


    # Controller Flow
    PENDING_CONTROLLER = "pending_controller"
    ASSIGNED_TO_TECHNICIAN = "assigned_to_technician"

    # Technician Flow
    TECHNICIAN_IN_PROGRESS = "technician_in_progress"
    PENDING_WAREHOUSE_CONFIRMATION = "pending_warehouse_confirmation"
    TECHNICIAN_COMPLETED = "technician_completed"

    # Warehouse Flow
    WAREHOUSE_CONFIRMED = "warehouse_confirmed"
    
    # Call Center Flow
    ASSIGNED_TO_CALL_CENTER = "assigned_to_call_center"
    CALL_CENTER_IN_PROGRESS = "call_center_in_progress"
    CALL_CENTER_COMPLETED = "call_center_completed"

    # Client Feedback
    PENDING_FEEDBACK = "pending_feedback"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Workflow-specific enums
class WorkflowType(Enum):
    CONNECTION_REQUEST = "connection_request"
    TECHNICAL_SERVICE = "technical_service"
    CALL_CENTER_DIRECT = "call_center_direct"

class RequestStatus(Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class WorkflowAction(Enum):
    # Connection workflow actions
    SUBMIT_REQUEST = "submit_request"
    ASSIGN_TO_JUNIOR_MANAGER = "assign_to_junior_manager"
    CALL_CLIENT = "call_client"
    FORWARD_TO_CONTROLLER = "forward_to_controller"
    ASSIGN_TO_TECHNICIAN = "assign_to_technician"
    START_INSTALLATION = "start_installation"
    DOCUMENT_EQUIPMENT = "document_equipment"
    UPDATE_INVENTORY = "update_inventory"
    CLOSE_REQUEST = "close_request"
    RATE_SERVICE = "rate_service"
    
    # Technical service actions
    SUBMIT_TECHNICAL_REQUEST = "submit_technical_request"
    ASSIGN_TECHNICAL_TO_TECHNICIAN = "assign_technical_to_technician"
    START_DIAGNOSTICS = "start_diagnostics"
    DECIDE_WAREHOUSE_INVOLVEMENT = "decide_warehouse_involvement"
    RESOLVE_WITHOUT_WAREHOUSE = "resolve_without_warehouse"
    REQUEST_WAREHOUSE_SUPPORT = "request_warehouse_support"
    PREPARE_EQUIPMENT = "prepare_equipment"
    CONFIRM_EQUIPMENT_READY = "confirm_equipment_ready"
    COMPLETE_TECHNICAL_SERVICE = "complete_technical_service"
    
    # Call center actions
    CREATE_CALL_CENTER_REQUEST = "create_call_center_request"
    ASSIGN_TO_CALL_CENTER_SUPERVISOR = "assign_to_call_center_supervisor"
    ASSIGN_TO_CALL_CENTER_OPERATOR = "assign_to_call_center_operator"
    RESOLVE_REMOTELY = "resolve_remotely"
    
    # Common actions
    ADD_COMMENTS = "add_comments"
    CANCEL_REQUEST = "cancel_request"
    ESCALATE = "escalate"

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

# Workflow-specific models
@dataclass
class ServiceRequest:
    id: Optional[str] = None
    workflow_type: str = WorkflowType.CONNECTION_REQUEST.value
    client_id: Optional[int] = None
    role_current: Optional[str] = None
    current_status: str = RequestStatus.CREATED.value
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    priority: str = Priority.MEDIUM.value
    
    # Request details
    description: Optional[str] = None
    location: Optional[str] = None
    contact_info: Dict[str, Any] = field(default_factory=dict)
    
    # Workflow state
    state_data: Dict[str, Any] = field(default_factory=dict)
    
    # Equipment tracking
    equipment_used: List[Dict[str, Any]] = field(default_factory=list)
    inventory_updated: bool = False
    
    # Quality tracking
    completion_rating: Optional[int] = None
    feedback_comments: Optional[str] = None
    
    # Staff creation tracking fields
    created_by_staff: bool = False
    staff_creator_id: Optional[int] = None
    staff_creator_role: Optional[str] = None
    creation_source: str = "client"  # "client", "manager", "junior_manager", "controller", "call_center"
    client_notified_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'workflow_type': self.workflow_type,
            'client_id': self.client_id,
            'role_current': self.role_current,
            'current_status': self.current_status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'priority': self.priority,
            'description': self.description,
            'location': self.location,
            'contact_info': self.contact_info,
            'state_data': self.state_data,
            'equipment_used': self.equipment_used,
            'inventory_updated': self.inventory_updated,
            'completion_rating': self.completion_rating,
            'feedback_comments': self.feedback_comments,
            'created_by_staff': self.created_by_staff,
            'staff_creator_id': self.staff_creator_id,
            'staff_creator_role': self.staff_creator_role,
            'creation_source': self.creation_source,
            'client_notified_at': self.client_notified_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceRequest':
        return cls(**data)

@dataclass
class StateTransition:
    id: Optional[int] = None
    request_id: Optional[str] = None
    from_role: Optional[str] = None
    to_role: Optional[str] = None
    action: Optional[str] = None
    actor_id: Optional[int] = None
    transition_data: Dict[str, Any] = field(default_factory=dict)
    comments: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'request_id': self.request_id,
            'from_role': self.from_role,
            'to_role': self.to_role,
            'action': self.action,
            'actor_id': self.actor_id,
            'transition_data': self.transition_data,
            'comments': self.comments,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateTransition':
        return cls(**data)

@dataclass
class WorkflowStep:
    role: str
    actions: List[str]
    next_steps: Dict[str, str] = field(default_factory=dict)  # action -> next_role mapping
    required_data: List[str] = field(default_factory=list)
    optional_data: List[str] = field(default_factory=list)

@dataclass
class WorkflowDefinition:
    name: str
    initial_role: str
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    completion_actions: List[str] = field(default_factory=list)

@dataclass
class WorkflowStatus:
    request_id: str
    role_current: str
    current_status: str
    available_actions: List[str]
    next_roles: List[str]
    history: List[StateTransition] = field(default_factory=list)

@dataclass
class ClientSelectionData:
    """Model for client selection during staff application creation"""
    id: Optional[int] = None
    search_method: str = "phone"  # "phone", "name", "id", "new"
    search_value: Optional[str] = None
    client_id: Optional[int] = None
    new_client_data: Optional[Dict[str, Any]] = field(default_factory=dict)
    verified: bool = False
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'search_method': self.search_method,
            'search_value': self.search_value,
            'client_id': self.client_id,
            'new_client_data': self.new_client_data,
            'verified': self.verified,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClientSelectionData':
        return cls(**data)

@dataclass
class StaffApplicationAudit:
    """Model for auditing staff-created applications"""
    id: Optional[int] = None
    application_id: Optional[str] = None
    creator_id: Optional[int] = None
    creator_role: Optional[str] = None
    client_id: Optional[int] = None
    application_type: Optional[str] = None  # "connection_request", "technical_service"
    creation_timestamp: Optional[datetime] = None
    client_notified: bool = False
    client_notified_at: Optional[datetime] = None
    workflow_initiated: bool = False
    workflow_initiated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Additional audit fields
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'application_id': self.application_id,
            'creator_id': self.creator_id,
            'creator_role': self.creator_role,
            'client_id': self.client_id,
            'application_type': self.application_type,
            'creation_timestamp': self.creation_timestamp,
            'client_notified': self.client_notified,
            'client_notified_at': self.client_notified_at,
            'workflow_initiated': self.workflow_initiated,
            'workflow_initiated_at': self.workflow_initiated_at,
            'metadata': self.metadata,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StaffApplicationAudit':
        return cls(**data)

# Utility functions for models
def get_status_display(status: str, language: str = 'ru') -> str:
    """Get display text for status"""
    status_map = {
        'new': {'uz': 'Yangi', 'ru': 'Новая'},
        'cancelled': {'uz': 'Bekor qilindi', 'ru': 'Отменена'},
        'closed': {'uz': 'Yopilgan', 'ru': 'Закрыта'},
        'pending_junior_manager': {'uz': 'Kichik menejerga yuborish', 'ru': 'Ожидает младшего менеджера'},
        'assigned_to_junior_manager': {'uz': 'Kichik menejerga tayinlangan', 'ru': 'Назначено младшему менеджеру'},
        'pending_controller': {'uz': 'Nazoratchiga yuborish', 'ru': 'Ожидает контролера'},
        'assigned_to_technician': {'uz': 'Texnikga tayinlangan', 'ru': 'Назначено технику'},
        'technician_in_progress': {'uz': 'Texnik ishlamoqda', 'ru': 'Техник в работе'},
        'pending_warehouse_confirmation': {'uz': 'Ombor tasdiqlashini kutmoqda', 'ru': 'Ожидает подтверждения склада'},
        'technician_completed': {'uz': 'Texnik yakunladi', 'ru': 'Техник завершил'},
        'warehouse_confirmed': {'uz': 'Ombor tasdiqladi', 'ru': 'Склад подтвердил'},
        'assigned_to_call_center': {'uz': 'Call-markazga tayinlangan', 'ru': 'Назначено call-центру'},
        'call_center_in_progress': {'uz': 'Call-markaz ishlamoqda', 'ru': 'Call-центр в работе'},
        'call_center_completed': {'uz': 'Call-markaz yakunladi', 'ru': 'Call-центр завершил'},
        'pending_feedback': {'uz': 'Fikr-mulohaza kutilmoqda', 'ru': 'Ожидается обратная связь'}
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
        'blocked': {'uz': 'Bloklangan', 'ru': 'Заблокирован'},
        'junior_manager': {'uz': 'Kichik menejer', 'ru': 'Младший менеджер'},
        'call_center_supervisor': {'uz': 'Call-markaz nazoratchisi', 'ru': 'Руководитель call-центра'}
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
    ServiceRequest = ServiceRequest
    StateTransition = StateTransition
    WorkflowStep = WorkflowStep
    WorkflowDefinition = WorkflowDefinition
    WorkflowStatus = WorkflowStatus
    ClientSelectionData = ClientSelectionData
    StaffApplicationAudit = StaffApplicationAudit

# Utility functions for models
def validate_staff_creation_data(service_request: ServiceRequest) -> List[str]:
    """Validate staff creation tracking data"""
    errors = []
    
    if service_request.created_by_staff:
        if not service_request.staff_creator_id:
            errors.append("staff_creator_id is required when created_by_staff is True")
        if not service_request.staff_creator_role:
            errors.append("staff_creator_role is required when created_by_staff is True")
        elif service_request.staff_creator_role not in ModelConstants.USER_ROLES:
            errors.append(f"Invalid staff_creator_role: {service_request.staff_creator_role}")
    
    if service_request.creation_source not in ModelConstants.CREATION_SOURCES:
        errors.append(f"Invalid creation_source: {service_request.creation_source}")
    
    return errors

def validate_client_selection_data(client_data: ClientSelectionData) -> List[str]:
    """Validate client selection data"""
    errors = []
    
    if client_data.search_method not in ModelConstants.SEARCH_METHODS:
        errors.append(f"Invalid search_method: {client_data.search_method}")
    
    if client_data.search_method != "new" and not client_data.search_value:
        errors.append("search_value is required for non-new search methods")
    
    if client_data.search_method == "new" and not client_data.new_client_data:
        errors.append("new_client_data is required when search_method is 'new'")
    
    return errors

# Constants
class ModelConstants:
    """Model-related constants"""
    
    USER_ROLES = [role.value for role in UserRole]
    ZAYAVKA_STATUSES = [status.value for status in ZayavkaStatus]
    PRIORITIES = [priority.value for priority in Priority]
    
    # Workflow constants
    WORKFLOW_TYPES = [wf_type.value for wf_type in WorkflowType]
    REQUEST_STATUSES = [status.value for status in RequestStatus]
    WORKFLOW_ACTIONS = [action.value for action in WorkflowAction]
    
    # Staff creation constants
    CREATION_SOURCES = ["client", "manager", "junior_manager", "controller", "call_center"]
    SEARCH_METHODS = ["phone", "name", "id", "new"]
    APPLICATION_TYPES = ["connection_request", "technical_service"]
    
    DEFAULT_LANGUAGE = "uz"
    DEFAULT_ROLE = UserRole.CLIENT.value
    DEFAULT_STATUS = ZayavkaStatus.NEW.value
    DEFAULT_PRIORITY = Priority.MEDIUM.value
    DEFAULT_WORKFLOW_TYPE = WorkflowType.CONNECTION_REQUEST.value
    DEFAULT_REQUEST_STATUS = RequestStatus.CREATED.value
    DEFAULT_CREATION_SOURCE = "client"
    DEFAULT_SEARCH_METHOD = "phone"
    
    # Validation constants
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_PHONE_LENGTH = 20
    MAX_ADDRESS_LENGTH = 500
    
    # Rating constants
    MIN_RATING = 1
    MAX_RATING = 5
