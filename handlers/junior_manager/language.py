from aiogram import Router, F
from aiogram.types import Message
from database.base_queries import set_user_language, get_user_lang
from states.junior_manager_states import JuniorManagerLanguageStates

router = Router()

@router.message(F.text.in_(["🌐 Tilni o'zgartirish", "🌐 Изменить язык"]))
async def change_language(message: Message):
    lang = await get_user_lang(message.from_user.id)
    if lang == "uz":
        await set_user_language(message.from_user.id, "ru")
        await message.answer("Til rus tiliga o'zgartirildi.\nЯзык изменён на русский.")
    else:
        await set_user_language(message.from_user.id, "uz")
        await message.answer("Язык изменён на узбекский.\nTil o'zbek tiliga o'zgartirildi.") 