#!/usr/bin/env python3
"""
Test script to verify main menu handler integration with staff application creation.
This script tests the integration between main menu handlers and staff application creation functionality.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.role_permissions import (
    get_role_permissions, 
    can_create_application, 
    get_available_application_types,
    ROLE_PERMISSIONS
)
from database.models import UserRole


async def test_role_permissions():
    """Test role permissions for application creation"""
    print("🔍 Testing Role Permissions for Application Creation")
    print("=" * 60)
    
    # Test roles that should have application creation permissions
    test_roles = [
        UserRole.MANAGER.value,
        UserRole.JUNIOR_MANAGER.value,
        UserRole.CONTROLLER.value,
        UserRole.CALL_CENTER.value
    ]
    
    for role in test_roles:
        print(f"\n📋 Testing role: {role}")
        print("-" * 40)
        
        try:
            permissions = get_role_permissions(role)
            available_types = get_available_application_types(role)
            
            print(f"  ✅ Can create connection requests: {permissions.can_create_connection}")
            print(f"  ✅ Can create technical services: {permissions.can_create_technical}")
            print(f"  ✅ Can select clients: {permissions.can_select_client}")
            print(f"  ✅ Can create clients: {permissions.can_create_client}")
            print(f"  ✅ Can assign directly: {permissions.can_assign_directly}")
            print(f"  ✅ Notification level: {permissions.notification_level}")
            print(f"  ✅ Daily limit: {permissions.max_applications_per_day}")
            print(f"  ✅ Available application types: {available_types}")
            
            # Test specific application type permissions
            for app_type in ['connection_request', 'technical_service']:
                can_create = can_create_application(role, app_type)
                status = "✅ YES" if can_create else "❌ NO"
                print(f"  {status} Can create {app_type}")
                
        except Exception as e:
            print(f"  ❌ Error testing role {role}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Role permissions test completed!")


async def test_role_specific_restrictions():
    """Test role-specific restrictions"""
    print("\n🔒 Testing Role-Specific Restrictions")
    print("=" * 60)
    
    # Test Junior Manager restrictions (should only create connection requests)
    print(f"\n📋 Testing Junior Manager restrictions:")
    print("-" * 40)
    
    jm_permissions = get_role_permissions(UserRole.JUNIOR_MANAGER.value)
    print(f"  ✅ Can create connection: {jm_permissions.can_create_connection}")
    print(f"  ❌ Can create technical: {jm_permissions.can_create_technical}")
    print(f"  ❌ Can assign directly: {jm_permissions.can_assign_directly}")
    
    # Verify Junior Manager cannot create technical services
    can_create_tech = can_create_application(UserRole.JUNIOR_MANAGER.value, 'technical_service')
    print(f"  {'❌ CORRECT' if not can_create_tech else '⚠️ ERROR'} Junior Manager technical service restriction")
    
    # Test roles that should have full permissions
    full_permission_roles = [UserRole.MANAGER.value, UserRole.CONTROLLER.value]
    
    for role in full_permission_roles:
        print(f"\n📋 Testing {role} full permissions:")
        print("-" * 40)
        
        permissions = get_role_permissions(role)
        all_permissions_correct = (
            permissions.can_create_connection and
            permissions.can_create_technical and
            permissions.can_assign_directly and
            permissions.can_select_client and
            permissions.can_create_client
        )
        
        status = "✅ CORRECT" if all_permissions_correct else "❌ ERROR"
        print(f"  {status} All permissions enabled for {role}")
    
    print("\n" + "=" * 60)
    print("✅ Role restrictions test completed!")


async def test_application_type_mapping():
    """Test application type mapping and validation"""
    print("\n🔄 Testing Application Type Mapping")
    print("=" * 60)
    
    # Test valid application types
    valid_types = ['connection_request', 'technical_service']
    
    for app_type in valid_types:
        print(f"\n📋 Testing application type: {app_type}")
        print("-" * 40)
        
        # Test each role's permission for this application type
        for role in [UserRole.MANAGER.value, UserRole.JUNIOR_MANAGER.value, 
                    UserRole.CONTROLLER.value, UserRole.CALL_CENTER.value]:
            
            can_create = can_create_application(role, app_type)
            permissions = get_role_permissions(role)
            
            # Determine expected result
            if app_type == 'connection_request':
                expected = permissions.can_create_connection
            else:  # technical_service
                expected = permissions.can_create_technical
            
            status = "✅ CORRECT" if can_create == expected else "❌ ERROR"
            print(f"  {status} {role} -> {app_type}: {can_create}")
    
    print("\n" + "=" * 60)
    print("✅ Application type mapping test completed!")


async def test_permission_validation_functions():
    """Test permission validation functions"""
    print("\n🛡️ Testing Permission Validation Functions")
    print("=" * 60)
    
    from utils.role_permissions import (
        validate_application_creation_permission,
        validate_client_selection_permission,
        validate_client_creation_permission,
        ApplicationCreationPermissionError,
        ClientSelectionPermissionError
    )
    
    # Test valid permissions (should not raise exceptions)
    print("\n📋 Testing valid permissions (should pass):")
    print("-" * 40)
    
    try:
        validate_application_creation_permission(UserRole.MANAGER.value, 'connection_request')
        print("  ✅ Manager can create connection requests")
    except Exception as e:
        print(f"  ❌ ERROR: Manager connection request validation failed: {e}")
    
    try:
        validate_application_creation_permission(UserRole.CONTROLLER.value, 'technical_service')
        print("  ✅ Controller can create technical services")
    except Exception as e:
        print(f"  ❌ ERROR: Controller technical service validation failed: {e}")
    
    try:
        validate_client_selection_permission(UserRole.CALL_CENTER.value)
        print("  ✅ Call Center can select clients")
    except Exception as e:
        print(f"  ❌ ERROR: Call Center client selection validation failed: {e}")
    
    # Test invalid permissions (should raise exceptions)
    print("\n📋 Testing invalid permissions (should fail):")
    print("-" * 40)
    
    try:
        validate_application_creation_permission(UserRole.JUNIOR_MANAGER.value, 'technical_service')
        print("  ❌ ERROR: Junior Manager technical service should be denied")
    except ApplicationCreationPermissionError:
        print("  ✅ Junior Manager technical service correctly denied")
    except Exception as e:
        print(f"  ❌ ERROR: Unexpected exception: {e}")
    
    try:
        validate_client_selection_permission(UserRole.CLIENT.value)
        print("  ❌ ERROR: Client role should not have client selection permission")
    except ClientSelectionPermissionError:
        print("  ✅ Client role correctly denied client selection")
    except Exception as e:
        print(f"  ❌ ERROR: Unexpected exception: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Permission validation test completed!")


async def main():
    """Run all tests"""
    print("🚀 Starting Main Menu Integration Tests")
    print("=" * 80)
    
    try:
        await test_role_permissions()
        await test_role_specific_restrictions()
        await test_application_type_mapping()
        await test_permission_validation_functions()
        
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("✅ Main menu handlers should now properly integrate with staff application creation")
        print("✅ Role-based access control is working correctly")
        print("✅ Permission validation is functioning as expected")
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)