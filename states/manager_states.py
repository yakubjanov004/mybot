from aiogram.fsm.state import State, StatesGroup

class ManagerStates(StatesGroup):
    # Application related states
    CREATE_APPLICATION = State()
    VIEW_APPLICATIONS = State()
    FILTER_APPLICATIONS = State()
    CHANGE_STATUS = State()
    SELECT_STATUS = State()
    
    # Assignment related states
    ASSIGN_RESPONSIBLE = State()
    SELECT_RESPONSIBLE = State()
    ASSIGN_TECHNICIAN = State()
    
    # Report related states
    GENERATE_REPORT = State()
    SELECT_REPORT_TYPE = State()
    
    # Equipment related states
    EQUIPMENT_ISSUANCE = State()
    SELECT_EQUIPMENT = State()
    READY_FOR_INSTALLATION = State()
    VIEW_EQUIPMENT_APPLICATIONS = State()
