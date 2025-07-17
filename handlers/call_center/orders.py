from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import (
    get_client_by_phone, create_client, create_order_from_call, log_call, get_pending_orders, get_order_by_id, accept_order, reject_order
)
from keyboards.call_center_buttons import (
    order_types_keyboard, call_status_keyboard, new_order_reply_menu
)
from states.call_center import CallCenterOrderStates
from utils.logger import logger
from utils.role_router import get_role_router
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory
from database.models import WorkflowType, UserRole, Priority

def get_call_center_orders_router():
    router = get_role_router("call_center")

    @router.message(F.text.in_(["🆕 Yangi buyurtma", "🆕 Новый заказ"]))
    async def reply_new_order(message: Message, state: FSMContext):
        """Start new order creation from reply keyboard"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        await state.set_state(CallCenterOrderStates.new_order_phone)
        lang = user.get('language', 'uz')
        text = "📞 Mijoz telefon raqamini kiriting:" if lang == 'uz' else "📞 Введите номер телефона клиента:"
        await message.answer(
            text,
            reply_markup=new_order_reply_menu(user['language'])
        )

    @router.callback_query(F.data == "new_order")
    async def new_order_start(callback: CallbackQuery, state: FSMContext):
        """Start creating new order"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        await state.set_state(CallCenterOrderStates.new_order_phone)
        text = "📞 Mijoz telefon raqamini kiriting:" if lang == 'uz' else "📞 Введите номер телефона клиента:"
        await callback.message.edit_text(
            text,
            reply_markup=new_order_reply_menu(user['language'])
        )

    @router.message(StateFilter(CallCenterOrderStates.new_order_phone))
    async def get_client_phone(message: Message, state: FSMContext):
        """Get client phone and check if exists"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        phone = message.text.strip()
        
        # Validate phone format
        if not phone.startswith('998'):
            text = "❌ Noto'g'ri telefon format. Masalan: 998901234567" if lang == 'uz' else "❌ Неверный формат телефона. Например: 998901234567"
            await message.answer(text)
            return
        
        try:
            client = await get_client_by_phone(phone)
            
            if client:
                # Existing client
                await state.update_data(client_id=client['id'], client_phone=phone)
                found_text = "✅ Mavjud mijoz topildi:" if lang == 'uz' else "✅ Найден существующий клиент:"
                text = f"{found_text}\n\n"
                text += f"👤 {client['full_name']}\n"
                text += f"📞 {client['phone_number']}\n"
                if client.get('address'):
                    text += f"📍 {client['address']}\n"
                
                # Show client's order history
                from database.call_center_queries import get_orders_by_client
                orders = await get_orders_by_client(client['id'], limit=3)
                if orders:
                    recent_text = "📋 So'nggi buyurtmalar:" if lang == 'uz' else "📋 Последние заказы:"
                    text += f"\n{recent_text}\n"
                    for order in orders:
                        status_emoji = "✅" if order['status'] == 'completed' else "⏳" if order['status'] in ['new', 'pending'] else "🔧"
                        text += f"{status_emoji} {order.get('zayavka_type', 'Xizmat')} - {order['status']}\n"
                
                await state.set_state(CallCenterOrderStates.select_service_type)
                await message.answer(
                    text,
                    reply_markup=order_types_keyboard(user['language'])
                )
            else:
                # New client
                await state.update_data(client_phone=phone)
                await state.set_state(CallCenterOrderStates.new_client_name)
                text = "👤 Yangi mijoz. Ismini kiriting:" if lang == 'uz' else "👤 Новый клиент. Введите имя:"
                await message.answer(text)
                
        except Exception as e:
            logger.error(f"Error getting client by phone: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(CallCenterOrderStates.new_client_name))
    async def get_client_name(message: Message, state: FSMContext):
        """Get new client name"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.update_data(client_name=message.text.strip())
        await state.set_state(CallCenterOrderStates.new_client_address)
        text = "📍 Mijoz manzilini kiriting:" if lang == 'uz' else "📍 Введите адрес клиента:"
        await message.answer(text)

    @router.message(StateFilter(CallCenterOrderStates.new_client_address))
    async def get_client_address(message: Message, state: FSMContext):
        """Get client address and create client"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        try:
            client_data = {
                'full_name': data['client_name'],
                'phone_number': data['client_phone'],
                'address': message.text.strip(),
                'language': user['language']
            }
            
            client_id = await create_client(client_data)
            
            if client_id:
                await state.update_data(client_id=client_id)
                await state.set_state(CallCenterOrderStates.select_service_type)
                text = "✅ Mijoz muvaffaqiyatli yaratildi!\n\n🔧 Xizmat turini tanlang:" if lang == 'uz' else "✅ Клиент успешно создан!\n\n🔧 Выберите тип услуги:"
                await message.answer(
                    text,
                    reply_markup=order_types_keyboard(user['language'])
                )
            else:
                text = "❌ Mijozni yaratishda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при создании клиента."
                await message.answer(text)
                
        except Exception as e:
            logger.error(f"Error creating client: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("service_type_"))
    async def select_service_type(callback: CallbackQuery, state: FSMContext):
        """Select service type and determine workflow type"""
        service_type = callback.data.split("_", 2)[2]
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        # Map service types to workflow types for call center initiated requests
        workflow_mapping = {
            'installation': WorkflowType.CONNECTION_REQUEST.value,
            'setup': WorkflowType.CONNECTION_REQUEST.value,
            'repair': WorkflowType.TECHNICAL_SERVICE.value,
            'maintenance': WorkflowType.TECHNICAL_SERVICE.value,
            'consultation': WorkflowType.CALL_CENTER_DIRECT.value
        }
        
        workflow_type = workflow_mapping.get(service_type, WorkflowType.TECHNICAL_SERVICE.value)
        
        await state.update_data(
            service_type=service_type,
            workflow_type=workflow_type
        )
        await state.set_state(CallCenterOrderStates.issue_description_capture)
        text = "📝 Mijoz muammosini batafsil tasvirlab bering:" if lang == 'uz' else "📝 Подробно опишите проблему клиента:"
        await callback.message.edit_text(text)

    @router.message(StateFilter(CallCenterOrderStates.issue_description_capture))
    async def get_issue_description(message: Message, state: FSMContext):
        """Get detailed issue description from call center operator"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        issue_description = message.text.strip()
        
        await state.update_data(
            description=issue_description,
            issue_description=issue_description
        )
        await state.set_state(CallCenterOrderStates.order_priority)
        text = "🎯 Buyurtma ustuvorligini tanlang:" if lang == 'uz' else "🎯 Выберите приоритет заказа:"
        await message.answer(
            text,
            reply_markup=call_status_keyboard(user['language'])
        )

    @router.message(StateFilter(CallCenterOrderStates.order_description))
    async def get_order_description(message: Message, state: FSMContext):
        """Get order description (legacy handler for backward compatibility)"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.update_data(description=message.text.strip())
        await state.set_state(CallCenterOrderStates.order_priority)
        text = "🎯 Buyurtma ustuvorligini tanlang:" if lang == 'uz' else "🎯 Выберите приоритет заказа:"
        await message.answer(
            text,
            reply_markup=call_status_keyboard(user['language'])
        )

    @router.callback_query(F.data.startswith("priority_"))
    async def set_order_priority(callback: CallbackQuery, state: FSMContext):
        """Set order priority and create workflow request with proper routing"""
        priority = callback.data.split("_")[1]
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        try:
            # Initialize workflow components
            state_manager = StateManagerFactory.create_state_manager()
            notification_system = NotificationSystemFactory.create_notification_system()
            workflow_engine = WorkflowEngineFactory.create_workflow_engine(
                state_manager, notification_system, None
            )
            
            # Get client details for contact info
            client = await get_client_by_phone(data['client_phone'])
            if not client:
                text = "❌ Mijoz ma'lumotlari topilmadi." if lang == 'uz' else "❌ Данные клиента не найдены."
                await callback.message.edit_text(text)
                return
            
            # Prepare workflow request data with enhanced client details capture
            workflow_type = data.get('workflow_type', WorkflowType.TECHNICAL_SERVICE.value)
            
            request_data = {
                'client_id': data['client_id'],
                'description': data.get('description', ''),
                'location': client.get('address', ''),
                'contact_info': {
                    'phone': data['client_phone'],
                    'name': client['full_name'],
                    'address': client.get('address', '')
                },
                'priority': priority,
                'service_type': data['service_type'],
                'created_by_role': UserRole.CALL_CENTER.value,
                'created_by': user['id'],
                'issue_description': data.get('issue_description', data.get('description', '')),
                'client_details': {
                    'name': client['full_name'],
                    'phone': data['client_phone'],
                    'address': client.get('address', ''),
                    'language': client.get('language', 'uz')
                }
            }
            
            # Create workflow request - this will route to appropriate role based on workflow type
            request_id = await workflow_engine.initiate_workflow(workflow_type, request_data)
            
            if request_id:
                # Log the call for audit trail
                call_log_data = {
                    'user_id': data['client_id'],
                    'phone_number': data['client_phone'],
                    'duration': 0,  # Will be updated later if needed
                    'result': 'workflow_request_created',
                    'notes': f"Workflow request {request_id[:8]} created via call center for {workflow_type}",
                    'created_by': user['id']
                }
                await log_call(call_log_data)
                
                # Determine routing information based on workflow type for user feedback
                routing_info = {
                    WorkflowType.CONNECTION_REQUEST.value: {
                        'uz': 'Menejer',
                        'ru': 'Менеджер'
                    },
                    WorkflowType.TECHNICAL_SERVICE.value: {
                        'uz': 'Nazoratchi',
                        'ru': 'Контроллер'
                    },
                    WorkflowType.CALL_CENTER_DIRECT.value: {
                        'uz': 'Call-markaz nazoratchisi',
                        'ru': 'Руководитель call-центра'
                    }
                }
                
                route_text = routing_info.get(workflow_type, {}).get(lang, 'Unknown')
                
                # Create success message
                success_text = "✅ So'rov muvaffaqiyatli yaratildi!" if lang == 'uz' else "✅ Запрос успешно создан!"
                request_id_text = "So'rov ID" if lang == 'uz' else "ID запроса"
                service_text = "Xizmat" if lang == 'uz' else "Услуга"
                priority_text = "Ustuvorlik" if lang == 'uz' else "Приоритет"
                routed_text = "Yo'naltirildi" if lang == 'uz' else "Направлено"
                workflow_text = "Ish jarayoni" if lang == 'uz' else "Тип процесса"
                
                # Map workflow types to user-friendly names
                workflow_names = {
                    WorkflowType.CONNECTION_REQUEST.value: {
                        'uz': 'Ulanish so\'rovi',
                        'ru': 'Запрос подключения'
                    },
                    WorkflowType.TECHNICAL_SERVICE.value: {
                        'uz': 'Texnik xizmat',
                        'ru': 'Техническое обслуживание'
                    },
                    WorkflowType.CALL_CENTER_DIRECT.value: {
                        'uz': 'To\'g\'ridan-to\'g\'ri xizmat',
                        'ru': 'Прямое обслуживание'
                    }
                }
                
                workflow_name = workflow_names.get(workflow_type, {}).get(lang, workflow_type)
                
                text = f"{success_text}\n\n"
                text += f"🆔 {request_id_text}: {request_id[:8]}\n"
                text += f"📋 {workflow_text}: {workflow_name}\n"
                text += f"🔧 {service_text}: {data['service_type']}\n"
                text += f"🎯 {priority_text}: {priority}\n"
                text += f"📞 Telefon: {data['client_phone']}\n"
                text += f"👤 Mijoz: {client['full_name']}\n"
                text += f"➡️ {routed_text}: {route_text}\n\n"
                
                # Add workflow-specific routing information
                if workflow_type == WorkflowType.CONNECTION_REQUEST.value:
                    routing_info_text = "So'rov menejerga yuborildi va keyingi bosqichlar: Kichik menejer → Nazoratchi → Texnik → Ombor" if lang == 'uz' else "Запрос направлен менеджеру, следующие этапы: Младший менеджер → Контроллер → Техник → Склад"
                elif workflow_type == WorkflowType.TECHNICAL_SERVICE.value:
                    routing_info_text = "So'rov nazoratchi orqali texnikka yuboriladi" if lang == 'uz' else "Запрос направляется технику через контроллера"
                else:  # CALL_CENTER_DIRECT
                    routing_info_text = "So'rov call-markaz nazoratchisiga yuborildi" if lang == 'uz' else "Запрос направлен руководителю call-центра"
                
                text += f"ℹ️ {routing_info_text}"
                
                await callback.message.edit_text(text)
                
                logger.info(f"Call center workflow request created: ID={request_id[:8]}, Type={workflow_type}, Operator={user['id']}, Client={client['full_name']}")
            else:
                text = "❌ So'rovni yaratishda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при создании запроса."
                await callback.message.edit_text(text)
            
            await state.set_state(CallCenterOrderStates.main_menu)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error creating call center workflow request: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.message(F.text.in_(["⏳ Kutilayotgan", "⏳ Ожидающие"]))
    async def show_pending_orders(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        orders = await get_pending_orders()
        if orders:
            text = ("⏳ Kutilayotgan buyurtmalar:\n\n" if lang == 'uz' else "⏳ Ожидающие заказы:\n\n")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"#{order['id']} | {order['client_name']} | 🕒 {order['created_at'].strftime('%H:%M')}",
                        callback_data=f"pending_order_{order['id']}"
                    ),
                    InlineKeyboardButton(
                        text=("Qabul qilish" if lang == 'uz' else "Принять"),
                        callback_data=f"accept_order_{order['id']}"
                    )
                ] for order in orders
            ] + [[InlineKeyboardButton(text=("Orqaga" if lang == 'uz' else "Назад"), callback_data="pending_orders_back")]])
            await message.answer(text, reply_markup=keyboard)
        else:
            text = ("📭 Kutilayotgan buyurtmalar yo'q" if lang == 'uz' else "📭 Нет ожидающих заказов")
            await message.answer(text)

    @router.callback_query(F.data.startswith("pending_order_"))
    async def show_pending_order_details(callback: CallbackQuery, state: FSMContext):
        order_id = int(callback.data.split("_")[-1])
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        order = await get_order_by_id(order_id)
        if not order:
            await callback.answer(("Buyurtma topilmadi" if lang == 'uz' else "Заказ не найден"), show_alert=True)
            return
        text = (
            f"🆔 Buyurtma ID: #{order['id']}\n"
            f"👤 Mijoz: {order['client_name']}\n"
            f"📞 Telefon: {order['phone_number']}\n"
            f"📝 Tavsif: {order['description']}\n"
            f"🕒 Yaratilgan: {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            if lang == 'uz' else
            f"🆔 ID заказа: #{order['id']}\n"
            f"👤 Клиент: {order['client_name']}\n"
            f"📞 Телефон: {order['phone_number']}\n"
            f"📝 Описание: {order['description']}\n"
            f"🕒 Создан: {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=("Qabul qilish" if lang == 'uz' else "Принять"),
                    callback_data=f"accept_order_{order['id']}"
                ),
                InlineKeyboardButton(
                    text=("Bekor qilish" if lang == 'uz' else "Отклонить"),
                    callback_data=f"reject_order_{order['id']}"
                ),
                InlineKeyboardButton(
                    text=("Orqaga" if lang == 'uz' else "Назад"),
                    callback_data="pending_orders_back"
                )
            ]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)

    @router.callback_query(F.data.startswith("accept_order_"))
    async def accept_pending_order(callback: CallbackQuery, state: FSMContext):
        order_id = int(callback.data.split("_")[-1])
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        success = await accept_order(order_id, user['id'])
        if success:
            text = ("✅ Buyurtma qabul qilindi!" if lang == 'uz' else "✅ Заказ принят!")
        else:
            text = ("❌ Buyurtmani qabul qilib bo‘lmadi." if lang == 'uz' else "❌ Не удалось принять заказ.")
        await callback.answer(text, show_alert=True)
        # Optionally, refresh the pending orders list

    @router.callback_query(F.data.startswith("reject_order_"))
    async def reject_pending_order(callback: CallbackQuery, state: FSMContext):
        order_id = int(callback.data.split("_")[-1])
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        success = await reject_order(order_id, user['id'])
        if success:
            text = ("❌ Buyurtma bekor qilindi!" if lang == 'uz' else "❌ Заказ отклонён!")
        else:
            text = ("❌ Buyurtmani bekor qilib bo‘lmadi." if lang == 'uz' else "❌ Не удалось отклонить заказ.")
        await callback.answer(text, show_alert=True)
        # Optionally, refresh the pending orders list

    @router.callback_query(F.data == "pending_orders_back")
    async def back_to_pending_orders(callback: CallbackQuery, state: FSMContext):
        # Re-show the pending orders list
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        orders = await get_pending_orders()
        if orders:
            text = ("⏳ Kutilayotgan buyurtmalar:\n\n" if lang == 'uz' else "⏳ Ожидающие заказы:\n\n")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"#{order['id']} | {order['client_name']} | 🕒 {order['created_at'].strftime('%H:%M')}",
                        callback_data=f"pending_order_{order['id']}"
                    ),
                    InlineKeyboardButton(
                        text=("Qabul qilish" if lang == 'uz' else "Принять"),
                        callback_data=f"accept_order_{order['id']}"
                    )
                ] for order in orders
            ] + [[InlineKeyboardButton(text=("Orqaga" if lang == 'uz' else "Назад"), callback_data="pending_orders_back")]])
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            text = ("📭 Kutilayotgan buyurtmalar yo'q" if lang == 'uz' else "📭 Нет ожидающих заказов")
            await callback.message.edit_text(text)

    return router
