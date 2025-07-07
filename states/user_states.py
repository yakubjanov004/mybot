from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    main_menu = State()
    waiting_for_contact = State()
    updating_contact = State()
    selecting_order_type = State()
    entering_description = State()
    entering_address = State()
    asking_for_media = State()
    waiting_for_media = State()
    asking_for_location = State()
    waiting_for_location = State()
    confirming_order = State()
    help_menu = State()
    profile_menu = State()
    language_settings = State()
    updating_address= State()
    waiting_for_comment = State()
