from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Dict, Any, List
from keyboards.technician_buttons import (
    get_technician_main_menu_keyboard, 
    get_language_keyboard, get_contact_keyboard, get_task_action_keyboard, get_completion_keyboard, get_technician_selection_keyboard, get_back_technician_keyboard, get_technician_help_menu, get_help_request_types_keyboard
)
from states.technician_states import TechnicianStates
from loader import bot
from database.queries import get_user_by_telegram_id, get_zayavka_by_id, start_task
from utils.logger import setup_logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import functools
from utils.cache_manager import CacheManager
from utils.inline_cleanup import safe_remove_inline, safe_remove_inline_call
from utils.get_lang import get_user_lang
from utils.get_role import get_user_role
from handlers.language import show_language_selection, process_language_change

# Setup logger
logger = setup_logger('bot.technician')

router = Router()

# Message tracking helpers
message_cache = CacheManager(max_size=2000, default_ttl=3600)

def get_task_message_key(user_id, zayavka_id):
    return f"taskmsg:{user_id}:{zayavka_id}"

async def delete_previous_task_message(user_id, zayavka_id, bot):
    key = get_task_message_key(user_id, zayavka_id)
    msg_info = message_cache.get(key)
    if msg_info:
        try:
            await bot.delete_message(chat_id=msg_info['chat_id'], message_id=msg_info['message_id'])
        except Exception:
            pass
        message_cache.delete(key)

async def save_task_message(user_id, zayavka_id, chat_id, message_id):
    key = get_task_message_key(user_id, zayavka_id)
    message_cache.set(key, {'chat_id': chat_id, 'message_id': message_id})

async def get_lang(user_id):
    user = await get_user_by_telegram_id(user_id)
    return user.get('language', 'uz') if user else 'uz'

