import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from utils.logger import setup_module_logger
logger = setup_module_logger("queries")

# Database manager class
class db_manager:
    @staticmethod
    async def get_pool() -> asyncpg.Pool:
        """Get database connection pool"""
        from loader import bot
        return bot.pool

    @staticmethod
    async def execute(query: str, *args, timeout: float = None) -> Any:
        """Execute query with args"""
        pool = await db_manager.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    @staticmethod
    async def fetch(query: str, *args, timeout: float = None) -> List[Dict[str, Any]]:
        """Fetch results from query"""
        pool = await db_manager.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    @staticmethod
    async def fetchrow(query: str, *args, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Fetch single row from query"""
        pool = await db_manager.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)

    @staticmethod
    async def fetchval(query: str, *args, timeout: float = None) -> Any:
        """Fetch single value from query"""
        pool = await db_manager.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args, timeout=timeout)

# Report-related queries
class ReportQueries:
    @staticmethod
    async def get_system_statistics(pool: asyncpg.Pool = None) -> Dict[str, Any]:
        """Get system-wide statistics"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

    @staticmethod
    async def get_technician_performance(technician_id: int, pool: asyncpg.Pool = None) -> Dict[str, Any]:
        """Get technician performance metrics"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

    @staticmethod
    async def get_service_quality_metrics(pool: asyncpg.Pool = None) -> Dict[str, Any]:
        """Get service quality metrics"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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
                time_stats AS (
                    SELECT 
                        AVG(completion_time) as avg_completion_time,
                        MAX(completion_time) as max_completion_time,
                        MIN(completion_time) as min_completion_time
                    FROM zayavki
                    WHERE status = 'completed'
                ),
                feedback_stats AS (
                    SELECT 
                        AVG(rating) as avg_rating,
                        COUNT(*) as total_feedbacks,
                        COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedbacks,
                        COUNT(CASE WHEN rating < 3 THEN 1 END) as negative_feedbacks
                    FROM feedbacks
                )
            SELECT 
                o.total_orders,
                o.completed_orders,
                o.cancelled_orders,
                o.rejected_orders,
                t.avg_completion_time,
                t.max_completion_time,
                t.min_completion_time,
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
            CROSS JOIN time_stats t
            CROSS JOIN feedback_stats f
        """
        
        try:
            async with pool.acquire() as conn:
                result = await conn.fetchrow(query)
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Error getting service quality metrics: {str(e)}", exc_info=True)
            return {}

# Orders-related queries
class OrderQueries:
    @staticmethod
    async def get_all_orders(pool: asyncpg.Pool = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get all orders with optional limit"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

    @staticmethod
    async def get_orders_by_status(status: str, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
        """Get orders by status"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

    @staticmethod
    async def get_order_details(order_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about an order"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

    @staticmethod
    async def update_order_priority(order_id: int, priority: str, pool: asyncpg.Pool = None) -> bool:
        """Update order priority"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

    @staticmethod
    async def get_unresolved_issues(pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
        """Get unresolved issues (open orders)"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

# User-related queries
class UserQueries:
    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
        """Get user by telegram ID"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

    @staticmethod
    async def get_user_by_id(user_id: int, pool: asyncpg.Pool = None) -> Optional[Dict[str, Any]]:
        """Get user by database ID"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

# Feedback-related queries
class FeedbackQueries:
    @staticmethod
    async def get_all_feedback(pool: asyncpg.Pool = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get all feedback with optional limit"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
        query = """
            SELECT 
                f.*, 
                u.full_name as user_name,
                u.telegram_id as user_telegram_id,
                u.language as user_language,
                t.full_name as technician_name,
                t.telegram_id as technician_telegram_id,
                t.language as technician_language
            FROM feedbacks f
            LEFT JOIN users u ON f.user_id = u.id
            LEFT JOIN users t ON f.technician_id = t.id
            ORDER BY f.created_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            async with pool.acquire() as conn:
                results = await conn.fetch(query)
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting all feedback: {str(e)}", exc_info=True)
            return []

    @staticmethod
    async def get_feedback_by_rating(rating: int, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
        """Get feedback by rating"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
        query = """
            SELECT 
                f.*, 
                u.full_name as user_name,
                u.telegram_id as user_telegram_id,
                u.language as user_language,
                t.full_name as technician_name,
                t.telegram_id as technician_telegram_id,
                t.language as technician_language
            FROM feedbacks f
            LEFT JOIN users u ON f.user_id = u.id
            LEFT JOIN users t ON f.technician_id = t.id
            WHERE f.rating = $1
            ORDER BY f.created_at DESC
        """
        
        try:
            async with pool.acquire() as conn:
                results = await conn.fetch(query, rating)
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting feedback by rating: {str(e)}", exc_info=True)
            return []

    @staticmethod
    async def get_unresolved_issues(pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
        """Get unresolved issues (open orders)"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
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

    @staticmethod
    async def get_quality_trends(pool: asyncpg.Pool = None, period: str = 'monthly') -> List[Dict[str, Any]]:
        """Get quality trends over time"""
        if not pool:
            from loader import bot
            pool = bot.pool
        
        query = """
            SELECT 
                date_trunc($1, f.created_at) as period,
                AVG(rating) as avg_rating,
                COUNT(*) as total_feedbacks,
                COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedbacks,
                COUNT(CASE WHEN rating < 3 THEN 1 END) as negative_feedbacks
            FROM feedbacks f
            GROUP BY date_trunc($1, f.created_at)
            ORDER BY period DESC
        """
        
        try:
            async with pool.acquire() as conn:
                results = await conn.fetch(query, period)
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting quality trends: {str(e)}", exc_info=True)
            return []
