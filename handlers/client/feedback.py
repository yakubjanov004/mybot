from aiogram import Router
from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from database.base_queries import get_user_by_telegram_id, get_user_lang
from database.base_queries import create_feedback
from states.user_states import UserStates
from utils.logger import setup_logger
from loader import inline_message_manager

def get_client_feedback_router():
    logger = setup_logger('bot.client.feedback')
    router = Router()

    # Step 1: Ask for rating (1-5) via inline keyboard
    def get_rating_keyboard(lang):
        buttons = [
            [InlineKeyboardButton(text=str(i), callback_data=f"feedback_rate_{i}") for i in range(1, 6)]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @router.message(F.text.in_(["⭐️ Fikr bildirish", "⭐️ Оставить отзыв"]))
    async def start_feedback(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Iltimos, buyurtma uchun 1-5 baho bering:" if lang == 'uz' else "Пожалуйста, оцените заявку от 1 до 5:",
            reply_markup=get_rating_keyboard(lang)
        )
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        await state.set_state(UserStates.waiting_for_rating)
        await state.update_data(last_message_id=sent_message.message_id)  # Saqlash uchun message_id

    @router.callback_query(F.data.regexp(r"^feedback_rate_[1-5]$"))
    async def get_feedback_rating_callback(call: CallbackQuery, state: FSMContext):
        user = await get_user_by_telegram_id(call.from_user.id)
        lang = user.get('language', 'uz')
        rating = int(call.data.split('_')[-1])
        await state.update_data(rating=rating)
        sent_message = await call.message.answer(
            "Izoh qoldirmoqchimisiz? (Yozing yoki o'tkazib yuborish uchun /skip)" if lang == 'uz' else "Хотите оставить комментарий? (Напишите или /skip для пропуска)"
        )
        await inline_message_manager.track(call.from_user.id, sent_message.message_id)
        await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
        await state.set_state(UserStates.waiting_for_comment)
        await call.answer()

    @router.message(StateFilter(UserStates.waiting_for_comment), F.text)
    async def get_feedback_comment(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        last_message_id = data.get('last_message_id')
        # Inline tugmalarni o'chirish
        if last_message_id:
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            except Exception as e:
                logger.error(f"Inline tugmalarni o'chirishda xatolik: {str(e)}", exc_info=True)
        
        # Fikrni saqlash
        zayavka_id = data.get('zayavka_id')
        await create_feedback(
            zayavka_id=zayavka_id,
            user_id=user['id'],
            rating=data['rating'],
            comment=message.text.strip(),
            created_by=user['id']
        )
        if lang == 'uz':
            text = "Fikringiz uchun rahmat!"
        else:
            text = "Спасибо за ваш отзыв!"
        await message.answer(text)
        await state.clear()

    @router.message(StateFilter(UserStates.waiting_for_comment), F.text == "/skip")
    async def skip_feedback_comment(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        last_message_id = data.get('last_message_id')
        # Inline tugmalarni o'chirish
        if last_message_id:
            try:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            except Exception as e:
                logger.error(f"Inline tugmalarni o'chirishda xatolik: {str(e)}", exc_info=True)
        
        # Fikrni saqlash (izohsiz)
        zayavka_id = data.get('zayavka_id')
        await create_feedback(
            zayavka_id=zayavka_id,
            user_id=user['id'],
            rating=data['rating'],
            comment="",
            created_by=user['id']
        )
        if lang == 'uz':
            text = "Fikringiz uchun rahmat!"
        else:
            text = "Спасибо за ваш отзыв!"
        await message.answer(text)
        await state.clear()

    return router