"""
Staff Application Retry Manager Integration Guide

This module provides practical examples and patterns for integrating
the retry manager into existing staff application creation workflows.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from utils.staff_application_retry_manager import (
    StaffApplicationRetryManager,
    RetryableOperation,
    RetryContext,
    RetryConfig,
    RetryStrategy,
    retryable_operation,
    get_retry_manager
)
from utils.staff_application_error_handler import StaffApplicationError, StaffApplicationErrorType


# Example 1: Simple Function Decoration
@retryable_operation("client_validation")
async def validate_client_data(client_data: Dict[str, Any]) -> bool:
    """Validate client data with automatic retry on transient failures"""
    # Your validation logic here
    if not client_data.get('phone'):
        raise StaffApplicationError(
            StaffApplicationErrorType.CLIENT_VALIDATION,
            "Phone number is required",
            {"field": "phone"}
        )
    return True


# Example 2: Custom Retryable Operation Class
class DatabaseApplicationCreation(RetryableOperation):
    """Retryable database operation for application creation"""
    
    def __init__(self, staff_id: int, client_id: int, app_data: Dict[str, Any]):
        self.staff_id = staff_id
        self.client_id = client_id
        self.app_data = app_data
        self.operation_id = f"db_app_create_{staff_id}_{client_id}_{datetime.now().timestamp()}"
    
    async def execute(self, context: RetryContext) -> Dict[str, Any]:
        """Execute database application creation"""
        # Add context for monitoring
        context.user_id = self.staff_id
        context.metadata.update({
            "client_id": self.client_id,
            "application_type": self.app_data.get("type"),
            "database_operation": "create_application"
        })
        
        # Simulate database operation
        try:
            # Your actual database logic here
            application_id = await self._create_in_database()
            return {
                "application_id": application_id,
                "status": "created",
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            # Convert to appropriate StaffApplicationError
            raise StaffApplicationError(
                StaffApplicationErrorType.DATABASE_ERROR,
                f"Failed to create application in database: {str(e)}",
                {"staff_id": self.staff_id, "client_id": self.client_id}
            )
    
    async def _create_in_database(self) -> int:
        """Simulate database creation"""
        # Your actual database logic would go here
        await asyncio.sleep(0.1)  # Simulate DB operation
        return 12345  # Return application ID
    
    def get_operation_id(self) -> str:
        return self.operation_id
    
    def get_operation_type(self) -> str:
        return "database_application_creation"


# Example 3: Integration with Existing Handler
class StaffApplicationHandler:
    """Example handler showing retry integration"""
    
    def __init__(self):
        # Configure retry manager for this handler
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay_seconds=1.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            retryable_errors=[
                StaffApplicationErrorType.DATABASE_ERROR,
                StaffApplicationErrorType.WORKFLOW_INITIALIZATION,
                StaffApplicationErrorType.NOTIFICATION_FAILURE
            ]
        )
        self.retry_manager = StaffApplicationRetryManager(retry_config=self.retry_config)
    
    async def create_application(self, staff_id: int, client_id: int, 
                               app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create application with comprehensive retry handling"""
        
        try:
            # Step 1: Validate client data (with retry)
            await validate_client_data(app_data.get("client_data", {}))
            
            # Step 2: Create application in database (with retry)
            db_operation = DatabaseApplicationCreation(staff_id, client_id, app_data)
            app_result = await self.retry_manager.execute_with_retry(db_operation)
            
            # Step 3: Send notifications (with retry)
            notification_result = await self._send_notifications_with_retry(
                app_result["application_id"], client_id
            )
            
            # Step 4: Update workflow state (with retry)
            await self._update_workflow_with_retry(app_result["application_id"], "created")
            
            return {
                "success": True,
                "application_id": app_result["application_id"],
                "notifications_sent": notification_result["sent"],
                "created_at": app_result["created_at"]
            }
            
        except StaffApplicationError as e:
            # Handle known application errors
            return {
                "success": False,
                "error_type": e.error_type.value,
                "error_message": e.message,
                "user_message": e.get_localized_user_message(),
                "error_id": e.id
            }
        except Exception as e:
            # Handle unexpected errors
            return {
                "success": False,
                "error_type": "unexpected_error",
                "error_message": str(e),
                "user_message": "Kutilmagan xatolik yuz berdi"
            }
    
    async def _send_notifications_with_retry(self, app_id: int, client_id: int) -> Dict[str, Any]:
        """Send notifications with retry logic"""
        
        class NotificationOperation(RetryableOperation):
            def __init__(self, application_id: int, client_id: int):
                self.application_id = application_id
                self.client_id = client_id
            
            async def execute(self, context: RetryContext) -> Dict[str, Any]:
                # Simulate notification sending
                await asyncio.sleep(0.05)
                return {"sent": True, "notification_id": f"notif_{self.application_id}"}
            
            def get_operation_id(self) -> str:
                return f"notification_{self.application_id}_{self.client_id}"
            
            def get_operation_type(self) -> str:
                return "client_notification"
        
        operation = NotificationOperation(app_id, client_id)
        return await self.retry_manager.execute_with_retry(operation)
    
    async def _update_workflow_with_retry(self, app_id: int, status: str):
        """Update workflow state with retry logic"""
        
        @retryable_operation("workflow_update")
        async def update_workflow_status(application_id: int, new_status: str):
            # Simulate workflow update
            await asyncio.sleep(0.02)
            return {"updated": True, "status": new_status}
        
        return await update_workflow_status(app_id, status)


