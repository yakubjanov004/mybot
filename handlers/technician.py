from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Dict, Any, List
from keyboards.technician_buttons import (
    get_technician_main_menu_keyboard, 
    get_language_keyboard, get_contact_keyboard, get_task_action_keyboard, get_completion_keyboard, get_technician_selection_keyboard, get_back_technician_keyboard
)
from states.technician_states import TechnicianStates
from loader import bot
from utils.i18n import i18n
from database.queries import get_user_by_telegram_id, get_zayavka_by_id, start_task
from utils.logger import setup_logger, log_user_action, log_error
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import functools
from utils.cache_manager import CacheManager
from utils.inline_cleanup import safe_remove_inline, safe_remove_inline_call
from utils.get_lang import get_user_lang
from utils.get_role import get_user_role
from utils.templates import get_template_text

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
        # message_or_call ni aniqlash
        message_or_call = args[0] if args else kwargs.get('message_or_call')
        user_id = message_or_call.from_user.id
        user = await get_user_by_telegram_id(user_id)
        if not user or user.get('role') != 'technician':
            text = "Sizda montajchi huquqi yo'q."
            if hasattr(message_or_call, 'answer'):
                await message_or_call.answer(text)
            else:
                await message_or_call.message.answer(text)
            return
        return await func(*args, **kwargs)
    return wrapper

# @router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start command handler for technicians"""
    try:
        await state.clear()
        db_user = await get_user_by_telegram_id(message.from_user.id)
        logger.info(f"Technician start - Foydalanuvchi tekshirildi: {message.from_user.id}, natija: {db_user}")
        if not db_user or db_user.get('role') != 'technician':
            await safe_remove_inline(message)
            lang = await get_user_lang(message.from_user.id)
            text = await get_template_text(lang, 'technician', 'no_access')
            await message.answer(text)
            return
        lang = await get_user_lang(message.from_user.id)
        role = await get_user_role(message.from_user.id)
        if not db_user['phone_number']:
            await safe_remove_inline(message)
            text = await get_template_text(lang, role, "share_contact")
            await message.answer(text, reply_markup=get_contact_keyboard(lang))
            await state.set_state(TechnicianStates.waiting_for_phone_number)
        else:
            await safe_remove_inline(message)
            text = await get_template_text(lang, role, "technician_welcome")
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
        text = await get_template_text(lang, 'technician', 'error_occurred')
        await message.answer(text)

