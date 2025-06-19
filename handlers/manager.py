from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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
    get_available_technicians
)
from keyboards.manager_buttons import (
    get_manager_main_keyboard,
    get_status_keyboard,
    get_report_type_keyboard,
    get_equipment_keyboard,
    get_assign_technician_keyboard
)
from states.manager_states import ManagerStates
from utils.i18n import get_locale
from utils.logger import setup_logger

router = Router()
logger = setup_logger(__name__)

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
    """Show manager menu"""
    locale = get_locale(message.from_user.language_code)
    await message.answer(
        text=locale["manager"]["welcome_message"],
        reply_markup=get_manager_main_keyboard(locale)
    )

@router.message(lambda m: text_matches_locale(m.text, ["manager", "create_application"]))
async def create_application_handler(message: Message, state: FSMContext):
    """Handle application creation"""
    locale = get_locale(message.from_user.language_code)
    await state.set_state(ManagerStates.CREATE_APPLICATION)
    await message.answer(locale["manager"]["enter_application_details"])

@router.message(StateFilter(ManagerStates.CREATE_APPLICATION))
async def process_application_creation(message: Message, state: FSMContext):
    """Process application creation"""
    locale = get_locale(message.from_user.language_code)
    try:
        await create_application(message.text, message.from_user.id)
        await message.answer(locale["manager"]["application_created"])
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        await message.answer(locale["errors"]["creation_failed"])
    await state.clear()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "view_applications"]))
async def view_applications_handler(message: Message):
    """Handle viewing applications"""
    locale = get_locale(message.from_user.language_code)
    applications = await get_applications()
    if not applications:
        await message.answer(locale["manager"]["no_applications"])
        return
    
    response = locale["manager"]["applications_list_header"] + "\n\n"
    for app in applications:
        response += f"ID: {app['id']}\n"
        response += f"{locale['fields']['status']}: {app['status']}\n"
        response += f"{locale['fields']['created_at']}: {app['created_at']}\n"
        response += "-------------------\n"
    
    await message.answer(response)

@router.message(lambda m: text_matches_locale(m.text, ["manager", "change_status"]))
async def change_status_handler(message: Message, state: FSMContext):
    """Handle status change"""
    locale = get_locale(message.from_user.language_code)
    await state.set_state(ManagerStates.CHANGE_STATUS)
    await message.answer(
        locale["manager"]["enter_application_id"],
        reply_markup=get_status_keyboard(["new", "in_progress", "completed"], locale)
    )

@router.callback_query(F.data.startswith("status_"))
async def process_status_change(callback: CallbackQuery, state: FSMContext):
    """Process status change"""
    locale = get_locale(callback.from_user.language_code)
    status = callback.data.split("_")[1]
    
    async with state.get_data() as data:
        application_id = data.get("application_id")
        
    try:
        await update_application_status(application_id, status)
        await callback.message.answer(locale["manager"]["status_updated"])
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        await callback.message.answer(locale["errors"]["update_failed"])
    
    await state.clear()
    await callback.answer()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "equipment_issuance"]))
async def equipment_issuance_handler(message: Message, state: FSMContext):
    """Handle equipment issuance"""
    locale = get_locale(message.from_user.language_code)
    equipment_list = await get_equipment_list()
    
    if not equipment_list:
        await message.answer(locale["manager"]["no_equipment"])
        return
    
    await state.set_state(ManagerStates.EQUIPMENT_ISSUANCE)
    await message.answer(
        locale["manager"]["select_equipment"],
        reply_markup=get_equipment_keyboard(equipment_list, locale)
    )

@router.callback_query(F.data.startswith("equipment_"))
async def process_equipment_issuance(callback: CallbackQuery, state: FSMContext):
    """Process equipment issuance"""
    locale = get_locale(callback.from_user.language_code)
    equipment_id = callback.data.split("_")[1]
    
    try:
        # Add your equipment issuance logic here
        await callback.message.answer(locale["manager"]["equipment_issued"])
    except Exception as e:
        logger.error(f"Error issuing equipment: {e}")
        await callback.message.answer(locale["errors"]["issuance_failed"])
    
    await state.clear()
    await callback.answer()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "ready_for_installation"]))
