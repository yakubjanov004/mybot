"""
Unit tests for role-based permission system.

Tests all permission validation functions and exception handling
for multi-role application creation feature.
"""

import pytest
from utils.role_permissions import (
    # Permission functions
    get_role_permissions,
    can_create_application,
    can_select_client,
    can_create_client,
    can_assign_directly,
    get_available_application_types,
    get_staff_roles_with_application_creation,
    get_notification_level,
    requires_approval,
    is_staff_role,
    get_role_hierarchy_level,
    can_manage_role,
    get_role_capabilities_summary,
    
    # Validation functions
    validate_application_creation_permission,
    validate_client_selection_permission,
    validate_client_creation_permission,
    validate_daily_limit,
    validate_comprehensive_permissions,
    
    # Exception classes
    RolePermissionError,
    ApplicationCreationPermissionError,
    ClientSelectionPermissionError,
    DailyLimitExceededError,
    
    # Constants and enums
    ROLE_PERMISSIONS,
    ApplicationType,
    STAFF_ROLES,
    APPLICATION_TYPES
)
from database.models import UserRole


class TestRolePermissions:
    """Test role permission matrix and basic permission checks"""
    
    def test_role_permissions_matrix_exists(self):
        """Test that permission matrix is properly defined"""
        assert isinstance(ROLE_PERMISSIONS, dict)
        assert len(ROLE_PERMISSIONS) > 0
        
        # Check that all UserRole values are in the matrix
        for role in UserRole:
            assert role.value in ROLE_PERMISSIONS
    
    def test_get_role_permissions_valid_roles(self):
        """Test getting permissions for valid roles"""
        for role in UserRole:
            permissions = get_role_permissions(role.value)
            assert permissions is not None
            assert hasattr(permissions, 'can_create_connection')
            assert hasattr(permissions, 'can_create_technical')
    
    def test_get_role_permissions_invalid_role(self):
        """Test getting permissions for invalid role raises ValueError"""
        with pytest.raises(ValueError, match="Unknown role"):
            get_role_permissions("invalid_role")
    
    def test_manager_permissions(self):
        """Test Manager role permissions"""
        permissions = get_role_permissions(UserRole.MANAGER.value)
        
        assert permissions.can_create_connection is True
        assert permissions.can_create_technical is True
        assert permissions.can_assign_directly is True
        assert permissions.can_select_client is True
        assert permissions.can_create_client is True
        assert permissions.notification_level == "high"
        assert permissions.max_applications_per_day is None
        assert permissions.requires_approval is False
    
    def test_junior_manager_permissions(self):
        """Test Junior Manager role permissions"""
        permissions = get_role_permissions(UserRole.JUNIOR_MANAGER.value)
        
        assert permissions.can_create_connection is True
        assert permissions.can_create_technical is False  # Key restriction
        assert permissions.can_assign_directly is False
        assert permissions.can_select_client is True
        assert permissions.can_create_client is True
        assert permissions.notification_level == "medium"
        assert permissions.max_applications_per_day == 50
        assert permissions.requires_approval is False
    
    def test_controller_permissions(self):
        """Test Controller role permissions"""
        permissions = get_role_permissions(UserRole.CONTROLLER.value)
        
        assert permissions.can_create_connection is True
        assert permissions.can_create_technical is True
        assert permissions.can_assign_directly is True
        assert permissions.can_select_client is True
        assert permissions.can_create_client is True
        assert permissions.notification_level == "high"
        assert permissions.max_applications_per_day is None
        assert permissions.requires_approval is False
    
    def test_call_center_permissions(self):
        """Test Call Center role permissions"""
        permissions = get_role_permissions(UserRole.CALL_CENTER.value)
        
        assert permissions.can_create_connection is True
        assert permissions.can_create_technical is True
        assert permissions.can_assign_directly is False
        assert permissions.can_select_client is True
        assert permissions.can_create_client is True
        assert permissions.notification_level == "medium"
        assert permissions.max_applications_per_day == 100
        assert permissions.requires_approval is False
    
    def test_client_permissions(self):
        """Test Client role has no application creation permissions"""
        permissions = get_role_permissions(UserRole.CLIENT.value)
        
        assert permissions.can_create_connection is False
        assert permissions.can_create_technical is False
        assert permissions.can_assign_directly is False
        assert permissions.can_select_client is False
        assert permissions.can_create_client is False
    
    def test_technician_permissions(self):
        """Test Technician role has no application creation permissions"""
        permissions = get_role_permissions(UserRole.TECHNICIAN.value)
        
        assert permissions.can_create_connection is False
        assert permissions.can_create_technical is False
        assert permissions.can_assign_directly is False
        assert permissions.can_select_client is False
        assert permissions.can_create_client is False


