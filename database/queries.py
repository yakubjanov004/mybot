import asyncpg
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import logging
from config import config
import tempfile

# Database connection pool
_pool = None

class DatabaseManager:
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
            logging.info("Database pool initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize database pool: {e}")
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

# Global database manager instance
db_manager = DatabaseManager()

async def get_connection():
    """Get database connection"""
    return await db_manager.get_connection()

# Import quality control functions
# from database.quality_queries import *

# ==================== CALL CENTER QUERIES ====================

async def get_call_center_stats(user_id: int, period: str = 'daily') -> Dict:
    """Get call center statistics for different periods"""
    conn = await db_manager.get_connection()
    try:
        if period == 'daily':
            date_filter = "DATE(created_at) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'monthly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        elif period == 'conversion':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        else:  # performance
            date_filter = "created_by = $1"
        
        # Get calls count
        calls_query = f"""
        SELECT COUNT(*) as calls,
               AVG(duration) as avg_call_time,
               COUNT(CASE WHEN result = 'order_created' THEN 1 END) as successful_calls
        FROM call_logs
        WHERE {date_filter}
        """
        
        # Get orders count
        orders_query = f"""
        SELECT COUNT(*) as orders
        FROM zayavki
        WHERE {date_filter}
        """
        
        if period == 'performance':
            calls_result = await conn.fetchrow(calls_query, user_id)
            orders_result = await conn.fetchrow(orders_query, user_id)
        else:
            calls_result = await conn.fetchrow(calls_query)
            orders_result = await conn.fetchrow(orders_query)
        
        calls_count = calls_result['calls'] if calls_result else 0
        orders_count = orders_result['orders'] if orders_result else 0
        avg_call_time = float(calls_result['avg_call_time']) if calls_result and calls_result['avg_call_time'] else 0
        successful_calls = calls_result['successful_calls'] if calls_result else 0
        
        conversion_rate = (orders_count / calls_count * 100) if calls_count > 0 else 0
        success_rate = (successful_calls / calls_count * 100) if calls_count > 0 else 0
        
        return {
            'calls': calls_count,
            'orders': orders_count,
            'conversion_rate': round(conversion_rate, 1),
            'avg_call_time': round(avg_call_time, 1),
            'success_rate': round(success_rate, 1),
            'rating': 4.5,  # Mock rating
            'feedback_count': 25  # Mock feedback count
        }
    except Exception as e:
        logging.error(f"Error getting call center stats: {e}")
        return {'calls': 0, 'orders': 0, 'conversion_rate': 0, 'avg_call_time': 0, 'success_rate': 0}
    finally:
        await db_manager.pool.release(conn)

async def search_customers(query: str) -> List[Dict]:
    """Search customers by name, phone or abonent_id"""
    conn = await db_manager.get_connection()
    try:
        search_query = """
        SELECT * FROM users
        WHERE (full_name ILIKE $1 OR phone_number ILIKE $1) 
        AND role = 'client'
        LIMIT 10
        """
        results = await conn.fetch(search_query, f"%{query}%")
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error searching clients: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def create_order_from_call(order_data: Dict) -> int:
    """Create order from call center"""
    return await create_zayavka(order_data)

