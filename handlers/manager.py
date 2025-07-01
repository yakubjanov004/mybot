from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from database.queries import (
    get_applications,
    update_application_status,
    assign_responsible,
    get_equipment_list,
    mark_equipment_ready,
    db_manager,
    get_available_technicians,
    get_zayavka_by_id,
    get_user_by_telegram_id,
    get_filtered_applications,
    get_user_by_id,
    update_user_language,
    get_all_technicians
)
from keyboards.manager_buttons import (
    confirmation_keyboard,
    get_manager_main_keyboard,
    get_report_type_keyboard,
    get_equipment_keyboard,
    get_assign_technician_keyboard,
    get_filter_keyboard,

    get_manager_language_keyboard,
    get_filtered_applications_keyboard,
    get_manager_back_keyboard,
    zayavka_type_keyboard,
    media_attachment_keyboard,
    geolocation_keyboard,
)
from states.manager_states import ManagerStates
from utils.logger import setup_logger
from utils.message_utils import safe_answer_message
from handlers.technician import get_task_inline_keyboard
from loader import bot
from utils.inline_cleanup import safe_remove_inline, safe_remove_inline_call
from utils.get_lang import get_user_lang
from utils.get_role import get_user_role
from handlers.language import show_language_selection, process_language_change
import datetime

router = Router()
logger = setup_logger('bot.manager')

def text_matches_locale(text: str, key_path: list) -> bool:
    """Check if text matches any locale version of the specified key"""
    # This function is no longer needed since we're not using locales
    # Keeping it for backward compatibility but it will always return False
    return False

@router.message(Command("manager"))
async def manager_menu(message: Message):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    reply_markup = get_manager_main_keyboard(lang)
    welcome_text = "👔 Menejer paneliga xush kelibsiz!" if lang == 'uz' else "👔 Добро пожаловать в панель менеджера!"
    await message.answer(welcome_text, reply_markup=reply_markup)

@router.message(lambda m: m.text in ["📋 Arizalarni ko'rish", "📋 Просмотр заявок"])
async def view_applications_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    try:
        data = await state.get_data()
        page = data.get('page', 1)
        per_page = 5
        offset = (page - 1) * per_page
        applications = await get_applications()
        if not applications:
            no_applications_text = "📋 Hozircha arizalar yo'q." if lang == 'uz' else "📋 Пока нет заявок."
            await safe_answer_message(
                message, 
                no_applications_text
            )
            return
        total = len(applications)
        start_idx = offset
        end_idx = min(start_idx + per_page, total)
        page_applications = applications[start_idx:end_idx]
        list_header = "📋 Arizalar ro'yxati:\n\n" if lang == 'uz' else "📋 Список заявок:\n\n"
        response = list_header
        for app in page_applications:
            if lang == 'uz':
                app_info = (
                    f"🆔 Ariza ID: <b>{app['id']}</b>\n"
                    f"👤 Mijoz: <b>{app.get('user_name', '-') }</b>\n"
                    f"📞 Telefon: <b>{app.get('user_phone', '-') }</b>\n"
                    f"📍 Manzil: <b>{app.get('address', '-') }</b>\n"
                    f"📝 Tavsif: <b>{app.get('description', '-') }</b>\n"
                    f"⏰ Yaratilgan vaqt: <b>{app.get('created_time', '-') }</b>\n"
                    f"👨‍🔧 Texnik: <b>{app.get('technician_name', '-') }</b>\n"
                    f"📞 Texnik tel: <b>{app.get('technician_phone', '-') }</b>\n"
                    f"⏰ Texnikka biriktirilgan: <b>{app.get('assigned_time', '-') }</b>\n"
                    f"⏰ Texnik qabul qilgan: <b>{app.get('accepted_time', '-') }</b>\n"
                    f"⏰ Texnik boshlagan: <b>{app.get('started_time', '-') }</b>\n"
                    f"⏰ Yakunlangan: <b>{app.get('completed_time', '-') }</b>"
                )
            else:
                app_info = (
                    f"🆔 ID заявки: <b>{app['id']}</b>\n"
                    f"👤 Клиент: <b>{app.get('user_name', '-') }</b>\n"
                    f"📞 Телефон: <b>{app.get('user_phone', '-') }</b>\n"
                    f"📍 Адрес: <b>{app.get('address', '-') }</b>\n"
                    f"📝 Описание: <b>{app.get('description', '-') }</b>\n"
                    f"⏰ Время создания: <b>{app.get('created_time', '-') }</b>\n"
                    f"👨‍🔧 Техник: <b>{app.get('technician_name', '-') }</b>\n"
                    f"📞 Тел. техника: <b>{app.get('technician_phone', '-') }</b>\n"
                    f"⏰ Назначен технику: <b>{app.get('assigned_time', '-') }</b>\n"
                    f"⏰ Принят техником: <b>{app.get('accepted_time', '-') }</b>\n"
                    f"⏰ Начат техником: <b>{app.get('started_time', '-') }</b>\n"
                    f"⏰ Завершен: <b>{app.get('completed_time', '-') }</b>"
                )
            response += app_info + "\n"
            response += "─" * 30 + "\n"
        await safe_answer_message(message, response)
        if total > per_page:
            total_pages = (total + per_page - 1) // per_page
            buttons = []
            if page > 1:
                buttons.append(InlineKeyboardButton(
                    text=f"◀️ {'Orqaga' if lang == 'uz' else 'Назад'}",
                    callback_data=f"applications_page_{page-1}"
                ))
            if page < total_pages:
                buttons.append(InlineKeyboardButton(
                    text=f"{'Oldinga' if lang == 'uz' else 'Вперёд'} ▶️",
                    callback_data=f"applications_page_{page+1}"
                ))
            if buttons:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                await message.answer(
                    f"📄 {end_idx}/{total}",
                    reply_markup=keyboard
                )
    except Exception as e:
        logger.error(f"Applications ko'rsatishda xatolik: {str(e)}", exc_info=True)
        error_text = "❌ Xatolik yuz berdi!" if lang == 'uz' else "❌ Произошла ошибка!"
        await safe_answer_message(
            message, 
            error_text
        )

