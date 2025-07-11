from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.technician_buttons import get_back_technician_keyboard
from states.technician_states import TechnicianProfileStates
from database.technician_queries import get_technician_by_telegram_id
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.logger import setup_logger
from utils.role_router import get_role_router
import functools

def get_technician_profile_router():
    logger = setup_logger('bot.technician.profile')
    router = get_role_router("technician")

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

    @router.message(lambda message: message.text in ["👤 Profil", "👤 Профиль"])
    @require_technician
    async def show_profile(message: Message, state: FSMContext):
        """Show technician's profile information"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            # Format profile information
            full_name = user.get('full_name', '')
            phone = user.get('phone', '')
            
            text = f"👤 Profil ma'lumotlari:\n\n" \
                  f"👤 To'liq ism: {full_name}\n" \
                  f"📱 Telefon raqam: {phone}"
            
            await message.answer(text, reply_markup=get_back_technician_keyboard(lang))
            await state.set_state(TechnicianProfileStates.profile)
        except Exception as e:
            logger.error(f"Error in show_profile: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            await message.answer("Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!")

    return router