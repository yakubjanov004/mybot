"""
Unit tests for staff creation tracking models and validation functions.
Tests Requirements 1.1, 1.2, 1.3 from the multi-role application creation spec.
"""

import pytest
from datetime import datetime
from database.models import (
    ServiceRequest, ClientSelectionData, StaffApplicationAudit,
    validate_staff_creation_data, validate_client_selection_data,
    ModelConstants, WorkflowType, RequestStatus, Priority
)


class TestServiceRequestStaffTracking:
    """Test ServiceRequest model with staff creation tracking fields"""
    
    def test_service_request_default_values(self):
        """Test that ServiceRequest has correct default values for staff tracking"""
        request = ServiceRequest()
        
        assert request.created_by_staff is False
        assert request.staff_creator_id is None
        assert request.staff_creator_role is None
        assert request.creation_source == "client"
        assert request.client_notified_at is None
    
    def test_service_request_staff_creation_fields(self):
        """Test ServiceRequest with staff creation fields populated"""
        now = datetime.now()
        request = ServiceRequest(
            id="test-123",
            created_by_staff=True,
            staff_creator_id=456,
            staff_creator_role="manager",
            creation_source="manager",
            client_notified_at=now
        )
        
        assert request.created_by_staff is True
        assert request.staff_creator_id == 456
        assert request.staff_creator_role == "manager"
        assert request.creation_source == "manager"
        assert request.client_notified_at == now
    
    def test_service_request_to_dict_includes_staff_fields(self):
        """Test that to_dict includes all staff creation tracking fields"""
        now = datetime.now()
        request = ServiceRequest(
            id="test-123",
            created_by_staff=True,
            staff_creator_id=456,
            staff_creator_role="manager",
            creation_source="manager",
            client_notified_at=now
        )
        
        data = request.to_dict()
        
        assert data['created_by_staff'] is True
        assert data['staff_creator_id'] == 456
        assert data['staff_creator_role'] == "manager"
        assert data['creation_source'] == "manager"
        assert data['client_notified_at'] == now
    
    def test_service_request_from_dict_with_staff_fields(self):
        """Test creating ServiceRequest from dict with staff fields"""
        now = datetime.now()
        data = {
            'id': 'test-123',
            'created_by_staff': True,
            'staff_creator_id': 456,
            'staff_creator_role': 'manager',
            'creation_source': 'manager',
            'client_notified_at': now
        }
        
        request = ServiceRequest.from_dict(data)
        
        assert request.created_by_staff is True
        assert request.staff_creator_id == 456
        assert request.staff_creator_role == "manager"
        assert request.creation_source == "manager"
        assert request.client_notified_at == now


class TestClientSelectionData:
    """Test ClientSelectionData model"""
    
    def test_client_selection_data_default_values(self):
        """Test ClientSelectionData default values"""
        data = ClientSelectionData()
        
        assert data.id is None
        assert data.search_method == "phone"
        assert data.search_value is None
        assert data.client_id is None
        assert data.new_client_data == {}
        assert data.verified is False
        assert data.created_at is None
    
    def test_client_selection_data_phone_search(self):
        """Test ClientSelectionData for phone search"""
        data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567",
            client_id=123,
            verified=True
        )
        
        assert data.search_method == "phone"
        assert data.search_value == "+998901234567"
        assert data.client_id == 123
        assert data.verified is True
    
    def test_client_selection_data_new_client(self):
        """Test ClientSelectionData for new client creation"""
        new_client_info = {
            "full_name": "Test User",
            "phone": "+998901234567",
            "language": "uz"
        }
        
        data = ClientSelectionData(
            search_method="new",
            new_client_data=new_client_info,
            verified=True
        )
        
        assert data.search_method == "new"
        assert data.new_client_data == new_client_info
        assert data.verified is True
    
    def test_client_selection_data_to_dict(self):
        """Test ClientSelectionData to_dict method"""
        now = datetime.now()
        data = ClientSelectionData(
            id=1,
            search_method="name",
            search_value="John Doe",
            client_id=456,
            verified=True,
            created_at=now
        )
        
        result = data.to_dict()
        
        assert result['id'] == 1
        assert result['search_method'] == "name"
        assert result['search_value'] == "John Doe"
        assert result['client_id'] == 456
        assert result['verified'] is True
        assert result['created_at'] == now
    
    def test_client_selection_data_from_dict(self):
        """Test ClientSelectionData from_dict method"""
        now = datetime.now()
        dict_data = {
            'id': 1,
            'search_method': 'id',
            'search_value': '789',
            'client_id': 789,
            'verified': True,
            'created_at': now
        }
        
        data = ClientSelectionData.from_dict(dict_data)
        
        assert data.id == 1
        assert data.search_method == "id"
        assert data.search_value == "789"
        assert data.client_id == 789
        assert data.verified is True
        assert data.created_at == now


