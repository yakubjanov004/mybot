from aiogram.fsm.state import State, StatesGroup

class StartStates(StatesGroup):
    selecting_language = State()
    entering_full_name = State()
    waiting_for_contact = State()

class MainMenuStates(StatesGroup):
    main_menu = State()

class OrderStates(StatesGroup):
    selecting_order_type = State()
    entering_description = State()
    entering_address = State()
    asking_for_media = State()
    waiting_for_media = State()
    asking_for_location = State()
    waiting_for_location = State()
    waiting_for_contact = State()
    confirming_order = State()

class ConnectionOrderStates(StatesGroup):
    selecting_connection_type = State()
    selecting_tariff = State()
    entering_description = State()
    entering_address = State()
    asking_for_geo = State()
    waiting_for_geo = State()
    confirming = State()

class ProfileStates(StatesGroup):
    profile_menu = State()
    editing_name = State()
    editing_address = State()
    updating_contact = State()
    updating_address = State()

class ContactStates(StatesGroup):
    waiting_for_contact = State()
    updating_contact = State()

class HelpStates(StatesGroup):
    help_menu = State()

class FeedbackStates(StatesGroup):
    waiting_for_comment = State()
    waiting_for_rating = State()  # Qo'shildi, kodda ishlatiladi

class LanguageStates(StatesGroup):
    language_settings = State()