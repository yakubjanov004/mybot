from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.i18n import i18n
from keyboards.client_buttons import get_main_menu_keyboard, get_language_keyboard
from states.user_states import UserStates
from database.queries import get_user_by_telegram_id, update_user_language
from utils.logger import logger

router = Router()

@router.callback_query(F.data == "language")
async def show_language_menu(callback: CallbackQuery):
    """Til tanlash menyusini ko'rsatish"""
    lang = "uz"  # TODO: Database dan olish
    text = i18n.get_message(lang, "select_language")
    keyboard = get_language_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("lang_"))
async def change_language(call: CallbackQuery, state: FSMContext):
    """Handle language change"""
    try:
        # Get new language from callback data
        new_lang = call.data.split("_")[1]
        
        # Update user's language in database
        await update_user_language(call.from_user.id, new_lang)
        
        # Send confirmation message
        await call.message.edit_text(
            i18n.get_message(new_lang, "language_changed"),
            reply_markup=None
        )
        
        # Show main menu in new language
        await call.message.answer(
            i18n.get_message(new_lang, "main_menu"),
            reply_markup=get_main_menu_keyboard(new_lang)
        )
        
        # Set state to main menu
        await state.set_state(UserStates.main_menu)
        
        # Answer callback query
        await call.answer()
        
    except Exception as e:
        logger.error(f"Tilni o'zgartirishda xatolik: {str(e)}", exc_info=True)
        await call.message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")
        await call.answer() 