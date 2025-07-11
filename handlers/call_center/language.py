from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.base_queries import get_user_by_telegram_id
from keyboards.call_center_buttons import call_center_main_menu_reply
from states.call_center import CallCenterSettingsStates, CallCenterMainMenuStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_call_center_language_router():
    router = get_role_router("call_center")

    @router.message(F.text.in_(["🌐 Tilni o'zgartirish", " Изменить язык"]))
    async def call_center_change_language(message: Message, state: FSMContext):
        """Change language for call center"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        try:
            success = await show_language_selection(message, "call_center", state)
            if not success:
                lang = user.get('language', 'uz')
                error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
                await message.answer(error_text)
                
        except Exception as e:
            logger.error(f"Error showing language selection: {str(e)}")
            lang = user.get('language', 'uz')
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("call_center_lang_"))
    async def process_call_center_language_change(callback: CallbackQuery, state: FSMContext):
        """Process call center language change"""
        try:
            await process_language_change(
                call=callback,
                role="call_center",
                get_main_keyboard_func=call_center_main_menu_reply,
                state=state
            )
            await state.set_state(CallCenterMainMenuStates.main_menu)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Call center tilni o'zgartirishda xatolik: {str(e)}")
            lang = await get_user_lang(callback.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.answer(error_text)
            await callback.answer()

    return router
