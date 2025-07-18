"""
Integration test for language switching functionality across all staff roles.

This test verifies that language switching works consistently across all
components of the staff application creation system.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from aiogram.types import User, Message, CallbackQuery
from utils.get_lang import get_user_language, get_language_from_message
from utils.staff_application_localization import (
    get_staff_application_text, get_staff_application_error,
    format_application_summary, get_role_specific_message
)
from utils.staff_notification_localization import (
    create_client_notification, create_staff_confirmation
)
from keyboards.manager_buttons import get_manager_main_keyboard
from keyboards.junior_manager_buttons import get_junior_manager_main_keyboard
from keyboards.controllers_buttons import controllers_main_menu
from keyboards.call_center_buttons import call_center_main_menu_reply


class TestLanguageSwitchingIntegration:
    """Test language switching integration across all components"""
    
    @pytest.mark.asyncio
    async def test_user_language_detection(self):
        """Test user language detection from different sources"""
        # Test with Telegram user object
        uz_user = Mock(spec=User)
        uz_user.id = 123
        uz_user.language_code = 'uz'
        
        ru_user = Mock(spec=User)
        ru_user.id = 456
        ru_user.language_code = 'ru'
        
        with patch('database.base_queries.get_user_by_telegram_id') as mock_get_user:
            # Mock database response
            mock_get_user.return_value = {'language': 'uz'}
            
            # Test Uzbek user
            uz_lang = await get_user_language(uz_user)
            assert uz_lang == 'uz'
            
            # Test Russian user
            mock_get_user.return_value = {'language': 'ru'}
            ru_lang = await get_user_language(ru_user)
            assert ru_lang == 'ru'
    
    @pytest.mark.asyncio
    async def test_message_language_detection(self):
        """Test language detection from message objects"""
        # Mock message with Uzbek user
        uz_message = Mock(spec=Message)
        uz_message.from_user = Mock(spec=User)
        uz_message.from_user.id = 123
        uz_message.from_user.language_code = 'uz'
        
        # Mock message with Russian user
        ru_message = Mock(spec=Message)
        ru_message.from_user = Mock(spec=User)
        ru_message.from_user.id = 456
        ru_message.from_user.language_code = 'ru'
        
        with patch('utils.get_lang.get_user_language') as mock_get_lang:
            mock_get_lang.return_value = 'uz'
            uz_lang = await get_language_from_message(uz_message)
            assert uz_lang == 'uz'
            
            mock_get_lang.return_value = 'ru'
            ru_lang = await get_language_from_message(ru_message)
            assert ru_lang == 'ru'
    
    def test_keyboard_language_consistency(self):
        """Test that all keyboards maintain language consistency"""
        languages = ['uz', 'ru']
        
        for lang in languages:
            # Test all role keyboards
            manager_kb = get_manager_main_keyboard(lang)
            junior_kb = get_junior_manager_main_keyboard(lang)
            controller_kb = controllers_main_menu(lang)
            call_center_kb = call_center_main_menu_reply(lang)
            
            # Extract button texts
            manager_texts = self._extract_button_texts(manager_kb)
            junior_texts = self._extract_button_texts(junior_kb)
            controller_texts = self._extract_button_texts(controller_kb)
            call_center_texts = self._extract_button_texts(call_center_kb)
            
            # Verify all keyboards have buttons
            assert len(manager_texts) > 0
            assert len(junior_texts) > 0
            assert len(controller_texts) > 0
            assert len(call_center_texts) > 0
            
            # Verify staff application creation buttons are present where expected
            connection_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', lang)
            technical_text = get_staff_application_text('CREATE_TECHNICAL_SERVICE', lang)
            
            # Manager should have both buttons
            assert any(connection_text in btn for btn in manager_texts)
            assert any(technical_text in btn for btn in manager_texts)
            
            # Junior manager should only have connection button
            assert any(connection_text in btn for btn in junior_texts)
            assert not any(technical_text in btn for btn in junior_texts)
            
            # Controller should have both buttons
            assert any(connection_text in btn for btn in controller_texts)
            assert any(technical_text in btn for btn in controller_texts)
            
            # Call center should have both buttons
            assert any(connection_text in btn for btn in call_center_texts)
            assert any(technical_text in btn for btn in call_center_texts)
    
    def test_error_message_language_consistency(self):
        """Test error message language consistency"""
        languages = ['uz', 'ru']
        error_keys = [
            'NO_CONNECTION_PERMISSION',
            'NO_TECHNICAL_PERMISSION',
            'INVALID_CLIENT_DATA',
            'DATABASE_ERROR'
        ]
        
        for lang in languages:
            for error_key in error_keys:
                error_msg = get_staff_application_error(error_key, lang)
                assert len(error_msg) > 0
                
                # Basic language consistency check
                if lang == 'uz':
                    # Uzbek text should not contain Cyrillic characters
                    cyrillic_count = sum(1 for c in error_msg if '\u0400' <= c <= '\u04FF')
                    total_letters = sum(1 for c in error_msg if c.isalpha())
                    if total_letters > 0:
                        cyrillic_ratio = cyrillic_count / total_letters
                        assert cyrillic_ratio < 0.5  # Should be mostly Latin
                elif lang == 'ru':
                    # Russian text should contain some Cyrillic characters
                    cyrillic_count = sum(1 for c in error_msg if '\u0400' <= c <= '\u04FF')
                    if any(c.isalpha() for c in error_msg):
                        assert cyrillic_count > 0  # Should contain Cyrillic
    
    def test_notification_language_consistency(self):
        """Test notification language consistency"""
        languages = ['uz', 'ru']
        
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
        
        client_data = {
            'full_name': 'Test Client',
            'phone': '+998901234567'
        }
        
        for lang in languages:
            # Test client notification
            client_notif = create_client_notification(application_data, creator_data, lang)
            assert len(client_notif['title']) > 0
            assert len(client_notif['body']) > 0
            assert 'APP123' in client_notif['body']
            
            # Test staff confirmation
            staff_confirm = create_staff_confirmation(application_data, client_data, lang)
            assert len(staff_confirm['title']) > 0
            assert len(staff_confirm['body']) > 0
            assert 'APP123' in staff_confirm['body']
    
    def test_role_specific_message_consistency(self):
        """Test role-specific message consistency"""
        languages = ['uz', 'ru']
        roles = ['manager', 'junior_manager', 'controller', 'call_center']
        
        for lang in languages:
            for role in roles:
                role_msg = get_role_specific_message(role, lang)
                if role_msg:  # Some roles might not have specific messages
                    assert len(role_msg) > 0
                    
                    # Verify message contains role-relevant information
                    if role == 'junior_manager':
                        # Junior manager message should mention limitation
                        if lang == 'uz':
                            assert 'faqat' in role_msg.lower() or 'ulanish' in role_msg.lower()
                        else:
                            assert 'только' in role_msg.lower() or 'подключение' in role_msg.lower()
    
    def test_application_summary_language_consistency(self):
        """Test application summary formatting consistency"""
        languages = ['uz', 'ru']
        
        application_data = {
            'application_type': 'technical',
            'client_name': 'Test Client',
            'client_phone': '+998901234567',
            'description': 'Test technical service description',
            'location': 'Test location address',
            'priority': 'urgent'
        }
        
        for lang in languages:
            summary = format_application_summary(application_data, lang)
            assert len(summary) > 0
            assert 'Test Client' in summary
            assert '+998901234567' in summary
            
            # Check that priority is localized
            if lang == 'uz':
                assert 'Shoshilinch' in summary
            else:
                assert 'Срочный' in summary
    
    def test_cross_component_language_switching(self):
        """Test language switching across different components"""
        # Test switching from Uzbek to Russian
        uz_connection_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'uz')
        ru_connection_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'ru')
        
        assert uz_connection_text != ru_connection_text
        assert 'Ulanish' in uz_connection_text
        assert 'подключение' in ru_connection_text.lower()
        
        # Test error messages
        uz_error = get_staff_application_error('NO_CONNECTION_PERMISSION', 'uz')
        ru_error = get_staff_application_error('NO_CONNECTION_PERMISSION', 'ru')
        
        assert uz_error != ru_error
        assert len(uz_error) > 0
        assert len(ru_error) > 0
        
        # Test keyboards
        uz_keyboard = get_manager_main_keyboard('uz')
        ru_keyboard = get_manager_main_keyboard('ru')
        
        uz_buttons = self._extract_button_texts(uz_keyboard)
        ru_buttons = self._extract_button_texts(ru_keyboard)
        
        assert uz_buttons != ru_buttons
        assert len(uz_buttons) == len(ru_buttons)  # Same number of buttons
    
    def test_language_fallback_behavior(self):
        """Test language fallback behavior for unsupported languages"""
        # Test with unsupported language
        fallback_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'fr')
        uz_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'uz')
        ru_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', 'ru')
        
        # Fallback should return either the key or one of the supported languages
        assert len(fallback_text) > 0
        assert fallback_text in [uz_text, ru_text, 'CREATE_CONNECTION_REQUEST']
    
    def test_special_characters_handling(self):
        """Test handling of special characters in different languages"""
        languages = ['uz', 'ru']
        
        for lang in languages:
            # Test texts with special characters
            connection_text = get_staff_application_text('CREATE_CONNECTION_REQUEST', lang)
            technical_text = get_staff_application_text('CREATE_TECHNICAL_SERVICE', lang)
            
            # Should handle Unicode characters properly
            assert len(connection_text.encode('utf-8')) >= len(connection_text)
            assert len(technical_text.encode('utf-8')) >= len(technical_text)
            
            # Should not contain broken encoding
            assert '�' not in connection_text
            assert '�' not in technical_text
    
    def test_language_switching_performance(self):
        """Test that language switching doesn't cause performance issues"""
        import time
        
        languages = ['uz', 'ru']
        text_keys = [
            'CREATE_CONNECTION_REQUEST',
            'CREATE_TECHNICAL_SERVICE',
            'SELECT_CLIENT',
            'APPLICATION_CREATED_SUCCESS'
        ]
        
        start_time = time.time()
        
        # Perform multiple language switches
        for _ in range(100):
            for lang in languages:
                for key in text_keys:
                    get_staff_application_text(key, lang)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (less than 1 second)
        assert duration < 1.0
    
    def _extract_button_texts(self, keyboard):
        """Extract button texts from keyboard"""
        texts = []
        if hasattr(keyboard, 'keyboard'):
            for row in keyboard.keyboard:
                for button in row:
                    if hasattr(button, 'text'):
                        texts.append(button.text)
        return texts


