"""
Test client search and selection UI functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from keyboards.client_search_buttons import (
    get_client_search_method_keyboard,
    get_client_selection_keyboard,
    get_client_confirmation_keyboard,
    get_new_client_form_keyboard,
    format_client_display_text,
    get_search_prompt_text
)
from utils.client_selection import (
    ClientValidator,
    ClientSearchEngine,
    ClientManager,
    ClientSearchResult
)
from database.models import ClientSelectionData


class TestClientSearchKeyboards:
    """Test client search keyboard generation"""
    
    def test_get_client_search_method_keyboard_uz(self):
        """Test search method keyboard in Uzbek"""
        keyboard = get_client_search_method_keyboard('uz')
        
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 5  # 4 search methods + back button
        
        # Check button texts
        buttons_text = [button[0].text for button in keyboard.inline_keyboard]
        assert "📞 Telefon raqami bo'yicha" in buttons_text
        assert "👤 Ism bo'yicha" in buttons_text
        assert "🆔 ID raqami bo'yicha" in buttons_text
        assert "➕ Yangi mijoz yaratish" in buttons_text
        assert "◀️ Orqaga" in buttons_text
    
    def test_get_client_search_method_keyboard_ru(self):
        """Test search method keyboard in Russian"""
        keyboard = get_client_search_method_keyboard('ru')
        
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 5
        
        # Check button texts
        buttons_text = [button[0].text for button in keyboard.inline_keyboard]
        assert "📞 По номеру телефона" in buttons_text
        assert "👤 По имени" in buttons_text
        assert "🆔 По ID" in buttons_text
        assert "➕ Создать нового клиента" in buttons_text
        assert "◀️ Назад" in buttons_text
    
    def test_get_client_selection_keyboard(self):
        """Test client selection keyboard with multiple clients"""
        clients = [
            {
                'id': 1,
                'full_name': 'John Doe',
                'phone_number': '+998901234567'
            },
            {
                'id': 2,
                'full_name': 'Jane Smith',
                'phone_number': '+998907654321'
            }
        ]
        
        keyboard = get_client_selection_keyboard(clients, 'uz')
        
        assert keyboard is not None
        # Should have 2 client buttons + 3 control buttons
        assert len(keyboard.inline_keyboard) >= 5
        
        # Check that client buttons are present
        buttons_text = [button[0].text for button in keyboard.inline_keyboard[:2]]
        assert any("John Doe" in text for text in buttons_text)
        assert any("Jane Smith" in text for text in buttons_text)
    
    def test_format_client_display_text_uz(self):
        """Test client display text formatting in Uzbek"""
        client_data = {
            'full_name': 'Test User',
            'phone_number': '+998901234567',
            'id': 123,
            'address': 'Test Address',
            'language': 'uz'
        }
        
        text = format_client_display_text(client_data, 'uz')
        
        assert "👤 **Mijoz ma'lumotlari:**" in text
        assert "Test User" in text
        assert "+998901234567" in text
        assert "123" in text
        assert "Test Address" in text
        assert "O'zbek" in text
    
    def test_format_client_display_text_ru(self):
        """Test client display text formatting in Russian"""
        client_data = {
            'full_name': 'Test User',
            'phone_number': '+998901234567',
            'id': 123,
            'language': 'ru'
        }
        
        text = format_client_display_text(client_data, 'ru')
        
        assert "👤 **Данные клиента:**" in text
        assert "Test User" in text
        assert "+998901234567" in text
        assert "123" in text
        assert "Русский" in text
    
    def test_get_search_prompt_text(self):
        """Test search prompt text generation"""
        phone_prompt_uz = get_search_prompt_text('phone', 'uz')
        assert "📞 **Mijoz telefon raqamini kiriting:**" in phone_prompt_uz
        assert "+998901234567" in phone_prompt_uz
        
        name_prompt_ru = get_search_prompt_text('name', 'ru')
        assert "👤 **Введите имя клиента:**" in name_prompt_ru
        
        id_prompt_uz = get_search_prompt_text('id', 'uz')
        assert "🆔 **Mijoz ID raqamini kiriting:**" in id_prompt_uz


class TestClientValidator:
    """Test client data validation"""
    
    def test_validate_phone_number_valid(self):
        """Test valid phone number validation"""
        validator = ClientValidator()
        
        # Valid formats
        assert validator.validate_phone_number("+998901234567")
        assert validator.validate_phone_number("998901234567")
        assert validator.validate_phone_number("901234567")
    
    def test_validate_phone_number_invalid(self):
        """Test invalid phone number validation"""
        validator = ClientValidator()
        
        # Invalid formats
        assert not validator.validate_phone_number("")
        assert not validator.validate_phone_number("123")
        assert not validator.validate_phone_number("+1234567890")
        assert not validator.validate_phone_number("abc123")
    
    def test_normalize_phone_number(self):
        """Test phone number normalization"""
        validator = ClientValidator()
        
        assert validator.normalize_phone_number("901234567") == "+998901234567"
        assert validator.normalize_phone_number("998901234567") == "+998901234567"
        assert validator.normalize_phone_number("+998901234567") == "+998901234567"
    
    def test_validate_full_name_valid(self):
        """Test valid full name validation"""
        validator = ClientValidator()
        
        assert validator.validate_full_name("John Doe")
        assert validator.validate_full_name("Алексей Иванов")
        assert validator.validate_full_name("Ahmad Karimov")
        assert validator.validate_full_name("O'tkir Rahimov")
    
    def test_validate_full_name_invalid(self):
        """Test invalid full name validation"""
        validator = ClientValidator()
        
        assert not validator.validate_full_name("")
        assert not validator.validate_full_name("A")
        assert not validator.validate_full_name("123")
        assert not validator.validate_full_name("John@Doe")
        assert not validator.validate_full_name("A" * 101)  # Too long
    
    def test_validate_client_data(self):
        """Test complete client data validation"""
        validator = ClientValidator()
        
        # Valid data
        valid_data = {
            'full_name': 'John Doe',
            'phone_number': '+998901234567',
            'language': 'uz',
            'address': 'Test Address'
        }
        errors = validator.validate_client_data(valid_data)
        assert len(errors) == 0
        
        # Invalid data
        invalid_data = {
            'full_name': 'A',  # Too short
            'phone_number': '123',  # Invalid format
            'language': 'invalid',  # Invalid language
            'address': 'A' * 501  # Too long
        }
        errors = validator.validate_client_data(invalid_data)
        assert len(errors) > 0


class TestClientSearchEngine:
    """Test client search functionality"""
    
    @pytest.mark.asyncio
    async def test_search_by_phone_success(self):
        """Test successful phone search"""
        with patch('utils.client_selection.bot') as mock_bot:
            # Mock database connection and results
            mock_conn = AsyncMock()
            mock_bot.db.acquire.return_value.__aenter__.return_value = mock_conn
            mock_conn.fetch.return_value = [
                {
                    'id': 1,
                    'full_name': 'Test User',
                    'phone_number': '+998901234567',
                    'role': 'client',
                    'language': 'uz'
                }
            ]
            
            search_engine = ClientSearchEngine()
            result = await search_engine.search_by_phone("+998901234567")
            
            assert result.found is True
            assert result.client is not None
            assert result.client['full_name'] == 'Test User'
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_search_by_phone_not_found(self):
        """Test phone search with no results"""
        with patch('utils.client_selection.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_bot.db.acquire.return_value.__aenter__.return_value = mock_conn
            mock_conn.fetch.return_value = []
            
            search_engine = ClientSearchEngine()
            result = await search_engine.search_by_phone("+998901234567")
            
            assert result.found is False
            assert result.client is None
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_search_by_phone_multiple_results(self):
        """Test phone search with multiple results"""
        with patch('utils.client_selection.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_bot.db.acquire.return_value.__aenter__.return_value = mock_conn
            mock_conn.fetch.return_value = [
                {'id': 1, 'full_name': 'User 1', 'phone_number': '+998901234567'},
                {'id': 2, 'full_name': 'User 2', 'phone_number': '+998901234567'}
            ]
            
            search_engine = ClientSearchEngine()
            result = await search_engine.search_by_phone("+998901234567")
            
            assert result.found is True
            assert result.multiple_matches is not None
            assert len(result.multiple_matches) == 2
    
    @pytest.mark.asyncio
    async def test_search_by_name_success(self):
        """Test successful name search"""
        with patch('utils.client_selection.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_bot.db.acquire.return_value.__aenter__.return_value = mock_conn
            mock_conn.fetch.return_value = [
                {
                    'id': 1,
                    'full_name': 'John Doe',
                    'phone_number': '+998901234567'
                }
            ]
            
            search_engine = ClientSearchEngine()
            result = await search_engine.search_by_name("John")
            
            assert result.found is True
            assert result.client is not None
            assert result.client['full_name'] == 'John Doe'
    
    @pytest.mark.asyncio
    async def test_search_by_id_success(self):
        """Test successful ID search"""
        with patch('utils.client_selection.get_user_by_id') as mock_get_user:
            mock_get_user.return_value = {
                'id': 123,
                'full_name': 'Test User',
                'phone_number': '+998901234567'
            }
            
            search_engine = ClientSearchEngine()
            result = await search_engine.search_by_id(123)
            
            assert result.found is True
            assert result.client is not None
            assert result.client['id'] == 123


class TestClientManager:
    """Test client manager functionality"""
    
    @pytest.mark.asyncio
    async def test_search_client_phone(self):
        """Test client search by phone"""
        with patch('utils.client_selection.bot') as mock_bot:
            mock_conn = AsyncMock()
            mock_bot.db.acquire.return_value.__aenter__.return_value = mock_conn
            mock_conn.fetch.return_value = [
                {'id': 1, 'full_name': 'Test User', 'phone_number': '+998901234567'}
            ]
            
            manager = ClientManager()
            result = await manager.search_client('phone', '+998901234567')
            
            assert result.found is True
            assert result.client is not None
    
    @pytest.mark.asyncio
    async def test_create_new_client_success(self):
        """Test successful client creation"""
        with patch('utils.client_selection.ClientValidator') as mock_validator_class:
            with patch('utils.client_selection.create_user') as mock_create_user:
                with patch('utils.client_selection.bot') as mock_bot:
                    # Mock validator
                    mock_validator = MagicMock()
                    mock_validator.validate_client_data.return_value = []
                    mock_validator.normalize_phone_number.return_value = '+998901234567'
                    mock_validator_class.return_value = mock_validator
                    
                    # Mock database search (no existing client)
                    mock_conn = AsyncMock()
                    mock_bot.db.acquire.return_value.__aenter__.return_value = mock_conn
                    mock_conn.fetch.return_value = []
                    
                    # Mock user creation
                    mock_create_user.return_value = 123
                    
                    manager = ClientManager()
                    success, client_id, errors = await manager.create_new_client({
                        'full_name': 'Test User',
                        'phone_number': '+998901234567',
                        'language': 'uz'
                    })
                    
                    assert success is True
                    assert client_id == 123
                    assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_create_new_client_validation_error(self):
        """Test client creation with validation errors"""
        manager = ClientManager()
        success, client_id, errors = await manager.create_new_client({
            'full_name': 'A',  # Too short
            'phone_number': '123',  # Invalid
        })
        
        assert success is False
        assert client_id is None
        assert len(errors) > 0
    
    def test_format_client_display(self):
        """Test client display formatting"""
        client_data = {
            'full_name': 'Test User',
            'phone_number': '+998901234567',
            'id': 123
        }
        
        manager = ClientManager()
        display_text = manager.format_client_display(client_data, 'uz')
        
        assert "Test User" in display_text
        assert "+998901234567" in display_text
        assert "123" in display_text
    
    def test_format_multiple_clients_display(self):
        """Test multiple clients display formatting"""
        clients = [
            {'id': 1, 'full_name': 'User 1', 'phone_number': '+998901234567'},
            {'id': 2, 'full_name': 'User 2', 'phone_number': '+998907654321'}
        ]
        
        manager = ClientManager()
        display_text = manager.format_multiple_clients_display(clients, 'uz')
        
        assert "Bir nechta mijoz topildi:" in display_text
        assert "User 1" in display_text
        assert "User 2" in display_text


class TestClientSelectionData:
    """Test client selection data model"""
    
    def test_client_selection_data_creation(self):
        """Test creating ClientSelectionData instance"""
        data = ClientSelectionData(
            search_method='phone',
            search_value='+998901234567',
            client_id=123,
            verified=True
        )
        
        assert data.search_method == 'phone'
        assert data.search_value == '+998901234567'
        assert data.client_id == 123
        assert data.verified is True
    
    def test_client_selection_data_to_dict(self):
        """Test converting ClientSelectionData to dictionary"""
        data = ClientSelectionData(
            search_method='name',
            search_value='John Doe',
            verified=False
        )
        
        data_dict = data.to_dict()
        
        assert data_dict['search_method'] == 'name'
        assert data_dict['search_value'] == 'John Doe'
        assert data_dict['verified'] is False
    
    def test_client_selection_data_from_dict(self):
        """Test creating ClientSelectionData from dictionary"""
        data_dict = {
            'search_method': 'id',
            'search_value': '123',
            'client_id': 123,
            'verified': True
        }
        
        data = ClientSelectionData.from_dict(data_dict)
        
        assert data.search_method == 'id'
        assert data.search_value == '123'
        assert data.client_id == 123
        assert data.verified is True


if __name__ == '__main__':
    pytest.main([__file__])