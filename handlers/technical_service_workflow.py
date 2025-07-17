"""
Technical Service Without Warehouse Workflow Handler
Implements the complete workflow: Client → Controller → Technician
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from typing import Optional

from database.models import WorkflowType, WorkflowAction, UserRole, RequestStatus
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory
from utils.logger import setup_module_logger
from database.base_queries import get_user_by_telegram_id
from states.client_states import TechnicalServiceStates
from states.technician_states import TechnicianTechnicalServiceStates
from keyboards.client_buttons import technical_service_keyboard, confirmation_keyboard
from loader import bot

logger = setup_module_logger("technical_service_workflow")

class TechnicalServiceWorkflowHandler:
    """Handles Technical Service Without Warehouse workflow"""
    
    def __init__(self):
        self.state_manager = StateManagerFactory.create_state_manager()
        self.notification_system = NotificationSystemFactory.create_notification_system()
        self.workflow_engine = WorkflowEngineFactory.create_workflow_engine(
            self.state_manager, self.notification_system
        )
        self.router = Router()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all workflow handlers"""
        # Client handlers
        self.router.message(F.text.in_(["🔧 Texnik xizmat", "🔧 Техническая служба"]))(self.start_technical_request)
        self.router.message(StateFilter(TechnicalServiceStates.entering_issue_description))(self.process_issue_description)
        self.router.callback_query(F.data == "confirm_technical_request", StateFilter(TechnicalServiceStates.confirming_request))(self.confirm_technical_request)
        
        # Technician handlers - these handle notifications from workflow engine
        self.router.callback_query(F.data.startswith("handle_request_"))(self.handle_technical_request)
        self.router.callback_query(F.data.startswith("start_technical_diagnostics_"))(self.start_diagnostics)
        self.router.callback_query(F.data.startswith("decide_warehouse_involvement_"))(self.decide_warehouse_involvement)
        self.router.callback_query(F.data.startswith("resolve_without_warehouse_"))(self.resolve_without_warehouse)
        self.router.message(StateFilter(TechnicianTechnicalServiceStates.entering_resolution_comments))(self.process_resolution_comments)
        
        # Client rating handlers
        self.router.callback_query(F.data.startswith("rate_technical_service_"))(self.show_rating_options)
        self.router.callback_query(F.data.startswith("technical_rating_"))(self.process_service_rating)
    
    async def start_technical_request(self, message: Message, state: FSMContext):
        """Client starts technical service request"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != UserRole.CLIENT.value:
                return
            
            lang = user.get('language', 'ru')
            
            if lang == 'uz':
                text = (
                    "🔧 <b>Texnik xizmat so'rovi</b>\n\n"
                    "Texnik muammoni batafsil tasvirlab bering:\n"
                    "• Internet ulanmayapti\n"
                    "• Sekin ishlayapti\n"
                    "• Uskunada nosozlik\n"
                    "• Boshqa texnik muammolar"
                )
            else:
                text = (
                    "🔧 <b>Запрос технического обслуживания</b>\n\n"
                    "Подробно опишите техническую проблему:\n"
                    "• Не подключается интернет\n"
                    "• Медленно работает\n"
                    "• Неисправность оборудования\n"
                    "• Другие технические проблемы"
                )
            
            await message.answer(text, parse_mode='HTML')
            await state.set_state(TechnicalServiceStates.entering_issue_description)
            
            logger.info(f"Client {user['id']} started technical service request")
            
        except Exception as e:
            logger.error(f"Error starting technical request: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def process_issue_description(self, message: Message, state: FSMContext):
        """Process client's issue description"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                return
            
            lang = user.get('language', 'ru')
            issue_description = message.text
            
            # Store issue description
            await state.update_data(
                issue_description=issue_description,
                issue_type="technical_support"
            )
            
            # Show confirmation
            if lang == 'uz':
                text = (
                    f"📝 <b>Texnik xizmat so'rovi</b>\n\n"
                    f"<b>Muammo tavsifi:</b>\n{issue_description}\n\n"
                    f"So'rovni tasdiqlaysizmi?"
                )
            else:
                text = (
                    f"📝 <b>Запрос технического обслуживания</b>\n\n"
                    f"<b>Описание проблемы:</b>\n{issue_description}\n\n"
                    f"Подтвердить запрос?"
                )
            
            await message.answer(
                text, 
                parse_mode='HTML',
                reply_markup=confirmation_keyboard(lang)
            )
            await state.set_state(TechnicalServiceStates.confirming_request)
            
        except Exception as e:
            logger.error(f"Error processing issue description: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def confirm_technical_request(self, callback: CallbackQuery, state: FSMContext):
        """Confirm and create technical service request"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                return
            
            lang = user.get('language', 'ru')
            data = await state.get_data()
            
            # Create technical service request workflow
            request_data = {
                'client_id': user['id'],
                'description': data['issue_description'],
                'issue_type': data['issue_type'],
                'priority': 'medium',
                'contact_info': {
                    'phone': user.get('phone'),
                    'telegram_id': user.get('telegram_id'),
                    'full_name': user.get('full_name')
                }
            }
            
            request_id = await self.workflow_engine.initiate_workflow(
                WorkflowType.TECHNICAL_SERVICE.value, request_data
            )
            
            if request_id:
                # Notify client
                if lang == 'uz':
                    success_text = (
                        f"✅ <b>Texnik xizmat so'rovi yaratildi!</b>\n\n"
                        f"🆔 So'rov ID: {request_id[:8]}\n"
                        f"📝 Muammo: {data['issue_description']}\n\n"
                        f"Nazoratchi tez orada texnikni tayinlaydi."
                    )
                else:
                    success_text = (
                        f"✅ <b>Запрос технического обслуживания создан!</b>\n\n"
                        f"🆔 ID запроса: {request_id[:8]}\n"
                        f"📝 Проблема: {data['issue_description']}\n\n"
                        f"Контролер скоро назначит техника."
                    )
                
                await callback.message.edit_text(success_text, parse_mode='HTML')
                
                logger.info(f"Technical service request {request_id} created for client {user['id']}")
                
            else:
                error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
                await callback.message.edit_text(error_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error confirming technical request: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def handle_technical_request(self, callback: CallbackQuery):
        """Technician handles technical request from notification"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            
            # Get request details
            request = await self.state_manager.get_request(request_id)
            if not request:
                error_text = "So'rov topilmadi!" if user.get('language') == 'uz' else "Запрос не найден!"
                await callback.answer(error_text)
                return
            
            # Check if this is a technical service request
            if request.workflow_type != WorkflowType.TECHNICAL_SERVICE.value:
                return
            
            lang = user.get('language', 'ru')
            
            if lang == 'uz':
                text = (
                    f"🔧 <b>Texnik xizmat so'rovi</b>\n\n"
                    f"🆔 So'rov ID: {request_id[:8]}\n"
                    f"📝 Muammo: {request.description}\n"
                    f"📅 Yaratilgan: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Diagnostikani boshlang:"
                )
            else:
                text = (
                    f"🔧 <b>Запрос технического обслуживания</b>\n\n"
                    f"🆔 ID запроса: {request_id[:8]}\n"
                    f"📝 Проблема: {request.description}\n"
                    f"📅 Создано: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Начните диагностику:"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔍 Diagnostikani boshlash" if lang == 'uz' else "🔍 Начать диагностику",
                    callback_data=f"start_technical_diagnostics_{request_id}"
                )]
            ])
            
            await callback.message.edit_text(text, parse_mode='HTML', reply_markup=keyboard)
            
            logger.info(f"Technician {user['id']} handling technical request {request_id}")
            
        except Exception as e:
            logger.error(f"Error handling technical request: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def assign_to_technician(self, callback: CallbackQuery):
        """Controller assigns technical request to technician"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.CONTROLLER.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            technician_id = int(callback.data.split("_")[-2])  # Assuming format: assign_technical_to_technician_{technician_id}_{request_id}
            
            # Process workflow transition
            transition_data = {
                'technician_id': technician_id,
                'actor_id': user['id'],
                'assigned_at': str(datetime.now())
            }
            
            success = await self.workflow_engine.transition_workflow(
                request_id, 
                WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                UserRole.CONTROLLER.value,
                transition_data
            )
            
            if success:
                lang = user.get('language', 'ru')
                success_text = "Texnikga tayinlandi!" if lang == 'uz' else "Назначено технику!"
                await callback.message.edit_text(f"✅ {success_text}")
                
                logger.info(f"Technical request {request_id} assigned to technician {technician_id} by controller {user['id']}")
            else:
                error_text = "Tayinlashda xatolik!" if user.get('language') == 'uz' else "Ошибка при назначении!"
                await callback.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error assigning to technician: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def start_diagnostics(self, callback: CallbackQuery):
        """Technician starts diagnostics"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            
            # Process workflow transition
            transition_data = {
                'actor_id': user['id'],
                'diagnostics_started_at': str(datetime.now()),
                'diagnostics_notes': 'Diagnostics started'
            }
            
            success = await self.workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.START_DIAGNOSTICS.value,
                UserRole.TECHNICIAN.value,
                transition_data
            )
            
            if success:
                lang = user.get('language', 'ru')
                
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
                
                logger.info(f"Diagnostics started for request {request_id} by technician {user['id']}")
            else:
                error_text = "Diagnostikani boshlashda xatolik!" if user.get('language') == 'uz' else "Ошибка при начале диагностики!"
                await callback.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error starting diagnostics: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def decide_warehouse_involvement(self, callback: CallbackQuery):
        """Technician decides on warehouse involvement"""
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
            
            if warehouse_needed:
                # This would transition to warehouse workflow (not implemented in this task)
                lang = user.get('language', 'ru')
                info_text = (
                    "📦 Ombor bilan ishlash workflow hali amalga oshirilmagan." 
                    if lang == 'uz' else 
                    "📦 Workflow с складом еще не реализован."
                )
                await callback.message.edit_text(info_text)
                return
            
            # Continue with warehouse-free resolution
            lang = user.get('language', 'ru')
            
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
            
        except Exception as e:
            logger.error(f"Error deciding warehouse involvement: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def resolve_without_warehouse(self, callback: CallbackQuery, state: FSMContext):
        """Technician resolves issue without warehouse"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.TECHNICIAN.value:
                await callback.answer("Sizda bu amalni bajarish huquqi yo'q!")
                return
            
            request_id = callback.data.split("_")[-1]
            
            # Ask for resolution comments
            await state.update_data(resolving_request_id=request_id)
            await state.set_state(TechnicianTechnicalServiceStates.entering_resolution_comments)
            
            lang = user.get('language', 'ru')
            text = (
                "📝 Bajarilgan ishlar haqida batafsil yozing:" 
                if lang == 'uz' else 
                "📝 Подробно опишите выполненные работы:"
            )
            
            await callback.message.edit_text(text)
            
        except Exception as e:
            logger.error(f"Error resolving without warehouse: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def process_resolution_comments(self, message: Message, state: FSMContext):
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
            
            # Complete technical service
            transition_data = {
                'actor_id': user['id'],
                'resolution_comments': resolution_comments,
                'completed_at': str(datetime.now()),
                'warehouse_involved': False
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
                
                # Send completion notification to client
                await self._send_completion_notification(request_id)
                
                logger.info(f"Technical service request {request_id} completed by technician {user['id']}")
            else:
                error_text = "Yakunlashda xatolik!" if user.get('language') == 'uz' else "Ошибка при завершении!"
                await message.answer(error_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing resolution comments: {e}", exc_info=True)
            await message.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def _send_completion_notification(self, request_id: str):
        """Send completion notification to client"""
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
                    f"📝 Muammo: {request.description}\n\n"
                    f"Xizmat sifatini baholang:"
                )
            else:
                text = (
                    f"✅ <b>Техническое обслуживание завершено!</b>\n\n"
                    f"🆔 ID запроса: {request_id[:8]}\n"
                    f"📝 Проблема: {request.description}\n\n"
                    f"Оцените качество обслуживания:"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⭐ Baholash" if lang == 'uz' else "⭐ Оценить",
                    callback_data=f"rate_technical_service_{request_id}"
                )]
            ])
            
            await bot.send_message(
                chat_id=client['telegram_id'],
                text=text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error sending completion notification: {e}", exc_info=True)
    
    async def show_rating_options(self, callback: CallbackQuery):
        """Show rating options to client"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.CLIENT.value:
                return
            
            request_id = callback.data.split("_")[-1]
            lang = user.get('language', 'ru')
            
            if lang == 'uz':
                text = "⭐ Texnik xizmat sifatini baholang (1-5 yulduz):"
            else:
                text = "⭐ Оцените качество технического обслуживания (1-5 звезд):"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="1⭐", callback_data=f"technical_rating_1_{request_id}"),
                    InlineKeyboardButton(text="2⭐", callback_data=f"technical_rating_2_{request_id}"),
                    InlineKeyboardButton(text="3⭐", callback_data=f"technical_rating_3_{request_id}"),
                    InlineKeyboardButton(text="4⭐", callback_data=f"technical_rating_4_{request_id}"),
                    InlineKeyboardButton(text="5⭐", callback_data=f"technical_rating_5_{request_id}")
                ]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing rating options: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    async def process_service_rating(self, callback: CallbackQuery):
        """Process client's service rating"""
        try:
            await callback.answer()
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['role'] != UserRole.CLIENT.value:
                return
            
            # Parse callback data: technical_rating_{rating}_{request_id}
            parts = callback.data.split("_")
            rating = int(parts[2])
            request_id = parts[3]
            
            # Complete workflow with rating
            completion_data = {
                'rating': rating,
                'feedback': f"Technical service rated {rating} stars",
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
                        f"Texnik xizmat yakunlandi."
                    )
                else:
                    text = (
                        f"✅ <b>Спасибо!</b>\n\n"
                        f"Ваша оценка: {rating}⭐\n"
                        f"Техническое обслуживание завершено."
                    )
                
                await callback.message.edit_text(text, parse_mode='HTML')
                
                logger.info(f"Technical service request {request_id} rated {rating} stars by client {user['id']}")
            else:
                error_text = "Baholashda xatolik!" if user.get('language') == 'uz' else "Ошибка при оценке!"
                await callback.answer(error_text)
            
        except Exception as e:
            logger.error(f"Error processing service rating: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi!" if user.get('language') == 'uz' else "Произошла ошибка!")
    
    def get_router(self) -> Router:
        """Get the router for registration"""
        return self.router


# Factory function for easy integration
def get_technical_service_workflow_handler() -> TechnicalServiceWorkflowHandler:
    """Factory function to create workflow handler"""
    return TechnicalServiceWorkflowHandler()
