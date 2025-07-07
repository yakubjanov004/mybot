from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
from keyboards.technician_buttons import get_technician_help_menu, get_help_request_types_keyboard
from states.technician_states import TechnicianStates
from database.technician_queries import get_technician_by_telegram_id, get_managers_telegram_ids
from database.base_queries import create_help_request
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.get_lang import get_user_lang
from loader import bot
import functools

def get_technician_help_router():
    logger = setup_logger('bot.technician.help')
    router = Router()

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

    @router.message(F.text.in_(["🆘 Yordam", "🆘 Помощь"]))
    @require_technician
    async def technician_help_menu_handler(message: Message, state: FSMContext):
        """Show technician help menu"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            help_text = "Yordam bo'limi" if lang == 'uz' else "Раздел помощи"
            await message.answer(
                help_text,
                reply_markup=get_technician_help_menu(lang)
            )
        except Exception as e:
            logger.error(f"Error in technician help menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "tech_request_help")
    @require_technician
    async def tech_request_help_handler(callback: CallbackQuery, state: FSMContext):
        """Handle help request from technician"""
        await cleanup_user_inline_messages(callback.from_user.id)
        try:
            user = await get_technician_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            help_type_text = "Yordam turini tanlang:" if lang == 'uz' else "Выберите тип помощи:"
            await callback.message.edit_text(
                help_type_text,
                reply_markup=get_help_request_types_keyboard(lang)
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in tech request help: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data.startswith("help_type_"))
    @require_technician
    async def process_help_type_selection(callback: CallbackQuery, state: FSMContext):
        """Process help type selection"""
        await cleanup_user_inline_messages(callback.from_user.id)
        try:
            help_type = callback.data.split("_")[2]
            user = await get_technician_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.update_data(help_type=help_type)
            await state.set_state(TechnicianStates.waiting_for_help_description)
            
            description_text = "Muammo haqida batafsil yozing:" if lang == 'uz' else "Опишите проблему подробно:"
            await callback.message.edit_text(description_text)
            await callback.answer()
        except Exception as e:
            logger.error(f"Error processing help type: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(TechnicianStates.waiting_for_help_description)
    @require_technician
    async def process_help_description(message: Message, state: FSMContext):
        """Process help description and send to managers"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            data = await state.get_data()
            help_type = data.get('help_type', 'general')
            
            # Determine priority based on help type
            priority = 'high' if help_type == 'emergency' else 'medium'
            
            # Create help request
            help_request_id = await create_help_request(user['id'], help_type, message.text, priority)
            
            if help_request_id:
                # Send notification to all managers
                managers = await get_managers_telegram_ids()
                
                # Prepare help type text
                help_type_texts = {
                    'equipment': 'Jihoz muammosi' if lang == 'uz' else 'Проблема с оборудованием',
                    'parts': 'Ehtiyot qism kerak' if lang == 'uz' else 'Нужны запчасти',
                    'question': 'Texnik savol' if lang == 'uz' else 'Технический вопрос',
                    'emergency': 'Favqulodda holat' if lang == 'uz' else 'Экстренная ситуация',
                    'client': 'Mijoz bilan muammo' if lang == 'uz' else 'Проблема с клиентом'
                }
                
                help_type_text = help_type_texts.get(help_type, help_type)
                priority_icon = "🚨" if priority == 'high' else "⚠️"
                
                for manager in managers:
                    try:
                        manager_lang = manager.get('language', 'uz')
                        
                        if manager_lang == 'uz':
                            manager_text = (
                                f"{priority_icon} Yordam so'rovi!\n\n"
                                f"👨‍🔧 Texnik: {user['full_name']}\n"
                                f"📞 Telefon: {user.get('phone_number', 'Noma\'lum')}\n"
                                f"🔧 Muammo turi: {help_type_text}\n"
                                f"📝 Tavsif: {message.text}\n"
                                f"⏰ Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                                f"🆔 So'rov ID: #{help_request_id}"
                            )
                        else:
                            manager_text = (
                                f"{priority_icon} Запрос помощи!\n\n"
                                f"👨‍🔧 Техник: {user['full_name']}\n"
                                f"📞 Телефон: {user.get('phone_number', 'Неизвестно')}\n"
                                f"🔧 Тип проблемы: {help_type_text}\n"
                                f"📝 Описание: {message.text}\n"
                                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                                f"🆔 ID запроса: #{help_request_id}"
                            )
                        
                        await bot.send_message(
                            chat_id=manager['telegram_id'],
                            text=manager_text
                        )
                    except Exception as e:
                        logger.error(f"Error sending help request to manager {manager['id']}: {str(e)}")
                
                # Confirm to technician
                success_text = (
                    "✅ Yordam so'rovi yuborildi!\n"
                    f"So'rov ID: #{help_request_id}\n"
                    "Menejerlar tez orada javob berishadi."
                ) if lang == 'uz' else (
                    "✅ Запрос помощи отправлен!\n"
                    f"ID запроса: #{help_request_id}\n"
                    "Менеджеры скоро ответят."
                )
                
                await message.answer(success_text)
            else:
                error_text = "Yordam so'rovini yuborishda xatolik" if lang == 'uz' else "Ошибка при отправке запроса помощи"
                await message.answer(error_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing help description: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
            await state.clear()

    @router.callback_query(F.data == "tech_help_menu")
    @require_technician
    async def tech_back_to_help_menu(callback: CallbackQuery, state: FSMContext):
        """Go back to help menu"""
        await cleanup_user_inline_messages(callback.from_user.id)
        try:
            user = await get_technician_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            help_text = "Yordam bo'limi" if lang == 'uz' else "Раздел помощи"
            await callback.message.edit_text(
                help_text,
                reply_markup=get_technician_help_menu(lang)
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Error going back to help menu: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    return router