class TestApplicationCreationPermissions:
    """Test application creation permission checks"""
    
    def test_can_create_connection_request(self):
        """Test connection request creation permissions"""
        # Roles that can create connection requests
        assert can_create_application(UserRole.MANAGER.value, ApplicationType.CONNECTION_REQUEST.value) is True
        assert can_create_application(UserRole.JUNIOR_MANAGER.value, ApplicationType.CONNECTION_REQUEST.value) is True
        assert can_create_application(UserRole.CONTROLLER.value, ApplicationType.CONNECTION_REQUEST.value) is True
        assert can_create_application(UserRole.CALL_CENTER.value, ApplicationType.CONNECTION_REQUEST.value) is True
        
        # Roles that cannot create connection requests
        assert can_create_application(UserRole.CLIENT.value, ApplicationType.CONNECTION_REQUEST.value) is False
        assert can_create_application(UserRole.TECHNICIAN.value, ApplicationType.CONNECTION_REQUEST.value) is False
        assert can_create_application(UserRole.WAREHOUSE.value, ApplicationType.CONNECTION_REQUEST.value) is False
    
    def test_can_create_technical_service(self):
        """Test technical service creation permissions"""
        # Roles that can create technical service requests
        assert can_create_application(UserRole.MANAGER.value, ApplicationType.TECHNICAL_SERVICE.value) is True
        assert can_create_application(UserRole.CONTROLLER.value, ApplicationType.TECHNICAL_SERVICE.value) is True
        assert can_create_application(UserRole.CALL_CENTER.value, ApplicationType.TECHNICAL_SERVICE.value) is True
        
        # Junior Manager cannot create technical service requests
        assert can_create_application(UserRole.JUNIOR_MANAGER.value, ApplicationType.TECHNICAL_SERVICE.value) is False
        
        # Other roles cannot create technical service requests
        assert can_create_application(UserRole.CLIENT.value, ApplicationType.TECHNICAL_SERVICE.value) is False
        assert can_create_application(UserRole.TECHNICIAN.value, ApplicationType.TECHNICAL_SERVICE.value) is False
    
    def test_can_create_application_invalid_type(self):
        """Test invalid application type returns False"""
        assert can_create_application(UserRole.MANAGER.value, "invalid_type") is False
    
    def test_can_create_application_invalid_role(self):
        """Test invalid role returns False"""
        assert can_create_application("invalid_role", ApplicationType.CONNECTION_REQUEST.value) is False


class TestClientPermissions:
    """Test client selection and creation permissions"""
    
    def test_can_select_client(self):
        """Test client selection permissions"""
        # Staff roles can select clients
        assert can_select_client(UserRole.MANAGER.value) is True
        assert can_select_client(UserRole.JUNIOR_MANAGER.value) is True
        assert can_select_client(UserRole.CONTROLLER.value) is True
        assert can_select_client(UserRole.CALL_CENTER.value) is True
        
        # Non-staff roles cannot select clients
        assert can_select_client(UserRole.CLIENT.value) is False
        assert can_select_client(UserRole.TECHNICIAN.value) is False
    
    def test_can_create_client(self):
        """Test client creation permissions"""
        # Staff roles can create clients
        assert can_create_client(UserRole.MANAGER.value) is True
        assert can_create_client(UserRole.JUNIOR_MANAGER.value) is True
        assert can_create_client(UserRole.CONTROLLER.value) is True
        assert can_create_client(UserRole.CALL_CENTER.value) is True
        
        # Non-staff roles cannot create clients
        assert can_create_client(UserRole.CLIENT.value) is False
        assert can_create_client(UserRole.TECHNICIAN.value) is False
    
    def test_can_assign_directly(self):
        """Test direct assignment permissions"""
        # High-level roles can assign directly
        assert can_assign_directly(UserRole.MANAGER.value) is True
        assert can_assign_directly(UserRole.CONTROLLER.value) is True
        
        # Lower-level roles cannot assign directly
        assert can_assign_directly(UserRole.JUNIOR_MANAGER.value) is False
        assert can_assign_directly(UserRole.CALL_CENTER.value) is False
        assert can_assign_directly(UserRole.CLIENT.value) is False


