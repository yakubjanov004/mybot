"""
Role-Based Application Creation Handler

This module implements the RoleBasedApplicationHandler class that manages
application creation for different staff roles with appropriate permissions
and validation, integrating with the existing workflow engine and state management.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod

from database.models import (
    ServiceRequest, WorkflowType, RequestStatus, Priority, UserRole,
    ClientSelectionData, StaffApplicationAudit
)
from utils.role_permissions import (
    validate_comprehensive_permissions, get_role_permissions,
    ApplicationCreationPermissionError, ClientSelectionPermissionError,
    DailyLimitExceededError, RolePermissionError
)
from utils.workflow_engine import WorkflowEngine
from utils.state_manager import StateManager
from utils.notification_system import NotificationSystem
from utils.logger import setup_module_logger

logger = setup_module_logger("staff_application_creation")


# Exception classes for application creation errors
class ApplicationCreationError(Exception):
    """Base exception for application creation errors"""
    
    def __init__(self, creator_id: int, error_type: str, details: str, request_id: Optional[str] = None):
        self.creator_id = creator_id
        self.error_type = error_type
        self.details = details
        self.request_id = request_id
        super().__init__(f"Application creation failed: {error_type} - {details}")


class ClientValidationError(ApplicationCreationError):
    """Exception for client validation errors"""
    
    def __init__(self, creator_id: int, field: str, value: str, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        error_type = "client_validation_error"
        details = f"Client validation failed for {field}: {reason}"
        super().__init__(creator_id, error_type, details)


class WorkflowInitializationError(ApplicationCreationError):
    """Exception for workflow initialization errors"""
    
    def __init__(self, creator_id: int, workflow_type: str, reason: str, request_id: Optional[str] = None):
        self.workflow_type = workflow_type
        self.reason = reason
        error_type = "workflow_initialization_error"
        details = f"Failed to initialize {workflow_type} workflow: {reason}"
        super().__init__(creator_id, error_type, details, request_id)


class NotificationError(ApplicationCreationError):
    """Exception for notification errors"""
    
    def __init__(self, creator_id: int, notification_type: str, reason: str, request_id: Optional[str] = None):
        self.notification_type = notification_type
        self.reason = reason
        error_type = "notification_error"
        details = f"Failed to send {notification_type} notification: {reason}"
        super().__init__(creator_id, error_type, details, request_id)


class RoleBasedApplicationHandlerInterface(ABC):
    """Abstract interface for role-based application creation handler"""
    
    @abstractmethod
    async def start_application_creation(self, creator_role: str, creator_id: int, 
                                       application_type: str) -> Dict[str, Any]:
        """Initiates application creation process for a staff member"""
        pass
    
    @abstractmethod
    async def process_application_form(self, form_data: Dict[str, Any], 
                                     creator_context: Dict[str, Any]) -> Dict[str, Any]:
        """Processes application form data with validation"""
        pass
    
    @abstractmethod
    async def validate_and_submit(self, application_data: Dict[str, Any], 
                                creator_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and submits the application"""
        pass
    
    @abstractmethod
    async def notify_stakeholders(self, application_id: str, 
                                creator_context: Dict[str, Any]) -> bool:
        """Notifies relevant stakeholders about the created application"""
        pass


