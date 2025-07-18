from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import get_call_center_dashboard_stats
from keyboards.call_center_buttons import call_center_main_menu_reply
from states.call_center import CallCenterMainMenuStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_call_center_main_menu_router():
    router = get_role_router("call_center")

    @router.message(F.text.in_(["📞 Call Center", " Колл-центр"]))
    async def call_center_start(message: Message, state: FSMContext):
        """Call center main menu"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        await state.set_state(CallCenterMainMenuStates.main_menu)
        lang = user.get('language', 'uz')
        
        # Get dashboard statistics
        try:
            stats = await get_call_center_dashboard_stats()
            
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            
            # Dashboard info
            calls_text = "Bugungi qo'ng'iroqlar" if lang == 'uz' else "Звонки сегодня"
            orders_text = "Bugungi buyurtmalar" if lang == 'uz' else "Заказы сегодня"
            pending_text = "Kutilayotgan" if lang == 'uz' else "Ожидающие"
            chats_text = "Faol chatlar" if lang == 'uz' else "Активные чаты"
            conversion_text = "Konversiya" if lang == 'uz' else "Конверсия"
            
            dashboard_text = f"\n\n📊 Dashboard:\n"
            dashboard_text += f"📞 {calls_text}: {stats.get('calls_today', 0)}\n"
            dashboard_text += f"📋 {orders_text}: {stats.get('orders_today', 0)}\n"
            dashboard_text += f"⏳ {pending_text}: {stats.get('pending_callbacks', 0)}\n"
            dashboard_text += f"💬 {chats_text}: {stats.get('active_chats', 0)}\n"
            dashboard_text += f"🎯 {conversion_text}: {stats.get('conversion_rate', 0)}%"
            
            full_text = welcome_text + dashboard_text
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            full_text = welcome_text
        
        await message.answer(
            full_text,
            reply_markup=call_center_main_menu_reply(user['language'])
        )

    @router.callback_query(F.data == "call_center_back")
    async def call_center_back(callback: CallbackQuery, state: FSMContext):
        """Go back to call center main menu"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(CallCenterMainMenuStates.main_menu)
        
        try:
            stats = await get_call_center_dashboard_stats()
            
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            
            # Dashboard info
            calls_text = "Bugungi qo'ng'iroqlar" if lang == 'uz' else "Звонки сегодня"
            orders_text = "Bugungi buyurtmalar" if lang == 'uz' else "Заказы сегодня"
            pending_text = "Kutilayotgan" if lang == 'uz' else "Ожидающие"
            chats_text = "Faol chatlar" if lang == 'uz' else "Активные чаты"
            conversion_text = "Konversiya" if lang == 'uz' else "Конверсия"
            
            dashboard_text = f"\n\n📊 Dashboard:\n"
            dashboard_text += f"📞 {calls_text}: {stats.get('calls_today', 0)}\n"
            dashboard_text += f"📋 {orders_text}: {stats.get('orders_today', 0)}\n"
            dashboard_text += f"⏳ {pending_text}: {stats.get('pending_callbacks', 0)}\n"
            dashboard_text += f"💬 {chats_text}: {stats.get('active_chats', 0)}\n"
            dashboard_text += f"🎯 {conversion_text}: {stats.get('conversion_rate', 0)}%"
            
            full_text = welcome_text + dashboard_text
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            full_text = welcome_text
        
        await callback.message.edit_text(full_text)
        await callback.answer()

    @router.callback_query(F.data == "cc_back_main")
    async def call_center_back_to_main(callback: CallbackQuery, state: FSMContext):
        """Go back to call center main menu"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(CallCenterMainMenuStates.main_menu)
        
        try:
            stats = await get_call_center_dashboard_stats()
            
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            
            # Dashboard info
            calls_text = "Bugungi qo'ng'iroqlar" if lang == 'uz' else "Звонки сегодня"
            orders_text = "Bugungi buyurtmalar" if lang == 'uz' else "Заказы сегодня"
            pending_text = "Kutilayotgan" if lang == 'uz' else "Ожидающие"
            chats_text = "Faol chatlar" if lang == 'uz' else "Активные чаты"
            conversion_text = "Konversiya" if lang == 'uz' else "Конверсия"
            
            dashboard_text = f"\n\n📊 Dashboard:\n"
            dashboard_text += f"📞 {calls_text}: {stats.get('calls_today', 0)}\n"
            dashboard_text += f"📋 {orders_text}: {stats.get('orders_today', 0)}\n"
            dashboard_text += f"⏳ {pending_text}: {stats.get('pending_callbacks', 0)}\n"
            dashboard_text += f"💬 {chats_text}: {stats.get('active_chats', 0)}\n"
            dashboard_text += f"🎯 {conversion_text}: {stats.get('conversion_rate', 0)}%"
            
            full_text = welcome_text + dashboard_text
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            welcome_text = "📞 Call center paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель call center!"
            full_text = welcome_text
        
        await callback.message.edit_text(full_text)
        await callback.answer()

    @router.callback_query(F.data == "pending_calls")
    async def show_pending_calls(callback: CallbackQuery, state: FSMContext):
        """Show pending calls and callbacks"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        try:
            from database.call_center_queries import get_pending_calls
            pending_calls = await get_pending_calls()
            
            pending_text = "⏳ Kutilayotgan qo'ng'iroqlar" if lang == 'uz' else "⏳ Ожидающие звонки"
            text = f"{pending_text}\n\n"
            
            if pending_calls:
                for call in pending_calls:
                    text += f"📞 {call['phone_number']}"
                    if call.get('client_name'):
                        text += f" - {call['client_name']}"
                    text += f"\n⏰ {call['created_at'].strftime('%H:%M')}\n"
                    if call.get('notes'):
                        text += f"📝 {call['notes']}\n"
                    text += "\n"
            else:
                no_calls_text = "Kutilayotgan qo'ng'iroqlar yo'q." if lang == 'uz' else "Ожидающих звонков нет."
                text += no_calls_text
            
            await callback.message.edit_text(text)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error getting pending calls: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    # Staff application creation handlers
    @router.message(F.text.in_(["🔌 Ulanish arizasi yaratish", "🔌 Создать заявку на подключение"]))
    async def call_center_create_connection_application(message: Message, state: FSMContext):
        """Handle call center creating connection application"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'call_center':
                lang = user.get('language', 'uz') if user else 'uz'
                error_text = "Sizda call center huquqi yo'q." if lang == 'uz' else "У вас нет прав call-центра."
                await message.answer(error_text)
                return
            
            lang = user.get('language', 'uz')
            logger.info(f"Call Center {user['id']} starting connection request creation")
            
            # Import the staff application creation handler
            from handlers.staff_application_creation import RoleBasedApplicationHandler
            app_handler = RoleBasedApplicationHandler()
            
            # Start application creation process
            result = await app_handler.start_application_creation(
                creator_role='call_center',
                creator_id=user['id'],
                application_type='connection_request'
            )
            
            if not result['success']:
                error_msg = result.get('error_message', 'Unknown error')
                if result.get('error_type') == 'permission_denied':
                    error_text = (
                        f"Ruxsat rad etildi: {error_msg}" if lang == 'uz' 
                        else f"Доступ запрещен: {error_msg}"
                    )
                else:
                    error_text = (
                        f"Xatolik yuz berdi: {error_msg}" if lang == 'uz'
                        else f"Произошла ошибка: {error_msg}"
                    )
                await message.answer(error_text)
                return
            
            # Store creator context in FSM data
            from states.staff_application_states import StaffApplicationStates
            await state.update_data(
                creator_context=result['creator_context'],
                application_type='connection_request'
            )
            
            # Set initial state and prompt for client selection
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
            prompt_text = (
                "📞 Call Center: Ulanish arizasi yaratish\n\n"
                "Mijoz bilan telefon orqali gaplashayotgan vaqtda ariza yaratish.\n\n"
                "Mijozni qanday qidirishni xohlaysiz?\n\n"
                "📱 Telefon raqami bo'yicha\n"
                "👤 Ism bo'yicha\n"
                "🆔 Mijoz ID bo'yicha\n"
                "➕ Yangi mijoz yaratish"
            ) if lang == 'uz' else (
                "📞 Call-центр: Создание заявки на подключение\n\n"
                "Создание заявки во время разговора с клиентом по телефону.\n\n"
                "Как вы хотите найти клиента?\n\n"
                "📱 По номеру телефона\n"
                "👤 По имени\n"
                "🆔 По ID клиента\n"
                "➕ Создать нового клиента"
            )
            
            # Create inline keyboard for client search options
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Telefon" if lang == 'uz' else "📱 Телефон",
                        callback_data="cc_client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data="cc_client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data="cc_client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data="cc_client_search_new"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data="cc_cancel_application_creation"
                    )
                ]
            ])
            
            await message.answer(prompt_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in call_center_create_connection_application: {e}", exc_info=True)
            from database.base_queries import get_user_lang
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(["🔧 Texnik xizmat yaratish", "🔧 Создать техническую заявку"]))
    async def call_center_create_technical_application(message: Message, state: FSMContext):
        """Handle call center creating technical service application"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'call_center':
                lang = user.get('language', 'uz') if user else 'uz'
                error_text = "Sizda call center huquqi yo'q." if lang == 'uz' else "У вас нет прав call-центра."
                await message.answer(error_text)
                return
            
            lang = user.get('language', 'uz')
            logger.info(f"Call Center {user['id']} starting technical service creation")
            
            # Import the staff application creation handler
            from handlers.staff_application_creation import RoleBasedApplicationHandler
            app_handler = RoleBasedApplicationHandler()
            
            # Start application creation process
            result = await app_handler.start_application_creation(
                creator_role='call_center',
                creator_id=user['id'],
                application_type='technical_service'
            )
            
            if not result['success']:
                error_msg = result.get('error_message', 'Unknown error')
                if result.get('error_type') == 'permission_denied':
                    error_text = (
                        f"Ruxsat rad etildi: {error_msg}" if lang == 'uz' 
                        else f"Доступ запрещен: {error_msg}"
                    )
                else:
                    error_text = (
                        f"Xatolik yuz berdi: {error_msg}" if lang == 'uz'
                        else f"Произошла ошибка: {error_msg}"
                    )
                await message.answer(error_text)
                return
            
            # Store creator context in FSM data
            from states.staff_application_states import StaffApplicationStates
            await state.update_data(
                creator_context=result['creator_context'],
                application_type='technical_service'
            )
            
            # Set initial state and prompt for client selection
            await state.set_state(StaffApplicationStates.selecting_client_search_method)
            
            prompt_text = (
                "📞 Call Center: Texnik xizmat arizasi yaratish\n\n"
                "Mijoz bilan telefon orqali gaplashayotgan vaqtda texnik muammo uchun ariza yaratish.\n\n"
                "Mijozni qanday qidirishni xohlaysiz?\n\n"
                "📱 Telefon raqami bo'yicha\n"
                "👤 Ism bo'yicha\n"
                "🆔 Mijoz ID bo'yicha\n"
                "➕ Yangi mijoz yaratish"
            ) if lang == 'uz' else (
                "📞 Call-центр: Создание заявки на техническое обслуживание\n\n"
                "Создание заявки на техническую проблему во время разговора с клиентом.\n\n"
                "Как вы хотите найти клиента?\n\n"
                "📱 По номеру телефона\n"
                "👤 По имени\n"
                "🆔 По ID клиента\n"
                "➕ Создать нового клиента"
            )
            
            # Create inline keyboard for client search options
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📱 Telefon" if lang == 'uz' else "📱 Телефон",
                        callback_data="cc_client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data="cc_client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data="cc_client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data="cc_client_search_new"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data="cc_cancel_application_creation"
                    )
                ]
            ])
            
            await message.answer(prompt_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in call_center_create_technical_application: {e}", exc_info=True)
            from database.base_queries import get_user_lang
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    return router
