"""
Workflow Engine - Core workflow management system
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from database.models import (
    ServiceRequest, StateTransition, WorkflowDefinition, WorkflowStep, 
    WorkflowStatus, WorkflowType, RequestStatus, WorkflowAction, UserRole
)


class WorkflowEngineInterface(ABC):
    """Abstract interface for workflow engine"""
    
    @abstractmethod
    async def initiate_workflow(self, workflow_type: str, request_data: dict) -> str:
        """Initiates a new workflow and returns request ID"""
        pass
    
    @abstractmethod
    async def transition_workflow(self, request_id: str, action: str, actor_role: str, data: dict) -> bool:
        """Processes workflow transitions between roles"""
        pass
    
    @abstractmethod
    async def get_workflow_status(self, request_id: str) -> Optional[WorkflowStatus]:
        """Returns current workflow status and next actions"""
        pass


class WorkflowEngine(WorkflowEngineInterface):
    """Core workflow engine implementation with integrated access control"""
    
    def __init__(self, state_manager, notification_system, inventory_manager, access_control=None):
        self.state_manager = state_manager
        self.notification_system = notification_system
        self.inventory_manager = inventory_manager
        self.access_control = access_control
        self.workflow_definitions = self._load_workflow_definitions()
        
        # Initialize access control if not provided
        if not self.access_control:
            from utils.workflow_access_control import WorkflowAccessControl
            self.access_control = WorkflowAccessControl()
    
    def _load_workflow_definitions(self) -> Dict[str, WorkflowDefinition]:
        """Load predefined workflow definitions"""
        definitions = {}
        
        # Connection Request Workflow
        connection_steps = {
            UserRole.CLIENT.value: WorkflowStep(
                role=UserRole.CLIENT.value,
                actions=[WorkflowAction.SUBMIT_REQUEST.value],
                next_steps={WorkflowAction.SUBMIT_REQUEST.value: UserRole.MANAGER.value},
                required_data=["description", "location", "contact_info"]
            ),
            UserRole.MANAGER.value: WorkflowStep(
                role=UserRole.MANAGER.value,
                actions=[WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value],
                next_steps={WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value: UserRole.JUNIOR_MANAGER.value},
                required_data=["junior_manager_id"]
            ),
            UserRole.JUNIOR_MANAGER.value: WorkflowStep(
                role=UserRole.JUNIOR_MANAGER.value,
                actions=[WorkflowAction.CALL_CLIENT.value, WorkflowAction.FORWARD_TO_CONTROLLER.value],
                next_steps={WorkflowAction.FORWARD_TO_CONTROLLER.value: UserRole.CONTROLLER.value},
                required_data=["call_notes"],
                optional_data=["additional_comments"]
            ),
            UserRole.CONTROLLER.value: WorkflowStep(
                role=UserRole.CONTROLLER.value,
                actions=[WorkflowAction.ASSIGN_TO_TECHNICIAN.value],
                next_steps={WorkflowAction.ASSIGN_TO_TECHNICIAN.value: UserRole.TECHNICIAN.value},
                required_data=["technician_id"]
            ),
            UserRole.TECHNICIAN.value: WorkflowStep(
                role=UserRole.TECHNICIAN.value,
                actions=[WorkflowAction.START_INSTALLATION.value, WorkflowAction.DOCUMENT_EQUIPMENT.value],
                next_steps={WorkflowAction.DOCUMENT_EQUIPMENT.value: UserRole.WAREHOUSE.value},
                required_data=["equipment_used", "installation_notes"]
            ),
            UserRole.WAREHOUSE.value: WorkflowStep(
                role=UserRole.WAREHOUSE.value,
                actions=[WorkflowAction.UPDATE_INVENTORY.value, WorkflowAction.CLOSE_REQUEST.value],
                next_steps={WorkflowAction.CLOSE_REQUEST.value: UserRole.CLIENT.value},
                required_data=["inventory_updates"]
            )
        }
        
        definitions[WorkflowType.CONNECTION_REQUEST.value] = WorkflowDefinition(
            name="Connection Request",
            initial_role=UserRole.CLIENT.value,
            steps=connection_steps,
            completion_actions=[WorkflowAction.RATE_SERVICE.value]
        )
        
        # Technical Service Workflow
        technical_steps = {
            UserRole.CLIENT.value: WorkflowStep(
                role=UserRole.CLIENT.value,
                actions=[WorkflowAction.SUBMIT_TECHNICAL_REQUEST.value],
                next_steps={WorkflowAction.SUBMIT_TECHNICAL_REQUEST.value: UserRole.CONTROLLER.value},
                required_data=["description", "issue_type"]
            ),
            UserRole.CONTROLLER.value: WorkflowStep(
                role=UserRole.CONTROLLER.value,
                actions=[WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value],
                next_steps={WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value: UserRole.TECHNICIAN.value},
                required_data=["technician_id"]
            ),
            UserRole.TECHNICIAN.value: WorkflowStep(
                role=UserRole.TECHNICIAN.value,
                actions=[
                    WorkflowAction.START_DIAGNOSTICS.value,
                    WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value,
                    WorkflowAction.RESOLVE_WITHOUT_WAREHOUSE.value,
                    WorkflowAction.REQUEST_WAREHOUSE_SUPPORT.value,
                    WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value,
                    WorkflowAction.DOCUMENT_EQUIPMENT.value
                ],
                next_steps={
                    WorkflowAction.REQUEST_WAREHOUSE_SUPPORT.value: UserRole.WAREHOUSE.value,
                    WorkflowAction.DOCUMENT_EQUIPMENT.value: UserRole.WAREHOUSE.value,
                    WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value: UserRole.CLIENT.value
                    # DECIDE_WAREHOUSE_INVOLVEMENT, RESOLVE_WITHOUT_WAREHOUSE and START_DIAGNOSTICS stay in same role
                },
                required_data=[],  # Different actions have different requirements
                optional_data=["diagnostics_notes", "equipment_needed", "equipment_used", "resolution_comments", "warehouse_decision"]
            ),
            UserRole.WAREHOUSE.value: WorkflowStep(
                role=UserRole.WAREHOUSE.value,
                actions=[
                    WorkflowAction.PREPARE_EQUIPMENT.value, 
                    WorkflowAction.CONFIRM_EQUIPMENT_READY.value,
                    WorkflowAction.UPDATE_INVENTORY.value
                ],
                next_steps={
                    WorkflowAction.CONFIRM_EQUIPMENT_READY.value: UserRole.TECHNICIAN.value,
                    WorkflowAction.UPDATE_INVENTORY.value: UserRole.TECHNICIAN.value
                },
                required_data=["equipment_prepared"],
                optional_data=["inventory_updates", "warehouse_comments"]
            )
        }
        
        definitions[WorkflowType.TECHNICAL_SERVICE.value] = WorkflowDefinition(
            name="Technical Service",
            initial_role=UserRole.CLIENT.value,
            steps=technical_steps,
            completion_actions=[WorkflowAction.RATE_SERVICE.value]
        )
        
        # Call Center Direct Resolution Workflow
        call_center_steps = {
            UserRole.CALL_CENTER_SUPERVISOR.value: WorkflowStep(
                role=UserRole.CALL_CENTER_SUPERVISOR.value,
                actions=[WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value],
                next_steps={WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value: UserRole.CALL_CENTER.value},
                required_data=["operator_id"]
            ),
            UserRole.CALL_CENTER.value: WorkflowStep(
                role=UserRole.CALL_CENTER.value,
                actions=[WorkflowAction.RESOLVE_REMOTELY.value],
                next_steps={WorkflowAction.RESOLVE_REMOTELY.value: UserRole.CLIENT.value},
                required_data=["resolution_notes"]
            )
        }
        
        definitions[WorkflowType.CALL_CENTER_DIRECT.value] = WorkflowDefinition(
            name="Call Center Direct Resolution",
            initial_role=UserRole.CALL_CENTER_SUPERVISOR.value,
            steps=call_center_steps,
            completion_actions=[WorkflowAction.RATE_SERVICE.value]
        )
        
        return definitions
    
    def _enhance_request_data_with_staff_context(self, request_data: dict) -> dict:
        """Enhance request data with staff creation context information"""
        enhanced_data = request_data.copy()
        
        # Check if this is a staff-created application
        created_by_staff = request_data.get('created_by_staff', False)
        staff_creator_info = request_data.get('staff_creator_info', {})
        
        if created_by_staff and staff_creator_info:
            # Add staff creation tracking to state data
            enhanced_data['state_data'] = enhanced_data.get('state_data', {})
            enhanced_data['state_data'].update({
                'created_by_staff': True,
                'staff_creator_info': staff_creator_info,
                'staff_creation_timestamp': datetime.now().isoformat(),
                'workflow_initiated_by_staff': True
            })
            
            # Set creation source based on creator role
            creator_role = staff_creator_info.get('creator_role', 'unknown')
            enhanced_data['creation_source'] = creator_role
            enhanced_data['staff_creator_id'] = staff_creator_info.get('creator_id')
            enhanced_data['staff_creator_role'] = creator_role
        else:
            # Regular client-created application
            enhanced_data['creation_source'] = 'client'
            enhanced_data['created_by_staff'] = False
        
        return enhanced_data
    
    def _get_workflow_initiation_comment(self, request_data: dict) -> str:
        """Generate appropriate comment for workflow initiation"""
        is_staff_created = request_data.get('created_by_staff', False)
        
        if is_staff_created:
            staff_creator_info = request_data.get('staff_creator_info', {})
            creator_role = staff_creator_info.get('creator_role', 'unknown')
            creator_name = staff_creator_info.get('creator_name', 'Unknown Staff')
            client_name = request_data.get('contact_info', {}).get('full_name', 'Unknown Client')
            
            return f"Workflow initiated by {creator_role} ({creator_name}) on behalf of client {client_name}"
        else:
            return "Workflow initiated by client"
    
    async def initiate_workflow(self, workflow_type: str, request_data: dict) -> str:
        """Initiates a new workflow and returns request ID"""
        if workflow_type not in self.workflow_definitions:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        workflow_def = self.workflow_definitions[workflow_type]
        
        # Enhance request data with staff creation context if applicable
        enhanced_request_data = self._enhance_request_data_with_staff_context(request_data)
        
        # Save to state manager and get request ID
        request_id = await self.state_manager.create_request(workflow_type, enhanced_request_data)
        
        # Get the actual initial role from the created request (may differ from workflow definition)
        request = await self.state_manager.get_request(request_id)
        actual_initial_role = request.role_current if request else workflow_def.initial_role
        
        # Create initial state transition with staff creation context
        initial_transition = StateTransition(
            request_id=request_id,
            from_role=None,
            to_role=actual_initial_role,
            action="workflow_initiated",
            actor_id=enhanced_request_data.get('client_id'),
            transition_data=enhanced_request_data,
            comments=self._get_workflow_initiation_comment(enhanced_request_data),
            created_at=datetime.now()
        )
        
        await self.state_manager.add_state_transition(initial_transition)
        
        # Send notification to the assigned role if notification system is available
        if self.notification_system and actual_initial_role:
            # Check if this is a staff-created application
            is_staff_created = enhanced_request_data.get('created_by_staff', False)
            
            if is_staff_created:
                # For staff-created applications, send enhanced notifications
                staff_creator_info = enhanced_request_data.get('staff_creator_info', {})
                creator_role = staff_creator_info.get('creator_role', 'unknown')
                client_name = enhanced_request_data.get('contact_info', {}).get('full_name', 'Unknown Client')
                
                # Send notification to workflow participants with staff creation context
                await self.notification_system.send_staff_workflow_notification(
                    actual_initial_role, request_id, workflow_type, creator_role,
                    client_name, enhanced_request_data
                )
                
                # Send client notification about staff-created application
                client_id = enhanced_request_data.get('client_id')
                if client_id:
                    await self.notification_system.send_staff_client_notification(
                        client_id, request_id, workflow_type, creator_role, enhanced_request_data
                    )
                
                # Send confirmation to staff member who created the application
                staff_creator_id = staff_creator_info.get('creator_id')
                if staff_creator_id:
                    await self.notification_system.send_staff_confirmation_notification(
                        staff_creator_id, request_id, workflow_type, client_name, enhanced_request_data
                    )
            else:
                # Regular client-created application notification
                await self.notification_system.send_assignment_notification(
                    actual_initial_role, request_id, workflow_type
                )
        
        return request_id
    
    async def transition_workflow(self, request_id: str, action: str, actor_role: str, data: dict) -> bool:
        """Processes workflow transitions between roles with access control validation"""
        # Get current request state
        request = await self.state_manager.get_request(request_id)
        if not request:
            return False
        
        workflow_def = self.workflow_definitions.get(request.workflow_type)
        if not workflow_def:
            return False
        
        current_step = workflow_def.steps.get(request.role_current)
        if not current_step:
            return False
        
        # Validate access control permissions
        if self.access_control:
            actor_id = data.get('actor_id')
            if actor_id:
                valid, reason = await self.access_control.validate_workflow_action(
                    user_id=actor_id,
                    user_role=actor_role,
                    action=action,
                    request_id=request_id,
                    target_data=data
                )
                
                if not valid:
                    # Log the unauthorized attempt
                    await self.access_control.log_access_attempt(
                        user_id=actor_id,
                        action=f"workflow_transition_{action}",
                        resource=f"request:{request_id}",
                        granted=False,
                        reason=f"Workflow transition denied: {reason}"
                    )
                    return False
        
        # Validate action is allowed for current role
        if action not in current_step.actions:
            return False
        
        # Validate required data is present
        for required_field in current_step.required_data:
            if required_field not in data:
                return False
        
        # Determine next role
        next_role = current_step.next_steps.get(action)
        if not next_role:
            # Action doesn't transition to another role (e.g., intermediate actions)
            next_role = request.role_current 
        
        # Update request state
        updated_request = ServiceRequest(
            id=request.id,
            workflow_type=request.workflow_type,
            client_id=request.client_id,
            role_current =next_role,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=request.created_at,
            updated_at=datetime.now(),
            priority=request.priority,
            description=request.description,
            location=request.location,
            contact_info=request.contact_info,
            state_data={**request.state_data, **data},
            equipment_used=request.equipment_used,
            inventory_updated=request.inventory_updated,
            completion_rating=request.completion_rating,
            feedback_comments=request.feedback_comments
        )
        
        # Enhance transition data with staff creation context
        enhanced_transition_data = self._enhance_transition_data_with_staff_context(request, data)
        
        # Update request state
        new_state = {
            'role_current ': next_role,
            'current_status': RequestStatus.IN_PROGRESS.value,
            'state_data': {**request.state_data, **enhanced_transition_data},
            'actor_id': data.get('actor_id'),
            'action': action,
            'comments': self._get_transition_comment(request, action, data)
        }
        
        await self.state_manager.update_request_state(request_id, new_state, str(data.get('actor_id', 'system')))
        
        # Create state transition record with enhanced context
        transition = StateTransition(
            request_id=request_id,
            from_role=request.role_current ,
            to_role=next_role,
            action=action,
            actor_id=data.get('actor_id'),
            transition_data=enhanced_transition_data,
            comments=self._get_transition_comment(request, action, data),
            created_at=datetime.now()
        )
        
        await self.state_manager.add_state_transition(transition)
        
        # Send notification to next role if role changed
        if next_role != request.role_current and self.notification_system:
            # Check if this is a staff-created application for enhanced notifications
            is_staff_created = request.state_data.get('created_by_staff', False)
            
            if is_staff_created:
                # For staff-created applications, send enhanced workflow notifications
                staff_creator_info = request.state_data.get('staff_creator_info', {})
                creator_role = staff_creator_info.get('creator_role', 'unknown')
                client_name = request.contact_info.get('full_name', 'Unknown Client')
                
                await self.notification_system.send_staff_workflow_notification(
                    next_role, request_id, request.workflow_type, creator_role,
                    client_name, request.state_data
                )
            else:
                # Regular client-created application notification
                await self.notification_system.send_assignment_notification(
                    next_role, request_id, request.workflow_type
                )
        
        # Handle inventory updates if needed
        if action == WorkflowAction.UPDATE_INVENTORY.value and self.inventory_manager:
            equipment_used = data.get('equipment_used', [])
            await self.inventory_manager.consume_equipment(request_id, equipment_used)
        
        return True
    
    def _enhance_transition_data_with_staff_context(self, request: ServiceRequest, transition_data: dict) -> dict:
        """Enhance transition data with staff creation context information"""
        enhanced_data = transition_data.copy()
        
        # Preserve staff creation context from request state
        if request.state_data.get('created_by_staff', False):
            enhanced_data.update({
                'staff_created_workflow': True,
                'original_staff_creator_info': request.state_data.get('staff_creator_info', {}),
                'workflow_transition_timestamp': datetime.now().isoformat()
            })
            
            # Add context about who is performing this transition vs who created the request
            staff_creator_info = request.state_data.get('staff_creator_info', {})
            current_actor_id = transition_data.get('actor_id')
            
            if current_actor_id != staff_creator_info.get('creator_id'):
                enhanced_data['transition_by_different_staff'] = True
                enhanced_data['original_creator_role'] = staff_creator_info.get('creator_role')
        
        return enhanced_data
    
    def _get_transition_comment(self, request: ServiceRequest, action: str, data: dict) -> str:
        """Generate appropriate comment for workflow transition"""
        base_comment = data.get('comments', f"Action: {action}")
        
        # Add staff creation context if applicable
        if request.state_data.get('created_by_staff', False):
            staff_creator_info = request.state_data.get('staff_creator_info', {})
            creator_role = staff_creator_info.get('creator_role', 'unknown')
            client_name = request.contact_info.get('full_name', 'Unknown Client')
            
            return f"{base_comment} (Staff-created request by {creator_role} for client {client_name})"
        
        return base_comment
    
    async def get_workflow_status(self, request_id: str) -> Optional[WorkflowStatus]:
        """Returns current workflow status and next actions"""
        request = await self.state_manager.get_request(request_id)
        if not request:
            return None
        
        workflow_def = self.workflow_definitions.get(request.workflow_type)
        if not workflow_def:
            return None
        
        current_step = workflow_def.steps.get(request.role_current )
        if not current_step:
            return None
        
        # Get transition history
        history = await self.state_manager.get_request_history(request_id)
        
        # Determine next possible roles
        next_roles = list(current_step.next_steps.values())
        
        return WorkflowStatus(
            request_id=request_id,
            role_current =request.role_current ,
            current_status=request.current_status,
            available_actions=current_step.actions,
            next_roles=next_roles,
            history=history
        )
    
    async def complete_workflow(self, request_id: str, completion_data: dict) -> bool:
        """Completes a workflow with final status"""
        request = await self.state_manager.get_request(request_id)
        if not request:
            return False
        
        # Update request to completed status
        completed_request = ServiceRequest(
            id=request.id,
            workflow_type=request.workflow_type,
            client_id=request.client_id,
            role_current =request.role_current ,
            current_status=RequestStatus.COMPLETED.value,
            created_at=request.created_at,
            updated_at=datetime.now(),
            priority=request.priority,
            description=request.description,
            location=request.location,
            contact_info=request.contact_info,
            state_data={**request.state_data, **completion_data},
            equipment_used=request.equipment_used,
            inventory_updated=request.inventory_updated,
            completion_rating=completion_data.get('rating'),
            feedback_comments=completion_data.get('feedback')
        )
        
        # Update request to completed status
        completion_state = {
            'current_status': RequestStatus.COMPLETED.value,
            'state_data': {**request.state_data, **completion_data},
            'completion_rating': completion_data.get('rating'),
            'feedback_comments': completion_data.get('feedback'),
            'actor_id': completion_data.get('actor_id'),
            'action': 'workflow_completed',
            'comments': 'Workflow completed'
        }
        
        await self.state_manager.update_request_state(request_id, completion_state, str(completion_data.get('actor_id', 'system')))
        
        # Create completion transition
        completion_transition = StateTransition(
            request_id=request_id,
            from_role=request.role_current ,
            to_role=None,
            action="workflow_completed",
            actor_id=completion_data.get('actor_id'),
            transition_data=completion_data,
            comments="Workflow completed",
            created_at=datetime.now()
        )
        
        await self.state_manager.add_state_transition(completion_transition)
        
        return True
    
    def get_workflow_definition(self, workflow_type: str) -> Optional[WorkflowDefinition]:
        """Returns workflow definition for given type"""
        return self.workflow_definitions.get(workflow_type)
    
    def get_available_workflows(self) -> List[str]:
        """Returns list of available workflow types"""
        return list(self.workflow_definitions.keys())


class WorkflowEngineFactory:
    """Factory for creating workflow engine instances"""
    
    @staticmethod
    def create_workflow_engine(state_manager, notification_system=None, inventory_manager=None) -> WorkflowEngine:
        """Creates a new workflow engine instance"""
        return WorkflowEngine(state_manager, notification_system, inventory_manager)