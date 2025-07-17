"""
Staff Application Creation FSM States
Defines state classes for staff members creating applications on behalf of clients
"""

from aiogram.fsm.state import State, StatesGroup
from typing import Dict, List, Optional, Any
from enum import Enum


class StaffApplicationStates(StatesGroup):
    """Main state group for staff application creation workflow"""
    
    # Initial states
    selecting_application_type = State()
    
    # Client selection and validation states
    selecting_client_search_method = State()
    entering_client_phone = State()
    entering_client_name = State()
    entering_client_id = State()
    searching_client = State()
    selecting_client_from_results = State()
    confirming_client_selection = State()
    
    # New client creation states
    creating_new_client = State()
    entering_new_client_name = State()
    entering_new_client_phone = State()
    entering_new_client_address = State()
    confirming_new_client = State()
    
    # Application form states
    entering_application_description = State()
    entering_application_address = State()
    selecting_connection_type = State()  # For connection requests
    selecting_tariff = State()  # For connection requests
    selecting_issue_type = State()  # For technical service
    asking_for_media = State()
    waiting_for_media = State()
    asking_for_location = State()
    waiting_for_location = State()
    
    # Confirmation and submission states
    reviewing_application_details = State()
    confirming_application_submission = State()
    processing_submission = State()
    application_submitted = State()
    
    # Error handling states
    handling_validation_error = State()
    handling_permission_error = State()
    handling_submission_error = State()


class ClientSearchStates(StatesGroup):
    """States specifically for client search and selection"""
    
    selecting_search_method = State()
    entering_search_criteria = State()
    displaying_search_results = State()
    selecting_client = State()
    confirming_client = State()
    creating_new_client = State()


class ApplicationFormStates(StatesGroup):
    """States for filling application forms"""
    
    # Common form states
    entering_description = State()
    entering_address = State()
    adding_media = State()
    adding_location = State()
    
    # Connection-specific states
    selecting_connection_type = State()
    selecting_tariff = State()
    entering_connection_details = State()
    
    # Technical service specific states
    selecting_issue_category = State()
    describing_technical_issue = State()
    selecting_urgency_level = State()
    
    # Form validation and confirmation
    validating_form = State()
    confirming_form = State()


class StaffApplicationValidationStates(StatesGroup):
    """States for validation and error handling"""
    
    validating_permissions = State()
    validating_client_data = State()
    validating_application_data = State()
    handling_validation_errors = State()
    retrying_validation = State()


# Enums for state management
class ClientSearchMethod(Enum):
    """Methods for searching clients"""
    PHONE = "phone"
    NAME = "name"
    ID = "client_id"
    NEW = "new_client"


class ApplicationType(Enum):
    """Types of applications staff can create"""
    CONNECTION = "connection_request"
    TECHNICAL = "technical_service"


class ValidationErrorType(Enum):
    """Types of validation errors"""
    PERMISSION_DENIED = "permission_denied"
    CLIENT_NOT_FOUND = "client_not_found"
    INVALID_CLIENT_DATA = "invalid_client_data"
    INVALID_APPLICATION_DATA = "invalid_application_data"
    SUBMISSION_FAILED = "submission_failed"


