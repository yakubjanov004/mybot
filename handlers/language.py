from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from typing import Union, Callable, Optional

from keyboards.client_buttons import get_main_menu_keyboard, get_language_keyboard
from states.user_states import UserStates
from database.queries import get_user_by_telegram_id, update_user_language
from utils.logger import logger
from utils.inline_cleanup import safe_remove_inline, safe_remove_inline_call
from keyboards.call_center_buttons import call_center_main_menu_reply

router = Router()

async def get_user_lang(user_id: int) -> str:
    """Get user language from database"""
    try:
        user = await get_user_by_telegram_id(user_id)
        return user.get('language', 'uz') if user else 'uz'
    except Exception as e:
        logger.error(f"Error getting user language: {str(e)}")
        return 'uz'

# Universal language change functions for all roles
async def show_language_selection(message: Message, role: str, state: FSMContext) -> bool:
    """Show language selection keyboard for any role"""
    try:
        # Get user's current language
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        
        text = "Tilni tanlang:" if lang == 'uz' else "Выберите язык:"
        keyboard = get_language_keyboard(role)
        
        await safe_remove_inline(message)
        await message.answer(text, reply_markup=keyboard)
        return True
        
    except Exception as e:
        logger.error(f"Error in show_language_selection: {str(e)}")
        return False

async def process_language_change(
    call: CallbackQuery, 
    role: str, 
    get_main_keyboard_func: Callable, 
    state: FSMContext
) -> None:
    """Process language change for any role"""
    try:
        # Get new language from callback data
        new_lang = call.data.split("_")[-1]  # lang_uz -> uz
        
        # Update user's language in database
        await update_user_language(call.from_user.id, new_lang)
        
        # Update language in state (faqat language ni o'zgartirish)
        user_data = await state.get_data()
        user = user_data.get('user', {})
        if not isinstance(user, dict):
            user = dict(user)
        user['language'] = new_lang
        await state.update_data(user=user)
        
        # Send confirmation message
        confirmation_text = "Til o'zgartirildi!" if new_lang == 'uz' else "Язык изменен!"
        await call.message.edit_text(
            confirmation_text,
            reply_markup=None
        )
        
        # Show main menu in new language according to role
        role = user.get('role', 'client')
        if role == 'admin':
            from keyboards.admin_buttons import get_admin_main_menu
            main_menu_text = "Admin paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель администратора!"
            await call.message.answer(
                main_menu_text,
                reply_markup=get_admin_main_menu(new_lang)
            )
        elif role == 'technician':
            from keyboards.technician_buttons import get_technician_main_menu_keyboard
            main_menu_text = "Montajchi paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель монтажника!"
            await call.message.answer(
                main_menu_text,
                reply_markup=get_technician_main_menu_keyboard(new_lang)
            )
        elif role == 'manager':
            from keyboards.manager_buttons import get_manager_main_keyboard
            main_menu_text = "Menejer paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель менеджера!"
            await call.message.answer(
                main_menu_text,
                reply_markup=get_manager_main_keyboard(new_lang)
            )
        elif role == 'call_center':
            main_menu_text = "Call center paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель call center!"
            await call.message.answer(
                main_menu_text,
                reply_markup=call_center_main_menu_reply(new_lang)
            )
        elif role == 'controller':
            from keyboards.controllers_buttons import controllers_main_menu
            main_menu_text = "Controller paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель контроллера!"
            await call.message.answer(
                main_menu_text,
                reply_markup=controllers_main_menu(new_lang)
            )
        elif role == 'warehouse':
            from keyboards.warehouse_buttons import warehouse_main_menu
            main_menu_text = "Warehouse paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель склада!"
            await call.message.answer(
                main_menu_text,
                reply_markup=warehouse_main_menu(new_lang)
            )
        else:
            from keyboards.client_buttons import get_main_menu_keyboard
            main_menu_text = "Asosiy menyu" if new_lang == 'uz' else "Главное меню"
            await call.message.answer(
                main_menu_text,
                reply_markup=get_main_menu_keyboard(new_lang)
            )
        
        # Answer callback query
        await call.answer()
        
    except Exception as e:
        logger.error(f"Error in process_language_change: {str(e)}")
        lang = await get_user_lang(call.from_user.id)
        error_text = "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте позже."
        await call.message.answer(error_text)
        await call.answer()

@router.callback_query(F.data == "language")
@router.message(F.text.in_(["🌐 Til o'zgartirish", "🌐 Изменить язык"]))
async def show_language_menu(update: Union[Message, CallbackQuery], state: FSMContext):
    """Til tanlash menyusini ko'rsatish"""
    try:
        # Determine if this is a callback or message
        if isinstance(update, CallbackQuery):
            message = update.message
            callback = update
        else:
            message = update
            callback = None
        
        # Get user's current language from state or database
        user_data = await state.get_data()
        user = user_data.get('user')
        
        if user and 'language' in user:
            lang = user['language']
        else:
            # Fallback to database if not in state
            user = await get_user_by_telegram_id(update.from_user.id)
            lang = user.get('language', 'uz') if user else 'uz'
            
            # Update state with user data if not present
            if user and not user_data.get('user'):
                await state.update_data(user=user)
        
        text = "Tilni tanlang:" if lang == 'uz' else "Выберите язык:"
        keyboard = get_language_keyboard("client")
        
        if callback:
            await message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
        else:
            await safe_remove_inline(message)
            await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in show_language_menu: {str(e)}")
        text = "Tilni tanlang:"  # Default to Uzbek
        keyboard = get_language_keyboard("client")
        
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(text, reply_markup=keyboard)
            await update.answer()
        else:
            await safe_remove_inline(update)
            await update.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("lang_"))
