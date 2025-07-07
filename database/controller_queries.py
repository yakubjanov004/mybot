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