# State transition mappings
STAFF_APPLICATION_STATE_TRANSITIONS = {
    # Initial flow
    'selecting_application_type': {
        'connection_selected': 'selecting_client_search_method',
        'technical_selected': 'selecting_client_search_method',
        'permission_denied': 'handling_permission_error'
    },
    
    # Client search flow
    'selecting_client_search_method': {
        'phone_search': 'entering_client_phone',
        'name_search': 'entering_client_name',
        'id_search': 'entering_client_id',
        'new_client': 'creating_new_client'
    },
    
    'entering_client_phone': {
        'phone_entered': 'searching_client',
        'invalid_phone': 'entering_client_phone'
    },
    
    'entering_client_name': {
        'name_entered': 'searching_client',
        'invalid_name': 'entering_client_name'
    },
    
    'entering_client_id': {
        'id_entered': 'searching_client',
        'invalid_id': 'entering_client_id'
    },
    
    'searching_client': {
        'client_found': 'confirming_client_selection',
        'multiple_found': 'selecting_client_from_results',
        'not_found': 'creating_new_client',
        'search_error': 'selecting_client_search_method'
    },
    
    'selecting_client_from_results': {
        'client_selected': 'confirming_client_selection',
        'create_new': 'creating_new_client',
        'search_again': 'selecting_client_search_method'
    },
    
    'confirming_client_selection': {
        'confirmed': 'entering_application_description',
        'rejected': 'selecting_client_search_method'
    },
    
    # New client creation flow
    'creating_new_client': {
        'start_creation': 'entering_new_client_name'
    },
    
    'entering_new_client_name': {
        'name_entered': 'entering_new_client_phone',
        'invalid_name': 'entering_new_client_name'
    },
    
    'entering_new_client_phone': {
        'phone_entered': 'entering_new_client_address',
        'invalid_phone': 'entering_new_client_phone'
    },
    
    'entering_new_client_address': {
        'address_entered': 'confirming_new_client',
        'skip_address': 'confirming_new_client'
    },
    
    'confirming_new_client': {
        'confirmed': 'entering_application_description',
        'edit': 'entering_new_client_name',
        'cancel': 'selecting_client_search_method'
    },
    
    # Application form flow
    'entering_application_description': {
        'description_entered': 'entering_application_address',
        'invalid_description': 'entering_application_description'
    },
    
    'entering_application_address': {
        'address_entered': 'selecting_connection_type',  # For connection
        'address_entered_technical': 'selecting_issue_type',  # For technical
        'invalid_address': 'entering_application_address'
    },
    
    # Connection-specific flow
    'selecting_connection_type': {
        'type_selected': 'selecting_tariff'
    },
    
    'selecting_tariff': {
        'tariff_selected': 'asking_for_media'
    },
    
    # Technical service specific flow
    'selecting_issue_type': {
        'issue_selected': 'asking_for_media'
    },
    
    # Media and location flow
    'asking_for_media': {
        'add_media': 'waiting_for_media',
        'skip_media': 'asking_for_location'
    },
    
    'waiting_for_media': {
        'media_received': 'asking_for_location',
        'skip_media': 'asking_for_location',
        'invalid_media': 'waiting_for_media'
    },
    
    'asking_for_location': {
        'add_location': 'waiting_for_location',
        'skip_location': 'reviewing_application_details'
    },
    
    'waiting_for_location': {
        'location_received': 'reviewing_application_details',
        'skip_location': 'reviewing_application_details',
        'invalid_location': 'waiting_for_location'
    },
    
    # Final confirmation flow
    'reviewing_application_details': {
        'confirm': 'confirming_application_submission',
        'edit_description': 'entering_application_description',
        'edit_address': 'entering_application_address',
        'edit_client': 'selecting_client_search_method'
    },
    
    'confirming_application_submission': {
        'submit': 'processing_submission',
        'cancel': 'reviewing_application_details'
    },
    
    'processing_submission': {
        'success': 'application_submitted',
        'validation_error': 'handling_validation_error',
        'submission_error': 'handling_submission_error'
    },
    
    # Error handling flows
    'handling_validation_error': {
        'retry': 'reviewing_application_details',
        'edit': 'entering_application_description',
        'cancel': 'selecting_application_type'
    },
    
    'handling_permission_error': {
        'acknowledged': 'selecting_application_type'
    },
    
    'handling_submission_error': {
        'retry': 'processing_submission',
        'edit': 'reviewing_application_details',
        'cancel': 'selecting_application_type'
    },
    
    # Final state
    'application_submitted': {
        'create_another': 'selecting_application_type',
        'finish': None  # End of flow
    }
}


