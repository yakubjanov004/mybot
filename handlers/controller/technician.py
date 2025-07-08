from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from filters.role_filter import RoleFilter
from utils.role_router import get_role_router
from database.base_queries import get_user_by_telegram_id, assign_zayavka_to_technician, get_all_technicians
from keyboards.controllers_buttons import (
    technicians_menu, technician_assignment_keyboard, back_to_controllers_menu
)
from states.controllers_states import ControllersStates
from utils.logger import logger

def get_controller_technician_router():
    router = get_role_router("controller")

    @router.message(F.text.in_(["\U0001F468\u200D\U0001F527 Texniklar nazorati", "\U0001F468\u200D\U0001F527 \u041A\u043E\u043D\u0442\u0440\u043E\u043B\u044C \u0442\u0435\u0445\u043D\u0438\u043A\u043E\u0432"]))
    async def technicians_control_menu(message: Message, state: FSMContext):
        """Texniklar nazorati menyusi"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(ControllersStates.technicians_control)
        
        # Texniklar ro'yxatini olish
        technicians = await get_all_technicians()
        
        active_count = len([t for t in technicians if t['is_active']])
        total_count = len(technicians)
        
        if lang == 'uz':
            text = f"""
\U0001F468\u200D\U0001F527 <b>Texniklar nazorati</b>

\U0001F4CA <b>Umumiy ma'lumot:</b>
• Jami texniklar: {total_count}
• Faol texniklar: {active_count}
• Nofaol texniklar: {total_count - active_count}

Kerakli amalni tanlang:"""
        else:
            text = f"""
\U0001F468\u200D\U0001F527 <b>\u041A\u043E\u043D\u0442\u0440\u043E\u043B\u044C \u0442\u0435\u0445\u043D\u0438\u043A\u043E\u0432</b>

\U0001F4CA <b>\u041E\u0431\u0449\u0430\u044F \u0438\u043D\u0444\u043E\u0440\u043C\u0430\u0446\u0438\u044F:</b>
• \u0412\u0441\u0435\u0433\u043E \u0442\u0435\u0445\u043D\u0438\u043A\u043E\u0432: {total_count}
• \u0410\u043A\u0442\u0438\u0432\u043D\u044B\u0435 \u0442\u0435\u0445\u043D\u0438\u043A\u0438: {active_count}
• \u041D\u0435\u0430\u043A\u0442\u0438\u0432\u043D\u044B\u0435 \u0442\u0435\u0445\u043D\u0438\u043A\u0438: {total_count - active_count}

