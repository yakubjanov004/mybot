from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    # Registration and setup
    waiting_for_contact = State()
    selecting_language = State()
    
    # Main menu
    main_menu = State()
    
    # Order creation
    selecting_order_type = State()
    entering_description = State()
    entering_address = State()
    asking_for_media = State()
    waiting_for_media = State()
    asking_for_location = State()
    waiting_for_location = State()
    confirming_order = State()
    
    # Profile management
    viewing_profile = State()
    updating_contact = State()
    updating_address = State()
    updating_personal_info = State()
    
    # Order tracking
    viewing_orders = State()
    tracking_order = State()
    order_details = State()
    
    # Support and help
    help_menu = State()
    contacting_support = State()
    creating_support_ticket = State()
    support_ticket_description = State()
    
    # FAQ
    viewing_faq = State()
    faq_category = State()
    
    # Feedback
    providing_feedback = State()
    feedback_rating = State()
    feedback_comment = State()
    
    # Notifications
    notification_settings = State()
    
    # Language settings
    language_settings = State()
    
    # Emergency contact
    emergency_contact = State()
    
    # Service history
    viewing_history = State()
    history_details = State()
    
    # Payment and billing
    viewing_bills = State()
    payment_methods = State()
    
    # Technical support
    technical_support = State()
    tech_issue_description = State()
    
    # Appointment scheduling
    scheduling_appointment = State()
    selecting_time_slot = State()
    confirming_appointment = State()

    waiting_for_phone_number = State()
