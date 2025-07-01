from aiogram import Router, F
from aiogram.types import Message
from utils.get_lang import get_user_lang
from utils.get_role import get_user_role
from keyboards.admin_buttons import get_admin_main_menu
from keyboards.manager_buttons import get_manager_main_keyboard
from keyboards.client_buttons import get_main_menu_keyboard
from keyboards.technician_buttons import get_technician_main_menu_keyboard
from keyboards.call_center_buttons import call_center_main_menu
from keyboards.controllers_buttons import controllers_main_menu
from keyboards.warehouse_buttons import warehouse_main_menu
from utils.inline_cleanup import safe_remove_inline

router = Router()

@router.message(F.text.in_(["🔙 Orqaga", "🔙 Назад", "🏠 Asosiy menyu", "🏠 Главное меню"]))
async def back_to_main(message: Message):
    lang = await get_user_lang(message.from_user.id)
    role = await get_user_role(message.from_user.id)

    if role == "admin":
        main_menu_text = "Admin paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель администратора!"
        await message.answer(main_menu_text, reply_markup=get_admin_main_menu(lang))
    elif role == "manager":
        welcome_text = "Menejer paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель менеджера!"
        await message.answer(welcome_text, reply_markup=get_manager_main_keyboard(lang))
    elif role == "technician":
        main_menu_text = "Montajchi paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель монтажника!"
        await message.answer(main_menu_text, reply_markup=get_technician_main_menu_keyboard(lang))
    elif role == "call_center":
        main_menu_text = "Call center paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель call center!"
        await message.answer(main_menu_text, reply_markup=call_center_main_menu(lang))
    elif role == "controller":
        main_menu_text = "Controller paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель контроллера!"
        await message.answer(main_menu_text, reply_markup=controllers_main_menu(lang))
    elif role == "warehouse":
        main_menu_text = "Warehouse paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель склада!"
        await message.answer(main_menu_text, reply_markup=warehouse_main_menu(lang))
    else:
        main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
        await message.answer(main_menu_text, reply_markup=get_main_menu_keyboard(lang))

    await safe_remove_inline(message)