# Helper functions for state management
class StaffApplicationStateManager:
    """Helper class for managing staff application states and transitions"""
    
    @staticmethod
    def get_next_state(current_state: State, action: str, application_type: str = None) -> Optional[State]:
        """
        Get the next state based on current state and action
        
        Args:
            current_state: Current FSM state
            action: Action taken by user
            application_type: Type of application (connection/technical)
            
        Returns:
            Next state or None if end of flow
        """
        if not current_state:
            return None
            
        # Extract state name from the state object
        if hasattr(current_state, 'state'):
            state_name = current_state.state.split(':')[-1]
        else:
            state_name = str(current_state).split('.')[-1]
        
        transitions = STAFF_APPLICATION_STATE_TRANSITIONS.get(state_name, {})
        
        # Handle application-type specific transitions
        if state_name == 'entering_application_address' and action == 'address_entered':
            if application_type == ApplicationType.CONNECTION.value:
                return StaffApplicationStates.selecting_connection_type
            elif application_type == ApplicationType.TECHNICAL.value:
                return StaffApplicationStates.selecting_issue_type
        
        next_state_name = transitions.get(action)
        if not next_state_name:
            return None
            
        # Convert state name to actual state
        return getattr(StaffApplicationStates, next_state_name, None)
    
    @staticmethod
    def is_client_selection_state(state: State) -> bool:
        """Check if current state is part of client selection flow"""
        client_selection_states = [
            'selecting_client_search_method',
            'entering_client_phone',
            'entering_client_name', 
            'entering_client_id',
            'searching_client',
            'selecting_client_from_results',
            'confirming_client_selection',
            'creating_new_client',
            'entering_new_client_name',
            'entering_new_client_phone',
            'entering_new_client_address',
            'confirming_new_client'
        ]
        
        if not state:
            return False
            
        # Extract state name from the state object
        if hasattr(state, 'state'):
            state_name = state.state.split(':')[-1]
        else:
            state_name = str(state).split('.')[-1]
        return state_name in client_selection_states
    
    @staticmethod
    def is_application_form_state(state: State) -> bool:
        """Check if current state is part of application form filling"""
        form_states = [
            'entering_application_description',
            'entering_application_address',
            'selecting_connection_type',
            'selecting_tariff',
            'selecting_issue_type',
            'asking_for_media',
            'waiting_for_media',
            'asking_for_location',
            'waiting_for_location'
        ]
        
        if not state:
            return False
            
        # Extract state name from the state object
        if hasattr(state, 'state'):
            state_name = state.state.split(':')[-1]
        else:
            state_name = str(state).split('.')[-1]
        return state_name in form_states
    
    @staticmethod
    def is_confirmation_state(state: State) -> bool:
        """Check if current state is part of confirmation flow"""
        confirmation_states = [
            'reviewing_application_details',
            'confirming_application_submission',
            'processing_submission',
            'application_submitted'
        ]
        
        if not state:
            return False
            
        # Extract state name from the state object
        if hasattr(state, 'state'):
            state_name = state.state.split(':')[-1]
        else:
            state_name = str(state).split('.')[-1]
        return state_name in confirmation_states
    
    @staticmethod
    def is_error_state(state: State) -> bool:
        """Check if current state is an error handling state"""
        error_states = [
            'handling_validation_error',
            'handling_permission_error',
            'handling_submission_error'
        ]
        
        if not state:
            return False
            
        # Extract state name from the state object
        if hasattr(state, 'state'):
            state_name = state.state.split(':')[-1]
        else:
            state_name = str(state).split('.')[-1]
        return state_name in error_states
    
    @staticmethod
    def get_state_description(state: State, lang: str = 'uz') -> str:
        """Get human-readable description of state"""
        descriptions = {
            'uz': {
                'selecting_application_type': "Ariza turini tanlash",
                'selecting_client_search_method': "Mijozni qidirish usulini tanlash",
                'entering_client_phone': "Mijoz telefon raqamini kiritish",
                'entering_client_name': "Mijoz ismini kiritish",
                'entering_client_id': "Mijoz ID raqamini kiritish",
                'searching_client': "Mijozni qidirish",
                'selecting_client_from_results': "Qidiruv natijalaridan mijozni tanlash",
                'confirming_client_selection': "Mijoz tanlovini tasdiqlash",
                'creating_new_client': "Yangi mijoz yaratish",
                'entering_new_client_name': "Yangi mijoz ismini kiritish",
                'entering_new_client_phone': "Yangi mijoz telefon raqamini kiritish",
                'entering_new_client_address': "Yangi mijoz manzilini kiritish",
                'confirming_new_client': "Yangi mijozni tasdiqlash",
                'entering_application_description': "Ariza tavsifini kiritish",
                'entering_application_address': "Ariza manzilini kiritish",
                'selecting_connection_type': "Ulanish turini tanlash",
                'selecting_tariff': "Tarifni tanlash",
                'selecting_issue_type': "Muammo turini tanlash",
                'asking_for_media': "Media fayllarini qo'shish",
                'waiting_for_media': "Media fayllarini kutish",
                'asking_for_location': "Joylashuvni qo'shish",
                'waiting_for_location': "Joylashuvni kutish",
                'reviewing_application_details': "Ariza tafsilotlarini ko'rib chiqish",
                'confirming_application_submission': "Ariza yuborishni tasdiqlash",
                'processing_submission': "Arizani qayta ishlash",
                'application_submitted': "Ariza yuborildi",
                'handling_validation_error': "Tekshirish xatosini hal qilish",
                'handling_permission_error': "Ruxsat xatosini hal qilish",
                'handling_submission_error': "Yuborish xatosini hal qilish"
            },
            'ru': {
                'selecting_application_type': "Выбор типа заявки",
                'selecting_client_search_method': "Выбор способа поиска клиента",
                'entering_client_phone': "Ввод номера телефона клиента",
                'entering_client_name': "Ввод имени клиента",
                'entering_client_id': "Ввод ID клиента",
                'searching_client': "Поиск клиента",
                'selecting_client_from_results': "Выбор клиента из результатов поиска",
                'confirming_client_selection': "Подтверждение выбора клиента",
                'creating_new_client': "Создание нового клиента",
                'entering_new_client_name': "Ввод имени нового клиента",
                'entering_new_client_phone': "Ввод телефона нового клиента",
                'entering_new_client_address': "Ввод адреса нового клиента",
                'confirming_new_client': "Подтверждение нового клиента",
                'entering_application_description': "Ввод описания заявки",
                'entering_application_address': "Ввод адреса заявки",
                'selecting_connection_type': "Выбор типа подключения",
                'selecting_tariff': "Выбор тарифа",
                'selecting_issue_type': "Выбор типа проблемы",
                'asking_for_media': "Добавление медиа файлов",
                'waiting_for_media': "Ожидание медиа файлов",
                'asking_for_location': "Добавление местоположения",
                'waiting_for_location': "Ожидание местоположения",
                'reviewing_application_details': "Просмотр деталей заявки",
                'confirming_application_submission': "Подтверждение отправки заявки",
                'processing_submission': "Обработка заявки",
                'application_submitted': "Заявка отправлена",
                'handling_validation_error': "Обработка ошибки валидации",
                'handling_permission_error': "Обработка ошибки доступа",
                'handling_submission_error': "Обработка ошибки отправки"
            }
        }
        
        if not state:
            return 'Unknown state'
            
        # Extract state name from the state object
        if hasattr(state, 'state'):
            state_name = state.state.split(':')[-1]
        else:
            state_name = str(state).split('.')[-1]
        return descriptions.get(lang, {}).get(state_name, state_name)
    
    @staticmethod
    def get_available_actions(state: State, application_type: str = None) -> List[str]:
        """Get list of available actions for current state"""
        if not state:
            return []
            
        # Extract state name from the state object
        if hasattr(state, 'state'):
            state_name = state.state.split(':')[-1]
        else:
            state_name = str(state).split('.')[-1]
        
        transitions = STAFF_APPLICATION_STATE_TRANSITIONS.get(state_name, {})
        
        # Filter actions based on application type if needed
        if state_name == 'selecting_application_type':
            return ['connection_selected', 'technical_selected']
        
        return list(transitions.keys())
    
    @staticmethod
    def validate_state_transition(current_state: State, action: str, context: Dict[str, Any] = None) -> bool:
        """
        Validate if a state transition is allowed
        
        Args:
            current_state: Current FSM state
            action: Proposed action
            context: Additional context for validation
            
        Returns:
            True if transition is valid, False otherwise
        """
        if not current_state:
            return False
            
        available_actions = StaffApplicationStateManager.get_available_actions(current_state)
        return action in available_actions


# Integration with existing state management system
def register_staff_application_states():
    """Register staff application states with the main state management system"""
    return [
        StaffApplicationStates,
        ClientSearchStates,
        ApplicationFormStates,
        StaffApplicationValidationStates
    ]


# Export main classes and functions
__all__ = [
    'StaffApplicationStates',
    'ClientSearchStates', 
    'ApplicationFormStates',
    'StaffApplicationValidationStates',
    'ClientSearchMethod',
    'ApplicationType',
    'ValidationErrorType',
    'StaffApplicationStateManager',
    'STAFF_APPLICATION_STATE_TRANSITIONS',
    'register_staff_application_states'
]