async def log_call(call_data: Dict) -> bool:
    """Log call information"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO call_logs (user_id, phone_number, duration, result, notes, created_by)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        await conn.execute(
            query,
            call_data.get('user_id'),
            call_data['phone_number'],
            call_data.get('duration', 0),
            call_data['result'],
            call_data.get('notes', ''),
            call_data['created_by']
        )
        return True
    except Exception as e:
        logging.error(f"Error creating call log: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

# ==================== CONTROLLERS QUERIES ====================

async def get_quality_stats() -> Dict:
    """Get quality control statistics"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT 
            AVG(rating) as avg_rating,
            COUNT(*) as total_reviews,
            COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_reviews
        FROM feedback
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        result = await conn.fetchrow(query)
        
        if result:
            total_reviews = result['total_reviews'] or 0
            positive_reviews = result['positive_reviews'] or 0
            satisfaction_rate = (positive_reviews / total_reviews * 100) if total_reviews > 0 else 0
            
            # Get rating distribution
            distribution_query = """
            SELECT rating, COUNT(*) as count
            FROM feedback
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY rating
            ORDER BY rating DESC
            """
            distribution_results = await conn.fetch(distribution_query)
            rating_distribution = {row['rating']: row['count'] for row in distribution_results}
            
            return {
                'avg_rating': float(result['avg_rating']) if result['avg_rating'] else 0.0,
                'total_reviews': total_reviews,
                'satisfaction_rate': round(satisfaction_rate, 1),
                'rating_distribution': rating_distribution
            }
        return {}
    except Exception as e:
        logging.error(f"Error getting service quality metrics: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def get_unresolved_issues() -> List[Dict]:
    """Get list of unresolved issues"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, u.full_name as client_name,
               EXTRACT(DAY FROM (CURRENT_TIMESTAMP - z.created_at)) as days_pending
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        WHERE z.status IN ('new', 'pending', 'assigned') 
        AND z.created_at <= CURRENT_TIMESTAMP - INTERVAL '2 days'
        ORDER BY z.created_at ASC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting unresolved issues: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_feedback_by_filter(filter_type: str, value: Any = None) -> List[Dict]:
    """Get feedback by different filters"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT f.*, u.full_name as client_name, z.description as order_description
        FROM feedback f
        LEFT JOIN users u ON f.user_id = u.id
        LEFT JOIN zayavki z ON f.zayavka_id = z.id
        ORDER BY f.created_at DESC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting all feedback: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_technician_performance() -> List[Dict]:
    """Get technician performance metrics"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT 
            COUNT(z.id) as total_orders,
            COUNT(CASE WHEN z.status = 'completed' THEN 1 END) as completed_orders,
            COUNT(CASE WHEN z.status IN ('assigned', 'in_progress') THEN 1 END) as active_orders,
            COUNT(CASE WHEN z.status = 'completed' AND DATE(z.completed_at) = CURRENT_DATE THEN 1 END) as completed_today,
            AVG(f.rating) as avg_rating
        FROM zayavki z
        LEFT JOIN feedback f ON z.id = f.zayavka_id
        WHERE z.assigned_to = $1
        """
        result = await conn.fetchrow(query, 1)
        
        if result:
            return {
                'total_orders': result['total_orders'] or 0,
                'completed_orders': result['completed_orders'] or 0,
                'active_orders': result['active_orders'] or 0,
                'completed_today': result['completed_today'] or 0,
                'avg_rating': float(result['avg_rating']) if result['avg_rating'] else 0.0
            }
        return {}
    except Exception as e:
        logging.error(f"Error getting technician performance: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

# ==================== TECHNICIAN QUERIES ====================

async def create_help_request(help_data: Dict) -> int:
    """Create help request from technician"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO help_requests (technician_id, help_type, description, media, location, priority, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'pending')
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            help_data['technician_id'],
            help_data['help_type'],
            help_data['description'],
            help_data.get('media'),
            help_data.get('location'),
            help_data.get('priority', 'normal')
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating help request: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def get_technician_tasks(technician_id: int, status: str = None) -> List[Dict]:
    """Get technician tasks"""
    conn = await db_manager.get_connection()
    try:
        if status:
            query = """
            SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            WHERE z.assigned_to = $1 AND z.status = $2
            ORDER BY z.created_at DESC
            """
            results = await conn.fetch(query, technician_id, status)
        else:
            query = """
            SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            WHERE z.assigned_to = $1
            ORDER BY z.created_at DESC
            """
            results = await conn.fetch(query, technician_id)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting technician tasks: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def update_task_status(task_id: int, status: str, technician_id: int, solution: str = None) -> bool:
    """Update task status"""
    conn = await db_manager.get_connection()
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
        await conn.execute(query, status, task_id)
        return True
    except Exception as e:
        logging.error(f"Error updating zayavka status: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_nearby_tasks(location: Dict, radius: float = 5.0) -> List[Dict]:
    """Get nearby tasks based on location"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        WHERE z.status IN ('new', 'pending') 
        AND z.assigned_to IS NULL
        ORDER BY z.created_at DESC
        LIMIT 10
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting all zayavki: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

# ==================== WAREHOUSE QUERIES ====================

async def get_inventory_items(category: str = None) -> List[Dict]:
    """Get inventory items"""
    return await get_materials()

async def add_inventory_item(item_data: Dict) -> bool:
    """Add new inventory item"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO materials (name, quantity, unit, min_quantity, description, category, price, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, true)
        """
        await conn.execute(
            query,
            item_data['name'],
            item_data['quantity'],
            item_data.get('unit', 'pcs'),
            item_data.get('min_quantity', 5),
            item_data.get('description', ''),
            item_data.get('category', 'general'),
            item_data.get('price', 0)
        )
        return True
    except Exception as e:
        logging.error(f"Error adding inventory item: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def update_inventory(item_id: int, quantity: int, operation: str) -> bool:
    """Update inventory quantity"""
    conn = await db_manager.get_connection()
    try:
        if operation == 'add':
            query = "UPDATE materials SET quantity = quantity + $1 WHERE id = $2"
        elif operation == 'subtract':
            query = "UPDATE materials SET quantity = quantity - $1 WHERE id = $2 AND quantity >= $1"
        else:  # set
            query = "UPDATE materials SET quantity = $1 WHERE id = $2"
        result = await conn.execute(query, quantity, item_id)
        return result != "UPDATE 0"
    except Exception as e:
        logging.error(f"Error updating inventory: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_warehouse_stats() -> Dict:
    """Get warehouse statistics"""
    conn = await db_manager.get_connection()
    try:
        if period == 'daily':
            date_filter = "DATE(created_at) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'monthly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        else:  # turnover
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        # Mock statistics for now
        return {
            'items_added': 15,
            'items_issued': 8,
            'total_value': 2500000,
            'low_stock_count': 3,
            'turnover_rate': 85.5
        }
    except Exception as e:
        logging.error(f"Error getting warehouse statistics: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def get_low_stock_items() -> List[Dict]:
    """Get items with low stock"""
    conn = await db_manager.get_connection()
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
        await db_manager.pool.release(conn)

async def export_inventory_data(format_type: str) -> Dict:
    """Export inventory data"""
    try:
        # Mock export functionality
        filename = f"warehouse_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        # In real implementation, generate actual file
        return filename
    except Exception as e:
        logging.error(f"Error exporting warehouse data: {e}")
        return None

# ==================== CLIENT QUERIES ====================

async def update_user_profile(user_id: int, profile_data: Dict) -> bool:
    """Update user profile"""
    conn = await db_manager.get_connection()
    try:
        fields = []
        values = []
        param_count = 1
        for field, value in profile_data.items():
            if field in ['full_name', 'phone_number', 'address', 'language']:
                fields.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
        if not fields:
            return False
        fields.append(f"updated_at = ${param_count}")
        values.append(datetime.now())
        param_count += 1
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = ${param_count}"
        values.append(user_id)
        await conn.execute(query, *values)
        return True
    except Exception as e:
        logging.error(f"Error updating user profile: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_user_orders(user_id: int, status: str = None) -> List[Dict]:
    """Get user orders"""
    conn = await db_manager.get_connection()
    try:
        if status:
            query = """
            SELECT z.*, u.full_name as technician_name
            FROM zayavki z
            LEFT JOIN users u ON z.assigned_to = u.id
            WHERE z.user_id = $1 AND z.status = $2
            ORDER BY z.created_at DESC
            """
            results = await conn.fetch(query, user_id, status)
        else:
            query = """
            SELECT z.*, u.full_name as technician_name
            FROM zayavki z
            LEFT JOIN users u ON z.assigned_to = u.id
            WHERE z.user_id = $1
            ORDER BY z.created_at DESC
            """
            results = await conn.fetch(query, user_id)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting user orders: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def create_support_ticket(ticket_data: Dict) -> int:
    """Create support ticket"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO support_tickets (user_id, subject, message, media, priority, status)
        VALUES ($1, $2, $3, $4, $5, 'open')
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            ticket_data['user_id'],
            ticket_data['subject'],
            ticket_data['message'],
            ticket_data.get('media'),
            ticket_data.get('priority', 'normal')
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating support ticket: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

# ==================== MANAGER QUERIES ====================

async def get_employee_stats(period: str = 'monthly') -> List[Dict]:
    """Get employee statistics"""
    conn = await db_manager.get_connection()
    try:
        if period == 'daily':
            date_filter = "DATE(z.created_at) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "z.created_at >= CURRENT_DATE - INTERVAL '7 days'"
        else:  # monthly
            date_filter = "z.created_at >= CURRENT_DATE - INTERVAL '30 days'"
        query = f"""
        SELECT 
            u.id, u.full_name, u.role,
            COUNT(z.id) as total_tasks,
            COUNT(CASE WHEN z.status = 'completed' THEN 1 END) as completed_tasks,
            AVG(CASE WHEN z.status = 'completed' THEN 
                EXTRACT(EPOCH FROM (z.completed_at - z.created_at))/3600 
            END) as avg_completion_time
        FROM users u
        LEFT JOIN zayavki z ON u.id = z.assigned_to
        WHERE u.role IN ('technician', 'manager', 'call_center')
        AND ({date_filter} OR z.id IS NULL)
        GROUP BY u.id, u.full_name, u.role
        ORDER BY completed_tasks DESC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting employee stats: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def assign_technician(order_id: int, technician_id: int, assigned_by: int) -> bool:
    """Assign technician to order"""
    conn = await db_manager.get_connection()
    try:
        query = """
        UPDATE zayavki 
        SET assigned_to = $1, status = 'assigned', assigned_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
        """
        await conn.execute(query, technician_id, order_id)
        # Log assignment if needed
        if assigned_by:
            log_query = """
            INSERT INTO assignment_logs (order_id, technician_id, assigned_by, assigned_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            """
            await conn.execute(log_query, order_id, technician_id, assigned_by)
        return True
    except Exception as e:
        logging.error(f"Error assigning zayavka to technician: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_notification_settings(user_id: int) -> Dict:
    """Get user notification settings"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT * FROM notification_settings WHERE user_id = $1"
        result = await conn.fetchrow(query, user_id)
        if result:
            return dict(result)
        else:
            # Return default settings
            return {
                'new_orders': True,
                'status_changes': True,
                'urgent_issues': True,
                'daily_summary': False,
                'system_alerts': True
            }
    except Exception as e:
        logging.error(f"Error getting notification settings: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def update_notification_settings(user_id: int, settings: Dict) -> bool:
    """Update notification settings"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO notification_settings (user_id, new_orders, status_changes, urgent_issues, daily_summary, system_alerts)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            new_orders = EXCLUDED.new_orders,
            status_changes = EXCLUDED.status_changes,
            urgent_issues = EXCLUDED.urgent_issues,
            daily_summary = EXCLUDED.daily_summary,
            system_alerts = EXCLUDED.system_alerts,
            updated_at = CURRENT_TIMESTAMP
        """
        await conn.execute(
            query,
            user_id,
            settings.get('new_orders', True),
            settings.get('status_changes', True),
            settings.get('urgent_issues', True),
            settings.get('daily_summary', False),
            settings.get('system_alerts', True)
        )
        return True
    except Exception as e:
        logging.error(f"Error updating notification settings: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

# ==================== GENERAL QUERIES ====================

async def get_user_by_telegram_id(telegram_id: Union[int, str]) -> Optional[Dict]:
    """Get user by telegram ID"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT * FROM users WHERE telegram_id = $1"
        result = await conn.fetchrow(query, int(telegram_id))
        return dict(result) if result else None
    except Exception as e:
        logging.error(f"Error getting user by telegram_id {telegram_id}: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def create_user(user_data: Dict) -> int:
    """Create new user"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO users (telegram_id, full_name, username, phone_number, role, language, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, true)
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            str(user_data['telegram_id']),
            user_data.get('full_name', ''),
            user_data.get('username'),
            user_data.get('phone_number'),
            user_data.get('role', 'client'),
            user_data.get('language', 'uz')
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def update_user_language(user_id: int, language: str) -> bool:
    """Update user language"""
    conn = await db_manager.get_connection()
    try:
        query = "UPDATE users SET language = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
        await conn.execute(query, language, user_id)
        return True
    except Exception as e:
        logging.error(f"Error updating user language: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_order_details(order_id: int) -> Optional[Dict]:
    """Get order details"""
    return await get_zayavka_by_id(order_id)

async def create_feedback(feedback_data: Dict) -> bool:
    """Create feedback"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO feedback (zayavka_id, user_id, rating, comment, created_by)
        VALUES ($1, $2, $3, $4, $5)
        """
        await conn.execute(
            query,
            feedback_data.get('zayavka_id'),
            feedback_data['user_id'],
            feedback_data['rating'],
            feedback_data.get('comment', ''),
            feedback_data.get('created_by')
        )
        return True
    except Exception as e:
        logging.error(f"Error creating feedback: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

# ==================== USER MANAGEMENT ====================

async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT * FROM users WHERE id = $1"
        result = await conn.fetchrow(query, user_id)
        return dict(result) if result else None
    except Exception as e:
        logging.error(f"Error getting user by id {user_id}: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def update_user_phone(user_id: int, phone_number: str) -> bool:
    """Update user phone number"""
    conn = await db_manager.get_connection()
    try:
        query = "UPDATE users SET phone_number = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
        await conn.execute(query, phone_number, user_id)
        return True
    except Exception as e:
        logging.error(f"Error updating user phone: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

# ==================== ZAYAVKA MANAGEMENT ====================

async def create_zayavka(zayavka_data: Dict) -> Optional[int]:
    """Create new zayavka"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO zayavki (user_id, zayavka_type, abonent_id, description, address, 
                           media, location, status, created_by_role, phone_number, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            zayavka_data.get('user_id'),
            zayavka_data.get('zayavka_type'),
            zayavka_data.get('abonent_id'),
            zayavka_data['description'],
            zayavka_data['address'],
            zayavka_data.get('media'),
            zayavka_data.get('location'),
            zayavka_data.get('status', 'new'),
            zayavka_data.get('created_by_role', 'client'),
            zayavka_data.get('phone_number'),
            zayavka_data.get('created_by')
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating zayavka: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def get_zayavka_by_id(zayavka_id: int) -> Optional[Dict]:
    """Get zayavka by ID"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, 
               u.full_name as user_name, u.phone_number as client_phone,
               t.full_name as technician_name, t.phone_number as technician_phone,
               a.full_name as assigned_name
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        LEFT JOIN users a ON z.assigned_to = a.id
        WHERE z.id = $1
        """
        result = await conn.fetchrow(query, zayavka_id)
        return dict(result) if result else None
    except Exception as e:
        logging.error(f"Error getting zayavka by id {zayavka_id}: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def get_user_zayavki(user_id: int, limit: int = 50) -> List[Dict]:
    """Get user's zayavki"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, t.full_name as technician_name
        FROM zayavki z
        LEFT JOIN users t ON z.assigned_to = t.id
        WHERE z.user_id = $1
        ORDER BY z.created_at DESC
        LIMIT $2
        """
        results = await conn.fetch(query, user_id, limit)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting user zayavki: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_all_zayavki(limit: int = 100) -> List[Dict]:
    """Get all zayavki"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, 
               u.full_name as client_name, u.phone_number as client_phone,
               t.full_name as technician_name
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        ORDER BY z.created_at DESC
        LIMIT $1
        """
        results = await conn.fetch(query, limit)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting all zayavki: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def update_zayavka_status(zayavka_id: int, status: str, updated_by: int = None) -> bool:
    """Update zayavka status"""
    conn = await db_manager.get_connection()
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
        
        await conn.execute(query, status, zayavka_id)
        return True
    except Exception as e:
        logging.error(f"Error updating zayavka status: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def assign_zayavka_to_technician(zayavka_id: int, technician_id: int, assigned_by: int = None) -> bool:
    """Assign zayavka to technician"""
    conn = await db_manager.get_connection()
    try:
        query = """
        UPDATE zayavki 
        SET assigned_to = $1, status = 'assigned', assigned_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
        """
        await conn.execute(query, technician_id, zayavka_id)
        
        # Log assignment if needed
        if assigned_by:
            log_query = """
            INSERT INTO assignment_logs (order_id, technician_id, assigned_by, assigned_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            """
            await conn.execute(log_query, zayavka_id, technician_id, assigned_by)
        
        return True
    except Exception as e:
        logging.error(f"Error assigning zayavka to technician: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_zayavka_solutions(zayavka_id: int) -> List[Dict]:
    """Get solutions for zayavka"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT s.*, u.full_name as instander_name
        FROM solutions s
        LEFT JOIN users u ON s.instander_id = u.id
        WHERE s.zayavka_id = $1
        ORDER BY s.created_at DESC
        """
        results = await conn.fetch(query, zayavka_id)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting zayavka solutions: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

# ==================== TECHNICIAN MANAGEMENT ====================

async def get_available_technicians() -> List[Dict]:
    """Get available technicians"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT u.*, 
               COUNT(z.id) as active_tasks
        FROM users u
        LEFT JOIN zayavki z ON u.id = z.assigned_to AND z.status IN ('assigned', 'in_progress')
        WHERE u.role = 'technician' AND u.is_active = true
        GROUP BY u.id, u.full_name, u.phone_number
        ORDER BY active_tasks ASC, u.full_name
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting available technicians: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_all_technicians(available_only: bool = False) -> List[Dict]:
    """Get all technicians"""
    conn = await db_manager.get_connection()
    try:
        if available_only:
            query = """
            SELECT u.*, COUNT(z.id) as active_tasks
            FROM users u
            LEFT JOIN zayavki z ON u.id = z.assigned_to AND z.status IN ('assigned', 'in_progress')
            WHERE u.role = 'technician' AND u.is_active = true
            GROUP BY u.id
            HAVING COUNT(z.id) < 5
            ORDER BY u.full_name
            """
        else:
            query = """
            SELECT u.*, COUNT(z.id) as active_tasks
            FROM users u
            LEFT JOIN zayavki z ON u.id = z.assigned_to AND z.status IN ('assigned', 'in_progress')
            WHERE u.role = 'technician'
            GROUP BY u.id
            ORDER BY u.full_name
            """
        
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting technicians: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_technician_tasks(technician_id: int, status: str = None) -> List[Dict]:
    """Get technician tasks"""
    conn = await db_manager.get_connection()
    try:
        if status:
            query = """
            SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            WHERE z.assigned_to = $1 AND z.status = $2
            ORDER BY z.created_at DESC
            """
            results = await conn.fetch(query, technician_id, status)
        else:
            query = """
            SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            WHERE z.assigned_to = $1
            ORDER BY z.created_at DESC
            """
            results = await conn.fetch(query, technician_id)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting technician tasks: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_zayavki_by_assigned(technician_id: int) -> List[Dict]:
    """Get zayavki assigned to technician"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, u.full_name as user_name, u.phone_number as client_phone
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        WHERE z.assigned_to = $1
        ORDER BY z.created_at DESC
        """
        results = await conn.fetch(query, technician_id)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting zayavki by assigned: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def accept_task(zayavka_id: int, technician_id: int) -> bool:
    """Accept task by technician"""
    conn = await db_manager.get_connection()
    try:
        query = """
        UPDATE zayavki 
        SET status = 'accepted', accepted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1 AND assigned_to = $2
        """
        await conn.execute(query, zayavka_id, technician_id)
        return True
    except Exception as e:
        logging.error(f"Error accepting task: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def start_task(zayavka_id: int, technician_id: int) -> bool:
    """Start task by technician"""
    conn = await db_manager.get_connection()
    try:
        query = """
        UPDATE zayavki 
        SET status = 'in_progress', started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1 AND assigned_to = $2
        """
        await conn.execute(query, zayavka_id, technician_id)
        return True
    except Exception as e:
        logging.error(f"Error starting task: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def complete_task(zayavka_id: int, technician_id: int, solution_text: str = None) -> Dict:
    """Complete task by technician"""
    conn = await db_manager.get_connection()
    try:
        # Update zayavka status
        query = """
        UPDATE zayavki 
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1 AND assigned_to = $2
        """
        await conn.execute(query, zayavka_id, technician_id)
        # Add solution if provided
        if solution_text:
            solution_query = """
            INSERT INTO solutions (zayavka_id, instander_id, solution_text)
            VALUES ($1, $2, $3)
            """
            await conn.execute(solution_query, zayavka_id, technician_id, solution_text)
        # Get zayavka details
        zayavka = await get_zayavka_by_id(zayavka_id)
        return zayavka
    except Exception as e:
        logging.error(f"Error completing task: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def request_task_transfer(zayavka_id: int, technician_id: int, reason: str) -> bool:
    """Request task transfer"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO task_transfer_requests (zayavka_id, from_technician_id, reason, status)
        VALUES ($1, $2, $3, 'pending')
        """
        await conn.execute(query, zayavka_id, technician_id, reason)
        return True
    except Exception as e:
        logging.error(f"Error requesting task transfer: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

# ==================== MANAGER QUERIES ====================

async def get_managers_telegram_ids() -> List[Dict]:
    """Get all managers' telegram IDs"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT telegram_id, language FROM users WHERE role = 'manager' AND is_active = true"
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting managers telegram ids: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_managers_list() -> List[Dict]:
    """Get list of managers"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT * FROM users WHERE role = 'manager' AND is_active = true"
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting managers list: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_applications() -> List[Dict]:
    """Get applications for manager view"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, 
               u.full_name as user_name, u.phone_number as user_phone,
               t.full_name as technician_name, t.phone_number as technician_phone,
               z.created_at as created_time,
               z.assigned_at as assigned_time,
               z.accepted_at as accepted_time,
               z.started_at as started_time,
               z.completed_at as completed_time
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        ORDER BY z.created_at DESC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting applications: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_filtered_applications(statuses: List[str] = None, date_from: datetime = None, 
                                  date_to: datetime = None, technician_id: int = None,
                                  assigned_only: bool = False, page: int = 1, limit: int = 10) -> Dict:
    """Get filtered applications"""
    conn = await db_manager.get_connection()
    try:
        conditions = []
        params = []
        param_count = 1
        if statuses:
            conditions.append(f"z.status = ANY(${param_count})")
            params.append(statuses)
            param_count += 1
        if date_from:
            conditions.append(f"z.created_at >= ${param_count}")
            params.append(date_from)
            param_count += 1
        if date_to:
            conditions.append(f"z.created_at <= ${param_count}")
            params.append(date_to)
            param_count += 1
        if technician_id == 0:  # Unassigned
            conditions.append("z.assigned_to IS NULL")
        elif technician_id:
            conditions.append(f"z.assigned_to = ${param_count}")
            params.append(technician_id)
            param_count += 1
        if assigned_only:
            conditions.append("z.assigned_to IS NOT NULL")
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        # Count total
        count_query = f"""
        SELECT COUNT(*) as total
        FROM zayavki z
        {where_clause}
        """
        total_result = await conn.fetchrow(count_query, *params)
        total = total_result['total'] if total_result else 0
        # Get paginated results
        offset = (page - 1) * limit
        query = f"""
        SELECT z.*, 
               u.full_name as user_name, u.phone_number as client_phone,
               t.full_name as technician_name, t.phone_number as technician_phone
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        {where_clause}
        ORDER BY z.created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])
        results = await conn.fetch(query, *params)
        applications = [dict(row) for row in results]
        total_pages = (total + limit - 1) // limit
        return {
            'applications': applications,
            'total': total,
            'page': page,
            'total_pages': total_pages
        }
    except Exception as e:
        logging.error(f"Error getting filtered applications: {e}")
        return {'applications': [], 'total': 0, 'page': 1, 'total_pages': 0}
    finally:
        await db_manager.pool.release(conn)

# ==================== CALL CENTER QUERIES ====================

async def get_call_center_stats(user_id: int, period: str = 'daily') -> Dict:
    """Get call center statistics for different periods"""
    conn = await db_manager.get_connection()
    try:
        if period == 'daily':
            date_filter = "DATE(created_at) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'monthly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        elif period == 'conversion':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        else:  # performance
            date_filter = "created_by = $1"
        
        # Get calls count
        calls_query = f"""
        SELECT COUNT(*) as calls,
               AVG(duration) as avg_call_time,
               COUNT(CASE WHEN result = 'order_created' THEN 1 END) as successful_calls
        FROM call_logs
        WHERE {date_filter}
        """
        
        # Get orders count
        orders_query = f"""
        SELECT COUNT(*) as orders
        FROM zayavki
        WHERE {date_filter}
        """
        
        if period == 'performance':
            calls_result = await conn.fetchrow(calls_query, user_id)
            orders_result = await conn.fetchrow(orders_query, user_id)
        else:
            calls_result = await conn.fetchrow(calls_query)
            orders_result = await conn.fetchrow(orders_query)
        
        calls_count = calls_result['calls'] if calls_result else 0
        orders_count = orders_result['orders'] if orders_result else 0
        avg_call_time = float(calls_result['avg_call_time']) if calls_result and calls_result['avg_call_time'] else 0
        successful_calls = calls_result['successful_calls'] if calls_result else 0
        
        conversion_rate = (orders_count / calls_count * 100) if calls_count > 0 else 0
        success_rate = (successful_calls / calls_count * 100) if calls_count > 0 else 0
        
        return {
            'calls': calls_count,
            'orders': orders_count,
            'conversion_rate': round(conversion_rate, 1),
            'avg_call_time': round(avg_call_time, 1),
            'success_rate': round(success_rate, 1),
            'rating': 4.5,  # Mock rating
            'feedback_count': 25  # Mock feedback count
        }
    except Exception as e:
        logging.error(f"Error getting call center stats: {e}")
        return {'calls': 0, 'orders': 0, 'conversion_rate': 0, 'avg_call_time': 0, 'success_rate': 0}
    finally:
        await db_manager.pool.release(conn)

async def get_client_by_phone(phone: str) -> Optional[Dict]:
    """Get client by phone number"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT * FROM users WHERE phone_number = $1"
        result = await conn.fetchrow(query, phone)
        return dict(result) if result else None
    except Exception as e:
        logging.error(f"Error getting client by phone: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def create_client(client_data: Dict) -> Optional[int]:
    """Create new client"""
    return await create_user(client_data)

async def get_orders_by_client(client_id: int, limit: int = 10) -> List[Dict]:
    """Get orders by client"""
    return await get_user_zayavki(client_id, limit)

async def create_order(order_data: Dict) -> Optional[int]:
    """Create order from call center"""
    return await create_zayavka(order_data)

async def get_pending_calls() -> List[Dict]:
    """Get pending calls"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT cl.*, u.full_name as client_name
        FROM call_logs cl
        LEFT JOIN users u ON cl.user_id = u.id
        WHERE cl.result = 'callback_requested'
        ORDER BY cl.created_at DESC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting pending calls: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def create_call_log(call_data: Dict) -> bool:
    """Create call log"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO call_logs (user_id, phone_number, duration, result, notes, created_by)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        await conn.execute(
            query,
            call_data.get('user_id'),
            call_data['phone_number'],
            call_data.get('duration', 0),
            call_data['result'],
            call_data.get('notes', ''),
            call_data['created_by']
        )
        return True
    except Exception as e:
        logging.error(f"Error creating call log: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def search_clients(query: str) -> List[Dict]:
    """Search clients"""
    conn = await db_manager.get_connection()
    try:
        search_query = """
        SELECT * FROM users
        WHERE (full_name ILIKE $1 OR phone_number ILIKE $1) 
        AND role = 'client'
        LIMIT 10
        """
        results = await conn.fetch(search_query, f"%{query}%")
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error searching clients: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def create_feedback(feedback_data: Dict) -> bool:
    """Create feedback"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO feedback (zayavka_id, user_id, rating, comment, created_by)
        VALUES ($1, $2, $3, $4, $5)
        """
        await conn.execute(
            query,
            feedback_data.get('zayavka_id'),
            feedback_data['user_id'],
            feedback_data['rating'],
            feedback_data.get('comment', ''),
            feedback_data.get('created_by')
        )
        return True
    except Exception as e:
        logging.error(f"Error creating feedback: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_client_feedback(client_id: int) -> Optional[Dict]:
    """Get client feedback"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT * FROM feedback
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """
        result = await conn.fetchrow(query, client_id)
        return dict(result) if result else None
    except Exception as e:
        logging.error(f"Error getting client feedback: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def create_chat_session(chat_data: Dict) -> Optional[int]:
    """Create chat session"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO chat_sessions (client_id, operator_id, status)
        VALUES ($1, $2, $3)
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            chat_data['client_id'],
            chat_data['operator_id'],
            chat_data.get('status', 'active')
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating chat session: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def get_active_chat_sessions(client_id: int) -> List[Dict]:
    """Get active chat sessions"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT * FROM chat_sessions
        WHERE client_id = $1 AND status = 'active'
        """
        results = await conn.fetch(query, client_id)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting active chat sessions: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_system_statistics() -> Dict:
    """Get system statistics"""
    conn = await db_manager.get_connection()
    try:
        # Total orders
        total_orders_query = "SELECT COUNT(*) as total FROM zayavki"
        total_orders = await conn.fetchval(total_orders_query)
        # Completed orders
        completed_orders_query = "SELECT COUNT(*) as completed FROM zayavki WHERE status = 'completed'"
        completed_orders = await conn.fetchval(completed_orders_query)
        # Pending orders
        pending_orders_query = "SELECT COUNT(*) as pending FROM zayavki WHERE status IN ('new', 'pending', 'assigned')"
        pending_orders = await conn.fetchval(pending_orders_query)
        # Active clients
        active_clients_query = "SELECT COUNT(*) as active FROM users WHERE role = 'client' AND is_active = true"
        active_clients = await conn.fetchval(active_clients_query)
        # Active technicians
        active_technicians_query = "SELECT COUNT(*) as active FROM users WHERE role = 'technician' AND is_active = true"
        active_technicians = await conn.fetchval(active_technicians_query)
        return {
            'total_orders': total_orders or 0,
            'completed_orders': completed_orders or 0,
            'pending_orders': pending_orders or 0,
            'active_clients': active_clients or 0,
            'active_technicians': active_technicians or 0,
            'revenue_today': 1500000,  # Mock data
            'avg_completion_time': 4.5  # Mock data
        }
    except Exception as e:
        logging.error(f"Error getting system statistics: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def get_technician_performance(technician_id: int) -> Dict:
    """Get technician performance"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT 
            COUNT(z.id) as total_orders,
            COUNT(CASE WHEN z.status = 'completed' THEN 1 END) as completed_orders,
            COUNT(CASE WHEN z.status IN ('assigned', 'in_progress') THEN 1 END) as active_orders,
            COUNT(CASE WHEN z.status = 'completed' AND DATE(z.completed_at) = CURRENT_DATE THEN 1 END) as completed_today,
            AVG(f.rating) as avg_rating
        FROM zayavki z
        LEFT JOIN feedback f ON z.id = f.zayavka_id
        WHERE z.assigned_to = $1
        """
        result = await conn.fetchrow(query, technician_id)
        if result:
            return {
                'total_orders': result['total_orders'] or 0,
                'completed_orders': result['completed_orders'] or 0,
                'active_orders': result['active_orders'] or 0,
                'completed_today': result['completed_today'] or 0,
                'avg_rating': float(result['avg_rating']) if result['avg_rating'] else 0.0
            }
        return {}
    except Exception as e:
        logging.error(f"Error getting technician performance: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def get_order_details(order_id: int) -> Optional[Dict]:
    """Get order details"""
    return await get_zayavka_by_id(order_id)

async def update_order_priority(order_id: int, priority: str) -> bool:
    """Update order priority"""
    conn = await db_manager.get_connection()
    try:
        query = "UPDATE zayavki SET priority = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
        await conn.execute(query, priority, order_id)
        return True
    except Exception as e:
        logging.error(f"Error updating order priority: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_orders_by_status(statuses: List[str]) -> List[Dict]:
    """Get orders by status"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        WHERE z.status = ANY($1)
        ORDER BY z.created_at DESC
        """
        results = await conn.fetch(query, statuses)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting orders by status: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_all_feedback() -> List[Dict]:
    """Get all feedback"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT f.*, u.full_name as client_name, z.description as order_description
        FROM feedback f
        LEFT JOIN users u ON f.user_id = u.id
        LEFT JOIN zayavki z ON f.zayavka_id = z.id
        ORDER BY f.created_at DESC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting all feedback: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_feedback_by_rating(ratings: List[int]) -> List[Dict]:
    """Get feedback by rating"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT f.*, u.full_name as client_name, z.description as order_description
        FROM feedback f
        LEFT JOIN users u ON f.user_id = u.id
        LEFT JOIN zayavki z ON f.zayavka_id = z.id
        WHERE f.rating = ANY($1)
        ORDER BY f.created_at DESC
        """
        results = await conn.fetch(query, ratings)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting feedback by rating: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_recent_feedback(days: int = 7) -> List[Dict]:
    """Get recent feedback"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT f.*, u.full_name as client_name, z.description as order_description
        FROM feedback f
        LEFT JOIN users u ON f.user_id = u.id
        LEFT JOIN zayavki z ON f.zayavka_id = z.id
        WHERE f.created_at >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY f.created_at DESC
        """ % days
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting recent feedback: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_unresolved_issues() -> List[Dict]:
    """Get unresolved issues"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT z.*, u.full_name as client_name,
               EXTRACT(DAY FROM (CURRENT_TIMESTAMP - z.created_at)) as days_pending
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        WHERE z.status IN ('new', 'pending', 'assigned') 
        AND z.created_at <= CURRENT_TIMESTAMP - INTERVAL '2 days'
        ORDER BY z.created_at ASC
        """
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting unresolved issues: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_service_quality_metrics() -> Dict:
    """Get service quality metrics"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT 
            AVG(rating) as avg_rating,
            COUNT(*) as total_reviews,
            COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_reviews
        FROM feedback
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        result = await conn.fetchrow(query)
        
        if result:
            total_reviews = result['total_reviews'] or 0
            positive_reviews = result['positive_reviews'] or 0
            satisfaction_rate = (positive_reviews / total_reviews * 100) if total_reviews > 0 else 0
            
            # Get rating distribution
            distribution_query = """
            SELECT rating, COUNT(*) as count
            FROM feedback
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY rating
            ORDER BY rating DESC
            """
            distribution_results = await conn.fetch(distribution_query)
            rating_distribution = {row['rating']: row['count'] for row in distribution_results}
            
            return {
                'avg_rating': float(result['avg_rating']) if result['avg_rating'] else 0.0,
                'total_reviews': total_reviews,
                'satisfaction_rate': round(satisfaction_rate, 1),
                'rating_distribution': rating_distribution
            }
        return {}
    except Exception as e:
        logging.error(f"Error getting service quality metrics: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def get_quality_trends() -> List[Dict]:
    """Get quality trends"""
    conn = await db_manager.get_connection()
    try:
        query = """
        SELECT 
            DATE_TRUNC('week', created_at) as period,
            AVG(rating) as avg_rating,
            COUNT(*) as review_count
        FROM feedback
        WHERE created_at >= CURRENT_DATE - INTERVAL '8 weeks'
        GROUP BY DATE_TRUNC('week', created_at)
        ORDER BY period DESC
        """
        results = await conn.fetch(query)
        
        trends = []
        prev_rating = None
        
        for row in results:
            current_rating = float(row['avg_rating']) if row['avg_rating'] else 0
            change = (current_rating - prev_rating) if prev_rating else 0
            
            trends.append({
                'period': row['period'].strftime('%Y-%m-%d'),
                'avg_rating': current_rating,
                'change': round(change, 1),
                'review_count': row['review_count']
            })
            
            prev_rating = current_rating
        
        return trends
    except Exception as e:
        logging.error(f"Error getting quality trends: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def get_materials() -> List[Dict]:
    """Get materials list"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT * FROM materials WHERE is_active = true ORDER BY name"
        results = await conn.fetch(query)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting materials: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

# ==================== WAREHOUSE QUERIES ====================

async def get_inventory_items(category: str = None) -> List[Dict]:
    """Get inventory items"""
    return await get_materials()

async def add_inventory_item(item_data: Dict) -> bool:
    """Add inventory item"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO materials (name, quantity, unit, min_quantity, description, category, price, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, true)
        """
        await conn.execute(
            query,
            item_data['name'],
            item_data['quantity'],
            item_data.get('unit', 'pcs'),
            item_data.get('min_quantity', 5),
            item_data.get('description', ''),
            item_data.get('category', 'general'),
            item_data.get('price', 0)
        )
        return True
    except Exception as e:
        logging.error(f"Error adding inventory item: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def update_inventory_item(item_id: int, item_data: Dict) -> bool:
    """Update inventory item"""
    async with (await db_manager.get_connection()) as conn:
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

async def get_low_stock_items() -> List[Dict]:
    """Get low stock items"""
    conn = await db_manager.get_connection()
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
        await db_manager.pool.release(conn)

async def get_warehouse_statistics(period: str = 'daily') -> Dict:
    """Get warehouse statistics"""
    conn = await db_manager.get_connection()
    try:
        if period == 'daily':
            date_filter = "DATE(created_at) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'monthly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        else:  # turnover
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        
        # Mock statistics for now
        return {
            'items_added': 15,
            'items_issued': 8,
            'total_value': 2500000,
            'low_stock_count': 3,
            'turnover_rate': 85.5
        }
    except Exception as e:
        logging.error(f"Error getting warehouse statistics: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def export_warehouse_data(format_type: str) -> Optional[str]:
    """Export warehouse data"""
    try:
        # Mock export functionality
        filename = f"warehouse_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        # In real implementation, generate actual file
        return filename
    except Exception as e:
        logging.error(f"Error exporting warehouse data: {e}")
        return None

async def get_warehouse_staff() -> List[Dict]:
    """Get warehouse staff"""
    async with (await db_manager.get_connection()) as conn:
        try:
            query = "SELECT * FROM users WHERE role = 'warehouse' AND is_active = true"
            results = await conn.fetch(query)
            return [dict(row) for row in results]
        except Exception as e:
            logging.error(f"Error getting warehouse staff: {e}")
            return []

# ==================== EQUIPMENT MANAGEMENT ====================

async def get_equipment_list() -> List[Dict]:
    """Get equipment list"""
    async with (await db_manager.get_connection()) as conn:
        try:
            query = "SELECT * FROM equipment WHERE is_active = true ORDER BY name"
            results = await conn.fetch(query)
            return [dict(row) for row in results]
        except Exception as e:
            logging.error(f"Error getting equipment list: {e}")
            return []

async def mark_equipment_ready(equipment_id: int) -> bool:
    """Mark equipment as ready"""
    async with (await db_manager.get_connection()) as conn:
        try:
            query = "UPDATE equipment SET status = 'ready', updated_at = CURRENT_TIMESTAMP WHERE id = $1"
            await conn.execute(query, equipment_id)
            return True
        except Exception as e:
            logging.error(f"Error marking equipment ready: {e}")
            return False

async def mark_ready_for_installation(application_id: int) -> bool:
    """Mark application as ready for installation"""
    async with (await db_manager.get_connection()) as conn:
        try:
            query = "UPDATE zayavki SET status = 'ready_for_installation', updated_at = CURRENT_TIMESTAMP WHERE id = $1"
            await conn.execute(query, application_id)
            return True
        except Exception as e:
            logging.error(f"Error marking ready for installation: {e}")
            return False

async def issue_equipment(equipment_id, user_id):
    try:
        async with (await db_manager.get_connection()) as conn:
            # Mark equipment as not ready to install
            await conn.execute('''
                UPDATE materials SET ready_to_install = FALSE WHERE id = $1
            ''', equipment_id)
            # Log the issuance
            await conn.execute('''
                INSERT INTO issued_items (material_id, quantity, issued_by)
                VALUES ($1, 1, $2)
            ''', equipment_id, user_id)
        return True
    except Exception as e:
        logging.error(f"Error issuing equipment: {e}")
        return False

# ==================== STAFF ACTIVITY ====================

async def get_staff_activity_stats(activity_type: str) -> Dict:
    """Get staff activity statistics"""
    async with (await db_manager.get_connection()) as conn:
        try:
            if activity_type == 'technician_performance':
                query = """
                SELECT 
                    u.full_name as name,
                    COUNT(z.id) as total_tasks,
                    COUNT(CASE WHEN z.status = 'completed' THEN 1 END) as completed_tasks,
                    (COUNT(CASE WHEN z.status = 'completed' THEN 1 END)::float / 
                     NULLIF(COUNT(z.id), 0) * 100) as score
                FROM users u
                LEFT JOIN zayavki z ON u.id = z.assigned_to
                WHERE u.role = 'technician' AND u.is_active = true
                GROUP BY u.id, u.full_name
                ORDER BY score DESC
                LIMIT 5
                """
                results = await conn.fetch(query)
                top_performers = [{'name': row['name'], 'score': round(float(row['score']) if row['score'] else 0, 1)} for row in results]
                
                return {
                    'active_staff': len(results),
                    'completed_tasks': sum(row['completed_tasks'] for row in results),
                    'avg_performance': round(sum(float(row['score']) if row['score'] else 0 for row in results) / len(results) if results else 0, 1),
                    'top_performers': top_performers
                }
            else:
                # Mock data for other activity types
                return {
                    'active_staff': 12,
                    'completed_tasks': 45,
                    'avg_performance': 87.5
                }
        except Exception as e:
            logging.error(f"Error getting staff activity stats: {e}")
            return {}

# ==================== NOTIFICATION SETTINGS ====================

async def get_notification_settings(user_id: int) -> Dict:
    """Get notification settings"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT * FROM notification_settings WHERE user_id = $1"
        result = await conn.fetchrow(query, user_id)
        if result:
            return dict(result)
        else:
            # Return default settings
            return {
                'new_orders': True,
                'status_changes': True,
                'urgent_issues': True,
                'daily_summary': False,
                'system_alerts': True
            }
    except Exception as e:
        logging.error(f"Error getting notification settings: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def update_notification_settings(user_id: int, settings: Dict) -> bool:
    """Update notification settings"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO notification_settings (user_id, new_orders, status_changes, urgent_issues, daily_summary, system_alerts)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            new_orders = EXCLUDED.new_orders,
            status_changes = EXCLUDED.status_changes,
            urgent_issues = EXCLUDED.urgent_issues,
            daily_summary = EXCLUDED.daily_summary,
            system_alerts = EXCLUDED.system_alerts,
            updated_at = CURRENT_TIMESTAMP
        """
        await conn.execute(
            query,
            user_id,
            settings.get('new_orders', True),
            settings.get('status_changes', True),
            settings.get('urgent_issues', True),
            settings.get('daily_summary', False),
            settings.get('system_alerts', True)
        )
        return True
    except Exception as e:
        logging.error(f"Error updating notification settings: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

# ==================== CLIENT SPECIFIC ====================

async def get_client_info(user_id: int) -> Optional[Dict]:
    """Get client information"""
    return await get_user_by_id(user_id)

async def update_client_info(user_id: int, info_data: Dict) -> bool:
    """Update client information"""
    return await update_user_profile(user_id, info_data)

async def create_support_ticket(ticket_data: Dict) -> Optional[int]:
    """Create support ticket"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO support_tickets (user_id, subject, message, media, priority, status)
        VALUES ($1, $2, $3, $4, $5, 'open')
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            ticket_data['user_id'],
            ticket_data['subject'],
            ticket_data['message'],
            ticket_data.get('media'),
            ticket_data.get('priority', 'normal')
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating support ticket: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

# ==================== HELP REQUESTS ====================

async def create_help_request(help_data: Dict) -> Optional[int]:
    """Create help request"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO help_requests (technician_id, help_type, description, media, location, priority, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'pending')
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            help_data['technician_id'],
            help_data['help_type'],
            help_data['description'],
            help_data.get('media'),
            help_data.get('location'),
            help_data.get('priority', 'normal')
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating help request: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

# ==================== UTILITY FUNCTIONS ====================

async def init_database():
    """Initialize database connection"""
    await db_manager.init_pool()

async def close_database():
    """Close database connection"""
    await db_manager.close_pool()

# Import quality control functions if they exist
try:
    from database.quality_queries import *
except ImportError:
    pass

async def create_tables(pool):
    async with pool.acquire() as conn:
        # Users table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            phone_number VARCHAR(20),
            abonent_id VARCHAR(50),
            role VARCHAR(20) NOT NULL DEFAULT 'client',
            language VARCHAR(2) DEFAULT 'uz',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        # Materials table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            stock INTEGER DEFAULT 0 CHECK (stock >= 0),
            ready_to_install BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        # Zayavki table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS zayavki (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            description TEXT NOT NULL,
            media TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'new',
            address TEXT,
            location TEXT,
            zayavka_type VARCHAR(50),
            abonent_id VARCHAR(50),
            assigned_to BIGINT REFERENCES users(id) ON DELETE SET NULL,
            ready_to_install BOOLEAN DEFAULT FALSE,
            created_by_role VARCHAR(20),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP WITH TIME ZONE
        );
        ''')
        # Solutions table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS solutions (
            id SERIAL PRIMARY KEY,
            zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
            instander_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            solution_text TEXT NOT NULL,
            media TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        # Feedback table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            rating INTEGER CHECK (rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        # Status Logs table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS status_logs (
            id SERIAL PRIMARY KEY,
            zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
            changed_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
            old_status VARCHAR(20),
            new_status VARCHAR(20),
            changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        # Issued Items table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS issued_items (
            id SERIAL PRIMARY KEY,
            zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
            material_id INTEGER REFERENCES materials(id) ON DELETE SET NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            issued_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
            issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        # Login Logs table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            ip_address TEXT,
            user_agent TEXT,
            logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        # Notifications table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
            zayavka_id BIGINT REFERENCES zayavki(id) ON DELETE SET NULL,
            message TEXT NOT NULL,
            channel VARCHAR(10),
            sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')

def set_pool(pool):
    db_manager.pool = pool

async def add_missing_columns(pool):
    async with pool.acquire() as conn:
        # Example: Add address column to users if missing
        await conn.execute('''
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='address') THEN
                ALTER TABLE users ADD COLUMN address TEXT;
            END IF;
        END$$;
        ''')
        # Add other missing columns as needed, following the same pattern

async def get_zayavki_by_status(conn, status):
    query = '''
        SELECT z.id, z.description, z.address, z.created_at, z.status,
               u.full_name as user_name, u.phone_number as user_phone, u.language,
               t.full_name as technician_name, t.phone_number as technician_phone
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        WHERE z.status = $1
        ORDER BY z.created_at DESC
    '''
    rows = await conn.fetch(query, status)
    return [dict(row) for row in rows]

async def assign_zayavka(conn, zayavka_id, staff_id):
    query = '''
        UPDATE zayavki
        SET assigned_to = $1
        WHERE id = $2
    '''
    await conn.execute(query, staff_id, zayavka_id)

async def get_staff_members(conn):
    query = '''
        SELECT id, full_name, role, telegram_id
        FROM users
        WHERE role IN ('admin', 'manager', 'technician', 'call_center', 'controller', 'warehouse')
        ORDER BY full_name
    '''
    rows = await conn.fetch(query)
    return [dict(row) for row in rows]

async def genere_report(report_format, lang):
    # This is a dummy implementation. Replace with real report generation as needed.
    suffix = '.docx' if report_format == 'word' else '.pdf' if report_format == 'pdf' else '.txt'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='w', encoding='utf-8') as f:
        if lang == 'uz':
            f.write('Bu test hisobot fayli. Format: ' + report_format.upper())
        else:
            f.write('Это тестовый файл отчета. Формат: ' + report_format.upper())
        return f.name

async def get_filtered_zayavki(filters):
    query = '''
        SELECT z.id, z.description, z.address, z.created_at, z.status,
               u.full_name as user_name, u.phone_number as user_phone, u.language,
               t.full_name as technician_name, t.phone_number as technician_phone
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        WHERE 1=1
    '''
    params = []
    if 'status' in filters:
        query += ' AND z.status = $' + str(len(params) + 1)
        params.append(filters['status'])
    if 'date' in filters:
        query += ' AND DATE(z.created_at) = $' + str(len(params) + 1)
        params.append(filters['date'])
    if 'technician' in filters:
        query += ' AND t.id = $' + str(len(params) + 1)
        params.append(filters['technician'])
    query += ' ORDER BY z.created_at DESC'
    conn = await db_manager.get_connection()
    try:
        rows = await conn.fetch(query, *params)
        return [dict(row) for row in rows]
    finally:
        await db_manager.pool.release(conn)

async def get_all_orders(limit: int = 20) -> list:
    """Barcha buyurtmalarni (zayavki) limit bilan qaytaradi"""
    conn = await db_manager.get_connection()
    try:
        query = '''
            SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            ORDER BY z.created_at DESC
            LIMIT $1
        '''
        results = await conn.fetch(query, limit)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting all orders: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)
