from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.junior_manager_buttons import get_application_keyboard
from utils.role_router import get_role_router
from database.junior_manager_queries import get_pending_applications, get_application_by_id
from database.models import ZayavkaStatus
from utils.workflow_manager import WorkflowManager
from loader import bot

def get_applications_router():
    router = get_role_router("junior_manager")
    workflow_manager = WorkflowManager(bot.db)

    @router.message(F.text == "🆕 Yangi arizalar")
    async def list_new_applications(message: Message, state: FSMContext):
        applications = await get_pending_applications('pending_junior_manager')
        if not applications:
            await message.answer("Yangi arizalar mavjud emas.")
            return

        for app in applications:
            text = f"ID: {app['public_id']}\nTavsif: {app['description']}"
            keyboard = await get_application_keyboard(app['id'])
            await message.answer(text, reply_markup=keyboard)

    @router.callback_query(F.data.startswith("view_app_"))
    async def view_application(callback: CallbackQuery, state: FSMContext):
        app_id = int(callback.data.split("_")[2])
        application = await get_application_by_id(app_id)
        # Detailed application view logic here
        await callback.answer(f"{application['public_id']} raqamli ariza ko'rildi.")

    @router.callback_query(F.data.startswith("process_app_"))
    async def process_application(callback: CallbackQuery, state: FSMContext):
        app_id = int(callback.data.split("_")[2])
        # Logic to process and forward to controller
        next_status = await workflow_manager.get_next_status(app_id, 'forward_to_controller', 'junior_manager')
        if next_status:
            # Update application status in DB
            await bot.db.update_zayavka_status(app_id, next_status)
            await callback.answer("Ariza nazoratchiga yuborildi.")
        else:
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    return router