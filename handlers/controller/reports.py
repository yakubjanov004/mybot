from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from filters.role_filter import RoleFilter
from utils.role_router import get_role_router
from database.queries import (
    UserQueries,
    OrderQueries,
    ReportQueries
)
from keyboards.controllers_buttons import reports_menu, back_to_controllers_menu
from states.controllers_states import ControllersStates
from utils.logger import logger
from datetime import datetime, timedelta

def get_controller_reports_router():
    router = get_role_router("controller")

    @router.message(F.text.in_(["📊 Hisobotlar", "📊 Отчеты"]))
    async def reports_menu_handler(message: Message, state: FSMContext):
        """Hisobotlar menyusi"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(ControllersStates.reports_menu)
        
        if lang == 'uz':
            text = """📊 <b>Hisobotlar bo'limi</b>

Quyidagi hisobotlarni olishingiz mumkin:

• Tizim hisoboti
• Texniklar hisoboti  
• Sifat hisoboti
• Kunlik hisobot
• Haftalik hisobot

Kerakli hisobotni tanlang:"""
        else:
            text = """📊 <b>Раздел отчетов</b>

Вы можете получить следующие отчеты:

• Системный отчет
• Отчет по техникам
• Отчет по качеству
• Ежедневный отчет
• Еженедельный отчет

Выберите нужный отчет:"""
        
        await message.answer(
            text,
            reply_markup=reports_menu(lang),
            parse_mode='HTML'
        )

    @router.message(F.text.in_(["📈 Tizim hisoboti", "📈 Системный отчет"]))
    async def system_report(message: Message, state: FSMContext):
        """Tizim hisoboti"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        stats = await get_system_statistics()
        
        if lang == 'uz':
            text = f"""📈 <b>Tizim hisoboti</b>
📅 <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

📊 <b>Buyurtmalar:</b>
• Jami buyurtmalar: {stats.get('total_orders', 0)}
• Bajarilgan buyurtmalar: {stats.get('completed_orders', 0)}
• Kutilayotgan buyurtmalar: {stats.get('pending_orders', 0)}

👥 <b>Foydalanuvchilar:</b>
• Faol mijozlar: {stats.get('active_clients', 0)}
• Faol texniklar: {stats.get('active_technicians', 0)}

💰 <b>Moliyaviy ko'rsatkichlar:</b>
• Bugungi tushum: {stats.get('revenue_today', 0):,} so'm
• O'rtacha bajarish vaqti: {stats.get('avg_completion_time', 0)} soat

📊 <b>Samaradorlik:</b>
• Bajarish foizi: {(stats.get('completed_orders', 0) / max(stats.get('total_orders', 1), 1) * 100):.1f}%"""
        else:
            text = f"""📈 <b>Системный отчет</b>
📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

📊 <b>Заказы:</b>
• Всего заказов: {stats.get('total_orders', 0)}
• Завершенные заказы: {stats.get('completed_orders', 0)}
• Ожидающие заказы: {stats.get('pending_orders', 0)}

👥 <b>Пользователи:</b>
• Активные клиенты: {stats.get('active_clients', 0)}
• Активные техники: {stats.get('active_technicians', 0)}

💰 <b>Финансовые показатели:</b>
• Доход сегодня: {stats.get('revenue_today', 0):,} сум
• Среднее время выполнения: {stats.get('avg_completion_time', 0)} ч

📊 <b>Эффективность:</b>
• Процент выполнения: {(stats.get('completed_orders', 0) / max(stats.get('total_orders', 1), 1) * 100):.1f}%"""
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["👨‍🔧 Texniklar hisoboti", "👨‍🔧 Отчет по техникам"]))
    async def technicians_report(message: Message, state: FSMContext):
        """Texniklar hisoboti"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        technicians = await get_all_technicians()
        
        # Statistikani hisoblash
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
            text = f"""👨‍🔧 <b>Texniklar hisoboti</b>
📅 <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

👥 <b>Texniklar soni:</b>
• Jami texniklar: {total_technicians}
• Faol texniklar: {active_technicians}
• Nofaol texniklar: {total_technicians - active_technicians}

📊 <b>Ish samaradorligi:</b>
• Jami bajarilgan vazifalar: {total_completed}
• Hozir jarayonda: {total_active}
• O'rtacha reyting: {avg_rating:.1f}/5.0

📈 <b>Eng faol texniklar:</b>"""
        else:
            text = f"""👨‍🔧 <b>Отчет по техникам</b>
📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

👥 <b>Количество техников:</b>
• Всего техников: {total_technicians}
• Активные техники: {active_technicians}
• Неактивные техники: {total_technicians - active_technicians}

📊 <b>Производительность:</b>
• Всего выполненных задач: {total_completed}
• Сейчас в работе: {total_active}
• Средний рейтинг: {avg_rating:.1f}/5.0

