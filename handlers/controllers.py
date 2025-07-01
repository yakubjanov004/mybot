from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime

from database.queries import (
    get_user_by_telegram_id, get_all_orders, get_technician_performance,
    get_system_statistics, get_all_technicians, get_order_details, update_order_priority,
    get_orders_by_status, assign_zayavka_to_technician, get_all_feedback,
    get_feedback_by_rating, get_unresolved_issues, get_service_quality_metrics,
    get_quality_trends, get_recent_feedback
)
from keyboards.controllers_buttons import (
    controllers_main_menu, orders_control_menu, technicians_menu,
    reports_menu, order_priority_keyboard, technician_assignment_keyboard
)
from states.controllers_states import ControllersStates 
from utils.logger import logger

router = Router()

@router.message(F.text.in_(["🎛️ Controller", "🎛️ Контроллер", "🎛️ Nazoratchi"]))
async def controllers_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'controller':
        lang = user.get('language', 'uz') if user else 'uz'
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    await state.set_state(ControllersStates.main_menu)
    lang = user.get('language', 'uz')
    welcome_text = "Controller paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель контроллера!"
    await message.answer(
        welcome_text,
        reply_markup=controllers_main_menu(user['language'])
    )

@router.callback_query(F.data == "orders_control")
async def orders_control(callback: CallbackQuery, state: FSMContext):
    """Orders control and monitoring"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    orders = await get_all_orders(limit=20)
    
    overview_text = "Buyurtmalar bo'yicha ma'lumot:" if lang == 'uz' else "Обзор заказов:"
    text = overview_text + "\n\n"
    
    status_counts = {}
    for order in orders:
        status = order['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        status_text = {
            'new': 'Yangi' if lang == 'uz' else 'Новые',
            'in_progress': 'Jarayonda' if lang == 'uz' else 'В работе',
            'completed': 'Bajarilgan' if lang == 'uz' else 'Завершенные',
            'cancelled': 'Bekor qilingan' if lang == 'uz' else 'Отмененные'
        }.get(status, status)
        text += f"• {status_text}: {count}\n"
    
    recent_text = "So'nggi buyurtmalar:" if lang == 'uz' else "Последние заказы:"
    text += "\n" + recent_text + "\n"
    for order in orders[:10]:
        priority_icon = "🔴" if order.get('priority') == 'high' else "🟡" if order.get('priority') == 'medium' else "🟢"
        text += f"{priority_icon} #{order['id']} - {order['client_name']} ({order['status']})\n"
    
    await state.set_state(ControllersStates.orders_control)
    await callback.message.edit_text(
        text,
        reply_markup=orders_control_menu(user['language'])
    )

@router.callback_query(F.data == "technicians_control")
async def technicians_control(callback: CallbackQuery, state: FSMContext):
    """Technicians performance monitoring"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    technicians = await get_all_technicians()
    
    overview_text = "Texniklar bo'yicha ma'lumot:" if lang == 'uz' else "Обзор техников:"
    text = overview_text + "\n\n"
    
    for tech in technicians:
        performance = await get_technician_performance(tech['id'])
        status_icon = "🟢" if tech['is_active'] else "🔴"
        text += f"{status_icon} {tech['full_name']}\n"
        
        active_text = "Faol buyurtmalar" if lang == 'uz' else "Активные заказы"
        completed_text = "Bugun bajarilgan" if lang == 'uz' else "Завершено сегодня"
        rating_text = "Reyting" if lang == 'uz' else "Рейтинг"
        
        text += f"   📋 {active_text}: {performance['active_orders']}\n"
        text += f"   ✅ {completed_text}: {performance['completed_today']}\n"
        text += f"   ⭐ {rating_text}: {performance['avg_rating']:.1f}\n\n"
    
    await state.set_state(ControllersStates.technicians_control)
    await callback.message.edit_text(
        text,
        reply_markup=technicians_menu(user['language'])
    )

