from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from states.technician_states import TechnicianEquipmentStates
from database.technician_queries import get_warehouse_staff, get_managers_telegram_ids, get_technician_by_telegram_id
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.inline_cleanup import cleanup_user_inline_messages
from keyboards.technician_buttons import get_equipment_keyboard, get_back_technician_keyboard
from loader import bot
from utils.logger import setup_logger
from utils.role_router import get_role_router
import functools

def get_technician_equipment_router():
    logger = setup_logger('bot.technician.equipment')
    router = get_role_router("technician")

    def require_technician(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                message_or_call = args[0] if args else kwargs.get('message_or_call')
                user_id = message_or_call.from_user.id
                user = await get_technician_by_telegram_id(user_id)
                if not user:
                    lang = await get_user_lang(user_id)
                    text = "Sizda montajchi huquqi yo'q." if lang == 'uz' else "У вас нет прав монтажника."
                    if hasattr(message_or_call, 'answer'):
                        await message_or_call.answer(text)
                    else:
                        await message_or_call.message.answer(text)
                    return
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in require_technician decorator: {str(e)}", exc_info=True)
                if args and hasattr(args[0], 'answer'):
                    lang = await get_user_lang(args[0].from_user.id)
                    await args[0].answer("Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!")
        return wrapper

    @router.callback_query(F.data == "tech_equipment_request")
    @require_technician
    async def tech_equipment_request_handler(callback: CallbackQuery, state: FSMContext):
        """Request equipment from warehouse"""
        await cleanup_user_inline_messages(callback.from_user.id)
        try:
            user = await get_technician_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.set_state(TechnicianEquipmentStates.waiting_for_equipment_request)
            equipment_text = "Kerakli jihozlar ro'yxatini yozing:" if lang == 'uz' else "Напишите список необходимого оборудования:"
            await callback.message.edit_text(equipment_text)
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in tech equipment request: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(TechnicianEquipmentStates.waiting_for_equipment_request)
    @require_technician
    async def process_equipment_request(message: Message, state: FSMContext):
        """Process equipment request and send to warehouse"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            # Send equipment request to warehouse staff and managers
            warehouse_staff = await get_warehouse_staff()
            managers = await get_managers_telegram_ids()
            
            # Combine warehouse staff and managers
            recipients = warehouse_staff + managers
            
            for recipient in recipients:
                try:
                    recipient_lang = recipient.get('language', 'uz')
                    recipient_role = recipient.get('role', 'unknown')
                    
                    if recipient_lang == 'uz':
                        request_text = (
                            f"📦 Jihoz so'rovi\n\n"
                            f"👨‍🔧 Texnik: {user['full_name']}\n"
                            f"📞 Telefon: {user.get('phone_number', 'Noma\'lum')}\n"
                            f"📝 Kerakli jihozlar: {message.text}\n"
                            f"⏰ Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                        )
                    else:
                        request_text = (
                            f"📦 Запрос оборудования\n\n"
                            f"👨‍🔧 Техник: {user['full_name']}\n"
                            f"📞 Телефон: {user.get('phone_number', 'Неизвестно')}\n"
                            f"📝 Необходимое оборудование: {message.text}\n"
                            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                        )
                    
                    await bot.send_message(
                        chat_id=recipient['telegram_id'],
                        text=request_text
                    )
                except Exception as e:
                    logger.error(f"Error sending equipment request to {recipient['role']} {recipient['id']}: {str(e)}")
            
            # Confirm to technician
            success_text = "✅ Jihoz so'rovi yuborildi!" if lang == 'uz' else "✅ Запрос оборудования отправлен!"
            await message.answer(success_text)
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing equipment request: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
            await state.clear()

    return router
