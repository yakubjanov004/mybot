from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from keyboards.client_buttons import get_main_menu_keyboard
from utils.inline_cleanup import InlineMessageManager, get_inline_manager
from states.client_states import MainMenuStates
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.get_role import get_user_role
from utils.logger import setup_logger
from loader import inline_message_manager
from utils.role_router import get_role_router

def get_client_main_menu_router():
    logger = setup_logger('bot.client')
    router = get_role_router("client")

    @router.message(StateFilter(MainMenuStates.main_menu), F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
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
            await state.set_state(MainMenuStates.main_menu)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in main_menu_handler: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(MainMenuStates.main_menu))
    async def fallback_main_menu(message: Message, state: FSMContext):
        known_texts = [
            "🆕 Yangi buyurtma", "🆕 Новый заказ", "📋 Mening buyurtmalarim", "📋 Мои заказы",
            "👤 Profil", "👤 Профиль", "📞 Operator bilan bog'lanish", "📞 Связаться с оператором",
            "❓ Yordam", "❓ Помощь", "🌐 Til o'zgartirish", "🌐 Изменить язык", "🏠 Asosiy menyu", "🏠 Главное меню"
        ]
        if message.text not in known_texts:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            sent_message = await message.answer(
                "Noma'lum buyruq. Iltimos, menyudan tanlang." if lang == 'uz' else "Неизвестная команда. Пожалуйста, выберите из меню.",
                reply_markup=get_main_menu_keyboard(lang)
            )
            await state.set_state(MainMenuStates.main_menu)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    return router