from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards.manager_buttons import get_manager_main_keyboard
from states.manager_states import ManagerStates
from database.base_queries import get_user_by_telegram_id
from database.base_queries import get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.role_router import get_role_router

def get_manager_main_menu_router():
    logger = setup_logger('bot.manager.main_menu')
    router = get_role_router("manager")

    @router.message(F.text.in_(["👨‍💼 Manager", "👨‍💼 Менеджер", "👨‍💼 Menejer"]))
    async def manager_start(message: Message, state: FSMContext):
        """Manager main menu"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            await state.clear()
            user = await get_user_by_telegram_id(message.from_user.id)
            
            if not user or user['role'] != 'manager':
                lang = user.get('language', 'uz') if user else 'uz'
                text = "Sizda menejer huquqi yo'q." if lang == 'uz' else "У вас нет прав менеджера."
                await message.answer(text)
                return
            
            lang = user.get('language', 'uz')
            welcome_text = "Menejer paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель менеджера!"
            
            await message.answer(
                welcome_text,
                reply_markup=get_manager_main_keyboard(lang)
            )
            await state.set_state(ManagerStates.main_menu)
            
            logger.info(f"Manager {user['id']} accessed main menu")
            
        except Exception as e:
            logger.error(f"Error in manager_start: {str(e)}", exc_info=True)
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

    @router.message(F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
    async def manager_main_menu_handler(message: Message, state: FSMContext):
        """Handle manager main menu button"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            lang = user.get('language', 'uz')
            main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
            
            await message.answer(
                main_menu_text,
                reply_markup=get_manager_main_keyboard(lang)
            )
            if state is not None:
                await state.set_state(ManagerStates.main_menu)
            
        except Exception as e:
            logger.error(f"Error in manager main menu handler: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    return router
