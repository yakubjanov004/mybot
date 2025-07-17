"""
Simple test for RoleBasedApplicationHandler to verify implementation
"""

import asyncio
from datetime import datetime
from database.models import UserRole
from handlers.staff_application_creation import (
    RoleBasedApplicationHandler, ApplicationCreationError,
    ClientValidationError, WorkflowInitializationError
)

async def test_basic_functionality():
    """Test basic functionality of RoleBasedApplicationHandler"""
    
    print("Testing RoleBasedApplicationHandler...")
    
    # Create handler instance
    handler = RoleBasedApplicationHandler()
    
    # Test 1: Start application creation with valid role
    print("\n1. Testing start_application_creation with Manager role...")
    try:
        result = await handler.start_application_creation(
            creator_role=UserRole.MANAGER.value,
            creator_id=1,
            application_type='connection_request'
        )
        
        if result['success']:
            print("✅ Manager can create connection requests")
            print(f"   Next step: {result['next_step']}")
            print(f"   Permissions: {result['available_permissions']}")
        else:
            print(f"❌ Failed: {result['error_message']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Start application creation with Junior Manager for technical service (should fail)
    print("\n2. Testing start_application_creation with Junior Manager for technical service...")
    try:
        result = await handler.start_application_creation(
            creator_role=UserRole.JUNIOR_MANAGER.value,
            creator_id=2,
            application_type='technical_service'
        )
        
        if result['success']:
            print("❌ Junior Manager should not be able to create technical service requests")
        else:
            print("✅ Junior Manager correctly denied technical service creation")
            print(f"   Error: {result['error_message']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Test form processing with valid data
    print("\n3. Testing process_application_form with valid data...")
    try:
        creator_context = {
            'creator_id': 1,
            'creator_role': UserRole.MANAGER.value,
            'application_type': 'connection_request',
            'permissions': {},
            'session_id': 'test-session'
        }
        
        form_data = {
            'client_data': {
                'phone': '+998901234567',
                'full_name': 'Test Client',
                'address': 'Test Address'
            },
            'application_data': {
                'description': 'Test connection request for new client',
                'location': 'Test Location',
                'priority': 'medium'
            }
        }
        
        result = await handler.process_application_form(form_data, creator_context)
        
        if result['success']:
            print("✅ Form processing successful")
            print(f"   Next step: {result['next_step']}")
        else:
            print(f"❌ Form processing failed: {result['error_message']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Test form processing with invalid data
    print("\n4. Testing process_application_form with invalid data...")
    try:
        creator_context = {
            'creator_id': 1,
            'creator_role': UserRole.MANAGER.value,
            'application_type': 'connection_request',
            'permissions': {},
            'session_id': 'test-session'
        }
        
        form_data = {
            'client_data': {
                'phone': 'invalid-phone',  # Invalid phone format
                'full_name': 'A',  # Too short name
            },
            'application_data': {
                'description': 'Short',  # Too short description
                'location': '',  # Empty location
            }
        }
        
        result = await handler.process_application_form(form_data, creator_context)
        
        if result['success']:
            print("❌ Form processing should have failed with invalid data")
        else:
            print("✅ Form processing correctly failed with invalid data")
            print(f"   Error: {result['error_message']}")
            
    except Exception as e:
        print(f"✅ Exception correctly raised: {type(e).__name__}: {e}")
    
    print("\n✅ Basic functionality tests completed!")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())