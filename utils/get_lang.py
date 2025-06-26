from utils.cache_manager import user_cache
from database.queries import get_user_by_telegram_id

async def get_user_lang(user_id: int) -> str:
    user = user_cache.get_user(user_id)
    if user and 'language' in user:
        return user['language']

    db_user = await get_user_by_telegram_id(user_id)
    if db_user and db_user.get('language') in ['uz', 'ru']:
        return db_user['language']

    return 'uz'