\u0412\u044B\u0431\u0435\u0440\u0438\u0442\u0435 \u043D\u0443\u0436\u043D\u043E\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:"""
        
        await message.answer(
            text,
            reply_markup=technicians_menu(lang),
            parse_mode='HTML'
        )

    @router.message(F.text.in_(["📋 Texniklar ro'yxati", "📋 Список техников"]))
    async def show_technicians_list(message: Message, state: FSMContext):
        """Texniklar ro'yxatini ko'rsatish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        technicians = await get_all_technicians()
        
        if lang == 'uz':
            text = "📋 <b>Texniklar ro'yxati:</b>\n\n"
        else:
            text = "📋 <b>Список техников:</b>\n\n"
        
        if technicians:
            for tech in technicians:
                status_icon = "🟢" if tech['is_active'] else "🔴"
                performance = await get_technician_performance(tech['id'])
                
                text += f"{status_icon} <b>{tech['full_name']}</b>\n"
                text += f"📞 {tech.get('phone_number', 'Noma\'lum')}\n"
                
                active_text = "Faol vazifalar" if lang == 'uz' else "Активные задачи"
                completed_text = "Bajarilgan" if lang == 'uz' else "Завершено"
                rating_text = "Reyting" if lang == 'uz' else "Рейтинг"
                
                text += f"📋 {active_text}: {performance.get('active_orders', 0)}\n"
                text += f"✅ {completed_text}: {performance.get('completed_orders', 0)}\n"
                text += f"⭐ {rating_text}: {performance.get('avg_rating', 0):.1f}\n\n"
        else:
            no_technicians_text = "Texniklar topilmadi" if lang == 'uz' else "Техники не найдены"
            text += no_technicians_text
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["📊 Texniklar samaradorligi", "📊 Эффективность техников"]))
    async def show_technicians_performance(message: Message, state: FSMContext):
        """Texniklar samaradorligini ko'rsatish"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        technicians = await get_all_technicians()
        
        # Samaradorlik bo'yicha tartiblash
        performance_data = []
        for tech in technicians:
            performance = await get_technician_performance(tech['id'])
            performance_data.append({
                'name': tech['full_name'],
                'completed': performance.get('completed_orders', 0),
                'active': performance.get('active_orders', 0),
                'rating': performance.get('avg_rating', 0),
                'is_active': tech['is_active']
            })
        
        # Bajarilgan vazifalar bo'yicha tartiblash
        performance_data.sort(key=lambda x: x['completed'], reverse=True)
        
        if lang == 'uz':
            text = "📊 <b>Texniklar samaradorligi:</b>\n\n"
        else:
            text = "📊 <b>Эффективность техников:</b>\n\n"
        
        for i, perf in enumerate(performance_data[:10], 1):
            status_icon = "🟢" if perf['is_active'] else "🔴"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            text += f"{medal} {status_icon} <b>{perf['name']}</b>\n"
            
            completed_text = "Bajarilgan" if lang == 'uz' else "Завершено"
            active_text = "Faol" if lang == 'uz' else "Активные"
            rating_text = "Reyting" if lang == 'uz' else "Рейтинг"
            
            text += f"   ✅ {completed_text}: {perf['completed']}\n"
            text += f"   📋 {active_text}: {perf['active']}\n"
            text += f"   ⭐ {rating_text}: {perf['rating']:.1f}\n\n"
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["🎯 Vazifa tayinlash", "🎯 Назначение задач"]))
    async def task_assignment_menu(message: Message, state: FSMContext):
        """Vazifa tayinlash menyusi"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(ControllersStates.assign_technicians)
        
        # Tayinlanmagan buyurtmalarni olish
        unassigned_orders = await get_orders_by_status(['new', 'pending'])
        
        if lang == 'uz':
            text = f"""🎯 <b>Vazifa tayinlash</b>

📋 <b>Tayinlanmagan buyurtmalar:</b> {len(unassigned_orders)}

Quyidagi buyurtmalarni texniklarga tayinlashingiz mumkin:"""
        else:
            text = f"""🎯 <b>Назначение задач</b>

📋 <b>Неназначенные заказы:</b> {len(unassigned_orders)}

Вы можете назначить следующие заказы техникам:"""
        
        if unassigned_orders:
            text += "\n\n"
            for order in unassigned_orders[:5]:  # Faqat 5 tasini ko'rsatish
                client_name = order.get('client_name', 'Noma\'lum')
                description = order.get('description', '')[:40] + "..." if len(order.get('description', '')) > 40 else order.get('description', '')
                
                text += f"🔹 <b>#{order['id']}</b> - {client_name}\n"
                text += f"📝 {description}\n\n"
        else:
            no_orders_text = "Tayinlanmagan buyurtmalar yo'q" if lang == 'uz' else "Нет неназначенных заказов"
            text += f"\n\n{no_orders_text}"
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["📈 Texniklar hisoboti", "📈 Отчет по техникам"]))
    async def technicians_report(message: Message, state: FSMContext):
        """Texniklar hisoboti"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        technicians = await get_all_technicians()
        
        # Umumiy statistika
        total_technicians = len(technicians)
        active_technicians = len([t for t in technicians if t['is_active']])
        
        total_completed = 0
        total_active = 0
        total_rating = 0
        rated_count = 0
        
        for tech in technicians:
            performance = await get_technician_performance(tech['id'])
            total_completed += performance.get('completed_orders', 0)
            total_active += performance.get('active_orders', 0)
            
            rating = performance.get('avg_rating', 0)
            if rating > 0:
                total_rating += rating
                rated_count += 1
        
        avg_rating = (total_rating / rated_count) if rated_count > 0 else 0
        
        if lang == 'uz':
            text = f"""📈 <b>Texniklar hisoboti</b>

👥 <b>Texniklar soni:</b>
• Jami: {total_technicians}
• Faol: {active_technicians}
• Nofaol: {total_technicians - active_technicians}

📊 <b>Ish samaradorligi:</b>
• Jami bajarilgan: {total_completed}
• Hozir jarayonda: {total_active}
• O'rtacha reyting: {avg_rating:.1f}

📅 <b>Hisobot sanasi:</b> {message.date.strftime('%d.%m.%Y %H:%M')}"""
        else:
            text = f"""📈 <b>Отчет по техникам</b>

👥 <b>Количество техников:</b>
• Всего: {total_technicians}
• Активные: {active_technicians}
• Неактивные: {total_technicians - active_technicians}

📊 <b>Производительность:</b>
• Всего выполнено: {total_completed}
• Сейчас в работе: {total_active}
• Средний рейтинг: {avg_rating:.1f}

📅 <b>Дата отчета:</b> {message.date.strftime('%d.%m.%Y %H:%M')}"""
        
        await message.answer(text, parse_mode='HTML')

    return router