async def ready_for_installation_handler(message: Message, state: FSMContext):
    """Handle ready for installation marking"""
    locale = get_locale(message.from_user.language_code)
    await state.set_state(ManagerStates.READY_FOR_INSTALLATION)
    await message.answer(locale["manager"]["enter_equipment_id"])

@router.message(StateFilter(ManagerStates.READY_FOR_INSTALLATION))
async def process_installation_ready(message: Message, state: FSMContext):
    """Process installation ready marking"""
    locale = get_locale(message.from_user.language_code)
    try:
        equipment_id = int(message.text)
        await mark_equipment_ready(equipment_id)
        await message.answer(locale["manager"]["marked_ready"])
    except ValueError:
        await message.answer(locale["errors"]["invalid_id"])
    except Exception as e:
        logger.error(f"Error marking ready: {e}")
        await message.answer(locale["errors"]["update_failed"])
    
    await state.clear()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "generate_report"]))
async def generate_report_handler(message: Message, state: FSMContext):
    """Handle report generation"""
    locale = get_locale(message.from_user.language_code)
    await state.set_state(ManagerStates.GENERATE_REPORT)
    await message.answer(
        locale["manager"]["select_report_type"],
        reply_markup=get_report_type_keyboard(locale)
    )

@router.callback_query(F.data.startswith("report_"))
async def process_report_generation(callback: CallbackQuery, state: FSMContext):
    """Process report generation"""
    locale = get_locale(callback.from_user.language_code)
    report_type = callback.data.split("_")[1]
    
    try:
        # Add your report generation logic here
        await callback.message.answer(locale["manager"]["report_generated"])
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        await callback.message.answer(locale["errors"]["report_failed"])
    
    await state.clear()
    await callback.answer()

@router.message(lambda m: text_matches_locale(m.text, ["manager", "assign_responsible"]))
async def assign_technician_start(message: Message, state: FSMContext):
    """Start technician assignment: ask for application ID"""
    print("DEBUG: assign_technician_start handler called")
    print(f"DEBUG: message text = {message.text}")
    
    locale = get_locale(message.from_user.language_code)
    await state.set_state(ManagerStates.ASSIGN_TECHNICIAN)
    current_state = await state.get_state()
    print(f"DEBUG: state after set_state = {current_state}")
    
    await message.answer(locale["manager"].get("enter_application_id", "Zayavka ID ni kiriting:"))
    print("DEBUG: sent ID request message")

@router.message(StateFilter(ManagerStates.ASSIGN_TECHNICIAN))
async def assign_technician_select(message: Message, state: FSMContext):
    """Show technician list for assignment"""
    print("DEBUG: assign_technician_select handler called")
    current_state = await state.get_state()
    print(f"DEBUG: current state = {current_state}")
    
    locale = get_locale(message.from_user.language_code)
    try:
        print(f"DEBUG: trying to parse ID from message: {message.text}")
        application_id = int(message.text)
        print(f"DEBUG: parsed application_id = {application_id}")
        
        # Get available technicians with active task count
        technicians = await get_available_technicians()
        print(f"DEBUG: got technicians = {technicians}")
        
        if not technicians:
            print("DEBUG: no technicians found")
            await message.answer(locale["manager"].get("no_technicians", "Hozircha texniklar yo'q."))
            await state.clear()
            return
            
        # Prepare technician list for keyboard
        tech_list = [
            {"id": t["id"], "full_name": f"{t['full_name']} ({t['active_tasks']} vazifa)"}
            for t in technicians
        ]
        print(f"DEBUG: prepared tech_list = {tech_list}")
        
        await message.answer(
            locale["manager"].get("select_technician", "Texnikni tanlang:"),
            reply_markup=get_assign_technician_keyboard(application_id, tech_list)
        )
        print("DEBUG: sent technician selection keyboard")
        
    except ValueError as e:
        print(f"DEBUG: ValueError while parsing ID: {e}")
        await message.answer(locale["errors"].get("invalid_id", "ID noto'g'ri."))
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        await message.answer(locale["errors"].get("invalid_id", "ID noto'g'ri."))
    
    print("DEBUG: clearing state")
    await state.clear()