def require_technician(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # message_or_call ni aniqlash
            message_or_call = args[0] if args else kwargs.get('message_or_call')
            user_id = message_or_call.from_user.id
            user = await get_user_by_telegram_id(user_id)
            if not user or user.get('role') != 'technician':
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

# @router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start command handler for technicians"""
    try:
        await safe_remove_inline(message)
        await state.clear()
        db_user = await get_user_by_telegram_id(message.from_user.id)
        logger.info(f"Technician start - Foydalanuvchi tekshirildi: {message.from_user.id}, natija: {db_user}")
        if not db_user or db_user.get('role') != 'technician':
            await safe_remove_inline(message)
            lang = await get_user_lang(message.from_user.id)
            text = "Sizda montajchi huquqi yo'q." if lang == 'uz' else "У вас нет прав монтажника."
            await message.answer(text)
            return
        lang = await get_user_lang(message.from_user.id)
        role = await get_user_role(message.from_user.id)
        if not db_user['phone_number']:
            await safe_remove_inline(message)
            text = "Iltimos, kontaktingizni ulashing." if lang == 'uz' else "Пожалуйста, предоставьте свой контактный номер."
            await message.answer(text, reply_markup=get_contact_keyboard(lang))
            await state.set_state(TechnicianStates.waiting_for_phone_number)
        else:
            await safe_remove_inline(message)
            text = "Xush kelibsiz! Montajchi paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать! Добро пожаловать в панель монтажника!"
            await message.answer(
                text=text,
                reply_markup=get_technician_main_menu_keyboard(lang)
            )
            await state.set_state(TechnicianStates.main_menu)
        logger.info(f"Technician start buyrug'i muvaffaqiyatli yakunlandi: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Technician start buyrug'ida xatolik: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        await safe_remove_inline(message)
        text = "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == 'uz' else "Произошла ошибка. Пожалуйста, попробуйте еще раз."
        await message.answer(text)

@router.message(F.text.in_(["📋 Vazifalarim", "📋 Мои задачи"]))
@require_technician
async def my_tasks(message: Message, state: FSMContext):
    """Show technician's assigned tasks"""
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        from database.queries import get_technician_tasks
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

@router.message(F.text.in_(["📊 Hisobot", "📊 Hisobotlar", "📊 Отчет", "📊 Отчеты"]))
@require_technician
async def reports(message: Message, state: FSMContext):
    """Show technician's completed work stats with a single 'Batafsil'/'Подробнее' button (multilingual)"""
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        from database.queries import get_zayavki_by_assigned
        tasks = await get_zayavki_by_assigned(user['id'])
        completed = [t for t in tasks if t['status'] == 'completed']
        now = datetime.now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        count_total = len(completed)
        count_today = sum(1 for t in completed if t['completed_at'] and t['completed_at'].date() == today)
        count_week = sum(1 for t in completed if t['completed_at'] and t['completed_at'].date() >= week_start)
        count_month = sum(1 for t in completed if t['completed_at'] and t['completed_at'].date() >= month_start)

        if lang == "ru":
            stat_text = (
                f"📝 Ваши отчеты\n"
                f"✅ Всего завершено: {count_total}\n"
                f"📅 Сегодня: {count_today}\n"
                f"🗓️ За неделю: {count_week}\n"
                f"📆 За месяц: {count_month}\n"
            )
            details_btn_text = "🔎 Подробнее"
        else:
            stat_text = (
                f"📝 Hisobotlaringiz\n"
                f"✅ Jami yakunlangan: {count_total} ta\n"
                f"📅 Bugun: {count_today} ta\n"
                f"🗓️ Haftada: {count_week} ta\n"
                f"📆 Oyda: {count_month} ta\n"
            )
            details_btn_text = "🔎 Batafsil"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=details_btn_text, callback_data="techreport_page_1")]
        ])
        await message.answer(stat_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in reports: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        await message.answer("Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!")

@router.callback_query(F.data.startswith("techreport_page_"))
@require_technician
async def report_details_page(call: CallbackQuery, state: FSMContext):
    try:
        page = int(call.data.split('_')[-1])
        user = await get_user_by_telegram_id(call.from_user.id)
        lang = user.get('language', 'uz')
        from database.queries import get_zayavki_by_assigned
        tasks = await get_zayavki_by_assigned(user['id'])
        completed = [t for t in tasks if t['status'] == 'completed']
        PAGE_SIZE = 3
        total_pages = (len(completed) + PAGE_SIZE - 1) // PAGE_SIZE
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_tasks = completed[start:end]
        if not page_tasks:
            no_reports_text = "Hisobotlar yo'q." if lang == 'uz' else "Отчетов нет."
            await call.message.edit_text(no_reports_text)
            await call.answer()
            return
        lines = []
        for t in page_tasks:
            date_str = t['completed_at'].strftime('%d.%m.%Y %H:%M') if t.get('completed_at') else '-'
            created_str = t['created_at'].strftime('%d.%m.%Y %H:%M') if t.get('created_at') else '-'
            solution = t.get('solution', '-')
            if lang == 'uz':
                lines.append(
                    f"📝 Vazifa tafsilotlari #{t['id']}\n"
                    f"👤 Foydalanuvchi: {t.get('user_name', '-')}\n"
                    f"📞 Buyurtma holati: {t.get('client_phone', '-')}\n"
                    f"📝 Vazifa tavsifi: {t.get('description', '-')}\n"
                    f"📍 Manzil: {t.get('address', '-')}\n"
                    f"📅 Vazifa sanasi: {created_str}\n"
                    f"📊 Vazifa holati: Yakunlangan\n"
                    f"🕑 Yakunlangan: {date_str}\n"
                    f"💬 Yechim: {solution}\n"
                    "-----------------------------"
                )
            elif lang == 'ru':
                lines.append(
                    f"📝 Детали задачи #{t['id']}\n"
                    f"👤 Пользователь: {t.get('user_name', '-')}\n"
                    f"📞 Статус заказа: {t.get('client_phone', '-')}\n"
                    f"📝 Описание задачи: {t.get('description', '-')}\n"
                    f"📍 Адрес: {t.get('address', '-')}\n"
                    f"📅 Дата задачи: {created_str}\n"
                    f"📊 Статус задачи: Завершено\n"
                    f"🕑 Завершено: {date_str}\n"
                    f"💬 Решение: {solution}\n"
                    "-----------------------------"
                )
        reports_list_text = "Hisobotlar ro'yxati:" if lang == 'uz' else "Список отчетов:"
        text = reports_list_text + "\n\n" + "\n".join(lines)
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Orqaga" if lang == "uz" else "⬅️ Назад",
                callback_data=f"techreport_page_{page-1}"
            ))
        if end < len(completed):
            nav_buttons.append(InlineKeyboardButton(
                text="Oldinga ➡️" if lang == "uz" else "Вперёд ➡️",
                callback_data=f"techreport_page_{page+1}"
            ))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[nav_buttons] if nav_buttons else [])
        await call.message.edit_text(text, reply_markup=keyboard)
        await call.answer()
    except Exception as e:
        logger.error(f"Error in report_details_page: {str(e)}", exc_info=True)
        await call.message.answer("Xatolik yuz berdi!")

