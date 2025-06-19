from aiogram.fsm.state import State, StatesGroup

class TechnicianStates(StatesGroup):
    """Montajchi holatlari"""
    main_menu = State()
    waiting_for_phone_number = State()
    viewing_new_tasks = State()
    viewing_my_tasks = State()
    viewing_reports = State()
    selecting_language = State()
    
    # CRM states
    waiting_for_completion_comment = State()
    waiting_for_transfer_reason = State()