class TestValidationFunctions:
    """Test permission validation functions"""
    
    def test_validate_application_creation_permission_success(self):
        """Test successful application creation validation"""
        # Should not raise exception
        validate_application_creation_permission(UserRole.MANAGER.value, ApplicationType.CONNECTION_REQUEST.value)
        validate_application_creation_permission(UserRole.CONTROLLER.value, ApplicationType.TECHNICAL_SERVICE.value)
    
    def test_validate_application_creation_permission_failure(self):
        """Test failed application creation validation"""
        with pytest.raises(ApplicationCreationPermissionError) as exc_info:
            validate_application_creation_permission(UserRole.JUNIOR_MANAGER.value, ApplicationType.TECHNICAL_SERVICE.value)
        
        assert exc_info.value.role == UserRole.JUNIOR_MANAGER.value
        assert exc_info.value.application_type == ApplicationType.TECHNICAL_SERVICE.value
        assert "cannot create" in str(exc_info.value)
    
    def test_validate_client_selection_permission_success(self):
        """Test successful client selection validation"""
        # Should not raise exception
        validate_client_selection_permission(UserRole.MANAGER.value)
        validate_client_selection_permission(UserRole.CALL_CENTER.value)
    
    def test_validate_client_selection_permission_failure(self):
        """Test failed client selection validation"""
        with pytest.raises(ClientSelectionPermissionError) as exc_info:
            validate_client_selection_permission(UserRole.CLIENT.value)
        
        assert exc_info.value.role == UserRole.CLIENT.value
        assert "client selection" in str(exc_info.value)
    
    def test_validate_client_creation_permission_success(self):
        """Test successful client creation validation"""
        # Should not raise exception
        validate_client_creation_permission(UserRole.MANAGER.value)
        validate_client_creation_permission(UserRole.JUNIOR_MANAGER.value)
    
    def test_validate_client_creation_permission_failure(self):
        """Test failed client creation validation"""
        with pytest.raises(ClientSelectionPermissionError) as exc_info:
            validate_client_creation_permission(UserRole.TECHNICIAN.value)
        
        assert exc_info.value.role == UserRole.TECHNICIAN.value
        assert "client creation" in str(exc_info.value)
    
    def test_validate_daily_limit_success(self):
        """Test successful daily limit validation"""
        # Should not raise exception for roles without limits
        validate_daily_limit(UserRole.MANAGER.value, 1000)
        
        # Should not raise exception when under limit
        validate_daily_limit(UserRole.JUNIOR_MANAGER.value, 25)
        validate_daily_limit(UserRole.CALL_CENTER.value, 50)
    
    def test_validate_daily_limit_failure(self):
        """Test failed daily limit validation"""
        with pytest.raises(DailyLimitExceededError) as exc_info:
            validate_daily_limit(UserRole.JUNIOR_MANAGER.value, 50)
        
        assert exc_info.value.role == UserRole.JUNIOR_MANAGER.value
        assert exc_info.value.current_count == 50
        assert exc_info.value.limit == 50
        assert "exceeded daily" in str(exc_info.value)
    
    def test_validate_daily_limit_at_limit(self):
        """Test daily limit validation at exact limit"""
        with pytest.raises(DailyLimitExceededError):
            validate_daily_limit(UserRole.CALL_CENTER.value, 100)
    
    def test_validate_comprehensive_permissions_success(self):
        """Test successful comprehensive validation"""
        # Should not raise exception
        validate_comprehensive_permissions(
            role=UserRole.MANAGER.value,
            application_type=ApplicationType.CONNECTION_REQUEST.value,
            needs_client_selection=True,
            needs_client_creation=True,
            current_daily_count=10
        )
    
    def test_validate_comprehensive_permissions_failure(self):
        """Test failed comprehensive validation"""
        with pytest.raises(ApplicationCreationPermissionError):
            validate_comprehensive_permissions(
                role=UserRole.JUNIOR_MANAGER.value,
                application_type=ApplicationType.TECHNICAL_SERVICE.value,
                needs_client_selection=True,
                needs_client_creation=False,
                current_daily_count=10
            )


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_get_available_application_types(self):
        """Test getting available application types for roles"""
        # Manager can create both types
        manager_types = get_available_application_types(UserRole.MANAGER.value)
        assert ApplicationType.CONNECTION_REQUEST.value in manager_types
        assert ApplicationType.TECHNICAL_SERVICE.value in manager_types
        assert len(manager_types) == 2
        
        # Junior Manager can only create connection requests
        junior_types = get_available_application_types(UserRole.JUNIOR_MANAGER.value)
        assert ApplicationType.CONNECTION_REQUEST.value in junior_types
        assert ApplicationType.TECHNICAL_SERVICE.value not in junior_types
        assert len(junior_types) == 1
        
        # Client cannot create any applications
        client_types = get_available_application_types(UserRole.CLIENT.value)
        assert len(client_types) == 0
    
    def test_get_staff_roles_with_application_creation(self):
        """Test getting staff roles that can create applications"""
        staff_roles = get_staff_roles_with_application_creation()
        
        assert UserRole.MANAGER.value in staff_roles
        assert UserRole.JUNIOR_MANAGER.value in staff_roles
        assert UserRole.CONTROLLER.value in staff_roles
        assert UserRole.CALL_CENTER.value in staff_roles
        assert UserRole.ADMIN.value in staff_roles
        
        assert UserRole.CLIENT.value not in staff_roles
        assert UserRole.TECHNICIAN.value not in staff_roles
        assert UserRole.WAREHOUSE.value not in staff_roles
    
    def test_get_notification_level(self):
        """Test getting notification levels for roles"""
        assert get_notification_level(UserRole.MANAGER.value) == "high"
        assert get_notification_level(UserRole.JUNIOR_MANAGER.value) == "medium"
        assert get_notification_level(UserRole.CONTROLLER.value) == "high"
        assert get_notification_level(UserRole.CALL_CENTER.value) == "medium"
        assert get_notification_level("invalid_role") == "low"
    
    def test_requires_approval(self):
        """Test approval requirements for roles"""
        # Staff roles don't require approval
        assert requires_approval(UserRole.MANAGER.value) is False
        assert requires_approval(UserRole.JUNIOR_MANAGER.value) is False
        assert requires_approval(UserRole.CONTROLLER.value) is False
        assert requires_approval(UserRole.CALL_CENTER.value) is False
        
        # Unknown roles require approval by default
        assert requires_approval("invalid_role") is True
    
    def test_is_staff_role(self):
        """Test staff role identification"""
        assert is_staff_role(UserRole.MANAGER.value) is True
        assert is_staff_role(UserRole.JUNIOR_MANAGER.value) is True
        assert is_staff_role(UserRole.CONTROLLER.value) is True
        assert is_staff_role(UserRole.CALL_CENTER.value) is True
        
        assert is_staff_role(UserRole.CLIENT.value) is False
        assert is_staff_role(UserRole.TECHNICIAN.value) is False
        assert is_staff_role(UserRole.WAREHOUSE.value) is False
    
    def test_get_role_hierarchy_level(self):
        """Test role hierarchy levels"""
        assert get_role_hierarchy_level(UserRole.ADMIN.value) == 100
        assert get_role_hierarchy_level(UserRole.MANAGER.value) == 80
        assert get_role_hierarchy_level(UserRole.CONTROLLER.value) == 70
        assert get_role_hierarchy_level(UserRole.JUNIOR_MANAGER.value) == 60
        assert get_role_hierarchy_level(UserRole.CALL_CENTER.value) == 50
        assert get_role_hierarchy_level(UserRole.CLIENT.value) == 10
        assert get_role_hierarchy_level(UserRole.BLOCKED.value) == 0
        assert get_role_hierarchy_level("invalid_role") == 0
    
    def test_can_manage_role(self):
        """Test role management permissions"""
        # Manager can manage lower roles
        assert can_manage_role(UserRole.MANAGER.value, UserRole.JUNIOR_MANAGER.value) is True
        assert can_manage_role(UserRole.MANAGER.value, UserRole.TECHNICIAN.value) is True
        assert can_manage_role(UserRole.MANAGER.value, UserRole.CLIENT.value) is True
        
        # Manager cannot manage equal or higher roles
        assert can_manage_role(UserRole.MANAGER.value, UserRole.MANAGER.value) is False
        assert can_manage_role(UserRole.MANAGER.value, UserRole.ADMIN.value) is False
        
        # Lower roles cannot manage higher roles
        assert can_manage_role(UserRole.TECHNICIAN.value, UserRole.MANAGER.value) is False
    
    def test_get_role_capabilities_summary(self):
        """Test role capabilities summary"""
        # Test valid role
        summary = get_role_capabilities_summary(UserRole.MANAGER.value)
        
        assert summary['role'] == UserRole.MANAGER.value
        assert summary['can_create_applications'] is True
        assert len(summary['available_application_types']) == 2
        assert summary['can_select_client'] is True
        assert summary['can_create_client'] is True
        assert summary['can_assign_directly'] is True
        assert summary['notification_level'] == "high"
        assert summary['daily_limit'] is None
        assert summary['requires_approval'] is False
        assert 'permissions' in summary
        
        # Test invalid role
        invalid_summary = get_role_capabilities_summary("invalid_role")
        assert invalid_summary['role'] == "invalid_role"
        assert invalid_summary['can_create_applications'] is False
        assert len(invalid_summary['available_application_types']) == 0


