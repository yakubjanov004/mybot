"""
Unit tests for inbox system data models
"""

import pytest
from datetime import datetime
from database.inbox_models import (
    InboxMessage, ApplicationTransfer, InboxRole, ApplicationType, 
    MessageType, MessagePriority, validate_role_transfer,
    get_role_display_name, get_priority_display_name,
    create_inbox_message_for_application, create_transfer_audit_record,
    InboxConstants
)

class TestInboxMessage:
    """Test InboxMessage model"""
    
    def test_valid_inbox_message_creation(self):
        """Test creating a valid inbox message"""
        message = InboxMessage(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value,
            title="Test Message",
            description="Test description"
        )
        
        assert message.application_id == "123"
        assert message.application_type == ApplicationType.ZAYAVKA.value
        assert message.assigned_role == InboxRole.MANAGER.value
        assert message.title == "Test Message"
        assert message.description == "Test description"
        assert message.message_type == MessageType.APPLICATION.value
        assert message.priority == MessagePriority.MEDIUM.value
        assert message.is_read is False
    
    def test_inbox_message_validation_required_fields(self):
        """Test validation of required fields"""
        with pytest.raises(ValueError, match="application_id is required"):
            InboxMessage(
                application_type=ApplicationType.ZAYAVKA.value,
                assigned_role=InboxRole.MANAGER.value
            )
        
        with pytest.raises(ValueError, match="application_type is required"):
            InboxMessage(
                application_id="123",
                assigned_role=InboxRole.MANAGER.value
            )
        
        with pytest.raises(ValueError, match="assigned_role is required"):
            InboxMessage(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value
            )
    
    def test_inbox_message_validation_invalid_enums(self):
        """Test validation of enum values"""
        with pytest.raises(ValueError, match="Invalid application_type"):
            InboxMessage(
                application_id="123",
                application_type="invalid_type",
                assigned_role=InboxRole.MANAGER.value
            )
        
        with pytest.raises(ValueError, match="Invalid assigned_role"):
            InboxMessage(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                assigned_role="invalid_role"
            )
        
        with pytest.raises(ValueError, match="Invalid message_type"):
            InboxMessage(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                assigned_role=InboxRole.MANAGER.value,
                message_type="invalid_message_type"
            )
        
        with pytest.raises(ValueError, match="Invalid priority"):
            InboxMessage(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                assigned_role=InboxRole.MANAGER.value,
                priority="invalid_priority"
            )
    
    def test_inbox_message_application_id_format_validation(self):
        """Test application_id format validation"""
        # Valid zayavka ID (numeric)
        message = InboxMessage(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value
        )
        assert message.application_id == "123"
        
        # Invalid zayavka ID (non-numeric)
        with pytest.raises(ValueError, match="application_id must be numeric for zayavka type"):
            InboxMessage(
                application_id="abc",
                application_type=ApplicationType.ZAYAVKA.value,
                assigned_role=InboxRole.MANAGER.value
            )
        
        # Valid service request ID (UUID format)
        message = InboxMessage(
            application_id="550e8400-e29b-41d4-a716-446655440000",
            application_type=ApplicationType.SERVICE_REQUEST.value,
            assigned_role=InboxRole.MANAGER.value
        )
        assert message.application_id == "550e8400-e29b-41d4-a716-446655440000"
        
        # Invalid service request ID (not UUID format)
        with pytest.raises(ValueError, match="application_id must be UUID format for service_request type"):
            InboxMessage(
                application_id="123",
                application_type=ApplicationType.SERVICE_REQUEST.value,
                assigned_role=InboxRole.MANAGER.value
            )
    
    def test_inbox_message_string_length_validation(self):
        """Test string length validation"""
        # Valid lengths
        message = InboxMessage(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value,
            title="A" * 255,
            description="B" * 2000
        )
        assert len(message.title) == 255
        assert len(message.description) == 2000
        
        # Title too long
        with pytest.raises(ValueError, match="title cannot exceed 255 characters"):
            InboxMessage(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                assigned_role=InboxRole.MANAGER.value,
                title="A" * 256
            )
        
        # Description too long
        with pytest.raises(ValueError, match="description cannot exceed 2000 characters"):
            InboxMessage(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                assigned_role=InboxRole.MANAGER.value,
                description="B" * 2001
            )
    
    def test_inbox_message_to_dict(self):
        """Test converting inbox message to dictionary"""
        now = datetime.now()
        message = InboxMessage(
            id=1,
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value,
            title="Test",
            created_at=now
        )
        
        data = message.to_dict()
        assert data['id'] == 1
        assert data['application_id'] == "123"
        assert data['application_type'] == ApplicationType.ZAYAVKA.value
        assert data['assigned_role'] == InboxRole.MANAGER.value
        assert data['title'] == "Test"
        assert data['created_at'] == now
    
    def test_inbox_message_from_dict(self):
        """Test creating inbox message from dictionary"""
        now = datetime.now()
        data = {
            'id': 1,
            'application_id': "123",
            'application_type': ApplicationType.ZAYAVKA.value,
            'assigned_role': InboxRole.MANAGER.value,
            'title': "Test",
            'created_at': now
        }
        
        message = InboxMessage.from_dict(data)
        assert message.id == 1
        assert message.application_id == "123"
        assert message.title == "Test"
        assert message.created_at == now
    
    def test_inbox_message_mark_as_read(self):
        """Test marking message as read"""
        message = InboxMessage(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value
        )
        
        assert message.is_read is False
        assert message.updated_at is None
        
        message.mark_as_read()
        
        assert message.is_read is True
        assert message.updated_at is not None
    
    def test_inbox_message_update_priority(self):
        """Test updating message priority"""
        message = InboxMessage(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value
        )
        
        assert message.priority == MessagePriority.MEDIUM.value
        assert message.updated_at is None
        
        message.update_priority(MessagePriority.HIGH.value)
        
        assert message.priority == MessagePriority.HIGH.value
        assert message.updated_at is not None
        
        # Test invalid priority
        with pytest.raises(ValueError, match="Invalid priority"):
            message.update_priority("invalid_priority")

