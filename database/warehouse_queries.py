import asyncpg
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from config import config

# Database connection pool
_pool = None

class WarehouseDatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def init_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                min_size=1,
                max_size=10
            )
            logging.info("Warehouse database pool initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize warehouse database pool: {e}")
            raise
    
    async def get_connection(self):
        """Get connection from pool"""
        if not self.pool:
            await self.init_pool()
        return await self.pool.acquire()
    
    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()

# Global warehouse database manager instance
warehouse_db_manager = WarehouseDatabaseManager()

async def get_warehouse_connection():
    """Get warehouse database connection"""
    return await warehouse_db_manager.get_connection()

# ==================== INVENTORY MANAGEMENT ====================

async def get_all_inventory_items(category: str = None) -> List[Dict]:
    """Get all inventory items with optional category filter"""
    conn = await warehouse_db_manager.get_connection()
    try:
        if category:
            query = """
            SELECT * FROM materials 
            WHERE is_active = true AND category = $1 
            ORDER BY name
            """
            results = await conn.fetch(query, category)
        else:
            query = """
            SELECT * FROM materials 
            WHERE is_active = true 
            ORDER BY name
            """
            results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting inventory items: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def add_new_inventory_item(item_data: Dict) -> Optional[int]:
    """Add new inventory item"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        INSERT INTO materials (name, quantity, unit, min_quantity, description, category, price, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, true)
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            item_data['name'],
            item_data['quantity'],
            item_data.get('unit', 'pcs'),
            item_data.get('min_quantity', 5),
            item_data.get('description', ''),
            item_data.get('category', 'general'),
            item_data.get('price', 0)
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error adding inventory item: {e}")
        return None
    finally:
        await warehouse_db_manager.pool.release(conn)

async def update_inventory_item_data(item_id: int, item_data: Dict) -> bool:
    """Update inventory item data"""
    conn = await warehouse_db_manager.get_connection()
    try:
        fields = []
        values = []
        param_count = 1
        
        for field, value in item_data.items():
            if field in ['name', 'quantity', 'unit', 'min_quantity', 'description', 'category', 'price']:
                fields.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
        
        if not fields:
            return False
        
        fields.append(f"updated_at = ${param_count}")
        values.append(datetime.now())
        param_count += 1
        
        query = f"UPDATE materials SET {', '.join(fields)} WHERE id = ${param_count}"
        values.append(item_id)
        
        await conn.execute(query, *values)
        return True
    except Exception as e:
        logging.error(f"Error updating inventory item: {e}")
        return False
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_inventory_item_by_id(item_id: int) -> Optional[Dict]:
    """Get inventory item by ID"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = "SELECT * FROM materials WHERE id = $1 AND is_active = true"
        result = await conn.fetchrow(query, item_id)
        return dict(result) if result else None
    except Exception as e:
        logging.error(f"Error getting inventory item by ID: {e}")
        return None
    finally:
        await warehouse_db_manager.pool.release(conn)

async def search_inventory_items(search_query: str) -> List[Dict]:
    """Search inventory items by name or description"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT * FROM materials 
        WHERE is_active = true 
        AND (name ILIKE $1 OR description ILIKE $1)
        ORDER BY name
        """
        results = await conn.fetch(query, f"%{search_query}%")
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error searching inventory items: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_low_stock_inventory_items() -> List[Dict]:
    """Get items with low stock"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT * FROM materials
        WHERE is_active = true AND quantity <= min_quantity
        ORDER BY (quantity::float / min_quantity::float) ASC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting low stock items: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_out_of_stock_items() -> List[Dict]:
    """Get items that are out of stock"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT * FROM materials
        WHERE is_active = true AND quantity = 0
        ORDER BY name
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting out of stock items: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def update_inventory_quantity(item_id: int, quantity: int, operation: str) -> bool:
    """Update inventory quantity"""
    conn = await warehouse_db_manager.get_connection()
    try:
        if operation == 'add':
            query = "UPDATE materials SET quantity = quantity + $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
        elif operation == 'subtract':
            query = "UPDATE materials SET quantity = quantity - $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 AND quantity >= $1"
        else:  # set
            query = "UPDATE materials SET quantity = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
        
        result = await conn.execute(query, quantity, item_id)
        return result != "UPDATE 0"
    except Exception as e:
        logging.error(f"Error updating inventory quantity: {e}")
        return False
    finally:
        await warehouse_db_manager.pool.release(conn)

# ==================== ORDERS MANAGEMENT ====================

