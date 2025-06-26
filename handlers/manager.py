from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.filters.callback_data import CallbackData

from database.queries import (
    create_application,
    get_applications,
    update_application_status,
    assign_responsible,
    get_equipment_list,
    mark_equipment_ready,
    get_equipment_applications,
    get_available_technicians,
    get_zayavka_by_id,
    get_user_by_telegram_id,
    get_filtered_applications,
    get_user_by_id,
    update_user_language
)
from keyboards.manager_buttons import (
    get_manager_main_keyboard,
    get_status_keyboard,
    get_report_type_keyboard,
    get_equipment_keyboard,
    get_assign_technician_keyboard,
    get_back_inline_keyboard,
    manager_main_menu,
    get_filter_keyboard,
    get_filter_results_keyboard,
    get_confirmation_keyboard,
    get_application_actions_keyboard,
    get_manager_language_keyboard,
    get_filtered_applications_keyboard,
    get_manager_back_keyboard
)
from keyboards.client_buttons import zayavka_type_keyboard, media_attachment_keyboard, geolocation_keyboard, confirmation_keyboard, get_back_keyboard, get_main_menu_keyboard
from states.manager_states import ManagerStates
from utils.i18n import get_locale
from utils.logger import setup_logger
from utils.message_utils import safe_answer_message
from handlers.technician import get_task_inline_keyboard
from loader import bot
from utils.inline_cleanup import safe_remove_inline, safe_remove_inline_call
from utils.get_lang import get_user_lang
from utils.get_role import get_user_role
from utils.templates import get_template_text
import datetime

router = Router()
logger = setup_logger('bot.manager')

def text_matches_locale(text: str, key_path: list) -> bool:
    """Check if text matches any locale version of the specified key"""
    for lang in ['uz', 'ru']:
        locale = get_locale(lang)
        current = locale
        for key in key_path:
            if key not in current:
                return False
            current = current[key]
        if text == current:
            return True
    return False

@router.message(Command("manager"))
async def manager_menu(message: Message):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    reply_markup = await get_manager_main_keyboard(lang)
    welcome_text = await get_template_text(lang, 'manager', 'manager_welcome')
    await message.answer(welcome_text, reply_markup=reply_markup)

@router.message(lambda m: text_matches_locale(m.text, ["manager", "create_application"]))
async def create_application_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    role = await get_user_role(message.from_user.id)
    await state.set_state(ManagerStates.CREATE_APPLICATION)
    text = await get_template_text(lang, role, "enter_application_details")
    reply_markup = None
    if role == 'manager':
        reply_markup = await get_manager_back_keyboard(lang)
    await safe_answer_message(
        message, 
        text,
        reply_markup=reply_markup
    )

@router.message(StateFilter(ManagerStates.CREATE_APPLICATION))
async def process_application_creation(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    role = await get_user_role(message.from_user.id)
    try:
        await create_application(message.text, message.from_user.id, created_by_role='manager')
        text = await get_template_text(lang, role, "application_created")
        await safe_answer_message(
            message, 
            text
        )
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        text = await get_template_text(lang, role, "creation_failed")
        await safe_answer_message(
            message, 
            text
        )
    await state.clear()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "view_applications"]))
