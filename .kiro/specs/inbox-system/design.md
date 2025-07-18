# Design Document

## Overview

The inbox system is designed to provide a centralized application management interface for all user roles (except client and admin). The system enables role-based viewing, processing, and transferring of applications while maintaining proper ownership tracking and bilingual support. The design leverages the existing database structure and extends it with proper role assignment tracking.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Interface │    │  Business Logic │    │    Database     │
│                 │    │                 │    │                 │
│ - Inbox Handlers│◄──►│ - Inbox Service │◄──►│ - Applications  │
│ - Role Keyboards│    │ - Transfer Logic│    │ - Role Tracking │
│ - Localization  │    │ - Notification  │    │ - Audit Logs    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Interaction Flow

1. **User Request**: User clicks "📥 Inbox" button
2. **Role Detection**: System identifies user's role from database
3. **Application Filtering**: Query applications assigned to user's role
4. **Localization**: Apply language-specific formatting
5. **UI Generation**: Create role-specific keyboard and message
6. **Transfer Handling**: Process application transfers between roles
7. **Database Update**: Update role ownership atomically

## Components and Interfaces

### 1. Database Schema Extensions

#### Applications Table Modification
```sql
-- Add role tracking column to existing tables
ALTER TABLE zayavki ADD COLUMN assigned_role VARCHAR(50);
ALTER TABLE service_requests ADD COLUMN role_current VARCHAR(50);

-- Create index for efficient role-based queries
CREATE INDEX idx_zayavki_assigned_role ON zayavki(assigned_role);
CREATE INDEX idx_service_requests_role_current ON service_requests(role_current);
```

#### Inbox Messages Table (New)
```sql
CREATE TABLE inbox_messages (
    id SERIAL PRIMARY KEY,
    application_id VARCHAR(255) NOT NULL,
    application_type VARCHAR(50) NOT NULL, -- 'zayavka', 'service_request'
    assigned_role VARCHAR(50) NOT NULL,
    message_type VARCHAR(50) DEFAULT 'application',
    title VARCHAR(255),
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_inbox_application_type CHECK (application_type IN ('zayavka', 'service_request')),
    CONSTRAINT fk_inbox_assigned_role CHECK (assigned_role IN ('manager', 'junior_manager', 'technician', 'warehouse', 'call_center', 'call_center_supervisor', 'controller'))
);

CREATE INDEX idx_inbox_messages_role ON inbox_messages(assigned_role, is_read);
CREATE INDEX idx_inbox_messages_created ON inbox_messages(created_at DESC);
```

### 2. Core Service Classes

#### InboxService
```python
class InboxService:
    async def get_role_applications(self, role: str, user_id: int) -> List[Dict]
    async def transfer_application(self, app_id: str, from_role: str, to_role: str, user_id: int) -> bool
    async def create_inbox_message(self, app_id: str, app_type: str, role: str, title: str, description: str) -> bool
    async def mark_as_read(self, message_id: int, user_id: int) -> bool
    async def get_transfer_options(self, current_role: str) -> List[str]
```

#### ApplicationTransferService
```python
class ApplicationTransferService:
    async def validate_transfer(self, app_id: str, from_role: str, to_role: str) -> bool
    async def execute_transfer(self, app_id: str, from_role: str, to_role: str, user_id: int) -> Dict
    async def notify_target_role(self, app_id: str, to_role: str) -> bool
    async def log_transfer(self, app_id: str, from_role: str, to_role: str, user_id: int) -> bool
```

### 3. Handler Architecture

#### Universal Inbox Handler
```python
# handlers/inbox_handler.py
class InboxHandler:
    def __init__(self):
        self.inbox_service = InboxService()
        self.transfer_service = ApplicationTransferService()
    
    async def show_inbox(self, message: Message, state: FSMContext)
    async def handle_application_selection(self, callback: CallbackQuery)
    async def handle_transfer_request(self, callback: CallbackQuery)
    async def handle_mark_as_read(self, callback: CallbackQuery)
```

### 4. Keyboard Generation

#### Role-Specific Keyboards
```python
# keyboards/inbox_keyboards.py
def get_inbox_main_keyboard(applications: List[Dict], lang: str) -> InlineKeyboardMarkup
def get_application_actions_keyboard(app_id: str, current_role: str, lang: str) -> InlineKeyboardMarkup
def get_transfer_options_keyboard(app_id: str, available_roles: List[str], lang: str) -> InlineKeyboardMarkup
def get_inbox_navigation_keyboard(page: int, total_pages: int, lang: str) -> InlineKeyboardMarkup
```

## Data Models

### InboxMessage Model
```python
@dataclass
class InboxMessage:
    id: Optional[int] = None
    application_id: str = None
    application_type: str = None  # 'zayavka', 'service_request'
    assigned_role: str = None
    message_type: str = 'application'
    title: Optional[str] = None
    description: Optional[str] = None
    priority: str = 'medium'
    is_read: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### ApplicationTransfer Model
```python
@dataclass
class ApplicationTransfer:
    id: Optional[int] = None
    application_id: str = None
    application_type: str = None
    from_role: str = None
    to_role: str = None
    transferred_by: int = None
    transfer_reason: Optional[str] = None
    created_at: Optional[datetime] = None