class RoleBasedApplicationHandler(RoleBasedApplicationHandlerInterface):
    """
    Handles application creation for different staff roles with appropriate 
    permissions and validation, integrating with existing workflow engine 
    and state management.
    """
    
    def __init__(self, workflow_engine: Optional[WorkflowEngine] = None,
                 state_manager: Optional[StateManager] = None,
                 notification_system: Optional[NotificationSystem] = None,
                 pool=None):
        """
        Initialize the handler with required dependencies.
        
        Args:
            workflow_engine: Workflow engine instance
            state_manager: State manager instance  
            notification_system: Notification system instance
            pool: Database connection pool
        """
        self.pool = pool
        self.workflow_engine = workflow_engine or self._get_workflow_engine()
        self.state_manager = state_manager or self._get_state_manager()
        self.notification_system = notification_system or self._get_notification_system()
        
        # Application type mapping
        self.application_type_mapping = {
            'connection_request': WorkflowType.CONNECTION_REQUEST.value,
            'technical_service': WorkflowType.TECHNICAL_SERVICE.value
        }
    
    def _get_pool(self):
        """Get database pool"""
        if self.pool:
            return self.pool
        try:
            from loader import bot
            return bot.db
        except ImportError:
            logger.error("No database pool available")
            return None
    
    def _get_workflow_engine(self) -> WorkflowEngine:
        """Get workflow engine instance"""
        if not hasattr(self, '_workflow_engine_instance'):
            from utils.workflow_engine import WorkflowEngineFactory
            self._workflow_engine_instance = WorkflowEngineFactory.create_workflow_engine(
                self._get_state_manager(), self._get_notification_system()
            )
        return self._workflow_engine_instance
    
    def _get_state_manager(self) -> StateManager:
        """Get state manager instance"""
        if not hasattr(self, '_state_manager_instance'):
            from utils.state_manager import StateManagerFactory
            self._state_manager_instance = StateManagerFactory.create_state_manager()
        return self._state_manager_instance
    
    def _get_notification_system(self) -> NotificationSystem:
        """Get notification system instance"""
        if not hasattr(self, '_notification_system_instance'):
            from utils.notification_system import NotificationSystemFactory
            self._notification_system_instance = NotificationSystemFactory.create_notification_system()
        return self._notification_system_instance
    
    async def start_application_creation(self, creator_role: str, creator_id: int, 
                                       application_type: str) -> Dict[str, Any]:
        """
        Initiates application creation process for a staff member.
        
        Args:
            creator_role: Role of the staff member creating the application
            creator_id: ID of the staff member
            application_type: Type of application to create
            
        Returns:
            Dictionary containing creation status and next steps
            
        Raises:
            ApplicationCreationPermissionError: If role doesn't have permission
            DailyLimitExceededError: If daily limit exceeded
        """
        try:
            logger.info(f"Starting application creation: role={creator_role}, "
                       f"creator_id={creator_id}, type={application_type}")
            
            # Get current daily count for the creator
            current_daily_count = await self._get_daily_application_count(creator_id)
            
            # Validate comprehensive permissions
            validate_comprehensive_permissions(
                role=creator_role,
                application_type=application_type,
                needs_client_selection=True,
                needs_client_creation=True,
                current_daily_count=current_daily_count
            )
            
            # Get role permissions for additional context
            permissions = get_role_permissions(creator_role)
            
            # Create creator context
            creator_context = {
                'creator_id': creator_id,
                'creator_role': creator_role,
                'application_type': application_type,
                'permissions': permissions.to_dict(),
                'daily_count': current_daily_count,
                'session_id': str(uuid.uuid4()),
                'started_at': datetime.now()
            }
            
            logger.info(f"Application creation initiated successfully for creator {creator_id}")
            
            return {
                'success': True,
                'creator_context': creator_context,
                'next_step': 'client_selection',
                'available_permissions': {
                    'can_select_client': permissions.can_select_client,
                    'can_create_client': permissions.can_create_client,
                    'can_assign_directly': permissions.can_assign_directly
                }
            }
            
        except (ApplicationCreationPermissionError, DailyLimitExceededError, 
                ClientSelectionPermissionError) as e:
            logger.warning(f"Permission denied for application creation: {e}")
            return {
                'success': False,
                'error_type': 'permission_denied',
                'error_message': str(e),
                'error_details': {
                    'role': creator_role,
                    'application_type': application_type,
                    'daily_count': current_daily_count
                }
            }
        except Exception as e:
            logger.error(f"Error starting application creation: {e}", exc_info=True)
            raise ApplicationCreationError(
                creator_id, "initialization_error", str(e)
            )
    
    async def process_application_form(self, form_data: Dict[str, Any], 
                                     creator_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes application form data with validation.
        
        Args:
            form_data: Application form data including client and application details
            creator_context: Context information about the creator
            
        Returns:
            Dictionary containing processing status and validated data
            
        Raises:
            ClientValidationError: If client data validation fails
            ApplicationCreationError: If form processing fails
        """
        try:
            creator_id = creator_context['creator_id']
            creator_role = creator_context['creator_role']
            application_type = creator_context['application_type']
            
            logger.info(f"Processing application form for creator {creator_id}")
            
            # Validate client data
            client_data = form_data.get('client_data', {})
            validated_client = await self._validate_client_data(client_data, creator_context)
            
            # Validate application data
            application_data = form_data.get('application_data', {})
            validated_application = await self._validate_application_data(
                application_data, application_type, creator_context
            )
            
            # Create processed form data
            processed_data = {
                'client_data': validated_client,
                'application_data': validated_application,
                'creator_context': creator_context,
                'validation_timestamp': datetime.now(),
                'form_valid': True
            }
            
            logger.info(f"Application form processed successfully for creator {creator_id}")
            
            return {
                'success': True,
                'processed_data': processed_data,
                'next_step': 'confirmation'
            }
            
        except ClientValidationError as e:
            logger.warning(f"Client validation failed: {e}")
            return {
                'success': False,
                'error_type': 'client_validation_error',
                'error_message': str(e),
                'error_details': {
                    'field': e.field,
                    'value': e.value,
                    'reason': e.reason
                }
            }
        except Exception as e:
            logger.error(f"Error processing application form: {e}", exc_info=True)
            raise ApplicationCreationError(
                creator_context['creator_id'], "form_processing_error", str(e)
            )
    
    async def validate_and_submit(self, application_data: Dict[str, Any], 
                                creator_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates and submits the application.
        
        Args:
            application_data: Complete application data
            creator_context: Context information about the creator
            
        Returns:
            Dictionary containing submission status and application ID
            
        Raises:
            WorkflowInitializationError: If workflow initialization fails
            ApplicationCreationError: If submission fails
        """
        try:
            creator_id = creator_context['creator_id']
            creator_role = creator_context['creator_role']
            application_type = creator_context['application_type']
            
            logger.info(f"Validating and submitting application for creator {creator_id}")
            
            # Final validation
            final_validation = await self._perform_final_validation(
                application_data, creator_context
            )
            
            if not final_validation['valid']:
                return {
                    'success': False,
                    'error_type': 'validation_error',
                    'error_message': 'Final validation failed',
                    'error_details': final_validation['errors']
                }
            
            # Create service request
            service_request = await self._create_service_request(
                application_data, creator_context
            )
            
            # Initialize workflow
            workflow_type = self.application_type_mapping[application_type]
            request_id = await self.workflow_engine.initiate_workflow(
                workflow_type, service_request.to_dict()
            )
            
            if not request_id:
                raise WorkflowInitializationError(
                    creator_id, workflow_type, "Failed to get request ID from workflow engine"
                )
            
            # Update service request with actual ID
            service_request.id = request_id
            
            # Create audit record
            await self._create_audit_record(service_request, creator_context)
            
            # Notify stakeholders
            notification_success = await self.notify_stakeholders(request_id, creator_context)
            
            logger.info(f"Application submitted successfully: {request_id}")
            
            return {
                'success': True,
                'application_id': request_id,
                'workflow_type': workflow_type,
                'client_id': service_request.client_id,
                'notification_sent': notification_success,
                'created_at': service_request.created_at
            }
            
        except WorkflowInitializationError as e:
            logger.error(f"Workflow initialization failed: {e}")
            return {
                'success': False,
                'error_type': 'workflow_error',
                'error_message': str(e),
                'error_details': {
                    'workflow_type': e.workflow_type,
                    'reason': e.reason
                }
            }
        except Exception as e:
            logger.error(f"Error validating and submitting application: {e}", exc_info=True)
            raise ApplicationCreationError(
                creator_context['creator_id'], "submission_error", str(e)
            )
    
    async def notify_stakeholders(self, application_id: str, 
                                creator_context: Dict[str, Any]) -> bool:
        """
        Notifies relevant stakeholders about the created application.
        
        Args:
            application_id: ID of the created application
            creator_context: Context information about the creator
            
        Returns:
            True if notifications sent successfully, False otherwise
        """
        try:
            creator_id = creator_context['creator_id']
            application_type = creator_context['application_type']
            
            logger.info(f"Sending notifications for application {application_id}")
            
            # Get the created service request
            service_request = await self.state_manager.get_request(application_id)
            if not service_request:
                logger.error(f"Service request {application_id} not found for notifications")
                return False
            
            notifications_sent = []
            
            # Notify client about staff-created application
            if service_request.client_id:
                client_notification_success = await self._notify_client_about_staff_creation(
                    service_request, creator_context
                )
                notifications_sent.append(('client', client_notification_success))
            
            # Notify staff about successful creation (confirmation)
            staff_notification_success = await self._notify_staff_confirmation(
                service_request, creator_context
            )
            notifications_sent.append(('staff_confirmation', staff_notification_success))
            
            # Workflow notifications are handled by the workflow engine automatically
            # when the workflow is initiated, so we don't need to send them here
            
            # Log notification results
            successful_notifications = [n for n in notifications_sent if n[1]]
            failed_notifications = [n for n in notifications_sent if not n[1]]
            
            logger.info(f"Notifications sent for application {application_id}: "
                       f"successful={len(successful_notifications)}, "
                       f"failed={len(failed_notifications)}")
            
            # Return True if at least one critical notification was sent
            return len(successful_notifications) > 0
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}", exc_info=True)
            raise NotificationError(
                creator_context['creator_id'], "stakeholder_notification", str(e), application_id
            )
    
    # Helper methods
    
    async def _get_daily_application_count(self, creator_id: int) -> int:
        """Get the number of applications created by the creator today"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return 0
        
        try:
            async with pool.acquire() as conn:
                query = """
                SELECT COUNT(*) as count
                FROM staff_application_audit
                WHERE creator_id = $1 
                AND DATE(creation_timestamp) = CURRENT_DATE
                """
                
                row = await conn.fetchrow(query, creator_id)
                return row['count'] if row else 0
                
        except Exception as e:
            logger.error(f"Error getting daily application count: {e}", exc_info=True)
            return 0
    
    async def _validate_client_data(self, client_data: Dict[str, Any], 
                                  creator_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate client data"""
        creator_id = creator_context['creator_id']
        
        # Required fields
        required_fields = ['phone', 'full_name']
        for field in required_fields:
            if not client_data.get(field):
                raise ClientValidationError(
                    creator_id, field, client_data.get(field, ''), 
                    f"Field {field} is required"
                )
        
        # Validate phone format (basic validation)
        phone = client_data['phone']
        if not phone.startswith('+') or len(phone) < 10:
            raise ClientValidationError(
                creator_id, 'phone', phone, 
                "Phone must start with + and be at least 10 digits"
            )
        
        # Validate name length
        full_name = client_data['full_name']
        if len(full_name) < 2 or len(full_name) > 100:
            raise ClientValidationError(
                creator_id, 'full_name', full_name,
                "Name must be between 2 and 100 characters"
            )
        
        return {
            'phone': phone.strip(),
            'full_name': full_name.strip(),
            'address': client_data.get('address', '').strip(),
            'additional_info': client_data.get('additional_info', '').strip()
        }
    
    async def _validate_application_data(self, application_data: Dict[str, Any], 
                                       application_type: str, 
                                       creator_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate application-specific data"""
        creator_id = creator_context['creator_id']
        
        # Common required fields
        if not application_data.get('description'):
            raise ClientValidationError(
                creator_id, 'description', '', 
                "Application description is required"
            )
        
        if not application_data.get('location'):
            raise ClientValidationError(
                creator_id, 'location', '', 
                "Service location is required"
            )
        
        # Validate description length
        description = application_data['description']
        if len(description) < 10 or len(description) > 1000:
            raise ClientValidationError(
                creator_id, 'description', description,
                "Description must be between 10 and 1000 characters"
            )
        
        validated_data = {
            'description': description.strip(),
            'location': application_data['location'].strip(),
            'priority': application_data.get('priority', Priority.MEDIUM.value),
            'additional_notes': application_data.get('additional_notes', '').strip()
        }
        
        # Application type specific validation
        if application_type == 'technical_service':
            if not application_data.get('issue_type'):
                raise ClientValidationError(
                    creator_id, 'issue_type', '', 
                    "Issue type is required for technical service requests"
                )
            validated_data['issue_type'] = application_data['issue_type']
        
        return validated_data
    
    async def _perform_final_validation(self, application_data: Dict[str, Any], 
                                      creator_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform final validation before submission"""
        errors = []
        
        # Check if all required data is present
        if not application_data.get('client_data'):
            errors.append("Client data is missing")
        
        if not application_data.get('application_data'):
            errors.append("Application data is missing")
        
        # Validate creator context
        required_context_fields = ['creator_id', 'creator_role', 'application_type']
        for field in required_context_fields:
            if not creator_context.get(field):
                errors.append(f"Creator context missing {field}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    async def _create_service_request(self, application_data: Dict[str, Any], 
                                    creator_context: Dict[str, Any]) -> ServiceRequest:
        """Create ServiceRequest object from application data"""
        client_data = application_data['client_data']
        app_data = application_data['application_data']
        
        # For staff-created applications, we need to handle client_id
        # In a real implementation, you would either:
        # 1. Look up existing client by phone/name
        # 2. Create new client record
        # For this implementation, we'll use a placeholder
        client_id = await self._resolve_client_id(client_data, creator_context)
        
        current_time = datetime.now()
        
        return ServiceRequest(
            id=None,  # Will be set by workflow engine
            workflow_type=self.application_type_mapping[creator_context['application_type']],
            client_id=client_id,
            role_current=None,  # Will be set by workflow engine
            current_status=RequestStatus.CREATED.value,
            created_at=current_time,
            updated_at=current_time,
            priority=app_data.get('priority', Priority.MEDIUM.value),
            description=app_data['description'],
            location=app_data['location'],
            contact_info={
                'phone': client_data['phone'],
                'full_name': client_data['full_name'],
                'address': client_data.get('address', ''),
                'additional_info': client_data.get('additional_info', '')
            },
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': creator_context['creator_id'],
                    'creator_role': creator_context['creator_role'],
                    'session_id': creator_context['session_id']
                },
                'application_details': app_data,
                'created_by_role': creator_context['creator_role']
            },
            equipment_used=[],
            inventory_updated=False,
            completion_rating=None,
            feedback_comments=None,
            # Staff creation tracking fields
            created_by_staff=True,
            staff_creator_id=creator_context['creator_id'],
            staff_creator_role=creator_context['creator_role'],
            creation_source=creator_context['creator_role'],
            client_notified_at=None  # Will be set when client is notified
        )
    
    async def _resolve_client_id(self, client_data: Dict[str, Any], 
                                creator_context: Dict[str, Any]) -> int:
        """
        Resolve client ID by looking up existing client or creating new one.
        This is a simplified implementation - in production you would have
        proper client management with search and creation capabilities.
        """
        # For this implementation, we'll return a placeholder client ID
        # In production, this would:
        # 1. Search for existing client by phone number
        # 2. If found, return existing client ID
        # 3. If not found and creator has permission, create new client
        # 4. Return the client ID
        
        # Placeholder implementation
        return 1  # This should be replaced with actual client resolution logic
    
    async def _create_audit_record(self, service_request: ServiceRequest, 
                                 creator_context: Dict[str, Any]) -> bool:
        """Create audit record for staff-created application"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available for audit")
            return False
        
        try:
            audit_record = StaffApplicationAudit(
                application_id=service_request.id,
                creator_id=creator_context['creator_id'],
                creator_role=creator_context['creator_role'],
                client_id=service_request.client_id,
                application_type=creator_context['application_type'],
                creation_timestamp=datetime.now(),
                client_notified=False,  # Will be updated when client is notified
                workflow_initiated=True,
                metadata={
                    'session_id': creator_context['session_id'],
                    'permissions': creator_context.get('permissions', {}),
                    'application_data': service_request.state_data
                }
            )
            
            async with pool.acquire() as conn:
                query = """
                INSERT INTO staff_application_audit (
                    application_id, creator_id, creator_role, client_id, application_type,
                    creation_timestamp, client_notified, workflow_initiated, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                
                await conn.execute(
                    query,
                    audit_record.application_id,
                    audit_record.creator_id,
                    audit_record.creator_role,
                    audit_record.client_id,
                    audit_record.application_type,
                    audit_record.creation_timestamp,
                    audit_record.client_notified,
                    audit_record.workflow_initiated,
                    audit_record.metadata
                )
            
            logger.info(f"Created audit record for application {service_request.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating audit record: {e}", exc_info=True)
            return False
    
    async def _notify_client_about_staff_creation(self, service_request: ServiceRequest, 
                                                creator_context: Dict[str, Any]) -> bool:
        """Notify client about application created on their behalf"""
        try:
            # This would integrate with the notification system to send
            # a message to the client informing them that an application
            # was created on their behalf
            
            # For now, we'll log the notification
            logger.info(f"Would notify client {service_request.client_id} about "
                       f"staff-created application {service_request.id}")
            
            # In production, this would:
            # 1. Get client contact information
            # 2. Send notification via appropriate channel (Telegram, SMS, etc.)
            # 3. Update audit record with notification status
            
            return True
            
        except Exception as e:
            logger.error(f"Error notifying client: {e}", exc_info=True)
            return False
    
    async def _notify_staff_confirmation(self, service_request: ServiceRequest, 
                                       creator_context: Dict[str, Any]) -> bool:
        """Send confirmation notification to staff member"""
        try:
            # This would send a confirmation message to the staff member
            # who created the application
            
            logger.info(f"Would send confirmation to staff {creator_context['creator_id']} "
                       f"for application {service_request.id}")
            
            # In production, this would:
            # 1. Get staff member's contact information
            # 2. Send confirmation message with application details
            # 3. Include application ID and next steps
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending staff confirmation: {e}", exc_info=True)
            return False


class RoleBasedApplicationHandlerFactory:
    """Factory for creating role-based application handler instances"""
    
    @staticmethod
    def create_handler(workflow_engine: Optional[WorkflowEngine] = None,
                      state_manager: Optional[StateManager] = None,
                      notification_system: Optional[NotificationSystem] = None,
                      pool=None) -> RoleBasedApplicationHandler:
        """Creates a new role-based application handler instance"""
        return RoleBasedApplicationHandler(
            workflow_engine=workflow_engine,
            state_manager=state_manager,
            notification_system=notification_system,
            pool=pool
        )


# Convenience function for getting handler instance
def get_role_based_application_handler() -> RoleBasedApplicationHandler:
    """Get a role-based application handler instance"""
    return RoleBasedApplicationHandlerFactory.create_handler()