import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states.admin_states import AdminStates
from handlers.admin.main_menu import admin_statistics, admin_blocking, admin_change_language, admin_help, admin_back, admin_home, fallback_admin_main_menu

class DummyMessage:
    def __init__(self, text, user_id=123):
        self.text = text
        self.from_user = type('User', (), {'id': user_id})()
    async def answer(self, *args, **kwargs):
        return type('Msg', (), {'message_id': 1})()

@pytest.mark.asyncio
@pytest.mark.parametrize("text,handler,state", [
    ("📊 Statistika", admin_statistics, AdminStates.main_menu),
    ("🔒 Bloklash/Blokdan chiqarish", admin_blocking, AdminStates.blocking),
    ("🌐 Til o'zgartirish", admin_change_language, AdminStates.change_language),
    ("ℹ️ Yordam", admin_help, AdminStates.main_menu),
    ("◀️ Orqaga", admin_back, AdminStates.main_menu),
    ("🏠 Bosh sahifa", admin_home, AdminStates.main_menu),
])
async def test_admin_main_menu_buttons(text, handler, state):
    message = DummyMessage(text)
    fsm = FSMContext(None, None, None)
    await handler(message, fsm)
    # Here you would check FSM state and reply, but this is a stub

@pytest.mark.asyncio
async def test_admin_main_menu_fallback():
    message = DummyMessage("Noto'g'ri buyruq")
    fsm = FSMContext(None, None, None)
    await fallback_admin_main_menu(message, fsm)
    # Here you would check that fallback reply is sent 