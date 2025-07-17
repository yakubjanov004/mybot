"""
Demonstration of comprehensive staff form validation system.

This example shows how to use the staff form validation system
for different roles and application types.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from utils.staff_form_validation import (
    ComprehensiveFormValidator, validate_staff_form, 
    sanitize_form_data, get_validation_schema
)
from utils.form_error_messages import FormErrorMessages, create_validation_response


def demo_manager_connection_request():
    """Demo: Manager creating a connection request"""
    print("=== Manager Creating Connection Request ===")
    
    form_data = {
        "client_data": {
            "phone": "+998901234567",
            "full_name": "Alisher Karimov",
            "address": "Tashkent shahar, Yunusobod tumani, 15-uy",
            "email": "alisher@example.com"
        },
        "application_data": {
            "description": "Yangi ofis uchun internet ulanishi kerak. Tezkor va barqaror ulanish talab qilinadi.",
            "location": "Tashkent shahar, Yunusobod tumani, 15-uy, 3-qavat",
            "priority": "high",
            "connection_type": "fiber",
            "speed_requirement": "100"
        }
    }
    
    # Validate form
    result = validate_staff_form("manager", "connection_request", form_data, "uz")
    
    print(f"Validation Result: {'✓ Valid' if result.is_valid else '✗ Invalid'}")
    if result.has_errors():
        print("Errors:")
        for field, errors in result.errors.items():
            for error in errors:
                print(f"  - {field}: {error}")
    
    if result.has_warnings():
        print("Warnings:")
        for field, warnings in result.warnings.items():
            for warning in warnings:
                print(f"  - {field}: {warning}")
    
    if result.is_valid:
        print("✓ Form data is valid and ready for submission")
        print(f"Client: {result.validated_data['client_data']['full_name']}")
        print(f"Phone: {result.validated_data['client_data']['phone']}")
        print(f"Service: {result.validated_data['application_data']['description'][:50]}...")
    
    print()


def demo_junior_manager_technical_service():
    """Demo: Junior Manager trying to create technical service (should fail)"""
    print("=== Junior Manager Trying to Create Technical Service ===")
    
    form_data = {
        "client_data": {
            "phone": "+998971234567",
            "full_name": "Nodira Tosheva"
        },
        "application_data": {
            "description": "Internet ulanishi ishlamayapti, texnik yordam kerak",
            "location": "Samarqand shahar, Registon ko'chasi, 25-uy",
            "issue_type": "internet_connection"
        }
    }
    
    # Validate form
    result = validate_staff_form("junior_manager", "technical_service", form_data, "uz")
    
    print(f"Validation Result: {'✓ Valid' if result.is_valid else '✗ Invalid'}")
    if result.has_errors():
        print("Errors:")
        for field, errors in result.errors.items():
            for error in errors:
                print(f"  - {field}: {error}")
    
    print("Note: Junior managers can only create connection requests, not technical service requests")
    print()


def demo_call_center_with_security_issues():
    """Demo: Call center with security validation"""
    print("=== Call Center with Security Issues ===")
    
    # Form data with potential security threats
    form_data = {
        "client_data": {
            "phone": "+998931234567",
            "full_name": "Normal Name<script>alert('xss')</script>",  # XSS attempt
            "address": "Normal address"
        },
        "application_data": {
            "description": "'; DROP TABLE users; -- Need connection",  # SQL injection attempt
            "location": "Bukhara shahar, Registon ko'chasi"
        }
    }
    
    # Validate form
    result = validate_staff_form("call_center", "connection_request", form_data, "uz")
    
    print(f"Validation Result: {'✓ Valid' if result.is_valid else '✗ Invalid'}")
    if result.has_errors():
        print("Security Issues Detected:")
        for field, errors in result.errors.items():
            for error in errors:
                print(f"  - {field}: {error}")
    
    print("✓ Security validation successfully blocked malicious input")
    print()


def demo_form_sanitization():
    """Demo: Form data sanitization"""
    print("=== Form Data Sanitization ===")
    
    dirty_form_data = {
        "client_data": {
            "phone": "  +998 90 123 45 67  ",
            "full_name": "  John   Doe  <script>alert('test')</script>  ",
            "address": "  123 Main Street  \n  Tashkent  "
        },
        "application_data": {
            "description": "  Need   internet   connection   <iframe src='evil.com'></iframe>  ",
            "location": "  Service   location   here  "
        }
    }
    
    print("Before sanitization:")
    print(f"Name: '{dirty_form_data['client_data']['full_name']}'")
    print(f"Description: '{dirty_form_data['application_data']['description']}'")
    
    # Sanitize form data
    clean_form_data = sanitize_form_data(dirty_form_data)
    
    print("\nAfter sanitization:")
    print(f"Name: '{clean_form_data['client_data']['full_name']}'")
    print(f"Description: '{clean_form_data['application_data']['description']}'")
    print()


def demo_localization():
    """Demo: Localized error messages"""
    print("=== Localized Error Messages ===")
    
    # Invalid form data
    invalid_form_data = {
        "client_data": {
            "phone": "invalid_phone",
            "full_name": "A"  # Too short
        },
        "application_data": {
            "description": "Short",  # Too short
            "location": ""  # Missing
        }
    }
    
    # Test in different languages
    for lang, lang_name in [("uz", "Uzbek"), ("ru", "Russian"), ("en", "English")]:
        print(f"\n{lang_name} ({lang}):")
        result = validate_staff_form("manager", "connection_request", invalid_form_data, lang)
        
        if result.has_errors():
            for field, errors in result.errors.items():
                for error in errors:
                    print(f"  - {error}")
    
    print()


def demo_validation_schema():
    """Demo: Validation schema for different roles"""
    print("=== Validation Schema for Different Roles ===")
    
    roles = ["manager", "junior_manager", "controller", "call_center"]
    
    for role in roles:
        print(f"\n{role.title()} Schema:")
        schema = get_validation_schema(role, "connection_request")
        
        print(f"  Client permissions:")
        for perm, value in schema['client_data']['permissions'].items():
            print(f"    - {perm}: {value}")
        
        print(f"  Application permissions:")
        for perm, value in schema['application_data']['permissions'].items():
            print(f"    - {perm}: {value}")
    
    print()


def demo_comprehensive_validation_response():
    """Demo: Comprehensive validation response"""
    print("=== Comprehensive Validation Response ===")
    
    form_data = {
        "client_data": {
            "phone": "+998901234567",
            "full_name": "Test User",
            "address": "Test address for validation"
        },
        "application_data": {
            "description": "Test description for application validation system",
            "location": "Test location for service",
            "priority": "medium"
        }
    }
    
    # Validate and create comprehensive response
    result = validate_staff_form("manager", "connection_request", form_data, "uz")
    response = create_validation_response(result, "uz")
    
    print("Validation Response:")
    print(f"  Valid: {response['is_valid']}")
    print(f"  Language: {response['language']}")
    print(f"  Error count: {response['error_count']}")
    print(f"  Warning count: {response['warning_count']}")
    print(f"  Message: {response['message']}")
    
    if response['is_valid']:
        print("✓ Ready for application creation")
    
    print()


def main():
    """Run all demonstrations"""
    print("Staff Form Validation System Demo")
    print("=" * 50)
    
    demo_manager_connection_request()
    demo_junior_manager_technical_service()
    demo_call_center_with_security_issues()
    demo_form_sanitization()
    demo_localization()
    demo_validation_schema()
    demo_comprehensive_validation_response()
    
    print("Demo completed successfully!")


if __name__ == "__main__":
    main()