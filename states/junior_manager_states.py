from aiogram.fsm.state import StatesGroup, State

class JuniorManagerMainMenuStates(StatesGroup):
    main_menu = State()

class JuniorManagerOrderStates(StatesGroup):
    creating = State()
    viewing = State()
    filtering = State()
    assigning = State()
    reporting = State()

class JuniorManagerFilterStates(StatesGroup):
    selecting_filter = State()
    applying_filter = State()

class JuniorManagerAssignStates(StatesGroup):
    selecting_technician = State()
    confirming_assignment = State()

class JuniorManagerStatisticsStates(StatesGroup):
    viewing_statistics = State()

class JuniorManagerLanguageStates(StatesGroup):
    selecting_language = State() 