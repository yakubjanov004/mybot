from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.role_router import get_role_router
from states.call_center_supervisor_states import CallCenterSupervisorFeedbackStates

def get_call_center_supervisor_feedback_router():
    router = get_role_router("call_center_supervisor")

    @router.message(F.text.in_(["⭐️ Fikr-mulohaza", "⭐️ Обратная связь"]))
    async def supervisor_feedback(message: Message, state: FSMContext):
        lang = 'uz' if message.text == "⭐️ Fikr-mulohaza" else 'ru'
        await state.set_state(CallCenterSupervisorFeedbackStates.feedback)
        # TODO: Replace with real feedback logic
        text = "Fikr-mulohaza uchun rahmat!" if lang == 'uz' else "Спасибо за обратную связь!"
        await message.answer(text)
    return router 