from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database.base_queries import get_user_by_telegram_id
from keyboards.call_center_buttons import remote_resolution_keyboard, rating_keyboard
from states.call_center import CallCenterDirectResolutionStates
from utils.logger import logger
from utils.role_router import get_role_router
from utils.workflow_manager import EnhancedWorkflowManager
from utils.notification_system import NotificationSystemFactory
from utils.inventory_manager import InventoryManagerFactory
from database.models import UserRole, WorkflowType

def get_call_center_direct_resolution_router():
    router = get_role_router("call_center")

    @router.message(F.text.in_(["📋 Masofadan hal qilish", "📋 Удаленное решение"]))
    async def show_direct_resolution_requests(message: Message, state: FSMContext):
        """Show call center direct resolution requests assigned to operator"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            return
        
        lang = user.get('language', 'uz')
        
        try:
            # Initialize workflow manager
            notification_system = NotificationSystemFactory.create_notification_system()
            inventory_manager = InventoryManagerFactory.create_inventory_manager()
            workflow_manager = EnhancedWorkflowManager(notification_system, inventory_manager)
            
            # Get call center direct resolution requests assigned to this operator
            requests = await workflow_manager.get_requests_for_role(UserRole.CALL_CENTER.value)
            direct_requests = [r for r in requests if r.workflow_type == WorkflowType.CALL_CENTER_DIRECT.value]
            
            if direct_requests:
                await state.set_state(CallCenterDirectResolutionStates.operator_working)
                
                pending_text = "📋 Masofadan hal qilish uchun so'rovlar:" if lang == 'uz' else "📋 Запросы для удаленного решения:"
                text = f"{pending_text}\n\n"
                
                for request in direct_requests:
                    text += f"🆔 ID: {request.id[:8]}\n"
                    text += f"📝 Tavsif: {request.description}\n"
                    text += f"🎯 Ustuvorlik: {request.priority}\n"
                    text += f"⏰ Yaratilgan: {request.created_at.strftime('%H:%M')}\n"
                    
                    # Show client info if available
                    if request.contact_info:
                        client_name = request.contact_info.get('name', 'N/A')
                        client_phone = request.contact_info.get('phone', 'N/A')
                        text += f"👤 Mijoz: {client_name}\n"
                        text += f"📞 Telefon: {client_phone}\n"
                    
                    text += "\n"
                
                # Store requests in state for later use
                await state.update_data(direct_requests=[r.id for r in direct_requests])
                
                action_text = "Harakatni tanlang:" if lang == 'uz' else "Выберите действие:"
                text += f"\n{action_text}"
                
                await message.answer(
                    text,
                    reply_markup=remote_resolution_keyboard(lang)
                )
            else:
                no_requests_text = "Masofadan hal qilish uchun so'rovlar yo'q." if lang == 'uz' else "Нет запросов для удаленного решения."
                await message.answer(no_requests_text)
                
        except Exception as e:
            logger.error(f"Error showing direct resolution requests: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "resolve_remotely")
    async def start_remote_resolution(callback: CallbackQuery, state: FSMContext):
        """Start remote resolution process"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(CallCenterDirectResolutionStates.resolution_notes)
        
        resolution_text = "📝 Masofadan hal qilish jarayonini batafsil tasvirlab bering:" if lang == 'uz' else "📝 Подробно опишите процесс удаленного решения:"
        await callback.message.edit_text(resolution_text)
        await callback.answer()

    @router.message(StateFilter(CallCenterDirectResolutionStates.resolution_notes))
    async def get_resolution_notes(message: Message, state: FSMContext):
        """Get resolution notes and complete the request"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        resolution_notes = message.text.strip()
        data = await state.get_data()
        direct_requests = data.get('direct_requests', [])
        
        if not direct_requests:
            no_requests_text = "Hal qilish uchun so'rovlar yo'q." if lang == 'uz' else "Нет запросов для решения."
            await message.answer(no_requests_text)
            return
        
        try:
            # Initialize workflow manager
            notification_system = NotificationSystemFactory.create_notification_system()
            inventory_manager = InventoryManagerFactory.create_inventory_manager()
            workflow_manager = EnhancedWorkflowManager(notification_system, inventory_manager)
            
            # Resolve the first pending request
            request_id = direct_requests[0]
            success = await workflow_manager.resolve_remotely(
                request_id, resolution_notes, user['id']
            )
            
            if success:
                await state.set_state(CallCenterDirectResolutionStates.completed)
                
                success_text = "✅ So'rov muvaffaqiyatli hal qilindi!" if lang == 'uz' else "✅ Запрос успешно решен!"
                text = f"{success_text}\n\n"
                text += f"🆔 So'rov ID: {request_id[:8]}\n"
                text += f"📝 Hal qilish izohlar: {resolution_notes}\n\n"
                
                completion_text = "Mijozga xabar yuborildi va baholash so'raladi." if lang == 'uz' else "Клиенту отправлено уведомление и запрошена оценка."
                text += completion_text
                
                await message.answer(text)
                
                logger.info(f"Call center operator {user['id']} resolved request {request_id[:8]} remotely")
            else:
                error_text = "❌ So'rovni hal qilishda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при решении запроса."
                await message.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error resolving remotely: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "escalate_request")
    async def escalate_request(callback: CallbackQuery, state: FSMContext):
        """Escalate request to technical service"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        # For now, just show a message that escalation is not implemented
        escalate_text = "⬆️ So'rovni yuqoriga ko'tarish funksiyasi hozircha mavjud emas." if lang == 'uz' else "⬆️ Функция эскалации запроса пока недоступна."
        await callback.message.edit_text(escalate_text)
        await callback.answer()

    @router.callback_query(F.data == "cc_operator_back")
    async def operator_back(callback: CallbackQuery, state: FSMContext):
        """Go back to operator main menu"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        await state.set_state(CallCenterDirectResolutionStates.operator_working)
        
        back_text = "📞 Call center operatori paneliga qaytdingiz." if lang == 'uz' else "📞 Вы вернулись в панель оператора call-центра."
        await callback.message.edit_text(back_text)
        await callback.answer()

    return router