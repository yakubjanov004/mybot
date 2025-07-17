from aiogram.fsm.state import State, StatesGroup

class CallCenterInboxStates(StatesGroup):
    inbox = State()

class CallCenterMainMenuStates(StatesGroup):
    main_menu = State()

class CallCenterOrderStates(StatesGroup):
    new_order_phone = State()
    new_client_name = State()
    new_client_address = State()
    select_service_type = State()
    order_description = State()
    order_priority = State()
    create_order = State()
    order_address = State()
    order_phone = State()
    order_confirm = State()
    order_details = State()
    order_status_update = State()
    
    # Enhanced workflow states
    workflow_request_created = State()
    client_details_capture = State()
    issue_description_capture = State()
    workflow_type_selection = State()
    main_menu = State()

class CallCenterClientStates(StatesGroup):
    customer_search = State()
    customer_details = State()
    customer_orders = State()
    client_details = State()
    client_history = State()
    client_orders = State()
    client_feedback = State()
    client_search = State()

class CallCenterCallStates(StatesGroup):
    logging_call = State()
    call_duration = State()
    call_notes = State()
    active_call = State()
    call_completion = State()

class CallCenterFeedbackStates(StatesGroup):
    waiting_feedback = State()
    feedback_comment = State()

class CallCenterChatStates(StatesGroup):
    in_chat = State()
    chat_file_upload = State()
    chat_closing = State()
    client_chat = State()
    client_chat_file = State()
    client_chat_closing = State()
    client_chat_closing_confirm = State()

class CallCenterReportsStates(StatesGroup):
    reports_menu = State()
    conversion_report = State()
    calls_report = State()
    viewing_statistics = State()
    statistics = State()

class CallCenterSettingsStates(StatesGroup):
    settings_menu = State()
    language_change = State()
    notifications_settings = State()
    selecting_language = State()
class CallCenterSupervisorStates(StatesGroup):
    main_menu = State()
    assign_requests = State()
    pending_assignments = State()
    operator_selection = State()
    team_performance = State()

class CallCenterDirectResolutionStates(StatesGroup):
    awaiting_assignment = State()
    operator_working = State()
    resolution_notes = State()
    completed = State()
    client_rating = State()