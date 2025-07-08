from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
from states.technician_states import TechnicianStates
from database.technician_queries import get_technician_chat_history, save_technician_message, get_technician_by_telegram_id, get_managers_telegram_ids
from database.base_queries import get_user_by_telegram_id, get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages
from loader import bot
from utils.role_router import get_role_router
import functools

def get_technician_communication_router():
    logger = setup_logger('bot.technician.communication')
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

    @router.callback_query(F.data == "tech_send_location")
    @require_technician
    async def tech_send_location_handler(callback: CallbackQuery, state: FSMContext):
        """Request location from technician"""
        await cleanup_user_inline_messages(callback.from_user.id)
        try:
            user = await get_technician_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            location_text = "📍 Geolokatsiyangizni yuboring:" if lang == 'uz' else "📍 Отправьте вашу геолокацию:"
            await callback.message.edit_text(location_text)
            await state.set_state(TechnicianStates.waiting_for_location)
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in tech send location: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(TechnicianStates.waiting_for_location, F.location)
    @require_technician
    async def process_technician_location(message: Message, state: FSMContext):
        """Process technician location and send to managers"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            location = message.location
            
            # Send location to all managers
            managers = await get_managers_telegram_ids()
            
            for manager in managers:
                try:
                    manager_lang = manager.get('language', 'uz')
                    
                    if manager_lang == 'uz':
                        location_text = (
                            f"📍 Texnik geolokatsiyasi\n\n"
                            f"👨‍🔧 Texnik: {user['full_name']}\n"
                            f"📞 Telefon: {user.get('phone_number', 'Noma\'lum')}\n"
                            f"⏰ Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                        )
                    else:
                        location_text = (
                            f"📍 Геолокация техника\n\n"
                            f"👨‍🔧 Техник: {user['full_name']}\n"
                            f"📞 Телефон: {user.get('phone_number', 'Неизвестно')}\n"
                            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                        )
                    
                    await bot.send_location(
                        chat_id=manager['telegram_id'],
                        latitude=location.latitude,
                        longitude=location.longitude
                    )
                    await bot.send_message(
                        chat_id=manager['telegram_id'],
                        text=location_text
                    )
                except Exception as e:
                    logger.error(f"Error sending location to manager {manager['id']}: {str(e)}")
            
            # Confirm to technician
            success_text = "✅ Geolokatsiya muvaffaqiyatli yuborildi!" if lang == 'uz' else "✅ Геолокация успешно отправлена!"
            await message.answer(success_text)
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing technician location: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
            await state.clear()

    @router.callback_query(F.data == "tech_contact_manager")
    @require_technician
    async def tech_contact_manager_handler(callback: CallbackQuery, state: FSMContext):
        """Contact manager directly"""
        await cleanup_user_inline_messages(callback.from_user.id)
        try:
            user = await get_technician_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.set_state(TechnicianStates.waiting_for_manager_message)
            message_text = "Menejerga xabar yozing:" if lang == 'uz' else "Напишите сообщение менеджеру:"
            await callback.message.edit_text(message_text)
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in tech contact manager: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(TechnicianStates.waiting_for_manager_message)
    @require_technician
    async def process_manager_message(message: Message, state: FSMContext):
        """Process message to manager"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            # Send message to all managers
            managers = await get_managers_telegram_ids()
            
            for manager in managers:
                try:
                    manager_lang = manager.get('language', 'uz')
                    
                    if manager_lang == 'uz':
                        manager_text = (
                            f"💬 Texnikdan xabar\n\n"
                            f"👨‍🔧 Texnik: {user['full_name']}\n"
                            f"📞 Telefon: {user.get('phone_number', 'Noma\'lum')}\n"
                            f"💬 Xabar: {message.text}\n"
                            f"⏰ Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                        )
                    else:
                        manager_text = (
                            f"💬 Сообщение от техника\n\n"
                            f"👨‍🔧 Техник: {user['full_name']}\n"
                            f"📞 Телефон: {user.get('phone_number', 'Неизвестно')}\n"
                            f"💬 Сообщение: {message.text}\n"
                            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                        )
                    
                    await bot.send_message(
                        chat_id=manager['telegram_id'],
                        text=manager_text
                    )
                except Exception as e:
                    logger.error(f"Error sending message to manager {manager['id']}: {str(e)}")
            
            # Confirm to technician
            success_text = "✅ Xabar menejerga yuborildi!" if lang == 'uz' else "✅ Сообщение отправлено менеджеру!"
            await message.answer(success_text)
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing manager message: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
            await state.clear()

    return router
