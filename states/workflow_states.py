"""
Workflow System FSM States
Defines state classes for workflow operations across all roles
"""

from aiogram.fsm.state import State, StatesGroup


class WorkflowRequestStates(StatesGroup):
    """States for creating workflow requests"""
    selecting_type = State()
    entering_description = State()
    entering_location = State()
    entering_contact_info = State()
    selecting_priority = State()
    confirming_request = State()


class ConnectionWorkflowStates(StatesGroup):
    """States for connection request workflow"""
    # Client states
    selecting_connection_type = State()
    selecting_tariff = State()
    entering_address = State()
    entering_contact_details = State()
    confirming_connection_request = State()
    
    # Manager states
    reviewing_connection_request = State()
    selecting_junior_manager = State()
    
    # Junior Manager states
    calling_client = State()
    entering_call_notes = State()
    adding_comments = State()
    forwarding_to_controller = State()
    
    # Controller states
    reviewing_controller_assignment = State()
    selecting_technician = State()
    
    # Technician states
    starting_installation = State()
    documenting_equipment = State()
    entering_installation_notes = State()
    selecting_equipment_used = State()
    
    # Warehouse states
    reviewing_equipment_documentation = State()
    updating_inventory = State()
    confirming_inventory_update = State()
    closing_connection_request = State()


class TechnicalServiceStates(StatesGroup):
    """States for technical service workflow"""
    # Client states
    selecting_issue_type = State()
    describing_technical_issue = State()
    confirming_technical_request = State()
    
    # Controller states
    reviewing_technical_request = State()
    selecting_technician_for_technical = State()
    
    # Technician states
    starting_diagnostics = State()
    entering_diagnostics_notes = State()
    deciding_warehouse_involvement = State()
    resolving_without_warehouse = State()
    entering_resolution_notes = State()
    requesting_warehouse_support = State()
    documenting_required_equipment = State()
    completing_technical_service = State()
    
    # Warehouse states
    reviewing_equipment_request = State()
    preparing_equipment = State()
    confirming_equipment_ready = State()
    adding_warehouse_comments = State()


class CallCenterWorkflowStates(StatesGroup):
    """States for call center workflow"""
    # Call Center states
    creating_client_request = State()
    entering_client_details = State()
    entering_issue_description = State()
    selecting_request_type = State()
    
    # Call Center Direct Resolution states
    creating_direct_resolution = State()
    
    # Call Center Supervisor states
    reviewing_direct_resolution = State()
    selecting_call_center_operator = State()
    
    # Call Center Operator states
    resolving_remotely = State()
    entering_resolution_details = State()
    confirming_remote_resolution = State()


class WorkflowManagementStates(StatesGroup):
    """States for workflow management operations"""
    viewing_requests = State()
    filtering_requests = State()
    searching_requests = State()
    viewing_request_details = State()
    viewing_request_history = State()
    adding_comments = State()
    entering_comment_text = State()
    updating_request_status = State()
    assigning_request = State()
    selecting_assignee = State()


class InventoryWorkflowStates(StatesGroup):
    """States for inventory-related workflow operations"""
    selecting_materials = State()
    entering_quantity = State()
    confirming_material_usage = State()
    updating_stock_levels = State()
    reviewing_inventory_transaction = State()
    entering_transaction_notes = State()


class NotificationStates(StatesGroup):
    """States for notification handling"""
    viewing_notifications = State()
    handling_notification = State()
    marking_notification_handled = State()


class WorkflowReportingStates(StatesGroup):
    """States for workflow reporting and statistics"""
    selecting_report_type = State()
    selecting_date_range = State()
    viewing_statistics = State()
    exporting_report = State()


class WorkflowAdminStates(StatesGroup):
    """States for workflow administration"""
    managing_workflows = State()
    viewing_system_status = State()
    configuring_workflow_settings = State()
    managing_user_assignments = State()
    viewing_audit_logs = State()


class RatingStates(StatesGroup):
    """States for service rating"""
    selecting_rating = State()
    entering_feedback_comment = State()
    confirming_rating = State()


class WorkflowErrorStates(StatesGroup):
    """States for error handling in workflows"""
    handling_workflow_error = State()
    recovering_from_error = State()
    reporting_error = State()


# State groups mapping for easy access
WORKFLOW_STATE_GROUPS = {
    'request': WorkflowRequestStates,
    'connection': ConnectionWorkflowStates,
    'technical': TechnicalServiceStates,
    'call_center': CallCenterWorkflowStates,
    'management': WorkflowManagementStates,
    'inventory': InventoryWorkflowStates,
    'notifications': NotificationStates,
    'reporting': WorkflowReportingStates,
    'admin': WorkflowAdminStates,
    'rating': RatingStates,
    'error': WorkflowErrorStates
}


def get_state_group(group_name: str):
    """Get state group by name"""
    return WORKFLOW_STATE_GROUPS.get(group_name)


def get_all_workflow_states():
    """Get all workflow states for registration"""
    return list(WORKFLOW_STATE_GROUPS.values())


