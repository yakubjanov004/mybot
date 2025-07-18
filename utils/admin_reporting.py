"""
Administrative reporting system for staff application creation tracking.
Implements Requirements 6.2, 6.3, 6.4 from multi-role application creation spec.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import csv
import io

from utils.application_tracker import application_tracker, ApplicationSource, TrackingAlert
from utils.audit_viewer import audit_viewer, AuditFilter, AuditFilterType
from utils.audit_analyzer import StaffApplicationAuditAnalyzer
from database.queries import db_manager
from database.admin_queries import get_admin_dashboard_stats
from utils.logger import setup_module_logger

logger = setup_module_logger("admin_reporting")

class ReportFormat(Enum):
    """Available report formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    SUMMARY = "summary"

class ReportPeriod(Enum):
    """Standard reporting periods"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"

@dataclass
class ReportRequest:
    """Request for generating a report"""
    report_type: str
    period: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format_type: str = ReportFormat.JSON.value
    filters: Optional[Dict[str, Any]] = None
    include_details: bool = True
    
    def get_days_back(self) -> int:
        """Calculate days back based on period"""
        if self.period == ReportPeriod.DAILY.value:
            return 1
        elif self.period == ReportPeriod.WEEKLY.value:
            return 7
        elif self.period == ReportPeriod.MONTHLY.value:
            return 30
        elif self.period == ReportPeriod.QUARTERLY.value:
            return 90
        elif self.period == ReportPeriod.CUSTOM.value and self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        else:
            return 7  # Default to weekly

@dataclass
class ReportResult:
    """Result of report generation"""
    report_id: str
    report_type: str
    generated_at: datetime
    period: str
    format_type: str
    data: Any
    summary: Dict[str, Any]
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'report_type': self.report_type,
            'generated_at': self.generated_at.isoformat(),
            'period': self.period,
            'format_type': self.format_type,
            'data': self.data,
            'summary': self.summary,
            'file_path': self.file_path
        }

class AdminReportingSystem:
    """Main administrative reporting system"""
    
    def __init__(self):
        self.logger = logger
        self.analyzer = StaffApplicationAuditAnalyzer()
        self._report_cache = {}
        self._cache_ttl = timedelta(minutes=30)
    
    async def generate_dashboard_report(self) -> Dict[str, Any]:
        """
        Generate real-time dashboard report for administrators.
        
        Returns:
            Dict containing dashboard data
        """
        try:
            # Get basic admin dashboard stats
            admin_stats = await get_admin_dashboard_stats()
            
            # Get application tracking data
            today_stats = await application_tracker.get_application_statistics(1)
            week_stats = await application_tracker.get_application_statistics(7)
            month_stats = await application_tracker.get_application_statistics(30)
            
            # Get role performance
            role_stats = await application_tracker.get_role_statistics(7)
            
            # Check for alerts
            alerts = await application_tracker.detect_unusual_patterns(7)
            critical_alerts = [alert for alert in alerts if alert.severity == "critical"]
            
            # Get recent audit activity
            recent_audits = await audit_viewer.get_audit_trail(
                start_date=datetime.utcnow() - timedelta(hours=24),
                limit=50
            )
            
            dashboard = {
                'generated_at': datetime.utcnow().isoformat(),
                'system_overview': {
                    'total_users': admin_stats.get('total_users', 0),
                    'total_orders': admin_stats.get('total_orders', 0),
                    'active_technicians': admin_stats.get('active_technicians', 0),
                    'pending_orders': admin_stats.get('pending_orders', 0)
                },
                'application_metrics': {
                    'today': {
                        'total': today_stats.total_applications,
                        'staff_created': today_stats.staff_created,
                        'client_created': today_stats.client_created,
                        'staff_percentage': today_stats.staff_creation_percentage,
                        'success_rate': today_stats.success_rate
                    },
                    'this_week': {
                        'total': week_stats.total_applications,
                        'staff_created': week_stats.staff_created,
                        'client_created': week_stats.client_created,
                        'staff_percentage': week_stats.staff_creation_percentage,
                        'success_rate': week_stats.success_rate
                    },
                    'this_month': {
                        'total': month_stats.total_applications,
                        'staff_created': month_stats.staff_created,
                        'client_created': month_stats.client_created,
                        'staff_percentage': month_stats.staff_creation_percentage,
                        'success_rate': month_stats.success_rate
                    }
                },
                'role_performance': {
                    role: {
                        'total_applications': stats.total_applications,
                        'success_rate': stats.success_rate,
                        'error_rate': stats.error_rate,
                        'avg_per_day': stats.average_per_day
                    } for role, stats in role_stats.items()
                },
                'alerts': {
                    'total_alerts': len(alerts),
                    'critical_alerts': len(critical_alerts),
                    'recent_critical': [alert.to_dict() for alert in critical_alerts[:5]]
                },
                'recent_activity': {
                    'total_audit_records': recent_audits.total_count,
                    'recent_applications': len(recent_audits.audits),
                    'activity_summary': recent_audits.summary
                }
            }
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard report: {e}")
            return {
                'generated_at': datetime.utcnow().isoformat(),
                'error': str(e),
                'system_overview': {},
                'application_metrics': {},
                'role_performance': {},
                'alerts': {},
                'recent_activity': {}
            }
    
    async def generate_performance_report(self, request: ReportRequest) -> ReportResult:
        """
        Generate performance analysis report.
        
        Args:
            request: Report request parameters
            
        Returns:
            ReportResult: Generated performance report
        """
        try:
            days_back = request.get_days_back()
            
            # Get comprehensive tracking report
            tracking_report = await application_tracker.generate_comprehensive_tracking_report(days_back)
            
            # Get audit analysis
            audit_analysis = await self.analyzer.generate_comprehensive_report(days_back)
            
            # Combine into performance report
            performance_data = {
                'report_metadata': {
                    'report_type': 'performance_analysis',
                    'period': request.period,
                    'days_analyzed': days_back,
                    'generated_at': datetime.utcnow().isoformat()
                },
                'executive_summary': tracking_report.get('executive_summary', {}),
                'performance_metrics': {
                    'application_statistics': tracking_report.get('application_statistics', {}),
                    'success_rates': {
                        'overall': tracking_report.get('executive_summary', {}).get('overall_success_rate', 0),
                        'by_source': {
                            'client': tracking_report.get('application_statistics', {}).get('by_source', {}).get('client', {}).get('success_rate', 0),
                            'staff': tracking_report.get('application_statistics', {}).get('by_source', {}).get('staff', {}).get('success_rate', 0)
                        },
                        'by_role': {
                            role: stats.get('success_rate', 0) 
                            for role, stats in tracking_report.get('application_statistics', {}).get('by_role', {}).items()
                        }
                    },
                    'efficiency_metrics': {
                        'average_applications_per_day': tracking_report.get('application_statistics', {}).get('overall', {}).get('average_per_day', 0),
                        'peak_hours': tracking_report.get('application_statistics', {}).get('overall', {}).get('peak_hours', []),
                        'role_efficiency': {
                            role: stats.get('average_per_day', 0)
                            for role, stats in tracking_report.get('application_statistics', {}).get('by_role', {}).items()
                        }
                    }
                },
                'trend_analysis': tracking_report.get('trend_analysis', {}),
                'audit_compliance': audit_analysis.get('compliance_analysis', {}),
                'alerts_and_issues': {
                    'pattern_alerts': tracking_report.get('pattern_alerts', []),
                    'audit_alerts': audit_analysis.get('anomaly_detection', {}).get('alerts', [])
                },
                'recommendations': tracking_report.get('recommendations', {}),
                'detailed_analysis': audit_analysis if request.include_details else {}
            }
            
            # Generate summary
            summary = {
                'total_applications': tracking_report.get('executive_summary', {}).get('total_applications', 0),
                'staff_creation_rate': tracking_report.get('executive_summary', {}).get('staff_creation_percentage', 0),
                'overall_success_rate': tracking_report.get('executive_summary', {}).get('overall_success_rate', 0),
                'critical_alerts': tracking_report.get('executive_summary', {}).get('critical_alerts', 0),
                'top_performing_role': self._get_top_performing_role(tracking_report.get('application_statistics', {}).get('by_role', {})),
                'key_insights': tracking_report.get('key_insights', [])
            }
            
            # Format output
            formatted_data = await self._format_report_data(performance_data, request.format_type)
            
            report_id = f"perf_{request.period}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return ReportResult(
                report_id=report_id,
                report_type='performance_analysis',
                generated_at=datetime.utcnow(),
                period=request.period,
                format_type=request.format_type,
                data=formatted_data,
                summary=summary
            )
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return ReportResult(
                report_id=f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                report_type='performance_analysis',
                generated_at=datetime.utcnow(),
                period=request.period,
                format_type=request.format_type,
                data={'error': str(e)},
                summary={'error': str(e)}
            )
    
    async def generate_audit_report(self, request: ReportRequest) -> ReportResult:
        """
        Generate audit trail report.
        
        Args:
            request: Report request parameters
            
        Returns:
            ReportResult: Generated audit report
        """
        try:
            days_back = request.get_days_back()
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Build filters from request
            filters = []
            if request.filters:
                if request.filters.get('role'):
                    filters.append(AuditFilter(AuditFilterType.BY_ROLE.value, request.filters['role']))
                if request.filters.get('creator_id'):
                    filters.append(AuditFilter(AuditFilterType.BY_CREATOR.value, request.filters['creator_id']))
                if request.filters.get('application_type'):
                    filters.append(AuditFilter(AuditFilterType.BY_APPLICATION_TYPE.value, request.filters['application_type']))
            
            # Get audit trail
            audit_result = await audit_viewer.get_audit_trail(
                filters=filters,
                start_date=start_date,
                limit=5000
            )
            
            # Get system audit summary
            system_summary = await audit_viewer.get_system_audit_summary(days_back)
            
            # Prepare audit data
            audit_data = {
                'report_metadata': {
                    'report_type': 'audit_trail',
                    'period': request.period,
                    'days_analyzed': days_back,
                    'generated_at': datetime.utcnow().isoformat(),
                    'filters_applied': request.filters or {}
                },
                'audit_summary': {
                    'total_records': audit_result.total_count,
                    'filtered_records': audit_result.filtered_count,
                    'summary_statistics': audit_result.summary
                },
                'system_health': system_summary.get('system_health', {}),
                'compliance_metrics': {
                    'audit_coverage': 100.0,  # All staff applications are audited
                    'notification_compliance': audit_result.summary.get('notification_rate', 0),
                    'workflow_compliance': audit_result.summary.get('workflow_initiation_rate', 0),
                    'success_rate': audit_result.summary.get('success_rate', 0)
                },
                'activity_breakdown': {
                    'by_role': audit_result.summary.get('applications_by_role', {}),
                    'by_type': audit_result.summary.get('applications_by_type', {}),
                    'by_time': audit_result.summary.get('time_distribution', {}),
                    'most_active_creators': audit_result.summary.get('most_active_creators', [])
                },
                'audit_records': [audit.to_dict() for audit in audit_result.audits] if request.include_details else [],
                'alerts': system_summary.get('alerts', [])
            }
            
            # Generate summary
            summary = {
                'total_audit_records': audit_result.total_count,
                'compliance_score': (
                    audit_result.summary.get('notification_rate', 0) + 
                    audit_result.summary.get('workflow_initiation_rate', 0) + 
                    audit_result.summary.get('success_rate', 0)
                ) / 3,
                'most_active_role': max(audit_result.summary.get('applications_by_role', {}).items(), 
                                      key=lambda x: x[1], default=('none', 0))[0],
                'alert_count': len(system_summary.get('alerts', [])),
                'period_analyzed': f"{days_back} days"
            }
            
            # Format output
            formatted_data = await self._format_report_data(audit_data, request.format_type)
            
            report_id = f"audit_{request.period}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return ReportResult(
                report_id=report_id,
                report_type='audit_trail',
                generated_at=datetime.utcnow(),
                period=request.period,
                format_type=request.format_type,
                data=formatted_data,
                summary=summary
            )
            
        except Exception as e:
            self.logger.error(f"Error generating audit report: {e}")
            return ReportResult(
                report_id=f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                report_type='audit_trail',
                generated_at=datetime.utcnow(),
                period=request.period,
                format_type=request.format_type,
                data={'error': str(e)},
                summary={'error': str(e)}
            )
    
    async def generate_comparison_report(self, request: ReportRequest) -> ReportResult:
        """
        Generate staff vs client comparison report.
        
        Args:
            request: Report request parameters
            
        Returns:
            ReportResult: Generated comparison report
        """
        try:
            days_back = request.get_days_back()
            
            # Get comparison analysis
            comparison = await application_tracker.generate_comparison_report(days_back)
            
            # Get trend data
            trend_data = await application_tracker.generate_trend_report(days_back)
            
            # Prepare comparison data
            comparison_data = {
                'report_metadata': {
                    'report_type': 'staff_client_comparison',
                    'period': request.period,
                    'days_analyzed': days_back,
                    'generated_at': datetime.utcnow().isoformat()
                },
                'comparison_summary': {
                    'total_applications': comparison.client_stats.total_applications + comparison.staff_stats.total_applications,
                    'client_percentage': (comparison.client_stats.total_applications / 
                                        (comparison.client_stats.total_applications + comparison.staff_stats.total_applications) * 100) 
                                       if (comparison.client_stats.total_applications + comparison.staff_stats.total_applications) > 0 else 0,
                    'staff_percentage': (comparison.staff_stats.total_applications / 
                                       (comparison.client_stats.total_applications + comparison.staff_stats.total_applications) * 100) 
                                      if (comparison.client_stats.total_applications + comparison.staff_stats.total_applications) > 0 else 0
                },
                'detailed_comparison': {
                    'client_statistics': comparison.client_stats.to_dict(),
                    'staff_statistics': comparison.staff_stats.to_dict(),
                    'performance_comparison': {
                        'success_rate_difference': comparison.staff_stats.success_rate - comparison.client_stats.success_rate,
                        'error_rate_difference': comparison.staff_stats.error_rate - comparison.client_stats.error_rate,
                        'efficiency_comparison': {
                            'client_avg_per_day': comparison.client_stats.average_per_day,
                            'staff_avg_per_day': comparison.staff_stats.average_per_day
                        }
                    }
                },
                'role_breakdown': {
                    role: stats.to_dict() for role, stats in comparison.role_breakdown.items()
                },
                'trend_analysis': trend_data,
                'insights': comparison.insights,
                'recommendations': comparison.recommendations
            }
            
            # Generate summary
            summary = {
                'total_applications': comparison.client_stats.total_applications + comparison.staff_stats.total_applications,
                'staff_dominance': comparison.staff_stats.total_applications > comparison.client_stats.total_applications,
                'better_performer': 'staff' if comparison.staff_stats.success_rate > comparison.client_stats.success_rate else 'client',
                'success_rate_gap': abs(comparison.staff_stats.success_rate - comparison.client_stats.success_rate),
                'most_active_role': max(comparison.role_breakdown.items(), 
                                      key=lambda x: x[1].total_applications, default=('none', None))[0],
                'key_insights': comparison.insights[:3]  # Top 3 insights
            }
            
            # Format output
            formatted_data = await self._format_report_data(comparison_data, request.format_type)
            
            report_id = f"comp_{request.period}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return ReportResult(
                report_id=report_id,
                report_type='staff_client_comparison',
                generated_at=datetime.utcnow(),
                period=request.period,
                format_type=request.format_type,
                data=formatted_data,
                summary=summary
            )
            
        except Exception as e:
            self.logger.error(f"Error generating comparison report: {e}")
            return ReportResult(
                report_id=f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                report_type='staff_client_comparison',
                generated_at=datetime.utcnow(),
                period=request.period,
                format_type=request.format_type,
                data={'error': str(e)},
                summary={'error': str(e)}
            )
    
    async def generate_alert_report(self, request: ReportRequest) -> ReportResult:
        """
        Generate alerts and anomaly detection report.
        
        Args:
            request: Report request parameters
            
        Returns:
            ReportResult: Generated alert report
        """
        try:
            days_back = request.get_days_back()
            
            # Get tracking alerts
            tracking_alerts = await application_tracker.detect_unusual_patterns(days_back)
            
            # Get audit analysis alerts
            audit_alerts = await self.analyzer.detect_anomalies(days_back)
            
            # Combine and categorize alerts
            all_alerts = tracking_alerts + audit_alerts
            critical_alerts = [alert for alert in all_alerts if alert.severity == "critical"]
            warning_alerts = [alert for alert in all_alerts if alert.severity == "warning"]
            info_alerts = [alert for alert in all_alerts if alert.severity == "info"]
            
            # Prepare alert data
            alert_data = {
                'report_metadata': {
                    'report_type': 'alerts_and_anomalies',
                    'period': request.period,
                    'days_analyzed': days_back,
                    'generated_at': datetime.utcnow().isoformat()
                },
                'alert_summary': {
                    'total_alerts': len(all_alerts),
                    'critical_count': len(critical_alerts),
                    'warning_count': len(warning_alerts),
                    'info_count': len(info_alerts),
                    'alert_rate': len(all_alerts) / days_back if days_back > 0 else 0
                },
                'alerts_by_severity': {
                    'critical': [alert.to_dict() if hasattr(alert, 'to_dict') else asdict(alert) for alert in critical_alerts],
                    'warning': [alert.to_dict() if hasattr(alert, 'to_dict') else asdict(alert) for alert in warning_alerts],
                    'info': [alert.to_dict() if hasattr(alert, 'to_dict') else asdict(alert) for alert in info_alerts]
                },
                'alert_categories': self._categorize_alerts(all_alerts),
                'recommended_actions': self._compile_alert_recommendations(all_alerts),
                'system_health_indicators': {
                    'overall_health': 'critical' if critical_alerts else 'warning' if warning_alerts else 'good',
                    'requires_immediate_attention': len(critical_alerts) > 0,
                    'monitoring_needed': len(warning_alerts) > 0
                }
            }
            
            # Generate summary
            summary = {
                'total_alerts': len(all_alerts),
                'severity_breakdown': {
                    'critical': len(critical_alerts),
                    'warning': len(warning_alerts),
                    'info': len(info_alerts)
                },
                'system_status': 'critical' if critical_alerts else 'warning' if warning_alerts else 'healthy',
                'immediate_action_required': len(critical_alerts) > 0,
                'top_alert_types': self._get_top_alert_types(all_alerts)
            }
            
            # Format output
            formatted_data = await self._format_report_data(alert_data, request.format_type)
            
            report_id = f"alert_{request.period}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return ReportResult(
                report_id=report_id,
                report_type='alerts_and_anomalies',
                generated_at=datetime.utcnow(),
                period=request.period,
                format_type=request.format_type,
                data=formatted_data,
                summary=summary
            )
            
        except Exception as e:
            self.logger.error(f"Error generating alert report: {e}")
            return ReportResult(
                report_id=f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                report_type='alerts_and_anomalies',
                generated_at=datetime.utcnow(),
                period=request.period,
                format_type=request.format_type,
                data={'error': str(e)},
                summary={'error': str(e)}
            )
    
    async def _format_report_data(self, data: Dict[str, Any], format_type: str) -> Any:
        """Format report data according to requested format"""
        try:
            if format_type == ReportFormat.JSON.value:
                return data
            elif format_type == ReportFormat.CSV.value:
                return await self._convert_to_csv(data)
            elif format_type == ReportFormat.HTML.value:
                return await self._convert_to_html(data)
            elif format_type == ReportFormat.SUMMARY.value:
                return await self._create_summary_format(data)
            else:
                return data
        except Exception as e:
            self.logger.error(f"Error formatting report data: {e}")
            return data
    
    async def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert report data to CSV format"""
        try:
            output = io.StringIO()
            
            # Write metadata
            output.write("# Report Metadata\n")
            metadata = data.get('report_metadata', {})
            for key, value in metadata.items():
                output.write(f"{key},{value}\n")
            output.write("\n")
            
            # Write summary data
            if 'executive_summary' in data or 'audit_summary' in data or 'comparison_summary' in data:
                output.write("# Summary Data\n")
                summary_data = data.get('executive_summary') or data.get('audit_summary') or data.get('comparison_summary', {})
                for key, value in summary_data.items():
                    output.write(f"{key},{value}\n")
                output.write("\n")
            
            # Write detailed data if available
            if 'application_statistics' in data:
                output.write("# Application Statistics\n")
                stats = data['application_statistics']
                if 'by_role' in stats:
                    output.write("Role,Total Applications,Success Rate,Error Rate,Avg Per Day\n")
                    for role, role_stats in stats['by_role'].items():
                        output.write(f"{role},{role_stats.get('total_applications', 0)},{role_stats.get('success_rate', 0)},{role_stats.get('error_rate', 0)},{role_stats.get('average_per_day', 0)}\n")
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error converting to CSV: {e}")
            return f"Error generating CSV: {str(e)}"
    
    async def _convert_to_html(self, data: Dict[str, Any]) -> str:
        """Convert report data to HTML format"""
        try:
            html = ["<html><head><title>Application Tracking Report</title></head><body>"]
            
            # Add metadata
            metadata = data.get('report_metadata', {})
            html.append("<h1>Application Tracking Report</h1>")
            html.append(f"<p><strong>Generated:</strong> {metadata.get('generated_at', 'Unknown')}</p>")
            html.append(f"<p><strong>Period:</strong> {metadata.get('period', 'Unknown')}</p>")
            html.append(f"<p><strong>Report Type:</strong> {metadata.get('report_type', 'Unknown')}</p>")
            
            # Add summary
            if 'executive_summary' in data:
                html.append("<h2>Executive Summary</h2>")
                summary = data['executive_summary']
                html.append("<ul>")
                for key, value in summary.items():
                    html.append(f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>")
                html.append("</ul>")
            
            # Add role performance if available
            if 'role_performance' in data:
                html.append("<h2>Role Performance</h2>")
                html.append("<table border='1'><tr><th>Role</th><th>Applications</th><th>Success Rate</th><th>Error Rate</th></tr>")
                for role, stats in data['role_performance'].items():
                    html.append(f"<tr><td>{role}</td><td>{stats.get('total_applications', 0)}</td><td>{stats.get('success_rate', 0):.1f}%</td><td>{stats.get('error_rate', 0):.1f}%</td></tr>")
                html.append("</table>")
            
            html.append("</body></html>")
            return "".join(html)
            
        except Exception as e:
            self.logger.error(f"Error converting to HTML: {e}")
            return f"<html><body>Error generating HTML: {str(e)}</body></html>"
    
    async def _create_summary_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create condensed summary format"""
        try:
            summary = {
                'report_info': data.get('report_metadata', {}),
                'key_metrics': {},
                'top_insights': [],
                'critical_issues': [],
                'recommendations': []
            }
            
            # Extract key metrics
            if 'executive_summary' in data:
                summary['key_metrics'] = data['executive_summary']
            elif 'audit_summary' in data:
                summary['key_metrics'] = data['audit_summary']
            elif 'comparison_summary' in data:
                summary['key_metrics'] = data['comparison_summary']
            
            # Extract insights
            if 'insights' in data:
                summary['top_insights'] = data['insights'][:5]  # Top 5 insights
            elif 'key_insights' in data:
                summary['top_insights'] = data['key_insights'][:5]
            
            # Extract critical issues
            if 'alerts' in data:
                critical_alerts = [alert for alert in data['alerts'] if alert.get('severity') == 'critical']
                summary['critical_issues'] = [alert.get('title', 'Unknown issue') for alert in critical_alerts[:3]]
            
            # Extract recommendations
            if 'recommendations' in data:
                if isinstance(data['recommendations'], dict):
                    all_recs = []
                    for rec_list in data['recommendations'].values():
                        if isinstance(rec_list, list):
                            all_recs.extend(rec_list)
                    summary['recommendations'] = all_recs[:5]  # Top 5 recommendations
                elif isinstance(data['recommendations'], list):
                    summary['recommendations'] = data['recommendations'][:5]
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error creating summary format: {e}")
            return {'error': str(e)}
    
    def _get_top_performing_role(self, role_stats: Dict[str, Any]) -> str:
        """Get the top performing role based on success rate"""
        if not role_stats:
            return "none"
        
        top_role = max(role_stats.items(), 
                      key=lambda x: x[1].get('success_rate', 0), 
                      default=('none', {}))
        return top_role[0]
    
    def _categorize_alerts(self, alerts: List[Any]) -> Dict[str, int]:
        """Categorize alerts by type"""
        categories = {}
        for alert in alerts:
            alert_type = getattr(alert, 'alert_type', 'unknown')
            categories[alert_type] = categories.get(alert_type, 0) + 1
        return categories
    
    def _compile_alert_recommendations(self, alerts: List[Any]) -> List[str]:
        """Compile unique recommendations from all alerts"""
        recommendations = set()
        for alert in alerts:
            alert_recs = getattr(alert, 'recommendations', [])
            recommendations.update(alert_recs)
        return list(recommendations)[:10]  # Top 10 unique recommendations
    
    def _get_top_alert_types(self, alerts: List[Any]) -> List[str]:
        """Get the most common alert types"""
        categories = self._categorize_alerts(alerts)
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        return [cat[0] for cat in sorted_categories[:5]]  # Top 5 alert types

# Global admin reporting system instance
admin_reporting = AdminReportingSystem()

# Convenience functions for common reporting operations
async def get_admin_dashboard() -> Dict[str, Any]:
    """Get real-time admin dashboard data"""
    return await admin_reporting.generate_dashboard_report()

async def generate_weekly_performance_report() -> ReportResult:
    """Generate weekly performance report"""
    request = ReportRequest(
        report_type='performance_analysis',
        period=ReportPeriod.WEEKLY.value,
        format_type=ReportFormat.JSON.value
    )
    return await admin_reporting.generate_performance_report(request)

async def generate_monthly_audit_report() -> ReportResult:
    """Generate monthly audit report"""
    request = ReportRequest(
        report_type='audit_trail',
        period=ReportPeriod.MONTHLY.value,
        format_type=ReportFormat.JSON.value
    )
    return await admin_reporting.generate_audit_report(request)

async def generate_staff_client_comparison() -> ReportResult:
    """Generate staff vs client comparison report"""
    request = ReportRequest(
        report_type='staff_client_comparison',
        period=ReportPeriod.MONTHLY.value,
        format_type=ReportFormat.JSON.value
    )
    return await admin_reporting.generate_comparison_report(request)

async def check_system_alerts() -> ReportResult:
    """Check for system alerts and anomalies"""
    request = ReportRequest(
        report_type='alerts_and_anomalies',
        period=ReportPeriod.WEEKLY.value,
        format_type=ReportFormat.SUMMARY.value
    )
    return await admin_reporting.generate_alert_report(request)

async def export_audit_data_csv(days_back: int = 30) -> ReportResult:
    """Export audit data in CSV format"""
    request = ReportRequest(
        report_type='audit_trail',
        period=ReportPeriod.CUSTOM.value,
        start_date=datetime.utcnow() - timedelta(days=days_back),
        end_date=datetime.utcnow(),
        format_type=ReportFormat.CSV.value,
        include_details=True
    )
    return await admin_reporting.generate_audit_report(request)