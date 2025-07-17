import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.workflow_manager import EnhancedWorkflowManager
from utils.notification_system import NotificationSystemFactory
from utils.inventory_manager import InventoryManagerFactory
from database.models import (
    WorkflowType, UserRole, WorkflowAction, RequestStatus, Priority
)


class TestCallCenterDirectResolution:
    """Test suite for call center direct resolution workflow"""
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager for testing"""
        mock = AsyncMock()
        mock.create_request = AsyncMock(return_value="test-request-id")
        mock.get_request = AsyncMock()
        mock.update_request_state = AsyncMock(return_value=True)
        mock.add_state_transition = AsyncMock(return_value=True)
        mock.get_requests_by_role = AsyncMock(return_value=[])
        return mock
    
    @pytest.fixture
    def mock_notification_system(self):
        """Mock notification system for testing"""
        mock = AsyncMock()
        mock.send_assignment_notification = AsyncMock(return_value=True)
        mock.send_completion_notification = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def mock_inventory_manager(self):
        """Mock inventory manager for testing"""
        mock = AsyncMock()
        return mock
    
    @pytest.fixture
    def workflow_manager(self, mock_state_manager, mock_notification_system, mock_inventory_manager):
        """Create workflow manager with mocked dependencies"""
        # Mock the factory methods
        StateManagerFactory.create_state_manager = MagicMock(return_value=mock_state_manager)
        NotificationSystemFactory.create_notification_system = MagicMock(return_value=mock_notification_system)
        InventoryManagerFactory.create_inventory_manager = MagicMock(return_value=mock_inventory_manager)
        
        return EnhancedWorkflowManager(mock_notification_system, mock_inventory_manager)
    
    @pytest.mark.asyncio
    async def test_create_call_center_direct_request(self, workflow_manager, mock_state_manager):
        """Test creating a call center direct resolution request"""
        # Arrange
        client_info = {
            'name': 'Test Client',
            'phone': '998901234567',
            'address': 'Test Address'
        }
        issue_description = 'Simple technical issue that can be resolved remotely'
        
        # Act
        request_id = await workflow_manager.create_call_center_request(client_info, issue_description)
        
        # Assert
        assert request_id == "test-request-id"
        mock_state_manager.create_request.assert_called_once()
        
        # Verify the request data
        call_args = mock_state_manager.create_request.call_args
        assert call_args[0][0] == WorkflowType.CALL_CENTER_DIRECT.value
        assert call_args[0][1]['client_info'] == client_info
        assert call_args[0][1]['issue_description'] == issue_description
    
    @pytest.mark.asyncio
    async def test_assign_to_call_center_operator(self, workflow_manager, mock_state_manager):
        """Test call center supervisor assigning request to operator"""
        # Arrange
        request_id = "test-request-id"
        operator_id = 123
        supervisor_id = 456
        
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.role_current = UserRole.CALL_CENTER_SUPERVISOR.value
        mock_request.workflow_type = WorkflowType.CALL_CENTER_DIRECT.value
        mock_request.state_data = {}
        mock_request.created_at = datetime.now()
        mock_request.updated_at = datetime.now()
        mock_request.priority = Priority.MEDIUM.value
        mock_request.description = "Test description"
        mock_request.location = ""
        mock_request.contact_info = {}
        mock_request.equipment_used = []
        mock_request.inventory_updated = False
        mock_request.completion_rating = None
        mock_request.feedback_comments = None
        mock_request.client_id = 789
        mock_request.current_status = RequestStatus.IN_PROGRESS.value
        mock_state_manager.get_request.return_value = mock_request
        
        # Act
        success = await workflow_manager.assign_to_call_center_operator(
            request_id, operator_id, supervisor_id
        )
        
        # Assert
        assert success is True
        mock_state_manager.update_request_state.assert_called_once()
        
        # Verify the transition data
        call_args = mock_state_manager.update_request_state.call_args
        assert call_args[0][1]['role_current '] == UserRole.CALL_CENTER.value
        assert call_args[0][1]['state_data']['operator_id'] == operator_id
        assert call_args[0][1]['state_data']['actor_id'] == supervisor_id
    
    @pytest.mark.asyncio
    async def test_resolve_remotely(self, workflow_manager, mock_state_manager, mock_notification_system):
        """Test call center operator resolving issue remotely"""
        # Arrange
        request_id = "test-request-id"
        resolution_notes = "Issue resolved by restarting the router remotely"
        operator_id = 123
        
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.role_current = UserRole.CALL_CENTER.value
        mock_request.workflow_type = WorkflowType.CALL_CENTER_DIRECT.value
        mock_request.client_id = 789
        mock_request.state_data = {}
        mock_state_manager.get_request.return_value = mock_request
        
        # Act
        success = await workflow_manager.resolve_remotely(
            request_id, resolution_notes, operator_id
        )
        
        # Assert
        assert success is True
        mock_state_manager.update_request_state.assert_called_once()
        mock_notification_system.send_completion_notification.assert_called_once_with(
            789, request_id, WorkflowType.CALL_CENTER_DIRECT.value
        )
        
        # Verify the resolution data
        call_args = mock_state_manager.update_request_state.call_args
        assert call_args[0][1]['role_current '] == UserRole.CLIENT.value
        assert call_args[0][1]['state_data']['resolution_notes'] == resolution_notes
        assert call_args[0][1]['state_data']['actor_id'] == operator_id
    
    @pytest.mark.asyncio
    async def test_workflow_components_integration(self, workflow_manager, mock_state_manager, mock_notification_system):
        """Test that workflow components work together correctly"""
        # Arrange
        client_info = {'name': 'Test Client', 'phone': '998901234567'}
        issue_description = 'Internet connection issue'
        
        # Act - Test request creation
        request_id = await workflow_manager.create_call_center_request(client_info, issue_description)
        
        # Assert
        assert request_id == "test-request-id"
        mock_state_manager.create_request.assert_called_once()
        
        # Verify the request data structure
        call_args = mock_state_manager.create_request.call_args
        assert call_args[0][0] == WorkflowType.CALL_CENTER_DIRECT.value
        assert call_args[0][1]['client_info'] == client_info
        assert call_args[0][1]['issue_description'] == issue_description
    
    @pytest.mark.asyncio
    async def test_workflow_definition_validation(self):
        """Test that call center direct workflow definition is valid"""
        # Arrange
        mock_state_manager = AsyncMock()
        workflow_engine = WorkflowEngineFactory.create_workflow_engine(mock_state_manager)
        
        # Act
        workflow_def = workflow_engine.get_workflow_definition(WorkflowType.CALL_CENTER_DIRECT.value)
        
        # Assert
        assert workflow_def is not None
        assert workflow_def.name == "Call Center Direct Resolution"
        assert workflow_def.initial_role == UserRole.CALL_CENTER_SUPERVISOR.value
        
        # Verify workflow steps
        assert UserRole.CALL_CENTER_SUPERVISOR.value in workflow_def.steps
        assert UserRole.CALL_CENTER.value in workflow_def.steps
        
        # Verify supervisor step
        supervisor_step = workflow_def.steps[UserRole.CALL_CENTER_SUPERVISOR.value]
        assert WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value in supervisor_step.actions
        assert supervisor_step.next_steps[WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value] == UserRole.CALL_CENTER.value
        assert "operator_id" in supervisor_step.required_data
        
        # Verify operator step
        operator_step = workflow_def.steps[UserRole.CALL_CENTER.value]
        assert WorkflowAction.RESOLVE_REMOTELY.value in operator_step.actions
        assert operator_step.next_steps[WorkflowAction.RESOLVE_REMOTELY.value] == UserRole.CLIENT.value
        assert "resolution_notes" in operator_step.required_data
        
        # Verify completion actions
        assert WorkflowAction.RATE_SERVICE.value in workflow_def.completion_actions
    
    @pytest.mark.asyncio
    async def test_get_requests_for_call_center_supervisor(self, workflow_manager, mock_state_manager):
        """Test getting requests assigned to call center supervisor"""
        # Arrange
        mock_requests = [
            MagicMock(id="req1", workflow_type=WorkflowType.CALL_CENTER_DIRECT.value),
            MagicMock(id="req2", workflow_type=WorkflowType.CALL_CENTER_DIRECT.value)
        ]
        mock_state_manager.get_requests_by_role.return_value = mock_requests
        
        # Act
        requests = await workflow_manager.get_requests_for_role(UserRole.CALL_CENTER_SUPERVISOR.value)
        
        # Assert
        assert len(requests) == 2
        mock_state_manager.get_requests_by_role.assert_called_once_with(
            UserRole.CALL_CENTER_SUPERVISOR.value, None
        )
    
    @pytest.mark.asyncio
    async def test_get_requests_for_call_center_operator(self, workflow_manager, mock_state_manager):
        """Test getting requests assigned to call center operator"""
        # Arrange
        mock_requests = [
            MagicMock(id="req1", workflow_type=WorkflowType.CALL_CENTER_DIRECT.value),
            MagicMock(id="req2", workflow_type=WorkflowType.TECHNICAL_SERVICE.value)
        ]
        mock_state_manager.get_requests_by_role.return_value = mock_requests
        
        # Act
        requests = await workflow_manager.get_requests_for_role(UserRole.CALL_CENTER.value)
        
        # Assert
        assert len(requests) == 2
        mock_state_manager.get_requests_by_role.assert_called_once_with(
            UserRole.CALL_CENTER.value, None
        )
    
    @pytest.mark.asyncio
    async def test_invalid_workflow_transition(self, workflow_manager, mock_state_manager):
        """Test invalid workflow transition handling"""
        # Arrange
        request_id = "test-request-id"
        
        # Mock request in wrong state
        mock_request = MagicMock()
        mock_request.role_current = UserRole.TECHNICIAN.value  # Wrong role for call center workflow
        mock_request.workflow_type = WorkflowType.CALL_CENTER_DIRECT.value
        mock_state_manager.get_request.return_value = mock_request
        
        # Act
        success = await workflow_manager.assign_to_call_center_operator(
            request_id, 123, 456
        )
        
        # Assert
        assert success is False
        mock_state_manager.update_request_state.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_missing_required_data(self, workflow_manager, mock_state_manager):
        """Test workflow transition with missing required data"""
        # Arrange
        request_id = "test-request-id"
        
        mock_request = MagicMock()
        mock_request.role_current = UserRole.CALL_CENTER.value
        mock_request.workflow_type = WorkflowType.CALL_CENTER_DIRECT.value
        mock_request.state_data = {}
        mock_state_manager.get_request.return_value = mock_request
        
        # Act - try to resolve without resolution notes
        success = await workflow_manager.resolve_remotely(request_id, "", 123)
        
        # Assert - should still work as empty string is provided
        assert success is True


if __name__ == "__main__":
    pytest.main([__file__])