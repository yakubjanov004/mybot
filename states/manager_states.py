from aiogram.fsm.state import State, StatesGroup

class ManagerStates(StatesGroup):
    main_menu = State()
    # Application related states
    CREATE_APPLICATION = State()
    VIEW_APPLICATIONS = State()
    FILTER_APPLICATIONS = State()
    CHANGE_STATUS = State()
    WAITING_FOR_APP_ID_FOR_STATUS_CHANGE = State()
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

    waiting_for_application_id = State()
    waiting_for_status = State()

    # Multi-step zayavka creation (like client)
    choosing_zayavka_type = State()
    waiting_for_abonent_id = State()
    waiting_for_description = State()
    waiting_for_media = State()
    waiting_for_address = State()
    asking_for_location = State()
    confirming_zayavka = State()
