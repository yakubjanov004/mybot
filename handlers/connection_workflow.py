"""
Connection Request Workflow Handlers
Implements the complete connection request workflow:
Client → Manager → Junior Manager → Controller → Technician → Warehouse
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from typing import Optional

from database.models import UserRole, WorkflowType, WorkflowAction, Priority
from utils.workflow_manager import EnhancedWorkflowManager
from utils.notification_system import NotificationSystem
from utils.inventory_manager import InventoryManager
from utils.logger import setup_module_logger
from database.base_queries import get_user_by_telegram_id
from database.manager_queries import get_users_by_role
from states.client_states import ConnectionOrderStates
from keyboards.client_buttons import zayavka_type_keyboard, geolocation_keyboard
from loader import bot

logger = setup_module_logger("connection_workflow")

class ConnectionWorkflowHandler:
    """Handles connection request workflow operations"""
    
    def __init__(self):
        self.notification_system = NotificationSystem()
        self.inventory_manager = InventoryManager()
        self.workflow_manager = EnhancedWorkflowManager(
            self.notification_system, 
            self.inventory_manager
        )
        self.router = Router()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all workflow handlers"""
        self._setup_client_handlers()
        self._setup_manager_handlers()
        self._setup_junior_manager_handlers()
        self._setup_controller_handlers()
        self._setup_technician_handlers()
        self._setup_warehouse_handlers()
    
    def _setup_client_handlers(self):
        """Setup client request submission handlers"""
        
        @self.router.message(F.text.in_(["🔌 Ulanish uchun ariza", "🔌 Заявка на подключение"]))
        async def start_connection_request(message: Message, state: FSMContext):
            """Start connection request workflow"""
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await message.answer(
                "Ulanish turini tanlang:" if lang == 'uz' else "Выберите тип подключения:",
                reply_markup=zayavka_type_keyboard(lang)
            )
            await state.set_state(ConnectionOrderStates.selecting_connection_type)
        
        @self.router.callback_query(F.data.startswith("zayavka_type_"), StateFilter(ConnectionOrderStates.selecting_connection_type))
        async def select_connection_type(callback: CallbackQuery, state: FSMContext):
            """Select connection type"""
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            
            connection_type = callback.data.split("_")[-1]
            await state.update_data(connection_type=connection_type)
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Show tariff selection
            tariff_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Standard", callback_data="tariff_standard"),
                        InlineKeyboardButton(text="Premium", callback_data="tariff_premium")
                    ]
                ]
            )
            
            await callback.message.answer(
                "Tarifni tanlang:" if lang == 'uz' else "Выберите тариф:",
                reply_markup=tariff_keyboard
            )
            await state.set_state(ConnectionOrderStates.selecting_tariff)
        
        @self.router.callback_query(F.data.in_(["tariff_standard", "tariff_premium"]), StateFilter(ConnectionOrderStates.selecting_tariff))
        async def select_tariff(callback: CallbackQuery, state: FSMContext):
            """Select tariff plan"""
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            
            tariff = "Standard" if callback.data == "tariff_standard" else "Premium"
            await state.update_data(selected_tariff=tariff)
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            await callback.message.answer(
                "Manzilingizni kiriting:" if lang == 'uz' else "Введите ваш адрес:"
            )
            await state.set_state(ConnectionOrderStates.entering_address)
        
        @self.router.message(StateFilter(ConnectionOrderStates.entering_address))
        async def get_connection_address(message: Message, state: FSMContext):
            """Get installation address"""
            await state.update_data(address=message.text)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await message.answer(
                "Geolokatsiya yuborasizmi?" if lang == 'uz' else "Отправите геолокацию?",
                reply_markup=geolocation_keyboard(lang)
            )
            await state.set_state(ConnectionOrderStates.asking_for_geo)
        
        @self.router.callback_query(F.data.in_(["send_location_yes", "send_location_no"]), StateFilter(ConnectionOrderStates.asking_for_geo))
        async def ask_for_geo(callback: CallbackQuery, state: FSMContext):
            """Ask for geolocation"""
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
            
            if callback.data == "send_location_yes":
                user = await get_user_by_telegram_id(callback.from_user.id)
                lang = user.get('language', 'uz')
                
                await callback.message.answer(
                    "Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:"
                )
                await state.set_state(ConnectionOrderStates.waiting_for_geo)
            else:
                await self._finish_connection_request(callback, state, geo=None)
        
        @self.router.message(StateFilter(ConnectionOrderStates.waiting_for_geo), F.location)
        async def get_geo(message: Message, state: FSMContext):
            """Get geolocation"""
            await self._finish_connection_request(message, state, geo=message.location)
    
    async def _finish_connection_request(self, message_or_callback, state: FSMContext, geo=None):
        """Complete connection request submission"""
        try:
            data = await state.get_data()
            user = await get_user_by_telegram_id(message_or_callback.from_user.id)
            
            # Prepare request data
            description = f"Connection Request - {data.get('connection_type', 'Standard')}"
            if data.get('selected_tariff'):
                description += f"\nTariff: {data.get('selected_tariff')}"
            
            contact_info = {
                'phone': user.get('phone'),
                'telegram_id': user.get('telegram_id'),
                'full_name': user.get('full_name')
            }
            
            if geo:
                contact_info['latitude'] = geo.latitude
                contact_info['longitude'] = geo.longitude
            
            # Create workflow request
            request_id = await self.workflow_manager.create_connection_request(
                client_id=user['id'],
                description=description,
                location=data.get('address'),
                contact_info=contact_info
            )
            
            if request_id:
                user_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.message.from_user.id
                lang = user.get('language', 'uz')
                
                success_msg = (
                    f"✅ Arizangiz qabul qilindi!\nAriza ID: {request_id[:8]}\n"
                    "Menejerlar tez orada siz bilan bog'lanadi."
                    if lang == 'uz' else
                    f"✅ Ваша заявка принята!\nID заявки: {request_id[:8]}\n"
                    "Менеджеры свяжутся с вами в ближайшее время."
                )
                
                await bot.send_message(user_id, success_msg)
                logger.info(f"Connection request {request_id} created for user {user['id']}")
            else:
                user_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.message.from_user.id
                await bot.send_message(user_id, "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")
                logger.error(f"Failed to create connection request for user {user['id']}")
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error finishing connection request: {e}", exc_info=True)
            user_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.message.from_user.id
            await bot.send_message(user_id, "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")
    
    def _setup_manager_handlers(self):
        """Setup manager assignment handlers"""
        
        @self.router.callback_query(F.data.startswith("assign_junior_"))
        async def assign_to_junior_manager(callback: CallbackQuery):
            """Manager assigns request to junior manager"""
            try:
                request_id = callback.data.split("_")[-1]
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                if user.get('role') != UserRole.MANAGER.value:
                    await callback.answer("❌ Sizda bu amalni bajarish huquqi yo'q!")
                    return
                
                # Get available junior managers
                pool = bot.db
                junior_managers = await get_users_by_role(pool, UserRole.JUNIOR_MANAGER.value)
                
                if not junior_managers:
                    await callback.answer("❌ Kichik menejerlar topilmadi!")
                    return
                
                # Create selection keyboard
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            text=f"{jm.get('full_name', 'Unknown')}",
                            callback_data=f"select_junior_{request_id}_{jm['id']}"
                        )] for jm in junior_managers[:5]  # Limit to 5 for UI
                    ]
                )
                
                await callback.message.edit_text(
                    "Kichik menejerni tanlang:",
                    reply_markup=keyboard
                )
                
            except Exception as e:
                logger.error(f"Error in assign_to_junior_manager: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
        
        @self.router.callback_query(F.data.startswith("select_junior_"))
        async def select_junior_manager(callback: CallbackQuery):
            """Select specific junior manager"""
            try:
                parts = callback.data.split("_")
                request_id = parts[2]
                junior_manager_id = int(parts[3])
                
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                success = await self.workflow_manager.assign_to_junior_manager(
                    request_id, junior_manager_id, user['id']
                )
                
                if success:
                    await callback.message.edit_text(
                        f"✅ Ariza kichik menejerga tayinlandi!\nAriza ID: {request_id[:8]}"
                    )
                    logger.info(f"Request {request_id} assigned to junior manager {junior_manager_id}")
                else:
                    await callback.answer("❌ Tayinlashda xatolik yuz berdi!")
                
            except Exception as e:
                logger.error(f"Error in select_junior_manager: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
    
    def _setup_junior_manager_handlers(self):
        """Setup junior manager handlers"""
        
        @self.router.callback_query(F.data.startswith("call_client_"))
        async def call_client(callback: CallbackQuery, state: FSMContext):
            """Junior manager calls client"""
            try:
                request_id = callback.data.split("_")[-1]
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                if user.get('role') != UserRole.JUNIOR_MANAGER.value:
                    await callback.answer("❌ Sizda bu amalni bajarish huquqi yo'q!")
                    return
                
                await state.update_data(request_id=request_id)
                await callback.message.edit_text(
                    "Mijoz bilan qo'ng'iroq natijasini kiriting:"
                )
                await state.set_state("waiting_call_notes")
                
            except Exception as e:
                logger.error(f"Error in call_client: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
        
        @self.router.message(StateFilter("waiting_call_notes"))
        async def get_call_notes(message: Message, state: FSMContext):
            """Get call notes from junior manager"""
            try:
                data = await state.get_data()
                request_id = data.get('request_id')
                user = await get_user_by_telegram_id(message.from_user.id)
                
                call_notes = message.text
                
                # Forward to controller with call notes
                success = await self.workflow_manager.call_client_and_forward(
                    request_id, call_notes, user['id']
                )
                
                if success:
                    await message.answer(
                        f"✅ Qo'ng'iroq natijalari saqlandi va nazoratchi bilan bog'landi!\n"
                        f"Ariza ID: {request_id[:8]}"
                    )
                    logger.info(f"Call notes recorded and forwarded for request {request_id}")
                else:
                    await message.answer("❌ Xatolik yuz berdi!")
                
                await state.clear()
                
            except Exception as e:
                logger.error(f"Error in get_call_notes: {e}", exc_info=True)
                await message.answer("❌ Xatolik yuz berdi!")
                await state.clear()
    
    def _setup_controller_handlers(self):
        """Setup controller handlers"""
        
        @self.router.callback_query(F.data.startswith("assign_tech_"))
        async def assign_to_technician(callback: CallbackQuery):
            """Controller assigns request to technician"""
            try:
                request_id = callback.data.split("_")[-1]
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                if user.get('role') != UserRole.CONTROLLER.value:
                    await callback.answer("❌ Sizda bu amalni bajarish huquqi yo'q!")
                    return
                
                # Get available technicians
                pool = bot.db
                technicians = await get_users_by_role(pool, UserRole.TECHNICIAN.value)
                
                if not technicians:
                    await callback.answer("❌ Texniklar topilmadi!")
                    return
                
                # Create selection keyboard
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            text=f"{tech.get('full_name', 'Unknown')}",
                            callback_data=f"select_tech_{request_id}_{tech['id']}"
                        )] for tech in technicians[:5]  # Limit to 5 for UI
                    ]
                )
                
                await callback.message.edit_text(
                    "Texnikni tanlang:",
                    reply_markup=keyboard
                )
                
            except Exception as e:
                logger.error(f"Error in assign_to_technician: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
        
        @self.router.callback_query(F.data.startswith("select_tech_"))
        async def select_technician(callback: CallbackQuery):
            """Select specific technician"""
            try:
                parts = callback.data.split("_")
                request_id = parts[2]
                technician_id = int(parts[3])
                
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                success = await self.workflow_manager.assign_to_technician(
                    request_id, technician_id, user['id']
                )
                
                if success:
                    await callback.message.edit_text(
                        f"✅ Ariza texnikga tayinlandi!\nAriza ID: {request_id[:8]}"
                    )
                    logger.info(f"Request {request_id} assigned to technician {technician_id}")
                else:
                    await callback.answer("❌ Tayinlashda xatolik yuz berdi!")
                
            except Exception as e:
                logger.error(f"Error in select_technician: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
    
    def _setup_technician_handlers(self):
        """Setup technician handlers"""
        
        @self.router.callback_query(F.data.startswith("start_install_"))
        async def start_installation(callback: CallbackQuery):
            """Technician starts installation"""
            try:
                request_id = callback.data.split("_")[-1]
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                if user.get('role') != UserRole.TECHNICIAN.value:
                    await callback.answer("❌ Sizda bu amalni bajarish huquqi yo'q!")
                    return
                
                success = await self.workflow_manager.start_installation(
                    request_id, user['id'], "Installation started"
                )
                
                if success:
                    # Show equipment documentation button
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(
                                text="📋 Uskunalarni hujjatlash",
                                callback_data=f"doc_equipment_{request_id}"
                            )]
                        ]
                    )
                    
                    await callback.message.edit_text(
                        f"✅ O'rnatish boshlandi!\nAriza ID: {request_id[:8]}\n\n"
                        "O'rnatish tugagach, ishlatilgan uskunalarni hujjatlang:",
                        reply_markup=keyboard
                    )
                    logger.info(f"Installation started for request {request_id}")
                else:
                    await callback.answer("❌ Xatolik yuz berdi!")
                
            except Exception as e:
                logger.error(f"Error in start_installation: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
        
        @self.router.callback_query(F.data.startswith("doc_equipment_"))
        async def document_equipment(callback: CallbackQuery, state: FSMContext):
            """Document equipment usage"""
            try:
                request_id = callback.data.split("_")[-1]
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                if user.get('role') != UserRole.TECHNICIAN.value:
                    await callback.answer("❌ Sizda bu amalni bajarish huquqi yo'q!")
                    return
                
                await state.update_data(request_id=request_id)
                await callback.message.edit_text(
                    "Ishlatilgan uskunalar ro'yxatini kiriting:\n"
                    "(Har bir uskuna uchun: Nomi - Miqdori)"
                )
                await state.set_state("waiting_equipment_list")
                
            except Exception as e:
                logger.error(f"Error in document_equipment: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
        
        @self.router.message(StateFilter("waiting_equipment_list"))
        async def get_equipment_list(message: Message, state: FSMContext):
            """Get equipment list from technician"""
            try:
                data = await state.get_data()
                request_id = data.get('request_id')
                user = await get_user_by_telegram_id(message.from_user.id)
                
                equipment_text = message.text
                
                # Parse equipment list (simple format for now)
                equipment_used = []
                for line in equipment_text.split('\n'):
                    if '-' in line:
                        parts = line.split('-')
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            try:
                                quantity = int(parts[1].strip())
                                equipment_used.append({
                                    'name': name,
                                    'quantity': quantity
                                })
                            except ValueError:
                                continue
                
                if not equipment_used:
                    await message.answer("❌ Uskuna ro'yxati noto'g'ri formatda. Qaytadan kiriting:")
                    return
                
                # Document equipment and forward to warehouse
                success = await self.workflow_manager.document_equipment_usage(
                    request_id, equipment_used, f"Equipment documented: {equipment_text}", user['id']
                )
                
                if success:
                    await message.answer(
                        f"✅ Uskunalar hujjatlandi va omborga yuborildi!\n"
                        f"Ariza ID: {request_id[:8]}\n\n"
                        "Ombor xodimlari inventarni yangilaydi."
                    )
                    logger.info(f"Equipment documented for request {request_id}: {equipment_used}")
                else:
                    await message.answer("❌ Xatolik yuz berdi!")
                
                await state.clear()
                
            except Exception as e:
                logger.error(f"Error in get_equipment_list: {e}", exc_info=True)
                await message.answer("❌ Xatolik yuz berdi!")
                await state.clear()
    
    def _setup_warehouse_handlers(self):
        """Setup warehouse handlers"""
        
        @self.router.callback_query(F.data.startswith("update_inventory_"))
        async def update_inventory(callback: CallbackQuery):
            """Warehouse updates inventory and closes request"""
            try:
                request_id = callback.data.split("_")[-1]
                user = await get_user_by_telegram_id(callback.from_user.id)
                
                if user.get('role') != UserRole.WAREHOUSE.value:
                    await callback.answer("❌ Sizda bu amalni bajarish huquqi yo'q!")
                    return
                
                # Get request details to see equipment used
                request = await self.workflow_manager.state_manager.get_request(request_id)
                if not request:
                    await callback.answer("❌ Ariza topilmadi!")
                    return
                
                equipment_used = request.state_data.get('equipment_used', [])
                
                # Update inventory
                inventory_updates = {
                    'equipment_consumed': equipment_used,
                    'updated_by': user['id'],
                    'updated_at': str(datetime.now())
                }
                
                success = await self.workflow_manager.update_inventory_and_close(
                    request_id, inventory_updates, user['id']
                )
                
                if success:
                    await callback.message.edit_text(
                        f"✅ Inventar yangilandi va ariza yopildi!\n"
                        f"Ariza ID: {request_id[:8]}\n\n"
                        "Mijozga xabar yuborildi va baholash so'raladi."
                    )
                    logger.info(f"Inventory updated and request {request_id} closed")
                else:
                    await callback.answer("❌ Xatolik yuz berdi!")
                
            except Exception as e:
                logger.error(f"Error in update_inventory: {e}", exc_info=True)
                await callback.answer("❌ Xatolik yuz berdi!")
    
    def get_router(self) -> Router:
        """Get the workflow router"""
        return self.router


# Create global instance
connection_workflow_handler = ConnectionWorkflowHandler()

def get_connection_workflow_router() -> Router:
    """Get connection workflow router"""
    return connection_workflow_handler.get_router()