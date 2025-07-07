import asyncpg
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import logging
from config import config
from database.queries import db_manager

logger = logging.getLogger(__name__)

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

async def get_client_by_phone(phone: str) -> Optional[Dict]:
    """Get client by phone number"""
    conn = await db_manager.get_connection()
    try:
        query = "SELECT * FROM users WHERE phone_number = $1 AND role = 'client'"
        result = await conn.fetchrow(query, phone)
        return dict(result) if result else None
    except Exception as e:
        logging.error(f"Error getting client by phone: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def create_client(client_data: Dict) -> Optional[int]:
    """Create new client"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO users (telegram_id, full_name, phone_number, address, role, language, is_active)
        VALUES ($1, $2, $3, $4, 'client', $5, true)
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            client_data.get('telegram_id', 0),
            client_data['full_name'],
            client_data['phone_number'],
            client_data.get('address', ''),
            client_data.get('language', 'uz')
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating client: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

async def get_orders_by_client(client_id: int, limit: int = 10) -> List[Dict]:
    """Get orders by client"""
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
        results = await conn.fetch(query, client_id, limit)
        return [dict(row) for row in results]
    except Exception as e:
        logging.error(f"Error getting orders by client: {e}")
        return []
    finally:
        await db_manager.pool.release(conn)

async def create_order_from_call(order_data: Dict) -> Optional[int]:
    """Create order from call center"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO zayavki (user_id, zayavka_type, description, address, 
                           phone_number, status, created_by_role, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, 'call_center', $7)
        RETURNING id
        """
        result = await conn.fetchrow(
            query,
            order_data.get('client_id'),
            order_data.get('service_type'),
            order_data['description'],
            order_data.get('address', ''),
            order_data.get('phone_number'),
            order_data.get('status', 'new'),
            order_data['created_by']
        )
        return result['id'] if result else None
    except Exception as e:
        logging.error(f"Error creating order from call: {e}")
        return None
    finally:
        await db_manager.pool.release(conn)

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

async def get_pending_calls() -> List[Dict]:
    """Get pending calls"""
    conn = await db_manager.get_connection()

async def create_feedback(client_id: int, feedback_text: str, rating: int, operator_id: int, pool: asyncpg.Pool = None) -> Optional[int]:
    """Create new feedback for a client"""
    if not pool:
        pool = await db_manager.get_pool()
    
    query = """
        INSERT INTO feedback (client_id, feedback_text, rating, operator_id, created_at)
        VALUES ($1, $2, $3, $4, NOW())
        RETURNING id
    """
    
    try:
        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, client_id, feedback_text, rating, operator_id)
            return result['id'] if result else None
    except Exception as e:
        logger.error(f"Error creating feedback: {str(e)}")
        return None

async def get_client_feedback(client_id: int, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """Get all feedback for a client"""
    if not pool:
        pool = await db_manager.get_pool()
    
    query = """
        SELECT 
            f.*, 
            u.full_name as operator_name,
            u.telegram_id as operator_telegram_id,
            u.language as operator_language
        FROM feedback f
        LEFT JOIN users u ON f.operator_id = u.id
        WHERE f.client_id = $1
        ORDER BY f.created_at DESC
    """
    
    try:
        async with pool.acquire() as conn:
            results = await conn.fetch(query, client_id)
            return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting client feedback: {str(e)}")
        return []

async def get_pending_calls() -> List[Dict]:
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

async def close_chat_session(chat_id: int) -> bool:
    """Close chat session"""
    conn = await db_manager.get_connection()
    try:
        query = """
        UPDATE chat_sessions 
        SET status = 'closed', closed_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """
        await conn.execute(query, chat_id)
        return True
    except Exception as e:
        logging.error(f"Error closing chat session: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def save_chat_message(message_data: Dict) -> bool:
    """Save chat message"""
    conn = await db_manager.get_connection()
    try:
        query = """
        INSERT INTO chat_messages (session_id, sender_id, message_text, message_type)
        VALUES ($1, $2, $3, $4)
        """
        await conn.execute(
            query,
            message_data['session_id'],
            message_data['sender_id'],
            message_data['message_text'],
            message_data.get('message_type', 'text')
        )
        return True
    except Exception as e:
        logging.error(f"Error saving chat message: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)

async def get_operator_performance(operator_id: int, period: str = 'daily') -> Dict:
    """Get operator performance metrics"""
    conn = await db_manager.get_connection()
    try:
        if period == 'daily':
            date_filter = "DATE(created_at) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
        else:  # monthly
            date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
        
        # Get call statistics
        calls_query = f"""
        SELECT 
            COUNT(*) as total_calls,
            AVG(duration) as avg_duration,
            COUNT(CASE WHEN result = 'order_created' THEN 1 END) as successful_calls
        FROM call_logs
        WHERE created_by = $1 AND {date_filter}
        """
        
        # Get orders created
        orders_query = f"""
        SELECT COUNT(*) as orders_created
        FROM zayavki
        WHERE created_by = $1 AND created_by_role = 'call_center' AND {date_filter}
        """
        
        calls_result = await conn.fetchrow(calls_query, operator_id)
        orders_result = await conn.fetchrow(orders_query, operator_id)
        
        total_calls = calls_result['total_calls'] if calls_result else 0
        orders_created = orders_result['orders_created'] if orders_result else 0
        successful_calls = calls_result['successful_calls'] if calls_result else 0
        avg_duration = float(calls_result['avg_duration']) if calls_result and calls_result['avg_duration'] else 0
        
        conversion_rate = (orders_created / total_calls * 100) if total_calls > 0 else 0
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        return {
            'total_calls': total_calls,
            'orders_created': orders_created,
            'successful_calls': successful_calls,
            'conversion_rate': round(conversion_rate, 1),
            'success_rate': round(success_rate, 1),
            'avg_duration': round(avg_duration, 1)
        }
    except Exception as e:
        logging.error(f"Error getting operator performance: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def get_call_center_dashboard_stats() -> Dict:
    """Get dashboard statistics for call center"""
    conn = await db_manager.get_connection()
    try:
        # Today's statistics
        today_calls_query = """
        SELECT COUNT(*) as calls_today
        FROM call_logs
        WHERE DATE(created_at) = CURRENT_DATE
        """
        
        today_orders_query = """
        SELECT COUNT(*) as orders_today
        FROM zayavki
        WHERE DATE(created_at) = CURRENT_DATE AND created_by_role = 'call_center'
        """
        
        pending_callbacks_query = """
        SELECT COUNT(*) as pending_callbacks
        FROM call_logs
        WHERE result = 'callback_requested' AND status = 'pending'
        """
        
        active_chats_query = """
        SELECT COUNT(*) as active_chats
        FROM chat_sessions
        WHERE status = 'active'
        """
        
        calls_today = await conn.fetchval(today_calls_query) or 0
        orders_today = await conn.fetchval(today_orders_query) or 0
        pending_callbacks = await conn.fetchval(pending_callbacks_query) or 0
        active_chats = await conn.fetchval(active_chats_query) or 0
        
        conversion_rate = (orders_today / calls_today * 100) if calls_today > 0 else 0
        
        return {
            'calls_today': calls_today,
            'orders_today': orders_today,
            'pending_callbacks': pending_callbacks,
            'active_chats': active_chats,
            'conversion_rate': round(conversion_rate, 1)
        }
    except Exception as e:
        logging.error(f"Error getting dashboard stats: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def get_client_history(client_id: int) -> Dict:
    """Get comprehensive client history"""
    conn = await db_manager.get_connection()
    try:
        # Get client info
        client_query = "SELECT * FROM users WHERE id = $1"
        client = await conn.fetchrow(client_query, client_id)
        
        if not client:
            return {}
        
        # Get orders
        orders_query = """
        SELECT z.*, t.full_name as technician_name
        FROM zayavki z
        LEFT JOIN users t ON z.assigned_to = t.id
        WHERE z.user_id = $1
        ORDER BY z.created_at DESC
        LIMIT 10
        """
        orders = await conn.fetch(orders_query, client_id)
        
        # Get call logs
        calls_query = """
        SELECT * FROM call_logs
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 10
        """
        calls = await conn.fetch(calls_query, client_id)
        
        # Get feedback
        feedback_query = """
        SELECT f.*, z.description as order_description
        FROM feedback f
        LEFT JOIN zayavki z ON f.zayavka_id = z.id
        WHERE f.user_id = $1
        ORDER BY f.created_at DESC
        LIMIT 5
        """
        feedback = await conn.fetch(feedback_query, client_id)
        
        return {
            'client': dict(client),
            'orders': [dict(row) for row in orders],
            'calls': [dict(row) for row in calls],
            'feedback': [dict(row) for row in feedback]
        }
    except Exception as e:
        logging.error(f"Error getting client history: {e}")
        return {}
    finally:
        await db_manager.pool.release(conn)

async def update_client_info(client_id: int, update_data: Dict) -> bool:
    """Update client information"""
    conn = await db_manager.get_connection()
    try:
        fields = []
        values = []
        param_count = 1
        
        for field, value in update_data.items():
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
        values.append(client_id)
        
        await conn.execute(query, *values)
        return True
    except Exception as e:
        logging.error(f"Error updating client info: {e}")
        return False
    finally:
        await db_manager.pool.release(conn)
