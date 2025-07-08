from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime
from keyboards.technician_buttons import get_back_technician_keyboard, get_task_action_keyboard
from states.technician_states import TechnicianStates
from database.technician_queries import (
    get_technician_by_telegram_id, get_technician_tasks, accept_task, 
    start_task, complete_task, request_task_transfer, get_managers_telegram_ids
)
from utils.logger import setup_logger
from database.base_queries import get_zayavka_by_id, get_user_by_telegram_id, get_user_lang
from utils.logger import setup_logger
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message, cleanup_user_inline_messages
from utils.cache_manager import MemoryCache
from loader import bot
from utils.role_router import get_role_router
import functools

def get_technician_tasks_router():
    logger = setup_logger('bot.technician.tasks')
    router = get_role_router("technician")

    # Message tracking helpers
    message_cache = MemoryCache(default_ttl=3600)

    def get_task_message_key(user_id, zayavka_id):
        return f"taskmsg:{user_id}:{zayavka_id}"

    async def delete_previous_task_message(user_id, zayavka_id, bot):
        key = get_task_message_key(user_id, zayavka_id)
        msg_info = message_cache.get(key)
        if msg_info:
            try:
                await safe_delete_message(bot, msg_info['chat_id'], msg_info['message_id'])
            except Exception:
                pass
            message_cache.delete(key)

    async def save_task_message(user_id, zayavka_id, chat_id, message_id):
        key = get_task_message_key(user_id, zayavka_id)
        message_cache.set(key, {'chat_id': chat_id, 'message_id': message_id})

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

    @router.message(F.text.in_(["📋 Vazifalarim", "📋 Мои задачи"]))
    @require_technician
    async def my_tasks(message: Message, state: FSMContext):
        """Show technician's assigned tasks"""
        await cleanup_user_inline_messages(message.from_user.id)
        try:
            user = await get_technician_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            tasks = await get_technician_tasks(user['id'])
            
            if not tasks:
                if lang == 'uz':
                    await message.answer(
                        "Sizda hozircha birorta ham vazifa yo'q.",
                        reply_markup=get_back_technician_keyboard(lang)
                    )
                else:
                    await message.answer(
                        "У вас пока нет задач.",
                        reply_markup=get_back_technician_keyboard(lang)
                    )
                return
            
            if lang == 'uz':
                await message.answer(
                    f"Sizga biriktirilgan vazifalar soni: {len(tasks)} ta",
                    reply_markup=get_back_technician_keyboard(lang)
                )
            else:
                await message.answer(
                    f"Количество назначенных вам задач: {len(tasks)}",
                    reply_markup=get_back_technician_keyboard(lang)
                )
            
            for task in tasks:
                status_emoji = "🆕" if task['status'] == 'assigned' else ("✅" if task['status'] == 'accepted' else ("⏳" if task['status'] == 'in_progress' else "📋"))
                
                if lang == 'uz':
                    status_text = {
                        'assigned': 'Yangi',
                        'accepted': 'Qabul qilingan',
                        'in_progress': 'Jarayonda',
                        'completed': 'Yakunlangan'
                    }.get(task['status'], task['status'])
                    
                    task_text = (
                        f"{status_emoji} Vazifa #{task['id']}\n"
                        f"👤 Mijoz: {task['client_name']}\n"
                        f"📞 Telefon: {task['client_phone'] or 'Kiritilmagan'}\n"
                        f"📝 Tavsif: {task['description']}\n"
                        f"📍 Manzil: {task['address']}\n"
                        f"📅 Sana: {task['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                        f"📊 Status: {status_text}"
                    )
                else:
                    status_text = {
                        'assigned': 'Новая',
                        'accepted': 'Принята',
                        'in_progress': 'В процессе',
                        'completed': 'Завершена'
                    }.get(task['status'], task['status'])
                    
                    task_text = (
                        f"{status_emoji} Задача #{task['id']}\n"
                        f"👤 Клиент: {task['client_name']}\n"
                        f"📞 Телефон: {task['client_phone'] or 'Не указано'}\n"
                        f"📝 Описание: {task['description']}\n"
                        f"📍 Адрес: {task['address']}\n"
                        f"📅 Дата: {task['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                        f"📊 Статус: {status_text}"
                    )
                
                if task.get('media'):
                    await message.answer_photo(
                        photo=task['media'],
                        caption=task_text,
                        reply_markup=get_task_action_keyboard(task['id'], task['status'], lang)
                    )
                else:
                    await message.answer(
                        task_text,
                        reply_markup=get_task_action_keyboard(task['id'], task['status'], lang)
                    )
        except Exception as e:
            logger.error(f"Error in my_tasks: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            await message.answer("Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!")

    def get_task_inline_keyboard(zayavka_id, status, lang='uz'):
        """Get task inline keyboard based on status"""
        lang = (lang or 'uz').lower()
        if lang not in ['uz', 'ru']:
            lang = 'uz'
        
        texts = {
            'assigned': {
                'uz': [("✅ Qabul qilish", f"accept_task_{zayavka_id}"), ("🔄 O'tkazish so'rovi", f"transfer_task_{zayavka_id}")],
                'ru': [("✅ Принять", f"accept_task_{zayavka_id}"), ("🔄 Запрос на передачу", f"transfer_task_{zayavka_id}")]
            },
            'accepted': {
                'uz': [("▶️ Boshlash", f"start_task_{zayavka_id}"), ("🔄 O'tkazish so'rovi", f"transfer_task_{zayavka_id}")],
                'ru': [("▶️ Начать", f"start_task_{zayavka_id}"), ("🔄 Запрос на передачу", f"transfer_task_{zayavka_id}")]
            },
            'in_progress': {
                'uz': [("✅ Yakunlash", f"complete_task_{zayavka_id}")],
                'ru': [("✅ Завершить", f"complete_task_{zayavka_id}")]
            }
        }
        
        if status in texts:
            buttons = [
                [InlineKeyboardButton(text=btn_text, callback_data=cb_data)]
                for btn_text, cb_data in texts[status][lang]
            ]
            return InlineKeyboardMarkup(inline_keyboard=buttons)
        return None

    @router.callback_query(F.data.startswith("accept_task_"))
    @require_technician
    async def accept_task_callback(callback: CallbackQuery, state: FSMContext):
        """Accept a task (without starting)"""
        await answer_and_cleanup(callback)
        zayavka_id = int(callback.data.split("_")[-1])
        
        zayavka = await get_zayavka_by_id(zayavka_id)
        if not zayavka:
            await callback.message.answer("Zayavka topilmadi!")
            return
        
        if zayavka['status'] == 'in_progress':
            await callback.answer("Bu vazifa allaqachon boshlangan.")
            return
        
        if zayavka['status'] == 'completed':
            await callback.answer("Bu vazifa allaqachon yakunlangan.")
            return
        
        success = await accept_task(zayavka_id, callback.from_user.id)
        if not success:
            await callback.answer("Xatolik yuz berdi!")
            return
        
        # Delete previous short message
        await delete_previous_task_message(callback.from_user.id, zayavka_id, bot)
        
        # Send full info message
        user = await get_technician_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        if lang == 'ru':
            text = (
                f"📝 <b>Заявка №{zayavka['id']}</b>\n"
                f"👤 Клиент: {zayavka.get('user_name', '-')}\n"
                f"📞 Телефон: {zayavka.get('phone_number', '-')}\n"
                f"🏠 Адрес: {zayavka.get('address', '-')}\n"
                f"📝 Описание: {zayavka.get('description', '-')}\n"
                f"🕒 Создано: {zayavka.get('created_at', '-')}"
            )
        else:
            text = (
                f"📝 <b>Buyurtma №{zayavka['id']}</b>\n"
                f"👤 Mijoz: {zayavka.get('user_name', '-')}\n"
                f"📞 Telefon: {zayavka.get('phone_number', '-')}\n"
                f"🏠 Manzil: {zayavka.get('address', '-')}\n"
                f"📝 Tavsif: {zayavka.get('description', '-')}\n"
                f"🕒 Yaratilgan: {zayavka.get('created_at', '-')}"
            )
        
        await callback.message.answer(text, reply_markup=get_task_inline_keyboard(zayavka_id, 'accepted', lang))
        await save_task_message(callback.from_user.id, zayavka_id, callback.message.chat.id, callback.message.message_id)
        await callback.message.delete()
        
        # Notify managers about task acceptance
        managers = await get_managers_telegram_ids()
        now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        try:
            for manager in managers:
                manager_lang = manager.get('language')
                if not manager_lang or manager_lang not in ['uz', 'ru']:
                    manager_lang = 'uz'
                
                if manager_lang == 'uz':
                    manager_text = (
                        f"✅ Vazifa #{zayavka_id} qabul qilindi!\n\n"
                        f"👨‍🔧 Montajchi: {callback.from_user.full_name}\n"
                        f"Telegram ID: {callback.from_user.id}\n"
                        f"⏰ Sana va vaqt: {now_str}"
                    )
                else:
                    manager_text = (
                        f"✅ Заявка #{zayavka_id} принята!\n\n"
                        f"👨‍🔧 Монтажник: {callback.from_user.full_name}\n"
                        f"Telegram ID: {callback.from_user.id}\n"
                        f"⏰ Дата и время: {now_str}"
                    )
                
                await bot.send_message(chat_id=manager['telegram_id'], text=manager_text)
        except Exception as e:
            logger.error(f"Error sending task acceptance notification to managers: {e}")

    @router.callback_query(F.data.startswith("start_task_"))
    @require_technician
    async def start_task_callback(callback: CallbackQuery, state: FSMContext):
        """Start working on a task"""
        await answer_and_cleanup(callback)
        zayavka_id = int(callback.data.split("_")[-1])
        
        zayavka = await get_zayavka_by_id(zayavka_id)
        if not zayavka:
            await callback.message.answer("Zayavka topilmadi!")
            return
        
        if zayavka['status'] == 'in_progress':
            await callback.answer("Bu vazifa allaqachon boshlangan.")
            return
        
        if zayavka['status'] == 'completed':
            await callback.answer("Bu vazifa allaqachon yakunlangan.")
            return
        
        success = await start_task(zayavka_id, callback.from_user.id)
        if not success:
            await callback.answer("Xatolik yuz berdi!")
            return
        
        # Update inline keyboard to only 'complete'
        user = await get_technician_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        await callback.message.edit_reply_markup(reply_markup=get_task_inline_keyboard(zayavka_id, 'in_progress', lang))
        
        # Notify managers about task start
        managers = await get_managers_telegram_ids()
        now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        try:
            for manager in managers:
                manager_lang = manager.get('language')
                if not manager_lang or manager_lang not in ['uz', 'ru']:
                    manager_lang = 'uz'
                
                if manager_lang == 'uz':
                    manager_text = (
                        f"▶️ Vazifa #{zayavka_id} boshlandi!\n\n"
                        f"👨‍🔧 Montajchi: {callback.from_user.full_name}\n"
                        f"Telegram ID: {callback.from_user.id}\n"
                        f"⏰ Sana va vaqt: {now_str}"
                    )
                else:
                    manager_text = (
                        f"▶️ Заявка #{zayavka_id} начата!\n\n"
                        f"👨‍🔧 Монтажник: {callback.from_user.full_name}\n"
                        f"Telegram ID: {callback.from_user.id}\n"
                        f"⏰ Дата и время: {now_str}"
                    )
                
                await bot.send_message(chat_id=manager['telegram_id'], text=manager_text)
        except Exception as e:
            logger.error(f"Error sending task start notification to managers: {e}")

    @router.callback_query(F.data.startswith("complete_task_"))
    @require_technician
    async def complete_task_callback(callback: CallbackQuery, state: FSMContext):
        """Handle task completion request"""
        await answer_and_cleanup(callback)
        
        # Remove inline keyboard immediately
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        
        zayavka_id = int(callback.data.split("_")[-1])
        await state.update_data(completing_zayavka_id=zayavka_id)
        await state.set_state(TechnicianStates.waiting_for_completion_comment)
        
        lang = await get_user_lang(callback.from_user.id)
        completion_text = "📝 Bajarilgan ish haqida izoh yozing:" if lang == 'uz' else "📝 Напишите комментарий о выполненной работе:"
        await callback.message.edit_text(completion_text)

    @router.message(TechnicianStates.waiting_for_completion_comment)
    @require_technician
    async def process_completion_comment(message: Message, state: FSMContext):
        """Process completion comment"""
        await cleanup_user_inline_messages(message.from_user.id)
        
        user = await get_technician_by_telegram_id(message.from_user.id)
        if not user:
            return
        
        data = await state.get_data()
        zayavka_id = data.get('completing_zayavka_id')
        
        if not zayavka_id:
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
            await message.answer(error_text)
            return
        
        await complete_task_final(message, user, zayavka_id, message.text)
        await state.clear()

    async def complete_task_final(message_or_call, user, zayavka_id, solution_text):
        """Final task completion with notifications"""
        await cleanup_user_inline_messages(message_or_call.from_user.id)
        
        try:
            # Complete the task
            zayavka = await complete_task(zayavka_id, user['id'], solution_text)
            
            # Prepare completion messages
            uz_text = (
                f"✅ Vazifa #{zayavka_id} yakunlandi!\n\n"
                f"👤 Mijoz: {zayavka['client_name']}\n"
                f"📝 Tavsif: {zayavka['description']}\n"
                f"📍 Manzil: {zayavka['address']}\n"
            )
            if solution_text:
                uz_text += f"💬 Izoh: {solution_text}\n"
            uz_text += f"⏰ Yakunlangan: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            ru_text = (
                f"✅ Заявка #{zayavka_id} завершена!\n\n"
                f"👤 Клиент: {zayavka['client_name']}\n"
                f"📝 Описание: {zayavka['description']}\n"
                f"📍 Адрес: {zayavka['address']}\n"
            )
            if solution_text:
                ru_text += f"💬 Комментарий: {solution_text}\n"
            ru_text += f"⏰ Завершено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            # Remove inline keyboard
            if hasattr(message_or_call, 'edit_reply_markup'):
                try:
                    await message_or_call.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
            
            # Send confirmation to technician
            if hasattr(message_or_call, 'edit_text'):
                try:
                    await message_or_call.edit_text(uz_text)
                    await message_or_call.answer(ru_text)
                except Exception:
                    if hasattr(message_or_call, 'chat') and hasattr(message_or_call, 'message_id'):
                        await bot.send_message(chat_id=message_or_call.chat.id, text=uz_text)
                        await bot.send_message(chat_id=message_or_call.chat.id, text=ru_text)
            else:
                await message_or_call.answer(uz_text)
                await message_or_call.answer(ru_text)
            
            # Notify managers
            managers = await get_managers_telegram_ids()
            for manager in managers:
                try:
                    manager_lang = manager.get('language')
                    if not manager_lang or manager_lang not in ['uz', 'ru']:
                        manager_lang = 'uz'
                    
                    if manager_lang == 'uz':
                        manager_text = (
                            f"✅ Vazifa #{zayavka_id} yakunlandi!\n\n"
                            f"👨‍🔧 Montajchi: {user['full_name']}\n"
                            f"👤 Mijoz: {zayavka['client_name']}\n"
                            f"📝 Tavsif: {zayavka['description']}\n"
                        )
                        if solution_text:
                            manager_text += f"💬 Izoh: {solution_text}\n"
                        manager_text += f"⏰ Yakunlangan: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    else:
                        manager_text = (
                            f"✅ Заявка #{zayavka_id} завершена!\n\n"
                            f"👨‍🔧 Техник: {user['full_name']}\n"
                            f"👤 Клиент: {zayavka['client_name']}\n"
                            f"📝 Описание: {zayavka['description']}\n"
                        )
                        if solution_text:
                            manager_text += f"💬 Комментарий: {solution_text}\n"
                        manager_text += f"⏰ Завершено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    
                    await bot.send_message(chat_id=manager['telegram_id'], text=manager_text)
                except Exception as e:
                    logger.error(f"Error sending completion notification to manager: {e}")
        
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            if hasattr(message_or_call, 'answer'):
                lang = await get_user_lang(message_or_call.from_user.id)
                error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
                await message_or_call.answer(error_text)

    @router.callback_query(F.data.startswith("transfer_task_"))
    @require_technician
    async def transfer_task_callback(callback: CallbackQuery, state: FSMContext):
        """Request task transfer"""
        await answer_and_cleanup(callback)
        
        user = await get_technician_by_telegram_id(callback.from_user.id)
        zayavka_id = int(callback.data.split("_")[-1])
        await state.update_data(transferring_zayavka_id=zayavka_id)
        await state.set_state(TechnicianStates.waiting_for_transfer_reason)
        
        lang = await get_user_lang(callback.from_user.id)
        transfer_reason_text = "📝 O'tkazish sababini yozing:" if lang == 'uz' else "📝 Напишите причину передачи:"
        await callback.message.edit_text(transfer_reason_text)

    @router.message(TechnicianStates.waiting_for_transfer_reason)
    @require_technician
    async def process_transfer_reason(message: Message, state: FSMContext):
        """Process transfer reason"""
        await cleanup_user_inline_messages(message.from_user.id)
        
        user = await get_technician_by_telegram_id(message.from_user.id)
        if not user:
            return
        
        data = await state.get_data()
        zayavka_id = data.get('transferring_zayavka_id')
        
        if not zayavka_id:
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
            await message.answer(error_text)
            return
        
        try:
            # Create transfer request
            success = await request_task_transfer(zayavka_id, user['id'], message.text)
            if not success:
                lang = await get_user_lang(message.from_user.id)
                error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
                await message.answer(error_text)
                return
            
            # Notify managers
            managers = await get_managers_telegram_ids()
            
            transfer_text_uz = (
                f"🔄 Vazifa o'tkazish so'rovi!\n\n"
                f"🆔 Zayavka ID: {zayavka_id}\n"
                f"👨‍🔧 Technician: {user['full_name']}\n"
                f"📝 Sabab: {message.text}\n\n"
                f"Zayavkani boshqa technicianga o'tkazish kerakmi?"
            )
            transfer_text_ru = (
                f"🔄 Запрос на передачу задачи!\n\n"
                f"🆔 Заявка ID: {zayavka_id}\n"
                f"👨‍🔧 Техник: {user['full_name']}\n"
                f"📝 Причина: {message.text}\n\n"
                f"Нужно передать заявку другому технику?"
            )
            
            transfer_keyboard_uz = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔄 Boshqa technicianga o'tkazish",
                    callback_data=f"reassign_zayavka_{zayavka_id}"
                )]
            ])
            transfer_keyboard_ru = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔄 Передать другому технику",
                    callback_data=f"reassign_zayavka_{zayavka_id}"
                )]
            ])
            
            for manager in managers:
                try:
                    manager_lang = manager.get('language')
                    if not manager_lang or manager_lang not in ['uz', 'ru']:
                        manager_lang = 'uz'
                    
                    if manager_lang == 'uz':
                        await bot.send_message(
                            chat_id=manager['telegram_id'],
                            text=transfer_text_uz,
                            reply_markup=transfer_keyboard_uz
                        )
                    else:
                        await bot.send_message(
                            chat_id=manager['telegram_id'],
                            text=transfer_text_ru,
                            reply_markup=transfer_keyboard_ru
                        )
                except Exception as e:
                    logger.error(f"Error sending transfer request to manager: {e}")
            
            lang = await get_user_lang(message.from_user.id)
            success_text_uz = "✅ O'tkazish so'rovi yuborildi! Menejer tez orada ko'rib chiqadi."
            success_text_ru = "✅ Запрос на передачу отправлен! Менеджер скоро рассмотрит его."
            await message.answer(success_text_uz if lang == 'uz' else success_text_ru)
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing transfer request: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
            await message.answer(error_text)

    return router