# Helper functions for state management
def is_workflow_state(state):
    """Check if a state belongs to workflow system"""
    if not state:
        return False
    
    state_name = str(state)
    workflow_prefixes = [
        'WorkflowRequestStates',
        'ConnectionWorkflowStates', 
        'TechnicalServiceStates',
        'CallCenterWorkflowStates',
        'WorkflowManagementStates',
        'InventoryWorkflowStates',
        'NotificationStates',
        'WorkflowReportingStates',
        'WorkflowAdminStates',
        'RatingStates',
        'WorkflowErrorStates'
    ]
    
    return any(prefix in state_name for prefix in workflow_prefixes)


def get_state_description(state, lang: str = 'ru'):
    """Get human-readable description of state"""
    descriptions = {
        'ru': {
            'selecting_type': 'Выбор типа запроса',
            'entering_description': 'Ввод описания',
            'entering_location': 'Ввод местоположения',
            'selecting_priority': 'Выбор приоритета',
            'confirming_request': 'Подтверждение запроса',
            'reviewing_connection_request': 'Рассмотрение запроса подключения',
            'selecting_junior_manager': 'Выбор младшего менеджера',
            'calling_client': 'Звонок клиенту',
            'entering_call_notes': 'Ввод заметок звонка',
            'forwarding_to_controller': 'Пересылка контролеру',
            'selecting_technician': 'Выбор техника',
            'starting_installation': 'Начало установки',
            'documenting_equipment': 'Документирование оборудования',
            'updating_inventory': 'Обновление инвентаря',
            'starting_diagnostics': 'Начало диагностики',
            'deciding_warehouse_involvement': 'Решение об участии склада',
            'resolving_without_warehouse': 'Решение без склада',
            'preparing_equipment': 'Подготовка оборудования',
            'resolving_remotely': 'Удаленное решение',
            'selecting_rating': 'Выбор оценки',
            'entering_feedback_comment': 'Ввод комментария'
        },
        'uz': {
            'selecting_type': "So'rov turini tanlash",
            'entering_description': 'Tavsif kiritish',
            'entering_location': 'Joylashuvni kiritish',
            'selecting_priority': 'Muhimlikni tanlash',
            'confirming_request': "So'rovni tasdiqlash",
            'reviewing_connection_request': "Ulanish so'rovini ko'rib chiqish",
            'selecting_junior_manager': 'Kichik menejer tanlash',
            'calling_client': "Mijozga qo'ng'iroq qilish",
            'entering_call_notes': "Qo'ng'iroq eslatmalarini kiritish",
            'forwarding_to_controller': 'Nazoratchiga yuborish',
            'selecting_technician': 'Texnik tanlash',
            'starting_installation': "O'rnatishni boshlash",
            'documenting_equipment': 'Jihozlarni hujjatlash',
            'updating_inventory': 'Inventarni yangilash',
            'starting_diagnostics': 'Diagnostikani boshlash',
            'deciding_warehouse_involvement': 'Ombor ishtirokini hal qilish',
            'resolving_without_warehouse': 'Omborsiz hal qilish',
            'preparing_equipment': 'Jihozlarni tayyorlash',
            'resolving_remotely': 'Masofadan hal qilish',
            'selecting_rating': 'Baholashni tanlash',
            'entering_feedback_comment': 'Izoh kiritish'
        }
    }
    
    if not state:
        return 'Unknown state'
    
    state_name = str(state).split('.')[-1] if '.' in str(state) else str(state)
    return descriptions.get(lang, {}).get(state_name, state_name)


# State transition helpers
class StateTransitionHelper:
    """Helper class for managing state transitions in workflows"""
    
    @staticmethod
    def get_next_state(current_state, action: str):
        """Get next state based on current state and action"""
        # Define state transition mappings
        transitions = {
            # Connection workflow transitions
            'selecting_connection_type': {
                'type_selected': 'selecting_tariff'
            },
            'selecting_tariff': {
                'tariff_selected': 'entering_address'
            },
            'entering_address': {
                'address_entered': 'entering_contact_details'
            },
            'entering_contact_details': {
                'contact_entered': 'confirming_connection_request'
            },
            
            # Technical service transitions
            'selecting_issue_type': {
                'issue_selected': 'describing_technical_issue'
            },
            'describing_technical_issue': {
                'description_entered': 'confirming_technical_request'
            },
            
            # Management transitions
            'reviewing_connection_request': {
                'assign_junior': 'selecting_junior_manager'
            },
            'selecting_junior_manager': {
                'junior_selected': None  # End state for this role
            }
        }
        
        current_state_name = str(current_state).split('.')[-1] if '.' in str(current_state) else str(current_state)
        return transitions.get(current_state_name, {}).get(action)
    
    @staticmethod
    def is_final_state(state):
        """Check if state is a final state in workflow"""
        final_states = [
            'confirming_request',
            'closing_connection_request',
            'completing_technical_service',
            'confirming_remote_resolution',
            'confirming_rating'
        ]
        
        state_name = str(state).split('.')[-1] if '.' in str(state) else str(state)
        return state_name in final_states