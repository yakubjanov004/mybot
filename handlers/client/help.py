from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from keyboards.client_buttons import get_client_help_menu, get_client_help_back_inline, get_main_menu_keyboard
from states.user_states import UserStates
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import answer_and_cleanup
from loader import inline_message_manager
from utils.role_router import get_role_router

def get_client_help_router():
    logger = setup_logger('bot.client')
    router = get_role_router("client")

    @router.message(F.text.in_(["❓ Yordam", "❓ Помощь"]))
    async def client_help_handler(message: Message, state: FSMContext):
        """Mijoz uchun yordam bo'limi"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            help_text = (
                "Yordam bo'limi. Kerakli savolni tanlang."
                if lang == 'uz' else
                "Раздел помощи. Выберите нужный вопрос."
            )
            # Yangi xabar yuborish va uni saqlash
            sent_message = await message.answer(help_text, reply_markup=get_client_help_menu(lang))
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.set_state(UserStates.help_menu)
            
        except Exception as e:
            logger.error(f"client_help_handler da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    # Foydalanuvchi matn yuborganida inline tugmalarni o'chirish
    @router.message(UserStates.help_menu, F.text)
    async def clear_inline_on_text(message: Message, state: FSMContext):
        """Inline tugmalarni o'chirish va holatni tiklash"""
        try:
            # Saqlangan xabar ID sini olish
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            
            if last_message_id:
                try:
                    # Faqat inline tugmalarni o'chirish
                    await message.bot.edit_message_reply_markup(
                        chat_id=message.from_user.id,
                        message_id=last_message_id,
                        reply_markup=None
                    )
                except Exception as e:
                    logger.debug(f"Xabar o'zgartirishda xatolik: {str(e)}")
            
            await state.set_state(UserStates.main_menu)  # Holatni tiklash
            
        except Exception as e:
            logger.error(f"clear_inline_on_text da xatolik: {str(e)}", exc_info=True)
            await state.set_state(UserStates.main_menu)  # Xatolik bo'lsa ham holatni tiklash

    @router.callback_query(F.data == "client_faq")
    async def client_faq_handler(callback: CallbackQuery, state: FSMContext):
        """Tez-tez so'raladigan savollar"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            faq_text = (
                "❓ Tez-tez so'raladigan savollar:\n\n"
                "1. Qanday buyurtma beraman?\n"
                "   - 'Yangi buyurtma' tugmasini bosing\n\n"
                "2. Buyurtmam qachon bajariladi?\n"
                "   - Odatda 1-3 ish kuni ichida\n\n"
                "3. Narxlar qanday?\n"
                "   - Operator siz bilan bog'lanib narxni aytadi\n\n"
                "4. Bekor qilsam bo'ladimi?\n"
                "   - Ha, operator orqali bekor qilishingiz mumkin"
                if lang == 'uz' else
                "❓ Часто задаваемые вопросы:\n\n"
                "1. Как сделать заказ?\n"
                "   - Нажмите кнопку 'Новый заказ'\n\n"
                "2. Когда выполнят мой заказ?\n"
                "   - Обычно в течение 1-3 рабочих дней\n\n"
                "3. Какие цены?\n"
                "   - Оператор свяжется с вами и сообщит цену\n\n"
                "4. Можно ли отменить?\n"
                "   - Да, можете отменить через оператора"
            )
            sent_message = await callback.message.edit_text(faq_text, reply_markup=get_client_help_back_inline(lang))
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"client_faq_handler da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "client_how_to_order")
    async def client_how_to_order_handler(callback: CallbackQuery, state: FSMContext):
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            guide_text = (
                "📝 Qanday buyurtma berish:\n\n"
                "1️⃣ 'Yangi buyurtma' tugmasini bosing\n"
                "2️⃣ Buyurtma turini tanlang\n"
                "3️⃣ Tavsifni kiriting\n"
                "4️⃣ Manzilni kiriting\n"
                "5️⃣ Rasm biriktiring (ixtiyoriy)\n"
                "6️⃣ Geolokatsiya yuboring (ixtiyoriy)\n"
                "7️⃣ Buyurtmani tasdiqlang\n\n"
                "✅ Tayyor! Operator siz bilan bog'lanadi."
                if lang == 'uz' else
                "📝 Как сделать заказ:\n\n"
                "1️⃣ Нажмите 'Новый заказ'\n"
                "2️⃣ Выберите тип заказа\n"
                "3️⃣ Введите описание\n"
                "4️⃣ Введите адрес\n"
                "5️⃣ Прикрепите фото (по желанию)\n"
                "6️⃣ Отправьте геолокацию (по желанию)\n"
                "7️⃣ Подтвердите заказ\n\n"
                "✅ Готово! Оператор свяжется с вами."
            )
            sent_message = await callback.message.edit_text(guide_text, reply_markup=get_client_help_back_inline(lang))
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in how to order guide: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "client_track_order")
    async def client_track_order_handler(callback: CallbackQuery, state: FSMContext):
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            track_text = (
                "📍 Buyurtmani kuzatish:\n\n"
                "Buyurtmangiz holatini bilish uchun:\n"
                "• 'Mening buyurtmalarim' bo'limiga o'ting\n"
                "• Yoki operator bilan bog'laning\n\n"
                "Buyurtma holatlari:\n"
                "🆕 Yangi - qabul qilindi\n"
                "✅ Tasdiqlangan - ishga olingan\n"
                "⏳ Jarayonda - bajarilmoqda\n"
                "✅ Bajarilgan - tugallangan"
                if lang == 'uz' else
                "📍 Отслеживание заказа:\n\n"
                "Чтобы узнать статус заказа:\n"
                "• Перейдите в 'Мои заказы'\n"
                "• Или свяжитесь с оператором\n\n"
                "Статусы заказа:\n"
                "🆕 Новый - принят\n"
                "✅ Подтвержден - взят в работу\n"
                "⏳ В процессе - выполняется\n"
                "✅ Выполнен - завершен"
            )
            sent_message = await callback.message.edit_text(track_text, reply_markup=get_client_help_back_inline(lang))
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in track order: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "client_contact_support")
    async def client_contact_support_handler(callback: CallbackQuery, state: FSMContext):
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            support_text = (
                "📞 Qo'llab-quvvatlash xizmati:\n\n"
                "📱 Telefon: +998 90 123 45 67\n"
                "📧 Email: support@company.uz\n"
                "💬 Telegram: @support_bot\n\n"
                "🕐 Ish vaqti:\n"
                "Dushanba - Juma: 9:00 - 18:00\n"
                "Shanba: 9:00 - 14:00\n"
                "Yakshanba: Dam olish kuni\n\n"
                "Yoki botda xabar qoldiring!"
                if lang == 'uz' else
                "📞 Служба поддержки:\n\n"
                "📱 Телефон: +998 90 123 45 67\n"
                "📧 Email: support@company.uz\n"
                "💬 Telegram: @support_bot\n\n"
                "🕐 Рабочее время:\n"
                "Понедельник - Пятница: 9:00 - 18:00\n"
                "Суббота: 9:00 - 14:00\n"
                "Воскресенье: Выходной\n\n"
                "Или оставьте сообщение в боте!"
            )
            sent_message = await callback.message.edit_text(support_text, reply_markup=get_client_help_back_inline(lang))
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in contact support: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "client_back_help")
    async def client_back_help_handler(callback: CallbackQuery, state: FSMContext):
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            help_text = "Yordam bo'limi" if lang == 'uz' else "Раздел помощи"
            sent_message = await callback.message.edit_text(help_text, reply_markup=get_client_help_menu(lang))
            inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in client back help: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(F.text.in_(["📞 Operator bilan bog'lanish", "📞 Связаться с оператором"]))
    async def client_contact_operator_handler(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        support_text = (
            "📞 Qo'llab-quvvatlash xizmati:\n\n"
            "📱 Telefon: +998 90 123 45 67\n"
            "📧 Email: support@company.uz\n"
            "💬 Telegram: @support_bot\n\n"
            "🕐 Ish vaqti:\n"
            "Dushanba - Juma: 9:00 - 18:00\n"
            "Shanba: 9:00 - 14:00\n"
            "Yakshanba: Dam olish kuni\n\n"
            "Yoki botda xabar qoldiring!"
            if lang == 'uz' else
            "📞 Служба поддержки:\n\n"
            "📱 Телефон: +998 90 123 45 67\n"
            "📧 Email: support@company.uz\n"
            "💬 Telegram: @support_bot\n\n"
            "🕐 Рабочее время:\n"
            "Понедельник - Пятница: 9:00 - 18:00\n"
            "Суббота: 9:00 - 14:00\n"
            "Воскресенье: Выходной\n\n"
            "Или оставьте сообщение в боте!"
        )
        await message.answer(support_text)

    return router