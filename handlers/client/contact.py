from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from keyboards.client_buttons import get_contact_keyboard, get_main_menu_keyboard, zayavka_type_keyboard
from states.user_states import UserStates
from database.base_queries import get_user_by_telegram_id, update_user_phone, get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import answer_and_cleanup
from loader import inline_message_manager
from utils.role_router import get_role_router

def get_client_contact_router():
    logger = setup_logger('bot.client')
    router = get_role_router("client")

    @router.message(StateFilter(UserStates.waiting_for_contact), F.contact)
    async def process_contact(message: Message, state: FSMContext):
        """Kontakt ulashishni qayta ishlash"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("Foydalanuvchi topilmadi.")
                return
            
            # Foydalanuvchining telefon raqamini yangilash
            logger.info(f"Calling update_user_phone with user['id']: {user['id']} (type: {type(user['id'])}), user['telegram_id']: {user['telegram_id']} (type: {type(user['telegram_id'])}), message.from_user.id: {message.from_user.id} (type: {type(message.from_user.id)})")
            await update_user_phone(user['telegram_id'], message.contact.phone_number)
            
            # Log updated user data after phone update
            updated_user = await get_user_by_telegram_id(message.from_user.id)
            logger.info(f"After update, user data: {updated_user}")
            if not updated_user.get('phone_number'):
                logger.error(f"Phone number missing after update for user {message.from_user.id}")
            
            # Check if order_in_progress is set in FSM data
            data = await state.get_data()
            if data.get('order_in_progress'):
                # Resume order FSM
                lang = user.get('language', 'uz')
                order_type_text = (
                    "Buyurtma turini tanlang:"
                    if lang == 'uz' else
                    "Выберите тип заказа:"
                )
                sent_message = await message.answer(
                    order_type_text,
                    reply_markup=zayavka_type_keyboard(lang)
                )
                await state.update_data(order_in_progress=None)  # Clear the flag
                await state.set_state(UserStates.selecting_order_type)
                logger.info(f"Mijoz kontakti yangilandi va buyurtma jarayoni davom etmoqda: {message.from_user.id}")
                await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                return
            
            lang = user.get('language', 'uz')
            success_text = (
                "Rahmat! Endi barcha xizmatlardan foydalanishingiz mumkin."
                if lang == 'uz' else
                "Спасибо! Теперь вы можете пользоваться всеми услугами."
            )
            
            sent_message = await message.answer(
                success_text,
                reply_markup=get_main_menu_keyboard(lang)
            )
            await state.set_state(UserStates.main_menu)
            
            logger.info(f"Mijoz kontakti yangilandi: {message.from_user.id}")
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"process_contact da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "client_update_contact")
    async def client_update_contact_handler(callback: CallbackQuery, state: FSMContext):
        """Mijoz kontaktini yangilash uchun handler"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            contact_text = (
                "Yangi kontaktni yuboring."
                if lang == 'uz' else
                "Отправьте новый контакт."
            )
            sent_message = await callback.message.edit_text(contact_text, reply_markup=None)
            await state.set_state(UserStates.updating_contact)
            
            # Foydalanuvchi kontakt yuborganida inline tugmalarni o‘chirish
            @router.message(StateFilter(UserStates.updating_contact), F.contact)
            async def clear_inline_on_contact(message: Message, state: FSMContext):
                try:
                    # Oxirgi xabarning inline tugmalarni o‘chirish
                    await sent_message.bot.edit_message_reply_markup(
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id,
                        reply_markup=None
                    )
                    # Asosiy logikani saqlab qolish
                    user = await get_user_by_telegram_id(message.from_user.id)
                    if not user:
                        await message.answer("Foydalanuvchi topilmadi.")
                        return
                    
                    await update_user_phone(user['telegram_id'], message.contact.phone_number)
                    lang = user.get('language', 'uz')
                    success_text = (
                        "Kontakt yangilandi!"
                        if lang == 'uz' else
                        "Контакт обновлен!"
                    )
                    await message.answer(
                        success_text,
                        reply_markup=get_main_menu_keyboard(lang)
                    )
                    await state.set_state(UserStates.main_menu)
                    logger.info(f"Mijoz kontakti yangilandi: {message.from_user.id}")
                    await inline_message_manager.track(message.from_user.id, sent_message.message_id)
                except Exception as e:
                    logger.error(f"process_contact_update da xatolik: {str(e)}", exc_info=True)
                    lang = await get_user_lang(message.from_user.id)
                    error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
                    await message.answer(error_text)
            
        except Exception as e:
            logger.error(f"client_update_contact_handler da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(StateFilter(UserStates.updating_contact), F.contact)
    async def process_contact_update(message: Message, state: FSMContext):
        """Mijozdan yangilangan kontaktni qayta ishlash"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("Foydalanuvchi topilmadi.")
                return
            
            await update_user_phone(user['telegram_id'], message.contact.phone_number)
            lang = user.get('language', 'uz')
            success_text = (
                "Kontakt yangilandi!"
                if lang == 'uz' else
                "Контакт обновлен!"
            )
            await message.answer(
                success_text,
                reply_markup=get_main_menu_keyboard(lang)
            )
            await state.set_state(UserStates.main_menu)
            logger.info(f"Mijoz kontakti yangilandi: {message.from_user.id}")
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"process_contact_update da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    return router