"""
Simple unit tests for InventoryManager

Tests the core functionality without database dependencies.
"""

import pytest
from datetime import datetime
from typing import Dict, List, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.inventory_manager import (
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


class TestEnums:
    """Test enum classes"""
    
    def test_transaction_type_enum(self):
        """Test TransactionType enum values"""
        assert TransactionType.RESERVE.value == "reserve"
        assert TransactionType.CONSUME.value == "consume"
        assert TransactionType.RETURN.value == "return"
    
    def test_stock_level_enum(self):
        """Test StockLevel enum values"""
        assert StockLevel.NORMAL.value == "normal"
        assert StockLevel.LOW.value == "low"
        assert StockLevel.CRITICAL.value == "critical"
        assert StockLevel.OUT_OF_STOCK.value == "out_of_stock"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])