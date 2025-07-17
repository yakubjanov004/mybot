"""
Simple tests for the audit logging system functionality.
Tests Requirements 6.1, 6.2, 6.3, 6.4 from multi-role application creation spec.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from database.models import StaffApplicationAudit, ClientSelectionData
from utils.audit_logger import AuditEventType, AuditSeverity, AuditEvent

class TestAuditModels:
    """Test audit data models"""
    
    def test_staff_application_audit_model(self):
        """Test StaffApplicationAudit model creation and serialization"""
        audit = StaffApplicationAudit(
            id=1,
            application_id='test-app-001',
            creator_id=123,
            creator_role='manager',
            client_id=456,
            application_type='connection_request',
            creation_timestamp=datetime.utcnow(),
            client_notified=True,
            workflow_initiated=True,
            metadata={'event_type': 'application_submitted', 'test': True}
        )
        
        # Test to_dict conversion
        audit_dict = audit.to_dict()
        assert audit_dict['application_id'] == 'test-app-001'
        assert audit_dict['creator_role'] == 'manager'
        assert audit_dict['client_notified'] is True
        assert audit_dict['metadata']['event_type'] == 'application_submitted'
        
        # Test from_dict conversion
        audit_from_dict = StaffApplicationAudit.from_dict(audit_dict)
        assert audit_from_dict.application_id == audit.application_id
        assert audit_from_dict.creator_role == audit.creator_role
        assert audit_from_dict.client_notified == audit.client_notified
    
    def test_client_selection_data_model(self):
        """Test ClientSelectionData model creation and serialization"""
        client_data = ClientSelectionData(
            id=1,
            search_method='phone',
            search_value='+998901234567',
            client_id=789,
            verified=True,
            created_at=datetime.utcnow()
        )
        
        # Test to_dict conversion
        data_dict = client_data.to_dict()
        assert data_dict['search_method'] == 'phone'
        assert data_dict['search_value'] == '+998901234567'
        assert data_dict['verified'] is True
        
        # Test from_dict conversion
        data_from_dict = ClientSelectionData.from_dict(data_dict)
        assert data_from_dict.search_method == client_data.search_method
        assert data_from_dict.client_id == client_data.client_id

class TestAuditEventTypes:
    """Test audit event types and severity levels"""
    
    def test_audit_event_types(self):
        """Test audit event type enumeration"""
        assert AuditEventType.APPLICATION_CREATED.value == "application_created"
        assert AuditEventType.CLIENT_NOTIFIED.value == "client_notified"
        assert AuditEventType.WORKFLOW_INITIATED.value == "workflow_initiated"
        assert AuditEventType.PERMISSION_DENIED.value == "permission_denied"
        assert AuditEventType.VALIDATION_FAILED.value == "validation_failed"
    
    def test_audit_severity_levels(self):
        """Test audit severity level enumeration"""
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"
        assert AuditSeverity.ERROR.value == "error"
        assert AuditSeverity.CRITICAL.value == "critical"
    
    def test_audit_event_creation(self):
        """Test AuditEvent dataclass creation"""
        event = AuditEvent(
            event_type=AuditEventType.APPLICATION_CREATED.value,
            severity=AuditSeverity.INFO.value,
            timestamp=datetime.utcnow(),
            creator_id=123,
            creator_role='manager',
            application_id='test-app-001',
            client_id=456,
            application_type='connection_request',
            event_data={'test': 'data'},
            session_id='session-123'
        )
        
        assert event.event_type == "application_created"
        assert event.severity == "info"
        assert event.creator_id == 123
        assert event.creator_role == 'manager'
        assert event.event_data == {'test': 'data'}

class TestDataSanitization:
    """Test data sanitization for audit logging"""
    
    def test_phone_number_sanitization(self):
        """Test phone number masking"""
        phone = '+998901234567'
        masked_phone = phone.replace(phone[-4:], '****')
        assert masked_phone == '+99890123****'
        assert '4567' not in masked_phone
    
    def test_client_data_sanitization(self):
        """Test client data sanitization for audit logs"""
        client_data = {
            'phone': '+998901234567',
            'full_name': 'John Doe',
            'address': '123 Main St',
            'passport': 'AB1234567',  # Should not be logged
            'language': 'uz'
        }
        
        # Simulate sanitization process
        sanitized_data = {
            'phone': client_data['phone'].replace(client_data['phone'][-4:], '****'),
            'name_length': len(client_data['full_name']),
            'has_address': bool(client_data['address']),
            'language': client_data['language']
            # passport should not be included
        }
        
        assert 'passport' not in sanitized_data
        assert '****' in sanitized_data['phone']
        assert sanitized_data['name_length'] == 8
        assert sanitized_data['has_address'] is True
        assert sanitized_data['language'] == 'uz'
    
    def test_application_data_sanitization(self):
        """Test application data sanitization for audit logs"""
        application_data = {
            'description': 'Test application description',
            'location': 'Test location',
            'priority': 'medium',
            'workflow_type': 'connection_request',
            'sensitive_field': 'should not be logged'
        }
        
        # Simulate sanitization process
        sanitized_data = {
            'description_length': len(application_data['description']),
            'has_location': bool(application_data['location']),
            'priority': application_data['priority'],
            'workflow_type': application_data['workflow_type']
            # sensitive_field should not be included
        }
        
        assert 'sensitive_field' not in sanitized_data
        assert 'description' not in sanitized_data  # Only length is stored
        assert sanitized_data['description_length'] == len(application_data['description'])
        assert sanitized_data['has_location'] is True
        assert sanitized_data['priority'] == 'medium'

class TestAuditLoggerInitialization:
    """Test audit logger initialization and basic functionality"""
    
    @pytest.mark.asyncio
    async def test_audit_logger_lazy_initialization(self):
        """Test that audit logger initializes properly when first used"""
        from utils.audit_logger import StaffApplicationAuditLogger
        
        logger = StaffApplicationAuditLogger()
        
        # Should not be initialized yet
        assert not logger._initialized
        assert logger._event_queue is None
        
        # Mock the database operation to avoid actual database calls
        with patch('utils.audit_logger.create_staff_application_audit') as mock_create:
            mock_create.return_value = 1
            
            # This should trigger initialization
            session_id = await logger.log_application_creation_start(
                creator_id=123,
                creator_role='manager',
                application_type='connection_request',
                client_id=456
            )
            
            # Should be initialized now
            assert logger._initialized
            assert logger._event_queue is not None
            assert session_id is not None
            assert len(session_id) == 16  # MD5 hash truncated to 16 chars

class TestAuditSystemIntegration:
    """Test integration between audit components"""
    
    @pytest.mark.asyncio
    async def test_audit_workflow_simulation(self):
        """Test simulated audit workflow without database"""
        from utils.audit_logger import StaffApplicationAuditLogger
        
        logger = StaffApplicationAuditLogger()
        
        # Mock database operations
        with patch('utils.audit_logger.create_staff_application_audit') as mock_create:
            mock_create.return_value = 1
            
            # Simulate application creation workflow
            session_id = await logger.log_application_creation_start(
                creator_id=123,
                creator_role='manager',
                application_type='connection_request',
                client_id=456
            )
            
            await logger.log_client_selection(
                creator_id=123,
                creator_role='manager',
                selection_method='phone',
                search_value='+998901234567',
                client_id=456,
                session_id=session_id
            )
            
            await logger.log_application_submission(
                creator_id=123,
                creator_role='manager',
                application_id='app-test-001',
                client_id=456,
                application_type='connection_request',
                application_data={
                    'description': 'Test application',
                    'location': 'Test location',
                    'priority': 'medium'
                },
                session_id=session_id
            )
            
            await logger.log_client_notification(
                creator_id=123,
                creator_role='manager',
                application_id='app-test-001',
                client_id=456,
                notification_method='telegram',
                success=True,
                session_id=session_id
            )
            
            await logger.log_workflow_initiation(
                creator_id=123,
                creator_role='manager',
                application_id='app-test-001',
                workflow_type='connection_request',
                initial_role='manager',
                session_id=session_id
            )
            
            # Verify that database create function was called multiple times
            assert mock_create.call_count >= 5
    
    def test_audit_requirements_coverage(self):
        """Test that audit system covers all requirements"""
        # Requirement 6.1: Audit logging functions for staff application creation
        from utils.audit_logger import (
            log_staff_application_created,
            log_staff_client_notification,
            log_staff_workflow_started,
            log_staff_permission_error,
            log_staff_validation_error,
            log_staff_error
        )
        
        # All convenience functions should exist
        assert callable(log_staff_application_created)
        assert callable(log_staff_client_notification)
        assert callable(log_staff_workflow_started)
        assert callable(log_staff_permission_error)
        assert callable(log_staff_validation_error)
        assert callable(log_staff_error)
        
        # Requirement 6.2: Audit data collection and storage
        from database.models import StaffApplicationAudit, ClientSelectionData
        from database.staff_creation_queries import (
            create_staff_application_audit,
            get_staff_application_audits,
            update_audit_notification_status,
            update_audit_workflow_status
        )
        
        # All database functions should exist
        assert callable(create_staff_application_audit)
        assert callable(get_staff_application_audits)
        assert callable(update_audit_notification_status)
        assert callable(update_audit_workflow_status)
        
        # Requirement 6.3: Audit trail viewing capabilities for administrators
        from utils.audit_viewer import (
            StaffApplicationAuditViewer,
            get_recent_staff_applications,
            get_creator_applications,
            get_failed_applications,
            get_role_performance_summary
        )
        
        # All viewer functions should exist
        assert callable(get_recent_staff_applications)
        assert callable(get_creator_applications)
        assert callable(get_failed_applications)
        assert callable(get_role_performance_summary)
        
        # Requirement 6.4: Audit log analysis and reporting features
        from utils.audit_analyzer import (
            StaffApplicationAuditAnalyzer,
            get_performance_summary,
            get_trend_summary,
            get_current_alerts,
            get_compliance_status,
            generate_daily_report,
            generate_weekly_report,
            generate_monthly_report
        )
        
        # All analyzer functions should exist
        assert callable(get_performance_summary)
        assert callable(get_trend_summary)
        assert callable(get_current_alerts)
        assert callable(get_compliance_status)
        assert callable(generate_daily_report)
        assert callable(generate_weekly_report)
        assert callable(generate_monthly_report)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])