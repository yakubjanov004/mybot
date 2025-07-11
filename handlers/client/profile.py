from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from keyboards.client_buttons import get_client_profile_menu, get_back_to_profile_menu, get_main_menu_keyboard, get_client_profile_edit_menu, get_cancel_edit_keyboard
from states.client_states import ProfileStates
from database.client_queries import get_client_info, get_user_zayavka_statistics
from database.base_queries import get_user_by_telegram_id, update_client_info, get_user_lang, update_user_full_name, update_user_address
from utils.logger import setup_logger
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from utils.role_checks import client_only
from loader import inline_message_manager
from utils.role_router import get_role_router

def get_client_profile_router():
    logger = setup_logger('bot.client')
    router = get_role_router("client")

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
            await state.set_state(ProfileStates.profile_menu)
            
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
            
            # Format created_at date
            created_at = user.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_date = created_at
                else:
                    created_date = created_at.strftime("%d.%m.%Y %H:%M")
            else:
                created_date = "Noma'lum"
            
            # Format updated_at date
            updated_at = user.get('updated_at')
            if updated_at:
                if isinstance(updated_at, str):
                    updated_date = updated_at
                else:
                    updated_date = updated_at.strftime("%d.%m.%Y %H:%M")
            else:
                updated_date = "Noma'lum"
            
            info_text = (
                f"👤 **Shaxsiy ma'lumotlar:**\n\n"
                f"🆔 **ID:** `{user.get('id', 'Noma\'lum')}`\n"
                f"📱 **Telegram ID:** `{user.get('telegram_id', 'Noma\'lum')}`\n"
                f"📝 **Ism:** {user.get('full_name', 'Kiritilmagan')}\n"
                f"📞 **Telefon:** {user.get('phone_number', 'Kiritilmagan')}\n"
                f"📍 **Manzil:** {user.get('address', 'Kiritilmagan')}\n"
                f"🌐 **Til:** {'O\'zbekcha' if user.get('language') == 'uz' else 'Русский'}\n"
                f"📅 **Ro'yxatdan o'tgan:** {created_date}\n"
                f"🔄 **Oxirgi yangilangan:** {updated_date}\n"
                f"✅ **Faol:** {'Ha' if user.get('is_active') else 'Yo\'q'}"
                if lang == 'uz' else
                f"👤 **Личная информация:**\n\n"
                f"🆔 **ID:** `{user.get('id', 'Неизвестно')}`\n"
                f"📱 **Telegram ID:** `{user.get('telegram_id', 'Неизвестно')}`\n"
                f"📝 **Имя:** {user.get('full_name', 'Не указано')}\n"
                f"📞 **Телефон:** {user.get('phone_number', 'Не указано')}\n"
                f"📍 **Адрес:** {user.get('address', 'Не указано')}\n"
                f"🌐 **Язык:** {'Узбекский' if user.get('language') == 'uz' else 'Русский'}\n"
                f"📅 **Зарегистрирован:** {created_date}\n"
                f"🔄 **Последнее обновление:** {updated_date}\n"
                f"✅ **Активен:** {'Да' if user.get('is_active') else 'Нет'}"
            )
            
            await callback.message.edit_text(
                info_text,
                reply_markup=get_back_to_profile_menu(lang),
                parse_mode="Markdown"
            )
            await callback.answer()
            
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
            
        except Exception as e:
            logger.error(f"handle_back_to_profile da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    # Yangi profil o'zgartirish handlerlari
    @client_only
    @router.callback_query(F.data == "client_edit_profile")
    async def handle_edit_profile(callback: CallbackQuery):
        """Profil o'zgartirish menyusini ochish"""
        try:
            lang = await get_user_lang(callback.from_user.id)
            edit_text = (
                "Profil o'zgartirish. Qaysi ma'lumotni o'zgartirmoqchisiz?"
                if lang == 'uz' else
                "Редактирование профиля. Какую информацию хотите изменить?"
            )
            
            await callback.message.edit_text(
                edit_text,
                reply_markup=get_client_profile_edit_menu(lang)
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"handle_edit_profile da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @client_only
    @router.callback_query(F.data == "client_edit_name")
    async def handle_edit_name(callback: CallbackQuery, state: FSMContext):
        """Ism o'zgartirish"""
        try:
            lang = await get_user_lang(callback.from_user.id)
            edit_text = (
                "Yangi ismingizni kiriting:"
                if lang == 'uz' else
                "Введите новое имя:"
            )
            
            await callback.message.edit_text(
                edit_text,
                reply_markup=get_cancel_edit_keyboard(lang)
            )
            await state.set_state(ProfileStates.editing_name)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"handle_edit_name da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @client_only
    @router.message(ProfileStates.editing_name)
    async def handle_name_input(message: Message, state: FSMContext):
        """Ism kiritish"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            
            new_name = message.text.strip()
            if len(new_name) < 2:
                lang = await get_user_lang(message.from_user.id)
                error_text = (
                    "Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:"
                    if lang == 'uz' else
                    "Имя слишком короткое. Пожалуйста, введите полное имя:"
                )
                sent_message = await message.answer(error_text)
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                return
            
            # Update name in database
            success = await update_user_full_name(message.from_user.id, new_name)
            
            if success:
                lang = await get_user_lang(message.from_user.id)
                success_text = (
                    f"Ism muvaffaqiyatli o'zgartirildi: {new_name}"
                    if lang == 'uz' else
                    f"Имя успешно изменено: {new_name}"
                )
                sent_message = await message.answer(success_text)
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            else:
                lang = await get_user_lang(message.from_user.id)
                error_text = (
                    "Ism o'zgartirishda xatolik yuz berdi."
                    if lang == 'uz' else
                    "Ошибка при изменении имени."
                )
                sent_message = await message.answer(error_text)
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"handle_name_input da xatolik: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
            sent_message = await message.answer(error_text)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.clear()

    @client_only
    @router.callback_query(F.data == "client_edit_address")
    async def handle_edit_address(callback: CallbackQuery, state: FSMContext):
        """Manzil o'zgartirish"""
        try:
            lang = await get_user_lang(callback.from_user.id)
            edit_text = (
                "Yangi manzilingizni kiriting:"
                if lang == 'uz' else
                "Введите новый адрес:"
            )
            
            await callback.message.edit_text(
                edit_text,
                reply_markup=get_cancel_edit_keyboard(lang)
            )
            await state.set_state(ProfileStates.editing_address)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"handle_edit_address da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @client_only
    @router.message(ProfileStates.editing_address)
    async def handle_address_input(message: Message, state: FSMContext):
        """Manzil kiritish"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            
            new_address = message.text.strip()
            if len(new_address) < 5:
                lang = await get_user_lang(message.from_user.id)
                error_text = (
                    "Manzil juda qisqa. Iltimos, to'liq manzilni kiriting:"
                    if lang == 'uz' else
                    "Адрес слишком короткий. Пожалуйста, введите полный адрес:"
                )
                sent_message = await message.answer(error_text)
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                return
            
            # Update address in database
            success = await update_user_address(message.from_user.id, new_address)
            
            if success:
                lang = await get_user_lang(message.from_user.id)
                success_text = (
                    f"Manzil muvaffaqiyatli o'zgartirildi: {new_address}"
                    if lang == 'uz' else
                    f"Адрес успешно изменен: {new_address}"
                )
                sent_message = await message.answer(success_text)
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            else:
                lang = await get_user_lang(message.from_user.id)
                error_text = (
                    "Manzil o'zgartirishda xatolik yuz berdi."
                    if lang == 'uz' else
                    "Ошибка при изменении адреса."
                )
                sent_message = await message.answer(error_text)
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"handle_address_input da xatolik: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
            sent_message = await message.answer(error_text)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.clear()

    return router
