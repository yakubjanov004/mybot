"""
Integration Tests for Technical Service Without Warehouse Workflow

Tests the complete workflow: Client → Controller → Technician
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from database.models import WorkflowType, WorkflowAction, UserRole, RequestStatus, Priority
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory
from handlers.technical_service_workflow import TechnicalServiceWorkflowHandler


class TestTechnicalServiceWithoutWarehouseWorkflow:
    """Test suite for Technical Service Without Warehouse workflow"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = conn
        return pool, conn
    
    @pytest.fixture
    def mock_bot(self):
        """Mock bot instance"""
        bot = AsyncMock()
        return bot
    
    @pytest.fixture
    def workflow_handler(self):
        """Create workflow handler instance"""
        return TechnicalServiceWorkflowHandler()
    
    @pytest.fixture
    def sample_client_user(self):
        """Sample client user data"""
        return {
            'id': 1,
            'telegram_id': 12345,
            'full_name': 'Test Client',
            'phone': '+998901234567',
            'role': UserRole.CLIENT.value,
            'language': 'uz'
        }
    
    @pytest.fixture
    def sample_controller_user(self):
        """Sample controller user data"""
        return {
            'id': 2,
            'telegram_id': 23456,
            'full_name': 'Test Controller',
            'phone': '+998901234568',
            'role': UserRole.CONTROLLER.value,
            'language': 'ru'
        }
    
    @pytest.fixture
    def sample_technician_user(self):
        """Sample technician user data"""
        return {
            'id': 3,
            'telegram_id': 34567,
            'full_name': 'Test Technician',
            'phone': '+998901234569',
            'role': UserRole.TECHNICIAN.value,
            'language': 'uz'
        }
    
    @pytest.fixture
    def sample_technical_request(self):
        """Sample technical service request"""
        return {
            'client_id': 1,
            'description': 'Internet connection is very slow',
            'issue_type': 'technical_support',
            'priority': Priority.MEDIUM.value,
            'contact_info': {
                'phone': '+998901234567',
                'telegram_id': 12345,
                'full_name': 'Test Client'
            }
        }
    
    @pytest.mark.asyncio
    async def test_client_technical_request_submission(self, workflow_handler, sample_client_user, sample_technical_request, mock_pool, mock_bot):
        """
        Test Requirement 2.1: Client submits technical service request
        """
        pool, conn = mock_pool
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_client_user), \
             patch('loader.bot', mock_bot), \
             patch.object(workflow_handler.workflow_engine, 'initiate_workflow', return_value='test-request-id-123'):
            
            # Mock message and state
            message = AsyncMock()
            message.from_user.id = sample_client_user['telegram_id']
            message.text = "Internet connection is very slow"
            
            state = AsyncMock()
            state.get_data.return_value = {
                'issue_description': 'Internet connection is very slow',
                'issue_type': 'technical_support'
            }
            
            # Mock callback query for confirmation
            callback = AsyncMock()
            callback.from_user.id = sample_client_user['telegram_id']
            callback.message.edit_text = AsyncMock()
            
            # Test request submission
            await workflow_handler.start_technical_request(message, state)
            
            # Verify state was set
            state.set_state.assert_called()
            
            # Test issue description processing
            await workflow_handler.process_issue_description(message, state)
            
            # Verify confirmation message
            message.answer.assert_called()
            state.set_state.assert_called()
            
            # Test request confirmation
            await workflow_handler.confirm_technical_request(callback, state)
            
            # Verify workflow was initiated
            workflow_handler.workflow_engine.initiate_workflow.assert_called_once_with(
                WorkflowType.TECHNICAL_SERVICE.value,
                sample_technical_request
            )
            
            # Verify success message
            callback.message.edit_text.assert_called()
            state.clear.assert_called()
    
    @pytest.mark.asyncio
    async def test_controller_assigns_to_technician(self, workflow_handler, sample_controller_user, sample_technician_user, mock_pool):
        """
        Test Requirement 2.3: Controller assigns technical request to technician
        """
        pool, conn = mock_pool
        request_id = 'test-request-id-123'
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_controller_user), \
             patch('database.technician_queries.get_available_technicians', return_value=[sample_technician_user]), \
             patch.object(workflow_handler.workflow_engine, 'transition_workflow', return_value=True):
            
            # Mock callback query
            callback = AsyncMock()
            callback.from_user.id = sample_controller_user['telegram_id']
            callback.data = f"assign_technical_to_technician_{sample_technician_user['id']}_{request_id}"
            callback.message.edit_text = AsyncMock()
            
            # Test technician assignment
            await workflow_handler.assign_to_technician(callback)
            
            # Verify workflow transition was called
            workflow_handler.workflow_engine.transition_workflow.assert_called_once_with(
                request_id,
                WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                UserRole.CONTROLLER.value,
                {
                    'technician_id': sample_technician_user['id'],
                    'actor_id': sample_controller_user['id'],
                    'assigned_at': pytest.approx(str(datetime.now()), abs=5),
                    'technician_name': sample_technician_user['full_name']
                }
            )
            
            # Verify success message
            callback.message.edit_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_technician_starts_diagnostics(self, workflow_handler, sample_technician_user, mock_pool):
        """
        Test Requirement 2.4: Technician starts diagnostics
        """
        pool, conn = mock_pool
        request_id = 'test-request-id-123'
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_technician_user), \
             patch.object(workflow_handler.workflow_engine, 'transition_workflow', return_value=True):
            
            # Mock callback query
            callback = AsyncMock()
            callback.from_user.id = sample_technician_user['telegram_id']
            callback.data = f"start_technical_diagnostics_{request_id}"
            callback.message.edit_text = AsyncMock()
            
            # Test diagnostics start
            await workflow_handler.start_diagnostics(callback)
            
            # Verify workflow transition was called
            workflow_handler.workflow_engine.transition_workflow.assert_called_once_with(
                request_id,
                WorkflowAction.START_DIAGNOSTICS.value,
                UserRole.TECHNICIAN.value,
                {
                    'actor_id': sample_technician_user['id'],
                    'diagnostics_started_at': pytest.approx(str(datetime.now()), abs=5),
                    'diagnostics_notes': 'Diagnostics started'
                }
            )
            
            # Verify warehouse involvement decision UI
            callback.message.edit_text.assert_called()
            args, kwargs = callback.message.edit_text.call_args
            assert "warehouse" in args[0].lower() or "ombor" in args[0].lower()
    
    @pytest.mark.asyncio
    async def test_technician_decides_no_warehouse_involvement(self, workflow_handler, sample_technician_user, mock_pool):
        """
        Test Requirement 2.5: Technician decides no warehouse involvement needed
        """
        pool, conn = mock_pool
        request_id = 'test-request-id-123'
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_technician_user):
            
            # Mock callback query for no warehouse involvement
            callback = AsyncMock()
            callback.from_user.id = sample_technician_user['telegram_id']
            callback.data = f"decide_warehouse_involvement_no_{request_id}"
            callback.message.edit_text = AsyncMock()
            
            # Test warehouse involvement decision
            await workflow_handler.decide_warehouse_involvement(callback)
            
            # Verify resolution UI is shown
            callback.message.edit_text.assert_called()
            args, kwargs = callback.message.edit_text.call_args
            assert "resolve" in args[0].lower() or "hal qil" in args[0].lower()
    
    @pytest.mark.asyncio
    async def test_technician_resolves_without_warehouse(self, workflow_handler, sample_technician_user, mock_pool):
        """
        Test Requirement 2.6: Technician resolves issue without inventory
        """
        pool, conn = mock_pool
        request_id = 'test-request-id-123'
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_technician_user):
            
            # Mock callback query and state
            callback = AsyncMock()
            callback.from_user.id = sample_technician_user['telegram_id']
            callback.data = f"resolve_without_warehouse_{request_id}"
            callback.message.edit_text = AsyncMock()
            
            state = AsyncMock()
            
            # Test resolution initiation
            await workflow_handler.resolve_without_warehouse(callback, state)
            
            # Verify state is set for comments
            state.update_data.assert_called_with(resolving_request_id=request_id)
            state.set_state.assert_called()
            
            # Verify comment prompt
            callback.message.edit_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_technician_completes_resolution_with_comments(self, workflow_handler, sample_technician_user, mock_pool):
        """
        Test Requirement 2.7: Technician adds resolution comments and closes request
        """
        pool, conn = mock_pool
        request_id = 'test-request-id-123'
        resolution_comments = "Fixed network configuration issue. Connection speed restored."
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_technician_user), \
             patch.object(workflow_handler.workflow_engine, 'transition_workflow', return_value=True), \
             patch.object(workflow_handler, '_send_completion_notification', return_value=True):
            
            # Mock message and state
            message = AsyncMock()
            message.from_user.id = sample_technician_user['telegram_id']
            message.text = resolution_comments
            message.answer = AsyncMock()
            
            state = AsyncMock()
            state.get_data.return_value = {'resolving_request_id': request_id}
            
            # Test resolution comments processing
            await workflow_handler.process_resolution_comments(message, state)
            
            # Verify workflow completion
            workflow_handler.workflow_engine.transition_workflow.assert_called_once_with(
                request_id,
                WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value,
                UserRole.TECHNICIAN.value,
                {
                    'actor_id': sample_technician_user['id'],
                    'resolution_comments': resolution_comments,
                    'completed_at': pytest.approx(str(datetime.now()), abs=5),
                    'warehouse_involved': False
                }
            )
            
            # Verify completion notification sent
            workflow_handler._send_completion_notification.assert_called_once_with(request_id)
            
            # Verify success message
            message.answer.assert_called()
            state.clear.assert_called()
    
    @pytest.mark.asyncio
    async def test_client_receives_completion_notification(self, workflow_handler, sample_client_user, mock_pool, mock_bot):
        """
        Test Requirement 2.8: Client receives completion notification
        """
        pool, conn = mock_pool
        request_id = 'test-request-id-123'
        
        # Mock service request
        mock_request = AsyncMock()
        mock_request.client_id = sample_client_user['id']
        mock_request.description = 'Internet connection is very slow'
        mock_request.id = request_id
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_client_user), \
             patch.object(workflow_handler.state_manager, 'get_request', return_value=mock_request), \
             patch('loader.bot', mock_bot):
            
            # Test completion notification
            await workflow_handler._send_completion_notification(request_id)
            
            # Verify notification was sent to client
            mock_bot.send_message.assert_called_once()
            args, kwargs = mock_bot.send_message.call_args
            
            assert kwargs['chat_id'] == sample_client_user['telegram_id']
            assert 'yakunlandi' in kwargs['text'] or 'завершено' in kwargs['text']
            assert 'reply_markup' in kwargs
    
    @pytest.mark.asyncio
    async def test_client_rates_technical_service(self, workflow_handler, sample_client_user, mock_pool):
        """
        Test Requirement 2.9: Client rates technical service completion
        """
        pool, conn = mock_pool
        request_id = 'test-request-id-123'
        rating = 5
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_client_user), \
             patch.object(workflow_handler.workflow_engine, 'complete_workflow', return_value=True):
            
            # Mock callback query for rating
            callback = AsyncMock()
            callback.from_user.id = sample_client_user['telegram_id']
            callback.data = f"technical_rating_{rating}_{request_id}"
            callback.message.edit_text = AsyncMock()
            
            # Test service rating
            await workflow_handler.process_service_rating(callback)
            
            # Verify workflow completion with rating
            workflow_handler.workflow_engine.complete_workflow.assert_called_once_with(
                request_id,
                {
                    'rating': rating,
                    'feedback': f"Technical service rated {rating} stars",
                    'actor_id': sample_client_user['id'],
                    'rated_at': pytest.approx(str(datetime.now()), abs=5)
                }
            )
            
            # Verify thank you message
            callback.message.edit_text.assert_called()
            args, kwargs = callback.message.edit_text.call_args
            assert str(rating) in args[0]
    
    @pytest.mark.asyncio
    async def test_complete_workflow_end_to_end(self, workflow_handler, sample_client_user, sample_controller_user, sample_technician_user, mock_pool, mock_bot):
        """
        Test complete end-to-end workflow execution
        """
        pool, conn = mock_pool
        request_id = 'test-request-id-123'
        
        # Mock all dependencies
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id') as mock_get_user, \
             patch('database.technician_queries.get_available_technicians', return_value=[sample_technician_user]), \
             patch.object(workflow_handler.workflow_engine, 'initiate_workflow', return_value=request_id), \
             patch.object(workflow_handler.workflow_engine, 'transition_workflow', return_value=True), \
             patch.object(workflow_handler.workflow_engine, 'complete_workflow', return_value=True), \
             patch.object(workflow_handler.state_manager, 'get_request') as mock_get_request, \
             patch('loader.bot', mock_bot):
            
            # Setup mock request
            mock_request = AsyncMock()
            mock_request.client_id = sample_client_user['id']
            mock_request.description = 'Internet connection is very slow'
            mock_request.id = request_id
            mock_request.workflow_type = WorkflowType.TECHNICAL_SERVICE.value
            mock_request.created_at = datetime.now()
            mock_get_request.return_value = mock_request
            
            # Step 1: Client submits request
            mock_get_user.return_value = sample_client_user
            
            message = AsyncMock()
            message.from_user.id = sample_client_user['telegram_id']
            message.text = "Internet connection is very slow"
            
            state = AsyncMock()
            state.get_data.return_value = {
                'issue_description': 'Internet connection is very slow',
                'issue_type': 'technical_support'
            }
            
            callback = AsyncMock()
            callback.from_user.id = sample_client_user['telegram_id']
            callback.message.edit_text = AsyncMock()
            
            await workflow_handler.start_technical_request(message, state)
            await workflow_handler.process_issue_description(message, state)
            await workflow_handler.confirm_technical_request(callback, state)
            
            # Step 2: Controller assigns to technician
            mock_get_user.return_value = sample_controller_user
            
            callback.from_user.id = sample_controller_user['telegram_id']
            callback.data = f"assign_technical_to_technician_{sample_technician_user['id']}_{request_id}"
            
            await workflow_handler.assign_to_technician(callback)
            
            # Step 3: Technician handles request
            mock_get_user.return_value = sample_technician_user
            
            callback.from_user.id = sample_technician_user['telegram_id']
            callback.data = f"handle_request_{request_id}"
            
            await workflow_handler.handle_technical_request(callback)
            
            # Step 4: Technician starts diagnostics
            callback.data = f"start_technical_diagnostics_{request_id}"
            await workflow_handler.start_diagnostics(callback)
            
            # Step 5: Technician decides no warehouse involvement
            callback.data = f"decide_warehouse_involvement_no_{request_id}"
            await workflow_handler.decide_warehouse_involvement(callback)
            
            # Step 6: Technician resolves without warehouse
            callback.data = f"resolve_without_warehouse_{request_id}"
            await workflow_handler.resolve_without_warehouse(callback, state)
            
            # Step 7: Technician adds resolution comments
            message.from_user.id = sample_technician_user['telegram_id']
            message.text = "Fixed network configuration issue"
            state.get_data.return_value = {'resolving_request_id': request_id}
            
            await workflow_handler.process_resolution_comments(message, state)
            
            # Step 8: Client rates service
            mock_get_user.return_value = sample_client_user
            
            callback.from_user.id = sample_client_user['telegram_id']
            callback.data = f"technical_rating_5_{request_id}"
            
            await workflow_handler.process_service_rating(callback)
            
            # Verify all workflow transitions occurred
            assert workflow_handler.workflow_engine.initiate_workflow.called
            assert workflow_handler.workflow_engine.transition_workflow.call_count >= 2
            assert workflow_handler.workflow_engine.complete_workflow.called
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_user_role(self, workflow_handler):
        """
        Test error handling for invalid user roles
        """
        # Mock user with wrong role
        wrong_role_user = {
            'id': 999,
            'telegram_id': 99999,
            'role': UserRole.ADMIN.value,
            'language': 'uz'
        }
        
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=wrong_role_user):
            
            callback = AsyncMock()
            callback.from_user.id = wrong_role_user['telegram_id']
            callback.answer = AsyncMock()
            
            # Test technician-only action with wrong role
            await workflow_handler.start_diagnostics(callback)
            
            # Verify access denied
            callback.answer.assert_called_with("Sizda bu amalni bajarish huquqi yo'q!")
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_request(self, workflow_handler, sample_technician_user):
        """
        Test error handling for missing requests
        """
        with patch('handlers.technical_service_workflow.get_user_by_telegram_id', return_value=sample_technician_user), \
             patch.object(workflow_handler.state_manager, 'get_request', return_value=None):
            
            callback = AsyncMock()
            callback.from_user.id = sample_technician_user['telegram_id']
            callback.data = "handle_request_nonexistent-id"
            callback.answer = AsyncMock()
            
            # Test handling non-existent request
            await workflow_handler.handle_technical_request(callback)
            
            # Verify error message
            callback.answer.assert_called()
            args = callback.answer.call_args[0]
            assert "topilmadi" in args[0] or "не найден" in args[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])