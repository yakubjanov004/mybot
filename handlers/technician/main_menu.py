from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from keyboards.technician_buttons import get_technician_main_menu_keyboard, get_back_technician_keyboard
from states.technician_states import TechnicianStates
from keyboards.technician_buttons import get_main_menu_keyboard as get_technician_main_menu_keyboard
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages, answer_and_cleanup
from utils.get_role import get_user_role
import functools

logger = setup_logger('bot.technician.main_menu')

def get_technician_main_menu_router():
    router = Router()

    def require_technician(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                message_or_call = args[0] if args else kwargs.get('message_or_call')
                user_id = message_or_call.from_user.id
                user = await get_technician_by_telegram_id(user_id)
                if not user:
                    lang = await get_user_lang(user_id)
                    text = "Sizda montajchi huquqi yo'q." if lang == 'uz' else "У вас нет прав монтажника."
                    if hasattr(message_or_call, 'answer'):
                        await message_or_call.answer(text)
                    else:
                        await message_or_call.message.answer(text)
                    return
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in require_technician decorator: {str(e)}", exc_info=True)
                if args and hasattr(args[0], 'answer'):
                    lang = await get_user_lang(args[0].from_user.id)
                    await args[0].answer("Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!")
        return wrapper

    @router.message(Command("start"))
    async def cmd_start(message: Message, state: FSMContext):
        """Start command handler for technicians"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            await state.clear()
            
            user = await get_technician_by_telegram_id(message.from_user.id)
            logger.info(f"Technician start - User checked: {message.from_user.id}, result: {user}")
            
            if not user:
                await cleanup_user_inline_messages(message.from_user.id)
                lang = await get_user_lang(message.from_user.id)
                text = "Sizda montajchi huquqi yo'q." if lang == 'uz' else "У вас нет прав монтажника."
                await message.answer(text)
                return
            
            lang = user.get('language', 'uz')
            
            if not user.get('phone_number'):
                await cleanup_user_inline_messages(message.from_user.id)
                text = "Iltimos, kontaktingizni ulashing." if lang == 'uz' else "Пожалуйста, предоставьте свой контактный номер."
                from keyboards.technician_buttons import get_contact_keyboard
                await message.answer(text, reply_markup=get_contact_keyboard(lang))
                await state.set_state(TechnicianStates.waiting_for_phone_number)
            else:
                await cleanup_user_inline_messages(message.from_user.id)
                text = "Xush kelibsiz! Montajchi paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать! Добро пожаловать в панель монтажника!"
                await message.answer(
                    text=text,
                    reply_markup=get_technician_main_menu_keyboard(lang)
                )
                await state.set_state(TechnicianStates.main_menu)
            
            logger.info(f"Technician start command completed successfully: {message.from_user.id}")
        except Exception as e:
            logger.error(f"Error in technician start command: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            await cleanup_user_inline_messages(message.from_user.id)
            text = "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте еще раз."
            await message.answer(text)

    @router.message(F.text.in_(["Orqaga", "Назад"]))
    @require_technician
    async def handle_back(message: Message, state: FSMContext):
        """Handle back button"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
            await message.answer(
                main_menu_text,
                reply_markup=get_technician_main_menu_keyboard(lang)
            )
            await state.set_state(TechnicianStates.main_menu)
        except Exception as e:
            logger.error(f"Error in handle_back: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
    @require_technician
    async def main_menu_handler(message: Message, state: FSMContext):
        """Handle main menu button"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
            await message.answer(
                main_menu_text,
                reply_markup=get_technician_main_menu_keyboard(lang)
            )
            await state.set_state(TechnicianStates.main_menu)
        except Exception as e:
            logger.error(f"Error in main menu handler: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "tech_main_menu")
    @require_technician
    async def tech_back_to_main_menu(callback: CallbackQuery, state: FSMContext):
        """Go back to technician main menu"""
        await cleanup_user_inline_messages(callback.from_user.id)
        try:
            await answer_and_cleanup(callback)
            user = await get_technician_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
            await callback.message.edit_text(
                main_menu_text,
                reply_markup=get_technician_main_menu_keyboard(lang)
            )
            await state.set_state(TechnicianStates.main_menu)
        except Exception as e:
            logger.error(f"Error going back to main menu: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    return router
