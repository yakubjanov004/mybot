"""
Demonstration of the application tracking and reporting system.
Shows how to use the tracking, reporting, and alert systems.
"""

import asyncio
from datetime import datetime, timedelta
from utils.application_tracker import (
    application_tracker, ApplicationSource, get_staff_vs_client_stats,
    get_role_performance_report, check_for_unusual_activity
)
from utils.admin_reporting import (
    admin_reporting, ReportRequest, ReportFormat, ReportPeriod,
    get_admin_dashboard, generate_weekly_performance_report
)
from utils.application_alerts import (
    alert_system, AlertRule, AlertFrequency, AlertChannel, AlertType
)

async def demo_application_statistics():
    """Demonstrate application statistics functionality"""
    print("=== Application Statistics Demo ===")
    
    try:
        # Get overall statistics
        overall_stats = await application_tracker.get_application_statistics(30)
        print(f"Overall Statistics (30 days):")
        print(f"  Total Applications: {overall_stats.total_applications}")
        print(f"  Client Created: {overall_stats.client_created}")
        print(f"  Staff Created: {overall_stats.staff_created}")
        print(f"  Staff Creation %: {overall_stats.staff_creation_percentage:.1f}%")
        print(f"  Success Rate: {overall_stats.success_rate:.1f}%")
        print(f"  Error Rate: {overall_stats.error_rate:.1f}%")
        print(f"  Average per Day: {overall_stats.average_per_day:.1f}")
        print(f"  Peak Hours: {overall_stats.peak_hours}")
        
        # Get staff vs client comparison
        comparison_stats = await get_staff_vs_client_stats(30)
        print(f"\nStaff vs Client Comparison:")
        print(f"  Client Stats: {comparison_stats['client'].total_applications} applications")
        print(f"  Staff Stats: {comparison_stats['staff'].total_applications} applications")
        
    except Exception as e:
        print(f"Error in statistics demo: {e}")

async def demo_role_performance():
    """Demonstrate role performance reporting"""
    print("\n=== Role Performance Demo ===")
    
    try:
        role_stats = await get_role_performance_report(30)
        
        if role_stats:
            print("Role Performance (30 days):")
            for role, stats in role_stats.items():
                print(f"  {role.title()}:")
                print(f"    Total Applications: {stats.total_applications}")
                print(f"    Success Rate: {stats.success_rate:.1f}%")
                print(f"    Error Rate: {stats.error_rate:.1f}%")
                print(f"    Notification Success: {stats.notification_success_rate:.1f}%")
                print(f"    Workflow Success: {stats.workflow_success_rate:.1f}%")
                print(f"    Average per Day: {stats.average_per_day:.1f}")
                print(f"    Most Active Hours: {stats.most_active_hours}")
        else:
            print("No role performance data available")
            
    except Exception as e:
        print(f"Error in role performance demo: {e}")

async def demo_comparison_report():
    """Demonstrate comparison report generation"""
    print("\n=== Comparison Report Demo ===")
    
    try:
        comparison_report = await application_tracker.generate_comparison_report(30)
        
        print(f"Comparison Report ({comparison_report.period_days} days):")
        print(f"  Client Applications: {comparison_report.client_stats.total_applications}")
        print(f"  Staff Applications: {comparison_report.staff_stats.total_applications}")
        
        print(f"\nKey Insights:")
        for insight in comparison_report.insights[:3]:  # Show top 3 insights
            print(f"  - {insight}")
        
        print(f"\nRecommendations:")
        for recommendation in comparison_report.recommendations[:3]:  # Show top 3 recommendations
            print(f"  - {recommendation}")
            
    except Exception as e:
        print(f"Error in comparison report demo: {e}")

async def demo_trend_analysis():
    """Demonstrate trend analysis"""
    print("\n=== Trend Analysis Demo ===")
    
    try:
        trend_report = await application_tracker.generate_trend_report(30, "daily")
        
        print(f"Trend Analysis ({trend_report['period_days']} days, {trend_report['granularity']}):")
        print(f"  Data Points: {len(trend_report['data_points'])}")
        print(f"  Trends:")
        for trend_type, direction in trend_report['trends'].items():
            print(f"    {trend_type.replace('_', ' ').title()}: {direction}")
        
        print(f"  Summary:")
        summary = trend_report['summary']
        print(f"    Avg Applications per Period: {summary.get('avg_applications_per_period', 0):.1f}")
        print(f"    Avg Staff Percentage: {summary.get('avg_staff_percentage', 0):.1f}%")
        print(f"    Avg Success Rate: {summary.get('avg_success_rate', 0):.1f}%")
        
    except Exception as e:
        print(f"Error in trend analysis demo: {e}")

async def demo_alert_detection():
    """Demonstrate alert detection"""
    print("\n=== Alert Detection Demo ===")
    
    try:
        alerts = await check_for_unusual_activity(7)
        
        if alerts:
            print(f"Detected {len(alerts)} unusual patterns:")
            for alert in alerts:
                print(f"  Alert: {alert.title}")
                print(f"    Type: {alert.alert_type}")
                print(f"    Severity: {alert.severity}")
                print(f"    Description: {alert.description}")
                print(f"    Recommendations: {len(alert.recommendations)} items")
        else:
            print("No unusual patterns detected - system is operating normally")
            
    except Exception as e:
        print(f"Error in alert detection demo: {e}")

