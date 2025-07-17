from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.role_router import get_role_router
from database.base_queries import get_user_by_telegram_id, get_orders_by_status, get_unresolved_issues
from states.call_center_supervisor_states import CallCenterSupervisorInboxStates

def get_call_center_supervisor_inbox_router():
    router = get_role_router("call_center_supervisor")

    @router.message(F.text == '📥 Inbox')
    async def supervisor_inbox(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center_supervisor':
            return

        lang = user.get('language', 'uz')
        await state.set_state(CallCenterSupervisorInboxStates.inbox)
        new_orders = await get_orders_by_status(['new', 'pending'])
        issues = await get_unresolved_issues()

        if not new_orders and not issues:
            text = "📭 Inbox bo'sh." if lang == 'uz' else "📭 Inbox пустой."
            await message.answer(text)
            return

        if new_orders:
            text = "🔎 <b>Inbox buyurtmalar:</b>\n\n" if lang == 'uz' else "🔎 <b>Заказы в Inbox:</b>\n\n"
            for order in new_orders[:10]:
                desc = order.get('description', '')[:50] + "..." if len(order.get('description', '')) > 50 else order.get('description', '')
                text += f"🔹 <b>#{order['id']}</b> - {desc}\n"
            await message.answer(text, parse_mode='HTML')

        if issues:
            text = "🔴 <b>Muammoli buyurtmalar:</b>\n\n" if lang == 'uz' else "🔴 <b>Проблемные заказы:</b>\n\n"
            for issue in issues[:10]:
                desc = issue.get('description', '')[:50] + "..." if len(issue.get('description', '')) > 50 else issue.get('description', '')
                text += f"🔴 <b>#{issue['id']}</b> - {desc}\n"
            await message.answer(text, parse_mode='HTML')

    return router 