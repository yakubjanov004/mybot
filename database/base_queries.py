import asyncpg
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date, timedelta
import json
from utils.logger import setup_module_logger
logger = setup_module_logger("base_queries")
from database.models import User, Zayavka, Material, Feedback, Equipment, ChatMessage, HelpRequest, ServiceRequest, StateTransition

# User language functions
async def create_user_if_not_exists(
    telegram_id: int,
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    pool: asyncpg.Pool = None
) -> bool:
    """Create user if they don't exist in the database, always with role='client'"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        INSERT INTO users (telegram_id, username, role)
        VALUES ($1, $2, 'client')
        ON CONFLICT (telegram_id) DO NOTHING
    """
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(query, telegram_id, username)
            return True
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        return False

async def get_user_lang(telegram_id: int, pool: asyncpg.Pool = None) -> str:
    """Get user's language preference"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT language 
        FROM users 
        WHERE telegram_id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchval(query, telegram_id)
            return result or "uz"  # Default to 'uz' if no language is set
    except Exception as e:
        logger.error(f"Error getting user language: {str(e)}", exc_info=True)
        return "uz"  # Default to 'uz' on error

async def get_zayavka_by_id(zayavka_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
    """Get detailed information about a zayavka by its ID"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT 
            z.*, 
            u.full_name as client_name,
            u.phone_number as client_phone,
            u.telegram_id as client_telegram_id,
            u.language as client_language,
            t.full_name as technician_name,
            t.telegram_id as technician_telegram_id,
            t.language as technician_language,
            s.solution_text as solution
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        LEFT JOIN solutions s ON z.id = s.zayavka_id
        WHERE z.id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, zayavka_id)
            if result:
                return dict(result)
            return None
    except Exception as e:
        logger.error(f"Error getting zayavka by ID: {str(e)}", exc_info=True)
        return None

async def update_zayavka_status(zayavka_id: int, new_status: str, pool: asyncpg.Pool = None) -> bool:
    """Update zayavka status and log the change"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE zayavki 
        SET status = $1,
            status_updated_at = NOW()
        WHERE id = $2
        RETURNING id
    """
    
    try:
        async with pool.acquire() as conn:
            # Update status
            result = await conn.fetchval(query, new_status, zayavka_id)
            if not result:
                return False
            
            # Log status change
            await conn.execute(
                """
                    INSERT INTO status_logs (zayavka_id, old_status, new_status, changed_at)
                    SELECT id, status, $1, NOW()
                    FROM zayavki WHERE id = $2
                """,
                new_status, zayavka_id
            )
            return True
    except Exception as e:
        logger.error(f"Error updating zayavka status: {str(e)}", exc_info=True)
        return False

async def assign_technician(zayavka_id: int, technician_id: int, pool: asyncpg.Pool = None) -> bool:
    """Assign a technician to a zayavka"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE zayavki 
        SET assigned_to = $1, 
            status = 'assigned',
            assigned_at = NOW()
        WHERE id = $2
        RETURNING id
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchval(query, technician_id, zayavka_id)
            return result is not None
    except Exception as e:
        logger.error(f"Error assigning technician: {str(e)}", exc_info=True)
        return False

async def get_reports(report_type: str, start_date: date = None, end_date: date = None, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get reports based on type and date range"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    if report_type == 'daily':
        query = """
            SELECT 
                z.id as zayavka_id,
                z.created_at,
                u.full_name as client_name,
                z.status,
                z.priority,
                z.assigned_to,
                t.full_name as technician_name,
                z.solution_text
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            LEFT JOIN users t ON z.assigned_to = t.id
            WHERE z.created_at >= $1 AND z.created_at <= $2
            ORDER BY z.created_at DESC
        """
    elif report_type == 'monthly':
        query = """
            SELECT 
                DATE_TRUNC('day', z.created_at) as date,
                COUNT(*) as total_count,
                SUM(CASE WHEN z.status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN z.priority = 'high' THEN 1 ELSE 0 END) as high_priority_count
            FROM zayavki z
            WHERE z.created_at >= $1 AND z.created_at <= $2
            GROUP BY DATE_TRUNC('day', z.created_at)
            ORDER BY date
        """
    elif report_type == 'custom':
        query = """
            SELECT 
                z.id as zayavka_id,
                z.created_at,
                u.full_name as client_name,
                z.status,
                z.priority,
                z.assigned_to,
                t.full_name as technician_name,
                z.solution_text,
                z.status_updated_at
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            LEFT JOIN users t ON z.assigned_to = t.id
            WHERE z.created_at >= $1 AND z.created_at <= $2
            ORDER BY z.status_updated_at DESC
        """
    else:
        return []
    
    try:
        async with pool.acquire() as conn:
            if not start_date:
                start_date = date.today() - timedelta(days=1)
            if not end_date:
                end_date = date.today()
            
            result = await conn.fetch(query, start_date, end_date)
            return [dict(row) for row in result]
    except Exception as e:
        logger.error(f"Error getting reports: {str(e)}", exc_info=True)
        return []

class DatabaseManager:
    """Base database manager with common operations"""
    
    def __init__(self):
        self.pool = None

    async def init_pool(self):
        import asyncpg
        from config import config
        self.pool = await asyncpg.create_pool(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )

    def get_pool(self):
        if not self.pool:
            raise RuntimeError("Database pool is not initialized. Call init_pool() first.")
        return self.pool

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchval(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args) -> bool:
        if not self.pool:
            raise RuntimeError("Database pool is not initialized. Call init_pool() first.")
        """Execute a query without return"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *args)
                return True
        except Exception as e:
            logger.error(f"Database execute error: {str(e)}", exc_info=True)
            return False

