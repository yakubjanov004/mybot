from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards.client_buttons import get_contact_keyboard, get_main_menu_keyboard
from states.user_states import UserStates
from database.base_queries import get_user_by_telegram_id, create_user, get_user_lang
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
        user = None  # Fix: always define user before usage
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            await state.clear()
            
            # Check if user is admin and update role if needed
            if str(message.from_user.id) in config.ADMIN_IDS:
                role = 'admin'
            else:
                role = 'client'
            
            # Always check if user exists before creating
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                user_id = await create_user(
                    telegram_id=int(message.from_user.id),
                    full_name=message.from_user.full_name,
                    username=message.from_user.username,
                    role=role,  # Set role based on ADMIN_IDS
                    language='uz'  # default language
                )
                if user_id:
                    user = await get_user_by_telegram_id(message.from_user.id)
                    logger.info(f"Yangi foydalanuvchi yaratildi: {message.from_user.id}")

            if not user:
                await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
                return
            
            lang = user.get('language', 'uz')
            phone_number = user.get('phone_number')
            
            # Check if user is admin and update role if needed
            if str(message.from_user.id) in config.ADMIN_IDS:
                if user.get('role') != 'admin':
                    await update_user_role(message.from_user.id, 'admin', message.from_user.id)
                role = 'admin'
            else:
                role = user.get('role', 'client')

            current_state = await state.get_state()

            if not phone_number and current_state != UserStates.waiting_for_contact.state:
                contact_text = (
                    "Iltimos, kontaktingizni ulashing." if lang == 'uz' 
                    else "Пожалуйста, поделитесь своим контактом."
                )
                sent_message = await message.answer(
                    contact_text,
                    reply_markup=get_contact_keyboard(lang)
                )
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                await state.set_state(UserStates.waiting_for_contact)
                return

            welcome_text = get_welcome_message(lang)
            sent_message = await message.answer(
                welcome_text,
                reply_markup=get_main_menu_keyboard(lang, role)
            )
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.clear()

        except Exception as e:
            logger.error(f"cmd_start da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            sent_message = await message.answer(error_text)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    return router