async def view_applications_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    locale = get_locale(lang)
    try:
        data = await state.get_data()
        page = data.get('page', 1)
        per_page = 10
        offset = (page - 1) * per_page
        applications = await get_applications()
        if not applications:
            await safe_answer_message(
                message, 
                f"📋 {locale['manager']['no_applications']}"
            )
            return
        total = len(applications)
        start_idx = offset
        end_idx = min(start_idx + per_page, total)
        page_applications = applications[start_idx:end_idx]
        response = f"📋 {locale['manager']['applications_list_header']}\n\n"
        for app in page_applications:
            status_emoji = {
                'new': '🆕',
                'assigned': '👤',
                'accepted': '✅',
                'in_progress': '⏳',
                'completed': '✅',
                'cancelled': '❌'
            }.get(app.get('status', 'new'), '📋')
            text = await get_template_text(
                lang, 'manager', 'manager_order_info',
                order_id=app['id'],
                client_name=app.get('user_name', '-'),
                client_phone=app.get('user_phone', '-'),
                address=app.get('address', '-'),
                description=app.get('description', '-'),
                created_at=app.get('created_at', '-'),
                technician_name=app.get('technician_name', '-'),
                technician_phone=app.get('technician_phone', '-')
            )
            response += text + "\n"
            response += "─" * 30 + "\n"
        await safe_answer_message(message, response)
        if total > per_page:
            total_pages = (total + per_page - 1) // per_page
            buttons = []
            if page > 1:
                buttons.append(InlineKeyboardButton(
                    text=f"◀️ {locale['common']['prev']}",
                    callback_data=f"applications_page_{page-1}"
                ))
            if page < total_pages:
                buttons.append(InlineKeyboardButton(
                    text=f"{locale['common']['next']} ▶️",
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
        await safe_answer_message(
            message, 
            f"❌ {locale['errors']['error_occurred']}"
        )

@router.callback_query(lambda c: c.data.startswith('applications_page_'))
async def process_applications_page(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(callback.from_user.id)
    locale = get_locale(lang)
    try:
        page = int(callback.data.split('_')[-1])
        await state.update_data(page=page)
        per_page = 10
        offset = (page - 1) * per_page
        applications = await get_applications()
        if not applications:
            await safe_answer_message(
                callback.message, 
                f"📋 {locale['manager']['no_applications']}"
            )
            return
        total = len(applications)
        start_idx = offset
        end_idx = min(start_idx + per_page, total)
        page_applications = applications[start_idx:end_idx]
        response = f"📋 {locale['manager']['applications_list_header']}\n\n"
        for app in page_applications:
            status_emoji = {
                'new': '🆕',
                'assigned': '👤',
                'accepted': '✅',
                'in_progress': '⏳',
                'completed': '✅',
                'cancelled': '❌'
            }.get(app.get('status', 'new'), '📋')
            text = await get_template_text(
                lang, 'manager', 'manager_order_info',
                order_id=app['id'],
                client_name=app.get('user_name', '-'),
                client_phone=app.get('user_phone', '-'),
                address=app.get('address', '-'),
                description=app.get('description', '-'),
                created_at=app.get('created_at', '-'),
                technician_name=app.get('technician_name', '-'),
                technician_phone=app.get('technician_phone', '-')
            )
            response += text + "\n"
            response += "─" * 30 + "\n"
        await callback.message.delete()
        await safe_answer_message(callback.message, response)
        if total > per_page:
            total_pages = (total + per_page - 1) // per_page
            buttons = []
            if page > 1:
                buttons.append(InlineKeyboardButton(
                    text=f"◀️ {locale['common']['prev']}",
                    callback_data=f"applications_page_{page-1}"
                ))
            if page < total_pages:
                buttons.append(InlineKeyboardButton(
                    text=f"{locale['common']['next']} ▶️",
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
        await safe_answer_message(
            callback.message, 
            f"❌ {locale['errors']['error_occurred']}"
        )

@router.message(lambda m: text_matches_locale(m.text, ["manager", "change_status"]))
async def change_status_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = message.from_user.language_code or 'uz'
    locale = get_locale(lang)
    role = await get_user_role(message.from_user.id)
    await state.set_state(ManagerStates.WAITING_FOR_APP_ID_FOR_STATUS_CHANGE)
    reply_markup = None
    if role == 'manager':
        reply_markup = await get_manager_back_keyboard(lang)
    await safe_answer_message(
        message, 
        f"🆔 {locale['manager']['enter_application_id']}",
        reply_markup=reply_markup
    )

@router.message(StateFilter(ManagerStates.WAITING_FOR_APP_ID_FOR_STATUS_CHANGE))
async def process_app_id_for_status(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    locale = get_locale(lang)
    try:
        application_id = int(message.text)
        app = await get_zayavka_by_id(application_id)

        if not app:
            await safe_answer_message(
                message, 
                f"❌ {locale['errors'].get('application_not_found', 'Ariza topilmadi.')}"
            )
            await state.clear()
            return
        # Show detailed info (no asterisks)
        info_text = (
            f"📋 {locale['manager'].get('application_info', 'Ariza ma\'lumotlari' if lang == 'uz' else 'Информация о заявке')}\n"
            f"🆔 ID: {app['id']}\n"
            f"👤 {locale['client']['order_details'] if lang == 'uz' else 'Клиент'}: {app.get('user_name', '-')}\n"
            f"📞 {locale['admin']['enter_phone'] if lang == 'uz' else 'Телефон'}: {app.get('phone_number', '-')}\n"
            f"📝 {locale['client']['order_description'] if lang == 'uz' else 'Описание'}: {app.get('description', '-')}\n"
            f"📍 {locale['client']['enter_order_address'] if lang == 'uz' else 'Адрес'}: {app.get('address', '-')}\n"
            f"📅 {locale['client']['order_date'] if lang == 'uz' else 'Дата'}: {app.get('created_at', '-')}\n"
            f"📊 {locale['client']['order_status'] if lang == 'uz' else 'Статус'}: {locale['statuses'].get(app.get('status', 'new'), app.get('status', '-'))}"
        )
        await safe_answer_message(message, info_text)
        # Status button emojis
        status_buttons = [
            ("new", "🆕 " + locale['statuses']['new']),
            ("in_progress", "⏳ " + locale['statuses']['in_progress']),
            ("completed", "✅ " + locale['statuses']['completed']),
            ("cancelled", "❌ " + locale['statuses']['cancelled'])
        ]
        await safe_answer_message(
            message, 
            f"{locale['manager'].get('select_new_status', 'Yangi statusni tanlang:' if lang == 'uz' else 'Выберите новый статус:')}", 
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
            f"❌ {locale['errors'].get('invalid_id', 'ID raqam bo\'lishi kerak.')}"
        )
    except Exception as e:
        logger.error(f"Error processing app ID for status change: {e}")
        await safe_answer_message(
            message, 
            f"❌ {locale['errors']['error_occurred']}"
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
    locale = get_locale(lang)
    user = await get_user_by_telegram_id(callback.from_user.id)
    if not user or user.get('role') not in ['manager', 'admin']:
        await callback.answer(
            f"❌ {locale['errors']['access_denied']}", 
            show_alert=True
        )
        return
    try:
        # status callback: status_<status>_<id> (status may contain underscores)
        parts = callback.data.split("_")
        application_id = int(parts[-1])
        status = "_".join(parts[1:-1])
        await update_application_status(application_id, status)
        status_text = locale['statuses'].get(status, status)
        emoji = {
            "new": "🆕",
            "in_progress": "⏳",
            "completed": "✅",
            "cancelled": "❌"
        }.get(status, "")
        success_message = (
            f"✅ {locale['manager'].get('status_change_success', 'Status muvaffaqiyatli o\'zgartirildi' if lang == 'uz' else 'Статус успешно изменен')}\n\n"
            f"ID: {application_id}\n"
            f"{locale['manager'].get('new_status', 'Yangi status' if lang == 'uz' else 'Новый статус')}: {emoji} {status_text}"
        )
        await callback.message.edit_text(success_message)
    except (ValueError, IndexError) as e:
        logger.error(f"Could not parse status callback: {callback.data}, error: {e}")
        await safe_answer_message(
            callback.message, 
            f"❌ {locale['errors']['update_failed']}"
        )
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        await safe_answer_message(
            callback.message, 
            f"❌ {locale['errors']['update_failed']}"
        )
    finally:
        await callback.answer()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "equipment_issuance"]))
async def equipment_issuance_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Handle equipment issuance with locale support"""
    lang = message.from_user.language_code or 'uz'
    locale = get_locale(lang)
    
    equipment_list = await get_equipment_list()
    
    if not equipment_list:
        await safe_answer_message(
            message, 
            f"📦 {locale['manager']['no_equipment']}"
        )
        return
    
    await state.set_state(ManagerStates.EQUIPMENT_ISSUANCE)
    await safe_answer_message(
        message, 
        f"📦 {locale['manager']['select_equipment']}", 
        reply_markup=get_equipment_keyboard(equipment_list, locale, lang)
    )

@router.callback_query(F.data.startswith("equipment_"))
async def process_equipment_issuance(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Process equipment issuance"""
    locale = get_locale(callback.from_user.language_code)
    equipment_id = callback.data.split("_")[1]
    
    try:
        # Add your equipment issuance logic here
        await safe_answer_message(callback.message, locale["manager"]["equipment_issued"])
    except Exception as e:
        logger.error(f"Error issuing equipment: {e}")
        await safe_answer_message(callback.message, locale["errors"]["issuance_failed"])
    
    await state.clear()
    await callback.answer()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "ready_for_installation"]))
async def ready_for_installation_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Handle ready for installation marking"""
    locale = get_locale(message.from_user.language_code)
    await state.set_state(ManagerStates.READY_FOR_INSTALLATION)
    await safe_answer_message(message, locale["manager"]["enter_equipment_id"])

@router.message(StateFilter(ManagerStates.READY_FOR_INSTALLATION))
async def process_installation_ready(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Process installation ready marking"""
    locale = get_locale(message.from_user.language_code)
    try:
        equipment_id = int(message.text)
        await mark_equipment_ready(equipment_id)
        await safe_answer_message(message, locale["manager"]["marked_ready"])
    except ValueError:
        await safe_answer_message(message, locale["errors"]["invalid_id"])
    except Exception as e:
        logger.error(f"Error marking ready: {e}")
        await safe_answer_message(message, locale["errors"]["update_failed"])
    
    await state.clear()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "generate_report"]))