async def get_warehouse_orders_by_status(statuses: List[str]) -> List[Dict]:
    """Get orders by status for warehouse"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT z.*, u.full_name as client_name, u.phone_number as client_phone,
               t.full_name as technician_name, t.phone_number as technician_phone
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        WHERE z.status = ANY($1)
        ORDER BY z.created_at DESC
        """
        results = await conn.fetch(query, statuses)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting orders by status: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_pending_warehouse_orders() -> List[Dict]:
    """Get pending orders for warehouse processing"""
    return await get_warehouse_orders_by_status(['new', 'confirmed'])

async def get_in_progress_warehouse_orders() -> List[Dict]:
    """Get in progress orders"""
    return await get_warehouse_orders_by_status(['in_progress', 'assigned'])

async def get_completed_warehouse_orders(limit: int = 10) -> List[Dict]:
    """Get completed orders with limit"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT z.*, u.full_name as client_name, u.phone_number as client_phone,
               t.full_name as technician_name, t.phone_number as technician_phone
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        WHERE z.status = 'completed'
        ORDER BY z.completed_at DESC
        LIMIT $1
        """
        results = await conn.fetch(query, limit)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting completed orders: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def update_order_status_warehouse(order_id: int, status: str, updated_by: int = None) -> bool:
    """Update order status from warehouse"""
    conn = await warehouse_db_manager.get_connection()
    try:
        if status == 'completed':
            query = """
            UPDATE zayavki 
            SET status = $1, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            """
        else:
            query = """
            UPDATE zayavki 
            SET status = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            """
        
        await conn.execute(query, status, order_id)
        
        # Log status change if needed
        if updated_by:
            log_query = """
            INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
            SELECT $1, $2, status, $3 FROM zayavki WHERE id = $1
            """
            await conn.execute(log_query, order_id, updated_by, status)
        
        return True
    except Exception as e:
        logging.error(f"Error updating order status: {e}")
        return False
    finally:
        await warehouse_db_manager.pool.release(conn)

async def mark_order_ready_for_installation(order_id: int, warehouse_user_id: int) -> bool:
    """Mark order as ready for installation"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        UPDATE zayavki 
        SET ready_to_install = true, status = 'ready_for_installation', updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """
        await conn.execute(query, order_id)
        
        # Log the action
        log_query = """
        INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
        VALUES ($1, $2, 'in_progress', 'ready_for_installation')
        """
        await conn.execute(log_query, order_id, warehouse_user_id)
        
        return True
    except Exception as e:
        logging.error(f"Error marking order ready for installation: {e}")
        return False
    finally:
        await warehouse_db_manager.pool.release(conn)

# ==================== STATISTICS AND REPORTS ====================

