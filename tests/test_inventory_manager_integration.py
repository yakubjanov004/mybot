"""
Simple integration test for InventoryManager instantiation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.inventory_manager import InventoryManager, get_inventory_manager

def test_inventory_manager_creation():
    """Test that InventoryManager can be created"""
    manager = InventoryManager()
    assert manager is not None
    assert hasattr(manager, 'logger')
    assert hasattr(manager, '_reserved_items')
    assert len(manager._reserved_items) == 0

def test_get_inventory_manager():
    """Test the global inventory manager function"""
    import asyncio
    
    async def test_async():
        manager = await get_inventory_manager()
        assert manager is not None
        assert isinstance(manager, InventoryManager)
    
    asyncio.run(test_async())

def test_reserved_items_operations():
    """Test basic reserved items operations"""
    manager = InventoryManager()
    
    # Test getting reserved items for non-existent request
    reserved = manager.get_reserved_items("req-nonexistent")
    assert len(reserved) == 0
    
    # Test setting reserved items
    equipment_list = [{'material_id': 1, 'quantity': 10}]
    manager._reserved_items["req-123"] = equipment_list
    
    reserved = manager.get_reserved_items("req-123")
    assert len(reserved) == 1
    assert reserved[0]['material_id'] == 1
    assert reserved[0]['quantity'] == 10

if __name__ == "__main__":
    test_inventory_manager_creation()
    test_get_inventory_manager()
    test_reserved_items_operations()
    print("All integration tests passed!")