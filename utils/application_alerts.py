"""
Alert system for unusual application creation activities.
Implements Requirements 6.4 from multi-role application creation spec.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json

from utils.application_tracker import application_tracker, TrackingAlert, AlertType
from utils.audit_analyzer import StaffApplicationAuditAnalyzer, AnalysisAlert
from database.queries import db_manager
from utils.logger import setup_module_logger

logger = setup_module_logger("application_alerts")

class AlertChannel(Enum):
    """Alert delivery channels"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    DATABASE = "database"
    LOG = "log"
    WEBHOOK = "webhook"

class AlertFrequency(Enum):
    """Alert check frequencies"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"

@dataclass
class AlertRule:
    """Configuration for an alert rule"""
    rule_id: str
    name: str
    description: str
    alert_type: str
    threshold_config: Dict[str, Any]
    frequency: str
    channels: List[str]
    recipients: List[int]  # User IDs to notify
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AlertNotification:
    """Alert notification to be sent"""
    alert_id: str
    rule_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    data: Dict[str, Any]
    channels: List[str]
    recipients: List[int]
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivery_status: Dict[str, str] = None
    
    def __post_init__(self):
        if self.delivery_status is None:
            self.delivery_status = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'rule_id': self.rule_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'channels': self.channels,
            'recipients': self.recipients,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivery_status': self.delivery_status
        }

class ApplicationAlertSystem:
    """Main alert system for application creation monitoring"""
    
    def __init__(self):
        self.logger = logger
        self.analyzer = StaffApplicationAuditAnalyzer()
        self._alert_rules = {}
        self._alert_history = []
        self._notification_queue = asyncio.Queue()
        self._processing_task = None
        self._is_running = False
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                rule_id="high_staff_creation_rate",
                name="High Staff Creation Rate",
                description="Alert when staff creation rate exceeds normal levels",
                alert_type=AlertType.HIGH_STAFF_CREATION_RATE.value,
                threshold_config={
                    "staff_percentage_threshold": 70,
                    "baseline_comparison": True,
                    "minimum_applications": 10
                },
                frequency=AlertFrequency.HOURLY.value,
                channels=[AlertChannel.TELEGRAM.value, AlertChannel.DATABASE.value],
                recipients=[],  # Will be populated with admin user IDs
                created_at=datetime.utcnow()
            ),
            AlertRule(
                rule_id="low_client_creation_rate",
                name="Low Client Self-Service Rate",
                description="Alert when client self-service rate drops significantly",
                alert_type=AlertType.LOW_CLIENT_CREATION_RATE.value,
                threshold_config={
                    "client_percentage_threshold": 30,
                    "baseline_comparison": True,
                    "drop_percentage": 20
                },
                frequency=AlertFrequency.HOURLY.value,
                channels=[AlertChannel.TELEGRAM.value, AlertChannel.DATABASE.value],
                recipients=[],
                created_at=datetime.utcnow()
            ),
            AlertRule(
                rule_id="success_rate_drop",
                name="Success Rate Drop",
                description="Alert when application success rate drops below acceptable levels",
                alert_type=AlertType.SUCCESS_RATE_DROP.value,
                threshold_config={
                    "success_rate_threshold": 80,
                    "drop_percentage": 15,
                    "baseline_comparison": True
                },
                frequency=AlertFrequency.HOURLY.value,
                channels=[AlertChannel.TELEGRAM.value, AlertChannel.DATABASE.value],
                recipients=[],
                created_at=datetime.utcnow()
            ),
            AlertRule(
                rule_id="error_spike",
                name="Error Rate Spike",
                description="Alert when error rate spikes above normal levels",
                alert_type=AlertType.ERROR_SPIKE.value,
                threshold_config={
                    "error_rate_threshold": 10,
                    "spike_percentage": 5,
                    "baseline_comparison": True
                },
                frequency=AlertFrequency.HOURLY.value,
                channels=[AlertChannel.TELEGRAM.value, AlertChannel.DATABASE.value],
                recipients=[],
                created_at=datetime.utcnow()
            ),
            AlertRule(
                rule_id="unusual_role_activity",
                name="Unusual Role Activity",
                description="Alert when specific roles show unusual activity patterns",
                alert_type=AlertType.UNUSUAL_ROLE_ACTIVITY.value,
                threshold_config={
                    "activity_multiplier": 3,
                    "minimum_baseline": 1,
                    "roles_to_monitor": ["manager", "junior_manager", "controller", "call_center"]
                },
                frequency=AlertFrequency.DAILY.value,
                channels=[AlertChannel.TELEGRAM.value, AlertChannel.DATABASE.value],
                recipients=[],
                created_at=datetime.utcnow()
            )
        ]
        
        for rule in default_rules:
            self._alert_rules[rule.rule_id] = rule
    
    async def start_monitoring(self):
        """Start the alert monitoring system"""
        if self._is_running:
            return
        
        self._is_running = True
        self.logger.info("Starting application alert monitoring system")
        
        # Start notification processing task
        self._processing_task = asyncio.create_task(self._process_notifications())
        
        # Start periodic alert checks
        asyncio.create_task(self._run_periodic_checks())
    
    async def stop_monitoring(self):
        """Stop the alert monitoring system"""
        self._is_running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped application alert monitoring system")
    
    async def _run_periodic_checks(self):
        """Run periodic alert checks based on configured frequencies"""
        last_hourly_check = datetime.utcnow()
        last_daily_check = datetime.utcnow()
        last_weekly_check = datetime.utcnow()
        
        while self._is_running:
            try:
                now = datetime.utcnow()
                
                # Hourly checks
                if (now - last_hourly_check).total_seconds() >= 3600:  # 1 hour
                    await self._run_frequency_checks(AlertFrequency.HOURLY.value)
                    last_hourly_check = now
                
                # Daily checks
                if (now - last_daily_check).total_seconds() >= 86400:  # 24 hours
                    await self._run_frequency_checks(AlertFrequency.DAILY.value)
                    last_daily_check = now
                
                # Weekly checks
                if (now - last_weekly_check).total_seconds() >= 604800:  # 7 days
                    await self._run_frequency_checks(AlertFrequency.WEEKLY.value)
                    last_weekly_check = now
                
                # Sleep for 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in periodic alert checks: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _run_frequency_checks(self, frequency: str):
        """Run alert checks for a specific frequency"""
        try:
            rules_to_check = [rule for rule in self._alert_rules.values() 
                            if rule.frequency == frequency and rule.is_active]
            
            for rule in rules_to_check:
                try:
                    await self._check_alert_rule(rule)
                except Exception as e:
                    self.logger.error(f"Error checking alert rule {rule.rule_id}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error running frequency checks for {frequency}: {e}")
    
    async def _check_alert_rule(self, rule: AlertRule):
        """Check a specific alert rule and trigger if conditions are met"""
        try:
            # Get appropriate time window based on frequency
            if rule.frequency == AlertFrequency.HOURLY.value:
                days_back = 1
            elif rule.frequency == AlertFrequency.DAILY.value:
                days_back = 7
            elif rule.frequency == AlertFrequency.WEEKLY.value:
                days_back = 30
            else:
                days_back = 1
            
            # Check if rule should be triggered
            should_trigger, alert_data = await self._evaluate_alert_condition(rule, days_back)
            
            if should_trigger:
                # Create and queue alert notification
                notification = await self._create_alert_notification(rule, alert_data)
                await self._notification_queue.put(notification)
                
                # Update rule statistics
                rule.last_triggered = datetime.utcnow()
                rule.trigger_count += 1
                
                self.logger.info(f"Alert rule {rule.rule_id} triggered")
            
        except Exception as e:
            self.logger.error(f"Error checking alert rule {rule.rule_id}: {e}")
    
    async def _evaluate_alert_condition(self, rule: AlertRule, days_back: int) -> tuple[bool, Dict[str, Any]]:
        """Evaluate if an alert condition is met"""
        try:
            config = rule.threshold_config
            
            if rule.alert_type == AlertType.HIGH_STAFF_CREATION_RATE.value:
                return await self._check_high_staff_creation_rate(config, days_back)
            
            elif rule.alert_type == AlertType.LOW_CLIENT_CREATION_RATE.value:
                return await self._check_low_client_creation_rate(config, days_back)
            
            elif rule.alert_type == AlertType.SUCCESS_RATE_DROP.value:
                return await self._check_success_rate_drop(config, days_back)
            
            elif rule.alert_type == AlertType.ERROR_SPIKE.value:
                return await self._check_error_spike(config, days_back)
            
            elif rule.alert_type == AlertType.UNUSUAL_ROLE_ACTIVITY.value:
                return await self._check_unusual_role_activity(config, days_back)
            
            return False, {}
            
        except Exception as e:
            self.logger.error(f"Error evaluating alert condition for {rule.rule_id}: {e}")
            return False, {}
    
    async def _check_high_staff_creation_rate(self, config: Dict[str, Any], days_back: int) -> tuple[bool, Dict[str, Any]]:
        """Check for high staff creation rate"""
        current_stats = await application_tracker.get_application_statistics(days_back)
        
        # Check minimum applications threshold
        if current_stats.total_applications < config.get("minimum_applications", 10):
            return False, {}
        
        # Check staff percentage threshold
        threshold = config.get("staff_percentage_threshold", 70)
        if current_stats.staff_creation_percentage <= threshold:
            return False, {}
        
        # If baseline comparison is enabled, check against historical data
        if config.get("baseline_comparison", False):
            baseline_stats = await application_tracker.get_application_statistics(days_back * 2)
            if baseline_stats.staff_creation_percentage >= threshold:
                return False, {}  # This is normal for this system
        
        return True, {
            "current_staff_percentage": current_stats.staff_creation_percentage,
            "threshold": threshold,
            "total_applications": current_stats.total_applications,
            "staff_created": current_stats.staff_created
        }
    
    async def _check_low_client_creation_rate(self, config: Dict[str, Any], days_back: int) -> tuple[bool, Dict[str, Any]]:
        """Check for low client creation rate"""
        current_stats = await application_tracker.get_application_statistics(days_back)
        
        if current_stats.total_applications == 0:
            return False, {}
        
        client_percentage = (current_stats.client_created / current_stats.total_applications * 100)
        threshold = config.get("client_percentage_threshold", 30)
        
        if client_percentage >= threshold:
            return False, {}
        
        # Check against baseline if enabled
        if config.get("baseline_comparison", False):
            baseline_stats = await application_tracker.get_application_statistics(days_back * 2)
            if baseline_stats.total_applications > 0:
                baseline_client_percentage = (baseline_stats.client_created / baseline_stats.total_applications * 100)
                drop_threshold = config.get("drop_percentage", 20)
                
                if baseline_client_percentage - client_percentage < drop_threshold:
                    return False, {}  # Drop is not significant enough
        
        return True, {
            "current_client_percentage": client_percentage,
            "threshold": threshold,
            "total_applications": current_stats.total_applications,
            "client_created": current_stats.client_created
        }
    
    async def _check_success_rate_drop(self, config: Dict[str, Any], days_back: int) -> tuple[bool, Dict[str, Any]]:
        """Check for success rate drop"""
        current_stats = await application_tracker.get_application_statistics(days_back)
        threshold = config.get("success_rate_threshold", 80)
        
        if current_stats.success_rate >= threshold:
            return False, {}
        
        # Check against baseline if enabled
        if config.get("baseline_comparison", False):
            baseline_stats = await application_tracker.get_application_statistics(days_back * 2)
            drop_threshold = config.get("drop_percentage", 15)
            
            if baseline_stats.success_rate - current_stats.success_rate < drop_threshold:
                return False, {}  # Drop is not significant enough
        
        return True, {
            "current_success_rate": current_stats.success_rate,
            "threshold": threshold,
            "total_applications": current_stats.total_applications
        }
    
    async def _check_error_spike(self, config: Dict[str, Any], days_back: int) -> tuple[bool, Dict[str, Any]]:
        """Check for error rate spike"""
        current_stats = await application_tracker.get_application_statistics(days_back)
        threshold = config.get("error_rate_threshold", 10)
        
        if current_stats.error_rate <= threshold:
            return False, {}
        
        # Check against baseline if enabled
        if config.get("baseline_comparison", False):
            baseline_stats = await application_tracker.get_application_statistics(days_back * 2)
            spike_threshold = config.get("spike_percentage", 5)
            
            if current_stats.error_rate - baseline_stats.error_rate < spike_threshold:
                return False, {}  # Spike is not significant enough
        
        return True, {
            "current_error_rate": current_stats.error_rate,
            "threshold": threshold,
            "total_applications": current_stats.total_applications
        }
    
    async def _check_unusual_role_activity(self, config: Dict[str, Any], days_back: int) -> tuple[bool, Dict[str, Any]]:
        """Check for unusual role activity"""
        current_role_stats = await application_tracker.get_role_statistics(days_back)
        baseline_role_stats = await application_tracker.get_role_statistics(days_back * 2)
        
        roles_to_monitor = config.get("roles_to_monitor", ["manager", "junior_manager", "controller", "call_center"])
        activity_multiplier = config.get("activity_multiplier", 3)
        minimum_baseline = config.get("minimum_baseline", 1)
        
        unusual_roles = []
        
        for role in roles_to_monitor:
            if role in current_role_stats and role in baseline_role_stats:
                current_activity = current_role_stats[role].average_per_day
                baseline_activity = baseline_role_stats[role].average_per_day
                
                if (baseline_activity >= minimum_baseline and 
                    current_activity > baseline_activity * activity_multiplier):
                    unusual_roles.append({
                        "role": role,
                        "current_activity": current_activity,
                        "baseline_activity": baseline_activity,
                        "multiplier": current_activity / baseline_activity if baseline_activity > 0 else 0
                    })
        
        if unusual_roles:
            return True, {"unusual_roles": unusual_roles}
        
        return False, {}
    
    async def _create_alert_notification(self, rule: AlertRule, alert_data: Dict[str, Any]) -> AlertNotification:
        """Create an alert notification"""
        alert_id = f"{rule.rule_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate title and message based on alert type
        title, message = self._generate_alert_content(rule, alert_data)
        
        # Determine severity
        severity = self._determine_alert_severity(rule.alert_type, alert_data)
        
        return AlertNotification(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            alert_type=rule.alert_type,
            severity=severity,
            title=title,
            message=message,
            data=alert_data,
            channels=rule.channels,
            recipients=rule.recipients,
            created_at=datetime.utcnow()
        )
    
    def _generate_alert_content(self, rule: AlertRule, alert_data: Dict[str, Any]) -> tuple[str, str]:
        """Generate alert title and message"""
        if rule.alert_type == AlertType.HIGH_STAFF_CREATION_RATE.value:
            title = "High Staff Application Creation Rate"
            message = f"Staff are creating {alert_data.get('current_staff_percentage', 0):.1f}% of applications, above threshold of {alert_data.get('threshold', 0)}%"
        
        elif rule.alert_type == AlertType.LOW_CLIENT_CREATION_RATE.value:
            title = "Low Client Self-Service Rate"
            message = f"Client self-service rate dropped to {alert_data.get('current_client_percentage', 0):.1f}%, below threshold of {alert_data.get('threshold', 0)}%"
        
        elif rule.alert_type == AlertType.SUCCESS_RATE_DROP.value:
            title = "Application Success Rate Drop"
            message = f"Success rate dropped to {alert_data.get('current_success_rate', 0):.1f}%, below threshold of {alert_data.get('threshold', 0)}%"
        
        elif rule.alert_type == AlertType.ERROR_SPIKE.value:
            title = "Application Error Rate Spike"
            message = f"Error rate spiked to {alert_data.get('current_error_rate', 0):.1f}%, above threshold of {alert_data.get('threshold', 0)}%"
        
        elif rule.alert_type == AlertType.UNUSUAL_ROLE_ACTIVITY.value:
            unusual_roles = alert_data.get('unusual_roles', [])
            role_names = [role['role'] for role in unusual_roles]
            title = "Unusual Role Activity Detected"
            message = f"Unusual activity detected for roles: {', '.join(role_names)}"
        
        else:
            title = rule.name
            message = rule.description
        
        return title, message
    
    def _determine_alert_severity(self, alert_type: str, alert_data: Dict[str, Any]) -> str:
        """Determine alert severity based on type and data"""
        if alert_type in [AlertType.LOW_CLIENT_CREATION_RATE.value, AlertType.SUCCESS_RATE_DROP.value]:
            return "critical"
        elif alert_type == AlertType.ERROR_SPIKE.value:
            error_rate = alert_data.get('current_error_rate', 0)
            return "critical" if error_rate > 20 else "warning"
        elif alert_type == AlertType.HIGH_STAFF_CREATION_RATE.value:
            return "warning"
        elif alert_type == AlertType.UNUSUAL_ROLE_ACTIVITY.value:
            return "info"
        else:
            return "warning"
    
    async def _process_notifications(self):
        """Process alert notifications from the queue"""
        while self._is_running:
            try:
                # Wait for notification with timeout
                try:
                    notification = await asyncio.wait_for(
                        self._notification_queue.get(), 
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Send notification through configured channels
                await self._send_notification(notification)
                
                # Mark task as done
                self._notification_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error processing notification: {e}")
                await asyncio.sleep(1)
    
    async def _send_notification(self, notification: AlertNotification):
        """Send notification through configured channels"""
        try:
            notification.sent_at = datetime.utcnow()
            
            for channel in notification.channels:
                try:
                    if channel == AlertChannel.TELEGRAM.value:
                        await self._send_telegram_notification(notification)
                    elif channel == AlertChannel.DATABASE.value:
                        await self._store_notification_in_database(notification)
                    elif channel == AlertChannel.LOG.value:
                        await self._log_notification(notification)
                    # Add other channels as needed
                    
                    notification.delivery_status[channel] = "sent"
                    
                except Exception as e:
                    self.logger.error(f"Error sending notification via {channel}: {e}")
                    notification.delivery_status[channel] = f"failed: {str(e)}"
            
            # Store notification in history
            self._alert_history.append(notification)
            
            # Keep only last 1000 notifications in memory
            if len(self._alert_history) > 1000:
                self._alert_history = self._alert_history[-1000:]
            
        except Exception as e:
            self.logger.error(f"Error sending notification {notification.alert_id}: {e}")
    
    async def _send_telegram_notification(self, notification: AlertNotification):
        """Send notification via Telegram"""
        try:
            # Get admin users to notify
            admin_users = await self._get_admin_users()
            
            message = f"🚨 *{notification.title}*\n\n{notification.message}\n\n_Alert ID: {notification.alert_id}_"
            
            # For now, just log the notification - can be extended to use actual Telegram API
            self.logger.info(f"Telegram notification would be sent to {len(admin_users)} admin users: {message}")
            
            # TODO: Integrate with actual notification system when available
            # for admin_user in admin_users:
            #     try:
            #         await notification_system.send_notification(
            #             user_id=admin_user['id'],
            #             title=notification.title,
            #             message=notification.message,
            #             notification_type="alert",
            #             related_id=notification.alert_id,
            #             related_type="application_alert"
            #         )
            #     except Exception as e:
            #         self.logger.error(f"Error sending Telegram notification to user {admin_user['id']}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in Telegram notification: {e}")
    
    async def _store_notification_in_database(self, notification: AlertNotification):
        """Store notification in database"""
        try:
            query = """
            INSERT INTO application_alerts (
                alert_id, rule_id, alert_type, severity, title, message, 
                data, channels, recipients, created_at, sent_at, delivery_status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """
            
            await db_manager.execute(
                query,
                notification.alert_id,
                notification.rule_id,
                notification.alert_type,
                notification.severity,
                notification.title,
                notification.message,
                json.dumps(notification.data),
                json.dumps(notification.channels),
                json.dumps(notification.recipients),
                notification.created_at,
                notification.sent_at,
                json.dumps(notification.delivery_status)
            )
            
        except Exception as e:
            self.logger.error(f"Error storing notification in database: {e}")
    
    async def _log_notification(self, notification: AlertNotification):
        """Log notification"""
        self.logger.warning(f"ALERT: {notification.title} - {notification.message} (ID: {notification.alert_id})")
    
    async def _get_admin_users(self) -> List[Dict[str, Any]]:
        """Get list of admin users for notifications"""
        try:
            query = "SELECT id, telegram_id FROM users WHERE role = 'admin' AND is_active = true"
            results = await db_manager.fetch(query)
            return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting admin users: {e}")
            return []
    
    # Public API methods
    
    async def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule"""
        try:
            self._alert_rules[rule.rule_id] = rule
            self.logger.info(f"Added alert rule: {rule.rule_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding alert rule: {e}")
            return False
    
    async def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert rule"""
        try:
            if rule_id not in self._alert_rules:
                return False
            
            rule = self._alert_rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            self.logger.info(f"Updated alert rule: {rule_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating alert rule: {e}")
            return False
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        try:
            if rule_id in self._alert_rules:
                del self._alert_rules[rule_id]
                self.logger.info(f"Deleted alert rule: {rule_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting alert rule: {e}")
            return False
    
    async def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules"""
        return list(self._alert_rules.values())
    
    async def get_alert_history(self, limit: int = 100) -> List[AlertNotification]:
        """Get alert history"""
        return self._alert_history[-limit:]
    
    async def trigger_manual_check(self, rule_id: Optional[str] = None) -> Dict[str, Any]:
        """Manually trigger alert checks"""
        try:
            if rule_id:
                if rule_id in self._alert_rules:
                    rule = self._alert_rules[rule_id]
                    await self._check_alert_rule(rule)
                    return {"status": "success", "message": f"Checked rule {rule_id}"}
                else:
                    return {"status": "error", "message": f"Rule {rule_id} not found"}
            else:
                # Check all active rules
                for rule in self._alert_rules.values():
                    if rule.is_active:
                        await self._check_alert_rule(rule)
                return {"status": "success", "message": "Checked all active rules"}
        except Exception as e:
            self.logger.error(f"Error in manual check: {e}")
            return {"status": "error", "message": str(e)}

# Global alert system instance
alert_system = ApplicationAlertSystem()

# Convenience functions for alert management
async def start_alert_monitoring():
    """Start the alert monitoring system"""
    await alert_system.start_monitoring()

async def stop_alert_monitoring():
    """Stop the alert monitoring system"""
    await alert_system.stop_monitoring()

async def add_custom_alert_rule(rule_config: Dict[str, Any]) -> bool:
    """Add a custom alert rule"""
    rule = AlertRule(**rule_config)
    return await alert_system.add_alert_rule(rule)

async def get_recent_alerts(hours: int = 24) -> List[AlertNotification]:
    """Get recent alerts within specified hours"""
    all_alerts = await alert_system.get_alert_history(1000)
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    return [alert for alert in all_alerts if alert.created_at >= cutoff_time]

async def check_system_health() -> Dict[str, Any]:
    """Check overall system health based on recent alerts"""
    recent_alerts = await get_recent_alerts(24)
    critical_alerts = [alert for alert in recent_alerts if alert.severity == "critical"]
    warning_alerts = [alert for alert in recent_alerts if alert.severity == "warning"]
    
    if critical_alerts:
        health_status = "critical"
    elif warning_alerts:
        health_status = "warning"
    else:
        health_status = "healthy"
    
    return {
        "health_status": health_status,
        "total_alerts_24h": len(recent_alerts),
        "critical_alerts_24h": len(critical_alerts),
        "warning_alerts_24h": len(warning_alerts),
        "last_alert": recent_alerts[-1].created_at.isoformat() if recent_alerts else None
    }