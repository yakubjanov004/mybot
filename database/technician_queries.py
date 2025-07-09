import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger('database.technician_queries')

async def get_technician_tasks(technician_id: int) -> List[Dict[str, Any]]:
    """Get all tasks assigned to a technician"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    z.*, 
                    u.full_name as client_name,
                    u.phone_number as client_phone
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                WHERE z.assigned_to = $1 AND z.status != 'completed'
                ORDER BY z.created_at DESC
            """
            rows = await conn.fetch(query, technician_id)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting technician tasks: {str(e)}", exc_info=True)
        return []

async def get_technician_chat_history(technician_id: int, client_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get chat history between technician and client"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    m.*, 
                    u1.full_name as sender_name,
                    u2.full_name as recipient_name
                FROM messages m
                LEFT JOIN users u1 ON m.sender_id = u1.id
                LEFT JOIN users u2 ON m.recipient_id = u2.id
                WHERE (m.sender_id = $1 AND m.recipient_id = $2)
                   OR (m.sender_id = $2 AND m.recipient_id = $1)
                ORDER BY m.created_at DESC
                LIMIT $3
            """
            rows = await conn.fetch(query, technician_id, client_id, limit)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting technician chat history: {str(e)}", exc_info=True)
        return []

async def save_technician_message(technician_id: int, client_id: int, message_text: str, is_technician: bool = True) -> bool:
    """Save a message in the chat history"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            sender_id = technician_id if is_technician else client_id
            recipient_id = client_id if is_technician else technician_id
            
            query = """
                INSERT INTO messages (sender_id, recipient_id, message_text, created_at)
                VALUES ($1, $2, $3, NOW())
                RETURNING id
            """
            result = await conn.fetchval(query, sender_id, recipient_id, message_text)
            return result is not None
    except Exception as e:
        logger.error(f"Error saving technician message: {str(e)}", exc_info=True)
        return False

async def accept_task(zayavka_id: int, technician_id: int) -> bool:
    """Accept a task assigned to technician"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            await conn.execute(
                """
                    UPDATE zayavki
                    SET status = 'accepted',
                        assigned_to = $1,
                        accepted_at = NOW()
                    WHERE id = $2
                """,
                technician_id, zayavka_id
            )
            return True
    except Exception as e:
        logger.error(f"Error accepting task: {str(e)}", exc_info=True)
        return False

async def start_task(zayavka_id: int, technician_id: int) -> bool:
    """Start working on a task"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE zayavki SET status = 'in_progress' WHERE id = $1 AND assigned_to = $2",
                zayavka_id, technician_id
            )
            
            # Log status change
            await conn.execute(
                """INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status) 
                   VALUES ($1, $2, 'accepted', 'in_progress')""",
                zayavka_id, technician_id
            )
            return True
    except Exception as e:
        logger.error(f"Error starting task: {str(e)}", exc_info=True)
        return False

async def complete_task(zayavka_id: int, technician_id: int, solution_text: str = None) -> Dict[str, Any]:
    """Complete a task with optional solution text"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            # Update task status
            await conn.execute(
                "UPDATE zayavki SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = $1 AND assigned_to = $2",
                zayavka_id, technician_id
            )
            
            # Add solution if provided
            if solution_text:
                await conn.execute(
                    """INSERT INTO solutions (zayavka_id, instander_id, solution_text) 
                       VALUES ($1, $2, $3)""",
                    zayavka_id, technician_id, solution_text
                )
            
            # Log status change
            await conn.execute(
                """INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status) 
                   VALUES ($1, $2, 'in_progress', 'completed')""",
                zayavka_id, technician_id
            )
            
            # Get task details for notification
            task = await conn.fetchrow(
                """SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
                   FROM zayavki z
                   LEFT JOIN users u ON z.user_id = u.id
                   WHERE z.id = $1""",
                zayavka_id
            )
            
            return dict(task) if task else {}
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}", exc_info=True)
        return {}

async def request_task_transfer(zayavka_id: int, technician_id: int, reason: str) -> bool:
    """Request task transfer to another technician"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            # Create transfer request record
            await conn.execute(
                """INSERT INTO task_transfer_requests (zayavka_id, from_technician_id, reason, status) 
                   VALUES ($1, $2, $3, 'pending')""",
                zayavka_id, technician_id, reason
            )
            return True
    except Exception as e:
        logger.error(f"Error requesting task transfer: {str(e)}", exc_info=True)
        return False

async def get_technician_completed_tasks(technician_id: int, limit: int = None) -> List[Dict[str, Any]]:
    """Get completed tasks for a technician"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            query = """
                SELECT z.*, u.full_name as client_name, u.phone_number as client_phone,
                       s.solution_text as solution
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN solutions s ON z.id = s.zayavka_id
                WHERE z.assigned_to = $1 AND z.status = 'completed'
                ORDER BY z.completed_at DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await conn.fetch(query, technician_id)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting completed tasks: {str(e)}", exc_info=True)
        return []

