import asyncpg
from typing import List, Dict, Any, Optional

# Controller role uchun query funksiyalari

async def get_quality_control_stats(pool: asyncpg.Pool) -> Dict[str, Any]:
    """Controller uchun sifat nazorati statistikasi"""
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as total_feedback
            FROM feedback
        """)
        return dict(result) if result else {}

async def get_unresolved_issues(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Controller uchun hal qilinmagan muammolar ro'yxati"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM zayavki WHERE status != 'completed' ORDER BY created_at DESC
        """)
        return [dict(row) for row in rows]

async def mark_issue_resolved(issue_id: int, pool: asyncpg.Pool) -> bool:
    """Controller muammoni hal qilindi deb belgilaydi"""
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE zayavki SET status = 'completed' WHERE id = $1
        """, issue_id)
        return True

async def get_controller_reports(period: str, pool: asyncpg.Pool) -> Dict[str, Any]:
    """Controller uchun hisobotlar (kunlik, haftalik, sifat)"""
    async with pool.acquire() as conn:
        if period == 'daily':
            query = "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed FROM zayavki WHERE DATE(created_at) = CURRENT_DATE"
        elif period == 'weekly':
            query = "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed FROM zayavki WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'quality':
            query = "SELECT AVG(rating) as avg_rating, COUNT(*) as total_feedback FROM feedback"
        else:
            return {}
        result = await conn.fetchrow(query)
        return dict(result) if result else {}

async def get_technician_performance(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Controller uchun texniklar samaradorligi"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.id, u.full_name, AVG(f.rating) as avg_rating, COUNT(z.id) as completed_orders
            FROM users u
            LEFT JOIN zayavki z ON u.id = z.assigned_to AND z.status = 'completed'
            LEFT JOIN feedback f ON z.id = f.zayavka_id
            WHERE u.role = 'technician'
            GROUP BY u.id, u.full_name
            ORDER BY completed_orders DESC
        """)
        return [dict(row) for row in rows]

async def get_recent_feedback(days: int = 7, pool: asyncpg.Pool = None) -> List[Dict[str, Any]]:
    """So'nggi N kun ichidagi mijoz fikrlarini (feedback) qaytaradi"""
    if not pool:
        from loader import bot
        pool = bot.db
    async with pool.acquire() as conn:
        query = f"""
            SELECT f.id, f.zayavka_id, f.user_id, u.full_name as user_name, f.rating, f.comment, f.created_at
            FROM feedback f
            LEFT JOIN users u ON f.user_id = u.id
            WHERE f.created_at >= NOW() - INTERVAL '{days} days'
            ORDER BY f.created_at DESC
        """
        rows = await conn.fetch(query)
        return [dict(row) for row in rows] 

async def get_quality_trends(pool: asyncpg.Pool = None, period: str = 'monthly') -> List[Dict[str, Any]]:
    """Get quality trends over time"""
    if not pool:
        from loader import bot
        pool = bot.db 

    query = """
        SELECT 
            date_trunc($1, f.created_at) as period,
            AVG(rating) as avg_rating,
            COUNT(*) as total_feedbacks,
            COUNT(CASE WHEN rating >= 4 THEN 1 END) as positive_feedbacks,
            COUNT(CASE WHEN rating < 3 THEN 1 END) as negative_feedbacks
        FROM feedback f
        GROUP BY date_trunc($1, f.created_at)
        ORDER BY period DESC
    """

    try:
        async with pool.acquire() as conn:
            results = await conn.fetch(query, period)
            return [dict(row) for row in results]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting quality trends: {str(e)}", exc_info=True)
        return []

async def get_application_by_id(app_id: int, pool: asyncpg.Pool) -> Optional[Dict[str, Any]]:
    """Get an application by its ID"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM zayavki WHERE id = $1", app_id)
        return dict(row) if row else None