"""
Unit Tests for Staff Application Confirmation Flows

Tests the application creation confirmation flows including:
- Application preview and confirmation screens
- Edit capabilities before final submission
- Submission confirmation and success messages
- Error handling and retry mechanisms

Requirements: 1.5, 2.4, 3.4, 4.4
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

# Mock aiogram components
class MockMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.from_user = MockUser()
    
    async def answer(self, text: str, reply_markup=None, parse_mode=None):
        return {"text": text, "reply_markup": reply_markup, "parse_mode": parse_mode}
    
    async def edit_text(self, text: str, reply_markup=None, parse_mode=None):
        return {"text": text, "reply_markup": reply_markup, "parse_mode": parse_mode}

class MockCallbackQuery:
    def __init__(self, data: str = ""):
        self.data = data
        self.from_user = MockUser()
        self.message = MockMessage()
    
    async def answer(self, text: str = "", show_alert: bool = False):
        return {"text": text, "show_alert": show_alert}

class MockUser:
    def __init__(self, user_id: int = 12345):
        self.id = user_id

class MockFSMContext:
    def __init__(self, initial_data: Dict[str, Any] = None):
        self._data = initial_data or {}
        self._state = None
    
    async def get_data(self) -> Dict[str, Any]:
        return self._data.copy()
    
    async def update_data(self, data: Dict[str, Any]):
        self._data.update(data)
    
    async def set_state(self, state):
        self._state = state
    
    async def clear(self):
        self._data.clear()
        self._state = None

# Test fixtures
@pytest.fixture
def sample_application_data():
    """Sample application data for testing"""
    return {
        'application_type': 'connection_request',
        'confirmed_client': {
            'id': 123,
            'full_name': 'Test User',
            'phone_number': '+998901234567',
            'address': '123 Test Street'
        },
        'application_description': 'Test internet connection request',
        'application_address': '123 Test Street, Tashkent',
        'connection_type': 'Fiber Optic',
        'tariff': 'Premium 100Mbps',
        'priority': 'medium',
        'session_id': 'test-session-123',
        'started_at': datetime.now(),
        'media_files': ['test1.jpg'],
        'location_data': {'lat': 41.2995, 'lon': 69.2401}
    }

@pytest.fixture
def mock_fsm_context(sample_application_data):
    """Mock FSM context with sample data"""
    return MockFSMContext(sample_application_data)

@pytest.fixture
def mock_callback_query():
    """Mock callback query"""
    return MockCallbackQuery("app_preview_confirm")

@pytest.fixture
def mock_message():
    """Mock message"""
    return MockMessage("Test message")

# Test keyboard functions
class TestConfirmationKeyboards:
    """Test confirmation keyboard functions"""
    
    def test_application_preview_keyboard_uzbek(self):
        """Test application preview keyboard in Uzbek"""
        from keyboards.staff_confirmation_buttons import get_application_preview_keyboard
        
        keyboard = get_application_preview_keyboard('uz')
        
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 4  # 4 rows of buttons
        
        # Check first row (confirm button)
        assert keyboard.inline_keyboard[0][0].text == "✅ Tasdiqlash"
        assert keyboard.inline_keyboard[0][0].callback_data == "app_preview_confirm"
        
        # Check edit buttons
        assert "tahrirlash" in keyboard.inline_keyboard[1][0].text.lower()
        assert "tahrirlash" in keyboard.inline_keyboard[1][1].text.lower()
    
    def test_application_preview_keyboard_russian(self):
        """Test application preview keyboard in Russian"""
        from keyboards.staff_confirmation_buttons import get_application_preview_keyboard
        
        keyboard = get_application_preview_keyboard('ru')
        
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 4
        
        # Check first row (confirm button)
        assert keyboard.inline_keyboard[0][0].text == "✅ Подтвердить"
        assert keyboard.inline_keyboard[0][0].callback_data == "app_preview_confirm"
        
        # Check edit buttons
        assert "редактировать" in keyboard.inline_keyboard[1][0].text.lower()
        assert "редактировать" in keyboard.inline_keyboard[1][1].text.lower()
    
    def test_submission_confirmation_keyboard(self):
        """Test submission confirmation keyboard"""
        from keyboards.staff_confirmation_buttons import get_submission_confirmation_keyboard
        
        keyboard_uz = get_submission_confirmation_keyboard('uz')
        keyboard_ru = get_submission_confirmation_keyboard('ru')
        
        # Test Uzbek
        assert keyboard_uz.inline_keyboard[0][0].text == "✅ Ha, yuborish"
        assert keyboard_uz.inline_keyboard[0][0].callback_data == "app_submit_confirm"
        
        # Test Russian
        assert keyboard_ru.inline_keyboard[0][0].text == "✅ Да, отправить"
        assert keyboard_ru.inline_keyboard[0][0].callback_data == "app_submit_confirm"
    
    def test_success_keyboard(self):
        """Test success keyboard"""
        from keyboards.staff_confirmation_buttons import get_submission_success_keyboard
        
        keyboard_uz = get_submission_success_keyboard('uz')
        keyboard_ru = get_submission_success_keyboard('ru')
        
        # Test Uzbek
        assert "yangi ariza" in keyboard_uz.inline_keyboard[0][0].text.lower()
        assert keyboard_uz.inline_keyboard[0][0].callback_data == "app_success_create_another"
        
        # Test Russian
        assert "новую заявку" in keyboard_ru.inline_keyboard[0][0].text.lower()
        assert keyboard_ru.inline_keyboard[0][0].callback_data == "app_success_create_another"
    
    def test_error_retry_keyboard(self):
        """Test error retry keyboard"""
        from keyboards.staff_confirmation_buttons import get_error_retry_keyboard
        
        # Test validation error (should have edit option)
        keyboard_validation = get_error_retry_keyboard('validation_error', 'uz')
        assert len(keyboard_validation.inline_keyboard) == 3  # retry, edit, cancel
        
        # Test system error (should not have edit option)
        keyboard_system = get_error_retry_keyboard('system_error', 'uz')
        assert len(keyboard_system.inline_keyboard) == 2  # retry, cancel

# Test text formatting functions
class TestTextFormatting:
    """Test text formatting functions"""
    
    def test_application_preview_text_formatting(self, sample_application_data):
        """Test application preview text formatting"""
        from keyboards.staff_confirmation_buttons import format_application_preview_text
        
        # Test Uzbek
        text_uz = format_application_preview_text(sample_application_data, 'uz')
        assert "Ariza ko'rib chiqish" in text_uz
        assert "Test User" in text_uz
        assert "+998901234567" in text_uz
        assert "Test internet connection request" in text_uz
        
        # Test Russian
        text_ru = format_application_preview_text(sample_application_data, 'ru')
        assert "Просмотр заявки" in text_ru
        assert "Test User" in text_ru
        assert "+998901234567" in text_ru
        assert "Test internet connection request" in text_ru
    
    def test_submission_confirmation_text(self, sample_application_data):
        """Test submission confirmation text"""
        from keyboards.staff_confirmation_buttons import format_submission_confirmation_text
        
        text_uz = format_submission_confirmation_text(sample_application_data, 'uz')
        assert "Yakuniy tasdiqlash" in text_uz
        assert "Test User" in text_uz
        
        text_ru = format_submission_confirmation_text(sample_application_data, 'ru')
        assert "Окончательное подтверждение" in text_ru
        assert "Test User" in text_ru
    
    def test_success_message_text(self):
        """Test success message text"""
        from keyboards.staff_confirmation_buttons import format_success_message_text
        
        result = {
            'application_id': 'APP-2024-001',
            'workflow_type': 'connection_request',
            'client_id': 123,
            'notification_sent': True,
            'created_at': datetime.now()
        }
        
        text_uz = format_success_message_text(result, 'uz')
        assert "muvaffaqiyatli yaratildi" in text_uz
        assert "APP-2024-001" in text_uz
        
        text_ru = format_success_message_text(result, 'ru')
        assert "успешно создана" in text_ru
        assert "APP-2024-001" in text_ru
    
    def test_error_message_text(self):
        """Test error message text"""
        from keyboards.staff_confirmation_buttons import format_error_message_text
        
        error_result = {
            'error_type': 'validation_error',
            'error_message': 'Data validation failed',
            'error_details': {
                'phone': 'Invalid format',
                'address': 'Required field'
            }
        }
        
        text_uz = format_error_message_text(error_result, 'uz')
        assert "xatolik" in text_uz.lower()
        assert "validation" in text_uz.lower() or "tekshiruvi" in text_uz.lower()
        
        text_ru = format_error_message_text(error_result, 'ru')
        assert "ошибка" in text_ru.lower()
        assert "проверки" in text_ru.lower()

# Test handler functions (mocked)
class TestConfirmationHandlers:
    """Test confirmation handler functions"""
    
    @pytest.mark.asyncio
    async def test_show_application_preview(self, mock_message, mock_fsm_context):
        """Test showing application preview"""
        # Mock the required imports
        with patch('handlers.staff_application_confirmation.get_user_language', return_value='uz'):
            with patch('keyboards.staff_confirmation_buttons.format_application_preview_text', return_value="Preview text"):
                with patch('keyboards.staff_confirmation_buttons.get_application_preview_keyboard', return_value=MagicMock()):
                    # Import and test the function
                    from handlers.staff_application_confirmation import show_application_preview
                    
                    data = await mock_fsm_context.get_data()
                    await show_application_preview(mock_message, mock_fsm_context, data, 'uz')
                    
                    # Verify state was set
                    assert mock_fsm_context._state is not None
    
    @pytest.mark.asyncio
    async def test_prepare_application_for_submission(self, sample_application_data):
        """Test preparing application for submission"""
        from handlers.staff_application_confirmation import prepare_application_for_submission
        
        result = await prepare_application_for_submission(sample_application_data, 12345, 'manager')
        
        assert 'client_data' in result
        assert 'application_data' in result
        assert result['client_data']['phone'] == '+998901234567'
        assert result['client_data']['full_name'] == 'Test User'
        assert result['application_data']['description'] == 'Test internet connection request'
        assert result['application_data']['location'] == '123 Test Street, Tashkent'
    
    @pytest.mark.asyncio
    async def test_application_type_specific_data(self):
        """Test application type specific data preparation"""
        from handlers.staff_application_confirmation import prepare_application_for_submission
        
        # Test connection request
        connection_data = {
            'application_type': 'connection_request',
            'confirmed_client': {'phone_number': '+998901234567', 'full_name': 'Test'},
            'application_description': 'Test',
            'application_address': 'Test Address',
            'connection_type': 'Fiber',
            'tariff': 'Premium'
        }
        
        result = await prepare_application_for_submission(connection_data, 12345, 'manager')
        assert result['application_data']['connection_type'] == 'Fiber'
        assert result['application_data']['tariff'] == 'Premium'
        
        # Test technical service
        technical_data = {
            'application_type': 'technical_service',
            'confirmed_client': {'phone_number': '+998901234567', 'full_name': 'Test'},
            'application_description': 'Test',
            'application_address': 'Test Address',
            'issue_type': 'Network Issue'
        }
        
        result = await prepare_application_for_submission(technical_data, 12345, 'manager')
        assert result['application_data']['issue_type'] == 'Network Issue'

# Test error handling
class TestErrorHandling:
    """Test error handling functionality"""
    
    def test_error_message_formatting_different_types(self):
        """Test error message formatting for different error types"""
        from keyboards.staff_confirmation_buttons import format_error_message_text
        
        error_types = [
            {
                'error_type': 'validation_error',
                'error_message': 'Validation failed',
                'error_details': {'field': 'issue'}
            },
            {
                'error_type': 'client_validation_error',
                'error_message': 'Client data invalid',
                'error_details': {}
            },
            {
                'error_type': 'workflow_error',
                'error_message': 'Workflow failed',
                'error_details': {}
            },
            {
                'error_type': 'permission_denied',
                'error_message': 'No permission',
                'error_details': {}
            },
            {
                'error_type': 'unknown_error',
                'error_message': 'Unknown issue',
                'error_details': {}
            }
        ]
        
        for error_case in error_types:
            text_uz = format_error_message_text(error_case, 'uz')
            text_ru = format_error_message_text(error_case, 'ru')
            
            assert len(text_uz) > 0
            assert len(text_ru) > 0
            assert "xatolik" in text_uz.lower() or "xato" in text_uz.lower()
            assert "ошибка" in text_ru.lower()
    
    def test_retry_keyboard_for_different_errors(self):
        """Test retry keyboard for different error types"""
        from keyboards.staff_confirmation_buttons import get_error_retry_keyboard
        
        # Validation errors should have edit option
        validation_keyboard = get_error_retry_keyboard('validation_error', 'uz')
        assert len(validation_keyboard.inline_keyboard) >= 2
        
        # System errors should not have edit option
        system_keyboard = get_error_retry_keyboard('system_error', 'uz')
        assert len(system_keyboard.inline_keyboard) >= 2

# Test language support
class TestLanguageSupport:
    """Test language support functionality"""
    
    def test_all_keyboards_support_both_languages(self):
        """Test that all keyboards support both Uzbek and Russian"""
        from keyboards.staff_confirmation_buttons import (
            get_application_preview_keyboard,
            get_submission_confirmation_keyboard,
            get_submission_success_keyboard,
            get_error_retry_keyboard
        )
        
        keyboards = [
            get_application_preview_keyboard,
            get_submission_confirmation_keyboard,
            get_submission_success_keyboard,
            lambda lang: get_error_retry_keyboard('validation_error', lang)
        ]
        
        for keyboard_func in keyboards:
            keyboard_uz = keyboard_func('uz')
            keyboard_ru = keyboard_func('ru')
            
            assert keyboard_uz is not None
            assert keyboard_ru is not None
            assert len(keyboard_uz.inline_keyboard) > 0
            assert len(keyboard_ru.inline_keyboard) > 0
    
    def test_all_text_formatters_support_both_languages(self, sample_application_data):
        """Test that all text formatters support both languages"""
        from keyboards.staff_confirmation_buttons import (
            format_application_preview_text,
            format_submission_confirmation_text,
            format_success_message_text,
            format_error_message_text
        )
        
        success_result = {
            'application_id': 'APP-001',
            'workflow_type': 'connection_request',
            'created_at': datetime.now()
        }
        
        error_result = {
            'error_type': 'validation_error',
            'error_message': 'Test error',
            'error_details': {}
        }
        
        formatters = [
            (format_application_preview_text, sample_application_data),
            (format_submission_confirmation_text, sample_application_data),
            (format_success_message_text, success_result),
            (format_error_message_text, error_result)
        ]
        
        for formatter_func, data in formatters:
            text_uz = formatter_func(data, 'uz')
            text_ru = formatter_func(data, 'ru')
            
            assert len(text_uz) > 0
            assert len(text_ru) > 0
            assert text_uz != text_ru  # Should be different for different languages

# Test edge cases
class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_application_data(self):
        """Test handling of empty application data"""
        from keyboards.staff_confirmation_buttons import format_application_preview_text
        
        empty_data = {}
        text = format_application_preview_text(empty_data, 'uz')
        
        # Should not crash and should contain some default text
        assert len(text) > 0
        assert "Kiritilmagan" in text or "Unknown" in text
    
    def test_missing_client_data(self):
        """Test handling of missing client data"""
        from keyboards.staff_confirmation_buttons import format_application_preview_text
        
        data_without_client = {
            'application_type': 'connection_request',
            'application_description': 'Test'
        }
        
        text = format_application_preview_text(data_without_client, 'uz')
        assert len(text) > 0
    
    def test_invalid_error_type(self):
        """Test handling of invalid error type"""
        from keyboards.staff_confirmation_buttons import format_error_message_text
        
        invalid_error = {
            'error_type': 'invalid_type_that_does_not_exist',
            'error_message': 'Some error',
            'error_details': {}
        }
        
        text = format_error_message_text(invalid_error, 'uz')
        assert len(text) > 0
        assert "xatolik" in text.lower() or "xato" in text.lower()
    
    @pytest.mark.asyncio
    async def test_prepare_application_with_missing_fields(self):
        """Test preparing application with missing fields"""
        from handlers.staff_application_confirmation import prepare_application_for_submission
        
        minimal_data = {
            'confirmed_client': {'phone_number': '+998901234567'},
            'application_description': 'Test'
        }
        
        # Should not crash
        result = await prepare_application_for_submission(minimal_data, 12345, 'manager')
        assert 'client_data' in result
        assert 'application_data' in result

# Integration tests
class TestIntegration:
    """Test integration between components"""
    
    @pytest.mark.asyncio
    async def test_full_confirmation_flow(self, sample_application_data):
        """Test full confirmation flow integration"""
        from keyboards.staff_confirmation_buttons import (
            format_application_preview_text,
            get_application_preview_keyboard,
            format_submission_confirmation_text,
            get_submission_confirmation_keyboard
        )
        from handlers.staff_application_confirmation import prepare_application_for_submission
        
        # Step 1: Format preview
        preview_text = format_application_preview_text(sample_application_data, 'uz')
        preview_keyboard = get_application_preview_keyboard('uz')
        
        assert len(preview_text) > 0
        assert preview_keyboard is not None
        
        # Step 2: Format confirmation
        confirmation_text = format_submission_confirmation_text(sample_application_data, 'uz')
        confirmation_keyboard = get_submission_confirmation_keyboard('uz')
        
        assert len(confirmation_text) > 0
        assert confirmation_keyboard is not None
        
        # Step 3: Prepare for submission
        prepared_data = await prepare_application_for_submission(sample_application_data, 12345, 'manager')
        
        assert 'client_data' in prepared_data
        assert 'application_data' in prepared_data
    
    def test_keyboard_callback_data_consistency(self):
        """Test that keyboard callback data is consistent"""
        from keyboards.staff_confirmation_buttons import (
            get_application_preview_keyboard,
            get_submission_confirmation_keyboard,
            get_submission_success_keyboard,
            get_error_retry_keyboard
        )
        
        # Collect all callback data
        all_callbacks = set()
        
        keyboards = [
            get_application_preview_keyboard('uz'),
            get_submission_confirmation_keyboard('uz'),
            get_submission_success_keyboard('uz'),
            get_error_retry_keyboard('validation_error', 'uz')
        ]
        
        for keyboard in keyboards:
            for row in keyboard.inline_keyboard:
                for button in row:
                    all_callbacks.add(button.callback_data)
        
        # Check that callback data follows consistent pattern
        for callback in all_callbacks:
            assert isinstance(callback, str)
            assert len(callback) > 0
            # Most callbacks should start with 'app_'
            if not callback.startswith('app_'):
                print(f"Warning: Callback '{callback}' doesn't follow 'app_' pattern")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])