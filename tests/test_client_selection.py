"""
Tests for Client Selection and Validation System
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from utils.client_selection import (
    ClientValidator, ClientSearchEngine, ClientManager,
    ClientValidationError, ClientSelectionError, ClientSearchResult,
    search_client_by_phone, search_client_by_name, search_client_by_id,
    create_client_from_data
)
from database.models import ClientSelectionData


class TestClientValidator:
    """Test ClientValidator class"""
    
    def test_validate_phone_number_valid_formats(self):
        """Test valid phone number formats"""
        validator = ClientValidator()
        
        # Valid formats
        assert validator.validate_phone_number("+998901234567")
        assert validator.validate_phone_number("998901234567")
        assert validator.validate_phone_number("901234567")
        assert validator.validate_phone_number("+998 90 123 45 67")
        assert validator.validate_phone_number("998-90-123-45-67")
    
    def test_validate_phone_number_invalid_formats(self):
        """Test invalid phone number formats"""
        validator = ClientValidator()
        
        # Invalid formats
        assert not validator.validate_phone_number("")
        assert not validator.validate_phone_number("123")
        assert not validator.validate_phone_number("+1234567890")
        assert not validator.validate_phone_number("abcdefghij")
        assert not validator.validate_phone_number("+998 90 123")
    
    def test_normalize_phone_number(self):
        """Test phone number normalization"""
        validator = ClientValidator()
        
        # Test normalization
        assert validator.normalize_phone_number("901234567") == "+998901234567"
        assert validator.normalize_phone_number("998901234567") == "+998901234567"
        assert validator.normalize_phone_number("+998901234567") == "+998901234567"
        assert validator.normalize_phone_number("998-90-123-45-67") == "+998901234567"
        assert validator.normalize_phone_number("+998 90 123 45 67") == "+998901234567"
        assert validator.normalize_phone_number("") == ""
    
    def test_validate_full_name_valid(self):
        """Test valid full names"""
        validator = ClientValidator()
        
        # Valid names
        assert validator.validate_full_name("John Doe")
        assert validator.validate_full_name("Алиев Вали")
        assert validator.validate_full_name("O'Connor")
        assert validator.validate_full_name("Jean-Pierre")
        # Note: Some Uzbek characters might not be in the regex, so testing with basic ones
        assert validator.validate_full_name("Uzbekiston")
    
    def test_validate_full_name_invalid(self):
        """Test invalid full names"""
        validator = ClientValidator()
        
        # Invalid names
        assert not validator.validate_full_name("")
        assert not validator.validate_full_name("A")
        assert not validator.validate_full_name("John123")
        assert not validator.validate_full_name("John@Doe")
        assert not validator.validate_full_name("A" * 101)  # Too long
    
    def test_validate_client_data_valid(self):
        """Test validation of valid client data"""
        validator = ClientValidator()
        
        valid_data = {
            'full_name': 'John Doe',
            'phone_number': '+998901234567',
            'language': 'uz',
            'address': '123 Main St'
        }
        
        errors = validator.validate_client_data(valid_data)
        assert len(errors) == 0
    
    def test_validate_client_data_invalid(self):
        """Test validation of invalid client data"""
        validator = ClientValidator()
        
        invalid_data = {
            'full_name': 'A',  # Too short
            'phone_number': '123',  # Invalid format
            'language': 'fr',  # Invalid language
            'address': 'A' * 501  # Too long
        }
        
        errors = validator.validate_client_data(invalid_data)
        assert len(errors) == 4  # All fields should have errors


class TestClientSearchEngine:
    """Test ClientSearchEngine class"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection"""
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        
        # Create a proper async context manager
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = async_context_manager
        
        return mock_conn, mock_pool
    
    @pytest.mark.asyncio
    async def test_search_by_phone_found(self, mock_db_connection):
        """Test successful phone search"""
        mock_conn, mock_pool = mock_db_connection
        
        # Mock database result
        mock_result = [{
            'id': 1,
            'telegram_id': 123456789,
            'full_name': 'John Doe',
            'phone_number': '+998901234567',
            'role': 'client',
            'language': 'uz',
            'is_active': True,
            'address': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }]
        mock_conn.fetch.return_value = mock_result
        
        with patch('utils.client_selection.bot.db', mock_pool):
            engine = ClientSearchEngine()
            result = await engine.search_by_phone("+998901234567")
            
            assert result.found is True
            assert result.client is not None
            assert result.client['full_name'] == 'John Doe'
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_search_by_phone_not_found(self, mock_db_connection):
        """Test phone search with no results"""
        mock_conn, mock_pool = mock_db_connection
        mock_conn.fetch.return_value = []
        
        with patch('utils.client_selection.bot.db', mock_pool):
            engine = ClientSearchEngine()
            result = await engine.search_by_phone("+998901234567")
            
            assert result.found is False
            assert result.client is None
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_search_by_phone_multiple_results(self, mock_db_connection):
        """Test phone search with multiple results"""
        mock_conn, mock_pool = mock_db_connection
        
        # Mock multiple results
        mock_results = [
            {'id': 1, 'full_name': 'John Doe', 'phone_number': '+998901234567'},
            {'id': 2, 'full_name': 'Jane Doe', 'phone_number': '+998901234567'}
        ]
        mock_conn.fetch.return_value = mock_results
        
        with patch('utils.client_selection.bot.db', mock_pool):
            engine = ClientSearchEngine()
            result = await engine.search_by_phone("+998901234567")
            
            assert result.found is True
            assert result.client is None
            assert result.multiple_matches is not None
            assert len(result.multiple_matches) == 2
    
    @pytest.mark.asyncio
    async def test_search_by_phone_invalid_format(self):
        """Test phone search with invalid format"""
        engine = ClientSearchEngine()
        result = await engine.search_by_phone("invalid")
        
        assert result.found is False
        assert result.error == "Invalid phone number format"
    
    @pytest.mark.asyncio
    async def test_search_by_name_found(self, mock_db_connection):
        """Test successful name search"""
        mock_conn, mock_pool = mock_db_connection
        
        mock_result = [{
            'id': 1,
            'full_name': 'John Doe',
            'phone_number': '+998901234567'
        }]
        mock_conn.fetch.return_value = mock_result
        
        with patch('utils.client_selection.bot.db', mock_pool):
            engine = ClientSearchEngine()
            result = await engine.search_by_name("John Doe")
            
            assert result.found is True
            assert result.client is not None
            assert result.client['full_name'] == 'John Doe'
    
    @pytest.mark.asyncio
    async def test_search_by_name_too_short(self):
        """Test name search with too short name"""
        engine = ClientSearchEngine()
        result = await engine.search_by_name("A")
        
        assert result.found is False
        assert result.error == "Name must be at least 2 characters"
    
    @pytest.mark.asyncio
    async def test_search_by_id_found(self):
        """Test successful ID search"""
        mock_client_data = {
            'id': 1,
            'full_name': 'John Doe',
            'phone_number': '+998901234567'
        }
        
        with patch('utils.client_selection.get_user_by_id', return_value=mock_client_data):
            engine = ClientSearchEngine()
            result = await engine.search_by_id(1)
            
            assert result.found is True
            assert result.client is not None
            assert result.client['id'] == 1
    
    @pytest.mark.asyncio
    async def test_search_by_id_not_found(self):
        """Test ID search with no result"""
        with patch('utils.client_selection.get_user_by_id', return_value=None):
            engine = ClientSearchEngine()
            result = await engine.search_by_id(999)
            
            assert result.found is False
            assert result.client is None
    
    @pytest.mark.asyncio
    async def test_search_by_id_invalid(self):
        """Test ID search with invalid ID"""
        engine = ClientSearchEngine()
        result = await engine.search_by_id(-1)
        
        assert result.found is False
        assert result.error == "Invalid client ID"