@router.callback_query(lambda c: c.data.startswith('applications_page_'))
async def process_applications_page(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(callback.from_user.id)
    try:
        page = int(callback.data.split('_')[-1])
        await state.update_data(page=page)
        per_page = 5
        offset = (page - 1) * per_page
        applications = await get_applications()
        if not applications:
            no_applications_text = "📋 Hozircha arizalar yo'q." if lang == 'uz' else "📋 Пока нет заявок."
            await safe_answer_message(
                callback.message, 
                no_applications_text
            )
            return
        total = len(applications)
        start_idx = offset
        end_idx = min(start_idx + per_page, total)
        page_applications = applications[start_idx:end_idx]
        list_header = "📋 Arizalar ro'yxati:\n\n" if lang == 'uz' else "📋 Список заявок:\n\n"
        response = list_header
        for app in page_applications:
            if lang == 'uz':
                app_info = (
                    f"🆔 Ariza ID: <b>{app['id']}</b>\n"
                    f"👤 Mijoz: <b>{app.get('user_name', '-') }</b>\n"
                    f"📞 Telefon: <b>{app.get('user_phone', '-') }</b>\n"
                    f"📍 Manzil: <b>{app.get('address', '-') }</b>\n"
                    f"📝 Tavsif: <b>{app.get('description', '-') }</b>\n"
                    f"⏰ Yaratilgan vaqt: <b>{app.get('created_time', '-') }</b>\n"
                    f"👨‍🔧 Texnik: <b>{app.get('technician_name', '-') }</b>\n"
                    f"📞 Texnik tel: <b>{app.get('technician_phone', '-') }</b>\n"
                    f"⏰ Texnikka biriktirilgan: <b>{app.get('assigned_time', '-') }</b>\n"
                    f"⏰ Texnik qabul qilgan: <b>{app.get('accepted_time', '-') }</b>\n"
                    f"⏰ Texnik boshlagan: <b>{app.get('started_time', '-') }</b>\n"
                    f"⏰ Yakunlangan: <b>{app.get('completed_time', '-') }</b>"
                )
            else:
                app_info = (
                    f"🆔 ID заявки: <b>{app['id']}</b>\n"
                    f"👤 Клиент: <b>{app.get('user_name', '-') }</b>\n"
                    f"📞 Телефон: <b>{app.get('user_phone', '-') }</b>\n"
                    f"📍 Адрес: <b>{app.get('address', '-') }</b>\n"
                    f"📝 Описание: <b>{app.get('description', '-') }</b>\n"
                    f"⏰ Время создания: <b>{app.get('created_time', '-') }</b>\n"
                    f"👨‍🔧 Техник: <b>{app.get('technician_name', '-') }</b>\n"
                    f"📞 Тел. техника: <b>{app.get('technician_phone', '-') }</b>\n"
                    f"⏰ Назначен технику: <b>{app.get('assigned_time', '-') }</b>\n"
                    f"⏰ Принят техником: <b>{app.get('accepted_time', '-') }</b>\n"
                    f"⏰ Начат техником: <b>{app.get('started_time', '-') }</b>\n"
                    f"⏰ Завершен: <b>{app.get('completed_time', '-') }</b>"
                )
            response += app_info + "\n"
            response += "─" * 30 + "\n"
        await callback.message.delete()
        await safe_answer_message(callback.message, response)
        if total > per_page:
            total_pages = (total + per_page - 1) // per_page
            buttons = []
            if page > 1:
                buttons.append(InlineKeyboardButton(
                    text=f"◀️ {'Orqaga' if lang == 'uz' else 'Назад'}",
                    callback_data=f"applications_page_{page-1}"
                ))
            if page < total_pages:
                buttons.append(InlineKeyboardButton(
                    text=f"{'Oldinga' if lang == 'uz' else 'Вперёд'} ▶️",
                    callback_data=f"applications_page_{page+1}"
                ))
            if buttons:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                await callback.message.answer(
                    f"📄 {end_idx}/{total}",
                    reply_markup=keyboard
                )
        await callback.answer()
    except Exception as e:
        logger.error(f"Applications sahifalarini ko'rsatishda xatolik: {str(e)}", exc_info=True)
        error_text = "❌ Xatolik yuz berdi!" if lang == 'uz' else "❌ Произошла ошибка!"
        await safe_answer_message(
            callback.message, 
            error_text
        )

@router.message(lambda m: m.text in ["🔄 Status o'zgartirish", "🔄 Изменить статус"])
async def change_status_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    role = await get_user_role(message.from_user.id)
    await state.set_state(ManagerStates.WAITING_FOR_APP_ID_FOR_STATUS_CHANGE)
    reply_markup = None
    if role == 'manager':
        reply_markup = get_manager_back_keyboard(lang)
    await safe_answer_message(
        message, 
        "🆔 Ariza ID ni kiriting:" if lang == 'uz' else "🆔 Введите ID заявки:",
        reply_markup=reply_markup
    )

@router.message(StateFilter(ManagerStates.WAITING_FOR_APP_ID_FOR_STATUS_CHANGE))
async def process_app_id_for_status(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    try:
        application_id = int(message.text)
        app = await get_zayavka_by_id(application_id)

        if not app:
            await safe_answer_message(
                message, 
                "❌ Ariza topilmadi." if lang == 'uz' else "❌ Заявка не найдена."
            )
            await state.clear()
            return
        # Show detailed info (no asterisks)
        info_text = (
            ("📋 Ariza ma'lumotlari" if lang == 'uz' else "📋 Информация о заявке") + "\n"
            f"🆔 ID: {app['id']}\n"
            f"👤 {'Mijoz' if lang == 'uz' else 'Клиент'}: {app.get('user_name', '-')}\n"
            f"📞 {'Telefon' if lang == 'uz' else 'Телефон'}: {app.get('phone_number', '-')}\n"
            f"📝 {'Tavsif' if lang == 'uz' else 'Описание'}: {app.get('description', '-')}\n"
            f"📍 {'Manzil' if lang == 'uz' else 'Адрес'}: {app.get('address', '-')}\n"
            f"📅 {'Sana' if lang == 'uz' else 'Дата'}: {app.get('created_at', '-')}\n"
            f"📊 {'Status' if lang == 'uz' else 'Статус'}: {app.get('status', '-')}"
        )
        await safe_answer_message(message, info_text)
        # Status button emojis
        status_buttons = [
            ("new", "🆕 " + ("Yangi" if lang == 'uz' else "Новый")),
            ("in_progress", "⏳ " + ("Jarayonda" if lang == 'uz' else "В процессе")),
            ("completed", "✅ " + ("Yakunlandi" if lang == 'uz' else "Завершено")),
            ("cancelled", "❌ " + ("Bekor qilindi" if lang == 'uz' else "Отменено"))
        ]
        await safe_answer_message(
            message, 
            "Yangi statusni tanlang:" if lang == 'uz' else "Выберите новый статус:", 
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=btn_text, callback_data=f"status_{status}_{application_id}") for status, btn_text in status_buttons]
                ]
            )
        )
        await state.clear()
    except (ValueError, TypeError):
        await safe_answer_message(
            message, 
            "❌ ID raqam bo'lishi kerak." if lang == 'uz' else "❌ ID должен быть числом."
        )
    except Exception as e:
        logger.error(f"Error processing app ID for status change: {e}")
        await safe_answer_message(
            message, 
            "❌ Xatolik yuz berdi!" if lang == 'uz' else "❌ Произошла ошибка!"
        )
        await state.clear()

