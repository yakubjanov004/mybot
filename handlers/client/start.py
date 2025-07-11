from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.client_buttons import get_contact_keyboard, get_main_menu_keyboard, get_language_selection_keyboard
from states.client_states import StartStates
from database.base_queries import get_user_by_telegram_id, create_user, get_user_lang, update_user_language, update_user_full_name, update_user_phone
from database.admin_queries import update_user_role
from utils.logger import setup_logger
from utils.inline_cleanup import safe_delete_message
from utils.message_utils import get_main_menu_keyboard
from loader import inline_message_manager, config
from utils.role_router import get_role_router

def get_client_start_router():
    logger = setup_logger('bot.client')
    router = get_role_router("client")

    def get_welcome_message(lang: str) -> str:
        """Get welcome message in the specified language"""
        if lang == 'uz':
            return "Xush kelibsiz! Asosiy menyu quyidagicha:"
        else:
            return "Добро пожаловать! Основное меню следующее:"

    @router.message(F.text == "/start")
    async def cmd_start(message: Message, state: FSMContext):
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            await state.clear()
            
            # Check if user exists
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if user:
                # User already exists, show main menu
                lang = user.get('language', 'uz')
                phone_number = user.get('phone_number')
                
                # Check if user is admin and update role if needed
                if str(message.from_user.id) in config.ADMIN_IDS:
                    if user.get('role') != 'admin':
                        await update_user_role(message.from_user.id, 'admin', message.from_user.id)
                    role = 'admin'
                else:
                    role = user.get('role', 'client')

                if not phone_number:
                    contact_text = (
                        "Iltimos, kontaktingizni ulashing." if lang == 'uz' 
                        else "Пожалуйста, поделитесь своим контактом."
                    )
                    sent_message = await message.answer(
                        contact_text,
                        reply_markup=get_contact_keyboard(lang)
                    )
                    await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                    await state.set_state(StartStates.waiting_for_contact)
                    return

                welcome_text = get_welcome_message(lang)
                sent_message = await message.answer(
                    welcome_text,
                    reply_markup=get_main_menu_keyboard(lang, role)
                )
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                await state.clear()
            else:
                # New user - start onboarding
                welcome_text = (
                    "Xush kelibsiz! Iltimos, tilni tanlang:\n\n"
                    "Добро пожаловать! Пожалуйста, выберите язык:"
                )
                sent_message = await message.answer(
                    welcome_text,
                    reply_markup=get_language_selection_keyboard()
                )
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                await state.set_state(StartStates.selecting_language)

        except Exception as e:
            logger.error(f"cmd_start da xatolik: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
            sent_message = await message.answer(error_text)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.callback_query(F.data.startswith("select_lang_"))
    async def handle_language_selection(callback: CallbackQuery, state: FSMContext):
        try:
            selected_lang = callback.data.split("_")[-1]  # uz or ru
            
            # Create user with selected language
            role = 'admin' if str(callback.from_user.id) in config.ADMIN_IDS else 'client'
            
            user_id = await create_user(
                telegram_id=int(callback.from_user.id),
                full_name="",  # Will be filled later
                username=callback.from_user.username,
                role=role,
                language=selected_lang
            )
            
            if user_id:
                # Ask for full name
                full_name_text = (
                    "Iltimos, to'liq ismingizni kiriting:" if selected_lang == 'uz'
                    else "Пожалуйста, введите ваше полное имя:"
                )
                
                sent_message = await callback.message.edit_text(full_name_text)
                await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
                await state.set_state(StartStates.entering_full_name)
                await state.update_data(language=selected_lang)
            else:
                error_text = (
                    "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring." if selected_lang == 'uz'
                    else "Произошла ошибка. Пожалуйста, попробуйте снова."
                )
                await callback.message.edit_text(error_text)
                
        except Exception as e:
            logger.error(f"Language selection error: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(StartStates.entering_full_name)
    async def handle_full_name_input(message: Message, state: FSMContext):
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            
            full_name = message.text.strip()
            if len(full_name) < 2:
                data = await state.get_data()
                lang = data.get('language', 'uz')
                error_text = (
                    "Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:" if lang == 'uz'
                    else "Имя слишком короткое. Пожалуйста, введите полное имя:"
                )
                sent_message = await message.answer(error_text)
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                return
            
            # Update user's full name
            await update_user_full_name(message.from_user.id, full_name)
            
            # Ask for contact
            data = await state.get_data()
            lang = data.get('language', 'uz')
            contact_text = (
                "Iltimos, kontaktingizni ulashing:" if lang == 'uz'
                else "Пожалуйста, поделитесь своим контактом:"
            )
            
            sent_message = await message.answer(
                contact_text,
                reply_markup=get_contact_keyboard(lang)
            )
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.set_state(StartStates.waiting_for_contact)
            
        except Exception as e:
            logger.error(f"Full name input error: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
            sent_message = await message.answer(error_text)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.message(StartStates.waiting_for_contact, F.contact)
    async def handle_contact_received(message: Message, state: FSMContext):
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            
            # Update user's phone number
            phone_number = message.contact.phone_number
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if user:
                # Update phone number in database
                await update_user_phone(message.from_user.id, phone_number)
                
                # Show main menu
                lang = user.get('language', 'uz')
                role = user.get('role', 'client')
                
                welcome_text = get_welcome_message(lang)
                sent_message = await message.answer(
                    welcome_text,
                    reply_markup=get_main_menu_keyboard(lang, role)
                )
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                await state.clear()
            else:
                error_text = "Xatolik yuz berdi. Iltimos, /start buyrug'ini qaytadan bosing."
                sent_message = await message.answer(error_text)
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                
        except Exception as e:
            logger.error(f"Contact received error: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
            sent_message = await message.answer(error_text)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    return router
