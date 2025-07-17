from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.role_router import get_role_router
from states.call_center_supervisor_states import CallCenterSupervisorOrdersStates

def get_call_center_supervisor_orders_router():
    router = get_role_router("call_center_supervisor")

    @router.message(F.text.in_(["📝 Buyurtmalar", "📝 Заказы"]))
    async def supervisor_orders(message: Message, state: FSMContext):
        lang = 'uz' if message.text == "📝 Buyurtmalar" else 'ru'
        await state.set_state(CallCenterSupervisorOrdersStates.orders)
        # TODO: Replace with real DB call
        orders = [
            {"id": 1, "desc": "Internet ulash"},
            {"id": 2, "desc": "Telefon sozlash"}
        ]
        if not orders:
            text = "Buyurtmalar topilmadi." if lang == 'uz' else "Заказы не найдены."
            await message.answer(text)
            return
        text = "📋 Buyurtmalar ro'yxati:\n" if lang == 'uz' else "📋 Список заказов:\n"
        for order in orders:
            text += f"#{order['id']}: {order['desc']}\n"
        await message.answer(text)
    return router 