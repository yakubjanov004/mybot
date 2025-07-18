"""
Unit tests for staff form validation system.

Tests comprehensive form validation for staff-entered client data and application details,
including security validation, localization, and role-based permissions.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from utils.validators import (
    SecurityValidator, ValidationResult, ValidationSeverity,
    validate_staff_form, InputValidator, ApplicationDataValidator
)
from utils.form_error_messages import FormErrorMessages, ErrorKeys, WarningKeys
from utils.role_permissions import ApplicationType, UserRole


class TestSecurityValidator:
    """Test security validation functionality"""
    
    def test_validate_input_security_safe_input(self):
        """Test security validation with safe input"""
        safe_input = "This is a normal text input"
        is_safe, threats = SecurityValidator.validate_input_security(safe_input, "test_field")
        
        assert is_safe is True
        assert len(threats) == 0
    
    def test_validate_input_security_xss_attack(self):
        """Test security validation detects XSS attacks"""
        xss_input = "<script>alert('xss')</script>"
        is_safe, threats = SecurityValidator.validate_input_security(xss_input, "test_field")
        
        assert is_safe is False
        assert len(threats) > 0
        assert any("XSS" in threat for threat in threats)
    
    def test_validate_input_security_sql_injection(self):
        """Test security validation detects SQL injection"""
        sql_input = "'; DROP TABLE users; --"
        is_safe, threats = SecurityValidator.validate_input_security(sql_input, "test_field")
        
        assert is_safe is False
        assert len(threats) > 0
        assert any("SQL injection" in threat for threat in threats)
    
    def test_validate_input_security_excessive_length(self):
        """Test security validation detects excessive input length"""
        long_input = "a" * 15000
        is_safe, threats = SecurityValidator.validate_input_security(long_input, "test_field")
        
        assert is_safe is False
        assert len(threats) > 0
        assert any("too long" in threat for threat in threats)
    
    def test_sanitize_input_basic(self):
        """Test basic input sanitization"""
        input_text = "  Hello <script>alert('test')</script> World  "
        sanitized = SecurityValidator.sanitize_input(input_text)
        
        assert "<script>" not in sanitized
        assert "Hello" in sanitized
        assert "World" in sanitized
        assert sanitized.strip() == sanitized
    
    def test_sanitize_input_preserve_newlines(self):
        """Test input sanitization with newline preservation"""
        input_text = "Line 1\nLine 2\rLine 3"
        sanitized = SecurityValidator.sanitize_input(input_text, preserve_newlines=True)
        
        assert "\n" in sanitized or "Line 1" in sanitized
        assert "Line 2" in sanitized
        assert "Line 3" in sanitized


class TestClientDataValidator:
    """Test client data validation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = ClientDataValidator("manager", "uz")
        self.valid_client_data = {
            "phone": "+998901234567",
            "full_name": "John Doe",
            "address": "123 Main Street, Tashkent",
            "email": "john.doe@example.com",
            "additional_info": "Regular customer"
        }
    
    def test_validate_client_data_valid(self):
        """Test validation with valid client data"""
        result = self.validator.validate_client_data(self.valid_client_data)
        
        assert result.is_valid is True
        assert not result.has_errors()
        assert result.validated_data is not None
        assert "phone" in result.validated_data
        assert "full_name" in result.validated_data
    
    def test_validate_client_data_missing_required_fields(self):
        """Test validation with missing required fields"""
        invalid_data = {"address": "Some address"}
        result = self.validator.validate_client_data(invalid_data)
        
        assert result.is_valid is False
        assert result.has_errors()
        assert "phone" in result.errors
        assert "full_name" in result.errors
    
    def test_validate_phone_number_valid_uzbek(self):
        """Test phone number validation with valid Uzbek number"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_phone_number("+998901234567", result)
        
        assert not result.has_errors()
    
    def test_validate_phone_number_invalid_format(self):
        """Test phone number validation with invalid format"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_phone_number("123456", result)
        
        assert result.has_errors()
        assert "phone" in result.errors
    
    def test_validate_full_name_valid(self):
        """Test full name validation with valid name"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_full_name("John Doe", result)
        
        assert not result.has_errors()
    
    def test_validate_full_name_too_short(self):
        """Test full name validation with too short name"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_full_name("A", result)
        
        assert result.has_errors()
        assert "full_name" in result.errors
    
    def test_validate_full_name_too_long(self):
        """Test full name validation with too long name"""
        result = ValidationResult(is_valid=True)
        long_name = "A" * 150
        self.validator._validate_full_name(long_name, result)
        
        assert result.has_errors()
        assert "full_name" in result.errors
    
    def test_validate_full_name_single_word_warning(self):
        """Test full name validation generates warning for single word"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_full_name("John", result)
        
        assert not result.has_errors()  # Should not be an error
        assert result.has_warnings()   # Should be a warning
        assert "full_name" in result.warnings
    
    def test_validate_email_valid(self):
        """Test email validation with valid email"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_email("test@example.com", result)
        
        assert not result.has_errors()
    
    def test_validate_email_invalid_format(self):
        """Test email validation with invalid format"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_email("invalid-email", result)
        
        assert result.has_errors()
        assert "email" in result.errors
    
    def test_validate_address_valid(self):
        """Test address validation with valid address"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_address("123 Main Street, City", result)
        
        assert not result.has_errors()
    
    def test_validate_address_too_short(self):
        """Test address validation with too short address"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_address("123", result)
        
        assert result.has_errors()
        assert "address" in result.errors
    
    def test_security_validation_xss_in_client_data(self):
        """Test security validation detects XSS in client data"""
        malicious_data = {
            "phone": "+998901234567",
            "full_name": "<script>alert('xss')</script>",
            "address": "Normal address"
        }
        result = self.validator.validate_client_data(malicious_data)
        
        assert result.is_valid is False
        assert result.has_errors()
        assert "full_name" in result.errors
    
    def test_role_permissions_validation(self):
        """Test role-specific permission validation"""
        # Test with role that can't select clients
        validator = ClientDataValidator("client", "uz")  # Client role can't select clients
        result = validator.validate_client_data(self.valid_client_data)
        
        assert result.is_valid is False
        assert result.has_errors()
        assert "general" in result.errors


class TestApplicationDataValidator:
    """Test application data validation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = ApplicationDataValidator("manager", "connection_request", "uz")
        self.valid_application_data = {
            "description": "Need internet connection for new office",
            "location": "123 Business Street, Tashkent",
            "priority": "medium",
            "additional_notes": "Urgent setup required",
            "connection_type": "fiber",
            "speed_requirement": "100"
        }
    
    def test_validate_application_data_valid(self):
        """Test validation with valid application data"""
        result = self.validator.validate_application_data(self.valid_application_data)
        
        assert result.is_valid is True
        assert not result.has_errors()
        assert result.validated_data is not None
        assert "description" in result.validated_data
        assert "location" in result.validated_data
    
    def test_validate_application_data_missing_required_fields(self):
        """Test validation with missing required fields"""
        invalid_data = {"priority": "high"}
        result = self.validator.validate_application_data(invalid_data)
        
        assert result.is_valid is False
        assert result.has_errors()
        assert "description" in result.errors
        assert "location" in result.errors
    
    def test_validate_description_valid(self):
        """Test description validation with valid description"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_description("This is a detailed description of the issue", result)
        
        assert not result.has_errors()
    
    def test_validate_description_too_short(self):
        """Test description validation with too short description"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_description("Short", result)
        
        assert result.has_errors()
        assert "description" in result.errors
    
    def test_validate_description_too_long(self):
        """Test description validation with too long description"""
        result = ValidationResult(is_valid=True)
        long_description = "A" * 2500
        self.validator._validate_description(long_description, result)
        
        assert result.has_errors()
        assert "description" in result.errors
    
    def test_validate_description_brief_warning(self):
        """Test description validation generates warning for brief description"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_description("Short description", result)
        
        assert not result.has_errors()  # Should not be an error
        assert result.has_warnings()   # Should be a warning
        assert "description" in result.warnings
    
    def test_validate_location_valid(self):
        """Test location validation with valid location"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_location("123 Main Street, Tashkent", result)
        
        assert not result.has_errors()
    
    def test_validate_location_too_short(self):
        """Test location validation with too short location"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_location("123", result)
        
        assert result.has_errors()
        assert "location" in result.errors
    
    def test_validate_priority_valid(self):
        """Test priority validation with valid priority"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_priority("high", result)
        
        assert not result.has_errors()
    
    def test_validate_priority_invalid(self):
        """Test priority validation with invalid priority"""
        result = ValidationResult(is_valid=True)
        self.validator._validate_priority("invalid_priority", result)
        
        assert result.has_errors()
        assert "priority" in result.errors
    
    def test_validate_technical_service_fields(self):
        """Test technical service specific field validation"""
        tech_validator = ApplicationDataValidator("manager", "technical_service", "uz")
        
        # Test missing issue_type
        result = ValidationResult(is_valid=True)
        tech_validator._validate_technical_service_fields({}, result)
        
        assert result.has_errors()
        assert "issue_type" in result.errors
        
        # Test valid issue_type
        result = ValidationResult(is_valid=True)
        tech_validator._validate_technical_service_fields({"issue_type": "internet_connection"}, result)
        
        assert not result.has_errors()
    
    def test_validate_connection_request_fields(self):
        """Test connection request specific field validation"""
        conn_validator = ApplicationDataValidator("manager", "connection_request", "uz")
        
        # Test valid connection_type
        result = ValidationResult(is_valid=True)
        conn_validator._validate_connection_request_fields({"connection_type": "fiber"}, result)
        
        assert not result.has_errors()
        
        # Test invalid connection_type
        result = ValidationResult(is_valid=True)
        conn_validator._validate_connection_request_fields({"connection_type": "invalid"}, result)
        
        assert result.has_errors()
        assert "connection_type" in result.errors
    
    def test_security_validation_xss_in_application_data(self):
        """Test security validation detects XSS in application data"""
        malicious_data = {
            "description": "<script>alert('xss')</script>Need connection",
            "location": "123 Main Street",
            "priority": "high"
        }
        result = self.validator.validate_application_data(malicious_data)
        
        assert result.is_valid is False
        assert result.has_errors()
        assert "description" in result.errors
    
    def test_role_permissions_validation(self):
        """Test role-specific permission validation for application creation"""
        # Test junior manager trying to create technical service (not allowed)
        validator = ApplicationDataValidator("junior_manager", "technical_service", "uz")
        result = validator.validate_application_data(self.valid_application_data)
        
        assert result.is_valid is False
        assert result.has_errors()
        assert "general" in result.errors


