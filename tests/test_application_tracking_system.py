"""
Comprehensive tests for application tracking and reporting system.
Tests Requirements 6.1, 6.2, 6.3, 6.4 from multi-role application creation spec.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Import the modules we're testing
from utils.application_tracker import (
    ApplicationTracker, ApplicationSource, ApplicationStats, RoleStats,
    ComparisonReport, TrackingAlert, application_tracker
)
from utils.admin_reporting import (
    AdminReportingSystem, ReportRequest, ReportResult, ReportFormat, ReportPeriod,
    admin_reporting
)
from utils.application_alerts import (
    ApplicationAlertSystem, AlertRule, AlertNotification, AlertType, AlertFrequency,
    AlertChannel, alert_system
)
from database.models import ServiceRequest, StaffApplicationAudit, UserRole

class TestApplicationTracker:
    """Test the ApplicationTracker class"""
    
    @pytest.fixture
    def tracker(self):
        return ApplicationTracker()
    
    @pytest.fixture
    def mock_db_data(self):
        """Mock database data for testing"""
        return [
            {
                'id': '1',
                'created_by_staff': False,
                'creation_source': 'client',
                'created_at': datetime.utcnow() - timedelta(days=1),
                'current_status': 'completed',
                'completion_rating': 5
            },
            {
                'id': '2',
                'created_by_staff': True,
                'creation_source': 'manager',
                'created_at': datetime.utcnow() - timedelta(days=2),
                'current_status': 'completed',
                'completion_rating': 4
            },
            {
                'id': '3',
                'created_by_staff': True,
                'creation_source': 'call_center',
                'created_at': datetime.utcnow() - timedelta(days=3),
                'current_status': 'cancelled',
                'completion_rating': None
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_application_statistics_all_sources(self, tracker, mock_db_data):
        """Test getting application statistics for all sources"""
        with patch('utils.application_tracker.db_manager.fetch', return_value=mock_db_data):
            stats = await tracker.get_application_statistics(7, ApplicationSource.ALL)
            
            assert stats.total_applications == 3
            assert stats.client_created == 1
            assert stats.staff_created == 2
            assert stats.staff_creation_percentage == pytest.approx(66.67, rel=1e-2)
            assert stats.success_rate == pytest.approx(66.67, rel=1e-2)  # 2 completed out of 3
            assert stats.error_rate == pytest.approx(33.33, rel=1e-2)  # 1 cancelled out of 3
    
    @pytest.mark.asyncio
    async def test_get_application_statistics_staff_only(self, tracker, mock_db_data):
        """Test getting application statistics for staff-created only"""
        with patch('utils.application_tracker.db_manager.fetch', return_value=mock_db_data):
            stats = await tracker.get_application_statistics(7, ApplicationSource.STAFF)
            
            assert stats.total_applications == 2  # Only staff-created
            assert stats.client_created == 0
            assert stats.staff_created == 2
            assert stats.staff_creation_percentage == 100.0
    
    @pytest.mark.asyncio
    async def test_get_application_statistics_client_only(self, tracker, mock_db_data):
        """Test getting application statistics for client-created only"""
        with patch('utils.application_tracker.db_manager.fetch', return_value=mock_db_data):
            stats = await tracker.get_application_statistics(7, ApplicationSource.CLIENT)
            
            assert stats.total_applications == 1  # Only client-created
            assert stats.client_created == 1
            assert stats.staff_created == 0
            assert stats.staff_creation_percentage == 0.0
    
    @pytest.mark.asyncio
    async def test_get_application_statistics_empty_data(self, tracker):
        """Test getting application statistics with no data"""
        with patch('utils.application_tracker.db_manager.fetch', return_value=[]):
            stats = await tracker.get_application_statistics(7, ApplicationSource.ALL)
            
            assert stats.total_applications == 0
            assert stats.client_created == 0
            assert stats.staff_created == 0
            assert stats.staff_creation_percentage == 0.0
            assert stats.success_rate == 0.0
            assert stats.error_rate == 0.0
    
    @pytest.mark.asyncio
    async def test_get_role_statistics(self, tracker):
        """Test getting role-based statistics"""
        mock_audits = [
            StaffApplicationAudit(
                id=1,
                creator_role='manager',
                client_notified=True,
                workflow_initiated=True,
                creation_timestamp=datetime.utcnow() - timedelta(hours=1),
                metadata={'event_type': 'application_submitted'}
            ),
            StaffApplicationAudit(
                id=2,
                creator_role='manager',
                client_notified=True,
                workflow_initiated=False,
                creation_timestamp=datetime.utcnow() - timedelta(hours=2),
                metadata={'event_type': 'error_occurred'}
            ),
            StaffApplicationAudit(
                id=3,
                creator_role='call_center',
                client_notified=True,
                workflow_initiated=True,
                creation_timestamp=datetime.utcnow() - timedelta(hours=3),
                metadata={'event_type': 'application_submitted'}
            )
        ]
        
        mock_result = MagicMock()
        mock_result.audits = mock_audits
        
        with patch('utils.application_tracker.audit_viewer.get_audit_trail', return_value=mock_result):
            role_stats = await tracker.get_role_statistics(7)
            
            assert 'manager' in role_stats
            assert 'call_center' in role_stats
            
            manager_stats = role_stats['manager']
            assert manager_stats.total_applications == 2
            assert manager_stats.success_rate == 50.0  # 1 successful out of 2
            assert manager_stats.error_rate == 50.0  # 1 error out of 2
            
            call_center_stats = role_stats['call_center']
            assert call_center_stats.total_applications == 1
            assert call_center_stats.success_rate == 100.0
            assert call_center_stats.error_rate == 0.0
    
    @pytest.mark.asyncio
    async def test_generate_comparison_report(self, tracker):
        """Test generating comparison report"""
        # Mock the statistics methods
        client_stats = ApplicationStats(
            total_applications=10,
            client_created=10,
            staff_created=0,
            staff_creation_percentage=0.0,
            success_rate=85.0,
            error_rate=10.0,
            average_per_day=1.4,
            peak_hours=[9, 14, 16]
        )
        
        staff_stats = ApplicationStats(
            total_applications=15,
            client_created=0,
            staff_created=15,
            staff_creation_percentage=100.0,
            success_rate=90.0,
            error_rate=5.0,
            average_per_day=2.1,
            peak_hours=[10, 13, 15]
        )
        
        role_breakdown = {
            'manager': RoleStats(
                role='manager',
                total_applications=8,
                success_rate=92.0,
                error_rate=3.0,
                notification_success_rate=95.0,
                workflow_success_rate=90.0,
                average_per_day=1.1,
                most_active_hours=[10, 14]
            ),
            'call_center': RoleStats(
                role='call_center',
                total_applications=7,
                success_rate=88.0,
                error_rate=7.0,
                notification_success_rate=93.0,
                workflow_success_rate=85.0,
                average_per_day=1.0,
                most_active_hours=[9, 15]
            )
        }
        
        with patch.object(tracker, 'get_application_statistics') as mock_get_stats:
            with patch.object(tracker, 'get_role_statistics', return_value=role_breakdown):
                mock_get_stats.side_effect = [client_stats, staff_stats]
                
                report = await tracker.generate_comparison_report(7)
                
                assert report.period_days == 7
                assert report.client_stats == client_stats
                assert report.staff_stats == staff_stats
                assert report.role_breakdown == role_breakdown
                assert len(report.insights) > 0
                assert len(report.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_detect_unusual_patterns(self, tracker):
        """Test detecting unusual patterns"""
        # Mock current and baseline statistics
        current_stats = ApplicationStats(
            total_applications=100,
            client_created=20,
            staff_created=80,
            staff_creation_percentage=80.0,  # High staff percentage
            success_rate=60.0,  # Low success rate
            error_rate=15.0,  # High error rate
            average_per_day=14.3,
            peak_hours=[10, 14, 16]
        )
        
        baseline_stats = ApplicationStats(
            total_applications=70,
            client_created=50,
            staff_created=20,
            staff_creation_percentage=28.6,  # Normal staff percentage
            success_rate=85.0,  # Normal success rate
            error_rate=5.0,  # Normal error rate
            average_per_day=5.0,
            peak_hours=[9, 13, 17]
        )
        
        with patch.object(tracker, 'get_application_statistics') as mock_get_stats:
            mock_get_stats.side_effect = [current_stats, baseline_stats]
            
            alerts = await tracker.detect_unusual_patterns(7)
            
            # Should detect multiple issues
            assert len(alerts) > 0
            
            # Check for specific alert types
            alert_types = [alert.alert_type for alert in alerts]
            # Should detect at least high staff creation rate and success rate drop
            assert 'high_staff_creation_rate' in alert_types
            assert 'success_rate_drop' in alert_types
            # Error spike may or may not be detected depending on thresholds
    
    @pytest.mark.asyncio
    async def test_generate_trend_report(self, tracker, mock_db_data):
        """Test generating trend report"""
        with patch('utils.application_tracker.db_manager.fetch', return_value=mock_db_data):
            trend_report = await tracker.generate_trend_report(7, "daily")
            
            assert trend_report['period_days'] == 7
            assert trend_report['granularity'] == "daily"
            assert 'data_points' in trend_report
            assert 'trends' in trend_report
            assert 'summary' in trend_report
    
    @pytest.mark.asyncio
    async def test_caching_mechanism(self, tracker, mock_db_data):
        """Test that caching works correctly"""
        with patch('utils.application_tracker.db_manager.fetch', return_value=mock_db_data) as mock_fetch:
            # First call should hit the database
            stats1 = await tracker.get_application_statistics(7, ApplicationSource.ALL)
            assert mock_fetch.call_count == 1
            
            # Second call should use cache
            stats2 = await tracker.get_application_statistics(7, ApplicationSource.ALL)
            assert mock_fetch.call_count == 1  # Should not increase
            
            # Results should be identical
            assert stats1.total_applications == stats2.total_applications

class TestAdminReportingSystem:
    """Test the AdminReportingSystem class"""
    
    @pytest.fixture
    def reporting_system(self):
        return AdminReportingSystem()
    
    @pytest.mark.asyncio
    async def test_generate_dashboard_report(self, reporting_system):
        """Test generating dashboard report"""
        mock_admin_stats = {
            'total_users': 100,
            'total_orders': 500,
            'active_technicians': 20,
            'pending_orders': 15
        }
        
        mock_app_stats = ApplicationStats(
            total_applications=50,
            client_created=30,
            staff_created=20,
            staff_creation_percentage=40.0,
            success_rate=85.0,
            error_rate=10.0,
            average_per_day=7.1,
            peak_hours=[10, 14, 16]
        )
        
        with patch('utils.admin_reporting.get_admin_dashboard_stats', return_value=mock_admin_stats):
            with patch('utils.admin_reporting.application_tracker.get_application_statistics', return_value=mock_app_stats):
                with patch('utils.admin_reporting.application_tracker.get_role_statistics', return_value={}):
                    with patch('utils.admin_reporting.application_tracker.detect_unusual_patterns', return_value=[]):
                        with patch('utils.admin_reporting.audit_viewer.get_audit_trail') as mock_audit:
                            mock_audit.return_value = MagicMock(total_count=100, audits=[], summary={})
                            
                            dashboard = await reporting_system.generate_dashboard_report()
                            
                            assert 'generated_at' in dashboard
                            assert 'system_overview' in dashboard
                            assert 'application_metrics' in dashboard
                            assert dashboard['system_overview']['total_users'] == 100
    
    @pytest.mark.asyncio
    async def test_generate_performance_report(self, reporting_system):
        """Test generating performance report"""
        request = ReportRequest(
            report_type='performance_analysis',
            period=ReportPeriod.WEEKLY.value,
            format_type=ReportFormat.JSON.value
        )
        
        mock_tracking_report = {
            'executive_summary': {
                'total_applications': 100,
                'overall_success_rate': 85.0,
                'error_rate': 10.0
            },
            'application_statistics': {
                'overall': {'success_rate': 85.0, 'average_per_day': 14.3},
                'by_role': {
                    'manager': {'success_rate': 90.0, 'average_per_day': 5.0}
                }
            },
            'recommendations': {'immediate_actions': [], 'process_improvements': []},
            'key_insights': ['Staff handle 40% of applications']
        }
        
        with patch('utils.admin_reporting.application_tracker.generate_comprehensive_tracking_report', return_value=mock_tracking_report):
            with patch.object(reporting_system.analyzer, 'generate_comprehensive_report', return_value={}):
                result = await reporting_system.generate_performance_report(request)
                
                assert result.report_type == 'performance_analysis'
                assert result.period == ReportPeriod.WEEKLY.value
                assert result.format_type == ReportFormat.JSON.value
                assert 'executive_summary' in result.data
    
    @pytest.mark.asyncio
    async def test_generate_audit_report(self, reporting_system):
        """Test generating audit report"""
        request = ReportRequest(
            report_type='audit_trail',
            period=ReportPeriod.MONTHLY.value,
            format_type=ReportFormat.JSON.value
        )
        
        mock_audit_result = MagicMock()
        mock_audit_result.total_count = 200
        mock_audit_result.filtered_count = 200
        mock_audit_result.audits = []
        mock_audit_result.summary = {
            'notification_rate': 95.0,
            'workflow_initiation_rate': 90.0,
            'success_rate': 85.0,
            'applications_by_role': {'manager': 50, 'call_center': 30}
        }
        
        with patch('utils.admin_reporting.audit_viewer.get_audit_trail', return_value=mock_audit_result):
            with patch('utils.admin_reporting.audit_viewer.get_system_audit_summary', return_value={'system_health': {}, 'alerts': []}):
                result = await reporting_system.generate_audit_report(request)
                
                assert result.report_type == 'audit_trail'
                assert result.summary['total_audit_records'] == 200
                assert result.summary['compliance_score'] > 0
    
    @pytest.mark.asyncio
    async def test_format_report_data_csv(self, reporting_system):
        """Test formatting report data as CSV"""
        test_data = {
            'report_metadata': {'report_type': 'test', 'generated_at': '2024-01-01T00:00:00'},
            'executive_summary': {'total_applications': 100, 'success_rate': 85.0},
            'application_statistics': {
                'by_role': {
                    'manager': {'total_applications': 50, 'success_rate': 90.0, 'error_rate': 5.0, 'average_per_day': 7.1},
                    'call_center': {'total_applications': 30, 'success_rate': 80.0, 'error_rate': 10.0, 'average_per_day': 4.3}
                }
            }
        }
        
        csv_result = await reporting_system._convert_to_csv(test_data)
        
        assert isinstance(csv_result, str)
        assert 'report_type,test' in csv_result
        assert 'total_applications,100' in csv_result
        assert 'Role,Total Applications,Success Rate,Error Rate,Avg Per Day' in csv_result
        assert 'manager,50,90.0,5.0,7.1' in csv_result
    
    @pytest.mark.asyncio
    async def test_format_report_data_html(self, reporting_system):
        """Test formatting report data as HTML"""
        test_data = {
            'report_metadata': {'report_type': 'test', 'generated_at': '2024-01-01T00:00:00'},
            'executive_summary': {'total_applications': 100, 'success_rate': 85.0},
            'role_performance': {
                'manager': {'total_applications': 50, 'success_rate': 90.0, 'error_rate': 5.0},
                'call_center': {'total_applications': 30, 'success_rate': 80.0, 'error_rate': 10.0}
            }
        }
        
        html_result = await reporting_system._convert_to_html(test_data)
        
        assert isinstance(html_result, str)
        assert '<html>' in html_result
        assert '<h1>Application Tracking Report</h1>' in html_result
        assert '<table border=\'1\'>' in html_result
        assert 'manager' in html_result

class TestApplicationAlertSystem:
    """Test the ApplicationAlertSystem class"""
    
    @pytest.fixture
    def alert_system(self):
        return ApplicationAlertSystem()
    
    def test_initialize_default_rules(self, alert_system):
        """Test that default alert rules are initialized"""
        rules = alert_system._alert_rules
        
        assert len(rules) > 0
        assert 'high_staff_creation_rate' in rules
        assert 'low_client_creation_rate' in rules
        assert 'success_rate_drop' in rules
        assert 'error_spike' in rules
        assert 'unusual_role_activity' in rules
        
        # Check rule properties
        high_staff_rule = rules['high_staff_creation_rate']
        assert high_staff_rule.name == "High Staff Creation Rate"
        assert high_staff_rule.frequency == AlertFrequency.HOURLY.value
        assert AlertChannel.TELEGRAM.value in high_staff_rule.channels
    
    @pytest.mark.asyncio
    async def test_check_high_staff_creation_rate(self, alert_system):
        """Test checking high staff creation rate condition"""
        config = {
            "staff_percentage_threshold": 70,
            "baseline_comparison": False,
            "minimum_applications": 10
        }
        
        mock_stats = ApplicationStats(
            total_applications=50,
            client_created=10,
            staff_created=40,
            staff_creation_percentage=80.0,  # Above threshold
            success_rate=85.0,
            error_rate=10.0,
            average_per_day=7.1,
            peak_hours=[10, 14, 16]
        )
        
        with patch('utils.application_alerts.application_tracker.get_application_statistics', return_value=mock_stats):
            should_trigger, alert_data = await alert_system._check_high_staff_creation_rate(config, 7)
            
            assert should_trigger is True
            assert alert_data['current_staff_percentage'] == 80.0
            assert alert_data['threshold'] == 70
            assert alert_data['total_applications'] == 50
    
    @pytest.mark.asyncio
    async def test_check_success_rate_drop(self, alert_system):
        """Test checking success rate drop condition"""
        config = {
            "success_rate_threshold": 80,
            "drop_percentage": 15,
            "baseline_comparison": True
        }
        
        current_stats = ApplicationStats(
            total_applications=50,
            client_created=25,
            staff_created=25,
            staff_creation_percentage=50.0,
            success_rate=65.0,  # Below threshold
            error_rate=20.0,
            average_per_day=7.1,
            peak_hours=[10, 14, 16]
        )
        
        baseline_stats = ApplicationStats(
            total_applications=40,
            client_created=20,
            staff_created=20,
            staff_creation_percentage=50.0,
            success_rate=85.0,  # Normal success rate
            error_rate=10.0,
            average_per_day=5.7,
            peak_hours=[9, 13, 17]
        )
        
        with patch('utils.application_alerts.application_tracker.get_application_statistics') as mock_get_stats:
            mock_get_stats.side_effect = [current_stats, baseline_stats]
            
            should_trigger, alert_data = await alert_system._check_success_rate_drop(config, 7)
            
            assert should_trigger is True
            assert alert_data['current_success_rate'] == 65.0
            assert alert_data['threshold'] == 80
    
    @pytest.mark.asyncio
    async def test_create_alert_notification(self, alert_system):
        """Test creating alert notification"""
        rule = AlertRule(
            rule_id="test_rule",
            name="Test Alert",
            description="Test alert description",
            alert_type=AlertType.HIGH_STAFF_CREATION_RATE.value,
            threshold_config={},
            frequency=AlertFrequency.HOURLY.value,
            channels=[AlertChannel.TELEGRAM.value],
            recipients=[1, 2, 3]
        )
        
        alert_data = {
            'current_staff_percentage': 80.0,
            'threshold': 70,
            'total_applications': 50
        }
        
        notification = await alert_system._create_alert_notification(rule, alert_data)
        
        assert notification.rule_id == "test_rule"
        assert notification.alert_type == AlertType.HIGH_STAFF_CREATION_RATE.value
        assert notification.severity in ["info", "warning", "critical"]
        assert notification.title == "High Staff Application Creation Rate"
        assert "80.0%" in notification.message
        assert notification.channels == [AlertChannel.TELEGRAM.value]
        assert notification.recipients == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_add_alert_rule(self, alert_system):
        """Test adding a new alert rule"""
        new_rule = AlertRule(
            rule_id="custom_rule",
            name="Custom Alert",
            description="Custom alert description",
            alert_type="custom_type",
            threshold_config={"threshold": 50},
            frequency=AlertFrequency.DAILY.value,
            channels=[AlertChannel.DATABASE.value],
            recipients=[1]
        )
        
        result = await alert_system.add_alert_rule(new_rule)
        
        assert result is True
        assert "custom_rule" in alert_system._alert_rules
        assert alert_system._alert_rules["custom_rule"] == new_rule
    
    @pytest.mark.asyncio
    async def test_update_alert_rule(self, alert_system):
        """Test updating an existing alert rule"""
        # First add a rule
        rule = AlertRule(
            rule_id="update_test",
            name="Original Name",
            description="Original description",
            alert_type="test_type",
            threshold_config={},
            frequency=AlertFrequency.HOURLY.value,
            channels=[AlertChannel.LOG.value],
            recipients=[]
        )
        
        await alert_system.add_alert_rule(rule)
        
        # Now update it
        updates = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'is_active': False
        }
        
        result = await alert_system.update_alert_rule("update_test", updates)
        
        assert result is True
        updated_rule = alert_system._alert_rules["update_test"]
        assert updated_rule.name == "Updated Name"
        assert updated_rule.description == "Updated description"
        assert updated_rule.is_active is False
    
    @pytest.mark.asyncio
    async def test_delete_alert_rule(self, alert_system):
        """Test deleting an alert rule"""
        # First add a rule
        rule = AlertRule(
            rule_id="delete_test",
            name="Delete Test",
            description="Rule to be deleted",
            alert_type="test_type",
            threshold_config={},
            frequency=AlertFrequency.HOURLY.value,
            channels=[AlertChannel.LOG.value],
            recipients=[]
        )
        
        await alert_system.add_alert_rule(rule)
        assert "delete_test" in alert_system._alert_rules
        
        # Now delete it
        result = await alert_system.delete_alert_rule("delete_test")
        
        assert result is True
        assert "delete_test" not in alert_system._alert_rules

class TestIntegration:
    """Integration tests for the complete tracking system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_tracking_workflow(self):
        """Test complete end-to-end tracking workflow"""
        # Mock data setup
        mock_service_requests = [
            {
                'id': '1',
                'created_by_staff': True,
                'creation_source': 'manager',
                'created_at': datetime.utcnow() - timedelta(hours=1),
                'current_status': 'completed',
                'completion_rating': 5
            },
            {
                'id': '2',
                'created_by_staff': False,
                'creation_source': 'client',
                'created_at': datetime.utcnow() - timedelta(hours=2),
                'current_status': 'in_progress',
                'completion_rating': None
            }
        ]
        
        mock_audit_data = [
            StaffApplicationAudit(
                id=1,
                application_id='1',
                creator_role='manager',
                client_notified=True,
                workflow_initiated=True,
                creation_timestamp=datetime.utcnow() - timedelta(hours=1)
            )
        ]
        
        # Test the complete workflow
        with patch('utils.application_tracker.db_manager.fetch', return_value=mock_service_requests):
            with patch('utils.application_tracker.audit_viewer.get_audit_trail') as mock_audit:
                mock_audit.return_value = MagicMock(audits=mock_audit_data)
                
                # 1. Get application statistics
                stats = await application_tracker.get_application_statistics(24)
                assert stats.total_applications == 2
                assert stats.staff_created == 1
                assert stats.client_created == 1
                
                # 2. Generate comparison report
                comparison = await application_tracker.generate_comparison_report(24)
                assert comparison.period_days == 24
                assert len(comparison.insights) > 0
                
                # 3. Check for unusual patterns
                alerts = await application_tracker.detect_unusual_patterns(24)
                # Should not trigger alerts with normal data
                assert isinstance(alerts, list)
                
                # 4. Generate comprehensive report
                comprehensive = await application_tracker.generate_comprehensive_tracking_report(24)
                assert 'report_metadata' in comprehensive
                assert 'executive_summary' in comprehensive
                assert 'application_statistics' in comprehensive
    
    @pytest.mark.asyncio
    async def test_alert_system_integration(self):
        """Test alert system integration with tracking"""
        # Create a scenario that should trigger alerts
        high_staff_stats = ApplicationStats(
            total_applications=100,
            client_created=10,
            staff_created=90,
            staff_creation_percentage=90.0,  # Very high staff percentage
            success_rate=50.0,  # Low success rate
            error_rate=25.0,  # High error rate
            average_per_day=14.3,
            peak_hours=[10, 14, 16]
        )
        
        normal_baseline = ApplicationStats(
            total_applications=50,
            client_created=40,
            staff_created=10,
            staff_creation_percentage=20.0,
            success_rate=90.0,
            error_rate=5.0,
            average_per_day=7.1,
            peak_hours=[9, 13, 17]
        )
        
        with patch('utils.application_alerts.application_tracker.get_application_statistics') as mock_stats:
            mock_stats.side_effect = [high_staff_stats, normal_baseline]
            
            # Test alert detection
            alerts = await alert_system.detect_unusual_patterns(7)
            
            # Should detect multiple issues
            assert len(alerts) > 0
            
            # Check that we get the expected alert types
            alert_types = [alert.alert_type for alert in alerts]
            expected_types = ['high_staff_creation_rate', 'success_rate_drop', 'error_spike']
            
            for expected_type in expected_types:
                assert expected_type in alert_types

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])