# Order-related functions
async def get_all_orders(pool: asyncpg.Pool = None, limit: int = None) -> List[Dict[str, Any]]:
    """Get all orders with optional limit"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT 
            z.*, 
            u.full_name as client_name,
            u.phone_number as client_phone,
            u.telegram_id as client_telegram_id,
            u.language as client_language,
            t.full_name as technician_name,
            t.telegram_id as technician_telegram_id,
            t.language as technician_language,
            s.solution_text as solution
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        LEFT JOIN solutions s ON z.id = s.zayavka_id
        ORDER BY z.created_at DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    try:
        async with pool.acquire() as conn:
            results = await conn.fetch(query)
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting all orders: {str(e)}", exc_info=True)
        return []
        
async def get_orders_by_status(
    status: Union[str, List[str]], pool: asyncpg.Pool = None
) -> List[Dict[str, Any]]:
    """Get orders by status (single or multiple)"""
    if not pool:
        from loader import bot
        pool = bot.db

    if isinstance(status, list):
        query = """
            SELECT 
                z.*, 
                u.full_name as client_name,
                u.phone_number as client_phone,
                u.telegram_id as client_telegram_id,
                u.language as client_language,
                t.full_name as technician_name,
                t.telegram_id as technician_telegram_id,
                t.language as technician_language,
                s.solution_text as solution
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            LEFT JOIN users t ON z.assigned_to = t.id
            LEFT JOIN solutions s ON z.id = s.zayavka_id
            WHERE z.status = ANY($1)
            ORDER BY z.created_at DESC
        """
    else:
        query = """
            SELECT 
                z.*, 
                u.full_name as client_name,
                u.phone_number as client_phone,
                u.telegram_id as client_telegram_id,
                u.language as client_language,
                t.full_name as technician_name,
                t.telegram_id as technician_telegram_id,
                t.language as technician_language,
                s.solution_text as solution
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            LEFT JOIN users t ON z.assigned_to = t.id
            LEFT JOIN solutions s ON z.id = s.zayavka_id
            WHERE z.status = $1
            ORDER BY z.created_at DESC
        """

    try:
        async with pool.acquire() as conn:
            results = await conn.fetch(query, status)
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting orders by status: {str(e)}", exc_info=True)
        return []

async def get_order_details(order_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
    """Get detailed information about an order"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT 
            z.*, 
            u.full_name as client_name,
            u.phone_number as client_phone,
            u.telegram_id as client_telegram_id,
            u.language as client_language,
            t.full_name as technician_name,
            t.telegram_id as technician_telegram_id,
            t.language as technician_language,
            s.solution_text as solution,
            m.material_name as assigned_material,
            m.quantity as material_quantity,
            m.unit as material_unit
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        LEFT JOIN solutions s ON z.id = s.zayavka_id
        LEFT JOIN materials m ON z.id = m.zayavka_id
        WHERE z.id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, order_id)
            if result:
                return dict(result)
            return None
    except Exception as e:
        logger.error(f"Error getting order details: {str(e)}", exc_info=True)
        return None

