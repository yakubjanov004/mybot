from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from loader import bot
from database.utils_inbox import get_user_tasks
from database.base_queries import get_user_by_telegram_id
from keyboards.junior_manager_buttons import get_junior_manager_inbox_actions
import random

def get_junior_manager_inbox_router():
    router = Router()

    @router.message(F.text == "📥 Inbox")
    async def junior_manager_inbox_handler(message: Message):
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi.")
            return

        pool = bot.db
        items = await get_user_tasks(user['id'])
        if not items:
            await message.answer("📭 Inbox bo‘sh.")
            return

        for item in items:
            text = render_inbox_item(item)
            keyboard = get_junior_manager_inbox_actions(item['id'])
            await message.answer(text, reply_markup=keyboard, parse_mode='HTML')

    def render_inbox_item(item):
        if item['type'] == 'zayavka':
            return f"📝 <b>Zayavka #{item['id']}</b>\n{item['data']}\nStatus: {item['status']}"
        return f"{item['type'].capitalize()} #{item['id']}"

    @router.callback_query(F.data.startswith("action_"))
    async def junior_manager_action_handler(callback: CallbackQuery):
        _, action, item_type, item_id = callback.data.split("_", 3)
        pool = bot.db

        if item_type == 'zayavka':
            if action == 'assign' or action == 'assign_technician':
                tech_users = await pool.fetch("SELECT id FROM users WHERE role = 'technician' AND is_active = true")
                if tech_users:
                    new_user = random.choice(tech_users)
                    new_user_id = new_user['id']
                    new_role = 'technician'
                    await pool.execute(
                        "UPDATE zayavki SET assigned_to = $1, role = $2 WHERE id = $3",
                        new_user_id, new_role, int(item_id)
                    )
                    await callback.answer("Zayavka texnikka o'tkazildi!")
                else:
                    await callback.answer("Faol texnik topilmadi!", show_alert=True)
            elif action == 'complete':
                await pool.execute(
                    "UPDATE zayavki SET status = 'done' WHERE id = $1",
                    int(item_id)
                )
                await callback.answer("Zayavka yopildi!")
            elif action == 'comment':
                await callback.answer("Izoh qo'shish funksiyasi hali yo'q.")
        await callback.message.delete()

    return router
