from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from keyboards.client_buttons import (
    zayavka_type_keyboard, geolocation_keyboard
)
from states.client_states import ConnectionOrderStates
from database.base_queries import get_user_by_telegram_id, create_zayavka
from utils.logger import setup_logger
from loader import bot, ZAYAVKA_GROUP_ID
from utils.role_router import get_role_router
from database.manager_queries import get_users_by_role
from .order_utils import format_group_zayavka_message
from utils.workflow_manager import EnhancedWorkflowManager
from utils.notification_system import NotificationSystem
from utils.inventory_manager import InventoryManager

def get_connection_order_router():
    logger = setup_logger('bot.client.connection')
    router = get_role_router("client")

    @router.message(F.text.in_(["🔌 Ulanish uchun ariza", "🔌 Заявка на подключение"]))
    async def start_connection_order(message: Message, state: FSMContext):
        """Yangi ulanish uchun ariza jarayonini boshlash"""
        lang = (await get_user_by_telegram_id(message.from_user.id)).get('language', 'uz')
        await message.answer(
            "Ulanish turini tanlang:" if lang == 'uz' else "Выберите тип подключения:",
            reply_markup=zayavka_type_keyboard(lang)
        )
        await state.set_state(ConnectionOrderStates.selecting_connection_type)

    @router.callback_query(F.data.startswith("zayavka_type_"), StateFilter(ConnectionOrderStates.selecting_connection_type))
    async def select_connection_type(callback: CallbackQuery, state: FSMContext):
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        order_type = callback.data.split("_")[-1]
        await state.update_data(connection_type=order_type)
        lang = (await get_user_by_telegram_id(callback.from_user.id)).get('language', 'uz')
        tariff_image_path = "static/image.png"
        photo = FSInputFile(tariff_image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=("Tariflardan birini tanlang:" if lang == 'uz' else "Выберите один из тарифов:"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Standard", callback_data="tariff_standard"),
                        InlineKeyboardButton(text="Yangi", callback_data="tariff_new")
                    ]
                ]
            )
        )
        await state.set_state(ConnectionOrderStates.selecting_tariff)

    @router.callback_query(F.data.in_(["tariff_standard", "tariff_new"]), StateFilter(ConnectionOrderStates.selecting_tariff))
    async def select_tariff(callback: CallbackQuery, state: FSMContext):
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        tariff = "Standard" if callback.data == "tariff_standard" else "Yangi"
        await state.update_data(selected_tariff=tariff)
        lang = (await get_user_by_telegram_id(callback.from_user.id)).get('language', 'uz')
        await callback.message.answer(
            "Manzilingizni kiriting:" if lang == 'uz' else "Введите ваш адрес:",
        )
        await state.set_state(ConnectionOrderStates.entering_address)

    @router.message(StateFilter(ConnectionOrderStates.entering_address))
    async def get_connection_address(message: Message, state: FSMContext):
        await state.update_data(address=message.text)
        lang = (await get_user_by_telegram_id(message.from_user.id)).get('language', 'uz')
        await message.answer(
            "Geolokatsiya yuborasizmi?" if lang == 'uz' else "Отправите геолокацию?",
            reply_markup=geolocation_keyboard(lang)
        )
        await state.set_state(ConnectionOrderStates.asking_for_geo)

    @router.callback_query(F.data.in_(["send_location_yes", "send_location_no"]), StateFilter(ConnectionOrderStates.asking_for_geo))
    async def ask_for_geo(callback: CallbackQuery, state: FSMContext):
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        if callback.data == "send_location_yes":
            lang = (await get_user_by_telegram_id(callback.from_user.id)).get('language', 'uz')
            await callback.message.edit_text(
                "Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:",
                reply_markup=None
            )
            await state.set_state(ConnectionOrderStates.waiting_for_geo)
        else:
            await finish_connection_order(callback, state, geo=None)

    @router.message(StateFilter(ConnectionOrderStates.waiting_for_geo), F.location)
    async def get_geo(message: Message, state: FSMContext):
        await state.update_data(geo=message.location)
        await finish_connection_order(message, state, geo=message.location)

    async def finish_connection_order(message_or_callback, state: FSMContext, geo=None):
        """Complete connection request submission using enhanced workflow system"""
        try:
            data = await state.get_data()
            user = await get_user_by_telegram_id(message_or_callback.from_user.id)
            
            # Prepare request data for enhanced workflow
            connection_type = data.get('connection_type', 'standard')
            tariff = data.get('selected_tariff', 'Standard')
            description = f"Connection Request - {connection_type}\nTariff: {tariff}"
            
            contact_info = {
                'phone': user.get('phone'),
                'telegram_id': user.get('telegram_id'),
                'full_name': user.get('full_name')
            }
            
            if geo:
                contact_info['latitude'] = geo.latitude
                contact_info['longitude'] = geo.longitude
            
            # Initialize enhanced workflow manager
            notification_system = NotificationSystem()
            inventory_manager = InventoryManager()
            workflow_manager = EnhancedWorkflowManager(
                notification_system, inventory_manager
            )
            
            # Create enhanced workflow request
            request_id = await workflow_manager.create_connection_request(
                client_id=user['id'],
                description=description,
                location=data.get('address'),
                contact_info=contact_info
            )
            
            user_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.message.from_user.id
            lang = user.get('language', 'uz')
            
            if request_id:
                # Success message with request ID
                success_msg = (
                    f"✅ Arizangiz qabul qilindi!\n"
                    f"Ariza ID: {request_id[:8]}\n"
                    f"Menejerlar tez orada siz bilan bog'lanadi."
                    if lang == 'uz' else
                    f"✅ Ваша заявка принята!\n"
                    f"ID заявки: {request_id[:8]}\n"
                    f"Менеджеры свяжутся с вами в ближайшее время."
                )
                
                await bot.send_message(user_id, success_msg)
                
                # Optional: Send to group for legacy compatibility
                if ZAYAVKA_GROUP_ID:
                    try:
                        group_msg = format_group_zayavka_message(
                            order_type='connection',
                            public_id=request_id[:8],
                            user=user,
                            phone=user.get('phone'),
                            address=data.get('address'),
                            description=description,
                            tariff=tariff,
                            geo=geo,
                            media=None
                        )
                        await bot.send_message(ZAYAVKA_GROUP_ID, group_msg, parse_mode='HTML')
                    except Exception as e:
                        logger.error(f"Group notification error: {str(e)}")
                
                logger.info(f"Enhanced connection request {request_id} created for user {user['id']}")
            else:
                # Error message
                error_msg = (
                    "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring."
                    if lang == 'uz' else
                    "❌ Произошла ошибка. Пожалуйста, попробуйте снова."
                )
                await bot.send_message(user_id, error_msg)
                logger.error(f"Failed to create enhanced connection request for user {user['id']}")
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in finish_connection_order: {e}", exc_info=True)
            user_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.message.from_user.id
            await bot.send_message(user_id, "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")
            await state.clear()

    return router
