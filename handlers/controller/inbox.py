from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.role_router import get_role_router
from database.base_queries import get_user_by_telegram_id, get_orders_by_status, get_unresolved_issues
from states.controllers_states import ControllerInboxStates

def get_controller_inbox_router():
    router = get_role_router("controller")

    @router.message(F.text.in_("📥 Inbox"))
    async def controller_inbox(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return

        lang = user.get('language', 'uz')
        await state.set_state(ControllerInboxStates.inbox)
        # Yangi va muammoli buyurtmalarni olish
        new_orders = await get_orders_by_status(['new', 'pending'])
        issues = await get_unresolved_issues()

        if not new_orders and not issues:
            text = "📭 Inbox bo'sh." if lang == 'uz' else "📭 Inbox пустой."
            await message.answer(text)
            return

        # Yangi buyurtmalar
        if new_orders:
            text = "🔎 <b>Inbox buyurtmalar:</b>\n\n" if lang == 'uz' else "🔎 <b>Заказы в Inbox:</b>\n\n"
            for order in new_orders[:10]:
                desc = order.get('description', '')[:50] + "..." if len(order.get('description', '')) > 50 else order.get('description', '')
                text += f"\ud83d\udd39 <b>#{order['id']}</b> - {desc}\n"
            await message.answer(text, parse_mode='HTML')

        # Muammoli buyurtmalar
        if issues:
            text = "\ud83d\udd34 <b>Muammoli buyurtmalar:</b>\n\n" if lang == 'uz' else "\ud83d\udd34 <b>Проблемные заказы:</b>\n\n"
            for issue in issues[:10]:
                desc = issue.get('description', '')[:50] + "..." if len(issue.get('description', '')) > 50 else issue.get('description', '')
                text += f"\ud83d\udd34 <b>#{issue['id']}</b> - {desc}\n"
            await message.answer(text, parse_mode='HTML')

    return router 