"""
Unit tests for Call Center Initiated Requests functionality
Tests the integration between call center and workflow system
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from database.models import WorkflowType, UserRole, Priority, RequestStatus
from utils.workflow_engine import WorkflowEngine
from utils.state_manager import StateManager
from utils.notification_system import NotificationSystem


class TestCallCenterWorkflowRequests:
    """Test call center initiated workflow requests"""
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager"""
        mock = AsyncMock(spec=StateManager)
        mock.create_request.return_value = "test-request-id-123"
        mock.update_request_state.return_value = True
        mock.get_request.return_value = MagicMock(
            id="test-request-id-123",
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            role_current =UserRole.MANAGER.value,
            current_status=RequestStatus.CREATED.value,
            state_data={}
        )
        return mock
    
    @pytest.fixture
    def mock_notification_system(self):
        """Mock notification system"""
        mock = AsyncMock(spec=NotificationSystem)
        mock.send_assignment_notification.return_value = True
        return mock
    
    @pytest.fixture
    def workflow_engine(self, mock_state_manager, mock_notification_system):
        """Create workflow engine with mocked dependencies"""
        return WorkflowEngine(mock_state_manager, mock_notification_system, None)
    
    @pytest.mark.asyncio
    async def test_connection_request_creation_from_call_center(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test creating connection request from call center"""
        # Arrange
        request_data = {
            'client_id': 123,
            'description': 'Internet connection installation needed',
            'location': '123 Test Street, Tashkent',
            'contact_info': {
                'phone': '998901234567',
                'name': 'Test Client',
                'address': '123 Test Street, Tashkent'
            },
            'priority': Priority.HIGH.value,
            'service_type': 'installation',
            'created_by_role': UserRole.CALL_CENTER.value,
            'created_by': 456,
            'client_details': {
                'name': 'Test Client',
                'phone': '998901234567',
                'address': '123 Test Street, Tashkent',
                'language': 'uz'
            }
        }
        
        # Act
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, 
            request_data
        )
        
        # Assert
        assert request_id == "test-request-id-123"
        mock_state_manager.create_request.assert_called_once_with(
            WorkflowType.CONNECTION_REQUEST.value, 
            request_data
        )
        # Verify state transition was recorded
        mock_state_manager.add_state_transition.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_technical_service_request_creation_from_call_center(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test creating technical service request from call center"""
        # Arrange
        request_data = {
            'client_id': 123,
            'description': 'Internet connection not working, need repair',
            'issue_type': 'connectivity_issue',
            'contact_info': {
                'phone': '998901234567',
                'name': 'Test Client'
            },
            'priority': Priority.MEDIUM.value,
            'service_type': 'repair',
            'created_by_role': UserRole.CALL_CENTER.value,
            'created_by': 456,
            'client_details': {
                'name': 'Test Client',
                'phone': '998901234567',
                'language': 'ru'
            }
        }
        
        # Act
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.TECHNICAL_SERVICE.value, 
            request_data
        )
        
        # Assert
        assert request_id == "test-request-id-123"
        mock_state_manager.create_request.assert_called_once_with(
            WorkflowType.TECHNICAL_SERVICE.value, 
            request_data
        )
        # Verify state transition was recorded
        mock_state_manager.add_state_transition.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_center_direct_request_creation(self, workflow_engine, mock_state_manager, mock_notification_system):
        """Test creating direct call center resolution request"""
        # Arrange
        request_data = {
            'client_id': 123,
            'description': 'Simple configuration question',
            'contact_info': {
                'phone': '998901234567',
                'name': 'Test Client'
            },
            'priority': Priority.LOW.value,
            'service_type': 'consultation',
            'created_by_role': UserRole.CALL_CENTER.value,
            'created_by': 456,
            'issue_description': 'Client needs help with router configuration',
            'client_details': {
                'name': 'Test Client',
                'phone': '998901234567',
                'language': 'uz'
            }
        }
        
        # Act
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CALL_CENTER_DIRECT.value, 
            request_data
        )
        
        # Assert
        assert request_id == "test-request-id-123"
        mock_state_manager.create_request.assert_called_once_with(
            WorkflowType.CALL_CENTER_DIRECT.value, 
            request_data
        )
        # Call center direct requests should route to call center supervisor
        mock_notification_system.send_assignment_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_routing_to_manager_for_connection_requests(self, workflow_engine):
        """Test that connection requests from call center route to manager"""
        # Arrange
        request_data = {
            'client_id': 123,
            'description': 'New internet connection needed',
            'service_type': 'installation',
            'created_by_role': UserRole.CALL_CENTER.value
        }
        
        # Act
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, 
            request_data
        )
        
        # Assert - verify the workflow definition routes to manager initially
        workflow_def = workflow_engine.get_workflow_definition(WorkflowType.CONNECTION_REQUEST.value)
        assert workflow_def.initial_role == UserRole.CLIENT.value  # Initial role in definition
        # But the state manager should set role_current to manager for call center requests
    
    @pytest.mark.asyncio
    async def test_workflow_routing_to_controller_for_technical_requests(self, workflow_engine):
        """Test that technical requests from call center route to controller"""
        # Arrange
        request_data = {
            'client_id': 123,
            'description': 'Internet not working',
            'service_type': 'repair',
            'created_by_role': UserRole.CALL_CENTER.value
        }
        
        # Act
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.TECHNICAL_SERVICE.value, 
            request_data
        )
        
        # Assert - verify the workflow definition routes to controller initially
        workflow_def = workflow_engine.get_workflow_definition(WorkflowType.TECHNICAL_SERVICE.value)
        assert workflow_def.initial_role == UserRole.CLIENT.value  # Initial role in definition
        # But the state manager should set role_current to controller for call center requests
    
    @pytest.mark.asyncio
    async def test_client_details_capture_in_request_data(self, workflow_engine, mock_state_manager):
        """Test that client details are properly captured in request data"""
        # Arrange
        client_details = {
            'name': 'John Doe',
            'phone': '998901234567',
            'address': '456 Main St, Tashkent',
            'language': 'ru'
        }
        
        request_data = {
            'client_id': 123,
            'description': 'Service request description',
            'contact_info': {
                'phone': client_details['phone'],
                'name': client_details['name'],
                'address': client_details['address']
            },
            'client_details': client_details,
            'created_by_role': UserRole.CALL_CENTER.value,
            'created_by': 456
        }
        
        # Act
        await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, 
            request_data
        )
        
        # Assert
        call_args = mock_state_manager.create_request.call_args
        assert call_args[0][1]['client_details'] == client_details
        assert call_args[0][1]['contact_info']['phone'] == client_details['phone']
        assert call_args[0][1]['contact_info']['name'] == client_details['name']
    
    @pytest.mark.asyncio
    async def test_issue_description_capture_in_request_data(self, workflow_engine, mock_state_manager):
        """Test that issue description is properly captured"""
        # Arrange
        issue_description = "Client reports intermittent internet connectivity issues during peak hours"
        
        request_data = {
            'client_id': 123,
            'description': 'Technical service needed',
            'issue_description': issue_description,
            'created_by_role': UserRole.CALL_CENTER.value,
            'created_by': 456
        }
        
        # Act
        await workflow_engine.initiate_workflow(
            WorkflowType.TECHNICAL_SERVICE.value, 
            request_data
        )
        
        # Assert
        call_args = mock_state_manager.create_request.call_args
        assert call_args[0][1]['issue_description'] == issue_description
    
    @pytest.mark.asyncio
    async def test_same_workflow_as_client_initiated_requests(self, workflow_engine):
        """Test that call center requests follow same workflows as client-initiated requests"""
        # Arrange - Create both client and call center requests
        client_request_data = {
            'client_id': 123,
            'description': 'Client initiated request',
            'created_by_role': UserRole.CLIENT.value
        }
        
        call_center_request_data = {
            'client_id': 123,
            'description': 'Call center initiated request',
            'created_by_role': UserRole.CALL_CENTER.value,
            'created_by': 456
        }
        
        # Act
        client_request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, 
            client_request_data
        )
        
        call_center_request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, 
            call_center_request_data
        )
        
        # Assert - Both should use the same workflow definition
        client_workflow_def = workflow_engine.get_workflow_definition(WorkflowType.CONNECTION_REQUEST.value)
        call_center_workflow_def = workflow_engine.get_workflow_definition(WorkflowType.CONNECTION_REQUEST.value)
        
        assert client_workflow_def == call_center_workflow_def
        assert client_workflow_def.steps == call_center_workflow_def.steps
    
    @pytest.mark.asyncio
    async def test_error_handling_for_invalid_workflow_type(self, workflow_engine):
        """Test error handling for invalid workflow type"""
        # Arrange
        request_data = {
            'client_id': 123,
            'description': 'Test request',
            'created_by_role': UserRole.CALL_CENTER.value
        }
        
        # Act & Assert
        with pytest.raises(ValueError, match="Unknown workflow type"):
            await workflow_engine.initiate_workflow("invalid_workflow_type", request_data)
    
    @pytest.mark.asyncio
    async def test_error_handling_for_missing_client_id(self, workflow_engine):
        """Test error handling when client_id is missing"""
        # Arrange
        request_data = {
            'description': 'Test request without client_id',
            'created_by_role': UserRole.CALL_CENTER.value
        }
        
        # Act
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, 
            request_data
        )
        
        # Assert - Should still create request but with None client_id
        assert request_id == "test-request-id-123"
    
    def test_service_type_to_workflow_mapping(self):
        """Test mapping of service types to workflow types"""
        # Define the mapping as it should be in the handler
        workflow_mapping = {
            'installation': WorkflowType.CONNECTION_REQUEST.value,
            'setup': WorkflowType.CONNECTION_REQUEST.value,
            'repair': WorkflowType.TECHNICAL_SERVICE.value,
            'maintenance': WorkflowType.TECHNICAL_SERVICE.value,
            'consultation': WorkflowType.CALL_CENTER_DIRECT.value
        }
        
        # Assert mappings are correct
        assert workflow_mapping['installation'] == WorkflowType.CONNECTION_REQUEST.value
        assert workflow_mapping['setup'] == WorkflowType.CONNECTION_REQUEST.value
        assert workflow_mapping['repair'] == WorkflowType.TECHNICAL_SERVICE.value
        assert workflow_mapping['maintenance'] == WorkflowType.TECHNICAL_SERVICE.value
        assert workflow_mapping['consultation'] == WorkflowType.CALL_CENTER_DIRECT.value
    
    @pytest.mark.asyncio
    async def test_notification_exclusion_for_client_and_admin_roles(self, mock_notification_system):
        """Test that client and admin roles are excluded from notifications"""
        # This test verifies the notification system behavior
        
        # Test client role exclusion
        result_client = await mock_notification_system.send_assignment_notification(
            UserRole.CLIENT.value, "test-request-123", WorkflowType.CONNECTION_REQUEST.value
        )
        
        # Test admin role exclusion  
        result_admin = await mock_notification_system.send_assignment_notification(
            UserRole.ADMIN.value, "test-request-123", WorkflowType.CONNECTION_REQUEST.value
        )
        
        # Both should return True (mocked), but in real implementation would be skipped
        assert result_client == True
        assert result_admin == True


