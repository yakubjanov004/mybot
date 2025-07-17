"""
Controller handlers for Technical Service requests
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database.models import UserRole, WorkflowType, RequestStatus
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory
from utils.logger import setup_module_logger
from database.base_queries import get_user_by_telegram_id
from database.technician_queries import get_available_technicians
from keyboards.controllers_buttons import technical_service_assignment_keyboard
from utils.role_router import get_role_router

logger = setup_module_logger("controller_technical_service")

def get_controller_technical_service_router():
    """Get controller technical service router"""
    router = get_role_router("controller")
    
    # Initialize workflow components
    state_manager = StateManagerFactory.create_state_manager()
    notification_system = NotificationSystemFactory.create_notification_system()
    workflow_engine = WorkflowEngineFactory.create_workflow_engine(
        state_manager, notification_system
    )
    
    @router.message(F.text.in_(["🔧 Texnik xizmatlar", "🔧 Технические услуги"]))
    async def show_technical_requests(message: Message, state: FSMContext):
        """Show pending technical service requests"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != UserRole.CONTROLLER.value:
                return
            
            lang = user.get('language', 'ru')
            
            # Get pending technical service requests
            requests = await state_manager.get_requests_by_role(
                UserRole.CONTROLLER.value, 
                RequestStatus.IN_PROGRESS.value
            )
            
            # Filter for technical service requests
            technical_requests = [
                req for req in requests 
                if req.workflow_type == WorkflowType.TECHNICAL_SERVICE.value
            ]
            
            if not technical_requests:
                if lang == 'uz':
                    text = "🔧 Hozirda texnik xizmat so'rovlari yo'q."
                else:
                    text = "🔧 В настоящее время нет запросов технического обслуживания."
                
                await message.answer(text)
                return
            
            if lang == 'uz':
                text = f"🔧 <b>Texnik xizmat so'rovlari ({len(technical_requests)} ta):</b>\n\n"
            else:
                text = f"🔧 <b>Запросы технического обслуживания ({len(technical_requests)} шт.):</b>\n\n"
            
            for i, request in enumerate(technical_requests[:10], 1):
                priority_emoji = {
                    'low': '🟢',
                    'medium': '🟡', 
                    'high': '🟠',
                    'urgent': '🔴'
                }.get(request.priority, '⚪')
                
                text += (
                    f"{priority_emoji} <b>{i}. ID: {request.id[:8]}</b>\n"
                    f"📝 {request.description[:60]}...\n"
                    f"📅 {request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                )
            
            if lang == 'uz':
                text += "Texnikni tayinlash uchun so'rovni tanlang:"
            else:
                text += "Выберите запрос для назначения техника:"
            
            # Create inline keyboard with requests
            keyboard = []
            for i, request in enumerate(technical_requests[:10], 1):
                button_text = f"{i}. {request.id[:8]} - {request.description[:20]}..."
                keyboard.append([{
                    'text': button_text,
                    'callback_data': f"assign_technical_request_{request.id}"
                }])
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn['text'], callback_data=btn['callback_data'])]
                for btn in keyboard
            ])
            
            await message.answer(text, parse_mode='HTML', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing technical requests: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    @router.callback_query(F.data.startswith("assign_technical_request_"))
    async def show_technician_selection(callback: CallbackQuery):
        """Show available technicians for assignment"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.CONTROLLER.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            lang = user.get('language', 'ru')
            
            # Get request details
            request = await state_manager.get_request(request_id)
            if not request:
                error_text = "So'rov topilmadi!" if lang == 'uz' else "Запрос не найден!"
                await callback.answer(error_text)
                return
            
            # Get available technicians
            technicians = await get_available_technicians()
            
            if not technicians:
                no_tech_text = "Mavjud texniklar yo'q!" if lang == 'uz' else "Нет доступных техников!"
                await callback.answer(no_tech_text)
                return
            
            if lang == 'uz':
                text = (
                    f"🔧 <b>Texnik xizmat so'rovi</b>\n\n"
                    f"🆔 ID: {request.id[:8]}\n"
                    f"📝 Muammo: {request.description}\n"
                    f"📅 Yaratilgan: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Texnikni tanlang:"
                )
            else:
                text = (
                    f"🔧 <b>Запрос технического обслуживания</b>\n\n"
                    f"🆔 ID: {request.id[:8]}\n"
                    f"📝 Проблема: {request.description}\n"
                    f"📅 Создано: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Выберите техника:"
                )
            
            keyboard = technical_service_assignment_keyboard(request_id, technicians, lang)
            
            await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing technician selection: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    @router.callback_query(F.data.startswith("assign_technical_to_technician_"))
    async def assign_technical_to_technician(callback: CallbackQuery):
        """Assign technical request to technician"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.CONTROLLER.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            # Parse callback data: assign_technical_to_technician_{technician_id}_{request_id}
            parts = callback.data.split("_")
            technician_id = int(parts[4])
            request_id = parts[5]
            
            lang = user.get('language', 'ru')
            
            # Get technician details
            technicians = await get_available_technicians()
            technician = next((t for t in technicians if t['id'] == technician_id), None)
            
            if not technician:
                error_text = "Texnik topilmadi!" if lang == 'uz' else "Техник не найден!"
                await callback.answer(error_text)
                return
            
            # Process workflow transition
            from database.models import WorkflowAction
            transition_data = {
                'technician_id': technician_id,
                'actor_id': user['id'],
                'assigned_at': str(datetime.now()),
                'technician_name': technician['full_name']
            }
            
            success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                UserRole.CONTROLLER.value,
                transition_data
            )
            
            if success:
                if lang == 'uz':
                    success_text = (
                        f"✅ <b>Texnik tayinlandi!</b>\n\n"
                        f"👨‍🔧 Texnik: {technician['full_name']}\n"
                        f"🆔 So'rov ID: {request_id[:8]}\n\n"
                        f"Texnikga bildirishnoma yuborildi."
                    )
                else:
                    success_text = (
                        f"✅ <b>Техник назначен!</b>\n\n"
                        f"👨‍🔧 Техник: {technician['full_name']}\n"
                        f"🆔 ID запроса: {request_id[:8]}\n\n"
                        f"Технику отправлено уведомление."
                    )
                
                await callback.message.edit_text(success_text, parse_mode='HTML')
                
                logger.info(f"Technical request {request_id} assigned to technician {technician_id} by controller {user['id']}")
            else:
                error_text = "Tayinlashda xatolik!" if lang == 'uz' else "Ошибка при назначении!"
                await callback.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error assigning technical to technician: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    return router