async def demo_admin_dashboard():
    """Demonstrate admin dashboard"""
    print("\n=== Admin Dashboard Demo ===")
    
    try:
        dashboard = await get_admin_dashboard()
        
        print("Admin Dashboard:")
        
        # System overview
        system_overview = dashboard.get('system_overview', {})
        print(f"  System Overview:")
        print(f"    Total Users: {system_overview.get('total_users', 0)}")
        print(f"    Total Orders: {system_overview.get('total_orders', 0)}")
        print(f"    Active Technicians: {system_overview.get('active_technicians', 0)}")
        print(f"    Pending Orders: {system_overview.get('pending_orders', 0)}")
        
        # Application metrics
        app_metrics = dashboard.get('application_metrics', {})
        if 'today' in app_metrics:
            today = app_metrics['today']
            print(f"  Today's Applications:")
            print(f"    Total: {today.get('total', 0)}")
            print(f"    Staff Created: {today.get('staff_created', 0)}")
            print(f"    Client Created: {today.get('client_created', 0)}")
            print(f"    Staff %: {today.get('staff_percentage', 0):.1f}%")
            print(f"    Success Rate: {today.get('success_rate', 0):.1f}%")
        
        # Alerts
        alerts_info = dashboard.get('alerts', {})
        print(f"  Alerts:")
        print(f"    Total Alerts: {alerts_info.get('total_alerts', 0)}")
        print(f"    Critical Alerts: {alerts_info.get('critical_alerts', 0)}")
        
    except Exception as e:
        print(f"Error in admin dashboard demo: {e}")

async def demo_report_generation():
    """Demonstrate report generation"""
    print("\n=== Report Generation Demo ===")
    
    try:
        # Generate a weekly performance report
        report = await generate_weekly_performance_report()
        
        print(f"Generated Report:")
        print(f"  Report ID: {report.report_id}")
        print(f"  Report Type: {report.report_type}")
        print(f"  Period: {report.period}")
        print(f"  Format: {report.format_type}")
        print(f"  Generated At: {report.generated_at}")
        
        # Show summary
        summary = report.summary
        print(f"  Summary:")
        for key, value in summary.items():
            if isinstance(value, (int, float)):
                if isinstance(value, float):
                    print(f"    {key.replace('_', ' ').title()}: {value:.1f}")
                else:
                    print(f"    {key.replace('_', ' ').title()}: {value}")
            else:
                print(f"    {key.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        print(f"Error in report generation demo: {e}")

async def demo_alert_system():
    """Demonstrate alert system configuration"""
    print("\n=== Alert System Demo ===")
    
    try:
        # Get current alert rules
        rules = await alert_system.get_alert_rules()
        print(f"Current Alert Rules: {len(rules)}")
        
        for rule in rules[:3]:  # Show first 3 rules
            print(f"  Rule: {rule.name}")
            print(f"    Type: {rule.alert_type}")
            print(f"    Frequency: {rule.frequency}")
            print(f"    Active: {rule.is_active}")
            print(f"    Channels: {rule.channels}")
            print(f"    Triggered: {rule.trigger_count} times")
        
        # Get alert history
        history = await alert_system.get_alert_history(10)
        print(f"\nRecent Alerts: {len(history)}")
        
        for alert in history[:3]:  # Show first 3 alerts
            print(f"  Alert: {alert.title}")
            print(f"    Type: {alert.alert_type}")
            print(f"    Severity: {alert.severity}")
            print(f"    Created: {alert.created_at}")
            print(f"    Sent: {alert.sent_at}")
        
    except Exception as e:
        print(f"Error in alert system demo: {e}")

async def demo_comprehensive_report():
    """Demonstrate comprehensive tracking report"""
    print("\n=== Comprehensive Report Demo ===")
    
    try:
        comprehensive_report = await application_tracker.generate_comprehensive_tracking_report(30)
        
        print("Comprehensive Tracking Report:")
        
        # Executive summary
        exec_summary = comprehensive_report.get('executive_summary', {})
        print(f"  Executive Summary:")
        print(f"    Total Applications: {exec_summary.get('total_applications', 0)}")
        print(f"    Staff Creation %: {exec_summary.get('staff_creation_percentage', 0):.1f}%")
        print(f"    Overall Success Rate: {exec_summary.get('overall_success_rate', 0):.1f}%")
        print(f"    Error Rate: {exec_summary.get('error_rate', 0):.1f}%")
        print(f"    Active Roles: {exec_summary.get('active_roles', 0)}")
        print(f"    Critical Alerts: {exec_summary.get('critical_alerts', 0)}")
        
        # Key insights
        insights = comprehensive_report.get('key_insights', [])
        if insights:
            print(f"  Key Insights:")
            for insight in insights[:3]:
                print(f"    - {insight}")
        
        # Recommendations
        recommendations = comprehensive_report.get('recommendations', {})
        immediate_actions = recommendations.get('immediate_actions', [])
        if immediate_actions:
            print(f"  Immediate Actions Needed:")
            for action in immediate_actions[:3]:
                if isinstance(action, list):
                    for sub_action in action[:2]:
                        print(f"    - {sub_action}")
                else:
                    print(f"    - {action}")
        
    except Exception as e:
        print(f"Error in comprehensive report demo: {e}")

async def main():
    """Run all demonstrations"""
    print("Application Tracking and Reporting System Demo")
    print("=" * 50)
    
    # Run all demo functions
    await demo_application_statistics()
    await demo_role_performance()
    await demo_comparison_report()
    await demo_trend_analysis()
    await demo_alert_detection()
    await demo_admin_dashboard()
    await demo_report_generation()
    await demo_alert_system()
    await demo_comprehensive_report()
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nNote: This demo uses mock data since no actual database is connected.")
    print("In a real environment, the system would show actual application tracking data.")

if __name__ == "__main__":
    asyncio.run(main())