"""
Client Rating System for Completed Requests
Handles 1-5 star rating system for completed service requests
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from typing import Optional

from database.models import UserRole
from utils.workflow_manager import EnhancedWorkflowManager
from utils.logger import setup_module_logger
from database.base_queries import get_user_by_telegram_id
from loader import bot

logger = setup_module_logger("client_rating")

class ClientRatingHandler:
    """Handles client rating functionality"""
    
    def __init__(self):
        self.workflow_manager = EnhancedWorkflowManager()
        self.router = Router()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup rating handlers"""
        
        @self.router.callback_query(F.data.startswith("rate_service_"))
        async def show_rating_options(callback: CallbackQuery):
            """Show rating options to client"""
            try:
                request_id = callback.data.split("_")[-1]
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                if user.get('role') != UserRole.CLIENT.value:
                    await callback.answer("❌ Sizda bu amalni bajarish huquqi yo'q!")
                    return
                
                # Create rating keyboard (1-5 stars)
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="⭐", callback_data=f"rating_{request_id}_1"),
                            InlineKeyboardButton(text="⭐⭐", callback_data=f"rating_{request_id}_2"),
                            InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rating_{request_id}_3"),
                        ],
                        [
                            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rating_{request_id}_4"),
                            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rating_{request_id}_5"),
                        ]
                    ]
                )
                
                lang = user.get('language', 'uz')
                message_text = (
                    f"Xizmat sifatini baholang:\nAriza ID: {request_id[:8]}"
                    if lang == 'uz' else
                    f"Оцените качество обслуживания:\nID заявки: {request_id[:8]}"
                )
                
                await callback.message.edit_text(
                    message_text,
                    reply_markup=keyboard
                )
                
            except Exception as e:
                logger.error(f"Error in show_rating_options: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
        
        @self.router.callback_query(F.data.startswith("rating_"))
        async def handle_rating(callback: CallbackQuery, state: FSMContext):
            """Handle rating selection"""
            try:
                parts = callback.data.split("_")
                request_id = parts[1]
                rating = int(parts[2])
                
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                # Store rating and request ID for feedback
                await state.update_data(request_id=request_id, rating=rating)
                
                lang = user.get('language', 'uz')
                
                # Ask for optional feedback
                feedback_keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            text="✍️ Izoh qoldirish" if lang == 'uz' else "✍️ Оставить комментарий",
                            callback_data=f"add_feedback_{request_id}"
                        )],
                        [InlineKeyboardButton(
                            text="✅ Baholashni yakunlash" if lang == 'uz' else "✅ Завершить оценку",
                            callback_data=f"finish_rating_{request_id}"
                        )]
                    ]
                )
                
                rating_stars = "⭐" * rating
                message_text = (
                    f"Rahmat! Sizning bahoyingiz: {rating_stars}\n\n"
                    "Qo'shimcha izoh qoldirmoqchimisiz?"
                    if lang == 'uz' else
                    f"Спасибо! Ваша оценка: {rating_stars}\n\n"
                    "Хотите оставить дополнительный комментарий?"
                )
                
                await callback.message.edit_text(
                    message_text,
                    reply_markup=feedback_keyboard
                )
                
            except Exception as e:
                logger.error(f"Error in handle_rating: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
        
        @self.router.callback_query(F.data.startswith("add_feedback_"))
        async def add_feedback(callback: CallbackQuery, state: FSMContext):
            """Request feedback text"""
            try:
                request_id = callback.data.split("_")[-1]
                user = await get_user_by_telegram_id(callback.from_user.id)
                lang = user.get('language', 'uz')
                
                await callback.message.edit_text(
                    "Izohingizni yozing:" if lang == 'uz' else "Напишите ваш комментарий:"
                )
                await state.set_state("waiting_feedback")
                
            except Exception as e:
                logger.error(f"Error in add_feedback: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
        
        @self.router.message(StateFilter("waiting_feedback"))
        async def get_feedback_text(message: Message, state: FSMContext):
            """Get feedback text and complete rating"""
            try:
                data = await state.get_data()
                request_id = data.get('request_id')
                rating = data.get('rating')
                feedback = message.text
                
                user = await get_user_by_telegram_id(message.from_user.id)
                
                # Submit rating with feedback
                success = await self.workflow_manager.rate_service(
                    request_id, rating, feedback, user['id']
                )
                
                if success:
                    lang = user.get('language', 'uz')
                    success_msg = (
                        f"✅ Rahmat! Sizning bahoyingiz va izohingiz saqlandi.\n"
                        f"Ariza ID: {request_id[:8]}"
                        if lang == 'uz' else
                        f"✅ Спасибо! Ваша оценка и комментарий сохранены.\n"
                        f"ID заявки: {request_id[:8]}"
                    )
                    
                    await message.answer(success_msg)
                    logger.info(f"Rating {rating} and feedback submitted for request {request_id}")
                else:
                    await message.answer("❌ Xatolik yuz berdi!")
                
                await state.clear()
                
            except Exception as e:
                logger.error(f"Error in get_feedback_text: {e}", exc_info=True)
                await message.answer("❌ Xatolik yuz berdi!")
                await state.clear()
        
        @self.router.callback_query(F.data.startswith("finish_rating_"))
        async def finish_rating(callback: CallbackQuery, state: FSMContext):
            """Finish rating without additional feedback"""
            try:
                request_id = callback.data.split("_")[-1]
                data = await state.get_data()
                rating = data.get('rating')
                
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                # Submit rating without feedback
                success = await self.workflow_manager.rate_service(
                    request_id, rating, "", user['id']
                )
                
                if success:
                    lang = user.get('language', 'uz')
                    success_msg = (
                        f"✅ Rahmat! Sizning bahoyingiz saqlandi.\n"
                        f"Ariza ID: {request_id[:8]}"
                        if lang == 'uz' else
                        f"✅ Спасибо! Ваша оценка сохранена.\n"
                        f"ID заявки: {request_id[:8]}"
                    )
                    
                    await callback.message.edit_text(success_msg)
                    logger.info(f"Rating {rating} submitted for request {request_id}")
                else:
                    await callback.answer("❌ Xatolik yuz berdi!")
                
                await state.clear()
                
            except Exception as e:
                logger.error(f"Error in finish_rating: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
                await state.clear()
    
    def get_router(self) -> Router:
        """Get the rating router"""
        return self.router


# Create global instance
client_rating_handler = ClientRatingHandler()

def get_client_rating_router() -> Router:
    """Get client rating router"""
    return client_rating_handler.get_router()