"""
Comprehensive form validation for staff application creation.

This module provides validation for staff-entered client data and application details,
with consistent error messaging across all roles and security validation.
"""

import re
import html
import unicodedata
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum

from utils.validators import (
    ValidationError, StringValidator, PhoneValidator, EmailValidator,
    IntegerValidator, FloatValidator, ChoiceValidator, sanitize_input
)
from utils.role_permissions import get_role_permissions, ApplicationType
from utils.form_error_messages import FormErrorMessages, ErrorKeys, WarningKeys
from utils.logger import setup_module_logger

logger = setup_module_logger("staff_form_validation")


class ValidationSeverity(Enum):
    """Validation error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of form validation"""
    is_valid: bool
    validated_data: Optional[Dict[str, Any]] = None
    errors: Dict[str, List[str]] = None
    warnings: Dict[str, List[str]] = None
    field_errors: Dict[str, str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = {}
        if self.warnings is None:
            self.warnings = {}
        if self.field_errors is None:
            self.field_errors = {}
    
    def add_error(self, field: str, message: str, severity: ValidationSeverity = ValidationSeverity.ERROR):
        """Add validation error"""
        if severity == ValidationSeverity.ERROR or severity == ValidationSeverity.CRITICAL:
            if field not in self.errors:
                self.errors[field] = []
            self.errors[field].append(message)
            self.field_errors[field] = message
            self.is_valid = False
        elif severity == ValidationSeverity.WARNING:
            if field not in self.warnings:
                self.warnings[field] = []
            self.warnings[field].append(message)
    
    def has_errors(self) -> bool:
        """Check if validation has errors"""
        return bool(self.errors)
    
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return bool(self.warnings)
    
    def get_error_summary(self) -> str:
        """Get formatted error summary"""
        if not self.errors:
            return ""
        
        error_messages = []
        for field, messages in self.errors.items():
            for message in messages:
                error_messages.append(f"{field}: {message}")
        
        return "; ".join(error_messages)
    
    def get_localized_errors(self, language: str = 'uz') -> Dict[str, List[str]]:
        """Get localized error messages"""
        return self._localize_messages(self.errors, language)
    
    def get_localized_warnings(self, language: str = 'uz') -> Dict[str, List[str]]:
        """Get localized warning messages"""
        return self._localize_messages(self.warnings, language)
    
    def _localize_messages(self, messages: Dict[str, List[str]], language: str) -> Dict[str, List[str]]:
        """Localize validation messages"""
        # This would integrate with the existing localization system
        # For now, return the original messages
        return messages


class SecurityValidator:
    """Security validation for user inputs"""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'<iframe[^>]*>',  # Iframes
        r'<object[^>]*>',  # Objects
        r'<embed[^>]*>',  # Embeds
        r'<link[^>]*>',  # Links
        r'<meta[^>]*>',  # Meta tags
        r'<style[^>]*>.*?</style>',  # Style tags
        r'expression\s*\(',  # CSS expressions
        r'url\s*\(',  # CSS URLs
        r'@import',  # CSS imports
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\b(OR|AND)\s+[\'"][^\'"]*[\'"])',
        r'(--|#|/\*|\*/)',
        r'(\bxp_cmdshell\b)',
        r'(\bsp_executesql\b)',
    ]
    
    @classmethod
    def validate_input_security(cls, value: str, field_name: str) -> Tuple[bool, List[str]]:
        """
        Validate input for security threats.
        
        Args:
            value: Input value to validate
            field_name: Name of the field being validated
            
        Returns:
            Tuple of (is_safe, list_of_threats_found)
        """
        if not isinstance(value, str):
            return True, []
        
        threats = []
        value_lower = value.lower()
        
        # Check for XSS patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE | re.DOTALL):
                threats.append(f"Potential XSS attack detected in {field_name}")
                break
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                threats.append(f"Potential SQL injection detected in {field_name}")
                break
        
        # Check for excessive length (potential DoS)
        if len(value) > 10000:
            threats.append(f"Input too long in {field_name} (potential DoS)")
        
        # Check for suspicious Unicode characters
        if cls._has_suspicious_unicode(value):
            threats.append(f"Suspicious Unicode characters in {field_name}")
        
        return len(threats) == 0, threats
    
    @classmethod
    def _has_suspicious_unicode(cls, value: str) -> bool:
        """Check for suspicious Unicode characters"""
        suspicious_categories = ['Cc', 'Cf', 'Co', 'Cs']  # Control characters
        
        for char in value:
            if unicodedata.category(char) in suspicious_categories:
                # Allow common control characters
                if char not in ['\n', '\r', '\t']:
                    return True
        
        return False
    
    @classmethod
    def sanitize_input(cls, value: str, preserve_newlines: bool = False) -> str:
        """
        Sanitize input by removing dangerous content.
        
        Args:
            value: Input value to sanitize
            preserve_newlines: Whether to preserve newline characters
            
        Returns:
            Sanitized input
        """
        if not isinstance(value, str):
            return str(value)
        
        # HTML escape
        sanitized = html.escape(value, quote=True)
        
        # Remove dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Normalize Unicode
        sanitized = unicodedata.normalize('NFKC', sanitized)
        
        # Remove control characters except allowed ones
        allowed_chars = ['\n', '\r', '\t'] if preserve_newlines else ['\t']
        sanitized = ''.join(
            char for char in sanitized 
            if unicodedata.category(char) not in ['Cc', 'Cf', 'Co', 'Cs'] 
            or char in allowed_chars
        )
        
        # Normalize whitespace
        if not preserve_newlines:
            sanitized = ' '.join(sanitized.split())
        
        return sanitized.strip()


class ClientDataValidator:
    """Validator for client data entered by staff"""
    
    def __init__(self, creator_role: str, language: str = 'uz'):
        self.creator_role = creator_role
        self.language = language
        self.permissions = get_role_permissions(creator_role)
    
    def validate_client_data(self, client_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete client data.
        
        Args:
            client_data: Dictionary containing client information
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True, validated_data={})
        
        try:
            # Validate required fields
            self._validate_required_fields(client_data, result)
            
            if result.has_errors():
                return result
            
            # Validate individual fields
            self._validate_phone_number(client_data.get('phone', ''), result)
            self._validate_full_name(client_data.get('full_name', ''), result)
            self._validate_address(client_data.get('address', ''), result)
            self._validate_email(client_data.get('email', ''), result)
            self._validate_additional_info(client_data.get('additional_info', ''), result)
            
            # Security validation
            self._validate_security(client_data, result)
            
            # Role-specific validation
            self._validate_role_permissions(client_data, result)
            
            if not result.has_errors():
                result.validated_data = self._build_validated_client_data(client_data)
            
        except Exception as e:
            logger.error(f"Error validating client data: {e}", exc_info=True)
            result.add_error('general', f"Validation error: {str(e)}")
        
        return result
    
    def _validate_required_fields(self, client_data: Dict[str, Any], result: ValidationResult):
        """Validate required fields are present"""
        required_fields = ['phone', 'full_name']
        
        for field in required_fields:
            value = client_data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                error_msg = self._get_localized_error('required_field', field)
                result.add_error(field, error_msg)
    
    def _validate_phone_number(self, phone: str, result: ValidationResult):
        """Validate phone number format and security"""
        if not phone:
            return
        
        try:
            # Security check
            is_safe, threats = SecurityValidator.validate_input_security(phone, 'phone')
            if not is_safe:
                for threat in threats:
                    result.add_error('phone', threat, ValidationSeverity.CRITICAL)
                return
            
            # Sanitize input
            sanitized_phone = SecurityValidator.sanitize_input(phone)
            
            # Use existing phone validator
            phone_validator = PhoneValidator(country_code="UZ")
            validated_phone = phone_validator.validate(sanitized_phone, 'phone')
            
            # Additional Uzbek-specific validation
            if not self._is_valid_uzbek_phone(validated_phone):
                result.add_error('phone', self._get_localized_error('invalid_uzbek_phone'))
            
        except ValidationError as e:
            result.add_error('phone', str(e))
        except Exception as e:
            logger.error(f"Phone validation error: {e}")
            result.add_error('phone', self._get_localized_error('phone_validation_error'))
    
    def _validate_full_name(self, full_name: str, result: ValidationResult):
        """Validate full name format and content"""
        if not full_name:
            return
        
        try:
            # Security check
            is_safe, threats = SecurityValidator.validate_input_security(full_name, 'full_name')
            if not is_safe:
                for threat in threats:
                    result.add_error('full_name', threat, ValidationSeverity.CRITICAL)
                return
            
            # Sanitize input
            sanitized_name = SecurityValidator.sanitize_input(full_name)
            
            # Length validation
            if len(sanitized_name) < 2:
                result.add_error('full_name', self._get_localized_error('name_too_short'))
            elif len(sanitized_name) > 100:
                result.add_error('full_name', self._get_localized_error('name_too_long'))
            
            # Character validation (allow letters, spaces, hyphens, apostrophes)
            if not re.match(r"^[a-zA-ZА-Яа-яЁёўғқҳ\s\-'\.]+$", sanitized_name):
                result.add_error('full_name', self._get_localized_error('invalid_name_characters'))
            
            # Check for reasonable name structure
            name_parts = sanitized_name.strip().split()
            if len(name_parts) < 2:
                result.add_error('full_name', self._get_localized_error('name_single_word'), ValidationSeverity.WARNING)
            elif len(name_parts) > 5:
                result.add_error('full_name', self._get_localized_error('name_too_many_parts'), ValidationSeverity.WARNING)
            
        except Exception as e:
            logger.error(f"Name validation error: {e}")
            result.add_error('full_name', self._get_localized_error('name_validation_error'))
    
    def _validate_address(self, address: str, result: ValidationResult):
        """Validate address format and content"""
        if not address:
            return  # Address is optional
        
        try:
            # Security check
            is_safe, threats = SecurityValidator.validate_input_security(address, 'address')
            if not is_safe:
                for threat in threats:
                    result.add_error('address', threat, ValidationSeverity.CRITICAL)
                return
            
            # Sanitize input
            sanitized_address = SecurityValidator.sanitize_input(address, preserve_newlines=True)
            
            # Length validation
            if len(sanitized_address) < 5:
                result.add_error('address', self._get_localized_error('address_too_short'))
            elif len(sanitized_address) > 500:
                result.add_error('address', self._get_localized_error('address_too_long'))
            
            # Basic structure validation
            if len(sanitized_address.split()) < 2:
                result.add_error('address', self._get_localized_error('address_incomplete'), ValidationSeverity.WARNING)
            
        except Exception as e:
            logger.error(f"Address validation error: {e}")
            result.add_error('address', self._get_localized_error('address_validation_error'))
    
    def _validate_email(self, email: str, result: ValidationResult):
        """Validate email format if provided"""
        if not email:
            return  # Email is optional
        
        try:
            # Security check
            is_safe, threats = SecurityValidator.validate_input_security(email, 'email')
            if not is_safe:
                for threat in threats:
                    result.add_error('email', threat, ValidationSeverity.CRITICAL)
                return
            
            # Sanitize input
            sanitized_email = SecurityValidator.sanitize_input(email)
            
            # Use existing email validator
            email_validator = EmailValidator()
            validated_email = email_validator.validate(sanitized_email, 'email')
            
        except ValidationError as e:
            result.add_error('email', str(e))
        except Exception as e:
            logger.error(f"Email validation error: {e}")
            result.add_error('email', self._get_localized_error('email_validation_error'))
    
    def _validate_additional_info(self, additional_info: str, result: ValidationResult):
        """Validate additional information field"""
        if not additional_info:
            return  # Additional info is optional
        
        try:
            # Security check
            is_safe, threats = SecurityValidator.validate_input_security(additional_info, 'additional_info')
            if not is_safe:
                for threat in threats:
                    result.add_error('additional_info', threat, ValidationSeverity.CRITICAL)
                return
            
            # Sanitize input
            sanitized_info = SecurityValidator.sanitize_input(additional_info, preserve_newlines=True)
            
            # Length validation
            if len(sanitized_info) > 1000:
                result.add_error('additional_info', self._get_localized_error('additional_info_too_long'))
            
        except Exception as e:
            logger.error(f"Additional info validation error: {e}")
            result.add_error('additional_info', self._get_localized_error('additional_info_validation_error'))
    
    def _validate_security(self, client_data: Dict[str, Any], result: ValidationResult):
        """Perform comprehensive security validation"""
        for field_name, value in client_data.items():
            if isinstance(value, str) and value:
                is_safe, threats = SecurityValidator.validate_input_security(value, field_name)
                if not is_safe:
                    for threat in threats:
                        result.add_error(field_name, threat, ValidationSeverity.CRITICAL)
    
    def _validate_role_permissions(self, client_data: Dict[str, Any], result: ValidationResult):
        """Validate role-specific permissions for client data"""
        if not self.permissions.can_select_client:
            result.add_error('general', self._get_localized_error('no_client_selection_permission'))
        
        # Check if creating new client is allowed
        if client_data.get('is_new_client', False) and not self.permissions.can_create_client:
            result.add_error('general', self._get_localized_error('no_client_creation_permission'))
    
    def _build_validated_client_data(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build validated and sanitized client data"""
        validated = {}
        
        # Required fields
        if client_data.get('phone'):
            phone_validator = PhoneValidator(country_code="UZ")
            validated['phone'] = phone_validator.validate(
                SecurityValidator.sanitize_input(client_data['phone']), 'phone'
            )
        
        if client_data.get('full_name'):
            validated['full_name'] = SecurityValidator.sanitize_input(client_data['full_name'])
        
        # Optional fields
        if client_data.get('address'):
            validated['address'] = SecurityValidator.sanitize_input(
                client_data['address'], preserve_newlines=True
            )
        
        if client_data.get('email'):
            email_validator = EmailValidator()
            validated['email'] = email_validator.validate(
                SecurityValidator.sanitize_input(client_data['email']), 'email'
            )
        
        if client_data.get('additional_info'):
            validated['additional_info'] = SecurityValidator.sanitize_input(
                client_data['additional_info'], preserve_newlines=True
            )
        
        # Metadata
        validated['validated_at'] = datetime.now()
        validated['validated_by_role'] = self.creator_role
        
        return validated
    
    def _is_valid_uzbek_phone(self, phone: str) -> bool:
        """Validate Uzbek phone number format"""
        if not phone.startswith('+998'):
            return False
        
        # Remove country code and check length
        number = phone[4:]  # Remove +998
        
        # Valid Uzbek mobile operators
        valid_prefixes = ['90', '91', '93', '94', '95', '97', '98', '99', '33', '88']
        
        if len(number) == 9:
            prefix = number[:2]
            return prefix in valid_prefixes
        
        return False
    
    def _get_localized_error(self, error_key: str, field: str = None) -> str:
        """Get localized error message"""
        if field:
            field_name = FormErrorMessages.get_field_name(field, self.language)
            return FormErrorMessages.get_message(error_key, self.language, field=field_name)
        else:
            return FormErrorMessages.get_message(error_key, self.language)


class ApplicationDataValidator:
    """Validator for application data entered by staff"""
    
    def __init__(self, creator_role: str, application_type: str, language: str = 'uz'):
        self.creator_role = creator_role
        self.application_type = application_type
        self.language = language
        self.permissions = get_role_permissions(creator_role)
    
    def validate_application_data(self, application_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete application data.
        
        Args:
            application_data: Dictionary containing application information
            
        Returns:
            ValidationResult with validation status and errors
        """
        result = ValidationResult(is_valid=True, validated_data={})
        
        try:
            # Validate required fields
            self._validate_required_fields(application_data, result)
            
            if result.has_errors():
                return result
            
            # Validate common fields
            self._validate_description(application_data.get('description', ''), result)
            self._validate_location(application_data.get('location', ''), result)
            self._validate_priority(application_data.get('priority', ''), result)
            self._validate_additional_notes(application_data.get('additional_notes', ''), result)
            
            # Application type specific validation
            if self.application_type == ApplicationType.TECHNICAL_SERVICE.value:
                self._validate_technical_service_fields(application_data, result)
            elif self.application_type == ApplicationType.CONNECTION_REQUEST.value:
                self._validate_connection_request_fields(application_data, result)
            
            # Security validation
            self._validate_security(application_data, result)
            
            # Role-specific validation
            self._validate_role_permissions(application_data, result)
            
            if not result.has_errors():
                result.validated_data = self._build_validated_application_data(application_data)
            
        except Exception as e:
            logger.error(f"Error validating application data: {e}", exc_info=True)
            result.add_error('general', f"Validation error: {str(e)}")
        
        return result
    
    def _validate_required_fields(self, application_data: Dict[str, Any], result: ValidationResult):
        """Validate required fields are present"""
        required_fields = ['description', 'location']
        
        for field in required_fields:
            value = application_data.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                error_msg = self._get_localized_error('required_field', field)
                result.add_error(field, error_msg)
    
    def _validate_description(self, description: str, result: ValidationResult):
        """Validate application description"""
        if not description:
            return
        
        try:
            # Security check
            is_safe, threats = SecurityValidator.validate_input_security(description, 'description')
            if not is_safe:
                for threat in threats:
                    result.add_error('description', threat, ValidationSeverity.CRITICAL)
                return
            
            # Sanitize input
            sanitized_description = SecurityValidator.sanitize_input(description, preserve_newlines=True)
            
            # Length validation
            if len(sanitized_description) < 10:
                result.add_error('description', self._get_localized_error('description_too_short'))
            elif len(sanitized_description) > 2000:
                result.add_error('description', self._get_localized_error('description_too_long'))
            
            # Content validation
            if len(sanitized_description.split()) < 3:
                result.add_error('description', self._get_localized_error('description_too_brief'), ValidationSeverity.WARNING)
            
        except Exception as e:
            logger.error(f"Description validation error: {e}")
            result.add_error('description', self._get_localized_error('description_validation_error'))
    
    def _validate_location(self, location: str, result: ValidationResult):
        """Validate service location"""
        if not location:
            return
        
        try:
            # Security check
            is_safe, threats = SecurityValidator.validate_input_security(location, 'location')
            if not is_safe:
                for threat in threats:
                    result.add_error('location', threat, ValidationSeverity.CRITICAL)
                return
            
            # Sanitize input
            sanitized_location = SecurityValidator.sanitize_input(location, preserve_newlines=True)
            
            # Length validation
            if len(sanitized_location) < 5:
                result.add_error('location', self._get_localized_error('location_too_short'))
            elif len(sanitized_location) > 500:
                result.add_error('location', self._get_localized_error('location_too_long'))
            
        except Exception as e:
            logger.error(f"Location validation error: {e}")
            result.add_error('location', self._get_localized_error('location_validation_error'))
    
    def _validate_priority(self, priority: str, result: ValidationResult):
        """Validate application priority"""
        if not priority:
            return  # Priority is optional, will use default
        
        try:
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if priority not in valid_priorities:
                result.add_error('priority', self._get_localized_error('invalid_priority'))
            
        except Exception as e:
            logger.error(f"Priority validation error: {e}")
            result.add_error('priority', self._get_localized_error('priority_validation_error'))
    
    def _validate_additional_notes(self, additional_notes: str, result: ValidationResult):
        """Validate additional notes field"""
        if not additional_notes:
            return  # Additional notes are optional
        
        try:
            # Security check
            is_safe, threats = SecurityValidator.validate_input_security(additional_notes, 'additional_notes')
            if not is_safe:
                for threat in threats:
                    result.add_error('additional_notes', threat, ValidationSeverity.CRITICAL)
                return
            
            # Sanitize input
            sanitized_notes = SecurityValidator.sanitize_input(additional_notes, preserve_newlines=True)
            
            # Length validation
            if len(sanitized_notes) > 1000:
                result.add_error('additional_notes', self._get_localized_error('additional_notes_too_long'))
            
        except Exception as e:
            logger.error(f"Additional notes validation error: {e}")
            result.add_error('additional_notes', self._get_localized_error('additional_notes_validation_error'))
    
    def _validate_technical_service_fields(self, application_data: Dict[str, Any], result: ValidationResult):
        """Validate technical service specific fields"""
        # Issue type is required for technical service
        issue_type = application_data.get('issue_type')
        if not issue_type:
            result.add_error('issue_type', self._get_localized_error('required_field', 'issue_type'))
        else:
            valid_issue_types = [
                'internet_connection', 'equipment_malfunction', 'signal_quality',
                'billing_issue', 'installation_request', 'maintenance', 'other'
            ]
            if issue_type not in valid_issue_types:
                result.add_error('issue_type', self._get_localized_error('invalid_issue_type'))
        
        # Validate equipment info if provided
        equipment_info = application_data.get('equipment_info')
        if equipment_info:
            if len(equipment_info) > 500:
                result.add_error('equipment_info', self._get_localized_error('equipment_info_too_long'))
    
    def _validate_connection_request_fields(self, application_data: Dict[str, Any], result: ValidationResult):
        """Validate connection request specific fields"""
        # Connection type validation
        connection_type = application_data.get('connection_type')
        if connection_type:
            valid_connection_types = ['fiber', 'cable', 'wireless', 'satellite']
            if connection_type not in valid_connection_types:
                result.add_error('connection_type', self._get_localized_error('invalid_connection_type'))
        
        # Speed requirement validation
        speed_requirement = application_data.get('speed_requirement')
        if speed_requirement:
            try:
                speed = int(speed_requirement)
                if speed < 1 or speed > 1000:
                    result.add_error('speed_requirement', self._get_localized_error('invalid_speed_requirement'))
            except (ValueError, TypeError):
                result.add_error('speed_requirement', self._get_localized_error('speed_requirement_not_number'))
    
    def _validate_security(self, application_data: Dict[str, Any], result: ValidationResult):
        """Perform comprehensive security validation"""
        for field_name, value in application_data.items():
            if isinstance(value, str) and value:
                is_safe, threats = SecurityValidator.validate_input_security(value, field_name)
                if not is_safe:
                    for threat in threats:
                        result.add_error(field_name, threat, ValidationSeverity.CRITICAL)
    
    def _validate_role_permissions(self, application_data: Dict[str, Any], result: ValidationResult):
        """Validate role-specific permissions for application creation"""
        # Check if role can create this application type
        if self.application_type == ApplicationType.CONNECTION_REQUEST.value:
            if not self.permissions.can_create_connection:
                result.add_error('general', self._get_localized_error('no_connection_creation_permission'))
        elif self.application_type == ApplicationType.TECHNICAL_SERVICE.value:
            if not self.permissions.can_create_technical:
                result.add_error('general', self._get_localized_error('no_technical_creation_permission'))
        
        # Check direct assignment permission
        if application_data.get('assign_to_technician') and not self.permissions.can_assign_directly:
            result.add_error('assign_to_technician', self._get_localized_error('no_direct_assignment_permission'))
    
    def _build_validated_application_data(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build validated and sanitized application data"""
        validated = {}
        
        # Required fields
        if application_data.get('description'):
            validated['description'] = SecurityValidator.sanitize_input(
                application_data['description'], preserve_newlines=True
            )
        
        if application_data.get('location'):
            validated['location'] = SecurityValidator.sanitize_input(
                application_data['location'], preserve_newlines=True
            )
        
        # Optional common fields
        if application_data.get('priority'):
            validated['priority'] = application_data['priority']
        else:
            validated['priority'] = 'medium'  # Default priority
        
        if application_data.get('additional_notes'):
            validated['additional_notes'] = SecurityValidator.sanitize_input(
                application_data['additional_notes'], preserve_newlines=True
            )
        
        # Application type specific fields
        if self.application_type == ApplicationType.TECHNICAL_SERVICE.value:
            if application_data.get('issue_type'):
                validated['issue_type'] = application_data['issue_type']
            if application_data.get('equipment_info'):
                validated['equipment_info'] = SecurityValidator.sanitize_input(
                    application_data['equipment_info']
                )
        elif self.application_type == ApplicationType.CONNECTION_REQUEST.value:
            if application_data.get('connection_type'):
                validated['connection_type'] = application_data['connection_type']
            if application_data.get('speed_requirement'):
                validated['speed_requirement'] = application_data['speed_requirement']
        
        # Metadata
        validated['validated_at'] = datetime.now()
        validated['validated_by_role'] = self.creator_role
        validated['application_type'] = self.application_type
        
        return validated
    
    def _get_localized_error(self, error_key: str, field: str = None) -> str:
        """Get localized error message"""
        if field:
            field_name = FormErrorMessages.get_field_name(field, self.language)
            return FormErrorMessages.get_message(error_key, self.language, field=field_name)
        else:
            return FormErrorMessages.get_message(error_key, self.language)


class ComprehensiveFormValidator:
    """Main validator that combines client and application data validation"""
    
    def __init__(self, creator_role: str, application_type: str, language: str = 'uz'):
        self.creator_role = creator_role
        self.application_type = application_type
        self.language = language
        
        self.client_validator = ClientDataValidator(creator_role, language)
        self.application_validator = ApplicationDataValidator(creator_role, application_type, language)
    
    def validate_complete_form(self, form_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete form data including client and application information.
        
        Args:
            form_data: Dictionary containing both client_data and application_data
            
        Returns:
            ValidationResult with comprehensive validation status
        """
        result = ValidationResult(is_valid=True, validated_data={})
        
        try:
            # Extract client and application data
            client_data = form_data.get('client_data', {})
            application_data = form_data.get('application_data', {})
            
            # Validate client data
            client_result = self.client_validator.validate_client_data(client_data)
            
            # Validate application data
            application_result = self.application_validator.validate_application_data(application_data)
            
            # Combine results
            result.is_valid = client_result.is_valid and application_result.is_valid
            
            # Merge errors
            for field, errors in client_result.errors.items():
                result.errors[f"client.{field}"] = errors
                for error in errors:
                    result.field_errors[f"client.{field}"] = error
            
            for field, errors in application_result.errors.items():
                result.errors[f"application.{field}"] = errors
                for error in errors:
                    result.field_errors[f"application.{field}"] = error
            
            # Merge warnings
            for field, warnings in client_result.warnings.items():
                result.warnings[f"client.{field}"] = warnings
            
            for field, warnings in application_result.warnings.items():
                result.warnings[f"application.{field}"] = warnings
            
            # Build validated data if no errors
            if result.is_valid:
                result.validated_data = {
                    'client_data': client_result.validated_data,
                    'application_data': application_result.validated_data,
                    'validation_metadata': {
                        'validated_at': datetime.now(),
                        'validated_by_role': self.creator_role,
                        'application_type': self.application_type,
                        'language': self.language
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in comprehensive form validation: {e}", exc_info=True)
            result.add_error('general', f"Form validation error: {str(e)}")
        
        return result
    
    def validate_form_step(self, step_name: str, step_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate individual form step.
        
        Args:
            step_name: Name of the form step (client_selection, application_details, etc.)
            step_data: Data for the specific step
            
        Returns:
            ValidationResult for the step
        """
        if step_name == 'client_data':
            return self.client_validator.validate_client_data(step_data)
        elif step_name == 'application_data':
            return self.application_validator.validate_application_data(step_data)
        else:
            result = ValidationResult(is_valid=False)
            result.add_error('general', f"Unknown form step: {step_name}")
            return result


# Utility functions for external use
def validate_staff_form(creator_role: str, application_type: str, form_data: Dict[str, Any], 
                       language: str = 'uz') -> ValidationResult:
    """
    Convenience function to validate complete staff form.
    
    Args:
        creator_role: Role of the staff member creating the application
        application_type: Type of application being created
        form_data: Complete form data
        language: Language for error messages
        
    Returns:
        ValidationResult with validation status and errors
    """
    validator = ComprehensiveFormValidator(creator_role, application_type, language)
    return validator.validate_complete_form(form_data)


def sanitize_form_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize all string fields in form data.
    
    Args:
        form_data: Form data to sanitize
        
    Returns:
        Sanitized form data
    """
    sanitized = {}
    
    for key, value in form_data.items():
        if isinstance(value, str):
            sanitized[key] = SecurityValidator.sanitize_input(value, preserve_newlines=True)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_form_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                SecurityValidator.sanitize_input(item, preserve_newlines=True) 
                if isinstance(item, str) else item 
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


def get_validation_schema(creator_role: str, application_type: str) -> Dict[str, Any]:
    """
    Get validation schema for a specific role and application type.
    
    Args:
        creator_role: Role of the staff member
        application_type: Type of application
        
    Returns:
        Dictionary describing validation requirements
    """
    permissions = get_role_permissions(creator_role)
    
    schema = {
        'client_data': {
            'required_fields': ['phone', 'full_name'],
            'optional_fields': ['address', 'email', 'additional_info'],
            'permissions': {
                'can_select_client': permissions.can_select_client,
                'can_create_client': permissions.can_create_client
            }
        },
        'application_data': {
            'required_fields': ['description', 'location'],
            'optional_fields': ['priority', 'additional_notes'],
            'permissions': {
                'can_create_connection': permissions.can_create_connection,
                'can_create_technical': permissions.can_create_technical,
                'can_assign_directly': permissions.can_assign_directly
            }
        }
    }
    
    # Add application type specific fields
    if application_type == ApplicationType.TECHNICAL_SERVICE.value:
        schema['application_data']['required_fields'].append('issue_type')
        schema['application_data']['optional_fields'].extend(['equipment_info'])
    elif application_type == ApplicationType.CONNECTION_REQUEST.value:
        schema['application_data']['optional_fields'].extend(['connection_type', 'speed_requirement'])
    
    return schema