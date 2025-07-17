"""
Unit tests for staff creation database queries.
Tests Requirements 1.1, 1.2, 1.3 from the multi-role application creation spec.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from database.staff_creation_queries import (
    create_staff_service_request, get_staff_created_requests,
    update_client_notification_status, create_client_selection_data,
    get_client_selection_data, update_client_selection_verification,
    cleanup_old_client_selection_data, create_staff_application_audit,
    update_audit_notification_status, update_audit_workflow_status,
    get_staff_application_audits, get_audit_by_application_id
)
from database.models import ServiceRequest, ClientSelectionData, StaffApplicationAudit


class TestStaffCreationQueries:
    """Test staff creation database queries"""
    
    def setup_mock_pool_and_conn(self):
        """Helper method to set up mock pool and connection"""
        mock_pool = Mock()
        mock_conn = AsyncMock()
        
        # Create a proper async context manager
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Make acquire() return the context manager directly (not a coroutine)
        mock_pool.acquire.return_value = AsyncContextManager()
        
        return mock_pool, mock_conn
    
    @pytest.mark.asyncio
    @patch('database.staff_creation_queries.logger')
    async def test_create_staff_service_request_success(self, mock_logger):
        """Test successful creation of staff service request"""
        # Create test request
        request = ServiceRequest(
            id='test-123',
            workflow_type='connection_request',
            client_id=456,
            role_current='manager',
            current_status='created',
            created_by_staff=True,
            staff_creator_id=789,
            staff_creator_role='manager',
            creation_source='manager'
        )
        
        # Mock the pool and connection
        mock_pool = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = 'test-123'
        
        # Create a proper async context manager
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Make acquire() return the context manager directly (not a coroutine)
        mock_pool.acquire.return_value = AsyncContextManager()
        
        # Execute
        result = await create_staff_service_request(request, mock_pool)
        
        # Verify
        assert result == 'test-123'
        mock_conn.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_staff_service_request_validation_error(self):
        """Test creation fails with validation error"""
        # Create invalid request (missing staff_creator_id)
        request = ServiceRequest(
            id='test-123',
            created_by_staff=True,
            staff_creator_role='manager',
            creation_source='manager'
        )
        
        # Execute
        result = await create_staff_service_request(request)
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_staff_created_requests(self):
        """Test getting staff created requests"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        
        # Mock database row
        mock_row = {
            'id': 'test-123',
            'workflow_type': 'connection_request',
            'client_id': 456,
            'role_current': 'manager',
            'current_status': 'created',
            'created_by_staff': True,
            'staff_creator_id': 789,
            'staff_creator_role': 'manager',
            'creation_source': 'manager',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'priority': 'medium',
            'description': None,
            'location': None,
            'contact_info': '{}',
            'state_data': '{}',
            'equipment_used': '[]',
            'inventory_updated': False,
            'completion_rating': None,
            'feedback_comments': None,
            'client_notified_at': None
        }
        mock_conn.fetch.return_value = [mock_row]
        
        # Execute
        result = await get_staff_created_requests(789, 10, mock_pool)
        
        # Verify
        assert len(result) == 1
        assert isinstance(result[0], ServiceRequest)
        assert result[0].id == 'test-123'
        assert result[0].staff_creator_id == 789
        mock_conn.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_client_notification_status_success(self):
        """Test successful client notification status update"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.execute.return_value = "UPDATE 1"
        
        # Execute
        now = datetime.now()
        result = await update_client_notification_status('test-123', now, mock_pool)
        
        # Verify
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_client_notification_status_not_found(self):
        """Test client notification status update when request not found"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.execute.return_value = "UPDATE 0"
        
        # Execute
        now = datetime.now()
        result = await update_client_notification_status('test-123', now, mock_pool)
        
        # Verify
        assert result is False
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_client_selection_data_success(self):
        """Test successful creation of client selection data"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.fetchval.return_value = 1
        
        # Create test data
        client_data = ClientSelectionData(
            search_method='phone',
            search_value='+998901234567',
            client_id=123,
            verified=True
        )
        
        # Execute
        result = await create_client_selection_data(client_data, mock_pool)
        
        # Verify
        assert result == 1
        mock_conn.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_client_selection_data_validation_error(self):
        """Test creation fails with validation error"""
        # Create invalid data (invalid search method)
        client_data = ClientSelectionData(
            search_method='invalid_method',
            search_value='test'
        )
        
        # Execute
        result = await create_client_selection_data(client_data)
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_client_selection_data_found(self):
        """Test getting client selection data when found"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        
        # Mock database row
        mock_row = {
            'id': 1,
            'search_method': 'phone',
            'search_value': '+998901234567',
            'client_id': 123,
            'new_client_data': '{}',
            'verified': True,
            'created_at': datetime.now()
        }
        mock_conn.fetchrow.return_value = mock_row
        
        # Execute
        result = await get_client_selection_data(1, mock_pool)
        
        # Verify
        assert result is not None
        assert isinstance(result, ClientSelectionData)
        assert result.id == 1
        assert result.search_method == 'phone'
        mock_conn.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_client_selection_data_not_found(self):
        """Test getting client selection data when not found"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.fetchrow.return_value = None
        
        # Execute
        result = await get_client_selection_data(999, mock_pool)
        
        # Verify
        assert result is None
        mock_conn.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_client_selection_verification(self):
        """Test updating client selection verification"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.execute.return_value = "UPDATE 1"
        
        # Execute
        result = await update_client_selection_verification(1, True, 123, mock_pool)
        
        # Verify
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_client_selection_data(self):
        """Test cleanup of old client selection data"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.execute.return_value = "DELETE 5"
        
        # Execute
        result = await cleanup_old_client_selection_data(7, mock_pool)
        
        # Verify
        assert result == 5
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_staff_application_audit_success(self):
        """Test successful creation of staff application audit"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.fetchval.return_value = 1
        
        # Create test audit
        audit = StaffApplicationAudit(
            application_id='app-123',
            creator_id=456,
            creator_role='manager',
            client_id=789,
            application_type='connection_request',
            creation_timestamp=datetime.now()
        )
        
        # Execute
        result = await create_staff_application_audit(audit, mock_pool)
        
        # Verify
        assert result == 1
        mock_conn.fetchval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_audit_notification_status(self):
        """Test updating audit notification status"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.execute.return_value = "UPDATE 1"
        
        # Execute
        now = datetime.now()
        result = await update_audit_notification_status(1, True, now, mock_pool)
        
        # Verify
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_audit_workflow_status(self):
        """Test updating audit workflow status"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.execute.return_value = "UPDATE 1"
        
        # Execute
        now = datetime.now()
        result = await update_audit_workflow_status(1, True, now, mock_pool)
        
        # Verify
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_staff_application_audits_no_filters(self):
        """Test getting staff application audits without filters"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        
        # Mock database row
        mock_row = {
            'id': 1,
            'application_id': 'app-123',
            'creator_id': 456,
            'creator_role': 'manager',
            'client_id': 789,
            'application_type': 'connection_request',
            'creation_timestamp': datetime.now(),
            'client_notified': False,
            'client_notified_at': None,
            'workflow_initiated': False,
            'workflow_initiated_at': None,
            'metadata': '{}',
            'ip_address': None,
            'user_agent': None,
            'session_id': None
        }
        mock_conn.fetch.return_value = [mock_row]
        
        # Execute
        result = await get_staff_application_audits(pool=mock_pool)
        
        # Verify
        assert len(result) == 1
        assert isinstance(result[0], StaffApplicationAudit)
        assert result[0].id == 1
        assert result[0].application_id == 'app-123'
        mock_conn.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_staff_application_audits_with_filters(self):
        """Test getting staff application audits with filters"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.fetch.return_value = []
        
        # Execute
        result = await get_staff_application_audits(
            creator_id=456,
            client_id=789,
            application_type='connection_request',
            limit=50,
            pool=mock_pool
        )
        
        # Verify
        assert len(result) == 0
        mock_conn.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_audit_by_application_id_found(self):
        """Test getting audit by application ID when found"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        
        # Mock database row
        mock_row = {
            'id': 1,
            'application_id': 'app-123',
            'creator_id': 456,
            'creator_role': 'manager',
            'client_id': 789,
            'application_type': 'connection_request',
            'creation_timestamp': datetime.now(),
            'client_notified': False,
            'client_notified_at': None,
            'workflow_initiated': False,
            'workflow_initiated_at': None,
            'metadata': '{}',
            'ip_address': None,
            'user_agent': None,
            'session_id': None
        }
        mock_conn.fetchrow.return_value = mock_row
        
        # Execute
        result = await get_audit_by_application_id('app-123', mock_pool)
        
        # Verify
        assert result is not None
        assert isinstance(result, StaffApplicationAudit)
        assert result.application_id == 'app-123'
        mock_conn.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_audit_by_application_id_not_found(self):
        """Test getting audit by application ID when not found"""
        # Setup mock pool and connection
        mock_pool, mock_conn = self.setup_mock_pool_and_conn()
        mock_conn.fetchrow.return_value = None
        
        # Execute
        result = await get_audit_by_application_id('app-999', mock_pool)
        
        # Verify
        assert result is None
        mock_conn.fetchrow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test database error handling"""
        # Setup mock pool to raise exception
        mock_pool = Mock()
        mock_pool.acquire.side_effect = Exception("Database connection failed")
        
        # Execute
        request = ServiceRequest(
            id='test-123',
            created_by_staff=True,
            staff_creator_id=789,
            staff_creator_role='manager',
            creation_source='manager'
        )
        result = await create_staff_service_request(request, mock_pool)
        
        # Verify
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])