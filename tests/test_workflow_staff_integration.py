"""
Test workflow integration for staff-created applications
Tests that staff-created applications follow the same workflow paths as client-created applications
and that staff creation context is properly preserved throughout the workflow.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from database.models import (
    ServiceRequest, UserRole, WorkflowType, WorkflowAction, 
    RequestStatus, Priority
)
from utils.workflow_engine import WorkflowEngine
from utils.state_manager import StateManager
from utils.notification_system import NotificationSystem
from utils.workflow_integration import WorkflowIntegration


class TestWorkflowStaffIntegration:
    """Test workflow integration for staff-created applications"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = conn
        return pool, conn
    
    @pytest.fixture
    def mock_state_manager(self, mock_pool):
        """Mock state manager"""
        pool, conn = mock_pool
        state_manager = StateManager(pool)
        return state_manager
    
    @pytest.fixture
    def mock_notification_system(self, mock_pool):
        """Mock notification system"""
        pool, conn = mock_pool
        notification_system = NotificationSystem(pool)
        return notification_system
    
    @pytest.fixture
    def workflow_engine(self, mock_state_manager, mock_notification_system):
        """Create workflow engine with mocked dependencies"""
        return WorkflowEngine(
            mock_state_manager, 
            mock_notification_system, 
            inventory_manager=None
        )
    
    @pytest.mark.asyncio
    async def test_staff_created_connection_request_workflow_path(self, workflow_engine, mock_pool):
        """Test that staff-created connection requests follow the same workflow path as client-created"""
        pool, conn = mock_pool
        
        # Mock database responses
        conn.fetchrow.return_value = {
            'id': 'test-request-id',
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 123,
            'role_current': UserRole.MANAGER.value,
            'current_status': RequestStatus.CREATED.value,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'priority': Priority.MEDIUM.value,
            'description': 'Test connection request',
            'location': 'Test location',
            'contact_info': '{"full_name": "Test Client", "phone": "+998901234567"}',
            'state_data': '{"created_by_staff": true, "staff_creator_info": {"creator_role": "manager"}}',
            'equipment_used': '[]',
            'inventory_updated': False,
            'completion_rating': None,
            'feedback_comments': None,
            'created_by_staff': True,
            'staff_creator_id': 456,
            'staff_creator_role': 'manager',
            'creation_source': 'manager',
            'client_notified_at': None
        }
        
        # Test staff-created connection request data
        staff_request_data = {
            'client_id': 123,
            'description': 'Test connection request created by manager',
            'location': 'Test location',
            'contact_info': {
                'full_name': 'Test Client',
                'phone': '+998901234567'
            },
            'priority': Priority.MEDIUM.value,
            'created_by_staff': True,
            'staff_creator_info': {
                'creator_id': 456,
                'creator_role': 'manager',
                'creator_name': 'Test Manager'
            }
        }
        
        # Initiate workflow
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, 
            staff_request_data
        )
        
        # Verify workflow was initiated
        assert request_id is not None
        
        # Verify state manager was called to create request
        workflow_engine.state_manager.create_request.assert_called_once()
        
        # Verify notification system was called with staff context
        workflow_engine.notification_system.send_staff_workflow_notification.assert_called_once()
        workflow_engine.notification_system.send_staff_client_notification.assert_called_once()
        workflow_engine.notification_system.send_staff_confirmation_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_staff_created_technical_service_workflow_path(self, workflow_engine, mock_pool):
        """Test that staff-created technical service requests follow the same workflow path"""
        pool, conn = mock_pool
        
        # Mock database responses for technical service
        conn.fetchrow.return_value = {
            'id': 'test-tech-request-id',
            'workflow_type': WorkflowType.TECHNICAL_SERVICE.value,
            'client_id': 123,
            'role_current': UserRole.CONTROLLER.value,
            'current_status': RequestStatus.CREATED.value,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'priority': Priority.HIGH.value,
            'description': 'Test technical service request',
            'location': 'Test location',
            'contact_info': '{"full_name": "Test Client", "phone": "+998901234567"}',
            'state_data': '{"created_by_staff": true, "staff_creator_info": {"creator_role": "call_center"}}',
            'equipment_used': '[]',
            'inventory_updated': False,
            'completion_rating': None,
            'feedback_comments': None,
            'created_by_staff': True,
            'staff_creator_id': 789,
            'staff_creator_role': 'call_center',
            'creation_source': 'call_center',
            'client_notified_at': None
        }
        
        # Test staff-created technical service request data
        staff_request_data = {
            'client_id': 123,
            'description': 'Test technical service request created by call center',
            'location': 'Test location',
            'contact_info': {
                'full_name': 'Test Client',
                'phone': '+998901234567'
            },
            'priority': Priority.HIGH.value,
            'created_by_staff': True,
            'staff_creator_info': {
                'creator_id': 789,
                'creator_role': 'call_center',
                'creator_name': 'Test Call Center Operator'
            }
        }
        
        # Initiate workflow
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.TECHNICAL_SERVICE.value, 
            staff_request_data
        )
        
        # Verify workflow was initiated
        assert request_id is not None
        
        # Verify state manager was called to create request
        workflow_engine.state_manager.create_request.assert_called_once()
        
        # Verify notification system was called with staff context
        workflow_engine.notification_system.send_staff_workflow_notification.assert_called_once()
        workflow_engine.notification_system.send_staff_client_notification.assert_called_once()
        workflow_engine.notification_system.send_staff_confirmation_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_transition_preserves_staff_context(self, workflow_engine, mock_pool):
        """Test that workflow transitions preserve staff creation context"""
        pool, conn = mock_pool
        
        # Create a mock request with staff creation context
        mock_request = ServiceRequest(
            id='test-request-id',
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=123,
            role_current=UserRole.MANAGER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description='Test request',
            location='Test location',
            contact_info={'full_name': 'Test Client'},
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': 456,
                    'creator_role': 'manager',
                    'creator_name': 'Test Manager'
                }
            },
            created_by_staff=True,
            staff_creator_id=456,
            staff_creator_role='manager',
            creation_source='manager'
        )
        
        # Mock state manager to return the request
        workflow_engine.state_manager.get_request = AsyncMock(return_value=mock_request)
        workflow_engine.state_manager.update_request_state = AsyncMock(return_value=True)
        workflow_engine.state_manager.add_state_transition = AsyncMock(return_value=True)
        
        # Test workflow transition
        transition_data = {
            'actor_id': 789,
            'junior_manager_id': 101,
            'comments': 'Assigning to junior manager'
        }
        
        success = await workflow_engine.transition_workflow(
            'test-request-id',
            WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
            UserRole.MANAGER.value,
            transition_data
        )
        
        # Verify transition was successful
        assert success is True
        
        # Verify state was updated with enhanced transition data
        workflow_engine.state_manager.update_request_state.assert_called_once()
        call_args = workflow_engine.state_manager.update_request_state.call_args[0]
        updated_state = call_args[1]
        
        # Verify staff context is preserved in state data
        assert 'staff_created_workflow' in updated_state['state_data']
        assert updated_state['state_data']['staff_created_workflow'] is True
        assert 'original_staff_creator_info' in updated_state['state_data']
        
        # Verify transition was recorded with staff context
        workflow_engine.state_manager.add_state_transition.assert_called_once()
        transition_call_args = workflow_engine.state_manager.add_state_transition.call_args[0]
        transition = transition_call_args[0]
        
        # Verify transition comment includes staff context
        assert 'Staff-created request by manager' in transition.comments
    
    @pytest.mark.asyncio
    async def test_workflow_completion_with_staff_context(self, workflow_engine, mock_pool):
        """Test that workflow completion properly handles staff-created applications"""
        pool, conn = mock_pool
        
        # Create a mock request with staff creation context
        mock_request = ServiceRequest(
            id='test-request-id',
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=123,
            role_current=UserRole.WAREHOUSE.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description='Test request',
            location='Test location',
            contact_info={'full_name': 'Test Client'},
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': 456,
                    'creator_role': 'manager',
                    'creator_name': 'Test Manager'
                }
            },
            created_by_staff=True,
            staff_creator_id=456,
            staff_creator_role='manager',
            creation_source='manager'
        )
        
        # Mock state manager
        workflow_engine.state_manager.get_request = AsyncMock(return_value=mock_request)
        workflow_engine.state_manager.update_request_state = AsyncMock(return_value=True)
        workflow_engine.state_manager.add_state_transition = AsyncMock(return_value=True)
        
        # Test workflow completion
        completion_data = {
            'actor_id': 999,
            'rating': 5,
            'feedback': 'Excellent service'
        }
        
        success = await workflow_engine.complete_workflow('test-request-id', completion_data)
        
        # Verify completion was successful
        assert success is True
        
        # Verify state was updated to completed
        workflow_engine.state_manager.update_request_state.assert_called_once()
        call_args = workflow_engine.state_manager.update_request_state.call_args[0]
        updated_state = call_args[1]
        
        assert updated_state['current_status'] == RequestStatus.COMPLETED.value
        assert updated_state['completion_rating'] == 5
        assert updated_state['feedback_comments'] == 'Excellent service'
    
    @pytest.mark.asyncio
    async def test_workflow_integration_create_staff_request(self):
        """Test WorkflowIntegration.create_workflow_request for staff-created applications"""
        
        # Mock user data for staff member
        mock_staff_user = {
            'id': 456,
            'role': UserRole.MANAGER.value,
            'full_name': 'Test Manager',
            'telegram_id': 12345
        }
        
        # Mock workflow engine
        mock_workflow_engine = AsyncMock()
        mock_workflow_engine.initiate_workflow = AsyncMock(return_value='test-request-id')
        
        with patch('utils.workflow_integration.get_user_by_telegram_id', return_value=mock_staff_user), \
             patch.object(WorkflowIntegration, 'get_workflow_manager', return_value=mock_workflow_engine):
            
            # Test creating staff request
            request_data = {
                'client_id': 123,  # Different from staff member ID
                'description': 'Test staff-created request',
                'location': 'Test location',
                'contact_info': {
                    'full_name': 'Test Client',
                    'phone': '+998901234567'
                }
            }
            
            request_id = await WorkflowIntegration.create_workflow_request(
                WorkflowType.CONNECTION_REQUEST.value,
                12345,  # Staff member telegram ID
                request_data
            )
            
            # Verify request was created
            assert request_id == 'test-request-id'
            
            # Verify workflow engine was called with staff context
            mock_workflow_engine.initiate_workflow.assert_called_once()
            call_args = mock_workflow_engine.initiate_workflow.call_args[0]
            workflow_type, enhanced_request_data = call_args
            
            # Verify staff creation context was added
            assert enhanced_request_data['created_by_staff'] is True
            assert enhanced_request_data['client_id'] == 123
            assert enhanced_request_data['staff_creator_info']['creator_id'] == 456
            assert enhanced_request_data['staff_creator_info']['creator_role'] == UserRole.MANAGER.value
    
    @pytest.mark.asyncio
    async def test_workflow_integration_create_client_request(self):
        """Test WorkflowIntegration.create_workflow_request for client-created applications"""
        
        # Mock user data for client
        mock_client_user = {
            'id': 123,
            'role': UserRole.CLIENT.value,
            'full_name': 'Test Client',
            'telegram_id': 67890
        }
        
        # Mock workflow engine
        mock_workflow_engine = AsyncMock()
        mock_workflow_engine.initiate_workflow = AsyncMock(return_value='test-client-request-id')
        
        with patch('utils.workflow_integration.get_user_by_telegram_id', return_value=mock_client_user), \
             patch.object(WorkflowIntegration, 'get_workflow_manager', return_value=mock_workflow_engine):
            
            # Test creating client request
            request_data = {
                'description': 'Test client-created request',
                'location': 'Test location',
                'contact_info': {
                    'full_name': 'Test Client',
                    'phone': '+998901234567'
                }
            }
            
            request_id = await WorkflowIntegration.create_workflow_request(
                WorkflowType.CONNECTION_REQUEST.value,
                67890,  # Client telegram ID
                request_data
            )
            
            # Verify request was created
            assert request_id == 'test-client-request-id'
            
            # Verify workflow engine was called with client context
            mock_workflow_engine.initiate_workflow.assert_called_once()
            call_args = mock_workflow_engine.initiate_workflow.call_args[0]
            workflow_type, enhanced_request_data = call_args
            
            # Verify client creation context
            assert enhanced_request_data['created_by_staff'] is False
            assert enhanced_request_data['client_id'] == 123  # Same as user ID for client
            assert 'staff_creator_info' not in enhanced_request_data
    
    @pytest.mark.asyncio
    async def test_staff_request_missing_client_id_error(self):
        """Test that staff-created requests without client_id are rejected"""
        
        # Mock user data for staff member
        mock_staff_user = {
            'id': 456,
            'role': UserRole.MANAGER.value,
            'full_name': 'Test Manager',
            'telegram_id': 12345
        }
        
        with patch('utils.workflow_integration.get_user_by_telegram_id', return_value=mock_staff_user):
            
            # Test creating staff request without client_id
            request_data = {
                # Missing client_id
                'description': 'Test staff-created request',
                'location': 'Test location'
            }
            
            request_id = await WorkflowIntegration.create_workflow_request(
                WorkflowType.CONNECTION_REQUEST.value,
                12345,  # Staff member telegram ID
                request_data
            )
            
            # Verify request creation failed
            assert request_id is None


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])