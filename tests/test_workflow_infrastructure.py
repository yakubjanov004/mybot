"""
Test suite for workflow infrastructure
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from database.models import (
    ServiceRequest, StateTransition, WorkflowType, RequestStatus, 
    WorkflowAction, UserRole, Priority
)
from utils.workflow_engine import WorkflowEngine, WorkflowEngineFactory
from utils.state_manager import StateManager, StateManagerFactory


class TestWorkflowModels:
    """Test workflow-related models"""
    
    def test_service_request_creation(self):
        """Test ServiceRequest model creation"""
        request = ServiceRequest(
            id="test-123",
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current =UserRole.CLIENT.value,
            current_status=RequestStatus.CREATED.value,
            priority=Priority.MEDIUM.value,
            description="Test connection request",
            location="Test location"
        )
        
        assert request.id == "test-123"
        assert request.workflow_type == WorkflowType.CONNECTION_REQUEST.value
        assert request.client_id == 1
        assert request.role_current == UserRole.CLIENT.value
        assert request.current_status == RequestStatus.CREATED.value
        
        # Test to_dict conversion
        request_dict = request.to_dict()
        assert request_dict['id'] == "test-123"
        assert request_dict['workflow_type'] == WorkflowType.CONNECTION_REQUEST.value
        
        # Test from_dict conversion
        restored_request = ServiceRequest.from_dict(request_dict)
        assert restored_request.id == request.id
        assert restored_request.workflow_type == request.workflow_type
    
    def test_state_transition_creation(self):
        """Test StateTransition model creation"""
        transition = StateTransition(
            request_id="test-123",
            from_role=UserRole.CLIENT.value,
            to_role=UserRole.MANAGER.value,
            action=WorkflowAction.SUBMIT_REQUEST.value,
            actor_id=1,
            comments="Initial request submission"
        )
        
        assert transition.request_id == "test-123"
        assert transition.from_role == UserRole.CLIENT.value
        assert transition.to_role == UserRole.MANAGER.value
        assert transition.action == WorkflowAction.SUBMIT_REQUEST.value
        
        # Test to_dict conversion
        transition_dict = transition.to_dict()
        assert transition_dict['request_id'] == "test-123"
        assert transition_dict['action'] == WorkflowAction.SUBMIT_REQUEST.value


class TestWorkflowEngine:
    """Test workflow engine functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_state_manager = AsyncMock()
        self.mock_notification_system = AsyncMock()
        self.mock_inventory_manager = AsyncMock()
        
        self.workflow_engine = WorkflowEngine(
            self.mock_state_manager,
            self.mock_notification_system,
            self.mock_inventory_manager
        )
    
    def test_workflow_definitions_loaded(self):
        """Test that workflow definitions are properly loaded"""
        definitions = self.workflow_engine.workflow_definitions
        
        assert WorkflowType.CONNECTION_REQUEST.value in definitions
        assert WorkflowType.TECHNICAL_SERVICE.value in definitions
        assert WorkflowType.CALL_CENTER_DIRECT.value in definitions
        
        # Test connection request workflow
        connection_workflow = definitions[WorkflowType.CONNECTION_REQUEST.value]
        assert connection_workflow.name == "Connection Request"
        assert connection_workflow.initial_role == UserRole.CLIENT.value
        assert UserRole.CLIENT.value in connection_workflow.steps
        assert UserRole.MANAGER.value in connection_workflow.steps
    
    async def test_initiate_workflow(self):
        """Test workflow initiation"""
        request_data = {
            'client_id': 1,
            'description': 'Test connection request',
            'location': 'Test location',
            'contact_info': {'phone': '123456789'},
            'priority': 'high'
        }
        
        # Mock state manager methods
        self.mock_state_manager.create_request.return_value = True
        self.mock_state_manager.add_state_transition.return_value = True
        
        request_id = await self.workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, request_data
        )
        
        assert request_id is not None
        assert len(request_id) > 0
        
        # Verify state manager was called
        self.mock_state_manager.create_request.assert_called_once()
        self.mock_state_manager.add_state_transition.assert_called_once()
    
    async def test_transition_workflow(self):
        """Test workflow transition"""
        request_id = "test-123"
        
        # Mock existing request
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current =UserRole.MANAGER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            state_data={'client_id': 1}
        )
        
        self.mock_state_manager.get_request.return_value = mock_request
        self.mock_state_manager.update_request.return_value = True
        self.mock_state_manager.add_state_transition.return_value = True
        
        transition_data = {
            'junior_manager_id': 2,
            'actor_id': 1
        }
        
        success = await self.workflow_engine.transition_workflow(
            request_id,
            WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
            UserRole.MANAGER.value,
            transition_data
        )
        
        assert success is True
        
        # Verify state manager methods were called
        self.mock_state_manager.get_request.assert_called_once_with(request_id)
        self.mock_state_manager.update_request.assert_called_once()
        self.mock_state_manager.add_state_transition.assert_called_once()
        self.mock_notification_system.send_assignment_notification.assert_called_once()
    
    async def test_get_workflow_status(self):
        """Test getting workflow status"""
        request_id = "test-123"
        
        # Mock existing request
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current =UserRole.MANAGER.value,
            current_status=RequestStatus.IN_PROGRESS.value
        )
        
        mock_history = [
            StateTransition(
                request_id=request_id,
                from_role=None,
                to_role=UserRole.CLIENT.value,
                action="workflow_initiated",
                actor_id=1
            )
        ]
        
        self.mock_state_manager.get_request.return_value = mock_request
        self.mock_state_manager.get_request_history.return_value = mock_history
        
        status = await self.workflow_engine.get_workflow_status(request_id)
        
        assert status is not None
        assert status.request_id == request_id
        assert status.role_current == UserRole.MANAGER.value
        assert status.current_status == RequestStatus.IN_PROGRESS.value
        assert len(status.available_actions) > 0
        assert len(status.history) == 1
    
    def test_get_workflow_definition(self):
        """Test getting workflow definition"""
        definition = self.workflow_engine.get_workflow_definition(
            WorkflowType.CONNECTION_REQUEST.value
        )
        
        assert definition is not None
        assert definition.name == "Connection Request"
        assert definition.initial_role == UserRole.CLIENT.value
    
    def test_get_available_workflows(self):
        """Test getting available workflow types"""
        workflows = self.workflow_engine.get_available_workflows()
        
        assert len(workflows) == 3
        assert WorkflowType.CONNECTION_REQUEST.value in workflows
        assert WorkflowType.TECHNICAL_SERVICE.value in workflows
        assert WorkflowType.CALL_CENTER_DIRECT.value in workflows


