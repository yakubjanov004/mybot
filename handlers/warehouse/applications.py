from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.warehouse_buttons import get_application_keyboard
from utils.role_router import get_role_router
from database.warehouse_queries import get_pending_warehouse_orders, get_inventory_item_by_id
from database.models import ZayavkaStatus
from utils.workflow_manager import WorkflowManager
from loader import bot

def get_applications_router():
    router = get_role_router("warehouse")
    workflow_manager = WorkflowManager(bot.db)

    @router.message(F.text == "🆕 Yangi arizalar")
    async def list_new_applications(message: Message, state: FSMContext):
        applications = await get_pending_warehouse_orders()
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
        application = await get_inventory_item_by_id(app_id)
        # Detailed application view logic here
        await callback.answer(f"{application['public_id']} raqamli ariza ko'rildi.")

    @router.callback_query(F.data.startswith("confirm_app_"))
    async def confirm_application(callback: CallbackQuery, state: FSMContext):
        app_id = int(callback.data.split("_")[2])
        # Logic to confirm and deduct materials
        next_status = await workflow_manager.get_next_status(app_id, 'confirm_materials', 'warehouse')
        if next_status:
            # Deduct materials from DB
            # ...
            await bot.db.update_zayavka_status(app_id, next_status)
            await callback.answer("Materiallar tasdiqlandi.")
        else:
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    return router
