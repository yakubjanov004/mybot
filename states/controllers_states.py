from aiogram.fsm.state import State, StatesGroup

class ControllersStates(StatesGroup):
    # Main menu states
    main_menu = State()
    
    # Orders control
    orders_control = State()
    viewing_orders = State()
    filtering_orders = State()
    
    # Technicians management states
    technicians_menu = State()
    technician_list = State()
    technician_performance = State()
    assign_technician = State()
    technician_details = State()
    
    # Quality control states
    quality_menu = State()
    customer_feedback = State()
    unresolved_issues = State()
    service_quality = State()
    quality_reports = State()
    
    # Orders monitoring states
    orders_monitoring = State()
    pending_orders = State()
    in_progress_orders = State()
    completed_orders = State()
    order_details = State()
    
    # Technicians control
    technicians_control = State()
    viewing_technician_performance = State()
    
    # Quality control
    quality_control = State()
    viewing_feedback = State()
    filtering_feedback = State()
    viewing_issues = State()
    quality_assessment = State()
    quality_trends = State()
    
    # System reports states
    system_reports = State()
    daily_report = State()
    weekly_report = State()
    monthly_report = State()
    custom_report = State()
    
    # Feedback management states
    feedback_management = State()
    feedback_filter = State()
    feedback_by_rating = State()
    feedback_by_date = State()
    feedback_response = State()
    
    # Settings states
    settings_menu = State()
    language_change = State()
    notification_settings = State()
    
    # Issue resolution states
    issue_resolution = State()
    issue_details = State()
    issue_assign = State()
    issue_escalate = State()
    
    # Reports
    reports_menu = State()
    generating_report = State()
    
    # System monitoring
    system_monitoring = State()
    
    # Assignment management
    assign_technicians = State()
    selecting_technician = State()
    
    # Priority management
    setting_priority = State()
    
    # Language selection
    selecting_language = State()
