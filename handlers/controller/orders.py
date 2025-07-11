from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from filters.role_filter import RoleFilter
from utils.role_router import get_role_router
from database.base_queries import get_user_by_telegram_id, get_all_orders, get_orders_by_status, get_order_details, update_order_priority, get_unresolved_issues
from keyboards.controllers_buttons import (
    orders_control_menu, order_priority_keyboard, back_to_controllers_menu
)
from states.controllers_states import ControllerOrdersStates
from utils.logger import logger

def get_controller_orders_router():
    router = get_role_router("controller")

    @router.message(F.text.in_(["📋 Buyurtmalar nazorati", "📋 Контроль заказов"]))
    async def orders_control_menu_handler(message: Message, state: FSMContext):
        """Buyurtmalar nazorati menyusi"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        lang = user.get('language', 'uz')
        await state.set_state(ControllerOrdersStates.orders_control)
        orders = await get_all_orders(limit=50)
        status_counts = {}
        for order in orders:
            status = order['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        if lang == 'uz':
            text = (
                "📋 <b>Buyurtmalar nazorati</b>\n\n"
                "📊 <b>Holat bo'yicha:</b>\n"
                f"• Yangi: {status_counts.get('new', 0)}\n"
                f"• Tayinlangan: {status_counts.get('assigned', 0)}\n"
                f"• Jarayonda: {status_counts.get('in_progress', 0)}\n"
                f"• Bajarilgan: {status_counts.get('completed', 0)}\n"
                f"• Bekor qilingan: {status_counts.get('cancelled', 0)}\n\n"
                "Kerakli amalni tanlang:"
            )
        else:
            text = (
                "📋 <b>Контроль заказов</b>\n\n"
                "📊 <b>По статусам:</b>\n"
                f"• Новые: {status_counts.get('new', 0)}\n"
                f"• Назначенные: {status_counts.get('assigned', 0)}\n"
                f"• В работе: {status_counts.get('in_progress', 0)}\n"
                f"• Завершенные: {status_counts.get('completed', 0)}\n"
                f"• Отмененные: {status_counts.get('cancelled', 0)}\n\n"
                "Выберите нужное действие:"
            )
        await message.answer(
            text,
            reply_markup=orders_control_menu(lang),
            parse_mode='HTML'
        )

    @router.message(F.text.in_(["🆕 Yangi buyurtmalar", "🆕 Новые заказы"]))
    async def show_new_orders(message: Message, state: FSMContext):
        """Yangi buyurtmalarni ko'rsatish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        orders = await get_orders_by_status(['new'])
        
        if lang == 'uz':
            text = "🆕 <b>Yangi buyurtmalar:</b>\n\n"
        else:
            text = "🆕 <b>Новые заказы:</b>\n\n"
        
        if orders:
            for order in orders[:10]:  # Faqat 10 tasini ko'rsatish
                client_name = order.get('client_name', 'Noma\'lum')
                created_at = order.get('created_at', '')
                description = order.get('description', '')[:50] + "..." if len(order.get('description', '')) > 50 else order.get('description', '')
                
                text += f"🔹 <b>#{order['id']}</b> - {client_name}\n"
                text += f"📝 {description}\n"
                text += f"📅 {created_at}\n\n"
        else:
            no_orders_text = "Yangi buyurtmalar yo'q" if lang == 'uz' else "Нет новых заказов"
            text += no_orders_text
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["⏳ Kutilayotgan", "⏳ Ожидающие"]))
    async def show_pending_orders(message: Message, state: FSMContext):
        """Kutilayotgan buyurtmalarni ko'rsatish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        orders = await get_orders_by_status(['pending', 'assigned'])
        
        if lang == 'uz':
            text = "⏳ <b>Kutilayotgan buyurtmalar:</b>\n\n"
        else:
            text = "⏳ <b>Ожидающие заказы:</b>\n\n"
        
        if orders:
            for order in orders[:10]:
                client_name = order.get('client_name', 'Noma\'lum')
                technician_name = order.get('technician_name', 'Tayinlanmagan')
                created_at = order.get('created_at', '')
                
                text += f"🔸 <b>#{order['id']}</b> - {client_name}\n"
                text += f"👨‍🔧 Texnik: {technician_name}\n"
                text += f"📅 {created_at}\n\n"
        else:
            no_orders_text = "Kutilayotgan buyurtmalar yo'q" if lang == 'uz' else "Нет ожидающих заказов"
            text += no_orders_text
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["🔴 Muammoli buyurtmalar", "🔴 Проблемные заказы"]))
    async def show_problem_orders(message: Message, state: FSMContext):
        """Muammoli buyurtmalarni ko'rsatish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        issues = await get_unresolved_issues()
        
        if lang == 'uz':
            text = "🔴 <b>Muammoli buyurtmalar:</b>\n\n"
        else:
            text = "🔴 <b>Проблемные заказы:</b>\n\n"
        
        if issues:
            for issue in issues[:10]:
                client_name = issue.get('client_name', 'Noma\'lum')
                days_pending = issue.get('days_pending', 0)
                description = issue.get('description', '')[:50] + "..." if len(issue.get('description', '')) > 50 else issue.get('description', '')
                
                text += f"🔴 <b>#{issue['id']}</b> - {client_name}\n"
                text += f"📝 {description}\n"
                
                pending_text = "kun kutmoqda" if lang == 'uz' else "дней ожидания"
                text += f"⏱️ {days_pending} {pending_text}\n\n"
        else:
            no_issues_text = "Muammoli buyurtmalar yo'q" if lang == 'uz' else "Нет проблемных заказов"
            text += no_issues_text
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["📊 Buyurtmalar hisoboti", "📊 Отчет по заказам"]))
    async def orders_report(message: Message, state: FSMContext):
        """Buyurtmalar hisoboti"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        orders = await get_all_orders(limit=100)
        
        # Statistikani hisoblash
        total_orders = len(orders)
        completed_orders = len([o for o in orders if o['status'] == 'completed'])
        pending_orders = len([o for o in orders if o['status'] in ['new', 'pending', 'assigned']])
        in_progress_orders = len([o for o in orders if o['status'] == 'in_progress'])
        
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        
        if lang == 'uz':
            text = f"""📊 <b>Buyurtmalar hisoboti</b>

📈 <b>Umumiy ko'rsatkichlar:</b>
• Jami buyurtmalar: {total_orders}
• Bajarilgan: {completed_orders}
• Jarayonda: {in_progress_orders}
• Kutilayotgan: {pending_orders}

📊 <b>Samaradorlik:</b>
• Bajarish foizi: {completion_rate:.1f}%

📅 <b>Sana:</b> {message.date.strftime('%d.%m.%Y %H:%M')}"""
        else:
            text = f"""📊 <b>Отчет по заказам</b>

📈 <b>Общие показатели:</b>
• Всего заказов: {total_orders}
• Завершено: {completed_orders}
• В работе: {in_progress_orders}
• Ожидает: {pending_orders}

📊 <b>Эффективность:</b>
• Процент выполнения: {completion_rate:.1f}%

📅 <b>Дата:</b> {message.date.strftime('%d.%m.%Y %H:%M')}"""
        
        await message.answer(text, parse_mode='HTML')

    return router
