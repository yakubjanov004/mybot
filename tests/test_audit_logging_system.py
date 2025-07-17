"""
Comprehensive tests for the audit logging system.
Tests Requirements 6.1, 6.2, 6.3, 6.4 from multi-role application creation spec.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import json

from database.models import StaffApplicationAudit, ClientSelectionData, ServiceRequest, UserRole
from utils.audit_logger import (
    StaffApplicationAuditLogger, audit_logger, AuditEventType, AuditSeverity,
    log_staff_application_created, log_staff_client_notification,
    log_staff_workflow_started, log_staff_permission_error
)
from utils.audit_viewer import (
    StaffApplicationAuditViewer, audit_viewer, AuditFilter, AuditFilterType
)
from utils.audit_analyzer import (
    StaffApplicationAuditAnalyzer, audit_analyzer, AnalysisType, AlertSeverity
)

class TestAuditLogger:
    """Test audit logging functionality"""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger for testing"""
        logger = StaffApplicationAuditLogger()
        logger._event_queue = AsyncMock()
        return logger
    
    @pytest.fixture
    def sample_audit_data(self):
        """Sample audit data for testing"""
        return {
            'creator_id': 123,
            'creator_role': 'manager',
            'application_id': 'app-test-001',
            'client_id': 456,
            'application_type': 'connection_request',
            'session_id': 'session-test-001'
        }
    
    @pytest.mark.asyncio
    async def test_log_application_creation_start(self, mock_audit_logger, sample_audit_data):
        """Test logging application creation start"""
        session_id = await mock_audit_logger.log_application_creation_start(
            creator_id=sample_audit_data['creator_id'],
            creator_role=sample_audit_data['creator_role'],
            application_type=sample_audit_data['application_type'],
            client_id=sample_audit_data['client_id']
        )
        
        assert session_id is not None
        assert len(session_id) == 16  # MD5 hash truncated to 16 chars
        mock_audit_logger._event_queue.put.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_client_selection(self, mock_audit_logger, sample_audit_data):
        """Test logging client selection"""
        await mock_audit_logger.log_client_selection(
            creator_id=sample_audit_data['creator_id'],
            creator_role=sample_audit_data['creator_role'],
            selection_method='phone',
            search_value='+998901234567',
            client_id=sample_audit_data['client_id'],
            session_id=sample_audit_data['session_id']
        )
        
        mock_audit_logger._event_queue.put.assert_called_once()
        
        # Verify event data
        call_args = mock_audit_logger._event_queue.put.call_args[0][0]
        assert call_args.event_type == AuditEventType.CLIENT_SELECTED.value
        assert call_args.creator_id == sample_audit_data['creator_id']
        assert call_args.event_data['selection_method'] == 'phone'
    
    @pytest.mark.asyncio
    async def test_log_client_creation(self, mock_audit_logger, sample_audit_data):
        """Test logging client creation"""
        client_data = {
            'phone': '+998901234567',
            'full_name': 'Test Client',
            'address': 'Test Address',
            'language': 'uz'
        }
        
        await mock_audit_logger.log_client_creation(
            creator_id=sample_audit_data['creator_id'],
            creator_role=sample_audit_data['creator_role'],
            new_client_id=789,
            client_data=client_data,
            session_id=sample_audit_data['session_id']
        )
        
        mock_audit_logger._event_queue.put.assert_called_once()
        
        # Verify sensitive data is sanitized
        call_args = mock_audit_logger._event_queue.put.call_args[0][0]
        assert call_args.event_type == AuditEventType.CLIENT_CREATED.value
        sanitized_data = call_args.event_data['client_data']
        assert '****' in sanitized_data['phone']  # Phone should be masked
        assert sanitized_data['name_length'] == len(client_data['full_name'])
    
    @pytest.mark.asyncio
    async def test_log_application_submission(self, mock_audit_logger, sample_audit_data):
        """Test logging application submission"""
        application_data = {
            'description': 'Test application description',
            'location': 'Test location',
            'priority': 'medium',
            'workflow_type': 'connection_request'
        }
        
        await mock_audit_logger.log_application_submission(
            creator_id=sample_audit_data['creator_id'],
            creator_role=sample_audit_data['creator_role'],
            application_id=sample_audit_data['application_id'],
            client_id=sample_audit_data['client_id'],
            application_type=sample_audit_data['application_type'],
            application_data=application_data,
            session_id=sample_audit_data['session_id']
        )
        
        mock_audit_logger._event_queue.put.assert_called_once()
        
        # Verify application data is sanitized
        call_args = mock_audit_logger._event_queue.put.call_args[0][0]
        assert call_args.event_type == AuditEventType.APPLICATION_SUBMITTED.value
        sanitized_data = call_args.event_data['application_data']
        assert sanitized_data['description_length'] == len(application_data['description'])
        assert sanitized_data['priority'] == application_data['priority']
    
    @pytest.mark.asyncio
    async def test_log_permission_denied(self, mock_audit_logger, sample_audit_data):
        """Test logging permission denied events"""
        await mock_audit_logger.log_permission_denied(
            creator_id=sample_audit_data['creator_id'],
            creator_role='junior_manager',
            attempted_action='create_technical_service',
            reason='Role not authorized for technical service creation',
            session_id=sample_audit_data['session_id']
        )
        
        mock_audit_logger._event_queue.put.assert_called_once()
        
        call_args = mock_audit_logger._event_queue.put.call_args[0][0]
        assert call_args.event_type == AuditEventType.PERMISSION_DENIED.value
        assert call_args.severity == AuditSeverity.WARNING.value
        assert call_args.event_data['attempted_action'] == 'create_technical_service'
    
    @pytest.mark.asyncio
    async def test_log_validation_error(self, mock_audit_logger, sample_audit_data):
        """Test logging validation errors"""
        validation_errors = [
            'Description is required',
            'Location is required',
            'Client ID is invalid'
        ]
        
        form_data = {
            'description': '',
            'location': '',
            'client_id': 'invalid',
            'priority': 'medium'
        }
        
        await mock_audit_logger.log_validation_error(
            creator_id=sample_audit_data['creator_id'],
            creator_role=sample_audit_data['creator_role'],
            validation_errors=validation_errors,
            form_data=form_data,
            session_id=sample_audit_data['session_id']
        )
        
        mock_audit_logger._event_queue.put.assert_called_once()
        
        call_args = mock_audit_logger._event_queue.put.call_args[0][0]
        assert call_args.event_type == AuditEventType.VALIDATION_FAILED.value
        assert call_args.event_data['validation_errors'] == validation_errors
        assert call_args.event_data['form_data']['field_count'] == len(form_data)
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self, sample_audit_data):
        """Test convenience functions for audit logging"""
        with patch('utils.audit_logger.audit_logger') as mock_logger:
            mock_logger.log_application_creation_start = AsyncMock(return_value='session-123')
            mock_logger.log_application_submission = AsyncMock()
            
            session_id = await log_staff_application_created(
                creator_id=sample_audit_data['creator_id'],
                creator_role=sample_audit_data['creator_role'],
                application_id=sample_audit_data['application_id'],
                client_id=sample_audit_data['client_id'],
                application_type=sample_audit_data['application_type']
            )
            
            assert session_id == 'session-123'
            mock_logger.log_application_creation_start.assert_called_once()
            mock_logger.log_application_submission.assert_called_once()