async def update_order_priority(order_id: int, priority: str, pool: asyncpg.Pool = None) -> bool:
    """Update order priority"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE zayavki
        SET priority = $1
        WHERE id = $2
        RETURNING id
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchval(query, priority, order_id)
            return result is not None
    except Exception as e:
        logger.error(f"Error updating order priority: {str(e)}", exc_info=True)
        return False

async def get_unresolved_issues(pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get unresolved issues (open orders)"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT 
            z.*, 
            u.full_name as client_name,
            u.phone_number as client_phone,
            u.telegram_id as client_telegram_id,
            u.language as client_language,
            t.full_name as technician_name,
            t.telegram_id as technician_telegram_id,
            t.language as technician_language,
            s.solution_text as solution
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        LEFT JOIN solutions s ON z.id = s.zayavka_id
        WHERE z.status IN ('new', 'pending', 'assigned', 'in_progress')
        ORDER BY z.created_at DESC
    """
    
    try:
        async with pool.acquire() as conn:
            results = await conn.fetch(query)
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting unresolved issues: {str(e)}", exc_info=True)
        return []

# User management functions
async def get_user_by_telegram_id(telegram_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
    """Get user by telegram ID"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, telegram_id, full_name, username, phone_number, role, 
               abonent_id, language, is_active, address, permissions,
               created_at, updated_at
        FROM users 
        WHERE telegram_id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, telegram_id)
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting user by telegram_id {telegram_id}: {str(e)}")
        return None


async def get_user_by_id(user_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
    """Get user by database ID"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, telegram_id, full_name, username, phone_number, role, 
               abonent_id, language, is_active, address, permissions,
               created_at, updated_at
        FROM users 
        WHERE id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting user by ID {user_id}: {str(e)}")
        return None

# Technician-related functions
async def get_all_technicians(pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get all technicians"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT 
            u.*, 
            COUNT(z.id) as total_orders,
            COUNT(CASE WHEN z.status = 'completed' THEN 1 END) as completed_orders,
            COUNT(CASE WHEN z.status = 'in_progress' THEN 1 END) as active_orders
        FROM users u
        LEFT JOIN zayavki z ON u.id = z.assigned_to
        WHERE u.role = 'technician'
        GROUP BY u.id
        ORDER BY u.full_name
    """
    
    try:
        async with pool.acquire() as conn:
            results = await conn.fetch(query)
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting all technicians: {str(e)}", exc_info=True)
        return []

async def get_technician_details(technician_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
    """Get detailed information about a technician"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT 
            u.*, 
            COUNT(z.id) as total_orders,
            COUNT(CASE WHEN z.status = 'completed' THEN 1 END) as completed_orders,
            COUNT(CASE WHEN z.status = 'in_progress' THEN 1 END) as active_orders,
            COUNT(CASE WHEN z.status = 'cancelled' THEN 1 END) as cancelled_orders,
            COUNT(CASE WHEN z.status = 'rejected' THEN 1 END) as rejected_orders,
            AVG(CASE WHEN z.status = 'completed' THEN z.completion_time ELSE NULL END) as avg_completion_time
        FROM users u
        LEFT JOIN zayavki z ON u.id = z.assigned_to
        WHERE u.id = $1
        GROUP BY u.id
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, technician_id)
            if result:
                return dict(result)
            return None
    except Exception as e:
        logger.error(f"Error getting technician details: {str(e)}", exc_info=True)
        return None

async def update_technician_status(technician_id: int, is_active: bool, pool: asyncpg.Pool = None) -> bool:
    """Update technician's active status"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE users
        SET is_active = $1
        WHERE id = $2
        RETURNING id
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchval(query, is_active, technician_id)
            return result is not None
    except Exception as e:
        logger.error(f"Error updating technician status: {str(e)}", exc_info=True)
        return False

# Report-related functions
async def get_system_statistics(pool: asyncpg.Pool = None) -> Dict[str, Any]:
    """Get system-wide statistics"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        WITH 
            orders_stats AS (
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_orders,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_orders
                FROM zayavki
            ),
            users_stats AS (
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN role = 'technician' THEN 1 END) as total_technicians,
                    COUNT(CASE WHEN role = 'controller' THEN 1 END) as total_controllers,
                    COUNT(CASE WHEN role = 'call_center' THEN 1 END) as total_call_center
                FROM users
            ),
            performance_stats AS (
                SELECT 
                    AVG(completion_time) as avg_completion_time,
                    MAX(completion_time) as max_completion_time,
                    MIN(completion_time) as min_completion_time
                FROM zayavki
                WHERE status = 'completed'
            )
        SELECT 
            o.total_orders,
            o.completed_orders,
            o.active_orders,
            o.cancelled_orders,
            o.rejected_orders,
            u.total_users,
            u.total_technicians,
            u.total_controllers,
            u.total_call_center,
            p.avg_completion_time,
            p.max_completion_time,
            p.min_completion_time
        FROM orders_stats o
        CROSS JOIN users_stats u
        CROSS JOIN performance_stats p
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query)
            return dict(result) if result else {}
    except Exception as e:
        logger.error(f"Error getting system statistics: {str(e)}", exc_info=True)
        return {}

