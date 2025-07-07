from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import (
    search_clients, get_client_history, update_client_info
)
from keyboards.call_center_buttons import client_search_menu
from states.call_center import CallCenterStates
from utils.logger import logger

def get_call_center_clients_router():
    router = Router()

    @router.message(F.text.in_(["🔍 Mijoz qidirish", "�� Поиск клиента"]))
    async def reply_client_search(message: Message, state: FSMContext):
        """Client search from reply keyboard"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        await state.set_state(CallCenterStates.client_search)
        lang = user.get('language', 'uz')
        text = "🔍 Qidiruv so'rovini kiriting (ism, telefon raqam):" if lang == 'uz' else "🔍 Введите поисковый запрос (имя, номер телефона):"
        await message.answer(
            text,
            reply_markup=client_search_menu(user['language'])
        )

    @router.callback_query(F.data == "client_search")
    async def client_search(callback: CallbackQuery, state: FSMContext):
        """Client search menu"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        await state.set_state(CallCenterStates.client_search)
        text = "🔍 Qidiruv so'rovini kiriting (ism, telefon raqam):" if lang == 'uz' else "🔍 Введите поисковый запрос (имя, номер телефона):"
        await callback.message.edit_text(
            text,
            reply_markup=client_search_menu(user['language'])
        )

    @router.message(StateFilter(CallCenterStates.client_search))
    async def search_client(message: Message, state: FSMContext):
        """Search for client"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        query = message.text.strip()
        
        if len(query) < 3:
            text = "❌ Qidiruv so'rovi kamida 3 ta belgidan iborat bo'lishi kerak." if lang == 'uz' else "❌ Поисковый запрос должен содержать минимум 3 символа."
            await message.answer(text)
            return
        
        try:
            clients = await search_clients(query)
            
            if clients:
                results_text = "🔍 Qidiruv natijalari:" if lang == 'uz' else "🔍 Результаты поиска:"
                text = f"{results_text}\n\n"
                
                for i, client in enumerate(clients[:10], 1):  # Limit to 10 results
                    text += f"{i}. 👤 {client['full_name']}\n"
                    text += f"   📞 {client['phone_number']}\n"
                    if client.get('address'):
                        text += f"   📍 {client['address']}\n"
                    
                    # Show recent orders count
                    from database.call_center_queries import get_orders_by_client
                    orders = await get_orders_by_client(client['id'], limit=1)
                    orders_count_text = "buyurtmalar" if lang == 'uz' else "заказов"
                    text += f"   📋 {len(orders)} {orders_count_text}\n\n"
                    
                    # Store client info for potential selection
                    await state.update_data({f'client_{i}': client['id']})
                
                select_text = "Mijozni tanlash uchun raqamini yuboring (1-10)" if lang == 'uz' else "Отправьте номер для выбора клиента (1-10)"
                text += f"📌 {select_text}"
                
                await state.set_state(CallCenterStates.client_details)
                
            else:
                text = "❌ Mijozlar topilmadi." if lang == 'uz' else "❌ Клиенты не найдены."
            
            await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error searching clients: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(CallCenterStates.client_details))
    async def select_client_by_number(message: Message, state: FSMContext):
        """Select client by number from search results"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        try:
            client_num = int(message.text.strip())
            if not 1 <= client_num <= 10:
                raise ValueError("Invalid number")
            
            data = await state.get_data()
            client_id = data.get(f'client_{client_num}')
            
            if not client_id:
                text = "❌ Noto'g'ri raqam." if lang == 'uz' else "❌ Неверный номер."
                await message.answer(text)
                return
            
            # Get detailed client history
            client_history = await get_client_history(client_id)
            
            if not client_history:
                text = "❌ Mijoz ma'lumotlari topilmadi." if lang == 'uz' else "❌ Информация о клиенте не найдена."
                await message.answer(text)
                return
            
            client = client_history['client']
            orders = client_history['orders']
            calls = client_history['calls']
            feedback = client_history['feedback']
            
            # Format client details
            details_text = "👤 Mijoz ma'lumotlari:" if lang == 'uz' else "👤 Информация о клиенте:"
            text = f"{details_text}\n\n"
            text += f"📛 {client['full_name']}\n"
            text += f"📞 {client['phone_number']}\n"
            if client.get('address'):
                text += f"📍 {client['address']}\n"
            text += f"📅 Ro'yxatdan o'tgan: {client['created_at'].strftime('%d.%m.%Y')}\n"
            
            # Orders summary
            if orders:
                orders_text = "📋 Buyurtmalar:" if lang == 'uz' else "📋 Заказы:"
                text += f"\n{orders_text}\n"
                for order in orders[:5]:
                    status_emoji = "✅" if order['status'] == 'completed' else "⏳" if order['status'] in ['new', 'pending'] else "🔧"
                    text += f"{status_emoji} {order.get('zayavka_type', 'Xizmat')} - {order['status']}\n"
                    text += f"   📅 {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            
            # Calls summary
            if calls:
                calls_text = "📞 Qo'ng'iroqlar:" if lang == 'uz' else "📞 Звонки:"
                text += f"\n{calls_text}\n"
                for call in calls[:3]:
                    result_emoji = "✅" if call['result'] == 'order_created' else "📞"
                    text += f"{result_emoji} {call['result']} - {call['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            
            # Feedback summary
            if feedback:
                feedback_text = "⭐ Baholash:" if lang == 'uz' else "⭐ Оценки:"
                text += f"\n{feedback_text}\n"
                avg_rating = sum(f['rating'] for f in feedback) / len(feedback)
                text += f"⭐ O'rtacha: {avg_rating:.1f}/5 ({len(feedback)} ta baholash)\n"
            
            await state.update_data(selected_client_id=client_id)
            await state.set_state(CallCenterStates.client_history)
            await message.answer(text)
            
        except ValueError:
            text = "❌ Iltimos, 1 dan 10 gacha raqam kiriting." if lang == 'uz' else "❌ Пожалуйста, введите число от 1 до 10."
            await message.answer(text)
        except Exception as e:
            logger.error(f"Error getting client details: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(CallCenterStates.client_history))
    async def handle_client_actions(message: Message, state: FSMContext):
        """Handle actions on selected client"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        action = message.text.strip().lower()
        
        data = await state.get_data()
        client_id = data.get('selected_client_id')
        
        if not client_id:
            text = "❌ Mijoz tanlanmagan." if lang == 'uz' else "❌ Клиент не выбран."
            await message.answer(text)
            return
        
        try:
            if action in ['yangi buyurtma', 'новый заказ', 'order']:
                # Start new order for this client
                await state.update_data(client_id=client_id)
                await state.set_state(CallCenterStates.select_service_type)
                
                from keyboards.call_center_buttons import order_types_keyboard
                text = "🔧 Xizmat turini tanlang:" if lang == 'uz' else "🔧 Выберите тип услуги:"
                await message.answer(
                    text,
                    reply_markup=order_types_keyboard(user['language'])
                )
                
            elif action in ['chat', 'чат']:
                # Start chat with client
                await state.update_data(client_id=client_id)
                await state.set_state(CallCenterStates.in_chat)
                
                text = "💬 Chat boshlandi. Xabaringizni yuboring:" if lang == 'uz' else "💬 Чат начат. Отправьте ваше сообщение:"
                await message.answer(text)
                
            else:
                help_text = "Mavjud amallar:" if lang == 'uz' else "Доступные действия:"
                text = f"{help_text}\n"
                text += "• 'yangi buyurtma' - yangi buyurtma yaratish\n" if lang == 'uz' else "• 'новый заказ' - создать новый заказ\n"
                text += "• 'chat' - mijoz bilan chat boshlash" if lang == 'uz' else "• 'чат' - начать чат с клиентом"
                await message.answer(text)
                
        except Exception as e:
            logger.error(f"Error handling client action: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    return router
