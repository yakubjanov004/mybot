from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    waiting_for_phone_number = State()
    choosing_zayavka_type = State()
    waiting_for_abonent_id = State()
    waiting_for_description = State()
    waiting_for_address = State()
    asking_for_media = State()
    waiting_for_media = State()
    asking_for_location = State()
    waiting_for_location = State()
    confirming_zayavka = State()
    main_menu = State()
    selecting_language = State() 