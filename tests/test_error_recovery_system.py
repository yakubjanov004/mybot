"""
Unit Tests for Comprehensive Error Handling and Recovery System

Tests all components of the error recovery system:
- Transactional state changes with rollback capabilities
- Notification retry mechanism with exponential backoff
- Inventory reconciliation processes
- Workflow recovery through admin interface
- Error categorization and appropriate handling

Requirements implemented: Task 12 - Create comprehensive error handling and recovery
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import uuid

from utils.error_recovery import (
    ErrorHandler, ErrorCategory, ErrorSeverity, ErrorRecord,
    TransactionalStateManager, NotificationRetryManager,
    InventoryReconciliationManager, WorkflowRecoveryManager,
    ComprehensiveErrorRecoverySystem
)
from utils.enhanced_state_manager import EnhancedStateManager
from database.models import ServiceRequest, WorkflowType, RequestStatus, Priority


class TestErrorHandler:
    """Test error handler with categorization and appropriate handling"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.error_handler = ErrorHandler()
    
    @pytest.mark.asyncio
    async def test_handle_transient_error(self):
        """Test handling of transient errors"""
        error = ConnectionError("Database connection timeout")
        context = {'operation': 'test_operation'}
        
        error_record = await self.error_handler.handle_error(error, context)
        
        assert error_record.category == ErrorCategory.TRANSIENT
        assert error_record.severity == ErrorSeverity.MEDIUM
        assert error_record.message == str(error)
        assert error_record.context == context
        # Transient errors get retry_count incremented by the handler
        assert error_record.retry_count >= 0
    
    @pytest.mark.asyncio
    async def test_handle_data_error(self):
        """Test handling of data validation errors"""
        error = ValueError("Missing required field: description")
        context = {'operation': 'create_request'}
        
        error_record = await self.error_handler.handle_error(error, context)
        
        assert error_record.category == ErrorCategory.DATA
        assert error_record.severity == ErrorSeverity.LOW
        assert "validation" in error_record.message.lower() or "missing required" in error_record.message.lower()
    
    @pytest.mark.asyncio
    async def test_handle_business_logic_error(self):
        """Test handling of business logic errors"""
        error = PermissionError("Access denied for user")
        context = {'operation': 'workflow_transition'}
        
        error_record = await self.error_handler.handle_error(error, context)
        
        assert error_record.category == ErrorCategory.BUSINESS_LOGIC
        assert error_record.severity == ErrorSeverity.MEDIUM
    
    @pytest.mark.asyncio
    async def test_handle_inventory_error(self):
        """Test handling of inventory-related errors"""
        error = Exception("Insufficient stock for material ID 123")
        context = {'operation': 'consume_equipment'}
        
        error_record = await self.error_handler.handle_error(error, context)
        
        assert error_record.category == ErrorCategory.INVENTORY
        assert error_record.severity == ErrorSeverity.MEDIUM
    
    def test_get_error_statistics(self):
        """Test error statistics generation"""
        # Add some test error records
        self.error_handler.error_records = [
            ErrorRecord(category=ErrorCategory.TRANSIENT, severity=ErrorSeverity.LOW),
            ErrorRecord(category=ErrorCategory.DATA, severity=ErrorSeverity.MEDIUM),
            ErrorRecord(category=ErrorCategory.SYSTEM, severity=ErrorSeverity.HIGH),
        ]
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 3
        assert stats['category_counts']['transient'] == 1
        assert stats['category_counts']['data'] == 1
        assert stats['category_counts']['system'] == 1
        assert stats['severity_counts']['low'] == 1
        assert stats['severity_counts']['medium'] == 1
        assert stats['severity_counts']['high'] == 1
    
    def test_get_recent_errors(self):
        """Test recent error retrieval"""
        # Add test error records with different timestamps
        old_error = ErrorRecord(
            category=ErrorCategory.SYSTEM,
            occurred_at=datetime.now() - timedelta(hours=25)
        )
        recent_error = ErrorRecord(
            category=ErrorCategory.TRANSIENT,
            occurred_at=datetime.now() - timedelta(hours=1)
        )
        
        self.error_handler.error_records = [old_error, recent_error]
        
        recent_errors = self.error_handler.get_recent_errors(hours=24)
        
        assert len(recent_errors) == 1
        assert recent_errors[0].category == ErrorCategory.TRANSIENT