@router.message(F.text.in_(["Vazifalarim", "Мои задачи"]))
@require_technician
async def my_tasks(message: Message, state: FSMContext):
    """Show technician's assigned tasks"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        from database.queries import get_technician_tasks
        tasks = await get_technician_tasks(user['id'])
        if not tasks:
            await message.answer(
                i18n.get_message(lang, "technician.no_my_tasks"),
                reply_markup=get_back_technician_keyboard(lang)  # Lang parametri qo'shildi
            )
            return
        await message.answer(
            i18n.get_message(lang, "technician.my_tasks_list").format(count=len(tasks)),
            reply_markup=get_back_technician_keyboard(lang)  # Lang parametri qo'shildi
        )
        for task in tasks:
            status_emoji = "🆕" if task['status'] == 'assigned' else ("✅" if task['status'] == 'accepted' else ("⏳" if task['status'] == 'in_progress' else "📋"))
            status_text = i18n.get_message(lang, f"statuses.{task['status']}") or task['status']
            task_text = (
                f"{status_emoji} {i18n.get_message(lang, 'technician.task_details')} #{task['id']}\n"
                f"👤 {i18n.get_message(lang, 'client.welcome').split(' ')[0]}: {task['client_name']}\n"
                f"📞 Telefon: {task['client_phone'] or 'Kiritilmagan'}\n"
                f"📝 {i18n.get_message(lang, 'technician.task_description')}: {task['description']}\n"
                f"📍 Manzil: {task['address']}\n"
                f"📅 {i18n.get_message(lang, 'technician.task_date')}: {task['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                f"📊 {i18n.get_message(lang, 'technician.task_status')}: {status_text}"
            )
            if task.get('media'):
                await message.answer_photo(
                    photo=task['media'],
                    caption=task_text,
                    reply_markup=get_task_action_keyboard(task['id'], task['status'], lang)  # Lang parametri qo'shildi
                )
            else:
                await message.answer(
                    task_text,
                    reply_markup=get_task_action_keyboard(task['id'], task['status'], lang)  # Lang parametri qo'shildi
                )
    except Exception as e:
        logger.error(f"Error in my_tasks: {str(e)}", exc_info=True)
        await message.answer(i18n.get_message(lang, "error"))

@router.message(F.text.in_([
    "Hisobot", "Hisobotlar",  # uz
    "Отчет", "Отчеты"         # ru
]))
@require_technician
async def reports(message: Message, state: FSMContext):
    """Show technician's completed work stats with a single 'Batafsil'/'Подробнее' button (multilingual)"""
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

        # Statistika matni 2 tilda
        if lang == "ru":
            stat_text = (
                f"\U0001F4DD {i18n.get_message(lang, 'technician.reports_list')}\n"
                f"Всего завершено: {count_total}\n"
                f"Сегодня: {count_today}\n"
                f"За неделю: {count_week}\n"
                f"За месяц: {count_month}\n"
            )
            details_btn_text = "Подробнее"
        else:
            stat_text = (
                f"\U0001F4DD {i18n.get_message(lang, 'technician.reports_list')}\n"
                f"Jami yakunlangan: {count_total} ta\n"
                f"Bugun: {count_today} ta\n"
                f"Haftada: {count_week} ta\n"
                f"Oyda: {count_month} ta\n"
            )
            details_btn_text = "Batafsil"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=details_btn_text, callback_data="techreport_page_1")]
        ])
        await message.answer(stat_text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in reports: {str(e)}", exc_info=True)
        await message.answer(i18n.get_message(lang, "error"))

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
            await call.message.edit_text(i18n.get_message(lang, 'technician.no_reports'))
            await call.answer()
            return
        lines = []
        for t in page_tasks:
            date_str = t['completed_at'].strftime('%d.%m.%Y %H:%M') if t.get('completed_at') else '-'
            created_str = t['created_at'].strftime('%d.%m.%Y %H:%M') if t.get('created_at') else '-'
            solution = t.get('solution', '-')
            lines.append(
                f"\U0001F4DD {i18n.get_message(lang, 'technician.task_details')} #{t['id']}\n"
                f"\U0001F464 {i18n.get_message(lang, 'client.welcome').split(' ')[0]}: {t.get('user_name', '-')}\n"
                f"\U0001F4DE {i18n.get_message(lang, 'client.order_status')}: {t.get('client_phone', '-')}\n"
                f"\U0001F4DD {i18n.get_message(lang, 'technician.task_description')}: {t.get('description', '-')}\n"
                f"\U0001F4CD {i18n.get_message(lang, 'enter_order_address')}: {t.get('address', '-')}\n"
                f"\U0001F4C5 {i18n.get_message(lang, 'technician.task_date')}: {created_str}\n"
                f"\U0001F4CA {i18n.get_message(lang, 'technician.task_status')}: {i18n.get_message(lang, 'statuses.completed')}\n"
                f"\U0001F551 {i18n.get_message(lang, 'technician.completed_at') if 'completed_at' in i18n.messages[lang].get('technician', {}) else ('Yakunlangan' if lang=='uz' else 'Завершено')}: {date_str}\n"
                f"\U0001F4AC {i18n.get_message(lang, 'technician.solution') if 'solution' in i18n.messages[lang].get('technician', {}) else ('Yechim' if lang=='uz' else 'Решение')}: {solution}\n"
                "-----------------------------"
            )
        text = i18n.get_message(lang, 'technician.reports_list') + "\n\n" + "\n".join(lines)
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text=("⬅️ Orqaga" if lang=="uz" else "⬅️ Назад"), callback_data=f"techreport_page_{page-1}"))
        if end < len(completed):
            nav_buttons.append(InlineKeyboardButton(text=("Oldinga ➡️" if lang=="uz" else "Вперёд ➡️"), callback_data=f"techreport_page_{page+1}"))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[nav_buttons] if nav_buttons else [])
        await call.message.edit_text(text, reply_markup=keyboard)
        await call.answer()
    except Exception as e:
        logger.error(f"Error in report_details_page: {str(e)}", exc_info=True)
        await call.message.edit_text(i18n.get_message(lang, 'error'))

