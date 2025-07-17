from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database.base_queries import get_user_by_telegram_id, get_users_by_role
from keyboards.call_center_buttons import (
    call_center_supervisor_main_menu, call_center_operator_selection_keyboard
)
from states.call_center import CallCenterSupervisorStates
from utils.logger import logger
from utils.role_router import get_role_router
from utils.workflow_manager import EnhancedWorkflowManager
from utils.notification_system import NotificationSystemFactory
from utils.inventory_manager import InventoryManagerFactory
from database.models import UserRole, WorkflowType

def get_call_center_supervisor_router():
    router = get_role_router("call_center_supervisor")

    @router.message(F.text.in_(["📞 Call Center Supervisor", "📞 Руководитель call-центра"]))
    async def call_center_supervisor_start(message: Message, state: FSMContext):
        """Call center supervisor main menu"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center_supervisor':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        await state.set_state(CallCenterSupervisorStates.main_menu)
        lang = user.get('language', 'uz')
        
        welcome_text = "📞 Call center supervisor paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель руководителя call-центра!"
        
        await message.answer(
            welcome_text,
            reply_markup=call_center_supervisor_main_menu(user['language'])
        )

    @router.message(F.text.in_(["📋 So'rovlarni tayinlash", "📋 Назначить запросы"]))
    async def show_pending_assignments(message: Message, state: FSMContext):
        """Show pending call center direct resolution requests"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center_supervisor':
            return
        
        lang = user.get('language', 'uz')
        
        try:
            # Initialize workflow manager
            notification_system = NotificationSystemFactory.create_notification_system()
            inventory_manager = InventoryManagerFactory.create_inventory_manager()
            workflow_manager = EnhancedWorkflowManager(notification_system, inventory_manager)
            
            # Get requests assigned to call center supervisor
            requests = await workflow_manager.get_requests_for_role(UserRole.CALL_CENTER_SUPERVISOR.value)
            
            if requests:
                await state.set_state(CallCenterSupervisorStates.assign_requests)
                
                pending_text = "📋 Tayinlash uchun so'rovlar:" if lang == 'uz' else "📋 Запросы для назначения:"
                text = f"{pending_text}\n\n"
                
                for request in requests:
                    text += f"🆔 ID: {request.id[:8]}\n"
                    text += f"📝 Tavsif: {request.description}\n"
                    text += f"🎯 Ustuvorlik: {request.priority}\n"
                    text += f"⏰ Yaratilgan: {request.created_at.strftime('%H:%M')}\n\n"
                
                # Store requests in state for later use
                await state.update_data(pending_requests=[r.id for r in requests])
                
                # Get available call center operators
                operators = await get_users_by_role(UserRole.CALL_CENTER.value)
                if operators:
                    select_text = "Operator tanlang:" if lang == 'uz' else "Выберите оператора:"
                    text += f"\n{select_text}"
                    
                    await message.answer(
                        text,
                        reply_markup=call_center_operator_selection_keyboard(operators, lang)
                    )
                else:
                    no_operators_text = "Mavjud operatorlar yo'q." if lang == 'uz' else "Нет доступных операторов."
                    await message.answer(f"{text}\n{no_operators_text}")
            else:
                no_requests_text = "Tayinlash uchun so'rovlar yo'q." if lang == 'uz' else "Нет запросов для назначения."
                await message.answer(no_requests_text)
                
        except Exception as e:
            logger.error(f"Error showing pending assignments: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("assign_cc_operator_"))
    async def assign_to_operator(callback: CallbackQuery, state: FSMContext):
        """Assign call center direct resolution request to operator"""
        operator_id = int(callback.data.split("_")[-1])
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center_supervisor':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        data = await state.get_data()
        pending_requests = data.get('pending_requests', [])
        
        if not pending_requests:
            no_requests_text = "Tayinlash uchun so'rovlar yo'q." if lang == 'uz' else "Нет запросов для назначения."
            await callback.message.edit_text(no_requests_text)
            return
        
        try:
            # Initialize workflow manager
            notification_system = NotificationSystemFactory.create_notification_system()
            inventory_manager = InventoryManagerFactory.create_inventory_manager()
            workflow_manager = EnhancedWorkflowManager(notification_system, inventory_manager)
            
            # Assign the first pending request to the selected operator
            request_id = pending_requests[0]
            success = await workflow_manager.assign_to_call_center_operator(
                request_id, operator_id, user['id']
            )
            
            if success:
                # Get operator details
                operator = await get_user_by_telegram_id(operator_id)
                operator_name = operator.get('full_name', f"Operator {operator_id}") if operator else f"Operator {operator_id}"
                
                success_text = "✅ So'rov muvaffaqiyatli tayinlandi!" if lang == 'uz' else "✅ Запрос успешно назначен!"
                text = f"{success_text}\n\n"
                text += f"🆔 So'rov ID: {request_id[:8]}\n"
                text += f"👤 Operator: {operator_name}\n"
                
                await callback.message.edit_text(text)
                
                logger.info(f"Call center supervisor {user['id']} assigned request {request_id[:8]} to operator {operator_id}")
            else:
                error_text = "❌ So'rovni tayinlashda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при назначении запроса."
                await callback.message.edit_text(error_text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error assigning to operator: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "cc_supervisor_back")
    async def supervisor_back(callback: CallbackQuery, state: FSMContext):
        """Go back to supervisor main menu"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center_supervisor':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(CallCenterSupervisorStates.main_menu)
        
        welcome_text = "📞 Call center supervisor paneliga xush kelibsiz!" if lang == 'uz' else "📞 Добро пожаловать в панель руководителя call-центра!"
        
        await callback.message.edit_text(welcome_text)
        await callback.answer()

    return router