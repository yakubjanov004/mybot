"""
Application tracking and reporting system for staff-created vs client-created applications.
Implements Requirements 6.1, 6.2, 6.3, 6.4 from multi-role application creation spec.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict

from database.models import ServiceRequest, StaffApplicationAudit, UserRole
from database.queries import db_manager
from utils.audit_viewer import audit_viewer, AuditFilter, AuditFilterType
from utils.audit_analyzer import StaffApplicationAuditAnalyzer, AnalysisAlert, AlertSeverity
from utils.logger import setup_module_logger

logger = setup_module_logger("application_tracker")

class ApplicationSource(Enum):
    """Source of application creation"""
    CLIENT = "client"
    STAFF = "staff"
    ALL = "all"

class ReportType(Enum):
    """Types of reports available"""
    SUMMARY = "summary"
    DETAILED = "detailed"
    COMPARISON = "comparison"
    TREND = "trend"
    PERFORMANCE = "performance"

class AlertType(Enum):
    """Types of alerts for unusual patterns"""
    HIGH_STAFF_CREATION_RATE = "high_staff_creation_rate"
    LOW_CLIENT_CREATION_RATE = "low_client_creation_rate"
    UNUSUAL_ROLE_ACTIVITY = "unusual_role_activity"
    SUCCESS_RATE_DROP = "success_rate_drop"
    ERROR_SPIKE = "error_spike"

@dataclass
class ApplicationStats:
    """Statistics for application creation"""
    total_applications: int
    client_created: int
    staff_created: int
    staff_creation_percentage: float
    success_rate: float
    error_rate: float
    average_per_day: float
    peak_hours: List[int]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RoleStats:
    """Statistics for a specific role"""
    role: str
    total_applications: int
    success_rate: float
    error_rate: float
    notification_success_rate: float
    workflow_success_rate: float
    average_per_day: float
    most_active_hours: List[int]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ComparisonReport:
    """Comparison between staff and client created applications"""
    period_days: int
    client_stats: ApplicationStats
    staff_stats: ApplicationStats
    role_breakdown: Dict[str, RoleStats]
    insights: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period_days': self.period_days,
            'client_stats': self.client_stats.to_dict(),
            'staff_stats': self.staff_stats.to_dict(),
            'role_breakdown': {role: stats.to_dict() for role, stats in self.role_breakdown.items()},
            'insights': self.insights,
            'recommendations': self.recommendations
        }

@dataclass
class TrackingAlert:
    """Alert for unusual application creation patterns"""
    alert_type: str
    severity: str
    title: str
    description: str
    metrics: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'metrics': self.metrics,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }

class ApplicationTracker:
    """Main application tracking and reporting system"""
    
    def __init__(self):
        self.logger = logger
        self.analyzer = StaffApplicationAuditAnalyzer()
        self._cache = {}
        self._cache_ttl = timedelta(minutes=10)
    
    async def get_application_statistics(self, 
                                       days_back: int = 30,
                                       source: ApplicationSource = ApplicationSource.ALL) -> ApplicationStats:
        """
        Get comprehensive application statistics.
        
        Args:
            days_back: Number of days to analyze
            source: Filter by application source
            
        Returns:
            ApplicationStats: Comprehensive statistics
        """
        try:
            cache_key = f"app_stats_{days_back}_{source.value}"
            if self._is_cached(cache_key):
                return self._cache[cache_key]['data']
            
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get all applications from service requests
            all_apps_query = """
            SELECT 
                id, created_by_staff, creation_source, created_at,
                current_status, completion_rating
            FROM service_requests 
            WHERE created_at >= $1
            ORDER BY created_at DESC
            """
            
            all_apps = await db_manager.fetch(all_apps_query, start_date)
            
            if not all_apps:
                return ApplicationStats(
                    total_applications=0,
                    client_created=0,
                    staff_created=0,
                    staff_creation_percentage=0.0,
                    success_rate=0.0,
                    error_rate=0.0,
                    average_per_day=0.0,
                    peak_hours=[]
                )
            
            # Filter by source if specified
            if source == ApplicationSource.CLIENT:
                filtered_apps = [app for app in all_apps if not app['created_by_staff']]
            elif source == ApplicationSource.STAFF:
                filtered_apps = [app for app in all_apps if app['created_by_staff']]
            else:
                filtered_apps = all_apps
            
            # Calculate statistics
            total_apps = len(filtered_apps)
            client_created = len([app for app in filtered_apps if not app['created_by_staff']])
            staff_created = len([app for app in filtered_apps if app['created_by_staff']])
            
            staff_percentage = (staff_created / total_apps * 100) if total_apps > 0 else 0
            
            # Success rate (completed applications)
            completed_apps = len([app for app in filtered_apps if app['current_status'] == 'completed'])
            success_rate = (completed_apps / total_apps * 100) if total_apps > 0 else 0
            
            # Error rate (cancelled or failed applications)
            error_apps = len([app for app in filtered_apps if app['current_status'] in ['cancelled', 'failed']])
            error_rate = (error_apps / total_apps * 100) if total_apps > 0 else 0
            
            # Average per day
            avg_per_day = total_apps / days_back if days_back > 0 else 0
            
            # Peak hours analysis
            hourly_counts = defaultdict(int)
            for app in filtered_apps:
                if app['created_at']:
                    hour = app['created_at'].hour
                    hourly_counts[hour] += 1
            
            # Get top 3 peak hours
            peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_hours_list = [hour for hour, count in peak_hours]
            
            stats = ApplicationStats(
                total_applications=total_apps,
                client_created=client_created,
                staff_created=staff_created,
                staff_creation_percentage=staff_percentage,
                success_rate=success_rate,
                error_rate=error_rate,
                average_per_day=avg_per_day,
                peak_hours=peak_hours_list
            )
            
            # Cache result
            self._cache_result(cache_key, stats)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting application statistics: {e}")
            return ApplicationStats(
                total_applications=0,
                client_created=0,
                staff_created=0,
                staff_creation_percentage=0.0,
                success_rate=0.0,
                error_rate=0.0,
                average_per_day=0.0,
                peak_hours=[]
            )
    
    async def get_role_statistics(self, days_back: int = 30) -> Dict[str, RoleStats]:
        """
        Get statistics broken down by staff role.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict mapping role names to their statistics
        """
        try:
            cache_key = f"role_stats_{days_back}"
            if self._is_cached(cache_key):
                return self._cache[cache_key]['data']
            
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get staff applications with audit data
            result = await audit_viewer.get_audit_trail(
                start_date=start_date,
                limit=10000
            )
            
            audits = result.audits
            role_data = defaultdict(lambda: {
                'total': 0,
                'successful': 0,
                'errors': 0,
                'notified': 0,
                'workflow_initiated': 0,
                'hourly_counts': defaultdict(int)
            })
            
            # Process audit data
            for audit in audits:
                role = audit.creator_role or 'unknown'
                role_data[role]['total'] += 1
                
                if audit.client_notified:
                    role_data[role]['notified'] += 1
                
                if audit.workflow_initiated:
                    role_data[role]['workflow_initiated'] += 1
                
                if audit.client_notified and audit.workflow_initiated:
                    role_data[role]['successful'] += 1
                
                if audit.metadata and audit.metadata.get('event_type') == 'error_occurred':
                    role_data[role]['errors'] += 1
                
                # Track hourly activity
                if audit.creation_timestamp:
                    hour = audit.creation_timestamp.hour
                    role_data[role]['hourly_counts'][hour] += 1
            
            # Convert to RoleStats objects
            role_stats = {}
            for role, data in role_data.items():
                total = data['total']
                if total == 0:
                    continue
                
                success_rate = (data['successful'] / total * 100)
                error_rate = (data['errors'] / total * 100)
                notification_rate = (data['notified'] / total * 100)
                workflow_rate = (data['workflow_initiated'] / total * 100)
                avg_per_day = total / days_back if days_back > 0 else 0
                
                # Get most active hours
                hourly_sorted = sorted(data['hourly_counts'].items(), key=lambda x: x[1], reverse=True)
                most_active_hours = [hour for hour, count in hourly_sorted[:3]]
                
                role_stats[role] = RoleStats(
                    role=role,
                    total_applications=total,
                    success_rate=success_rate,
                    error_rate=error_rate,
                    notification_success_rate=notification_rate,
                    workflow_success_rate=workflow_rate,
                    average_per_day=avg_per_day,
                    most_active_hours=most_active_hours
                )
            
            # Cache result
            self._cache_result(cache_key, role_stats)
            
            return role_stats
            
        except Exception as e:
            self.logger.error(f"Error getting role statistics: {e}")
            return {}
    
    async def generate_comparison_report(self, days_back: int = 30) -> ComparisonReport:
        """
        Generate comparison report between staff and client created applications.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            ComparisonReport: Detailed comparison analysis
        """
        try:
            # Get statistics for both sources
            client_stats = await self.get_application_statistics(days_back, ApplicationSource.CLIENT)
            staff_stats = await self.get_application_statistics(days_back, ApplicationSource.STAFF)
            role_breakdown = await self.get_role_statistics(days_back)
            
            # Generate insights
            insights = []
            recommendations = []
            
            # Staff vs Client creation analysis
            total_apps = client_stats.total_applications + staff_stats.total_applications
            if total_apps > 0:
                staff_percentage = (staff_stats.total_applications / total_apps * 100)
                
                if staff_percentage > 50:
                    insights.append(f"Staff create {staff_percentage:.1f}% of all applications, indicating high staff involvement in customer service")
                elif staff_percentage > 25:
                    insights.append(f"Staff create {staff_percentage:.1f}% of applications, showing balanced staff-client interaction")
                else:
                    insights.append(f"Staff create only {staff_percentage:.1f}% of applications, mostly client self-service")
            
            # Success rate comparison
            if staff_stats.success_rate > client_stats.success_rate + 10:
                insights.append(f"Staff-created applications have {staff_stats.success_rate - client_stats.success_rate:.1f}% higher success rate")
                recommendations.append("Consider promoting staff-assisted application creation for complex cases")
            elif client_stats.success_rate > staff_stats.success_rate + 10:
                insights.append(f"Client-created applications have {client_stats.success_rate - staff_stats.success_rate:.1f}% higher success rate")
                recommendations.append("Review staff application creation process for potential improvements")
            
            # Error rate analysis
            if staff_stats.error_rate > client_stats.error_rate + 5:
                insights.append(f"Staff applications have {staff_stats.error_rate - client_stats.error_rate:.1f}% higher error rate")
                recommendations.append("Provide additional training for staff on application creation best practices")
            
            # Activity pattern analysis
            if staff_stats.average_per_day > client_stats.average_per_day:
                insights.append("Staff are more active in application creation than clients on average")
                recommendations.append("Monitor staff workload to ensure balanced distribution")
            
            # Role-specific insights
            if role_breakdown:
                most_active_role = max(role_breakdown.items(), key=lambda x: x[1].total_applications)
                insights.append(f"{most_active_role[0].title()} is the most active role with {most_active_role[1].total_applications} applications")
                
                # Find roles with low success rates
                low_success_roles = [role for role, stats in role_breakdown.items() if stats.success_rate < 80]
                if low_success_roles:
                    recommendations.append(f"Review processes for roles with low success rates: {', '.join(low_success_roles)}")
            
            return ComparisonReport(
                period_days=days_back,
                client_stats=client_stats,
                staff_stats=staff_stats,
                role_breakdown=role_breakdown,
                insights=insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error generating comparison report: {e}")
            return ComparisonReport(
                period_days=days_back,
                client_stats=ApplicationStats(0, 0, 0, 0.0, 0.0, 0.0, 0.0, []),
                staff_stats=ApplicationStats(0, 0, 0, 0.0, 0.0, 0.0, 0.0, []),
                role_breakdown={},
                insights=[],
                recommendations=[]
            )
    
    async def detect_unusual_patterns(self, days_back: int = 7) -> List[TrackingAlert]:
        """
        Detect unusual patterns in application creation.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            List of alerts for unusual patterns
        """
        try:
            alerts = []
            
            # Get current and baseline statistics
            current_stats = await self.get_application_statistics(days_back)
            baseline_stats = await self.get_application_statistics(days_back * 2)  # Longer baseline
            
            # High staff creation rate alert
            if (current_stats.staff_creation_percentage > 70 and 
                baseline_stats.staff_creation_percentage < 50):
                alerts.append(TrackingAlert(
                    alert_type=AlertType.HIGH_STAFF_CREATION_RATE.value,
                    severity=AlertSeverity.WARNING.value,
                    title="Unusually High Staff Application Creation Rate",
                    description=f"Staff creation rate increased from {baseline_stats.staff_creation_percentage:.1f}% to {current_stats.staff_creation_percentage:.1f}%",
                    metrics={
                        'current_rate': current_stats.staff_creation_percentage,
                        'baseline_rate': baseline_stats.staff_creation_percentage,
                        'change': current_stats.staff_creation_percentage - baseline_stats.staff_creation_percentage
                    },
                    recommendations=[
                        "Investigate reasons for increased staff involvement",
                        "Check if client self-service systems are functioning properly",
                        "Review staff workload distribution"
                    ],
                    timestamp=datetime.utcnow()
                ))
            
            # Low client creation rate alert
            client_rate_current = (current_stats.client_created / current_stats.total_applications * 100) if current_stats.total_applications > 0 else 0
            client_rate_baseline = (baseline_stats.client_created / baseline_stats.total_applications * 100) if baseline_stats.total_applications > 0 else 0
            
            if client_rate_current < 30 and client_rate_baseline > 50:
                alerts.append(TrackingAlert(
                    alert_type=AlertType.LOW_CLIENT_CREATION_RATE.value,
                    severity=AlertSeverity.CRITICAL.value,
                    title="Significant Drop in Client Self-Service",
                    description=f"Client creation rate dropped from {client_rate_baseline:.1f}% to {client_rate_current:.1f}%",
                    metrics={
                        'current_rate': client_rate_current,
                        'baseline_rate': client_rate_baseline,
                        'change': client_rate_current - client_rate_baseline
                    },
                    recommendations=[
                        "Check client-facing application systems",
                        "Review user interface accessibility",
                        "Investigate potential system outages",
                        "Survey clients about application creation experience"
                    ],
                    timestamp=datetime.utcnow()
                ))
            
            # Success rate drop alert
            if (current_stats.success_rate < baseline_stats.success_rate - 15 and 
                baseline_stats.success_rate > 0):
                alerts.append(TrackingAlert(
                    alert_type=AlertType.SUCCESS_RATE_DROP.value,
                    severity=AlertSeverity.CRITICAL.value,
                    title="Significant Drop in Application Success Rate",
                    description=f"Success rate dropped from {baseline_stats.success_rate:.1f}% to {current_stats.success_rate:.1f}%",
                    metrics={
                        'current_rate': current_stats.success_rate,
                        'baseline_rate': baseline_stats.success_rate,
                        'change': current_stats.success_rate - baseline_stats.success_rate
                    },
                    recommendations=[
                        "Review recent system changes",
                        "Check workflow engine performance",
                        "Analyze notification system reliability",
                        "Review staff training effectiveness"
                    ],
                    timestamp=datetime.utcnow()
                ))
            
            # Error rate spike alert
            if current_stats.error_rate > baseline_stats.error_rate + 10:
                alerts.append(TrackingAlert(
                    alert_type=AlertType.ERROR_SPIKE.value,
                    severity=AlertSeverity.WARNING.value,
                    title="Spike in Application Error Rate",
                    description=f"Error rate increased from {baseline_stats.error_rate:.1f}% to {current_stats.error_rate:.1f}%",
                    metrics={
                        'current_rate': current_stats.error_rate,
                        'baseline_rate': baseline_stats.error_rate,
                        'change': current_stats.error_rate - baseline_stats.error_rate
                    },
                    recommendations=[
                        "Review error logs for common patterns",
                        "Check system resource utilization",
                        "Validate input validation rules",
                        "Review recent code deployments"
                    ],
                    timestamp=datetime.utcnow()
                ))
            
            # Role-specific unusual activity
            current_role_stats = await self.get_role_statistics(days_back)
            baseline_role_stats = await self.get_role_statistics(days_back * 2)
            
            for role, current_role_data in current_role_stats.items():
                if role in baseline_role_stats:
                    baseline_role_data = baseline_role_stats[role]
                    
                    # Unusual activity spike for specific role
                    if (current_role_data.average_per_day > baseline_role_data.average_per_day * 3 and
                        baseline_role_data.average_per_day > 0):
                        alerts.append(TrackingAlert(
                            alert_type=AlertType.UNUSUAL_ROLE_ACTIVITY.value,
                            severity=AlertSeverity.INFO.value,
                            title=f"Unusual Activity Spike for {role.title()}",
                            description=f"{role.title()} activity increased from {baseline_role_data.average_per_day:.1f} to {current_role_data.average_per_day:.1f} applications per day",
                            metrics={
                                'role': role,
                                'current_rate': current_role_data.average_per_day,
                                'baseline_rate': baseline_role_data.average_per_day,
                                'multiplier': current_role_data.average_per_day / baseline_role_data.average_per_day
                            },
                            recommendations=[
                                f"Check if {role} staff are handling special cases",
                                f"Review {role} workload distribution",
                                f"Investigate reasons for increased {role} activity"
                            ],
                            timestamp=datetime.utcnow()
                        ))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error detecting unusual patterns: {e}")
            return []
    
    async def generate_trend_report(self, days_back: int = 30, granularity: str = "daily") -> Dict[str, Any]:
        """
        Generate trend analysis report.
        
        Args:
            days_back: Number of days to analyze
            granularity: Time granularity (daily, hourly)
            
        Returns:
            Dict containing trend analysis
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get all applications
            apps_query = """
            SELECT created_at, created_by_staff, creation_source, current_status
            FROM service_requests 
            WHERE created_at >= $1
            ORDER BY created_at
            """
            
            apps = await db_manager.fetch(apps_query, start_date)
            
            # Group by time period
            time_groups = defaultdict(lambda: {
                'total': 0,
                'client_created': 0,
                'staff_created': 0,
                'successful': 0
            })
            
            for app in apps:
                if app['created_at']:
                    if granularity == "daily":
                        key = app['created_at'].date()
                    elif granularity == "hourly":
                        key = app['created_at'].replace(minute=0, second=0, microsecond=0)
                    else:
                        key = app['created_at'].date()
                    
                    time_groups[key]['total'] += 1
                    
                    if app['created_by_staff']:
                        time_groups[key]['staff_created'] += 1
                    else:
                        time_groups[key]['client_created'] += 1
                    
                    if app['current_status'] == 'completed':
                        time_groups[key]['successful'] += 1
            
            # Convert to trend data
            trend_data = []
            for time_key in sorted(time_groups.keys()):
                data = time_groups[time_key]
                staff_percentage = (data['staff_created'] / data['total'] * 100) if data['total'] > 0 else 0
                success_rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
                
                trend_data.append({
                    'timestamp': time_key.isoformat() if hasattr(time_key, 'isoformat') else str(time_key),
                    'total_applications': data['total'],
                    'client_created': data['client_created'],
                    'staff_created': data['staff_created'],
                    'staff_percentage': staff_percentage,
                    'success_rate': success_rate
                })
            
            # Calculate overall trends
            if len(trend_data) >= 2:
                # Simple trend calculation
                total_values = [point['total_applications'] for point in trend_data]
                staff_values = [point['staff_percentage'] for point in trend_data]
                success_values = [point['success_rate'] for point in trend_data]
                
                total_trend = "increasing" if total_values[-1] > total_values[0] else "decreasing" if total_values[-1] < total_values[0] else "stable"
                staff_trend = "increasing" if staff_values[-1] > staff_values[0] else "decreasing" if staff_values[-1] < staff_values[0] else "stable"
                success_trend = "increasing" if success_values[-1] > success_values[0] else "decreasing" if success_values[-1] < success_values[0] else "stable"
            else:
                total_trend = staff_trend = success_trend = "insufficient_data"
            
            return {
                'period_days': days_back,
                'granularity': granularity,
                'data_points': trend_data,
                'trends': {
                    'total_applications': total_trend,
                    'staff_percentage': staff_trend,
                    'success_rate': success_trend
                },
                'summary': {
                    'total_periods': len(trend_data),
                    'avg_applications_per_period': statistics.mean([point['total_applications'] for point in trend_data]) if trend_data else 0,
                    'avg_staff_percentage': statistics.mean([point['staff_percentage'] for point in trend_data]) if trend_data else 0,
                    'avg_success_rate': statistics.mean([point['success_rate'] for point in trend_data]) if trend_data else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating trend report: {e}")
            return {
                'period_days': days_back,
                'granularity': granularity,
                'data_points': [],
                'trends': {},
                'summary': {}
            }
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if result is cached and still valid"""
        if cache_key not in self._cache:
            return False
        
        cache_entry = self._cache[cache_key]
        return datetime.utcnow() - cache_entry['timestamp'] < self._cache_ttl
    
    def _cache_result(self, cache_key: str, data: Any):
        """Cache analysis result"""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.utcnow()
        }
    
    async def generate_comprehensive_tracking_report(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive tracking and reporting analysis.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict containing comprehensive tracking report
        """
        try:
            # Generate all report components
            overall_stats = await self.get_application_statistics(days_back)
            role_stats = await self.get_role_statistics(days_back)
            comparison_report = await self.generate_comparison_report(days_back)
            trend_report = await self.generate_trend_report(days_back)
            alerts = await self.detect_unusual_patterns(days_back)
            
            # Get audit analyzer insights
            audit_insights = await self.analyzer.generate_comprehensive_report(days_back)
            
            report = {
                'report_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'analysis_period_days': days_back,
                    'report_type': 'comprehensive_application_tracking'
                },
                'executive_summary': {
                    'total_applications': overall_stats.total_applications,
                    'staff_creation_percentage': overall_stats.staff_creation_percentage,
                    'overall_success_rate': overall_stats.success_rate,
                    'error_rate': overall_stats.error_rate,
                    'active_roles': len(role_stats),
                    'critical_alerts': len([a for a in alerts if a.severity == AlertSeverity.CRITICAL.value])
                },
                'application_statistics': {
                    'overall': overall_stats.to_dict(),
                    'by_source': {
                        'client': comparison_report.client_stats.to_dict(),
                        'staff': comparison_report.staff_stats.to_dict()
                    },
                    'by_role': {role: stats.to_dict() for role, stats in role_stats.items()}
                },
                'comparison_analysis': comparison_report.to_dict(),
                'trend_analysis': trend_report,
                'pattern_alerts': [alert.to_dict() for alert in alerts],
                'audit_insights': audit_insights,
                'recommendations': {
                    'immediate_actions': [alert.recommendations for alert in alerts if alert.severity == AlertSeverity.CRITICAL.value],
                    'process_improvements': comparison_report.recommendations,
                    'monitoring_suggestions': [
                        "Set up automated alerts for staff creation rate changes",
                        "Monitor role-specific performance metrics",
                        "Track client self-service adoption rates",
                        "Implement real-time success rate monitoring"
                    ]
                },
                'key_insights': comparison_report.insights + [
                    f"Staff handle {overall_stats.staff_creation_percentage:.1f}% of all applications",
                    f"System maintains {overall_stats.success_rate:.1f}% success rate overall",
                    f"Peak activity occurs during hours: {', '.join(map(str, overall_stats.peak_hours))}"
                ]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive tracking report: {e}")
            return {
                'report_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'analysis_period_days': days_back,
                    'report_type': 'comprehensive_application_tracking',
                    'error': str(e)
                },
                'executive_summary': {},
                'application_statistics': {},
                'comparison_analysis': {},
                'trend_analysis': {},
                'pattern_alerts': [],
                'audit_insights': {},
                'recommendations': {},
                'key_insights': []
            }

# Global application tracker instance
application_tracker = ApplicationTracker()

# Convenience functions for common tracking operations
async def get_staff_vs_client_stats(days: int = 30) -> Dict[str, ApplicationStats]:
    """Get comparison statistics between staff and client created applications"""
    client_stats = await application_tracker.get_application_statistics(days, ApplicationSource.CLIENT)
    staff_stats = await application_tracker.get_application_statistics(days, ApplicationSource.STAFF)
    return {
        'client': client_stats,
        'staff': staff_stats
    }

async def get_role_performance_report(days: int = 30) -> Dict[str, RoleStats]:
    """Get performance report for all staff roles"""
    return await application_tracker.get_role_statistics(days)

async def check_for_unusual_activity(days: int = 7) -> List[TrackingAlert]:
    """Check for unusual patterns in application creation"""
    return await application_tracker.detect_unusual_patterns(days)

async def generate_daily_tracking_summary() -> Dict[str, Any]:
    """Generate daily tracking summary for administrators"""
    return await application_tracker.generate_comprehensive_tracking_report(1)

async def generate_weekly_tracking_report() -> Dict[str, Any]:
    """Generate weekly tracking report for management"""
    return await application_tracker.generate_comprehensive_tracking_report(7)

async def generate_monthly_tracking_report() -> Dict[str, Any]:
    """Generate monthly tracking report for strategic analysis"""
    return await application_tracker.generate_comprehensive_tracking_report(30)