class TestExceptionClasses:
    """Test custom exception classes"""
    
    def test_role_permission_error(self):
        """Test base RolePermissionError"""
        error = RolePermissionError("manager", "test_action")
        
        assert error.role == "manager"
        assert error.action == "test_action"
        assert "manager" in str(error)
        assert "test_action" in str(error)
    
    def test_role_permission_error_custom_message(self):
        """Test RolePermissionError with custom message"""
        custom_message = "Custom error message"
        error = RolePermissionError("manager", "test_action", custom_message)
        
        assert error.message == custom_message
        assert str(error) == custom_message
    
    def test_application_creation_permission_error(self):
        """Test ApplicationCreationPermissionError"""
        error = ApplicationCreationPermissionError("junior_manager", "technical_service")
        
        assert error.role == "junior_manager"
        assert error.application_type == "technical_service"
        assert "junior_manager" in str(error)
        assert "technical_service" in str(error)
        assert "cannot create" in str(error)
    
    def test_client_selection_permission_error(self):
        """Test ClientSelectionPermissionError"""
        error = ClientSelectionPermissionError("client", "selection")
        
        assert error.role == "client"
        assert "client" in str(error)
        assert "selection" in str(error)
    
    def test_daily_limit_exceeded_error(self):
        """Test DailyLimitExceededError"""
        error = DailyLimitExceededError("junior_manager", 50, 50)
        
        assert error.role == "junior_manager"
        assert error.current_count == 50
        assert error.limit == 50
        assert "exceeded daily" in str(error)
        assert "50/50" in str(error)


