from aiogram.fsm.state import State, StatesGroup

class TechnicianMainMenuStates(StatesGroup):
    main_menu = State()
    waiting_for_phone_number = State()

class TechnicianTasksStates(StatesGroup):
    my_tasks = State()
    task_details = State()
    accept_task = State()
    start_task = State()
    complete_task = State()
    task_solution = State()
    task_media = State()
    waiting_for_completion_comment = State()
    waiting_for_transfer_reason = State()

class TechnicianHelpStates(StatesGroup):
    help_menu = State()
    help_type = State()
    technical_help = State()
    equipment_help = State()
    navigation_help = State()
    emergency_help = State()
    help_description = State()
    help_media = State()
    help_location = State()
    waiting_for_help_description = State()
    waiting_for_location = State()

class TechnicianCommunicationStates(StatesGroup):
    contact_manager = State()
    manager_message = State()
    urgent_request = State()
    waiting_for_manager_message = State()
    waiting_for_location = State()

class TechnicianEquipmentStates(StatesGroup):
    equipment_request = State()
    equipment_type = State()
    equipment_quantity = State()
    equipment_reason = State()
    waiting_for_equipment_request = State()
    waiting_for_equipment_type = State()
    waiting_for_equipment_quantity = State()
    waiting_for_equipment_reason = State()

class TechnicianProfileStates(StatesGroup):
    profile = State()

class TechnicianReportsStates(StatesGroup):
    completion_report = State()
    work_progress = State()
    status_update = State()
    waiting_for_status_update = State()
    waiting_for_work_progress = State()
    waiting_for_completion_report = State()

class TechnicianSettingsStates(StatesGroup):
    settings_menu = State()
    language_change = State()
    availability_status = State()
    notification_settings = State()
    waiting_for_language_change = State()

class TechnicianTechnicalServiceStates(StatesGroup):
    entering_resolution_comments = State()
    documenting_equipment = State()
    completing_with_warehouse = State()

class TechnicalServiceStates(StatesGroup):
    documenting_equipment = State()
    completing_with_warehouse = State()
