"""
Workflow Integration Handler
Provides handlers that integrate existing role-based handlers with the workflow system
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from typing import Optional, Dict, Any

from database.models import UserRole, WorkflowType, WorkflowAction
from database.base_queries import get_user_by_telegram_id, get_users_by_role
from utils.workflow_integration import WorkflowIntegration, create_workflow_request, transition_workflow
from utils.logger import setup_module_logger
from keyboards.workflow_buttons import (
    workflow_action_keyboard, user_selection_keyboard, 
    workflow_request_details_keyboard, confirmation_keyboard,
    create_dynamic_workflow_keyboard
)
from states.workflow_states import WorkflowManagementStates

logger = setup_module_logger("workflow_integration_handler")


class WorkflowIntegrationHandler:
    """Handles integration between existing handlers and workflow system"""
    
    def __init__(self):
        self.router = Router()
        self.workflow_integration = WorkflowIntegration()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup integration handlers"""
        self._setup_request_handlers()
        self._setup_action_handlers()
        self._setup_user_selection_handlers()
        self._setup_notification_handlers()
    
    def _setup_request_handlers(self):
        """Setup handlers for viewing and managing requests"""
        
        @self.router.callback_query(F.data.startswith("handle_request_"))
        async def handle_request_selection(callback: CallbackQuery, state: FSMContext):
            """Handle request selection from notification"""
            try:
                request_id = callback.data.replace("handle_request_", "")
                
                # Get user info
                user = await get_user_by_telegram_id(callback.from_user.id)
                if not user:
                    await callback.answer("Пользователь не найден", show_alert=True)
                    return
                
                # Get request details
                details = await self.workflow_integration.get_request_details(request_id)
                if not details:
                    await callback.answer("Запрос не найден", show_alert=True)
                    return
                
                request = details['request']
                lang = user.get('language', 'ru')
                
                # Create request details message
                message_text = await self._format_request_details(request, lang)
                
                # Create dynamic keyboard based on user role and workflow type
                keyboard = create_dynamic_workflow_keyboard(
                    user['role'], request.workflow_type, request_id, lang
                )
                
                # Update message
                await callback.message.edit_text(
                    text=message_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                
                # Store request_id in state for further actions
                await state.update_data(current_request_id=request_id)
                await state.set_state(WorkflowManagementStates.viewing_request_details)
                
                await callback.answer()
                
            except Exception as e:
                logger.error(f"Error handling request selection: {e}", exc_info=True)
                await callback.answer("Произошла ошибка", show_alert=True)
        
        @self.router.callback_query(F.data.startswith("view_request_details_"))
        async def view_request_details(callback: CallbackQuery):
            """View detailed request information"""
            try:
                request_id = callback.data.replace("view_request_details_", "")
                
                # Get user info
                user = await get_user_by_telegram_id(callback.from_user.id)
                if not user:
                    await callback.answer("Пользователь не найден", show_alert=True)
                    return
                
                # Get request details
                details = await self.workflow_integration.get_request_details(request_id)
                if not details:
                    await callback.answer("Запрос не найден", show_alert=True)
                    return
                
                request = details['request']
                lang = user.get('language', 'ru')
                
                # Create detailed message
                message_text = await self._format_detailed_request_info(request, details['history'], lang)
                
                # Create back keyboard
                keyboard = workflow_request_details_keyboard(request_id, user['role'], lang)
                
                await callback.message.edit_text(
                    text=message_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                
                await callback.answer()
                
            except Exception as e:
                logger.error(f"Error viewing request details: {e}", exc_info=True)
                await callback.answer("Произошла ошибка", show_alert=True)
        
        @self.router.callback_query(F.data.startswith("view_request_history_"))
        async def view_request_history(callback: CallbackQuery):
            """View request history"""
            try:
                request_id = callback.data.replace("view_request_history_", "")
                
                # Get user info
                user = await get_user_by_telegram_id(callback.from_user.id)
                if not user:
                    await callback.answer("Пользователь не найден", show_alert=True)
                    return
                
                # Get request details
                details = await self.workflow_integration.get_request_details(request_id)
                if not details:
                    await callback.answer("Запрос не найден", show_alert=True)
                    return
                
                lang = user.get('language', 'ru')
                
                # Create history message
                message_text = await self._format_request_history(details['history'], lang)
                
                # Create back keyboard
                keyboard = workflow_request_details_keyboard(request_id, user['role'], lang)
                
                await callback.message.edit_text(
                    text=message_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                
                await callback.answer()
                
            except Exception as e:
                logger.error(f"Error viewing request history: {e}", exc_info=True)
                await callback.answer("Произошла ошибка", show_alert=True)
    
    def _setup_action_handlers(self):
        """Setup handlers for workflow actions"""
        
        @self.router.callback_query(F.data.startswith("workflow_action_"))
        async def handle_workflow_action(callback: CallbackQuery, state: FSMContext):
            """Handle workflow action execution"""
            try:
                action = callback.data.replace("workflow_action_", "")
                
                # Get current request from state
                state_data = await state.get_data()
                request_id = state_data.get('current_request_id')
                
                if not request_id:
                    await callback.answer("Запрос не найден", show_alert=True)
                    return
                
                # Get user info
                user = await get_user_by_telegram_id(callback.from_user.id)
                if not user:
                    await callback.answer("Пользователь не найден", show_alert=True)
                    return
                
                # Handle specific actions
                if action == WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value:
                    await self._handle_assign_to_junior_manager(callback, state, request_id, user)
                elif action == WorkflowAction.ASSIGN_TO_TECHNICIAN.value:
                    await self._handle_assign_to_technician(callback, state, request_id, user)
                elif action == WorkflowAction.CALL_CLIENT.value:
                    await self._handle_call_client(callback, state, request_id, user)
                elif action == WorkflowAction.FORWARD_TO_CONTROLLER.value:
                    await self._handle_forward_to_controller(callback, state, request_id, user)
                elif action == WorkflowAction.START_INSTALLATION.value:
                    await self._handle_start_installation(callback, state, request_id, user)
                elif action == WorkflowAction.DOCUMENT_EQUIPMENT.value:
                    await self._handle_document_equipment(callback, state, request_id, user)
                elif action == WorkflowAction.UPDATE_INVENTORY.value:
                    await self._handle_update_inventory(callback, state, request_id, user)
                elif action == WorkflowAction.START_DIAGNOSTICS.value:
                    await self._handle_start_diagnostics(callback, state, request_id, user)
                elif action == WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value:
                    await self._handle_decide_warehouse_involvement(callback, state, request_id, user)
                elif action == WorkflowAction.RESOLVE_REMOTELY.value:
                    await self._handle_resolve_remotely(callback, state, request_id, user)
                else:
                    await callback.answer("Действие не поддерживается", show_alert=True)
                
            except Exception as e:
                logger.error(f"Error handling workflow action: {e}", exc_info=True)
                await callback.answer("Произошла ошибка", show_alert=True)
    
    def _setup_user_selection_handlers(self):
        """Setup handlers for user selection"""
        
        @self.router.callback_query(F.data.startswith("select_user_"))
        async def handle_user_selection(callback: CallbackQuery, state: FSMContext):
            """Handle user selection for assignments"""
            try:
                parts = callback.data.split("_")
                action = parts[2]
                user_id = int(parts[3])
                
                # Get current request from state
                state_data = await state.get_data()
                request_id = state_data.get('current_request_id')
                
                if not request_id:
                    await callback.answer("Запрос не найден", show_alert=True)
                    return
                
                # Get current user info
                current_user = await get_user_by_telegram_id(callback.from_user.id)
                if not current_user:
                    await callback.answer("Пользователь не найден", show_alert=True)
                    return
                
                # Execute assignment
                success = await transition_workflow(
                    request_id, action, callback.from_user.id, 
                    {f"{action.split('_')[-1]}_id": user_id}
                )
                
                if success:
                    lang = current_user.get('language', 'ru')
                    success_msg = "Назначение выполнено" if lang == 'ru' else "Tayinlash bajarildi"
                    await callback.answer(success_msg)
                    
                    # Update message to show success
                    await callback.message.edit_text(
                        text=f"✅ {success_msg}",
                        reply_markup=None
                    )
                else:
                    error_msg = "Ошибка назначения" if current_user.get('language', 'ru') == 'ru' else "Tayinlash xatosi"
                    await callback.answer(error_msg, show_alert=True)
                
            except Exception as e:
                logger.error(f"Error handling user selection: {e}", exc_info=True)
                await callback.answer("Произошла ошибка", show_alert=True)
    
    def _setup_notification_handlers(self):
        """Setup handlers for notification management"""
        
        @self.router.callback_query(F.data.startswith("mark_handled_"))
        async def mark_notification_handled(callback: CallbackQuery):
            """Mark notification as handled"""
            try:
                request_id = callback.data.replace("mark_handled_", "")
                
                # Mark notification as handled
                success = await self.workflow_integration.mark_notification_handled(
                    callback.from_user.id, request_id
                )
                
                if success:
                    await callback.answer("Уведомление обработано")
                else:
                    await callback.answer("Ошибка обработки уведомления", show_alert=True)
                
            except Exception as e:
                logger.error(f"Error marking notification as handled: {e}", exc_info=True)
                await callback.answer("Произошла ошибка", show_alert=True)
    
    # Helper methods for specific actions
    
    async def _handle_assign_to_junior_manager(self, callback: CallbackQuery, state: FSMContext, 
                                             request_id: str, user: Dict[str, Any]):
        """Handle assignment to junior manager"""
        # Get junior managers
        junior_managers = await get_users_by_role(UserRole.JUNIOR_MANAGER.value)
        
        if not junior_managers:
            await callback.answer("Младшие менеджеры не найдены", show_alert=True)
            return
        
        lang = user.get('language', 'ru')
        text = "Выберите младшего менеджера:" if lang == 'ru' else "Kichik menejer tanlang:"
        
        keyboard = user_selection_keyboard(
            junior_managers, WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value, lang
        )
        
        await callback.message.edit_text(text=text, reply_markup=keyboard)
        await callback.answer()
    
    async def _handle_assign_to_technician(self, callback: CallbackQuery, state: FSMContext,
                                         request_id: str, user: Dict[str, Any]):
        """Handle assignment to technician"""
        # Get technicians
        technicians = await get_users_by_role(UserRole.TECHNICIAN.value)
        
        if not technicians:
            await callback.answer("Техники не найдены", show_alert=True)
            return
        
        lang = user.get('language', 'ru')
        text = "Выберите техника:" if lang == 'ru' else "Texnik tanlang:"
        
        keyboard = user_selection_keyboard(
            technicians, WorkflowAction.ASSIGN_TO_TECHNICIAN.value, lang
        )
        
        await callback.message.edit_text(text=text, reply_markup=keyboard)
        await callback.answer()
    
    async def _handle_call_client(self, callback: CallbackQuery, state: FSMContext,
                                request_id: str, user: Dict[str, Any]):
        """Handle call client action"""
        lang = user.get('language', 'ru')
        
        if lang == 'uz':
            text = "Mijozga qo'ng'iroq qiling va qo'ng'iroq haqida eslatma yozing:"
        else:
            text = "Позвоните клиенту и напишите заметки о звонке:"
        
        await callback.message.edit_text(text=text, reply_markup=None)
        await state.update_data(awaiting_call_notes=True)
        await callback.answer()
    
    async def _handle_forward_to_controller(self, callback: CallbackQuery, state: FSMContext,
                                          request_id: str, user: Dict[str, Any]):
        """Handle forward to controller action"""
        # Execute transition
        success = await transition_workflow(
            request_id, WorkflowAction.FORWARD_TO_CONTROLLER.value, 
            callback.from_user.id, {}
        )
        
        if success:
            lang = user.get('language', 'ru')
            success_msg = "Переслано контролеру" if lang == 'ru' else "Nazoratchiga yuborildi"
            await callback.message.edit_text(f"✅ {success_msg}", reply_markup=None)
        else:
            await callback.answer("Ошибка пересылки", show_alert=True)
        
        await callback.answer()
    
    async def _handle_start_installation(self, callback: CallbackQuery, state: FSMContext,
                                       request_id: str, user: Dict[str, Any]):
        """Handle start installation action"""
        # Execute transition
        success = await transition_workflow(
            request_id, WorkflowAction.START_INSTALLATION.value,
            callback.from_user.id, {}
        )
        
        if success:
            lang = user.get('language', 'ru')
            success_msg = "Установка начата" if lang == 'ru' else "O'rnatish boshlandi"
            await callback.message.edit_text(f"✅ {success_msg}", reply_markup=None)
        else:
            await callback.answer("Ошибка начала установки", show_alert=True)
        
        await callback.answer()
    
    async def _handle_document_equipment(self, callback: CallbackQuery, state: FSMContext,
                                       request_id: str, user: Dict[str, Any]):
        """Handle document equipment action"""
        lang = user.get('language', 'ru')
        
        if lang == 'uz':
            text = "Ishlatilgan jihozlar ro'yxatini yozing:"
        else:
            text = "Укажите список использованного оборудования:"
        
        await callback.message.edit_text(text=text, reply_markup=None)
        await state.update_data(awaiting_equipment_documentation=True)
        await callback.answer()
    
    async def _handle_update_inventory(self, callback: CallbackQuery, state: FSMContext,
                                     request_id: str, user: Dict[str, Any]):
        """Handle update inventory action"""
        # Execute transition
        success = await transition_workflow(
            request_id, WorkflowAction.UPDATE_INVENTORY.value,
            callback.from_user.id, {}
        )
        
        if success:
            lang = user.get('language', 'ru')
            success_msg = "Инвентарь обновлен" if lang == 'ru' else "Inventar yangilandi"
            await callback.message.edit_text(f"✅ {success_msg}", reply_markup=None)
        else:
            await callback.answer("Ошибка обновления инвентаря", show_alert=True)
        
        await callback.answer()
    
    async def _handle_start_diagnostics(self, callback: CallbackQuery, state: FSMContext,
                                      request_id: str, user: Dict[str, Any]):
        """Handle start diagnostics action"""
        # Execute transition
        success = await transition_workflow(
            request_id, WorkflowAction.START_DIAGNOSTICS.value,
            callback.from_user.id, {}
        )
        
        if success:
            lang = user.get('language', 'ru')
            success_msg = "Диагностика начата" if lang == 'ru' else "Diagnostika boshlandi"
            await callback.message.edit_text(f"✅ {success_msg}", reply_markup=None)
        else:
            await callback.answer("Ошибка начала диагностики", show_alert=True)
        
        await callback.answer()
    
    async def _handle_decide_warehouse_involvement(self, callback: CallbackQuery, state: FSMContext,
                                                 request_id: str, user: Dict[str, Any]):
        """Handle decide warehouse involvement action"""
        from keyboards.workflow_buttons import warehouse_decision_keyboard
        
        lang = user.get('language', 'ru')
        text = "Нужно ли участие склада?" if lang == 'ru' else "Ombor ishtiroki kerakmi?"
        
        keyboard = warehouse_decision_keyboard(lang)
        
        await callback.message.edit_text(text=text, reply_markup=keyboard)
        await callback.answer()
    
    async def _handle_resolve_remotely(self, callback: CallbackQuery, state: FSMContext,
                                     request_id: str, user: Dict[str, Any]):
        """Handle resolve remotely action"""
        lang = user.get('language', 'ru')
        
        if lang == 'uz':
            text = "Masofadan hal qilish tafsilotlarini yozing:"
        else:
            text = "Опишите детали удаленного решения:"
        
        await callback.message.edit_text(text=text, reply_markup=None)
        await state.update_data(awaiting_resolution_details=True)
        await callback.answer()
    
    # Helper methods for formatting messages
    
    async def _format_request_details(self, request, lang: str = 'ru') -> str:
        """Format request details for display"""
        if lang == 'uz':
            text = f"""
            📋 <b>So'rov tafsilotlari</b>

            🆔 ID: {request.id[:8]}...
            📝 Tur: {request.workflow_type}
            👤 Hozirgi rol: {request.role_current }
            📊 Holat: {request.current_status}
            ⚡ Muhimlik: {request.priority}

            📄 Tavsif: {request.description or 'Tavsif yo\'q'}
            📍 Joylashuv: {request.location or 'Joylashuv ko\'rsatilmagan'}

            📅 Yaratilgan: {request.created_at.strftime('%d.%m.%Y %H:%M')}
            🔄 Yangilangan: {request.updated_at.strftime('%d.%m.%Y %H:%M')}
"""
        else:
            text = f"""
            📋 <b>Детали запроса</b>

            🆔 ID: {request.id[:8]}...
            📝 Тип: {request.workflow_type}
            👤 Текущая роль: {request.role_current }
            📊 Статус: {request.current_status}
            ⚡ Приоритет: {request.priority}

            📄 Описание: {request.description or 'Описание отсутствует'}
            📍 Местоположение: {request.location or 'Местоположение не указано'}

            📅 Создано: {request.created_at.strftime('%d.%m.%Y %H:%M')}
            🔄 Обновлено: {request.updated_at.strftime('%d.%m.%Y %H:%M')}
            """
        
        return text
    
    async def _format_detailed_request_info(self, request, history, lang: str = 'ru') -> str:
        """Format detailed request information"""
        basic_info = await self._format_request_details(request, lang)
        
        if lang == 'uz':
            history_text = "\n\n📜 <b>So'rov tarixi:</b>\n"
        else:
            history_text = "\n\n📜 <b>История запроса:</b>\n"
        
        for transition in history[-5:]:  # Show last 5 transitions
            actor_name = transition.get('actor_name', 'System')
            history_text += f"• {transition['action']} - {actor_name} ({transition['created_at'].strftime('%d.%m %H:%M')})\n"
        
        return basic_info + history_text
    
    async def _format_request_history(self, history, lang: str = 'ru') -> str:
        """Format request history"""
        if lang == 'uz':
            text = "📜 <b>So'rov tarixi</b>\n\n"
        else:
            text = "📜 <b>История запроса</b>\n\n"
        
        for transition in history:
            actor_name = transition.get('actor_name', 'System')
            comments = transition.get('comments', '')
            
            text += f"🔄 <b>{transition['action']}</b>\n"
            text += f"👤 {actor_name}\n"
            text += f"📅 {transition['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            
            if comments:
                text += f"💬 {comments}\n"
            
            text += "\n"
        
        return text
    
    def get_router(self) -> Router:
        """Get the router for this handler"""
        return self.router


def get_workflow_integration_handler() -> WorkflowIntegrationHandler:
    """Get workflow integration handler instance"""
    return WorkflowIntegrationHandler()