@router.message(lambda message: message.text in ["🌐 Tilni o'zgartirish", "🌐 Изменить язык"])
@require_technician
async def show_language_keyboard(message: Message, state: FSMContext):
    """Show language selection keyboard for technicians"""
    await safe_remove_inline(message)
    try:
        success = await show_language_selection(message, "technician", state)
        if not success:
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
    except Exception as e:
        logger.error(f"Error in show_language_keyboard: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("tech_lang_"))
@require_technician
async def change_language(call: CallbackQuery, state: FSMContext):
    """Handle language change callback for technician role"""
    await safe_remove_inline_call(call)
    try:
        await process_language_change(
            call=call,
            role="technician",
            get_main_keyboard_func=get_technician_main_menu_keyboard,
            state=state
        )
        await state.set_state(TechnicianStates.main_menu)
    except Exception as e:
        logger.error(f"Error in change_language: {str(e)}", exc_info=True)
        lang = await get_user_lang(call.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await call.message.answer(error_text)
        await call.message.answer("Xatolik yuz berdi.")

@router.message(F.text.in_(["Orqaga", "Назад"]))
@require_technician
async def handle_back(message: Message, state: FSMContext):
    """Handle back button"""
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
        await message.answer(
            main_menu_text,
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
    except Exception as e:
        logger.error(f"Error in handle_back: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.message(TechnicianStates.waiting_for_phone_number, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Process contact sharing for technicians"""
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            no_access_text = "Sizda bu amalni bajarish huquqi yo'q." if lang == 'uz' else "У вас нет доступа к этому действию."
            await message.answer(no_access_text)
            return
        lang = user.get('language', 'uz')
        from database.queries import _pool
        async with _pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET phone_number = $1 WHERE telegram_id = $2",
                message.contact.phone_number, str(message.from_user.id)
            )
        welcome_text = "Xush kelibsiz! Montajchi paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать! Добро пожаловать в панель монтажника!"
        await message.answer(
            welcome_text,
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
        logger.info(f"Technician contact updated: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in process_contact: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

# CRM Integration for Technicians

# Inline keyboard builder
def get_task_inline_keyboard(zayavka_id, status, lang='uz'):
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
async def accept_task_handler(call: CallbackQuery, state: FSMContext):
    """Vazifani qabul qilish (boshlashsiz)"""
    await safe_remove_inline_call(call)
    zayavka_id = int(call.data.split("_")[-1])
    zayavka = await get_zayavka_by_id(zayavka_id)
    if not zayavka:
        await call.message.answer("Zayavka topilmadi!")
        return
    if zayavka['status'] == 'in_progress':
        await call.answer("Bu vazifa allaqachon boshlangan.")
        return
    if zayavka['status'] == 'completed':
        await call.answer("Bu vazifa allaqachon yakunlangan.")
        return
    from database.queries import accept_task
    await accept_task(zayavka_id, call.from_user.id)
    # Delete previous short message
    await delete_previous_task_message(call.from_user.id, zayavka_id, bot)
    # Send full info message
    lang = await get_lang(call.from_user.id)
    # get_template ishlatmasdan, xabarni qo'lda tuzamiz
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
    await call.message.answer(text, reply_markup=get_task_inline_keyboard(zayavka_id, 'accepted', lang))
    await save_task_message(call.from_user.id, zayavka_id, call.message.chat.id, call.message.message_id)
    await call.message.delete()
    # Menejerlarga qabul qilindi xabarini yuborish (har bir menejer o'z tilida)
    from database.queries import get_managers_telegram_ids
    managers = await get_managers_telegram_ids()
    now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
    try:
        for manager in managers:
            # Menejerning tilini aniqlash
            manager_lang = manager.get('language')
            if not manager_lang or manager_lang not in ['uz', 'ru']:
                manager_lang = 'uz'
            
            if manager_lang == 'uz':
                manager_text = (
                    f"✅ Vazifa #{zayavka_id} qabul qilindi!\n\n"
                    f"👨‍🔧 Montajchi: {call.from_user.full_name}\n"
                    f"Telegram ID: {call.from_user.id}\n"
                    f"⏰ Sana va vaqt: {now_str}"
                )
            else:
                manager_text = (
                    f"✅ Заявка #{zayavka_id} принята!\n\n"
                    f"👨‍🔧 Монтажник: {call.from_user.full_name}\n"
                    f"Telegram ID: {call.from_user.id}\n"
                    f"⏰ Дата и время: {now_str}"
                )
            
            await bot.send_message(chat_id=manager['telegram_id'], text=manager_text)
    except Exception as e:
        logger.error(f"Menejerlarga vazifa qabul qilindi xabarini yuborishda xatolik: {e}")

@router.callback_query(F.data.startswith("start_task_"))
@require_technician
async def start_task_handler(call: CallbackQuery, state: FSMContext):
    """Vazifani boshlash"""
    await safe_remove_inline_call(call)
    zayavka_id = int(call.data.split("_")[-1])
    zayavka = await get_zayavka_by_id(zayavka_id)
    if not zayavka:
        await call.message.answer("Zayavka topilmadi!")
        return
    if zayavka['status'] == 'in_progress':
        await call.answer("Bu vazifa allaqachon boshlangan.")
        return
    if zayavka['status'] == 'completed':
        await call.answer("Bu vazifa allaqachon yakunlangan.")
        return
    await start_task(zayavka_id, call.from_user.id)
    # Update inline keyboard to only 'complete'
    lang = await get_lang(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=get_task_inline_keyboard(zayavka_id, 'in_progress', lang))
    # Message remains, just update inline
    # Menejerlarga boshladi xabarini yuborish (har bir menejer o'z tilida)
    from database.queries import get_managers_telegram_ids
    managers = await get_managers_telegram_ids()
    now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
    try:
        for manager in managers:
            # Menejerning tilini aniqlash
            manager_lang = manager.get('language')
            if not manager_lang or manager_lang not in ['uz', 'ru']:
                manager_lang = 'uz'
            
            if manager_lang == 'uz':
                manager_text = (
                    f"▶️ Vazifa #{zayavka_id} boshlandi!\n\n"
                    f"👨‍🔧 Montajchi: {call.from_user.full_name}\n"
                    f"Telegram ID: {call.from_user.id}\n"
                    f"⏰ Sana va vaqt: {now_str}"
                )
            else:
                manager_text = (
                    f"▶️ Заявка #{zayavka_id} начата!\n\n"
                    f"👨‍🔧 Монтажник: {call.from_user.full_name}\n"
                    f"Telegram ID: {call.from_user.id}\n"
                    f"⏰ Дата и время: {now_str}"
                )
            
            await bot.send_message(chat_id=manager['telegram_id'], text=manager_text)
    except Exception as e:
        logger.error(f"Menejerlarga vazifa boshlandi xabarini yuborishda xatolik: {e}")

@router.callback_query(F.data.startswith("complete_task_"))
@require_technician
async def complete_task_handler(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline(call.message)
    await call.answer()
    # Inline keyboardni birinchi bosishda yo'qotish
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    zayavka_id = int(call.data.split("_")[-1])
    await state.update_data(completing_zayavka_id=zayavka_id)
    lang = await get_user_lang(call.from_user.id)
    completion_text = "📝 Bajarilgan ish haqida izoh yozing:" if lang == 'uz' else "📝 Напишите комментарий о выполненной работе:"
    await call.message.edit_text(completion_text)

@router.callback_query(F.data.startswith("complete_with_comment_"))
@require_technician
async def complete_with_comment_handler(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline(call.message)
    await call.answer()
    # Inline keyboardni birinchi bosishda yo'qotish
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    zayavka_id = int(call.data.split("_")[-1])
    await state.update_data(completing_zayavka_id=zayavka_id)
    lang = await get_user_lang(call.from_user.id)
    completion_text = "📝 Bajarilgan ish haqida izoh yozing:" if lang == 'uz' else "📝 Напишите комментарий о выполненной работе:"
    await call.message.edit_text(completion_text)

@router.message(TechnicianStates.waiting_for_completion_comment)
@require_technician
async def process_completion_comment(message: Message, state: FSMContext):
    """Yakunlash izohi"""
    await safe_remove_inline(message)
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user.get('role') != 'technician':
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
    """Vazifani yakuniy yakunlash (2 tilda)"""
    if hasattr(message_or_call, 'message'):
        await safe_remove_inline(message_or_call.message)
    else:
        await safe_remove_inline(message_or_call)
    try:
        from database.queries import complete_task, get_managers_telegram_ids

        # Vazifani yakunlash
        zayavka = await complete_task(zayavka_id, user['id'], solution_text)

        # O'zbekcha matn
        uz_text = (
            f"✅ Vazifa #{zayavka_id} yakunlandi!\n\n"
            f"👤 Mijoz: {zayavka['client_name']}\n"
            f"📝 Tavsif: {zayavka['description']}\n"
            f"📍 Manzil: {zayavka['address']}\n"
        )
        if solution_text:
            uz_text += f"💬 Izoh: {solution_text}\n"
        uz_text += f"⏰ Yakunlangan: {datetime.now().strftime('%d.%m.%Y %H:%M')}"

        # Ruscha matn
        ru_text = (
            f"✅ Заявка #{zayavka_id} завершена!\n\n"
            f"👤 Клиент: {zayavka['client_name']}\n"
            f"📝 Описание: {zayavka['description']}\n"
            f"📍 Адрес: {zayavka['address']}\n"
        )
        if solution_text:
            ru_text += f"💬 Комментарий: {solution_text}\n"
        ru_text += f"⏰ Завершено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"

        # Inline keyboardni yo'qotish
        if hasattr(message_or_call, 'edit_reply_markup'):
            try:
                await message_or_call.edit_reply_markup(reply_markup=None)
            except Exception:
                pass

        # Technicianga tasdiqlash (har ikkala tilda)
        if hasattr(message_or_call, 'edit_text'):
            try:
                await message_or_call.edit_text(uz_text)
                await message_or_call.answer(ru_text)
            except Exception:
                # Agar xabarni o'zgartirib bo'lmasa, yangi xabar yuboriladi
                if hasattr(message_or_call, 'chat') and hasattr(message_or_call, 'message_id'):
                    await bot.send_message(
                        chat_id=message_or_call.chat.id,
                        text=uz_text
                    )
                    await bot.send_message(
                        chat_id=message_or_call.chat.id,
                        text=ru_text
                    )
        else:
            await message_or_call.answer(uz_text)
            await message_or_call.answer(ru_text)
        
        # Mijozga xabar yuborish (faqat o'z tilida)
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
                    manager_text += f"⏰ Yakunlangan: {datetime.now().strftime('%d.%m.%Y %H:%M') }"
                else:
                    manager_text = (
                        f"✅ Заявка #{zayavka_id} завершена!\n\n"
                        f"👨‍🔧 Техник: {user['full_name']}\n"
                        f"👤 Клиент: {zayavka['client_name']}\n"
                        f"📝 Описание: {zayavka['description']}\n"
                    )
                    if solution_text:
                        manager_text += f"💬 Комментарий: {solution_text}\n"
                    manager_text += f"⏰ Завершено: {datetime.now().strftime('%d.%m.%Y %H:%M') }"
                await bot.send_message(chat_id=manager['telegram_id'], text=manager_text)
            except Exception as e:
                logger.error(f"Menejerga xabar yuborishda xatolik: {e}")

    except Exception as e:
        logger.error(f"Vazifani yakunlashda xatolik: {e}")
        if hasattr(message_or_call, 'answer'):
            lang = await get_user_lang(message_or_call.from_user.id)
            error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
            await message_or_call.answer(error_text)

@router.callback_query(F.data.startswith("transfer_task_"))
@require_technician
async def transfer_task_handler(call: CallbackQuery, state: FSMContext):
    """Vazifani o'tkazish so'rovi"""
    await safe_remove_inline_call(call)
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    zayavka_id = int(call.data.split("_")[-1])
    await state.update_data(transferring_zayavka_id=zayavka_id)
    await state.set_state(TechnicianStates.waiting_for_transfer_reason)
    
    lang = await get_user_lang(call.from_user.id)
    transfer_reason_text = "📝 O'tkazish sababini yozing:" if lang == 'uz' else "📝 Напишите причину передачи:"
    await call.message.edit_text(transfer_reason_text)

@router.message(TechnicianStates.waiting_for_transfer_reason)
@require_technician
async def process_transfer_reason(message: Message, state: FSMContext):
    """O'tkazish sababini qayta ishlash"""
    await safe_remove_inline(message)
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user.get('role') != 'technician':
        return
    
    data = await state.get_data()
    zayavka_id = data.get('transferring_zayavka_id')
    
    if not zayavka_id:
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
        await message.answer(error_text)
        return

    try:
        from database.queries import request_task_transfer, get_managers_telegram_ids

        # So'rov yaratish
        await request_task_transfer(zayavka_id, user['id'], message.text)

        # Menejerlarga xabar yuborish
        managers = await get_managers_telegram_ids()

        # Prepare texts in both Uzbek and Russian
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
                # Try to get manager's language, fallback to 'uz'
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
                logger.error(f"Menejerga o'tkazish so'rovini yuborishda xatolik: {e}")

        lang = await get_user_lang(message.from_user.id)
        success_text_uz = "✅ O'tkazish so'rovi yuborildi! Menejer tez orada ko'rib chiqadi."
        success_text_ru = "✅ Запрос на передачу отправлен! Менеджер скоро рассмотрит его."
        await message.answer(success_text_uz if lang == 'uz' else success_text_ru)
        await state.clear()
    except Exception as e:
        logger.error(f"O'tkazish so'rovini yuborishda xatolik: {e}")
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("reassign_zayavka_"))
async def reassign_zayavka_handler(call: CallbackQuery, state: FSMContext):
    """Zayavkani qayta biriktirish"""
    await safe_remove_inline_call(call)
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user or user.get('role') != 'manager':
        lang = await get_user_lang(call.from_user.id)
        no_access_text = "Sizda bu amalni bajarish huquqi yo'q!" if lang == 'uz' else "У вас нет доступа к этому действию!"
        await call.message.answer(no_access_text)
        return
    
    zayavka_id = int(call.data.split("_")[-1])
    
    try:
        from database.queries import get_available_technicians
        technicians = await get_available_technicians()
        
        if not technicians:
            lang = await get_user_lang(call.from_user.id)
            no_techs_text = "Hozirda bo'sh technician yo'q!" if lang == 'uz' else "Сейчас нет доступных техников!"
            await call.message.edit_text(no_techs_text)
            return
        
        lang = await get_user_lang(call.from_user.id)
        select_tech_text = "Yangi technician tanlang:" if lang == 'uz' else "Выберите нового техника:"
        await call.message.edit_text(
            select_tech_text,
            reply_markup=get_technician_selection_keyboard(technicians)
        )
        await state.update_data(reassigning_zayavka_id=zayavka_id)
        
    except Exception as e:
        logger.error(f"Qayta biriktirish uchun technician ro'yxatini olishda xatolik: {e}")
        lang = await get_user_lang(call.from_user.id)
        error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
        await call.message.edit_text(error_text)

# nima edi o'zi bu? (Selection is a placeholder for manager assigning a zayavka to a technician)
# Real implementation would look like this:

@router.callback_query(F.data.startswith("manager_assign_zayavka_"))
async def manager_assign_zayavka_handler(callback: CallbackQuery, state: FSMContext):
    # Bu handler manager tomonidan technician-ga zayavka biriktirish uchun ishlatiladi.
    try:
        # Zayavka ID ni ajratib olish
        application_id = int(callback.data.split("_")[-1])

        # Technicianni tanlash uchun state-dan yoki boshqa joydan olish (bu yerda misol uchun state-dan)
        data = await state.get_data()
        technician = data.get('selected_technician')
        if not technician:
            lang = await get_user_lang(callback.from_user.id)
            no_tech_text = "Technician tanlanmagan." if lang == 'uz' else "Техник не выбран."
            await callback.message.answer(no_tech_text)
            return

        tech_telegram_id = technician.get('telegram_id')
        tech_lang = technician.get('language', 'uz')

        # Zayavka ma'lumotlarini olish
        from database.queries import get_zayavka_by_id
        application = await get_zayavka_by_id(application_id)
        if not application:
            lang = await get_user_lang(callback.from_user.id)
            no_app_text = "Zayavka topilmadi." if lang == 'uz' else "Заявка не найдена."
            await callback.message.answer(no_app_text)
            return

        # Qisqa info (assigned) - inline language check
        if tech_lang == 'uz':
            short_info = (
                f"🆕 Yangi buyurtma!\n"
                f"🆔 Buyurtma ID: {application['id']}\n"
                f"📍 Manzil: {application.get('address', '-')}\n"
                f"📝 Tavsif: {application.get('description', '-')}"
            )
        else:
            short_info = (
                f"🆕 Новый заказ!\n"
                f"🆔 ID заказа: {application['id']}\n"
                f"📍 Адрес: {application.get('address', '-')}\n"
                f"📝 Описание: {application.get('description', '-')}"
            )
        
        from handlers.technician import get_task_inline_keyboard
        inline_kb = get_task_inline_keyboard(application_id, 'assigned', tech_lang)
        await bot.send_message(
            chat_id=tech_telegram_id,
            text=short_info,
            reply_markup=inline_kb
        )

        lang = await get_user_lang(callback.from_user.id)
        success_text = "Zayavka technician-ga biriktirildi." if lang == 'uz' else "Заявка назначена технику."
        await callback.message.answer(success_text)
        await state.clear()
    except Exception as e:
        logger.error(f"manager_assign_zayavka_handler xatolik: {e}")
        lang = await get_user_lang(callback.from_user.id)
        error_text = "Xatolik yuz berdi!" if lang == 'uz' else "Произошла ошибка!"
        await callback.message.answer(error_text)

@router.message(F.text.in_(["🆘 Yordam", "🆘 Помощь"]))
@require_technician
async def technician_help_menu_handler(message: Message, state: FSMContext):
    """Show technician help menu"""
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        from keyboards.technician_buttons import get_technician_help_menu
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
    await safe_remove_inline_call(callback)
    try:
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        from keyboards.technician_buttons import get_help_request_types_keyboard
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
    await safe_remove_inline_call(callback)
    try:
        help_type = callback.data.split("_")[2]
        user = await get_user_by_telegram_id(callback.from_user.id)
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
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        help_type = data.get('help_type', 'general')
        
        # Determine priority based on help type
        priority = 'high' if help_type == 'emergency' else 'medium'
        
        # Create help request
        help_data = {
            'technician_id': user['id'],
            'help_type': help_type,
            'description': message.text,
            'status': 'new',
            'priority': priority
        }
        
        from database.quality_queries import create_help_request, get_managers_list
        help_request_id = await create_help_request(help_data)
        
        if help_request_id:
            # Send notification to all managers
            managers = await get_managers_list()
            
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

@router.callback_query(F.data == "tech_send_location")
@require_technician
async def tech_send_location_handler(callback: CallbackQuery, state: FSMContext):
    """Request location from technician"""
    await safe_remove_inline_call(callback)
    try:
        user = await get_user_by_telegram_id(callback.from_user.id)
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
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        location = message.location
        
        # Send location to all managers
        from database.queries import get_managers_telegram_ids
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
    await safe_remove_inline_call(callback)
    try:
        user = await get_user_by_telegram_id(callback.from_user.id)
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
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        # Send message to all managers
        from database.queries import get_managers_telegram_ids
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

@router.callback_query(F.data == "tech_equipment_request")
@require_technician
async def tech_equipment_request_handler(callback: CallbackQuery, state: FSMContext):
    """Request equipment from warehouse"""
    await safe_remove_inline_call(callback)
    try:
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.set_state(TechnicianStates.waiting_for_equipment_request)
        equipment_text = "Kerakli jihozlar ro'yxatini yozing:" if lang == 'uz' else "Напишите список необходимого оборудования:"
        await callback.message.edit_text(equipment_text)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in tech equipment request: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(TechnicianStates.waiting_for_equipment_request)
@require_technician
async def process_equipment_request(message: Message, state: FSMContext):
    """Process equipment request and send to warehouse"""
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        # Send equipment request to warehouse staff and managers
        from database.queries import get_warehouse_staff, get_managers_telegram_ids
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

@router.callback_query(F.data == "tech_main_menu")
@require_technician
async def tech_back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Go back to technician main menu"""
    await safe_remove_inline_call(callback)
    try:
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
        await callback.message.edit_text(
            main_menu_text,
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error going back to main menu: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "tech_help_menu")
@require_technician
async def tech_back_to_help_menu(callback: CallbackQuery, state: FSMContext):
    """Go back to help menu"""
    await safe_remove_inline_call(callback)
    try:
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        from keyboards.technician_buttons import get_technician_help_menu
        help_text = "Yordam bo'limi" if lang == 'uz' else "Раздел помощи"
        await callback.message.edit_text(
            help_text,
            reply_markup=get_technician_help_menu(lang)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error going back to help menu: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

# Completion comment handler
@router.message(lambda message: message.text and any(
    data.get('completing_zayavka_id') for data in [{}]  # This will be replaced by actual state data
))
async def handle_completion_comment(message: Message, state: FSMContext):
    """Handle completion comment from technician"""
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            return
        
        data = await state.get_data()
        zayavka_id = data.get('completing_zayavka_id')
        
        if zayavka_id:
            await complete_task_final(message, user, zayavka_id, message.text)
            await state.clear()
    except Exception as e:
        logger.error(f"Error handling completion comment: {str(e)}", exc_info=True)

# Main menu handler
@router.message(F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
@require_technician
async def main_menu_handler(message: Message, state: FSMContext):
    """Handle main menu button"""
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
        await message.answer(
            main_menu_text,
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
    except Exception as e:
        logger.error(f"Error in main menu handler: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

# Helper function to get task action keyboard
def get_task_action_keyboard(task_id: int, status: str, lang: str = 'uz') -> InlineKeyboardMarkup:
    """Get task action keyboard based on status"""
    buttons = []
    
    if status == 'assigned':
        accept_text = "✅ Qabul qilish" if lang == 'uz' else "✅ Принять"
        transfer_text = "🔄 O'tkazish so'rovi" if lang == 'uz' else "🔄 Запрос на передачу"
        buttons = [
            [InlineKeyboardButton(text=accept_text, callback_data=f"accept_task_{task_id}")],
            [InlineKeyboardButton(text=transfer_text, callback_data=f"transfer_task_{task_id}")]
        ]
    elif status == 'accepted':
        start_text = "▶️ Boshlash" if lang == 'uz' else "▶️ Начать"
        transfer_text = "🔄 O'tkazish so'rovi" if lang == 'uz' else "🔄 Запрос на передачу"
        buttons = [
            [InlineKeyboardButton(text=start_text, callback_data=f"start_task_{task_id}")],
            [InlineKeyboardButton(text=transfer_text, callback_data=f"transfer_task_{task_id}")]
        ]
    elif status == 'in_progress':
        complete_text = "✅ Yakunlash" if lang == 'uz' else "✅ Завершить"
        buttons = [
            [InlineKeyboardButton(text=complete_text, callback_data=f"complete_task_{task_id}")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
