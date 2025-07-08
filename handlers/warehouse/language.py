from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.warehouse_queries import get_warehouse_user_by_telegram_id
from database.base_queries import update_user_language
from keyboards.warehouse_buttons import language_selection_keyboard, warehouse_main_menu
from states.warehouse_states import WarehouseStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_warehouse_language_router():
    router = get_role_router("warehouse")

    @router.message(F.text.in_(["🌐 Tilni o'zgartirish", "🌐 Выберите язык"]))
    async def change_language_handler(message: Message, state: FSMContext):
        """Handle language change request"""
        try:
            user = await get_warehouse_user_by_telegram_id(message.from_user.id)
            if not user:
                return
            
            lang = user.get('language', 'uz')
            
            language_text = "🌐 Tilni tanlang:" if lang == 'uz' else "🌐 Выберите язык:"
            
            await message.answer(
                language_text,
                reply_markup=language_selection_keyboard()
            )
            await state.set_state(WarehouseStates.selecting_language)
            
        except Exception as e:
            logger.error(f"Error in change language handler: {str(e)}")

    @router.callback_query(F.data == "change_language")
    async def change_language_callback(callback: CallbackQuery, state: FSMContext):
        """Handle language change callback"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            language_text = "🌐 Tilni tanlang:" if lang == 'uz' else "🌐 Выберите язык:"
            
            await callback.message.edit_text(
                language_text,
                reply_markup=language_selection_keyboard()
            )
            await state.set_state(WarehouseStates.selecting_language)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in change language callback: {str(e)}")
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    @router.callback_query(F.data.startswith("set_lang_"))
    async def set_language_handler(callback: CallbackQuery, state: FSMContext):
        """Set user language"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            # Extract language from callback data
            new_lang = callback.data.split("_")[-1]  # set_lang_uz -> uz
            
            if new_lang not in ['uz', 'ru']:
                await callback.answer("Noto'g'ri til", show_alert=True)
                return
            
            # Update language in database
            success = await update_user_language(user['id'], new_lang)
            
            if success:
                # Success messages
                if new_lang == 'uz':
                    success_text = "✅ Til o'zbekchaga o'zgartirildi!"
                    welcome_text = "🏢 Ombor paneliga xush kelibsiz!"
                else:
                    success_text = "✅ Язык изменен на русский!"
                    welcome_text = "🏢 Добро пожаловать в панель склада!"
                
                await callback.message.edit_text(
                    f"{success_text}\n\n{welcome_text}",
                    reply_markup=warehouse_main_menu(new_lang)
                )
                
                await state.set_state(WarehouseStates.main_menu)
                logger.info(f"Warehouse user {user['id']} changed language to {new_lang}")
            else:
                error_text = "Tilni o'zgartirishda xatolik" if new_lang == 'uz' else "Ошибка при изменении языка"
                await callback.message.edit_text(error_text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error setting language: {str(e)}")
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    @router.callback_query(F.data == "warehouse_language_back")
    async def language_back_handler(callback: CallbackQuery, state: FSMContext):
        """Go back to warehouse main menu from language selection"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            lang = user.get('language', 'uz')
            welcome_text = "🏢 Ombor paneliga xush kelibsiz!" if lang == 'uz' else "🏢 Добро пожаловать в панель склада!"
            
            await callback.message.edit_text(
                welcome_text,
                reply_markup=warehouse_main_menu(lang)
            )
            await state.set_state(WarehouseStates.main_menu)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in language back handler: {str(e)}")
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    return router
