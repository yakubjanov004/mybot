from aiogram.fsm.state import State, StatesGroup

class CallCenterStates(StatesGroup):
    # Main menu
    main_menu = State()
    
    # Order creation states
    new_order_phone = State()
    new_client_name = State()
    new_client_address = State()
    select_service_type = State()
    order_description = State()
    order_priority = State()
    
    # Client search states
    client_search = State()
    
    # Feedback states
    waiting_feedback = State()
    feedback_comment = State()
    
    # Chat states
    in_chat = State()
    chat_file_upload = State()
    chat_closing = State()
    
    # Statistics states
    viewing_stats = State()
    viewing_calls = State()