class TestStaffApplicationAudit:
    """Test StaffApplicationAudit model"""
    
    def test_staff_application_audit_default_values(self):
        """Test StaffApplicationAudit default values"""
        audit = StaffApplicationAudit()
        
        assert audit.id is None
        assert audit.application_id is None
        assert audit.creator_id is None
        assert audit.creator_role is None
        assert audit.client_id is None
        assert audit.application_type is None
        assert audit.creation_timestamp is None
        assert audit.client_notified is False
        assert audit.client_notified_at is None
        assert audit.workflow_initiated is False
        assert audit.workflow_initiated_at is None
        assert audit.metadata == {}
        assert audit.ip_address is None
        assert audit.user_agent is None
        assert audit.session_id is None
    
    def test_staff_application_audit_full_data(self):
        """Test StaffApplicationAudit with full data"""
        now = datetime.now()
        metadata = {"priority": "high", "notes": "Urgent request"}
        
        audit = StaffApplicationAudit(
            id=1,
            application_id="app-123",
            creator_id=456,
            creator_role="manager",
            client_id=789,
            application_type="connection_request",
            creation_timestamp=now,
            client_notified=True,
            client_notified_at=now,
            workflow_initiated=True,
            workflow_initiated_at=now,
            metadata=metadata,
            ip_address="192.168.1.1",
            user_agent="TelegramBot/1.0",
            session_id="sess-abc123"
        )
        
        assert audit.id == 1
        assert audit.application_id == "app-123"
        assert audit.creator_id == 456
        assert audit.creator_role == "manager"
        assert audit.client_id == 789
        assert audit.application_type == "connection_request"
        assert audit.creation_timestamp == now
        assert audit.client_notified is True
        assert audit.client_notified_at == now
        assert audit.workflow_initiated is True
        assert audit.workflow_initiated_at == now
        assert audit.metadata == metadata
        assert audit.ip_address == "192.168.1.1"
        assert audit.user_agent == "TelegramBot/1.0"
        assert audit.session_id == "sess-abc123"
    
    def test_staff_application_audit_to_dict(self):
        """Test StaffApplicationAudit to_dict method"""
        now = datetime.now()
        audit = StaffApplicationAudit(
            application_id="app-123",
            creator_id=456,
            creator_role="junior_manager",
            client_id=789,
            application_type="technical_service",
            creation_timestamp=now
        )
        
        result = audit.to_dict()
        
        assert result['application_id'] == "app-123"
        assert result['creator_id'] == 456
        assert result['creator_role'] == "junior_manager"
        assert result['client_id'] == 789
        assert result['application_type'] == "technical_service"
        assert result['creation_timestamp'] == now
    
    def test_staff_application_audit_from_dict(self):
        """Test StaffApplicationAudit from_dict method"""
        now = datetime.now()
        dict_data = {
            'id': 1,
            'application_id': 'app-456',
            'creator_id': 123,
            'creator_role': 'controller',
            'client_id': 789,
            'application_type': 'connection_request',
            'creation_timestamp': now,
            'client_notified': True,
            'workflow_initiated': False,
            'metadata': {'test': 'data'}
        }
        
        audit = StaffApplicationAudit.from_dict(dict_data)
        
        assert audit.id == 1
        assert audit.application_id == "app-456"
        assert audit.creator_id == 123
        assert audit.creator_role == "controller"
        assert audit.client_id == 789
        assert audit.application_type == "connection_request"
        assert audit.creation_timestamp == now
        assert audit.client_notified is True
        assert audit.workflow_initiated is False
        assert audit.metadata == {'test': 'data'}


