"""
Audit log analysis and reporting features.
Implements Requirements 6.4 from multi-role application creation spec.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import defaultdict

from database.models import StaffApplicationAudit, UserRole
from utils.audit_viewer import audit_viewer, AuditFilter, AuditFilterType
from utils.logger import setup_module_logger

logger = setup_module_logger("audit_analyzer")

class AnalysisType(Enum):
    """Types of audit analysis"""
    PERFORMANCE_ANALYSIS = "performance_analysis"
    TREND_ANALYSIS = "trend_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    COMPLIANCE_ANALYSIS = "compliance_analysis"
    USER_BEHAVIOR_ANALYSIS = "user_behavior_analysis"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class AnalysisAlert:
    """Alert generated from audit analysis"""
    alert_type: str
    severity: str
    title: str
    description: str
    affected_entities: List[Any]
    timestamp: datetime
    recommendations: List[str]
    metrics: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    """Performance metrics for staff application creation"""
    total_applications: int
    success_rate: float
    average_processing_time: Optional[float]
    error_rate: float
    notification_success_rate: float
    workflow_initiation_rate: float
    applications_per_day: float
    peak_usage_hours: List[int]

@dataclass
class TrendData:
    """Trend analysis data"""
    period: str
    data_points: List[Tuple[datetime, float]]
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # 0-1, how strong the trend is
    forecast: Optional[List[Tuple[datetime, float]]]

class StaffApplicationAuditAnalyzer:
    """Advanced analyzer for staff application audit data"""
    
    def __init__(self):
        self.logger = logger
        self._analysis_cache = {}
        self._cache_ttl = timedelta(minutes=15)
    
    async def analyze_performance_metrics(self, 
                                        days_back: int = 30,
                                        role_filter: Optional[str] = None) -> PerformanceMetrics:
        """
        Analyze performance metrics for staff application creation.
        
        Args:
            days_back: Number of days to analyze
            role_filter: Optional role to filter by
            
        Returns:
            PerformanceMetrics: Comprehensive performance analysis
        """
        try:
            cache_key = f"performance_{days_back}_{role_filter}"
            if self._is_cached(cache_key):
                return self._analysis_cache[cache_key]['data']
            
            start_date = datetime.utcnow() - timedelta(days=days_back)
            filters = []
            
            if role_filter:
                filters.append(AuditFilter(AuditFilterType.BY_ROLE.value, role_filter))
            
            result = await audit_viewer.get_audit_trail(
                filters=filters,
                start_date=start_date,
                limit=10000
            )
            
            audits = result.audits
            
            if not audits:
                return PerformanceMetrics(
                    total_applications=0,
                    success_rate=0.0,
                    average_processing_time=None,
                    error_rate=0.0,
                    notification_success_rate=0.0,
                    workflow_initiation_rate=0.0,
                    applications_per_day=0.0,
                    peak_usage_hours=[]
                )
            
            # Calculate metrics
            total_apps = len(audits)
            successful_apps = sum(1 for audit in audits if audit.client_notified and audit.workflow_initiated)
            notified_apps = sum(1 for audit in audits if audit.client_notified)
            workflow_apps = sum(1 for audit in audits if audit.workflow_initiated)
            error_apps = sum(1 for audit in audits if audit.metadata and 
                           audit.metadata.get('event_type') == 'error_occurred')
            
            # Calculate rates
            success_rate = (successful_apps / total_apps * 100) if total_apps > 0 else 0
            error_rate = (error_apps / total_apps * 100) if total_apps > 0 else 0
            notification_rate = (notified_apps / total_apps * 100) if total_apps > 0 else 0
            workflow_rate = (workflow_apps / total_apps * 100) if total_apps > 0 else 0
            
            # Applications per day
            apps_per_day = total_apps / days_back if days_back > 0 else 0
            
            # Peak usage hours
            hourly_counts = defaultdict(int)
            for audit in audits:
                if audit.creation_timestamp:
                    hour = audit.creation_timestamp.hour
                    hourly_counts[hour] += 1
            
            # Get top 3 peak hours
            peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_usage_hours = [hour for hour, count in peak_hours]
            
            metrics = PerformanceMetrics(
                total_applications=total_apps,
                success_rate=success_rate,
                average_processing_time=None,  # Would need additional timing data
                error_rate=error_rate,
                notification_success_rate=notification_rate,
                workflow_initiation_rate=workflow_rate,
                applications_per_day=apps_per_day,
                peak_usage_hours=peak_usage_hours
            )
            
            # Cache result
            self._cache_result(cache_key, metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance metrics: {e}")
            return PerformanceMetrics(
                total_applications=0,
                success_rate=0.0,
                average_processing_time=None,
                error_rate=0.0,
                notification_success_rate=0.0,
                workflow_initiation_rate=0.0,
                applications_per_day=0.0,
                peak_usage_hours=[]
            )
    
    async def analyze_trends(self, 
                           metric: str = "application_count",
                           days_back: int = 30,
                           granularity: str = "daily") -> TrendData:
        """
        Analyze trends in staff application creation.
        
        Args:
            metric: Metric to analyze trends for
            days_back: Number of days to analyze
            granularity: Time granularity (daily, hourly)
            
        Returns:
            TrendData: Trend analysis results
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            result = await audit_viewer.get_audit_trail(
                start_date=start_date,
                limit=10000
            )
            
            audits = result.audits
            
            # Group data by time period
            time_groups = defaultdict(int)
            
            for audit in audits:
                if audit.creation_timestamp:
                    if granularity == "daily":
                        key = audit.creation_timestamp.date()
                    elif granularity == "hourly":
                        key = audit.creation_timestamp.replace(minute=0, second=0, microsecond=0)
                    else:
                        key = audit.creation_timestamp.date()
                    
                    if metric == "application_count":
                        time_groups[key] += 1
                    elif metric == "success_rate":
                        # For success rate, we need to track both total and successful
                        if not hasattr(time_groups[key], '__iter__'):
                            time_groups[key] = [0, 0]  # [total, successful]
                        time_groups[key][0] += 1
                        if audit.client_notified and audit.workflow_initiated:
                            time_groups[key][1] += 1
            
            # Convert to data points
            data_points = []
            for time_key in sorted(time_groups.keys()):
                if metric == "application_count":
                    value = time_groups[time_key]
                elif metric == "success_rate":
                    total, successful = time_groups[time_key]
                    value = (successful / total * 100) if total > 0 else 0
                else:
                    value = time_groups[time_key]
                
                data_points.append((time_key, float(value)))
            
            # Calculate trend
            if len(data_points) < 2:
                trend_direction = "stable"
                trend_strength = 0.0
            else:
                values = [point[1] for point in data_points]
                
                # Simple linear trend calculation
                x_values = list(range(len(values)))
                if len(values) > 1:
                    correlation = self._calculate_correlation(x_values, values)
                    
                    if correlation > 0.3:
                        trend_direction = "increasing"
                        trend_strength = abs(correlation)
                    elif correlation < -0.3:
                        trend_direction = "decreasing"
                        trend_strength = abs(correlation)
                    else:
                        trend_direction = "stable"
                        trend_strength = abs(correlation)
                else:
                    trend_direction = "stable"
                    trend_strength = 0.0
            
            return TrendData(
                period=f"{days_back}_days_{granularity}",
                data_points=data_points,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                forecast=None  # Could implement forecasting later
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return TrendData(
                period=f"{days_back}_days_{granularity}",
                data_points=[],
                trend_direction="stable",
                trend_strength=0.0,
                forecast=None
            )
    
    async def detect_anomalies(self, days_back: int = 7) -> List[AnalysisAlert]:
        """
        Detect anomalies in staff application creation patterns.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            List[AnalysisAlert]: List of detected anomalies
        """
        try:
            alerts = []
            
            # Get recent performance metrics
            current_metrics = await self.analyze_performance_metrics(days_back)
            baseline_metrics = await self.analyze_performance_metrics(days_back * 2)  # Longer baseline
            
            # Detect significant changes in success rate
            if baseline_metrics.success_rate > 0:
                success_rate_change = ((current_metrics.success_rate - baseline_metrics.success_rate) / 
                                     baseline_metrics.success_rate * 100)
                
                if success_rate_change < -20:  # 20% decrease
                    alerts.append(AnalysisAlert(
                        alert_type="success_rate_drop",
                        severity=AlertSeverity.CRITICAL.value,
                        title="Significant Drop in Success Rate",
                        description=f"Success rate dropped by {abs(success_rate_change):.1f}% from {baseline_metrics.success_rate:.1f}% to {current_metrics.success_rate:.1f}%",
                        affected_entities=[],
                        timestamp=datetime.utcnow(),
                        recommendations=[
                            "Review recent system changes",
                            "Check notification system status",
                            "Analyze workflow engine performance",
                            "Review staff training needs"
                        ],
                        metrics={
                            "current_success_rate": current_metrics.success_rate,
                            "baseline_success_rate": baseline_metrics.success_rate,
                            "change_percentage": success_rate_change
                        }
                    ))
            
            # Detect unusual error rate
            if current_metrics.error_rate > 10:  # More than 10% error rate
                alerts.append(AnalysisAlert(
                    alert_type="high_error_rate",
                    severity=AlertSeverity.WARNING.value,
                    title="High Error Rate Detected",
                    description=f"Current error rate is {current_metrics.error_rate:.1f}%, above normal threshold",
                    affected_entities=[],
                    timestamp=datetime.utcnow(),
                    recommendations=[
                        "Review error logs for common patterns",
                        "Check system resource usage",
                        "Validate input validation rules",
                        "Review staff training materials"
                    ],
                    metrics={
                        "current_error_rate": current_metrics.error_rate,
                        "threshold": 10.0
                    }
                ))
            
            # Detect unusual activity patterns
            if current_metrics.applications_per_day > baseline_metrics.applications_per_day * 2:
                alerts.append(AnalysisAlert(
                    alert_type="unusual_activity_spike",
                    severity=AlertSeverity.INFO.value,
                    title="Unusual Activity Spike",
                    description=f"Application creation rate is {current_metrics.applications_per_day:.1f} per day, significantly higher than baseline of {baseline_metrics.applications_per_day:.1f}",
                    affected_entities=[],
                    timestamp=datetime.utcnow(),
                    recommendations=[
                        "Monitor system performance",
                        "Check for promotional campaigns or events",
                        "Ensure adequate system capacity",
                        "Review staff workload distribution"
                    ],
                    metrics={
                        "current_rate": current_metrics.applications_per_day,
                        "baseline_rate": baseline_metrics.applications_per_day
                    }
                ))
            
            # Role-specific anomaly detection
            role_alerts = await self._detect_role_anomalies(days_back)
            alerts.extend(role_alerts)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return []
    
    async def _detect_role_anomalies(self, days_back: int) -> List[AnalysisAlert]:
        """Detect role-specific anomalies"""
        alerts = []
        
        try:
            roles = [role.value for role in UserRole if role.value in ['manager', 'junior_manager', 'controller', 'call_center']]
            
            for role in roles:
                current_metrics = await self.analyze_performance_metrics(days_back, role)
                baseline_metrics = await self.analyze_performance_metrics(days_back * 2, role)
                
                # Check for role-specific issues
                if current_metrics.total_applications > 0 and current_metrics.success_rate < 50:
                    alerts.append(AnalysisAlert(
                        alert_type="role_low_success_rate",
                        severity=AlertSeverity.WARNING.value,
                        title=f"Low Success Rate for {role.title()}",
                        description=f"{role.title()} role has success rate of {current_metrics.success_rate:.1f}%",
                        affected_entities=[role],
                        timestamp=datetime.utcnow(),
                        recommendations=[
                            f"Review {role} training materials",
                            f"Analyze common errors for {role} users",
                            f"Consider additional support for {role} staff"
                        ],
                        metrics={
                            "role": role,
                            "success_rate": current_metrics.success_rate,
                            "total_applications": current_metrics.total_applications
                        }
                    ))
                
                # Check for sudden drops in activity
                if (baseline_metrics.applications_per_day > 1 and 
                    current_metrics.applications_per_day < baseline_metrics.applications_per_day * 0.3):
                    alerts.append(AnalysisAlert(
                        alert_type="role_activity_drop",
                        severity=AlertSeverity.INFO.value,
                        title=f"Activity Drop for {role.title()}",
                        description=f"{role.title()} activity dropped from {baseline_metrics.applications_per_day:.1f} to {current_metrics.applications_per_day:.1f} applications per day",
                        affected_entities=[role],
                        timestamp=datetime.utcnow(),
                        recommendations=[
                            f"Check if {role} staff are available",
                            f"Review {role} workload distribution",
                            f"Verify {role} system access"
                        ],
                        metrics={
                            "role": role,
                            "current_rate": current_metrics.applications_per_day,
                            "baseline_rate": baseline_metrics.applications_per_day
                        }
                    ))
        
        except Exception as e:
            self.logger.error(f"Error detecting role anomalies: {e}")
        
        return alerts
    
    async def analyze_compliance(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze compliance with audit requirements.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict containing compliance analysis
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            result = await audit_viewer.get_audit_trail(
                start_date=start_date,
                limit=10000
            )
            
            audits = result.audits
            
            compliance_report = {
                'period_days': days_back,
                'total_applications': len(audits),
                'compliance_metrics': {
                    'audit_coverage': 0.0,  # Percentage of applications with audit records
                    'notification_compliance': 0.0,  # Percentage with client notifications
                    'workflow_compliance': 0.0,  # Percentage with workflow initiation
                    'data_completeness': 0.0,  # Percentage with complete audit data
                },
                'violations': [],
                'recommendations': []
            }
            
            if not audits:
                return compliance_report
            
            # Calculate compliance metrics
            total = len(audits)
            notified_count = sum(1 for audit in audits if audit.client_notified)
            workflow_count = sum(1 for audit in audits if audit.workflow_initiated)
            complete_data_count = sum(1 for audit in audits if self._is_audit_data_complete(audit))
            
            compliance_report['compliance_metrics'] = {
                'audit_coverage': 100.0,  # All applications have audit records by definition
                'notification_compliance': (notified_count / total * 100) if total > 0 else 0,
                'workflow_compliance': (workflow_count / total * 100) if total > 0 else 0,
                'data_completeness': (complete_data_count / total * 100) if total > 0 else 0,
            }
            
            # Identify violations
            violations = []
            
            # Applications without client notification
            unnotified_count = total - notified_count
            if unnotified_count > 0:
                violations.append({
                    'type': 'missing_client_notification',
                    'count': unnotified_count,
                    'percentage': (unnotified_count / total * 100),
                    'description': f"{unnotified_count} applications created without client notification"
                })
            
            # Applications without workflow initiation
            no_workflow_count = total - workflow_count
            if no_workflow_count > 0:
                violations.append({
                    'type': 'missing_workflow_initiation',
                    'count': no_workflow_count,
                    'percentage': (no_workflow_count / total * 100),
                    'description': f"{no_workflow_count} applications created without workflow initiation"
                })
            
            # Incomplete audit data
            incomplete_data_count = total - complete_data_count
            if incomplete_data_count > 0:
                violations.append({
                    'type': 'incomplete_audit_data',
                    'count': incomplete_data_count,
                    'percentage': (incomplete_data_count / total * 100),
                    'description': f"{incomplete_data_count} applications with incomplete audit data"
                })
            
            compliance_report['violations'] = violations
            
            # Generate recommendations
            recommendations = []
            
            if compliance_report['compliance_metrics']['notification_compliance'] < 95:
                recommendations.append("Implement automated client notification verification")
                recommendations.append("Review notification system reliability")
            
            if compliance_report['compliance_metrics']['workflow_compliance'] < 95:
                recommendations.append("Implement workflow initiation monitoring")
                recommendations.append("Add workflow status validation")
            
            if compliance_report['compliance_metrics']['data_completeness'] < 90:
                recommendations.append("Enhance audit data collection processes")
                recommendations.append("Implement data validation checks")
            
            compliance_report['recommendations'] = recommendations
            
            return compliance_report
            
        except Exception as e:
            self.logger.error(f"Error analyzing compliance: {e}")
            return {
                'period_days': days_back,
                'total_applications': 0,
                'compliance_metrics': {},
                'violations': [],
                'recommendations': []
            }
    
    def _is_audit_data_complete(self, audit: StaffApplicationAudit) -> bool:
        """Check if audit data is complete"""
        required_fields = [
            audit.application_id,
            audit.creator_id,
            audit.creator_role,
            audit.client_id,
            audit.application_type,
            audit.creation_timestamp
        ]
        
        return all(field is not None for field in required_fields)
    
    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate correlation coefficient between two series"""
        try:
            if len(x_values) != len(y_values) or len(x_values) < 2:
                return 0.0
            
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            sum_y2 = sum(y * y for y in y_values)
            
            numerator = n * sum_xy - sum_x * sum_y
            denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator
            
        except Exception:
            return 0.0
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if result is cached and still valid"""
        if cache_key not in self._analysis_cache:
            return False
        
        cache_entry = self._analysis_cache[cache_key]
        return datetime.utcnow() - cache_entry['timestamp'] < self._cache_ttl
    
    def _cache_result(self, cache_key: str, data: Any):
        """Cache analysis result"""
        self._analysis_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.utcnow()
        }
    
    async def generate_comprehensive_report(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive audit analysis report.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict containing comprehensive analysis report
        """
        try:
            # Run all analyses
            performance_metrics = await self.analyze_performance_metrics(days_back)
            trend_analysis = await self.analyze_trends("application_count", days_back)
            success_trend = await self.analyze_trends("success_rate", days_back)
            anomalies = await self.detect_anomalies(days_back)
            compliance = await self.analyze_compliance(days_back)
            
            # System summary
            system_summary = await audit_viewer.get_system_audit_summary(days_back)
            
            report = {
                'report_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'analysis_period_days': days_back,
                    'report_type': 'comprehensive_audit_analysis'
                },
                'executive_summary': {
                    'total_applications': performance_metrics.total_applications,
                    'overall_success_rate': performance_metrics.success_rate,
                    'error_rate': performance_metrics.error_rate,
                    'trend_direction': trend_analysis.trend_direction,
                    'critical_alerts': len([a for a in anomalies if a.severity == AlertSeverity.CRITICAL.value]),
                    'compliance_score': sum(compliance['compliance_metrics'].values()) / len(compliance['compliance_metrics']) if compliance['compliance_metrics'] else 0
                },
                'performance_analysis': {
                    'metrics': performance_metrics,
                    'role_breakdown': system_summary.get('role_performance', {}),
                    'application_type_distribution': system_summary.get('application_type_distribution', {})
                },
                'trend_analysis': {
                    'application_volume_trend': trend_analysis,
                    'success_rate_trend': success_trend,
                    'peak_usage_patterns': system_summary.get('peak_usage_times', {})
                },
                'anomaly_detection': {
                    'alerts': anomalies,
                    'alert_summary': {
                        'total_alerts': len(anomalies),
                        'critical_alerts': len([a for a in anomalies if a.severity == AlertSeverity.CRITICAL.value]),
                        'warning_alerts': len([a for a in anomalies if a.severity == AlertSeverity.WARNING.value]),
                        'info_alerts': len([a for a in anomalies if a.severity == AlertSeverity.INFO.value])
                    }
                },
                'compliance_analysis': compliance,
                'recommendations': {
                    'immediate_actions': [a.recommendations for a in anomalies if a.severity == AlertSeverity.CRITICAL.value],
                    'improvement_opportunities': compliance.get('recommendations', []),
                    'monitoring_suggestions': [
                        "Set up automated alerts for success rate drops",
                        "Implement real-time error rate monitoring",
                        "Create role-specific performance dashboards",
                        "Schedule regular compliance audits"
                    ]
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            return {
                'report_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'analysis_period_days': days_back,
                    'report_type': 'comprehensive_audit_analysis',
                    'error': str(e)
                },
                'executive_summary': {},
                'performance_analysis': {},
                'trend_analysis': {},
                'anomaly_detection': {},
                'compliance_analysis': {},
                'recommendations': {}
            }

# Global audit analyzer instance
audit_analyzer = StaffApplicationAuditAnalyzer()

# Convenience functions for common analysis operations
async def get_performance_summary(days: int = 7) -> PerformanceMetrics:
    """Get performance summary for recent period"""
    return await audit_analyzer.analyze_performance_metrics(days)

async def get_trend_summary(days: int = 30) -> TrendData:
    """Get trend summary for application creation"""
    return await audit_analyzer.analyze_trends("application_count", days)

async def get_current_alerts(days: int = 7) -> List[AnalysisAlert]:
    """Get current anomaly alerts"""
    return await audit_analyzer.detect_anomalies(days)

async def get_compliance_status(days: int = 30) -> Dict[str, Any]:
    """Get compliance status summary"""
    return await audit_analyzer.analyze_compliance(days)

async def generate_daily_report() -> Dict[str, Any]:
    """Generate daily audit analysis report"""
    return await audit_analyzer.generate_comprehensive_report(1)

async def generate_weekly_report() -> Dict[str, Any]:
    """Generate weekly audit analysis report"""
    return await audit_analyzer.generate_comprehensive_report(7)

async def generate_monthly_report() -> Dict[str, Any]:
    """Generate monthly audit analysis report"""
    return await audit_analyzer.generate_comprehensive_report(30)