class TestConstants:
    """Test module constants"""
    
    def test_staff_roles_constant(self):
        """Test STAFF_ROLES constant"""
        assert isinstance(STAFF_ROLES, list)
        assert len(STAFF_ROLES) > 0
        assert UserRole.MANAGER.value in STAFF_ROLES
        assert UserRole.CLIENT.value not in STAFF_ROLES
    
    def test_application_types_constant(self):
        """Test APPLICATION_TYPES constant"""
        assert isinstance(APPLICATION_TYPES, list)
        assert len(APPLICATION_TYPES) == 2
        assert ApplicationType.CONNECTION_REQUEST.value in APPLICATION_TYPES
        assert ApplicationType.TECHNICAL_SERVICE.value in APPLICATION_TYPES


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_role_string(self):
        """Test empty role string handling"""
        assert can_create_application("", ApplicationType.CONNECTION_REQUEST.value) is False
        assert can_select_client("") is False
        assert get_notification_level("") == "low"
    
    def test_none_role_handling(self):
        """Test None role handling"""
        with pytest.raises((ValueError, TypeError)):
            get_role_permissions(None)
    
    def test_case_sensitivity(self):
        """Test case sensitivity of role names"""
        # Role names should be case sensitive
        assert can_create_application("MANAGER", ApplicationType.CONNECTION_REQUEST.value) is False
        assert can_create_application("Manager", ApplicationType.CONNECTION_REQUEST.value) is False
    
    def test_zero_daily_limit(self):
        """Test zero daily limit handling"""
        # Test with current count of 0 against limit of 0
        with pytest.raises(DailyLimitExceededError):
            validate_daily_limit("test_role", 0)  # Will use unknown role logic
    
    def test_negative_daily_count(self):
        """Test negative daily count handling"""
        # Should not raise exception for negative counts (invalid but handled gracefully)
        validate_daily_limit(UserRole.MANAGER.value, -1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])