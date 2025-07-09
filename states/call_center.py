from aiogram.fsm.state import State, StatesGroup

class CallCenterStates(StatesGroup):
    # Main menu
    main_menu = State()
    
    # New order creation
    new_order_phone = State()
    new_client_name = State()
    new_client_address = State()
    select_service_type = State()
    order_description = State()
    order_priority = State()
    
    # Customer management states
    customer_search = State()
    customer_details = State()
    customer_orders = State()
    
    # Call management states
    logging_call = State()
    call_duration = State()
    call_notes = State()
    create_order = State()
    order_address = State()
    order_phone = State()
    order_confirm = State()
    
    # Reports states
    reports_menu = State()
    conversion_report = State()
    calls_report = State()
    
    # Settings states
    settings_menu = State()
    language_change = State()
    notifications_settings = State()
    
    # Feedback management
    waiting_feedback = State()
    feedback_comment = State()
    
    # Statistics
    viewing_statistics = State()
    
    # Chat management
    in_chat = State()
    chat_file_upload = State()
    chat_closing = State()
    
    # Language selection
    selecting_language = State()
    
    # Order management
    order_details = State()
    order_status_update = State()
    
    # Client management
    client_details = State()
    client_history = State()
    
    # Call management
    active_call = State()
    call_completion = State()
    client_search = State()
    client_details = State()
    client_history = State()
    client_orders = State()
    client_feedback = State()
    client_chat = State()
    client_chat_file = State()
    client_chat_closing = State()
    client_chat_closing_confirm = State()
    statistics = State()