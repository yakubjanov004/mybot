"""
Test workflow engine integration with staff notification system
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from utils.workflow_engine import WorkflowEngine
from utils.notification_system import NotificationSystem
from database.models import UserRole, WorkflowType


class TestWorkflowStaffNotificationIntegration:
    """Test workflow engine integration with staff notifications"""
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_notification_system(self):
        """Mock notification system"""
        return AsyncMock(spec=NotificationSystem)
    
    @pytest.fixture
    def mock_inventory_manager(self):
        """Mock inventory manager"""
        return AsyncMock()
    
    @pytest.fixture
    def workflow_engine(self, mock_state_manager, mock_notification_system, mock_inventory_manager):
        """Create workflow engine with mocked dependencies"""
        return WorkflowEngine(
            state_manager=mock_state_manager,
            notification_system=mock_notification_system,
            inventory_manager=mock_inventory_manager
        )
    
    @pytest.mark.asyncio
    async def test_initiate_workflow_staff_created_application(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test workflow initiation for staff-created application"""
        # Mock request data for staff-created application
        request_data = {
            'client_id': 1,
            'description': 'Test connection request',
            'location': 'Test address',
            'contact_info': {
                'full_name': 'Test Client',
                'phone': '+998901234567'
            },
            'created_by_staff': True,
            'staff_creator_info': {
                'creator_id': 2,
                'creator_role': 'manager',
                'session_id': 'test_session'
            }
        }
        
        # Mock state manager responses
        mock_request_id = 'test_request_123'
        mock_state_manager.create_request.return_value = mock_request_id
        
        # Mock request object
        mock_request = MagicMock()
        mock_request.role_current = UserRole.MANAGER.value
        mock_state_manager.get_request.return_value = mock_request
        
        # Mock notification system methods
        mock_notification_system.send_staff_workflow_notification.return_value = True
        mock_notification_system.send_staff_client_notification.return_value = True
        mock_notification_system.send_staff_confirmation_notification.return_value = True
        
        # Initiate workflow
        result_request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value,
            request_data
        )
        
        # Verify request was created
        assert result_request_id == mock_request_id
        mock_state_manager.create_request.assert_called_once()
        mock_state_manager.add_state_transition.assert_called_once()
        
        # Verify staff notifications were sent
        mock_notification_system.send_staff_workflow_notification.assert_called_once_with(
            UserRole.MANAGER.value,
            mock_request_id,
            WorkflowType.CONNECTION_REQUEST.value,
            'manager',
            'Test Client',
            request_data
        )
        
        mock_notification_system.send_staff_client_notification.assert_called_once_with(
            1,  # client_id
            mock_request_id,
            WorkflowType.CONNECTION_REQUEST.value,
            'manager',
            request_data
        )
        
        mock_notification_system.send_staff_confirmation_notification.assert_called_once_with(
            2,  # staff_creator_id
            mock_request_id,
            WorkflowType.CONNECTION_REQUEST.value,
            'Test Client',
            request_data
        )
    
    @pytest.mark.asyncio
    async def test_initiate_workflow_client_created_application(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test workflow initiation for client-created application (regular flow)"""
        # Mock request data for client-created application
        request_data = {
            'client_id': 1,
            'description': 'Test connection request',
            'location': 'Test address',
            'contact_info': {
                'full_name': 'Test Client',
                'phone': '+998901234567'
            },
            'created_by_staff': False  # Client-created
        }
        
        # Mock state manager responses
        mock_request_id = 'test_request_123'
        mock_state_manager.create_request.return_value = mock_request_id
        
        # Mock request object
        mock_request = MagicMock()
        mock_request.role_current = UserRole.MANAGER.value
        mock_state_manager.get_request.return_value = mock_request
        
        # Mock notification system methods
        mock_notification_system.send_assignment_notification.return_value = True
        
        # Initiate workflow
        result_request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value,
            request_data
        )
        
        # Verify request was created
        assert result_request_id == mock_request_id
        
        # Verify regular notification was sent (not staff notifications)
        mock_notification_system.send_assignment_notification.assert_called_once_with(
            UserRole.MANAGER.value,
            mock_request_id,
            WorkflowType.CONNECTION_REQUEST.value
        )
        
        # Verify staff notifications were NOT sent
        mock_notification_system.send_staff_workflow_notification.assert_not_called()
        mock_notification_system.send_staff_client_notification.assert_not_called()
        mock_notification_system.send_staff_confirmation_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_transition_workflow_staff_created_application(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test workflow transition for staff-created application"""
        # Mock current request state
        mock_request = MagicMock()
        mock_request.id = 'test_request_123'
        mock_request.workflow_type = WorkflowType.CONNECTION_REQUEST.value
        mock_request.role_current = UserRole.MANAGER.value
        mock_request.state_data = {
            'created_by_staff': True,
            'staff_creator_info': {
                'creator_id': 2,
                'creator_role': 'manager'
            }
        }
        mock_request.contact_info = {
            'full_name': 'Test Client'
        }
        
        mock_state_manager.get_request.return_value = mock_request
        mock_state_manager.update_request_state.return_value = True
        mock_state_manager.add_state_transition.return_value = True
        
        # Mock notification system
        mock_notification_system.send_staff_workflow_notification.return_value = True
        
        # Mock workflow definition
        workflow_engine.workflow_definitions[WorkflowType.CONNECTION_REQUEST.value].steps[UserRole.MANAGER.value].actions = ['assign_to_junior_manager']
        workflow_engine.workflow_definitions[WorkflowType.CONNECTION_REQUEST.value].steps[UserRole.MANAGER.value].next_steps = {'assign_to_junior_manager': UserRole.JUNIOR_MANAGER.value}
        
        # Transition workflow
        result = await workflow_engine.transition_workflow(
            'test_request_123',
            'assign_to_junior_manager',
            UserRole.MANAGER.value,
            {'actor_id': 2, 'junior_manager_id': 3}
        )
        
        # Verify transition was successful
        assert result is True
        
        # Verify staff workflow notification was sent
        mock_notification_system.send_staff_workflow_notification.assert_called_once_with(
            UserRole.JUNIOR_MANAGER.value,
            'test_request_123',
            WorkflowType.CONNECTION_REQUEST.value,
            'manager',
            'Test Client',
            mock_request.state_data
        )
        
        # Verify regular assignment notification was NOT sent
        mock_notification_system.send_assignment_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_transition_workflow_client_created_application(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test workflow transition for client-created application (regular flow)"""
        # Mock current request state
        mock_request = MagicMock()
        mock_request.id = 'test_request_123'
        mock_request.workflow_type = WorkflowType.CONNECTION_REQUEST.value
        mock_request.role_current = UserRole.MANAGER.value
        mock_request.state_data = {
            'created_by_staff': False  # Client-created
        }
        
        mock_state_manager.get_request.return_value = mock_request
        mock_state_manager.update_request_state.return_value = True
        mock_state_manager.add_state_transition.return_value = True
        
        # Mock notification system
        mock_notification_system.send_assignment_notification.return_value = True
        
        # Mock workflow definition
        workflow_engine.workflow_definitions[WorkflowType.CONNECTION_REQUEST.value].steps[UserRole.MANAGER.value].actions = ['assign_to_junior_manager']
        workflow_engine.workflow_definitions[WorkflowType.CONNECTION_REQUEST.value].steps[UserRole.MANAGER.value].next_steps = {'assign_to_junior_manager': UserRole.JUNIOR_MANAGER.value}
        
        # Transition workflow
        result = await workflow_engine.transition_workflow(
            'test_request_123',
            'assign_to_junior_manager',
            UserRole.MANAGER.value,
            {'actor_id': 2, 'junior_manager_id': 3}
        )
        
        # Verify transition was successful
        assert result is True
        
        # Verify regular assignment notification was sent
        mock_notification_system.send_assignment_notification.assert_called_once_with(
            UserRole.JUNIOR_MANAGER.value,
            'test_request_123',
            WorkflowType.CONNECTION_REQUEST.value
        )
        
        # Verify staff workflow notification was NOT sent
        mock_notification_system.send_staff_workflow_notification.assert_not_called()
    
    def test_workflow_definitions_loaded(self, workflow_engine):
        """Test that workflow definitions are properly loaded"""
        definitions = workflow_engine.workflow_definitions
        
        # Verify main workflow types exist
        assert WorkflowType.CONNECTION_REQUEST.value in definitions
        assert WorkflowType.TECHNICAL_SERVICE.value in definitions
        assert WorkflowType.CALL_CENTER_DIRECT.value in definitions
        
        # Verify workflow steps are defined
        connection_workflow = definitions[WorkflowType.CONNECTION_REQUEST.value]
        assert UserRole.CLIENT.value in connection_workflow.steps
        assert UserRole.MANAGER.value in connection_workflow.steps
        assert UserRole.JUNIOR_MANAGER.value in connection_workflow.steps
        assert UserRole.CONTROLLER.value in connection_workflow.steps
        assert UserRole.TECHNICIAN.value in connection_workflow.steps
        assert UserRole.WAREHOUSE.value in connection_workflow.steps


if __name__ == '__main__':
    pytest.main([__file__])