"""
Unit tests for Workflow Access Control System
Tests role-based access control, permission validation, and unauthorized access prevention
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from utils.workflow_access_control import WorkflowAccessControl, require_workflow_permission, PermissionTransferManager
from utils.role_based_filtering import RoleBasedRequestFilter
from database.models import UserRole, WorkflowType, WorkflowAction, RequestStatus


class TestWorkflowAccessControl:
    """Test cases for WorkflowAccessControl class"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = conn
        return pool, conn
    
    @pytest.fixture
    def access_control(self, mock_pool):
        """Create WorkflowAccessControl instance with mocked pool"""
        pool, _ = mock_pool
        return WorkflowAccessControl(pool)
    
    @pytest.mark.asyncio
    async def test_validate_workflow_action_client_submit_request(self, access_control):
        """Test client can submit requests"""
        # Test client submitting a request
        valid, reason = await access_control.validate_workflow_action(
            user_id=123,
            user_role=UserRole.CLIENT.value,
            action=WorkflowAction.SUBMIT_REQUEST.value
        )
        
        assert valid is True
        assert "Access granted" in reason
    
    @pytest.mark.asyncio
    async def test_validate_workflow_action_client_unauthorized(self, access_control):
        """Test client cannot perform unauthorized actions"""
        # Test client trying to assign requests
        valid, reason = await access_control.validate_workflow_action(
            user_id=123,
            user_role=UserRole.CLIENT.value,
            action=WorkflowAction.ASSIGN_TO_TECHNICIAN.value
        )
        
        assert valid is False
        assert "not authorized" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_validate_workflow_action_manager_permissions(self, access_control):
        """Test manager permissions"""
        # Test manager can assign to junior manager
        valid, reason = await access_control.validate_workflow_action(
            user_id=456,
            user_role=UserRole.MANAGER.value,
            action=WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value
        )
        
        assert valid is True
        assert "Access granted" in reason
        
        # Test manager cannot perform technician actions
        valid, reason = await access_control.validate_workflow_action(
            user_id=456,
            user_role=UserRole.MANAGER.value,
            action=WorkflowAction.START_INSTALLATION.value
        )
        
        assert valid is False
        assert "not authorized" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_validate_workflow_action_technician_permissions(self, access_control):
        """Test technician permissions"""
        # Test technician can start installation
        valid, reason = await access_control.validate_workflow_action(
            user_id=789,
            user_role=UserRole.TECHNICIAN.value,
            action=WorkflowAction.START_INSTALLATION.value
        )
        
        assert valid is True
        assert "Access granted" in reason
        
        # Test technician can document equipment
        valid, reason = await access_control.validate_workflow_action(
            user_id=789,
            user_role=UserRole.TECHNICIAN.value,
            action=WorkflowAction.DOCUMENT_EQUIPMENT.value
        )
        
        assert valid is True
        assert "Access granted" in reason
    
    @pytest.mark.asyncio
    async def test_validate_workflow_action_admin_full_access(self, access_control):
        """Test admin has full access to all actions"""
        admin_actions = [
            WorkflowAction.SUBMIT_REQUEST.value,
            WorkflowAction.ASSIGN_TO_TECHNICIAN.value,
            WorkflowAction.START_INSTALLATION.value,
            WorkflowAction.UPDATE_INVENTORY.value
        ]
        
        for action in admin_actions:
            valid, reason = await access_control.validate_workflow_action(
                user_id=1,
                user_role=UserRole.ADMIN.value,
                action=action
            )
            
            assert valid is True, f"Admin should have access to {action}"
            assert "Access granted" in reason
    
    @pytest.mark.asyncio
    async def test_validate_request_access_client_own_request(self, access_control, mock_pool):
        """Test client can access their own requests"""
        pool, conn = mock_pool
        
        # Mock database response for client's own request
        conn.fetchrow.return_value = {
            'id': 'req-123',
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 123,
            'role_current ': UserRole.MANAGER.value,
            'current_status': RequestStatus.IN_PROGRESS.value,
            'created_at': datetime.now(),
            'state_data': '{}'
        }
        
        valid, reason = await access_control.validate_request_access(
            user_id=123,
            user_role=UserRole.CLIENT.value,
            request_id='req-123'
        )
        
        assert valid is True
        assert "Own request" in reason
    
    @pytest.mark.asyncio
    async def test_validate_request_access_client_other_request(self, access_control, mock_pool):
        """Test client cannot access other clients' requests"""
        pool, conn = mock_pool
        
        # Mock database response for another client's request
        conn.fetchrow.return_value = {
            'id': 'req-456',
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 456,  # Different client
            'role_current ': UserRole.MANAGER.value,
            'current_status': RequestStatus.IN_PROGRESS.value,
            'created_at': datetime.now(),
            'state_data': '{}'
        }
        
        valid, reason = await access_control.validate_request_access(
            user_id=123,
            user_role=UserRole.CLIENT.value,
            request_id='req-456'
        )
        
        assert valid is False
        assert "can only access own requests" in reason
    
    @pytest.mark.asyncio
    async def test_validate_request_access_staff_assigned_request(self, access_control, mock_pool):
        """Test staff can access requests assigned to their role"""
        pool, conn = mock_pool
        
        # Mock database response for request assigned to technician
        conn.fetchrow.return_value = {
            'id': 'req-789',
            'workflow_type': WorkflowType.TECHNICAL_SERVICE.value,
            'client_id': 123,
            'role_current ': UserRole.TECHNICIAN.value,
            'current_status': RequestStatus.IN_PROGRESS.value,
            'created_at': datetime.now(),
            'state_data': '{}'
        }
        
        # Mock historical involvement check
        conn.fetch.return_value = []
        
        valid, reason = await access_control.validate_request_access(
            user_id=789,
            user_role=UserRole.TECHNICIAN.value,
            request_id='req-789'
        )
        
        assert valid is True
        assert "Assigned request" in reason
    
    @pytest.mark.asyncio
    async def test_validate_request_access_admin_all_requests(self, access_control, mock_pool):
        """Test admin can access all requests"""
        pool, conn = mock_pool
        
        # Mock database response for any request
        conn.fetchrow.return_value = {
            'id': 'req-admin',
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 999,
            'role_current ': UserRole.TECHNICIAN.value,
            'current_status': RequestStatus.IN_PROGRESS.value,
            'created_at': datetime.now(),
            'state_data': '{}'
        }
        
        valid, reason = await access_control.validate_request_access(
            user_id=1,
            user_role=UserRole.ADMIN.value,
            request_id='req-admin'
        )
        
        assert valid is True
        assert "Admin access" in reason
    
    @pytest.mark.asyncio
    async def test_log_access_attempt(self, access_control, mock_pool):
        """Test access attempt logging"""
        pool, conn = mock_pool
        
        # Test successful logging
        result = await access_control.log_access_attempt(
            user_id=123,
            action="test_action",
            resource="test_resource",
            granted=True,
            reason="Test reason"
        )
        
        assert result is True
        conn.execute.assert_called_once()
        
        # Verify the SQL call
        call_args = conn.execute.call_args
        assert "INSERT INTO access_control_logs" in call_args[0][0]
        assert call_args[0][1] == 123  # user_id
        assert call_args[0][2] == "test_action"  # action
        assert call_args[0][3] == "test_resource"  # resource
        assert call_args[0][4] is True  # granted
        assert call_args[0][5] == "Test reason"  # reason
    
    @pytest.mark.asyncio
    async def test_get_user_permissions(self, access_control, mock_pool):
        """Test getting user permissions"""
        pool, conn = mock_pool
        
        # Mock database responses for dynamic permissions
        conn.fetchrow.side_effect = [
            {'active_assignments': 3},  # assignments query
            {'historical_requests': 15}  # history query
        ]
        
        permissions = await access_control.get_user_permissions(
            user_id=456,
            user_role=UserRole.MANAGER.value
        )
        
        assert permissions['user_id'] == 456
        assert permissions['role'] == UserRole.MANAGER.value
        assert 'static_permissions' in permissions
        assert 'dynamic_permissions' in permissions
        assert 'effective_permissions' in permissions
        
        # Check static permissions for manager
        static_perms = permissions['static_permissions']
        assert WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value in static_perms['workflow_actions']
        assert static_perms['can_assign_requests'] is True
        
        # Check dynamic permissions
        dynamic_perms = permissions['dynamic_permissions']
        assert dynamic_perms['active_assignments'] == 3
        assert dynamic_perms['historical_requests'] == 15
    
    @pytest.mark.asyncio
    async def test_get_filtered_requests_for_role_client(self, access_control, mock_pool):
        """Test filtered requests for client role"""
        pool, conn = mock_pool
        
        # Mock database response for client's requests
        conn.fetch.return_value = [
            {
                'id': 'req-1',
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
                'client_id': 123,
                'role_current ': UserRole.MANAGER.value,
                'current_status': RequestStatus.IN_PROGRESS.value,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'priority': 'high',
                'description': 'Test request',
                'location': 'Test location',
                'contact_info': '{}'
            }
        ]
        
        requests = await access_control.get_filtered_requests_for_role(
            user_id=123,
            user_role=UserRole.CLIENT.value
        )
        
        assert len(requests) == 1
        assert requests[0]['id'] == 'req-1'
        assert requests[0]['client_id'] == 123
        
        # Verify the query included client filter
        call_args = conn.fetch.call_args
        assert "sr.client_id = $1" in call_args[0][0]
        assert call_args[0][1] == 123
    
    @pytest.mark.asyncio
    async def test_get_filtered_requests_for_role_staff(self, access_control, mock_pool):
        """Test filtered requests for staff roles"""
        pool, conn = mock_pool
        
        # Mock database response for technician's requests
        conn.fetch.return_value = [
            {
                'id': 'req-2',
                'workflow_type': WorkflowType.TECHNICAL_SERVICE.value,
                'client_id': 456,
                'role_current ': UserRole.TECHNICIAN.value,
                'current_status': RequestStatus.IN_PROGRESS.value,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'priority': 'medium',
                'description': 'Technical issue',
                'location': 'Client location',
                'contact_info': '{}'
            }
        ]
        
        requests = await access_control.get_filtered_requests_for_role(
            user_id=789,
            user_role=UserRole.TECHNICIAN.value
        )
        
        assert len(requests) == 1
        assert requests[0]['role_current '] == UserRole.TECHNICIAN.value
        
        # Verify the query included role filter
        call_args = conn.fetch.call_args
        assert "sr.role_current = $1" in call_args[0][0]
        assert call_args[0][1] == UserRole.TECHNICIAN.value