@router.callback_query(F.data.startswith("status_"))
async def process_status_change(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(callback.from_user.id)
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user or user.get('role') not in ['manager', 'admin']:
        await callback.answer(
            "❌ Ruxsat yo'q!" if lang == 'uz' else "❌ Нет доступа!", 
            show_alert=True
        )
        return
    try:
        # status callback: status_<status>_<id> (status may contain underscores)
        parts = callback.data.split("_")
        application_id = int(parts[-1])
        status = "_".join(parts[1:-1])
        await update_application_status(application_id, status)
        status_text = {
            "new": "Yangi" if lang == 'uz' else "Новый",
            "in_progress": "Jarayonda" if lang == 'uz' else "В процессе",
            "completed": "Yakunlandi" if lang == 'uz' else "Завершено",
            "cancelled": "Bekor qilindi" if lang == 'uz' else "Отменено"
        }.get(status, status)
        emoji = {
            "new": "🆕",
            "in_progress": "⏳",
            "completed": "✅",
            "cancelled": "❌"
        }.get(status, "")
        success_message = (
            ("✅ Status muvaffaqiyatli o'zgartirildi" if lang == 'uz' else "✅ Статус успешно изменен") + "\n\n"
            f"ID: {application_id}\n"
            f"{'Yangi status' if lang == 'uz' else 'Новый статус'}: {emoji} {status_text}"
        )
        await callback.message.edit_text(success_message)
    except (ValueError, IndexError) as e:
        logger.error(f"Could not parse status callback: {callback.data}, error: {e}")
        await safe_answer_message(
            callback.message, 
            "❌ Statusni yangilashda xatolik!" if lang == 'uz' else "❌ Ошибка при обновлении статуса!"
        )
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        await safe_answer_message(
            callback.message, 
            "❌ Statusni yangilashda xatolik!" if lang == 'uz' else "❌ Ошибка при обновлении статуса!"
        )
    finally:
        await callback.answer()

@router.message(lambda m: m.text in ["📦 Jihozlar berish", "📦 Выдача оборудования"])
async def equipment_issuance_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Handle equipment issuance with locale support"""
    lang = await get_user_lang(message.from_user.id)
    
    equipment_list = await get_equipment_list()
    
    if not equipment_list:
        await safe_answer_message(
            message, 
            "📦 Jihozlar mavjud emas." if lang == 'uz' else "📦 Оборудование отсутствует."
        )
        return
    
    await state.set_state(ManagerStates.EQUIPMENT_ISSUANCE)
    await safe_answer_message(
        message, 
        "📦 Jihoz tanlang:" if lang == 'uz' else "📦 Выберите оборудование:", 
        reply_markup=get_equipment_keyboard(equipment_list, lang)
    )

@router.callback_query(F.data.startswith("equipment_"))
async def process_equipment_issuance(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Process equipment issuance"""
    lang = await get_user_lang(callback.from_user.id)
    equipment_id = callback.data.split("_")[1]
    
    try:
        # Add your equipment issuance logic here
        await safe_answer_message(callback.message, "Jihoz berildi!" if lang == 'uz' else "Оборудование выдано!")
    except Exception as e:
        logger.error(f"Error issuing equipment: {e}")
        await safe_answer_message(callback.message, "Jihoz berishda xatolik!" if lang == 'uz' else "Ошибка при выдаче оборудования!")
    
    await state.clear()
    await callback.answer()

@router.message(lambda m: m.text in ["✅ O'rnatishga tayyor", "✅ Готов к установке"])
async def ready_for_installation_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Handle ready for installation marking"""
    lang = await get_user_lang(message.from_user.id)
    await state.set_state(ManagerStates.READY_FOR_INSTALLATION)
    await safe_answer_message(message, "Jihoz ID ni kiriting:" if lang == 'uz' else "Введите ID оборудования:")

@router.message(StateFilter(ManagerStates.READY_FOR_INSTALLATION))
async def process_installation_ready(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Process installation ready marking"""
    lang = await get_user_lang(message.from_user.id)
    try:
        equipment_id = int(message.text)
        await mark_equipment_ready(equipment_id)
        await safe_answer_message(message, "Tayyor deb belgilandi!" if lang == 'uz' else "Отмечено как готовое!")
    except ValueError:
        await safe_answer_message(message, "Noto'g'ri ID!" if lang == 'uz' else "Неверный ID!")
    except Exception as e:
        logger.error(f"Error marking ready: {e}")
        await safe_answer_message(message, "Yangilashda xatolik!" if lang == 'uz' else "Ошибка при обновлении!")
    
    await state.clear()

@router.message(lambda m: m.text in ["📊 Hisobot yaratish", "📊 Создать отчет"])
async def generate_report_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Handle report generation with locale support"""
    lang = await get_user_lang(message.from_user.id)
    
    await state.set_state(ManagerStates.GENERATE_REPORT)
    await safe_answer_message(
        message, 
        "📊 Hisobot turini tanlang:" if lang == 'uz' else "📊 Выберите тип отчета:", 
        reply_markup=get_report_type_keyboard(lang)
    )

@router.callback_query(F.data.startswith("report_"))
async def process_report_generation(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(callback.from_user.id)
    report_type = callback.data.split("_")[1]
    try:
        await safe_answer_message(callback.message, "📊 Hisobot tayyorlandi!" if lang == 'uz' else "📊 Отчет сгенерирован!")
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await safe_answer_message(callback.message, "❌ Hisobotda xatolik." if lang == 'uz' else "❌ Ошибка при генерации отчета.")
    await state.clear()
    await callback.answer()

@router.message(lambda m: m.text in ["👨‍🔧 Texnik biriktirish", "👨‍🔧 Назначить техника"])
async def assign_technician_start(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    role = await get_user_role(message.from_user.id)
    logger.info("assign_technician_start handler called")
    await state.set_state(ManagerStates.ASSIGN_TECHNICIAN)
    reply_markup = None
    if role == 'manager':
        reply_markup = get_manager_back_keyboard(lang)
    prompt = "🆔 Zayavka ID ni kiriting:" if lang == 'uz' else "🆔 Введите ID заявки:"
    await safe_answer_message(
        message, 
        prompt,
        reply_markup=reply_markup
    )

@router.message(StateFilter(ManagerStates.ASSIGN_TECHNICIAN))
async def assign_technician_select(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    try:
        application_id = int(message.text)
        application = await get_zayavka_by_id(application_id)
        if not application:
            not_found = "❌ Ariza topilmadi" if lang == 'uz' else "❌ Заявка не найдена"
            await safe_answer_message(message, not_found)
            await state.clear()
            return
        # Detailed application info
        if lang == 'uz':
            info = (
                f"📝 Ariza tafsilotlari\n\n"
                f"🆔 ID: {application['id']}\n"
                f"👤 Mijoz: {application.get('user_name', '-') }\n"
                f"📱 Telefon: {application.get('phone_number', '-') }\n"
                f"📝 Tavsif: {application.get('description', '-') }\n"
                f"📍 Manzil: {application.get('address', '-') }\n"
                f"🏷️ Abonent ID: {application.get('abonent_id', '-') }\n"
                f"🔖 Turi: {application.get('zayavka_type', '-') }\n"
                f"👨‍🔧 Biriktirilgan: {application.get('assigned_name', '-') }\n"
                f"📅 Sana: {application.get('created_at', '-') }\n"
                f"🏷️ Status: {application.get('status', '-') }"
            )
        else:
            info = (
                f"📝 Детали заявки\n\n"
                f"🆔 ID: {application['id']}\n"
                f"👤 Клиент: {application.get('user_name', '-') }\n"
                f"📱 Телефон: {application.get('phone_number', '-') }\n"
                f"📝 Описание: {application.get('description', '-') }\n"
                f"📍 Адрес: {application.get('address', '-') }\n"
                f"🏷️ ID абонента: {application.get('abonent_id', '-') }\n"
                f"🔖 Тип: {application.get('zayavka_type', '-') }\n"
                f"👨‍🔧 Назначен: {application.get('assigned_name', '-') }\n"
                f"📅 Дата: {application.get('created_at', '-') }\n"
                f"🏷️ Статус: {application.get('status', '-') }"
            )
        assigned_name = application.get('assigned_name')
        if assigned_name and assigned_name != '-':
            warning_text = f"⚠️ Diqqat! Bu arizaga allaqachon texnik biriktirilgan: **{assigned_name}**" if lang == 'uz' else f"⚠️ Внимание! К этой заявке уже назначен техник: **{assigned_name}**"
            await message.answer(warning_text)
        if application.get('media'):
            try:
                await message.answer_photo(photo=application['media'], caption=info)
            except Exception:
                await message.answer(info)
        else:
            await message.answer(info)
        technicians = await get_available_technicians()
        if not technicians:
            no_techs = "👨‍🔧 Hozircha texniklar yo'q." if lang == 'uz' else "👨‍🔧 Сейчас нет доступных техников."
            await safe_answer_message(message, no_techs)
            await state.clear()
            return
        tech_list = [
            {
                "id": t["id"],
                "full_name": f"{t['full_name']} ({t['active_tasks']} {'vazifa' if lang == 'uz' else 'задач'})"
            }
            for t in technicians
        ]
        select_tech = "👨‍🔧 Texnikni tanlang:" if lang == 'uz' else "👨‍🔧 Выберите техника:"
        await message.answer(
            select_tech,
            reply_markup=get_assign_technician_keyboard(application_id, tech_list, lang)
        )
        await state.update_data(assigning_zayavka_id=application_id)
    except ValueError:
        invalid_id = "❌ ID noto'g'ri." if lang == 'uz' else "❌ Неверный ID."
        await safe_answer_message(message, invalid_id)
        await state.clear()
    except Exception as e:
        logger.error(f"Error in assign_technician_select: {e}")
        await safe_answer_message(message, "❌ Xatolik yuz berdi!" if lang == 'uz' else "❌ Произошла ошибка!")
        await state.clear()

@router.callback_query(F.data == "back_to_assign_technician")
async def back_to_assign_technician_handler(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(callback.from_user.id)
    prompt = "🆔 Zayavka ID ni kiriting:" if lang == 'uz' else "🆔 Введите ID заявки:"
    await safe_answer_message(
        callback.message, 
        prompt
    )
    await state.set_state(ManagerStates.ASSIGN_TECHNICIAN)
    await callback.answer()

@router.callback_query(F.data.startswith("manager_assign_zayavka_"))
async def assign_technician_to_zayavka(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(call.from_user.id)
    try:
        _, zayavka_id, technician_id = call.data.rsplit('_', 2)
        zayavka_id = int(zayavka_id)
        technician_id = int(technician_id)
        
        # Get application and technician details
        application = await get_zayavka_by_id(zayavka_id)
        technician = await get_user_by_id(technician_id)
        
        if not technician:
            await call.message.answer(
                "❌ Texnik topilmadi." if lang == 'uz' else "❌ Техник не найден.",
                reply_markup=None
            )
            await state.clear()
            await call.answer()
            return
            
        # Assign technician to application
        await assign_responsible(zayavka_id, technician_id)
        
        # Prepare brief notification text for technician
        tech_lang = technician.get('language', 'uz')
        if tech_lang == 'uz':
            tech_notification = (
                f"📝 Yangi ariza sizga biriktirildi!\n\n"
                f"🆔 Ariza: #{zayavka_id}\n"
                f"📍 Manzil: {application.get('address', '-')}\n"
                f"⏰ Sana: {application.get('created_at', '-')}"
            )
        else:
            tech_notification = (
                f"📝 Вам назначена новая заявка!\n\n"
                f"🆔 Заявка: #{zayavka_id}\n"
                f"📍 Адрес: {application.get('address', '-')}\n"
                f"⏰ Дата: {application.get('created_at', '-')}"
            )
        
        # Create accept button for technician
        tech_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Qabul qilish" if tech_lang == 'uz' else "✅ Принять",
                    callback_data=f"tech_accept_{zayavka_id}"
                ),
                InlineKeyboardButton(
                    text="↪️ O'tkazish" if tech_lang == 'uz' else "↪️ Передать",
                    callback_data=f"tech_forward_{zayavka_id}"
                )
            ]
        ])
        
        # Send initial notification to technician
        try:
            await bot.send_message(
                chat_id=technician['telegram_id'],
                text=tech_notification,
                reply_markup=tech_keyboard
            )
        except Exception as e:
            logger.error(f"Error sending notification to technician: {e}")
        
        # Send confirmation to manager
        success_message = (
            f"✅ Texnik biriktirildi!\n\n"
            f"🆔 Ariza: #{zayavka_id}\n"
            f"👨‍🔧 Texnik: {technician.get('full_name', '-')}\n"
            f"📱 Tel: {technician.get('phone_number', '-')}" if lang == 'uz' else
            f"✅ Техник назначен!\n\n"
            f"🆔 Заявка: #{zayavka_id}\n"
            f"👨‍🔧 Техник: {technician.get('full_name', '-')}\n"
            f"📱 Тел: {technician.get('phone_number', '-')}"
        )
        await call.message.answer(success_message, reply_markup=get_manager_main_keyboard(lang))
        
    except Exception as e:
        logger.error(f"Error in assign_technician_to_zayavka: {e}")
        await call.message.answer(
            "❌ Biriktirishda xatolik." if lang == 'uz' else "❌ Ошибка при назначении."
        )
    finally:
        await state.clear()
        await call.answer()

@router.callback_query(F.data.startswith("tech_accept_"))
async def handle_tech_accept(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    try:
        zayavka_id = int(callback.data.split("_")[-1])
        application = await get_zayavka_by_id(zayavka_id)
        if not application:
            await callback.answer("❌ Ariza topilmadi")
            return
        
        tech_lang = await get_user_lang(callback.from_user.id)
        
        # Prepare detailed notification text
        if tech_lang == 'uz':
            detailed_notification = (
                f"📝 Ariza tafsilotlari:\n\n"
                f"🆔 Ariza: #{zayavka_id}\n"
                f"👤 Mijoz: {application.get('user_name', '-')}\n"
                f"📞 Telefon: {application.get('phone_number', '-')}\n"
                f"📝 Tavsif: {application.get('description', '-')}\n"
                f"📍 Manzil: {application.get('address', '-')}\n"
                f"⏰ Sana: {application.get('created_at', '-')}"
            )
        else:
            detailed_notification = (
                f"📝 Детали заявки:\n\n"
                f"🆔 Заявка: #{zayavka_id}\n"
                f"👤 Клиент: {application.get('user_name', '-')}\n"
                f"📞 Телефон: {application.get('phone_number', '-')}\n"
                f"📝 Описание: {application.get('description', '-')}\n"
                f"📍 Адрес: {application.get('address', '-')}\n"
                f"⏰ Дата: {application.get('created_at', '-')}"
            )
        
        # Create start button
        start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ Boshlash" if tech_lang == 'uz' else "▶️ Начать",
                    callback_data=f"tech_start_{zayavka_id}"
                )
            ]
        ])
        
        # Send detailed notification
        await callback.message.answer(detailed_notification, reply_markup=start_keyboard)
        
        # Update application status
        await update_application_status(zayavka_id, "in_progress")
        
        await callback.answer(
            "✅ Ariza qabul qilindi" if tech_lang == 'uz' else "✅ Заявка принята"
        )
        
    except Exception as e:
        logger.error(f"Error in handle_tech_accept: {e}")
        tech_lang = await get_user_lang(callback.from_user.id)
        await callback.answer(
            "❌ Xatolik yuz berdi" if tech_lang == 'uz' else "❌ Произошла ошибка",
            show_alert=True
        )

@router.callback_query(F.data == "manager_confirm_zayavka")
async def confirm_zayavka(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    data = await state.get_data()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    try:
        async with db_manager.get_connection() as conn:
            db_user = await conn.fetchrow("SELECT id, full_name FROM users WHERE telegram_id = $1", call.from_user.id)
            zayavka = await conn.fetchrow(
                '''INSERT INTO zayavki (user_id, zayavka_type, abonent_id, description, address, media, location, status, created_by_role)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, 'new', 'manager') RETURNING *''',
                db_user['id'],
                data['zayavka_type'],
                data['abonent_id'],
                data['description'],
                data['address'],
                data.get('media'),
                data.get('location')
            )
            await state.update_data(zayavka_id=zayavka['id'])
            # Now show technician selection
            technicians = await get_all_technicians()
            await call.message.answer(
                (f"✅ Ariza yaratildi! ID: {zayavka['id']}\n\nTexnikni tanlang:" if lang == 'uz' else f"✅ Заявка создана! ID: {zayavka['id']}\n\nВыберите техника:"),
                reply_markup=get_assign_technician_keyboard(zayavka['id'], technicians, lang)
            )
            await state.set_state(ManagerStates.assigning_technician)
    except Exception as e:
        await call.message.answer(f"Xatolik: {str(e)}" if lang == 'uz' else f"Ошибка: {str(e)}")
        await state.clear()

@router.message(lambda m: m.text in ["🔍 Filtrlar", "🔍 Фильтры"])
async def show_filter_menu(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    # Delete previous menu message if exists
    data = await state.get_data()
    last_msg_id = data.get('last_menu_msg_id')
    if last_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass
    lang = await get_user_lang(message.from_user.id)
    try:
        filter_text = f"🔍 {'Kerakli filtrlarni tanlang:' if lang == 'uz' else 'Выберите нужные фильтры:'}"
        sent_msg = await message.answer(filter_text, reply_markup=get_filter_keyboard(lang))
        await state.update_data(last_menu_msg_id=sent_msg.message_id)
    except Exception as e:
        logger.error(f"Filter menu error: {str(e)}", exc_info=True)
        await message.answer(f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}")

@router.callback_query(F.data.startswith("filter_"))
async def process_filter(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(callback.from_user.id)
    try:
        parts = callback.data.split('_')
        filter_type = parts[1]
        page = 1
        if len(parts) > 2 and parts[-1].isdigit():
            page = int(parts[-1])
        result = None
        filter_kwargs = {'page': page, 'limit': 5}
        # --- Filter label logic ---
        filter_label = ""
        if filter_type == 'status':
            status = '_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])
            if status == 'all':
                filter_label = f"📋 {'Barcha statuslar' if lang == 'uz' else 'Все статусы'}"
                result = await get_filtered_applications(**filter_kwargs)
            else:
                status_emoji = {
                    'new': '🆕',
                    'in_progress': '⏳',
                    'completed': '✅',
                    'cancelled': '❌'
                }.get(status, '📋')
                status_label = {
                    'new': 'Yangi' if lang == 'uz' else 'Новый',
                    'in_progress': 'Jarayonda' if lang == 'uz' else 'В процессе',
                    'completed': 'Yakunlandi' if lang == 'uz' else 'Завершено',
                    'cancelled': 'Bekor qilindi' if lang == 'uz' else 'Отменено'
                }.get(status, status)
                filter_label = f"{status_emoji} {'Status:' if lang == 'uz' else 'Статус:'} {status_label}"
                result = await get_filtered_applications(statuses=[status], **filter_kwargs)
        elif filter_type == 'date':
            date_type = parts[2]
            today = datetime.date.today()
            # 2ta tilda (uz va ru) date_labels lug'ati va ishlatishda to'g'ri tilni tanlash
            date_labels = {
                'today': {
                    'uz': "📅 Bugun",
                    'ru': "📅 Сегодня"
                },
                'yesterday': {
                    'uz': "📅 Kecha",
                    'ru': "📅 Вчера"
                },
                'week': {
                    'uz': "📅 Bu hafta",
                    'ru': "📅 На этой неделе"
                },
                'month': {
                    'uz': "📅 Bu oy",
                    'ru': "📅 В этом месяце"
                }
            }
            filter_label = date_labels.get(date_type, {}).get(lang, f"📅 {date_type}")
            filter_label = date_labels.get(date_type, f"📅 {date_type}")
            if date_type == 'today':
                date_from = date_to = today
            elif date_type == 'yesterday':
                date_from = date_to = today - datetime.timedelta(days=1)
            elif date_type == 'week':
                date_from = today - datetime.timedelta(days=today.weekday())
                date_to = today
            elif date_type == 'month':
                date_from = today.replace(day=1)
                date_to = today
            else:
                date_from = date_to = today
            result = await get_filtered_applications(date_from=date_from, date_to=date_to, **filter_kwargs)
        elif filter_type == 'tech':
            tech_type = parts[2]
            if tech_type == 'assigned':
                filter_label = f"👨‍🔧 {'Biriktirilgan' if lang == 'uz' else 'Назначенные'}"
                result = await get_filtered_applications(assigned_only=True, **filter_kwargs)
            elif tech_type == 'unassigned':
                filter_label = f"👨‍🔧 {'Biriktirilmagan' if lang == 'uz' else 'Не назначенные'}"
                result = await get_filtered_applications(technician_id=0, **filter_kwargs)
        elif filter_type == 'clear':
            filter_text = f"🔍 {'Kerakli filtrlarni tanlang:' if lang == 'uz' else 'Выберите нужные фильтры:'}"
            try:
                await callback.message.edit_text(
                    filter_text,
                    reply_markup=get_filter_keyboard(lang)
                )
            except Exception as e:
                logger.error(f"Edit text error (clear): {str(e)}", exc_info=True)
                await callback.answer(f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
                return
            await callback.answer()
            return
        applications = result['applications'] if result and result.get('applications') else []
        total_pages = result.get('total_pages', 1) if result else 1
        current_page = result.get('page', 1) if result else 1
        status_emojis = {
            'new': '🆕',
            'in_progress': '⏳',
            'completed': '✅',
            'cancelled': '❌'
        }
        # 2ta tilda, emojilar bilan
        labels_uz = {
            'status': "🆕 Status:",
            'client': "👤 Mijoz:",
            'address': "📍 Manzil:",
            'description': "📝 Izoh:",
            'technician': "👨‍🔧 Texnik:",
            'created': "🕒 Yaratilgan:",
            'no_technician': "❌ Texnik biriktirilmagan",
            'no_address': "❌ Manzil ko'rsatilmagan",
            'filtered': "🔍 Filtrlangan arizalar",
            'no_applications': "❌ Arizalar topilmadi",
            'clear_filter': "🔄 Filterni tozalash",
        }
        labels_ru = {
            'status': "🆕 Статус:",
            'client': "👤 Клиент:",
            'address': "📍 Адрес:",
            'description': "📝 Описание:",
            'technician': "👨‍🔧 Техник:",
            'created': "🕒 Создано:",
            'no_technician': "❌ Не назначен",
            'no_address': "❌ Адрес не указан",
            'filtered': "🔍 Отфильтрованные заявки",
            'no_applications': "❌ Заявки не найдены",
            'clear_filter': "🔄 Сбросить фильтр",
        }
        labels = labels_uz if lang == 'uz' else labels_ru
        applications_text = f"{filter_label} ({current_page}/{total_pages}):\n\n"
        if applications:
            for app in applications:
                status = app.get('status', 'new')
                status_emoji = status_emojis.get(status, '📋')
                # 2 tilda, emoji bilan chiroyli formatda chiqaramiz
                if lang == 'uz':
                    applications_text += (
                        f"{status_emoji} <b>Status:</b> <i>{status_label if 'status_label' in locals() else status}</i>\n"
                        f"👤 <b>Mijoz:</b> <i>{app.get('user_name',)}</i> | 📞 <b>Tel:</b> <i>{app.get('client_phone', '-')}</i>\n"
                        f"📍 <b>Manzil:</b> <i>{app.get('address') or labels['no_address']}</i>\n"
                        f"📝 <b>Izoh:</b> <i>{app.get('description', '')[:100]}</i>\n"
                        f"👨‍🔧 <b>Texnik:</b> <i>{app.get('technician_name', labels['no_technician'])}</i> | 📞 <i>{app.get('technician_phone', '-')}</i>\n"
                        f"🕒 <b>Yaratilgan:</b> <i>{app.get('created_at', '')}</i>\n"
                        f"🔎 <b>ID:</b> <code>{app.get('id', '-')}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                    )
                else:
                    applications_text += (
                        f"{status_emoji} <b>Статус:</b> <i>{status_label if 'status_label' in locals() else status}</i>\n"
                        f"👤 <b>Клиент:</b> <i>{app.get('user_name')}</i> | 📞 <b>Тел:</b> <i>{app.get('client_phone', '-')}</i>\n"
                        f"📍 <b>Адрес:</b> <i>{app.get('address') or labels['no_address']}</i>\n"
                        f"📝 <b>Описание:</b> <i>{app.get('description', '')[:100]}</i>\n"
                        f"👨‍🔧 <b>Техник:</b> <i>{app.get('technician_name', labels['no_technician'])}</i> | 📞 <i>{app.get('technician_phone', '-')}</i>\n"
                        f"🕒 <b>Создано:</b> <i>{app.get('created_at', '')}</i>\n"
                        f"🔎 <b>ID:</b> <code>{app.get('id', '-')}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                    )
        else:
            applications_text += f"❌ {labels['no_applications']}\n\n"
        # Pagination buttons
        inline_keyboard = []
        if total_pages > 1:
            nav_buttons = []
            if current_page > 1:
                nav_buttons.append(InlineKeyboardButton(
                    text="⬅️", callback_data=f"filter_{filter_type}_{'_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])}_{current_page-1}"
                ))
            nav_buttons.append(InlineKeyboardButton(
                text=f"{current_page}/{total_pages}", callback_data="noop"
            ))
            if current_page < total_pages:
                nav_buttons.append(InlineKeyboardButton(
                    text="➡️", callback_data=f"filter_{filter_type}_{'_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])}_{current_page+1}"
                ))
            inline_keyboard.append(nav_buttons)
        # Always show clear button
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🔄 {labels['clear_filter']}",
                callback_data="filter_clear"
            )
        ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
        try:
            await callback.message.edit_text(applications_text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Edit text error: {str(e)}", exc_info=True)
            await callback.answer(f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
            return
        await callback.answer()
    except Exception as e:
        logger.error(f"Error processing filter: {str(e)}", exc_info=True)
        await callback.answer(
            f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}",
            show_alert=True
        )

@router.callback_query(F.data.startswith("view_application_"))
async def view_filtered_application(callback: CallbackQuery):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Show detailed information about filtered application"""
    lang = await get_user_lang(callback.from_user.id)
    
    try:
        app_id = int(callback.data.replace("view_application_", ""))
        app = await get_zayavka_by_id(app_id)
        
        if not app:
            await callback.answer(f"❌ {'Ariza topilmadi.' if lang == 'uz' else 'Заявка не найдена.'}", show_alert=True)
            return
        
        status_emoji = {
            'new': '🆕',
            'in_progress': '⏳',
            'completed': '✅',
            'cancelled': '❌'
        }.get(app.get('status', 'new'), '📋')
        
        # 2ta tilda app_text_uz va app_text_ru chiroyli formatda

        app_text_uz = (
            f"📋 <b>Ariza ma'lumotlari</b>\n\n"
            f"🆔 <b>ID:</b> {app['id']}\n"
            f"👤 <b>Mijoz:</b> {app.get('user_name', '-')}\n"
            f"📞 <b>Telefon:</b> {app.get('phone_number', '-')}\n"
            f"📝 <b>Tavsif:</b> {app.get('description', '-')}\n"
            f"📍 <b>Manzil:</b> {app.get('address', '-')}\n"
            f"📅 <b>Sana:</b> {app.get('created_at', '-')}\n"
            f"📊 <b>Status:</b> {status_emoji} {app.get('status', '-')}"
        )

        app_text_ru = (
            f"📋 <b>Информация о заявке</b>\n\n"
            f"🆔 <b>ID:</b> {app['id']}\n"
            f"👤 <b>Клиент:</b> {app.get('user_name', '-')}\n"
            f"📞 <b>Телефон:</b> {app.get('phone_number', '-')}\n"
            f"📝 <b>Описание:</b> {app.get('description', '-')}\n"
            f"📍 Адрес: {app.get('address', '-')}\n"
            f"📅 Дата: {app.get('created_at', '-')}\n"
            f"📊 Статус: {status_emoji} {app.get('status', '-')}"
        )

        app_text = app_text_uz if lang == 'uz' else app_text_ru
        
        # Show application info with back to filter button
        await callback.message.edit_text(
            app_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"🔍 {'Filtrlashga qaytish' if lang == 'uz' else 'Вернуться к фильтрам'}", 
                    callback_data="filter_clear"
                )
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error viewing filtered application: {str(e)}", exc_info=True)
        await callback.answer(f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
    
    await callback.answer()

@router.message(lambda m: m.text in ["🌐 Tilni o'zgartirish", "🌐 Изменить язык"])
async def manager_change_language(message: Message, state: FSMContext):
    """Show language selection for manager"""
    await safe_remove_inline(message)
    success = await show_language_selection(message, "manager", state)
    if not success:
        lang = await get_user_lang(message.from_user.id)
        await message.answer("Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка")

@router.callback_query(F.data.startswith("manager_lang_"))
async def process_manager_language_change(callback: CallbackQuery, state: FSMContext):
    """Process manager language change using shared handler"""
    try:
        await safe_remove_inline_call(callback)
        await process_language_change(
            call=callback,
            role="manager",
            get_main_keyboard_func=get_manager_main_keyboard,
            state=state
        )
    except Exception as e:
        logger.error(f"Manager tilni o'zgartirishda xatolik: {str(e)}", exc_info=True)
        lang = await get_user_lang(callback.from_user.id)
        await callback.message.answer("Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка")
        await callback.answer()

@router.callback_query(F.data == "manager_back_to_menu")
async def manager_back_to_menu(callback: CallbackQuery):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Return to manager main menu"""
    # Get user's current language from database
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz') if user else 'uz'
    # To'g'ri reply_markup va xabarni yangilash
    reply_markup = get_manager_main_keyboard(lang)
    await callback.message.edit_text(
        ("👔 Menejer paneliga xush kelibsiz!" if lang == 'uz' else "👔 Добро пожаловать в панель менеджера!"),
        reply_markup=reply_markup
    )
    await callback.answer()

@router.message(lambda m: m.text in ["🏠 Asosiy menyu", "🏠 Главное меню"])
async def manager_back_to_main_menu(message: Message, state: FSMContext):
    role = await get_user_role(message.from_user.id)
    if role == "manager":
        await state.clear()
        lang = await get_user_lang(message.from_user.id)
        reply_markup = get_manager_main_keyboard(lang)
        welcome_text = "👔 Menejer paneliga xush kelibsiz!" if lang == 'uz' else "👔 Добро пожаловать в панель менеджера!"
        await message.answer(welcome_text, reply_markup=reply_markup)

@router.message(F.text.in_(['📝 Ariza yaratish', '📝 Создать заявку']))
async def start_zayavka(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    await state.clear()
    await message.answer(
        "Iltimos, ariza turini tanlang:" if lang == 'uz' else "Пожалуйста, выберите тип заявки:",
        reply_markup=zayavka_type_keyboard(lang)
    )
    await state.set_state(ManagerStates.choosing_zayavka_type)

@router.callback_query(F.data.in_(["manager_zayavka_type_b2b", "manager_zayavka_type_b2c"]))
async def choose_type(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    ztype = "Jismoniy shaxs" if call.data.endswith("b2b") else "Yuridik shaxs" if lang == 'uz' else "Физическое лицо" if call.data.endswith("b2b") else "Юридическое лицо"
    await state.update_data(zayavka_type=ztype)
    await call.message.answer("Iltimos, abonent ID ni kiriting:" if lang == 'uz' else "Пожалуйста, введите ID абонента:", reply_markup=get_manager_back_keyboard(lang))
    await state.set_state(ManagerStates.waiting_for_abonent_id)

@router.message(ManagerStates.waiting_for_abonent_id)
async def get_abonent_id(message: Message, state: FSMContext):
    await state.update_data(abonent_id=message.text)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    await message.answer("Iltimos, ariza tavsifini kiriting:" if lang == 'uz' else "Пожалуйста, введите описание заявки:", reply_markup=get_manager_back_keyboard(lang))
    await state.set_state(ManagerStates.waiting_for_description)

@router.message(ManagerStates.waiting_for_description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    await message.answer("Media fayl biriktirasizmi?" if lang == 'uz' else "Хотите прикрепить медиафайл?", reply_markup=media_attachment_keyboard(lang))
    await state.set_state(ManagerStates.waiting_for_media)

@router.callback_query(F.data.in_(["manager_attach_media_yes", "manager_attach_media_no"]))
async def handle_media_decision(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    if call.data.endswith("yes"):
        await call.message.answer("Media yuboring:" if lang == 'uz' else "Отправьте медиафайл:", reply_markup=get_manager_back_keyboard(lang))
        await state.set_state(ManagerStates.waiting_for_media)
    else:
        await state.update_data(media=None)
        await call.message.answer("Manzilni kiriting:" if lang == 'uz' else "Введите адрес:", reply_markup=get_manager_back_keyboard(lang))
        await state.set_state(ManagerStates.waiting_for_address)

@router.message(ManagerStates.waiting_for_media, F.photo | F.document)
async def receive_media(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    await state.update_data(media=file_id)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    await message.answer("Manzilni kiriting:" if lang == 'uz' else "Введите адрес:", reply_markup=get_manager_back_keyboard(lang))
    await state.set_state(ManagerStates.waiting_for_address)

@router.message(ManagerStates.waiting_for_address)
async def get_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    await message.answer("Geolokatsiya yuborilsinmi?" if lang == 'uz' else "Отправить геолокацию?", reply_markup=geolocation_keyboard(lang))
    await state.set_state(ManagerStates.asking_for_location)

@router.callback_query(F.data.in_(["manager_send_location_yes", "manager_send_location_no"]))
async def handle_location_decision(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    if call.data.endswith("yes"):
        location_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Geolokatsiyani yuborish" if lang == 'uz' else "Отправить геолокацию", request_location=True)]], resize_keyboard=True)
        await call.message.answer("Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:", reply_markup=location_keyboard)
        await state.set_state(ManagerStates.asking_for_location)
    else:
        await state.update_data(location=None)
        await show_manager_confirmation(call.message, state, lang)

@router.message(ManagerStates.asking_for_location, F.location)
async def receive_location(message: Message, state: FSMContext):
    location = f"{message.location.latitude},{message.location.longitude}"
    await state.update_data(location=location)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    await message.answer("Geolokatsiya qabul qilindi." if lang == 'uz' else "Геолокация получена.")
    await show_manager_confirmation(message, state, lang)

async def show_manager_confirmation(message_or_call, state, lang):
    data = await state.get_data()
    confirmation_text_uz = (
        f"📝 Ariza tafsilotlari:\n"
        f"📦 Zayavka turi: <b>{data.get('zayavka_type', '-')}</b>\n"
        f"#️⃣ Abonent ID: <b>{data.get('abonent_id', '-')}</b>\n"
        f"📝 Tavsif: <b>{data.get('description', '-')}</b>\n"
        f"📍 Manzil: <b>{data.get('address', '-')}</b>\n"
        f"📎 Media: {'✅' if data.get('media') else '❌'}\n"
        f"🌐 Geolokatsiya: <b>{'✅' if data.get('location') else '❌'}</b>\n"
        f"\nArizani tasdiqlaysizmi?"
    )
    confirmation_text_ru = (
        f"📝 Детали заявки:\n"
        f"📦 Тип заявки: <b>{data.get('zayavka_type', '-')}</b>\n"
        f"#️⃣ Абонент ID: <b>{data.get('abonent_id', '-')}</b>\n"
        f"📝 Описание: <b>{data.get('description', '-')}</b>\n"
        f"📍 Адрес: <b>{data.get('address', '-')}</b>\n"
        f"📎 Медиа: {'✅' if data.get('media') else '❌'}\n"
        f"🌐 Геолокация: <b>{'✅' if data.get('location') else '❌'}</b>\n"
        f"\nПодтвердить заявку?"
    )
    confirmation_text = confirmation_text_uz if lang == 'uz' else confirmation_text_ru
    await message_or_call.answer(confirmation_text, reply_markup=confirmation_keyboard(lang), parse_mode='HTML')
    await state.set_state(ManagerStates.confirming_zayavka)