@router.callback_query(F.data == "system_reports")
async def system_reports(callback: CallbackQuery, state: FSMContext):
    """System reports and analytics"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    stats = await get_system_statistics()
    
    reports_text = "Tizim hisobotlari" if lang == 'uz' else "Системные отчеты"
    total_orders_text = "Jami buyurtmalar" if lang == 'uz' else "Всего заказов"
    completed_text = "Bajarilgan buyurtmalar" if lang == 'uz' else "Завершенные заказы"
    pending_text = "Kutilayotgan buyurtmalar" if lang == 'uz' else "Ожидающие заказы"
    active_clients_text = "Faol mijozlar" if lang == 'uz' else "Активные клиенты"
    active_tech_text = "Faol texniklar" if lang == 'uz' else "Активные техники"
    revenue_text = "Bugungi tushum" if lang == 'uz' else "Доход сегодня"
    avg_time_text = "O'rtacha bajarish vaqti" if lang == 'uz' else "Среднее время выполнения"
    
    text = f"📊 {reports_text}\n\n"
    text += f"📈 {total_orders_text}: {stats['total_orders']}\n"
    text += f"✅ {completed_text}: {stats['completed_orders']}\n"
    text += f"⏳ {pending_text}: {stats['pending_orders']}\n"
    text += f"👥 {active_clients_text}: {stats['active_clients']}\n"
    text += f"🔧 {active_tech_text}: {stats['active_technicians']}\n"
    text += f"💰 {revenue_text}: {stats['revenue_today']} сум\n"
    text += f"📅 {avg_time_text}: {stats['avg_completion_time']} ч\n"
    
    await state.set_state(ControllersStates.reports_menu)
    await callback.message.edit_text(
        text,
        reply_markup=reports_menu(user['language'])
    )

@router.callback_query(F.data.startswith("order_priority_"))
async def order_priority_control(callback: CallbackQuery, state: FSMContext):
    """Control order priorities"""
    order_id = int(callback.data.split("_")[2])
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    order = await get_order_details(order_id)
    
    if not order:
        text = "Buyurtma topilmadi." if lang == 'uz' else "Заказ не найден."
        await callback.answer(text)
        return
    
    priority_text = "Buyurtma ustuvorligini boshqarish" if lang == 'uz' else "Управление приоритетом заказа"
    client_text = "Mijoz" if lang == 'uz' else "Клиент"
    service_text = "Xizmat" if lang == 'uz' else "Услуга"
    current_priority_text = "Joriy ustuvorlik" if lang == 'uz' else "Текущий приоритет"
    created_text = "Yaratilgan" if lang == 'uz' else "Создан"
    
    text = f"🎯 {priority_text} #{order['id']}\n\n"
    text += f"👤 {client_text}: {order['client_name']}\n"
    text += f"🔧 {service_text}: {order['service_type']}\n"
    text += f"📊 {current_priority_text}: {order.get('priority', 'normal')}\n"
    text += f"📅 {created_text}: {order['created_at']}\n"
    
    await state.update_data(current_order_id=order_id)
    await callback.message.edit_text(
        text,
        reply_markup=order_priority_keyboard(user['language'])
    )

@router.callback_query(F.data.startswith("set_priority_"))
async def set_order_priority(callback: CallbackQuery, state: FSMContext):
    """Set order priority"""
    priority = callback.data.split("_")[2]
    data = await state.get_data()
    order_id = data.get('current_order_id')
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    if not order_id:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await callback.answer(text)
        return
    
    success = await update_order_priority(order_id, priority)
    
    if success:
        text = "Ustuvorlik yangilandi." if lang == 'uz' else "Приоритет обновлен."
        await callback.answer(text)
        logger.info(f"Order {order_id} priority updated to {priority} by controller {user['id']}")
    else:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await callback.answer(text)

@router.callback_query(F.data == "assign_technicians")
async def assign_technicians_menu(callback: CallbackQuery, state: FSMContext):
    """Show technician assignment menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    unassigned_orders = await get_orders_by_status(['new', 'pending'])
    
    text = ("Tayinlanmagan buyurtmalar:" if lang == 'uz' else "Неназначенные заказы:") + "\n\n"
    for order in unassigned_orders:
        text += f"🔹 #{order['id']} - {order['client_name']}\n"
        text += f"   {order['service_type']} - {order['address']}\n\n"
    
    await state.set_state(ControllersStates.assign_technicians)
    await callback.message.edit_text(text)