async def get_technician_performance(technician_id: int, pool: asyncpg.Pool = None) -> Dict[str, Any]:
    """Get technician performance metrics"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        WITH 
            order_stats AS (
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_orders,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_orders
                FROM zayavki
                WHERE assigned_to = $1
            ),
            time_stats AS (
                SELECT 
                    AVG(completion_time) as avg_completion_time,
                    MAX(completion_time) as max_completion_time,
                    MIN(completion_time) as min_completion_time
                FROM zayavki
                WHERE assigned_to = $1 AND status = 'completed'
            )
        SELECT 
            u.*, 
            o.total_orders,
            o.completed_orders,
            o.active_orders,
            o.cancelled_orders,
            o.rejected_orders,
            t.avg_completion_time,
            t.max_completion_time,
            t.min_completion_time,
            CASE 
                WHEN o.completed_orders > 0 THEN 
                    CAST(o.completed_orders as float) / o.total_orders * 100
                ELSE 0
            END as completion_rate
        FROM users u
        CROSS JOIN order_stats o
        CROSS JOIN time_stats t
        WHERE u.id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, technician_id)
            return dict(result) if result else {}
    except Exception as e:
        logger.error(f"Error getting technician performance: {str(e)}", exc_info=True)
        return {}

async def get_service_quality_metrics(pool: asyncpg.Pool = None) -> Dict[str, Any]:
    """Get service quality metrics"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        WITH 
            order_stats AS (
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_orders
                FROM zayavki
            ),
            feedback_stats AS (
                SELECT 
                    AVG(rating) as avg_rating,
                    COUNT(*) as total_feedbacks,
                    COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedbacks,
                    COUNT(CASE WHEN rating < 3 THEN 1 END) as negative_feedbacks
                FROM feedback
            )
        SELECT 
            o.total_orders,
            o.completed_orders,
            o.cancelled_orders,
            o.rejected_orders,
            NULL as avg_completion_time,
            NULL as max_completion_time,
            NULL as min_completion_time,
            f.avg_rating,
            f.total_feedbacks,
            f.positive_feedbacks,
            f.negative_feedbacks,
            CASE 
                WHEN o.total_orders > 0 THEN 
                    CAST(o.completed_orders as float) / o.total_orders * 100
                ELSE 0
            END as completion_rate,
            CASE 
                WHEN f.total_feedbacks > 0 THEN 
                    CAST(f.positive_feedbacks as float) / f.total_feedbacks * 100
                ELSE 0
            END as positive_feedback_rate
        FROM order_stats o
        CROSS JOIN feedback_stats f
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query)
            return dict(result) if result else {}
    except Exception as e:
        logger.error(f"Error getting service quality metrics: {str(e)}", exc_info=True)
        return {}


async def update_client_info(client_id: int, update_data: dict, pool: asyncpg.Pool = None) -> bool:
    """
    Update client information in the users table.
    update_data: dict of fields to update (e.g. {'full_name': '...', 'phone_number': '...'})
    """
    if not pool:
        from loader import bot
        pool = bot.db

    allowed_fields = ['full_name', 'phone_number', 'address', 'language']
    fields = []
    values = []
    param_count = 1

    for field, value in update_data.items():
        if field in allowed_fields:
            fields.append(f"{field} = ${param_count}")
            values.append(value)
            param_count += 1

    if not fields:
        return False

    # Always update updated_at
    fields.append(f"updated_at = ${param_count}")
    from datetime import datetime
    values.append(datetime.now())
    param_count += 1

    query = f"UPDATE users SET {', '.join(fields)} WHERE id = ${param_count}"
    values.append(client_id)

    try:
        async with pool.acquire() as conn:
            await conn.execute(query, *values)
            return True
    except Exception as e:
        logger.error(f"Error updating client info for user_id {client_id}: {str(e)}")
        return False

