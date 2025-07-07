from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from keyboards.client_buttons import get_main_menu_keyboard
from utils.inline_cleanup import InlineMessageManager, get_inline_manager
from states.user_states import UserStates
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.get_role import get_user_role
from utils.logger import setup_logger
from loader import inline_message_manager

def get_client_main_menu_router():
    logger = setup_logger('bot.client')
    router = Router()

    @router.message(StateFilter(UserStates.main_menu))
    async def main_menu_handler(message: Message, state: FSMContext):
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            main_menu_text = (
                "Quyidagi menyudan kerakli bo'limni tanlang."
                if lang == 'uz' else
                "Выберите нужный раздел из меню ниже."
            )
            sent_message = await message.answer(main_menu_text, reply_markup=get_main_menu_keyboard(lang))
            await state.update_data(last_message_id=sent_message.message_id)  # Message_id saqlash
            await state.set_state(UserStates.main_menu)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in main_menu_handler: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(None))
    async def handle_unknown_message(message: Message, state: FSMContext):
        try:
            # Check if user is client before handling
            user_role = await get_user_role(message.from_user.id)
            if user_role != "client":
                return  # Not a client, don't handle this message

            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            unknown_text = (
                "Noma'lum buyruq. Iltimos, menyudan tanlang."
                if lang == 'uz' else
                "Неизвестная команда. Пожалуйста, выберите из меню."
            )
            sent_message = await message.answer(unknown_text, reply_markup=get_main_menu_keyboard(lang))
            await state.update_data(last_message_id=sent_message.message_id)  # Message_id saqlash
            await state.set_state(UserStates.main_menu)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in handle_unknown_message: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    return router