@router.message(F.text.in_(["Tilni o'zgartirish", "Изменить язык"]))
@require_technician
async def show_language_keyboard(message: Message, state: FSMContext):
    """Show language selection keyboard"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(
            i18n.get_message(lang, "select_language"),
            reply_markup=get_language_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in show_language_keyboard: {str(e)}", exc_info=True)
        await message.answer(i18n.get_message(lang, "error"))

@router.callback_query(F.data.in_(["lang_uz", "lang_ru"]))
async def change_language(call: CallbackQuery, state: FSMContext):
    try:
        await call.answer()
        user = await get_user_by_telegram_id(call.from_user.id)
        if not user:
            return
        new_lang = "uz" if call.data == "lang_uz" else "ru"
        role = user.get('role')
        from database.queries import _pool
        async with _pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET language = $1 WHERE telegram_id = $2",
                new_lang, str(call.from_user.id)
            )
        # Reply buttonni yangi tilga mos qilib yuborish
        if role == "technician":
            from keyboards.technician_buttons import get_technician_main_menu_keyboard
            reply_markup = get_technician_main_menu_keyboard(new_lang)
            menu_text = i18n.get_message(new_lang, "technician.main_menu")
        elif role == "client":
            from keyboards.client_buttons import get_main_menu_keyboard
            reply_markup = get_main_menu_keyboard(new_lang)
            menu_text = i18n.get_message(new_lang, "main_menu")
        elif role == "admin":
            from keyboards.admin_buttons import admin_main_menu
            reply_markup = admin_main_menu
            menu_text = i18n.get_message(new_lang, "admin.welcome") or "Admin paneliga xush kelibsiz!"
        else:
            reply_markup = None
            menu_text = "Bosh menyu."
        await call.message.edit_text(i18n.get_message(new_lang, "language_changed"))
        await call.message.answer(
            menu_text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in change_language: {str(e)}", exc_info=True)
        await call.message.answer("Xatolik yuz berdi.")

@router.message(F.text.in_([i18n.get_message('uz', 'back'), i18n.get_message('ru', 'back')]))
@require_technician
async def handle_back(message: Message, state: FSMContext):
    """Handle back button"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(
            i18n.get_message(lang, "technician.main_menu"),
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
    except Exception as e:
        logger.error(f"Error in handle_back: {str(e)}", exc_info=True)
        await message.answer(i18n.get_message(lang, "error"))

