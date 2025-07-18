"""
Integration tests for InboxService and ApplicationTransferService working together.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from utils.inbox_service import InboxService, ApplicationTransferService


class TestInboxIntegration:
    """Integration tests for inbox system components"""
    
    @pytest.fixture
    def mock_pool(self):
        """Create a mock database pool"""
        pool = MagicMock()
        conn = MagicMock()
        
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
    def services(self, mock_pool):
        """Create service instances with mock pool"""
        pool, _ = mock_pool
        inbox_service = InboxService(pool)
        transfer_service = ApplicationTransferService(pool)
        return inbox_service, transfer_service
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, services):
        """Test that services initialize correctly"""
        inbox_service, transfer_service = services
        
        assert inbox_service.pool is not None
        assert transfer_service.pool is not None
        assert transfer_service.inbox_service is not None
    
    @pytest.mark.asyncio
    async def test_transfer_options_consistency(self, services):
        """Test that transfer options are consistent between services"""
        inbox_service, transfer_service = services
        
        # Test that both services use the same valid roles
        assert inbox_service.VALID_ROLES == InboxService.VALID_ROLES
        assert transfer_service.inbox_service.VALID_ROLES == InboxService.VALID_ROLES
        
        # Test transfer options for different roles
        manager_options = await inbox_service.get_transfer_options('manager', 'zayavka')
        assert 'junior_manager' in manager_options
        assert 'controller' in manager_options
        
        technician_options = await inbox_service.get_transfer_options('technician', 'service_request')
        assert 'warehouse' in technician_options
        assert 'controller' in technician_options
    
    @pytest.mark.asyncio
    async def test_validation_rules_consistency(self, services):
        """Test that validation rules are consistent"""
        inbox_service, transfer_service = services
        
        # Test invalid role validation
        with pytest.raises(ValueError, match="Invalid role"):
            await inbox_service.get_role_applications('invalid_role', 1)
        
        # Test invalid application type validation
        with pytest.raises(ValueError, match="Invalid application_type"):
            await inbox_service.get_application_details('123', 'invalid_type', 'manager')
        
        # Test transfer validation with invalid roles
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'invalid_role', 'manager', 1
        )
        assert not is_valid
        assert "Invalid from_role" in message
    
    @pytest.mark.asyncio
    async def test_message_type_validation(self, services):
        """Test message type validation across services"""
        inbox_service, transfer_service = services
        
        # Test valid message types
        valid_types = ['application', 'transfer', 'notification', 'reminder']
        for msg_type in valid_types:
            # This should not raise an exception
            try:
                await inbox_service.create_inbox_message(
                    '123', 'zayavka', 'manager', 
                    message_type=msg_type
                )
            except ValueError as e:
                if "Invalid message_type" in str(e):
                    pytest.fail(f"Valid message type {msg_type} was rejected")
                # Other errors (like database errors) are expected in tests
    
    @pytest.mark.asyncio
    async def test_priority_validation(self, services):
        """Test priority validation across services"""
        inbox_service, transfer_service = services
        
        # Test valid priorities
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        for priority in valid_priorities:
            # This should not raise an exception for priority validation
            try:
                await inbox_service.get_role_applications(
                    'manager', 1, priority=priority
                )
            except ValueError as e:
                if "Invalid priority" in str(e):
                    pytest.fail(f"Valid priority {priority} was rejected")
                # Other errors are expected in tests
    
    def test_data_model_consistency(self):
        """Test that data models are consistent"""
        from utils.inbox_service import InboxMessage, ApplicationTransfer
        
        # Test InboxMessage model
        message = InboxMessage(
            application_id='123',
            application_type='zayavka',
            assigned_role='manager'
        )
        
        # Test serialization/deserialization
        data = message.to_dict()
        restored_message = InboxMessage.from_dict(data)
        
        assert restored_message.application_id == message.application_id
        assert restored_message.application_type == message.application_type
        assert restored_message.assigned_role == message.assigned_role
        
        # Test ApplicationTransfer model
        transfer = ApplicationTransfer(
            application_id='123',
            application_type='zayavka',
            from_role='manager',
            to_role='junior_manager',
            transferred_by=1
        )
        
        # Test serialization/deserialization
        data = transfer.to_dict()
        restored_transfer = ApplicationTransfer.from_dict(data)
        
        assert restored_transfer.application_id == transfer.application_id
        assert restored_transfer.from_role == transfer.from_role
        assert restored_transfer.to_role == transfer.to_role
    
    @pytest.mark.asyncio
    async def test_workflow_integration(self, services):
        """Test that services work together in a typical workflow"""
        inbox_service, transfer_service = services
        
        # Test workflow: get applications -> validate transfer -> check options
        
        # 1. Check transfer options for manager
        options = await inbox_service.get_transfer_options('manager', 'zayavka')
        assert len(options) > 0
        assert 'junior_manager' in options
        
        # 2. Validate a transfer to one of the valid options
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'manager', 'junior_manager', 1
        )
        # Note: This will fail due to database mocking, but should pass validation checks
        # The error should be about database operations, not validation
        if not is_valid and "Invalid" in message and "database" not in message.lower():
            pytest.fail(f"Transfer validation failed unexpectedly: {message}")
        
        # 3. Test that invalid transfers are properly rejected
        is_valid, message = await transfer_service.validate_transfer(
            '123', 'zayavka', 'manager', 'warehouse', 1  # Invalid target
        )
        assert not is_valid
        assert "not allowed" in message


if __name__ == '__main__':
    pytest.main([__file__])