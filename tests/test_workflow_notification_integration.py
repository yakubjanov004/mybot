"""
Integration tests for Workflow Engine and Notification System
Tests the integration between workflow transitions and notification delivery
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from utils.workflow_engine import WorkflowEngine
from utils.state_manager import StateManager
from utils.notification_system import NotificationSystem
from database.models import UserRole, WorkflowType, RequestStatus


class TestWorkflowNotificationIntegration:
    """Test integration between workflow engine and notification system"""
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager"""
        return AsyncMock(spec=StateManager)
    
    @pytest.fixture
    def mock_notification_system(self):
        """Mock notification system"""
        return AsyncMock(spec=NotificationSystem)
    
    @pytest.fixture
    def workflow_engine(self, mock_state_manager, mock_notification_system):
        """Create workflow engine with mocked dependencies"""
        return WorkflowEngine(
            state_manager=mock_state_manager,
            notification_system=mock_notification_system,
            inventory_manager=None
        )
    
    @pytest.mark.asyncio
    async def test_workflow_initiation_creates_notification(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test that workflow initiation creates appropriate notifications"""
        request_data = {
            'client_id': 123,
            'description': 'Test connection request',
            'location': 'Test Location',
            'contact_info': {'phone': '+998901234567'},
            'priority': 'high'
        }
        
        # Mock state manager responses
        mock_state_manager.create_request.return_value = None
        mock_state_manager.add_state_transition.return_value = None
        
        # Mock notification system
        mock_notification_system.send_assignment_notification.return_value = True
        
        # Initiate workflow
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, request_data
        )
        
        # Verify request was created
        assert request_id is not None
        mock_state_manager.create_request.assert_called_once()
        mock_state_manager.add_state_transition.assert_called_once()
        
        # Verify notification was not sent during initiation (only on transitions)
        mock_notification_system.send_assignment_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_workflow_transition_sends_notification(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test that workflow transitions send notifications to next role"""
        request_id = str(uuid.uuid4())
        
        # Mock current request state
        from database.models import ServiceRequest
        current_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=123,
            role_current =UserRole.MANAGER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority='high',
            description='Test request',
            location='Test Location',
            contact_info={'phone': '+998901234567'},
            state_data={'initial': 'data'}
        )
        
        # Mock state manager responses
        mock_state_manager.get_request.return_value = current_request
        mock_state_manager.update_request_state.return_value = True
        mock_state_manager.add_state_transition.return_value = True
        
        # Mock notification system
        mock_notification_system.send_assignment_notification.return_value = True
        
        # Perform workflow transition
        transition_data = {
            'junior_manager_id': 456,
            'actor_id': 789,
            'comments': 'Assigned to junior manager'
        }
        
        result = await workflow_engine.transition_workflow(
            request_id, 'assign_to_junior_manager', UserRole.MANAGER.value, transition_data
        )
        
        # Verify transition was successful
        assert result == True
        
        # Verify state was updated
        mock_state_manager.update_request_state.assert_called_once()
        mock_state_manager.add_state_transition.assert_called_once()
        
        # Verify notification was sent to next role
        mock_notification_system.send_assignment_notification.assert_called_once_with(
            UserRole.JUNIOR_MANAGER.value, request_id, WorkflowType.CONNECTION_REQUEST.value
        )
    
    @pytest.mark.asyncio
    async def test_workflow_transition_no_role_change_no_notification(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test that transitions without role change don't send notifications"""
        request_id = str(uuid.uuid4())
        
        # Mock current request state
        from database.models import ServiceRequest
        current_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=123,
            role_current =UserRole.TECHNICIAN.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority='medium',
            description='Test technical request',
            state_data={'diagnostics': 'in_progress'}
        )
        
        # Mock state manager responses
        mock_state_manager.get_request.return_value = current_request
        mock_state_manager.update_request_state.return_value = True
        mock_state_manager.add_state_transition.return_value = True
        
        # Mock notification system
        mock_notification_system.send_assignment_notification.return_value = True
        
        # Perform workflow transition that doesn't change role (intermediate action)
        transition_data = {
            'diagnostics_notes': 'Completed initial diagnostics',
            'actor_id': 789,
            'comments': 'Diagnostics completed'
        }
        
        result = await workflow_engine.transition_workflow(
            request_id, 'start_diagnostics', UserRole.TECHNICIAN.value, transition_data
        )
        
        # Verify transition was successful
        assert result == True
        
        # Verify state was updated
        mock_state_manager.update_request_state.assert_called_once()
        mock_state_manager.add_state_transition.assert_called_once()
        
        # Verify no notification was sent (same role)
        mock_notification_system.send_assignment_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_workflow_engine_without_notification_system(self, mock_state_manager):
        """Test that workflow engine works without notification system"""
        # Create workflow engine without notification system
        workflow_engine = WorkflowEngine(
            state_manager=mock_state_manager,
            notification_system=None,
            inventory_manager=None
        )
        
        request_id = str(uuid.uuid4())
        
        # Mock current request state
        from database.models import ServiceRequest
        current_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=123,
            role_current =UserRole.MANAGER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority='high',
            description='Test request',
            state_data={'initial': 'data'}
        )
        
        # Mock state manager responses
        mock_state_manager.get_request.return_value = current_request
        mock_state_manager.update_request_state.return_value = True
        mock_state_manager.add_state_transition.return_value = True
        
        # Perform workflow transition
        transition_data = {
            'junior_manager_id': 456,
            'actor_id': 789,
            'comments': 'Assigned to junior manager'
        }
        
        # Should not raise exception even without notification system
        result = await workflow_engine.transition_workflow(
            request_id, 'assign_to_junior_manager', UserRole.MANAGER.value, transition_data
        )
        
        # Verify transition was successful
        assert result == True
        
        # Verify state was updated
        mock_state_manager.update_request_state.assert_called_once()
        mock_state_manager.add_state_transition.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notification_system_excluded_roles(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test that notifications are not sent to excluded roles"""
        request_id = str(uuid.uuid4())
        
        # Mock current request state transitioning to client (excluded role)
        from database.models import ServiceRequest
        current_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=123,
            role_current =UserRole.WAREHOUSE.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority='high',
            description='Test request',
            state_data={'inventory_updated': True}
        )
        
        # Mock state manager responses
        mock_state_manager.get_request.return_value = current_request
        mock_state_manager.update_request_state.return_value = True
        mock_state_manager.add_state_transition.return_value = True
        
        # Mock notification system to return True for excluded roles
        mock_notification_system.send_assignment_notification.return_value = True
        
        # Perform workflow transition to client (excluded role)
        transition_data = {
            'inventory_updates': ['item1', 'item2'],
            'actor_id': 789,
            'comments': 'Request completed, notifying client'
        }
        
        result = await workflow_engine.transition_workflow(
            request_id, 'close_request', UserRole.WAREHOUSE.value, transition_data
        )
        
        # Verify transition was successful
        assert result == True
        
        # Verify notification was still called (notification system handles exclusion internally)
        mock_notification_system.send_assignment_notification.assert_called_once_with(
            UserRole.CLIENT.value, request_id, WorkflowType.CONNECTION_REQUEST.value
        )


class TestNotificationSystemWorkflowIntegration:
    """Test notification system integration with workflow concepts"""
    
    def test_notification_system_role_exclusion(self):
        """Test that notification system properly excludes client and admin roles"""
        notification_system = NotificationSystem()
        
        # Test excluded roles
        assert UserRole.CLIENT.value in notification_system.excluded_roles
        assert UserRole.ADMIN.value in notification_system.excluded_roles
        
        # Test non-excluded roles
        workflow_roles = [
            UserRole.TECHNICIAN.value,
            UserRole.MANAGER.value,
            UserRole.WAREHOUSE.value,
            UserRole.CONTROLLER.value,
            UserRole.JUNIOR_MANAGER.value,
            UserRole.CALL_CENTER.value,
            UserRole.CALL_CENTER_SUPERVISOR.value
        ]
        
        for role in workflow_roles:
            assert role not in notification_system.excluded_roles
    
    @pytest.mark.asyncio
    async def test_notification_system_workflow_type_support(self):
        """Test that notification system supports all workflow types"""
        notification_system = NotificationSystem()
        
        # Test workflow type translations exist
        workflow_types = [
            WorkflowType.CONNECTION_REQUEST.value,
            WorkflowType.TECHNICAL_SERVICE.value,
            WorkflowType.CALL_CENTER_DIRECT.value
        ]
        
        # Mock user and request data
        user = {
            'id': 1,
            'telegram_id': 123456789,
            'full_name': 'Test User',
            'language': 'ru'
        }
        
        request_data = {
            'description': 'Test request',
            'priority': 'medium',
            'created_at': datetime.now()
        }
        
        # Test that all workflow types can be processed
        with patch('loader.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            for workflow_type in workflow_types:
                await notification_system._send_notification_message(
                    user, str(uuid.uuid4()), workflow_type, 
                    request_data, str(uuid.uuid4())
                )
                
                # Verify message was sent
                assert mock_bot.send_message.called
                mock_bot.send_message.reset_mock()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])