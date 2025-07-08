from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import (
    create_feedback, get_client_feedback
)
from keyboards.feedback_buttons import (
    get_rating_keyboard,
    get_feedback_comment_keyboard,
    get_feedback_complete_keyboard
)
from states.call_center import CallCenterStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_call_center_feedback_router():
    router = get_role_router("call_center")

    @router.message(F.text.in_(["⭐️ Baholash", "⭐️ Оценка"]))
    async def reply_feedback(message: Message, state: FSMContext):
        """Request feedback from reply keyboard"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        if not data.get('client_id'):
            text = "❌ Avval mijozni tanlang" if lang == 'uz' else "❌ Сначала выберите клиента"
            await message.answer(text)
            return
        
        try:
            # Check if recent feedback exists
            recent_feedback = await get_client_feedback(data['client_id'])
            if recent_feedback and (datetime.now() - recent_feedback['created_at']).days < 7:
                text = "⚠️ Mijoz yaqinda fikr bildirgan (7 kun ichida)" if lang == 'uz' else "⚠️ Клиент недавно оставил отзыв (в течение 7 дней)"
                await message.answer(text)
                return
            
            await state.set_state(CallCenterStates.waiting_feedback)
            text = "⭐ Mijozdan baholash so'raldi" if lang == 'uz' else "⭐ Запрошена оценка от клиента"
            await message.answer(
                text,
                reply_markup=get_rating_keyboard(str(data['client_id']))
            )
            
        except Exception as e:
            logger.error(f"Error requesting feedback: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "request_feedback")
    async def request_client_feedback(callback: CallbackQuery, state: FSMContext):
        """Request feedback from client"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        if not data.get('client_id'):
            text = "Avval mijozni tanlang" if lang == 'uz' else "Сначала выберите клиента"
            await callback.answer(text, show_alert=True)
            return
        
        try:
            # Check if recent feedback exists
            recent_feedback = await get_client_feedback(data['client_id'])
            if recent_feedback and (datetime.now() - recent_feedback['created_at']).days < 7:
                text = "Mijoz yaqinda fikr bildirgan" if lang == 'uz' else "Клиент недавно оставил отзыв"
                await callback.answer(text, show_alert=True)
                return
            
            await state.set_state(CallCenterStates.waiting_feedback)
            text = "⭐ Mijozdan baholash so'raldi" if lang == 'uz' else "⭐ Запрошена оценка от клиента"
            await callback.message.edit_text(
                text,
                reply_markup=get_rating_keyboard(str(data['client_id']))
            )
            
        except Exception as e:
            logger.error(f"Error requesting feedback: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(lambda c: c.data.startswith('feedback:rate:'))
    async def process_feedback_rating(callback: CallbackQuery, state: FSMContext):
        """Process feedback rating"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        try:
            _, _, request_id, rating = callback.data.split(':')
            
            await state.update_data(feedback_rating=int(rating), feedback_client_id=request_id)
            
            text = "💬 Qo'shimcha izoh qoldirmoqchimisiz?" if lang == 'uz' else "💬 Хотите оставить комментарий?"
            await callback.message.edit_text(
                text,
                reply_markup=get_feedback_comment_keyboard(request_id)
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error processing feedback rating: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(lambda c: c.data.startswith('feedback:comment:'))
    async def start_feedback_comment(callback: CallbackQuery, state: FSMContext):
        """Start feedback comment process"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        await state.set_state(CallCenterStates.feedback_comment)
        text = "📝 Izohingizni kiriting:" if lang == 'uz' else "📝 Введите ваш комментарий:"
        await callback.message.edit_text(text)

    @router.callback_query(lambda c: c.data.startswith('feedback:skip:'))
    async def skip_feedback_comment(callback: CallbackQuery, state: FSMContext):
        """Skip feedback comment and save rating only"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        try:
            feedback_data = {
                'user_id': int(data['feedback_client_id']),
                'rating': data['feedback_rating'],
                'comment': '',
                'created_by': user['id']
            }
            
            success = await create_feedback(feedback_data)
            
            if success:
                await state.set_state(CallCenterStates.main_menu)
                text = "✅ Rahmat! Baholash saqlandi" if lang == 'uz' else "✅ Спасибо! Оценка сохранена"
                await callback.message.edit_text(
                    text,
                    reply_markup=get_feedback_complete_keyboard()
                )
            else:
                text = "❌ Baholashni saqlashda xatolik yuz berdi" if lang == 'uz' else "❌ Ошибка при сохранении оценки"
                await callback.message.edit_text(text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.message(StateFilter(CallCenterStates.feedback_comment))
    async def save_feedback_comment(message: Message, state: FSMContext):
        """Save feedback with comment"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        try:
            feedback_data = {
                'user_id': int(data['feedback_client_id']),
                'rating': data['feedback_rating'],
                'comment': message.text.strip(),
                'created_by': user['id']
            }
            
            success = await create_feedback(feedback_data)
            
            if success:
                await state.set_state(CallCenterStates.main_menu)
                text = "✅ Rahmat! Fikr-mulohaza saqlandi" if lang == 'uz' else "✅ Спасибо! Отзыв сохранен"
                await message.answer(
                    text,
                    reply_markup=get_feedback_complete_keyboard()
                )
                
                logger.info(f"Feedback saved by call center operator {user['id']} for client {data['feedback_client_id']}")
            else:
                text = "❌ Fikr-mulohazani saqlashda xatolik yuz berdi" if lang == 'uz' else "❌ Ошибка при сохранении отзыва"
                await message.answer(text)
                
        except Exception as e:
            logger.error(f"Error saving feedback with comment: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "feedback_complete")
    async def feedback_complete(callback: CallbackQuery, state: FSMContext):
        """Complete feedback process"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(CallCenterStates.main_menu)
        
        text = "📞 Call center paneliga qaytdingiz" if lang == 'uz' else "📞 Вы вернулись в панель call center"
        await callback.message.edit_text(text)
        await callback.answer()

    return router