async def generate_report_handler(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Handle report generation with locale support"""
    lang = message.from_user.language_code or 'uz'
    locale = get_locale(lang)
    
    await state.set_state(ManagerStates.GENERATE_REPORT)
    await safe_answer_message(
        message, 
        f"📊 {locale['manager']['select_report_type']}", 
        reply_markup=get_report_type_keyboard(locale, lang)
    )

@router.callback_query(F.data.startswith("report_"))
async def process_report_generation(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Process report generation"""
    locale = get_locale(callback.from_user.language_code)
    report_type = callback.data.split("_")[1]
    
    try:
        # Add your report generation logic here
        await safe_answer_message(callback.message, locale["manager"]["report_generated"])
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await safe_answer_message(callback.message, locale["errors"]["report_failed"])
    
    await state.clear()
    await callback.answer()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "assign_responsible"]))
async def assign_technician_start(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = message.from_user.language_code or 'uz'
    locale = get_locale(lang)
    role = await get_user_role(message.from_user.id)
    logger.info("assign_technician_start handler called")
    await state.set_state(ManagerStates.ASSIGN_TECHNICIAN)
    reply_markup = None
    if role == 'manager':
        reply_markup = await get_manager_back_keyboard(lang)
    await safe_answer_message(
        message, 
        f"🆔 {locale['manager'].get('enter_application_id', 'Zayavka ID ni kiriting:')}",
        reply_markup=reply_markup
    )

@router.message(StateFilter(ManagerStates.ASSIGN_TECHNICIAN))
async def assign_technician_select(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Show application info and manager's technician selection inline keyboard with locale support"""
    lang = message.from_user.language_code or 'uz'
    locale = get_locale(lang)
    
    try:
        application_id = int(message.text)
        application = await get_zayavka_by_id(application_id)
        
        if not application:
            await safe_answer_message(
                message, 
                f"❌ {locale['errors'].get('application_not_found', 'Ariza topilmadi')}"
            )
            await state.clear()
            return
        
        # Detailed application info
        info = (
            f"📝 {locale['manager'].get('application_details', 'Ariza tafsilotlari' if lang == 'uz' else 'Детали заявки')}\n\n"
            f"🆔 ID: {application['id']}\n"
            f"👤 {locale['client']['order_details'] if lang == 'uz' else 'Клиент'}: {application.get('user_name', '-')}\n"
            f"📱 {locale['admin']['enter_phone'] if lang == 'uz' else 'Телефон'}: {application.get('phone_number', '-')}\n"
            f"📝 {locale['client']['order_description'] if lang == 'uz' else 'Описание'}: {application.get('description', '-')}\n"
            f"📍 {locale['client']['enter_order_address'] if lang == 'uz' else 'Адрес'}: {application.get('address', '-')}\n"
            f"🏷️ {locale['manager'].get('subscriber_id', 'Abonent ID' if lang == 'uz' else 'ID абонента')}: {application.get('abonent_id', '-')}\n"
            f"🔖 {locale['manager'].get('type', 'Turi' if lang == 'uz' else 'Тип')}: {application.get('zayavka_type', '-')}\n"
            f"👨‍🔧 {locale['manager'].get('assigned_to', 'Biriktirilgan' if lang == 'uz' else 'Назначен')}: {application.get('assigned_name', '-')}\n"
            f"📅 {locale['client']['order_date'] if lang == 'uz' else 'Дата создания'}: {application.get('created_at', '-')}\n"
            f"🏷️ {locale['client']['order_status'] if lang == 'uz' else 'Статус'}: {locale['statuses'].get(application.get('status', 'new'), application.get('status', '-'))}"
        )
        
        # If already assigned, show warning
        assigned_name = application.get('assigned_name')
        if assigned_name and assigned_name != '-':
            warning_text = f"⚠️ {locale['manager'].get('already_assigned_warning', 'Diqqat! Bu arizaga allaqachon texnik biriktirilgan' if lang == 'uz' else 'Внимание! К этой заявке уже назначен техник')}: **{assigned_name}**"
            await message.answer(warning_text)
        
        # Send info with media if available
        if application.get('media'):
            try:
                await message.answer_photo(photo=application['media'], caption=info)
            except Exception:
                await message.answer(info)
        else:
            await message.answer(info)
        
        # Fetch available technicians
        technicians = await get_available_technicians()
        if not technicians:
            await safe_answer_message(
                message, 
                f"👨‍🔧 {locale['manager'].get('no_technicians', 'Hozircha texniklar yo\'q.')}"
            )
            await state.clear()
            return
        
        tech_list = [
            {
                "id": t["id"], 
                "full_name": f"{t['full_name']} ({t['active_tasks']} {locale['manager'].get('tasks', 'vazifa' if lang == 'uz' else 'задач')})"
            }
            for t in technicians
        ]
        
        await message.answer(
            f"👨‍🔧 {locale['manager'].get('select_technician', 'Texnikni tanlang:')}",
            reply_markup=get_assign_technician_keyboard(application_id, tech_list, locale, lang)
        )
        await state.update_data(assigning_zayavka_id=application_id)
        
    except ValueError:
        await safe_answer_message(
            message, 
            f"❌ {locale['errors'].get('invalid_id', 'ID noto\'g\'ri.')}"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error in assign_technician_select: {e}")
        await safe_answer_message(
            message, 
            f"❌ {locale['errors']['error_occurred']}"
        )
        await state.clear()

@router.callback_query(F.data == "back_to_assign_technician")
async def back_to_assign_technician_handler(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Handle 'Back' button: return to technician assignment step with locale support"""
    lang = callback.from_user.language_code or 'uz'
    locale = get_locale(lang)
    
    await safe_answer_message(
        callback.message, 
        f"🆔 {locale['manager'].get('enter_application_id', 'Zayavka ID ni kiriting:')}"
    )
    await state.set_state(ManagerStates.ASSIGN_TECHNICIAN)
    await callback.answer()

@router.callback_query(F.data.startswith("manager_assign_zayavka_"))
async def manager_assign_zayavka_handler(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Assign technician to application and notify both parties with locale support"""
    lang = callback.from_user.language_code or 'uz'
    locale = get_locale(lang)
    
    try:
        # callback_data: manager_assign_zayavka_{application_id}_{tech_id}
        _, application_id, technician_id = callback.data.rsplit('_', 2)
        application_id = int(application_id)
        technician_id = int(technician_id)
        
        # 1. Assign application to technician
        await assign_responsible(application_id, technician_id)
        
        # 2. Get technician's telegram_id
        technician = await get_user_by_id(technician_id)
        if technician and technician.get("telegram_id"):
            tech_telegram_id = technician["telegram_id"]
            application = await get_zayavka_by_id(application_id)
            
            # Get technician's language preference
            tech_lang = technician.get('language_code', 'uz')
            tech_locale = get_locale(tech_lang)
            
            # Short info for technician
            tech_info = (
                f"🆕 {tech_locale['technician'].get('new_task_assigned', 'Sizga yangi vazifa biriktirildi!' if tech_lang == 'uz' else 'Вам назначена новая задача!')}\n\n"
                f"🆔 **{tech_locale['manager'].get('application', 'Zayavka' if tech_lang == 'uz' else 'Заявка')} ID:** {application['id']}\n"
                f"👤 **{tech_locale['client']['order_details'] if tech_lang == 'uz' else 'Клиент'}:** {application.get('user_name', '-')}\n"
                f"📝 **{tech_locale['client']['order_description'] if tech_lang == 'uz' else 'Описание'}:** {application.get('description', '-')}\n"
                f"📍 **{tech_locale['client']['enter_order_address'] if tech_lang == 'uz' else 'Адрес'}:** {application.get('address', '-')}\n"
                f"📅 **{tech_locale['client']['order_date'] if tech_lang == 'uz' else 'Дата'}:** {application.get('created_at', '-')}"
            )
            
            inline_kb = get_task_inline_keyboard(application_id, 'assigned')
            
            if application.get('media'):
                try:
                    await bot.send_photo(
                        chat_id=tech_telegram_id, 
                        photo=application['media'], 
                        caption=tech_info, 
                        reply_markup=inline_kb
                    )
                except Exception:
                    await bot.send_message(
                        chat_id=tech_telegram_id, 
                        text=tech_info, 
                        reply_markup=inline_kb
                    )
            else:
                await bot.send_message(
                    chat_id=tech_telegram_id, 
                    text=tech_info, 
                    reply_markup=inline_kb
                )
        
        # 3. Success message to manager
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            if "message is not modified" in str(e):
                pass
            else:
                logger.error(f"Error editing reply markup: {e}")
        
        success_message = (
            f"✅ {locale['manager'].get('assignment_success', 'Muvaffaqiyatli biriktirildi!' if lang == 'uz' else 'Успешно назначено!')}\n\n"
            f"🆔 {locale['manager'].get('application', 'Ariza' if lang == 'uz' else 'Заявка')}: #{application_id}\n"
            f"👨‍🔧 {locale['technician']['main_menu'] if lang == 'uz' else 'Техник'}: {technician.get('full_name', '-')}"
        )
        
        await safe_answer_message(
            callback.message, 
            success_message, 
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Error assigning technician: {e}")
        await safe_answer_message(
            callback.message, 
            f"❌ {locale['errors'].get('assign_failed', 'Biriktirishda xatolik.')}"
        )
    finally:
        await state.clear()
        await callback.answer()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "filter_applications"]))
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
    locale = get_locale(lang)
    try:
        filter_text = f"🔍 {locale['manager'].get('select_filters', 'Kerakli filtrlarni tanlang:' if lang == 'uz' else 'Выберите нужные фильтры:')}"
        sent_msg = await message.answer(filter_text, reply_markup=get_filter_keyboard(locale, lang))
        await state.update_data(last_menu_msg_id=sent_msg.message_id)
    except Exception as e:
        logger.error(f"Filter menu error: {str(e)}", exc_info=True)
        await message.answer(f"❌ {locale['errors']['error_occurred']}")

@router.callback_query(F.data.startswith("filter_"))
async def process_filter(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(callback.from_user.id)
    locale = get_locale(lang)
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
                filter_label = f"📋 {locale['manager'].get('all_statuses', 'Barcha statuslar' if lang == 'uz' else 'Все статусы')}"
                result = await get_filtered_applications(**filter_kwargs)
            else:
                status_emoji = {
                    'new': '🆕',
                    'in_progress': '⏳',
                    'completed': '✅',
                    'cancelled': '❌'
                }.get(status, '📋')
                status_label = locale['statuses'].get(status, status)
                filter_label = f"{status_emoji} {locale['manager'].get('status_label', 'Status:' if lang == 'uz' else 'Статус:')} {status_label}"
                result = await get_filtered_applications(statuses=[status], **filter_kwargs)
        elif filter_type == 'date':
            date_type = parts[2]
            today = datetime.date.today()
            date_labels = {
                'today': f"📅 {locale['manager'].get('today', 'Bugun' if lang == 'uz' else 'Сегодня')}",
                'yesterday': f"📅 {locale['manager'].get('yesterday', 'Kecha' if lang == 'uz' else 'Вчера')}",
                'week': f"📅 {locale['manager'].get('this_week', 'Bu hafta' if lang == 'uz' else 'На этой неделе')}",
                'month': f"📅 {locale['manager'].get('this_month', 'Bu oy' if lang == 'uz' else 'В этом месяце')}"
            }
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
                filter_label = f"👨‍🔧 {locale['manager'].get('assigned', 'Biriktirilgan' if lang == 'uz' else 'Назначенные')}"
                result = await get_filtered_applications(assigned_only=True, **filter_kwargs)
            elif tech_type == 'unassigned':
                filter_label = f"👨‍🔧 {locale['manager'].get('unassigned', 'Biriktirilmagan' if lang == 'uz' else 'Не назначенные')}"
                result = await get_filtered_applications(technician_id=0, **filter_kwargs)
        elif filter_type == 'clear':
            filter_text = f"🔍 {locale['manager'].get('select_filters', 'Kerakli filtrlarni tanlang:' if lang == 'uz' else 'Выберите нужные фильтры:')}"
            try:
                await callback.message.edit_text(
                    filter_text,
                    reply_markup=get_filter_keyboard(locale, lang)
                )
            except Exception as e:
                logger.error(f"Edit text error (clear): {str(e)}", exc_info=True)
                await callback.answer(f"❌ {locale['errors'].get('error_occurred', 'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка')}", show_alert=True)
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
        labels = {
            'status': locale['manager'].get('status_label', 'Status:' if lang == 'uz' else 'Статус:'),
            'client': locale['manager'].get('client_label', 'Mijoz:' if lang == 'uz' else 'Клиент:'),
            'address': locale['manager'].get('address_label', 'Manzil:' if lang == 'uz' else 'Адрес:'),
            'description': locale['manager'].get('description_label', 'Izoh:' if lang == 'uz' else 'Описание:'),
            'technician': locale['manager'].get('technician_label', 'Texnik:' if lang == 'uz' else 'Техник:'),
            'created': locale['manager'].get('created_label', 'Yaratilgan:' if lang == 'uz' else 'Создано:'),
            'no_technician': locale['manager'].get('no_technician', 'Texnik biriktirilmagan' if lang == 'uz' else 'Не назначен'),
            'no_address': locale['manager'].get('no_address', 'Manzil ko\'rsatilmagan' if lang == 'uz' else 'Адрес не указан'),
            'filtered': locale['manager'].get('filtered_applications', 'Filtrlangan arizalar' if lang == 'uz' else 'Отфильтрованные заявки'),
            'no_applications': locale['manager'].get('no_applications_found', 'Arizalar topilmadi' if lang == 'uz' else 'Заявки не найдены'),
            'clear_filter': locale['manager'].get('clear_filter', 'Filterni tozalash' if lang == 'uz' else 'Сбросить фильтр'),
        }
        applications_text = f"{filter_label} ({current_page}/{total_pages}):\n\n"
        if applications:
            for app in applications:
                status = app.get('status', 'new')
                status_emoji = status_emojis.get(status, '📋')
                applications_text += (
                    f"{status_emoji} {labels['status']} {locale['statuses'].get(status, status)}\n"
                    f"👤 {labels['client']} {app.get('user_name', 'Noma\'lum')} ({app.get('client_phone', '-')})\n"
                    f"📍 {labels['address']} {app.get('address') or labels['no_address']}\n"
                    f"📝 {labels['description']} {app.get('description', '')[:100]}\n"
                    f"👨‍🔧 {labels['technician']} {app.get('technician_name', labels['no_technician'])} ({app.get('technician_phone', '-')})\n"
                    f"🕒 {labels['created']} {app.get('created_at', '')}\n"
                    "\n"
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
            await callback.answer(f"❌ {locale['errors'].get('error_occurred', 'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка')}", show_alert=True)
            return
        await callback.answer()
    except Exception as e:
        logger.error(f"Error processing filter: {str(e)}", exc_info=True)
        await callback.answer(
            f"❌ {locale['errors'].get('error_occurred', 'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка')}",
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
    locale = get_locale(lang)
    
    try:
        app_id = int(callback.data.replace("view_application_", ""))
        app = await get_zayavka_by_id(app_id)
        
        if not app:
            await callback.answer(f"❌ {locale['errors'].get('application_not_found', 'Ariza topilmadi.')}", show_alert=True)
            return
        
        status_emoji = {
            'new': '🆕',
            'in_progress': '⏳',
            'completed': '✅',
            'cancelled': '❌'
        }.get(app.get('status', 'new'), '📋')
        
        app_text = (
            f"📋 {locale['manager'].get('application_info', 'Ariza ma\'lumotlari' if lang == 'uz' else 'Информация о заявке')}\n\n"
            f"🆔 ID: {app['id']}\n"
            f"👤 {locale['client']['order_details'] if lang == 'uz' else 'Клиент'}: {app.get('user_name', '-')}\n"
            f"📞 {locale['admin']['enter_phone'] if lang == 'uz' else 'Телефон'}: {app.get('phone_number', '-')}\n"
            f"📝 {locale['client']['order_description'] if lang == 'uz' else 'Описание'}: {app.get('description', '-')}\n"
            f"📍 {locale['client']['enter_order_address'] if lang == 'uz' else 'Адрес'}: {app.get('address', '-')}\n"
            f"📅 {locale['client']['order_date'] if lang == 'uz' else 'Дата'}: {app.get('created_at', '-')}\n"
            f"📊 {locale['client']['order_status'] if lang == 'uz' else 'Статус'}: {status_emoji} {locale['statuses'].get(app.get('status', 'new'), app.get('status', '-'))}"
        )
        
        # Show application info with back to filter button
        await callback.message.edit_text(
            app_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"🔍 {locale['manager'].get('back_to_filter', 'Filtrlashga qaytish' if lang == 'uz' else 'Вернуться к фильтрам')}", 
                    callback_data="filter_clear"
                )
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error viewing filtered application: {str(e)}", exc_info=True)
        await callback.answer(f"❌ {locale['errors']['error_occurred']}", show_alert=True)
    
    await callback.answer()

@router.message(lambda m: text_matches_locale(m.text, ["common", "change_language"]))
async def manager_change_language(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    """Show language selection for manager"""
    lang = message.from_user.language_code or 'uz'
    locale = get_locale(lang)
    
    await message.answer(
        f"🌐 {locale['common']['select_language']}",
        reply_markup=get_manager_language_keyboard(locale, lang)
    )

@router.callback_query(F.data.startswith("manager_lang_"))
async def process_manager_language_change(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Process manager language change"""
    try:
        # Get new language from callback data
        new_lang = callback.data.split("_")[-1]  # manager_lang_uz -> uz
        
        # Update user's language in database
        await update_user_language(callback.from_user.id, new_lang)
        
        # Get new locale
        new_locale = get_locale(new_lang)
        
        # Send confirmation message
        await callback.message.edit_text(
            f"✅ {new_locale['common']['language_changed']}",
            reply_markup=None
        )
        
        # Show main menu in new language with updated keyboard
        await callback.message.answer(
            f"👔 {new_locale['manager']['welcome_message']}",
            reply_markup=await get_manager_main_keyboard(new_lang)
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Manager tilni o'zgartirishda xatolik: {str(e)}", exc_info=True)
        await callback.message.answer("❌ Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")
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
    locale = get_locale(lang)
    # To'g'ri reply_markup va xabarni yangilash
    reply_markup = await get_manager_main_keyboard(lang)
    await callback.message.edit_text(
        f"👔 {locale['manager']['welcome_message']}",
        reply_markup=reply_markup
    )
    await callback.answer()

@router.message(F.text.in_([
 "Asosiy menyu", "Главное меню"
]))
async def manager_back_to_main_menu(message: Message, state: FSMContext):
    role = await get_user_role(message.from_user.id)
    if role == "manager":
        await state.clear()
        lang = await get_user_lang(message.from_user.id)
        reply_markup = await get_manager_main_keyboard(lang)
        welcome_text = await get_template_text(lang, 'manager', 'welcome_message')
        # Remove old keyboard first
        await message.answer(".", reply_markup=ReplyKeyboardRemove())
        await message.answer(welcome_text, reply_markup=reply_markup)

@router.message(F.text.in_(["Yangi ariza", "Новая заявка"]))
async def manager_new_order(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    await state.clear()
    await message.answer(
        "Iltimos, ariza turini tanlang:",
        reply_markup=zayavka_type_keyboard(lang)
    )
    await state.set_state(ManagerStates.choosing_zayavka_type)

@router.callback_query(F.data.in_(["zayavka_type_b2b", "zayavka_type_b2c"]))
async def manager_choose_zayavka_type(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    lang = await get_user_lang(call.from_user.id)
    zayavka_type = "Jismoniy shaxs" if call.data == "zayavka_type_b2b" else "Yuridik shaxs"
    await state.update_data(zayavka_type=zayavka_type)
    await call.message.edit_text("Iltimos, abonent ID ni kiriting:")
    await state.set_state(ManagerStates.waiting_for_abonent_id)

@router.message(ManagerStates.waiting_for_abonent_id)
async def manager_get_abonent_id(message: Message, state: FSMContext):
    abonent_id = message.text
    await state.update_data(abonent_id=abonent_id)
    await message.answer("Iltimos, ariza tavsifini kiriting:", reply_markup=get_back_keyboard("uz"))
    await state.set_state(ManagerStates.waiting_for_description)

@router.message(ManagerStates.waiting_for_description)
async def manager_get_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.answer("Media fayl biriktirasizmi?", reply_markup=media_attachment_keyboard("uz"))
    await state.set_state(ManagerStates.waiting_for_media)

@router.message(ManagerStates.waiting_for_media, F.photo | F.document)
async def manager_receive_media(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    await state.update_data(media=file_id)
    await message.answer("Iltimos, manzilni kiriting:", reply_markup=get_back_keyboard("uz"))
    await state.set_state(ManagerStates.waiting_for_address)

@router.message(ManagerStates.waiting_for_media)
async def manager_skip_media(message: Message, state: FSMContext):
    # Agar media yuborilmasa, "O'tkazib yuborish" deb yozsa
    if message.text and message.text.lower() in ["o'tkazib yuborish", "пропустить"]:
        await state.update_data(media=None)
        await message.answer("Iltimos, manzilni kiriting:", reply_markup=get_back_keyboard("uz"))
        await state.set_state(ManagerStates.waiting_for_address)

@router.message(ManagerStates.waiting_for_address)
async def manager_get_address(message: Message, state: FSMContext):
    address = message.text.strip()
    await state.update_data(address=address)
    await message.answer("Geolokatsiya yuborilsinmi?", reply_markup=geolocation_keyboard("uz"))
    await state.set_state(ManagerStates.asking_for_location)

@router.callback_query(F.data.in_(["send_location_yes", "send_location_no"]))
async def manager_ask_for_location(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    if call.data == "send_location_yes":
        location_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Geolokatsiyani yuborish", request_location=True)]],
            resize_keyboard=True
        )
        await call.message.delete()
        await call.message.answer("Geolokatsiyani yuboring:", reply_markup=location_keyboard)
        await state.set_state(ManagerStates.asking_for_location)
    else:
        await state.update_data(location=None)
        await call.message.delete()
        await manager_show_order_confirmation(call.message, state)
        await state.set_state(ManagerStates.confirming_zayavka)

@router.message(ManagerStates.asking_for_location, F.location)
async def manager_receive_location(message: Message, state: FSMContext):
    location = f"{message.location.latitude},{message.location.longitude}"
    await state.update_data(location=location)
    await message.answer("Geolokatsiya qabul qilindi.", reply_markup=get_main_menu_keyboard("uz"))
    await manager_show_order_confirmation(message, state)
    await state.set_state(ManagerStates.confirming_zayavka)

async def manager_show_order_confirmation(message_or_call, state):
    data = await state.get_data()
    text = (
        f"Ariza ma'lumotlari:\n"
        f"Turi: {data.get('zayavka_type', '-')}, Abonent ID: {data.get('abonent_id', '-')},\n"
        f"Tavsif: {data.get('description', '-')}, Manzil: {data.get('address', '-')},\n"
        f"Media: {'✅' if data.get('media') else '❌'}, Geolokatsiya: {data.get('location', '-') or '❌'}"
    )
    await message_or_call.answer(text, reply_markup=confirmation_keyboard("uz"))

@router.callback_query(F.data == "confirm_zayavka")
async def manager_confirm_zayavka(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    data = await state.get_data()
    user = await get_user_by_telegram_id(call.from_user.id)
    try:
        async with db_manager.get_connection() as conn:
            db_user = await conn.fetchrow("SELECT id, full_name FROM users WHERE telegram_id = $1", call.from_user.id)
            if not db_user:
                await call.message.answer("Foydalanuvchi topilmadi!")
                return
            zayavka = await conn.fetchrow(
                '''INSERT INTO zayavki (user_id, zayavka_type, abonent_id, description, address, media, location, status, created_by_role)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *''',
                db_user['id'],
                data.get("zayavka_type"),
                data.get("abonent_id"),
                data.get("description"),
                data.get("address"),
                data.get("media"),
                data.get("location"),
                'new',
                'manager'
            )
            await call.message.answer(f"✅ Ariza yaratildi! ID: {zayavka['id']}")
    except Exception as e:
        await call.message.answer(f"Ariza yaratishda xatolik: {e}")
    await state.clear()
