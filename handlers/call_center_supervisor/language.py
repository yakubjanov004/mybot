from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.role_router import get_role_router
from states.call_center_supervisor_states import CallCenterSupervisorLanguageStates

def get_call_center_supervisor_language_router():
    router = get_role_router("call_center_supervisor")

    @router.message(F.text.in_(["🌐 Tilni o'zgartirish", "🌐 Изменить язык"]))
    async def supervisor_language(message: Message, state: FSMContext):
        # TODO: Replace with real language toggle logic
        await state.set_state(CallCenterSupervisorLanguageStates.language)
        text = "Til o'zgartirildi!" if message.text == "🌐 Tilni o'zgartirish" else "Язык изменён!"
        await message.answer(text)
    return router 