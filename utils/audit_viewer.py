"""
Audit trail viewing capabilities for administrators.
Implements Requirements 6.3, 6.4 from multi-role application creation spec.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from database.models import StaffApplicationAudit, UserRole
from database.staff_creation_queries import get_staff_application_audits
from database.queries import db_manager
from utils.logger import setup_module_logger

logger = setup_module_logger("audit_viewer")

class AuditFilterType(Enum):
    """Types of audit filters"""
    BY_CREATOR = "by_creator"
    BY_CLIENT = "by_client"
    BY_APPLICATION_TYPE = "by_application_type"
    BY_DATE_RANGE = "by_date_range"
    BY_ROLE = "by_role"
    BY_SUCCESS_STATUS = "by_success_status"

@dataclass
class AuditFilter:
    """Filter for audit queries"""
    filter_type: str
    value: Any
    operator: str = "equals"  # equals, contains, greater_than, less_than, between

@dataclass
class AuditViewResult:
    """Result of audit view query"""
    audits: List[StaffApplicationAudit]
    total_count: int
    filtered_count: int
    summary: Dict[str, Any]

class StaffApplicationAuditViewer:
    """Viewer for staff application audit trails"""
    
    def __init__(self):
        self.logger = logger
    
    async def get_audit_trail(self,
                            filters: List[AuditFilter] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            limit: int = 100,
                            offset: int = 0,
                            sort_by: str = "creation_timestamp",
                            sort_order: str = "desc") -> AuditViewResult:
        """
        Get audit trail with filtering and pagination.
        
        Args:
            filters: List of filters to apply
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of records to return
            offset: Number of records to skip
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            AuditViewResult: Filtered audit results with summary
        """
        try:
            # Build query conditions
            conditions = []
            params = []
            param_count = 0
            
            # Date range filter
            if start_date:
                param_count += 1
                conditions.append(f"creation_timestamp >= ${param_count}")
                params.append(start_date)
            
            if end_date:
                param_count += 1
                conditions.append(f"creation_timestamp <= ${param_count}")
                params.append(end_date)
            
            # Apply custom filters
            if filters:
                for filter_obj in filters:
                    condition, filter_params = self._build_filter_condition(filter_obj, param_count)
                    if condition:
                        conditions.append(condition)
                        params.extend(filter_params)
                        param_count += len(filter_params)
            
            # Build WHERE clause
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            # Build ORDER BY clause
            order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM staff_application_audit {where_clause}"
            total_count = await db_manager.fetchval(count_query, *params)
            
            # Get filtered results
            param_count += 1
            limit_param = param_count
            param_count += 1
            offset_param = param_count
            
            query = f"""
            SELECT * FROM staff_application_audit 
            {where_clause}
            {order_clause}
            LIMIT ${limit_param} OFFSET ${offset_param}
            """
            
            params.extend([limit, offset])
            rows = await db_manager.fetch(query, *params)
            
            # Convert to audit objects
            audits = []
            for row in rows:
                row_dict = dict(row)
                if row_dict.get('metadata'):
                    import json
                    row_dict['metadata'] = json.loads(row_dict['metadata']) if isinstance(row_dict['metadata'], str) else row_dict['metadata']
                audits.append(StaffApplicationAudit.from_dict(row_dict))
            
            # Generate summary
            summary = await self._generate_summary(audits, where_clause, params[:-2])  # Exclude limit/offset params
            
            return AuditViewResult(
                audits=audits,
                total_count=total_count or 0,
                filtered_count=len(audits),
                summary=summary
            )
            
        except Exception as e:
            self.logger.error(f"Error getting audit trail: {e}")
            return AuditViewResult(audits=[], total_count=0, filtered_count=0, summary={})
    
    def _build_filter_condition(self, filter_obj: AuditFilter, param_offset: int) -> Tuple[str, List[Any]]:
        """Build SQL condition for a filter"""
        try:
            if filter_obj.filter_type == AuditFilterType.BY_CREATOR.value:
                return f"creator_id = ${param_offset + 1}", [filter_obj.value]
            
            elif filter_obj.filter_type == AuditFilterType.BY_CLIENT.value:
                return f"client_id = ${param_offset + 1}", [filter_obj.value]
            
            elif filter_obj.filter_type == AuditFilterType.BY_APPLICATION_TYPE.value:
                return f"application_type = ${param_offset + 1}", [filter_obj.value]
            
            elif filter_obj.filter_type == AuditFilterType.BY_ROLE.value:
                return f"creator_role = ${param_offset + 1}", [filter_obj.value]
            
            elif filter_obj.filter_type == AuditFilterType.BY_SUCCESS_STATUS.value:
                if filter_obj.value:
                    return "client_notified = true AND workflow_initiated = true", []
                else:
                    return "client_notified = false OR workflow_initiated = false", []
            
            return "", []
            
        except Exception as e:
            self.logger.error(f"Error building filter condition: {e}")
            return "", []
    
    async def _generate_summary(self, audits: List[StaffApplicationAudit], where_clause: str, params: List[Any]) -> Dict[str, Any]:
        """Generate summary statistics for audit results"""
        try:
            summary = {
                'total_applications': len(audits),
                'applications_by_role': {},
                'applications_by_type': {},
                'success_rate': 0.0,
                'notification_rate': 0.0,
                'workflow_initiation_rate': 0.0,
                'most_active_creators': [],
                'error_count': 0,
                'time_distribution': {}
            }
            
            if not audits:
                return summary
            
            # Count by role
            role_counts = {}
            type_counts = {}
            successful_count = 0
            notified_count = 0
            workflow_initiated_count = 0
            creator_counts = {}
            
            for audit in audits:
                # Role distribution
                role = audit.creator_role or 'unknown'
                role_counts[role] = role_counts.get(role, 0) + 1
                
                # Type distribution
                app_type = audit.application_type or 'unknown'
                type_counts[app_type] = type_counts.get(app_type, 0) + 1
                
                # Success metrics
                if audit.client_notified and audit.workflow_initiated:
                    successful_count += 1
                
                if audit.client_notified:
                    notified_count += 1
                
                if audit.workflow_initiated:
                    workflow_initiated_count += 1
                
                # Creator activity
                creator_id = audit.creator_id
                if creator_id:
                    creator_counts[creator_id] = creator_counts.get(creator_id, 0) + 1
                
                # Error count (check metadata for error events)
                if audit.metadata and audit.metadata.get('event_type') in ['error_occurred', 'validation_failed']:
                    summary['error_count'] += 1
            
            # Calculate rates
            total = len(audits)
            summary['applications_by_role'] = role_counts
            summary['applications_by_type'] = type_counts
            summary['success_rate'] = (successful_count / total * 100) if total > 0 else 0
            summary['notification_rate'] = (notified_count / total * 100) if total > 0 else 0
            summary['workflow_initiation_rate'] = (workflow_initiated_count / total * 100) if total > 0 else 0
            
            # Most active creators
            sorted_creators = sorted(creator_counts.items(), key=lambda x: x[1], reverse=True)
            summary['most_active_creators'] = [
                {'creator_id': creator_id, 'count': count} 
                for creator_id, count in sorted_creators[:5]
            ]
            
            # Time distribution (by hour of day)
            hour_distribution = {}
            for audit in audits:
                if audit.creation_timestamp:
                    hour = audit.creation_timestamp.hour
                    hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            
            summary['time_distribution'] = hour_distribution
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating audit summary: {e}")
            return {}
    
    async def get_creator_activity_report(self, 
                                        creator_id: int,
                                        days_back: int = 30) -> Dict[str, Any]:
        """
        Get detailed activity report for a specific creator.
        
        Args:
            creator_id: ID of the creator
            days_back: Number of days to look back
            
        Returns:
            Dict containing detailed activity report
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            filters = [AuditFilter(AuditFilterType.BY_CREATOR.value, creator_id)]
            result = await self.get_audit_trail(
                filters=filters,
                start_date=start_date,
                limit=1000  # Get all records for this creator
            )
            
            audits = result.audits
            
            # Detailed analysis
            report = {
                'creator_id': creator_id,
                'period_days': days_back,
                'total_applications': len(audits),
                'applications_by_type': {},
                'applications_by_day': {},
                'success_metrics': {
                    'successful_applications': 0,
                    'failed_notifications': 0,
                    'failed_workflows': 0,
                    'validation_errors': 0
                },
                'client_interactions': {
                    'unique_clients': set(),
                    'new_clients_created': 0,
                    'existing_clients_used': 0
                },
                'performance_metrics': {
                    'avg_applications_per_day': 0,
                    'peak_activity_hour': None,
                    'most_active_day': None
                },
                'error_analysis': []
            }
            
            daily_counts = {}
            hourly_counts = {}
            
            for audit in audits:
                # Type distribution
                app_type = audit.application_type or 'unknown'
                report['applications_by_type'][app_type] = report['applications_by_type'].get(app_type, 0) + 1
                
                # Daily distribution
                if audit.creation_timestamp:
                    day_key = audit.creation_timestamp.date().isoformat()
                    daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
                    
                    # Hourly distribution
                    hour = audit.creation_timestamp.hour
                    hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
                
                # Success metrics
                if audit.client_notified and audit.workflow_initiated:
                    report['success_metrics']['successful_applications'] += 1
                
                if not audit.client_notified:
                    report['success_metrics']['failed_notifications'] += 1
                
                if not audit.workflow_initiated:
                    report['success_metrics']['failed_workflows'] += 1
                
                # Client interactions
                if audit.client_id:
                    report['client_interactions']['unique_clients'].add(audit.client_id)
                
                # Error analysis
                if audit.metadata:
                    event_type = audit.metadata.get('event_type')
                    if event_type == 'validation_failed':
                        report['success_metrics']['validation_errors'] += 1
                    elif event_type == 'error_occurred':
                        report['error_analysis'].append({
                            'timestamp': audit.creation_timestamp,
                            'error_type': audit.metadata.get('event_data', {}).get('error_type'),
                            'error_message': audit.metadata.get('event_data', {}).get('error_message')
                        })
            
            # Performance calculations
            report['applications_by_day'] = daily_counts
            report['client_interactions']['unique_clients'] = len(report['client_interactions']['unique_clients'])
            
            if days_back > 0:
                report['performance_metrics']['avg_applications_per_day'] = len(audits) / days_back
            
            if hourly_counts:
                peak_hour = max(hourly_counts.items(), key=lambda x: x[1])
                report['performance_metrics']['peak_activity_hour'] = peak_hour[0]
            
            if daily_counts:
                most_active_day = max(daily_counts.items(), key=lambda x: x[1])
                report['performance_metrics']['most_active_day'] = most_active_day[0]
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating creator activity report: {e}")
            return {}
    
    async def get_system_audit_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get system-wide audit summary.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict containing system audit summary
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            result = await self.get_audit_trail(
                start_date=start_date,
                limit=10000  # Large limit to get all recent records
            )
            
            audits = result.audits
            
            summary = {
                'period_days': days_back,
                'total_applications': len(audits),
                'system_health': {
                    'success_rate': 0,
                    'error_rate': 0,
                    'notification_success_rate': 0,
                    'workflow_success_rate': 0
                },
                'role_performance': {},
                'application_type_distribution': {},
                'peak_usage_times': {},
                'alerts': [],
                'trends': {
                    'daily_application_counts': {},
                    'growth_rate': 0
                }
            }
            
            if not audits:
                return summary
            
            # System health metrics
            successful_apps = sum(1 for audit in audits if audit.client_notified and audit.workflow_initiated)
            error_apps = sum(1 for audit in audits if audit.metadata and audit.metadata.get('event_type') == 'error_occurred')
            notified_apps = sum(1 for audit in audits if audit.client_notified)
            workflow_apps = sum(1 for audit in audits if audit.workflow_initiated)
            
            total = len(audits)
            summary['system_health']['success_rate'] = (successful_apps / total * 100) if total > 0 else 0
            summary['system_health']['error_rate'] = (error_apps / total * 100) if total > 0 else 0
            summary['system_health']['notification_success_rate'] = (notified_apps / total * 100) if total > 0 else 0
            summary['system_health']['workflow_success_rate'] = (workflow_apps / total * 100) if total > 0 else 0
            
            # Role performance analysis
            role_stats = {}
            for audit in audits:
                role = audit.creator_role or 'unknown'
                if role not in role_stats:
                    role_stats[role] = {'total': 0, 'successful': 0, 'errors': 0}
                
                role_stats[role]['total'] += 1
                
                if audit.client_notified and audit.workflow_initiated:
                    role_stats[role]['successful'] += 1
                
                if audit.metadata and audit.metadata.get('event_type') == 'error_occurred':
                    role_stats[role]['errors'] += 1
            
            # Calculate success rates for each role
            for role, stats in role_stats.items():
                stats['success_rate'] = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                stats['error_rate'] = (stats['errors'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            summary['role_performance'] = role_stats
            
            # Application type distribution
            type_counts = {}
            for audit in audits:
                app_type = audit.application_type or 'unknown'
                type_counts[app_type] = type_counts.get(app_type, 0) + 1
            
            summary['application_type_distribution'] = type_counts
            
            # Peak usage analysis
            hourly_usage = {}
            daily_usage = {}
            
            for audit in audits:
                if audit.creation_timestamp:
                    hour = audit.creation_timestamp.hour
                    hourly_usage[hour] = hourly_usage.get(hour, 0) + 1
                    
                    day = audit.creation_timestamp.date().isoformat()
                    daily_usage[day] = daily_usage.get(day, 0) + 1
            
            summary['peak_usage_times'] = {
                'hourly': hourly_usage,
                'daily': daily_usage
            }
            
            summary['trends']['daily_application_counts'] = daily_usage
            
            # Generate alerts for unusual patterns
            alerts = []
            
            # High error rate alert
            if summary['system_health']['error_rate'] > 10:
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'warning',
                    'message': f"Error rate is {summary['system_health']['error_rate']:.1f}%, above normal threshold"
                })
            
            # Low success rate alert
            if summary['system_health']['success_rate'] < 80:
                alerts.append({
                    'type': 'low_success_rate',
                    'severity': 'critical',
                    'message': f"Success rate is {summary['system_health']['success_rate']:.1f}%, below acceptable threshold"
                })
            
            # Role-specific alerts
            for role, stats in role_stats.items():
                if stats['error_rate'] > 15:
                    alerts.append({
                        'type': 'role_high_errors',
                        'severity': 'warning',
                        'message': f"Role {role} has high error rate: {stats['error_rate']:.1f}%"
                    })
            
            summary['alerts'] = alerts
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating system audit summary: {e}")
            return {}
    
    async def export_audit_data(self,
                              filters: List[AuditFilter] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              format_type: str = "json") -> Dict[str, Any]:
        """
        Export audit data in specified format.
        
        Args:
            filters: List of filters to apply
            start_date: Start date for filtering
            end_date: End date for filtering
            format_type: Export format (json, csv)
            
        Returns:
            Dict containing export data and metadata
        """
        try:
            result = await self.get_audit_trail(
                filters=filters,
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Large limit for export
            )
            
            export_data = {
                'metadata': {
                    'export_timestamp': datetime.utcnow().isoformat(),
                    'total_records': result.total_count,
                    'exported_records': len(result.audits),
                    'format': format_type,
                    'filters_applied': len(filters) if filters else 0
                },
                'summary': result.summary,
                'data': []
            }
            
            if format_type == "json":
                export_data['data'] = [audit.to_dict() for audit in result.audits]
            elif format_type == "csv":
                # Convert to CSV-friendly format
                csv_data = []
                for audit in result.audits:
                    csv_row = {
                        'id': audit.id,
                        'application_id': audit.application_id,
                        'creator_id': audit.creator_id,
                        'creator_role': audit.creator_role,
                        'client_id': audit.client_id,
                        'application_type': audit.application_type,
                        'creation_timestamp': audit.creation_timestamp.isoformat() if audit.creation_timestamp else None,
                        'client_notified': audit.client_notified,
                        'workflow_initiated': audit.workflow_initiated,
                        'event_type': audit.metadata.get('event_type') if audit.metadata else None,
                        'ip_address': audit.ip_address,
                        'session_id': audit.session_id
                    }
                    csv_data.append(csv_row)
                export_data['data'] = csv_data
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error exporting audit data: {e}")
            return {'metadata': {}, 'summary': {}, 'data': []}

