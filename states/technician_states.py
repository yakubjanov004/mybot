from aiogram.fsm.state import State, StatesGroup

class TechnicianStates(StatesGroup):
    # Main menu states
    main_menu = State()
    
    # Tasks management states
    my_tasks = State()
    task_details = State()
    accept_task = State()
    start_task = State()
    complete_task = State()
    task_solution = State()
    task_media = State()
    
    # Help request states
    help_menu = State()
    help_type = State()
    technical_help = State()
    equipment_help = State()
    navigation_help = State()
    emergency_help = State()
    help_description = State()
    help_media = State()
    help_location = State()
    
    # Location and navigation states
    location_menu = State()
    send_location = State()
    get_directions = State()
    nearby_tasks = State()
    
    # Manager communication states
    contact_manager = State()
    manager_message = State()
    urgent_request = State()
    
    # Equipment request states
    equipment_request = State()
    equipment_type = State()
    equipment_quantity = State()
    equipment_reason = State()
    
    # Status update states
    status_update = State()
    work_progress = State()
    completion_report = State()
    
    # Settings states
    settings_menu = State()
    language_change = State()
    availability_status = State()
    notification_settings = State()
    
    # Emergency states
    emergency_menu = State()
    emergency_type = State()
    emergency_description = State()
    emergency_location = State()

    waiting_for_phone_number = State()
    waiting_for_completion_comment = State()
    waiting_for_transfer_reason = State()
    waiting_for_help_description = State()
    waiting_for_location = State()
    waiting_for_manager_message = State()
    waiting_for_equipment_request = State()
    waiting_for_equipment_type = State()
    waiting_for_equipment_quantity = State()
    waiting_for_equipment_reason = State()
    waiting_for_status_update = State()
    waiting_for_work_progress = State()
    waiting_for_completion_report = State()
    waiting_for_language_change = State()