@router.callback_query(F.data.startswith("assign_order_"))
async def assign_order_to_tech(callback: CallbackQuery, state: FSMContext):
    """Assign order to technician"""
    order_id = int(callback.data.split("_")[2])
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    technicians = await get_all_technicians(available_only=True)
    
    select_text = "Texnikni tanlang" if lang == 'uz' else "Выберите техника"
    text = f"👨‍🔧 {select_text} #{order_id}:\n\n"
    
    await state.update_data(assign_order_id=order_id)
    await callback.message.edit_text(
        text,
        reply_markup=technician_assignment_keyboard(user['language'], technicians)
    )

@router.callback_query(F.data.startswith("assign_tech_"))
async def confirm_technician_assignment(callback: CallbackQuery, state: FSMContext):
    """Confirm technician assignment"""
    tech_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    order_id = data.get('assign_order_id')
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    if not order_id:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await callback.answer(text)
        return
    
    success = await assign_zayavka_to_technician(order_id, tech_id)
    
    if success:
        text = "Texnik tayinlandi." if lang == 'uz' else "Техник назначен."
        await callback.answer(text)
        logger.info(f"Order {order_id} assigned to technician {tech_id} by controller {user['id']}")
    else:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await callback.answer(text)

@router.callback_query(F.data == "controllers_back")
async def controllers_back(callback: CallbackQuery, state: FSMContext):
    """Go back to controllers main menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(ControllersStates.main_menu)
    welcome_text = "Controller paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель контроллера!"
    await callback.message.edit_text(
        welcome_text,
        reply_markup=controllers_main_menu(user['language'])
    )

@router.callback_query(F.data == "quality_control")
async def quality_control_menu_handler(callback: CallbackQuery, state: FSMContext):
    """Quality control main menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    from keyboards.controllers_buttons import quality_control_detailed_menu
    quality_text = "Sifat nazorati bo'limi" if lang == 'uz' else "Раздел контроля качества"
    await callback.message.edit_text(
        quality_text,
        reply_markup=quality_control_detailed_menu(lang)
    )
    await callback.answer()

