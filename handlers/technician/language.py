from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.technician_buttons import get_language_keyboard, get_main_menu_keyboard, get_technician_main_menu_keyboard
from states.technician_states import TechnicianStates
from database.technician_queries import get_technician_by_telegram_id
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages, answer_and_cleanup
import functools

def get_technician_language_router():
    logger = setup_logger('bot.technician.language')
    router = Router()

    def require_technician(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                message_or_call = args[0] if args else kwargs.get('message_or_call')
                user_id = message_or_call.from_user.id
                user = await get_technician_by_telegram_id(user_id)
                if not user:
                    lang = await get_user_lang(user_id)
                    text = "Sizda montajchi huquqi yo'q." if lang == 'uz' else "У вас нет прав монтажника."
                    if hasattr(message_or_call, 'answer'):
                        await message_or_call.answer(text)
                    else:
                        await message_or_call.message.answer(text)
                    return
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in require_technician decorator: {str(e)}", exc_info=True)
                if args and hasattr(args[0], 'answer'):
                    lang = await get_user_lang(args[0].from_user.id)
                    await args[0].answer("Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!")
        return wrapper

    @router.message(lambda message: message.text in ["🌐 Tilni o'zgartirish", "🌐 Изменить язык"])
    @require_technician
    async def show_language_keyboard(message: Message, state: FSMContext):
        """Show language selection keyboard for technicians"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            success = await show_language_selection(message, "technician", state)
            if not success:
                lang = await get_user_lang(message.from_user.id)
                error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
                await message.answer(error_text)
        except Exception as e:
            logger.error(f"Error in show_language_keyboard: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("tech_lang_"))
    async def tech_language_callback(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback)
        try:
            await process_language_change(
                call=callback,
                role="technician",
                get_main_keyboard_func=get_technician_main_menu_keyboard,
                state=state
            )
            await state.set_state(TechnicianStates.main_menu)
        except Exception as e:
            logger.error(f"Error in change_language: {str(e)}", exc_info=True)
            lang = await get_user_lang(callback.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.answer(error_text)

    return router
