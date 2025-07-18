"""
Inbox system data models with validation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class InboxRole(Enum):
    """Valid roles for inbox system"""
    MANAGER = "manager"
    JUNIOR_MANAGER = "junior_manager"
    TECHNICIAN = "technician"
    WAREHOUSE = "warehouse"
    CALL_CENTER = "call_center"
    CALL_CENTER_SUPERVISOR = "call_center_supervisor"
    CONTROLLER = "controller"

class ApplicationType(Enum):
    """Valid application types for inbox system"""
    ZAYAVKA = "zayavka"
    SERVICE_REQUEST = "service_request"

class MessageType(Enum):
    """Valid message types for inbox system"""
    APPLICATION = "application"
    TRANSFER = "transfer"
    NOTIFICATION = "notification"
    REMINDER = "reminder"

class MessagePriority(Enum):
    """Valid message priorities"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class InboxMessage:
    """Model for inbox messages and notifications"""
    id: Optional[int] = None
    application_id: str = None
    application_type: str = None
    assigned_role: str = None
    message_type: str = MessageType.APPLICATION.value
    title: Optional[str] = None
    description: Optional[str] = None
    priority: str = MessagePriority.MEDIUM.value
    is_read: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate data after initialization"""
        self._validate()
    
    def _validate(self):
        """Validate inbox message data"""
        errors = []
        
        # Validate required fields
        if not self.application_id:
            errors.append("application_id is required")
        
        if not self.application_type:
            errors.append("application_type is required")
        elif self.application_type not in [t.value for t in ApplicationType]:
            errors.append(f"Invalid application_type: {self.application_type}")
        
        if not self.assigned_role:
            errors.append("assigned_role is required")
        elif self.assigned_role not in [r.value for r in InboxRole]:
            errors.append(f"Invalid assigned_role: {self.assigned_role}")
        
        # Validate enums
        if self.message_type not in [t.value for t in MessageType]:
            errors.append(f"Invalid message_type: {self.message_type}")
        
        if self.priority not in [p.value for p in MessagePriority]:
            errors.append(f"Invalid priority: {self.priority}")
        
        # Validate application_id format based on type
        if self.application_id and self.application_type:
            if self.application_type == ApplicationType.ZAYAVKA.value:
                if not self.application_id.isdigit():
                    errors.append("application_id must be numeric for zayavka type")
            elif self.application_type == ApplicationType.SERVICE_REQUEST.value:
                # UUID format validation (basic check)
                if len(self.application_id) != 36 or self.application_id.count('-') != 4:
                    errors.append("application_id must be UUID format for service_request type")
        
        # Validate string lengths
        if self.title and len(self.title) > 255:
            errors.append("title cannot exceed 255 characters")
        
        if self.description and len(self.description) > 2000:
            errors.append("description cannot exceed 2000 characters")
        
        if errors:
            raise ValueError(f"InboxMessage validation errors: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'application_type': self.application_type,
            'assigned_role': self.assigned_role,
            'message_type': self.message_type,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'is_read': self.is_read,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InboxMessage':
        """Create from dictionary"""
        return cls(**data)
    
    def mark_as_read(self):
        """Mark message as read"""
        self.is_read = True
        self.updated_at = datetime.now()
    
    def update_priority(self, new_priority: str):
        """Update message priority"""
        if new_priority not in [p.value for p in MessagePriority]:
            raise ValueError(f"Invalid priority: {new_priority}")
        self.priority = new_priority
        self.updated_at = datetime.now()

@dataclass
class ApplicationTransfer:
    """Model for application transfer audit trail"""
    id: Optional[int] = None
    application_id: str = None
    application_type: str = None
    from_role: Optional[str] = None
    to_role: str = None
    transferred_by: int = None
    transfer_reason: Optional[str] = None
    transfer_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate data after initialization"""
        self._validate()
    
    def _validate(self):
        """Validate application transfer data"""
        errors = []
        
        # Validate required fields
        if not self.application_id:
            errors.append("application_id is required")
        
        if not self.application_type:
            errors.append("application_type is required")
        elif self.application_type not in [t.value for t in ApplicationType]:
            errors.append(f"Invalid application_type: {self.application_type}")
        
        if not self.to_role:
            errors.append("to_role is required")
        elif self.to_role not in [r.value for r in InboxRole]:
            errors.append(f"Invalid to_role: {self.to_role}")
        
        if self.transferred_by is None:
            errors.append("transferred_by is required")
        elif not isinstance(self.transferred_by, int) or self.transferred_by <= 0:
            errors.append("transferred_by must be a positive integer")
        
        # Validate from_role if provided
        if self.from_role and self.from_role not in [r.value for r in InboxRole]:
            errors.append(f"Invalid from_role: {self.from_role}")
        
        # Validate that from_role and to_role are different
        if self.from_role and self.from_role == self.to_role:
            errors.append("from_role and to_role cannot be the same")
        
        # Validate application_id format based on type
        if self.application_id and self.application_type:
            if self.application_type == ApplicationType.ZAYAVKA.value:
                if not self.application_id.isdigit():
                    errors.append("application_id must be numeric for zayavka type")
            elif self.application_type == ApplicationType.SERVICE_REQUEST.value:
                # UUID format validation (basic check)
                if len(self.application_id) != 36 or self.application_id.count('-') != 4:
                    errors.append("application_id must be UUID format for service_request type")
        
        # Validate string lengths
        if self.transfer_reason and len(self.transfer_reason) > 255:
            errors.append("transfer_reason cannot exceed 255 characters")
        
        if self.transfer_notes and len(self.transfer_notes) > 2000:
            errors.append("transfer_notes cannot exceed 2000 characters")
        
        if errors:
            raise ValueError(f"ApplicationTransfer validation errors: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'application_type': self.application_type,
            'from_role': self.from_role,
            'to_role': self.to_role,
            'transferred_by': self.transferred_by,
            'transfer_reason': self.transfer_reason,
            'transfer_notes': self.transfer_notes,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationTransfer':
        """Create from dictionary"""
        return cls(**data)

# Utility functions for inbox models
def validate_role_transfer(from_role: str, to_role: str) -> List[str]:
    """
    Validate if a role transfer is allowed based on business rules
    Returns list of validation errors
    """
    errors = []
    
    # Basic role validation
    valid_roles = [r.value for r in InboxRole]
    if from_role and from_role not in valid_roles:
        errors.append(f"Invalid from_role: {from_role}")
    if to_role not in valid_roles:
        errors.append(f"Invalid to_role: {to_role}")
    
    if errors:
        return errors
    
    # Business rule validations
    # Define allowed transfer paths based on workflow requirements
    allowed_transfers = {
        InboxRole.MANAGER.value: [
            InboxRole.JUNIOR_MANAGER.value,
            InboxRole.CONTROLLER.value,
            InboxRole.CALL_CENTER.value
        ],
        InboxRole.JUNIOR_MANAGER.value: [
            InboxRole.MANAGER.value,
            InboxRole.CONTROLLER.value,
            InboxRole.CALL_CENTER.value
        ],
        InboxRole.CONTROLLER.value: [
            InboxRole.TECHNICIAN.value,
            InboxRole.MANAGER.value,
            InboxRole.JUNIOR_MANAGER.value
        ],
        InboxRole.TECHNICIAN.value: [
            InboxRole.WAREHOUSE.value,
            InboxRole.CONTROLLER.value,
            InboxRole.MANAGER.value
        ],
        InboxRole.WAREHOUSE.value: [
            InboxRole.TECHNICIAN.value,
            InboxRole.CONTROLLER.value
        ],
        InboxRole.CALL_CENTER.value: [
            InboxRole.CALL_CENTER_SUPERVISOR.value,
            InboxRole.MANAGER.value,
            InboxRole.JUNIOR_MANAGER.value
        ],
        InboxRole.CALL_CENTER_SUPERVISOR.value: [
            InboxRole.CALL_CENTER.value,
            InboxRole.MANAGER.value
        ]
    }
    
    # Check if transfer is allowed
    if from_role:
        allowed_targets = allowed_transfers.get(from_role, [])
        if to_role not in allowed_targets:
            errors.append(f"Transfer from {from_role} to {to_role} is not allowed")
    
    return errors

def get_role_display_name(role: str, language: str = 'ru') -> str:
    """Get display name for role in specified language"""
    role_names = {
        InboxRole.MANAGER.value: {
            'uz': 'Menejer',
            'ru': 'Менеджер'
        },
        InboxRole.JUNIOR_MANAGER.value: {
            'uz': 'Kichik menejer',
            'ru': 'Младший менеджер'
        },
        InboxRole.TECHNICIAN.value: {
            'uz': 'Texnik',
            'ru': 'Техник'
        },
        InboxRole.WAREHOUSE.value: {
            'uz': 'Ombor',
            'ru': 'Склад'
        },
        InboxRole.CALL_CENTER.value: {
            'uz': 'Call-markaz',
            'ru': 'Call-центр'
        },
        InboxRole.CALL_CENTER_SUPERVISOR.value: {
            'uz': 'Call-markaz nazoratchisi',
            'ru': 'Руководитель call-центра'
        },
        InboxRole.CONTROLLER.value: {
            'uz': 'Nazoratchi',
            'ru': 'Контролер'
        }
    }
    
    return role_names.get(role, {}).get(language, role)

def get_priority_display_name(priority: str, language: str = 'ru') -> str:
    """Get display name for priority in specified language"""
    priority_names = {
        MessagePriority.LOW.value: {
            'uz': 'Past',
            'ru': 'Низкий'
        },
        MessagePriority.MEDIUM.value: {
            'uz': "O'rta",
            'ru': 'Средний'
        },
        MessagePriority.HIGH.value: {
            'uz': 'Yuqori',
            'ru': 'Высокий'
        },
        MessagePriority.URGENT.value: {
            'uz': 'Shoshilinch',
            'ru': 'Срочный'
        }
    }
    
    return priority_names.get(priority, {}).get(language, priority)

def create_inbox_message_for_application(
    application_id: str,
    application_type: str,
    assigned_role: str,
    title: str = None,
    description: str = None,
    priority: str = MessagePriority.MEDIUM.value
) -> InboxMessage:
    """
    Create an inbox message for a new application
    """
    if not title:
        title = f"New {application_type.replace('_', ' ').title()}"
    
    if not description:
        description = f"A new {application_type.replace('_', ' ')} has been assigned to your role."
    
    return InboxMessage(
        application_id=application_id,
        application_type=application_type,
        assigned_role=assigned_role,
        message_type=MessageType.APPLICATION.value,
        title=title,
        description=description,
        priority=priority,
        created_at=datetime.now()
    )

def create_transfer_audit_record(
    application_id: str,
    application_type: str,
    from_role: Optional[str],
    to_role: str,
    transferred_by: int,
    reason: str = None,
    notes: str = None
) -> ApplicationTransfer:
    """
    Create an application transfer audit record
    """
    return ApplicationTransfer(
        application_id=application_id,
        application_type=application_type,
        from_role=from_role,
        to_role=to_role,
        transferred_by=transferred_by,
        transfer_reason=reason,
        transfer_notes=notes,
        created_at=datetime.now()
    )

# Constants for inbox system
class InboxConstants:
    """Constants for inbox system"""
    
    VALID_ROLES = [role.value for role in InboxRole]
    VALID_APPLICATION_TYPES = [app_type.value for app_type in ApplicationType]
    VALID_MESSAGE_TYPES = [msg_type.value for msg_type in MessageType]
    VALID_PRIORITIES = [priority.value for priority in MessagePriority]
    
    # Default values
    DEFAULT_MESSAGE_TYPE = MessageType.APPLICATION.value
    DEFAULT_PRIORITY = MessagePriority.MEDIUM.value
    
    # Validation limits
    MAX_TITLE_LENGTH = 255
    MAX_DESCRIPTION_LENGTH = 2000
    MAX_REASON_LENGTH = 255
    MAX_NOTES_LENGTH = 2000
    
    # UUID pattern for service requests
    UUID_PATTERN = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'