async def get_warehouse_daily_statistics() -> Dict:
    """Get daily warehouse statistics"""
    conn = await warehouse_db_manager.get_connection()
    try:
        # Items added today
        items_added_query = """
        SELECT COUNT(*) as count FROM materials 
        WHERE DATE(created_at) = CURRENT_DATE
        """
        items_added = await conn.fetchval(items_added_query) or 0
        
        # Items issued today
        items_issued_query = """
        SELECT COUNT(*) as count FROM issued_items 
        WHERE DATE(issued_at) = CURRENT_DATE
        """
        items_issued = await conn.fetchval(items_issued_query) or 0
        
        # Total inventory value
        total_value_query = """
        SELECT SUM(quantity * price) as total FROM materials 
        WHERE is_active = true
        """
        total_value = await conn.fetchval(total_value_query) or 0
        
        # Low stock count
        low_stock_query = """
        SELECT COUNT(*) as count FROM materials 
        WHERE is_active = true AND quantity <= min_quantity
        """
        low_stock_count = await conn.fetchval(low_stock_query) or 0
        
        return {
            'items_added': items_added,
            'items_issued': items_issued,
            'total_value': float(total_value),
            'low_stock_count': low_stock_count,
            'turnover_rate': 85.5  # Mock data for now
        }
    except Exception as e:
        logging.error(f"Error getting daily statistics: {e}")
        return {}
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_warehouse_weekly_statistics() -> Dict:
    """Get weekly warehouse statistics"""
    conn = await warehouse_db_manager.get_connection()
    try:
        # Items added this week
        items_added_query = """
        SELECT COUNT(*) as count FROM materials 
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """
        items_added = await conn.fetchval(items_added_query) or 0
        
        # Items issued this week
        items_issued_query = """
        SELECT COUNT(*) as count FROM issued_items 
        WHERE issued_at >= CURRENT_DATE - INTERVAL '7 days'
        """
        items_issued = await conn.fetchval(items_issued_query) or 0
        
        # Total inventory value
        total_value_query = """
        SELECT SUM(quantity * price) as total FROM materials 
        WHERE is_active = true
        """
        total_value = await conn.fetchval(total_value_query) or 0
        
        # Low stock count
        low_stock_query = """
        SELECT COUNT(*) as count FROM materials 
        WHERE is_active = true AND quantity <= min_quantity
        """
        low_stock_count = await conn.fetchval(low_stock_query) or 0
        
        return {
            'items_added': items_added,
            'items_issued': items_issued,
            'total_value': float(total_value),
            'low_stock_count': low_stock_count,
            'turnover_rate': 78.3  # Mock data for now
        }
    except Exception as e:
        logging.error(f"Error getting weekly statistics: {e}")
        return {}
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_warehouse_monthly_statistics() -> Dict:
    """Get monthly warehouse statistics"""
    conn = await warehouse_db_manager.get_connection()
    try:
        # Items added this month
        items_added_query = """
        SELECT COUNT(*) as count FROM materials 
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        items_added = await conn.fetchval(items_added_query) or 0
        
        # Items issued this month
        items_issued_query = """
        SELECT COUNT(*) as count FROM issued_items 
        WHERE issued_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        items_issued = await conn.fetchval(items_issued_query) or 0
        
        # Total inventory value
        total_value_query = """
        SELECT SUM(quantity * price) as total FROM materials 
        WHERE is_active = true
        """
        total_value = await conn.fetchval(total_value_query) or 0
        
        # Low stock count
        low_stock_query = """
        SELECT COUNT(*) as count FROM materials 
        WHERE is_active = true AND quantity <= min_quantity
        """
        low_stock_count = await conn.fetchval(low_stock_query) or 0
        
        # Monthly turnover calculation
        turnover_query = """
        SELECT 
            COALESCE(SUM(ii.quantity), 0) as issued,
            COALESCE(AVG(m.quantity), 1) as avg_stock
        FROM issued_items ii
        LEFT JOIN materials m ON ii.material_id = m.id
        WHERE ii.issued_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        turnover_result = await conn.fetchrow(turnover_query)
        issued = turnover_result['issued'] if turnover_result else 0
        avg_stock = turnover_result['avg_stock'] if turnover_result else 1
        turnover_rate = (issued / avg_stock * 100) if avg_stock > 0 else 0
        
        return {
            'items_added': items_added,
            'items_issued': items_issued,
            'total_value': float(total_value),
            'low_stock_count': low_stock_count,
            'turnover_rate': round(turnover_rate, 1)
        }
    except Exception as e:
        logging.error(f"Error getting monthly statistics: {e}")
        return {}
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_inventory_turnover_statistics() -> Dict:
    """Get inventory turnover statistics"""
    conn = await warehouse_db_manager.get_connection()
    try:
        # Calculate turnover for last 30 days
        query = """
        SELECT 
            m.name,
            m.quantity as current_stock,
            COALESCE(SUM(ii.quantity), 0) as issued_quantity,
            CASE 
                WHEN m.quantity > 0 THEN (COALESCE(SUM(ii.quantity), 0)::float / m.quantity * 100)
                ELSE 0 
            END as turnover_rate
        FROM materials m
        LEFT JOIN issued_items ii ON m.id = ii.material_id 
            AND ii.issued_at >= CURRENT_DATE - INTERVAL '30 days'
        WHERE m.is_active = true
        GROUP BY m.id, m.name, m.quantity
        ORDER BY turnover_rate DESC
        LIMIT 10
        """
        results = await conn.fetch(query)
        
        top_turnover_items = []
        total_turnover = 0
        
        for row in results:
            item_data = {
                'name': row['name'],
                'current_stock': row['current_stock'],
                'issued_quantity': row['issued_quantity'],
                'turnover_rate': round(float(row['turnover_rate']), 1)
            }
            top_turnover_items.append(item_data)
            total_turnover += float(row['turnover_rate'])
        
        avg_turnover = total_turnover / len(results) if results else 0
        
        return {
            'items_added': len(results),
            'items_issued': sum(item['issued_quantity'] for item in top_turnover_items),
            'total_value': 0,  # Will be calculated separately if needed
            'low_stock_count': 0,  # Will be calculated separately if needed
            'turnover_rate': round(avg_turnover, 1),
            'top_turnover_items': top_turnover_items
        }
    except Exception as e:
        logging.error(f"Error getting turnover statistics: {e}")
        return {}
    finally:
        await warehouse_db_manager.pool.release(conn)

# ==================== EXPORT FUNCTIONALITY ====================

async def get_inventory_export_data() -> List[Dict]:
    """Get all inventory data for export"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT 
            id, name, category, quantity, unit, min_quantity, 
            price, description, created_at, updated_at
        FROM materials 
        WHERE is_active = true 
        ORDER BY name
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting export data: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_orders_export_data() -> List[Dict]:
    """Get orders data for export"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT 
            z.id, z.description, z.status, z.created_at, z.completed_at,
            u.full_name as client_name, u.phone_number as client_phone,
            t.full_name as technician_name
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        ORDER BY z.created_at DESC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting orders export data: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def get_issued_items_export_data() -> List[Dict]:
    """Get issued items data for export"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT 
            ii.id, ii.quantity, ii.issued_at,
            m.name as material_name, m.category,
            u.full_name as issued_by_name,
            z.id as order_id, z.description as order_description
        FROM issued_items ii
        LEFT JOIN materials m ON ii.material_id = m.id
        LEFT JOIN users u ON ii.issued_by = u.id
        LEFT JOIN zayavki z ON ii.zayavka_id = z.id
        ORDER BY ii.issued_at DESC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting issued items export data: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

