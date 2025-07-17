"""
Simplified Tests for Client Selection and Validation System
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from utils.client_selection import (
    ClientValidator, ClientManager,
    ClientValidationError, ClientSelectionError, ClientSearchResult
)
from database.models import ClientSelectionData


class TestClientValidatorSimple:
    """Test ClientValidator class with simple tests"""
    
    def test_validate_phone_number_valid_formats(self):
        """Test valid phone number formats"""
        validator = ClientValidator()
        
        # Valid formats
        assert validator.validate_phone_number("+998901234567")
        assert validator.validate_phone_number("998901234567")
        assert validator.validate_phone_number("901234567")
    
    def test_validate_phone_number_invalid_formats(self):
        """Test invalid phone number formats"""
        validator = ClientValidator()
        
        # Invalid formats
        assert not validator.validate_phone_number("")
        assert not validator.validate_phone_number("123")
        assert not validator.validate_phone_number("abcdefghij")
    
    def test_normalize_phone_number(self):
        """Test phone number normalization"""
        validator = ClientValidator()
        
        # Test normalization
        assert validator.normalize_phone_number("901234567") == "+998901234567"
        assert validator.normalize_phone_number("998901234567") == "+998901234567"
        assert validator.normalize_phone_number("+998901234567") == "+998901234567"
    
    def test_validate_full_name_valid(self):
        """Test valid full names"""
        validator = ClientValidator()
        
        # Valid names
        assert validator.validate_full_name("John Doe")
        assert validator.validate_full_name("Алиев Вали")
        assert validator.validate_full_name("O'Connor")
        assert validator.validate_full_name("Jean-Pierre")
    
    def test_validate_full_name_invalid(self):
        """Test invalid full names"""
        validator = ClientValidator()
        
        # Invalid names
        assert not validator.validate_full_name("")
        assert not validator.validate_full_name("A")
        assert not validator.validate_full_name("John123")
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


class TestClientManagerSimple:
    """Test ClientManager class with mocked dependencies"""
    
    @pytest.fixture
    def client_manager(self):
        """Create ClientManager instance"""
        return ClientManager()
    
    @pytest.mark.asyncio
    async def test_search_client_invalid_method(self, client_manager):
        """Test client search with invalid method"""
        with pytest.raises(ClientSelectionError):
            await client_manager.search_client("invalid", "value")
    
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


class TestErrorHandling:
    """Test error handling scenarios"""
    
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


class TestClientSearchResult:
    """Test ClientSearchResult dataclass"""
    
    def test_client_search_result_found(self):
        """Test ClientSearchResult when client is found"""
        client_data = {'id': 1, 'name': 'John'}
        result = ClientSearchResult(found=True, client=client_data)
        
        assert result.found is True
        assert result.client == client_data
        assert result.multiple_matches is None
        assert result.error is None
    
    def test_client_search_result_not_found(self):
        """Test ClientSearchResult when client is not found"""
        result = ClientSearchResult(found=False)
        
        assert result.found is False
        assert result.client is None
        assert result.multiple_matches is None
        assert result.error is None
    
    def test_client_search_result_multiple_matches(self):
        """Test ClientSearchResult with multiple matches"""
        clients = [{'id': 1, 'name': 'John'}, {'id': 2, 'name': 'Jane'}]
        result = ClientSearchResult(found=True, multiple_matches=clients)
        
        assert result.found is True
        assert result.client is None
        assert result.multiple_matches == clients
        assert result.error is None
    
    def test_client_search_result_error(self):
        """Test ClientSearchResult with error"""
        result = ClientSearchResult(found=False, error="Database error")
        
        assert result.found is False
        assert result.client is None
        assert result.multiple_matches is None
        assert result.error == "Database error"


class TestClientSelectionData:
    """Test ClientSelectionData model"""
    
    def test_client_selection_data_phone_search(self):
        """Test ClientSelectionData for phone search"""
        data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567"
        )
        
        assert data.search_method == "phone"
        assert data.search_value == "+998901234567"
        assert data.client_id is None
        assert data.new_client_data == {}
        assert data.verified is False
    
    def test_client_selection_data_new_client(self):
        """Test ClientSelectionData for new client"""
        new_client_data = {
            'full_name': 'John Doe',
            'phone_number': '+998901234567'
        }
        
        data = ClientSelectionData(
            search_method="new",
            new_client_data=new_client_data
        )
        
        assert data.search_method == "new"
        assert data.search_value is None
        assert data.new_client_data == new_client_data
        assert data.verified is False
    
    def test_client_selection_data_to_dict(self):
        """Test ClientSelectionData to_dict method"""
        data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567",
            client_id=1,
            verified=True
        )
        
        result_dict = data.to_dict()
        
        assert result_dict['search_method'] == "phone"
        assert result_dict['search_value'] == "+998901234567"
        assert result_dict['client_id'] == 1
        assert result_dict['verified'] is True
    
    def test_client_selection_data_from_dict(self):
        """Test ClientSelectionData from_dict method"""
        data_dict = {
            'search_method': 'name',
            'search_value': 'John Doe',
            'client_id': None,
            'new_client_data': {},
            'verified': False,
            'created_at': None
        }
        
        data = ClientSelectionData.from_dict(data_dict)
        
        assert data.search_method == "name"
        assert data.search_value == "John Doe"
        assert data.client_id is None
        assert data.verified is False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])