from aiogram import Router, F
from aiogram.types import Message
from keyboards.junior_manager_buttons import get_junior_manager_main_keyboard
from database.base_queries import get_user_lang
from states.junior_manager_states import JuniorManagerMainMenuStates

router = Router()

@router.message(F.text.in_(["/start", "🏠 Asosiy menyu", "🏠 Главное меню"]))
async def show_main_menu(message: Message):
    lang = await get_user_lang(message.from_user.id)
    keyboard = get_junior_manager_main_keyboard(lang)
    text = "🏠 Asosiy menyu" if lang == "uz" else "🏠 Главное меню"
    await message.answer(text, reply_markup=keyboard) 