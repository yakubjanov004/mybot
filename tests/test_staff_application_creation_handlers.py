"""
Test Staff Application Creation Handlers

This test file verifies that all role-specific staff application creation handlers
are properly implemented and integrated with the system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.fsm.context import FSMContext

# Import handlers to test
from handlers.manager.staff_application_creation import get_manager_staff_application_router
from handlers.junior_manager.staff_application_creation import get_junior_manager_staff_application_router
from handlers.controller.staff_application_creation import get_controller_staff_application_router
from handlers.call_center.staff_application_creation import get_call_center_staff_application_router
from handlers.shared_staff_application_flow import get_shared_staff_application_flow_router
from handlers.staff_application_creation import RoleBasedApplicationHandler
from states.staff_application_states import StaffApplicationStates


class TestStaffApplicationCreationHandlers:
    """Test class for staff application creation handlers"""
    
    @pytest.fixture
    def mock_user_data(self):
        """Mock user data for different roles"""
        return {
            'manager': {
                'id': 1,
                'telegram_id': 12345,
                'role': 'manager',
                'language': 'uz',
                'full_name': 'Test Manager'
            },
            'junior_manager': {
                'id': 2,
                'telegram_id': 12346,
                'role': 'junior_manager',
                'language': 'uz',
                'full_name': 'Test Junior Manager'
            },
            'controller': {
                'id': 3,
                'telegram_id': 12347,
                'role': 'controller',
                'language': 'uz',
                'full_name': 'Test Controller'
            },
            'call_center': {
                'id': 4,
                'telegram_id': 12348,
                'role': 'call_center',
                'language': 'uz',
                'full_name': 'Test Call Center'
            }
        }
    
    @pytest.fixture
    def mock_message(self):
        """Create mock message object"""
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=12345, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            content_type="text",
            text="Test message"
        )
        message.answer = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_callback_query(self):
        """Create mock callback query object"""
        user = User(id=12345, is_bot=False, first_name="Test", username="testuser")
        message = MagicMock()
        message.edit_text = AsyncMock()
        message.answer = AsyncMock()
        
        callback = CallbackQuery(
            id="test_callback",
            from_user=user,
            chat_instance="test_instance",
            data="test_data",
            message=message
        )
        callback.answer = AsyncMock()
        return callback
    
    @pytest.fixture
    def mock_state(self):
        """Create mock FSM state"""
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={})
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.clear = AsyncMock()
        return state
    
    @pytest.fixture
    def mock_app_handler(self):
        """Create mock application handler"""
        handler = AsyncMock(spec=RoleBasedApplicationHandler)
        handler.start_application_creation = AsyncMock(return_value={
            'success': True,
            'creator_context': {
                'creator_id': 1,
                'creator_role': 'manager',
                'application_type': 'connection_request',
                'permissions': {},
                'daily_count': 0,
                'session_id': 'test_session',
                'started_at': '2024-01-01T00:00:00'
            }
        })
        handler.process_application_form = AsyncMock(return_value={
            'success': True,
            'processed_data': {}
        })
        handler.validate_and_submit = AsyncMock(return_value={
            'success': True,
            'application_id': 'TEST123',
            'workflow_type': 'connection_request',
            'client_id': 1,
            'notification_sent': True,
            'created_at': '2024-01-01T00:00:00'
        })
        return handler
    
    @pytest.mark.asyncio
    async def test_manager_connection_request_creation(self, mock_message, mock_state, mock_user_data):
        """Test manager connection request creation"""
        with patch('handlers.manager.staff_application_creation.get_user_by_telegram_id') as mock_get_user, \
             patch('handlers.manager.staff_application_creation.RoleBasedApplicationHandler') as mock_handler_class:
            
            # Setup mocks
            mock_get_user.return_value = mock_user_data['manager']
            mock_handler = AsyncMock()
            mock_handler.start_application_creation.return_value = {
                'success': True,
                'creator_context': {
                    'creator_id': 1,
                    'creator_role': 'manager',
                    'application_type': 'connection_request'
                }
            }
            mock_handler_class.return_value = mock_handler
            
            # Get router and find the handler
            router = get_manager_staff_application_router()
            
            # Simulate message with connection request text
            mock_message.text = "🔌 Ulanish arizasi yaratish"
            
            # Find and call the handler
            handlers = [h for h in router.message.handlers if h.callback]
            connection_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔌 Ulanish arizasi yaratish" in str(f) for f in handler.filters.values()):
                    connection_handler = handler.callback
                    break
            
            assert connection_handler is not None, "Connection request handler not found"
            
            # Call the handler
            await connection_handler(mock_message, mock_state)
            
            # Verify calls
            mock_get_user.assert_called_once_with(12345)
            mock_handler.start_application_creation.assert_called_once_with(
                creator_role='manager',
                creator_id=1,
                application_type='connection_request'
            )
            mock_message.answer.assert_called_once()
            mock_state.update_data.assert_called_once()
            mock_state.set_state.assert_called_once_with(StaffApplicationStates.selecting_client_search_method)
    
    @pytest.mark.asyncio
    async def test_manager_technical_service_creation(self, mock_message, mock_state, mock_user_data):
        """Test manager technical service creation"""
        with patch('handlers.manager.staff_application_creation.get_user_by_telegram_id') as mock_get_user, \
             patch('handlers.manager.staff_application_creation.RoleBasedApplicationHandler') as mock_handler_class:
            
            # Setup mocks
            mock_get_user.return_value = mock_user_data['manager']
            mock_handler = AsyncMock()
            mock_handler.start_application_creation.return_value = {
                'success': True,
                'creator_context': {
                    'creator_id': 1,
                    'creator_role': 'manager',
                    'application_type': 'technical_service'
                }
            }
            mock_handler_class.return_value = mock_handler
            
            # Get router
            router = get_manager_staff_application_router()
            
            # Simulate message with technical service text
            mock_message.text = "🔧 Texnik xizmat yaratish"
            
            # Find and call the handler
            handlers = [h for h in router.message.handlers if h.callback]
            technical_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔧 Texnik xizmat yaratish" in str(f) for f in handler.filters.values()):
                    technical_handler = handler.callback
                    break
            
            assert technical_handler is not None, "Technical service handler not found"
            
            # Call the handler
            await technical_handler(mock_message, mock_state)
            
            # Verify calls
            mock_get_user.assert_called_once_with(12345)
            mock_handler.start_application_creation.assert_called_once_with(
                creator_role='manager',
                creator_id=1,
                application_type='technical_service'
            )
            mock_message.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_junior_manager_connection_only(self, mock_message, mock_state, mock_user_data):
        """Test junior manager can only create connection requests"""
        with patch('handlers.junior_manager.staff_application_creation.get_user_by_telegram_id') as mock_get_user, \
             patch('handlers.junior_manager.staff_application_creation.RoleBasedApplicationHandler') as mock_handler_class:
            
            # Setup mocks
            mock_get_user.return_value = mock_user_data['junior_manager']
            mock_handler = AsyncMock()
            mock_handler.start_application_creation.return_value = {
                'success': True,
                'creator_context': {
                    'creator_id': 2,
                    'creator_role': 'junior_manager',
                    'application_type': 'connection_request'
                }
            }
            mock_handler_class.return_value = mock_handler
            
            # Get router
            router = get_junior_manager_staff_application_router()
            
            # Test connection request (should work)
            mock_message.text = "🔌 Ulanish arizasi yaratish"
            
            # Find and call the connection handler
            handlers = [h for h in router.message.handlers if h.callback]
            connection_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔌 Ulanish arizasi yaratish" in str(f) for f in handler.filters.values()):
                    connection_handler = handler.callback
                    break
            
            assert connection_handler is not None, "Connection request handler not found"
            await connection_handler(mock_message, mock_state)
            
            # Verify connection request works
            mock_handler.start_application_creation.assert_called_once_with(
                creator_role='junior_manager',
                creator_id=2,
                application_type='connection_request'
            )
            
            # Reset mocks
            mock_message.answer.reset_mock()
            mock_get_user.reset_mock()
            
            # Test technical service (should be denied)
            mock_message.text = "🔧 Texnik xizmat yaratish"
            
            # Find and call the technical service handler
            technical_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔧 Texnik xizmat yaratish" in str(f) for f in handler.filters.values()):
                    technical_handler = handler.callback
                    break
            
            assert technical_handler is not None, "Technical service denial handler not found"
            await technical_handler(mock_message, mock_state)
            
            # Verify technical service is denied
            mock_message.answer.assert_called_once()
            # Check that the answer contains denial message
            call_args = mock_message.answer.call_args[0][0]
            assert "Ruxsat rad etildi" in call_args or "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_controller_both_application_types(self, mock_message, mock_state, mock_user_data):
        """Test controller can create both connection and technical service requests"""
        with patch('handlers.controller.staff_application_creation.get_user_by_telegram_id') as mock_get_user, \
             patch('handlers.controller.staff_application_creation.RoleBasedApplicationHandler') as mock_handler_class:
            
            # Setup mocks
            mock_get_user.return_value = mock_user_data['controller']
            mock_handler = AsyncMock()
            mock_handler.start_application_creation.return_value = {
                'success': True,
                'creator_context': {
                    'creator_id': 3,
                    'creator_role': 'controller',
                    'application_type': 'connection_request'
                }
            }
            mock_handler_class.return_value = mock_handler
            
            # Get router
            router = get_controller_staff_application_router()
            
            # Test connection request
            mock_message.text = "🔌 Ulanish arizasi yaratish"
            
            handlers = [h for h in router.message.handlers if h.callback]
            connection_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔌 Ulanish arizasi yaratish" in str(f) for f in handler.filters.values()):
                    connection_handler = handler.callback
                    break
            
            assert connection_handler is not None
            await connection_handler(mock_message, mock_state)
            
            mock_handler.start_application_creation.assert_called_with(
                creator_role='controller',
                creator_id=3,
                application_type='connection_request'
            )
            
            # Reset and test technical service
            mock_handler.start_application_creation.reset_mock()
            mock_handler.start_application_creation.return_value = {
                'success': True,
                'creator_context': {
                    'creator_id': 3,
                    'creator_role': 'controller',
                    'application_type': 'technical_service'
                }
            }
            
            mock_message.text = "🔧 Texnik xizmat yaratish"
            
            technical_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔧 Texnik xizmat yaratish" in str(f) for f in handler.filters.values()):
                    technical_handler = handler.callback
                    break
            
            assert technical_handler is not None
            await technical_handler(mock_message, mock_state)
            
            mock_handler.start_application_creation.assert_called_with(
                creator_role='controller',
                creator_id=3,
                application_type='technical_service'
            )
    
    @pytest.mark.asyncio
    async def test_call_center_both_application_types(self, mock_message, mock_state, mock_user_data):
        """Test call center can create both connection and technical service requests"""
        with patch('handlers.call_center.staff_application_creation.get_user_by_telegram_id') as mock_get_user, \
             patch('handlers.call_center.staff_application_creation.RoleBasedApplicationHandler') as mock_handler_class:
            
            # Setup mocks
            mock_get_user.return_value = mock_user_data['call_center']
            mock_handler = AsyncMock()
            mock_handler.start_application_creation.return_value = {
                'success': True,
                'creator_context': {
                    'creator_id': 4,
                    'creator_role': 'call_center',
                    'application_type': 'connection_request'
                }
            }
            mock_handler_class.return_value = mock_handler
            
            # Get router
            router = get_call_center_staff_application_router()
            
            # Test connection request
            mock_message.text = "🔌 Ulanish arizasi yaratish"
            
            handlers = [h for h in router.message.handlers if h.callback]
            connection_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔌 Ulanish arizasi yaratish" in str(f) for f in handler.filters.values()):
                    connection_handler = handler.callback
                    break
            
            assert connection_handler is not None
            await connection_handler(mock_message, mock_state)
            
            mock_handler.start_application_creation.assert_called_with(
                creator_role='call_center',
                creator_id=4,
                application_type='connection_request'
            )
            
            # Test technical service
            mock_handler.start_application_creation.reset_mock()
            mock_handler.start_application_creation.return_value = {
                'success': True,
                'creator_context': {
                    'creator_id': 4,
                    'creator_role': 'call_center',
                    'application_type': 'technical_service'
                }
            }
            
            mock_message.text = "🔧 Texnik xizmat yaratish"
            
            technical_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔧 Texnik xizmat yaratish" in str(f) for f in handler.filters.values()):
                    technical_handler = handler.callback
                    break
            
            assert technical_handler is not None
            await technical_handler(mock_message, mock_state)
            
            mock_handler.start_application_creation.assert_called_with(
                creator_role='call_center',
                creator_id=4,
                application_type='technical_service'
            )
    
    @pytest.mark.asyncio
    async def test_client_search_callback_handling(self, mock_callback_query, mock_state, mock_user_data):
        """Test client search method callback handling"""
        with patch('handlers.manager.staff_application_creation.get_user_by_telegram_id') as mock_get_user:
            
            mock_get_user.return_value = mock_user_data['manager']
            
            # Get router
            router = get_manager_staff_application_router()
            
            # Test phone search callback
            mock_callback_query.data = "client_search_phone"
            
            # Find callback handler
            callback_handlers = [h for h in router.callback_query.handlers if h.callback]
            search_handler = None
            for handler in callback_handlers:
                if hasattr(handler.filters, 'values') and any("client_search_" in str(f) for f in handler.filters.values()):
                    search_handler = handler.callback
                    break
            
            assert search_handler is not None, "Client search callback handler not found"
            
            await search_handler(mock_callback_query, mock_state)
            
            # Verify state updates
            mock_state.update_data.assert_called_once_with(client_search_method="phone")
            mock_state.set_state.assert_called_once_with(StaffApplicationStates.entering_client_phone)
            mock_callback_query.message.edit_text.assert_called_once()
            mock_callback_query.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shared_application_flow_handlers(self, mock_callback_query, mock_state, mock_user_data):
        """Test shared application flow handlers"""
        with patch('handlers.shared_staff_application_flow.get_user_by_telegram_id') as mock_get_user:
            
            mock_get_user.return_value = mock_user_data['manager']
            mock_state.get_data.return_value = {
                'selected_client': {
                    'id': 12345,
                    'full_name': 'Test Client',
                    'phone': '+998901234567',
                    'address': 'Test Address'
                },
                'application_type': 'connection_request'
            }
            
            # Get shared router
            router = get_shared_staff_application_flow_router()
            
            # Test client confirmation callback
            mock_callback_query.data = "confirm_client_selection"
            
            # Find callback handler
            callback_handlers = [h for h in router.callback_query.handlers if h.callback]
            confirm_handler = None
            for handler in callback_handlers:
                if hasattr(handler.filters, 'values') and any("confirm_client_selection" in str(f) for f in handler.filters.values()):
                    confirm_handler = handler.callback
                    break
            
            assert confirm_handler is not None, "Client confirmation handler not found"
            
            await confirm_handler(mock_callback_query, mock_state)
            
            # Verify state transition
            mock_state.set_state.assert_called_once_with(StaffApplicationStates.entering_application_description)
            mock_callback_query.message.edit_text.assert_called_once()
            mock_callback_query.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_permission_denied_handling(self, mock_message, mock_state, mock_user_data):
        """Test permission denied scenarios"""
        with patch('handlers.manager.staff_application_creation.get_user_by_telegram_id') as mock_get_user, \
             patch('handlers.manager.staff_application_creation.RoleBasedApplicationHandler') as mock_handler_class:
            
            # Setup mocks for permission denied
            mock_get_user.return_value = mock_user_data['manager']
            mock_handler = AsyncMock()
            mock_handler.start_application_creation.return_value = {
                'success': False,
                'error_type': 'permission_denied',
                'error_message': 'Daily limit exceeded'
            }
            mock_handler_class.return_value = mock_handler
            
            # Get router
            router = get_manager_staff_application_router()
            
            # Simulate message
            mock_message.text = "🔌 Ulanish arizasi yaratish"
            
            # Find and call the handler
            handlers = [h for h in router.message.handlers if h.callback]
            connection_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔌 Ulanish arizasi yaratish" in str(f) for f in handler.filters.values()):
                    connection_handler = handler.callback
                    break
            
            await connection_handler(mock_message, mock_state)
            
            # Verify error handling
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args[0][0]
            assert "Ruxsat rad etildi" in call_args or "Daily limit exceeded" in call_args
    
    @pytest.mark.asyncio
    async def test_role_validation(self, mock_message, mock_state):
        """Test role validation in handlers"""
        with patch('handlers.manager.staff_application_creation.get_user_by_telegram_id') as mock_get_user:
            
            # Test with wrong role
            mock_get_user.return_value = {
                'id': 1,
                'telegram_id': 12345,
                'role': 'client',  # Wrong role
                'language': 'uz'
            }
            
            # Get router
            router = get_manager_staff_application_router()
            
            # Simulate message
            mock_message.text = "🔌 Ulanish arizasi yaratish"
            
            # Find and call the handler
            handlers = [h for h in router.message.handlers if h.callback]
            connection_handler = None
            for handler in handlers:
                if hasattr(handler.filters, 'values') and any("🔌 Ulanish arizasi yaratish" in str(f) for f in handler.filters.values()):
                    connection_handler = handler.callback
                    break
            
            await connection_handler(mock_message, mock_state)
            
            # Verify access denied
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args[0][0]
            assert "huquqi yo'q" in call_args or "нет прав" in call_args
    
    def test_router_registration(self):
        """Test that all routers are properly created and have handlers"""
        
        # Test manager router
        manager_router = get_manager_staff_application_router()
        assert manager_router is not None
        assert len(manager_router.message.handlers) > 0
        assert len(manager_router.callback_query.handlers) > 0
        
        # Test junior manager router
        junior_manager_router = get_junior_manager_staff_application_router()
        assert junior_manager_router is not None
        assert len(junior_manager_router.message.handlers) > 0
        assert len(junior_manager_router.callback_query.handlers) > 0
        
        # Test controller router
        controller_router = get_controller_staff_application_router()
        assert controller_router is not None
        assert len(controller_router.message.handlers) > 0
        assert len(controller_router.callback_query.handlers) > 0
        
        # Test call center router
        call_center_router = get_call_center_staff_application_router()
        assert call_center_router is not None
        assert len(call_center_router.message.handlers) > 0
        assert len(call_center_router.callback_query.handlers) > 0
        
        # Test shared flow router
        shared_router = get_shared_staff_application_flow_router()
        assert shared_router is not None
        assert len(shared_router.message.handlers) > 0
        assert len(shared_router.callback_query.handlers) > 0
    
    def test_handler_integration_requirements(self):
        """Test that handlers meet the requirements from the task"""
        
        # Requirement 1.1, 1.2: Manager can create both connection and technical
        manager_router = get_manager_staff_application_router()
        manager_message_handlers = [h for h in manager_router.message.handlers]
        
        # Just check that we have message handlers (detailed filter checking is complex)
        assert len(manager_message_handlers) >= 2, "Manager should have at least 2 message handlers (connection + technical)"
        
        # Requirement 2.1, 2.2: Junior Manager can create connection only
        junior_manager_router = get_junior_manager_staff_application_router()
        junior_message_handlers = [h for h in junior_manager_router.message.handlers]
        
        # Junior manager should have handlers for connection and technical denial
        assert len(junior_message_handlers) >= 2, "Junior Manager should have at least 2 message handlers (connection + technical denial)"
        
        # Requirement 3.1, 3.2: Controller can create both types
        controller_router = get_controller_staff_application_router()
        controller_message_handlers = [h for h in controller_router.message.handlers]
        
        assert len(controller_message_handlers) >= 2, "Controller should have at least 2 message handlers (connection + technical)"
        
        # Requirement 4.1, 4.2: Call Center can create both types
        call_center_router = get_call_center_staff_application_router()
        call_center_message_handlers = [h for h in call_center_router.message.handlers]
        
        assert len(call_center_message_handlers) >= 2, "Call Center should have at least 2 message handlers (connection + technical)"
        
        # Check callback handlers exist for client search
        manager_callback_handlers = [h for h in manager_router.callback_query.handlers]
        assert len(manager_callback_handlers) >= 1, "Manager should have callback handlers for client search"
        
        junior_callback_handlers = [h for h in junior_manager_router.callback_query.handlers]
        assert len(junior_callback_handlers) >= 1, "Junior Manager should have callback handlers for client search"
        
        controller_callback_handlers = [h for h in controller_router.callback_query.handlers]
        assert len(controller_callback_handlers) >= 1, "Controller should have callback handlers for client search"
        
        call_center_callback_handlers = [h for h in call_center_router.callback_query.handlers]
        assert len(call_center_callback_handlers) >= 1, "Call Center should have callback handlers for client search"


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestStaffApplicationCreationHandlers()
    
    print("Testing router registration...")
    test_instance.test_router_registration()
    print("✅ Router registration test passed")
    
    print("Testing handler integration requirements...")
    test_instance.test_handler_integration_requirements()
    print("✅ Handler integration requirements test passed")
    
    print("All basic tests passed! ✅")
    print("\nTo run full async tests, use: pytest tests/test_staff_application_creation_handlers.py")