class TestLanguageConsistencyValidation:
    """Test language consistency validation across the system"""
    
    def test_all_staff_roles_have_consistent_buttons(self):
        """Test that all staff roles have consistent button localization"""
        languages = ['uz', 'ru']
        
        for lang in languages:
            # Get keyboards for all roles
            keyboards = {
                'manager': get_manager_main_keyboard(lang),
                'junior_manager': get_junior_manager_main_keyboard(lang),
                'controller': controllers_main_menu(lang),
                'call_center': call_center_main_menu_reply(lang)
            }
            
            # Extract all button texts
            all_texts = []
            for role, keyboard in keyboards.items():
                texts = self._extract_button_texts(keyboard)
                all_texts.extend(texts)
            
            # Verify no empty texts
            for text in all_texts:
                assert len(text.strip()) > 0
            
            # Basic language consistency check
            if lang == 'uz':
                # Should contain mostly Latin characters for Uzbek
                latin_texts = [t for t in all_texts if any(c.isalpha() and ord(c) < 256 for c in t)]
                assert len(latin_texts) > 0
            elif lang == 'ru':
                # Should contain some Cyrillic characters for Russian
                cyrillic_texts = [t for t in all_texts if any('\u0400' <= c <= '\u04FF' for c in t)]
                assert len(cyrillic_texts) > 0
    
    def test_error_messages_completeness(self):
        """Test that all error messages are available in both languages"""
        error_keys = [
            'NO_CONNECTION_PERMISSION',
            'NO_TECHNICAL_PERMISSION',
            'NO_CLIENT_SELECTION_PERMISSION',
            'INVALID_CLIENT_DATA',
            'DATABASE_ERROR',
            'WORKFLOW_ERROR'
        ]
        
        languages = ['uz', 'ru']
        
        for error_key in error_keys:
            for lang in languages:
                error_msg = get_staff_application_error(error_key, lang)
                assert len(error_msg) > 0
                assert error_msg != error_key  # Should be localized, not just return the key
    
    def test_notification_templates_completeness(self):
        """Test that all notification templates are complete in both languages"""
        languages = ['uz', 'ru']
        
        # Test data
        app_data = {'id': 'TEST', 'application_type': 'connection', 'created_at': 'now', 'location': 'test'}
        creator_data = {'full_name': 'Creator', 'role': 'manager'}
        client_data = {'full_name': 'Client', 'phone': '123456789'}
        
        for lang in languages:
            # Test client notification
            client_notif = create_client_notification(app_data, creator_data, lang)
            assert 'title' in client_notif
            assert 'body' in client_notif
            assert len(client_notif['title']) > 0
            assert len(client_notif['body']) > 0
            
            # Test staff confirmation
            staff_confirm = create_staff_confirmation(app_data, client_data, lang)
            assert 'title' in staff_confirm
            assert 'body' in staff_confirm
            assert len(staff_confirm['title']) > 0
            assert len(staff_confirm['body']) > 0
    
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