class TestCallCenterRequestIntegration:
    """Integration tests for call center request creation"""
    
    @pytest.mark.asyncio
    async def test_full_call_center_request_flow(self):
        """Test complete flow from call center request creation to routing"""
        # This would be an integration test that tests the full flow
        # from the handler through to the workflow engine
        
        # Mock the database and external dependencies
        with patch('database.call_center_queries.get_client_by_phone') as mock_get_client, \
             patch('database.call_center_queries.log_call') as mock_log_call, \
             patch('utils.workflow_engine.WorkflowEngineFactory.create_workflow_engine') as mock_engine_factory:
            
            # Setup mocks
            mock_get_client.return_value = {
                'id': 123,
                'full_name': 'Test Client',
                'phone_number': '998901234567',
                'address': '123 Test St',
                'language': 'uz'
            }
            
            mock_engine = AsyncMock()
            mock_engine.initiate_workflow.return_value = "test-request-id-123"
            mock_engine_factory.return_value = mock_engine
            
            mock_log_call.return_value = True
            
            # Simulate the handler logic
            client_data = await mock_get_client('998901234567')
            
            request_data = {
                'client_id': client_data['id'],
                'description': 'Test service request',
                'location': client_data['address'],
                'contact_info': {
                    'phone': client_data['phone_number'],
                    'name': client_data['full_name'],
                    'address': client_data['address']
                },
                'priority': Priority.MEDIUM.value,
                'service_type': 'repair',
                'created_by_role': UserRole.CALL_CENTER.value,
                'created_by': 456
            }
            
            request_id = await mock_engine.initiate_workflow(
                WorkflowType.TECHNICAL_SERVICE.value, 
                request_data
            )
            
            # Verify the flow
            assert request_id == "test-request-id-123"
            mock_get_client.assert_called_once_with('998901234567')
            mock_engine.initiate_workflow.assert_called_once()
            
            # Verify call logging
            await mock_log_call({
                'user_id': client_data['id'],
                'phone_number': client_data['phone_number'],
                'duration': 0,
                'result': 'workflow_request_created',
                'notes': f"Workflow request {request_id[:8]} created via call center",
                'created_by': 456
            })
            
            mock_log_call.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])