📈 <b>Самые активные техники:</b>"""
        
        # Eng faol texniklar
        performance_data = []
        for tech in technicians:
            performance = await get_technician_performance(tech['id'])
            performance_data.append({
                'name': tech['full_name'],
                'completed': performance.get('completed_orders', 0),
                'rating': performance.get('avg_rating', 0)
            })
        
        performance_data.sort(key=lambda x: x['completed'], reverse=True)
        
        for i, perf in enumerate(performance_data[:5], 1):
            text += f"\n{i}. {perf['name']} - {perf['completed']} vazifa (⭐{perf['rating']:.1f})"
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["⭐ Sifat hisoboti", "⭐ Отчет по качеству"]))
    async def quality_report(message: Message, state: FSMContext):
        """Sifat hisoboti"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        quality_metrics = await get_service_quality_metrics()
        
        if lang == 'uz':
            text = f"""⭐ <b>Sifat hisoboti</b>
📅 <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

📊 <b>Umumiy ko'rsatkichlar:</b>
• O'rtacha baho: {quality_metrics.get('avg_rating', 0):.1f}/5.0
• Jami sharhlar: {quality_metrics.get('total_reviews', 0)}
• Mijoz qoniqishi: {quality_metrics.get('satisfaction_rate', 0)}%

📈 <b>Baholar taqsimoti:</b>"""
        else:
            text = f"""⭐ <b>Отчет по качеству</b>
📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

📊 <b>Общие показатели:</b>
• Средняя оценка: {quality_metrics.get('avg_rating', 0):.1f}/5.0
• Всего отзывов: {quality_metrics.get('total_reviews', 0)}
• Удовлетворенность клиентов: {quality_metrics.get('satisfaction_rate', 0)}%

📈 <b>Распределение оценок:</b>"""
        
        # Baholar taqsimoti
        rating_distribution = quality_metrics.get('rating_distribution', {})
        total_reviews = quality_metrics.get('total_reviews', 0)
        
        for rating in range(5, 0, -1):
            count = rating_distribution.get(rating, 0)
            percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
            stars = "⭐" * rating
            text += f"\n{stars} {count} ({percentage:.1f}%)"
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["📅 Kunlik hisobot", "📅 Ежедневный отчет"]))
    async def daily_report(message: Message, state: FSMContext):
        """Kunlik hisobot"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        
        # Bugungi buyurtmalar
        today = datetime.now().date()
        orders = await get_all_orders(limit=100)
        today_orders = [o for o in orders if o.get('created_at') and o['created_at'].date() == today]
        
        completed_today = len([o for o in today_orders if o['status'] == 'completed'])
        new_today = len([o for o in today_orders if o['status'] == 'new'])
        in_progress_today = len([o for o in today_orders if o['status'] == 'in_progress'])
        
        if lang == 'uz':
            text = f"""📅 <b>Kunlik hisobot</b>
📅 <b>Sana:</b> {today.strftime('%d.%m.%Y')}

📊 <b>Bugungi buyurtmalar:</b>
• Jami yangi: {new_today}
• Jarayonda: {in_progress_today}
• Bajarilgan: {completed_today}
• Jami: {len(today_orders)}

📈 <b>Samaradorlik:</b>
• Bajarish foizi: {(completed_today / max(len(today_orders), 1) * 100):.1f}%

⏰ <b>Hisobot vaqti:</b> {datetime.now().strftime('%H:%M')}"""
        else:
            text = f"""📅 <b>Ежедневный отчет</b>
📅 <b>Дата:</b> {today.strftime('%d.%m.%Y')}

📊 <b>Заказы за сегодня:</b>
• Всего новых: {new_today}
• В работе: {in_progress_today}
• Завершено: {completed_today}
• Всего: {len(today_orders)}

📈 <b>Эффективность:</b>
• Процент выполнения: {(completed_today / max(len(today_orders), 1) * 100):.1f}%

⏰ <b>Время отчета:</b> {datetime.now().strftime('%H:%M')}"""
        
        await message.answer(text, parse_mode='HTML')

    @router.message(F.text.in_(["📊 Haftalik hisobot", "📊 Еженедельный отчет"]))
    async def weekly_report(message: Message, state: FSMContext):
        """Haftalik hisobot"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'controller':
            return
        
        lang = user.get('language', 'uz')
        
        # So'nggi hafta
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        orders = await get_all_orders(limit=200)
        week_orders = [o for o in orders if o.get('created_at') and o['created_at'].date() >= week_ago]
        
        completed_week = len([o for o in week_orders if o['status'] == 'completed'])
        new_week = len([o for o in week_orders if o['status'] == 'new'])
        
        if lang == 'uz':
            text = f"""📊 <b>Haftalik hisobot</b>
📅 <b>Davr:</b> {week_ago.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}

📊 <b>Haftalik buyurtmalar:</b>
• Jami yangi: {new_week}
•

📊 <b>Haftalik buyurtmalar:</b>
• Jami yangi: {new_week}
• Bajarilgan: {completed_week}
• Jami: {len(week_orders)}

📈 <b>Haftalik samaradorlik:</b>
• Bajarish foizi: {(completed_week / max(len(week_orders), 1) * 100):.1f}%
• Kunlik o'rtacha: {len(week_orders) / 7:.1f} buyurtma

⏰ <b>Hisobot vaqti:</b> {datetime.now().strftime('%H:%M')}"""
        else:
            text = f"""📊 <b>Еженедельный отчет</b>
📅 <b>Период:</b> {week_ago.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}

📊 <b>Заказы за неделю:</b>
• Всего новых: {new_week}
• Завершено: {completed_week}
• Всего: {len(week_orders)}

📈 <b>Недельная эффективность:</b>
• Процент выполнения: {(completed_week / max(len(week_orders), 1) * 100):.1f}%
• Среднее в день: {len(week_orders) / 7:.1f} заказов

⏰ <b>Время отчета:</b> {datetime.now().strftime('%H:%M')}"""
        
        await message.answer(text, parse_mode='HTML')

    return router
