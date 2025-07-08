from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import get_manager_main_keyboard
from database.base_queries import update_user_language
from database.base_queries import get_user_by_telegram_id
from database.base_queries import get_user_lang
from utils.logger import setup_logger
from utils.role_router import get_role_router

def get_manager_language_router():
    logger = setup_logger('bot.manager.language')
    router = get_role_router("manager")

    @router.message(F.text.in_(['🌐 Tilni o\'zgartirish', '🌐 Изменить язык']))
    async def change_manager_language(message: Message, state: FSMContext):
        """Change manager language"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            current_lang = user.get('language', 'uz')
            
            # Create language selection keyboard
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🇺🇿 O'zbekcha" + (" ✅" if current_lang == 'uz' else ""),
                        callback_data="manager_lang_uz"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🇷🇺 Русский" + (" ✅" if current_lang == 'ru' else ""),
                        callback_data="manager_lang_ru"
                    )
                ]
            ])
            
            lang_text = (
                "🌐 Tilni tanlang:\n\nJoriy til: O'zbekcha"
                if current_lang == 'uz' else
                "🌐 Выберите язык:\n\nТекущий язык: Русский"
            )
            
            await message.answer(lang_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in change_manager_language: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("manager_lang_"))
    async def set_manager_language(callback: CallbackQuery, state: FSMContext):
        """Set manager language"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            new_lang = callback.data.replace("manager_lang_", "")
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != 'manager':
                await callback.answer("Ruxsat yo'q", show_alert=True)
                return
            
            # Update language in database
            success = await update_user_language(user['id'], new_lang)
            
            if success:
                if new_lang == 'uz':
                    success_text = (
                        "✅ Til muvaffaqiyatli o'zgartirildi!\n\n"
                        "🇺🇿 Joriy til: O'zbekcha"
                    )
                    await callback.message.edit_text(success_text)
                    
                    # Show main menu in new language
                    await callback.message.answer(
                        "Menejer paneliga xush kelibsiz!",
                        reply_markup=get_manager_main_keyboard('uz')
                    )
                else:
                    success_text = (
                        "✅ Язык успешно изменен!\n\n"
                        "🇷🇺 Текущий язык: Русский"
                    )
                    await callback.message.edit_text(success_text)
                    
                    # Show main menu in new language
                    await callback.message.answer(
                        "Добро пожаловать в панель менеджера!",
                        reply_markup=get_manager_main_keyboard('ru')
                    )
                
                logger.info(f"Manager {user['id']} changed language to {new_lang}")
            else:
                error_text = "Tilni o'zgartirishda xatolik yuz berdi." if new_lang == 'uz' else "Ошибка при изменении языка."
                await callback.message.edit_text(error_text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in set_manager_language: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    return router
