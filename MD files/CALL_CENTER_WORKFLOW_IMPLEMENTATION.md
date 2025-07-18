# Call Center Initiated Requests Implementation

## Overview

This document describes the implementation of Call Center Initiated Requests functionality, which allows call center operators to create workflow requests on behalf of clients and route them to the appropriate roles based on the service type.

## Features Implemented

### 1. Call Center Request Creation Interface

- **Phone Number Input**: Call center operators can input client phone numbers
- **Client Management**: Automatic client lookup and creation of new clients if needed
- **Service Type Selection**: Operators can select from different service types with clear workflow routing indicators
- **Issue Description Capture**: Detailed issue description collection for better service quality
- **Priority Setting**: Ability to set request priority (low, medium, high)

### 2. Workflow Routing

The system implements intelligent routing based on service types:

#### Connection Requests → Manager
- **Service Types**: Installation, Setup
- **Workflow Type**: `connection_request`
- **Initial Role**: Manager
- **Flow**: Manager → Junior Manager → Controller → Technician → Warehouse

#### Technical Requests → Controller
- **Service Types**: Repair, Maintenance
- **Workflow Type**: `technical_service`
- **Initial Role**: Controller
- **Flow**: Controller → Technician (with optional Warehouse involvement)

#### Direct Call Center → Call Center Supervisor
- **Service Types**: Consultation
- **Workflow Type**: `call_center_direct`
- **Initial Role**: Call Center Supervisor
- **Flow**: Call Center Supervisor → Call Center Operator

### 3. Client Details Capture

Enhanced client information collection:
- **Contact Information**: Phone, name, address
- **Language Preference**: Uzbek or Russian
- **Service History**: Display of recent orders for existing clients
- **Client Creation**: Automatic creation of new client records

### 4. Issue Description Functionality

Detailed issue capture for better service quality:
- **Detailed Description**: Operators provide comprehensive problem descriptions
- **Issue Classification**: Automatic classification based on service type
- **Context Preservation**: Issue details are preserved throughout the workflow

## Technical Implementation

### Database Schema

The implementation uses the existing workflow infrastructure:

```sql
-- Service Requests table (from migration 016)
CREATE TABLE service_requests (
    id VARCHAR(36) PRIMARY KEY,
    workflow_type VARCHAR(50) NOT NULL,
    client_id INTEGER REFERENCES users(id),
    role_current VARCHAR(50) NOT NULL,
    current_status VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    description TEXT,
    location TEXT,
    contact_info JSONB DEFAULT '{}',
    state_data JSONB DEFAULT '{}',
    -- ... other fields
);

-- Pending Notifications table (from migration 017)
CREATE TABLE pending_notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    request_id VARCHAR(36) NOT NULL REFERENCES service_requests(id),
    workflow_type VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL,
    -- ... other fields
);
```

### Code Structure

#### Handler Implementation
- **File**: `handlers/call_center/orders.py`
- **Key Functions**:
  - `get_client_phone()`: Client lookup and validation
  - `select_service_type()`: Service type selection and workflow mapping
  - `get_issue_description()`: Detailed issue capture
  - `set_order_priority()`: Priority setting and workflow creation

#### State Management
- **File**: `states/call_center.py`
- **New States**:
  - `issue_description_capture`: For detailed issue collection
  - `main_menu`: For workflow completion

#### Workflow Engine Integration
- **File**: `utils/workflow_engine.py`
- **Enhancement**: Added notification sending during workflow initiation
- **Routing Logic**: Proper role assignment based on workflow type and creator

#### State Manager Enhancement
- **File**: `utils/state_manager.py`
- **Enhancement**: Role-based routing for call center initiated requests
- **Logic**: Different initial roles based on `created_by_role` parameter

### Service Type Mapping

```python
workflow_mapping = {
    'installation': WorkflowType.CONNECTION_REQUEST.value,
    'setup': WorkflowType.CONNECTION_REQUEST.value,
    'repair': WorkflowType.TECHNICAL_SERVICE.value,
    'maintenance': WorkflowType.TECHNICAL_SERVICE.value,
    'consultation': WorkflowType.CALL_CENTER_DIRECT.value
}
```

## User Interface

### Keyboard Layout

The call center interface includes:

1. **Service Type Selection**:
   ```
   🔌 O'rnatish (Ulanish)     | 🔌 Установка (Подключение)
   📡 Sozlash (Ulanish)      | 📡 Настройка (Подключение)
   🔧 Ta'mirlash (Texnik)    | 🔧 Ремонт (Техническая)
   🧰 Profilaktika (Texnik)  | 🧰 Профилактика (Техническая)
   ❓ Konsultatsiya (Direct) | ❓ Консультация (Прямая)
   ```

2. **Priority Selection**:
   ```
   🔴 Yuqori | 🟡 O'rta | 🟢 Past
   🔴 Высокий | 🟡 Средний | 🟢 Низкий
   ```

### Workflow States

```python
class CallCenterOrderStates(StatesGroup):
    new_order_phone = State()              # Phone number input
    new_client_name = State()              # New client name
    new_client_address = State()           # New client address
    select_service_type = State()          # Service type selection
    issue_description_capture = State()    # Issue description
    order_priority = State()               # Priority selection
    main_menu = State()                    # Completion state
```

## Testing

### Unit Tests

Comprehensive test suite in `tests/test_call_center_workflow_requests.py`:

- **Connection Request Creation**: Verifies proper creation and routing to manager
- **Technical Service Creation**: Verifies proper creation and routing to controller
- **Call Center Direct Creation**: Verifies proper creation and routing to supervisor
- **Client Details Capture**: Verifies proper data collection and storage
- **Issue Description Capture**: Verifies detailed issue collection
- **Workflow Compatibility**: Ensures same workflows as client-initiated requests
- **Error Handling**: Tests various error scenarios
- **Service Type Mapping**: Validates correct workflow type assignment

### Integration Testing

Integration test script `test_call_center_integration.py` verifies:
- End-to-end workflow creation
- Proper routing logic
- Service type mappings
- Component integration

## Usage Flow

### Typical Call Center Workflow

1. **Operator receives call** from client
2. **Phone number entry**: Operator enters client's phone number
3. **Client lookup**: System finds existing client or prompts for new client creation
4. **Service selection**: Operator selects appropriate service type
5. **Issue description**: Operator provides detailed problem description
6. **Priority setting**: Operator sets request priority
7. **Workflow creation**: System creates workflow request and routes to appropriate role
8. **Confirmation**: Operator receives confirmation with request ID and routing information

### Example Success Message

```
✅ So'rov muvaffaqiyatli yaratildi!

🆔 So'rov ID: abc12345
📋 Ish jarayoni: Texnik xizmat
🔧 Xizmat: repair
🎯 Ustuvorlik: medium
📞 Telefon: 998901234567
👤 Mijoz: John Doe
➡️ Yo'naltirildi: Nazoratchi

ℹ️ So'rov nazoratchi orqali texnikka yuboriladi
```

## Benefits

### For Call Center Operators
- **Streamlined Process**: Clear step-by-step workflow
- **Intelligent Routing**: Automatic routing based on service type
- **Client History**: Access to client's previous requests
- **Multi-language Support**: Uzbek and Russian interfaces

### For Management
- **Audit Trail**: Complete tracking of call center initiated requests
- **Performance Metrics**: Integration with existing analytics
- **Quality Control**: Detailed issue descriptions for better service
- **Workflow Consistency**: Same workflows as client-initiated requests

### For Clients
- **Faster Service**: Direct creation by trained operators
- **Better Documentation**: Detailed issue descriptions
- **Consistent Experience**: Same service quality regardless of initiation method

## Future Enhancements

### Potential Improvements
1. **Call Recording Integration**: Link workflow requests to call recordings
2. **Real-time Dashboard**: Live view of call center created requests
3. **Advanced Analytics**: Call center specific performance metrics
4. **Bulk Operations**: Handle multiple requests from single call
5. **Client Verification**: Enhanced client identity verification

### Scalability Considerations
- **Load Balancing**: Support for multiple call center operators
- **Database Optimization**: Efficient queries for high-volume operations
- **Caching**: Client data caching for faster lookups
- **Monitoring**: Real-time monitoring of workflow creation rates

## Conclusion

The Call Center Initiated Requests implementation provides a comprehensive solution for call center operators to create and manage workflow requests on behalf of clients. The system ensures proper routing, maintains data integrity, and provides a seamless experience for both operators and clients while integrating seamlessly with the existing workflow infrastructure.