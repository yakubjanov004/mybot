from datetime import datetime
from database.models import ZayavkaStatus, UserRole, WorkflowType, WorkflowAction
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory

class WorkflowManager:
    """Legacy workflow manager - maintained for backward compatibility"""
    
    def __init__(self, db_queries):
        self.db_queries = db_queries
        # Initialize new workflow engine components
        self.state_manager = StateManagerFactory.create_state_manager()
        self.workflow_engine = WorkflowEngineFactory.create_workflow_engine(
            self.state_manager
        )

    async def get_next_status(self, zayavka_id, action, user_role):
        """Legacy method for backward compatibility"""
        zayavka = await self.db_queries.get_zayavka(zayavka_id)
        if not zayavka:
            return None

        current_status = zayavka.status
        zayavka_type = getattr(zayavka, 'zayavka_type', 'ul')  # Default to connection request

        if zayavka_type == 'ul':  # Connection request
            return self._get_next_status_ul(current_status, action, user_role)
        elif zayavka_type == 'tx':  # Technical service request
            return self._get_next_status_tx(current_status, action, user_role)

        return None

    def _get_next_status_ul(self, current_status, action, user_role):
        """Legacy logic for connection request workflow"""
        if user_role == UserRole.MANAGER.value and action == 'assign_to_junior':
            return ZayavkaStatus.PENDING_JUNIOR_MANAGER.value
        elif user_role == UserRole.JUNIOR_MANAGER.value and action == 'forward_to_controller':
            return ZayavkaStatus.PENDING_CONTROLLER.value
        elif user_role == UserRole.CONTROLLER.value and action == 'assign_to_technician':
            return ZayavkaStatus.ASSIGNED_TO_TECHNICIAN.value
        elif user_role == UserRole.TECHNICIAN.value and action == 'start_work':
            return ZayavkaStatus.TECHNICIAN_IN_PROGRESS.value
        elif user_role == UserRole.TECHNICIAN.value and action == 'request_warehouse':
            return ZayavkaStatus.PENDING_WAREHOUSE_CONFIRMATION.value
        elif user_role == UserRole.WAREHOUSE.value and action == 'confirm_materials':
            return ZayavkaStatus.WAREHOUSE_CONFIRMED.value
        elif user_role == UserRole.TECHNICIAN.value and action == 'complete_work':
            return ZayavkaStatus.TECHNICIAN_COMPLETED.value
        elif action == 'request_feedback':
            return ZayavkaStatus.PENDING_FEEDBACK.value
        elif action == 'close_request':
            return ZayavkaStatus.CLOSED.value
        
        return None

    def _get_next_status_tx(self, current_status, action, user_role):
        """Legacy logic for technical service request workflow"""
        if user_role == UserRole.CONTROLLER.value and action == 'assign_to_technician':
            return ZayavkaStatus.ASSIGNED_TO_TECHNICIAN.value
        elif user_role == UserRole.TECHNICIAN.value and action == 'start_diagnostics':
            return ZayavkaStatus.TECHNICIAN_IN_PROGRESS.value
        elif user_role == UserRole.TECHNICIAN.value and action == 'request_warehouse':
            return ZayavkaStatus.PENDING_WAREHOUSE_CONFIRMATION.value
        elif user_role == UserRole.WAREHOUSE.value and action == 'prepare_equipment':
            return ZayavkaStatus.WAREHOUSE_CONFIRMED.value
        elif user_role == UserRole.TECHNICIAN.value and action == 'complete_service':
            return ZayavkaStatus.TECHNICIAN_COMPLETED.value
        elif action == 'request_feedback':
            return ZayavkaStatus.PENDING_FEEDBACK.value
        elif action == 'close_request':
            return ZayavkaStatus.CLOSED.value
        
        return None
    
    # New enhanced workflow methods
    async def initiate_enhanced_workflow(self, workflow_type: str, request_data: dict) -> str:
        """Initiates a new enhanced workflow"""
        return await self.workflow_engine.initiate_workflow(workflow_type, request_data)
    
    async def process_workflow_transition(self, request_id: str, action: str, actor_role: str, data: dict) -> bool:
        """Processes workflow transition using enhanced engine"""
        return await self.workflow_engine.transition_workflow(request_id, action, actor_role, data)
    
    async def get_workflow_status(self, request_id: str):
        """Gets current workflow status"""
        return await self.workflow_engine.get_workflow_status(request_id)
    
    async def get_requests_for_role(self, role: str, status_filter: str = None):
        """Gets requests assigned to specific role"""
        return await self.state_manager.get_requests_by_role(role, status_filter)
    
    async def get_client_requests(self, client_id: int):
        """Gets all requests for specific client"""
        return await self.state_manager.get_requests_by_client(client_id)


