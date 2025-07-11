from aiogram.fsm.state import State, StatesGroup

class AdminMainMenuStates(StatesGroup):
    main_menu = State()

class AdminUserStates(StatesGroup):
    user_management = State()
    adding_user = State()
    editing_user = State()
    user_roles = State()
    blocking = State()
    waiting_for_user_id_or_username = State()
    waiting_for_telegram_id = State()
    waiting_for_phone = State()
    waiting_for_role_selection = State()
    waiting_for_search_value = State()
    waiting_for_search_method = State()
    waiting_for_role_change_id = State()
    waiting_for_role_change_phone = State()

class AdminOrderStates(StatesGroup):
    filtering = State()
    filtering_selected = State()
    waiting_for_order_id = State()
    orders = State()

class AdminSettingsStates(StatesGroup):
    settings_menu = State()
    bot_settings = State()
    language_settings = State()
    notification_settings = State()
    security_settings = State()
    editing_setting = State()
    waiting_for_setting_value = State()
    settings = State()

class AdminStatisticsStates(StatesGroup):
    statistics_menu = State()
    system_stats = State()
    analytics_menu = State()
    system_analytics = State()
    user_analytics = State()
    performance_reports = State()

class AdminLanguageStates(StatesGroup):
    change_language = State()
    language_management = State()
    content_management = State()

class AdminCallbackStates(StatesGroup):
    waiting_for_search_value = State()