class TestClientManager:
    """Test ClientManager class"""
    
    @pytest.fixture
    def client_manager(self):
        """Create ClientManager instance"""
        return ClientManager()
    
    @pytest.mark.asyncio
    async def test_search_client_phone(self, client_manager):
        """Test client search by phone"""
        mock_result = ClientSearchResult(found=True, client={'id': 1, 'full_name': 'John'})
        
        with patch.object(client_manager.search_engine, 'search_by_phone', return_value=mock_result):
            result = await client_manager.search_client("phone", "+998901234567")
            
            assert result.found is True
            assert result.client['id'] == 1
    
    @pytest.mark.asyncio
    async def test_search_client_invalid_method(self, client_manager):
        """Test client search with invalid method"""
        with pytest.raises(ClientSelectionError):
            await client_manager.search_client("invalid", "value")
    
    @pytest.mark.asyncio
    async def test_create_new_client_success(self, client_manager):
        """Test successful client creation"""
        client_data = {
            'full_name': 'John Doe',
            'phone_number': '+998901234567',
            'language': 'uz'
        }
        
        # Mock search to return no existing client
        mock_search_result = ClientSearchResult(found=False)
        
        with patch.object(client_manager.search_engine, 'search_by_phone', return_value=mock_search_result), \
             patch('utils.client_selection.create_user', return_value=1):
            
            success, client_id, errors = await client_manager.create_new_client(client_data)
            
            assert success is True
            assert client_id == 1
            assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_create_new_client_validation_error(self, client_manager):
        """Test client creation with validation errors"""
        invalid_data = {
            'full_name': 'A',  # Too short
            'phone_number': 'invalid',
            'language': 'uz'
        }
        
        success, client_id, errors = await client_manager.create_new_client(invalid_data)
        
        assert success is False
        assert client_id is None
        assert len(errors) > 0
    
    @pytest.mark.asyncio
    async def test_create_new_client_already_exists(self, client_manager):
        """Test client creation when client already exists"""
        client_data = {
            'full_name': 'John Doe',
            'phone_number': '+998901234567',
            'language': 'uz'
        }
        
        # Mock search to return existing client
        mock_search_result = ClientSearchResult(found=True, client={'id': 1})
        
        with patch.object(client_manager.search_engine, 'search_by_phone', return_value=mock_search_result):
            success, client_id, errors = await client_manager.create_new_client(client_data)
            
            assert success is False
            assert client_id is None
            assert "already exists" in errors[0]
    
    @pytest.mark.asyncio
    async def test_validate_client_selection_valid(self, client_manager):
        """Test validation of valid client selection data"""
        selection_data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567"
        )
        
        errors = await client_manager.validate_client_selection(selection_data)
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_client_selection_invalid_method(self, client_manager):
        """Test validation with invalid search method"""
        selection_data = ClientSelectionData(
            search_method="invalid",
            search_value="value"
        )
        
        errors = await client_manager.validate_client_selection(selection_data)
        assert len(errors) > 0
        assert "Invalid search method" in errors[0]
    
    @pytest.mark.asyncio
    async def test_validate_client_selection_new_without_data(self, client_manager):
        """Test validation of new client without data"""
        selection_data = ClientSelectionData(
            search_method="new"
        )
        
        errors = await client_manager.validate_client_selection(selection_data)
        assert len(errors) > 0
        assert "New client data is required" in errors[0]
    
    @pytest.mark.asyncio
    async def test_process_client_selection_existing(self, client_manager):
        """Test processing existing client selection"""
        selection_data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567"
        )
        
        mock_result = ClientSearchResult(found=True, client={'id': 1, 'full_name': 'John'})
        
        with patch.object(client_manager, 'search_client', return_value=mock_result):
            success, client_data, errors = await client_manager.process_client_selection(selection_data)
            
            assert success is True
            assert client_data is not None
            assert client_data['id'] == 1
            assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_process_client_selection_new(self, client_manager):
        """Test processing new client selection"""
        new_client_data = {
            'full_name': 'John Doe',
            'phone_number': '+998901234567',
            'language': 'uz'
        }
        
        selection_data = ClientSelectionData(
            search_method="new",
            new_client_data=new_client_data
        )
        
        created_client_data = {'id': 1, 'full_name': 'John Doe'}
        
        with patch.object(client_manager, 'create_new_client', return_value=(True, 1, [])), \
             patch('utils.client_selection.get_user_by_id', return_value=created_client_data):
            
            success, client_data, errors = await client_manager.process_client_selection(selection_data)
            
            assert success is True
            assert client_data is not None
            assert client_data['id'] == 1
            assert len(errors) == 0
    
    def test_format_client_display(self, client_manager):
        """Test client display formatting"""
        client_data = {
            'id': 1,
            'full_name': 'John Doe',
            'phone_number': '+998901234567'
        }
        
        display = client_manager.format_client_display(client_data, 'uz')
        
        assert '👤 John Doe' in display
        assert '📞 +998901234567' in display
        assert '🆔 ID: 1' in display
    
    def test_format_multiple_clients_display(self, client_manager):
        """Test multiple clients display formatting"""
        clients = [
            {'id': 1, 'full_name': 'John Doe', 'phone_number': '+998901234567'},
            {'id': 2, 'full_name': 'Jane Doe', 'phone_number': '+998901234568'}
        ]
        
        display = client_manager.format_multiple_clients_display(clients, 'uz')
        
        assert 'John Doe' in display
        assert 'Jane Doe' in display
        assert '1.' in display
        assert '2.' in display


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.mark.asyncio
    async def test_search_client_by_phone(self):
        """Test search_client_by_phone convenience function"""
        mock_result = ClientSearchResult(found=True, client={'id': 1})
        
        with patch('utils.client_selection.ClientManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.search_client.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            result = await search_client_by_phone("+998901234567")
            
            assert result.found is True
            mock_manager.search_client.assert_called_once_with("phone", "+998901234567")
    
    @pytest.mark.asyncio
    async def test_search_client_by_name(self):
        """Test search_client_by_name convenience function"""
        mock_result = ClientSearchResult(found=True, client={'id': 1})
        
        with patch('utils.client_selection.ClientManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.search_client.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            result = await search_client_by_name("John Doe")
            
            assert result.found is True
            mock_manager.search_client.assert_called_once_with("name", "John Doe")
    
    @pytest.mark.asyncio
    async def test_search_client_by_id(self):
        """Test search_client_by_id convenience function"""
        mock_result = ClientSearchResult(found=True, client={'id': 1})
        
        with patch('utils.client_selection.ClientManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.search_client.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            result = await search_client_by_id(1)
            
            assert result.found is True
            mock_manager.search_client.assert_called_once_with("id", "1")
    
    @pytest.mark.asyncio
    async def test_create_client_from_data(self):
        """Test create_client_from_data convenience function"""
        client_data = {'full_name': 'John Doe', 'phone_number': '+998901234567'}
        
        with patch('utils.client_selection.ClientManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.create_new_client.return_value = (True, 1, [])
            mock_manager_class.return_value = mock_manager
            
            success, client_id, errors = await create_client_from_data(client_data)
            
            assert success is True
            assert client_id == 1
            assert len(errors) == 0
            mock_manager.create_new_client.assert_called_once_with(client_data)


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors"""
        mock_pool = AsyncMock()
        mock_pool.acquire.side_effect = Exception("Connection failed")
        
        with patch('utils.client_selection.bot.db', mock_pool):
            engine = ClientSearchEngine()
            result = await engine.search_by_phone("+998901234567")
            
            assert result.found is False
            assert "Database error" in result.error
    
    def test_client_validation_error_creation(self):
        """Test ClientValidationError creation"""
        error = ClientValidationError("phone", "+123", "Invalid format")
        
        assert error.field == "phone"
        assert error.value == "+123"
        assert error.reason == "Invalid format"
        assert "Client validation failed for phone" in str(error)
    
    def test_client_selection_error_creation(self):
        """Test ClientSelectionError creation"""
        error = ClientSelectionError("phone", "+123", "Not found")
        
        assert error.search_method == "phone"
        assert error.search_value == "+123"
        assert error.reason == "Not found"
        assert "Client selection failed for phone=+123" in str(error)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])