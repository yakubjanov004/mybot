from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import get_equipment_keyboard, get_manager_main_keyboard
from states.manager_states import ManagerStates
from loader import bot
from database.base_queries import get_user_by_telegram_id
from utils.logger import setup_logger
from utils.role_router import get_role_router

def get_manager_equipment_router():
    logger = setup_logger('bot.manager.equipment')
    router = get_role_router("manager")

    @router.message(F.text.in_(['🔧 Jihozlar', '🔧 Оборудование']))
    async def show_equipment_menu(message: Message, state: FSMContext):
        """Show equipment management menu"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            lang = user.get('language', 'uz')
            equipment_text = "🔧 Jihozlar boshqaruvi:" if lang == 'uz' else "🔧 Управление оборудованием:"
            
            await message.answer(
                equipment_text,
                reply_markup=get_equipment_keyboard(lang)
            )
            
        except Exception as e:
            logger.error(f"Error in show_equipment_menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("equipment_"))
    async def handle_equipment_action(callback: CallbackQuery, state: FSMContext):
        """Handle equipment actions"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            action = callback.data.replace("equipment_", "")
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            if action == "list":
                await show_equipment_list(callback, lang)
            elif action == "add":
                await start_add_equipment(callback, state, lang)
            elif action == "search":
                await start_search_equipment(callback, state, lang)
            elif action == "maintenance":
                await show_maintenance_schedule(callback, lang)
            else:
                unknown_text = "Noma'lum amal" if lang == 'uz' else "Неизвестное действие"
                await callback.message.edit_text(unknown_text)
            
        except Exception as e:
            logger.error(f"Error in handle_equipment_action: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    async def show_equipment_list(callback, lang):
        """Show list of all equipment"""
        try:
            conn = await bot.db.acquire()
            try:
                equipment_list = await conn.fetch(
                    '''SELECT * FROM equipment 
                       ORDER BY created_at DESC 
                       LIMIT 20'''
                )
                
                if not equipment_list:
                    no_equipment_text = "❌ Hozircha jihozlar ro'yxati bo'sh." if lang == 'uz' else "❌ Список оборудования пока пуст."
                    await callback.message.edit_text(no_equipment_text)
                    return
                
                if lang == 'uz':
                    equipment_text = "🔧 <b>Jihozlar ro'yxati:</b>\n\n"
                    
                    for eq in equipment_list:
                        status_emoji = "✅" if eq.get('status') == 'working' else "❌" if eq.get('status') == 'broken' else "⚠️"
                        equipment_text += (
                            f"{status_emoji} <b>{eq.get('name', 'Noma\'lum')}</b>\n"
                            f"   🏷️ Model: {eq.get('model', '-')}\n"
                            f"   📍 Joylashuv: {eq.get('location', '-')}\n"
                            f"   📊 Status: {eq.get('status', '-')}\n"
                            f"   📅 Qo'shilgan: {eq.get('created_at', '-')}\n\n"
                        )
                else:
                    equipment_text = "🔧 <b>Список оборудования:</b>\n\n"
                    
                    for eq in equipment_list:
                        status_emoji = "✅" if eq.get('status') == 'working' else "❌" if eq.get('status') == 'broken' else "⚠️"
                        equipment_text += (
                            f"{status_emoji} <b>{eq.get('name', 'Неизвестно')}</b>\n"
                            f"   🏷️ Модель: {eq.get('model', '-')}\n"
                            f"   📍 Расположение: {eq.get('location', '-')}\n"
                            f"   📊 Статус: {eq.get('status', '-')}\n"
                            f"   📅 Добавлено: {eq.get('created_at', '-')}\n\n"
                        )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="equipment_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(equipment_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_equipment_list: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def start_add_equipment(callback, state, lang):
        """Start adding new equipment"""
        try:
            add_text = "🔧 Yangi jihoz qo'shish:\n\nJihoz nomini kiriting:" if lang == 'uz' else "🔧 Добавление нового оборудования:\n\nВведите название оборудования:"
            await callback.message.edit_text(add_text)
            await state.set_state(ManagerStates.adding_equipment_name)
            
        except Exception as e:
            logger.error(f"Error in start_add_equipment: {str(e)}", exc_info=True)

    async def start_search_equipment(callback, state, lang):
        """Start equipment search"""
        try:
            search_text = "🔍 Jihoz qidirish:\n\nQidiruv so'zini kiriting:" if lang == 'uz' else "🔍 Поиск оборудования:\n\nВведите поисковый запрос:"
            await callback.message.edit_text(search_text)
            await state.set_state(ManagerStates.searching_equipment)
            
        except Exception as e:
            logger.error(f"Error in start_search_equipment: {str(e)}", exc_info=True)

    async def show_maintenance_schedule(callback, lang):
        """Show equipment maintenance schedule"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get equipment that needs maintenance
                maintenance_list = await conn.fetch(
                    '''SELECT * FROM equipment 
                       WHERE next_maintenance <= CURRENT_DATE + INTERVAL '7 days'
                       OR status = 'maintenance'
                       ORDER BY next_maintenance ASC'''
                )
                
                if not maintenance_list:
                    no_maintenance_text = (
                        "✅ Hozircha texnik xizmat ko'rsatish kerak bo'lgan jihozlar yo'q."
                        if lang == 'uz' else
                        "✅ В данный момент нет оборудования, требующего технического обслуживания."
                    )
                    await callback.message.edit_text(no_maintenance_text)
                    return
                
                if lang == 'uz':
                    maintenance_text = "🔧 <b>Texnik xizmat jadvali:</b>\n\n"
                    
                    for eq in maintenance_list:
                        status_emoji = "🟡"
                        maintenance_text += (
                            f"{status_emoji} <b>{eq.get('name', 'Noma\'lum')}</b>\n"
                            f"   📍 Joylashuv: {eq.get('location', '-')}\n"
                            f"   📅 Keyingi texnik xizmat: {eq.get('next_maintenance', '-')}\n"
                            f"   📊 Status: {eq.get('status', '-')}\n\n"
                        )
                else:
                    maintenance_text = "🔧 <b>График технического обслуживания:</b>\n\n"
                    
                    for eq in maintenance_list:
                        status_emoji = "🟡"
                        maintenance_text += (
                            f"{status_emoji} <b>{eq.get('name', 'Неизвестно')}</b>\n"
                            f"   📍 Расположение: {eq.get('location', '-')}\n"
                            f"   📅 Следующее ТО: {eq.get('next_maintenance', '-')}\n"
                            f"   📊 Статус: {eq.get('status', '-')}\n\n"
                        )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="equipment_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(maintenance_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_maintenance_schedule: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    @router.callback_query(F.data == "equipment_menu")
    async def back_to_equipment_menu(callback: CallbackQuery, state: FSMContext):
        """Return to equipment menu"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            equipment_text = "🔧 Jihozlar boshqaruvi:" if lang == 'uz' else "🔧 Управление оборудованием:"
            
            await callback.message.edit_text(
                equipment_text,
                reply_markup=get_equipment_keyboard(lang)
            )
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in back_to_equipment_menu: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    # Handle equipment name input
    @router.message(StateFilter(ManagerStates.adding_equipment_name))
    async def get_equipment_name(message: Message, state: FSMContext):
        """Get equipment name for adding"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            await state.update_data(equipment_name=message.text)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            model_text = "Jihoz modelini kiriting:" if lang == 'uz' else "Введите модель оборудования:"
            await message.answer(model_text)
            await state.set_state(ManagerStates.adding_equipment_model)
            
        except Exception as e:
            logger.error(f"Error in get_equipment_name: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.adding_equipment_model))
    async def get_equipment_model(message: Message, state: FSMContext):
        """Get equipment model for adding"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            await state.update_data(equipment_model=message.text)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            location_text = "Jihoz joylashuvini kiriting:" if lang == 'uz' else "Введите расположение оборудования:"
            await message.answer(location_text)
            await state.set_state(ManagerStates.adding_equipment_location)
            
        except Exception as e:
            logger.error(f"Error in get_equipment_model: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.adding_equipment_location))
    async def get_equipment_location(message: Message, state: FSMContext):
        """Get equipment location and save to database"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            data = await state.get_data()
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            # Save equipment to database
            conn = await bot.db.acquire()
            try:
                equipment_id = await conn.fetchval(
                    '''INSERT INTO equipment (name, model, location, status, created_by, created_at)
                       VALUES ($1, $2, $3, $4, $5, NOW())
                       RETURNING id''',
                    data['equipment_name'],
                    data['equipment_model'],
                    message.text,
                    'working',
                    user['id']
                )
                
                if equipment_id:
                    success_text = (
                        f"✅ Jihoz muvaffaqiyatli qo'shildi!\n\n"
                        f"🔧 Nom: {data['equipment_name']}\n"
                        f"🏷️ Model: {data['equipment_model']}\n"
                        f"📍 Joylashuv: {message.text}\n"
                        f"📊 Status: Ishlamoqda"
                        if lang == 'uz' else
                        f"✅ Оборудование успешно добавлено!\n\n"
                        f"🔧 Название: {data['equipment_name']}\n"
                        f"🏷️ Модель: {data['equipment_model']}\n"
                        f"📍 Расположение: {message.text}\n"
                        f"📊 Статус: Работает"
                    )
                    
                    await message.answer(success_text)
                    logger.info(f"Manager {user['id']} added equipment: {data['equipment_name']}")
                else:
                    error_text = "Jihozni qo'shishda xatolik yuz berdi." if lang == 'uz' else "Ошибка при добавлении оборудования."
                    await message.answer(error_text)
                    
            finally:
                await conn.release()
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in get_equipment_location: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.searching_equipment))
    async def search_equipment(message: Message, state: FSMContext):
        """Search equipment by name or model"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            search_query = message.text.strip()
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            conn = await bot.db.acquire()
            try:
                # Search equipment
                equipment_list = await conn.fetch(
                    '''SELECT * FROM equipment 
                       WHERE LOWER(name) LIKE LOWER($1) 
                       OR LOWER(model) LIKE LOWER($1)
                       OR LOWER(location) LIKE LOWER($1)
                       ORDER BY created_at DESC
                       LIMIT 10''',
                    f'%{search_query}%'
                )
                
                if not equipment_list:
                    not_found_text = f"❌ '{search_query}' bo'yicha hech narsa topilmadi." if lang == 'uz' else f"❌ По запросу '{search_query}' ничего не найдено."
                    await message.answer(not_found_text)
                    return
                
                if lang == 'uz':
                    result_text = f"🔍 <b>'{search_query}' bo'yicha qidiruv natijalari:</b>\n\n"
                    
                    for eq in equipment_list:
                        status_emoji = "✅" if eq.get('status') == 'working' else "❌" if eq.get('status') == 'broken' else "⚠️"
                        result_text += (
                            f"{status_emoji} <b>{eq.get('name', 'Noma\'lum')}</b>\n"
                            f"   🏷️ Model: {eq.get('model', '-')}\n"
                            f"   📍 Joylashuv: {eq.get('location', '-')}\n"
                            f"   📊 Status: {eq.get('status', '-')}\n\n"
                        )
                else:
                    result_text = f"🔍 <b>Результаты поиска по '{search_query}':</b>\n\n"
                    
                    for eq in equipment_list:
                        status_emoji = "✅"  if eq.get('status') == 'working' else "❌" if eq.get('status') == 'broken' else "⚠️"
                        result_text += (
                            f"{status_emoji} <b>{eq.get('name', 'Неизвестно')}</b>\n"
                            f"   🏷️ Модель: {eq.get('model', '-')}\n"
                            f"   📍 Расположение: {eq.get('location', '-')}\n"
                            f"   📊 Статус: {eq.get('status', '-')}\n\n"
                        )
                
                await message.answer(result_text, parse_mode='HTML')
                
            finally:
                await conn.release()
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in search_equipment: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    return router
