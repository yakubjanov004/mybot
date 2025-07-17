"""
Technical Service With Warehouse Workflow Handler
Implements the complete workflow: Client → Controller → Technician → Warehouse → Technician
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from typing import Optional, List, Dict, Any

from database.models import WorkflowType, WorkflowAction, UserRole, RequestStatus
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory
from utils.inventory_manager import get_inventory_manager
from utils.logger import setup_module_logger
from database.base_queries import get_user_by_telegram_id
from states.technician_states import TechnicalServiceStates
from states.warehouse_states import WarehouseWorkflowStates
from keyboards.technician_buttons import equipment_documentation_keyboard
from keyboards.warehouse_buttons import equipment_preparation_keyboard
from loader import bot

logger = setup_module_logger("technical_service_with_warehouse_workflow")

class TechnicalServiceWithWarehouseWorkflowHandler:
    """Handles Technical Service With Warehouse workflow"""
    
    def __init__(self):
        self.state_manager = StateManagerFactory.create_state_manager()
        self.notification_system = NotificationSystemFactory.create_notification_system()
        self.inventory_manager = None  # Will be initialized async
        self.workflow_engine = WorkflowEngineFactory.create_workflow_engine(
            self.state_manager, self.notification_system, self.inventory_manager
        )
        self.router = Router()
        self._setup_handlers()
    
    async def _get_inventory_manager(self):
        """Get inventory manager instance"""
        if self.inventory_manager is None:
            self.inventory_manager = await get_inventory_manager()
        return self.inventory_manager
    
    def _setup_handlers(self):
        """Setup all workflow handlers"""
        # Technician handlers for warehouse involvement
        self.router.callback_query(F.data.startswith("decide_warehouse_involvement_yes_"))(self.select_warehouse_involvement)
        self.router.callback_query(F.data.startswith("document_equipment_for_warehouse_"))(self.start_equipment_documentation)
        self.router.message(StateFilter(TechnicalServiceStates.documenting_equipment))(self.process_equipment_documentation)
        self.router.callback_query(F.data.startswith("confirm_equipment_documentation_"))(self.confirm_equipment_documentation)
        
        # Warehouse handlers
        self.router.callback_query(F.data.startswith("prepare_equipment_"))(self.start_equipment_preparation)
        self.router.callback_query(F.data.startswith("start_warehouse_preparation_"))(self.start_warehouse_preparation_state)
        self.router.message(StateFilter(WarehouseWorkflowStates.preparing_equipment))(self.process_equipment_preparation)
        self.router.callback_query(F.data.startswith("confirm_equipment_ready_"))(self.confirm_equipment_ready)
        
        # Technician completion after warehouse
        self.router.callback_query(F.data.startswith("complete_technical_with_warehouse_"))(self.complete_technical_with_warehouse)
        self.router.message(StateFilter(TechnicalServiceStates.completing_with_warehouse))(self.process_warehouse_completion)
        
        # Client rating handlers
        self.router.callback_query(F.data.startswith("rate_technical_warehouse_service_"))(self.show_warehouse_rating_options)
        self.router.callback_query(F.data.startswith("technical_warehouse_rating_"))(self.process_warehouse_service_rating)
    
    async def select_warehouse_involvement(self, callback: CallbackQuery):
        """Technician selects warehouse involvement"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            lang = user.get('language', 'ru')
            
            # Get request details to show context
            request = await self.state_manager.get_request(request_id)
            if not request:
                error_text = "So'rov topilmadi!" if lang == 'uz' else "Запрос не найден!"
                await callback.answer(error_text)
                return
            
            if lang == 'uz':
                text = (
                    "📦 <b>Ombor yordami kerak</b>\n\n"
                    f"🆔 So'rov ID: {request_id[:8]}\n"
                    f"📝 Muammo: {request.description}\n\n"
                    "Kerakli uskunalarni hujjatlashtirishni boshlang:"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📝 Uskunalarni hujjatlashtirish",
                        callback_data=f"document_equipment_for_warehouse_{request_id}"
                    )]
                ])
            else:
                text = (
                    "📦 <b>Требуется помощь склада</b>\n\n"
                    f"🆔 ID запроса: {request_id[:8]}\n"
                    f"📝 Проблема: {request.description}\n\n"
                    "Начните документирование необходимого оборудования:"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📝 Документировать оборудование",
                        callback_data=f"document_equipment_for_warehouse_{request_id}"
                    )]
                ])
            
            await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
            
            logger.info(f"Technician {user['id']} selected warehouse involvement for request {request_id}")
            
        except Exception as e:
            logger.error(f"Error selecting warehouse involvement: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def start_equipment_documentation(self, callback: CallbackQuery, state: FSMContext):
        """Technician starts equipment documentation"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            
            # Store request ID in state
            await state.update_data(documenting_request_id=request_id)
            await state.set_state(TechnicalServiceStates.documenting_equipment)
            
            lang = user.get('language', 'ru')
            
            if lang == 'uz':
                text = (
                    "📝 <b>Uskunalarni hujjatlashtirish</b>\n\n"
                    "Kerakli uskunalar ro'yxatini yozing:\n"
                    "• Uskuna nomi\n"
                    "• Miqdori\n"
                    "• Qo'shimcha izohlar\n\n"
                    "Misol:\n"
                    "Router TP-Link - 1 dona\n"
                    "Ethernet kabel - 10 metr\n"
                    "Konnektorlar - 2 dona"
                )
            else:
                text = (
                    "📝 <b>Документирование оборудования</b>\n\n"
                    "Напишите список необходимого оборудования:\n"
                    "• Название оборудования\n"
                    "• Количество\n"
                    "• Дополнительные комментарии\n\n"
                    "Пример:\n"
                    "Роутер TP-Link - 1 шт\n"
                    "Ethernet кабель - 10 метров\n"
                    "Коннекторы - 2 шт"
                )
            
            await callback.message.edit_text(text, parse_mode='HTML')
            
            logger.info(f"Equipment documentation started for request {request_id} by technician {user['id']}")
            
        except Exception as e:
            logger.error(f"Error starting equipment documentation: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def process_equipment_documentation(self, message: Message, state: FSMContext):
        """Process technician's equipment documentation"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                return
            
            data = await state.get_data()
            request_id = data.get('documenting_request_id')
            
            if not request_id:
                await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
                return
            
            equipment_documentation = message.text
            lang = user.get('language', 'ru')
            
            # Store equipment documentation
            await state.update_data(equipment_documentation=equipment_documentation)
            
            if lang == 'uz':
                text = (
                    f"📝 <b>Uskuna hujjatlashtirildi</b>\n\n"
                    f"<b>Kerakli uskunalar:</b>\n{equipment_documentation}\n\n"
                    f"Omborga yuborishni tasdiqlaysizmi?"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Omborga yuborish",
                        callback_data=f"confirm_equipment_documentation_{request_id}"
                    )]
                ])
            else:
                text = (
                    f"📝 <b>Оборудование задокументировано</b>\n\n"
                    f"<b>Необходимое оборудование:</b>\n{equipment_documentation}\n\n"
                    f"Подтвердить отправку на склад?"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Отправить на склад",
                        callback_data=f"confirm_equipment_documentation_{request_id}"
                    )]
                ])
            
            await message.answer(text, parse_mode='HTML', reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error processing equipment documentation: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def confirm_equipment_documentation(self, callback: CallbackQuery, state: FSMContext):
        """Confirm and forward equipment documentation to warehouse"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            data = await state.get_data()
            equipment_documentation = data.get('equipment_documentation')
            
            if not equipment_documentation:
                await callback.answer("Uskuna hujjatlashtirilmagan!" if user.get('language') == 'uz' else "Оборудование не задокументировано!")
                return
            
            # Process workflow transition to warehouse
            transition_data = {
                'actor_id': user['id'],
                'equipment_needed': equipment_documentation,
                'documented_at': str(datetime.now()),
                'warehouse_involvement': True
            }
            
            success = await self.workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.DOCUMENT_EQUIPMENT.value,
                UserRole.TECHNICIAN.value,
                transition_data
            )
            
            if success:
                lang = user.get('language', 'ru')
                
                if lang == 'uz':
                    success_text = (
                        f"✅ <b>Omborga yuborildi!</b>\n\n"
                        f"Uskuna hujjatlashtirildi va omborga yuborildi.\n"
                        f"Ombor xodimi tez orada uskunalarni tayyorlaydi."
                    )
                else:
                    success_text = (
                        f"✅ <b>Отправлено на склад!</b>\n\n"
                        f"Оборудование задокументировано и отправлено на склад.\n"
                        f"Сотрудник склада скоро подготовит оборудование."
                    )
                
                await callback.message.edit_text(success_text, parse_mode='HTML')
                
                logger.info(f"Equipment documentation forwarded to warehouse for request {request_id}")
            else:
                error_text = "Omborga yuborishda xatolik!" if user.get('language') == 'uz' else "Ошибка при отправке на склад!"
                await callback.answer(error_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error confirming equipment documentation: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def start_equipment_preparation(self, callback: CallbackQuery):
        """Warehouse starts equipment preparation"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.WAREHOUSE.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            
            # Get request details
            request = await self.state_manager.get_request(request_id)
            if not request:
                error_text = "So'rov topilmadi!" if user.get('language') == 'uz' else "Запрос не найден!"
                await callback.answer(error_text)
                return
            
            lang = user.get('language', 'ru')
            equipment_needed = request.state_data.get('equipment_needed', 'Uskuna ro\'yxati ko\'rsatilmagan')
            
            if lang == 'uz':
                text = (
                    f"📦 <b>Uskuna tayyorlash</b>\n\n"
                    f"🆔 So'rov ID: {request_id[:8]}\n"
                    f"📝 Muammo: {request.description}\n\n"
                    f"<b>Kerakli uskunalar:</b>\n{equipment_needed}\n\n"
                    f"Uskunalarni tayyorlang va izoh yozing:"
                )
            else:
                text = (
                    f"📦 <b>Подготовка оборудования</b>\n\n"
                    f"🆔 ID запроса: {request_id[:8]}\n"
                    f"📝 Проблема: {request.description}\n\n"
                    f"<b>Необходимое оборудование:</b>\n{equipment_needed}\n\n"
                    f"Подготовьте оборудование и напишите комментарий:"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📝 Izoh yozish" if lang == 'uz' else "📝 Написать комментарий",
                    callback_data=f"start_warehouse_preparation_{request_id}"
                )]
            ])
            
            await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
            
            logger.info(f"Equipment preparation started for request {request_id} by warehouse {user['id']}")
            
        except Exception as e:
            logger.error(f"Error starting equipment preparation: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def start_warehouse_preparation_state(self, callback: CallbackQuery, state: FSMContext):
        """Start warehouse preparation state for entering comments"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.WAREHOUSE.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            
            # Set state for warehouse preparation
            await state.update_data(preparing_request_id=request_id)
            await state.set_state(WarehouseWorkflowStates.preparing_equipment)
            
            lang = user.get('language', 'ru')
            
            if lang == 'uz':
                text = (
                    "📝 <b>Uskuna tayyorlash izohi</b>\n\n"
                    "Uskunalarni tayyorlash jarayoni haqida batafsil yozing:\n"
                    "• Qaysi uskunalar tayyorlandi\n"
                    "• Uskunalarning holati\n"
                    "• Qo'shimcha izohlar"
                )
            else:
                text = (
                    "📝 <b>Комментарий по подготовке оборудования</b>\n\n"
                    "Подробно опишите процесс подготовки оборудования:\n"
                    "• Какое оборудование подготовлено\n"
                    "• Состояние оборудования\n"
                    "• Дополнительные комментарии"
                )
            
            await callback.message.edit_text(text, parse_mode='HTML')
            
            logger.info(f"Warehouse preparation state started for request {request_id} by warehouse {user['id']}")
            
        except Exception as e:
            logger.error(f"Error starting warehouse preparation state: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def process_equipment_preparation(self, message: Message, state: FSMContext):
        """Process warehouse equipment preparation comments"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != UserRole.WAREHOUSE.value:
                return
            
            data = await state.get_data()
            request_id = data.get('preparing_request_id')
            
            if not request_id:
                await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
                return
            
            preparation_comments = message.text
            lang = user.get('language', 'ru')
            
            # Store preparation comments
            await state.update_data(preparation_comments=preparation_comments)
            
            if lang == 'uz':
                text = (
                    f"📦 <b>Uskuna tayyorlandi</b>\n\n"
                    f"<b>Izohlar:</b>\n{preparation_comments}\n\n"
                    f"Texnikga tayyorligini tasdiqlaysizmi?"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Texnikga tasdiqlamoq",
                        callback_data=f"confirm_equipment_ready_{request_id}"
                    )]
                ])
            else:
                text = (
                    f"📦 <b>Оборудование подготовлено</b>\n\n"
                    f"<b>Комментарии:</b>\n{preparation_comments}\n\n"
                    f"Подтвердить готовность технику?"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Подтвердить технику",
                        callback_data=f"confirm_equipment_ready_{request_id}"
                    )]
                ])
            
            await message.answer(text, parse_mode='HTML', reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error processing equipment preparation: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def confirm_equipment_ready(self, callback: CallbackQuery, state: FSMContext):
        """Warehouse confirms equipment is ready and returns to technician"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.WAREHOUSE.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            data = await state.get_data()
            preparation_comments = data.get('preparation_comments')
            
            # Process workflow transition back to technician
            transition_data = {
                'actor_id': user['id'],
                'equipment_prepared': True,
                'warehouse_comments': preparation_comments,
                'prepared_at': str(datetime.now())
            }
            
            success = await self.workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.CONFIRM_EQUIPMENT_READY.value,
                UserRole.WAREHOUSE.value,
                transition_data
            )
            
            if success:
                lang = user.get('language', 'ru')
                
                if lang == 'uz':
                    success_text = (
                        f"✅ <b>Texnikga tasdiqlandi!</b>\n\n"
                        f"Uskuna tayyorlandi va texnikga xabar berildi.\n"
                        f"Texnik tez orada ishni yakunlaydi."
                    )
                else:
                    success_text = (
                        f"✅ <b>Подтверждено технику!</b>\n\n"
                        f"Оборудование подготовлено и техник уведомлен.\n"
                        f"Техник скоро завершит работу."
                    )
                
                await callback.message.edit_text(success_text, parse_mode='HTML')
                
                # Update inventory if needed
                inventory_manager = await self._get_inventory_manager()
                if inventory_manager:
                    request = await self.state_manager.get_request(request_id)
                    if request:
                        equipment_needed = request.state_data.get('equipment_needed', '')
                        # Parse equipment list and update inventory
                        # This is a simplified approach - in production, you'd have structured equipment data
                        await self._update_inventory_from_equipment_list(request_id, equipment_needed)
                
                logger.info(f"Equipment confirmed ready for request {request_id} by warehouse {user['id']}")
            else:
                error_text = "Tasdiqlashda xatolik!" if user.get('language') == 'uz' else "Ошибка при подтверждении!"
                await callback.answer(error_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error confirming equipment ready: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def complete_technical_with_warehouse(self, callback: CallbackQuery, state: FSMContext):
        """Technician completes technical service after warehouse confirmation"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            
            # Get request details to show warehouse comments
            request = await self.state_manager.get_request(request_id)
            if not request:
                error_text = "So'rov topilmadi!" if user.get('language') == 'uz' else "Запрос не найден!"
                await callback.answer(error_text)
                return
            
            warehouse_comments = request.state_data.get('warehouse_comments', '')
            lang = user.get('language', 'ru')
            
            # Ask for completion comments
            await state.update_data(completing_warehouse_request_id=request_id)
            await state.set_state(TechnicalServiceStates.completing_with_warehouse)
            
            if lang == 'uz':
                text = (
                    f"✅ <b>Ombor tasdiqlaganidan keyin yakunlash</b>\n\n"
                    f"<b>Ombor izohlari:</b>\n{warehouse_comments}\n\n"
                    f"Bajarilgan ishlar haqida yakuniy izoh yozing:"
                )
            else:
                text = (
                    f"✅ <b>Завершение после подтверждения склада</b>\n\n"
                    f"<b>Комментарии склада:</b>\n{warehouse_comments}\n\n"
                    f"Напишите итоговый комментарий о выполненных работах:"
                )
            
            await callback.message.edit_text(text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error completing technical with warehouse: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def process_warehouse_completion(self, message: Message, state: FSMContext):
        """Process technician's final completion comments after warehouse"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                return
            
            data = await state.get_data()
            request_id = data.get('completing_warehouse_request_id')
            
            if not request_id:
                await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
                return
            
            completion_comments = message.text
            
            # Complete technical service with warehouse
            transition_data = {
                'actor_id': user['id'],
                'completion_comments': completion_comments,
                'completed_at': str(datetime.now()),
                'warehouse_involved': True
            }
            
            success = await self.workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value,
                UserRole.TECHNICIAN.value,
                transition_data
            )
            
            if success:
                lang = user.get('language', 'ru')
                
                if lang == 'uz':
                    success_text = (
                        f"✅ <b>Texnik xizmat yakunlandi!</b>\n\n"
                        f"📝 Bajarilgan ishlar:\n{completion_comments}\n\n"
                        f"Ombor yordami bilan muvaffaqiyatli yakunlandi.\n"
                        f"Mijozga bildirishnoma yuborildi."
                    )
                else:
                    success_text = (
                        f"✅ <b>Техническое обслуживание завершено!</b>\n\n"
                        f"📝 Выполненные работы:\n{completion_comments}\n\n"
                        f"Успешно завершено с помощью склада.\n"
                        f"Клиенту отправлено уведомление."
                    )
                
                await message.answer(success_text, parse_mode='HTML')
                
                # Send completion notification to client
                await self._send_warehouse_completion_notification(request_id)
                
                logger.info(f"Technical service with warehouse request {request_id} completed by technician {user['id']}")
            else:
                error_text = "Yakunlashda xatolik!" if user.get('language') == 'uz' else "Ошибка при завершении!"
                await message.answer(error_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing warehouse completion: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def _send_warehouse_completion_notification(self, request_id: str):
        """Send completion notification to client for warehouse-involved service"""
        try:
            # Get request details
            request = await self.state_manager.get_request(request_id)
            if not request:
                return
            
            # Get client details
            client = await get_user_by_telegram_id(request.client_id)
            if not client or not client.get('telegram_id'):
                return
            
            lang = client.get('language', 'ru')
            
            if lang == 'uz':
                text = (
                    f"✅ <b>Texnik xizmat yakunlandi!</b>\n\n"
                    f"🆔 So'rov ID: {request_id[:8]}\n"
                    f"📝 Muammo: {request.description}\n"
                    f"📦 Ombor yordami bilan hal qilindi\n\n"
                    f"Xizmat sifatini baholang:"
                )
            else:
                text = (
                    f"✅ <b>Техническое обслуживание завершено!</b>\n\n"
                    f"🆔 ID запроса: {request_id[:8]}\n"
                    f"📝 Проблема: {request.description}\n"
                    f"📦 Решено с помощью склада\n\n"
                    f"Оцените качество обслуживания:"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⭐ Baholash" if lang == 'uz' else "⭐ Оценить",
                    callback_data=f"rate_technical_warehouse_service_{request_id}"
                )]
            ])
            
            await bot.send_message(
                chat_id=client['telegram_id'],
                text=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error sending warehouse completion notification: {e}", exc_info=True)
    
    async def show_warehouse_rating_options(self, callback: CallbackQuery):
        """Show rating options to client for warehouse service"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.CLIENT.value:
                return
            
            request_id = callback.data.split("_")[-1]
            lang = user.get('language', 'ru')
            
            if lang == 'uz':
                text = "⭐ Ombor yordami bilan texnik xizmat sifatini baholang (1-5 yulduz):"
            else:
                text = "⭐ Оцените качество технического обслуживания со складом (1-5 звезд):"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="1⭐", callback_data=f"technical_warehouse_rating_1_{request_id}"),
                    InlineKeyboardButton(text="2⭐", callback_data=f"technical_warehouse_rating_2_{request_id}"),
                    InlineKeyboardButton(text="3⭐", callback_data=f"technical_warehouse_rating_3_{request_id}"),
                    InlineKeyboardButton(text="4⭐", callback_data=f"technical_warehouse_rating_4_{request_id}"),
                    InlineKeyboardButton(text="5⭐", callback_data=f"technical_warehouse_rating_5_{request_id}")
                ]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing warehouse rating options: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def process_warehouse_service_rating(self, callback: CallbackQuery):
        """Process client's warehouse service rating"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.CLIENT.value:
                return
            
            # Parse callback data: technical_warehouse_rating_{rating}_{request_id}
            parts = callback.data.split("_")
            rating = int(parts[3])
            request_id = parts[4]
            
            # Complete workflow with rating
            completion_data = {
                'rating': rating,
                'feedback': f"Technical service with warehouse rated {rating} stars",
                'actor_id': user['id'],
                'rated_at': str(datetime.now())
            }
            
            success = await self.workflow_engine.complete_workflow(request_id, completion_data)
            
            if success:
                lang = user.get('language', 'ru')
                
                if lang == 'uz':
                    text = (
                        f"✅ <b>Rahmat!</b>\n\n"
                        f"Sizning bahoyingiz: {rating}⭐\n"
                        f"Ombor yordami bilan texnik xizmat yakunlandi."
                    )
                else:
                    text = (
                        f"✅ <b>Спасибо!</b>\n\n"
                        f"Ваша оценка: {rating}⭐\n"
                        f"Техническое обслуживание со складом завершено."
                    )
                
                await callback.message.edit_text(text, parse_mode='HTML')
                
                logger.info(f"Technical warehouse service request {request_id} rated {rating} stars by client {user['id']}")
            else:
                error_text = "Baholashda xatolik!" if user.get('language') == 'uz' else "Ошибка при оценке!"
                await callback.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error processing warehouse service rating: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def _update_inventory_from_equipment_list(self, request_id: str, equipment_list: str):
        """Update inventory based on equipment list (simplified implementation)"""
        try:
            inventory_manager = await self._get_inventory_manager()
            if not inventory_manager or not equipment_list:
                return
            
            # This is a simplified implementation
            # In production, you'd parse the equipment list more robustly
            equipment_items = []
            lines = equipment_list.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and '-' in line:
                    parts = line.split('-')
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        quantity_part = parts[1].strip()
                        
                        # Extract quantity (simplified)
                        quantity = 1
                        if any(char.isdigit() for char in quantity_part):
                            import re
                            numbers = re.findall(r'\d+', quantity_part)
                            if numbers:
                                quantity = int(numbers[0])
                        
                        equipment_items.append({
                            'name': name,
                            'quantity': quantity,
                            'type': 'equipment'
                        })
            
            if equipment_items:
                await inventory_manager.consume_equipment(request_id, equipment_items)
                logger.info(f"Inventory updated for request {request_id}: {len(equipment_items)} items")
            
        except Exception as e:
            logger.error(f"Error updating inventory from equipment list: {e}", exc_info=True)
    
    def get_router(self) -> Router:
        """Get the router for registration"""
        return self.router


# Factory function for easy integration
def get_technical_service_with_warehouse_workflow_handler() -> TechnicalServiceWithWarehouseWorkflowHandler:
    """Factory function to create workflow handler"""
    return TechnicalServiceWithWarehouseWorkflowHandler()