class TestValidationFunctions:
    """Test validation functions for staff creation models"""
    
    def test_validate_staff_creation_data_valid_client_request(self):
        """Test validation of valid client-created request"""
        request = ServiceRequest(
            created_by_staff=False,
            creation_source="client"
        )
        
        errors = validate_staff_creation_data(request)
        assert len(errors) == 0
    
    def test_validate_staff_creation_data_valid_staff_request(self):
        """Test validation of valid staff-created request"""
        request = ServiceRequest(
            created_by_staff=True,
            staff_creator_id=123,
            staff_creator_role="manager",
            creation_source="manager"
        )
        
        errors = validate_staff_creation_data(request)
        assert len(errors) == 0
    
    def test_validate_staff_creation_data_missing_creator_id(self):
        """Test validation fails when staff_creator_id is missing"""
        request = ServiceRequest(
            created_by_staff=True,
            staff_creator_role="manager",
            creation_source="manager"
        )
        
        errors = validate_staff_creation_data(request)
        assert len(errors) == 1
        assert "staff_creator_id is required" in errors[0]
    
    def test_validate_staff_creation_data_missing_creator_role(self):
        """Test validation fails when staff_creator_role is missing"""
        request = ServiceRequest(
            created_by_staff=True,
            staff_creator_id=123,
            creation_source="manager"
        )
        
        errors = validate_staff_creation_data(request)
        assert len(errors) == 1
        assert "staff_creator_role is required" in errors[0]
    
    def test_validate_staff_creation_data_invalid_creator_role(self):
        """Test validation fails with invalid staff_creator_role"""
        request = ServiceRequest(
            created_by_staff=True,
            staff_creator_id=123,
            staff_creator_role="invalid_role",
            creation_source="manager"
        )
        
        errors = validate_staff_creation_data(request)
        assert len(errors) == 1
        assert "Invalid staff_creator_role" in errors[0]
    
    def test_validate_staff_creation_data_invalid_creation_source(self):
        """Test validation fails with invalid creation_source"""
        request = ServiceRequest(
            created_by_staff=False,
            creation_source="invalid_source"
        )
        
        errors = validate_staff_creation_data(request)
        assert len(errors) == 1
        assert "Invalid creation_source" in errors[0]
    
    def test_validate_client_selection_data_valid_phone_search(self):
        """Test validation of valid phone search"""
        data = ClientSelectionData(
            search_method="phone",
            search_value="+998901234567"
        )
        
        errors = validate_client_selection_data(data)
        assert len(errors) == 0
    
    def test_validate_client_selection_data_valid_new_client(self):
        """Test validation of valid new client data"""
        data = ClientSelectionData(
            search_method="new",
            new_client_data={"name": "Test", "phone": "+998901234567"}
        )
        
        errors = validate_client_selection_data(data)
        assert len(errors) == 0
    
    def test_validate_client_selection_data_invalid_search_method(self):
        """Test validation fails with invalid search method"""
        data = ClientSelectionData(
            search_method="invalid_method",
            search_value="test"
        )
        
        errors = validate_client_selection_data(data)
        assert len(errors) == 1
        assert "Invalid search_method" in errors[0]
    
    def test_validate_client_selection_data_missing_search_value(self):
        """Test validation fails when search_value is missing for non-new methods"""
        data = ClientSelectionData(
            search_method="phone"
        )
        
        errors = validate_client_selection_data(data)
        assert len(errors) == 1
        assert "search_value is required" in errors[0]
    
    def test_validate_client_selection_data_missing_new_client_data(self):
        """Test validation fails when new_client_data is missing for new method"""
        data = ClientSelectionData(
            search_method="new"
        )
        
        errors = validate_client_selection_data(data)
        assert len(errors) == 1
        assert "new_client_data is required" in errors[0]


class TestModelConstants:
    """Test ModelConstants for staff creation features"""
    
    def test_creation_sources_constant(self):
        """Test CREATION_SOURCES constant"""
        expected_sources = ["client", "manager", "junior_manager", "controller", "call_center"]
        assert ModelConstants.CREATION_SOURCES == expected_sources
    
    def test_search_methods_constant(self):
        """Test SEARCH_METHODS constant"""
        expected_methods = ["phone", "name", "id", "new"]
        assert ModelConstants.SEARCH_METHODS == expected_methods
    
    def test_application_types_constant(self):
        """Test APPLICATION_TYPES constant"""
        expected_types = ["connection_request", "technical_service"]
        assert ModelConstants.APPLICATION_TYPES == expected_types
    
    def test_default_values(self):
        """Test default values for staff creation"""
        assert ModelConstants.DEFAULT_CREATION_SOURCE == "client"
        assert ModelConstants.DEFAULT_SEARCH_METHOD == "phone"


if __name__ == "__main__":
    pytest.main([__file__])