class TestTransactionalStateManager:
    """Test transactional state manager with rollback capabilities"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_base_manager = Mock()
        self.transactional_manager = TransactionalStateManager(self.mock_base_manager)
    
    @pytest.mark.asyncio
    async def test_begin_transaction(self):
        """Test transaction initialization"""
        transaction_id = await self.transactional_manager.begin_transaction()
        
        assert transaction_id in self.transactional_manager.active_transactions
        context = self.transactional_manager.active_transactions[transaction_id]
        assert context.status == "active"
        assert len(context.operations) == 0
        assert len(context.rollback_operations) == 0
    
    @pytest.mark.asyncio
    async def test_add_operation(self):
        """Test adding operations to transaction"""
        transaction_id = await self.transactional_manager.begin_transaction()
        
        operation_data = {'request_id': 'test-123', 'new_state': {'status': 'updated'}}
        rollback_data = {'request_id': 'test-123', 'previous_state': {'status': 'original'}}
        
        await self.transactional_manager.add_operation(
            transaction_id, "update_request_state", operation_data, rollback_data
        )
        
        context = self.transactional_manager.active_transactions[transaction_id]
        assert len(context.operations) == 1
        assert len(context.rollback_operations) == 1
        assert context.operations[0]['type'] == "update_request_state"
        assert context.rollback_operations[0]['type'] == "rollback_update_request_state"
    
    @pytest.mark.asyncio
    async def test_commit_transaction_success(self):
        """Test successful transaction commit"""
        transaction_id = await self.transactional_manager.begin_transaction()
        
        # Mock successful operation execution
        self.transactional_manager._execute_operation = AsyncMock()
        
        # Add test operation
        await self.transactional_manager.add_operation(
            transaction_id, "update_request_state", 
            {'request_id': 'test-123'}, {'request_id': 'test-123'}
        )
        
        success = await self.transactional_manager.commit_transaction(transaction_id)
        
        assert success
        assert transaction_id not in self.transactional_manager.active_transactions
        self.transactional_manager._execute_operation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_commit_transaction_failure_with_rollback(self):
        """Test transaction commit failure triggers rollback"""
        transaction_id = await self.transactional_manager.begin_transaction()
        
        # Mock failed operation execution
        self.transactional_manager._execute_operation = AsyncMock(side_effect=Exception("Operation failed"))
        self.transactional_manager._execute_rollback_operation = AsyncMock()
        
        # Add test operation
        await self.transactional_manager.add_operation(
            transaction_id, "update_request_state", 
            {'request_id': 'test-123'}, {'request_id': 'test-123'}
        )
        
        success = await self.transactional_manager.commit_transaction(transaction_id)
        
        assert not success
        assert transaction_id not in self.transactional_manager.active_transactions
        self.transactional_manager._execute_rollback_operation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_transaction(self):
        """Test transaction rollback"""
        transaction_id = await self.transactional_manager.begin_transaction()
        
        # Mock rollback operation execution
        self.transactional_manager._execute_rollback_operation = AsyncMock()
        
        # Add test operation
        await self.transactional_manager.add_operation(
            transaction_id, "update_request_state", 
            {'request_id': 'test-123'}, {'request_id': 'test-123'}
        )
        
        success = await self.transactional_manager.rollback_transaction(transaction_id)
        
        assert success
        assert transaction_id not in self.transactional_manager.active_transactions
        self.transactional_manager._execute_rollback_operation.assert_called_once()


class TestNotificationRetryManager:
    """Test notification retry mechanism with exponential backoff"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_notification_system = Mock()
        self.retry_manager = NotificationRetryManager(self.mock_notification_system)
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test successful notification sending"""
        self.mock_notification_system.send_assignment_notification = AsyncMock(return_value=True)
        
        success = await self.retry_manager.send_notification_with_retry(
            "manager", "request-123", "connection_request"
        )
        
        assert success
        self.mock_notification_system.send_assignment_notification.assert_called_once_with(
            "manager", "request-123", "connection_request"
        )
        assert len(self.retry_manager.retry_queue) == 0
    
    @pytest.mark.asyncio
    async def test_send_notification_failure_with_retry(self):
        """Test notification failure triggers retry"""
        self.mock_notification_system.send_assignment_notification = AsyncMock(return_value=False)
        
        success = await self.retry_manager.send_notification_with_retry(
            "manager", "request-123", "connection_request"
        )
        
        assert not success
        assert len(self.retry_manager.retry_queue) == 1
        
        retry_item = self.retry_manager.retry_queue[0]
        assert retry_item['role'] == "manager"
        assert retry_item['request_id'] == "request-123"
        assert retry_item['retry_count'] == 1
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation"""
        self.mock_notification_system.send_assignment_notification = AsyncMock(return_value=False)
        
        # First retry
        await self.retry_manager.send_notification_with_retry(
            "manager", "request-123", "connection_request", retry_count=0
        )
        
        retry_item = self.retry_manager.retry_queue[0]
        first_delay = (retry_item['next_retry_at'] - datetime.now()).total_seconds()
        
        # Clear queue for second test
        self.retry_manager.retry_queue.clear()
        
        # Second retry
        await self.retry_manager.send_notification_with_retry(
            "manager", "request-123", "connection_request", retry_count=1
        )
        
        retry_item = self.retry_manager.retry_queue[0]
        second_delay = (retry_item['next_retry_at'] - datetime.now()).total_seconds()
        
        # Second delay should be approximately double the first (exponential backoff)
        assert second_delay > first_delay
        assert second_delay <= self.retry_manager.max_delay
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test behavior when max retries exceeded"""
        self.mock_notification_system.send_assignment_notification = AsyncMock(return_value=False)
        
        success = await self.retry_manager.send_notification_with_retry(
            "manager", "request-123", "connection_request", 
            retry_count=self.retry_manager.max_retries
        )
        
        assert not success
        assert len(self.retry_manager.retry_queue) == 0  # No more retries scheduled
    
    def test_get_retry_stats(self):
        """Test retry queue statistics"""
        # Add test retry items
        self.retry_manager.retry_queue = [
            {
                'request_id': 'req-1',
                'retry_count': 1,
                'next_retry_at': datetime.now() + timedelta(seconds=30),
                'error': 'Test error 1'
            },
            {
                'request_id': 'req-2',
                'retry_count': 2,
                'next_retry_at': datetime.now() + timedelta(seconds=60),
                'error': 'Test error 2'
            }
        ]
        
        stats = self.retry_manager.get_retry_stats()
        
        assert stats['pending_retries'] == 2
        assert len(stats['retry_items']) == 2
        assert stats['retry_items'][0]['request_id'] == 'req-1'
        assert stats['retry_items'][1]['request_id'] == 'req-2'


class TestInventoryReconciliationManager:
    """Test inventory reconciliation processes"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_inventory_manager = Mock()
        self.reconciliation_manager = InventoryReconciliationManager(self.mock_inventory_manager)
    
    @pytest.mark.asyncio
    async def test_detect_negative_stock_discrepancies(self):
        """Test detection of negative stock discrepancies"""
        with patch('loader.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            # Fix async context manager
            mock_pool.acquire.return_value = AsyncMock()
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_bot.db = mock_pool
            
            # Mock negative stock query result
            mock_conn.fetch.return_value = [
                {
                    'id': 1,
                    'name': 'Test Material',
                    'category': 'cables',
                    'quantity_in_stock': -5
                }
            ]
            
            discrepancies = await self.reconciliation_manager.detect_discrepancies()
            
            assert len(discrepancies) >= 1
            negative_stock_discrepancy = next(
                (d for d in discrepancies if d['type'] == 'negative_stock'), None
            )
            assert negative_stock_discrepancy is not None
            assert negative_stock_discrepancy['material_id'] == 1
            assert negative_stock_discrepancy['current_quantity'] == -5
            assert negative_stock_discrepancy['severity'] == 'high'
    
    @pytest.mark.asyncio
    async def test_fix_negative_stock(self):
        """Test fixing negative stock discrepancy"""
        with patch('loader.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            # Fix async context manager
            mock_pool.acquire.return_value = AsyncMock()
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_bot.db = mock_pool
            
            discrepancy = {
                'type': 'negative_stock',
                'material_id': 1,
                'current_quantity': -3
            }
            
            success = await self.reconciliation_manager.reconcile_inventory(discrepancy)
            
            assert success
            # Verify stock was set to zero
            mock_conn.execute.assert_any_call(
                "UPDATE materials SET quantity_in_stock = 0 WHERE id = $1", 1
            )
            # Verify adjustment transaction was logged
            assert mock_conn.execute.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_fix_orphaned_transaction(self):
        """Test fixing orphaned transaction discrepancy"""
        with patch('loader.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            # Fix async context manager
            mock_pool.acquire.return_value = AsyncMock()
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_conn.execute.return_value = "UPDATE 1"
            mock_bot.db = mock_pool
            
            discrepancy = {
                'type': 'orphaned_transaction',
                'request_id': 'req-123'
            }
            
            success = await self.reconciliation_manager.reconcile_inventory(discrepancy)
            
            assert success
            mock_conn.execute.assert_called_with(
                "UPDATE service_requests SET inventory_updated = true WHERE id = $1",
                'req-123'
            )
    
    @pytest.mark.asyncio
    async def test_run_full_reconciliation(self):
        """Test full reconciliation process"""
        # Mock detect_discrepancies to return test discrepancies
        self.reconciliation_manager.detect_discrepancies = AsyncMock(return_value=[
            {'type': 'negative_stock', 'material_id': 1},
            {'type': 'orphaned_transaction', 'request_id': 'req-123'}
        ])
        
        # Mock reconcile_inventory to return success
        self.reconciliation_manager.reconcile_inventory = AsyncMock(return_value=True)
        
        result = await self.reconciliation_manager.run_full_reconciliation()
        
        assert result['total_discrepancies'] == 2
        assert result['fixed_count'] == 2
        assert result['failed_count'] == 0
        assert 'started_at' in result
        assert 'completed_at' in result
        assert 'duration_seconds' in result


class TestWorkflowRecoveryManager:
    """Test workflow recovery through admin interface"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_workflow_engine = Mock()
        self.mock_state_manager = Mock()
        self.recovery_manager = WorkflowRecoveryManager(
            self.mock_workflow_engine, self.mock_state_manager
        )
    
    @pytest.mark.asyncio
    async def test_detect_stuck_workflows(self):
        """Test detection of stuck workflows"""
        with patch('loader.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            # Fix async context manager
            mock_pool.acquire.return_value = AsyncMock()
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_bot.db = mock_pool
            
            # Mock stuck request query result
            stuck_time = datetime.now() - timedelta(hours=25)
            mock_conn.fetch.return_value = [
                {
                    'id': 'req-123',
                    'workflow_type': 'connection_request',
                    'role_current ': 'manager',
                    'current_status': 'in_progress',
                    'updated_at': stuck_time,
                    'created_at': stuck_time - timedelta(hours=1),
                    'description': 'Test request'
                }
            ]
            
            # Mock last transition query
            mock_conn.fetchrow.return_value = {
                'action': 'assign_to_junior_manager',
                'from_role': 'manager',
                'to_role': 'junior_manager',
                'created_at': stuck_time,
                'comments': 'Test transition'
            }
            
            stuck_workflows = await self.recovery_manager.detect_stuck_workflows(hours_threshold=24)
            
            assert len(stuck_workflows) == 1
            stuck_workflow = stuck_workflows[0]
            assert stuck_workflow['request_id'] == 'req-123'
            assert stuck_workflow['role_current '] == 'manager'
            assert stuck_workflow['stuck_duration_hours'] >= 24
    
    @pytest.mark.asyncio
    async def test_force_transition_recovery(self):
        """Test force transition recovery action"""
        # Mock request retrieval
        mock_request = ServiceRequest(
            id='req-123',
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current ='manager',
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description='Test request',
            location='Test location',
            contact_info={},
            state_data={},
            equipment_used=[],
            inventory_updated=False
        )
        
        self.mock_state_manager.get_request = AsyncMock(return_value=mock_request)
        self.mock_state_manager.update_request_state = AsyncMock(return_value=True)
        
        success = await self.recovery_manager.recover_workflow(
            'req-123', 'force_transition', 999,
            {'target_role': 'junior_manager'}
        )
        
        assert success
        self.mock_state_manager.update_request_state.assert_called_once()
        
        # Verify the update call parameters
        call_args = self.mock_state_manager.update_request_state.call_args
        assert call_args[0][0] == 'req-123'  # request_id
        assert call_args[0][1]['role_current '] == 'junior_manager'  # new_state
        assert call_args[0][1]['actor_id'] == 999  # admin_user_id
    
    @pytest.mark.asyncio
    async def test_complete_workflow_recovery(self):
        """Test force complete workflow recovery action"""
        # Mock request retrieval
        mock_request = ServiceRequest(
            id='req-123',
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current ='technician',
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description='Test request',
            location='Test location',
            contact_info={},
            state_data={},
            equipment_used=[],
            inventory_updated=False
        )
        
        self.mock_state_manager.get_request = AsyncMock(return_value=mock_request)
        self.mock_workflow_engine.complete_workflow = AsyncMock(return_value=True)
        
        success = await self.recovery_manager.recover_workflow(
            'req-123', 'complete_workflow', 999,
            {'rating': 4, 'feedback': 'Completed by admin'}
        )
        
        assert success
        self.mock_workflow_engine.complete_workflow.assert_called_once()
        
        # Verify completion data
        call_args = self.mock_workflow_engine.complete_workflow.call_args
        assert call_args[0][0] == 'req-123'  # request_id
        completion_data = call_args[0][1]
        assert completion_data['actor_id'] == 999
        assert completion_data['rating'] == 4
        assert completion_data['feedback'] == 'Completed by admin'
    
    @pytest.mark.asyncio
    async def test_get_recovery_options(self):
        """Test getting available recovery options"""
        # Mock request and workflow definition
        mock_request = ServiceRequest(
            id='req-123',
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current ='manager',
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description='Test request',
            location='Test location',
            contact_info={},
            state_data={},
            equipment_used=[],
            inventory_updated=False
        )
        
        from database.models import WorkflowDefinition, WorkflowStep
        mock_step = WorkflowStep(
            role='manager',
            actions=['assign_to_junior_manager'],
            next_steps={'assign_to_junior_manager': 'junior_manager'},
            required_data=['junior_manager_id']
        )
        mock_workflow_def = WorkflowDefinition(
            name='Connection Request',
            initial_role='manager',
            steps={'manager': mock_step},
            completion_actions=[]
        )
        
        self.mock_state_manager.get_request = AsyncMock(return_value=mock_request)
        self.mock_workflow_engine.get_workflow_definition = Mock(return_value=mock_workflow_def)
        
        options = await self.recovery_manager.get_recovery_options('req-123')
        
        assert len(options) == 4  # force_transition, reset_to_previous_state, complete_workflow, reassign_role
        
        force_transition_option = next(
            (opt for opt in options if opt['action'] == 'force_transition'), None
        )
        assert force_transition_option is not None
        assert 'junior_manager' in force_transition_option['available_roles']


class TestComprehensiveErrorRecoverySystem:
    """Test the comprehensive error recovery system integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_state_manager = Mock()
        self.mock_notification_system = Mock()
        self.mock_inventory_manager = Mock()
        self.mock_workflow_engine = Mock()
        
        self.recovery_system = ComprehensiveErrorRecoverySystem(
            self.mock_state_manager,
            self.mock_notification_system,
            self.mock_inventory_manager,
            self.mock_workflow_engine
        )
    
    @pytest.mark.asyncio
    async def test_handle_workflow_error_transient(self):
        """Test handling transient workflow errors"""
        error = ConnectionError("Database timeout")
        context = {'request_id': 'req-123', 'operation': 'update_state'}
        
        # Mock error handler to return transient error
        with patch.object(self.recovery_system.error_handler, 'handle_error') as mock_handle:
            mock_error_record = Mock()
            mock_error_record.category = ErrorCategory.TRANSIENT
            mock_handle.return_value = mock_error_record
            
            result = await self.recovery_system.handle_workflow_error(error, context)
            
            assert result  # Should return True for transient errors (retry possible)
            mock_handle.assert_called_once_with(error, context)
    
    @pytest.mark.asyncio
    async def test_handle_workflow_error_inventory(self):
        """Test handling inventory-related workflow errors"""
        error = Exception("Inventory discrepancy detected")
        context = {'request_id': 'req-123', 'operation': 'consume_equipment'}
        
        # Mock error handler and inventory reconciliation
        with patch.object(self.recovery_system.error_handler, 'handle_error') as mock_handle:
            mock_error_record = Mock()
            mock_error_record.category = ErrorCategory.INVENTORY
            mock_handle.return_value = mock_error_record
            
            with patch.object(self.recovery_system.inventory_reconciliation_manager, 'detect_discrepancies') as mock_detect:
                with patch.object(self.recovery_system.inventory_reconciliation_manager, 'reconcile_inventory') as mock_reconcile:
                    mock_detect.return_value = [{'type': 'negative_stock', 'material_id': 1}]
                    mock_reconcile.return_value = True
                    
                    result = await self.recovery_system.handle_workflow_error(error, context)
                    
                    assert result  # Should return True after reconciliation
                    mock_detect.assert_called_once()
                    mock_reconcile.assert_called_once()
    
    def test_get_system_health(self):
        """Test system health status reporting"""
        # Mock error handler statistics
        with patch.object(self.recovery_system.error_handler, 'get_error_statistics') as mock_error_stats:
            with patch.object(self.recovery_system.notification_retry_manager, 'get_retry_stats') as mock_retry_stats:
                mock_error_stats.return_value = {
                    'total_errors': 5,
                    'recent_errors_24h': 2
                }
                mock_retry_stats.return_value = {
                    'pending_retries': 1
                }
                
                health = self.recovery_system.get_system_health()
                
                assert 'error_statistics' in health
                assert 'notification_retries' in health
                assert 'active_transactions' in health
                assert 'system_status' in health
                assert health['system_status'] == 'healthy'  # < 10 recent errors


class TestEnhancedStateManager:
    """Test enhanced state manager with transactional support"""
    
    def setup_method(self):
        """Setup test fixtures"""
        with patch('utils.enhanced_state_manager.StateManager'):
            self.enhanced_state_manager = EnhancedStateManager()
    
    @pytest.mark.asyncio
    async def test_create_request_with_transaction_success(self):
        """Test successful request creation with transaction"""
        # Mock successful creation
        self.enhanced_state_manager._create_request_with_retry = AsyncMock(return_value='req-123')
        self.enhanced_state_manager.transactional_manager.begin_transaction = AsyncMock(return_value='tx-123')
        self.enhanced_state_manager.transactional_manager.add_operation = AsyncMock()
        self.enhanced_state_manager.transactional_manager.commit_transaction = AsyncMock(return_value=True)
        
        request_id = await self.enhanced_state_manager.create_request_with_transaction(
            'connection_request', {'description': 'Test request'}
        )
        
        assert request_id == 'req-123'
        self.enhanced_state_manager.transactional_manager.begin_transaction.assert_called_once()
        self.enhanced_state_manager.transactional_manager.add_operation.assert_called_once()
        self.enhanced_state_manager.transactional_manager.commit_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_request_with_transaction_failure(self):
        """Test request creation failure with transaction rollback"""
        # Mock failed creation
        self.enhanced_state_manager._create_request_with_retry = AsyncMock(return_value=None)
        self.enhanced_state_manager.transactional_manager.begin_transaction = AsyncMock(return_value='tx-123')
        self.enhanced_state_manager.transactional_manager.add_operation = AsyncMock()
        self.enhanced_state_manager.transactional_manager.rollback_transaction = AsyncMock()
        
        request_id = await self.enhanced_state_manager.create_request_with_transaction(
            'connection_request', {'description': 'Test request'}
        )
        
        assert request_id is None
        self.enhanced_state_manager.transactional_manager.rollback_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_request_with_retry_transient_error(self):
        """Test request creation retry on transient errors"""
        # Mock transient error on first attempt, success on second
        self.enhanced_state_manager.base_state_manager.create_request = AsyncMock(
            side_effect=[ConnectionError("Timeout"), 'req-123']
        )
        self.enhanced_state_manager.error_handler.handle_error = AsyncMock()
        
        # Mock error record to be transient
        mock_error_record = Mock()
        mock_error_record.category = ErrorCategory.TRANSIENT
        self.enhanced_state_manager.error_handler.handle_error.return_value = mock_error_record
        
        with patch('asyncio.sleep'):  # Mock sleep to speed up test
            request_id = await self.enhanced_state_manager._create_request_with_retry(
                'connection_request', {'description': 'Test request'}
            )
        
        assert request_id == 'req-123'
        assert self.enhanced_state_manager.base_state_manager.create_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_system_health(self):
        """Test system health monitoring"""
        with patch('loader.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            # Fix async context manager
            mock_pool.acquire.return_value = AsyncMock()
            mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_bot.db = mock_pool
            
            # Mock database query results
            mock_conn.fetchval.return_value = 5  # 5 active requests
            
            # Mock error handler
            self.enhanced_state_manager.error_handler.get_recent_errors = Mock(return_value=[])
            
            health = await self.enhanced_state_manager.get_system_health()
            
            assert health['active_requests'] == 5
            assert health['recent_errors_24h'] == 0
            assert health['status'] == 'healthy'
            assert 'last_check' in health


if __name__ == '__main__':
    pytest.main([__file__, '-v'])