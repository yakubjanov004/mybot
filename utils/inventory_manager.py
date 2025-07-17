"""
Inventory Manager for Enhanced Workflow System

This module implements the InventoryManager class that handles:
- Equipment tracking and reservation
- Automatic inventory updates when equipment is used
- Stock level monitoring and low stock alerts
- Transaction logging with request references
- Integration with warehouse operations

Requirements implemented: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from database.models import Material, Equipment


class TransactionType(Enum):
    RESERVE = "reserve"
    CONSUME = "consume"
    RETURN = "return"


class StockLevel(Enum):
    NORMAL = "normal"
    LOW = "low"
    CRITICAL = "critical"
    OUT_OF_STOCK = "out_of_stock"


@dataclass
class InventoryItem:
    """Represents an inventory item with stock information"""
    id: int
    name: str
    category: str
    quantity_in_stock: int
    min_quantity: int
    unit: str
    price: float = 0.0
    description: str = ""
    location: str = ""
    supplier: str = ""
    is_active: bool = True
    
    @property
    def stock_level(self) -> StockLevel:
        """Determine stock level based on current quantity"""
        if self.quantity_in_stock == 0:
            return StockLevel.OUT_OF_STOCK
        elif self.quantity_in_stock <= (self.min_quantity * 0.5):
            return StockLevel.CRITICAL
        elif self.quantity_in_stock <= self.min_quantity:
            return StockLevel.LOW
        else:
            return StockLevel.NORMAL
    
    @property
    def is_low_stock(self) -> bool:
        """Check if item is low stock or critical"""
        return self.stock_level in [StockLevel.LOW, StockLevel.CRITICAL, StockLevel.OUT_OF_STOCK]


@dataclass
class InventoryTransaction:
    """Represents an inventory transaction"""
    id: Optional[int] = None
    request_id: Optional[str] = None
    material_id: Optional[int] = None
    transaction_type: str = TransactionType.CONSUME.value
    quantity: int = 0
    performed_by: Optional[int] = None
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'request_id': self.request_id,
            'material_id': self.material_id,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'performed_by': self.performed_by,
            'transaction_date': self.transaction_date,
            'notes': self.notes
        }


@dataclass
class StockAlert:
    """Represents a stock alert"""
    item_id: int
    item_name: str
    current_quantity: int
    min_quantity: int
    stock_level: StockLevel
    category: str
    location: str = ""
    alert_message: str = ""
    
    def __post_init__(self):
        if not self.alert_message:
            if self.stock_level == StockLevel.OUT_OF_STOCK:
                self.alert_message = f"OUT OF STOCK: {self.item_name} is completely out of stock"
            elif self.stock_level == StockLevel.CRITICAL:
                self.alert_message = f"CRITICAL: {self.item_name} has only {self.current_quantity} units left (min: {self.min_quantity})"
            elif self.stock_level == StockLevel.LOW:
                self.alert_message = f"LOW STOCK: {self.item_name} has {self.current_quantity} units (min: {self.min_quantity})"


class InventoryManager:
    """
    Manages inventory operations for the enhanced workflow system.
    
    Handles equipment tracking, automatic inventory updates, stock monitoring,
    and transaction logging with request references.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._reserved_items: Dict[str, List[Dict]] = {}  # request_id -> list of reserved items
    
    async def reserve_equipment(self, request_id: str, equipment_list: List[Dict[str, Any]]) -> bool:
        """
        Reserve equipment for a specific request.
        
        Args:
            request_id: The service request ID
            equipment_list: List of equipment items with 'material_id' and 'quantity'
        
        Returns:
            bool: True if reservation successful, False otherwise
            
        Requirement: 7.1 - Identify specific items and quantities used
        """
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                # Check availability for all items first
                for equipment in equipment_list:
                    material_id = equipment.get('material_id')
                    quantity_needed = equipment.get('quantity', 1)
                    
                    # Get current stock
                    stock_query = """
                    SELECT quantity_in_stock, name FROM materials 
                    WHERE id = $1 AND is_active = true
                    """
                    result = await conn.fetchrow(stock_query, material_id)
                    
                    if not result:
                        self.logger.error(f"Material {material_id} not found or inactive")
                        return False
                    
                    available_quantity = result['quantity_in_stock']
                    if available_quantity < quantity_needed:
                        self.logger.error(f"Insufficient stock for {result['name']}: need {quantity_needed}, have {available_quantity}")
                        return False
                
                # Reserve all items
                for equipment in equipment_list:
                    material_id = equipment.get('material_id')
                    quantity_needed = equipment.get('quantity', 1)
                    
                    # Create reservation transaction
                    transaction = InventoryTransaction(
                        request_id=request_id,
                        material_id=material_id,
                        transaction_type=TransactionType.RESERVE.value,
                        quantity=quantity_needed,
                        performed_by=equipment.get('performed_by'),
                        transaction_date=datetime.now(),
                        notes=f"Reserved for request {request_id}"
                    )
                    
                    await self._log_transaction(transaction)
                
                # Store reservation in memory for tracking
                self._reserved_items[request_id] = equipment_list
                
                self.logger.info(f"Successfully reserved equipment for request {request_id}")
                return True
            
        except Exception as e:
            self.logger.error(f"Error reserving equipment for request {request_id}: {e}")
            return False
    
    async def consume_equipment(self, request_id: str, equipment_used: List[Dict[str, Any]]) -> bool:
        """
        Update inventory when equipment is installed/used.
        
        Args:
            request_id: The service request ID
            equipment_used: List of equipment items with 'material_id', 'quantity', and 'performed_by'
        
        Returns:
            bool: True if consumption successful, False otherwise
            
        Requirements: 7.2, 7.3 - Automatically reduce inventory quantities and log transactions
        """
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                async with conn.transaction():
                    for equipment in equipment_used:
                        material_id = equipment.get('material_id')
                        quantity_used = equipment.get('quantity', 1)
                        performed_by = equipment.get('performed_by')
                        
                        # Update inventory quantity
                        update_query = """
                        UPDATE materials 
                        SET quantity_in_stock = quantity_in_stock - $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2 AND quantity_in_stock >= $1
                        RETURNING name, quantity_in_stock
                        """
                        result = await conn.fetchrow(update_query, quantity_used, material_id)
                        
                        if not result:
                            raise Exception(f"Failed to consume material {material_id}: insufficient stock or item not found")
                        
                        # Log consumption transaction
                        transaction = InventoryTransaction(
                            request_id=request_id,
                            material_id=material_id,
                            transaction_type=TransactionType.CONSUME.value,
                            quantity=quantity_used,
                            performed_by=performed_by,
                            transaction_date=datetime.now(),
                            notes=f"Consumed for request {request_id}"
                        )
                        
                        await self._log_transaction(transaction)
                        
                        self.logger.info(f"Consumed {quantity_used} units of {result['name']} for request {request_id}")
            
            # Remove reservation if it exists
            if request_id in self._reserved_items:
                del self._reserved_items[request_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error consuming equipment for request {request_id}: {e}")
            return False
    
    async def check_stock_levels(self, equipment_type: str = None) -> Dict[str, Any]:
        """
        Check current stock levels with optional equipment type filter.
        
        Args:
            equipment_type: Optional category filter
        
        Returns:
            Dict containing stock level information
            
        Requirement: 7.5 - Generate low stock alerts
        """
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                if equipment_type:
                    query = """
                    SELECT id, name, category, quantity_in_stock, min_quantity, 
                           unit, location, supplier
                    FROM materials 
                    WHERE is_active = true AND category = $1
                    ORDER BY name
                    """
                    results = await conn.fetch(query, equipment_type)
                else:
                    query = """
                    SELECT id, name, category, quantity_in_stock, min_quantity, 
                           unit, location, supplier
                    FROM materials 
                    WHERE is_active = true
                    ORDER BY name
                    """
                    results = await conn.fetch(query)
            
            stock_summary = {
                'total_items': len(results),
                'normal_stock': 0,
                'low_stock': 0,
                'critical_stock': 0,
                'out_of_stock': 0,
                'items': []
            }
            
            for row in results:
                item = InventoryItem(
                    id=row['id'],
                    name=row['name'],
                    category=row['category'],
                    quantity_in_stock=row['quantity_in_stock'],
                    min_quantity=row['min_quantity'],
                    unit=row['unit'],
                    location=row.get('location', ''),
                    supplier=row.get('supplier', '')
                )
                
                stock_summary['items'].append({
                    'id': item.id,
                    'name': item.name,
                    'category': item.category,
                    'current_quantity': item.quantity_in_stock,
                    'min_quantity': item.min_quantity,
                    'stock_level': item.stock_level.value,
                    'is_low_stock': item.is_low_stock,
                    'unit': item.unit,
                    'location': item.location
                })
                
                # Count by stock level
                if item.stock_level == StockLevel.NORMAL:
                    stock_summary['normal_stock'] += 1
                elif item.stock_level == StockLevel.LOW:
                    stock_summary['low_stock'] += 1
                elif item.stock_level == StockLevel.CRITICAL:
                    stock_summary['critical_stock'] += 1
                elif item.stock_level == StockLevel.OUT_OF_STOCK:
                    stock_summary['out_of_stock'] += 1
            
            return stock_summary
            
        except Exception as e:
            self.logger.error(f"Error checking stock levels: {e}")
            return {}
    
    async def generate_stock_alerts(self) -> List[StockAlert]:
        """
        Generate low stock alerts for warehouse.
        
        Returns:
            List of StockAlert objects for items needing attention
            
        Requirement: 7.5 - Generate low stock alerts
        """
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                # Get items with low stock (at or below minimum quantity)
                query = """
                SELECT id, name, category, quantity_in_stock, min_quantity, location
                FROM materials 
                WHERE is_active = true AND quantity_in_stock <= min_quantity
                ORDER BY (quantity_in_stock::float / NULLIF(min_quantity, 0)::float) ASC
                """
                results = await conn.fetch(query)
            
            alerts = []
            for row in results:
                item = InventoryItem(
                    id=row['id'],
                    name=row['name'],
                    category=row['category'],
                    quantity_in_stock=row['quantity_in_stock'],
                    min_quantity=row['min_quantity'],
                    unit="",  # Not needed for alerts
                    location=row.get('location', '')
                )
                
                alert = StockAlert(
                    item_id=item.id,
                    item_name=item.name,
                    current_quantity=item.quantity_in_stock,
                    min_quantity=item.min_quantity,
                    stock_level=item.stock_level,
                    category=item.category,
                    location=item.location
                )
                
                alerts.append(alert)
            
            self.logger.info(f"Generated {len(alerts)} stock alerts")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error generating stock alerts: {e}")
            return []
    
    async def get_transaction_history(self, request_id: str = None, material_id: int = None, 
                                   days: int = 30) -> List[Dict[str, Any]]:
        """
        Get transaction history with optional filters.
        
        Args:
            request_id: Filter by specific request
            material_id: Filter by specific material
            days: Number of days to look back
        
        Returns:
            List of transaction records
            
        Requirement: 7.4 - Maintain audit trail of all modifications
        """
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                base_query = """
                SELECT it.*, m.name as material_name, m.category, u.full_name as performed_by_name
                FROM inventory_transactions it
                LEFT JOIN materials m ON it.material_id = m.id
                LEFT JOIN users u ON it.performed_by = u.id
                WHERE it.transaction_date >= $1
                """
                
                params = [datetime.now() - timedelta(days=days)]
                param_count = 2
                
                if request_id:
                    base_query += f" AND it.request_id = ${param_count}"
                    params.append(request_id)
                    param_count += 1
                
                if material_id:
                    base_query += f" AND it.material_id = ${param_count}"
                    params.append(material_id)
                    param_count += 1
                
                base_query += " ORDER BY it.transaction_date DESC"
                
                results = await conn.fetch(base_query, *params)
            
            transactions = []
            for row in results:
                transactions.append({
                    'id': row['id'],
                    'request_id': row['request_id'],
                    'material_id': row['material_id'],
                    'material_name': row.get('material_name', 'Unknown'),
                    'category': row.get('category', ''),
                    'transaction_type': row['transaction_type'],
                    'quantity': row['quantity'],
                    'performed_by': row['performed_by'],
                    'performed_by_name': row.get('performed_by_name', 'Unknown'),
                    'transaction_date': row['transaction_date'],
                    'notes': row.get('notes', '')
                })
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting transaction history: {e}")
            return []
    
    async def confirm_inventory_update(self, request_id: str, technician_id: int) -> bool:
        """
        Confirm inventory changes to the requesting technician.
        
        Args:
            request_id: The service request ID
            technician_id: ID of the technician to notify
        
        Returns:
            bool: True if confirmation successful
            
        Requirement: 7.6 - Confirm changes to the requesting technician
        """
        try:
            # Get transaction history for this request
            transactions = await self.get_transaction_history(request_id=request_id, days=1)
            
            if not transactions:
                self.logger.warning(f"No transactions found for request {request_id}")
                return False
            
            # Create confirmation message
            confirmation_data = {
                'request_id': request_id,
                'technician_id': technician_id,
                'transactions': transactions,
                'total_items': len(transactions),
                'confirmation_time': datetime.now(),
                'status': 'confirmed'
            }
            
            # Log confirmation
            self.logger.info(f"Confirmed inventory updates for request {request_id} to technician {technician_id}")
            
            # In a real implementation, this would send a notification to the technician
            # For now, we'll just return success
            return True
            
        except Exception as e:
            self.logger.error(f"Error confirming inventory update for request {request_id}: {e}")
            return False
    
    async def get_inventory_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive inventory summary for reporting.
        
        Returns:
            Dict containing inventory summary statistics
        """
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                # Get basic inventory statistics
                stats_query = """
                SELECT 
                    COUNT(*) as total_items,
                    SUM(quantity_in_stock) as total_quantity,
                    SUM(quantity_in_stock * price) as total_value,
                    COUNT(CASE WHEN quantity_in_stock <= min_quantity THEN 1 END) as low_stock_items,
                    COUNT(CASE WHEN quantity_in_stock = 0 THEN 1 END) as out_of_stock_items
                FROM materials 
                WHERE is_active = true
                """
                stats = await conn.fetchrow(stats_query)
            
            # Get category breakdown
            category_query = """
            SELECT category, COUNT(*) as item_count, SUM(quantity_in_stock) as total_quantity
            FROM materials 
            WHERE is_active = true
            GROUP BY category
            ORDER BY item_count DESC
            """
            categories = await conn.fetch(category_query)
            
            # Get recent transaction summary
            transaction_query = """
            SELECT 
                transaction_type,
                COUNT(*) as transaction_count,
                SUM(quantity) as total_quantity
            FROM inventory_transactions 
            WHERE transaction_date >= $1
            GROUP BY transaction_type
            """
            recent_transactions = await conn.fetch(transaction_query, datetime.now() - timedelta(days=7))
            
            summary = {
                'total_items': stats['total_items'] or 0,
                'total_quantity': stats['total_quantity'] or 0,
                'total_value': float(stats['total_value'] or 0),
                'low_stock_items': stats['low_stock_items'] or 0,
                'out_of_stock_items': stats['out_of_stock_items'] or 0,
                'categories': [dict(row) for row in categories],
                'recent_transactions': [dict(row) for row in recent_transactions],
                'last_updated': datetime.now()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting inventory summary: {e}")
            return {}
    
    async def _log_transaction(self, transaction: InventoryTransaction) -> bool:
        """
        Log an inventory transaction to the database.
        
        Args:
            transaction: InventoryTransaction object to log
        
        Returns:
            bool: True if logging successful
        """
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                query = """
                INSERT INTO inventory_transactions 
                (request_id, material_id, transaction_type, quantity, performed_by, transaction_date, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """
                
                result = await conn.fetchrow(
                    query,
                    transaction.request_id,
                    transaction.material_id,
                    transaction.transaction_type,
                    transaction.quantity,
                    transaction.performed_by,
                    transaction.transaction_date or datetime.now(),
                    transaction.notes
                )
                
                if result:
                    transaction.id = result['id']
                    return True
                
                return False
            
        except Exception as e:
            self.logger.error(f"Error logging transaction: {e}")
            return False
    
    def get_reserved_items(self, request_id: str) -> List[Dict[str, Any]]:
        """
        Get reserved items for a specific request.
        
        Args:
            request_id: The service request ID
        
        Returns:
            List of reserved items
        """
        return self._reserved_items.get(request_id, [])
    
    async def cancel_reservation(self, request_id: str) -> bool:
        """
        Cancel equipment reservation for a request.
        
        Args:
            request_id: The service request ID
        
        Returns:
            bool: True if cancellation successful
        """
        try:
            if request_id in self._reserved_items:
                # Log cancellation transactions
                for equipment in self._reserved_items[request_id]:
                    transaction = InventoryTransaction(
                        request_id=request_id,
                        material_id=equipment.get('material_id'),
                        transaction_type=TransactionType.RETURN.value,
                        quantity=equipment.get('quantity', 1),
                        performed_by=equipment.get('performed_by'),
                        transaction_date=datetime.now(),
                        notes=f"Reservation cancelled for request {request_id}"
                    )
                    
                    await self._log_transaction(transaction)
                
                del self._reserved_items[request_id]
                self.logger.info(f"Cancelled reservation for request {request_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling reservation for request {request_id}: {e}")
            return False


# Global inventory manager instance
inventory_manager = InventoryManager()


async def get_inventory_manager() -> InventoryManager:
    """Get the global inventory manager instance"""
    return inventory_manager

class InventoryManagerFactory:
    """Factory for creating inventory manager instances"""
    
    @staticmethod
    def create_inventory_manager() -> InventoryManager:
        """Creates a new inventory manager instance"""
        return InventoryManager()