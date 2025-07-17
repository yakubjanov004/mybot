"""
Simple test for workflow integration with staff-created applications
Tests the core logic without complex database mocking
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from database.models import (
    ServiceRequest, UserRole, WorkflowType, WorkflowAction, 
    RequestStatus, Priority
)
from utils.workflow_engine import WorkflowEngine


class TestWorkflowIntegrationSimple:
    """Simple test for workflow integration logic"""
    
    def test_enhance_request_data_with_staff_context(self):
        """Test that request data is properly enhanced with staff context"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Test staff-created request data
        staff_request_data = {
            'client_id': 123,
            'description': 'Test request',
            'location': 'Test location',
            'created_by_staff': True,
            'staff_creator_info': {
                'creator_id': 456,
                'creator_role': 'manager',
                'creator_name': 'Test Manager'
            }
        }
        
        # Enhance request data
        enhanced_data = workflow_engine._enhance_request_data_with_staff_context(staff_request_data)
        
        # Verify staff context was added
        assert enhanced_data['created_by_staff'] is True
        assert enhanced_data['creation_source'] == 'manager'
        assert enhanced_data['staff_creator_id'] == 456
        assert enhanced_data['staff_creator_role'] == 'manager'
        
        # Verify state data contains staff context
        assert enhanced_data['state_data']['created_by_staff'] is True
        assert enhanced_data['state_data']['staff_creator_info']['creator_role'] == 'manager'
        assert enhanced_data['state_data']['workflow_initiated_by_staff'] is True
        assert 'staff_creation_timestamp' in enhanced_data['state_data']
    
    def test_enhance_request_data_client_context(self):
        """Test that client-created request data is properly handled"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Test client-created request data
        client_request_data = {
            'client_id': 123,
            'description': 'Test request',
            'location': 'Test location'
        }
        
        # Enhance request data
        enhanced_data = workflow_engine._enhance_request_data_with_staff_context(client_request_data)
        
        # Verify client context
        assert enhanced_data['created_by_staff'] is False
        assert enhanced_data['creation_source'] == 'client'
        assert 'staff_creator_id' not in enhanced_data
        assert 'staff_creator_role' not in enhanced_data
    
    def test_get_workflow_initiation_comment_staff(self):
        """Test workflow initiation comment for staff-created applications"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Test staff-created request data
        staff_request_data = {
            'created_by_staff': True,
            'staff_creator_info': {
                'creator_role': 'manager',
                'creator_name': 'Test Manager'
            },
            'contact_info': {
                'full_name': 'Test Client'
            }
        }
        
        comment = workflow_engine._get_workflow_initiation_comment(staff_request_data)
        
        # Verify comment includes staff context
        assert 'manager' in comment
        assert 'Test Manager' in comment
        assert 'Test Client' in comment
        assert 'Workflow initiated by' in comment
    
    def test_get_workflow_initiation_comment_client(self):
        """Test workflow initiation comment for client-created applications"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Test client-created request data
        client_request_data = {
            'created_by_staff': False
        }
        
        comment = workflow_engine._get_workflow_initiation_comment(client_request_data)
        
        # Verify comment is for client
        assert comment == "Workflow initiated by client"
    
    def test_enhance_transition_data_with_staff_context(self):
        """Test that transition data is enhanced with staff context"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Create mock request with staff creation context
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
        
        # Test transition data
        transition_data = {
            'actor_id': 789,
            'junior_manager_id': 101,
            'comments': 'Assigning to junior manager'
        }
        
        # Enhance transition data
        enhanced_data = workflow_engine._enhance_transition_data_with_staff_context(
            mock_request, transition_data
        )
        
        # Verify staff context was preserved
        assert enhanced_data['staff_created_workflow'] is True
        assert enhanced_data['original_staff_creator_info']['creator_role'] == 'manager'
        assert enhanced_data['transition_by_different_staff'] is True
        assert enhanced_data['original_creator_role'] == 'manager'
        assert 'workflow_transition_timestamp' in enhanced_data
    
    def test_get_transition_comment_staff_context(self):
        """Test transition comment includes staff context"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Create mock request with staff creation context
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
        
        # Test transition data
        transition_data = {
            'comments': 'Assigning to junior manager'
        }
        
        comment = workflow_engine._get_transition_comment(
            mock_request, WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value, transition_data
        )
        
        # Verify comment includes staff context
        assert 'Assigning to junior manager' in comment
        assert 'Staff-created request by manager' in comment
        assert 'Test Client' in comment
    
    def test_get_transition_comment_client_context(self):
        """Test transition comment for client-created applications"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Create mock request without staff creation context
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
            state_data={},
            created_by_staff=False,
            creation_source='client'
        )
        
        # Test transition data
        transition_data = {
            'comments': 'Assigning to junior manager'
        }
        
        comment = workflow_engine._get_transition_comment(
            mock_request, WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value, transition_data
        )
        
        # Verify comment is just the base comment
        assert comment == 'Assigning to junior manager'
    
    def test_workflow_definitions_include_all_types(self):
        """Test that workflow definitions include all required workflow types"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Verify all workflow types are defined
        available_workflows = workflow_engine.get_available_workflows()
        
        assert WorkflowType.CONNECTION_REQUEST.value in available_workflows
        assert WorkflowType.TECHNICAL_SERVICE.value in available_workflows
        assert WorkflowType.CALL_CENTER_DIRECT.value in available_workflows
    
    def test_workflow_definitions_have_correct_initial_roles(self):
        """Test that workflow definitions have correct initial roles"""
        # Create workflow engine with mock dependencies
        mock_state_manager = MagicMock()
        mock_notification_system = MagicMock()
        mock_inventory_manager = MagicMock()
        workflow_engine = WorkflowEngine(mock_state_manager, mock_notification_system, mock_inventory_manager)
        
        # Test connection request workflow
        connection_def = workflow_engine.get_workflow_definition(WorkflowType.CONNECTION_REQUEST.value)
        assert connection_def.initial_role == UserRole.CLIENT.value
        
        # Test technical service workflow
        technical_def = workflow_engine.get_workflow_definition(WorkflowType.TECHNICAL_SERVICE.value)
        assert technical_def.initial_role == UserRole.CLIENT.value
        
        # Test call center direct workflow
        call_center_def = workflow_engine.get_workflow_definition(WorkflowType.CALL_CENTER_DIRECT.value)
        assert call_center_def.initial_role == UserRole.CALL_CENTER_SUPERVISOR.value


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])