async def get_technician_stats(technician_id: int) -> Dict[str, int]:
    """Get technician statistics"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            # Get total completed tasks
            total_completed = await conn.fetchval(
                "SELECT COUNT(*) FROM zayavki WHERE assigned_to = $1 AND status = 'completed'",
                technician_id
            )
            
            # Get today's completed tasks
            today = datetime.now().date()
            today_completed = await conn.fetchval(
                """SELECT COUNT(*) FROM zayavki 
                   WHERE assigned_to = $1 AND status = 'completed' 
                   AND DATE(completed_at) = $2""",
                technician_id, today
            )
            
            # Get this week's completed tasks
            week_start = today - timedelta(days=today.weekday())
            week_completed = await conn.fetchval(
                """SELECT COUNT(*) FROM zayavki 
                   WHERE assigned_to = $1 AND status = 'completed' 
                   AND DATE(completed_at) >= $2""",
                technician_id, week_start
            )
            
            # Get this month's completed tasks
            month_start = today.replace(day=1)
            month_completed = await conn.fetchval(
                """SELECT COUNT(*) FROM zayavki 
                   WHERE assigned_to = $1 AND status = 'completed' 
                   AND DATE(completed_at) >= $2""",
                technician_id, month_start
            )
            
            return {
                'total': total_completed or 0,
                'today': today_completed or 0,
                'week': week_completed or 0,
                'month': month_completed or 0
            }
    except Exception as e:
        logger.error(f"Error getting technician stats: {str(e)}", exc_info=True)
        return {'total': 0, 'today': 0, 'week': 0, 'month': 0}

async def get_available_technicians() -> List[Dict[str, Any]]:
    """Get list of available technicians for task reassignment"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            query = """
                SELECT id, telegram_id, full_name, phone_number, language
                FROM users 
                WHERE role = 'technician' AND telegram_id IS NOT NULL
                ORDER BY full_name
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting available technicians: {str(e)}", exc_info=True)
        return []

async def get_managers_telegram_ids() -> List[Dict[str, Any]]:
    """Get telegram IDs of all managers"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            query = """
                SELECT telegram_id, language, full_name, id
                FROM users 
                WHERE role = 'manager' AND telegram_id IS NOT NULL
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting managers: {str(e)}", exc_info=True)
        return []


async def assign_technician_to_zayavka(zayavka_id: int, technician_id: int) -> bool:
    """
    Assign a technician to a zayavka (request).
    """
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE zayavki
                SET assigned_to = $1
                WHERE id = $2
                """,
                technician_id, zayavka_id
            )
            return True
    except Exception as e:
        logger.error(f"Error assigning technician to zayavka: {str(e)}", exc_info=True)
        return False

async def get_warehouse_staff() -> List[Dict[str, Any]]:
    """Get warehouse staff for equipment requests"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            query = """
                SELECT telegram_id, language, full_name, id, role
                FROM users 
                WHERE role IN ('warehouse') AND telegram_id IS NOT NULL
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting warehouse staff: {str(e)}", exc_info=True)
        return []

async def update_technician_phone(telegram_id: int, phone_number: str) -> bool:
    """Update technician phone number"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET phone_number = $1 WHERE telegram_id = $2",
                phone_number, str(telegram_id)
            )
            return True
    except Exception as e:
        logger.error(f"Error updating technician phone: {str(e)}", exc_info=True)
        return False

async def update_technician_language(telegram_id: int, language: str) -> bool:
    """Update technician language preference"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET language = $1 WHERE telegram_id = $2",
                language, str(telegram_id)
            )
            return True
    except Exception as e:
        logger.error(f"Error updating technician language: {str(e)}", exc_info=True)
        return False

async def get_technician_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get technician by telegram ID"""
    try:
        from loader import bot
        pool = bot.db
        telegram_id = int(telegram_id)  # always ensure integer
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1 AND role = 'technician'",
                telegram_id
            )
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting technician by telegram ID: {str(e)}", exc_info=True)
        return None

async def log_technician_activity(technician_id: int, activity_type: str, description: str) -> bool:
    """Log technician activity"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO technician_activity_logs (technician_id, activity_type, description) 
                   VALUES ($1, $2, $3)""",
                technician_id, activity_type, description
            )
            return True
    except Exception as e:
        logger.error(f"Error logging technician activity: {str(e)}", exc_info=True)
        return False

async def get_zayavki_by_assigned(technician_id: int) -> List[Dict[str, Any]]:
    """Get all zayavki assigned to technician (including completed)"""
    try:
        from loader import bot
        pool = bot.db
        async with pool.acquire() as conn:
            query = """
                SELECT z.*, u.full_name as user_name, u.phone_number as client_phone,
                       s.solution_text as solution
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN solutions s ON z.id = s.zayavka_id
                WHERE z.assigned_to = $1
                ORDER BY z.created_at DESC
            """
            rows = await conn.fetch(query, technician_id)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting zayavki by assigned: {str(e)}", exc_info=True)
        return []
