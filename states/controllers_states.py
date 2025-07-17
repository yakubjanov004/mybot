from aiogram.fsm.state import State, StatesGroup

class ControllerInboxStates(StatesGroup):
    inbox = State()

class ControllerMainMenuStates(StatesGroup):
    main_menu = State()

class ControllerOrdersStates(StatesGroup):
    orders_control = State()
    viewing_orders = State()
    filtering_orders = State()
    orders_monitoring = State()
    pending_orders = State()
    in_progress_orders = State()
    completed_orders = State()
    order_details = State()

class ControllerTechnicianStates(StatesGroup):
    technicians_menu = State()
    technician_list = State()
    technician_performance = State()
    assign_technician = State()
    technician_details = State()
    technicians_control = State()
    viewing_technician_performance = State()
    assign_technicians = State()
    selecting_technician = State()

class ControllerQualityStates(StatesGroup):
    quality_menu = State()
    customer_feedback = State()
    unresolved_issues = State()
    service_quality = State()
    quality_reports = State()
    quality_control = State()
    viewing_feedback = State()
    filtering_feedback = State()
    viewing_issues = State()
    quality_assessment = State()
    quality_trends = State()

class ControllerReportsStates(StatesGroup):
    system_reports = State()
    daily_report = State()
    weekly_report = State()
    monthly_report = State()
    custom_report = State()
    reports_menu = State()
    generating_report = State()

class ControllerFeedbackStates(StatesGroup):
    feedback_management = State()
    feedback_filter = State()
    feedback_by_rating = State()
    feedback_by_date = State()
    feedback_response = State()

class ControllerSettingsStates(StatesGroup):
    settings_menu = State()
    language_change = State()
    notification_settings = State()
    selecting_language = State()

class ControllerIssueStates(StatesGroup):
    issue_resolution = State()
    issue_details = State()
    issue_assign = State()
    issue_escalate = State()

class ControllerPriorityStates(StatesGroup):
    setting_priority = State()
