from aiogram.fsm.state import State, StatesGroup

class ControllersStates(StatesGroup):
    main_menu = State()
    orders_control = State()
    technicians_control = State()
    reports_menu = State()
    quality_control = State()
    
    # Order management states
    priority_orders = State()
    delayed_orders = State()
    assign_technicians = State()
    order_analytics = State()
    
    # Technician management states
    performance_report = State()
    workload_balance = State()
    technician_ratings = State()
    schedule_management = State()
    
    # Reports states
    daily_report = State()
    weekly_report = State()
    monthly_report = State()
    custom_report = State()
    export_data = State()
    
    # Quality control states
    quality_check = State()
    customer_feedback = State()
    service_rating = State()
