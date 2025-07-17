from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.role_router import get_role_router
from database.utils_inbox import get_user_tasks
from keyboards.task_buttons import get_task_keyboard

def get_universal_inbox_router():
    router = get_role_router(None) # Universal router for all roles

    @router.message(F.text == "📥 Inbox")
    async def show_inbox(message: Message, state: FSMContext):
        user_id = message.from_user.id
        tasks = await get_user_tasks(user_id)

        if not tasks:
            await message.answer("📭 Inbox bo'sh.")
            return

        await message.answer("Sizning vazifalaringiz:")
        for task in tasks:
            text = f"ID: {task['public_id']}\nStatus: {task['status']}\nTavsif: {task['description']}"
            keyboard = await get_task_keyboard(task['id'])
            await message.answer(text, reply_markup=keyboard)

    return router