class EnhancedWorkflowManager:
    """New enhanced workflow manager for the workflow system"""
    
    def __init__(self, notification_system=None, inventory_manager=None):
        self.state_manager = StateManagerFactory.create_state_manager()
        self.notification_system = notification_system
        self.inventory_manager = inventory_manager
        self.workflow_engine = WorkflowEngineFactory.create_workflow_engine(
            self.state_manager, notification_system, inventory_manager
        )
    
    async def create_connection_request(self, client_id: int, description: str, location: str, contact_info: dict) -> str:
        """Creates a new connection request workflow"""
        request_data = {
            'client_id': client_id,
            'description': description,
            'location': location,
            'contact_info': contact_info,
            'priority': 'medium'
        }
        
        return await self.workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, request_data
        )
    
    async def create_technical_request(self, client_id: int, description: str, issue_type: str) -> str:
        """Creates a new technical service request workflow"""
        request_data = {
            'client_id': client_id,
            'description': description,
            'issue_type': issue_type,
            'priority': 'medium'
        }
        
        return await self.workflow_engine.initiate_workflow(
            WorkflowType.TECHNICAL_SERVICE.value, request_data
        )
    
    async def create_call_center_request(self, client_info: dict, issue_description: str) -> str:
        """Creates a new call center direct resolution request"""
        request_data = {
            'client_info': client_info,
            'issue_description': issue_description,
            'priority': 'medium'
        }
        
        return await self.workflow_engine.initiate_workflow(
            WorkflowType.CALL_CENTER_DIRECT.value, request_data
        )
    
    async def assign_to_junior_manager(self, request_id: str, junior_manager_id: int, actor_id: int) -> bool:
        """Assigns connection request to junior manager"""
        data = {
            'junior_manager_id': junior_manager_id,
            'actor_id': actor_id
        }
        
        return await self.workflow_engine.transition_workflow(
            request_id, WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value, UserRole.MANAGER.value, data
        )
    
    async def call_client_and_forward(self, request_id: str, call_notes: str, actor_id: int, additional_comments: str = None) -> bool:
        """Junior manager calls client and forwards to controller"""
        # First, record the call
        call_data = {
            'call_notes': call_notes,
            'actor_id': actor_id,
            'additional_comments': additional_comments
        }
        
        call_success = await self.workflow_engine.transition_workflow(
            request_id, WorkflowAction.CALL_CLIENT.value, UserRole.JUNIOR_MANAGER.value, call_data
        )
        
        if call_success:
            # Then forward to controller
            forward_data = {
                'call_notes': call_notes,
                'additional_comments': additional_comments,
                'actor_id': actor_id
            }
            
            return await self.workflow_engine.transition_workflow(
                request_id, WorkflowAction.FORWARD_TO_CONTROLLER.value, UserRole.JUNIOR_MANAGER.value, forward_data
            )
        
        return False
    
    async def assign_to_technician(self, request_id: str, technician_id: int, actor_id: int) -> bool:
        """Assigns request to technician"""
        data = {
            'technician_id': technician_id,
            'actor_id': actor_id
        }
        
        return await self.workflow_engine.transition_workflow(
            request_id, WorkflowAction.ASSIGN_TO_TECHNICIAN.value, UserRole.CONTROLLER.value, data
        )
    
    async def start_installation(self, request_id: str, actor_id: int, installation_notes: str = None) -> bool:
        """Technician starts installation work"""
        data = {
            'actor_id': actor_id,
            'installation_notes': installation_notes,
            'started_at': str(datetime.now())
        }
        
        return await self.workflow_engine.transition_workflow(
            request_id, WorkflowAction.START_INSTALLATION.value, UserRole.TECHNICIAN.value, data
        )
    
    async def document_equipment_usage(self, request_id: str, equipment_used: list, installation_notes: str, actor_id: int) -> bool:
        """Technician documents equipment usage and forwards to warehouse"""
        data = {
            'equipment_used': equipment_used,
            'installation_notes': installation_notes,
            'actor_id': actor_id
        }
        
        return await self.workflow_engine.transition_workflow(
            request_id, WorkflowAction.DOCUMENT_EQUIPMENT.value, UserRole.TECHNICIAN.value, data
        )
    
    async def update_inventory_and_close(self, request_id: str, inventory_updates: dict, actor_id: int) -> bool:
        """Warehouse updates inventory and closes request"""
        data = {
            'inventory_updates': inventory_updates,
            'actor_id': actor_id
        }
        
        # Update inventory
        inventory_success = await self.workflow_engine.transition_workflow(
            request_id, WorkflowAction.UPDATE_INVENTORY.value, UserRole.WAREHOUSE.value, data
        )
        
        if inventory_success:
            # Close request
            close_success = await self.workflow_engine.transition_workflow(
                request_id, WorkflowAction.CLOSE_REQUEST.value, UserRole.WAREHOUSE.value, data
            )
            
            if close_success:
                # Send completion notification to client
                request = await self.state_manager.get_request(request_id)
                if request and self.notification_system:
                    await self.notification_system.send_completion_notification(
                        request.client_id, request_id, request.workflow_type
                    )
            
            return close_success
        
        return False
    
    async def rate_service(self, request_id: str, rating: int, feedback: str, client_id: int) -> bool:
        """Client rates completed service"""
        data = {
            'rating': rating,
            'feedback': feedback,
            'actor_id': client_id
        }
        
        return await self.workflow_engine.complete_workflow(request_id, data)
    
    async def get_workflow_status(self, request_id: str):
        """Gets current workflow status"""
        return await self.workflow_engine.get_workflow_status(request_id)
    
    async def get_requests_for_role(self, role: str, status_filter: str = None):
        """Gets requests assigned to specific role"""
        return await self.state_manager.get_requests_by_role(role, status_filter)
    
    async def get_client_requests(self, client_id: int):
        """Gets all requests for specific client"""
        return await self.state_manager.get_requests_by_client(client_id)    

    async def assign_to_call_center_operator(self, request_id: str, operator_id: int, supervisor_id: int) -> bool:
        """Call center supervisor assigns request to call center operator"""
        data = {
            'operator_id': operator_id,
            'actor_id': supervisor_id
        }
        
        return await self.workflow_engine.transition_workflow(
            request_id, WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value, UserRole.CALL_CENTER_SUPERVISOR.value, data
        )
    
    async def resolve_remotely(self, request_id: str, resolution_notes: str, operator_id: int) -> bool:
        """Call center operator resolves issue remotely"""
        data = {
            'resolution_notes': resolution_notes,
            'actor_id': operator_id,
            'resolved_at': str(datetime.now())
        }
        
        success = await self.workflow_engine.transition_workflow(
            request_id, WorkflowAction.RESOLVE_REMOTELY.value, UserRole.CALL_CENTER.value, data
        )
        
        if success:
            # Send completion notification to client
            request = await self.state_manager.get_request(request_id)
            if request and self.notification_system:
                await self.notification_system.send_completion_notification(
                    request.client_id, request_id, request.workflow_type
                )
        
        return success