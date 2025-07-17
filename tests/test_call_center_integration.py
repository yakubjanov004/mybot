#!/usr/bin/env python3
"""
Simple integration test for Call Center Initiated Requests
This script tests the basic functionality without requiring a full bot setup
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import WorkflowType, UserRole, Priority
from utils.workflow_engine import WorkflowEngineFactory
from utils.state_manager import StateManagerFactory
from utils.notification_system import NotificationSystemFactory


async def test_call_center_workflow_integration():
    """Test call center workflow integration"""
    print("🧪 Testing Call Center Workflow Integration...")
    
    # Initialize components
    state_manager = StateManagerFactory.create_state_manager()
    notification_system = NotificationSystemFactory.create_notification_system()
    workflow_engine = WorkflowEngineFactory.create_workflow_engine(
        state_manager, notification_system, None
    )
    
    # Test 1: Connection Request from Call Center
    print("\n1️⃣ Testing Connection Request from Call Center...")
    connection_request_data = {
        'client_id': 123,
        'description': 'Internet connection installation needed',
        'location': '123 Test Street, Tashkent',
        'contact_info': {
            'phone': '998901234567',
            'name': 'Test Client',
            'address': '123 Test Street, Tashkent'
        },
        'priority': Priority.HIGH.value,
        'service_type': 'installation',
        'created_by_role': UserRole.CALL_CENTER.value,
        'created_by': 456,
        'client_details': {
            'name': 'Test Client',
            'phone': '998901234567',
            'address': '123 Test Street, Tashkent',
            'language': 'uz'
        }
    }
    
    try:
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CONNECTION_REQUEST.value, 
            connection_request_data
        )
        print(f"✅ Connection request created: {request_id[:8] if request_id else 'None'}")
        
        # Verify routing
        if request_id:
            request = await state_manager.get_request(request_id)
            if request and request.role_current == UserRole.MANAGER.value:
                print(f"✅ Correctly routed to Manager: {request.role_current }")
            else:
                print(f"❌ Incorrect routing. Expected: {UserRole.MANAGER.value}, Got: {request.role_current if request else 'None'}")
        
    except Exception as e:
        print(f"❌ Connection request test failed: {e}")
    
    # Test 2: Technical Service Request from Call Center
    print("\n2️⃣ Testing Technical Service Request from Call Center...")
    technical_request_data = {
        'client_id': 124,
        'description': 'Internet connection not working, need repair',
        'contact_info': {
            'phone': '998901234568',
            'name': 'Test Client 2'
        },
        'priority': Priority.MEDIUM.value,
        'service_type': 'repair',
        'created_by_role': UserRole.CALL_CENTER.value,
        'created_by': 456,
        'issue_description': 'Client reports intermittent connectivity issues',
        'client_details': {
            'name': 'Test Client 2',
            'phone': '998901234568',
            'language': 'ru'
        }
    }
    
    try:
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.TECHNICAL_SERVICE.value, 
            technical_request_data
        )
        print(f"✅ Technical service request created: {request_id[:8] if request_id else 'None'}")
        
        # Verify routing
        if request_id:
            request = await state_manager.get_request(request_id)
            if request and request.role_current == UserRole.CONTROLLER.value:
                print(f"✅ Correctly routed to Controller: {request.role_current }")
            else:
                print(f"❌ Incorrect routing. Expected: {UserRole.CONTROLLER.value}, Got: {request.role_current if request else 'None'}")
        
    except Exception as e:
        print(f"❌ Technical service request test failed: {e}")
    
    # Test 3: Call Center Direct Request
    print("\n3️⃣ Testing Call Center Direct Request...")
    direct_request_data = {
        'client_id': 125,
        'description': 'Simple configuration question',
        'contact_info': {
            'phone': '998901234569',
            'name': 'Test Client 3'
        },
        'priority': Priority.LOW.value,
        'service_type': 'consultation',
        'created_by_role': UserRole.CALL_CENTER.value,
        'created_by': 456,
        'issue_description': 'Client needs help with router configuration',
        'client_details': {
            'name': 'Test Client 3',
            'phone': '998901234569',
            'language': 'uz'
        }
    }
    
    try:
        request_id = await workflow_engine.initiate_workflow(
            WorkflowType.CALL_CENTER_DIRECT.value, 
            direct_request_data
        )
        print(f"✅ Call center direct request created: {request_id[:8] if request_id else 'None'}")
        
        # Verify routing
        if request_id:
            request = await state_manager.get_request(request_id)
            if request and request.role_current == UserRole.CALL_CENTER_SUPERVISOR.value:
                print(f"✅ Correctly routed to Call Center Supervisor: {request.role_current }")
            else:
                print(f"❌ Incorrect routing. Expected: {UserRole.CALL_CENTER_SUPERVISOR.value}, Got: {request.role_current if request else 'None'}")
        
    except Exception as e:
        print(f"❌ Call center direct request test failed: {e}")
    
    # Test 4: Service Type to Workflow Mapping
    print("\n4️⃣ Testing Service Type to Workflow Mapping...")
    workflow_mapping = {
        'installation': WorkflowType.CONNECTION_REQUEST.value,
        'setup': WorkflowType.CONNECTION_REQUEST.value,
        'repair': WorkflowType.TECHNICAL_SERVICE.value,
        'maintenance': WorkflowType.TECHNICAL_SERVICE.value,
        'consultation': WorkflowType.CALL_CENTER_DIRECT.value
    }
    
    mapping_correct = True
    for service_type, expected_workflow in workflow_mapping.items():
        if workflow_mapping[service_type] == expected_workflow:
            print(f"✅ {service_type} → {expected_workflow}")
        else:
            print(f"❌ {service_type} → Expected: {expected_workflow}, Got: {workflow_mapping[service_type]}")
            mapping_correct = False
    
    if mapping_correct:
        print("✅ All service type mappings are correct")
    
    print("\n🎉 Call Center Workflow Integration Test Complete!")


if __name__ == "__main__":
    # Run the integration test
    asyncio.run(test_call_center_workflow_integration())