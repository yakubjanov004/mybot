from aiogram.types import Message
from loader import bot
from database.manager_queries import get_filtered_orders
from database.base_queries import get_user_by_telegram_id
import asyncpg

# Eski kodlar va callback handlerlar olib tashlandi

def get_manager_inbox_router():
    from utils.role_router import get_role_router
    router = get_role_router("manager")

    @router.message(lambda m: m.text == "📥 Inbox")
    async def show_all_inbox(message: Message):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        pool: asyncpg.Pool = bot.db

        # 1. Xabarlar (messages jadvalidan)
        async with pool.acquire() as conn:
            messages = await conn.fetch(
                """SELECT m.*, u.full_name as sender_name, u.role as sender_role
                   FROM messages m
                   LEFT JOIN users u ON m.sender_id = u.id
                   WHERE m.recipient_role = 'manager'
                   ORDER BY m.created_at DESC
                   LIMIT 20"""
            )

        # 2. Zayavkalar (status cheklanmagan)
        zayavkalar = await get_filtered_orders('', pool)

        if not messages and not zayavkalar:
            await message.answer("📭 Inbox bo'sh.")
            return

        # Xabarlarni chiqarish
        for msg in messages:
            sender = msg['sender_name'] or "Noma'lum"
            sender_role = msg['sender_role'] or ""
            text = msg['message_text']
            created = msg['created_at'].strftime('%d.%m %H:%M') if msg['created_at'] else '-'
            await message.answer(
                f"✉️ <b>{sender} ({sender_role})</b>\n📝 {text}\n⏰ {created}",
                parse_mode='HTML'
            )

        # Zayavkalarni chiqarish
        for z in zayavkalar:
            desc = z['description'][:50] + ('...' if len(z['description']) > 50 else '')
            created = z['created_at'].strftime('%d.%m %H:%M') if z['created_at'] else '-'
            client = z.get('client_name', "Noma'lum")
            status = z.get('status', '-')
            await message.answer(
                f"📝 <b>ID:</b> {z['id']}\n"
                f"<b>Kimdan:</b> {client}\n"
                f"<b>Ta'rif:</b> {desc}\n"
                f"<b>Status:</b> {status}\n"
                f"<b>Sana:</b> {created}",
                parse_mode='HTML'
            )

    return router
