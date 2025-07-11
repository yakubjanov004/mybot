from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
from keyboards.technician_buttons import get_technician_help_menu, get_help_request_types_keyboard, get_technician_main_menu_keyboard
from states.technician_states import TechnicianHelpStates
from aiogram.fsm.state import State, StatesGroup
from database.technician_queries import get_technician_by_telegram_id, get_managers_telegram_ids
from database.base_queries import create_help_request
from utils.logger import setup_logger
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.get_lang import get_user_lang
from loader import bot
from utils.role_router import get_role_router
import functools

class HelpNavigationStates(StatesGroup):
    """States for help menu navigation"""
    IN_HELP_MENU = State()  # In help menu
    IN_HELP_REQUEST_MENU = State()  # In help request types menu

def get_technician_help_router():
    logger = setup_logger('bot.technician.help')
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
            await state.set_state(HelpNavigationStates.IN_HELP_MENU)
        except Exception as e:
            logger.error(f"Error in technician help menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(['🆘 Yordam so\'rash', '🆘 Запросить помощь']))
    @require_technician
    async def tech_request_help_handler(message: Message, state: FSMContext):
        """Handle help request from technician"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            help_type_text = "Yordam turini tanlang:" if lang == 'uz' else "Выберите тип помощи:"
            await message.answer(
                help_type_text,
                reply_markup=get_help_request_types_keyboard(lang)
            )
            await state.set_state(HelpNavigationStates.IN_HELP_REQUEST_MENU)
        except Exception as e:
            logger.error(f"Error in tech request help: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(['🔧 Jihoz muammosi', '🔧 Проблема с оборудованием']))
    @require_technician
    async def tech_equipment_issue_handler(message: Message, state: FSMContext):
        """Handle equipment issue selection"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.update_data(help_type='equipment')
            await state.set_state(TechnicianHelpStates.waiting_for_help_description)
            await message.answer("Muammo haqida batafsil yozing:")
        except Exception as e:
            logger.error(f"Error in tech equipment issue: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(['🛠️ Qo\'shimcha ehtiyot qism kerak', '🛠️ Нужны дополнительные запчасти']))
    @require_technician
    async def tech_parts_needed_handler(message: Message, state: FSMContext):
        """Handle parts needed selection"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.update_data(help_type='parts')
            await state.set_state(TechnicianHelpStates.waiting_for_help_description)
            await message.answer("Muammo haqida batafsil yozing:")
        except Exception as e:
            logger.error(f"Error in tech parts needed: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(['❓ Texnik savol', '❓ Технический вопрос']))
    @require_technician
    async def tech_technical_question_handler(message: Message, state: FSMContext):
        """Handle technical question selection"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.update_data(help_type='question')
            await state.set_state(TechnicianHelpStates.waiting_for_help_description)
            await message.answer("Muammo haqida batafsil yozing:")
        except Exception as e:
            logger.error(f"Error in tech technical question: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(['🚨 Favqulodda holat', '🚨 Экстренная ситуация']))
    @require_technician
    async def tech_emergency_handler(message: Message, state: FSMContext):
        """Handle emergency situation selection"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.update_data(help_type='emergency')
            await state.set_state(TechnicianHelpStates.waiting_for_help_description)
            await message.answer("Muammo haqida batafsil yozing:")
        except Exception as e:
            logger.error(f"Error in tech emergency: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(['👤 Mijoz bilan muammo', '👤 Проблема с клиентом']))
    @require_technician
    async def tech_client_issue_handler(message: Message, state: FSMContext):
        """Handle client issue selection"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.update_data(help_type='client')
            await state.set_state(TechnicianHelpStates.waiting_for_help_description)
            await message.answer("Muammo haqida batafsil yozing:")
        except Exception as e:
            logger.error(f"Error in tech client issue: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(['📍 Geolokatsiya yuborish', '📍 Отправить геолокацию']))
    @require_technician
    async def tech_send_location_handler(message: Message, state: FSMContext):
        """Handle location sharing"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.set_state(TechnicianHelpStates.waiting_for_location)
            await message.answer("Geolokatsiyani yuboring:")
        except Exception as e:
            logger.error(f"Error in tech send location: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(TechnicianHelpStates.waiting_for_help_description)
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
                                fr"📞 Telefon: {user.get('phone_number', 'Noma\'lum')}\n"
                                f"🔧 Muammo turi: {help_type_text}\n"
                                f"📝 Tavsif: {message.text}\n"
                                f"⏰ Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                                f"🆔 So'rov ID: #{help_request_id}"
                            )
                        else:
                            manager_text = (
                                f"{priority_icon} Запрос помощи!\n\n"
                                f"👨‍🔧 Техник: {user['full_name']}\n"
                                fr"📞 Телефон: {user.get('phone_number', 'Неизвестно')}\n"
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
        except Exception as e:
            logger.error(f"Error processing help description: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
        finally:
            await state.clear()

    @router.message(F.text.in_(['◀️ Orqaga', '◀️ Назад']))
    @require_technician
    async def tech_back_to_help_menu_handler(message: Message, state: FSMContext):
        """Handle back navigation in help menu"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            current_state = await state.get_state()
            
            if current_state == HelpNavigationStates.IN_HELP_REQUEST_MENU:
                # If we're in help request types menu, go back to help menu
                help_text = "Yordam bo'limi" if lang == 'uz' else "Раздел помощи"
                await message.answer(
                    help_text,
                    reply_markup=get_technician_help_menu(lang)
                )
                await state.set_state(HelpNavigationStates.IN_HELP_MENU)
                return  # Prevent further processing
        
            # If we're in help menu, go back to main menu
            main_menu_text = "Asosiy menyuga xush kelibsiz" if lang == 'uz' else "Добро пожаловать в главное меню"
            await message.answer(
                main_menu_text,
                reply_markup=get_technician_main_menu_keyboard(lang)
            )
            await state.clear()
            return  # Prevent further processing
        except Exception as e:
            logger.error(f"Error in back navigation: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(F.text.in_(['👨‍💼 Menejer bilan bog\'lanish', '👨‍💼 Связаться с менеджером']))
    @require_technician
    async def tech_contact_manager_handler(message: Message, state: FSMContext):
        """Contact manager directly"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            await state.set_state(TechnicianHelpStates.waiting_for_manager_message)
            message_text = "Menejerga xabar yozing:" if lang == 'uz' else "Напишите сообщение менеджеру:"
            await message.answer(message_text)
        except Exception as e:
            logger.error(f"Error in tech contact manager: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    return router
