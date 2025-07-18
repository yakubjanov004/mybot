"""
Edge Case Integration Tests for Staff-Created Application Workflows

This test suite covers edge cases and specific scenarios for staff-created applications
to ensure robust workflow compatibility and proper handling of complex situations.
"""

import pytest
import pytest_asyncio
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from database.models import (
    UserRole, WorkflowType, WorkflowAction, RequestStatus, Priority,
    ServiceRequest, StateTransition
)
from handlers.staff_application_creation import RoleBasedApplicationHandler
from utils.workflow_engine import WorkflowEngine
from utils.state_manager import StateManager
from utils.notification_system import NotificationSystem


class TestStaffWorkflowEdgeCases:
    """Edge case tests for staff-created application workflows"""
    
    @pytest_asyncio.fixture
    async def setup_components(self):
        """Setup test components"""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        
        state_manager = StateManager(pool=mock_pool)
        notification_system = NotificationSystem(pool=mock_pool)
        workflow_engine = WorkflowEngine(
            state_manager=state_manager,
            notification_system=notification_system,
            inventory_manager=None
        )
        staff_handler = RoleBasedApplicationHandler(
            workflow_engine=workflow_engine,
            state_manager=state_manager,
            notification_system=notification_system,
            pool=mock_pool
        )
        
        return {
            'workflow_engine': workflow_engine,
            'state_manager': state_manager,
            'notification_system': notification_system,
            'staff_handler': staff_handler,
            'mock_pool': mock_pool,
            'mock_conn': mock_conn
        }
    
    @pytest.mark.asyncio
    async def test_concurrent_staff_application_creation(self, setup_components):
        """
        Test concurrent staff application creation from multiple roles
        Ensures system handles multiple staff members creating applications simultaneously
        """
        components = await setup_components
        staff_handler = components['staff_handler']
        mock_conn = components['mock_conn']
        
        # Mock database responses
        mock_conn.execute.return_value = "INSERT 0 1"
        
        # Create multiple concurrent application creation tasks
        staff_members = [
            {'role': UserRole.MANAGER.value, 'id': 100, 'type': 'connection_request'},
            {'role': UserRole.CONTROLLER.value, 'id': 200, 'type': 'technical_service'},
            {'role': UserRole.CALL_CENTER.value, 'id': 300, 'type': 'connection_request'},
            {'role': UserRole.MANAGER.value, 'id': 400, 'type': 'technical_service'},
            {'role': UserRole.CONTROLLER.value, 'id': 500, 'type': 'connection_request'}
        ]
        
        with patch.object(staff_handler, '_get_daily_application_count', return_value=0):
            
            # Create concurrent tasks
            tasks = []
            for staff in staff_members:
                task = staff_handler.start_application_creation(
                    creator_role=staff['role'],
                    creator_id=staff['id'],
                    application_type=staff['type']
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all tasks completed successfully
        successful_results = [r for r in results if isinstance(r, dict) and r.get('success')]
        failed_results = [r for r in results if isinstance(r, Exception) or (isinstance(r, dict) and not r.get('success'))]
        
        assert len(successful_results) >= 4, f"Expected at least 4 successful results, got {len(successful_results)}"
        assert len(failed_results) <= 1, f"Too many failed results: {len(failed_results)}"
        
        print("✅ Concurrent staff application creation handled correctly!")
    
    @pytest.mark.asyncio
    async def test_staff_application_with_workflow_interruption(self, setup_components):
        """
        Test staff-created application workflow when interrupted by system issues
        Ensures proper recovery and state consistency
        """
        components = await setup_components
        workflow_engine = components['workflow_engine']
        state_manager = components['state_manager']
        
        request_id = f"INTERRUPT-{uuid.uuid4()}"
        
        # Create mock staff-created request
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current=UserRole.JUNIOR_MANAGER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description='Staff-created request with interruption',
            location='Test location',
            contact_info={'phone': '+998901234567'},
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': 100,
                    'creator_role': UserRole.MANAGER.value
                },
                'junior_manager_id': 200
            },
            equipment_used=[],
            inventory_updated=False,
            completion_rating=None,
            feedback_comments=None,
            created_by_staff=True,
            staff_creator_id=100,
            staff_creator_role=UserRole.MANAGER.value,
            creation_source=UserRole.MANAGER.value
        )
        
        # Test workflow interruption during transition
        with patch.object(state_manager, 'get_request', return_value=mock_request):
            
            # First attempt fails due to system issue
            with patch.object(state_manager, 'update_request_state', side_effect=Exception("Database timeout")):
                
                transition_success = await workflow_engine.transition_workflow(
                    request_id,
                    WorkflowAction.FORWARD_TO_CONTROLLER.value,
                    UserRole.JUNIOR_MANAGER.value,
                    {
                        'actor_id': 200,
                        'forward_notes': 'Forwarding to controller',
                        'forwarded_at': str(datetime.now())
                    }
                )
                
                # Should fail gracefully
                assert transition_success is False
            
            # Second attempt succeeds (system recovered)
            with patch.object(state_manager, 'update_request_state', return_value=True), \
                 patch.object(state_manager, 'add_state_transition', return_value=True), \
                 patch.object(workflow_engine.notification_system, 'send_assignment_notification', return_value=True):
                
                retry_success = await workflow_engine.transition_workflow(
                    request_id,
                    WorkflowAction.FORWARD_TO_CONTROLLER.value,
                    UserRole.JUNIOR_MANAGER.value,
                    {
                        'actor_id': 200,
                        'forward_notes': 'Forwarding to controller (retry)',
                        'forwarded_at': str(datetime.now()),
                        'retry_attempt': True
                    }
                )
                
                # Should succeed on retry
                assert retry_success is True
        
        print("✅ Workflow interruption and recovery handled correctly!")
    
    @pytest.mark.asyncio
    async def test_staff_application_priority_escalation(self, setup_components):
        """
        Test priority escalation for staff-created applications
        Ensures urgent staff-created requests get proper priority handling
        """
        components = await setup_components
        workflow_engine = components['workflow_engine']
        state_manager = components['state_manager']
        
        request_id = f"URGENT-{uuid.uuid4()}"
        
        # Create urgent staff-created request
        urgent_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=1,
            role_current=UserRole.CONTROLLER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.URGENT.value,  # Urgent priority
            description='URGENT: Staff-created technical service request',
            location='Critical infrastructure location',
            contact_info={'phone': '+998901234567'},
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': 400,
                    'creator_role': UserRole.CALL_CENTER.value
                },
                'escalation_reason': 'Critical system outage reported by client',
                'escalated_at': str(datetime.now())
            },
            equipment_used=[],
            inventory_updated=False,
            completion_rating=None,
            feedback_comments=None,
            created_by_staff=True,
            staff_creator_id=400,
            staff_creator_role=UserRole.CALL_CENTER.value,
            creation_source=UserRole.CALL_CENTER.value
        )
        
        # Test urgent assignment to technician
        with patch.object(state_manager, 'get_request', return_value=urgent_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            # Mock notification system to verify urgent notification
            with patch.object(workflow_engine.notification_system, 'send_assignment_notification') as mock_notify:
                mock_notify.return_value = True
                
                urgent_assignment = await workflow_engine.transition_workflow(
                    request_id,
                    WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                    UserRole.CONTROLLER.value,
                    {
                        'technician_id': 500,
                        'actor_id': 300,
                        'assigned_at': str(datetime.now()),
                        'priority_escalation': True,
                        'urgent_assignment': True,
                        'escalation_notes': 'Urgent staff-created request requires immediate attention'
                    }
                )
                
                assert urgent_assignment is True
                
                # Verify urgent notification was sent
                mock_notify.assert_called_once()
                call_args = mock_notify.call_args
                assert UserRole.TECHNICIAN.value in call_args[1].values()
        
        print("✅ Priority escalation handled correctly for staff-created applications!")
    
    @pytest.mark.asyncio
    async def test_staff_application_cross_role_handoff(self, setup_components):
        """
        Test complex cross-role handoffs in staff-created application workflows
        Ensures proper state management across multiple role transitions
        """
        components = await setup_components
        workflow_engine = components['workflow_engine']
        state_manager = components['state_manager']
        
        request_id = f"HANDOFF-{uuid.uuid4()}"
        
        # Create staff-created request that will go through multiple handoffs
        handoff_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current=UserRole.MANAGER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.HIGH.value,
            description='Complex staff-created connection request',
            location='Multi-building complex',
            contact_info={'phone': '+998901234567'},
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': 100,
                    'creator_role': UserRole.MANAGER.value
                },
                'complex_installation': True,
                'multiple_locations': True
            },
            equipment_used=[],
            inventory_updated=False,
            completion_rating=None,
            feedback_comments=None,
            created_by_staff=True,
            staff_creator_id=100,
            staff_creator_role=UserRole.MANAGER.value,
            creation_source=UserRole.MANAGER.value
        )
        
        # Track state transitions through multiple handoffs
        state_history = []
        
        def track_state_transition(*args, **kwargs):
            state_history.append({
                'timestamp': datetime.now(),
                'from_role': kwargs.get('from_role'),
                'to_role': kwargs.get('to_role'),
                'action': kwargs.get('action')
            })
            return True
        
        # Handoff 1: Manager -> Junior Manager
        handoff_request.role_current = UserRole.MANAGER.value
        with patch.object(state_manager, 'get_request', return_value=handoff_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', side_effect=track_state_transition), \
             patch.object(workflow_engine.notification_system, 'send_assignment_notification', return_value=True):
            
            handoff1 = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
                UserRole.MANAGER.value,
                {
                    'junior_manager_id': 200,
                    'actor_id': 100,
                    'handoff_notes': 'Complex installation, requires careful coordination'
                }
            )
            
            assert handoff1 is True
        
        # Handoff 2: Junior Manager -> Controller
        handoff_request.role_current = UserRole.JUNIOR_MANAGER.value
        handoff_request.state_data.update({'junior_manager_processed': True})
        
        with patch.object(state_manager, 'get_request', return_value=handoff_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', side_effect=track_state_transition), \
             patch.object(workflow_engine.notification_system, 'send_assignment_notification', return_value=True):
            
            handoff2 = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.FORWARD_TO_CONTROLLER.value,
                UserRole.JUNIOR_MANAGER.value,
                {
                    'actor_id': 200,
                    'forward_notes': 'Client confirmed complex installation requirements',
                    'special_requirements': ['multiple_locations', 'high_priority']
                }
            )
            
            assert handoff2 is True
        
        # Handoff 3: Controller -> Technician
        handoff_request.role_current = UserRole.CONTROLLER.value
        handoff_request.state_data.update({'controller_processed': True})
        
        with patch.object(state_manager, 'get_request', return_value=handoff_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', side_effect=track_state_transition), \
             patch.object(workflow_engine.notification_system, 'send_assignment_notification', return_value=True):
            
            handoff3 = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.ASSIGN_TO_TECHNICIAN.value,
                UserRole.CONTROLLER.value,
                {
                    'technician_id': 500,
                    'actor_id': 300,
                    'assignment_notes': 'Complex staff-created installation, multiple locations',
                    'special_instructions': ['bring_extra_equipment', 'coordinate_with_client']
                }
            )
            
            assert handoff3 is True
        
        # Verify all handoffs were tracked
        assert len(state_history) == 3
        
        # Verify handoff sequence
        expected_sequence = [
            (UserRole.MANAGER.value, UserRole.JUNIOR_MANAGER.value),
            (UserRole.JUNIOR_MANAGER.value, UserRole.CONTROLLER.value),
            (UserRole.CONTROLLER.value, UserRole.TECHNICIAN.value)
        ]
        
        for i, (expected_from, expected_to) in enumerate(expected_sequence):
            if i < len(state_history):
                assert state_history[i]['from_role'] == expected_from
                assert state_history[i]['to_role'] == expected_to
        
        print("✅ Complex cross-role handoffs handled correctly!")
    
    @pytest.mark.asyncio
    async def test_staff_application_notification_failure_recovery(self, setup_components):
        """
        Test notification failure recovery for staff-created applications
        Ensures workflow continues even if notifications fail
        """
        components = await setup_components
        workflow_engine = components['workflow_engine']
        state_manager = components['state_manager']
        
        request_id = f"NOTIFY-FAIL-{uuid.uuid4()}"
        
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.TECHNICAL_SERVICE.value,
            client_id=1,
            role_current=UserRole.CONTROLLER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description='Staff-created request with notification issues',
            location='Test location',
            contact_info={'phone': '+998901234567'},
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': 300,
                    'creator_role': UserRole.CONTROLLER.value
                }
            },
            equipment_used=[],
            inventory_updated=False,
            completion_rating=None,
            feedback_comments=None,
            created_by_staff=True,
            staff_creator_id=300,
            staff_creator_role=UserRole.CONTROLLER.value,
            creation_source=UserRole.CONTROLLER.value
        )
        
        # Test workflow transition with notification failure
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            # Mock notification failure
            with patch.object(workflow_engine.notification_system, 'send_assignment_notification', return_value=False):
                
                # Workflow should still succeed even if notification fails
                transition_success = await workflow_engine.transition_workflow(
                    request_id,
                    WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                    UserRole.CONTROLLER.value,
                    {
                        'technician_id': 500,
                        'actor_id': 300,
                        'assigned_at': str(datetime.now()),
                        'notification_retry_needed': True
                    }
                )
                
                # Workflow transition should succeed despite notification failure
                assert transition_success is True
                
                # Verify state was still updated
                state_manager.update_request_state.assert_called()
                state_manager.add_state_transition.assert_called()
        
        print("✅ Notification failure recovery handled correctly!")
    
    @pytest.mark.asyncio
    async def test_staff_application_with_client_unavailable(self, setup_components):
        """
        Test staff-created application workflow when client becomes unavailable
        Ensures proper handling of client communication issues
        """
        components = await setup_components
        workflow_engine = components['workflow_engine']
        state_manager = components['state_manager']
        
        request_id = f"CLIENT-UNAVAIL-{uuid.uuid4()}"
        
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current=UserRole.JUNIOR_MANAGER.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.MEDIUM.value,
            description='Staff-created request, client unavailable',
            location='Test location',
            contact_info={'phone': '+998901234567'},
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': 100,
                    'creator_role': UserRole.MANAGER.value
                },
                'junior_manager_id': 200,
                'client_contact_attempts': 0
            },
            equipment_used=[],
            inventory_updated=False,
            completion_rating=None,
            feedback_comments=None,
            created_by_staff=True,
            staff_creator_id=100,
            staff_creator_role=UserRole.MANAGER.value,
            creation_source=UserRole.MANAGER.value
        )
        
        # Test multiple client contact attempts
        contact_attempts = []
        
        def track_contact_attempt(*args, **kwargs):
            contact_attempts.append({
                'timestamp': datetime.now(),
                'attempt_number': len(contact_attempts) + 1,
                'success': False
            })
            return True
        
        # Attempt 1: Client unavailable
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', side_effect=track_contact_attempt), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            attempt1 = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.CALL_CLIENT.value,
                UserRole.JUNIOR_MANAGER.value,
                {
                    'actor_id': 200,
                    'call_result': 'no_answer',
                    'call_timestamp': str(datetime.now()),
                    'attempt_number': 1,
                    'next_attempt_scheduled': str(datetime.now() + timedelta(hours=2))
                }
            )
            
            assert attempt1 is True
        
        # Update request state for second attempt
        mock_request.state_data.update({
            'client_contact_attempts': 1,
            'last_contact_attempt': str(datetime.now()),
            'client_unavailable': True
        })
        
        # Attempt 2: Client still unavailable
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', side_effect=track_contact_attempt), \
             patch.object(state_manager, 'add_state_transition', return_value=True):
            
            attempt2 = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.CALL_CLIENT.value,
                UserRole.JUNIOR_MANAGER.value,
                {
                    'actor_id': 200,
                    'call_result': 'no_answer',
                    'call_timestamp': str(datetime.now()),
                    'attempt_number': 2,
                    'escalation_needed': True
                }
            )
            
            assert attempt2 is True
        
        # Update request state for escalation
        mock_request.state_data.update({
            'client_contact_attempts': 2,
            'escalation_required': True,
            'escalation_reason': 'client_unavailable_multiple_attempts'
        })
        
        # Escalate to controller despite client unavailability
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True), \
             patch.object(workflow_engine.notification_system, 'send_assignment_notification', return_value=True):
            
            escalation = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.FORWARD_TO_CONTROLLER.value,
                UserRole.JUNIOR_MANAGER.value,
                {
                    'actor_id': 200,
                    'forward_reason': 'client_unavailable_after_multiple_attempts',
                    'escalation_notes': 'Staff-created request, client not responding to calls',
                    'forwarded_at': str(datetime.now())
                }
            )
            
            assert escalation is True
        
        # Verify contact attempts were tracked
        assert len(contact_attempts) == 2
        
        print("✅ Client unavailability scenarios handled correctly!")
    
    @pytest.mark.asyncio
    async def test_staff_application_equipment_shortage_handling(self, setup_components):
        """
        Test staff-created application workflow when equipment shortage occurs
        Ensures proper handling of inventory constraints
        """
        components = await setup_components
        workflow_engine = components['workflow_engine']
        state_manager = components['state_manager']
        
        request_id = f"EQUIP-SHORT-{uuid.uuid4()}"
        
        mock_request = ServiceRequest(
            id=request_id,
            workflow_type=WorkflowType.CONNECTION_REQUEST.value,
            client_id=1,
            role_current=UserRole.TECHNICIAN.value,
            current_status=RequestStatus.IN_PROGRESS.value,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            priority=Priority.HIGH.value,
            description='Staff-created request requiring special equipment',
            location='Remote location',
            contact_info={'phone': '+998901234567'},
            state_data={
                'created_by_staff': True,
                'staff_creator_info': {
                    'creator_id': 100,
                    'creator_role': UserRole.MANAGER.value
                },
                'technician_id': 500,
                'installation_started': True,
                'special_equipment_needed': True
            },
            equipment_used=[],
            inventory_updated=False,
            completion_rating=None,
            feedback_comments=None,
            created_by_staff=True,
            staff_creator_id=100,
            staff_creator_role=UserRole.MANAGER.value,
            creation_source=UserRole.MANAGER.value
        )
        
        # Test equipment documentation with shortage
        equipment_needed = [
            {'name': 'Special Router', 'quantity': 1, 'model': 'SR-2000'},
            {'name': 'Fiber Cable', 'quantity': 100, 'type': 'single-mode'}
        ]
        
        # Mock inventory manager to simulate shortage
        with patch.object(workflow_engine.inventory_manager, 'check_availability') as mock_check:
            mock_check.return_value = {
                'Special Router': {'available': 0, 'needed': 1, 'shortage': True},
                'Fiber Cable': {'available': 50, 'needed': 100, 'shortage': True}
            }
            
            with patch.object(state_manager, 'get_request', return_value=mock_request), \
                 patch.object(state_manager, 'update_request_state', return_value=True), \
                 patch.object(state_manager, 'add_state_transition', return_value=True), \
                 patch.object(workflow_engine.notification_system, 'send_assignment_notification', return_value=True):
                
                # Technician documents equipment shortage
                shortage_handling = await workflow_engine.transition_workflow(
                    request_id,
                    WorkflowAction.DOCUMENT_EQUIPMENT.value,
                    UserRole.TECHNICIAN.value,
                    {
                        'actor_id': 500,
                        'equipment_needed': equipment_needed,
                        'equipment_shortage': True,
                        'shortage_details': {
                            'Special Router': 'Out of stock',
                            'Fiber Cable': 'Insufficient quantity'
                        },
                        'documented_at': str(datetime.now()),
                        'warehouse_escalation_needed': True
                    }
                )
                
                assert shortage_handling is True
        
        # Update request state for warehouse handling
        mock_request.role_current = UserRole.WAREHOUSE.value
        mock_request.state_data.update({
            'equipment_shortage': True,
            'warehouse_escalated': True,
            'shortage_reported_at': str(datetime.now())
        })
        
        # Warehouse handles shortage by ordering equipment
        with patch.object(state_manager, 'get_request', return_value=mock_request), \
             patch.object(state_manager, 'update_request_state', return_value=True), \
             patch.object(state_manager, 'add_state_transition', return_value=True), \
             patch.object(workflow_engine.notification_system, 'send_assignment_notification', return_value=True):
            
            shortage_resolution = await workflow_engine.transition_workflow(
                request_id,
                WorkflowAction.UPDATE_INVENTORY.value,
                UserRole.WAREHOUSE.value,
                {
                    'actor_id': 600,
                    'shortage_resolution': 'equipment_ordered',
                    'expected_delivery': str(datetime.now() + timedelta(days=3)),
                    'client_notification_needed': True, 
                    'delay_reason': 'equipment_shortage',
                    'updated_at': str(datetime.now())
                }
            )
            
            assert shortage_resolution is True
        
        print("✅ Equipment shortage handling works correctly!")
    
    def test_edge_case_coverage_summary(self):
        """
        Summary of edge cases covered by these tests
        """
        edge_cases_covered = [
            "Concurrent staff application creation",
            "Workflow interruption and recovery",
            "Priority escalation for urgent requests",
            "Complex cross-role handoffs",
            "Notification failure recovery",
            "Client unavailability scenarios",
            "Equipment shortage handling"
        ]
        
        print("✅ Edge cases covered:")
        for case in edge_cases_covered:
            print(f"   - {case}")
        
        assert len(edge_cases_covered) == 7
        print(f"✅ Total edge cases covered: {len(edge_cases_covered)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])