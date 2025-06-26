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
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(F.text.in_(["🔙 Orqaga", "🔙 Назад", "🏠 Asosiy menyu", "🏠 Главное меню"]))
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()  # Rol buzilmasligi uchun FSM tozalash
    lang = await get_user_lang(message.from_user.id)
    role = await get_user_role(message.from_user.id)
    locale = get_locale(lang)

    if role == "admin":
        await message.answer(locale.get('admin', {}).get('main_menu', "Admin panel"), reply_markup=get_admin_main_menu(lang))
    elif role == "manager":
        return  # manager uchun faqat manager.py dagi handler ishlasin
    elif role == "technician":
        await message.answer(locale.get('technician', {}).get('main_menu', "Texnik menyu"), reply_markup=get_technician_main_menu_keyboard(lang))
    else:
        await message.answer(locale.get('client', {}).get('main_menu', "Asosiy menyu"), reply_markup=get_main_menu_keyboard(lang))

    await safe_remove_inline(message)