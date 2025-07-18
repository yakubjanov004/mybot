"""
Unit tests for InboxService and ApplicationTransferService.

Tests cover:
- Role-based application retrieval with filtering and pagination
- Application transfer functionality with validation
- Inbox message management
- Error handling and edge cases
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import the classes we're testing
from utils.inbox_service import InboxService, ApplicationTransferService, InboxMessage, ApplicationTransfer


class TestInboxService:
    """Test cases for InboxService class"""
    
    @pytest.fixture
    def mock_pool(self):
        """Create a mock database pool"""
        pool = MagicMock()
        conn = AsyncMock()
        
        # Create a proper async context manager mock
        class MockAsyncContextManager:
            def __init__(self, conn):
                self.conn = conn
            
            async def __aenter__(self):
                return self.conn
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        pool.acquire.return_value = MockAsyncContextManager(conn)
        
        return pool, conn
    
    @pytest.fixture
    def inbox_service(self, mock_pool):
        """Create InboxService instance with mock pool"""
        pool, _ = mock_pool
        return InboxService(pool)
    
    def test_init_with_pool(self, mock_pool):
        """Test InboxService initialization with pool"""
        pool, _ = mock_pool
        service = InboxService(pool)
        assert service.pool == pool
    
    def test_init_without_pool(self):
        """Test InboxService initialization without pool"""
        service = InboxService()
        assert service.pool is None
    
    def test_valid_roles(self):
        """Test that valid roles are properly defined"""
        expected_roles = [
            'manager', 'junior_manager', 'technician', 'warehouse',
            'call_center', 'call_center_supervisor', 'controller'
        ]
        assert InboxService.VALID_ROLES == expected_roles
    
    def test_valid_application_types(self):
        """Test that valid application types are properly defined"""
        expected_types = ['zayavka', 'service_request']
        assert InboxService.VALID_APPLICATION_TYPES == expected_types
    
    @pytest.mark.asyncio
    async def test_get_role_applications_basic(self, inbox_service, mock_pool):
        """Test basic role application retrieval"""
        pool, conn = mock_pool
        
        # Mock database responses - create proper row objects
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            'application_id': '123',
            'application_type': 'zayavka',
            'assigned_role': 'manager',
            'priority': 'medium',
            'is_read': False,
            'inbox_created_at': datetime.now(),
            'inbox_updated_at': datetime.now(),
            'application_details': {
                'id': 123,
                'description': 'Test application',
                'status': 'new',
                'client_name': 'Test Client'
            }
        }[key]
        
        # Mock dict() conversion
        def mock_dict(row):
            return {
                'application_id': '123',
                'application_type': 'zayavka',
                'assigned_role': 'manager',
                'priority': 'medium',
                'is_read': False,
                'inbox_created_at': datetime.now(),
                'inbox_updated_at': datetime.now(),
                'application_details': {
                    'id': 123,
                    'description': 'Test application',
                    'status': 'new',
                    'client_name': 'Test Client'
                }
            }
        
        with patch('builtins.dict', side_effect=mock_dict):
            conn.fetch.return_value = [mock_row]
            conn.fetchval.return_value = 1  # Total count
            
            result = await inbox_service.get_role_applications('manager', 1)
            
            assert result['pagination']['total_count'] == 1
            assert len(result['applications']) == 1
            assert result['applications'][0]['application_id'] == '123'
            assert result['filters']['role'] == 'manager'
    
    @pytest.mark.asyncio
    async def test_get_role_applications_with_filters(self, inbox_service, mock_pool):
        """Test role application retrieval with filters"""
        pool, conn = mock_pool
        
        conn.fetch.return_value = []
        conn.fetchval.return_value = 0
        
        result = await inbox_service.get_role_applications(
            role='manager',
            user_id=1,
            application_type='zayavka',
            priority='high',
            include_read=False
        )
        
        assert result['filters']['application_type'] == 'zayavka'
        assert result['filters']['priority'] == 'high'
        assert result['filters']['include_read'] == False
    
    @pytest.mark.asyncio
    async def test_get_role_applications_pagination(self, inbox_service, mock_pool):
        """Test pagination in role application retrieval"""
        pool, conn = mock_pool
        
        conn.fetch.return_value = []
        conn.fetchval.return_value = 25  # Total count
        
        result = await inbox_service.get_role_applications(
            role='manager',
            user_id=1,
            page=2,
            page_size=10
        )
        
        pagination = result['pagination']
        assert pagination['current_page'] == 2
        assert pagination['page_size'] == 10
        assert pagination['total_count'] == 25
        assert pagination['total_pages'] == 3
        assert pagination['has_next'] == True
        assert pagination['has_prev'] == True
    
    @pytest.mark.asyncio
    async def test_get_role_applications_invalid_role(self, inbox_service):
        """Test error handling for invalid role"""
        with pytest.raises(ValueError, match="Invalid role"):
            await inbox_service.get_role_applications('invalid_role', 1)
    
    @pytest.mark.asyncio
    async def test_get_role_applications_invalid_application_type(self, inbox_service):
        """Test error handling for invalid application type"""
        with pytest.raises(ValueError, match="Invalid application_type"):
            await inbox_service.get_role_applications(
                'manager', 1, application_type='invalid_type'
            )
    
    @pytest.mark.asyncio
    async def test_get_application_details_zayavka(self, inbox_service, mock_pool):
        """Test getting application details for zayavka"""
        pool, conn = mock_pool
        
        mock_result = {
            'id': 123,
            'description': 'Test zayavka',
            'status': 'new',
            'assigned_role': 'manager',
            'client_name': 'Test Client',
            'client_phone': '+1234567890'
        }
        
        conn.fetchrow.return_value = MagicMock(**mock_result)
        
        result = await inbox_service.get_application_details('123', 'zayavka', 'manager')
        
        assert result['id'] == 123
        assert result['description'] == 'Test zayavka'
        assert result['client_name'] == 'Test Client'
    
    @pytest.mark.asyncio
    async def test_get_application_details_service_request(self, inbox_service, mock_pool):
        """Test getting application details for service_request"""
        pool, conn = mock_pool
        
        mock_result = {
            'id': 'uuid-123',
            'workflow_type': 'connection_request',
            'current_status': 'created',
            'role_current': 'manager',
            'contact_info': '{"phone": "+1234567890"}',
            'state_data': '{"step": 1}',
            'equipment_used': '[]'
        }
        
        conn.fetchrow.return_value = MagicMock(**mock_result)
        
        result = await inbox_service.get_application_details('uuid-123', 'service_request', 'manager')
        
        assert result['id'] == 'uuid-123'
        assert result['workflow_type'] == 'connection_request'
        assert isinstance(result['contact_info'], dict)
        assert result['contact_info']['phone'] == '+1234567890'
    
    @pytest.mark.asyncio
    async def test_get_application_details_not_found(self, inbox_service, mock_pool):
        """Test getting application details when not found"""
        pool, conn = mock_pool
        conn.fetchrow.return_value = None
        
        result = await inbox_service.get_application_details('999', 'zayavka', 'manager')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_transfer_options(self, inbox_service):
        """Test getting valid transfer options"""
        # Test zayavka transfer options
        options = await inbox_service.get_transfer_options('manager', 'zayavka')
        expected_options = ['junior_manager', 'controller', 'call_center']
        assert set(options) == set(expected_options)
        
        # Test service_request transfer options
        options = await inbox_service.get_transfer_options('technician', 'service_request')
        expected_options = ['warehouse', 'controller', 'manager']
        assert set(options) == set(expected_options)
    
    @pytest.mark.asyncio
    async def test_get_transfer_options_invalid_role(self, inbox_service):
        """Test error handling for invalid role in transfer options"""
        with pytest.raises(ValueError, match="Invalid current_role"):
            await inbox_service.get_transfer_options('invalid_role', 'zayavka')
    
    @pytest.mark.asyncio
    async def test_create_inbox_message(self, inbox_service, mock_pool):
        """Test creating inbox message"""
        pool, conn = mock_pool
        conn.fetchval.return_value = 1  # Message ID
        
        result = await inbox_service.create_inbox_message(
            application_id='123',
            application_type='zayavka',
            assigned_role='manager',
            title='Test Message',
            description='Test Description',
            message_type='application',
            priority='high'
        )
        
        assert result == True
        conn.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_inbox_message_invalid_params(self, inbox_service):
        """Test error handling for invalid parameters in create_inbox_message"""
        with pytest.raises(ValueError, match="Invalid application_type"):
            await inbox_service.create_inbox_message(
                '123', 'invalid_type', 'manager'
            )
        
        with pytest.raises(ValueError, match="Invalid assigned_role"):
            await inbox_service.create_inbox_message(
                '123', 'zayavka', 'invalid_role'
            )
    
    @pytest.mark.asyncio
    async def test_mark_as_read(self, inbox_service, mock_pool):
        """Test marking message as read"""
        pool, conn = mock_pool
        conn.fetchval.return_value = 1  # Message ID
        
        result = await inbox_service.mark_as_read(1, 123)
        
        assert result == True
        conn.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, inbox_service, mock_pool):
        """Test marking non-existent message as read"""
        pool, conn = mock_pool
        conn.fetchval.return_value = None
        
        result = await inbox_service.mark_as_read(999, 123)
        
        assert result == False
    
    @pytest.mark.asyncio
    async def test_cleanup_old_messages(self, inbox_service, mock_pool):
        """Test cleaning up old messages"""
        pool, conn = mock_pool
        conn.execute.return_value = "DELETE 5"  # Mock result
        
        result = await inbox_service.cleanup_old_messages(30)
        
        assert result == 5
        conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, inbox_service, mock_pool):
        """Test getting unread message count"""
        pool, conn = mock_pool
        conn.fetchval.return_value = 3
        
        result = await inbox_service.get_unread_count('manager')
        
        assert result == 3
        conn.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_unread_count_invalid_role(self, inbox_service):
        """Test error handling for invalid role in unread count"""
        with pytest.raises(ValueError, match="Invalid role"):
            await inbox_service.get_unread_count('invalid_role')


class TestApplicationTransferService:
    """Test cases for ApplicationTransferService class"""
    
    @pytest.fixture
    def mock_pool(self):
        """Create a mock database pool"""
        pool = MagicMock()
        conn = AsyncMock()
        
        # Create a proper async context manager mock
        class MockAsyncContextManager:
            def __init__(self, conn):
                self.conn = conn
            
            async def __aenter__(self):
                return self.conn
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        pool.acquire.return_value = MockAsyncContextManager(conn)
        
        return pool, conn
    
    @pytest.fixture
    def transfer_service(self, mock_pool):
        """Create ApplicationTransferService instance with mock pool"""
        pool, _ = mock_pool
        return ApplicationTransferService(pool)
    
    @pytest.mark.asyncio
    async def test_validate_transfer_success(self, transfer_service, mock_pool):
        """Test successful transfer validation"""
        pool, conn = mock_pool
        
        # Mock application exists and is in correct state
        mock_result = {
            'id': 123,
            'assigned_role': 'manager',
            'status': 'new'
        }
        conn.fetchrow.return_value = MagicMock(**mock_result)
        
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'manager', 'junior_manager', 1
        )
        
        assert is_valid == True
        assert message == "Transfer validation successful"
    
    @pytest.mark.asyncio
    async def test_validate_transfer_invalid_roles(self, transfer_service):
        """Test transfer validation with invalid roles"""
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'invalid_role', 'manager', 1
        )
        
        assert is_valid == False
        assert "Invalid from_role" in message
    
    @pytest.mark.asyncio
    async def test_validate_transfer_same_role(self, transfer_service):
        """Test transfer validation with same from and to role"""
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'manager', 'manager', 1
        )
        
        assert is_valid == False
        assert "Cannot transfer to the same role" in message
    
    @pytest.mark.asyncio
    async def test_validate_transfer_invalid_target(self, transfer_service):
        """Test transfer validation with invalid target role"""
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'manager', 'warehouse', 1  # warehouse not valid target for manager
        )
        
        assert is_valid == False
        assert "Transfer from manager to warehouse is not allowed" in message
    
    @pytest.mark.asyncio
    async def test_validate_transfer_application_not_found(self, transfer_service, mock_pool):
        """Test transfer validation when application not found"""
        pool, conn = mock_pool
        conn.fetchrow.return_value = None
        
        is_valid, message = await transfer_service.validate_transfer(
            '999', 'zayavka', 'manager', 'junior_manager', 1
        )
        
        assert is_valid == False
        assert "Application 999 not found" in message
    
    @pytest.mark.asyncio
    async def test_validate_transfer_wrong_current_role(self, transfer_service, mock_pool):
        """Test transfer validation when application is assigned to different role"""
        pool, conn = mock_pool
        
        mock_result = {
            'id': 123,
            'assigned_role': 'controller',  # Different from expected 'manager'
            'status': 'new'
        }
        conn.fetchrow.return_value = MagicMock(**mock_result)
        
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'manager', 'junior_manager', 1
        )
        
        assert is_valid == False
        assert "Application is currently assigned to controller, not manager" in message
    
    @pytest.mark.asyncio
    async def test_validate_transfer_non_transferable_status(self, transfer_service, mock_pool):
        """Test transfer validation with non-transferable status"""
        pool, conn = mock_pool
        
        mock_result = {
            'id': 123,
            'assigned_role': 'manager',
            'status': 'completed'  # Non-transferable status
        }
        conn.fetchrow.return_value = MagicMock(**mock_result)
        
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'manager', 'junior_manager', 1
        )
        
        assert is_valid == False
        assert "Cannot transfer application with status: completed" in message
    
    @pytest.mark.asyncio
    async def test_execute_transfer_success(self, transfer_service, mock_pool):
        """Test successful transfer execution"""
        pool, conn = mock_pool
        
        # Mock validation success
        with patch.object(transfer_service, 'validate_transfer', return_value=(True, "Valid")):
            # Mock database operations
            conn.fetchval.side_effect = [123, 1]  # Update result, transfer ID
            conn.execute.return_value = None
            
            # Mock inbox service
            with patch.object(transfer_service.inbox_service, 'create_inbox_message', return_value=True):
                result = await transfer_service.execute_transfer(
                    '123', 'zayavka', 'manager', 'junior_manager', 1,
                    'Test transfer', 'Test notes'
                )
        
        assert result['success'] == True
        assert result['transfer_id'] == 1
        assert result['from_role'] == 'manager'
        assert result['to_role'] == 'junior_manager'
    
    @pytest.mark.asyncio
    async def test_execute_transfer_validation_failure(self, transfer_service):
        """Test transfer execution with validation failure"""
        with patch.object(transfer_service, 'validate_transfer', return_value=(False, "Invalid transfer")):
            result = await transfer_service.execute_transfer(
                '123', 'zayavka', 'manager', 'junior_manager', 1
            )
        
        assert result['success'] == False
        assert result['error'] == "Invalid transfer"
        assert result['transfer_id'] is None
    
    @pytest.mark.asyncio
    async def test_get_transfer_history(self, transfer_service, mock_pool):
        """Test getting transfer history"""
        pool, conn = mock_pool
        
        mock_transfers = [
            {
                'id': 1,
                'application_id': '123',
                'application_type': 'zayavka',
                'from_role': 'manager',
                'to_role': 'junior_manager',
                'transferred_by': 1,
                'created_at': datetime.now(),
                'transferred_by_name': 'Test User',
                'transferred_by_role': 'admin'
            }
        ]
        
        conn.fetch.return_value = [MagicMock(**transfer) for transfer in mock_transfers]
        
        result = await transfer_service.get_transfer_history('123', 'zayavka')
        
        assert len(result) == 1
        assert result[0]['from_role'] == 'manager'
        assert result[0]['to_role'] == 'junior_manager'
    
    @pytest.mark.asyncio
    async def test_rollback_transfer(self, transfer_service, mock_pool):
        """Test transfer rollback"""
        pool, conn = mock_pool
        
        # Mock transfer data
        mock_transfer = {
            'id': 1,
            'application_id': '123',
            'application_type': 'zayavka',
            'from_role': 'manager',
            'to_role': 'junior_manager',
            'transferred_by': 1
        }
        
        conn.fetchrow.return_value = MagicMock(**mock_transfer)
        
        # Mock execute_transfer for rollback
        with patch.object(transfer_service, 'execute_transfer', return_value={'success': True, 'transfer_id': 2}):
            result = await transfer_service.rollback_transfer(1, 2, 'Test rollback')
        
        assert result['success'] == True
    
    @pytest.mark.asyncio
    async def test_rollback_transfer_not_found(self, transfer_service, mock_pool):
        """Test rollback when transfer not found"""
        pool, conn = mock_pool
        conn.fetchrow.return_value = None
        
        result = await transfer_service.rollback_transfer(999, 1)
        
        assert result['success'] == False
        assert result['error'] == 'Transfer not found'
    
    @pytest.mark.asyncio
    async def test_notify_target_role(self, transfer_service):
        """Test notifying target role"""
        with patch.object(transfer_service.inbox_service, 'create_inbox_message', return_value=True):
            result = await transfer_service.notify_target_role(
                '123', 'zayavka', 'manager', 'transfer'
            )
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_get_role_transfer_stats(self, transfer_service, mock_pool):
        """Test getting role transfer statistics"""
        pool, conn = mock_pool
        
        mock_stats = {
            'total_transfers': 10,
            'transfers_out': 6,
            'transfers_in': 4,
            'unique_applications': 8,
            'unique_transferers': 3
        }
        
        conn.fetchrow.return_value = MagicMock(**mock_stats)
        
        result = await transfer_service.get_role_transfer_stats('manager', 30)
        
        assert result['total_transfers'] == 10
        assert result['transfers_out'] == 6
        assert result['transfers_in'] == 4
        assert result['role'] == 'manager'
        assert result['period_days'] == 30


class TestDataModels:
    """Test cases for data models"""
    
    def test_inbox_message_model(self):
        """Test InboxMessage data model"""
        message = InboxMessage(
            application_id='123',
            application_type='zayavka',
            assigned_role='manager',
            title='Test Message',
            priority='high'
        )
        
        assert message.application_id == '123'
        assert message.application_type == 'zayavka'
        assert message.assigned_role == 'manager'
        assert message.priority == 'high'
        assert message.is_read == False  # Default value
        
        # Test to_dict
        data = message.to_dict()
        assert data['application_id'] == '123'
        assert data['is_read'] == False
        
        # Test from_dict
        new_message = InboxMessage.from_dict(data)
        assert new_message.application_id == '123'
        assert new_message.is_read == False
    
    def test_application_transfer_model(self):
        """Test ApplicationTransfer data model"""
        transfer = ApplicationTransfer(
            application_id='123',
            application_type='zayavka',
            from_role='manager',
            to_role='junior_manager',
            transferred_by=1,
            transfer_reason='Workload balancing'
        )
        
        assert transfer.application_id == '123'
        assert transfer.from_role == 'manager'
        assert transfer.to_role == 'junior_manager'
        assert transfer.transferred_by == 1
        
        # Test to_dict
        data = transfer.to_dict()
        assert data['from_role'] == 'manager'
        assert data['transfer_reason'] == 'Workload balancing'
        
        # Test from_dict
        new_transfer = ApplicationTransfer.from_dict(data)
        assert new_transfer.from_role == 'manager'
        assert new_transfer.transfer_reason == 'Workload balancing'


if __name__ == '__main__':
    pytest.main([__file__])