class TestApplicationTransfer:
    """Test ApplicationTransfer model"""
    
    def test_valid_application_transfer_creation(self):
        """Test creating a valid application transfer"""
        transfer = ApplicationTransfer(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            from_role=InboxRole.MANAGER.value,
            to_role=InboxRole.JUNIOR_MANAGER.value,
            transferred_by=1,
            transfer_reason="Workload distribution"
        )
        
        assert transfer.application_id == "123"
        assert transfer.application_type == ApplicationType.ZAYAVKA.value
        assert transfer.from_role == InboxRole.MANAGER.value
        assert transfer.to_role == InboxRole.JUNIOR_MANAGER.value
        assert transfer.transferred_by == 1
        assert transfer.transfer_reason == "Workload distribution"
    
    def test_application_transfer_validation_required_fields(self):
        """Test validation of required fields"""
        with pytest.raises(ValueError, match="application_id is required"):
            ApplicationTransfer(
                application_type=ApplicationType.ZAYAVKA.value,
                to_role=InboxRole.MANAGER.value,
                transferred_by=1
            )
        
        with pytest.raises(ValueError, match="application_type is required"):
            ApplicationTransfer(
                application_id="123",
                to_role=InboxRole.MANAGER.value,
                transferred_by=1
            )
        
        with pytest.raises(ValueError, match="to_role is required"):
            ApplicationTransfer(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                transferred_by=1
            )
        
        with pytest.raises(ValueError, match="transferred_by is required"):
            ApplicationTransfer(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                to_role=InboxRole.MANAGER.value
            )
    
    def test_application_transfer_validation_invalid_enums(self):
        """Test validation of enum values"""
        with pytest.raises(ValueError, match="Invalid application_type"):
            ApplicationTransfer(
                application_id="123",
                application_type="invalid_type",
                to_role=InboxRole.MANAGER.value,
                transferred_by=1
            )
        
        with pytest.raises(ValueError, match="Invalid to_role"):
            ApplicationTransfer(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                to_role="invalid_role",
                transferred_by=1
            )
        
        with pytest.raises(ValueError, match="Invalid from_role"):
            ApplicationTransfer(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                from_role="invalid_role",
                to_role=InboxRole.MANAGER.value,
                transferred_by=1
            )
    
    def test_application_transfer_same_roles_validation(self):
        """Test validation that from_role and to_role are different"""
        with pytest.raises(ValueError, match="from_role and to_role cannot be the same"):
            ApplicationTransfer(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                from_role=InboxRole.MANAGER.value,
                to_role=InboxRole.MANAGER.value,
                transferred_by=1
            )
    
    def test_application_transfer_transferred_by_validation(self):
        """Test validation of transferred_by field"""
        with pytest.raises(ValueError, match="transferred_by must be a positive integer"):
            ApplicationTransfer(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                to_role=InboxRole.MANAGER.value,
                transferred_by=0
            )
        
        with pytest.raises(ValueError, match="transferred_by must be a positive integer"):
            ApplicationTransfer(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                to_role=InboxRole.MANAGER.value,
                transferred_by=-1
            )
    
    def test_application_transfer_to_dict(self):
        """Test converting application transfer to dictionary"""
        now = datetime.now()
        transfer = ApplicationTransfer(
            id=1,
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            from_role=InboxRole.MANAGER.value,
            to_role=InboxRole.JUNIOR_MANAGER.value,
            transferred_by=1,
            created_at=now
        )
        
        data = transfer.to_dict()
        assert data['id'] == 1
        assert data['application_id'] == "123"
        assert data['from_role'] == InboxRole.MANAGER.value
        assert data['to_role'] == InboxRole.JUNIOR_MANAGER.value
        assert data['transferred_by'] == 1
        assert data['created_at'] == now
    
    def test_application_transfer_from_dict(self):
        """Test creating application transfer from dictionary"""
        now = datetime.now()
        data = {
            'id': 1,
            'application_id': "123",
            'application_type': ApplicationType.ZAYAVKA.value,
            'from_role': InboxRole.MANAGER.value,
            'to_role': InboxRole.JUNIOR_MANAGER.value,
            'transferred_by': 1,
            'created_at': now
        }
        
        transfer = ApplicationTransfer.from_dict(data)
        assert transfer.id == 1
        assert transfer.application_id == "123"
        assert transfer.from_role == InboxRole.MANAGER.value
        assert transfer.to_role == InboxRole.JUNIOR_MANAGER.value
        assert transfer.transferred_by == 1
        assert transfer.created_at == now

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_validate_role_transfer_valid_transfers(self):
        """Test valid role transfers"""
        # Manager to junior manager
        errors = validate_role_transfer(
            InboxRole.MANAGER.value, 
            InboxRole.JUNIOR_MANAGER.value
        )
        assert len(errors) == 0
        
        # Controller to technician
        errors = validate_role_transfer(
            InboxRole.CONTROLLER.value, 
            InboxRole.TECHNICIAN.value
        )
        assert len(errors) == 0
        
        # Initial assignment (no from_role)
        errors = validate_role_transfer(None, InboxRole.MANAGER.value)
        assert len(errors) == 0
    
    def test_validate_role_transfer_invalid_roles(self):
        """Test invalid role transfers"""
        errors = validate_role_transfer("invalid_role", InboxRole.MANAGER.value)
        assert len(errors) == 1
        assert "Invalid from_role" in errors[0]
        
        errors = validate_role_transfer(InboxRole.MANAGER.value, "invalid_role")
        assert len(errors) == 1
        assert "Invalid to_role" in errors[0]
    
    def test_validate_role_transfer_not_allowed(self):
        """Test transfers that are not allowed by business rules"""
        # Warehouse to call center (not allowed)
        errors = validate_role_transfer(
            InboxRole.WAREHOUSE.value, 
            InboxRole.CALL_CENTER.value
        )
        assert len(errors) == 1
        assert "Transfer from warehouse to call_center is not allowed" in errors[0]
    
    def test_get_role_display_name(self):
        """Test getting role display names"""
        # Russian
        assert get_role_display_name(InboxRole.MANAGER.value, 'ru') == 'Менеджер'
        assert get_role_display_name(InboxRole.TECHNICIAN.value, 'ru') == 'Техник'
        
        # Uzbek
        assert get_role_display_name(InboxRole.MANAGER.value, 'uz') == 'Menejer'
        assert get_role_display_name(InboxRole.TECHNICIAN.value, 'uz') == 'Texnik'
        
        # Unknown role returns original
        assert get_role_display_name('unknown_role', 'ru') == 'unknown_role'
    
    def test_get_priority_display_name(self):
        """Test getting priority display names"""
        # Russian
        assert get_priority_display_name(MessagePriority.HIGH.value, 'ru') == 'Высокий'
        assert get_priority_display_name(MessagePriority.LOW.value, 'ru') == 'Низкий'
        
        # Uzbek
        assert get_priority_display_name(MessagePriority.HIGH.value, 'uz') == 'Yuqori'
        assert get_priority_display_name(MessagePriority.LOW.value, 'uz') == 'Past'
        
        # Unknown priority returns original
        assert get_priority_display_name('unknown_priority', 'ru') == 'unknown_priority'
    
    def test_create_inbox_message_for_application(self):
        """Test creating inbox message for application"""
        message = create_inbox_message_for_application(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value
        )
        
        assert message.application_id == "123"
        assert message.application_type == ApplicationType.ZAYAVKA.value
        assert message.assigned_role == InboxRole.MANAGER.value
        assert message.title == "New Zayavka"
        assert "new zayavka" in message.description.lower()
        assert message.priority == MessagePriority.MEDIUM.value
        assert message.created_at is not None
        
        # With custom title and description
        message = create_inbox_message_for_application(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value,
            title="Custom Title",
            description="Custom Description",
            priority=MessagePriority.HIGH.value
        )
        
        assert message.title == "Custom Title"
        assert message.description == "Custom Description"
        assert message.priority == MessagePriority.HIGH.value
    
    def test_create_transfer_audit_record(self):
        """Test creating transfer audit record"""
        transfer = create_transfer_audit_record(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            from_role=InboxRole.MANAGER.value,
            to_role=InboxRole.JUNIOR_MANAGER.value,
            transferred_by=1,
            reason="Workload distribution",
            notes="Transfer notes"
        )
        
        assert transfer.application_id == "123"
        assert transfer.application_type == ApplicationType.ZAYAVKA.value
        assert transfer.from_role == InboxRole.MANAGER.value
        assert transfer.to_role == InboxRole.JUNIOR_MANAGER.value
        assert transfer.transferred_by == 1
        assert transfer.transfer_reason == "Workload distribution"
        assert transfer.transfer_notes == "Transfer notes"
        assert transfer.created_at is not None