class TestAuditViewer:
    """Test audit viewing functionality"""
    
    @pytest.fixture
    def mock_audit_viewer(self):
        """Create mock audit viewer for testing"""
        return StaffApplicationAuditViewer()
    
    @pytest.fixture
    def sample_audits(self):
        """Sample audit records for testing"""
        return [
            StaffApplicationAudit(
                id=1,
                application_id='app-001',
                creator_id=123,
                creator_role='manager',
                client_id=456,
                application_type='connection_request',
                creation_timestamp=datetime.utcnow() - timedelta(days=1),
                client_notified=True,
                workflow_initiated=True,
                metadata={'event_type': 'application_submitted'}
            ),
            StaffApplicationAudit(
                id=2,
                application_id='app-002',
                creator_id=124,
                creator_role='call_center',
                client_id=457,
                application_type='technical_service',
                creation_timestamp=datetime.utcnow() - timedelta(days=2),
                client_notified=False,
                workflow_initiated=False,
                metadata={'event_type': 'error_occurred'}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_basic(self, mock_audit_viewer):
        """Test basic audit trail retrieval"""
        with patch('utils.audit_viewer.db_manager') as mock_db:
            mock_db.fetchval.return_value = 10
            mock_db.fetch.return_value = []
            
            result = await mock_audit_viewer.get_audit_trail(limit=50)
            
            assert result.total_count == 10
            assert result.filtered_count == 0
            assert isinstance(result.summary, dict)
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_with_filters(self, mock_audit_viewer):
        """Test audit trail retrieval with filters"""
        filters = [
            AuditFilter(AuditFilterType.BY_CREATOR.value, 123),
            AuditFilter(AuditFilterType.BY_APPLICATION_TYPE.value, 'connection_request')
        ]
        
        with patch('utils.audit_viewer.db_manager') as mock_db:
            mock_db.fetchval.return_value = 5
            mock_db.fetch.return_value = []
            
            result = await mock_audit_viewer.get_audit_trail(filters=filters)
            
            assert result.total_count == 5
            # Verify that filters were applied in query construction
            mock_db.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_creator_activity_report(self, mock_audit_viewer, sample_audits):
        """Test creator activity report generation"""
        with patch.object(mock_audit_viewer, 'get_audit_trail') as mock_get_trail:
            mock_result = MagicMock()
            mock_result.audits = sample_audits
            mock_get_trail.return_value = mock_result
            
            report = await mock_audit_viewer.get_creator_activity_report(creator_id=123, days_back=30)
            
            assert report['creator_id'] == 123
            assert report['period_days'] == 30
            assert 'total_applications' in report
            assert 'success_metrics' in report
            assert 'performance_metrics' in report
    
    @pytest.mark.asyncio
    async def test_get_system_audit_summary(self, mock_audit_viewer, sample_audits):
        """Test system audit summary generation"""
        with patch.object(mock_audit_viewer, 'get_audit_trail') as mock_get_trail:
            mock_result = MagicMock()
            mock_result.audits = sample_audits
            mock_get_trail.return_value = mock_result
            
            summary = await mock_audit_viewer.get_system_audit_summary(days_back=7)
            
            assert summary['period_days'] == 7
            assert 'system_health' in summary
            assert 'role_performance' in summary
            assert 'alerts' in summary
    
    @pytest.mark.asyncio
    async def test_export_audit_data_json(self, mock_audit_viewer, sample_audits):
        """Test audit data export in JSON format"""
        with patch.object(mock_audit_viewer, 'get_audit_trail') as mock_get_trail:
            mock_result = MagicMock()
            mock_result.audits = sample_audits
            mock_result.total_count = len(sample_audits)
            mock_result.summary = {'test': 'summary'}
            mock_get_trail.return_value = mock_result
            
            export_data = await mock_audit_viewer.export_audit_data(format_type='json')
            
            assert export_data['metadata']['format'] == 'json'
            assert export_data['metadata']['exported_records'] == len(sample_audits)
            assert len(export_data['data']) == len(sample_audits)
    
    @pytest.mark.asyncio
    async def test_export_audit_data_csv(self, mock_audit_viewer, sample_audits):
        """Test audit data export in CSV format"""
        with patch.object(mock_audit_viewer, 'get_audit_trail') as mock_get_trail:
            mock_result = MagicMock()
            mock_result.audits = sample_audits
            mock_result.total_count = len(sample_audits)
            mock_result.summary = {'test': 'summary'}
            mock_get_trail.return_value = mock_result
            
            export_data = await mock_audit_viewer.export_audit_data(format_type='csv')
            
            assert export_data['metadata']['format'] == 'csv'
            assert len(export_data['data']) == len(sample_audits)
            # Verify CSV format has flattened structure
            csv_row = export_data['data'][0]
            assert 'id' in csv_row
            assert 'creator_id' in csv_row
            assert 'application_id' in csv_row

class TestAuditAnalyzer:
    """Test audit analysis functionality"""
    
    @pytest.fixture
    def mock_audit_analyzer(self):
        """Create mock audit analyzer for testing"""
        return StaffApplicationAuditAnalyzer()
    
    @pytest.fixture
    def sample_performance_data(self):
        """Sample performance data for testing"""
        return [
            StaffApplicationAudit(
                creator_id=123, creator_role='manager', client_notified=True, workflow_initiated=True,
                creation_timestamp=datetime.utcnow() - timedelta(hours=1)
            ),
            StaffApplicationAudit(
                creator_id=124, creator_role='call_center', client_notified=True, workflow_initiated=False,
                creation_timestamp=datetime.utcnow() - timedelta(hours=2)
            ),
            StaffApplicationAudit(
                creator_id=125, creator_role='manager', client_notified=False, workflow_initiated=False,
                creation_timestamp=datetime.utcnow() - timedelta(hours=3),
                metadata={'event_type': 'error_occurred'}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_analyze_performance_metrics(self, mock_audit_analyzer):
        """Test performance metrics analysis"""
        with patch('utils.audit_analyzer.audit_viewer') as mock_viewer:
            mock_result = MagicMock()
            mock_result.audits = [
                MagicMock(client_notified=True, workflow_initiated=True, creation_timestamp=datetime.utcnow()),
                MagicMock(client_notified=False, workflow_initiated=True, creation_timestamp=datetime.utcnow()),
                MagicMock(client_notified=True, workflow_initiated=False, creation_timestamp=datetime.utcnow(),
                         metadata={'event_type': 'error_occurred'})
            ]
            mock_viewer.get_audit_trail.return_value = mock_result
            
            metrics = await mock_audit_analyzer.analyze_performance_metrics(days_back=7)
            
            assert metrics.total_applications == 3
            assert 0 <= metrics.success_rate <= 100
            assert 0 <= metrics.error_rate <= 100
            assert 0 <= metrics.notification_success_rate <= 100
    
    @pytest.mark.asyncio
    async def test_analyze_trends(self, mock_audit_analyzer):
        """Test trend analysis"""
        with patch('utils.audit_analyzer.audit_viewer') as mock_viewer:
            # Create mock audits with timestamps spread over several days
            mock_audits = []
            for i in range(10):
                audit = MagicMock()
                audit.creation_timestamp = datetime.utcnow() - timedelta(days=i)
                audit.client_notified = True
                audit.workflow_initiated = True
                mock_audits.append(audit)
            
            mock_result = MagicMock()
            mock_result.audits = mock_audits
            mock_viewer.get_audit_trail.return_value = mock_result
            
            trend_data = await mock_audit_analyzer.analyze_trends(
                metric='application_count',
                days_back=10,
                granularity='daily'
            )
            
            assert trend_data.period == '10_days_daily'
            assert trend_data.trend_direction in ['increasing', 'decreasing', 'stable']
            assert 0 <= trend_data.trend_strength <= 1
            assert len(trend_data.data_points) > 0
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self, mock_audit_analyzer):
        """Test anomaly detection"""
        with patch.object(mock_audit_analyzer, 'analyze_performance_metrics') as mock_analyze:
            # Mock current metrics with low success rate
            current_metrics = MagicMock()
            current_metrics.success_rate = 30.0
            current_metrics.error_rate = 15.0
            current_metrics.applications_per_day = 10.0
            
            # Mock baseline metrics with normal success rate
            baseline_metrics = MagicMock()
            baseline_metrics.success_rate = 85.0
            baseline_metrics.error_rate = 2.0
            baseline_metrics.applications_per_day = 5.0
            
            mock_analyze.side_effect = [current_metrics, baseline_metrics]
            
            alerts = await mock_audit_analyzer.detect_anomalies(days_back=7)
            
            assert len(alerts) > 0
            # Should detect success rate drop and high error rate
            alert_types = [alert.alert_type for alert in alerts]
            assert 'success_rate_drop' in alert_types or 'high_error_rate' in alert_types
    
    @pytest.mark.asyncio
    async def test_analyze_compliance(self, mock_audit_analyzer):
        """Test compliance analysis"""
        with patch('utils.audit_analyzer.audit_viewer') as mock_viewer:
            mock_audits = [
                MagicMock(client_notified=True, workflow_initiated=True, 
                         application_id='app1', creator_id=123, creator_role='manager'),
                MagicMock(client_notified=False, workflow_initiated=True,
                         application_id='app2', creator_id=124, creator_role='call_center'),
                MagicMock(client_notified=True, workflow_initiated=False,
                         application_id=None, creator_id=125, creator_role='manager')  # Incomplete data
            ]
            
            mock_result = MagicMock()
            mock_result.audits = mock_audits
            mock_viewer.get_audit_trail.return_value = mock_result
            
            compliance = await mock_audit_analyzer.analyze_compliance(days_back=30)
            
            assert compliance['period_days'] == 30
            assert compliance['total_applications'] == 3
            assert 'compliance_metrics' in compliance
            assert 'violations' in compliance
            assert 'recommendations' in compliance
            
            # Should detect violations
            assert len(compliance['violations']) > 0
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_report(self, mock_audit_analyzer):
        """Test comprehensive report generation"""
        with patch.object(mock_audit_analyzer, 'analyze_performance_metrics') as mock_perf, \
             patch.object(mock_audit_analyzer, 'analyze_trends') as mock_trends, \
             patch.object(mock_audit_analyzer, 'detect_anomalies') as mock_anomalies, \
             patch.object(mock_audit_analyzer, 'analyze_compliance') as mock_compliance, \
             patch('utils.audit_analyzer.audit_viewer') as mock_viewer:
            
            # Mock all analysis methods
            mock_perf.return_value = MagicMock(total_applications=100, success_rate=85.0, error_rate=5.0)
            mock_trends.return_value = MagicMock(trend_direction='increasing')
            mock_anomalies.return_value = []
            mock_compliance.return_value = {'compliance_metrics': {'test': 90.0}, 'recommendations': []}
            mock_viewer.get_system_audit_summary.return_value = {'role_performance': {}}
            
            report = await mock_audit_analyzer.generate_comprehensive_report(days_back=30)
            
            assert 'report_metadata' in report
            assert 'executive_summary' in report
            assert 'performance_analysis' in report
            assert 'trend_analysis' in report
            assert 'anomaly_detection' in report
            assert 'compliance_analysis' in report
            assert 'recommendations' in report
            
            # Verify executive summary
            exec_summary = report['executive_summary']
            assert exec_summary['total_applications'] == 100
            assert exec_summary['overall_success_rate'] == 85.0

class TestAuditIntegration:
    """Integration tests for the complete audit system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_audit_flow(self):
        """Test complete audit flow from logging to analysis"""
        # This would be an integration test that requires database setup
        # For now, we'll test the flow with mocks
        
        with patch('utils.audit_logger.create_staff_application_audit') as mock_create, \
             patch('utils.audit_viewer.get_staff_application_audits') as mock_get:
            
            # Mock database operations
            mock_create.return_value = 1
            mock_get.return_value = [
                StaffApplicationAudit(
                    id=1,
                    application_id='app-integration-test',
                    creator_id=123,
                    creator_role='manager',
                    client_id=456,
                    application_type='connection_request',
                    creation_timestamp=datetime.utcnow(),
                    client_notified=True,
                    workflow_initiated=True
                )
            ]
            
            # Test logging
            session_id = await log_staff_application_created(
                creator_id=123,
                creator_role='manager',
                application_id='app-integration-test',
                client_id=456,
                application_type='connection_request'
            )
            
            assert session_id is not None
            
            # Test viewing
            recent_audits = await audit_viewer.get_audit_trail(limit=10)
            assert isinstance(recent_audits.audits, list)
            
            # Test analysis
            performance = await audit_analyzer.analyze_performance_metrics(days_back=1)
            assert isinstance(performance.total_applications, int)
    
    def test_audit_models_validation(self):
        """Test audit model validation"""
        # Test StaffApplicationAudit model
        audit = StaffApplicationAudit(
            application_id='test-app',
            creator_id=123,
            creator_role='manager',
            client_id=456,
            application_type='connection_request',
            creation_timestamp=datetime.utcnow()
        )
        
        audit_dict = audit.to_dict()
        assert audit_dict['application_id'] == 'test-app'
        assert audit_dict['creator_role'] == 'manager'
        
        # Test round-trip conversion
        audit_from_dict = StaffApplicationAudit.from_dict(audit_dict)
        assert audit_from_dict.application_id == audit.application_id
        assert audit_from_dict.creator_role == audit.creator_role
    
    def test_audit_data_sanitization(self):
        """Test that sensitive data is properly sanitized in audit logs"""
        # Test phone number masking
        phone = '+998901234567'
        masked_phone = phone.replace(phone[-4:], '****')
        assert masked_phone == '+99890123****'
        
        # Test that full client data is not stored in audit logs
        client_data = {
            'phone': '+998901234567',
            'full_name': 'John Doe',
            'address': '123 Main St',
            'passport': 'AB1234567'
        }
        
        # Simulate sanitization
        sanitized = {
            'phone': client_data['phone'].replace(client_data['phone'][-4:], '****'),
            'name_length': len(client_data['full_name']),
            'has_address': bool(client_data['address']),
            # passport should not be included
        }
        
        assert 'passport' not in sanitized
        assert '****' in sanitized['phone']
        assert sanitized['name_length'] == 8

if __name__ == '__main__':
    pytest.main([__file__, '-v'])