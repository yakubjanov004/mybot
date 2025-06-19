from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.technician_buttons import (
    get_technician_main_menu_keyboard, get_back_keyboard,
    get_language_keyboard, get_contact_keyboard
)
from keyboards.client_buttons import get_task_action_keyboard, get_completion_keyboard, get_technician_selection_keyboard
from states.technician_states import TechnicianStates
from loader import bot
from utils.i18n import i18n
from database.queries import get_user_by_telegram_id
from utils.logger import logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

router = Router()

async def get_lang(user_id):
    user = await get_user_by_telegram_id(user_id)
    return user.get('language', 'uz') if user else 'uz'

# @router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start command handler for technicians"""
    try:
        await state.clear()
        
        db_user = await get_user_by_telegram_id(message.from_user.id)
        logger.info(f"Technician start - Foydalanuvchi tekshirildi: {message.from_user.id}, natija: {db_user}")
        
        if not db_user or db_user.get('role') != 'technician':
            await message.answer("Sizda montajchi huquqi yo'q. Iltimos, administrator bilan bog'laning.")
            return
        
        lang = db_user.get('language', 'uz')
        
        if not db_user['phone_number']:
            await message.answer(i18n.get_message(lang, "share_contact"), reply_markup=get_contact_keyboard(lang))
            await state.set_state(TechnicianStates.waiting_for_phone_number)
        else:
            await message.answer(
                text=i18n.get_message(lang, "technician_welcome"),
                reply_markup=get_technician_main_menu_keyboard(lang)
            )
            await state.set_state(TechnicianStates.main_menu)
        
        logger.info(f"Technician start buyrug'i muvaffaqiyatli yakunlandi: {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Technician start buyrug'ida xatolik: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@router.message(F.text.in_(["Yangi topshiriqlar", "Новые задания"]))
async def new_tasks(message: Message, state: FSMContext):
    """Show new unassigned tasks"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            await message.answer("Sizda montajchi huquqi yo'q.")
            return
        
        lang = user.get('language', 'uz')
        
        # Here you would fetch new unassigned tasks from database
        # For now, showing a placeholder message
        await message.answer(
            i18n.get_message(lang, "new_tasks_list"),
            reply_markup=get_back_keyboard(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in new_tasks: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi.")

@router.message(F.text.in_(["Vazifalarim", "Мои задачи"]))
async def my_tasks(message: Message, state: FSMContext):
    """Show technician's assigned tasks"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            await message.answer("Sizda montajchi huquqi yo'q.")
            return
        
        lang = user.get('language', 'uz')
        
        # Technician vazifalarini olish
        from database.queries import get_technician_tasks
        tasks = await get_technician_tasks(user['id'])
        
        if not tasks:
            await message.answer(
                "📋 Sizda hozirda vazifa yo'q.",
                reply_markup=get_back_keyboard(lang)
            )
            return
        
        await message.answer(
            f"📋 Sizning vazifalaringiz ({len(tasks)} ta):",
            reply_markup=get_back_keyboard(lang)
        )
        
        # Har bir vazifani ko'rsatish
        for task in tasks:
            status_emoji = "🆕" if task['status'] == 'assigned' else "⏳"
            task_text = (
                f"{status_emoji} Vazifa #{task['id']}\n"
                f"👤 Mijoz: {task['client_name']}\n"
                f"📞 Telefon: {task['client_phone'] or 'Kiritilmagan'}\n"
                f"📝 Tavsif: {task['description']}\n"
                f"📍 Manzil: {task['address']}\n"
                f"📅 Sana: {task['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                f"📊 Status: {task['status']}"
            )
            
            if task.get('media'):
                await message.answer_photo(
                    photo=task['media'],
                    caption=task_text,
                    reply_markup=get_task_action_keyboard(task['id'])
                )
            else:
                await message.answer(
                    task_text,
                    reply_markup=get_task_action_keyboard(task['id'])
                )
        
    except Exception as e:
        logger.error(f"Error in my_tasks: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi.")

@router.message(F.text.in_(["Hisobot", "Отчёт"]))
async def reports(message: Message, state: FSMContext):
    """Show technician's completed work reports"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            await message.answer("Sizda montajchi huquqi yo'q.")
            return
        
        lang = user.get('language', 'uz')
        
        # Here you would fetch technician's completed work reports from database
        # For now, showing a placeholder message
        await message.answer(
            i18n.get_message(lang, "reports_list"),
            reply_markup=get_back_keyboard(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in reports: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi.")

@router.message(F.text.in_(["Tilni o'zgartirish", "Изменить язык"]))
async def show_language_keyboard(message: Message, state: FSMContext):
    """Show language selection keyboard"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            await message.answer("Sizda montajchi huquqi yo'q.")
            return
        
        lang = user.get('language', 'uz')
        
        await message.answer(
            i18n.get_message(lang, "select_language"),
            reply_markup=get_language_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in show_language_keyboard: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi.")

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
                new_lang, call.from_user.id
            )
        # Reply buttonni yangi tilga mos qilib yuborish
        if role == "technician":
            from keyboards.technician_buttons import get_technician_main_menu_keyboard
            reply_markup = get_technician_main_menu_keyboard(new_lang)
            menu_text = i18n.get_message(new_lang, "technician_main_menu")
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
async def handle_back(message: Message, state: FSMContext):
    """Handle back button"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            await message.answer("Sizda montajchi huquqi yo'q.")
            return
        
        lang = user.get('language', 'uz')
        
        await message.answer(
            i18n.get_message(lang, "technician_main_menu"),
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
        
    except Exception as e:
        logger.error(f"Error in handle_back: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi.")

@router.message(TechnicianStates.waiting_for_phone_number, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Process contact sharing for technicians"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user.get('role') != 'technician':
            await message.answer("Sizda montajchi huquqi yo'q.")
            return
        
        lang = user.get('language', 'uz')
        from database.queries import _pool
        async with _pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET phone_number = $1 WHERE telegram_id = $2",
                message.contact.phone_number, message.from_user.id
            )
        
        await message.answer(
            i18n.get_message(lang, "technician_welcome"),
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
        
        logger.info(f"Technician contact updated: {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in process_contact: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi.")

# CRM Integration for Technicians

@router.callback_query(F.data.startswith("start_task_"))
async def start_task_handler(call: CallbackQuery, state: FSMContext):
    """Vazifani boshlash"""
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user or user.get('role') != 'technician':
        await call.message.answer("Sizda technician huquqi yo'q!")
        return
    
    zayavka_id = int(call.data.split("_")[-1])
    
    try:
        from database.queries import start_task
        await start_task(zayavka_id, user['id'])
        
        await call.message.edit_text(
            f"▶️ Vazifa #{zayavka_id} boshlandi!\n\n"
            f"{call.message.text}",
            reply_markup=get_task_action_keyboard(zayavka_id)
        )
        
    except Exception as e:
        logger.error(f"Vazifani boshlashda xatolik: {e}")
        await call.message.answer("Xatolik yuz berdi!")

@router.callback_query(F.data.startswith("complete_task_"))
async def complete_task_handler(call: CallbackQuery, state: FSMContext):
    """Vazifani yakunlash"""
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user or user.get('role') != 'technician':
        await call.message.answer("Sizda technician huquqi yo'q!")
        return
    
    zayavka_id = int(call.data.split("_")[-1])
    
    await call.message.edit_text(
        "Vazifani qanday yakunlamoqchisiz?",
        reply_markup=get_completion_keyboard(zayavka_id)
    )

@router.callback_query(F.data.startswith("complete_no_comment_"))
async def complete_no_comment_handler(call: CallbackQuery, state: FSMContext):
    """Izohsiz yakunlash"""
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    zayavka_id = int(call.data.split("_")[-1])
    
    await complete_task_final(call, user, zayavka_id, None)

@router.callback_query(F.data.startswith("complete_with_comment_"))
async def complete_with_comment_handler(call: CallbackQuery, state: FSMContext):
    """Izoh bilan yakunlash"""
    await call.answer()
    
    zayavka_id = int(call.data.split("_")[-1])
    await state.update_data(completing_zayavka_id=zayavka_id)
    await state.set_state(TechnicianStates.waiting_for_completion_comment)
    
    await call.message.edit_text("📝 Bajarilgan ish haqida izoh yozing:")

@router.message(TechnicianStates.waiting_for_completion_comment)
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
    """Vazifani yakuniy yakunlash"""
    try:
        from database.queries import complete_task, get_managers_telegram_ids
        
        # Vazifani yakunlash
        zayavka = await complete_task(zayavka_id, user['id'], solution_text)
        
        completion_text = (
            f"✅ Vazifa #{zayavka_id} yakunlandi!\n\n"
            f"👤 Mijoz: {zayavka['client_name']}\n"
            f"📝 Tavsif: {zayavka['description']}\n"
            f"📍 Manzil: {zayavka['address']}\n"
        )
        
        if solution_text:
            completion_text += f"💬 Izoh: {solution_text}\n"
        
        completion_text += f"⏰ Yakunlangan: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        # Technicianga tasdiqlash
        if hasattr(message_or_call, 'edit_text'):
            await message_or_call.edit_text(completion_text)
        else:
            await message_or_call.answer(completion_text)
        
        # Mijozga xabar yuborish
        try:
            await bot.send_message(
                chat_id=zayavka['client_telegram_id'],
                text=f"✅ Sizning zayavkangiz #{zayavka_id} yakunlandi!\n\n"
                     f"📝 Tavsif: {zayavka['description']}\n"
                     f"📍 Manzil: {zayavka['address']}\n" +
                     (f"💬 Technician izohi: {solution_text}\n" if solution_text else "") +
                     f"⏰ Yakunlangan: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                     f"Xizmatimizdan foydalanganingiz uchun rahmat! 🙏"
            )
        except Exception as e:
            logger.error(f"Mijozga xabar yuborishda xatolik: {e}")
        
        # Menejerlarга xabar yuborish
        managers = await get_managers_telegram_ids()
        for manager_id in managers:
            try:
                await bot.send_message(
                    chat_id=manager_id,
                    text=f"✅ Zayavka #{zayavka_id} yakunlandi!\n\n"
                         f"👨‍🔧 Technician: {user['full_name']}\n"
                         f"👤 Mijoz: {zayavka['client_name']}\n"
                         f"📝 Tavsif: {zayavka['description']}\n" +
                         (f"💬 Izoh: {solution_text}\n" if solution_text else "") +
                         f"⏰ Yakunlangan: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
            except Exception as e:
                logger.error(f"Menejerga xabar yuborishda xatolik: {e}")
        
    except Exception as e:
        logger.error(f"Vazifani yakunlashda xatolik: {e}")
        if hasattr(message_or_call, 'answer'):
            await message_or_call.answer("Xatolik yuz berdi!")

@router.callback_query(F.data.startswith("transfer_task_"))
async def transfer_task_handler(call: CallbackQuery, state: FSMContext):
    """Vazifani o'tkazish so'rovi"""
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user or user.get('role') != 'technician':
        await call.message.answer("Sizda technician huquqi yo'q!")
        return
    
    zayavka_id = int(call.data.split("_")[-1])
    await state.update_data(transferring_zayavka_id=zayavka_id)
    await state.set_state(TechnicianStates.waiting_for_transfer_reason)
    
    await call.message.edit_text("📝 O'tkazish sababini yozing:")

@router.message(TechnicianStates.waiting_for_transfer_reason)
async def process_transfer_reason(message: Message, state: FSMContext):
    """O'tkazish sababini qayta ishlash"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user.get('role') != 'technician':
        return
    
    data = await state.get_data()
    zayavka_id = data.get('transferring_zayavka_id')
    
    if not zayavka_id:
        await message.answer("Xatolik yuz berdi!")
        return
    
    try:
        from database.queries import request_task_transfer, get_managers_telegram_ids
        
        # So'rov yaratish
        await request_task_transfer(zayavka_id, user['id'], message.text)
        
        # Menejerlarга xabar yuborish
        managers = await get_managers_telegram_ids()
        transfer_text = (
            f"🔄 Vazifa o'tkazish so'rovi!\n\n"
            f"🆔 Zayavka ID: {zayavka_id}\n"
            f"👨‍🔧 Technician: {user['full_name']}\n"
            f"📝 Sabab: {message.text}\n\n"
            f"Zayavkani boshqa technicianga o'tkazish kerakmi?"
        )
        
        transfer_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Boshqa technicianga o'tkazish",
                callback_data=f"reassign_zayavka_{zayavka_id}"
            )]
        ])
        
        for manager_id in managers:
            try:
                await bot.send_message(
                    chat_id=manager_id,
                    text=transfer_text,
                    reply_markup=transfer_keyboard
                )
            except Exception as e:
                logger.error(f"Menejerga o'tkazish so'rovi yuborishda xatolik: {e}")
        
        await message.answer("✅ O'tkazish so'rovi menejerlarга yuborildi!")
        await state.clear()
        
    except Exception as e:
        logger.error(f"O'tkazish so'rovi yaratishda xatolik: {e}")
        await message.answer("Xatolik yuz berdi!")

@router.callback_query(F.data.startswith("reassign_zayavka_"))
async def reassign_zayavka_handler(call: CallbackQuery, state: FSMContext):
    """Zayavkani qayta biriktirish"""
    await call.answer()
    
    # Faqat menejerlar uchun
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user or user.get('role') != 'manager':
        await call.message.answer("Sizda bu amalni bajarish huquqi yo'q!")
        return
    
    zayavka_id = int(call.data.split("_")[-1])
    
    # Bo'sh technicianlari olish
    from database.queries import get_available_technicians
    technicians = await get_available_technicians()
    
    if not technicians:
        await call.message.answer("Hozirda bo'sh technician yo'q!")
        return
    
    await call.message.edit_text(
        f"Zayavka #{zayavka_id} uchun yangi technician tanlang:",
        reply_markup=get_technician_selection_keyboard(technicians)
    )
    await state.update_data(assigning_zayavka_id=zayavka_id)
