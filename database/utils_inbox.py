from loader import bot

async def get_user_tasks(user_id):
    """
    Get all tasks assigned to a user based on their role and ID.
    """
    user = await bot.db.get_user_by_telegram_id(user_id)
    if not user:
        return []

    role = user.get('role')
    
    query = """
        SELECT z.id, z.public_id, z.status, z.description
        FROM zayavki z
        WHERE z.current_user_id = $1 AND z.status NOT IN ('closed', 'cancelled')
        ORDER BY z.created_at DESC
    """
    
    async with bot.db.acquire() as connection:
        tasks = await connection.fetch(query, user['id'])
    
    return tasks