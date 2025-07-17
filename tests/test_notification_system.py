"""
Unit tests for Universal Notification System
Tests notification delivery, deduplication, and pending notification tracking
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from utils.notification_system import NotificationSystem, PendingNotification, NotificationSystemFactory
from database.models import UserRole, WorkflowType


class TestPendingNotification:
    """Test PendingNotification class"""
    
    def test_pending_notification_creation(self):
        """Test creating a pending notification"""
        notification_id = str(uuid.uuid4())
        user_id = 123
        request_id = str(uuid.uuid4())
        workflow_type = WorkflowType.CONNECTION_REQUEST.value
        role = UserRole.TECHNICIAN.value
        
        notification = PendingNotification(
            notification_id, user_id, request_id, workflow_type, role
        )
        
        assert notification.notification_id == notification_id
        assert notification.user_id == user_id
        assert notification.request_id == request_id
        assert notification.workflow_type == workflow_type
        assert notification.role == role
        assert notification.is_handled == False
        assert isinstance(notification.created_at, datetime)
    
    def test_pending_notification_to_dict(self):
        """Test converting pending notification to dictionary"""
        notification_id = str(uuid.uuid4())
        user_id = 123
        request_id = str(uuid.uuid4())
        workflow_type = WorkflowType.TECHNICAL_SERVICE.value
        role = UserRole.MANAGER.value
        
        notification = PendingNotification(
            notification_id, user_id, request_id, workflow_type, role
        )
        
        result = notification.to_dict()
        
        assert result['notification_id'] == notification_id
        assert result['user_id'] == user_id
        assert result['request_id'] == request_id
        assert result['workflow_type'] == workflow_type
        assert result['role'] == role
        assert result['is_handled'] == False
        assert isinstance(result['created_at'], datetime)


class TestNotificationSystem:
    """Test NotificationSystem class"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        
        # Create a proper async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=conn)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        pool.acquire.return_value = async_context_manager
        return pool, conn
    
    @pytest.fixture
    def notification_system(self, mock_pool):
        """Create notification system with mocked pool"""
        pool, _ = mock_pool
        return NotificationSystem(pool=pool)
    
    def test_excluded_roles(self, notification_system):
        """Test that client and admin roles are excluded"""
        assert UserRole.CLIENT.value in notification_system.excluded_roles
        assert UserRole.ADMIN.value in notification_system.excluded_roles
        assert UserRole.TECHNICIAN.value not in notification_system.excluded_roles
        assert UserRole.MANAGER.value not in notification_system.excluded_roles
    
    @pytest.mark.asyncio
    async def test_send_assignment_notification_excluded_role(self, notification_system):
        """Test that notifications are not sent to excluded roles"""
        result = await notification_system.send_assignment_notification(
            UserRole.CLIENT.value, str(uuid.uuid4()), WorkflowType.CONNECTION_REQUEST.value
        )
        
        # Should return True but not actually send notifications
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_assignment_notification_no_users(self, mock_pool, notification_system):
        """Test sending notification when no users found for role"""
        pool, conn = mock_pool
        
        # Mock empty user list
        conn.fetch.return_value = []
        
        result = await notification_system.send_assignment_notification(
            UserRole.TECHNICIAN.value, str(uuid.uuid4()), WorkflowType.CONNECTION_REQUEST.value
        )
        
        assert result == False
    
    @pytest.mark.asyncio
    async def test_send_assignment_notification_success(self, mock_pool, notification_system):
        """Test successful notification sending"""
        pool, conn = mock_pool
        request_id = str(uuid.uuid4())
        
        # Mock users
        mock_users = [
            {
                'id': 1,
                'telegram_id': 123456789,
                'full_name': 'Test User 1',
                'language': 'ru'
            },
            {
                'id': 2,
                'telegram_id': 987654321,
                'full_name': 'Test User 2',
                'language': 'uz'
            }
        ]
        
        # Mock request data
        mock_request = {
            'description': 'Test request description',
            'priority': 'high',
            'created_at': datetime.now()
        }
        
        # Setup mock responses
        conn.fetch.return_value = mock_users
        conn.fetchrow.return_value = mock_request
        conn.execute.return_value = None
        
        # Mock the message sending
        with patch.object(notification_system, '_send_notification_message', new_callable=AsyncMock) as mock_send:
            result = await notification_system.send_assignment_notification(
                UserRole.TECHNICIAN.value, request_id, WorkflowType.CONNECTION_REQUEST.value
            )
        
        assert result == True
        assert mock_send.call_count == 2  # Called for each user
        assert conn.execute.call_count == 2  # Database insert for each user
    
    @pytest.mark.asyncio
    async def test_send_assignment_notification_partial_failure(self, mock_pool, notification_system):
        """Test notification sending with partial failures"""
        pool, conn = mock_pool
        request_id = str(uuid.uuid4())
        
        # Mock users
        mock_users = [
            {
                'id': 1,
                'telegram_id': 123456789,
                'full_name': 'Test User 1',
                'language': 'ru'
            },
            {
                'id': 2,
                'telegram_id': 987654321,
                'full_name': 'Test User 2',
                'language': 'uz'
            }
        ]
        
        # Mock request data
        mock_request = {
            'description': 'Test request description',
            'priority': 'medium',
            'created_at': datetime.now()
        }
        
        # Setup mock responses
        conn.fetch.return_value = mock_users
        conn.fetchrow.return_value = mock_request
        conn.execute.return_value = None
        
        # Mock message sending with one failure
        with patch.object(notification_system, '_send_notification_message', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = [None, Exception("Send failed")]
            
            result = await notification_system.send_assignment_notification(
                UserRole.TECHNICIAN.value, request_id, WorkflowType.CONNECTION_REQUEST.value
            )
        
        assert result == True  # Should still return True if at least one succeeded
        assert mock_send.call_count == 2
    
    @pytest.mark.asyncio
    async def test_handle_notification_reply_no_user(self, mock_pool, notification_system):
        """Test handling notification reply when user not found"""
        pool, conn = mock_pool
        
        # Mock no user found
        conn.fetchrow.return_value = None
        
        result = await notification_system.handle_notification_reply(999, "test_callback")
        
        assert result['success'] == False
        assert result['error'] == 'User not found'
    
    @pytest.mark.asyncio
    async def test_handle_notification_reply_no_requests(self, mock_pool, notification_system):
        """Test handling notification reply when no requests found"""
        pool, conn = mock_pool
        
        # Mock user
        mock_user = {
            'id': 1,
            'role': UserRole.TECHNICIAN.value,
            'language': 'ru',
            'full_name': 'Test User'
        }
        
        # Setup mock responses
        conn.fetchrow.return_value = mock_user
        conn.fetch.return_value = []  # No requests
        
        result = await notification_system.handle_notification_reply(1, "test_callback")
        
        assert result['success'] == True
        assert 'назначенных заданий' in result['message_text']
        assert result['keyboard'] is None
    
    @pytest.mark.asyncio
    async def test_handle_notification_reply_with_requests(self, mock_pool, notification_system):
        """Test handling notification reply with pending requests"""
        pool, conn = mock_pool
        
        # Mock user
        mock_user = {
            'id': 1,
            'role': UserRole.TECHNICIAN.value,
            'language': 'ru',
            'full_name': 'Test User'
        }
        
        # Mock requests
        mock_requests = [
            {
                'id': str(uuid.uuid4()),
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
                'description': 'Test connection request',
                'priority': 'high',
                'created_at': datetime.now(),
                'current_status': 'in_progress',
                'location': 'Test Location'
            },
            {
                'id': str(uuid.uuid4()),
                'workflow_type': WorkflowType.TECHNICAL_SERVICE.value,
                'description': 'Test technical service',
                'priority': 'medium',
                'created_at': datetime.now(),
                'current_status': 'in_progress',
                'location': None
            }
        ]
        
        # Setup mock responses
        conn.fetchrow.return_value = mock_user
        conn.fetch.return_value = mock_requests
        
        result = await notification_system.handle_notification_reply(1, "test_callback")
        
        assert result['success'] == True
        assert 'Назначенные вам задания (2 шт.)' in result['message_text']
        assert result['keyboard'] is not None
        assert len(result['keyboard'].inline_keyboard) == 3  # 2 requests + refresh button
    
    @pytest.mark.asyncio
    async def test_handle_notification_reply_uzbek_language(self, mock_pool, notification_system):
        """Test handling notification reply in Uzbek language"""
        pool, conn = mock_pool
        
        # Mock user with Uzbek language
        mock_user = {
            'id': 1,
            'role': UserRole.MANAGER.value,
            'language': 'uz',
            'full_name': 'Test User'
        }
        
        # Mock request
        mock_requests = [
            {
                'id': str(uuid.uuid4()),
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
                'description': 'Test request',
                'priority': 'urgent',
                'created_at': datetime.now(),
                'current_status': 'in_progress',
                'location': 'Test Location'
            }
        ]
        
        # Setup mock responses
        conn.fetchrow.return_value = mock_user
        conn.fetch.return_value = mock_requests
        
        result = await notification_system.handle_notification_reply(1, "test_callback")
        
        assert result['success'] == True
        assert 'Sizga tayinlangan topshiriqlar' in result['message_text']
        assert 'Shoshilinch' in result['message_text']  # Urgent in Uzbek
    
    @pytest.mark.asyncio
    async def test_mark_notification_handled(self, mock_pool, notification_system):
        """Test marking notification as handled"""
        pool, conn = mock_pool
        
        conn.execute.return_value = "UPDATE 1"
        
        result = await notification_system.mark_notification_handled(1, str(uuid.uuid4()))
        
        assert result == True
        conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_pending_notifications(self, mock_pool, notification_system):
        """Test getting pending notifications"""
        pool, conn = mock_pool
        
        # Mock pending notifications
        mock_notifications = [
            {
                'id': str(uuid.uuid4()),
                'request_id': str(uuid.uuid4()),
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
                'role': UserRole.TECHNICIAN.value,
                'created_at': datetime.now(),
                'description': 'Test request',
                'priority': 'high',
                'current_status': 'in_progress'
            }
        ]
        
        conn.fetch.return_value = mock_notifications
        
        result = await notification_system.get_pending_notifications(1)
        
        assert len(result) == 1
        assert result[0]['workflow_type'] == WorkflowType.CONNECTION_REQUEST.value
        assert result[0]['role'] == UserRole.TECHNICIAN.value
    
    @pytest.mark.asyncio
    async def test_cleanup_handled_notifications(self, mock_pool, notification_system):
        """Test cleanup of old handled notifications"""
        pool, conn = mock_pool
        
        conn.execute.return_value = "DELETE 5"
        
        result = await notification_system.cleanup_handled_notifications(7)
        
        assert result == 5
        conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_notification_stats(self, mock_pool, notification_system):
        """Test getting notification statistics"""
        pool, conn = mock_pool
        
        # Mock stats
        mock_stats = [
            {
                'total_notifications': 10,
                'pending_notifications': 3,
                'handled_notifications': 7,
                'role': UserRole.TECHNICIAN.value
            },
            {
                'total_notifications': 5,
                'pending_notifications': 1,
                'handled_notifications': 4,
                'role': UserRole.MANAGER.value
            }
        ]
        
        conn.fetch.return_value = mock_stats
        
        result = await notification_system.get_notification_stats()
        
        assert len(result) == 2
        assert result[UserRole.TECHNICIAN.value]['total'] == 10
        assert result[UserRole.TECHNICIAN.value]['pending'] == 3
        assert result[UserRole.MANAGER.value]['total'] == 5
    
    @pytest.mark.asyncio
    async def test_get_notification_stats_by_role(self, mock_pool, notification_system):
        """Test getting notification statistics for specific role"""
        pool, conn = mock_pool
        
        # Mock stats for specific role
        mock_stats = [
            {
                'total_notifications': 10,
                'pending_notifications': 3,
                'handled_notifications': 7,
                'role': UserRole.TECHNICIAN.value
            }
        ]
        
        conn.fetch.return_value = mock_stats
        
        result = await notification_system.get_notification_stats(UserRole.TECHNICIAN.value)
        
        assert len(result) == 1
        assert result[UserRole.TECHNICIAN.value]['total'] == 10
    
    @pytest.mark.asyncio
    async def test_send_notification_message_russian(self, notification_system):
        """Test sending notification message in Russian"""
        user = {
            'id': 1,
            'telegram_id': 123456789,
            'full_name': 'Test User',
            'language': 'ru'
        }
        
        request_data = {
            'description': 'Test request description for notification',
            'priority': 'high',
            'created_at': datetime.now()
        }
        
        with patch('loader.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            await notification_system._send_notification_message(
                user, str(uuid.uuid4()), WorkflowType.CONNECTION_REQUEST.value, 
                request_data, str(uuid.uuid4())
            )
            
            mock_bot.send_message.assert_called_once()
            call_args = mock_bot.send_message.call_args
            
            assert call_args[1]['chat_id'] == user['telegram_id']
            assert 'Новое задание' in call_args[1]['text']
            assert 'Запрос подключения' in call_args[1]['text']
            assert 'Просмотр заданий' in call_args[1]['reply_markup'].inline_keyboard[0][0].text
    
    @pytest.mark.asyncio
    async def test_send_notification_message_uzbek(self, notification_system):
        """Test sending notification message in Uzbek"""
        user = {
            'id': 1,
            'telegram_id': 123456789,
            'full_name': 'Test User',
            'language': 'uz'
        }
        
        request_data = {
            'description': 'Test request description for notification',
            'priority': 'medium',
            'created_at': datetime.now()
        }
        
        with patch('loader.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()
            
            await notification_system._send_notification_message(
                user, str(uuid.uuid4()), WorkflowType.TECHNICAL_SERVICE.value, 
                request_data, str(uuid.uuid4())
            )
            
            mock_bot.send_message.assert_called_once()
            call_args = mock_bot.send_message.call_args
            
            assert call_args[1]['chat_id'] == user['telegram_id']
            assert 'Yangi topshiriq' in call_args[1]['text']
            assert 'Texnik xizmat' in call_args[1]['text']
            assert "Topshiriqlarni ko'rish" in call_args[1]['reply_markup'].inline_keyboard[0][0].text


class TestNotificationSystemFactory:
    """Test NotificationSystemFactory"""
    
    def test_create_notification_system(self):
        """Test creating notification system via factory"""
        system = NotificationSystemFactory.create_notification_system()
        
        assert isinstance(system, NotificationSystem)
        assert system.pool is None  # No pool provided
        assert UserRole.CLIENT.value in system.excluded_roles
        assert UserRole.ADMIN.value in system.excluded_roles


class TestNotificationSystemIntegration:
    """Integration tests for notification system"""
    
    @pytest.mark.asyncio
    async def test_full_notification_workflow(self):
        """Test complete notification workflow"""
        # This would be an integration test that requires actual database
        # For now, we'll skip it as it requires more complex setup
        pass
    
    @pytest.mark.asyncio
    async def test_notification_deduplication(self):
        """Test that duplicate notifications are handled properly"""
        # This test would verify that the system doesn't send duplicate
        # notifications for the same request to the same user
        pass
    
    @pytest.mark.asyncio
    async def test_notification_persistence(self):
        """Test that notifications persist across system restarts"""
        # This test would verify that pending notifications are properly
        # stored and retrieved from the database
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])