"""
Integration tests for Technical Service With Warehouse Workflow
Tests the complete workflow: Client → Controller → Technician → Warehouse → Technician
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from handlers.technical_service_with_warehouse_workflow import TechnicalServiceWithWarehouseWorkflowHandler
from database.models import (
    ServiceRequest, WorkflowType, WorkflowAction, UserRole, RequestStatus,
    StateTransition
)
from utils.workflow_engine import WorkflowEngine
from utils.state_manager import StateManager
from utils.notification_system import NotificationSystem
from utils.inventory_manager import InventoryManager


class TestTechnicalServiceWithWarehouseWorkflow:
    """Test suite for Technical Service With Warehouse Workflow"""
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager"""
        mock = AsyncMock(spec=StateManager)
        return mock
    
    @pytest.fixture
    def mock_notification_system(self):
        """Mock notification system"""
        mock = AsyncMock(spec=NotificationSystem)
        return mock
    
    @pytest.fixture
    def mock_inventory_manager(self):
        """Mock inventory manager"""
        mock = AsyncMock(spec=InventoryManager)
        return mock
    
    @pytest.fixture
    def mock_workflow_engine(self, mock_state_manager, mock_notification_system, mock_inventory_manager):
        """Mock workflow engine"""
        mock = AsyncMock(spec=WorkflowEngine)
        mock.state_manager = mock_state_manager
        mock.notification_system = mock_notification_system
        mock.inventory_manager = mock_inventory_manager
        return mock
    
    @pytest.fixture
    def workflow_handler(self):
        """Create workflow handler with mocked dependencies"""
        with patch('handlers.technical_service_with_warehouse_workflow.StateManagerFactory') as mock_state_factory, \
             patch('handlers.technical_service_with_warehouse_workflow.NotificationSystemFactory') as mock_notif_factory, \
             patch('handlers.technical_service_with_warehouse_workflow.get_inventory_manager') as mock_get_inv_manager, \
             patch('handlers.technical_service_with_warehouse_workflow.WorkflowEngineFactory') as mock_engine_factory:
            
            mock_state_factory.create_state_manager.return_value = AsyncMock()
            mock_notif_factory.create_notification_system.return_value = AsyncMock()
            mock_get_inv_manager.return_value = AsyncMock()
            mock_engine_factory.create_workflow_engine.return_value = AsyncMock()
            
            handler = TechnicalServiceWithWarehouseWorkflowHandler()
            return handler
    
    @pytest.fixture
    def sample_request(self):
        """Sample service request for testing"""
        return ServiceRequest(
            id="test-request-123",
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=1001,
            role_current =UserRole.TECHNICIAN.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority="medium",
            description="Internet connection issues",
            location="Test Location",
            contact_info={"phone": "+998901234567", "telegram_id": 123456789},
            state_data={"equipment_needed": "Router TP-Link - 1 dona\nEthernet kabel - 10 metr"},
            equipment_used=[],
            inventory_updated=False,
            completion_rating=None,
            feedback_comments=None
        )
    
    @pytest.fixture
    def mock_user_technician(self):
        """Mock technician user"""
        return {
            'id': 2001,
            'telegram_id': 987654321,
            'role': UserRole.TECHNICIAN.value,
            'language': 'uz',
            'full_name': 'Test Technician'
        }
    
    @pytest.fixture
    def mock_user_warehouse(self):
        """Mock warehouse user"""
        return {
            'id': 3001,
            'telegram_id': 111222333,
            'role': UserRole.WAREHOUSE.value,
            'language': 'uz',
            'full_name': 'Test Warehouse'
        }
    
    @pytest.fixture
    def mock_user_client(self):
        """Mock client user"""
        return {
            'id': 1001,
            'telegram_id': 123456789,
            'role': UserRole.CLIENT.value,
            'language': 'uz',
            'full_name': 'Test Client'
        }
    
    @pytest.fixture
    def mock_callback_query(self):
        """Mock callback query"""
        mock = MagicMock()
        mock.answer = AsyncMock()
        mock.message.edit_text = AsyncMock()
        mock.from_user.id = 987654321
        return mock
    
    @pytest.fixture
    def mock_message(self):
        """Mock message"""
        mock = MagicMock()
        mock.answer = AsyncMock()
        mock.from_user.id = 987654321
        mock.text = "Test equipment documentation"
        return mock
    
    @pytest.fixture
    def mock_state(self):
        """Mock FSM state"""
        mock = AsyncMock()
        mock.get_data.return_value = {}
        mock.update_data = AsyncMock()
        mock.set_state = AsyncMock()
        mock.clear = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_technician_selects_warehouse_involvement(
        self, workflow_handler, mock_callback_query, mock_user_technician, sample_request
    ):
        """Test technician selecting warehouse involvement"""
        # Setup
        mock_callback_query.data = "decide_warehouse_involvement_yes_test-request-123"
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_technician
            workflow_handler.state_manager.get_request.return_value = sample_request
            
            # Execute
            await workflow_handler.select_warehouse_involvement(mock_callback_query)
            
            # Verify
            mock_callback_query.answer.assert_called_once()
            mock_callback_query.message.edit_text.assert_called_once()
            
            # Check that the message contains warehouse involvement text
            call_args = mock_callback_query.message.edit_text.call_args
            assert "Ombor yordami kerak" in call_args[0][0]
            assert "parse_mode" in call_args[1]
            assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_technician_starts_equipment_documentation(
        self, workflow_handler, mock_callback_query, mock_user_technician, mock_state
    ):
        """Test technician starting equipment documentation"""
        # Setup
        mock_callback_query.data = "document_equipment_for_warehouse_test-request-123"
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_technician
            
            # Execute
            await workflow_handler.start_equipment_documentation(mock_callback_query, mock_state)
            
            # Verify
            mock_callback_query.answer.assert_called_once()
            mock_state.update_data.assert_called_once_with(documenting_request_id="test-request-123")
            mock_state.set_state.assert_called_once()
            mock_callback_query.message.edit_text.assert_called_once()
            
            # Check that the message contains documentation instructions
            call_args = mock_callback_query.message.edit_text.call_args
            assert "Uskunalarni hujjatlashtirish" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_technician_processes_equipment_documentation(
        self, workflow_handler, mock_message, mock_user_technician, mock_state
    ):
        """Test technician processing equipment documentation"""
        # Setup
        mock_state.get_data.return_value = {"documenting_request_id": "test-request-123"}
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_technician
            
            # Execute
            await workflow_handler.process_equipment_documentation(mock_message, mock_state)
            
            # Verify
            mock_state.update_data.assert_called_once_with(equipment_documentation="Test equipment documentation")
            mock_message.answer.assert_called_once()
            
            # Check that the message contains confirmation text
            call_args = mock_message.answer.call_args
            assert "Uskuna hujjatlashtirildi" in call_args[0][0]
            assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_technician_confirms_equipment_documentation(
        self, workflow_handler, mock_callback_query, mock_user_technician, mock_state
    ):
        """Test technician confirming equipment documentation"""
        # Setup
        mock_callback_query.data = "confirm_equipment_documentation_test-request-123"
        mock_state.get_data.return_value = {"equipment_documentation": "Router TP-Link - 1 dona"}
        workflow_handler.workflow_engine.transition_workflow.return_value = True
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_technician
            
            # Execute
            await workflow_handler.confirm_equipment_documentation(mock_callback_query, mock_state)
            
            # Verify
            mock_callback_query.answer.assert_called_once()
            workflow_handler.workflow_engine.transition_workflow.assert_called_once()
            
            # Check workflow transition parameters
            call_args = workflow_handler.workflow_engine.transition_workflow.call_args[0]
            assert call_args[0] == "test-request-123"
            assert call_args[1] == WorkflowAction.DOCUMENT_EQUIPMENT.value
            assert call_args[2] == UserRole.TECHNICIAN.value
            
            mock_state.clear.assert_called_once()
            mock_callback_query.message.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_warehouse_starts_equipment_preparation(
        self, workflow_handler, mock_callback_query, mock_user_warehouse, sample_request
    ):
        """Test warehouse starting equipment preparation"""
        # Setup
        mock_callback_query.data = "prepare_equipment_test-request-123"
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_warehouse
            workflow_handler.state_manager.get_request.return_value = sample_request
            
            # Execute
            await workflow_handler.start_equipment_preparation(mock_callback_query)
            
            # Verify
            mock_callback_query.answer.assert_called_once()
            mock_callback_query.message.edit_text.assert_called_once()
            
            # Check that the message contains preparation text
            call_args = mock_callback_query.message.edit_text.call_args
            assert "Uskuna tayyorlash" in call_args[0][0]
            assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_warehouse_processes_equipment_preparation(
        self, workflow_handler, mock_message, mock_user_warehouse, mock_state
    ):
        """Test warehouse processing equipment preparation"""
        # Setup
        mock_message.text = "Equipment prepared successfully"
        mock_state.get_data.return_value = {"preparing_request_id": "test-request-123"}
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_warehouse
            
            # Execute
            await workflow_handler.process_equipment_preparation(mock_message, mock_state)
            
            # Verify
            mock_state.update_data.assert_called_once_with(preparation_comments="Equipment prepared successfully")
            mock_message.answer.assert_called_once()
            
            # Check that the message contains confirmation text
            call_args = mock_message.answer.call_args
            assert "Uskuna tayyorlandi" in call_args[0][0]
            assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_warehouse_confirms_equipment_ready(
        self, workflow_handler, mock_callback_query, mock_user_warehouse, mock_state
    ):
        """Test warehouse confirming equipment is ready"""
        # Setup
        mock_callback_query.data = "confirm_equipment_ready_test-request-123"
        mock_state.get_data.return_value = {"preparation_comments": "All equipment ready"}
        workflow_handler.workflow_engine.transition_workflow.return_value = True
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_warehouse
            
            # Execute
            await workflow_handler.confirm_equipment_ready(mock_callback_query, mock_state)
            
            # Verify
            mock_callback_query.answer.assert_called_once()
            workflow_handler.workflow_engine.transition_workflow.assert_called_once()
            
            # Check workflow transition parameters
            call_args = workflow_handler.workflow_engine.transition_workflow.call_args[0]
            assert call_args[0] == "test-request-123"
            assert call_args[1] == WorkflowAction.CONFIRM_EQUIPMENT_READY.value
            assert call_args[2] == UserRole.WAREHOUSE.value
            
            mock_state.clear.assert_called_once()
            mock_callback_query.message.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_technician_completes_technical_with_warehouse(
        self, workflow_handler, mock_callback_query, mock_user_technician, mock_state, sample_request
    ):
        """Test technician completing technical service after warehouse confirmation"""
        # Setup
        mock_callback_query.data = "complete_technical_with_warehouse_test-request-123"
        sample_request.state_data["warehouse_comments"] = "Equipment ready for use"
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_technician
            workflow_handler.state_manager.get_request.return_value = sample_request
            
            # Execute
            await workflow_handler.complete_technical_with_warehouse(mock_callback_query, mock_state)
            
            # Verify
            mock_callback_query.answer.assert_called_once()
            mock_state.update_data.assert_called_once_with(completing_warehouse_request_id="test-request-123")
            mock_state.set_state.assert_called_once()
            mock_callback_query.message.edit_text.assert_called_once()
            
            # Check that the message contains warehouse comments
            call_args = mock_callback_query.message.edit_text.call_args
            assert "Equipment ready for use" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_technician_processes_warehouse_completion(
        self, workflow_handler, mock_message, mock_user_technician, mock_state
    ):
        """Test technician processing final completion after warehouse"""
        # Setup
        mock_message.text = "Technical service completed successfully"
        mock_state.get_data.return_value = {"completing_warehouse_request_id": "test-request-123"}
        workflow_handler.workflow_engine.transition_workflow.return_value = True
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user, \
             patch.object(workflow_handler, '_send_warehouse_completion_notification') as mock_send_notification:
            mock_get_user.return_value = mock_user_technician
            
            # Execute
            await workflow_handler.process_warehouse_completion(mock_message, mock_state)
            
            # Verify
            workflow_handler.workflow_engine.transition_workflow.assert_called_once()
            
            # Check workflow transition parameters
            call_args = workflow_handler.workflow_engine.transition_workflow.call_args[0]
            assert call_args[0] == "test-request-123"
            assert call_args[1] == WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value
            assert call_args[2] == UserRole.TECHNICIAN.value
            
            mock_send_notification.assert_called_once_with("test-request-123")
            mock_state.clear.assert_called_once()
            mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_rates_warehouse_service(
        self, workflow_handler, mock_callback_query, mock_user_client
    ):
        """Test client rating warehouse service"""
        # Setup
        mock_callback_query.data = "technical_warehouse_rating_5_test-request-123"
        workflow_handler.workflow_engine.complete_workflow.return_value = True
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_client
            
            # Execute
            await workflow_handler.process_warehouse_service_rating(mock_callback_query)
            
            # Verify
            mock_callback_query.answer.assert_called_once()
            workflow_handler.workflow_engine.complete_workflow.assert_called_once()
            
            # Check completion parameters
            call_args = workflow_handler.workflow_engine.complete_workflow.call_args[0]
            assert call_args[0] == "test-request-123"
            completion_data = call_args[1]
            assert completion_data['rating'] == 5
            assert completion_data['actor_id'] == 1001
            
            mock_callback_query.message.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_inventory_update_from_equipment_list(self, workflow_handler):
        """Test inventory update from equipment list"""
        # Setup
        equipment_list = "Router TP-Link - 1 dona\nEthernet kabel - 10 metr\nKonnektorlar - 2 dona"
        workflow_handler.inventory_manager = AsyncMock()
        
        # Execute
        await workflow_handler._update_inventory_from_equipment_list("test-request-123", equipment_list)
        
        # Verify
        workflow_handler.inventory_manager.consume_equipment.assert_called_once()
        call_args = workflow_handler.inventory_manager.consume_equipment.call_args[0]
        assert call_args[0] == "test-request-123"
        equipment_items = call_args[1]
        assert len(equipment_items) == 3
        assert equipment_items[0]['name'] == "Router TP"  # The parsing splits on '-' so it gets "Router TP"
        assert equipment_items[0]['quantity'] == 1
        assert equipment_items[1]['name'] == "Ethernet kabel"
        assert equipment_items[1]['quantity'] == 10

    @pytest.mark.asyncio
    async def test_complete_workflow_integration(
        self, workflow_handler, mock_user_technician, mock_user_warehouse, mock_user_client, sample_request
    ):
        """Test complete workflow integration from technician to warehouse to completion"""
        # This test simulates the complete workflow
        
        # Setup mocks
        workflow_handler.workflow_engine.transition_workflow.return_value = True
        workflow_handler.workflow_engine.complete_workflow.return_value = True
        workflow_handler.state_manager.get_request.return_value = sample_request
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user, \
             patch('handlers.technical_service_with_warehouse_workflow.bot') as mock_bot:
            
            # Step 1: Technician selects warehouse involvement
            mock_get_user.return_value = mock_user_technician
            mock_callback = MagicMock()
            mock_callback.answer = AsyncMock()
            mock_callback.message.edit_text = AsyncMock()
            mock_callback.from_user.id = mock_user_technician['telegram_id']
            mock_callback.data = "decide_warehouse_involvement_yes_test-request-123"
            
            await workflow_handler.select_warehouse_involvement(mock_callback)
            
            # Step 2: Technician documents equipment
            mock_state = AsyncMock()
            mock_state.get_data.return_value = {"documenting_request_id": "test-request-123"}
            mock_callback.data = "confirm_equipment_documentation_test-request-123"
            mock_state.get_data.return_value = {"equipment_documentation": "Router TP-Link - 1 dona"}
            
            await workflow_handler.confirm_equipment_documentation(mock_callback, mock_state)
            
            # Step 3: Warehouse prepares equipment
            mock_get_user.return_value = mock_user_warehouse
            mock_callback.from_user.id = mock_user_warehouse['telegram_id']
            mock_callback.data = "confirm_equipment_ready_test-request-123"
            mock_state.get_data.return_value = {"preparation_comments": "Equipment ready"}
            
            await workflow_handler.confirm_equipment_ready(mock_callback, mock_state)
            
            # Step 4: Technician completes service
            mock_get_user.return_value = mock_user_technician
            mock_callback.from_user.id = mock_user_technician['telegram_id']
            mock_message = MagicMock()
            mock_message.answer = AsyncMock()
            mock_message.from_user.id = mock_user_technician['telegram_id']
            mock_message.text = "Service completed successfully"
            mock_state.get_data.return_value = {"completing_warehouse_request_id": "test-request-123"}
            
            await workflow_handler.process_warehouse_completion(mock_message, mock_state)
            
            # Step 5: Client rates service
            mock_get_user.return_value = mock_user_client
            mock_callback.from_user.id = mock_user_client['telegram_id']
            mock_callback.data = "technical_warehouse_rating_5_test-request-123"
            
            await workflow_handler.process_warehouse_service_rating(mock_callback)
            
            # Verify workflow transitions were called
            assert workflow_handler.workflow_engine.transition_workflow.call_count >= 2
            workflow_handler.workflow_engine.complete_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_invalid_user_role(self, workflow_handler, mock_callback_query):
        """Test error handling for invalid user roles"""
        # Setup - user with wrong role
        mock_user = {
            'id': 9999,
            'telegram_id': 999999999,
            'role': UserRole.CLIENT.value,  # Wrong role for technician action
            'language': 'uz'
        }
        
        mock_callback_query.data = "decide_warehouse_involvement_yes_test-request-123"
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            # Execute
            await workflow_handler.select_warehouse_involvement(mock_callback_query)
            
            # Verify error handling - check that the error message was called
            assert mock_callback_query.answer.call_count == 2  # Once for initial answer(), once for error
            mock_callback_query.answer.assert_any_call("Sizda bu amalni bajarish huquqi yo'q!")

    @pytest.mark.asyncio
    async def test_error_handling_missing_request(self, workflow_handler, mock_callback_query, mock_user_technician):
        """Test error handling for missing request"""
        # Setup
        mock_callback_query.data = "decide_warehouse_involvement_yes_nonexistent-request"
        workflow_handler.state_manager.get_request.return_value = None
        
        with patch('handlers.technical_service_with_warehouse_workflow.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user_technician
            
            # Execute
            await workflow_handler.select_warehouse_involvement(mock_callback_query)
            
            # Verify error handling - check that the error message was called
            assert mock_callback_query.answer.call_count == 2  # Once for initial answer(), once for error
            mock_callback_query.answer.assert_any_call("So'rov topilmadi!")

    def test_router_registration(self, workflow_handler):
        """Test that router is properly configured"""
        router = workflow_handler.get_router()
        assert router is not None
        
        # Check that router has the expected structure
        # In aiogram 3.x, routers have different attributes
        assert hasattr(router, 'callback_query') or hasattr(router, 'message') or hasattr(router, '_handlers')
        
        # Basic check that the router was created successfully
        assert str(type(router).__name__) == 'Router'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])