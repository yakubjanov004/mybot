"""
Technician handlers for Technical Service workflow
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime

from database.models import UserRole, WorkflowType, WorkflowAction, RequestStatus
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory
from utils.logger import setup_module_logger
from database.base_queries import get_user_by_telegram_id
from states.technician_states import TechnicianTechnicalServiceStates
from utils.role_router import get_role_router

logger = setup_module_logger("technician_technical_service")

def get_technician_technical_service_router():
    """Get technician technical service router"""
    router = get_role_router("technician")
    
    # Initialize workflow components
    state_manager = StateManagerFactory.create_state_manager()
    notification_system = NotificationSystemFactory.create_notification_system()
    workflow_engine = WorkflowEngineFactory.create_workflow_engine(
        state_manager, notification_system
    )
    
    @router.message(F.text.in_(["🔧 Texnik xizmatlar", "🔧 Технические услуги"]))
    async def show_technical_assignments(message: Message):
        """Show assigned technical service requests"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                return
            
            lang = user.get('language', 'ru')
            
            # Get assigned technical service requests
            requests = await state_manager.get_requests_by_role(
                UserRole.TECHNICIAN.value,
                RequestStatus.IN_PROGRESS.value
            )
            
            # Filter for technical service requests
            technical_requests = [
                req for req in requests 
                if req.workflow_type == WorkflowType.TECHNICAL_SERVICE.value
            ]
            
            if not technical_requests:
                if lang == 'uz':
                    text = "🔧 Sizga tayinlangan texnik xizmat so'rovlari yo'q."
                else:
                    text = "🔧 У вас нет назначенных запросов технического обслуживания."
                
                await message.answer(text)
                return
            
            if lang == 'uz':
                text = f"🔧 <b>Sizning texnik xizmat vazifalaringiz ({len(technical_requests)} ta):</b>\n\n"
            else:
                text = f"🔧 <b>Ваши задачи технического обслуживания ({len(technical_requests)} шт.):</b>\n\n"
            
            for i, request in enumerate(technical_requests[:10], 1):
                priority_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🟠', 
                    'urgent': '🔴'
                }.get(request.priority, '⚪')
                
                # Determine current step
                state_data = request.state_data or {}
                if state_data.get('diagnostics_started_at'):
                    status_text = "Diagnostika" if lang == 'uz' else "Диагностика"
                    status_emoji = "🔍"
                else:
                    status_text = "Yangi" if lang == 'uz' else "Новая"
                    status_emoji = "🆕"
                
                text += (
                    f"{priority_emoji} <b>{i}. ID: {request.id[:8]}</b> {status_emoji}\n"
                    f"📝 {request.description[:50]}...\n"
                    f"📅 {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"📊 {status_text}\n\n"
                )
            
            # Create inline keyboard with requests
            keyboard = []
            for i, request in enumerate(technical_requests[:10], 1):
                state_data = request.state_data or {}
                
                if not state_data.get('diagnostics_started_at'):
                    # Can start diagnostics
                    button_text = f"{i}. Diagnostikani boshlash" if lang == 'uz' else f"{i}. Начать диагностику"
                    callback_data = f"start_technical_diagnostics_{request.id}"
                elif state_data.get('diagnostics_started_at') and not state_data.get('warehouse_decision'):
                    # Can decide on warehouse involvement
                    button_text = f"{i}. Ombor qarorini qabul qilish" if lang == 'uz' else f"{i}. Принять решение о складе"
                    callback_data = f"decide_warehouse_involvement_{request.id}"
                elif state_data.get('warehouse_decision') == 'no':
                    # Can resolve without warehouse
                    button_text = f"{i}. Muammoni hal qilish" if lang == 'uz' else f"{i}. Решить проблему"
                    callback_data = f"resolve_without_warehouse_{request.id}"
                else:
                    continue  # Skip if in warehouse workflow
                
                keyboard.append([InlineKeyboardButton(
                    text=button_text,
                    callback_data=callback_data
                )])
            
            if keyboard:
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                await message.answer(text, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await message.answer(text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error showing technical assignments: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    @router.callback_query(F.data.startswith("start_technical_diagnostics_"))
    async def start_diagnostics(callback: CallbackQuery):
        """Start technical diagnostics"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            lang = user.get('language', 'ru')
            
            # Process workflow transition
            transition_data = {
                'actor_id': user['id'],
                'diagnostics_started_at': str(datetime.now()),
                'diagnostics_notes': 'Technical diagnostics started'
            }
            
            success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.START_DIAGNOSTICS.value,
                UserRole.TECHNICIAN.value,
                transition_data
            )
            
            if success:
                if lang == 'uz':
                    text = (
                        "🔍 <b>Diagnostika boshlandi</b>\n\n"
                        "Muammoni tekshiring va ombor yordami kerakligini aniqlang:"
                    )
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="✅ Omborsiz hal qilish mumkin",
                            callback_data=f"decide_warehouse_involvement_no_{request_id}"
                        )],
                        [InlineKeyboardButton(
                            text="📦 Ombor yordami kerak",
                            callback_data=f"decide_warehouse_involvement_yes_{request_id}"
                        )]
                    ])
                else:
                    text = (
                        "🔍 <b>Диагностика начата</b>\n\n"
                        "Проверьте проблему и определите, нужна ли помощь склада:"
                    )
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="✅ Можно решить без склада",
                            callback_data=f"decide_warehouse_involvement_no_{request_id}"
                        )],
                        [InlineKeyboardButton(
                            text="📦 Нужна помощь склада",
                            callback_data=f"decide_warehouse_involvement_yes_{request_id}"
                        )]
                    ])
                
                await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
                
                logger.info(f"Technical diagnostics started for request {request_id} by technician {user['id']}")
            else:
                error_text = "Diagnostikani boshlashda xatolik!" if lang == 'uz' else "Ошибка при начале диагностики!"
                await callback.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error starting diagnostics: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    @router.callback_query(F.data.startswith("decide_warehouse_involvement_"))
    async def decide_warehouse_involvement(callback: CallbackQuery):
        """Decide on warehouse involvement"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            # Parse callback data: decide_warehouse_involvement_{yes/no}_{request_id}
            parts = callback.data.split("_")
            warehouse_needed = parts[3] == "yes"
            request_id = parts[4]
            
            lang = user.get('language', 'ru')
            
            if warehouse_needed:
                # This would transition to warehouse workflow (not implemented in this task)
                info_text = (
                    "📦 Ombor bilan ishlash workflow hali amalga oshirilmagan." 
                    if lang == 'uz' else 
                    "📦 Workflow с складом еще не реализован."
                )
                await callback.message.edit_text(info_text)
                return
            
            # Update state with warehouse decision
            transition_data = {
                'actor_id': user['id'],
                'warehouse_decision': 'no',
                'warehouse_decision_at': str(datetime.now())
            }
            
            success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value,
                UserRole.TECHNICIAN.value,
                transition_data
            )
            
            if success:
                if lang == 'uz':
                    text = (
                        "✅ <b>Omborsiz hal qilish</b>\n\n"
                        "Muammoni hal qiling va yakuniy izoh yozing:"
                    )
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="✅ Muammoni hal qildim",
                            callback_data=f"resolve_without_warehouse_{request_id}"
                        )]
                    ])
                else:
                    text = (
                        "✅ <b>Решение без склада</b>\n\n"
                        "Решите проблему и напишите итоговый комментарий:"
                    )
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="✅ Проблема решена",
                            callback_data=f"resolve_without_warehouse_{request_id}"
                        )]
                    ])
                
                await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
                
                logger.info(f"Warehouse involvement decision made for request {request_id}: {warehouse_needed}")
            else:
                error_text = "Qaror qabul qilishda xatolik!" if lang == 'uz' else "Ошибка при принятии решения!"
                await callback.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error deciding warehouse involvement: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    @router.callback_query(F.data.startswith("resolve_without_warehouse_"))
    async def resolve_without_warehouse(callback: CallbackQuery, state: FSMContext):
        """Start resolution without warehouse"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            lang = user.get('language', 'ru')
            
            # Ask for resolution comments
            await state.update_data(resolving_request_id=request_id)
            await state.set_state(TechnicianTechnicalServiceStates.entering_resolution_comments)
            
            text = (
                "📝 Bajarilgan ishlar haqida batafsil yozing:" 
                if lang == 'uz' else 
                "📝 Подробно опишите выполненные работы:"
            )
            
            await callback.message.edit_text(text)
            
        except Exception as e:
            logger.error(f"Error starting resolution without warehouse: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    @router.message(StateFilter(TechnicianTechnicalServiceStates.entering_resolution_comments))
    async def process_resolution_comments(message: Message, state: FSMContext):
        """Process technician's resolution comments"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                return
            
            data = await state.get_data()
            request_id = data.get('resolving_request_id')
            
            if not request_id:
                await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
                return
            
            resolution_comments = message.text
            lang = user.get('language', 'ru')
            
            # Complete technical service
            transition_data = {
                'actor_id': user['id'],
                'resolution_comments': resolution_comments,
                'completed_at': str(datetime.now()),
                'warehouse_involved': False
            }
            
            success = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value,
                UserRole.TECHNICIAN.value,
                transition_data
            )
            
            if success:
                if lang == 'uz':
                    success_text = (
                        f"✅ <b>Texnik xizmat yakunlandi!</b>\n\n"
                        f"📝 Bajarilgan ishlar:\n{resolution_comments}\n\n"
                        f"Mijozga bildirishnoma yuborildi."
                    )
                else:
                    success_text = (
                        f"✅ <b>Техническое обслуживание завершено!</b>\n\n"
                        f"📝 Выполненные работы:\n{resolution_comments}\n\n"
                        f"Клиенту отправлено уведомление."
                    )
                
                await message.answer(success_text, parse_mode='HTML')
                
                logger.info(f"Technical service request {request_id} completed by technician {user['id']}")
            else:
                error_text = "Yakunlashda xatolik!" if lang == 'uz' else "Ошибка при завершении!"
                await message.answer(error_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing resolution comments: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    return router