class TestRoleBasedRequestFilter:
    """Test cases for RoleBasedRequestFilter class"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = conn
        return pool, conn
    
    @pytest.fixture
    def request_filter(self, mock_pool):
        """Create RoleBasedRequestFilter instance with mocked pool"""
        pool, _ = mock_pool
        return RoleBasedRequestFilter(pool)
    
    @pytest.mark.asyncio
    async def test_filter_request_data_client(self, request_filter):
        """Test request data filtering for client role"""
        request_data = {
            'id': 'req-123',
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 123,
            'description': 'Test request',
            'location': 'Test location',
            'priority': 'high',
            'current_status': RequestStatus.IN_PROGRESS.value,
            'state_data': {'internal_notes': 'Secret info', 'client_comments': 'Public info'},
            'equipment_used': [{'name': 'Router', 'quantity': 1}],
            'inventory_updated': True
        }
        
        filtered_data = await request_filter.filter_request_data(
            user_id=123,
            user_role=UserRole.CLIENT.value,
            request_data=request_data
        )
        
        # Client should see basic fields but not sensitive data
        assert 'id' in filtered_data
        assert 'description' in filtered_data
        assert 'location' in filtered_data
        assert 'priority' in filtered_data
        assert 'current_status' in filtered_data
        
        # Client should not see sensitive fields
        assert 'state_data' not in filtered_data
        assert 'equipment_used' not in filtered_data
        assert 'inventory_updated' not in filtered_data
        
        # Should have computed fields
        assert 'user_permissions' in filtered_data
        assert 'is_own_request' in filtered_data
    
    @pytest.mark.asyncio
    async def test_filter_request_data_technician(self, request_filter):
        """Test request data filtering for technician role"""
        request_data = {
            'id': 'req-456',
            'workflow_type': WorkflowType.TECHNICAL_SERVICE.value,
            'client_id': 789,
            'description': 'Technical issue',
            'location': 'Client site',
            'priority': 'medium',
            'role_current ': UserRole.TECHNICIAN.value,
            'current_status': RequestStatus.IN_PROGRESS.value,
            'state_data': {'technician_notes': 'Diagnostic info', 'warehouse_decision': 'required'},
            'equipment_used': [{'name': 'Cable', 'quantity': 2}],
            'inventory_updated': False,
            'contact_info': {'phone': '123-456-7890', 'name': 'John Doe'}
        }
        
        filtered_data = await request_filter.filter_request_data(
            user_id=456,
            user_role=UserRole.TECHNICIAN.value,
            request_data=request_data
        )
        
        # Technician should see most fields including equipment
        assert 'id' in filtered_data
        assert 'description' in filtered_data
        assert 'state_data' in filtered_data
        assert 'equipment_used' in filtered_data
        assert 'contact_info' in filtered_data
        
        # But not inventory management fields
        assert 'inventory_updated' not in filtered_data
        
        # Should have assignment flag
        assert filtered_data.get('is_assigned_to_me') is True
    
    @pytest.mark.asyncio
    async def test_filter_request_data_admin(self, request_filter):
        """Test request data filtering for admin role"""
        request_data = {
            'id': 'req-admin',
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'client_id': 999,
            'description': 'Admin test',
            'state_data': {'all_internal_data': 'visible'},
            'equipment_used': [{'name': 'All equipment', 'quantity': 10}],
            'inventory_updated': True,
            'sensitive_field': 'admin_only_data'
        }
        
        filtered_data = await request_filter.filter_request_data(
            user_id=1,
            user_role=UserRole.ADMIN.value,
            request_data=request_data
        )
        
        # Admin should see all data unchanged
        assert filtered_data == request_data
    
    @pytest.mark.asyncio
    async def test_filter_requests_for_user_access_control(self, request_filter):
        """Test request filtering with access control validation"""
        requests = [
            {'id': 'req-1', 'client_id': 123, 'description': 'Request 1'},
            {'id': 'req-2', 'client_id': 456, 'description': 'Request 2'},
            {'id': 'req-3', 'client_id': 123, 'description': 'Request 3'}
        ]
        
        # Mock access control to allow only requests 1 and 3
        with patch.object(request_filter.access_control, 'validate_request_access') as mock_validate:
            mock_validate.side_effect = [
                (True, "Access granted"),   # req-1
                (False, "Access denied"),   # req-2
                (True, "Access granted")    # req-3
            ]
            
            filtered_requests = await request_filter.filter_requests_for_user(
                user_id=123,
                user_role=UserRole.CLIENT.value,
                requests=requests
            )
            
            # Should only return accessible requests
            assert len(filtered_requests) == 2
            assert filtered_requests[0]['id'] == 'req-1'
            assert filtered_requests[1]['id'] == 'req-3'
    
    @pytest.mark.asyncio
    async def test_get_accessible_request_ids(self, request_filter):
        """Test getting accessible request IDs"""
        # Mock the access control method
        mock_requests = [
            {'id': 'req-1'},
            {'id': 'req-2'},
            {'id': 'req-3'}
        ]
        
        with patch.object(request_filter.access_control, 'get_filtered_requests_for_role') as mock_get:
            mock_get.return_value = mock_requests
            
            accessible_ids = await request_filter.get_accessible_request_ids(
                user_id=123,
                user_role=UserRole.CLIENT.value
            )
            
            assert accessible_ids == {'req-1', 'req-2', 'req-3'}
    
    @pytest.mark.asyncio
    async def test_get_request_summary_for_role(self, request_filter):
        """Test getting request summary statistics"""
        mock_requests = [
            {
                'id': 'req-1',
                'current_status': RequestStatus.IN_PROGRESS.value,
                'priority': 'high',
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value
            },
            {
                'id': 'req-2',
                'current_status': RequestStatus.COMPLETED.value,
                'priority': 'medium',
                'workflow_type': WorkflowType.TECHNICAL_SERVICE.value
            },
            {
                'id': 'req-3',
                'current_status': RequestStatus.IN_PROGRESS.value,
                'priority': 'high',
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value
            }
        ]
        
        with patch.object(request_filter.access_control, 'get_filtered_requests_for_role') as mock_get:
            mock_get.return_value = mock_requests
            
            summary = await request_filter.get_request_summary_for_role(
                user_id=456,
                user_role=UserRole.MANAGER.value
            )
            
            assert summary['user_id'] == 456
            assert summary['user_role'] == UserRole.MANAGER.value
            assert summary['total_requests'] == 3
            
            # Check status breakdown
            assert summary['status_breakdown'][RequestStatus.IN_PROGRESS.value] == 2
            assert summary['status_breakdown'][RequestStatus.COMPLETED.value] == 1
            
            # Check priority breakdown
            assert summary['priority_breakdown']['high'] == 2
            assert summary['priority_breakdown']['medium'] == 1
            
            # Check workflow breakdown
            assert summary['workflow_breakdown'][WorkflowType.CONNECTION_REQUEST.value] == 2
            assert summary['workflow_breakdown'][WorkflowType.TECHNICAL_SERVICE.value] == 1


class TestAccessControlDecorator:
    """Test cases for access control decorator"""
    
    @pytest.mark.asyncio
    async def test_require_workflow_permission_granted(self):
        """Test decorator allows access when permission is granted"""
        
        @require_workflow_permission(WorkflowAction.SUBMIT_REQUEST.value)
        async def test_handler(user_id=None, user_role=None, **kwargs):
            return {'success': True, 'message': 'Handler executed'}
        
        with patch('utils.workflow_access_control.WorkflowAccessControl') as mock_ac_class:
            mock_ac = AsyncMock()
            mock_ac_class.return_value = mock_ac
            mock_ac.validate_workflow_action.return_value = (True, "Access granted")
            
            result = await test_handler(
                user_id=123,
                user_role=UserRole.CLIENT.value
            )
            
            assert result['success'] is True
            assert result['message'] == 'Handler executed'
    
    @pytest.mark.asyncio
    async def test_require_workflow_permission_denied(self):
        """Test decorator blocks access when permission is denied"""
        
        @require_workflow_permission(WorkflowAction.ASSIGN_TO_TECHNICIAN.value)
        async def test_handler(user_id=None, user_role=None, **kwargs):
            return {'success': True, 'message': 'Handler executed'}
        
        with patch('utils.workflow_access_control.WorkflowAccessControl') as mock_ac_class:
            mock_ac = AsyncMock()
            mock_ac_class.return_value = mock_ac
            mock_ac.validate_workflow_action.return_value = (False, "Access denied: insufficient permissions")
            
            result = await test_handler(
                user_id=123,
                user_role=UserRole.CLIENT.value
            )
            
            assert result['success'] is False
            assert 'Access denied' in result['error']
    
    @pytest.mark.asyncio
    async def test_require_workflow_permission_missing_auth(self):
        """Test decorator handles missing authentication"""
        
        @require_workflow_permission(WorkflowAction.SUBMIT_REQUEST.value)
        async def test_handler(**kwargs):
            return {'success': True, 'message': 'Handler executed'}
        
        result = await test_handler()
        
        assert result['success'] is False
        assert 'Authentication required' in result['error']


class TestPermissionTransferManager:
    """Test cases for PermissionTransferManager class"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        transaction = AsyncMock()
        conn.transaction.return_value.__aenter__.return_value = transaction
        pool.acquire.return_value.__aenter__.return_value = conn
        return pool, conn
    
    @pytest.fixture
    def transfer_manager(self, mock_pool):
        """Create PermissionTransferManager instance with mocked pool"""
        pool, _ = mock_pool
        return PermissionTransferManager(pool)
    
    @pytest.mark.asyncio
    async def test_transfer_request_permissions_success(self, transfer_manager, mock_pool):
        """Test successful permission transfer"""
        pool, conn = mock_pool
        
        result = await transfer_manager.transfer_request_permissions(
            request_id='req-123',
            from_role=UserRole.MANAGER.value,
            to_role=UserRole.JUNIOR_MANAGER.value,
            actor_id=456
        )
        
        assert result is True
        
        # Verify database calls
        assert conn.execute.call_count == 2  # Update request + Insert transition
        
        # Check update query
        update_call = conn.execute.call_args_list[0]
        assert "UPDATE service_requests" in update_call[0][0]
        assert update_call[0][1] == UserRole.JUNIOR_MANAGER.value
        assert update_call[0][3] == 'req-123'
        
        # Check transition log
        transition_call = conn.execute.call_args_list[1]
        assert "INSERT INTO state_transitions" in transition_call[0][0]
        assert transition_call[0][1] == 'req-123'
        assert transition_call[0][2] == UserRole.MANAGER.value
        assert transition_call[0][3] == UserRole.JUNIOR_MANAGER.value
        assert transition_call[0][4] == 456
    
    @pytest.mark.asyncio
    async def test_validate_permission_transfer_valid(self, transfer_manager, mock_pool):
        """Test valid permission transfer validation"""
        pool, conn = mock_pool
        
        # Mock request data
        conn.fetchrow.return_value = {
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value
        }
        
        # Mock access control validation
        with patch.object(transfer_manager.access_control, 'validate_workflow_action') as mock_validate:
            mock_validate.return_value = (True, "Transfer allowed")
            
            valid, reason = await transfer_manager.validate_permission_transfer(
                request_id='req-123',
                from_role=UserRole.MANAGER.value,
                to_role=UserRole.JUNIOR_MANAGER.value,
                actor_id=456,
                actor_role=UserRole.MANAGER.value
            )
            
            assert valid is True
            assert "Permission transfer valid" in reason
    
    @pytest.mark.asyncio
    async def test_validate_permission_transfer_invalid_transition(self, transfer_manager, mock_pool):
        """Test invalid role transition validation"""
        pool, conn = mock_pool
        
        # Mock request data
        conn.fetchrow.return_value = {
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value
        }
        
        # Mock access control validation
        with patch.object(transfer_manager.access_control, 'validate_workflow_action') as mock_validate:
            mock_validate.return_value = (True, "Transfer allowed")
            
            # Try invalid transition (client to warehouse)
            valid, reason = await transfer_manager.validate_permission_transfer(
                request_id='req-123',
                from_role=UserRole.CLIENT.value,
                to_role=UserRole.WAREHOUSE.value,
                actor_id=456,
                actor_role=UserRole.MANAGER.value
            )
            
            assert valid is False
            assert "Invalid role transition" in reason
    
    @pytest.mark.asyncio
    async def test_validate_permission_transfer_actor_unauthorized(self, transfer_manager, mock_pool):
        """Test unauthorized actor validation"""
        pool, conn = mock_pool
        
        # Mock access control validation to deny
        with patch.object(transfer_manager.access_control, 'validate_workflow_action') as mock_validate:
            mock_validate.return_value = (False, "Actor not authorized")
            
            valid, reason = await transfer_manager.validate_permission_transfer(
                request_id='req-123',
                from_role=UserRole.MANAGER.value,
                to_role=UserRole.JUNIOR_MANAGER.value,
                actor_id=123,  # Client trying to transfer
                actor_role=UserRole.CLIENT.value
            )
            
            assert valid is False
            assert "Actor cannot transfer permissions" in reason


