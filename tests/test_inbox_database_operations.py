"""
Unit tests for inbox database operations
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from database.inbox_queries import InboxQueries
from database.inbox_models import (
    InboxMessage, ApplicationTransfer, InboxRole, ApplicationType,
    MessageType, MessagePriority
)

class TestInboxQueries:
    """Test inbox database queries"""
    
    @pytest.fixture
    def mock_connection(self):
        """Mock database connection"""
        conn = AsyncMock()
        return conn
    
    @pytest.fixture
    def sample_inbox_message(self):
        """Sample inbox message for testing"""
        return InboxMessage(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value,
            title="Test Message",
            description="Test description",
            priority=MessagePriority.HIGH.value
        )
    
    @pytest.fixture
    def sample_application_transfer(self):
        """Sample application transfer for testing"""
        return ApplicationTransfer(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            from_role=InboxRole.MANAGER.value,
            to_role=InboxRole.JUNIOR_MANAGER.value,
            transferred_by=1,
            transfer_reason="Workload distribution"
        )
    
    @pytest.mark.asyncio
    async def test_add_role_to_zayavka_success(self, mock_connection):
        """Test successfully adding role to zayavka"""
        # Mock the pool and connection
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        
        result = await InboxQueries.add_role_to_zayavka(123, InboxRole.MANAGER.value, mock_pool)
        
        assert result is True
        mock_connection.execute.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_add_role_to_zayavka_invalid_role(self, mock_get_connection, mock_connection):
        """Test adding invalid role to zayavka"""
        mock_get_connection.return_value = mock_connection
        
        result = await InboxQueries.add_role_to_zayavka(123, "invalid_role")
        
        assert result is False
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_add_role_to_service_request_success(self, mock_get_connection, mock_connection):
        """Test successfully adding role to service request"""
        mock_get_connection.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        
        result = await InboxQueries.add_role_to_service_request(
            "550e8400-e29b-41d4-a716-446655440000", 
            InboxRole.TECHNICIAN.value
        )
        
        assert result is True
        mock_connection.execute.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_role_applications_success(self, mock_get_connection, mock_connection):
        """Test getting role applications successfully"""
        mock_get_connection.return_value = mock_connection
        
        # Mock database rows
        mock_rows = [
            {
                'application_id': '123',
                'application_type': 'zayavka',
                'assigned_role': 'manager',
                'description': 'Test zayavka',
                'status': 'new',
                'priority': 'medium',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'client_name': 'Test Client',
                'client_phone': '+998901234567',
                'address': 'Test Address',
                'is_read': False,
                'message_priority': 'medium'
            },
            {
                'application_id': '550e8400-e29b-41d4-a716-446655440000',
                'application_type': 'service_request',
                'assigned_role': 'manager',
                'description': 'Test service request',
                'status': 'created',
                'priority': 'high',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'client_name': 'Test Client 2',
                'client_phone': '+998901234568',
                'address': 'Test Location',
                'is_read': True,
                'message_priority': 'high'
            }
        ]
        
        mock_connection.fetch.return_value = mock_rows
        
        applications = await InboxQueries.get_role_applications(InboxRole.MANAGER.value)
        
        assert len(applications) == 2
        assert applications[0]['application_id'] == '123'
        assert applications[0]['application_type'] == 'zayavka'
        assert applications[1]['application_id'] == '550e8400-e29b-41d4-a716-446655440000'
        assert applications[1]['application_type'] == 'service_request'
        
        mock_connection.fetch.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_role_applications_invalid_role(self, mock_get_connection, mock_connection):
        """Test getting applications with invalid role"""
        mock_get_connection.return_value = mock_connection
        
        applications = await InboxQueries.get_role_applications("invalid_role")
        
        assert applications == []
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_application_details_zayavka(self, mock_get_connection, mock_connection):
        """Test getting zayavka details"""
        mock_get_connection.return_value = mock_connection
        
        mock_row = {
            'application_id': '123',
            'application_type': 'zayavka',
            'assigned_role': 'manager',
            'description': 'Test zayavka',
            'status': 'new',
            'priority': 'medium',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'address': 'Test Address',
            'phone': '+998901234567',
            'client_name': 'Test Client',
            'client_phone': '+998901234567',
            'client_telegram_id': 123456789,
            'technician_id': None,
            'technician_name': None
        }
        
        mock_connection.fetchrow.return_value = mock_row
        
        details = await InboxQueries.get_application_details("123", ApplicationType.ZAYAVKA.value)
        
        assert details is not None
        assert details['application_id'] == '123'
        assert details['application_type'] == 'zayavka'
        assert details['client_name'] == 'Test Client'
        
        mock_connection.fetchrow.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_application_details_service_request(self, mock_get_connection, mock_connection):
        """Test getting service request details"""
        mock_get_connection.return_value = mock_connection
        
        mock_row = {
            'application_id': '550e8400-e29b-41d4-a716-446655440000',
            'application_type': 'service_request',
            'assigned_role': 'technician',
            'description': 'Test service request',
            'status': 'created',
            'priority': 'high',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'address': 'Test Location',
            'contact_info': {'phone': '+998901234567'},
            'client_name': 'Test Client',
            'client_phone': '+998901234567',
            'client_telegram_id': 123456789,
            'workflow_type': 'connection_request',
            'state_data': {}
        }
        
        mock_connection.fetchrow.return_value = mock_row
        
        details = await InboxQueries.get_application_details(
            "550e8400-e29b-41d4-a716-446655440000", 
            ApplicationType.SERVICE_REQUEST.value
        )
        
        assert details is not None
        assert details['application_id'] == '550e8400-e29b-41d4-a716-446655440000'
        assert details['application_type'] == 'service_request'
        assert details['workflow_type'] == 'connection_request'
        
        mock_connection.fetchrow.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_application_details_not_found(self, mock_get_connection, mock_connection):
        """Test getting details for non-existent application"""
        mock_get_connection.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        
        details = await InboxQueries.get_application_details("999", ApplicationType.ZAYAVKA.value)
        
        assert details is None
        mock_connection.fetchrow.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_create_inbox_message_success(self, mock_get_connection, mock_connection, sample_inbox_message):
        """Test creating inbox message successfully"""
        mock_get_connection.return_value = mock_connection
        mock_connection.fetchrow.return_value = {'id': 1}
        
        message_id = await InboxQueries.create_inbox_message(sample_inbox_message)
        
        assert message_id == 1
        mock_connection.fetchrow.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_create_inbox_message_failure(self, mock_get_connection, mock_connection, sample_inbox_message):
        """Test creating inbox message failure"""
        mock_get_connection.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        
        message_id = await InboxQueries.create_inbox_message(sample_inbox_message)
        
        assert message_id is None
        mock_connection.fetchrow.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_mark_message_as_read_success(self, mock_get_connection, mock_connection):
        """Test marking message as read successfully"""
        mock_get_connection.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 1"
        
        result = await InboxQueries.mark_message_as_read(1, 123)
        
        assert result is True
        mock_connection.execute.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_mark_message_as_read_failure(self, mock_get_connection, mock_connection):
        """Test marking message as read failure"""
        mock_get_connection.return_value = mock_connection
        mock_connection.execute.return_value = "UPDATE 0"
        
        result = await InboxQueries.mark_message_as_read(999, 123)
        
        assert result is False
        mock_connection.execute.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_transfer_application_zayavka_success(self, mock_get_connection, mock_connection):
        """Test transferring zayavka successfully"""
        mock_get_connection.return_value = mock_connection
        
        # Mock transaction context
        mock_transaction = AsyncMock()
        mock_connection.transaction.return_value = mock_transaction
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        
        # Mock successful updates
        mock_connection.execute.side_effect = ["UPDATE 1", None, None, None]
        
        result = await InboxQueries.transfer_application(
            "123",
            ApplicationType.ZAYAVKA.value,
            InboxRole.MANAGER.value,
            InboxRole.JUNIOR_MANAGER.value,
            1,
            "Test transfer"
        )
        
        assert result is True
        assert mock_connection.execute.call_count == 4  # Update app, insert audit, update messages, insert notification
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_transfer_application_service_request_success(self, mock_get_connection, mock_connection):
        """Test transferring service request successfully"""
        mock_get_connection.return_value = mock_connection
        
        # Mock transaction context
        mock_transaction = AsyncMock()
        mock_connection.transaction.return_value = mock_transaction
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        
        # Mock successful updates
        mock_connection.execute.side_effect = ["UPDATE 1", None, None, None]
        
        result = await InboxQueries.transfer_application(
            "550e8400-e29b-41d4-a716-446655440000",
            ApplicationType.SERVICE_REQUEST.value,
            InboxRole.CONTROLLER.value,
            InboxRole.TECHNICIAN.value,
            2,
            "Technical assignment"
        )
        
        assert result is True
        assert mock_connection.execute.call_count == 4
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_transfer_application_invalid_type(self, mock_get_connection, mock_connection):
        """Test transferring application with invalid type"""
        mock_get_connection.return_value = mock_connection
        
        # Mock transaction context
        mock_transaction = AsyncMock()
        mock_connection.transaction.return_value = mock_transaction
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        
        result = await InboxQueries.transfer_application(
            "123",
            "invalid_type",
            InboxRole.MANAGER.value,
            InboxRole.JUNIOR_MANAGER.value,
            1
        )
        
        assert result is False
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_transfer_history_success(self, mock_get_connection, mock_connection):
        """Test getting transfer history successfully"""
        mock_get_connection.return_value = mock_connection
        
        mock_rows = [
            {
                'id': 1,
                'application_id': '123',
                'application_type': 'zayavka',
                'from_role': 'manager',
                'to_role': 'junior_manager',
                'transferred_by': 1,
                'transferred_by_name': 'Test Manager',
                'transfer_reason': 'Workload distribution',
                'transfer_notes': 'Test notes',
                'created_at': datetime.now()
            },
            {
                'id': 2,
                'application_id': '123',
                'application_type': 'zayavka',
                'from_role': 'junior_manager',
                'to_role': 'technician',
                'transferred_by': 2,
                'transferred_by_name': 'Test Junior Manager',
                'transfer_reason': 'Technical assignment',
                'transfer_notes': None,
                'created_at': datetime.now()
            }
        ]
        
        mock_connection.fetch.return_value = mock_rows
        
        history = await InboxQueries.get_transfer_history("123", ApplicationType.ZAYAVKA.value)
        
        assert len(history) == 2
        assert history[0]['from_role'] == 'manager'
        assert history[0]['to_role'] == 'junior_manager'
        assert history[1]['from_role'] == 'junior_manager'
        assert history[1]['to_role'] == 'technician'
        
        mock_connection.fetch.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_role_statistics_success(self, mock_get_connection, mock_connection):
        """Test getting role statistics successfully"""
        mock_get_connection.return_value = mock_connection
        
        mock_row = {
            'total_applications': 15,
            'new_applications': 5,
            'unread_applications': 3,
            'total_zayavki': 10,
            'total_service_requests': 5
        }
        
        mock_connection.fetchrow.return_value = mock_row
        
        stats = await InboxQueries.get_role_statistics(InboxRole.MANAGER.value)
        
        assert stats['total_applications'] == 15
        assert stats['new_applications'] == 5
        assert stats['unread_applications'] == 3
        assert stats['total_zayavki'] == 10
        assert stats['total_service_requests'] == 5
        
        mock_connection.fetchrow.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_role_statistics_invalid_role(self, mock_get_connection, mock_connection):
        """Test getting statistics with invalid role"""
        mock_get_connection.return_value = mock_connection
        
        stats = await InboxQueries.get_role_statistics("invalid_role")
        
        assert stats['total_applications'] == 0
        assert stats['new_applications'] == 0
        assert stats['unread_applications'] == 0
        assert stats['total_zayavki'] == 0
        assert stats['total_service_requests'] == 0
        
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_get_role_statistics_no_data(self, mock_get_connection, mock_connection):
        """Test getting statistics when no data exists"""
        mock_get_connection.return_value = mock_connection
        mock_connection.fetchrow.return_value = None
        
        stats = await InboxQueries.get_role_statistics(InboxRole.MANAGER.value)
        
        assert stats['total_applications'] == 0
        assert stats['new_applications'] == 0
        assert stats['unread_applications'] == 0
        assert stats['total_zayavki'] == 0
        assert stats['total_service_requests'] == 0
        
        mock_connection.fetchrow.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_cleanup_old_messages_success(self, mock_get_connection, mock_connection):
        """Test cleaning up old messages successfully"""
        mock_get_connection.return_value = mock_connection
        mock_connection.execute.return_value = "DELETE 5"
        
        deleted_count = await InboxQueries.cleanup_old_messages(30)
        
        assert deleted_count == 5
        mock_connection.execute.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_cleanup_old_messages_no_deletions(self, mock_get_connection, mock_connection):
        """Test cleaning up old messages with no deletions"""
        mock_get_connection.return_value = mock_connection
        mock_connection.execute.return_value = "DELETE 0"
        
        deleted_count = await InboxQueries.cleanup_old_messages(30)
        
        assert deleted_count == 0
        mock_connection.execute.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('database.inbox_queries.get_connection')
    async def test_database_connection_error_handling(self, mock_get_connection):
        """Test database connection error handling"""
        mock_get_connection.side_effect = Exception("Connection failed")
        
        # Test various methods handle connection errors gracefully
        result = await InboxQueries.add_role_to_zayavka(123, InboxRole.MANAGER.value)
        assert result is False
        
        applications = await InboxQueries.get_role_applications(InboxRole.MANAGER.value)
        assert applications == []
        
        details = await InboxQueries.get_application_details("123", ApplicationType.ZAYAVKA.value)
        assert details is None
        
        stats = await InboxQueries.get_role_statistics(InboxRole.MANAGER.value)
        assert stats['total_applications'] == 0