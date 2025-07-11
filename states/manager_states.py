from aiogram.fsm.state import State, StatesGroup

class ManagerMainMenuStates(StatesGroup):
    main_menu = State()

class ManagerApplicationStates(StatesGroup):
    creating_application_client_name = State()
    creating_application_address = State()
    creating_application_phone = State()
    creating_application_description = State()
    creating_application_media = State()
    creating_application_location = State()
    confirming_application = State()
    selecting_connection_type = State()
    selecting_tariff = State()
    waiting_for_media = State()
    asking_for_location = State()
    waiting_for_location = State()
    viewing_applications = State()
    application_details = State()
    filtering_applications = State()
    entering_application_id_for_assignment = State()
    entering_application_id_for_status = State()
    selecting_new_status = State()
    selecting_technician = State()

class ManagerEquipmentStates(StatesGroup):
    equipment_management = State()
    adding_equipment_name = State()
    adding_equipment_model = State()
    adding_equipment_location = State()
    searching_equipment = State()

class ManagerNotificationStates(StatesGroup):
    notifications_menu = State()
    notification_settings = State()
    urgent_notifications = State()
    sending_notification_user_id = State()
    sending_notification_message = State()

class ManagerStaffStates(StatesGroup):
    staff_menu = State()
    viewing_staff = State()
    staff_performance = State()
    staff_statistics = State()

class ManagerReportsStates(StatesGroup):
    reports_menu = State()
    daily_reports = State()
    weekly_reports = State()
    monthly_reports = State()
    custom_reports = State()

class ManagerStatisticsStates(StatesGroup):
    performance_metrics = State()
    system_monitoring = State()

class ManagerStatusManagementStates(StatesGroup):
    entering_application_id_for_status = State()
    selecting_new_status = State()

class ManagerTechnicianAssignmentStates(StatesGroup):
    entering_application_id_for_assignment = State()
    selecting_technician = State()

class ManagerLanguageStates(StatesGroup):
    language_settings = State()