@router.message(TechnicianStates.waiting_for_phone_number, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Process contact sharing for technicians"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            await message.answer(i18n.get_message('uz', 'admin.no_access'))
            return
        lang = user.get('language', 'uz')
        from database.queries import _pool
        async with _pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET phone_number = $1 WHERE telegram_id = $2",
                message.contact.phone_number, str(message.from_user.id)
            )
        await message.answer(
            i18n.get_message(lang, "technician.welcome"),
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
        logger.info(f"Technician contact updated: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in process_contact: {str(e)}", exc_info=True)
        await message.answer(i18n.get_message(lang, "error"))

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
    text = await get_template_text(
        lang, 'technician', 'tech_order_full',
        order_id=zayavka['id'],
        client_name=zayavka.get('user_name', '-'),
        client_phone=zayavka.get('phone_number', '-'),
        address=zayavka.get('address', '-'),
        description=zayavka.get('description', '-'),
        created_at=zayavka.get('created_at', '-')
    )
    await call.message.answer(text, reply_markup=get_task_inline_keyboard(zayavka_id, 'accepted', lang))
    await save_task_message(call.from_user.id, zayavka_id, call.message.chat.id, call.message.message_id)
    await call.message.delete()
    # Menejerlarga qabul qilindi xabarini yuborish (2ta tilda)
    from database.queries import get_managers_telegram_ids
    managers = await get_managers_telegram_ids()
    now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
    try:
        uz_text = (
            f"✅ Vazifa #{zayavka_id} qabul qilindi!\n\n"
            f"👨‍🔧 Montajchi: {call.from_user.full_name}\n"
            f"Telegram ID: {call.from_user.id}\n"
            f"⏰ Sana va vaqt: {now_str}"
        )
        ru_text = (
            f"✅ Заявка #{zayavka_id} принята!\n\n"
            f"👨‍🔧 Монтажник: {call.from_user.full_name}\n"
            f"Telegram ID: {call.from_user.id}\n"
            f"⏰ Дата и время: {now_str}"
        )
        for manager_id in managers:
            await bot.send_message(chat_id=manager_id, text=uz_text)
            await bot.send_message(chat_id=manager_id, text=ru_text)
    except Exception as e:
        logger.error(f"Menejerlarga vazifa qabul qilindi xabarini yuborishda xatolik: {e}")

@router.callback_query(F.data.startswith("start_task_"))
@require_technician
async def start_task_handler(call: CallbackQuery, state: FSMContext):
    """Vazifani boshlash"""
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
    await call.message.edit_reply_markup(reply_markup=get_task_inline_keyboard(zayavka_id, 'in_progress', await get_lang(call.from_user.id)))
    # Message remains, just update inline
    # Menejerlarga boshladi xabarini yuborish (2ta tilda)
    from database.queries import get_managers_telegram_ids
    managers = await get_managers_telegram_ids()
    now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
    try:
        uz_text = (
            f"▶️ Vazifa #{zayavka_id} boshlandi!\n\n"
            f"👨‍🔧 Montajchi: {call.from_user.full_name}\n"
            f"Telegram ID: {call.from_user.id}\n"
            f"⏰ Sana va vaqt: {now_str}"
        )
        ru_text = (
            f"▶️ Заявка #{zayavka_id} начата!\n\n"
            f"👨‍🔧 Монтажник: {call.from_user.full_name}\n"
            f"Telegram ID: {call.from_user.id}\n"
            f"⏰ Дата и время: {now_str}"
        )
        for manager_id in managers:
            await bot.send_message(chat_id=manager_id, text=uz_text)
            await bot.send_message(chat_id=manager_id, text=ru_text)
    except Exception as e:
        logger.error(f"Menejerlarga vazifa boshlandi xabarini yuborishda xatolik: {e}")

@router.callback_query(F.data.startswith("complete_task_"))
@require_technician
async def complete_task_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    # Inline keyboardni birinchi bosishda yo'qotish
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    zayavka_id = int(call.data.split("_")[-1])
    await state.update_data(completing_zayavka_id=zayavka_id)
    await state.set_state(TechnicianStates.waiting_for_completion_comment)
    await call.message.edit_text("📝 Bajarilgan ish haqida izoh yozing:")

@router.callback_query(F.data.startswith("complete_with_comment_"))
@require_technician
async def complete_with_comment_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    # Inline keyboardni birinchi bosishda yo'qotish
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    zayavka_id = int(call.data.split("_")[-1])
    await state.update_data(completing_zayavka_id=zayavka_id)
    await state.set_state(TechnicianStates.waiting_for_completion_comment)
    await call.message.edit_text("📝 Bajarilgan ish haqida izoh yozing:")

@router.message(TechnicianStates.waiting_for_completion_comment)
@require_technician
async def process_completion_comment(message: Message, state: FSMContext):
    """Yakunlash izohi"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user.get('role') != 'technician':
        return
    
    data = await state.get_data()
    zayavka_id = data.get('completing_zayavka_id')
    
    if not zayavka_id:
        await message.answer("Xatolik yuz berdi!")
        return
    
    await complete_task_final(message, user, zayavka_id, message.text)
    await state.clear()

async def complete_task_final(message_or_call, user, zayavka_id, solution_text):
    """Vazifani yakuniy yakunlash (2 tilda)"""
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
        for manager_id in managers:
            try:
                manager = await get_user_by_telegram_id(manager_id)
                lang = manager.get('language', 'uz') if manager else 'uz'
                if lang == 'ru':
                    manager_text = (
                        f"✅ Заявка #{zayavka_id} завершена!\n\n"
                        f"👨‍🔧 Техник: {user['full_name']}\n"
                        f"👤 Клиент: {zayavka['client_name']}\n"
                        f"📝 Описание: {zayavka['description']}\n"
                    )
                    if solution_text:
                        manager_text += f"💬 Комментарий: {solution_text}\n"
                    manager_text += f"⏰ Завершено: {datetime.now().strftime('%d.%m.%Y %H:%M') }"
                else:
                    manager_text = (
                        f"✅ Zayavka #{zayavka_id} yakunlandi!\n\n"
                        f"👨‍🔧 Technician: {user['full_name']}\n"
                        f"👤 Mijoz: {zayavka['client_name']}\n"
                        f"📝 Tavsif: {zayavka['description']}\n"
                    )
                    if solution_text:
                        manager_text += f"💬 Izoh: {solution_text}\n"
                    manager_text += f"⏰ Yakunlangan: {datetime.now().strftime('%d.%m.%Y %H:%M') }"
                await bot.send_message(chat_id=manager_id, text=manager_text)
            except Exception as e:
                logger.error(f"Menejerga xabar yuborishda xatolik: {e}")

    except Exception as e:
        logger.error(f"Vazifani yakunlashda xatolik: {e}")
        if hasattr(message_or_call, 'answer'):
            await message_or_call.answer("Xatolik yuz berdi!")

@router.callback_query(F.data.startswith("transfer_task_"))
@require_technician
async def transfer_task_handler(call: CallbackQuery, state: FSMContext):
    """Vazifani o'tkazish so'rovi"""
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    zayavka_id = int(call.data.split("_")[-1])
    await state.update_data(transferring_zayavka_id=zayavka_id)
    await state.set_state(TechnicianStates.waiting_for_transfer_reason)
    
    await call.message.edit_text("📝 O'tkazish sababini yozing:")

@router.message(TechnicianStates.waiting_for_transfer_reason)
@require_technician
async def process_transfer_reason(message: Message, state: FSMContext):
    """O'tkazish sababini qayta ishlash"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user.get('role') != 'technician':
        return
    
    data = await state.get_data()
    zayavka_id = data.get('transferring_zayavka_id')
    
    if not zayavka_id:
        await message.answer("Xatolik yuz berdi!\nПроизошла ошибка!")
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

        for manager_id in managers:
            try:
                # Try to get manager's language, fallback to 'uz'
                manager = await get_user_by_telegram_id(manager_id)
                lang = manager.get('language', 'uz') if manager else 'uz'
                if lang == 'ru':
                    await bot.send_message(
                        chat_id=manager_id,
                        text=transfer_text_ru,
                        reply_markup=transfer_keyboard_ru
                    )
                else:
                    await bot.send_message(
                        chat_id=manager_id,
                        text=transfer_text_uz,
                        reply_markup=transfer_keyboard_uz
                    )
            except Exception as e:
                logger.error(f"Menejerga o'tkazish so'rovini yuborishda xatolik: {e}")

        await message.answer("✅ O'tkazish so'rovi yuborildi! Menejer tez orada ko'rib chiqadi.\n"
                             "✅ Запрос на передачу отправлен! Менеджер скоро рассмотрит его.")
        await state.clear()
    except Exception as e:
        logger.error(f"O'tkazish so'rovini yuborishda xatolik: {e}")
        await message.answer("Xatolik yuz berdi!")

@router.callback_query(F.data.startswith("reassign_zayavka_"))
async def reassign_zayavka_handler(call: CallbackQuery, state: FSMContext):
    """Zayavkani qayta biriktirish"""
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user or user.get('role') != 'manager':
        await call.message.answer("Sizda bu amalni bajarish huquqi yo'q!")
        return
    
    zayavka_id = int(call.data.split("_")[-1])
    
    try:
        from database.queries import get_available_technicians
        technicians = await get_available_technicians()
        
        if not technicians:
            await call.message.edit_text("Hozirda bo'sh technician yo'q!")
            return
        
        await call.message.edit_text(
            "Yangi technician tanlang:",
            reply_markup=get_technician_selection_keyboard(technicians)
        )
        await state.update_data(reassigning_zayavka_id=zayavka_id)
        
    except Exception as e:
        logger.error(f"Qayta biriktirish uchun technician ro'yxatini olishda xatolik: {e}")
        await call.message.edit_text("Xatolik yuz berdi!")

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
            await callback.message.answer("Technician tanlanmagan.")
            return

        tech_telegram_id = technician.get('telegram_id')
        tech_lang = technician.get('language', 'uz')

        # Zayavka ma'lumotlarini olish
        from database.queries import get_zayavka_by_id
        application = await get_zayavka_by_id(application_id)
        if not application:
            await callback.message.answer("Zayavka topilmadi.")
            return

        # Qisqa info (assigned)
        short_info = i18n.get_template(
            tech_lang, 'technician', 'tech_order_brief',
            order_id=application['id'],
            address=application.get('address', '-'),
            description=application.get('description', '-')
        )
        from handlers.technician import get_task_inline_keyboard
        inline_kb = get_task_inline_keyboard(application_id, 'assigned', tech_lang)
        await bot.send_message(
            chat_id=tech_telegram_id,
            text=short_info,
            reply_markup=inline_kb
        )

        await callback.message.answer("Zayavka technician-ga biriktirildi.")
        await state.clear()
    except Exception as e:
        logger.error(f"manager_assign_zayavka_handler xatolik: {e}")
        await callback.message.answer("Xatolik yuz berdi!")

# Texnikka birinchi (assigned) xabarda qisqacha, lekin ko'proq info
async def notify_technician_assigned(tech_telegram_id, lang, zayavka):
    text = (
        f"🆕 {'Yangi vazifa' if lang == 'uz' else 'Новая задача'}\n"
        f"🆔 ID: {zayavka['id']}\n"
        f"👤 {'Mijoz' if lang == 'uz' else 'Клиент'}: {zayavka.get('client_name', '-') }\n"
        f"📞 {zayavka.get('phone_number', '-') }\n"
        f"📍 {'Manzil' if lang == 'uz' else 'Адрес'}: {zayavka.get('address', '-') }\n"
        f"📝 {'Tavsif' if lang == 'uz' else 'Описание'}: {zayavka.get('description', '-') }\n"
    )
    await bot.send_message(
        chat_id=tech_telegram_id,
        text=text,
        reply_markup=get_task_inline_keyboard(zayavka['id'], 'assigned', lang)
    )

# Qabul qilganda va boshlaganda esa to'liq info yuboriladi (allaqachon mavjud get_template_text orqali)
