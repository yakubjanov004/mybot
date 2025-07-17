"""
Integration tests for Technical Service Without Warehouse Workflow
Tests the complete workflow: Client → Controller → Technician
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from database.models import (
    WorkflowType, WorkflowAction, UserRole, RequestStatus, Priority,
    ServiceRequest, StateTransition
)
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory
from handlers.technical_service_workflow import TechnicalServiceWorkflowHandler


class TestTechnicalServiceWorkflow:
    """Test suite for Technical Service Without Warehouse workflow"""
    
    @pytest.fixture
    async def setup_workflow(self):
        """Setup workflow components for testing"""
        # Mock database pool
        mock_pool = AsyncMock()
        
        # Create workflow components
        state_manager = StateManagerFactory.create_state_manager()
        notification_system = NotificationSystemFactory.create_notification_system()
        workflow_engine = WorkflowEngineFactory.create_workflow_engine(
            state_manager, notification_system
        )
        
        # Mock database operations
        state_manager.pool = mock_pool
        notification_system.pool = mock_pool
        
        return {
            'state_manager': state_manager,
            'notification_system': notification_system,
            'workflow_engine': workflow_engine,
            'mock_pool': mock_pool
        }
    
    @pytest.fixture
    def sample_client_data(self):           
        """Sample client data for testing"""
        return {
            'id': 1,
            'telegram_id': 12345,
            'full_name': 'Test Client',
            'phone': '+998901234567',
            'role': UserRole.CLIENT.value,
            'language': 'uz'
        }
    
    @pytest.fixture
    def sample_controller_data(self):
        """Sample controller data for testing"""
        return {
            'id': 2,
            'telegram_id': 23456,
            'full_name': 'Test Controller',
            'role': UserRole.CONTROLLER.value,
            'language': 'ru'
        }
    
    @pytest.fixture
    def sample_technician_data(self):
        """Sample technician data for testing"""
        return {
            'id': 3,
            'telegram_id': 34567,
            'full_name': 'Test Technician',
            'role': UserRole.TECHNICIAN.value,
            'language': 'uz'
        }
    
    @pytest.mark.asyncio
    async def test_complete_technical_service_workflow(self, setup_workflow, sample_client_data, 
                                                     sample_controller_data, sample_technician_data):
        """Test complete technical service workflow from client to completion"""
        components = await setup_workflow
        workflow_engine = components['workflow_engine']
        state_manager = components['state_manager']
        mock_pool = components['mock_pool']
        
        # Mock database responses
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        
        # Mock request creation
        request_id = "test-request-123"
        mock_conn.execute.return_value = "INSERT 1"
        
        # Step 1: Client creates technical service request
        request_data = {
            'client_id': sample_client_data['id'],
            'description': 'Internet connection is very slow',
            'issue_type': 'technical_support',
            'priority': Priority.MEDIUM.value,
            'contact_info': {
                'phone': sample_client_data['phone'],
                'telegram_id': sample_client_data['telegram_id'],
                'full_name': sample_client_data['full_name']
            }
        }
        
        # Mock state manager methods
        with patch.object(state_manager, 'create_request', return_value=request_id):
            created_request_id = await workflow_engine.initiate_workflow(
                WorkflowType.TECHNICAL_SERVICE.value, request_data
            )
        
        assert created_request_id == request_id
        
        # Mock request object for subsequent operations
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=sample_client_data['id'],
            role_current =UserRole.CONTROLLER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description=request_data['description'],
            contact_info=request_data['contact_info'],
            state_data={}
        )
        
        # Step 2: Controller assigns to technician
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            assignment_data = {
                'technician_id': sample_technician_data['id'],
                'actor_id': sample_controller_data['id'],
                'assigned_at': str(datetime.now())
            }
            
            assignment_success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                UserRole.CONTROLLER.value,
                assignment_data
            )
        
        assert assignment_success is True
        
        # Update mock request for technician role
        mock_request.role_current = UserRole.TECHNICIAN.value
        mock_request.state_data = assignment_data
        
        # Step 3: Technician starts diagnostics
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            diagnostics_data = {
                'actor_id': sample_technician_data['id'],
                'diagnostics_started_at': str(datetime.now()),
                'diagnostics_notes': 'Started checking connection speed'
            }
            
            diagnostics_success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.START_DIAGNOSTICS.value,
                UserRole.TECHNICIAN.value,
                diagnostics_data
            )
        
        assert diagnostics_success is True
        
        # Update mock request state
        mock_request.state_data.update(diagnostics_data)
        
        # Step 4: Technician decides no warehouse involvement needed
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            decision_data = {
                'actor_id': sample_technician_data['id'],
                'warehouse_decision': 'no',
                'warehouse_decision_at': str(datetime.now())
            }
            
            decision_success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value,
                UserRole.TECHNICIAN.value,
                decision_data
            )
        
        assert decision_success is True
        
        # Update mock request state
        mock_request.state_data.update(decision_data)
        
        # Step 5: Technician completes service without warehouse
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            completion_data = {
                'actor_id': sample_technician_data['id'],
                'resolution_comments': 'Reconfigured router settings, speed issue resolved',
                'completed_at': str(datetime.now()),
                'warehouse_involved': False
            }
            
            completion_success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value,
                UserRole.TECHNICIAN.value,
                completion_data
            )
        
        assert completion_success is True
        
        # Step 6: Client rates the service
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            rating_data = {
                'rating': 5,
                'feedback': 'Excellent service, problem solved quickly',
                'actor_id': sample_client_data['id'],
                'rated_at': str(datetime.now())
            }
            
            rating_success = await workflow_engine.complete_workflow(request_id, rating_data)
        
        assert rating_success is True
    
    @pytest.mark.asyncio
    async def test_client_technical_request_creation(self, setup_workflow, sample_client_data):
        """Test client technical service request creation"""
        components = await setup_workflow
        workflow_engine = components['workflow_engine']
        
        request_data = {
            'client_id': sample_client_data['id'],
            'description': 'WiFi keeps disconnecting',
            'issue_type': 'connectivity_issue',
            'priority': Priority.HIGH.value,
            'contact_info': {
                'phone': sample_client_data['phone'],
                'telegram_id': sample_client_data['telegram_id']
            }
        }
        
        with patch.object(workflow_engine.state_manager, 'create_request', return_value="req-456"):
            request_id = await workflow_engine.initiate_workflow(
                WorkflowType.TECHNICAL_SERVICE.value, request_data
            )
        
        assert request_id == "req-456"
    
    @pytest.mark.asyncio
    async def test_controller_technician_assignment(self, setup_workflow, sample_controller_data, sample_technician_data):
        """Test controller assigning technical request to technician"""
        components = await setup_workflow
        workflow_engine = components['workflow_engine']
        
        request_id = "test-req-789"
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=1,
            role_current =UserRole.CONTROLLER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description="Equipment malfunction",
            state_data={}
        )
        
        assignment_data = {
            'technician_id': sample_technician_data['id'],
            'actor_id': sample_controller_data['id'],
            'assigned_at': str(datetime.now())
        }
        
        with patch.object(workflow_engine.state_manager, 'get_request', return_value=mock_request), \
             patch.object(workflow_engine.state_manager, 'update_request_state', return_value=True), \
             patch.object(workflow_engine.state_manager, 'add_state_transition', return_value=True):
            
            success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                UserRole.CONTROLLER.value,
                assignment_data
            )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_technician_diagnostics_workflow(self, setup_workflow, sample_technician_data):
        """Test technician diagnostics and resolution workflow"""
        components = await setup_workflow
        workflow_engine = components['workflow_engine']
        
        request_id = "test-req-diag"
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=1,
            role_current =UserRole.TECHNICIAN.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description="Slow internet speed",
            state_data={'technician_id': sample_technician_data['id']}
        )
        
        # Test diagnostics start
        diagnostics_data = {
            'actor_id': sample_technician_data['id'],
            'diagnostics_started_at': str(datetime.now()),
            'diagnostics_notes': 'Checking connection parameters'
        }
        
        with patch.object(workflow_engine.state_manager, 'get_request', return_value=mock_request), \
             patch.object(workflow_engine.state_manager, 'update_request_state', return_value=True), \
             patch.object(workflow_engine.state_manager, 'add_state_transition', return_value=True):
            
            diagnostics_success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.START_DIAGNOSTICS.value,
                UserRole.TECHNICIAN.value,
                diagnostics_data
            )
        
        assert diagnostics_success is True
        
        # Test warehouse decision
        mock_request.state_data.update(diagnostics_data)
        
        decision_data = {
            'actor_id': sample_technician_data['id'],
            'warehouse_decision': 'no',
            'warehouse_decision_at': str(datetime.now())
        }
        
        with patch.object(workflow_engine.state_manager, 'get_request', return_value=mock_request), \
             patch.object(workflow_engine.state_manager, 'update_request_state', return_value=True), \
             patch.object(workflow_engine.state_manager, 'add_state_transition', return_value=True):
            
            decision_success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value,
                UserRole.TECHNICIAN.value,
                decision_data
            )
        
        assert decision_success is True
        
        # Test completion
        mock_request.state_data.update(decision_data)
        
        completion_data = {
            'actor_id': sample_technician_data['id'],
            'resolution_comments': 'Optimized network settings, speed improved',
            'completed_at': str(datetime.now()),
            'warehouse_involved': False
        }
        
        with patch.object(workflow_engine.state_manager, 'get_request', return_value=mock_request), \
             patch.object(workflow_engine.state_manager, 'update_request_state', return_value=True), \
             patch.object(workflow_engine.state_manager, 'add_state_transition', return_value=True):
            
            completion_success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value,
                UserRole.TECHNICIAN.value,
                completion_data
            )
        
        assert completion_success is True
    
    @pytest.mark.asyncio
    async def test_client_service_rating(self, setup_workflow, sample_client_data):
        """Test client rating of completed technical service"""
        components = await setup_workflow
        workflow_engine = components['workflow_engine']
        
        request_id = "test-req-rating"
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=sample_client_data['id'],
            role_current =UserRole.CLIENT.value,
            current_status=RequestStatus.COMPLETED.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description="Service completed",
            state_data={'completed_at': str(datetime.now())}
        )
        
        rating_data = {
            'rating': 4,
            'feedback': 'Good service, resolved the issue',
            'actor_id': sample_client_data['id'],
            'rated_at': str(datetime.now())
        }
        
        with patch.object(workflow_engine.state_manager, 'get_request', return_value=mock_request), \
             patch.object(workflow_engine.state_manager, 'update_request_state', return_value=True), \
             patch.object(workflow_engine.state_manager, 'add_state_transition', return_value=True):
            
            rating_success = await workflow_engine.complete_workflow(request_id, rating_data)
        
        assert rating_success is True
    
    @pytest.mark.asyncio
    async def test_notification_system_integration(self, setup_workflow, sample_controller_data, sample_technician_data):
        """Test notification system integration with workflow"""
        components = await setup_workflow
        notification_system = components['notification_system']
        mock_pool = components['mock_pool']
        
        # Mock database responses for notifications
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock users query
        mock_conn.fetch.return_value = [
            {
                'id': sample_controller_data['id'],
                'telegram_id': sample_controller_data['telegram_id'],
                'full_name': sample_controller_data['full_name'],
                'language': sample_controller_data['language']
            }
        ]
        
        # Mock request query
        mock_conn.fetchrow.return_value = {
            'description': 'Test technical issue',
            'priority': 'medium',
            'created_at': datetime.now()
        }
        
        # Mock notification insert
        mock_conn.execute.return_value = "INSERT 1"
        
        with patch('handlers.technical_service_workflow.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            # Test sending assignment notification
            success = await notification_system.send_assignment_notification(
                UserRole.CONTROLLER.value,
                "test-request-notify",
                WorkflowType.TECHNICAL_SERVICE.value
            )
        
        assert success is True
        mock_bot.send_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self, setup_workflow):
        """Test workflow state transitions and audit trail"""
        components = await setup_workflow
        state_manager = components['state_manager']
        mock_pool = components['mock_pool']
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = "INSERT 1"
        
        request_id = "test-transitions"
        
        # Test state transition recording
        success = await state_manager.record_state_transition(
            request_id,
            UserRole.CONTROLLER.value,
            UserRole.TECHNICIAN.value,
            WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
            2,  # actor_id
            {'technician_id': 3, 'assigned_at': str(datetime.now())},
            'Assigned to technician for diagnostics'
        )
        
        assert success is True
        mock_conn.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_transitions(self, setup_workflow):
        """Test error handling for invalid workflow transitions"""
        components = await setup_workflow
        workflow_engine = components['workflow_engine']
        
        # Mock invalid request
        with patch.object(workflow_engine.state_manager, 'get_request', return_value=None):
            success = await workflow_engine.transition_workflow(
                "invalid-request",
                WorkflowAction.START_DIAGNOSTICS.value,
                UserRole.TECHNICIAN.value,
                {'actor_id': 1}
            )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_workflow_status_retrieval(self, setup_workflow):
        """Test workflow status retrieval"""
        components = await setup_workflow
        workflow_engine = components['workflow_engine']
        
        request_id = "test-status"
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=1,
            role_current =UserRole.TECHNICIAN.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description="Test request",
            state_data={}
        )
        
        mock_transitions = [
            StateTransition(
                id=1,
                request_id=request_id,
                from_role=UserRole.CONTROLLER.value,
                to_role=UserRole.TECHNICIAN.value,
                action=WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                actor_id=2,
                created_at=datetime.now()
            )
        ]
        
        with patch.object(workflow_engine.state_manager, 'get_request', return_value=mock_request), \
             patch.object(workflow_engine.state_manager, 'get_request_history', return_value=mock_transitions):
            
            status = await workflow_engine.get_workflow_status(request_id)
        
        assert status is not None
        assert status.request_id == request_id
        assert status.role_current == UserRole.TECHNICIAN.value
        assert len(status.history) == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])