async def create_user(telegram_id: int, full_name: str = None, username: str = None, 
                     phone_number: str = None, role: str = 'client', language: str = 'uz',
                     pool: asyncpg.Pool = None) -> Optional[int]:
    """Create new user"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        INSERT INTO users (telegram_id, full_name, username, phone_number, role, language)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    """
    
    try:
        async with pool.acquire() as conn:
            user_id = await conn.fetchval(query, telegram_id, full_name, username, phone_number, role, language)
            logger.info(f"Created user {user_id} with telegram_id {telegram_id}")
            return user_id
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None

async def update_user_language(telegram_id: int, language: str, pool: asyncpg.Pool = None) -> bool:
    """Update user language"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE users 
        SET language = $2, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(query, telegram_id, language)
            logger.info(f"Updated language for user {telegram_id} to {language}")
            return True
    except Exception as e:
        logger.error(f"Error updating user language: {str(e)}")
        return False

async def update_user_full_name(telegram_id: int, full_name: str, pool: asyncpg.Pool = None) -> bool:
    """Update user's full name"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE users 
        SET full_name = $2, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(query, telegram_id, full_name)
            logger.info(f"Updated full name for user {telegram_id} to {full_name}")
            return True
    except Exception as e:
        logger.error(f"Error updating user full name: {str(e)}")
        return False

async def update_user_phone(telegram_id: int, phone_number: str, pool: asyncpg.Pool = None) -> bool:
    """Update user's phone number"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE users 
        SET phone_number = $2, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(query, telegram_id, phone_number)
            logger.info(f"Updated phone for user {telegram_id} to {phone_number}")
            return True
    except Exception as e:
        logger.error(f"Error updating user phone: {str(e)}")
        return False

async def update_user_address(telegram_id: int, address: str, pool: asyncpg.Pool = None) -> bool:
    """Update user's address"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE users 
        SET address = $2, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(query, telegram_id, address)
            logger.info(f"Updated address for user {telegram_id} to {address}")
            return True
    except Exception as e:
        logger.error(f"Error updating user address: {str(e)}")
        return False

# Zayavka management functions
async def create_zayavka(user_id: int, description: str, address: str = None, 
                        phone_number: str = None, media: str = None, 
                        zayavka_type: str = None, latitude: float = None, 
                        longitude: float = None, created_by: int = None,
                        created_by_role: str = None, tariff: str = None, pool: asyncpg.Pool = None) -> Optional[int]:
    """Create new zayavka with public_id"""
    if not pool:
        from loader import bot
        pool = bot.db

    async with pool.acquire() as conn:
        query = """
            INSERT INTO zayavki (
                user_id, description, address, phone_number, media, 
                zayavka_type, latitude, longitude, created_by, created_by_role, tariff,
                status, priority, ready_to_install
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10, $11,
                'new', 1, false
            )
            RETURNING id
        """
        try:
            zayavka_id = await conn.fetchval(
                query, 
                user_id, description, address, phone_number, media,
                zayavka_type, latitude, longitude, created_by, created_by_role, tariff
            )
            # Use the auto-generated id for public_id
            prefix = "TX" if zayavka_type == "service" else "UL"
            public_id = f"{prefix}-{zayavka_id}"
            logger.info(f"Created zayavka {zayavka_id} for user {user_id} (public_id={public_id})")
            return zayavka_id, public_id
        except Exception as e:
            logger.error(f"Error creating zayavka: {str(e)}")
            return None, None