@router.callback_query(F.data == "quality_customer_feedback")
async def customer_feedback_view_handler(callback: CallbackQuery, state: FSMContext):
    """View customer feedback"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    from keyboards.controllers_buttons import feedback_detailed_filter_menu
    feedback_text = "Mijoz fikrlarini ko'rish" if lang == 'uz' else "Просмотр отзывов клиентов"
    await callback.message.edit_text(
        feedback_text,
        reply_markup=feedback_detailed_filter_menu(lang)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("feedback_filter_"))
async def filter_feedback_handler(callback: CallbackQuery, state: FSMContext):
    """Filter feedback by rating or criteria"""
    filter_type = callback.data.split("_")[2]
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        # Get filtered feedback from database
        if filter_type == "all":
            feedback_list = await get_all_feedback()
            title = "Barcha fikrlar" if lang == 'uz' else "Все отзывы"
        elif filter_type in ["1", "2", "3", "4", "5"]:
            rating = int(filter_type)
            feedback_list = await get_feedback_by_rating([rating])
            stars = "⭐" * rating
            title = f"{stars} ({rating}) baholar" if lang == 'uz' else f"{stars} ({rating}) оценки"
        elif filter_type == "recent":
            feedback_list = await get_recent_feedback(days=7)
            title = "So'nggi fikrlar" if lang == 'uz' else "Последние отзывы"
        
        text = f"📋 {title}\n\n"
        
        if feedback_list:
            for feedback in feedback_list[:10]:  # Show first 10
                stars = "⭐" * feedback['rating']
                client_name = feedback.get('client_name', 'Noma\'lum')
                comment = feedback.get('comment', '')
                created_date = feedback.get('created_at', '')
                
                text += f"{stars} {client_name}\n"
                if comment:
                    comment_preview = comment[:80] + "..." if len(comment) > 80 else comment
                    text += f"💬 {comment_preview}\n"
                text += f"📅 {created_date}\n\n"
        else:
            no_feedback_text = "Fikrlar topilmadi" if lang == 'uz' else "Отзывы не найдены"
            text += no_feedback_text
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error filtering feedback: {str(e)}")
        error_text = "Fikrlarni olishda xatolik" if lang == 'uz' else "Ошибка при получении отзывов"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "quality_unresolved_issues")
async def unresolved_issues_view_handler(callback: CallbackQuery, state: FSMContext):
    """View unresolved issues"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        # Get unresolved issues from database
        issues = await get_unresolved_issues()
        
        title = "Hal etilmagan muammolar" if lang == 'uz' else "Нерешенные проблемы"
        text = f"⚠️ {title}\n\n"
        
        if issues:
            for issue in issues[:10]:  # Show first 10
                order_id = issue.get('id', 'N/A')
                client_name = issue.get('client_name', 'Noma\'lum')
                description = issue.get('description', '')
                created_date = issue.get('created_at', '')
                days_pending = issue.get('days_pending', 0)
                
                text += f"🔹 #{order_id} - {client_name}\n"
                if description:
                    desc_preview = description[:60] + "..." if len(description) > 60 else description
                    text += f"📝 {desc_preview}\n"
                text += f"📅 {created_date}\n"
                
                pending_text = "kun kutmoqda" if lang == 'uz' else "дней ожидания"
                text += f"⏱️ {days_pending} {pending_text}\n\n"
        else:
            no_issues_text = "Hal etilmagan muammolar yo'q" if lang == 'uz' else "Нет нерешенных проблем"
            text += no_issues_text
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error getting unresolved issues: {str(e)}")
        error_text = "Muammolarni olishda xatolik" if lang == 'uz' else "Ошибка при получении проблем"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "quality_service_assessment")
async def service_quality_assessment_handler(callback: CallbackQuery, state: FSMContext):
    """Service quality assessment"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        # Get service quality metrics
        quality_metrics = await get_service_quality_metrics()
        
        title = "Xizmat sifatini baholash" if lang == 'uz' else "Оценка качества услуг"
        avg_rating_text = "O'rtacha baho" if lang == 'uz' else "Средняя оценка"
        total_reviews_text = "Jami sharhlar" if lang == 'uz' else "Всего отзывов"
        satisfaction_text = "Mijoz qoniqishi" if lang == 'uz' else "Удовлетворенность клиентов"
        
        text = f"⭐ {title}\n\n"
        text += f"📊 {avg_rating_text}: {quality_metrics.get('avg_rating', 0):.1f}/5.0\n"
        text += f"📝 {total_reviews_text}: {quality_metrics.get('total_reviews', 0)}\n"
        text += f"😊 {satisfaction_text}: {quality_metrics.get('satisfaction_rate', 0)}%\n\n"
        
        # Show rating distribution
        distribution_text = "Baholar taqsimoti:" if lang == 'uz' else "Распределение оценок:"
        text += f"📈 {distribution_text}\n"
        
        rating_distribution = quality_metrics.get('rating_distribution', {})
        total_reviews = quality_metrics.get('total_reviews', 0)
        
        for rating in range(5, 0, -1):
            count = rating_distribution.get(rating, 0)
            percentage = (count / total_reviews * 100) if total_reviews > 0 else 0
            stars = "⭐" * rating
            text += f"{stars} {count} ({percentage:.1f}%)\n"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error getting service quality metrics: {str(e)}")
        error_text = "Sifat ko'rsatkichlarini olishda xatolik" if lang == 'uz' else "Ошибка при получении показателей качества"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "quality_trends")
async def quality_trends_view_handler(callback: CallbackQuery, state: FSMContext):
    """View quality trends"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        # Get quality trends data
        trends = await get_quality_trends()
        
        title = "Sifat tendensiyalari" if lang == 'uz' else "Тенденции качества"
        text = f"📈 {title}\n\n"
        
        if trends:
            for period in trends:
                period_name = period.get('period', '')
                rating = period.get('avg_rating', 0)
                change = period.get('change', 0)
                
                trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                text += f"{trend_icon} {period_name}: {rating:.1f} "
                
                if change != 0:
                    change_text = f"({change:+.1f})"
                    text += change_text
                text += "\n"
        else:
            no_trends_text = "Tendensiya ma'lumotlari yo'q" if lang == 'uz' else "Нет данных о тенденциях"
            text += no_trends_text
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error getting quality trends: {str(e)}")
        error_text = "Tendensiyalarni olishda xatolik" if lang == 'uz' else "Ошибка при получении тенденций"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "quality_reports")
