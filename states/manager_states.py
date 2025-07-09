from aiogram.fsm.state import State, StatesGroup

class ManagerStates(StatesGroup):
    # Main menu
    main_menu = State()
    
    # Application management
    viewing_applications = State()
    application_details = State()
    filtering_applications = State()
    
    # Technician assignment
    assigning_technician = State()
    selecting_technician = State()
    
    # Staff management
    staff_menu = State()
    viewing_staff = State()
    staff_performance = State()
    staff_statistics = State()
    
    # Reports and analytics
    reports_menu = State()
    daily_reports = State()
    weekly_reports = State()
    monthly_reports = State()
    custom_reports = State()
    
    # Notification management
    notifications_menu = State()
    notification_settings = State()
    urgent_notifications = State()
    
    # System monitoring
    system_monitoring = State()
    performance_metrics = State()
    
    # Quality control
    quality_control = State()
    reviewing_feedback = State()
    
    # Resource management
    resource_allocation = State()
    equipment_management = State()
    adding_equipment_name = State()
    adding_equipment_model = State()
    adding_equipment_location = State()
    searching_equipment = State()
    
    # Communication
    team_communication = State()
    announcements = State()
    
    # Settings
    settings_menu = State()
    language_settings = State()
    
    # Emergency management
    emergency_response = State()
    escalation_management = State()
    
    # Training and development
    training_menu = State()
    staff_training = State()
    
    # Budget and finance
    budget_overview = State()
    cost_analysis = State()
    
    # Client relations
    client_management = State()
    vip_clients = State()
    
    # Inventory oversight
    inventory_overview = State()
    supply_management = State()

    creating_application_description = State()
    creating_application_address = State()
    creating_application_client_name = State()
    creating_application_phone = State()
    creating_application_waiting_media = State()
    creating_application_waiting_location = State()
    creating_application_waiting_confirmation = State()
    creating_application_waiting_resend = State()
    creating_application_waiting_status = State()
    creating_application_waiting_assignment = State()
    entering_application_id_for_status = State()
    entering_application_id_for_assignment = State()
    entering_application_id_for_report = State()
    entering_application_id_for_equipment = State()
    entering_application_id_for_ready = State()
    entering_application_id_for_staff = State()
    entering_application_id_for_notification = State()
    entering_application_id_for_system = State()
    entering_application_id_for_quality = State()
    marking_ready_for_installation = State()
    entering_application_id_for_quality = State()
    entering_application_id_for_quality = State()

    changing_status = State()
    adding_equipment_name = State()
    adding_equipment_model = State()
    adding_equipment_location = State()
    searching_equipment = State()
    sending_notification_user_id = State()
    sending_notification_message = State()
    selecting_new_status = State()
