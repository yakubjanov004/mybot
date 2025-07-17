"""
Integration Tests for Client Selection and Validation System
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from utils.client_selection import ClientManager, ClientSearchResult
from database.models import ClientSelectionData, User


class TestClientSelectionIntegration:
    """Integration tests for client selection system"""
    
    @pytest.fixture
    def client_manager(self):
        """Create ClientManager instance"""
        return ClientManager()
    
    @pytest.fixture
    def sample_client_data(self):
        """Sample client data for testing"""
        return {
            'id': 1,
            'telegram_id': 123456789,
            'full_name': 'John Doe',
            'phone_number': '+998901234567',
            'role': 'client',
            'language': 'uz',
            'is_active': True,
            'address': '123 Main St',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    @pytest.mark.asyncio
    async def test_search_client_by_phone_integration(self, client_manager, sample_client_data):
        """Test client search by phone with mocked database response"""
        
        # Mock the search engine method
        mock_result = ClientSearchResult(found=True, client=sample_client_data)
        
        with patch.object(client_manager.search_engine, 'search_by_phone', return_value=mock_result):
            result = await client_manager.search_client("phone", "+998901234567")
            
            assert result.found is True
            assert result.client is not None
            assert result.client['full_name'] == 'John Doe'
            assert result.client['phone_number'] == '+998901234567'
    
    @pytest.mark.asyncio
    async def test_search_client_by_name_integration(self, client_manager, sample_client_data):
        """Test client search by name with mocked database response"""
        
        # Mock the search engine method
        mock_result = ClientSearchResult(found=True, client=sample_client_data)
        
        with patch.object(client_manager.search_engine, 'search_by_name', return_value=mock_result):
            result = await client_manager.search_client("name", "John Doe")
            
            assert result.found is True
            assert result.client is not None
            assert result.client['full_name'] == 'John Doe'
    
    @pytest.mark.asyncio
    async def test_search_client_by_id_integration(self, client_manager, sample_client_data):
        """Test client search by ID with mocked database response"""
        
        # Mock the search engine method
        mock_result = ClientSearchResult(found=True, client=sample_client_data)
        
        with patch.object(client_manager.search_engine, 'search_by_id', return_value=mock_result):
            result = await client_manager.search_client("id", "1")
            
            assert result.found is True
            assert result.client is not None
            assert result.client['id'] == 1
    
    @pytest.mark.asyncio
    async def test_create_new_client_integration(self, client_manager):
        """Test new client creation with mocked database operations"""
        
        new_client_data = {
            'full_name': 'Jane Smith',
            'phone_number': '+998901234568',
            'language': 'ru',
            'address': '456 Oak St'
        }
        
        # Mock search to return no existing client
        mock_search_result = ClientSearchResult(found=False)
        
        with patch.object(client_manager.search_engine, 'search_by_phone', return_value=mock_search_result), \
             patch('utils.client_selection.create_user', return_value=2):
            
            success, client_id, errors = await client_manager.create_new_client(new_client_data)
            
            assert success is True
            assert client_id == 2
            assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_process_client_selection_existing_client(self, client_manager, sample_client_data):
        """Test processing client selection for existing client"""
        
        selection_data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567"
        )
        
        # Mock search to return existing client
        mock_search_result = ClientSearchResult(found=True, client=sample_client_data)
        
        with patch.object(client_manager, 'search_client', return_value=mock_search_result):
            success, client_data, errors = await client_manager.process_client_selection(selection_data)
            
            assert success is True
            assert client_data is not None
            assert client_data['id'] == 1
            assert client_data['full_name'] == 'John Doe'
            assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_process_client_selection_new_client(self, client_manager):
        """Test processing client selection for new client"""
        
        new_client_data = {
            'full_name': 'Jane Smith',
            'phone_number': '+998901234568',
            'language': 'ru'
        }
        
        selection_data = ClientSelectionData(
            search_method="new",
            new_client_data=new_client_data
        )
        
        created_client_data = {
            'id': 2,
            'full_name': 'Jane Smith',
            'phone_number': '+998901234568',
            'role': 'client',
            'language': 'ru'
        }
        
        with patch.object(client_manager, 'create_new_client', return_value=(True, 2, [])), \
             patch('utils.client_selection.get_user_by_id', return_value=created_client_data):
            
            success, client_data, errors = await client_manager.process_client_selection(selection_data)
            
            assert success is True
            assert client_data is not None
            assert client_data['id'] == 2
            assert client_data['full_name'] == 'Jane Smith'
            assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_process_client_selection_client_not_found(self, client_manager):
        """Test processing client selection when client is not found"""
        
        selection_data = ClientSelectionData(
            search_method="phone",
            search_value="+998999999999"
        )
        
        # Mock search to return no client found
        mock_search_result = ClientSearchResult(found=False)
        
        with patch.object(client_manager, 'search_client', return_value=mock_search_result):
            success, client_data, errors = await client_manager.process_client_selection(selection_data)
            
            assert success is False
            assert client_data is None
            assert len(errors) > 0
            assert "Client not found" in errors[0]
    
    @pytest.mark.asyncio
    async def test_process_client_selection_multiple_matches(self, client_manager):
        """Test processing client selection with multiple matches"""
        
        selection_data = ClientSelectionData(
            search_method="name",
            search_value="John"
        )
        
        # Mock search to return multiple matches
        multiple_clients = [
            {'id': 1, 'full_name': 'John Doe', 'phone_number': '+998901234567'},
            {'id': 2, 'full_name': 'John Smith', 'phone_number': '+998901234568'}
        ]
        mock_search_result = ClientSearchResult(found=True, multiple_matches=multiple_clients)
        
        with patch.object(client_manager, 'search_client', return_value=mock_search_result):
            success, client_data, errors = await client_manager.process_client_selection(selection_data)
            
            assert success is False
            assert client_data is None
            assert len(errors) > 0
            assert "Multiple clients found" in errors[0]
    
    def test_client_display_formatting_integration(self, client_manager, sample_client_data):
        """Test client display formatting with real client data"""
        
        # Test Uzbek display
        display_uz = client_manager.format_client_display(sample_client_data, 'uz')
        assert '👤 John Doe' in display_uz
        assert '📞 +998901234567' in display_uz
        assert '🆔 ID: 1' in display_uz
        
        # Test Russian display
        display_ru = client_manager.format_client_display(sample_client_data, 'ru')
        assert '👤 John Doe' in display_ru
        assert '📞 +998901234567' in display_ru
        assert '🆔 ID: 1' in display_ru
    
    def test_multiple_clients_display_formatting_integration(self, client_manager):
        """Test multiple clients display formatting"""
        
        clients = [
            {'id': 1, 'full_name': 'John Doe', 'phone_number': '+998901234567'},
            {'id': 2, 'full_name': 'Jane Smith', 'phone_number': '+998901234568'},
            {'id': 3, 'full_name': 'Bob Johnson', 'phone_number': '+998901234569'}
        ]
        
        # Test Uzbek display
        display_uz = client_manager.format_multiple_clients_display(clients, 'uz')
        assert 'Bir nechta mijoz topildi:' in display_uz
        assert '1. John Doe' in display_uz
        assert '2. Jane Smith' in display_uz
        assert '3. Bob Johnson' in display_uz
        
        # Test Russian display
        display_ru = client_manager.format_multiple_clients_display(clients, 'ru')
        assert 'Найдено несколько клиентов:' in display_ru
        assert '1. John Doe' in display_ru
        assert '2. Jane Smith' in display_ru
        assert '3. Bob Johnson' in display_ru
    
    @pytest.mark.asyncio
    async def test_validation_integration_with_models(self, client_manager):
        """Test validation integration with database models"""
        
        # Test valid ClientSelectionData
        valid_selection = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567",
            client_id=1,
            verified=True
        )
        
        errors = await client_manager.validate_client_selection(valid_selection)
        assert len(errors) == 0
        
        # Test invalid ClientSelectionData
        invalid_selection = ClientSelectionData(
            search_method="invalid_method",
            search_value="test"
        )
        
        errors = await client_manager.validate_client_selection(invalid_selection)
        assert len(errors) > 0
        assert "Invalid search method" in errors[0]
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, client_manager):
        """Test error handling in integration scenarios"""
        
        # Test database error handling
        selection_data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567"
        )
        
        # Mock search to return error
        mock_search_result = ClientSearchResult(found=False, error="Database connection failed")
        
        with patch.object(client_manager, 'search_client', return_value=mock_search_result):
            success, client_data, errors = await client_manager.process_client_selection(selection_data)
            
            assert success is False
            assert client_data is None
            assert len(errors) > 0
            assert "Database connection failed" in errors[0]


class TestClientSelectionDataIntegration:
    """Integration tests for ClientSelectionData model"""
    
    def test_client_selection_data_serialization(self):
        """Test ClientSelectionData serialization and deserialization"""
        
        original_data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567",
            client_id=1,
            new_client_data={'full_name': 'John Doe'},
            verified=True,
            created_at=datetime.now()
        )
        
        # Convert to dict and back
        data_dict = original_data.to_dict()
        restored_data = ClientSelectionData.from_dict(data_dict)
        
        assert restored_data.search_method == original_data.search_method
        assert restored_data.search_value == original_data.search_value
        assert restored_data.client_id == original_data.client_id
        assert restored_data.new_client_data == original_data.new_client_data
        assert restored_data.verified == original_data.verified
    
    def test_client_selection_data_with_user_model(self):
        """Test ClientSelectionData integration with User model"""
        
        # Create a User model instance
        user = User(
            id=1,
            telegram_id=123456789,
            full_name='John Doe',
            phone='+998901234567',
            role='client',
            language='uz'
        )
        
        # Create ClientSelectionData that references this user
        selection_data = ClientSelectionData(
            search_method="id",
            search_value=str(user.id),
            client_id=user.id,
            verified=True
        )
        
        assert selection_data.client_id == user.id
        assert selection_data.search_value == str(user.id)
        
        # Test serialization with user data
        user_dict = user.to_dict()
        selection_data.new_client_data = user_dict
        
        serialized = selection_data.to_dict()
        assert serialized['new_client_data']['full_name'] == 'John Doe'
        assert serialized['new_client_data']['phone'] == '+998901234567'


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])