class TestEnhancedAccessControl:
    """Test cases for enhanced access control features"""
    
    @pytest.fixture
    def mock_pool(self):
        """Mock database pool"""
        pool = AsyncMock()
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = conn
        return pool, conn
    
    @pytest.fixture
    def access_control(self, mock_pool):
        """Create WorkflowAccessControl instance with mocked pool"""
        pool, _ = mock_pool
        return WorkflowAccessControl(pool)
    
    @pytest.mark.asyncio
    async def test_unauthorized_access_logging(self, access_control, mock_pool):
        """Test that unauthorized access attempts are logged"""
        pool, conn = mock_pool
        
        # Test unauthorized action
        valid, reason = await access_control.validate_workflow_action(
            user_id=123,
            user_role=UserRole.CLIENT.value,
            action=WorkflowAction.ASSIGN_TO_TECHNICIAN.value
        )
        
        assert valid is False
        assert "not authorized" in reason.lower()
        
        # Verify logging was called
        conn.execute.assert_called()
        log_call = conn.execute.call_args
        assert "INSERT INTO access_control_logs" in log_call[0][0]
        assert log_call[0][1] == 123  # user_id
        assert log_call[0][4] is False  # granted = False
    
    @pytest.mark.asyncio
    async def test_role_based_request_filtering_client(self, access_control, mock_pool):
        """Test role-based request filtering for clients"""
        pool, conn = mock_pool
        
        # Mock database response for client's requests only
        conn.fetch.return_value = [
            {
                'id': 'req-1',
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
                'client_id': 123,
                'role_current ': UserRole.MANAGER.value,
                'current_status': RequestStatus.IN_PROGRESS.value,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'priority': 'high',
                'description': 'Client request',
                'location': 'Test location',
                'contact_info': '{}',
                'state_data': '{}',
                'equipment_used': '[]',
                'inventory_updated': False,
                'completion_rating': None,
                'feedback_comments': None
            }
        ]
        
        requests = await access_control.get_filtered_requests_for_role(
            user_id=123,
            user_role=UserRole.CLIENT.value
        )
        
        assert len(requests) == 1
        assert requests[0]['client_id'] == 123
        
        # Verify query included client filter
        call_args = conn.fetch.call_args
        assert "sr.client_id = $1" in call_args[0][0]
        assert call_args[0][1] == 123
    
    @pytest.mark.asyncio
    async def test_role_based_request_filtering_staff(self, access_control, mock_pool):
        """Test role-based request filtering for staff roles"""
        pool, conn = mock_pool
        
        # Mock database response for technician's requests
        conn.fetch.return_value = [
            {
                'id': 'req-2',
                'workflow_type': WorkflowType.TECHNICAL_SERVICE.value,
                'client_id': 456,
                'role_current ': UserRole.TECHNICIAN.value,
                'current_status': RequestStatus.IN_PROGRESS.value,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'priority': 'medium',
                'description': 'Technical issue',
                'location': 'Client location',
                'contact_info': '{}',
                'state_data': '{}',
                'equipment_used': '[]',
                'inventory_updated': False,
                'completion_rating': None,
                'feedback_comments': None
            }
        ]
        
        requests = await access_control.get_filtered_requests_for_role(
            user_id=789,
            user_role=UserRole.TECHNICIAN.value
        )
        
        assert len(requests) == 1
        assert requests[0]['role_current '] == UserRole.TECHNICIAN.value
        
        # Verify query included role-based filters
        call_args = conn.fetch.call_args
        query = call_args[0][0]
        assert "sr.role_current = $1" in query
        assert UserRole.TECHNICIAN.value in call_args[0]
    
    @pytest.mark.asyncio
    async def test_workflow_state_transition_validation(self, access_control, mock_pool):
        """Test workflow state transition validation"""
        pool, conn = mock_pool
        
        # Mock request data
        conn.fetchrow.return_value = {
            'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
            'role_current ': UserRole.MANAGER.value,
            'current_status': RequestStatus.IN_PROGRESS.value
        }
        
        # Test valid transition
        valid, reason = await access_control.validate_workflow_action(
            user_id=456,
            user_role=UserRole.MANAGER.value,
            action=WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
            request_id='req-123'
        )
        
        assert valid is True
        assert "Access granted" in reason
    
    @pytest.mark.asyncio
    async def test_assignment_permission_validation(self, access_control, mock_pool):
        """Test assignment permission validation"""
        pool, conn = mock_pool
        
        # Mock request access validation
        conn.fetchrow.side_effect = [
            {  # Request data
                'workflow_type': WorkflowType.CONNECTION_REQUEST.value,
                'role_current ': UserRole.MANAGER.value,
                'current_status': RequestStatus.IN_PROGRESS.value
            },
            {  # Target user data
                'id': 789,
                'role': UserRole.JUNIOR_MANAGER.value,
                'is_active': True
            }
        ]
        
        # Test valid assignment
        valid, reason = await access_control.validate_workflow_action(
            user_id=456,
            user_role=UserRole.MANAGER.value,
            action=WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
            request_id='req-123',
            target_data={'junior_manager_id': 789}
        )
        
        assert valid is True
        assert "Access granted" in reason


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])