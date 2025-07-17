from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.manager_buttons import get_application_keyboard
from utils.role_router import get_role_router
from database.manager_queries import get_filtered_applications, get_order_details
from database.models import ZayavkaStatus
from utils.workflow_manager import WorkflowManager
from loader import bot

def get_applications_router():
    router = get_role_router("manager")
    workflow_manager = WorkflowManager(bot.db)

    @router.message(F.text == "🆕 Yangi arizalar")
    async def list_new_applications(message: Message, state: FSMContext):
        result = await get_filtered_applications(bot.db, statuses=['pending_controller'])
        applications = result.get('applications', [])
        if not applications:
            await message.answer("Yangi arizalar mavjud emas.")
            return

        for app in applications:
            text = f"ID: {app['public_id']}\nTavsif: {app['description']}"
            keyboard = get_application_keyboard(app['id'])
            await message.answer(text, reply_markup=keyboard)

    @router.callback_query(F.data.startswith("view_app_"))
    async def view_application(callback: CallbackQuery, state: FSMContext):
        app_id = int(callback.data.split("_")[2])
        application = await get_order_details(app_id, bot.db)
        # Detailed application view logic here
        await callback.answer(f"{application['public_id']} raqamli ariza ko'rildi.")

    @router.callback_query(F.data.startswith("assign_app_"))
    async def assign_application(callback: CallbackQuery, state: FSMContext):
        app_id = int(callback.data.split("_")[2])
        # Logic to assign to junior manager
        next_status = await workflow_manager.get_next_status(app_id, 'assign_to_junior', 'manager')
        if next_status:
            # Update application status in DB
            await bot.db.update_zayavka_status(app_id, next_status)
            await callback.answer("Ariza kichik menejerga yuborildi.")
        else:
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    return router
