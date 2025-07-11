from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.base_queries import get_user_by_telegram_id
from states.client_states import MainMenuStates
from states.technician_states import TechnicianMainMenuStates
from states.admin_states import AdminMainMenuStates
from states.call_center import CallCenterMainMenuStates
from states.controllers_states import ControllerMainMenuStates
from states.warehouse_states import WarehouseMainMenuStates
from states.junior_manager_states import JuniorManagerMainMenuStates
from keyboards.client_buttons import get_main_menu_keyboard as get_client_main_menu_keyboard
from keyboards.manager_buttons import get_manager_main_keyboard
from keyboards.technician_buttons import get_technician_main_menu_keyboard
from keyboards.admin_buttons import get_admin_main_menu
from keyboards.call_center_buttons import call_center_main_menu_reply
from keyboards.controllers_buttons import controllers_main_menu
from keyboards.warehouse_buttons import warehouse_main_menu
from keyboards.junior_manager_buttons import get_junior_manager_main_keyboard
from loader import inline_message_manager


def get_global_navigation_router():
    router = Router()

    @router.message(F.text == "/start")
    async def global_start_handler(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Siz ro'yxatdan o'tmagansiz. Iltimos, admin bilan bog'laning.")
            return
        if user.get('role') == 'blocked' or not user.get('is_active', True):
            lang = user.get('language', 'uz')
            blocked_text = (
                "❌ Sizning hisobingiz bloklangan." if lang == 'uz' else
                "❌ Ваш аккаунт заблокирован."
            )
            await message.answer(blocked_text)
            return
        role = user.get('role', 'client')
        lang = user.get('language', 'uz')
        # Show correct menu and set FSM state
        if role == "client":
            await state.set_state(MainMenuStates.main_menu)
            sent_message = await message.answer("Xush kelibsiz!", reply_markup=get_client_main_menu_keyboard(lang))
        elif role == "manager":
            await state.set_state(MainMenuStates.main_menu)
            sent_message = await message.answer("Menejer paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель менеджера!", reply_markup=get_manager_main_keyboard(lang))
        elif role == "technician":
            await state.set_state(TechnicianMainMenuStates.main_menu)
            sent_message = await message.answer("Montajchi paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель монтажника!", reply_markup=get_technician_main_menu_keyboard(lang))
        elif role == "admin":
            await state.set_state(AdminMainMenuStates.main_menu)
            sent_message = await message.answer("Admin paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в админ-панель!", reply_markup=get_admin_main_menu(lang))
        elif role == "call_center":
            await state.set_state(CallCenterMainMenuStates.main_menu)
            sent_message = await message.answer("Call center paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель call center!", reply_markup=call_center_main_menu_reply(lang))
        elif role == "controller":
            await state.set_state(ControllerMainMenuStates.main_menu)
            sent_message = await message.answer("Nazoratchi paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель контролера!", reply_markup=controllers_main_menu(lang))
        elif role == "junior_manager":
            await state.set_state(JuniorManagerMainMenuStates.main_menu)
            sent_message = await message.answer("Junior menejer paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель junior менеджера!", reply_markup=get_junior_manager_main_menu(lang))
        elif role == "warehouse":
            await state.set_state(WarehouseMainMenuStates.main_menu)
            sent_message = await message.answer("Ombor paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель склада!", reply_markup=warehouse_main_menu(lang))
        else:
            await state.set_state(MainMenuStates.main_menu)
            sent_message = await message.answer("Xush kelibsiz!", reply_markup=get_client_main_menu_keyboard(lang))
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    return router