from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database.base_queries import get_user_by_telegram_id
from keyboards.call_center_buttons import rating_keyboard
from states.call_center import CallCenterDirectResolutionStates
from utils.logger import logger
from utils.role_router import get_role_router
from utils.workflow_manager import EnhancedWorkflowManager
from utils.notification_system import NotificationSystemFactory
from utils.inventory_manager import InventoryManagerFactory
from database.models import UserRole, WorkflowType

def get_call_center_client_rating_router():
    router = get_role_router("client")

    @router.message(F.text.in_(["⭐ Xizmatni baholash", "⭐ Оценить услугу"]))
    async def show_rating_requests(message: Message, state: FSMContext):
        """Show completed call center requests for rating"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'client':
            return
        
        lang = user.get('language', 'uz')
        
        try:
            # Initialize workflow manager
            notification_system = NotificationSystemFactory.create_notification_system()
            inventory_manager = InventoryManagerFactory.create_inventory_manager()
            workflow_manager = EnhancedWorkflowManager(notification_system, inventory_manager)
            
            # Get completed requests for this client
            requests = await workflow_manager.get_client_requests(user['id'])
            completed_requests = [r for r in requests if r.current_status == 'completed' and not r.completion_rating]
            
            if completed_requests:
                await state.set_state(CallCenterDirectResolutionStates.client_rating)
                
                rating_text = "⭐ Baholash uchun yakunlangan xizmatlar:" if lang == 'uz' else "⭐ Завершенные услуги для оценки:"
                text = f"{rating_text}\n\n"
                
                for request in completed_requests:
                    text += f"🆔 ID: {request.id[:8]}\n"
                    text += f"📝 Tavsif: {request.description}\n"
                    text += f"🔧 Tur: {request.workflow_type}\n"
                    text += f"✅ Yakunlangan: {request.updated_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                
                # Store requests in state for later use
                await state.update_data(rating_requests=[r.id for r in completed_requests])
                
                select_rating_text = "Xizmat sifatini baholang:" if lang == 'uz' else "Оцените качество услуги:"
                text += f"\n{select_rating_text}"
                
                await message.answer(
                    text,
                    reply_markup=rating_keyboard(lang)
                )
            else:
                no_requests_text = "Baholash uchun yakunlangan xizmatlar yo'q." if lang == 'uz' else "Нет завершенных услуг для оценки."
                await message.answer(no_requests_text)
                
        except Exception as e:
            logger.error(f"Error showing rating requests: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("rate_service_"))
    async def rate_service(callback: CallbackQuery, state: FSMContext):
        """Rate completed service"""
        rating = int(callback.data.split("_")[-1])
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'client':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        data = await state.get_data()
        rating_requests = data.get('rating_requests', [])
        
        if not rating_requests:
            no_requests_text = "Baholash uchun so'rovlar yo'q." if lang == 'uz' else "Нет запросов для оценки."
            await callback.message.edit_text(no_requests_text)
            return
        
        try:
            # Initialize workflow manager
            notification_system = NotificationSystemFactory.create_notification_system()
            inventory_manager = InventoryManagerFactory.create_inventory_manager()
            workflow_manager = EnhancedWorkflowManager(notification_system, inventory_manager)
            
            # Rate the first pending request
            request_id = rating_requests[0]
            feedback = f"Client rated the service {rating}/5 stars"
            
            success = await workflow_manager.rate_service(
                request_id, rating, feedback, user['id']
            )
            
            if success:
                star_text = "⭐" * rating
                success_text = "✅ Baholash muvaffaqiyatli yuborildi!" if lang == 'uz' else "✅ Оценка успешно отправлена!"
                text = f"{success_text}\n\n"
                text += f"🆔 So'rov ID: {request_id[:8]}\n"
                text += f"⭐ Baho: {star_text} ({rating}/5)\n\n"
                
                thanks_text = "Fikr-mulohazangiz uchun rahmat!" if lang == 'uz' else "Спасибо за ваш отзыв!"
                text += thanks_text
                
                await callback.message.edit_text(text)
                
                logger.info(f"Client {user['id']} rated request {request_id[:8]} with {rating}/5 stars")
            else:
                error_text = "❌ Baholashda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при оценке."
                await callback.message.edit_text(error_text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error rating service: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    return router