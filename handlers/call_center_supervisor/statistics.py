from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.role_router import get_role_router
from states.call_center_supervisor_states import CallCenterSupervisorStatisticsStates

def get_call_center_supervisor_statistics_router():
    router = get_role_router("call_center_supervisor")

    @router.message(F.text.in_(["📊 Statistikalar", "📊 Статистика"]))
    async def supervisor_statistics(message: Message, state: FSMContext):
        lang = 'uz' if message.text == "📊 Statistikalar" else 'ru'
        await state.set_state(CallCenterSupervisorStatisticsStates.statistics)
        # TODO: Replace with real statistics
        text = "📊 Statistika: 10 ta yangi buyurtma, 2 ta muammo." if lang == 'uz' else "📊 Статистика: 10 новых заказов, 2 проблемы."
        await message.answer(text)
    return router 