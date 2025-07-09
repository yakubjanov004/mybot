from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    # Main menu states
    main_menu = State()
    
    # User management states
    user_management = State()
    adding_user = State()
    editing_user = State()
    user_roles = State()
    
    # Order management states
    filtering = State()
    filtering_selected = State()
    
    # System management states
    system_menu = State()
    system_stats = State()
    system_logs = State()
    system_backup = State()
    system_maintenance = State()
    
    # Database management states
    database_menu = State()
    database_backup = State()
    database_restore = State()
    database_cleanup = State()
    
    # Settings states
    settings_menu = State()
    bot_settings = State()
    language_settings = State()
    notification_settings = State()
    security_settings = State()
    
    # Reports states
    reports_menu = State()
    system_report = State()
    user_activity_report = State()
    performance_report = State()
    error_report = State()
    
    # Monitoring states
    monitoring_menu = State()
    real_time_monitoring = State()
    performance_monitoring = State()
    error_monitoring = State()
    
    # Broadcast states
    broadcast_menu = State()
    broadcast_message = State()
    broadcast_recipients = State()
    broadcast_confirm = State()
    
    # Maintenance states
    maintenance_menu = State()
    scheduled_maintenance = State()
    emergency_maintenance = State()
    maintenance_notification = State()
    
    # System settings
    system_settings = State()
    database_management = State()
    backup_restore = State()
    
    # Analytics and reports
    analytics_menu = State()
    system_analytics = State()
    user_analytics = State()
    performance_reports = State()
    
    # Configuration
    bot_configuration = State()
    feature_toggles = State()
    maintenance_mode = State()
    
    # Security
    security_settings = State()
    access_control = State()
    audit_logs = State()
    
    # Notifications
    system_notifications = State()
    broadcast_messages = State()
    
    # Integration management
    integration_settings = State()
    api_management = State()
    
    # Language and localization
    language_management = State()
    content_management = State()
    
    # Backup and recovery
    backup_settings = State()
    recovery_options = State()
    
    # System health
    health_checks = State()
    diagnostic_tools = State()
    
    # Update management
    system_updates = State()
    feature_updates = State()

    waiting_for_user_id_or_username = State()
    waiting_for_telegram_id = State()
    waiting_for_phone = State()
    waiting_for_role_selection = State()
    waiting_for_search_value = State()
    waiting_for_order_id = State()
    editing_setting = State()
    waiting_for_setting_value = State()

    settings = State()
    orders = State()
    change_role = State()
    blocking = State()
    change_language = State()
    waiting_for_search_method = State()
    waiting_for_role_change_id = State()
    waiting_for_role_change_phone = State()