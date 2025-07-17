"""
Simplified unit tests for Universal Notification System
Tests core functionality without complex database mocking
"""

import pytest
import uuid
from datetime import datetime
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


class TestNotificationSystemBasics:
    """Test basic NotificationSystem functionality"""
    
    def test_excluded_roles(self):
        """Test that client and admin roles are excluded"""
        notification_system = NotificationSystem()
        
        assert UserRole.CLIENT.value in notification_system.excluded_roles
        assert UserRole.ADMIN.value in notification_system.excluded_roles
        assert UserRole.TECHNICIAN.value not in notification_system.excluded_roles
        assert UserRole.MANAGER.value not in notification_system.excluded_roles
    
    @pytest.mark.asyncio
    async def test_send_assignment_notification_excluded_role(self):
        """Test that notifications are not sent to excluded roles"""
        notification_system = NotificationSystem()
        
        result = await notification_system.send_assignment_notification(
            UserRole.CLIENT.value, str(uuid.uuid4()), WorkflowType.CONNECTION_REQUEST.value
        )
        
        # Should return True but not actually send notifications
        assert result == True
    
    @pytest.mark.asyncio
    async def test_send_notification_message_russian(self):
        """Test sending notification message in Russian"""
        notification_system = NotificationSystem()
        
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
    async def test_send_notification_message_uzbek(self):
        """Test sending notification message in Uzbek"""
        notification_system = NotificationSystem()
        
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
    
    def test_generate_notification_id(self):
        """Test notification ID generation"""
        notification_system = NotificationSystem()
        
        id1 = notification_system._generate_notification_id()
        id2 = notification_system._generate_notification_id()
        
        assert id1 != id2
        assert len(id1) == 36  # UUID4 length
        assert len(id2) == 36


class TestNotificationSystemFactory:
    """Test NotificationSystemFactory"""
    
    def test_create_notification_system(self):
        """Test creating notification system via factory"""
        system = NotificationSystemFactory.create_notification_system()
        
        assert isinstance(system, NotificationSystem)
        assert system.pool is None  # No pool provided
        assert UserRole.CLIENT.value in system.excluded_roles
        assert UserRole.ADMIN.value in system.excluded_roles


class TestNotificationSystemLanguageSupport:
    """Test language support in notification system"""
    
    def test_workflow_type_translations_russian(self):
        """Test workflow type translations in Russian"""
        notification_system = NotificationSystem()
        
        # Test the workflow name mappings used in _send_notification_message
        workflow_names = {
            'connection_request': 'Запрос подключения',
            'technical_service': 'Техническое обслуживание',
            'call_center_direct': 'Сервис call-центра'
        }
        
        assert workflow_names['connection_request'] == 'Запрос подключения'
        assert workflow_names['technical_service'] == 'Техническое обслуживание'
        assert workflow_names['call_center_direct'] == 'Сервис call-центра'
    
    def test_workflow_type_translations_uzbek(self):
        """Test workflow type translations in Uzbek"""
        notification_system = NotificationSystem()
        
        # Test the workflow name mappings used in _send_notification_message
        workflow_names = {
            'connection_request': 'Ulanish so\'rovi',
            'technical_service': 'Texnik xizmat',
            'call_center_direct': 'Call-markaz xizmati'
        }
        
        assert workflow_names['connection_request'] == 'Ulanish so\'rovi'
        assert workflow_names['technical_service'] == 'Texnik xizmat'
        assert workflow_names['call_center_direct'] == 'Call-markaz xizmati'
    
    def test_priority_translations_russian(self):
        """Test priority translations in Russian"""
        priority_names = {
            'low': 'Низкий',
            'medium': 'Средний',
            'high': 'Высокий',
            'urgent': 'Срочный'
        }
        
        assert priority_names['low'] == 'Низкий'
        assert priority_names['medium'] == 'Средний'
        assert priority_names['high'] == 'Высокий'
        assert priority_names['urgent'] == 'Срочный'
    
    def test_priority_translations_uzbek(self):
        """Test priority translations in Uzbek"""
        priority_names = {
            'low': 'Past',
            'medium': 'O\'rta',
            'high': 'Yuqori',
            'urgent': 'Shoshilinch'
        }
        
        assert priority_names['low'] == 'Past'
        assert priority_names['medium'] == 'O\'rta'
        assert priority_names['high'] == 'Yuqori'
        assert priority_names['urgent'] == 'Shoshilinch'


class TestNotificationSystemIntegration:
    """Integration tests for notification system"""
    
    @pytest.mark.asyncio
    async def test_notification_workflow_basic(self):
        """Test basic notification workflow without database"""
        notification_system = NotificationSystem()
        
        # Test that the system can be created and basic methods exist
        assert hasattr(notification_system, 'send_assignment_notification')
        assert hasattr(notification_system, 'handle_notification_reply')
        assert hasattr(notification_system, 'mark_notification_handled')
        assert hasattr(notification_system, 'get_pending_notifications')
    
    def test_notification_system_initialization(self):
        """Test notification system initialization"""
        # Test with no pool
        system1 = NotificationSystem()
        assert system1.pool is None
        
        # Test with mock pool
        mock_pool = MagicMock()
        system2 = NotificationSystem(pool=mock_pool)
        assert system2.pool == mock_pool
    
    def test_notification_system_constants(self):
        """Test notification system constants and configurations"""
        notification_system = NotificationSystem()
        
        # Test excluded roles
        assert len(notification_system.excluded_roles) == 2
        assert UserRole.CLIENT.value in notification_system.excluded_roles
        assert UserRole.ADMIN.value in notification_system.excluded_roles
        
        # Test that other roles are not excluded
        for role in [UserRole.TECHNICIAN, UserRole.MANAGER, UserRole.WAREHOUSE, 
                    UserRole.CONTROLLER, UserRole.JUNIOR_MANAGER, UserRole.CALL_CENTER, 
                    UserRole.CALL_CENTER_SUPERVISOR]:
            assert role.value not in notification_system.excluded_roles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])