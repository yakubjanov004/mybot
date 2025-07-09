from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.technician_buttons import get_language_keyboard, get_technician_main_menu_keyboard
from states.technician_states import TechnicianStates
from database.technician_queries import get_technician_by_telegram_id
from database.base_queries import get_user_by_telegram_id, get_user_lang, update_user_language
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages, answer_and_cleanup
from utils.role_router import get_role_router
import functools

# process_language_change funksiyasini modul darajasiga ko'chirdim
def setup_logger_for_language():
    return setup_logger('bot.technician.language')

async def process_language_change(call: CallbackQuery, role: str, get_main_keyboard_func, state: FSMContext):
    logger = setup_logger_for_language()
    try:
        # Extract language code from callback data
        lang_code = call.data.split('_')[-1]
        # Update user's language in database
        await update_user_language(call.from_user.id, lang_code)
        # Tozalash: callback xabarini va barcha eski inline xabarlarni o'chirish
        try:
            await answer_and_cleanup(call)  # Inline tugma xabarini o'chirish
        except Exception as e:
            logger.warning(f"answer_and_cleanup error: {e}")
        try:
            await cleanup_user_inline_messages(call.from_user.id)  # Barcha eski inline xabarlarni o'chirish
        except Exception as e:
            logger.warning(f"cleanup_user_inline_messages error: {e}")
        # Get new language
        lang = lang_code
        # Send success message
        success_text = "Til o'zgartirildi!" if lang == 'uz' else "Язык изменён!"
        await call.message.answer(
            success_text,
            reply_markup=get_main_keyboard_func(lang)
        )
        # Clear state
        await state.clear()
        return True
    except Exception as e:
        logger.error(f"Error processing language change: {str(e)}", exc_info=True)
        return False

def get_technician_language_router():
    logger = setup_logger_for_language()
    router = get_role_router("technician")

    @router.message(lambda message: message.text in ["🌐 Tilni o'zgartirish", "🌐 Изменить язык"])
    async def show_language_keyboard(message: Message, state: FSMContext):
        """Show language selection keyboard for technicians"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            lang = await get_user_lang(message.from_user.id)
            await message.answer(
                "Tilni tanlang" if lang == 'uz' else "Выберите язык",
                reply_markup=get_language_keyboard()
            )
        except Exception as e:
            logger.error(f"Error in show_language_keyboard: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("tech_lang_"))
    async def tech_language_callback(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback)
        try:
            success = await process_language_change(
                call=callback,
                role="technician",
                get_main_keyboard_func=get_technician_main_menu_keyboard,
                state=state
            )
            if not success:
                lang = await get_user_lang(callback.from_user.id)
                error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
                await callback.message.answer(error_text)
        except Exception as e:
            logger.error(f"Error in change_language: {str(e)}", exc_info=True)
            lang = await get_user_lang(callback.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.answer(error_text)

    return router
