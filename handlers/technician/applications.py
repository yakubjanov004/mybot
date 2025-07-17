from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.technician_buttons import get_task_action_keyboard
from utils.role_router import get_role_router
from database.technician_queries import get_technician_tasks, get_zayavki_by_assigned
from database.models import ZayavkaStatus
from utils.workflow_manager import WorkflowManager
from loader import bot

def get_applications_router():
    router = get_role_router("technician")
    workflow_manager = WorkflowManager(bot.db)

    @router.message(F.text == "🆕 Yangi arizalar")
    async def list_new_applications(message: Message, state: FSMContext):
        applications = await get_technician_tasks(message.from_user.id)
        if not applications:
            await message.answer("Sizga tayinlangan yangi arizalar mavjud emas.")
            return

        for app in applications:
            text = f"ID: {app['public_id']}\nTavsif: {app['description']}"
            keyboard = await get_task_action_keyboard(app['id'], app['status'])
            await message.answer(text, reply_markup=keyboard)

    @router.callback_query(F.data.startswith("view_app_"))
    async def view_application(callback: CallbackQuery, state: FSMContext):
        app_id = int(callback.data.split("_")[2])
        application = await get_zayavki_by_assigned(app_id)
        # Detailed application view logic here
        await callback.answer(f"{application['public_id']} raqamli ariza ko'rildi.")

    @router.callback_query(F.data.startswith("start_app_"))
    async def start_application(callback: CallbackQuery, state: FSMContext):
        app_id = int(callback.data.split("_")[2])
        next_status = await workflow_manager.get_next_status(app_id, 'start_work', 'technician')
        if next_status:
            await bot.db.update_zayavka_status(app_id, next_status)
            await callback.answer("Ish boshlandi.")
        else:
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    @router.callback_query(F.data.startswith("complete_app_"))
    async def complete_application(callback: CallbackQuery, state: FSMContext):
        app_id = int(callback.data.split("_")[2])
        # Here we need to ask if warehouse is involved
        # For now, we assume it's not
        next_status = await workflow_manager.get_next_status(app_id, 'complete_work', 'technician')
        if next_status:
            await bot.db.update_zayavka_status(app_id, next_status)
            await callback.answer("Ish yakunlandi.")
        else:
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    return router