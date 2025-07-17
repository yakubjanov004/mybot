"""
Tests for staff-created application notification system extensions
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from utils.notification_system import NotificationSystem
from database.models import UserRole


class TestStaffNotificationSystem:
    """Test staff notification system extensions"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        
        # Create a proper async context manager mock
        context_manager = AsyncMock()
        context_manager.__aenter__ = AsyncMock(return_value=conn)
        context_manager.__aexit__ = AsyncMock(return_value=None)
        
        pool.acquire.return_value = context_manager
        
        return pool, conn
    
    @pytest.fixture
    def notification_system(self, mock_pool):
        """Create notification system with mocked pool"""
        pool, _ = mock_pool
        return NotificationSystem(pool=pool)
    
    @pytest.fixture
    def sample_request_data(self):
        """Sample request data for testing"""
        return {
            'description': 'Test connection request',
            'location': 'Test address 123',
            'contact_info': {
                'full_name': 'Test Client',
                'phone': '+998901234567'
            },
            'priority': 'medium',
            'created_by_staff': True,
            'staff_creator_info': {
                'creator_id': 1,
                'creator_role': 'manager',
                'session_id': 'test_session'
            }
        }
    
    def test_staff_notification_templates_loaded(self, notification_system):
        """Test that staff notification templates are properly loaded"""
        templates = notification_system.staff_notification_templates
        
        # Check main template categories exist
        assert 'client_notification' in templates
        assert 'staff_confirmation' in templates
        assert 'workflow_participant' in templates
        
        # Check language support
        for category in templates.values():
            assert 'uz' in category
            assert 'ru' in category
            
            # Check application types
            for lang_templates in category.values():
                assert 'connection_request' in lang_templates
                assert 'technical_service' in lang_templates
                
                # Check template structure
                for app_templates in lang_templates.values():
                    assert 'title' in app_templates
                    assert 'body' in app_templates
                    assert 'button' in app_templates
    
    def test_format_creator_role_uzbek(self, notification_system):
        """Test creator role formatting in Uzbek"""
        assert notification_system._format_creator_role('manager', 'uz') == 'Menejer'
        assert notification_system._format_creator_role('junior_manager', 'uz') == 'Kichik menejer'
        assert notification_system._format_creator_role('controller', 'uz') == 'Nazoratchi'
        assert notification_system._format_creator_role('call_center', 'uz') == 'Call-markaz operatori'
        assert notification_system._format_creator_role('unknown_role', 'uz') == 'unknown_role'
    
    def test_format_creator_role_russian(self, notification_system):
        """Test creator role formatting in Russian"""
        assert notification_system._format_creator_role('manager', 'ru') == 'Менеджер'
        assert notification_system._format_creator_role('junior_manager', 'ru') == 'Младший менеджер'
        assert notification_system._format_creator_role('controller', 'ru') == 'Контроллер'
        assert notification_system._format_creator_role('call_center', 'ru') == 'Оператор call-центра'
        assert notification_system._format_creator_role('unknown_role', 'ru') == 'unknown_role'
    
    @pytest.mark.asyncio
    async def test_send_staff_client_notification_success(self, notification_system, sample_request_data):
        """Test successful client notification for staff-created application"""
        # Mock the _get_pool method to return a working mock
        with patch.object(notification_system, '_get_pool') as mock_get_pool:
            # Create proper async context manager mock
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            
            # Mock client data
            client_data = {
                'id': 1,
                'telegram_id': 123456789,
                'full_name': 'Test Client',
                'language': 'uz'
            }
            mock_conn.fetchrow.return_value = client_data
            mock_conn.execute.return_value = None
            
            # Setup async context manager
            async def mock_acquire():
                return mock_conn
            
            mock_pool.acquire = mock_acquire
            mock_get_pool.return_value = mock_pool
            
            with patch('loader.bot') as mock_bot:
                mock_bot.send_message = AsyncMock()
                
                result = await notification_system.send_staff_client_notification(
                    client_id=1,
                    request_id='test_request_123',
                    workflow_type='connection_request',
                    creator_role='manager',
                    request_data=sample_request_data
                )
                
                assert result is True
                
                # Verify message sent
                mock_bot.send_message.assert_called_once()
                call_args = mock_bot.send_message.call_args
                
                assert call_args[1]['chat_id'] == 123456789
                assert 'Sizning nomingizdan ariza yaratildi' in call_args[1]['text']
                assert call_args[1]['reply_markup'] is not None
    
    @pytest.mark.asyncio
    async def test_send_staff_client_notification_client_not_found(self, notification_system, mock_pool):
        """Test client notification when client not found"""
        pool, conn = mock_pool
        conn.fetchrow.return_value = None
        
        result = await notification_system.send_staff_client_notification(
            client_id=999,
            request_id='test_request_123',
            workflow_type='connection_request',
            creator_role='manager',
            request_data={}
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_staff_confirmation_notification_success(self, notification_system, sample_request_data):
        """Test successful staff confirmation notification"""
        # Mock the _get_pool method to return a working mock
        with patch.object(notification_system, '_get_pool') as mock_get_pool:
            # Create proper async context manager mock
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            
            # Mock staff data
            staff_data = {
                'id': 1,
                'telegram_id': 987654321,
                'full_name': 'Test Manager',
                'language': 'ru',
                'role': 'manager'
            }
            mock_conn.fetchrow.return_value = staff_data
            
            # Setup async context manager
            async def mock_acquire():
                return mock_conn
            
            mock_pool.acquire = mock_acquire
            mock_get_pool.return_value = mock_pool
            
            with patch('loader.bot') as mock_bot:
                mock_bot.send_message = AsyncMock()
                
                result = await notification_system.send_staff_confirmation_notification(
                    staff_id=1,
                    request_id='test_request_123',
                    workflow_type='technical_service',
                    client_name='Test Client',
                    request_data=sample_request_data
                )
                
                assert result is True
                
                # Verify message sent
                mock_bot.send_message.assert_called_once()
                call_args = mock_bot.send_message.call_args
                
                assert call_args[1]['chat_id'] == 987654321
                assert 'успешно создана' in call_args[1]['text']
                assert 'Test Client' in call_args[1]['text']
    
    @pytest.mark.asyncio
    async def test_send_staff_workflow_notification_success(self, notification_system, sample_request_data):
        """Test successful workflow participant notification"""
        # Mock the _get_pool method to return a working mock
        with patch.object(notification_system, '_get_pool') as mock_get_pool:
            # Create proper async context manager mock
            mock_conn = AsyncMock()
            mock_pool = AsyncMock()
            
            # Mock workflow participants
            participants = [
                {
                    'id': 2,
                    'telegram_id': 111222333,
                    'full_name': 'Junior Manager 1',
                    'language': 'uz'
                },
                {
                    'id': 3,
                    'telegram_id': 444555666,
                    'full_name': 'Junior Manager 2',
                    'language': 'ru'
                }
            ]
            mock_conn.fetch.return_value = participants
            mock_conn.execute.return_value = None
            
            # Setup async context manager
            async def mock_acquire():
                return mock_conn
            
            mock_pool.acquire = mock_acquire
            mock_get_pool.return_value = mock_pool
            
            with patch('loader.bot') as mock_bot:
                mock_bot.send_message = AsyncMock()
                
                result = await notification_system.send_staff_workflow_notification(
                    role='junior_manager',
                    request_id='test_request_123',
                    workflow_type='connection_request',
                    creator_role='manager',
                    client_name='Test Client',
                    request_data=sample_request_data
                )
                
                assert result is True
                
                # Verify notifications sent to all participants
                assert mock_bot.send_message.call_count == 2
                
                # Verify notification records created
                assert mock_conn.execute.call_count == 2  # One for each participant
    
    @pytest.mark.asyncio
    async def test_send_staff_workflow_notification_excluded_roles(self, notification_system, mock_pool):
        """Test that excluded roles don't receive workflow notifications"""
        result = await notification_system.send_staff_workflow_notification(
            role='client',  # Excluded role
            request_id='test_request_123',
            workflow_type='connection_request',
            creator_role='manager',
            client_name='Test Client',
            request_data={}
        )
        
        assert result is True  # Returns True but doesn't send notifications
    
    @pytest.mark.asyncio
    async def test_send_staff_workflow_notification_no_participants(self, notification_system, mock_pool):
        """Test workflow notification when no participants found"""
        pool, conn = mock_pool
        conn.fetch.return_value = []  # No participants
        
        result = await notification_system.send_staff_workflow_notification(
            role='technician',
            request_id='test_request_123',
            workflow_type='connection_request',
            creator_role='manager',
            client_name='Test Client',
            request_data={}
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_notification_templates_uzbek_connection_request(self, notification_system):
        """Test Uzbek templates for connection request"""
        templates = notification_system.staff_notification_templates
        
        # Client notification template
        client_template = templates['client_notification']['uz']['connection_request']
        assert 'Sizning nomingizdan ariza yaratildi' in client_template['title']
        assert '{client_name}' in client_template['body']
        assert '{description}' in client_template['body']
        assert '{location}' in client_template['body']
        assert '{creator_role}' in client_template['body']
        assert '{request_id}' in client_template['body']
        
        # Staff confirmation template
        staff_template = templates['staff_confirmation']['uz']['connection_request']
        assert 'muvaffaqiyatli yaratildi' in staff_template['title']
        assert '{client_name}' in staff_template['body']
        
        # Workflow participant template
        workflow_template = templates['workflow_participant']['uz']['connection_request']
        assert 'Xodim tomonidan yaratilgan' in workflow_template['title']
        assert '{creator_role}' in workflow_template['body']
    
    @pytest.mark.asyncio
    async def test_notification_templates_russian_technical_service(self, notification_system):
        """Test Russian templates for technical service"""
        templates = notification_system.staff_notification_templates
        
        # Client notification template
        client_template = templates['client_notification']['ru']['technical_service']
        assert 'техническое обслуживание' in client_template['title']
        assert '{client_name}' in client_template['body']
        assert '{description}' in client_template['body']
        
        # Staff confirmation template
        staff_template = templates['staff_confirmation']['ru']['technical_service']
        assert 'успешно создана' in staff_template['title']
        assert '{client_name}' in staff_template['body']
        
        # Workflow participant template
        workflow_template = templates['workflow_participant']['ru']['technical_service']
        assert 'техническая заявка' in workflow_template['title']
        assert '{creator_role}' in workflow_template['body']
    
    @pytest.mark.asyncio
    async def test_notification_error_handling(self, notification_system, mock_pool):
        """Test error handling in notification methods"""
        pool, conn = mock_pool
        
        # Simulate database error
        conn.fetchrow.side_effect = Exception("Database error")
        
        # Test client notification error handling
        result = await notification_system.send_staff_client_notification(
            client_id=1,
            request_id='test_request_123',
            workflow_type='connection_request',
            creator_role='manager',
            request_data={}
        )
        assert result is False
        
        # Test staff confirmation error handling
        result = await notification_system.send_staff_confirmation_notification(
            staff_id=1,
            request_id='test_request_123',
            workflow_type='connection_request',
            client_name='Test Client',
            request_data={}
        )
        assert result is False
        
        # Test workflow notification error handling
        result = await notification_system.send_staff_workflow_notification(
            role='manager',
            request_id='test_request_123',
            workflow_type='connection_request',
            creator_role='manager',
            client_name='Test Client',
            request_data={}
        )
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__])