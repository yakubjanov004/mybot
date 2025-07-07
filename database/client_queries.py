"""
client_queries.py - Client-specific database queries
"""
from typing import Any, Dict, List, Optional, Union
import logging
from database.models import *
from database.base_queries import get_user_by_id
from loader import bot


async def get_user_zayavki(user_id: int, limit: int = 50) -> List[Dict]:
    """Get user's zayavki"""
    async with bot.db.acquire() as conn:
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

async def get_zayavka_solutions(zayavka_id: int) -> List[Dict]:
    """Get solutions for zayavka"""
    async with bot.db.acquire() as conn:
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

async def get_user_zayavka_statistics(telegram_id: int) -> dict:
    """Get user's zayavka statistics with weekly and monthly counts"""
    try:
        async with bot.db.acquire() as conn:
            query = """
                WITH weekly_stats AS (
                    SELECT z.status, COUNT(*) as weekly_count
                    FROM zayavki z
                    JOIN users u ON z.user_id = u.id
                    WHERE u.telegram_id = $1 
                    AND z.created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY z.status
                ),
                monthly_stats AS (
                    SELECT z.status, COUNT(*) as monthly_count
                    FROM zayavki z
                    JOIN users u ON z.user_id = u.id
                    WHERE u.telegram_id = $1 
                    AND z.created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY z.status
                )
                SELECT 
                    COALESCE(w.status, m.status) as status,
                    COALESCE(w.weekly_count, 0) as weekly_count,
                    COALESCE(m.monthly_count, 0) as monthly_count
                FROM weekly_stats w
                FULL OUTER JOIN monthly_stats m ON w.status = m.status
            """
            
            result = await conn.fetch(query, telegram_id)
            stats = {row['status']: {
                'weekly': row['weekly_count'],
                'monthly': row['monthly_count']
            } for row in result}
            
            # Add default values for statuses that don't exist in the database
            default_statuses = ['new', 'in_progress', 'completed', 'cancelled']
            for status in default_statuses:
                if status not in stats:
                    stats[status] = {'weekly': 0, 'monthly': 0}
            
            return stats
    except Exception as e:
        logging.error(f"Error getting user zayavka statistics: {e}")
        return {'new': 0, 'in_progress': 0, 'completed': 0, 'cancelled': 0}

async def get_client_info(user_id: int) -> Optional[Dict]:
    """Get client information"""
    return await get_user_by_id(user_id)