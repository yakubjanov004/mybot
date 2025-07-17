"""
Integration test for staff notification system
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from utils.notification_system import NotificationSystem


class TestStaffNotificationIntegration:
    """Integration tests for staff notification system"""
    
    def test_notification_templates_structure(self):
        """Test that notification templates have correct structure"""
        notification_system = NotificationSystem()
        templates = notification_system.staff_notification_templates
        
        # Test template categories
        assert 'client_notification' in templates
        assert 'staff_confirmation' in templates
        assert 'workflow_participant' in templates
        
        # Test languages
        for category in templates.values():
            assert 'uz' in category
            assert 'ru' in category
        
        # Test application types
        for category in templates.values():
            for lang in category.values():
                assert 'connection_request' in lang
                assert 'technical_service' in lang
        
        # Test template fields
        for category in templates.values():
            for lang in category.values():
                for app_type in lang.values():
                    assert 'title' in app_type
                    assert 'body' in app_type
                    assert 'button' in app_type
                    
                    # Test that templates contain placeholders
                    assert '{client_name}' in app_type['body']
                    assert '{description}' in app_type['body']
                    assert '{request_id}' in app_type['body']
    
    def test_creator_role_formatting(self):
        """Test creator role formatting for different languages"""
        notification_system = NotificationSystem()
        
        # Test Uzbek formatting
        assert notification_system._format_creator_role('manager', 'uz') == 'Menejer'
        assert notification_system._format_creator_role('junior_manager', 'uz') == 'Kichik menejer'
        assert notification_system._format_creator_role('controller', 'uz') == 'Nazoratchi'
        assert notification_system._format_creator_role('call_center', 'uz') == 'Call-markaz operatori'
        
        # Test Russian formatting
        assert notification_system._format_creator_role('manager', 'ru') == 'Менеджер'
        assert notification_system._format_creator_role('junior_manager', 'ru') == 'Младший менеджер'
        assert notification_system._format_creator_role('controller', 'ru') == 'Контроллер'
        assert notification_system._format_creator_role('call_center', 'ru') == 'Оператор call-центра'
        
        # Test unknown role fallback
        assert notification_system._format_creator_role('unknown_role', 'uz') == 'unknown_role'
        assert notification_system._format_creator_role('unknown_role', 'ru') == 'unknown_role'
    
    def test_template_content_uzbek(self):
        """Test Uzbek template content"""
        notification_system = NotificationSystem()
        templates = notification_system.staff_notification_templates
        
        # Test client notification template
        client_template = templates['client_notification']['uz']['connection_request']
        assert 'Sizning nomingizdan ariza yaratildi' in client_template['title']
        assert 'Hurmatli {client_name}' in client_template['body']
        assert 'Yaratuvchi: {creator_role}' in client_template['body']
        assert 'Ariza ID: {request_id}' in client_template['body']
        
        # Test staff confirmation template
        staff_template = templates['staff_confirmation']['uz']['technical_service']
        assert 'muvaffaqiyatli yaratildi' in staff_template['title']
        assert 'Mijoz: {client_name}' in staff_template['body']
        assert 'Ariza ID: {request_id}' in staff_template['body']
        
        # Test workflow participant template
        workflow_template = templates['workflow_participant']['uz']['connection_request']
        assert 'Xodim tomonidan yaratilgan' in workflow_template['title']
        assert 'Yaratuvchi: {creator_role}' in workflow_template['body']
        assert 'Mijoz: {client_name}' in workflow_template['body']
    
    def test_template_content_russian(self):
        """Test Russian template content"""
        notification_system = NotificationSystem()
        templates = notification_system.staff_notification_templates
        
        # Test client notification template
        client_template = templates['client_notification']['ru']['technical_service']
        assert 'создана от вашего имени' in client_template['title']
        assert 'Уважаемый(ая) {client_name}' in client_template['body']
        assert 'Создатель: {creator_role}' in client_template['body']
        assert 'ID заявки: {request_id}' in client_template['body']
        
        # Test staff confirmation template
        staff_template = templates['staff_confirmation']['ru']['connection_request']
        assert 'успешно создана' in staff_template['title']
        assert 'Клиент: {client_name}' in staff_template['body']
        assert 'ID заявки: {request_id}' in staff_template['body']
        
        # Test workflow participant template
        workflow_template = templates['workflow_participant']['ru']['technical_service']
        assert 'создана сотрудником' in workflow_template['title']
        assert 'Создатель: {creator_role}' in workflow_template['body']
        assert 'Клиент: {client_name}' in workflow_template['body']
    
    def test_excluded_roles_handling(self):
        """Test that excluded roles are properly handled"""
        notification_system = NotificationSystem()
        
        # Test excluded roles
        assert 'client' in notification_system.excluded_roles
        assert 'admin' in notification_system.excluded_roles
        
        # Test that excluded roles return True without processing
        # (This would be tested in actual async methods, but we can verify the logic)
        assert len(notification_system.excluded_roles) == 2
    
    @pytest.mark.asyncio
    async def test_notification_id_generation(self):
        """Test notification ID generation"""
        notification_system = NotificationSystem()
        
        # Generate multiple IDs
        id1 = notification_system._generate_notification_id()
        id2 = notification_system._generate_notification_id()
        id3 = notification_system._generate_notification_id()
        
        # Verify they are unique
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3
        
        # Verify they are valid UUIDs (basic check)
        assert len(id1) == 36  # UUID string length
        assert '-' in id1
        assert len(id2) == 36
        assert '-' in id2
    
    def test_template_placeholder_consistency(self):
        """Test that all templates use consistent placeholders"""
        notification_system = NotificationSystem()
        templates = notification_system.staff_notification_templates
        
        required_placeholders = {
            'client_notification': ['{client_name}', '{description}', '{location}', '{creator_role}', '{request_id}'],
            'staff_confirmation': ['{client_name}', '{description}', '{location}', '{request_id}'],
            'workflow_participant': ['{client_name}', '{description}', '{location}', '{creator_role}', '{request_id}']
        }
        
        for category_name, category_templates in templates.items():
            expected_placeholders = required_placeholders[category_name]
            
            for lang in category_templates.values():
                for app_type in lang.values():
                    body = app_type['body']
                    
                    # Check that all required placeholders are present
                    for placeholder in expected_placeholders:
                        assert placeholder in body, f"Missing {placeholder} in {category_name} template"
    
    def test_notification_system_initialization(self):
        """Test notification system initialization"""
        # Test with no pool
        ns1 = NotificationSystem()
        assert ns1.pool is None
        assert hasattr(ns1, 'staff_notification_templates')
        assert hasattr(ns1, 'excluded_roles')
        
        # Test with mock pool
        mock_pool = AsyncMock()
        ns2 = NotificationSystem(pool=mock_pool)
        assert ns2.pool is mock_pool
        assert hasattr(ns2, 'staff_notification_templates')
        assert hasattr(ns2, 'excluded_roles')


if __name__ == '__main__':
    pytest.main([__file__])