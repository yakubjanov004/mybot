from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.client_buttons import get_language_keyboard, get_main_menu_keyboard
from states.client_states import LanguageStates
from database.base_queries import get_user_by_telegram_id, update_user_language, get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import answer_and_cleanup
from loader import inline_message_manager
from utils.role_router import get_role_router

def get_client_language_router():
    logger = setup_logger('bot.client')
    router = get_role_router("client")

    @router.message(F.text.in_(["🌐 Til o'zgartirish", "🌐 Изменить язык"]))
    async def client_change_language(message: Message, state: FSMContext):
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            sent_message = await show_language_selection(message, lang, role='client')
            await state.update_data(last_message_id=sent_message.message_id)  
            await state.set_state(LanguageStates.language_settings)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in client_change_language: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    async def process_client_language_change(callback: CallbackQuery, state: FSMContext):
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            await process_language_change(callback, state, role='client')
        except Exception as e:
            logger.error(f"Error in process_client_language_change: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data.startswith("client_lang_"))
    async def handle_language_change_callback(call: CallbackQuery, state: FSMContext):
        try:
            # Get current user data
            user = await get_user_by_telegram_id(call.from_user.id)
            if not user:
                await call.answer("Xatolik yuz berdi", show_alert=True)
                return
            
            # Extract language from callback data
            new_lang = call.data.replace("client_lang_", "")
            await update_user_language(call.from_user.id, new_lang)
            
            # Prepare success message
            success_text = "Til muvaffaqiyatli o'zgartirildi" if new_lang == "uz" else "Язык успешно изменен"
            
            # Remove old message's keyboard
            try:
                await call.message.edit_reply_markup(reply_markup=None)
            except Exception as e:
                logger.warning(f"Error removing old keyboard: {str(e)}")
            
            # Send new message with updated language
            new_message = await call.message.answer(
                success_text,
                reply_markup=get_main_menu_keyboard(new_lang)
            )
            
            # Track new message for cleanup
            await inline_message_manager.track(call.from_user.id, new_message.message_id)
            
            # Clear state
            await state.clear()
            
            # Answer callback
            await call.answer()
            
        except Exception as e:
            logger.error(f"Error in handle_language_change_callback: {str(e)}", exc_info=True)
            lang = user.get('language', 'uz') if user else 'uz'
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await call.answer(error_text, show_alert=True)

    async def show_language_selection(message: Message, lang: str, role: str = 'client'):
        text = "Tilni tanlang:" if lang == 'uz' else "Выберите язык:"
        sent_message = await message.answer(
            text,
            reply_markup=get_language_keyboard(role)
        )
        return sent_message

    return router