"""
Audit logging system for staff application creation.
Implements Requirements 6.1, 6.2, 6.3, 6.4 from multi-role application creation spec.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import uuid

from database.models import StaffApplicationAudit, UserRole
from database.staff_creation_queries import (
    create_staff_application_audit,
    get_staff_application_audits,
    get_audit_by_application_id
)
from utils.logger import setup_module_logger

logger = setup_module_logger("audit_logger")

class AuditEventType(Enum):
    """Types of audit events"""
    APPLICATION_CREATED = "application_created"
    CLIENT_NOTIFIED = "client_notified"
    WORKFLOW_INITIATED = "workflow_initiated"
    PERMISSION_DENIED = "permission_denied"
    VALIDATION_FAILED = "validation_failed"
    CLIENT_SELECTED = "client_selected"
    CLIENT_CREATED = "client_created"
    APPLICATION_SUBMITTED = "application_submitted"
    ERROR_OCCURRED = "error_occurred"

class AuditSeverity(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Individual audit event"""
    event_type: str
    severity: str
    timestamp: datetime
    creator_id: int
    creator_role: str
    application_id: Optional[str] = None
    client_id: Optional[int] = None
    application_type: Optional[str] = None
    event_data: Dict[str, Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.event_data is None:
            self.event_data = {}

@dataclass
class AuditSummary:
    """Summary of audit activities"""
    total_applications: int
    applications_by_role: Dict[str, int]
    applications_by_type: Dict[str, int]
    success_rate: float
    error_count: int
    most_active_creator: Optional[Dict[str, Any]]
    time_period: Dict[str, datetime]

class StaffApplicationAuditLogger:
    """Main audit logger for staff application creation"""
    
    def __init__(self):
        self.logger = logger
        self._event_queue = None
        self._processing_task = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure the logger is initialized with event loop"""
        if not self._initialized:
            self._event_queue = asyncio.Queue()
            self._start_processing()
            self._initialized = True
    
    def _start_processing(self):
        """Start background task for processing audit events"""
        try:
            if self._processing_task is None or self._processing_task.done():
                self._processing_task = asyncio.create_task(self._process_events())
        except RuntimeError:
            # No event loop running, will be initialized later
            pass
    
    async def _process_events(self):
        """Background task to process audit events"""
        while True:
            try:
                event = await self._event_queue.get()
                await self._store_audit_event(event)
                self._event_queue.task_done()
            except Exception as e:
                self.logger.error(f"Error processing audit event: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing
    
    async def _store_audit_event(self, event: AuditEvent):
        """Store audit event in database"""
        try:
            audit = StaffApplicationAudit(
                application_id=event.application_id,
                creator_id=event.creator_id,
                creator_role=event.creator_role,
                client_id=event.client_id,
                application_type=event.application_type,
                creation_timestamp=event.timestamp,
                metadata={
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'event_data': event.event_data
                },
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                session_id=event.session_id
            )
            
            audit_id = await create_staff_application_audit(audit)
            if audit_id:
                self.logger.debug(f"Stored audit event {event.event_type} with ID {audit_id}")
            else:
                self.logger.error(f"Failed to store audit event {event.event_type}")
                
        except Exception as e:
            self.logger.error(f"Error storing audit event: {e}")
    
    def _generate_session_id(self, creator_id: int, timestamp: datetime) -> str:
        """Generate unique session ID"""
        data = f"{creator_id}_{timestamp.isoformat()}_{uuid.uuid4()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    async def log_application_creation_start(self, 
                                           creator_id: int, 
                                           creator_role: str,
                                           application_type: str,
                                           client_id: Optional[int] = None,
                                           **context) -> str:
        """
        Log the start of application creation process.
        
        Args:
            creator_id: ID of staff member creating application
            creator_role: Role of staff member
            application_type: Type of application being created
            client_id: ID of client (if known)
            **context: Additional context data
            
        Returns:
            str: Session ID for tracking this creation session
        """
        await self._ensure_initialized()
        
        timestamp = datetime.utcnow()
        session_id = self._generate_session_id(creator_id, timestamp)
        
        event = AuditEvent(
            event_type=AuditEventType.APPLICATION_CREATED.value,
            severity=AuditSeverity.INFO.value,
            timestamp=timestamp,
            creator_id=creator_id,
            creator_role=creator_role,
            client_id=client_id,
            application_type=application_type,
            event_data={
                'action': 'creation_started',
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        self.logger.info(f"Application creation started by {creator_role} {creator_id} for {application_type}")
        return session_id
    
    async def log_client_selection(self,
                                 creator_id: int,
                                 creator_role: str,
                                 selection_method: str,
                                 search_value: Optional[str] = None,
                                 client_id: Optional[int] = None,
                                 session_id: Optional[str] = None,
                                 **context):
        """
        Log client selection during application creation.
        
        Args:
            creator_id: ID of staff member
            creator_role: Role of staff member
            selection_method: Method used to select client
            search_value: Value used for search
            client_id: Selected client ID
            session_id: Session ID for tracking
            **context: Additional context data
        """
        await self._ensure_initialized()
        
        event = AuditEvent(
            event_type=AuditEventType.CLIENT_SELECTED.value,
            severity=AuditSeverity.INFO.value,
            timestamp=datetime.utcnow(),
            creator_id=creator_id,
            creator_role=creator_role,
            client_id=client_id,
            event_data={
                'selection_method': selection_method,
                'search_value': search_value,
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        self.logger.info(f"Client selected by {creator_role} {creator_id}: method={selection_method}, client_id={client_id}")
    
    async def log_client_creation(self,
                                creator_id: int,
                                creator_role: str,
                                new_client_id: int,
                                client_data: Dict[str, Any],
                                session_id: Optional[str] = None,
                                **context):
        """
        Log creation of new client by staff.
        
        Args:
            creator_id: ID of staff member
            creator_role: Role of staff member
            new_client_id: ID of newly created client
            client_data: Client data (sanitized)
            session_id: Session ID for tracking
            **context: Additional context data
        """
        await self._ensure_initialized()
        
        # Sanitize client data for logging
        sanitized_data = {
            'phone': client_data.get('phone', '').replace(client_data.get('phone', '')[-4:], '****') if client_data.get('phone') else None,
            'name_length': len(client_data.get('full_name', '')),
            'has_address': bool(client_data.get('address')),
            'language': client_data.get('language')
        }
        
        event = AuditEvent(
            event_type=AuditEventType.CLIENT_CREATED.value,
            severity=AuditSeverity.INFO.value,
            timestamp=datetime.utcnow(),
            creator_id=creator_id,
            creator_role=creator_role,
            client_id=new_client_id,
            event_data={
                'client_data': sanitized_data,
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        self.logger.info(f"New client created by {creator_role} {creator_id}: client_id={new_client_id}")
    
    async def log_application_submission(self,
                                       creator_id: int,
                                       creator_role: str,
                                       application_id: str,
                                       client_id: int,
                                       application_type: str,
                                       application_data: Dict[str, Any],
                                       session_id: Optional[str] = None,
                                       **context):
        """
        Log successful application submission.
        
        Args:
            creator_id: ID of staff member
            creator_role: Role of staff member
            application_id: ID of created application
            client_id: ID of client
            application_type: Type of application
            application_data: Application data (sanitized)
            session_id: Session ID for tracking
            **context: Additional context data
        """
        await self._ensure_initialized()
        
        # Sanitize application data for logging
        sanitized_data = {
            'description_length': len(application_data.get('description', '')),
            'has_location': bool(application_data.get('location')),
            'priority': application_data.get('priority'),
            'workflow_type': application_data.get('workflow_type')
        }
        
        event = AuditEvent(
            event_type=AuditEventType.APPLICATION_SUBMITTED.value,
            severity=AuditSeverity.INFO.value,
            timestamp=datetime.utcnow(),
            creator_id=creator_id,
            creator_role=creator_role,
            application_id=application_id,
            client_id=client_id,
            application_type=application_type,
            event_data={
                'application_data': sanitized_data,
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        self.logger.info(f"Application submitted by {creator_role} {creator_id}: {application_id}")
    
    async def log_client_notification(self,
                                    creator_id: int,
                                    creator_role: str,
                                    application_id: str,
                                    client_id: int,
                                    notification_method: str,
                                    success: bool,
                                    session_id: Optional[str] = None,
                                    **context):
        """
        Log client notification attempt.
        
        Args:
            creator_id: ID of staff member
            creator_role: Role of staff member
            application_id: ID of application
            client_id: ID of client
            notification_method: Method used for notification
            success: Whether notification was successful
            session_id: Session ID for tracking
            **context: Additional context data
        """
        await self._ensure_initialized()
        
        event = AuditEvent(
            event_type=AuditEventType.CLIENT_NOTIFIED.value,
            severity=AuditSeverity.INFO.value if success else AuditSeverity.WARNING.value,
            timestamp=datetime.utcnow(),
            creator_id=creator_id,
            creator_role=creator_role,
            application_id=application_id,
            client_id=client_id,
            event_data={
                'notification_method': notification_method,
                'success': success,
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        status = "successful" if success else "failed"
        self.logger.info(f"Client notification {status} for application {application_id}")
    
    async def log_workflow_initiation(self,
                                    creator_id: int,
                                    creator_role: str,
                                    application_id: str,
                                    workflow_type: str,
                                    initial_role: str,
                                    session_id: Optional[str] = None,
                                    **context):
        """
        Log workflow initiation for staff-created application.
        
        Args:
            creator_id: ID of staff member
            creator_role: Role of staff member
            application_id: ID of application
            workflow_type: Type of workflow
            initial_role: Initial role in workflow
            session_id: Session ID for tracking
            **context: Additional context data
        """
        await self._ensure_initialized()
        
        event = AuditEvent(
            event_type=AuditEventType.WORKFLOW_INITIATED.value,
            severity=AuditSeverity.INFO.value,
            timestamp=datetime.utcnow(),
            creator_id=creator_id,
            creator_role=creator_role,
            application_id=application_id,
            event_data={
                'workflow_type': workflow_type,
                'initial_role': initial_role,
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        self.logger.info(f"Workflow initiated for application {application_id}: {workflow_type}")
    
    async def log_permission_denied(self,
                                  creator_id: int,
                                  creator_role: str,
                                  attempted_action: str,
                                  reason: str,
                                  session_id: Optional[str] = None,
                                  **context):
        """
        Log permission denied events.
        
        Args:
            creator_id: ID of staff member
            creator_role: Role of staff member
            attempted_action: Action that was attempted
            reason: Reason for denial
            session_id: Session ID for tracking
            **context: Additional context data
        """
        await self._ensure_initialized()
        
        event = AuditEvent(
            event_type=AuditEventType.PERMISSION_DENIED.value,
            severity=AuditSeverity.WARNING.value,
            timestamp=datetime.utcnow(),
            creator_id=creator_id,
            creator_role=creator_role,
            event_data={
                'attempted_action': attempted_action,
                'reason': reason,
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        self.logger.warning(f"Permission denied for {creator_role} {creator_id}: {attempted_action} - {reason}")
    
    async def log_validation_error(self,
                                 creator_id: int,
                                 creator_role: str,
                                 validation_errors: List[str],
                                 form_data: Dict[str, Any],
                                 session_id: Optional[str] = None,
                                 **context):
        """
        Log validation errors during application creation.
        
        Args:
            creator_id: ID of staff member
            creator_role: Role of staff member
            validation_errors: List of validation error messages
            form_data: Form data that failed validation (sanitized)
            session_id: Session ID for tracking
            **context: Additional context data
        """
        await self._ensure_initialized()
        
        # Sanitize form data
        sanitized_form_data = {
            'field_count': len(form_data),
            'has_description': bool(form_data.get('description')),
            'has_location': bool(form_data.get('location')),
            'has_client_info': bool(form_data.get('client_id') or form_data.get('client_data'))
        }
        
        event = AuditEvent(
            event_type=AuditEventType.VALIDATION_FAILED.value,
            severity=AuditSeverity.WARNING.value,
            timestamp=datetime.utcnow(),
            creator_id=creator_id,
            creator_role=creator_role,
            event_data={
                'validation_errors': validation_errors,
                'form_data': sanitized_form_data,
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        self.logger.warning(f"Validation failed for {creator_role} {creator_id}: {len(validation_errors)} errors")
    
    async def log_error(self,
                       creator_id: int,
                       creator_role: str,
                       error_type: str,
                       error_message: str,
                       application_id: Optional[str] = None,
                       session_id: Optional[str] = None,
                       **context):
        """
        Log errors during application creation process.
        
        Args:
            creator_id: ID of staff member
            creator_role: Role of staff member
            error_type: Type of error
            error_message: Error message
            application_id: ID of application (if applicable)
            session_id: Session ID for tracking
            **context: Additional context data
        """
        await self._ensure_initialized()
        
        event = AuditEvent(
            event_type=AuditEventType.ERROR_OCCURRED.value,
            severity=AuditSeverity.ERROR.value,
            timestamp=datetime.utcnow(),
            creator_id=creator_id,
            creator_role=creator_role,
            application_id=application_id,
            event_data={
                'error_type': error_type,
                'error_message': error_message,
                'context': context
            },
            session_id=session_id,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent')
        )
        
        await self._event_queue.put(event)
        
        self.logger.error(f"Error in application creation by {creator_role} {creator_id}: {error_type} - {error_message}")

# Global audit logger instance
audit_logger = StaffApplicationAuditLogger()

# Convenience functions for common audit operations
async def log_staff_application_created(creator_id: int, creator_role: str, application_id: str, 
                                      client_id: int, application_type: str, **context) -> str:
    """Convenience function to log application creation"""
    session_id = await audit_logger.log_application_creation_start(
        creator_id, creator_role, application_type, client_id, **context
    )
    
    # Extract application_data from context to avoid duplicate parameter
    application_data = context.pop('application_data', {})
    await audit_logger.log_application_submission(
        creator_id, creator_role, application_id, client_id, 
        application_type, application_data, session_id, **context
    )
    return session_id

async def log_staff_client_notification(creator_id: int, creator_role: str, application_id: str,
                                      client_id: int, success: bool, **context):
    """Convenience function to log client notification"""
    await audit_logger.log_client_notification(
        creator_id, creator_role, application_id, client_id, 
        context.get('notification_method', 'telegram'), success, **context
    )

async def log_staff_workflow_started(creator_id: int, creator_role: str, application_id: str,
                                   workflow_type: str, **context):
    """Convenience function to log workflow initiation"""
    await audit_logger.log_workflow_initiation(
        creator_id, creator_role, application_id, workflow_type,
        context.get('initial_role', 'manager'), **context
    )

async def log_staff_permission_error(creator_id: int, creator_role: str, action: str, reason: str, **context):
    """Convenience function to log permission errors"""
    await audit_logger.log_permission_denied(creator_id, creator_role, action, reason, **context)

async def log_staff_validation_error(creator_id: int, creator_role: str, errors: List[str], 
                                   form_data: Dict[str, Any], **context):
    """Convenience function to log validation errors"""
    await audit_logger.log_validation_error(creator_id, creator_role, errors, form_data, **context)

async def log_staff_error(creator_id: int, creator_role: str, error_type: str, 
                         error_message: str, **context):
    """Convenience function to log general errors"""
    await audit_logger.log_error(creator_id, creator_role, error_type, error_message, **context)