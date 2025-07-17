"""
Integration tests for Connection Request Workflow
Tests the complete workflow: Client → Manager → Junior Manager → Controller → Technician → Warehouse
"""

import pytest
import pytest_asyncio
import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from database.models import (
    UserRole, WorkflowType, WorkflowAction, RequestStatus, Priority
)
from utils.workflow_manager import EnhancedWorkflowManager
from utils.state_manager import StateManager
from utils.notification_system import NotificationSystem
from utils.inventory_manager import InventoryManager


class TestConnectionWorkflowIntegration:
    """Integration tests for connection request workflow"""
    
    @pytest_asyncio.fixture
    async def setup_workflow_manager(self):
        """Setup workflow manager with mocked dependencies"""
        # Mock database pool
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock state manager
        state_manager = StateManager(pool=mock_pool)
        
        # Mock notification system
        notification_system = NotificationSystem(pool=mock_pool)
        
        # Mock inventory manager
        inventory_manager = InventoryManager()
        
        # Create workflow manager
        workflow_manager = EnhancedWorkflowManager(
            notification_system=notification_system,
            inventory_manager=inventory_manager
        )
        
        return workflow_manager, mock_conn
    
    @pytest.mark.asyncio
    async def test_complete_connection_workflow(self, setup_workflow_manager):
        """Test complete connection request workflow from client to warehouse"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        # Mock database responses
        request_id = str(uuid.uuid4())
        client_id = 1
        junior_manager_id = 2
        technician_id = 3
        
        # Mock request creation
        mock_conn.execute.return_value = "INSERT 0 1"
        mock_conn.fetchrow.return_value = {
            'id': request_id,
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': client_id,
            'role_current ': UserRole.MANAGER.value,
            'current_status': RequestStatus.CREATED.value,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'priority': Priority.MEDIUM.value,
            'description': 'Test connection request',
            'location': 'Test address',
            'contact_info': '{}',
            'state_data': '{}',
            'equipment_used': '[]',
            'inventory_updated': False,
            'completion_rating': None,
            'feedback_comments': None
        }
        
        # Step 1: Client creates connection request
        created_request_id = await workflow_manager.create_connection_request(
            client_id=client_id,
            description="Test connection request",
            location="Test address",
            contact_info={'phone': '+998901234567'}
        )
        
        assert created_request_id is not None
        
        # Step 2: Manager assigns to junior manager
        with patch.object(workflow_manager.notification_system, 'send_assignment_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = True
            
            success = await workflow_manager.assign_to_junior_manager(
                request_id, junior_manager_id, 100  # manager_id
            )
            
            assert success is True
            mock_notify.assert_called_once()
        
        # Step 3: Junior manager calls client and forwards to controller
        with patch.object(workflow_manager.notification_system, 'send_assignment_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = True
            
            success = await workflow_manager.call_client_and_forward(
                request_id, "Client contacted successfully", junior_manager_id
            )
            
            assert success is True
            mock_notify.assert_called_once()
        
        # Step 4: Controller assigns to technician
        with patch.object(workflow_manager.notification_system, 'send_assignment_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = True
            
            success = await workflow_manager.assign_to_technician(
                request_id, technician_id, 200  # controller_id
            )
            
            assert success is True
            mock_notify.assert_called_once()
        
        # Step 5: Technician starts installation
        success = await workflow_manager.start_installation(
            request_id, technician_id, "Installation started"
        )
        
        assert success is True
        
        # Step 6: Technician documents equipment usage
        equipment_used = [
            {'name': 'Router', 'quantity': 1},
            {'name': 'Cable', 'quantity': 50}
        ]
        
        with patch.object(workflow_manager.notification_system, 'send_assignment_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = True
            
            success = await workflow_manager.document_equipment_usage(
                request_id, equipment_used, "Equipment documented", technician_id
            )
            
            assert success is True
            mock_notify.assert_called_once()
        
        # Step 7: Warehouse updates inventory and closes request
        inventory_updates = {
            'equipment_consumed': equipment_used,
            'updated_by': 300,  # warehouse_id
            'updated_at': str(datetime.now())
        }
        
        with patch.object(workflow_manager.notification_system, 'send_completion_notification', new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = True
            
            success = await workflow_manager.update_inventory_and_close(
                request_id, inventory_updates, 300  # warehouse_id
            )
            
            assert success is True
            mock_completion.assert_called_once_with(client_id, request_id, WorkflowType.CONNECTION_REQUEST.value)
        
        # Step 8: Client rates the service
        success = await workflow_manager.rate_service(
            request_id, 5, "Excellent service!", client_id
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self, setup_workflow_manager):
        """Test that workflow state transitions are properly recorded"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        request_id = str(uuid.uuid4())
        
        # Mock state manager methods
        mock_request = MagicMock()
        mock_request.id = request_id
        mock_request.workflow_type = WorkflowType.CONNECTION_REQUEST.value
        mock_request.role_current = UserRole.MANAGER.value
        mock_request.current_status = RequestStatus.IN_PROGRESS.value
        mock_request.state_data = {}
        mock_request.equipment_used = []
        mock_request.inventory_updated = False
        mock_request.client_id = 1
        
        with patch.object(workflow_manager.state_manager, 'get_request', return_value=mock_request):
            with patch.object(workflow_manager.state_manager, 'update_request_state', return_value=True):
                with patch.object(workflow_manager.state_manager, 'add_state_transition', return_value=True):
                    
                    # Test junior manager assignment
                    success = await workflow_manager.assign_to_junior_manager(
                        request_id, 2, 100
                    )
                    
                    assert success is True
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, setup_workflow_manager):
        """Test workflow error handling scenarios"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        # Test with non-existent request
        with patch.object(workflow_manager.state_manager, 'get_request', return_value=None):
            success = await workflow_manager.assign_to_junior_manager(
                "non-existent-id", 2, 100
            )
            
            assert success is False
        
        # Test with database error
        with patch.object(workflow_manager.state_manager, 'get_request', side_effect=Exception("Database error")):
            success = await workflow_manager.assign_to_junior_manager(
                "test-id", 2, 100
            )
            
            assert success is False
    
    @pytest.mark.asyncio
    async def test_notification_system_integration(self, setup_workflow_manager):
        """Test notification system integration with workflow"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        request_id = str(uuid.uuid4())
        
        # Mock notification system
        with patch.object(workflow_manager.notification_system, 'send_assignment_notification') as mock_notify:
            mock_notify.return_value = True
            
            # Mock successful workflow transition
            with patch.object(workflow_manager.workflow_engine, 'transition_workflow', return_value=True):
                success = await workflow_manager.assign_to_junior_manager(
                    request_id, 2, 100
                )
                
                assert success is True
                mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_inventory_integration(self, setup_workflow_manager):
        """Test inventory manager integration with workflow"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        request_id = str(uuid.uuid4())
        equipment_used = [{'name': 'Router', 'quantity': 1}]
        
        # Mock inventory manager
        with patch.object(workflow_manager.inventory_manager, 'consume_equipment') as mock_consume:
            mock_consume.return_value = True
            
            # Mock successful workflow transition
            with patch.object(workflow_manager.workflow_engine, 'transition_workflow', return_value=True):
                success = await workflow_manager.document_equipment_usage(
                    request_id, equipment_used, "Equipment used", 3
                )
                
                assert success is True
    
    @pytest.mark.asyncio
    async def test_client_rating_system(self, setup_workflow_manager):
        """Test client rating system integration"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        request_id = str(uuid.uuid4())
        
        # Mock successful rating submission
        with patch.object(workflow_manager.workflow_engine, 'complete_workflow', return_value=True):
            success = await workflow_manager.rate_service(
                request_id, 4, "Good service", 1
            )
            
            assert success is True
    
    @pytest.mark.asyncio
    async def test_workflow_status_tracking(self, setup_workflow_manager):
        """Test workflow status tracking throughout the process"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        request_id = str(uuid.uuid4())
        
        # Mock workflow status
        mock_status = MagicMock()
        mock_status.request_id = request_id
        mock_status.role_current = UserRole.MANAGER.value
        mock_status.current_status = RequestStatus.IN_PROGRESS.value
        mock_status.available_actions = [WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value]
        mock_status.next_roles = [UserRole.JUNIOR_MANAGER.value]
        mock_status.history = []
        
        with patch.object(workflow_manager.workflow_engine, 'get_workflow_status', return_value=mock_status):
            status = await workflow_manager.get_workflow_status(request_id)
            
            assert status is not None
            assert status.request_id == request_id
            assert status.role_current == UserRole.MANAGER.value
    
    @pytest.mark.asyncio
    async def test_role_based_request_filtering(self, setup_workflow_manager):
        """Test role-based request filtering"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        # Mock requests for specific role
        mock_requests = [
            MagicMock(id="req1", role_current =UserRole.MANAGER.value),
            MagicMock(id="req2", role_current =UserRole.MANAGER.value)
        ]
        
        with patch.object(workflow_manager.state_manager, 'get_requests_by_role', return_value=mock_requests):
            requests = await workflow_manager.get_requests_for_role(UserRole.MANAGER.value)
            
            assert len(requests) == 2
            assert all(req.role_current == UserRole.MANAGER.value for req in requests)
    
    @pytest.mark.asyncio
    async def test_client_request_history(self, setup_workflow_manager):
        """Test client request history tracking"""
        workflow_manager, mock_conn = setup_workflow_manager
        
        client_id = 1
        
        # Mock client requests
        mock_requests = [
            MagicMock(id="req1", client_id=client_id, workflow_type=WorkflowType.CONNECTION_REQUEST.value),
            MagicMock(id="req2", client_id=client_id, workflow_type=WorkflowType.CONNECTION_REQUEST.value)
        ]
        
        with patch.object(workflow_manager.state_manager, 'get_requests_by_client', return_value=mock_requests):
            requests = await workflow_manager.get_client_requests(client_id)
            
            assert len(requests) == 2
            assert all(req.client_id == client_id for req in requests)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])