```

## Error Handling

### Transfer Validation
- **Role Validation**: Ensure source and target roles are valid
- **Application Existence**: Verify application exists and is accessible
- **Permission Check**: Confirm user has permission to transfer
- **Workflow Validation**: Ensure transfer follows business rules

### Database Consistency
- **Atomic Operations**: Use database transactions for transfers
- **Rollback Mechanism**: Implement rollback on transfer failures
- **Duplicate Prevention**: Prevent applications from existing in multiple roles
- **Audit Trail**: Log all transfer operations for debugging

### Error Response Handling
```python
class InboxError(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code

# Error codes
ERRORS = {
    'INVALID_ROLE': 'Invalid role specified',
    'APPLICATION_NOT_FOUND': 'Application not found',
    'TRANSFER_NOT_ALLOWED': 'Transfer not allowed for this workflow',
    'DATABASE_ERROR': 'Database operation failed',
    'PERMISSION_DENIED': 'User does not have permission'
}
```

## Testing Strategy

### Unit Tests
- **Service Layer Tests**: Test InboxService and ApplicationTransferService methods
- **Database Query Tests**: Verify correct filtering and updates
- **Validation Tests**: Test transfer validation logic
- **Localization Tests**: Verify correct text rendering in both languages

### Integration Tests
- **End-to-End Workflow**: Test complete application transfer flow
- **Role-Based Access**: Verify role-specific application visibility
- **Database Consistency**: Test atomic operations and rollbacks
- **Notification Integration**: Test notification system integration

### Test Data Setup
```python
# Test fixtures for different scenarios
@pytest.fixture
async def sample_applications():
    return [
        {
            'id': 'app_001',
            'type': 'zayavka',
            'assigned_role': 'manager',
            'status': 'new',
            'client_name': 'Test Client',
            'description': 'Test application'
        }
    ]

@pytest.fixture
async def role_transfer_scenarios():
    return [
        ('manager', 'junior_manager'),
        ('junior_manager', 'technician'),
        ('controller', 'technician'),
        ('technician', 'warehouse')
    ]
```

## Localization Strategy

### Text Management
```python
# utils/inbox_localization.py
INBOX_TEXTS = {
    'uz': {
        'inbox_title': '📥 Inbox',
        'new_applications': '🆕 Yangi arizalar: {}',
        'no_applications': '📭 Hech qanday ariza yo\'q',
        'transfer_success': '✅ Ariza muvaffaqiyatli o\'tkazildi',
        'transfer_failed': '❌ Arizani o\'tkazishda xatolik',
        'application_details': '📋 Ariza tafsilotlari',
        'transfer_to': '📤 Quyidagiga o\'tkazish:',
        'mark_as_read': '✅ O\'qilgan deb belgilash'
    },
    'ru': {
        'inbox_title': '📥 Inbox',
        'new_applications': '🆕 Новые заявки: {}',
        'no_applications': '📭 Нет заявок',
        'transfer_success': '✅ Заявка успешно передана',
        'transfer_failed': '❌ Ошибка при передаче заявки',
        'application_details': '📋 Детали заявки',
        'transfer_to': '📤 Передать в:',
        'mark_as_read': '✅ Отметить как прочитанное'
    }
}
```

### Dynamic Text Generation
```python
def get_inbox_text(key: str, lang: str, *args) -> str:
    text = INBOX_TEXTS.get(lang, INBOX_TEXTS['uz']).get(key, key)
    return text.format(*args) if args else text
```

## Performance Considerations

### Database Optimization
- **Indexed Queries**: Use indexes on role and timestamp columns
- **Pagination**: Implement pagination for large application lists
- **Query Optimization**: Use efficient JOIN operations for application details
- **Connection Pooling**: Leverage existing connection pool

### Caching Strategy
- **Role-Based Caching**: Cache application counts per role
- **Localization Caching**: Cache translated texts
- **Application Metadata**: Cache frequently accessed application details

### Memory Management
- **Lazy Loading**: Load application details on demand
- **Batch Processing**: Process transfers in batches for bulk operations
- **Resource Cleanup**: Properly dispose of database connections

## Security Considerations

### Access Control
- **Role-Based Access**: Users can only see applications assigned to their role
- **Transfer Permissions**: Validate user permissions before transfers
- **Audit Logging**: Log all access and transfer operations

### Data Protection
- **Input Validation**: Sanitize all user inputs
- **SQL Injection Prevention**: Use parameterized queries
- **XSS Prevention**: Escape output in message formatting

### Authentication Integration
```python
async def verify_role_access(user_id: int, role: str) -> bool:
    user = await get_user_by_telegram_id(user_id)
    return user and user['role'] == role and user['is_active']
```