# Example 4: Monitoring and Statistics Integration
class ApplicationMonitoringService:
    """Service for monitoring application creation operations"""
    
    def __init__(self):
        self.retry_manager = get_retry_manager()
    
    async def get_operation_health(self) -> Dict[str, Any]:
        """Get comprehensive health metrics"""
        stats = self.retry_manager.get_operation_statistics()
        cb_status = self.retry_manager.get_circuit_breaker_status()
        active_ops = self.retry_manager.get_active_operations()
        
        return {
            "overall_health": "healthy" if stats["success_rate"] > 0.8 else "degraded",
            "success_rate": stats["success_rate"],
            "total_operations": stats["total_operations"],
            "active_operations": len(active_ops),
            "circuit_breaker_state": cb_status["state"],
            "can_accept_requests": cb_status["can_execute"],
            "operation_types": stats["operation_types"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific operation"""
        return self.retry_manager.get_operation_status(operation_id)
    
    async def reset_circuit_breaker_if_needed(self) -> bool:
        """Reset circuit breaker if manual intervention is needed"""
        cb_status = self.retry_manager.get_circuit_breaker_status()
        
        if cb_status["state"] == "open" and not cb_status["can_execute"]:
            # Check if enough time has passed or admin intervention is needed
            self.retry_manager.reset_circuit_breaker()
            return True
        
        return False


# Example 5: Configuration Management
class RetryConfigurationManager:
    """Manage retry configurations for different environments"""
    
    @staticmethod
    def get_production_config() -> RetryConfig:
        """Production-ready retry configuration"""
        return RetryConfig(
            max_attempts=3,
            base_delay_seconds=2.0,
            max_delay_seconds=60.0,
            backoff_multiplier=2.0,
            jitter=True,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            retryable_errors=[
                StaffApplicationErrorType.DATABASE_ERROR,
                StaffApplicationErrorType.WORKFLOW_INITIALIZATION,
                StaffApplicationErrorType.NOTIFICATION_FAILURE,
                StaffApplicationErrorType.RATE_LIMIT_EXCEEDED,
                StaffApplicationErrorType.STATE_MANAGEMENT
            ],
            non_retryable_errors=[
                StaffApplicationErrorType.PERMISSION_DENIED,
                StaffApplicationErrorType.CLIENT_VALIDATION,
                StaffApplicationErrorType.APPLICATION_VALIDATION,
                StaffApplicationErrorType.SECURITY_VIOLATION,
                StaffApplicationErrorType.ROLE_VALIDATION
            ]
        )
    
    @staticmethod
    def get_development_config() -> RetryConfig:
        """Development-friendly retry configuration"""
        return RetryConfig(
            max_attempts=2,
            base_delay_seconds=0.5,
            max_delay_seconds=5.0,
            backoff_multiplier=1.5,
            jitter=False,
            strategy=RetryStrategy.LINEAR_BACKOFF
        )
    
    @staticmethod
    def get_testing_config() -> RetryConfig:
        """Testing configuration with minimal delays"""
        return RetryConfig(
            max_attempts=2,
            base_delay_seconds=0.1,
            max_delay_seconds=1.0,
            backoff_multiplier=1.2,
            jitter=False,
            strategy=RetryStrategy.FIXED_DELAY
        )


# Example Usage Patterns
async def example_usage_patterns():
    """Demonstrate various usage patterns"""
    
    # Pattern 1: Simple decorator usage
    @retryable_operation("data_validation")
    async def validate_data(data: Dict[str, Any]) -> bool:
        # Your validation logic
        return True
    
    # Pattern 2: Custom operation with context
    class CustomOperation(RetryableOperation):
        def __init__(self, data: Dict[str, Any]):
            self.data = data
        
        async def execute(self, context: RetryContext) -> Any:
            # Your operation logic
            context.metadata["operation_data"] = self.data
            return {"result": "success"}
        
        def get_operation_id(self) -> str:
            return f"custom_op_{id(self)}"
        
        def get_operation_type(self) -> str:
            return "custom_operation"
    
    # Pattern 3: Handler integration
    handler = StaffApplicationHandler()
    result = await handler.create_application(
        staff_id=123,
        client_id=456,
        app_data={"type": "connection_request", "client_data": {"phone": "+998901234567"}}
    )
    
    # Pattern 4: Monitoring integration
    monitor = ApplicationMonitoringService()
    health = await monitor.get_operation_health()
    
    print(f"System health: {health['overall_health']}")
    print(f"Success rate: {health['success_rate']:.2%}")


if __name__ == "__main__":
    asyncio.run(example_usage_patterns())