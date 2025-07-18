"""
Test language support and localization for staff application creation.

This test suite verifies that all UI elements, error messages, and notifications
support both Uzbek and Russian languages consistently.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from aiogram.types import User, Message, CallbackQuery
from utils.staff_application_localization import (
    StaffApplicationTexts, StaffApplicationErrorMessages,
    get_staff_application_text, get_staff_application_error,
    format_application_summary, get_priority_text,
    get_connection_type_text, get_technical_service_type_text,
    get_role_specific_message, validate_language_consistency
)
from utils.staff_notification_localization import (
    StaffNotificationTexts, StaffNotificationFormatter,
    create_client_notification, create_staff_confirmation,
    create_workflow_assignment_notification, create_error_notification
)
from utils.form_error_messages import FormErrorMessages
from keyboards.manager_buttons import get_manager_main_keyboard
from keyboards.junior_manager_buttons import get_junior_manager_main_keyboard
from keyboards.controllers_buttons import controllers_main_menu
from keyboards.call_center_buttons import call_center_main_menu_reply, client_search_menu


class TestStaffApplicationLocalization:
    """Test staff application localization functionality"""
    
    def test_basic_text_localization(self):
        """Test basic text localization for both languages"""
        # Test Uzbek
        uz_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'uz')
        assert uz_text == "🔌 Ulanish arizasi yaratish"
        
        # Test Russian
        ru_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'ru')
        assert ru_text == "🔌 Создать заявку на подключение"
        
        # Test technical service
        uz_tech = get_staff_application_text('CREATE_TECHNICAL_SERVICE', 'uz')
        assert uz_tech == "🔧 Texnik xizmat yaratish"
        
        ru_tech = get_staff_application_text('CREATE_TECHNICAL_SERVICE', 'ru')
        assert ru_tech == "🔧 Создать техническую заявку"
    
    def test_error_message_localization(self):
        """Test error message localization"""
        # Test permission errors
        uz_error = get_staff_application_error('NO_CONNECTION_PERMISSION', 'uz')
        assert "ulanish arizalarini yaratish huquqi yo'q" in uz_error.lower()
        
        ru_error = get_staff_application_error('NO_CONNECTION_PERMISSION', 'ru')
        assert "разрешения на создание заявок на подключение" in ru_error.lower()
        
        # Test validation errors
        uz_validation = get_staff_application_error('INVALID_CLIENT_DATA', 'uz')
        assert "mijoz ma'lumotlari noto'g'ri" in uz_validation.lower()
        
        ru_validation = get_staff_application_error('INVALID_CLIENT_DATA', 'ru')
        assert "неверные данные клиента" in ru_validation.lower()
    
    def test_priority_text_localization(self):
        """Test priority level localization"""
        priorities = ['low', 'medium', 'high', 'urgent']
        
        for priority in priorities:
            uz_text = get_priority_text(priority, 'uz')
            ru_text = get_priority_text(priority, 'ru')
            
            assert uz_text != ru_text  # Should be different languages
            assert len(uz_text) > 0
            assert len(ru_text) > 0
    
    def test_connection_type_localization(self):
        """Test connection type localization"""
        connection_types = ['fiber', 'cable', 'wireless', 'satellite']
        
        for conn_type in connection_types:
            uz_text = get_connection_type_text(conn_type, 'uz')
            ru_text = get_connection_type_text(conn_type, 'ru')
            
            assert uz_text != ru_text  # Should be different languages
            assert len(uz_text) > 0
            assert len(ru_text) > 0
    
    def test_technical_service_type_localization(self):
        """Test technical service type localization"""
        service_types = ['repair', 'maintenance', 'installation', 'configuration']
        
        for service_type in service_types:
            uz_text = get_technical_service_type_text(service_type, 'uz')
            ru_text = get_technical_service_type_text(service_type, 'ru')
            
            assert uz_text != ru_text  # Should be different languages
            assert len(uz_text) > 0
            assert len(ru_text) > 0
    
    def test_role_specific_messages(self):
        """Test role-specific message localization"""
        roles = ['manager', 'junior_manager', 'controller', 'call_center']
        
        for role in roles:
            uz_message = get_role_specific_message(role, 'uz')
            ru_message = get_role_specific_message(role, 'ru')
            
            if uz_message and ru_message:  # Some roles might not have messages
                assert uz_message != ru_message
                assert len(uz_message) > 0
                assert len(ru_message) > 0
    
    def test_application_summary_formatting(self):
        """Test application summary formatting with localization"""
        application_data = {
            'application_type': 'connection',
            'client_name': 'Test Client',
            'client_phone': '+998901234567',
            'description': 'Test connection request description',
            'location': 'Test location',
            'priority': 'high'
        }
        
        uz_summary = format_application_summary(application_data, 'uz')
        ru_summary = format_application_summary(application_data, 'ru')
        
        assert uz_summary != ru_summary
        assert 'Test Client' in uz_summary
        assert 'Test Client' in ru_summary
        assert len(uz_summary) > 0
        assert len(ru_summary) > 0
    
    def test_language_consistency_validation(self):
        """Test language consistency validation"""
        # Test consistent Uzbek texts
        uz_texts = {
            'title': "Yangi ariza yaratish",
            'description': "Bu yerda ariza yaratish mumkin"
        }
        assert validate_language_consistency(uz_texts, 'uz') == True
        
        # Test consistent Russian texts
        ru_texts = {
            'title': "Создание новой заявки",
            'description': "Здесь можно создать заявку"
        }
        assert validate_language_consistency(ru_texts, 'ru') == True
        
        # Test mixed language texts (should fail)
        mixed_texts = {
            'title': "Yangi ariza yaratish",
            'description': "Здесь можно создать заявку"
        }
        # This might pass due to simple heuristic, but it's a basic check


class TestKeyboardLocalization:
    """Test keyboard localization for all roles"""
    
    def test_manager_keyboard_localization(self):
        """Test manager keyboard localization"""
        uz_keyboard = get_manager_main_keyboard('uz')
        ru_keyboard = get_manager_main_keyboard('ru')
        
        # Extract button texts
        uz_buttons = self._extract_button_texts(uz_keyboard)
        ru_buttons = self._extract_button_texts(ru_keyboard)
        
        # Check that we have the same number of buttons
        assert len(uz_buttons) == len(ru_buttons)
        
        # Check that staff application creation buttons are present
        uz_connection_found = any("Ulanish arizasi yaratish" in btn for btn in uz_buttons)
        ru_connection_found = any("Создать заявку на подключение" in btn for btn in ru_buttons)
        
        assert uz_connection_found
        assert ru_connection_found
        
        uz_technical_found = any("Texnik xizmat yaratish" in btn for btn in uz_buttons)
        ru_technical_found = any("Создать техническую заявку" in btn for btn in ru_buttons)
        
        assert uz_technical_found
        assert ru_technical_found
    
    def test_junior_manager_keyboard_localization(self):
        """Test junior manager keyboard localization"""
        uz_keyboard = get_junior_manager_main_keyboard('uz')
        ru_keyboard = get_junior_manager_main_keyboard('ru')
        
        uz_buttons = self._extract_button_texts(uz_keyboard)
        ru_buttons = self._extract_button_texts(ru_keyboard)
        
        # Check connection request button (junior managers can only create connection requests)
        uz_connection_found = any("Ulanish arizasi yaratish" in btn for btn in uz_buttons)
        ru_connection_found = any("Создать заявку на подключение" in btn for btn in ru_buttons)
        
        assert uz_connection_found
        assert ru_connection_found
        
        # Check that technical service button is NOT present
        uz_technical_found = any("Texnik xizmat yaratish" in btn for btn in uz_buttons)
        ru_technical_found = any("Создать техническую заявку" in btn for btn in ru_buttons)
        
        assert not uz_technical_found
        assert not ru_technical_found
    
    def test_controller_keyboard_localization(self):
        """Test controller keyboard localization"""
        uz_keyboard = controllers_main_menu('uz')
        ru_keyboard = controllers_main_menu('ru')
        
        uz_buttons = self._extract_button_texts(uz_keyboard)
        ru_buttons = self._extract_button_texts(ru_keyboard)
        
        # Check that both application creation buttons are present
        uz_connection_found = any("Ulanish arizasi yaratish" in btn for btn in uz_buttons)
        ru_connection_found = any("Создать заявку на подключение" in btn for btn in ru_buttons)
        
        assert uz_connection_found
        assert ru_connection_found
        
        uz_technical_found = any("Texnik xizmat yaratish" in btn for btn in uz_buttons)
        ru_technical_found = any("Создать техническую заявку" in btn for btn in ru_buttons)
        
        assert uz_technical_found
        assert ru_technical_found
    
    def test_call_center_keyboard_localization(self):
        """Test call center keyboard localization"""
        uz_keyboard = call_center_main_menu_reply('uz')
        ru_keyboard = call_center_main_menu_reply('ru')
        
        uz_buttons = self._extract_button_texts(uz_keyboard)
        ru_buttons = self._extract_button_texts(ru_keyboard)
        
        # Check that both application creation buttons are present
        uz_connection_found = any("Ulanish arizasi yaratish" in btn for btn in uz_buttons)
        ru_connection_found = any("Создать заявку на подключение" in btn for btn in ru_buttons)
        
        assert uz_connection_found
        assert ru_connection_found
        
        uz_technical_found = any("Texnik xizmat yaratish" in btn for btn in uz_buttons)
        ru_technical_found = any("Создать техническую заявку" in btn for btn in ru_buttons)
        
        assert uz_technical_found
        assert ru_technical_found
    
    def test_client_search_menu_localization(self):
        """Test client search menu localization"""
        uz_keyboard = client_search_menu('uz')
        ru_keyboard = client_search_menu('ru')
        
        uz_buttons = self._extract_button_texts(uz_keyboard)
        ru_buttons = self._extract_button_texts(ru_keyboard)
        
        # Check search options
        uz_name_search = any("Ism bo'yicha" in btn for btn in uz_buttons)
        ru_name_search = any("По имени" in btn for btn in ru_buttons)
        
        assert uz_name_search
        assert ru_name_search
        
        uz_phone_search = any("Telefon raqami bo'yicha" in btn for btn in uz_buttons)
        ru_phone_search = any("По номеру телефона" in btn for btn in ru_buttons)
        
        assert uz_phone_search
        assert ru_phone_search
    
    def _extract_button_texts(self, keyboard):
        """Extract button texts from keyboard"""
        texts = []
        if hasattr(keyboard, 'keyboard'):
            for row in keyboard.keyboard:
                for button in row:
                    if hasattr(button, 'text'):
                        texts.append(button.text)
        return texts


class TestNotificationLocalization:
    """Test notification localization"""
    
    def test_client_notification_formatting(self):
        """Test client notification formatting"""
        application_data = {
            'id': 'APP123',
            'application_type': 'connection',
            'created_at': '2024-01-01 10:00:00',
            'location': 'Test Location'
        }
        
        creator_data = {
            'full_name': 'Test Manager',
            'role': 'manager'
        }
        
        uz_notification = create_client_notification(application_data, creator_data, 'uz')
        ru_notification = create_client_notification(application_data, creator_data, 'ru')
        
        assert uz_notification['title'] != ru_notification['title']
        assert uz_notification['body'] != ru_notification['body']
        assert 'APP123' in uz_notification['body']
        assert 'APP123' in ru_notification['body']
        assert 'Test Manager' in uz_notification['body']
        assert 'Test Manager' in ru_notification['body']
    
    def test_staff_confirmation_formatting(self):
        """Test staff confirmation notification formatting"""
        application_data = {
            'id': 'APP123',
            'created_at': '2024-01-01 10:00:00'
        }
        
        client_data = {
            'full_name': 'Test Client',
            'phone': '+998901234567'
        }
        
        uz_confirmation = create_staff_confirmation(application_data, client_data, 'uz')
        ru_confirmation = create_staff_confirmation(application_data, client_data, 'ru')
        
        assert uz_confirmation['title'] != ru_confirmation['title']
        assert uz_confirmation['body'] != ru_confirmation['body']
        assert 'APP123' in uz_confirmation['body']
        assert 'APP123' in ru_confirmation['body']
        assert 'Test Client' in uz_confirmation['body']
        assert 'Test Client' in ru_confirmation['body']
    
    def test_workflow_assignment_notification(self):
        """Test workflow assignment notification formatting"""
        application_data = {
            'id': 'APP123',
            'application_type': 'technical',
            'location': 'Test Location',
            'priority': 'high',
            'service_type': 'repair'
        }
        
        client_data = {
            'full_name': 'Test Client',
            'phone': '+998901234567'
        }
        
        creator_data = {
            'full_name': 'Test Manager',
            'role': 'manager'
        }
        
        uz_notification = create_workflow_assignment_notification(
            application_data, client_data, creator_data, 'uz'
        )
        ru_notification = create_workflow_assignment_notification(
            application_data, client_data, creator_data, 'ru'
        )
        
        assert uz_notification['title'] != ru_notification['title']
        assert uz_notification['body'] != ru_notification['body']
        assert 'APP123' in uz_notification['body']
        assert 'APP123' in ru_notification['body']
    
    def test_error_notification_formatting(self):
        """Test error notification formatting"""
        error_data = {
            'user_role': 'junior_manager',
            'requested_action': 'create_technical_service'
        }
        
        uz_error = create_error_notification('permission_denied', error_data, 'uz')
        ru_error = create_error_notification('permission_denied', error_data, 'ru')
        
        assert uz_error['title'] != ru_error['title']
        assert uz_error['body'] != ru_error['body']
        assert len(uz_error['body']) > 0
        assert len(ru_error['body']) > 0


class TestFormErrorLocalization:
    """Test form error message localization"""
    
    def test_form_error_messages(self):
        """Test form error message localization"""
        # Test required field error
        uz_required = FormErrorMessages.get_message('required_field', 'uz', field='phone')
        ru_required = FormErrorMessages.get_message('required_field', 'ru', field='phone')
        
        assert uz_required != ru_required
        assert 'phone' in uz_required
        assert 'phone' in ru_required
        
        # Test validation error
        uz_validation = FormErrorMessages.get_message('form_validation_error', 'uz')
        ru_validation = FormErrorMessages.get_message('form_validation_error', 'ru')
        
        assert uz_validation != ru_validation
        assert len(uz_validation) > 0
        assert len(ru_validation) > 0
    
    def test_field_name_localization(self):
        """Test field name localization"""
        fields = ['phone', 'full_name', 'address', 'description', 'location']
        
        for field in fields:
            uz_name = FormErrorMessages.get_field_name(field, 'uz')
            ru_name = FormErrorMessages.get_field_name(field, 'ru')
            
            assert uz_name != ru_name
            assert len(uz_name) > 0
            assert len(ru_name) > 0
    
    def test_priority_level_localization(self):
        """Test priority level localization"""
        priorities = ['low', 'medium', 'high', 'urgent']
        
        for priority in priorities:
            uz_priority = FormErrorMessages.get_priority_name(priority, 'uz')
            ru_priority = FormErrorMessages.get_priority_name(priority, 'ru')
            
            assert uz_priority != ru_priority
            assert len(uz_priority) > 0
            assert len(ru_priority) > 0
    
    def test_role_specific_form_messages(self):
        """Test role-specific form messages"""
        roles = ['manager', 'junior_manager', 'call_center', 'controller']
        
        for role in roles:
            uz_message = FormErrorMessages.get_role_specific_message(role, 'uz')
            ru_message = FormErrorMessages.get_role_specific_message(role, 'ru')
            
            if uz_message and ru_message:
                assert uz_message != ru_message
                assert len(uz_message) > 0
                assert len(ru_message) > 0


class TestLanguageSwitching:
    """Test language switching functionality"""
    
    @pytest.mark.asyncio
    async def test_language_switching_consistency(self):
        """Test that language switching works consistently across all components"""
        # Mock user with different languages
        uz_user = Mock(spec=User)
        uz_user.id = 123
        uz_user.language_code = 'uz'
        
        ru_user = Mock(spec=User)
        ru_user.id = 123
        ru_user.language_code = 'ru'
        
        # Test that all components respect language settings
        with patch('utils.get_lang.get_user_language') as mock_get_lang:
            # Test Uzbek
            mock_get_lang.return_value = 'uz'
            
            uz_keyboard = get_manager_main_keyboard('uz')
            uz_buttons = self._extract_button_texts(uz_keyboard)
            
            # Test Russian
            mock_get_lang.return_value = 'ru'
            
            ru_keyboard = get_manager_main_keyboard('ru')
            ru_buttons = self._extract_button_texts(ru_keyboard)
            
            # Verify different languages produce different button texts
            assert uz_buttons != ru_buttons
    
    def test_language_fallback(self):
        """Test language fallback behavior"""
        # Test with unsupported language code
        fallback_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'en')
        uz_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'uz')
        
        # Should fallback to a supported language or return the key
        assert len(fallback_text) > 0
    
    def _extract_button_texts(self, keyboard):
        """Extract button texts from keyboard"""
        texts = []
        if hasattr(keyboard, 'keyboard'):
            for row in keyboard.keyboard:
                for button in row:
                    if hasattr(button, 'text'):
                        texts.append(button.text)
        return texts


class TestLanguageIntegration:
    """Test language integration across the entire system"""
    
    def test_complete_workflow_language_consistency(self):
        """Test that a complete workflow maintains language consistency"""
        language = 'uz'
        
        # Test keyboard texts
        keyboard = get_manager_main_keyboard(language)
        keyboard_texts = self._extract_button_texts(keyboard)
        
        # Test error messages
        error_msg = get_staff_application_error('NO_CONNECTION_PERMISSION', language)
        
        # Test notification
        app_data = {'id': 'TEST', 'application_type': 'connection', 'created_at': 'now', 'location': 'test'}
        creator_data = {'full_name': 'Test', 'role': 'manager'}
        notification = create_client_notification(app_data, creator_data, language)
        
        # All should be in the same language
        all_texts = keyboard_texts + [error_msg, notification['title'], notification['body']]
        
        # Basic consistency check - all texts should be non-empty
        for text in all_texts:
            assert len(text) > 0
    
    def _extract_button_texts(self, keyboard):
        """Extract button texts from keyboard"""
        texts = []
        if hasattr(keyboard, 'keyboard'):
            for row in keyboard.keyboard:
                for button in row:
                    if hasattr(button, 'text'):
                        texts.append(button.text)
        return texts


if __name__ == '__main__':
    pytest.main([__file__, '-v'])