async def change_language(call: CallbackQuery, state: FSMContext):
    """Handle language change"""
    try:
        # Get new language from callback data
        new_lang = call.data.split("_")[1]
        
        # Update user's language in database
        await update_user_language(call.from_user.id, new_lang)
        
        # Update language in state (faqat language ni o'zgartirish)
        user_data = await state.get_data()
        user = user_data.get('user', {})
        if not isinstance(user, dict):
            user = dict(user)
        user['language'] = new_lang
        await state.update_data(user=user)
        
        # Send confirmation message
        confirmation_text = "Til o'zgartirildi!" if new_lang == 'uz' else "Язык изменен!"
        await call.message.edit_text(
            confirmation_text,
            reply_markup=None
        )
        
        # Show main menu in new language according to role
        role = user.get('role', 'client')
        if role == 'admin':
            from keyboards.admin_buttons import get_admin_main_menu
            main_menu_text = "Admin paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель администратора!"
            await call.message.answer(
                main_menu_text,
                reply_markup=get_admin_main_menu(new_lang)
            )
        elif role == 'technician':
            from keyboards.technician_buttons import get_technician_main_menu_keyboard
            main_menu_text = "Montajchi paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель монтажника!"
            await call.message.answer(
                main_menu_text,
                reply_markup=get_technician_main_menu_keyboard(new_lang)
            )
        elif role == 'manager':
            from keyboards.manager_buttons import get_manager_main_keyboard
            main_menu_text = "Menejer paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель менеджера!"
            await call.message.answer(
                main_menu_text,
                reply_markup=get_manager_main_keyboard(new_lang)
            )
        elif role == 'call_center':
            main_menu_text = "Call center paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель call center!"
            await call.message.answer(
                main_menu_text,
                reply_markup=call_center_main_menu_reply(new_lang)
            )
        elif role == 'controller':
            from keyboards.controllers_buttons import controllers_main_menu
            main_menu_text = "Controller paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель контроллера!"
            await call.message.answer(
                main_menu_text,
                reply_markup=controllers_main_menu(new_lang)
            )
        elif role == 'warehouse':
            from keyboards.warehouse_buttons import warehouse_main_menu
            main_menu_text = "Warehouse paneliga xush kelibsiz!" if new_lang == 'uz' else "Добро пожаловать в панель склада!"
            await call.message.answer(
                main_menu_text,
                reply_markup=warehouse_main_menu(new_lang)
            )
        else:
            from keyboards.client_buttons import get_main_menu_keyboard
            main_menu_text = "Asosiy menyu" if new_lang == 'uz' else "Главное меню"
            await call.message.answer(
                main_menu_text,
                reply_markup=get_main_menu_keyboard(new_lang)
            )
        
        # Set state to main menu
        await state.set_state(UserStates.main_menu)
        
        # Answer callback query
        await call.answer()
        
    except Exception as e:
        logger.error(f"Tilni o'zgartirishda xatolik: {str(e)}", exc_info=True)
        lang = await get_user_lang(call.from_user.id)
        error_text = "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте позже."
        await call.message.answer(error_text)
        await call.answer()

# Role-specific language change handlers
@router.message(F.text.in_(["Tilni o'zgartirish", "Изменить язык"]))
async def universal_language_change(message: Message, state: FSMContext):
    """Universal language change handler for all roles"""
    try:
        # Get user role
        user = await get_user_by_telegram_id(message.from_user.id)
        role = user.get('role', 'client') if user else 'client'
        
        # Show language selection based on role
        success = await show_language_selection(message, role, state)
        if not success:
            lang = user.get('language', 'uz') if user else 'uz'
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
            
    except Exception as e:
        logger.error(f"Error in universal_language_change: {str(e)}")
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте позже."
        await message.answer(error_text)

# Role-specific callback handlers
@router.callback_query(F.data.startswith("tech_lang_"))
async def technician_language_change(call: CallbackQuery, state: FSMContext):
    """Handle language change for technician role"""
    try:
        from keyboards.technician_buttons import get_technician_main_menu_keyboard
        from states.technician_states import TechnicianStates
        
        await process_language_change(
            call=call,
            role="technician",
            get_main_keyboard_func=get_technician_main_menu_keyboard,
            state=state
        )
        await state.set_state(TechnicianStates.main_menu)
        
    except Exception as e:
        logger.error(f"Error in technician_language_change: {str(e)}")
        lang = await get_user_lang(call.from_user.id)
        error_text = "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте позже."
        await call.message.answer(error_text)
        await call.answer()

@router.callback_query(F.data.startswith("manager_lang_"))
async def manager_language_change(call: CallbackQuery, state: FSMContext):
    """Handle language change for manager role"""
    try:
        from keyboards.manager_buttons import get_manager_main_keyboard
        
        await safe_remove_inline_call(call)
        await process_language_change(
            call=call,
            role="manager",
            get_main_keyboard_func=get_manager_main_keyboard,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error in manager_language_change: {str(e)}")
        lang = await get_user_lang(call.from_user.id)
        error_text = "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте позже."
        await call.message.answer(error_text)
        await call.answer()

@router.callback_query(F.data.startswith("client_lang_"))
async def client_language_change(call: CallbackQuery, state: FSMContext):
    """Handle language change for client role"""
    try:
        await process_language_change(
            call=call,
            role="client",
            get_main_keyboard_func=get_main_menu_keyboard,
            state=state
        )
        await state.set_state(UserStates.main_menu)
        
    except Exception as e:
        logger.error(f"Error in client_language_change: {str(e)}")
        lang = await get_user_lang(call.from_user.id)
        error_text = "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте позже."
        await call.message.answer(error_text)
        await call.answer()