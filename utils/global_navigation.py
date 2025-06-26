from aiogram import Router, F
from aiogram.types import Message
from utils.get_lang import get_user_lang
from utils.get_role import get_user_role
from keyboards.admin_buttons import get_admin_main_menu
from keyboards.manager_buttons import get_manager_main_keyboard
from keyboards.client_buttons import get_main_menu_keyboard
from keyboards.technician_buttons import get_technician_main_menu_keyboard
from utils.inline_cleanup import safe_remove_inline
from utils.i18n import get_locale

router = Router()

@router.message(F.text.in_(["🔙 Orqaga", "🔙 Назад", "🏠 Asosiy menyu", "🏠 Главное меню"]))
async def back_to_main(message: Message):
    lang = await get_user_lang(message.from_user.id)
    role = await get_user_role(message.from_user.id)
    locale = get_locale(lang)

    if role == "admin":
        await message.answer(locale['admin']['main_menu'], reply_markup=get_admin_main_menu(lang))
    elif role == "manager":
        await message.answer(locale['manager']['welcome_message'], reply_markup=get_manager_main_keyboard(locale, lang))
    elif role == "technician":
        await message.answer(locale['technician']['main_menu'], reply_markup=get_technician_main_menu_keyboard(lang))
    else:
        await message.answer(locale['client']['main_menu'], reply_markup=get_main_menu_keyboard(lang))

    await safe_remove_inline(message)