class TestWorkflowEngineFactory:
    """Test workflow engine factory"""
    
    def test_create_workflow_engine(self):
        """Test factory creates workflow engine"""
        mock_state_manager = MagicMock()
        
        engine = WorkflowEngineFactory.create_workflow_engine(mock_state_manager)
        
        assert isinstance(engine, WorkflowEngine)
        assert engine.state_manager == mock_state_manager


class TestStateManager:
    """Test state manager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_pool = AsyncMock()
        self.mock_conn = AsyncMock()
        self.mock_transaction = AsyncMock()
        
        # Setup mock pool behavior
        self.mock_pool.acquire.return_value.__aenter__.return_value = self.mock_conn
        self.mock_conn.transaction.return_value.__aenter__.return_value = self.mock_transaction
        
        self.state_manager = StateManager(self.mock_pool)
    
    async def test_create_request_connection_workflow(self):
        """Test creating a connection request"""
        initial_data = {
            'client_id': 1,
            'description': 'Test connection request',
            'location': 'Test location',
            'contact_info': {'phone': '123456789'},
            'priority': 'high'
        }
        
        # Mock database responses
        self.mock_conn.execute.return_value = None
        
        request_id = await self.state_manager.create_request(
            WorkflowType.CONNECTION_REQUEST.value, initial_data
        )
        
        assert request_id is not None
        assert len(request_id) > 0
        
        # Verify database calls
        assert self.mock_conn.execute.call_count == 2  # INSERT request + INSERT transition
    
    async def test_create_request_technical_workflow(self):
        """Test creating a technical service request"""
        initial_data = {
            'client_id': 2,
            'description': 'Technical issue with connection',
            'location': 'Client location',
            'priority': 'medium'
        }
        
        self.mock_conn.execute.return_value = None
        
        request_id = await self.state_manager.create_request(
            WorkflowType.TECHNICAL_SERVICE.value, initial_data
        )
        
        assert request_id is not None
        # Verify correct initial role for technical service
        call_args = self.mock_conn.execute.call_args_list[0][0]
        assert 'controller' in str(call_args).lower()  # Should route to controller initially
    
    async def test_update_request_state(self):
        """Test updating request state with audit logging"""
        request_id = "test-123"
        
        # Mock existing request
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current ='manager',
            current_status='in_progress',
            state_data={'client_id': 1}
        )
        
        self.mock_conn.fetchrow.return_value = {
            'id': request_id,
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 1,
            'role_current ': 'manager',
            'current_status': 'in_progress',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'priority': 'medium',
            'description': 'Test',
            'location': 'Test location',
            'contact_info': '{}',
            'state_data': '{"client_id": 1}',
            'equipment_used': '[]',
            'inventory_updated': False,
            'completion_rating': None,
            'feedback_comments': None
        }
        
        self.mock_conn.execute.return_value = "UPDATE 1"
        
        new_state = {
            'role_current ': 'junior_manager',
            'current_status': 'in_progress',
            'action': 'assign_to_junior_manager',
            'actor_id': 1,
            'comments': 'Assigned to junior manager'
        }
        
        success = await self.state_manager.update_request_state(
            request_id, new_state, "manager"
        )
        
        assert success is True
        # Verify both UPDATE and INSERT (transition) were called
        assert self.mock_conn.execute.call_count == 2
    
    async def test_get_request(self):
        """Test getting request by ID"""
        request_id = "test-123"
        
        self.mock_conn.fetchrow.return_value = {
            'id': request_id,
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 1,
            'role_current ': 'manager',
            'current_status': 'in_progress',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'priority': 'medium',
            'description': 'Test request',
            'location': 'Test location',
            'contact_info': '{"phone": "123456789"}',
            'state_data': '{"client_id": 1}',
            'equipment_used': '[]',
            'inventory_updated': False,
            'completion_rating': None,
            'feedback_comments': None
        }
        
        request = await self.state_manager.get_request(request_id)
        
        assert request is not None
        assert request.id == request_id
        assert request.workflow_type == WorkflowType.CONNECTION_REQUEST.value
        assert request.client_id == 1
        assert request.contact_info == {"phone": "123456789"}
    
    async def test_get_requests_by_role(self):
        """Test getting requests by role with filtering"""
        role = 'manager'
        
        mock_rows = [
            {
                'id': 'req-1',
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
                'client_id': 1,
                'role_current ': role,
                'current_status': 'in_progress',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'priority': 'high',
                'description': 'High priority request',
                'location': 'Location 1',
                'contact_info': '{}',
                'state_data': '{}',
                'equipment_used': '[]',
                'inventory_updated': False,
                'completion_rating': None,
                'feedback_comments': None
            },
            {
                'id': 'req-2',
                'workflow_type': WorkflowType.TECHNICAL_SERVICE.value,
                'client_id': 2,
                'role_current ': role,
                'current_status': 'in_progress',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'priority': 'medium',
                'description': 'Medium priority request',
                'location': 'Location 2',
                'contact_info': '{}',
                'state_data': '{}',
                'equipment_used': '[]',
                'inventory_updated': False,
                'completion_rating': None,
                'feedback_comments': None
            }
        ]
        
        self.mock_conn.fetch.return_value = mock_rows
        
        requests = await self.state_manager.get_requests_by_role(role)
        
        assert len(requests) == 2
        assert requests[0].id == 'req-1'
        assert requests[1].id == 'req-2'
        assert all(req.role_current == role for req in requests)
    
    async def test_get_requests_by_role_with_status_filter(self):
        """Test getting requests by role with status filter"""
        role = 'technician'
        status_filter = 'in_progress'
        
        self.mock_conn.fetch.return_value = []
        
        requests = await self.state_manager.get_requests_by_role(role, status_filter)
        
        # Verify the query included status filter
        call_args = self.mock_conn.fetch.call_args[0]
        assert 'current_status = $2' in call_args[0]
        assert call_args[1] == role
        assert call_args[2] == status_filter
    
    async def test_record_state_transition(self):
        """Test recording state transition"""
        request_id = "test-123"
        from_role = "manager"
        to_role = "junior_manager"
        action = "assign_to_junior_manager"
        actor_id = 1
        transition_data = {"junior_manager_id": 2}
        comments = "Assigned to junior manager"
        
        self.mock_conn.execute.return_value = None
        
        success = await self.state_manager.record_state_transition(
            request_id, from_role, to_role, action, actor_id, transition_data, comments
        )
        
        assert success is True
        self.mock_conn.execute.assert_called_once()
    
    async def test_get_request_history(self):
        """Test getting complete request history"""
        request_id = "test-123"
        
        mock_transitions = [
            {
                'id': 1,
                'request_id': request_id,
                'from_role': None,
                'to_role': 'manager',
                'action': 'workflow_initiated',
                'actor_id': 1,
                'transition_data': '{"client_id": 1}',
                'comments': 'Request created',
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'request_id': request_id,
                'from_role': 'manager',
                'to_role': 'junior_manager',
                'action': 'assign_to_junior_manager',
                'actor_id': 1,
                'transition_data': '{"junior_manager_id": 2}',
                'comments': 'Assigned to junior manager',
                'created_at': datetime.now()
            }
        ]
        
        self.mock_conn.fetch.return_value = mock_transitions
        
        history = await self.state_manager.get_request_history(request_id)
        
        assert len(history) == 2
        assert history[0].action == 'workflow_initiated'
        assert history[1].action == 'assign_to_junior_manager'
        assert history[0].from_role is None
        assert history[1].from_role == 'manager'
    
    async def test_get_requests_by_client(self):
        """Test getting requests for specific client"""
        client_id = 1
        
        mock_rows = [
            {
                'id': 'req-1',
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
                'client_id': client_id,
                'role_current ': 'manager',
                'current_status': 'completed',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'priority': 'medium',
                'description': 'Completed request',
                'location': 'Location 1',
                'contact_info': '{}',
                'state_data': '{}',
                'equipment_used': '[]',
                'inventory_updated': True,
                'completion_rating': 5,
                'feedback_comments': 'Great service'
            }
        ]
        
        self.mock_conn.fetch.return_value = mock_rows
        
        requests = await self.state_manager.get_requests_by_client(client_id)
        
        assert len(requests) == 1
        assert requests[0].client_id == client_id
        assert requests[0].completion_rating == 5
    
    async def test_get_requests_by_status(self):
        """Test getting requests by status"""
        status = 'completed'
        
        self.mock_conn.fetch.return_value = []
        
        requests = await self.state_manager.get_requests_by_status(status)
        
        # Verify the query used status filter
        call_args = self.mock_conn.fetch.call_args[0]
        assert 'current_status = $1' in call_args[0]
        assert call_args[1] == status
    
    async def test_delete_request(self):
        """Test deleting request and its history"""
        request_id = "test-123"
        
        self.mock_conn.execute.side_effect = [None, "DELETE 1"]
        
        success = await self.state_manager.delete_request(request_id)
        
        assert success is True
        # Verify both DELETE operations were called
        assert self.mock_conn.execute.call_count == 2
    
    def test_generate_request_id(self):
        """Test request ID generation"""
        request_id = self.state_manager._generate_request_id()
        
        assert request_id is not None
        assert len(request_id) > 0
        assert isinstance(request_id, str)
        
        # Generate another ID to ensure uniqueness
        request_id2 = self.state_manager._generate_request_id()
        assert request_id != request_id2
    
    def test_get_initial_role(self):
        """Test initial role determination based on workflow type"""
        # Test connection request
        role = self.state_manager._get_initial_role(WorkflowType.CONNECTION_REQUEST.value)
        assert role == 'manager'
        
        # Test technical service
        role = self.state_manager._get_initial_role(WorkflowType.TECHNICAL_SERVICE.value)
        assert role == 'controller'
        
        # Test call center direct
        role = self.state_manager._get_initial_role(WorkflowType.CALL_CENTER_DIRECT.value)
        assert role == 'call_center_supervisor'
        
        # Test unknown workflow type (should default to manager)
        role = self.state_manager._get_initial_role('unknown_workflow')
        assert role == 'manager'


class TestStateManagerFactory:
    """Test state manager factory"""
    
    def test_create_state_manager(self):
        """Test factory creates state manager"""
        manager = StateManagerFactory.create_state_manager()
        
        assert isinstance(manager, StateManager)


if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running workflow infrastructure tests...")
    
    # Test model creation
    print("✓ Testing ServiceRequest model...")
    request = ServiceRequest(
        id="test-123",
        workflow_type=WorkflowType.CONNECTION_REQUEST.value,
        client_id=1,
        role_current =UserRole.CLIENT.value
    )
    assert request.id == "test-123"
    print("✓ ServiceRequest model works correctly")
    
    # Test workflow engine creation
    print("✓ Testing WorkflowEngine creation...")
    mock_state_manager = MagicMock()
    engine = WorkflowEngineFactory.create_workflow_engine(mock_state_manager)
    assert isinstance(engine, WorkflowEngine)
    print("✓ WorkflowEngine created successfully")
    
    # Test workflow definitions
    print("✓ Testing workflow definitions...")
    definitions = engine.workflow_definitions
    assert len(definitions) == 3
    assert WorkflowType.CONNECTION_REQUEST.value in definitions
    print("✓ Workflow definitions loaded correctly")
    
    print("\n🎉 All basic workflow infrastructure tests passed!")
    print("✅ Core workflow infrastructure is properly set up")