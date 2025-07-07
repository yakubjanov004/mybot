from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from keyboards.client_buttons import get_client_profile_menu, get_back_to_profile_menu, get_main_menu_keyboard
from utils.inline_cleanup import safe_remove_inline_call
from states.user_states import UserStates
from database.client_queries import get_client_info, get_user_zayavka_statistics
from database.base_queries import get_user_by_telegram_id, update_client_info, get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from utils.role_checks import client_only
from loader import inline_message_manager

def get_client_profile_router():
    logger = setup_logger('bot.client')
    router = Router()

    @client_only
    @router.message(F.text.in_(['👤 Profil', '👤 Профиль']))
    async def client_profile_handler(message: Message, state: FSMContext):
        """Mijoz profili bilan ishlash"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("Foydalanuvchi topilmadi.")
                return
            
            lang = user.get('language', 'uz')
            profile_text = (
                "Profil menyusi. Kerakli amalni tanlang."
                if lang == 'uz' else
                "Меню профиля. Выберите нужное действие."
            )
            
            sent_message = await message.answer(
                profile_text,
                reply_markup=get_client_profile_menu(lang)
            )
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.set_state(UserStates.profile_menu)
            
        except Exception as e:
            logger.error(f"client_profile_handler da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @client_only
    @router.callback_query(F.data == "client_view_info")
    async def handle_view_info(callback: CallbackQuery):
        """Mijoz ma'lumotlarini ko'rish"""
        try:
            lang = await get_user_lang(callback.from_user.id)
            user = await get_user_by_telegram_id(callback.from_user.id)
            
            if not user:
                await callback.answer("Foydalanuvchi topilmadi")
                return
            
            client_info = await get_client_info(user['id'])
            
            if client_info:
                info_text = (
                    f"👤 Shaxsiy ma'lumotlar:\n\n"
                    f"📝 Ism: {client_info.get('full_name', 'Kiritilmagan')}\n"
                    f"📞 Telefon: {client_info.get('phone_number', 'Kiritilmagan')}\n"
                    f"📍 Manzil: {client_info.get('address', 'Kiritilmagan')}\n"
                    f"🌐 Til: {'O\'zbekcha' if client_info.get('language') == 'uz' else 'Русский'}\n"
                    f"📅 Ro'yxatdan o'tgan: {client_info.get('created_at', 'Noma\'lum')}"
                    if lang == 'uz' else
                    f"👤 Личная информация:\n\n"
                    f"📝 Имя: {client_info.get('full_name', 'Не указано')}\n"
                    f"📞 Телефон: {client_info.get('phone_number', 'Не указано')}\n"
                    f"📍 Адрес: {client_info.get('address', 'Не указано')}\n"
                    f"🌐 Язык: {'Узбекский' if client_info.get('language') == 'uz' else 'Русский'}\n"
                    f"📅 Зарегистрирован: {client_info.get('created_at', 'Неизвестно')}"
                )
            else:
                info_text = "Ma'lumotlar topilmadi" if lang == 'uz' else "Информация не найдена"
            
            await callback.message.edit_text(
                info_text,
                reply_markup=get_back_to_profile_menu(lang)
            )
            await callback.answer()
            await safe_remove_inline_call(callback)
            
        except Exception as e:
            logger.error(f"handle_view_info da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @client_only
    @router.callback_query(F.data == "client_order_stats")
    async def handle_order_stats(callback: CallbackQuery):
        """Mijoz arizalar statistikasini ko'rish"""
        try:
            lang = await get_user_lang(callback.from_user.id)
            stats = await get_user_zayavka_statistics(callback.from_user.id)
            
            # If stats is an integer (error case), convert to default stats
            if isinstance(stats, int):
                stats = {
                    'new': {'weekly': 0, 'monthly': 0},
                    'in_progress': {'weekly': 0, 'monthly': 0},
                    'completed': {'weekly': 0, 'monthly': 0},
                    'cancelled': {'weekly': 0, 'monthly': 0}
                }
            
            stats_text = (
                f"📊 Arizalar statistikasi:\n"
                f"🆕 Yangi: {stats['new']['weekly']}/{stats['new']['monthly']}\n"
                f"🚧 Jarayonda: {stats['in_progress']['weekly']}/{stats['in_progress']['monthly']}\n"
                f"✅ Bajarilgan: {stats['completed']['weekly']}/{stats['completed']['monthly']}\n"
                f"❌ Bekor qilingan: {stats['cancelled']['weekly']}/{stats['cancelled']['monthly']}\n"
                if lang == 'uz' else
                f"📊 Статистика заявок:\n"
                f"🆕 Новые: {stats['new']['weekly']}/{stats['new']['monthly']}\n"
                f"🚧 В процессе: {stats['in_progress']['weekly']}/{stats['in_progress']['monthly']}\n"
                f"✅ Завершены: {stats['completed']['weekly']}/{stats['completed']['monthly']}\n"
                f"❌ Отменены: {stats['cancelled']['weekly']}/{stats['cancelled']['monthly']}\n"
            )
            
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_back_to_profile_menu(lang)
            )
            await callback.answer()
            await safe_remove_inline_call(callback)
            
        except Exception as e:
            logger.error(f"handle_order_stats da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @client_only
    @router.callback_query(F.data == "client_profile_back")
    async def handle_back_to_profile(callback: CallbackQuery):
        """Orqaga qaytish"""
        try:
            lang = await get_user_lang(callback.from_user.id)
            profile_text = (
                "Profil menyusi. Kerakli amalni tanlang."
                if lang == 'uz' else
                "Меню профиля. Выберите нужное действие."
            )
            
            await callback.message.edit_text(
                profile_text,
                reply_markup=get_client_profile_menu(lang)
            )
            await callback.answer()
            await safe_remove_inline_call(callback)
            
        except Exception as e:
            logger.error(f"handle_back_to_profile da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    return router
