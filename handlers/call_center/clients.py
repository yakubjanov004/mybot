from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.utils.i18n import lazy_gettext as _
from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import (
    search_clients, get_client_history, update_client_info
)
from keyboards.call_center_buttons import client_search_menu, new_order_reply_menu, get_client_actions_reply, call_center_main_menu_reply
from states.call_center import CallCenterStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_call_center_clients_router():
    router = get_role_router("call_center")

    @router.message(F.text.in_(set(["🔍 Mijoz qidirish", "🔍 Поиск клиента"])))
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
        text = " Mijoz qidirish" if lang == 'uz' else " Поиск клиента"
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
        text = "🔍 Mijoz qidirish" if lang == 'uz' else "🔍 Поиск клиента"
        await callback.message.edit_text(
            text,
            reply_markup=client_search_menu(user['language'])
        )
        await callback.answer()

    @router.callback_query(CallCenterStates.client_search, F.data.in_(['search_by_name', 'search_by_phone', 'search_by_id', 'back']))
    async def handle_search_method(callback: CallbackQuery, state: FSMContext):
        """Handle search method selection"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return

        lang = user.get('language', 'uz')
        
        if callback.data == 'back':
            await state.clear()
            await callback.message.edit_text(
                " Mijoz qidirish" if lang == 'uz' else " Поиск клиента",
                reply_markup=client_search_menu(lang)
            )
            await callback.answer()
            return

        method = callback.data.replace('search_by_', '')
        method_text = {
            'name': "Ism" if lang == 'uz' else "Имя",
            'phone': "Tel" if lang == 'uz' else "Тел",
            'id': "ID" if lang == 'uz' else "ID"
        }[method]
        
        await state.update_data(search_method=method)
        await callback.message.edit_text(
            f" {method_text} bo'yicha qidiruv\nMa'lumot kiriting:" if lang == 'uz' else 
            f" Поиск по {method_text}\nВведите данные:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text=" " + ("Ortga" if lang == 'uz' else "Назад"),
                        callback_data='back'
                    )]
                ]
            )
        )
        await callback.answer()

    @router.message(CallCenterStates.client_search)
    async def handle_search_method(message: Message, state: FSMContext):
        """Handle search method selection and full info request"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return

        lang = user.get('language', 'uz')
        
        # Get current state data
        data = await state.get_data()
        search_method = data.get('search_method')
        client = data.get('client')
        
        # Handle back button first
        if message.text == "🔙 Orqaga" or message.text == "Назад":
            # If we're viewing client details, go back to search input
            if client:
                await state.update_data(client=None)
                await message.answer(
                    f"🔍 {method_text[search_method]} bo'yicha qidiruv\nMa'lumot kiriting:" if lang == 'uz' else 
                    f"🔍 Поиск по {method_text[search_method]}\nВведите данные:",
                    reply_markup=new_order_reply_menu(lang)
                )
                return
            # If we're in search input state, go back to method selection
            elif search_method:
                await state.update_data(search_method=None)
                await message.answer(
                    "🔍 Mijoz qidirish" if lang == 'uz' else "🔍 Поиск клиента",
                    reply_markup=client_search_menu(lang)
                )
                return
            # If we're at method selection, go back to main menu
            else:
                await state.clear()
                await message.answer(
                    " Bosh menyu" if lang == 'uz' else "главное меню",
                    reply_markup=call_center_main_menu_reply(lang)
                )
                return

        # If not back button, continue with normal flow
        method_text = {
            'name': "Ism bo'yicha qidirish" if lang == 'uz' else "Поиск по имени",
            'phone': "Telefon raqami bo'yicha" if lang == 'uz' else "По номеру телефона",
            'id': "ID raqami bo'yicha" if lang == 'uz' else "По ID"
        }

        # Get the search method from message text
        method = None
        if message.text.startswith('🔤 '):
            method = 'name'
        elif message.text.startswith('📞 '):
            method = 'phone'
        elif message.text.startswith('🆔 '):
            method = 'id'

        method_text = {
            'name': "Ism bo'yicha qidirish" if lang == 'uz' else "Поиск по имени",
            'phone': "Telefon raqami bo'yicha" if lang == 'uz' else "По номеру телефона",
            'id': "ID raqami bo'yicha" if lang == 'uz' else "По ID"
        }
        
        # Get the search method from message text
        method = None
        if message.text.startswith('🔤 '):
            method = 'name'
        elif message.text.startswith('📞 '):
            method = 'phone'
        elif message.text.startswith('🆔 '):
            method = 'id'
        elif message.text == "🔍 To'liq ma'lumot" or message.text == "🔍 Полная информация":
            # Show full client information
            data = await state.get_data()
            client = data.get('client')
            
            if not client:
                await message.answer(
                    "Iltimos, avval mijozni toping.",
                    reply_markup=client_search_menu(lang)
                )
                return

            # Get client history
            client_history = await get_client_history(client['telegram_id'])
            
            # Format full information
            full_info = (
                f"🔍 To'liq ma'lumotlar:\n"
                f"👤 Ism: {client['full_name']}\n"
                f"📞 Telefon: {client['phone_number']}\n"
                f"🆔 ID: {client['telegram_id']}\n"
                f"📍 Manzil: {client.get('address', 'Ma\'lumot yo\'q')}\n"
                f"💼 Status: {client.get('role', 'Aktiv')}\n"
                f"📅 Oxirgi faoliyati: {client.get('last_activity', 'Ma\'lumot yo\'q')}\n\n"
                
                f"📊 Buyruqlar tarixi:\n"
            )
            
            # Add orders
            if client_history['orders']:
                for order in client_history['orders']:
                    full_info += (
                        f"• Buyruq #{order['id']}\n"
                        f"  Status: {order['status']}\n"
                        f"  Sana: {order['created_at']}\n"
                        f"  Xodim: {order.get('technician_name', 'Ma\'lumot yo\'q')}\n\n"
                    )
            else:
                full_info += "• Buyruqlar mavjud emas\n\n"
            
            # Add calls
            full_info += "📞 Qo'ng\'iroqlar tarixi:\n"
            if client_history['calls']:
                for call in client_history['calls']:
                    full_info += (
                        f"• {call['created_at']}\n"
                        f"  Davomiyligi: {call['duration']}\n"
                        f"  Natija: {call['result']}\n\n"
                    )
            else:
                full_info += "• Qo'ng'iroqlar mavjud emas\n\n"
            
            # Add feedback
            full_info += "📝 Fikr- mulohaza:\n"
            if client_history['feedback']:
                for feedback in client_history['feedback']:
                    full_info += (
                        f"• {feedback['created_at']}\n"
                        f"  Baholash: {feedback['rating']}\n"
                        f"  Matn: {feedback['text']}\n\n"
                    )
            else:
                full_info += "• Fikr-mulohaza yo'q\n\n"
            
            await message.answer(
                full_info,
                reply_markup=client_search_menu(lang)
            )
            return

        if method:
            await state.update_data(search_method=method)
            await message.answer(
                f"🔍 {method_text[method]} bo'yicha qidiruv\nMa'lumot kiriting:" if lang == 'uz' else 
                f"🔍 Поиск по {method_text[method]}\nВведите данные:",
                reply_markup=new_order_reply_menu(lang)
            )
            return

        # If we're here, user entered search value
        data = await state.get_data()
        search_method = data.get('search_method')
        search_value = message.text
        
        if not search_method:
            await message.answer(
                "Iltimos, qidiruv usulini tanlang.",
                reply_markup=client_search_menu(lang)
            )
            return

        # Format the query based on search method
        query = search_value
        if search_method == 'name':
            query = f"name:{search_value}"
        elif search_method == 'phone':
            query = f"phone:{search_value}"
        elif search_method == 'id':
            query = f"id:{search_value}"
        
        # Process search immediately
        clients = await search_clients(query)
        
        if clients:
            await state.update_data(client=clients[0])
            
            # Format client info
            client = clients[0]
            summary = (
                f"🔍 Mijoz topildi:\n"
                f"👤 Ism: {client['full_name']}\n"
                f"📞 Telefon: {client['phone_number']}\n"
                f"📅 Oxirgi faoliyati: {client.get('last_activity', 'Ma\'lumot yo\'q')}\n"
                f"\nBu mijoz haqida qo'shimcha ma'lumotlar:\n"
                f"🆔 ID: {client['telegram_id']}\n"
                f"📍 Manzil: {client.get('address', 'Ma\'lumot yo\'q')}\n"
                f"💼 Status: {client.get('role', 'Aktiv')}\n"
            )
            
            await message.answer(
                summary,
                reply_markup=get_client_actions_reply(lang)
            )
        else:
            await message.answer(
                "🔍 Mijoz topilmadi.\n"
                "Iltimos, ma'lumotlarni qayta tekshirib ko'ring.\n"
                "Agar mijoz bazada mavjud bo'lsa, quyidagi xatolardan biri bo'lishi mumkin:\n"
                "• Ism yoki telefon raqami noto'g'ri yozilgan\n"
                "• Mijoz ID raqami xato kiritilgan\n"
                "• Mijoz bazada mavjud emas\n\n"
                "Qayta qidiruv qilish uchun quyidagi tugmalardan foydalaning.",
                reply_markup=client_search_menu(lang)
            )

    @router.message(CallCenterStates.client_search)
    async def process_search(message: Message, state: FSMContext):
        """Process the actual search after method selection"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return

        lang = user.get('language', 'uz')
        data = await state.get_data()
        search_method = data.get('search_method')
        search_value = data.get('search_value')

        if not search_method or not search_value:
            await message.answer(
                "Iltimos, qidiruv usulini tanlang.",
                reply_markup=client_search_menu(lang)
            )
            return

        # Format the query based on search method
        query = search_value
        if search_method == 'name':
            query = f"name:{search_value}"
        elif search_method == 'phone':
            query = f"phone:{search_value}"
        elif search_method == 'id':
            query = f"id:{search_value}"
        
        clients = await search_clients(query)

        if clients:
            await state.update_data(client=clients[0])
            
            # Format client info
            client = clients[0]
            summary = (
                f"🔍 Mijoz topildi:\n"
                f"👤 Ism: {client['full_name']}\n"
                f"📞 Telefon: {client['phone_number']}\n"
                f"📅 Oxirgi faoliyati: {client.get('last_activity', 'Ma\'lumot yo\'q')}\n"
                f"\nBu mijoz haqida qo'shimcha ma'lumotlar:\n"
                f"🆔 ID: {client['telegram_id']}\n"
                f"📍 Manzil: {client.get('address', 'Ma\'lumot yo\'q')}\n"
                f"💼 Status: {client.get('role', 'Aktiv')}\n"
            )
            
            await message.answer(
                summary,
                reply_markup=get_client_actions_reply(lang)
            )
        else:
            await message.answer(
                "🔍 Mijoz topilmadi.\n"
                "Iltimos, ma'lumotlarni qayta tekshirib ko'ring.\n"
                "Agar mijoz bazada mavjud bo'lsa, quyidagi xatolardan biri bo'lishi mumkin:\n"
                "• Ism yoki telefon raqami noto'g'ri yozilgan\n"
                "• Mijoz ID raqami xato kiritilgan\n"
                "• Mijoz bazada mavjud emas\n\n"
                "Qayta qidiruv qilish uchun quyidagi tugmalardan foydalaning.",
                reply_markup=client_search_menu(lang)
            )

    @router.callback_query(CallCenterStates.client_search, F.data.in_(['open_order', 'call', 'chat', 'details', 'back']))
    async def handle_client_action(callback: CallbackQuery, state: FSMContext):
        """Handle client actions"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return

        lang = user.get('language', 'uz')
        data = await state.get_data()
        client = data.get('client')
        
        action = callback.data
        if action == 'open_order':
            # TODO: Implement order creation FSM
            await callback.message.answer(
                "Buyurtma yaratish jarayoni boshlandi..." if lang == 'uz' else "Процесс создания заказа начался..."
            )
        elif action == 'call':
            await callback.message.answer(
                f"📞 {client['phone']}"
            )
        elif action == 'chat':
            # TODO: Implement chat interface
            await callback.message.answer(
                "Chat interfeysi ishga tushirildi..." if lang == 'uz' else "Интерфейс чата запущен..."
            )
        elif action == 'details':
            # TODO: Implement full profile view
            await callback.message.answer(
                "To'liq profil ko'rsatilmoqda..." if lang == 'uz' else "Показывается полный профиль..."
            )
        elif action == 'back':
            await state.update_data(search_method=None)
            await callback.message.edit_text(
                "🔍 Mijoz qidirish" if lang == 'uz' else "🔍 Поиск клиента",
                reply_markup=client_search_menu(lang)
            )
        
        await callback.answer()

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
