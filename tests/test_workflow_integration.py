"""
Integration Tests for Workflow System with Existing Bot Infrastructure
Tests the integration between the workflow system and existing handlers, database, and components
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from database.models import UserRole, WorkflowType, WorkflowAction, RequestStatus
from utils.workflow_integration import WorkflowIntegration, create_workflow_request, transition_workflow
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory
from utils.inventory_manager import InventoryManagerFactory
from handlers.workflow_integration_handler import WorkflowIntegrationHandler


class TestWorkflowSystemIntegration:
    """Test workflow system integration with existing infrastructure"""
    
    @pytest.fixture
    async def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = conn
        return pool
    
    @pytest.fixture
    async def workflow_components(self, mock_pool):
        """Setup workflow system components"""
        state_manager = StateManagerFactory.create_state_manager()
        notification_system = NotificationSystemFactory.create_notification_system()
        inventory_manager = InventoryManagerFactory.create_inventory_manager()
        
        workflow_engine = WorkflowEngineFactory.create_workflow_engine(
            state_manager, notification_system, inventory_manager
        )
        
        return {
            'state_manager': state_manager,
            'notification_system': notification_system,
            'inventory_manager': inventory_manager,
            'workflow_engine': workflow_engine
        }
    
    @pytest.fixture
    def mock_user(self):
        """Mock user data"""
        return {
            'id': 1,
            'telegram_id': 123456789,
            'full_name': 'Test User',
            'role': UserRole.CLIENT.value,
            'language': 'ru'
        }
    
    @pytest.fixture
    def mock_request(self):
        """Mock service request"""
        return {
            'id': 'test-request-123',
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 1,
            'role_current ': UserRole.MANAGER.value,
            'current_status': RequestStatus.IN_PROGRESS.value,
            'description': 'Test connection request',
            'location': 'Test location',
            'priority': 'medium',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    @pytest.mark.asyncio
    async def test_workflow_engine_initialization(self, workflow_components):
        """Test that workflow engine initializes correctly"""
        workflow_engine = workflow_components['workflow_engine']
        
        assert workflow_engine is not None
        assert workflow_engine.state_manager is not None
        assert workflow_engine.notification_system is not None
        assert workflow_engine.inventory_manager is not None
        
        # Test workflow definitions are loaded
        definitions = workflow_engine.get_available_workflows()
        assert WorkflowType.CONNECTION_REQUEST.value in definitions
        assert WorkflowType.TECHNICAL_SERVICE.value in definitions
        assert WorkflowType.CALL_CENTER_DIRECT.value in definitions
    
    @pytest.mark.asyncio
    async def test_workflow_integration_helper(self, mock_pool):
        """Test WorkflowIntegration helper class"""
        integration = WorkflowIntegration()
        
        # Mock bot instance
        with patch('utils.workflow_integration.bot') as mock_bot:
            mock_bot.workflow_engine = AsyncMock()
            mock_bot.state_manager = AsyncMock()
            mock_bot.notification_system = AsyncMock()
            mock_bot.inventory_manager = AsyncMock()
            
            # Test getting components
            workflow_manager = await integration.get_workflow_manager()
            state_manager = await integration.get_state_manager()
            notification_system = await integration.get_notification_system()
            inventory_manager = await integration.get_inventory_manager()
            
            assert workflow_manager is not None
            assert state_manager is not None
            assert notification_system is not None
            assert inventory_manager is not None
    
    @pytest.mark.asyncio
    async def test_create_workflow_request_integration(self, mock_pool, mock_user):
        """Test creating workflow request through integration"""
        with patch('utils.workflow_integration.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('utils.workflow_integration.WorkflowIntegration.get_workflow_manager') as mock_get_engine:
                mock_engine = AsyncMock()
                mock_engine.initiate_workflow.return_value = 'test-request-123'
                mock_get_engine.return_value = mock_engine
                
                # Test creating connection request
                request_id = await create_workflow_request(
                    WorkflowType.CONNECTION_REQUEST.value,
                    123456789,
                    {
                        'description': 'Test connection',
                        'location': 'Test location',
                        'priority': 'medium'
                    }
                )
                
                assert request_id == 'test-request-123'
                mock_engine.initiate_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transition_workflow_integration(self, mock_pool, mock_user):
        """Test workflow transition through integration"""
        with patch('utils.workflow_integration.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            with patch('utils.workflow_integration.WorkflowIntegration.get_workflow_manager') as mock_get_engine:
                mock_engine = AsyncMock()
                mock_engine.transition_workflow.return_value = True
                mock_get_engine.return_value = mock_engine
                
                # Test transitioning workflow
                success = await transition_workflow(
                    'test-request-123',
                    WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
                    123456789,
                    {'junior_manager_id': 2}
                )
                
                assert success is True
                mock_engine.transition_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_queries_integration(self, mock_pool):
        """Test that workflow database queries work with existing infrastructure"""
        from database.base_queries import (
            get_service_request_by_id,
            get_service_requests_by_role,
            get_state_transitions_by_request
        )
        
        # Mock database responses
        mock_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
            'id': 'test-request-123',
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 1,
            'role_current ': UserRole.MANAGER.value,
            'current_status': RequestStatus.IN_PROGRESS.value,
            'description': 'Test request',
            'location': 'Test location',
            'priority': 'medium',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'contact_info': '{}',
            'state_data': '{}',
            'equipment_used': '[]',
            'inventory_updated': False,
            'completion_rating': None,
            'feedback_comments': None
        }
        
        with patch('database.base_queries.bot') as mock_bot:
            mock_bot.db = mock_pool
            
            # Test getting service request
            request = await get_service_request_by_id('test-request-123')
            assert request is not None
            assert request['id'] == 'test-request-123'
            assert request['workflow_type'] == WorkflowType.CONNECTION_REQUEST.value
    
    @pytest.mark.asyncio
    async def test_handler_integration(self):
        """Test that workflow integration handler works with existing handler structure"""
        handler = WorkflowIntegrationHandler()
        
        assert handler.router is not None
        assert handler.workflow_integration is not None
        
        # Test that router has handlers registered
        router = handler.get_router()
        assert len(router.callback_query.handlers) > 0
    
    @pytest.mark.asyncio
    async def test_keyboard_integration(self):
        """Test that workflow keyboards integrate with existing keyboard structure"""
        from keyboards.workflow_buttons import (
            workflow_request_type_keyboard,
            workflow_action_keyboard,
            user_selection_keyboard
        )
        
        # Test workflow request type keyboard
        keyboard = workflow_request_type_keyboard('ru')
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) > 0
        
        # Test workflow action keyboard
        actions = [WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value]
        action_keyboard = workflow_action_keyboard(UserRole.MANAGER.value, actions, 'ru')
        assert action_keyboard is not None
        assert len(action_keyboard.inline_keyboard) > 0
        
        # Test user selection keyboard
        users = [{'id': 1, 'full_name': 'Test User'}]
        user_keyboard = user_selection_keyboard(users, 'assign_technician', 'ru')
        assert user_keyboard is not None
        assert len(user_keyboard.inline_keyboard) > 0
    
    @pytest.mark.asyncio
    async def test_state_integration(self):
        """Test that workflow states integrate with existing FSM structure"""
        from states.workflow_states import (
            WorkflowRequestStates,
            ConnectionWorkflowStates,
            TechnicalServiceStates,
            is_workflow_state,
            get_state_description
        )
        
        # Test state groups exist
        assert WorkflowRequestStates is not None
        assert ConnectionWorkflowStates is not None
        assert TechnicalServiceStates is not None
        
        # Test state detection
        assert is_workflow_state(WorkflowRequestStates.selecting_type) is True
        assert is_workflow_state(ConnectionWorkflowStates.selecting_connection_type) is True
        
        # Test state descriptions
        description = get_state_description(WorkflowRequestStates.selecting_type, 'ru')
        assert description is not None
        assert len(description) > 0
    
    @pytest.mark.asyncio
    async def test_notification_system_integration(self, mock_pool):
        """Test that notification system integrates with existing infrastructure"""
        notification_system = NotificationSystemFactory.create_notification_system()
        
        # Mock database operations
        with patch('utils.notification_system.bot') as mock_bot:
            mock_bot.db = mock_pool
            mock_bot.send_message = AsyncMock()
            
            # Mock user data
            mock_pool.acquire.return_value.__aenter__.return_value.fetch.return_value = [
                {
                    'id': 1,
                    'telegram_id': 123456789,
                    'full_name': 'Test Manager',
                    'language': 'ru'
                }
            ]
            
            # Mock request data
            mock_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
                'description': 'Test request',
                'priority': 'medium',
                'created_at': datetime.now()
            }
            
            # Test sending notification
            success = await notification_system.send_assignment_notification(
                UserRole.MANAGER.value,
                'test-request-123',
                WorkflowType.CONNECTION_REQUEST.value
            )
            
            assert success is True
            mock_bot.send_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_inventory_manager_integration(self, mock_pool):
        """Test that inventory manager integrates with existing infrastructure"""
        inventory_manager = InventoryManagerFactory.create_inventory_manager()
        
        with patch('utils.inventory_manager.bot') as mock_bot:
            mock_bot.db = mock_pool
            
            # Mock material data
            mock_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
                'quantity_in_stock': 10,
                'name': 'Test Material'
            }
            
            # Test reserving equipment
            equipment_list = [{'material_id': 1, 'quantity': 2}]
            success = await inventory_manager.reserve_equipment('test-request-123', equipment_list)
            
            # Should not fail (may return False due to mocking, but shouldn't raise exception)
            assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_legacy_bridge_integration(self):
        """Test that legacy workflow bridge works with existing zayavka system"""
        from utils.workflow_integration import LegacyWorkflowBridge
        
        with patch('utils.workflow_integration.get_zayavka_by_id') as mock_get_zayavka:
            mock_get_zayavka.return_value = {
                'id': 1,
                'user_id': 123456789,
                'description': 'Test zayavka',
                'address': 'Test address',
                'priority': 'medium',
                'phone': '+1234567890'
            }
            
            with patch('utils.workflow_integration.WorkflowIntegration.create_workflow_request') as mock_create:
                mock_create.return_value = 'test-request-123'
                
                # Test migrating zayavka to workflow
                request_id = await LegacyWorkflowBridge.migrate_zayavka_to_workflow(1)
                
                assert request_id == 'test-request-123'
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_pool):
        """Test that error handling works correctly in integration scenarios"""
        integration = WorkflowIntegration()
        
        # Test with invalid user
        with patch('utils.workflow_integration.get_user_by_telegram_id') as mock_get_user:
            mock_get_user.return_value = None
            
            request_id = await integration.create_workflow_request(
                WorkflowType.CONNECTION_REQUEST.value,
                999999999,  # Invalid user ID
                {'description': 'Test'}
            )
            
            assert request_id is None
        
        # Test with workflow engine unavailable
        with patch('utils.workflow_integration.WorkflowIntegration.get_workflow_manager') as mock_get_engine:
            mock_get_engine.return_value = None
            
            success = await integration.transition_workflow(
                'test-request-123',
                WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
                123456789,
                {}
            )
            
            assert success is False
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_operations(self, workflow_components, mock_pool):
        """Test that workflow system handles concurrent operations correctly"""
        workflow_engine = workflow_components['workflow_engine']
        
        with patch('utils.state_manager.bot') as mock_bot:
            mock_bot.db = mock_pool
            
            # Mock database operations for concurrent requests
            mock_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = None
            mock_pool.acquire.return_value.__aenter__.return_value.execute.return_value = "INSERT 0 1"
            
            # Create multiple workflow requests concurrently
            tasks = []
            for i in range(5):
                task = workflow_engine.initiate_workflow(
                    WorkflowType.CONNECTION_REQUEST.value,
                    {
                        'client_id': i + 1,
                        'description': f'Test request {i}',
                        'location': f'Test location {i}',
                        'priority': 'medium'
                    }
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that all requests were processed (may be None due to mocking)
            assert len(results) == 5
            for result in results:
                assert not isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_workflow_system_cleanup(self, mock_pool):
        """Test that workflow system cleanup operations work correctly"""
        from database.base_queries import cleanup_old_notifications
        
        with patch('database.base_queries.bot') as mock_bot:
            mock_bot.db = mock_pool
            mock_pool.acquire.return_value.__aenter__.return_value.execute.return_value = "DELETE 5"
            
            # Test cleanup operation
            deleted_count = await cleanup_old_notifications(7)
            
            assert deleted_count == 5
    
    def test_workflow_constants_integration(self):
        """Test that workflow constants integrate with existing model constants"""
        from database.models import ModelConstants
        
        # Test that workflow constants are available
        assert hasattr(ModelConstants, 'WORKFLOW_TYPES')
        assert hasattr(ModelConstants, 'REQUEST_STATUSES')
        assert hasattr(ModelConstants, 'WORKFLOW_ACTIONS')
        
        # Test that workflow types are properly defined
        assert WorkflowType.CONNECTION_REQUEST.value in ModelConstants.WORKFLOW_TYPES
        assert WorkflowType.TECHNICAL_SERVICE.value in ModelConstants.WORKFLOW_TYPES
        assert WorkflowType.CALL_CENTER_DIRECT.value in ModelConstants.WORKFLOW_TYPES


class TestWorkflowSystemCompatibility:
    """Test compatibility with existing bot components"""
    
    def test_role_compatibility(self):
        """Test that workflow system roles are compatible with existing roles"""
        from database.models import UserRole, ModelConstants
        
        # Test that all workflow roles exist in existing role system
        workflow_roles = [
            UserRole.CLIENT.value,
            UserRole.MANAGER.value,
            UserRole.JUNIOR_MANAGER.value,
            UserRole.CONTROLLER.value,
            UserRole.TECHNICIAN.value,
            UserRole.WAREHOUSE.value,
            UserRole.CALL_CENTER.value,
            UserRole.CALL_CENTER_SUPERVISOR.value
        ]
        
        for role in workflow_roles:
            assert role in ModelConstants.USER_ROLES
    
    def test_status_compatibility(self):
        """Test that workflow statuses are compatible with existing status system"""
        from database.models import RequestStatus, ZayavkaStatus
        
        # Test that workflow statuses don't conflict with existing statuses
        workflow_statuses = [status.value for status in RequestStatus]
        zayavka_statuses = [status.value for status in ZayavkaStatus]
        
        # Should not have conflicting status names
        conflicts = set(workflow_statuses) & set(zayavka_statuses)
        # Some overlap is expected (like 'cancelled'), but should be minimal
        assert len(conflicts) <= 2
    
    def test_database_schema_compatibility(self):
        """Test that workflow database schema is compatible with existing schema"""
        # This would typically involve checking actual database schema
        # For now, we'll test that the models are properly defined
        from database.models import ServiceRequest, StateTransition
        
        # Test that workflow models have required fields
        assert hasattr(ServiceRequest, 'id')
        assert hasattr(ServiceRequest, 'workflow_type')
        assert hasattr(ServiceRequest, 'client_id')
        assert hasattr(ServiceRequest, 'role_current ')
        assert hasattr(ServiceRequest, 'current_status')
        
        assert hasattr(StateTransition, 'id')
        assert hasattr(StateTransition, 'request_id')
        assert hasattr(StateTransition, 'from_role')
        assert hasattr(StateTransition, 'to_role')
        assert hasattr(StateTransition, 'action')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])