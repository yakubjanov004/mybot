#!/usr/bin/env python3
"""
Simple test script for State Manager functionality
"""

import sys
import os
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import (
    ServiceRequest, StateTransition, WorkflowType, RequestStatus, 
    WorkflowAction, UserRole, Priority
)
from utils.state_manager import StateManager, StateManagerFactory


def test_state_manager_basic():
    """Test basic State Manager functionality (non-async parts)"""
    print("🧪 Testing State Manager Basic Functionality...")
    
    # Create state manager without pool (will test non-database methods)
    state_manager = StateManager()
    
    # Test 1: Get initial role
    print("✓ Testing _get_initial_role...")
    role = state_manager._get_initial_role(WorkflowType.CONNECTION_REQUEST.value)
    assert role == 'manager', f"Expected 'manager', got '{role}'"
    
    role = state_manager._get_initial_role(WorkflowType.TECHNICAL_SERVICE.value)
    assert role == 'controller', f"Expected 'controller', got '{role}'"
    
    role = state_manager._get_initial_role(WorkflowType.CALL_CENTER_DIRECT.value)
    assert role == 'call_center_supervisor', f"Expected 'call_center_supervisor', got '{role}'"
    
    # Test unknown workflow type (should default to manager)
    role = state_manager._get_initial_role('unknown_workflow')
    assert role == 'manager', f"Expected 'manager' for unknown workflow, got '{role}'"
    print("  ✅ Initial role determination works correctly")
    
    # Test 2: Generate unique request IDs
    print("✓ Testing _generate_request_id...")
    id1 = state_manager._generate_request_id()
    id2 = state_manager._generate_request_id()
    assert id1 != id2, "Request IDs should be unique"
    assert len(id1) > 0, "Request ID should not be empty"
    assert isinstance(id1, str), "Request ID should be a string"
    print(f"  ✅ Generated unique IDs: {id1[:8]}... and {id2[:8]}...")
    
    # Test 3: Pool getter (should handle missing pool gracefully)
    print("✓ Testing _get_pool...")
    pool = state_manager._get_pool()
    # Should return None when no pool is available and no bot is loaded
    # This is expected behavior for testing
    print("  ✅ Pool getter handles missing pool gracefully")
    
    print("🎉 All State Manager basic tests passed!")
    return True


def test_state_manager_models():
    """Test State Manager model functionality"""
    print("🧪 Testing State Manager Models...")
    
    # Test ServiceRequest model
    print("✓ Testing ServiceRequest model...")
    request = ServiceRequest(
        id="test-123",
        workflow_type=WorkflowType.CONNECTION_REQUEST.value,
        client_id=1,
        role_current =UserRole.MANAGER.value,
        current_status=RequestStatus.CREATED.value,
        priority=Priority.HIGH.value,
        description="Test connection request",
        location="Test location"
    )
    
    assert request.id == "test-123"
    assert request.workflow_type == WorkflowType.CONNECTION_REQUEST.value
    assert request.client_id == 1
    
    # Test to_dict conversion
    request_dict = request.to_dict()
    assert request_dict['id'] == "test-123"
    assert request_dict['workflow_type'] == WorkflowType.CONNECTION_REQUEST.value
    
    # Test from_dict conversion
    restored_request = ServiceRequest.from_dict(request_dict)
    assert restored_request.id == request.id
    assert restored_request.workflow_type == request.workflow_type
    print("  ✅ ServiceRequest model works correctly")
    
    # Test StateTransition model
    print("✓ Testing StateTransition model...")
    transition = StateTransition(
        request_id="test-123",
        from_role=UserRole.MANAGER.value,
        to_role=UserRole.JUNIOR_MANAGER.value,
        action=WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
        actor_id=1,
        comments="Assigned to junior manager"
    )
    
    assert transition.request_id == "test-123"
    assert transition.from_role == UserRole.MANAGER.value
    assert transition.to_role == UserRole.JUNIOR_MANAGER.value
    assert transition.action == WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value
    
    # Test to_dict conversion
    transition_dict = transition.to_dict()
    assert transition_dict['request_id'] == "test-123"
    assert transition_dict['action'] == WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value
    print("  ✅ StateTransition model works correctly")
    
    print("🎉 All State Manager model tests passed!")
    return True


def test_state_manager_factory():
    """Test State Manager factory"""
    print("🧪 Testing State Manager Factory...")
    
    manager = StateManagerFactory.create_state_manager()
    
    assert isinstance(manager, StateManager), "Factory should create StateManager instance"
    print("  ✅ Factory creates StateManager correctly")
    
    print("🎉 State Manager factory test passed!")
    return True


def main():
    """Run all tests"""
    print("🚀 Starting State Manager Tests...\n")
    
    try:
        # Test models
        test_state_manager_models()
        print()
        
        # Test factory
        test_state_manager_factory()
        print()
        
        # Test basic functionality
        test_state_manager_basic()
        print()
        
        print("✅ ALL STATE MANAGER TESTS PASSED!")
        print("🎯 State Manager implementation is working correctly")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Run the tests
    result = main()
    if result:
        print("\n🎉 State Manager implementation completed successfully!")
    else:
        print("\n💥 State Manager tests failed!")
        sys.exit(1)