class TestInboxConstants:
    """Test inbox constants"""
    
    def test_constants_values(self):
        """Test that constants have expected values"""
        assert len(InboxConstants.VALID_ROLES) == 7
        assert InboxRole.MANAGER.value in InboxConstants.VALID_ROLES
        assert InboxRole.TECHNICIAN.value in InboxConstants.VALID_ROLES
        
        assert len(InboxConstants.VALID_APPLICATION_TYPES) == 2
        assert ApplicationType.ZAYAVKA.value in InboxConstants.VALID_APPLICATION_TYPES
        assert ApplicationType.SERVICE_REQUEST.value in InboxConstants.VALID_APPLICATION_TYPES
        
        assert len(InboxConstants.VALID_MESSAGE_TYPES) == 4
        assert MessageType.APPLICATION.value in InboxConstants.VALID_MESSAGE_TYPES
        
        assert len(InboxConstants.VALID_PRIORITIES) == 4
        assert MessagePriority.HIGH.value in InboxConstants.VALID_PRIORITIES
        
        assert InboxConstants.DEFAULT_MESSAGE_TYPE == MessageType.APPLICATION.value
        assert InboxConstants.DEFAULT_PRIORITY == MessagePriority.MEDIUM.value
        
        assert InboxConstants.MAX_TITLE_LENGTH == 255
        assert InboxConstants.MAX_DESCRIPTION_LENGTH == 2000