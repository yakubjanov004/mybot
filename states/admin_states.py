from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    """Admin states"""
    main_menu = State()
    waiting_for_user_id_or_username = State()
    waiting_for_telegram_id = State()
    waiting_for_phone = State()
    waiting_for_role = State()
    waiting_for_zayavka_id = State()
    waiting_for_zayavka_status = State()
    waiting_for_zayavka_assignee = State()
    waiting_for_zayavka_filter = State()
    waiting_for_settings = State()
    waiting_for_statistics = State()
    
    # User management states
    waiting_for_username = State()
    waiting_for_role_change = State()
    
    # Zayavka management states
    waiting_for_zayavka_search = State()
    waiting_for_zayavka_comment = State()
    waiting_for_zayavka_assignment = State()
    
    # Settings states
    waiting_for_notification_text = State()
    waiting_for_template_text = State()
    waiting_for_system_setting = State()
    
    # Statistics states
    waiting_for_date_range = State()
    waiting_for_statistics_type = State() 