async def quality_reports_handler(callback: CallbackQuery, state: FSMContext):
    """Generate quality reports"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        # Generate comprehensive quality report
        report_title = "Sifat hisoboti" if lang == 'uz' else "Отчет по качеству"
        
        # Get various quality metrics
        quality_metrics = await get_service_quality_metrics()
        recent_feedback = await get_recent_feedback(days=30)
        unresolved_issues = await get_unresolved_issues()
        
        text = f"📋 {report_title}\n"
        text += f"📅 Sana: {datetime.now().strftime('%d.%m.%Y')}\n\n"
        
        # Overall metrics
        overall_text = "Umumiy ko'rsatkichlar:" if lang == 'uz' else "Общие показатели:"
        text += f"📊 {overall_text}\n"
        text += f"⭐ O'rtacha baho: {quality_metrics.get('avg_rating', 0):.1f}/5.0\n"
        text += f"📝 Jami fikrlar: {quality_metrics.get('total_reviews', 0)}\n"
        text += f"😊 Qoniqish darajasi: {quality_metrics.get('satisfaction_rate', 0)}%\n\n"
        
        # Recent activity
        recent_text = "So'nggi faollik (30 kun):" if lang == 'uz' else "Недавняя активность (30 дней):"
        text += f"📈 {recent_text}\n"
        text += f"💬 Yangi fikrlar: {len(recent_feedback)}\n"
        text += f"⚠️ Hal etilmagan muammolar: {len(unresolved_issues)}\n\n"
        
        # Recommendations
        recommendations_text = "Tavsiyalar:" if lang == 'uz' else "Рекомендации:"
        text += f"💡 {recommendations_text}\n"
        
        avg_rating = quality_metrics.get('avg_rating', 0)
        if avg_rating < 3.0:
            rec_text = "Xizmat sifatini yaxshilash zarur" if lang == 'uz' else "Необходимо улучшить качество обслуживания"
            text += f"• {rec_text}\n"
        elif avg_rating < 4.0:
            rec_text = "Yaxshi natija, lekin yaxshilash mumkin" if lang == 'uz' else "Хороший результат, но есть место для улучшения"
            text += f"• {rec_text}\n"
        else:
            rec_text = "A'lo xizmat sifati saqlanmoqda" if lang == 'uz' else "Отличное качество обслуживания поддерживается"
            text += f"• {rec_text}\n"
        
        if len(unresolved_issues) > 5:
            urgent_text = "Hal etilmagan muammolarga e'tibor bering" if lang == 'uz' else "Обратите внимание на нерешенные проблемы"
            text += f"• {urgent_text}\n"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error generating quality report: {str(e)}")
        error_text = "Hisobotni yaratishda xatolik" if lang == 'uz' else "Ошибка при создании отчета"
        await callback.message.edit_text(error_text)
        await callback.answer()
