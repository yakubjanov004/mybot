"""
Unit tests for InventoryManager

Tests all functionality of the InventoryManager class including:
- Equipment tracking and reservation
- Automatic inventory updates
- Stock level monitoring and alerts
- Transaction logging
- Integration with workflow system

Requirements tested: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.inventory_manager import (
    InventoryManager, 
    InventoryItem, 
    InventoryTransaction, 
    StockAlert,
    TransactionType,
    StockLevel
)


class TestInventoryItem:
    """Test InventoryItem dataclass and properties"""
    
    def test_inventory_item_creation(self):
        """Test creating an inventory item"""
        item = InventoryItem(
            id=1,
            name="Test Cable",
            category="cables",
            quantity_in_stock=50,
            min_quantity=10,
            unit="meters"
        )
        
        assert item.id == 1
        assert item.name == "Test Cable"
        assert item.category == "cables"
        assert item.quantity_in_stock == 50
        assert item.min_quantity == 10
        assert item.unit == "meters"
    
    def test_stock_level_normal(self):
        """Test normal stock level detection"""
        item = InventoryItem(
            id=1, name="Test", category="test", 
            quantity_in_stock=50, min_quantity=10, unit="pcs"
        )
        assert item.stock_level == StockLevel.NORMAL
        assert not item.is_low_stock
    
    def test_stock_level_low(self):
        """Test low stock level detection"""
        item = InventoryItem(
            id=1, name="Test", category="test", 
            quantity_in_stock=10, min_quantity=10, unit="pcs"
        )
        assert item.stock_level == StockLevel.LOW
        assert item.is_low_stock
    
    def test_stock_level_critical(self):
        """Test critical stock level detection"""
        item = InventoryItem(
            id=1, name="Test", category="test", 
            quantity_in_stock=3, min_quantity=10, unit="pcs"
        )
        assert item.stock_level == StockLevel.CRITICAL
        assert item.is_low_stock
    
    def test_stock_level_out_of_stock(self):
        """Test out of stock detection"""
        item = InventoryItem(
            id=1, name="Test", category="test", 
            quantity_in_stock=0, min_quantity=10, unit="pcs"
        )
        assert item.stock_level == StockLevel.OUT_OF_STOCK
        assert item.is_low_stock


class TestInventoryTransaction:
    """Test InventoryTransaction dataclass"""
    
    def test_transaction_creation(self):
        """Test creating an inventory transaction"""
        transaction = InventoryTransaction(
            request_id="req-123",
            material_id=1,
            transaction_type=TransactionType.CONSUME.value,
            quantity=5,
            performed_by=100,
            notes="Test consumption"
        )
        
        assert transaction.request_id == "req-123"
        assert transaction.material_id == 1
        assert transaction.transaction_type == TransactionType.CONSUME.value
        assert transaction.quantity == 5
        assert transaction.performed_by == 100
        assert transaction.notes == "Test consumption"
    
    def test_transaction_to_dict(self):
        """Test transaction serialization"""
        transaction = InventoryTransaction(
            id=1,
            request_id="req-123",
            material_id=1,
            transaction_type=TransactionType.RESERVE.value,
            quantity=3
        )
        
        data = transaction.to_dict()
        assert data['id'] == 1
        assert data['request_id'] == "req-123"
        assert data['material_id'] == 1
        assert data['transaction_type'] == TransactionType.RESERVE.value
        assert data['quantity'] == 3


class TestStockAlert:
    """Test StockAlert dataclass"""
    
    def test_stock_alert_creation(self):
        """Test creating a stock alert"""
        alert = StockAlert(
            item_id=1,
            item_name="Test Cable",
            current_quantity=2,
            min_quantity=10,
            stock_level=StockLevel.CRITICAL,
            category="cables"
        )
        
        assert alert.item_id == 1
        assert alert.item_name == "Test Cable"
        assert alert.current_quantity == 2
        assert alert.min_quantity == 10
        assert alert.stock_level == StockLevel.CRITICAL
        assert "CRITICAL" in alert.alert_message
    
    def test_out_of_stock_alert_message(self):
        """Test out of stock alert message generation"""
        alert = StockAlert(
            item_id=1,
            item_name="Test Item",
            current_quantity=0,
            min_quantity=5,
            stock_level=StockLevel.OUT_OF_STOCK,
            category="test"
        )
        
        assert "OUT OF STOCK" in alert.alert_message
        assert "Test Item" in alert.alert_message
    
    def test_low_stock_alert_message(self):
        """Test low stock alert message generation"""
        alert = StockAlert(
            item_id=1,
            item_name="Test Item",
            current_quantity=5,
            min_quantity=5,
            stock_level=StockLevel.LOW,
            category="test"
        )
        
        assert "LOW STOCK" in alert.alert_message
        assert "5 units" in alert.alert_message


@pytest.fixture
def inventory_manager():
    """Create an InventoryManager instance for testing"""
    return InventoryManager()


@pytest.fixture
def mock_connection():
    """Create a mock database connection"""
    conn = AsyncMock()
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.execute = AsyncMock()
    conn.close = AsyncMock()
    conn.transaction = AsyncMock()
    return conn


class TestInventoryManager:
    """Test InventoryManager class functionality"""
    
    @pytest.mark.asyncio
    async def test_reserve_equipment_success(self, inventory_manager, mock_connection):
        """Test successful equipment reservation - Requirement 7.1"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock database responses
            mock_connection.fetchrow.return_value = {'quantity_in_stock': 100, 'name': 'Test Cable'}
            
            equipment_list = [
                {'material_id': 1, 'quantity': 10, 'performed_by': 100}
            ]
            
            result = await inventory_manager.reserve_equipment("req-123", equipment_list)
            
            assert result is True
            assert "req-123" in inventory_manager._reserved_items
            assert len(inventory_manager._reserved_items["req-123"]) == 1
    
    @pytest.mark.asyncio
    async def test_reserve_equipment_insufficient_stock(self, inventory_manager, mock_connection):
        """Test equipment reservation with insufficient stock"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock insufficient stock
            mock_connection.fetchrow.return_value = {'quantity_in_stock': 5, 'name': 'Test Cable'}
            
            equipment_list = [
                {'material_id': 1, 'quantity': 10, 'performed_by': 100}
            ]
            
            result = await inventory_manager.reserve_equipment("req-123", equipment_list)
            
            assert result is False
            assert "req-123" not in inventory_manager._reserved_items
    
    @pytest.mark.asyncio
    async def test_consume_equipment_success(self, inventory_manager, mock_connection):
        """Test successful equipment consumption - Requirements 7.2, 7.3"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock successful consumption
            mock_connection.fetchrow.return_value = {'name': 'Test Cable', 'quantity_in_stock': 90}
            mock_connection.transaction.return_value.__aenter__ = AsyncMock()
            mock_connection.transaction.return_value.__aexit__ = AsyncMock()
            
            # Set up reservation first
            inventory_manager._reserved_items["req-123"] = [{'material_id': 1, 'quantity': 10}]
            
            equipment_used = [
                {'material_id': 1, 'quantity': 10, 'performed_by': 100}
            ]
            
            result = await inventory_manager.consume_equipment("req-123", equipment_used)
            
            assert result is True
            assert "req-123" not in inventory_manager._reserved_items  # Reservation should be cleared
    
    @pytest.mark.asyncio
    async def test_consume_equipment_insufficient_stock(self, inventory_manager, mock_connection):
        """Test equipment consumption with insufficient stock"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock insufficient stock (fetchrow returns None)
            mock_connection.fetchrow.return_value = None
            mock_connection.transaction.return_value.__aenter__ = AsyncMock()
            mock_connection.transaction.return_value.__aexit__ = AsyncMock(side_effect=Exception("Insufficient stock"))
            
            equipment_used = [
                {'material_id': 1, 'quantity': 10, 'performed_by': 100}
            ]
            
            result = await inventory_manager.consume_equipment("req-123", equipment_used)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_stock_levels_all_items(self, inventory_manager, mock_connection):
        """Test checking stock levels for all items - Requirement 7.5"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock database response
            mock_connection.fetch.return_value = [
                {
                    'id': 1, 'name': 'Cable A', 'category': 'cables',
                    'quantity_in_stock': 50, 'min_quantity': 10,
                    'unit': 'meters', 'location': 'A1', 'supplier': 'Supplier1'
                },
                {
                    'id': 2, 'name': 'Cable B', 'category': 'cables',
                    'quantity_in_stock': 5, 'min_quantity': 10,
                    'unit': 'meters', 'location': 'A2', 'supplier': 'Supplier2'
                },
                {
                    'id': 3, 'name': 'Router', 'category': 'equipment',
                    'quantity_in_stock': 0, 'min_quantity': 5,
                    'unit': 'pcs', 'location': 'B1', 'supplier': 'Supplier3'
                }
            ]
            
            result = await inventory_manager.check_stock_levels()
            
            assert result['total_items'] == 3
            assert result['normal_stock'] == 1  # Cable A
            assert result['low_stock'] == 1     # Cable B
            assert result['out_of_stock'] == 1  # Router
            assert len(result['items']) == 3
    
    @pytest.mark.asyncio
    async def test_check_stock_levels_filtered(self, inventory_manager, mock_connection):
        """Test checking stock levels with category filter"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock database response for cables only
            mock_connection.fetch.return_value = [
                {
                    'id': 1, 'name': 'Cable A', 'category': 'cables',
                    'quantity_in_stock': 50, 'min_quantity': 10,
                    'unit': 'meters', 'location': 'A1', 'supplier': 'Supplier1'
                }
            ]
            
            result = await inventory_manager.check_stock_levels("cables")
            
            assert result['total_items'] == 1
            assert result['normal_stock'] == 1
            assert result['items'][0]['category'] == 'cables'
    
    @pytest.mark.asyncio
    async def test_generate_stock_alerts(self, inventory_manager, mock_connection):
        """Test generating stock alerts - Requirement 7.5"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock low stock items
            mock_connection.fetch.return_value = [
                {
                    'id': 1, 'name': 'Low Stock Cable', 'category': 'cables',
                    'quantity_in_stock': 3, 'min_quantity': 10, 'location': 'A1'
                },
                {
                    'id': 2, 'name': 'Out of Stock Router', 'category': 'equipment',
                    'quantity_in_stock': 0, 'min_quantity': 5, 'location': 'B1'
                }
            ]
            
            alerts = await inventory_manager.generate_stock_alerts()
            
            assert len(alerts) == 2
            assert alerts[0].item_name == 'Low Stock Cable'
            assert alerts[0].stock_level == StockLevel.CRITICAL
            assert alerts[1].item_name == 'Out of Stock Router'
            assert alerts[1].stock_level == StockLevel.OUT_OF_STOCK
    
    @pytest.mark.asyncio
    async def test_get_transaction_history(self, inventory_manager, mock_connection):
        """Test getting transaction history - Requirement 7.4"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock transaction history
            mock_connection.fetch.return_value = [
                {
                    'id': 1, 'request_id': 'req-123', 'material_id': 1,
                    'transaction_type': 'consume', 'quantity': 10,
                    'performed_by': 100, 'transaction_date': datetime.now(),
                    'notes': 'Test consumption', 'material_name': 'Test Cable',
                    'category': 'cables', 'performed_by_name': 'John Doe'
                }
            ]
            
            history = await inventory_manager.get_transaction_history(request_id="req-123")
            
            assert len(history) == 1
            assert history[0]['request_id'] == 'req-123'
            assert history[0]['material_name'] == 'Test Cable'
            assert history[0]['transaction_type'] == 'consume'
            assert history[0]['quantity'] == 10
    
    @pytest.mark.asyncio
    async def test_confirm_inventory_update(self, inventory_manager, mock_connection):
        """Test confirming inventory updates to technician - Requirement 7.6"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock transaction history
            mock_connection.fetch.return_value = [
                {
                    'id': 1, 'request_id': 'req-123', 'material_id': 1,
                    'transaction_type': 'consume', 'quantity': 10,
                    'performed_by': 100, 'transaction_date': datetime.now(),
                    'notes': 'Test consumption', 'material_name': 'Test Cable',
                    'category': 'cables', 'performed_by_name': 'John Doe'
                }
            ]
            
            result = await inventory_manager.confirm_inventory_update("req-123", 200)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_confirm_inventory_update_no_transactions(self, inventory_manager, mock_connection):
        """Test confirming inventory updates with no transactions"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock empty transaction history
            mock_connection.fetch.return_value = []
            
            result = await inventory_manager.confirm_inventory_update("req-123", 200)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_inventory_summary(self, inventory_manager, mock_connection):
        """Test getting comprehensive inventory summary"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock statistics
            mock_connection.fetchrow.return_value = {
                'total_items': 100,
                'total_quantity': 1000,
                'total_value': 50000.0,
                'low_stock_items': 5,
                'out_of_stock_items': 2
            }
            
            # Mock category breakdown
            mock_connection.fetch.side_effect = [
                [
                    {'category': 'cables', 'item_count': 50, 'total_quantity': 500},
                    {'category': 'equipment', 'item_count': 30, 'total_quantity': 300}
                ],
                [
                    {'transaction_type': 'consume', 'transaction_count': 20, 'total_quantity': 100},
                    {'transaction_type': 'reserve', 'transaction_count': 15, 'total_quantity': 75}
                ]
            ]
            
            summary = await inventory_manager.get_inventory_summary()
            
            assert summary['total_items'] == 100
            assert summary['total_quantity'] == 1000
            assert summary['total_value'] == 50000.0
            assert summary['low_stock_items'] == 5
            assert summary['out_of_stock_items'] == 2
            assert len(summary['categories']) == 2
            assert len(summary['recent_transactions']) == 2
    
    def test_get_reserved_items(self, inventory_manager):
        """Test getting reserved items for a request"""
        # Set up reservation
        equipment_list = [{'material_id': 1, 'quantity': 10}]
        inventory_manager._reserved_items["req-123"] = equipment_list
        
        reserved = inventory_manager.get_reserved_items("req-123")
        
        assert len(reserved) == 1
        assert reserved[0]['material_id'] == 1
        assert reserved[0]['quantity'] == 10
    
    def test_get_reserved_items_not_found(self, inventory_manager):
        """Test getting reserved items for non-existent request"""
        reserved = inventory_manager.get_reserved_items("req-nonexistent")
        
        assert len(reserved) == 0
    
    @pytest.mark.asyncio
    async def test_cancel_reservation(self, inventory_manager, mock_connection):
        """Test cancelling equipment reservation"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Set up reservation
            equipment_list = [{'material_id': 1, 'quantity': 10, 'performed_by': 100}]
            inventory_manager._reserved_items["req-123"] = equipment_list
            
            result = await inventory_manager.cancel_reservation("req-123")
            
            assert result is True
            assert "req-123" not in inventory_manager._reserved_items
    
    @pytest.mark.asyncio
    async def test_cancel_reservation_not_found(self, inventory_manager):
        """Test cancelling non-existent reservation"""
        result = await inventory_manager.cancel_reservation("req-nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_log_transaction(self, inventory_manager, mock_connection):
        """Test logging inventory transaction"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            mock_connection.fetchrow.return_value = {'id': 1}
            
            transaction = InventoryTransaction(
                request_id="req-123",
                material_id=1,
                transaction_type=TransactionType.CONSUME.value,
                quantity=10,
                performed_by=100,
                notes="Test transaction"
            )
            
            result = await inventory_manager._log_transaction(transaction)
            
            assert result is True
            assert transaction.id == 1
    
    @pytest.mark.asyncio
    async def test_log_transaction_failure(self, inventory_manager, mock_connection):
        """Test logging transaction failure"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            mock_connection.fetchrow.return_value = None
            
            transaction = InventoryTransaction(
                request_id="req-123",
                material_id=1,
                transaction_type=TransactionType.CONSUME.value,
                quantity=10
            )
            
            result = await inventory_manager._log_transaction(transaction)
            
            assert result is False


class TestInventoryManagerIntegration:
    """Integration tests for InventoryManager with workflow system"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self, inventory_manager, mock_connection):
        """Test complete workflow: reserve -> consume -> confirm"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock database responses for reservation
            mock_connection.fetchrow.side_effect = [
                {'quantity_in_stock': 100, 'name': 'Test Cable'},  # For reservation check
                {'name': 'Test Cable', 'quantity_in_stock': 90},   # For consumption
                {'id': 1}, {'id': 2}  # For transaction logging
            ]
            mock_connection.transaction.return_value.__aenter__ = AsyncMock()
            mock_connection.transaction.return_value.__aexit__ = AsyncMock()
            
            # Mock transaction history for confirmation
            mock_connection.fetch.return_value = [
                {
                    'id': 1, 'request_id': 'req-123', 'material_id': 1,
                    'transaction_type': 'consume', 'quantity': 10,
                    'performed_by': 100, 'transaction_date': datetime.now(),
                    'notes': 'Test consumption', 'material_name': 'Test Cable',
                    'category': 'cables', 'performed_by_name': 'John Doe'
                }
            ]
            
            equipment_list = [{'material_id': 1, 'quantity': 10, 'performed_by': 100}]
            
            # Step 1: Reserve equipment
            reserve_result = await inventory_manager.reserve_equipment("req-123", equipment_list)
            assert reserve_result is True
            
            # Step 2: Consume equipment
            consume_result = await inventory_manager.consume_equipment("req-123", equipment_list)
            assert consume_result is True
            
            # Step 3: Confirm to technician
            confirm_result = await inventory_manager.confirm_inventory_update("req-123", 200)
            assert confirm_result is True
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, inventory_manager, mock_connection):
        """Test error handling throughout the workflow"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            # Mock database error
            mock_connection.fetchrow.side_effect = Exception("Database error")
            
            equipment_list = [{'material_id': 1, 'quantity': 10, 'performed_by': 100}]
            
            # Should handle errors gracefully
            result = await inventory_manager.reserve_equipment("req-123", equipment_list)
            assert result is False
    
    @pytest.mark.asyncio
    async def test_concurrent_reservations(self, inventory_manager, mock_connection):
        """Test handling concurrent reservations"""
        with patch('utils.inventory_manager.get_connection', return_value=mock_connection):
            mock_connection.fetchrow.return_value = {'quantity_in_stock': 100, 'name': 'Test Cable'}
            
            equipment_list1 = [{'material_id': 1, 'quantity': 10, 'performed_by': 100}]
            equipment_list2 = [{'material_id': 1, 'quantity': 15, 'performed_by': 101}]
            
            # Simulate concurrent reservations
            task1 = inventory_manager.reserve_equipment("req-123", equipment_list1)
            task2 = inventory_manager.reserve_equipment("req-124", equipment_list2)
            
            results = await asyncio.gather(task1, task2)
            
            assert results[0] is True
            assert results[1] is True
            assert len(inventory_manager._reserved_items) == 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])