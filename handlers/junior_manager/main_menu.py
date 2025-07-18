from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards.junior_manager_buttons import get_junior_manager_main_keyboard
from database.base_queries import get_user_lang, get_user_by_telegram_id
from states.junior_manager_states import JuniorManagerMainMenuStates
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.role_router import get_role_router

def get_junior_manager_main_menu_router():
    logger = setup_logger('bot.junior_manager.main_menu')
    router = get_role_router("junior_manager")

    @router.message(F.text.in_(["/start", "🏠 Asosiy menyu", "🏠 Главное меню"]))
    async def show_main_menu(message: Message, state: FSMContext):
        """Junior Manager main menu"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'junior_manager':
                lang = user.get('language', 'uz') if user else 'uz'
                text = "Sizda kichik menejer huquqi yo'q." if lang == 'uz' else "У вас нет прав младшего менеджера."
                await message.answer(text)
                return
            
            lang = user.get('language', 'uz')
            keyboard = get_junior_manager_main_keyboard(lang)
            text = "🏠 Asosiy menyu" if lang == "uz" else "🏠 Главное меню"
            await message.answer(text, reply_markup=keyboard)
            
            if state is not None:
                await state.set_state(JuniorManagerMainMenuStates.main_menu)
            
            logger.info(f"Junior Manager {user['id']} accessed main menu")
            
        except Exception as e:
            logger.error(f"Error in junior_manager show_main_menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    # Staff application creation handler (connection requests only)
    @router.message(F.text.in_(["🔌 Ulanish arizasi yaratish", "🔌 Создать заявку на подключение"]))
    async def junior_manager_create_connection_application(message: Message, state: FSMContext):
        """Handle junior manager creating connection application"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'junior_manager':
                lang = user.get('language', 'uz') if user else 'uz'
                error_text = "Sizda kichik menejer huquqi yo'q." if lang == 'uz' else "У вас нет прав младшего менеджера."
                await message.answer(error_text)
                return
            
            lang = user.get('language', 'uz')
            logger.info(f"Junior Manager {user['id']} starting connection request creation")
            
            # Import the staff application creation handler
            from handlers.staff_application_creation import RoleBasedApplicationHandler
            app_handler = RoleBasedApplicationHandler()
            
            # Start application creation process
            result = await app_handler.start_application_creation(
                creator_role='junior_manager',
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
                "🔌 Ulanish arizasi yaratish\n\n"
                "Mijozni qanday qidirishni xohlaysiz?\n\n"
                "📱 Telefon raqami bo'yicha\n"
                "👤 Ism bo'yicha\n"
                "🆔 Mijoz ID bo'yicha\n"
                "➕ Yangi mijoz yaratish"
            ) if lang == 'uz' else (
                "🔌 Создание заявки на подключение\n\n"
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
                        callback_data="jm_client_search_phone"
                    ),
                    InlineKeyboardButton(
                        text="👤 Ism" if lang == 'uz' else "👤 Имя",
                        callback_data="jm_client_search_name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 ID" if lang == 'uz' else "🆔 ID",
                        callback_data="jm_client_search_id"
                    ),
                    InlineKeyboardButton(
                        text="➕ Yangi" if lang == 'uz' else "➕ Новый",
                        callback_data="jm_client_search_new"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                        callback_data="jm_cancel_application_creation"
                    )
                ]
            ])
            
            await message.answer(prompt_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in junior_manager_create_connection_application: {e}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    # Technical service creation is not allowed for junior managers
    @router.message(F.text.in_(["🔧 Texnik xizmat yaratish", "🔧 Создать техническую заявку"]))
    async def junior_manager_technical_service_denied(message: Message, state: FSMContext):
        """Handle junior manager attempting to create technical service (denied)"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'junior_manager':
                return
            
            lang = user.get('language', 'uz')
            logger.warning(f"Junior Manager {user['id']} attempted to create technical service (denied)")
            
            # Junior managers cannot create technical service requests
            denied_text = (
                "❌ Ruxsat rad etildi\n\n"
                "Kichik menejerlar faqat ulanish arizalarini yarata oladi.\n"
                "Texnik xizmat arizalarini yaratish uchun menejer yoki controller bilan bog'laning."
            ) if lang == 'uz' else (
                "❌ Доступ запрещен\n\n"
                "Младшие менеджеры могут создавать только заявки на подключение.\n"
                "Для создания заявок на техническое обслуживание обратитесь к менеджеру или контроллеру."
            )
            
            await message.answer(denied_text)
            
        except Exception as e:
            logger.error(f"Error in junior_manager_technical_service_denied: {e}", exc_info=True)

    return router 