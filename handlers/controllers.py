from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.queries import (
    get_user_by_telegram_id, get_all_orders, get_technician_performance,
    get_system_statistics, get_all_technicians, get_order_details, update_order_priority,
    get_orders_by_status, assign_zayavka_to_technician
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