class TestComprehensiveFormValidator:
    """Test comprehensive form validation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = ComprehensiveFormValidator("manager", "connection_request", "uz")
        self.valid_form_data = {
            "client_data": {
                "phone": "+998901234567",
                "full_name": "John Doe",
                "address": "123 Main Street, Tashkent"
            },
            "application_data": {
                "description": "Need internet connection for new office",
                "location": "123 Business Street, Tashkent",
                "priority": "medium"
            }
        }
    
    def test_validate_complete_form_valid(self):
        """Test comprehensive validation with valid form data"""
        result = self.validator.validate_complete_form(self.valid_form_data)
        
        assert result.is_valid is True
        assert not result.has_errors()
        assert result.validated_data is not None
        assert "client_data" in result.validated_data
        assert "application_data" in result.validated_data
        assert "validation_metadata" in result.validated_data
    
    def test_validate_complete_form_client_errors(self):
        """Test comprehensive validation with client data errors"""
        invalid_form_data = {
            "client_data": {
                "phone": "invalid_phone",
                "full_name": "A"  # Too short
            },
            "application_data": self.valid_form_data["application_data"]
        }
        result = self.validator.validate_complete_form(invalid_form_data)
        
        assert result.is_valid is False
        assert result.has_errors()
        assert any("client." in field for field in result.errors.keys())
    
    def test_validate_complete_form_application_errors(self):
        """Test comprehensive validation with application data errors"""
        invalid_form_data = {
            "client_data": self.valid_form_data["client_data"],
            "application_data": {
                "description": "Short",  # Too short
                "location": "123"  # Too short
            }
        }
        result = self.validator.validate_complete_form(invalid_form_data)
        
        assert result.is_valid is False
        assert result.has_errors()
        assert any("application." in field for field in result.errors.keys())
    
    def test_validate_form_step_client_data(self):
        """Test individual form step validation for client data"""
        result = self.validator.validate_form_step("client_data", self.valid_form_data["client_data"])
        
        assert result.is_valid is True
        assert not result.has_errors()
    
    def test_validate_form_step_application_data(self):
        """Test individual form step validation for application data"""
        result = self.validator.validate_form_step("application_data", self.valid_form_data["application_data"])
        
        assert result.is_valid is True
        assert not result.has_errors()
    
    def test_validate_form_step_unknown_step(self):
        """Test validation with unknown form step"""
        result = self.validator.validate_form_step("unknown_step", {})
        
        assert result.is_valid is False
        assert result.has_errors()
        assert "general" in result.errors


class TestValidationResult:
    """Test ValidationResult functionality"""
    
    def test_validation_result_initialization(self):
        """Test ValidationResult initialization"""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert result.errors == {}
        assert result.warnings == {}
        assert result.field_errors == {}
    
    def test_add_error(self):
        """Test adding errors to ValidationResult"""
        result = ValidationResult(is_valid=True)
        result.add_error("test_field", "Test error message")
        
        assert result.is_valid is False
        assert result.has_errors()
        assert "test_field" in result.errors
        assert "test_field" in result.field_errors
    
    def test_add_warning(self):
        """Test adding warnings to ValidationResult"""
        result = ValidationResult(is_valid=True)
        result.add_error("test_field", "Test warning", ValidationSeverity.WARNING)
        
        assert result.is_valid is True  # Warnings don't make result invalid
        assert result.has_warnings()
        assert "test_field" in result.warnings
    
    def test_get_error_summary(self):
        """Test error summary generation"""
        result = ValidationResult(is_valid=False)
        result.add_error("field1", "Error 1")
        result.add_error("field2", "Error 2")
        
        summary = result.get_error_summary()
        assert "field1: Error 1" in summary
        assert "field2: Error 2" in summary


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_validate_staff_form(self):
        """Test validate_staff_form utility function"""
        form_data = {
            "client_data": {
                "phone": "+998901234567",
                "full_name": "John Doe"
            },
            "application_data": {
                "description": "Need internet connection",
                "location": "123 Main Street"
            }
        }
        
        result = validate_staff_form("manager", "connection_request", form_data, "uz")
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
    
    def test_sanitize_form_data(self):
        """Test sanitize_form_data utility function"""
        form_data = {
            "text_field": "  <script>alert('test')</script>  Normal text  ",
            "nested_data": {
                "inner_field": "  Another text  "
            },
            "list_field": ["  Item 1  ", "  Item 2  "],
            "number_field": 123
        }
        
        sanitized = sanitize_form_data(form_data)
        
        assert "<script>" not in sanitized["text_field"]
        assert "Normal text" in sanitized["text_field"]
        assert sanitized["nested_data"]["inner_field"].strip() == sanitized["nested_data"]["inner_field"]
        assert all(item.strip() == item for item in sanitized["list_field"])
        assert sanitized["number_field"] == 123
    
    def test_get_validation_schema(self):
        """Test get_validation_schema utility function"""
        schema = get_validation_schema("manager", "connection_request")
        
        assert "client_data" in schema
        assert "application_data" in schema
        assert "required_fields" in schema["client_data"]
        assert "permissions" in schema["client_data"]
        assert "phone" in schema["client_data"]["required_fields"]
        assert "full_name" in schema["client_data"]["required_fields"]


class TestLocalization:
    """Test localization functionality"""
    
    def test_uzbek_localization(self):
        """Test Uzbek language localization"""
        validator = ClientDataValidator("manager", "uz")
        result = validator.validate_client_data({"phone": "", "full_name": ""})
        
        # Should have Uzbek error messages
        assert result.has_errors()
        # The actual error messages should be in Uzbek, but we can't easily test
        # the exact content without mocking the FormErrorMessages
    
    def test_russian_localization(self):
        """Test Russian language localization"""
        validator = ClientDataValidator("manager", "ru")
        result = validator.validate_client_data({"phone": "", "full_name": ""})
        
        # Should have Russian error messages
        assert result.has_errors()
        # The actual error messages should be in Russian
    
    def test_english_fallback(self):
        """Test English fallback localization"""
        validator = ClientDataValidator("manager", "en")
        result = validator.validate_client_data({"phone": "", "full_name": ""})
        
        # Should have English error messages
        assert result.has_errors()


class TestRoleSpecificValidation:
    """Test role-specific validation scenarios"""
    
    def test_manager_permissions(self):
        """Test manager role permissions"""
        validator = ComprehensiveFormValidator("manager", "technical_service", "uz")
        form_data = {
            "client_data": {"phone": "+998901234567", "full_name": "John Doe"},
            "application_data": {
                "description": "Technical issue description",
                "location": "Service location",
                "issue_type": "internet_connection"
            }
        }
        
        result = validator.validate_complete_form(form_data)
        assert result.is_valid is True
    
    def test_junior_manager_limitations(self):
        """Test junior manager role limitations"""
        validator = ComprehensiveFormValidator("junior_manager", "technical_service", "uz")
        form_data = {
            "client_data": {"phone": "+998901234567", "full_name": "John Doe"},
            "application_data": {
                "description": "Technical issue description",
                "location": "Service location",
                "issue_type": "internet_connection"
            }
        }
        
        result = validator.validate_complete_form(form_data)
        assert result.is_valid is False  # Junior manager can't create technical service
        assert result.has_errors()
    
    def test_call_center_permissions(self):
        """Test call center role permissions"""
        validator = ComprehensiveFormValidator("call_center", "connection_request", "uz")
        form_data = {
            "client_data": {"phone": "+998901234567", "full_name": "John Doe"},
            "application_data": {
                "description": "Connection request description",
                "location": "Service location"
            }
        }
        
        result = validator.validate_complete_form(form_data)
        assert result.is_valid is True
    
    def test_controller_permissions(self):
        """Test controller role permissions"""
        validator = ComprehensiveFormValidator("controller", "technical_service", "uz")
        form_data = {
            "client_data": {"phone": "+998901234567", "full_name": "John Doe"},
            "application_data": {
                "description": "Technical issue description",
                "location": "Service location",
                "issue_type": "equipment_malfunction"
            }
        }
        
        result = validator.validate_complete_form(form_data)
        assert result.is_valid is True


if __name__ == "__main__":
    pytest.main([__file__])