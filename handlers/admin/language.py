from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from functools import wraps
import logging

from database.admin_queries import is_admin, log_admin_action
from database.base_queries import update_user_language, get_user_by_telegram_id, get_user_lang
from keyboards.admin_buttons import language_keyboard, get_admin_main_menu
from utils.inline_cleanup import safe_delete_message, answer_and_cleanup
from utils.logger import setup_logger
from utils.role_router import get_role_router
from utils.role_checks import admin_only

# Setup logger
logger = setup_logger('bot.admin.language')

def get_admin_language_router():
    router = get_role_router("admin")

    @router.message(F.text.in_(["🌐 Til sozlamalari", "🌐 Языковые настройки"]))
    @admin_only
    async def admin_language_settings(message: Message):
        """Admin language settings"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            if lang == 'uz':
                text = (
                    f"🌐 <b>Admin til sozlamalari</b>\n\n"
                    f"Joriy til: <b>O'zbek tili</b> 🇺🇿\n\n"
                    f"Admin panel tilini o'zgartirish uchun\n"
                    f"quyidagi tugmalardan birini tanlang:"
                )
            else:
                text = (
                    f"🌐 <b>Языковые настройки администратора</b>\n\n"
                    f"Текущий язык: <b>Русский язык</b> 🇷🇺\n\n"
                    f"Для изменения языка панели администратора\n"
                    f"выберите одну из кнопок ниже:"
                )
            
            await message.answer(
                text,
                reply_markup=language_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in admin language settings: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.callback_query(F.data.in_(["lang_uz", "lang_ru"]))
    @admin_only
    async def change_admin_language(call: CallbackQuery):
        """Change admin language"""
        try:
            await answer_and_cleanup(call, cleanup_after=True)
            new_lang = call.data.split("_")[1]  # uz or ru
            user_id = call.from_user.id
            # Update user language
            success = await update_user_language(user_id, new_lang)
            if success:
                # Log admin action
                await log_admin_action(user_id, "change_language", {"new_language": new_lang})
                if new_lang == 'uz':
                    text = (
                        f"✅ <b>Til muvaffaqiyatli o'zgartirildi!</b>\n\n"
                        f"🇺🇿 Admin panel endi O'zbek tilida ishlaydi.\n\n"
                        f"Barcha menyu va xabarlar O'zbek tilida\n"
                        f"ko'rsatiladi."
                    )
                else:
                    text = (
                        f"✅ <b>Язык успешно изменен!</b>\n\n"
                        f"🇷🇺 Панель администратора теперь работает на русском языке.\n\n"
                        f"Все меню и сообщения будут отображаться\n"
                        f"на русском языке."
                    )
                await call.message.edit_text(text)
                # Send new reply keyboard in the new language
                await call.message.answer(
                    "Asosiy menyu yangilandi." if new_lang == 'uz' else "Главное меню обновлено.",
                    reply_markup=get_admin_main_menu(new_lang)
                )
                await call.answer("Til o'zgartirildi!" if new_lang == 'uz' else "Язык изменен!")
            else:
                current_lang = await get_user_lang(user_id)
                error_text = "Tilni o'zgartirishda xatolik yuz berdi." if current_lang == 'uz' else "Ошибка при изменении языка."
                await call.message.edit_text(error_text)
                await call.answer("Xatolik!" if current_lang == 'uz' else "Ошибка!")
        except Exception as e:
            logger.error(f"Error changing admin language: {e}")
            current_lang = await get_user_lang(call.from_user.id)
            await call.answer("Xatolik yuz berdi." if current_lang == 'uz' else "Произошла ошибка!")

    @router.message(F.text.in_(["🔄 Tilni qayta tiklash", "🔄 Сбросить язык"]))
    @admin_only
    async def reset_admin_language(message: Message):
        """Reset admin language to default"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user_id = message.from_user.id
            
            # Reset to Uzbek (default)
            success = await update_user_language(user_id, 'uz')
            
            if success:
                # Log admin action
                await log_admin_action(user_id, "reset_language", {"reset_to": "uz"})
                
                text = (
                    f"🔄 <b>Til standart holatga qaytarildi!</b>\n\n"
                    f"🇺🇿 Admin panel endi O'zbek tilida (standart)\n"
                    f"ishlaydi.\n\n"
                    f"Kerak bo'lsa, tilni qayta o'zgartirishingiz mumkin."
                )
                
                await message.answer(text)
            else:
                lang = await get_user_lang(user_id)
                error_text = "Tilni qayta tiklashda xatolik." if lang == 'uz' else "Ошибка при сбросе языка."
                await message.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error resetting admin language: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["📊 Til statistikasi", "📊 Языковая статистика"]))
    @admin_only
    async def language_statistics(message: Message):
        """Show language usage statistics"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # This would require a database query to get language statistics
            # For now, showing placeholder data
            
            if lang == 'uz':
                text = (
                    f"📊 <b>Til statistikasi</b>\n\n"
                    f"🇺🇿 <b>O'zbek tili:</b>\n"
                    f"• Foydalanuvchilar: <b>85%</b>\n"
                    f"• Adminlar: <b>90%</b>\n"
                    f"• Texniklar: <b>95%</b>\n\n"
                    f"🇷🇺 <b>Rus tili:</b>\n"
                    f"• Foydalanuvchilar: <b>15%</b>\n"
                    f"• Adminlar: <b>10%</b>\n"
                    f"• Texniklar: <b>5%</b>\n\n"
                    f"📈 <b>Tendentsiyalar:</b>\n"
                    f"• O'zbek tili foydalanuvchilari ko'paymoqda\n"
                    f"• Rus tili barqaror holatda\n\n"
                    f"💡 <b>Tavsiya:</b>\n"
                    f"O'zbek tilidagi kontentni rivojlantirish\n"
                    f"tavsiya etiladi."
                )
            else:
                text = (
                    f"📊 <b>Языковая статистика</b>\n\n"
                    f"🇺🇿 <b>Узбекский язык:</b>\n"
                    f"• Пользователи: <b>85%</b>\n"
                    f"• Администраторы: <b>90%</b>\n"
                    f"• Техники: <b>95%</b>\n\n"
                    f"🇷🇺 <b>Русский язык:</b>\n"
                    f"• Пользователи: <b>15%</b>\n"
                    f"• Администраторы: <b>10%</b>\n"
                    f"• Техники: <b>5%</b>\n\n"
                    f"📈 <b>Тенденции:</b>\n"
                    f"• Пользователи узбекского языка растут\n"
                    f"• Русский язык в стабильном состоянии\n\n"
                    f"💡 <b>Рекомендация:</b>\n"
                    f"Рекомендуется развивать контент\n"
                    f"на узбекском языке."
                )
            
            await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error showing language statistics: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    return router