# ==================== EQUIPMENT MANAGEMENT ====================

async def get_warehouse_equipment_list() -> List[Dict]:
    """Get equipment list for warehouse"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        SELECT * FROM materials 
        WHERE is_active = true AND category = 'equipment'
        ORDER BY name
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting equipment list: {e}")
        return []
    finally:
        await warehouse_db_manager.pool.release(conn)

async def mark_equipment_ready_warehouse(equipment_id: int, warehouse_user_id: int) -> bool:
    """Mark equipment as ready from warehouse"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        UPDATE materials 
        SET ready_to_install = true, updated_at = CURRENT_TIMESTAMP 
        WHERE id = $1
        """
        await conn.execute(query, equipment_id)
        
        # Log the action
        log_query = """
        INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
        VALUES (NULL, $1, 'equipment_preparing', 'equipment_ready')
        """
        await conn.execute(log_query, warehouse_user_id)
        
        return True
    except Exception as e:
        logging.error(f"Error marking equipment ready: {e}")
        return False
    finally:
        await warehouse_db_manager.pool.release(conn)

async def issue_equipment_to_technician(equipment_id: int, technician_id: int, quantity: int, warehouse_user_id: int) -> bool:
    """Issue equipment to technician"""
    conn = await warehouse_db_manager.get_connection()
    try:
        # Check if enough quantity available
        check_query = "SELECT quantity FROM materials WHERE id = $1"
        current_quantity = await conn.fetchval(check_query, equipment_id)
        
        if current_quantity < quantity:
            return False
        
        # Update material quantity
        update_query = """
        UPDATE materials 
        SET quantity = quantity - $1, updated_at = CURRENT_TIMESTAMP 
        WHERE id = $2
        """
        await conn.execute(update_query, quantity, equipment_id)
        
        # Log issued item
        log_query = """
        INSERT INTO issued_items (material_id, quantity, issued_by, issued_to)
        VALUES ($1, $2, $3, $4)
        """
        await conn.execute(log_query, equipment_id, quantity, warehouse_user_id, technician_id)
        
        return True
    except Exception as e:
        logging.error(f"Error issuing equipment: {e}")
        return False
    finally:
        await warehouse_db_manager.pool.release(conn)

# ==================== UTILITY FUNCTIONS ====================

async def init_warehouse_database():
    """Initialize warehouse database connection"""
    await warehouse_db_manager.init_pool()

async def close_warehouse_database():
    """Close warehouse database connection"""
    await warehouse_db_manager.close_pool()

async def get_warehouse_user_by_telegram_id(telegram_id: int) -> Optional[Dict]:
    """Get warehouse user by telegram ID"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = "SELECT * FROM users WHERE telegram_id = $1 AND role = 'warehouse'"
        result = await conn.fetchrow(query, telegram_id)
        return dict(result) if result else None
    except Exception as e:
        logging.error(f"Error getting warehouse user: {e}")
        return None
    finally:
        await warehouse_db_manager.pool.release(conn)

async def log_warehouse_activity(user_id: int, activity: str, details: str = None) -> bool:
    """Log warehouse activity"""
    conn = await warehouse_db_manager.get_connection()
    try:
        query = """
        INSERT INTO activity_logs (user_id, activity_type, activity_details, created_at)
        VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
        """
        await conn.execute(query, user_id, activity, details)
        return True
    except Exception as e:
        logging.error(f"Error logging warehouse activity: {e}")
        return False
    finally:
        await warehouse_db_manager.pool.release(conn)
