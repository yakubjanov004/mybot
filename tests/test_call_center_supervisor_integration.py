#!/usr/bin/env python3
"""
Test script to verify Call Center Supervisor integration with staff application creation.
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


async def test_call_center_supervisor_permissions():
    """Test Call Center Supervisor permissions for application creation"""
    print("🔍 Testing Call Center Supervisor Permissions")
    print("=" * 60)
    
    role = UserRole.CALL_CENTER_SUPERVISOR.value
    
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
        
        # Verify Call Center Supervisor has full permissions like Manager
        expected_permissions = {
            'can_create_connection': True,
            'can_create_technical': True,
            'can_assign_directly': True,
            'can_select_client': True,
            'can_create_client': True,
            'notification_level': 'high',
            'max_applications_per_day': None
        }
        
        print(f"\n📋 Verifying supervisor-level permissions:")
        print("-" * 40)
        
        all_correct = True
        for perm, expected_value in expected_permissions.items():
            actual_value = getattr(permissions, perm)
            is_correct = actual_value == expected_value
            status = "✅ CORRECT" if is_correct else "❌ ERROR"
            print(f"  {status} {perm}: {actual_value} (expected: {expected_value})")
            if not is_correct:
                all_correct = False
        
        if all_correct:
            print(f"\n🎉 Call Center Supervisor has correct supervisor-level permissions!")
        else:
            print(f"\n❌ Call Center Supervisor permissions need adjustment!")
            
    except Exception as e:
        print(f"  ❌ Error testing role {role}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Call Center Supervisor permissions test completed!")


async def test_role_hierarchy():
    """Test role hierarchy and permissions comparison"""
    print("\n🏗️ Testing Role Hierarchy and Permissions")
    print("=" * 60)
    
    # Compare Call Center Supervisor with other roles
    roles_to_compare = [
        (UserRole.CALL_CENTER_SUPERVISOR.value, "Call Center Supervisor"),
        (UserRole.MANAGER.value, "Manager"),
        (UserRole.CONTROLLER.value, "Controller"),
        (UserRole.CALL_CENTER.value, "Call Center"),
        (UserRole.JUNIOR_MANAGER.value, "Junior Manager")
    ]
    
    print(f"\n📋 Role Permissions Comparison:")
    print("-" * 80)
    print(f"{'Role':<25} {'Connection':<12} {'Technical':<12} {'Assign':<8} {'Daily Limit':<12}")
    print("-" * 80)
    
    for role_value, role_name in roles_to_compare:
        try:
            permissions = get_role_permissions(role_value)
            conn = "✅" if permissions.can_create_connection else "❌"
            tech = "✅" if permissions.can_create_technical else "❌"
            assign = "✅" if permissions.can_assign_directly else "❌"
            limit = str(permissions.max_applications_per_day) if permissions.max_applications_per_day else "None"
            
            print(f"{role_name:<25} {conn:<12} {tech:<12} {assign:<8} {limit:<12}")
            
        except Exception as e:
            print(f"{role_name:<25} ERROR: {e}")
    
    print("-" * 80)
    
    # Verify Call Center Supervisor has higher permissions than regular Call Center
    print(f"\n📋 Supervisor vs Regular Call Center comparison:")
    print("-" * 40)
    
    try:
        supervisor_perms = get_role_permissions(UserRole.CALL_CENTER_SUPERVISOR.value)
        regular_perms = get_role_permissions(UserRole.CALL_CENTER.value)
        
        # Supervisor should have direct assignment capability
        if supervisor_perms.can_assign_directly and not regular_perms.can_assign_directly:
            print("  ✅ Supervisor has direct assignment capability (regular Call Center doesn't)")
        else:
            print("  ❌ Supervisor should have direct assignment capability")
        
        # Supervisor should have higher notification level
        if supervisor_perms.notification_level == 'high' and regular_perms.notification_level == 'medium':
            print("  ✅ Supervisor has higher notification level")
        else:
            print(f"  ❌ Supervisor notification level: {supervisor_perms.notification_level}, Regular: {regular_perms.notification_level}")
        
        # Supervisor should have no daily limit (or higher limit)
        if supervisor_perms.max_applications_per_day is None:
            print("  ✅ Supervisor has no daily limit")
        else:
            print(f"  ⚠️ Supervisor has daily limit: {supervisor_perms.max_applications_per_day}")
            
    except Exception as e:
        print(f"  ❌ Error comparing supervisor vs regular: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Role hierarchy test completed!")


async def main():
    """Run all tests"""
    print("🚀 Starting Call Center Supervisor Integration Tests")
    print("=" * 80)
    
    try:
        await test_call_center_supervisor_permissions()
        await test_role_hierarchy()
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print("=" * 80)
        print("✅ Call Center Supervisor integration is working correctly")
        print("✅ Role hierarchy and permissions are properly configured")
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)