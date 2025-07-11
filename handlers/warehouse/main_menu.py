from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.warehouse_queries import get_warehouse_user_by_telegram_id
from keyboards.warehouse_buttons import warehouse_main_menu
from states.warehouse_states import WarehouseMainMenuStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_warehouse_main_menu_router():
    router = get_role_router("warehouse")

    @router.message(F.text.in_(["📦 Warehouse", "📦 Склад", "📦 Ombor"]))
    async def warehouse_start(message: Message, state: FSMContext):
        """Warehouse main menu handler"""
        try:
            user = await get_warehouse_user_by_telegram_id(message.from_user.id)
            if not user:
                lang = 'uz'  # Default language
                text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
                await message.answer(text)
                return
            
            await state.set_state(WarehouseMainMenuStates.main_menu)
            lang = user.get('language', 'uz')
            
            welcome_text = "🏢 Ombor paneliga xush kelibsiz!" if lang == 'uz' else "🏢 Добро пожаловать в панель склада!"
            
            await message.answer(
                welcome_text,
                reply_markup=warehouse_main_menu(lang)
            )
            
            logger.info(f"Warehouse user {user['id']} accessed main menu")
            
        except Exception as e:
            logger.error(f"Error in warehouse start: {str(e)}")
            await message.answer("Xatolik yuz berdi" if 'uz' in str(e) else "Произошла ошибка")

    @router.callback_query(F.data == "warehouse_main_menu")
    async def warehouse_main_menu_callback(callback: CallbackQuery, state: FSMContext):
        """Return to warehouse main menu"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            await state.set_state(WarehouseMainMenuStates.main_menu)
            lang = user.get('language', 'uz')
            
            welcome_text = "🏢 Ombor paneliga xush kelibsiz!" if lang == 'uz' else "🏢 Добро пожаловать в панель склада!"
            
            await callback.message.edit_text(
                welcome_text,
                reply_markup=warehouse_main_menu(lang)
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in warehouse main menu callback: {str(e)}")
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    @router.callback_query(F.data == "warehouse_back")
    async def warehouse_back_handler(callback: CallbackQuery, state: FSMContext):
        """Go back to warehouse main menu"""
        await warehouse_main_menu_callback(callback, state)

    return router