# Global audit viewer instance
audit_viewer = StaffApplicationAuditViewer()

# Convenience functions for common audit viewing operations
async def get_recent_staff_applications(days: int = 7, limit: int = 50) -> List[StaffApplicationAudit]:
    """Get recent staff-created applications"""
    start_date = datetime.utcnow() - timedelta(days=days)
    result = await audit_viewer.get_audit_trail(start_date=start_date, limit=limit)
    return result.audits

async def get_creator_applications(creator_id: int, days: int = 30) -> List[StaffApplicationAudit]:
    """Get applications created by specific staff member"""
    filters = [AuditFilter(AuditFilterType.BY_CREATOR.value, creator_id)]
    start_date = datetime.utcnow() - timedelta(days=days)
    result = await audit_viewer.get_audit_trail(filters=filters, start_date=start_date, limit=200)
    return result.audits

async def get_failed_applications(days: int = 7) -> List[StaffApplicationAudit]:
    """Get applications that failed notification or workflow initiation"""
    filters = [AuditFilter(AuditFilterType.BY_SUCCESS_STATUS.value, False)]
    start_date = datetime.utcnow() - timedelta(days=days)
    result = await audit_viewer.get_audit_trail(filters=filters, start_date=start_date, limit=100)
    return result.audits

async def get_role_performance_summary(role: str, days: int = 30) -> Dict[str, Any]:
    """Get performance summary for specific role"""
    filters = [AuditFilter(AuditFilterType.BY_ROLE.value, role)]
    start_date = datetime.utcnow() - timedelta(days=days)
    result = await audit_viewer.get_audit_trail(filters=filters, start_date=start_date, limit=500)
    return result.summary