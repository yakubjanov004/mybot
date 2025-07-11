from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime, timedelta
from keyboards.junior_manager_buttons import (
    get_junior_manager_main_keyboard, get_order_filter_keyboard,
    get_order_action_keyboard, get_assign_order_keyboard
)
from states.junior_manager_states import JuniorManagerOrderStates, JuniorManagerFilterStates, JuniorManagerAssignStates, JuniorManagerStatisticsStates, JuniorManagerLanguageStates, JuniorManagerMainMenuStates
from database.base_queries import get_user_lang, get_user_by_telegram_id
from database.manager_queries import (
    get_orders_for_junior_manager, assign_order_to_technician,
    get_available_technicians, get_order_details, get_filtered_orders,
    get_junior_manager_reports, get_technician_by_id, get_order_address
)
from utils.logger import setup_logger
from utils.inline_cleanup import answer_and_cleanup
from utils.role_router import get_role_router
from loader import inline_message_manager, bot, get_pool

logger = setup_logger('bot.junior_manager.orders')

def get_junior_manager_orders_router():
    router = get_role_router("junior_manager")
    
    @router.message(F.text.in_(["📋 Zayavkalarni ko'rish", "📋 Просмотр заявок"]))
    async def view_orders(message: Message, state: FSMContext):
        """Kichik menejer uchun zayavkalarni ko'rish"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            # Database pool olish
            pool = await get_pool()
            
            # Zayavkalarni olish
            orders = await get_orders_for_junior_manager(pool)
            
            if not orders:
                text = "Hozircha zayavkalar mavjud emas." if lang == 'uz' else "Заявок пока нет."
                await message.answer(text)
                return
            
            # Zayavkalarni ko'rsatish
            text = "📋 Zayavkalar ro'yxati:" if lang == 'uz' else "📋 Список заявок:"
            keyboard = []
            
            for order in orders[:10]:  # Faqat 10 ta zayavkani ko'rsatamiz
                order_id = order['id']
                status = order['status']
                created_at = order['created_at']
                description = order['description'][:50] + "..." if len(order['description']) > 50 else order['description']
                
                status_emoji = {
                    'new': '🆕',
                    'assigned': '👨‍🔧',
                    'in_progress': '⚡',
                    'completed': '✅',
                    'cancelled': '❌'
                }.get(status, '📋')
                
                status_text = {
                    'new': 'Yangi',
                    'assigned': 'Tayinlangan',
                    'in_progress': 'Jarayonda',
                    'completed': 'Bajarilgan',
                    'cancelled': 'Bekor qilingan'
                }.get(status, 'Noma\'lum')
                
                button_text = f"{status_emoji} #{order_id} - {status_text} - {description}"
                keyboard.append([InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"view_order:{order_id}"
                )])
            
            # Pagination tugmalari
            if len(orders) > 10:
                keyboard.append([
                    InlineKeyboardButton(text="◀️ Oldingi" if lang == 'uz' else "◀️ Предыдущая", callback_data="orders_page:prev"),
                    InlineKeyboardButton(text="Keyingi ▶️" if lang == 'uz' else "Следующая ▶️", callback_data="orders_page:next")
                ])
            
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            sent_message = await message.answer(text, reply_markup=reply_markup)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Error in view_orders: {e}")
            await message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    @router.callback_query(F.data.startswith("view_order:"))
    async def view_order_details(callback: CallbackQuery, state: FSMContext):
        """Zayavka tafsilotlarini ko'rish"""
        await answer_and_cleanup(callback, cleanup_after=True)
        
        try:
            order_id = int(callback.data.split(":")[1])
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Database pool olish
            pool = await get_pool()
            
            # Zayavka ma'lumotlarini olish
            order = await get_order_details(order_id, pool)
            
            if not order:
                text = "Zayavka topilmadi." if lang == 'uz' else "Заявка не найдена."
                await callback.message.answer(text)
                return
            
            # Zayavka tafsilotlarini ko'rsatish
            status_emoji = {
                'new': '🆕',
                'assigned': '👨‍🔧',
                'in_progress': '⚡',
                'completed': '✅',
                'cancelled': '❌'
            }.get(order['status'], '📋')
            
            status_text = {
                'new': 'Yangi',
                'assigned': 'Tayinlangan',
                'in_progress': 'Jarayonda',
                'completed': 'Bajarilgan',
                'cancelled': 'Bekor qilingan'
            }.get(order['status'], 'Noma\'lum')
            
            text = (
                f"{status_emoji} <b>Zayavka #{order_id}</b>\n\n"
                f"📝 <b>Tavsif:</b> {order['description']}\n"
                f"📍 <b>Manzil:</b> {order['address']}\n"
                f"👤 <b>Mijoz:</b> {order['client_name']}\n"
                f"📞 <b>Telefon:</b> {order['client_phone']}\n"
                f"📅 <b>Yaratilgan:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                f"🔧 <b>Status:</b> {status_text}\n"
            )
            
            if order['assigned_technician']:
                text += f"👨‍🔧 <b>Tayinlangan texnik:</b> {order['assigned_technician']}\n"
            
            # Harakatlar tugmalari
            keyboard = get_order_action_keyboard(order_id, order['status'], lang)
            
            sent_message = await callback.message.answer(text, parse_mode='HTML', reply_markup=keyboard)
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Error in view_order_details: {e}")
            await callback.message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    @router.callback_query(F.data.startswith("assign_order:"))
    async def assign_order(callback: CallbackQuery, state: FSMContext):
        """Zayavkani texnikka tayinlash"""
        await answer_and_cleanup(callback, cleanup_after=True)
        
        try:
            order_id = int(callback.data.split(":")[1])
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Database pool olish
            pool = await get_pool()
            
            # Mavjud texniklarni olish
            technicians = await get_available_technicians(pool)
            
            if not technicians:
                text = "Mavjud texniklar yo'q." if lang == 'uz' else "Нет доступных техников."
                await callback.message.answer(text)
                return
            
            # Texniklarni tanlash uchun tugmalar
            keyboard = []
            for tech in technicians:
                keyboard.append([InlineKeyboardButton(
                    text=f"👨‍🔧 {tech['name']} ({tech['phone']})",
                    callback_data=f"assign_to_tech:{order_id}:{tech['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton(
                text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                callback_data="cancel_assign"
            )])
            
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            text = "Texnikni tanlang:" if lang == 'uz' else "Выберите техника:"
            
            sent_message = await callback.message.answer(text, reply_markup=reply_markup)
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Error in assign_order: {e}")
            await callback.message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    @router.callback_query(F.data.startswith("assign_to_tech:"))
    async def confirm_assign_order(callback: CallbackQuery, state: FSMContext):
        """Zayavkani texnikka tayinlashni tasdiqlash"""
        await answer_and_cleanup(callback, cleanup_after=True)
        
        try:
            parts = callback.data.split(":")
            order_id = int(parts[1])
            technician_id = int(parts[2])
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Database pool olish
            pool = await get_pool()
            
            # Zayavkani tayinlash
            success = await assign_order_to_technician(order_id, technician_id, callback.from_user.id, pool)
            
            if success:
                text = f"✅ Zayavka #{order_id} texnikka muvaffaqiyatli tayinlandi!" if lang == 'uz' else f"✅ Заявка #{order_id} успешно назначена технику!"
                
                # Texnikka xabar yuborish
                technician = await get_technician_by_id(technician_id, pool)
                if technician and technician.get('telegram_id'):
                    order_address = await get_order_address(order_id, pool)
                    notification_text = (
                        f"🆕 Sizga yangi zayavka tayinlandi!\n"
                        f"📋 Zayavka #{order_id}\n"
                        f"📍 Manzil: {order_address or 'Manzil ko\'rsatilmagan'}"
                    )
                    try:
                        await bot.send_message(technician['telegram_id'], notification_text)
                    except Exception as e:
                        logger.error(f"Error sending notification to technician: {e}")
            else:
                text = "❌ Zayavkani tayinlashda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при назначении заявки."
            
            await callback.message.answer(text)
            
        except Exception as e:
            logger.error(f"Error in confirm_assign_order: {e}")
            await callback.message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    @router.message(F.text.in_(["🔍 Zayavkani filtrlash", "🔍 Фильтровать заявки"]))
    async def filter_orders(message: Message, state: FSMContext):
        """Zayavkalarni filtrlash"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            keyboard = get_order_filter_keyboard(lang)
            text = "Filtr parametrlarini tanlang:" if lang == 'uz' else "Выберите параметры фильтра:"
            
            sent_message = await message.answer(text, reply_markup=keyboard)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Error in filter_orders: {e}")
            await message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    @router.callback_query(F.data.startswith("filter_orders:"))
    async def apply_order_filter(callback: CallbackQuery, state: FSMContext):
        """Filtrni qo'llash"""
        await answer_and_cleanup(callback, cleanup_after=True)
        
        try:
            filter_type = callback.data.split(":")[1]
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Database pool olish
            pool = await get_pool()
            
            # Filtr bo'yicha zayavkalarni olish
            filtered_orders = await get_filtered_orders(filter_type, pool)
            
            if not filtered_orders:
                text = "Bu filtr bo'yicha zayavkalar topilmadi." if lang == 'uz' else "По этому фильтру заявки не найдены."
                await callback.message.answer(text)
                return
            
            # Filtrlangan zayavkalarni ko'rsatish
            text = f"🔍 Filtrlangan zayavkalar ({len(filtered_orders)} ta):" if lang == 'uz' else f"🔍 Отфильтрованные заявки ({len(filtered_orders)}):"
            keyboard = []
            
            for order in filtered_orders[:10]:
                order_id = order['id']
                status = order['status']
                description = order['description'][:50] + "..." if len(order['description']) > 50 else order['description']
                
                status_emoji = {
                    'new': '🆕',
                    'assigned': '👨‍🔧',
                    'in_progress': '⚡',
                    'completed': '✅',
                    'cancelled': '❌'
                }.get(status, '📋')
                
                keyboard.append([InlineKeyboardButton(
                    text=f"{status_emoji} #{order_id} - {description}",
                    callback_data=f"view_order:{order_id}"
                )])
            
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            sent_message = await callback.message.answer(text, reply_markup=reply_markup)
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Error in apply_order_filter: {e}")
            await callback.message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    @router.message(F.text.in_(["📊 Hisobotlar", "📊 Отчеты"]))
    async def show_reports(message: Message, state: FSMContext):
        """Kichik menejer uchun hisobotlar"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            # Database pool olish
            pool = await get_pool()
            
            # Hisobot ma'lumotlarini olish
            report_data = await get_junior_manager_reports(pool)
            
            text = (
                f"📊 <b>Kichik menejer hisoboti</b>\n\n"
                f"📋 <b>Jami zayavkalar:</b> {report_data['total_orders']}\n"
                f"🆕 <b>Yangi zayavkalar:</b> {report_data['new_orders']}\n"
                f"👨‍🔧 <b>Tayinlangan zayavkalar:</b> {report_data['assigned_orders']}\n"
                f"⚡ <b>Jarayonda:</b> {report_data['in_progress_orders']}\n"
                f"✅ <b>Bajarilgan:</b> {report_data['completed_orders']}\n"
                f"❌ <b>Bekor qilingan:</b> {report_data['cancelled_orders']}\n\n"
                f"📅 <b>Bugun:</b> {report_data['today_orders']} ta zayavka\n"
                f"📅 <b>Kecha:</b> {report_data['yesterday_orders']} ta zayavka"
            )
            
            await message.answer(text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error in show_reports: {e}")
            await message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    return router 

router = get_junior_manager_orders_router() 