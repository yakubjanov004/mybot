from utils.cache_manager import user_cache
from database.queries import get_user_by_telegram_id

async def get_user_role(user_id: int) -> str:
    user = user_cache.get_user(user_id)
    if user and 'role' in user:
        return user['role']

    db_user = await get_user_by_telegram_id(user_id)
    if db_user:
        return db_user.get('role', 'client')

    return 'client'