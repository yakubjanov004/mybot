"""
Integration tests for inbox system components
"""

import pytest
from datetime import datetime
from database.inbox_models import (
    InboxMessage, ApplicationTransfer, InboxRole, ApplicationType,
    MessageType, MessagePriority, validate_role_transfer,
    create_inbox_message_for_application, create_transfer_audit_record
)

class TestInboxSystemIntegration:
    """Test inbox system integration"""
    
    def test_create_inbox_message_for_zayavka(self):
        """Test creating inbox message for zayavka"""
        message = create_inbox_message_for_application(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value
        )
        
        assert message.application_id == "123"
        assert message.application_type == ApplicationType.ZAYAVKA.value
        assert message.assigned_role == InboxRole.MANAGER.value
        assert message.message_type == MessageType.APPLICATION.value
        assert message.priority == MessagePriority.MEDIUM.value
        assert message.created_at is not None
    
    def test_create_inbox_message_for_service_request(self):
        """Test creating inbox message for service request"""
        message = create_inbox_message_for_application(
            application_id="550e8400-e29b-41d4-a716-446655440000",
            application_type=ApplicationType.SERVICE_REQUEST.value,
            assigned_role=InboxRole.TECHNICIAN.value,
            title="Technical Service Request",
            description="New technical service request assigned",
            priority=MessagePriority.HIGH.value
        )
        
        assert message.application_id == "550e8400-e29b-41d4-a716-446655440000"
        assert message.application_type == ApplicationType.SERVICE_REQUEST.value
        assert message.assigned_role == InboxRole.TECHNICIAN.value
        assert message.title == "Technical Service Request"
        assert message.description == "New technical service request assigned"
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
            notes="Transferred due to high workload"
        )
        
        assert transfer.application_id == "123"
        assert transfer.application_type == ApplicationType.ZAYAVKA.value
        assert transfer.from_role == InboxRole.MANAGER.value
        assert transfer.to_role == InboxRole.JUNIOR_MANAGER.value
        assert transfer.transferred_by == 1
        assert transfer.transfer_reason == "Workload distribution"
        assert transfer.transfer_notes == "Transferred due to high workload"
        assert transfer.created_at is not None
    
    def test_role_transfer_validation_workflow(self):
        """Test complete role transfer validation workflow"""
        # Test valid transfers in typical workflow
        valid_transfers = [
            (InboxRole.MANAGER.value, InboxRole.JUNIOR_MANAGER.value),
            (InboxRole.JUNIOR_MANAGER.value, InboxRole.CONTROLLER.value),
            (InboxRole.CONTROLLER.value, InboxRole.TECHNICIAN.value),
            (InboxRole.TECHNICIAN.value, InboxRole.WAREHOUSE.value),
            (InboxRole.WAREHOUSE.value, InboxRole.TECHNICIAN.value),
            (InboxRole.MANAGER.value, InboxRole.CALL_CENTER.value),
            (InboxRole.CALL_CENTER.value, InboxRole.CALL_CENTER_SUPERVISOR.value)
        ]
        
        for from_role, to_role in valid_transfers:
            errors = validate_role_transfer(from_role, to_role)
            assert len(errors) == 0, f"Transfer from {from_role} to {to_role} should be valid"
    
    def test_role_transfer_validation_invalid_workflow(self):
        """Test invalid role transfer validation"""
        # Test invalid transfers that should not be allowed
        invalid_transfers = [
            (InboxRole.WAREHOUSE.value, InboxRole.CALL_CENTER.value),
            (InboxRole.CALL_CENTER.value, InboxRole.TECHNICIAN.value),
            (InboxRole.TECHNICIAN.value, InboxRole.CALL_CENTER_SUPERVISOR.value)
        ]
        
        for from_role, to_role in invalid_transfers:
            errors = validate_role_transfer(from_role, to_role)
            assert len(errors) > 0, f"Transfer from {from_role} to {to_role} should be invalid"
    
    def test_inbox_message_lifecycle(self):
        """Test complete inbox message lifecycle"""
        # Create message
        message = InboxMessage(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value,
            title="New Application",
            description="New application needs review"
        )
        
        # Verify initial state
        assert message.is_read is False
        assert message.updated_at is None
        
        # Mark as read
        message.mark_as_read()
        assert message.is_read is True
        assert message.updated_at is not None
        
        # Update priority
        original_updated_at = message.updated_at
        message.update_priority(MessagePriority.HIGH.value)
        assert message.priority == MessagePriority.HIGH.value
        assert message.updated_at > original_updated_at
    
    def test_application_transfer_lifecycle(self):
        """Test complete application transfer lifecycle"""
        # Create initial assignment (no from_role)
        initial_transfer = ApplicationTransfer(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            from_role=None,  # Initial assignment
            to_role=InboxRole.MANAGER.value,
            transferred_by=1,
            transfer_reason="Initial assignment"
        )
        
        assert initial_transfer.from_role is None
        assert initial_transfer.to_role == InboxRole.MANAGER.value
        
        # Create subsequent transfer
        subsequent_transfer = ApplicationTransfer(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            from_role=InboxRole.MANAGER.value,
            to_role=InboxRole.JUNIOR_MANAGER.value,
            transferred_by=2,
            transfer_reason="Workload distribution"
        )
        
        assert subsequent_transfer.from_role == InboxRole.MANAGER.value
        assert subsequent_transfer.to_role == InboxRole.JUNIOR_MANAGER.value
    
    def test_mixed_application_types_handling(self):
        """Test handling of both zayavki and service requests"""
        # Create messages for both types
        zayavka_message = create_inbox_message_for_application(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value
        )
        
        service_request_message = create_inbox_message_for_application(
            application_id="550e8400-e29b-41d4-a716-446655440000",
            application_type=ApplicationType.SERVICE_REQUEST.value,
            assigned_role=InboxRole.TECHNICIAN.value
        )
        
        # Verify both are valid
        assert zayavka_message.application_type == ApplicationType.ZAYAVKA.value
        assert service_request_message.application_type == ApplicationType.SERVICE_REQUEST.value
        
        # Create transfers for both types
        zayavka_transfer = create_transfer_audit_record(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            from_role=InboxRole.MANAGER.value,
            to_role=InboxRole.JUNIOR_MANAGER.value,
            transferred_by=1
        )
        
        service_request_transfer = create_transfer_audit_record(
            application_id="550e8400-e29b-41d4-a716-446655440000",
            application_type=ApplicationType.SERVICE_REQUEST.value,
            from_role=InboxRole.CONTROLLER.value,
            to_role=InboxRole.TECHNICIAN.value,
            transferred_by=2
        )
        
        # Verify both transfers are valid
        assert zayavka_transfer.application_type == ApplicationType.ZAYAVKA.value
        assert service_request_transfer.application_type == ApplicationType.SERVICE_REQUEST.value
    
    def test_error_handling_scenarios(self):
        """Test error handling in various scenarios"""
        # Test invalid application ID format for zayavka
        with pytest.raises(ValueError, match="application_id must be numeric for zayavka type"):
            InboxMessage(
                application_id="invalid-uuid",
                application_type=ApplicationType.ZAYAVKA.value,
                assigned_role=InboxRole.MANAGER.value
            )
        
        # Test invalid application ID format for service request
        with pytest.raises(ValueError, match="application_id must be UUID format for service_request type"):
            InboxMessage(
                application_id="123",
                application_type=ApplicationType.SERVICE_REQUEST.value,
                assigned_role=InboxRole.MANAGER.value
            )
        
        # Test same role transfer
        with pytest.raises(ValueError, match="from_role and to_role cannot be the same"):
            ApplicationTransfer(
                application_id="123",
                application_type=ApplicationType.ZAYAVKA.value,
                from_role=InboxRole.MANAGER.value,
                to_role=InboxRole.MANAGER.value,
                transferred_by=1
            )
        
        # Test invalid priority update
        message = InboxMessage(
            application_id="123",
            application_type=ApplicationType.ZAYAVKA.value,
            assigned_role=InboxRole.MANAGER.value
        )
        
        with pytest.raises(ValueError, match="Invalid priority"):
            message.update_priority("invalid_priority")