async def get_zayavka_by_id(zayavka_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
    """Get zayavka by ID"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT z.*, u.full_name as user_name, u.phone_number as user_phone,
               t.full_name as technician_name
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users t ON z.assigned_to = t.id
        WHERE z.id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, zayavka_id)
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting zayavka {zayavka_id}: {str(e)}")
        return None

async def get_user_zayavkas(user_id: int, limit: int = 10, offset: int = 0, 
                           pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get user's zayavkas"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT z.*, t.full_name as technician_name
        FROM zayavki z
        LEFT JOIN users t ON z.assigned_to = t.id
        WHERE z.user_id = $1
        ORDER BY z.created_at DESC
        LIMIT $2 OFFSET $3
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit, offset)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting user zayavkas: {str(e)}")
        return []

async def update_zayavka_status(zayavka_id: int, new_status: str, changed_by: int,
                               pool: asyncpg.Pool = None) -> bool:
    """Update zayavka status"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            # Get current status
            current_status = await conn.fetchval(
                "SELECT status FROM zayavki WHERE id = $1", zayavka_id
            )
            
            if not current_status:
                return False
            
            # Update status
            await conn.execute(
                "UPDATE zayavki SET status = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                zayavka_id, new_status
            )
            
            # Log status change
            await conn.execute(
                """INSERT INTO status_logs (zayavka_id, old_status, new_status, changed_by)
                   VALUES ($1, $2, $3, $4)""",
                zayavka_id, current_status, new_status, changed_by
            )
            
            logger.info(f"Updated zayavka {zayavka_id} status from {current_status} to {new_status}")
            return True
    except Exception as e:
        logger.error(f"Error updating zayavka status: {str(e)}")
        return False

async def assign_zayavka(zayavka_id: int, technician_id: int, assigned_by: int,
                        pool: asyncpg.Pool = None) -> bool:
    """Assign zayavka to technician"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE zayavki 
        SET assigned_to = $2, assigned_at = CURRENT_TIMESTAMP, 
            status = 'assigned', updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(query, zayavka_id, technician_id)
            
            # Log status change
            await conn.execute(
                """INSERT INTO status_logs (zayavka_id, old_status, new_status, changed_by)
                   VALUES ($1, 'new', 'assigned', $2)""",
                zayavka_id, assigned_by
            )
            
            logger.info(f"Assigned zayavka {zayavka_id} to technician {technician_id}")
            return True
    except Exception as e:
        logger.error(f"Error assigning zayavka: {str(e)}")
        return False

assign_zayavka_to_technician = assign_zayavka

# Material management functions
async def get_all_materials(pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get all materials"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, name, category, quantity, unit, min_quantity, price, 
               description, supplier, is_active, created_at, updated_at
        FROM materials 
        WHERE is_active = true
        ORDER BY name
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting materials: {str(e)}")
        return []

async def update_material_quantity(material_id: int, quantity: int, updated_by: int,
                                  pool: asyncpg.Pool = None) -> bool:
    """Update material quantity"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        UPDATE materials 
        SET quantity = $2, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(query, material_id, quantity)
            logger.info(f"Updated material {material_id} quantity to {quantity}")
            return True
    except Exception as e:
        logger.error(f"Error updating material quantity: {str(e)}")
        return False

# Statistics functions
async def get_user_statistics(pool: asyncpg.Pool = None) -> Dict[str, Any]:
    """Get user statistics"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = true")
            
            role_stats = await conn.fetch("""
                SELECT role, COUNT(*) as count 
                FROM users 
                WHERE is_active = true 
                GROUP BY role
            """)
            
            return {
                'total_users': total_users,
                'role_distribution': {row['role']: row['count'] for row in role_stats}
            }
    except Exception as e:
        logger.error(f"Error getting user statistics: {str(e)}")
        return {'total_users': 0, 'role_distribution': {}}

async def get_zayavka_statistics(pool: asyncpg.Pool = None) -> Dict[str, Any]:
    """Get zayavka statistics"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            total_zayavkas = await conn.fetchval("SELECT COUNT(*) FROM zayavki")
            
            status_stats = await conn.fetch("""
                SELECT status, COUNT(*) as count 
                FROM zayavki 
                GROUP BY status
            """)
            
            today_zayavkas = await conn.fetchval("""
                SELECT COUNT(*) FROM zayavki 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            
            return {
                'total_zayavkas': total_zayavkas,
                'today_zayavkas': today_zayavkas,
                'status_distribution': {row['status']: row['count'] for row in status_stats}
            }
    except Exception as e:
        logger.error(f"Error getting zayavka statistics: {str(e)}")
        return {'total_zayavkas': 0, 'today_zayavkas': 0, 'status_distribution': {}}

async def get_system_statistics(pool: asyncpg.Pool = None) -> Dict[str, Any]:
    """Get overall system statistics (users + zayavkas)"""
    if not pool:
        from loader import bot
        pool = bot.db
    try:
        user_stats = await get_user_statistics(pool)
        zayavka_stats = await get_zayavka_statistics(pool)
        return {
            'users': user_stats,
            'zayavkas': zayavka_stats
        }
    except Exception as e:
        logger.error(f"Error getting system statistics: {str(e)}")
        return {'users': {}, 'zayavkas': {}}

# Feedback functions
async def create_feedback(zayavka_id: int, user_id: int, rating: int, 
                         comment: str = None, pool: asyncpg.Pool = None) -> Optional[int]:
    """Create feedback"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        INSERT INTO feedback (zayavka_id, user_id, rating, comment)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """
    
    try:
        async with pool.acquire() as conn:
            feedback_id = await conn.fetchval(query, zayavka_id, user_id, rating, comment)
            logger.info(f"Created feedback {feedback_id} for zayavka {zayavka_id}")
            return feedback_id
    except Exception as e:
        logger.error(f"Error creating feedback: {str(e)}")
        return None

# Help request functions
async def create_help_request(technician_id: int, help_type: str, description: str,
                             priority: str = 'medium', pool: asyncpg.Pool = None) -> Optional[int]:
    """Create help request"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        INSERT INTO help_requests (technician_id, help_type, description, priority)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """
    
    try:
        async with pool.acquire() as conn:
            request_id = await conn.fetchval(query, technician_id, help_type, description, priority)
            logger.info(f"Created help request {request_id} for technician {technician_id}")
            return request_id
    except Exception as e:
        logger.error(f"Error creating help request: {str(e)}")
        return None

# Search functions
async def search_users(search_term: str, limit: int = 10, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Search users by name or phone"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, telegram_id, full_name, username, phone_number, role, language
        FROM users 
        WHERE (full_name ILIKE $1 OR phone_number ILIKE $1 OR username ILIKE $1)
        AND is_active = true
        ORDER BY full_name
        LIMIT $2
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, f"%{search_term}%", limit)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        return []

async def get_technicians(pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get all technicians"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, telegram_id, full_name, phone_number, language,
               (SELECT COUNT(*) FROM zayavki WHERE assigned_to = users.id AND status IN ('assigned', 'in_progress')) as active_tasks
        FROM users 
        WHERE role = 'technician' AND is_active = true
        ORDER BY full_name
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting technicians: {str(e)}")
        return []

async def get_staff_members(pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get all staff members (non-client users)"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, telegram_id, full_name, phone_number, role, language
        FROM users 
        WHERE role != 'client' AND is_active = true
        ORDER BY role, full_name
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting staff members: {str(e)}")
        return []

# Alias for compatibility with handler imports
get_application_by_id = get_zayavka_by_id

async def set_user_language(telegram_id: int, language: str, pool: asyncpg.Pool = None) -> bool:
    """Set user language in database (wrapper for update_user_language)"""
    from utils.logger import setup_module_logger
    logger = setup_module_logger("base_queries")
    from utils.get_lang import is_supported_language
    if not is_supported_language(language):
        logger.warning(f"Unsupported language: {language}")
        return False
    try:
        success = await update_user_language(telegram_id, language, pool)
        if success:
            logger.info(f"Updated language for user {telegram_id} to {language}")
        return success
    except Exception as e:
        logger.error(f"Error setting user language: {str(e)}")
        return False
# ===== WORKFLOW SYSTEM DATABASE QUERIES =====

async def get_service_request_by_id(request_id: str, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
    """Get service request by ID"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, workflow_type, client_id, role_current , current_status,
               created_at, updated_at, priority, description, location,
               contact_info, state_data, equipment_used, inventory_updated,
               completion_rating, feedback_comments
        FROM service_requests
        WHERE id = $1
    """
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, request_id)
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting service request by ID: {e}", exc_info=True)
        return None

async def get_service_requests_by_role(role: str, status_filter: str = None, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get service requests assigned to specific role"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    base_query = """
        SELECT sr.id, sr.workflow_type, sr.client_id, sr.role_current , sr.current_status,
               sr.created_at, sr.updated_at, sr.priority, sr.description, sr.location,
               sr.contact_info, sr.state_data, sr.equipment_used, sr.inventory_updated,
               sr.completion_rating, sr.feedback_comments,
               u.full_name as client_name, u.phone_number as client_phone
        FROM service_requests sr
        LEFT JOIN users u ON sr.client_id = u.id
        WHERE sr.role_current = $1
    """
    
    params = [role]
    
    if status_filter:
        base_query += " AND sr.current_status = $2"
        params.append(status_filter)
    
    base_query += " ORDER BY sr.priority DESC, sr.created_at DESC"
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting service requests by role: {e}", exc_info=True)
        return []

async def get_service_requests_by_client(client_id: int, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get service requests for specific client"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, workflow_type, client_id, role_current , current_status,
               created_at, updated_at, priority, description, location,
               contact_info, state_data, equipment_used, inventory_updated,
               completion_rating, feedback_comments
        FROM service_requests
        WHERE client_id = $1
        ORDER BY created_at DESC
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, client_id)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting service requests by client: {e}", exc_info=True)
        return []

async def get_state_transitions_by_request(request_id: str, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get state transitions for a request"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT st.id, st.request_id, st.from_role, st.to_role, st.action, 
               st.actor_id, st.transition_data, st.comments, st.created_at,
               u.full_name as actor_name
        FROM state_transitions st
        LEFT JOIN users u ON st.actor_id = u.id
        WHERE st.request_id = $1
        ORDER BY st.created_at ASC
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, request_id)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting state transitions: {e}", exc_info=True)
        return []

async def get_pending_notifications_by_user(user_id: int, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get pending notifications for user"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT pn.id, pn.request_id, pn.workflow_type, pn.role, pn.created_at,
               sr.description, sr.priority, sr.current_status
        FROM pending_notifications pn
        JOIN service_requests sr ON pn.request_id = sr.id
        WHERE pn.user_id = $1 AND pn.is_handled = false
        ORDER BY pn.created_at DESC
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting pending notifications: {e}", exc_info=True)
        return []

async def get_inventory_transactions_by_request(request_id: str, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get inventory transactions for a request"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT it.*, m.name as material_name, m.category, u.full_name as performed_by_name
        FROM inventory_transactions it
        LEFT JOIN materials m ON it.material_id = m.id
        LEFT JOIN users u ON it.performed_by = u.id
        WHERE it.request_id = $1
        ORDER BY it.transaction_date DESC
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, request_id)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting inventory transactions: {e}", exc_info=True)
        return []

async def get_workflow_statistics(pool: asyncpg.Pool = None) -> Dict[str, Any]:
    """Get workflow system statistics"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        WITH workflow_stats AS (
            SELECT 
                workflow_type,
                current_status,
                COUNT(*) as count
            FROM service_requests
            GROUP BY workflow_type, current_status
        ),
        role_stats AS (
            SELECT 
                role_current ,
                COUNT(*) as pending_count
            FROM service_requests
            WHERE current_status IN ('created', 'in_progress')
            GROUP BY role_current 
        ),
        completion_stats AS (
            SELECT 
                workflow_type,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) as avg_completion_hours,
                COUNT(*) as completed_count
            FROM service_requests
            WHERE current_status = 'completed'
            GROUP BY workflow_type
        )
        SELECT 
            (SELECT json_agg(row_to_json(ws)) FROM workflow_stats ws) as workflow_stats,
            (SELECT json_agg(row_to_json(rs)) FROM role_stats rs) as role_stats,
            (SELECT json_agg(row_to_json(cs)) FROM completion_stats cs) as completion_stats,
            (SELECT COUNT(*) FROM service_requests) as total_requests,
            (SELECT COUNT(*) FROM service_requests WHERE current_status = 'completed') as completed_requests,
            (SELECT COUNT(*) FROM pending_notifications WHERE is_handled = false) as pending_notifications
    """
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return dict(row) if row else {}
    except Exception as e:
        logger.error(f"Error getting workflow statistics: {e}", exc_info=True)
        return {}

async def cleanup_old_notifications(days_old: int = 7, pool: asyncpg.Pool = None) -> int:
    """Cleanup old handled notifications"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        DELETE FROM pending_notifications 
        WHERE is_handled = true 
        AND handled_at < NOW() - INTERVAL '%s days'
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.execute(query, days_old)
            # Extract number of deleted rows from result
            deleted_count = int(result.split()[-1]) if result.startswith('DELETE') else 0
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {e}", exc_info=True)
        return 0

async def get_users_by_role(role: str, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get all users with specific role"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, telegram_id, full_name, username, phone_number, role, 
               language, is_active, created_at, updated_at
        FROM users 
        WHERE role = $1 AND is_active = true
        ORDER BY full_name
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, role)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting users by role: {e}", exc_info=True)
        return []

async def get_materials_with_low_stock(pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get materials with low stock levels"""
    if not pool:
        from loader import bot
        pool = bot.db
    
    query = """
        SELECT id, name, category, quantity_in_stock, min_quantity, unit, location
        FROM materials 
        WHERE is_active = true AND quantity_in_stock <= min_quantity
        ORDER BY (quantity_in_stock::float / NULLIF(min_quantity, 0)::float) ASC
    """
    
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting materials with low stock: {e}", exc_info=True)
        return []

# ===== END WORKFLOW SYSTEM QUERIES =====