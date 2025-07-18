"""
Staff Application Retry Manager Usage Examples

This module demonstrates how to use the retry manager for staff application
creation operations with various scenarios and configurations.
"""

import asyncio
import random
from datetime import datetime
from typing import Any, Optional

from utils.staff_application_retry_manager import (
    StaffApplicationRetryManager,
    RetryableOperation,
    RetryContext,
    RetryConfig,
    CircuitBreakerConfig,
    RetryStrategy,
    retryable_operation,
    get_retry_manager,
    configure_retry_manager
)
from utils.staff_application_error_handler import StaffApplicationError, StaffApplicationErrorType
from utils.logger import setup_module_logger

logger = setup_module_logger("staff_application_retry_example")


class StaffApplicationCreationOperation(RetryableOperation):
    """Example retryable operation for staff application creation"""
    
    def __init__(self, staff_id: int, client_id: int, application_type: str, 
                 failure_rate: float = 0.3):
        self.staff_id = staff_id
        self.client_id = client_id
        self.application_type = application_type
        self.failure_rate = failure_rate
        self.operation_id = f"app_creation_{staff_id}_{client_id}_{datetime.now().timestamp()}"
    
    async def execute(self, context: RetryContext) -> dict:
        """Simulate application creation with potential failures"""
        
        # Add context metadata
        context.user_id = self.staff_id
        context.metadata.update({
            "client_id": self.client_id,
            "application_type": self.application_type,
            "attempt_number": len(context.attempts)
        })
        
        # Simulate processing time
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Simulate various failure scenarios
        if random.random() < self.failure_rate:
            failure_type = random.choice([
                "database_error",
                "validation_error", 
                "rate_limit",
                "network_timeout",
                "permission_denied"
            ])
            
            if failure_type == "database_error":
                raise StaffApplicationError(
                    StaffApplicationErrorType.DATABASE_ERROR,
                    "Database connection failed during application creation",
                    {"client_id": self.client_id, "staff_id": self.staff_id}
                )
            elif failure_type == "validation_error":
                raise StaffApplicationError(
                    StaffApplicationErrorType.APPLICATION_VALIDATION,
                    "Application data validation failed",
                    {"invalid_fields": ["phone_number", "address"]}
                )
            elif failure_type == "rate_limit":
                raise StaffApplicationError(
                    StaffApplicationErrorType.RATE_LIMIT_EXCEEDED,
                    "Rate limit exceeded for application creation",
                    {"retry_after": 30}
                )
            elif failure_type == "network_timeout":
                raise StaffApplicationError(
                    StaffApplicationErrorType.WORKFLOW_INITIALIZATION,
                    "Network timeout during workflow initialization",
                    {"timeout_seconds": 10}
                )
            elif failure_type == "permission_denied":
                raise StaffApplicationError(
                    StaffApplicationErrorType.PERMISSION_DENIED,
                    "Staff member does not have permission to create this application type",
                    {"required_permission": f"create_{self.application_type}"}
                )
        
        # Success case
        application_id = random.randint(10000, 99999)
        logger.info(f"Successfully created application {application_id}")
        
        return {
            "application_id": application_id,
            "staff_id": self.staff_id,
            "client_id": self.client_id,
            "application_type": self.application_type,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }
    
    def get_operation_id(self) -> str:
        return self.operation_id
    
    def get_operation_type(self) -> str:
        return f"staff_application_creation_{self.application_type}"


class ClientNotificationOperation(RetryableOperation):
    """Example retryable operation for client notifications"""
    
    def __init__(self, client_id: int, application_id: int, notification_type: str):
        self.client_id = client_id
        self.application_id = application_id
        self.notification_type = notification_type
        self.operation_id = f"notification_{client_id}_{application_id}_{datetime.now().timestamp()}"
    
    async def execute(self, context: RetryContext) -> dict:
        """Simulate client notification with potential failures"""
        
        context.metadata.update({
            "client_id": self.client_id,
            "application_id": self.application_id,
            "notification_type": self.notification_type
        })
        
        # Simulate notification processing
        await asyncio.sleep(random.uniform(0.05, 0.2))
        
        # Simulate notification failures (lower rate than application creation)
        if random.random() < 0.2:
            raise StaffApplicationError(
                StaffApplicationErrorType.NOTIFICATION_FAILURE,
                f"Failed to send {self.notification_type} notification to client",
                {"client_id": self.client_id, "application_id": self.application_id}
            )
        
        logger.info(f"Successfully sent {self.notification_type} notification to client {self.client_id}")
        
        return {
            "notification_id": random.randint(1000, 9999),
            "client_id": self.client_id,
            "application_id": self.application_id,
            "notification_type": self.notification_type,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
    
    def get_operation_id(self) -> str:
        return self.operation_id
    
    def get_operation_type(self) -> str:
        return f"client_notification_{self.notification_type}"


# Decorator example
@retryable_operation("database_update")
async def update_application_status(application_id: int, status: str) -> dict:
    """Example function using retry decorator"""
    
    # Simulate database update with potential failures
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    if random.random() < 0.25:
        raise StaffApplicationError(
            StaffApplicationErrorType.DATABASE_ERROR,
            "Failed to update application status in database",
            {"application_id": application_id, "new_status": status}
        )
    
    logger.info(f"Successfully updated application {application_id} status to {status}")
    
    return {
        "application_id": application_id,
        "status": status,
        "updated_at": datetime.now().isoformat()
    }


async def example_basic_retry():
    """Basic retry example with default configuration"""
    print("\n=== Basic Retry Example ===")
    
    retry_manager = StaffApplicationRetryManager()
    
    # Create an operation that might fail
    operation = StaffApplicationCreationOperation(
        staff_id=123,
        client_id=456,
        application_type="connection_request",
        failure_rate=0.6  # High failure rate to demonstrate retries
    )
    
    try:
        result = await retry_manager.execute_with_retry(operation)
        print(f"✅ Operation succeeded: {result}")
    except Exception as e:
        print(f"❌ Operation failed after all retries: {e}")
    
    # Show operation statistics
    stats = retry_manager.get_operation_statistics()
    print(f"📊 Statistics: {stats}")


async def example_custom_retry_config():
    """Example with custom retry configuration"""
    print("\n=== Custom Retry Configuration Example ===")
    
    # Configure aggressive retry policy
    custom_config = RetryConfig(
        max_attempts=5,
        base_delay_seconds=0.5,
        max_delay_seconds=10.0,
        backoff_multiplier=1.5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True
    )
    
    retry_manager = StaffApplicationRetryManager(retry_config=custom_config)
    
    operation = StaffApplicationCreationOperation(
        staff_id=789,
        client_id=101,
        application_type="technical_service",
        failure_rate=0.7
    )
    
    try:
        result = await retry_manager.execute_with_retry(operation)
        print(f"✅ Operation succeeded with custom config: {result}")
    except Exception as e:
        print(f"❌ Operation failed with custom config: {e}")


async def example_circuit_breaker():
    """Example demonstrating circuit breaker functionality"""
    print("\n=== Circuit Breaker Example ===")
    
    # Configure circuit breaker with low thresholds for demo
    circuit_config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout_seconds=5.0,
        success_threshold=2
    )
    
    retry_manager = StaffApplicationRetryManager(
        circuit_breaker_config=circuit_config
    )
    
    # Create multiple operations that will fail
    operations = [
        StaffApplicationCreationOperation(
            staff_id=i,
            client_id=i + 100,
            application_type="connection_request",
            failure_rate=0.9  # Very high failure rate
        )
        for i in range(1, 8)
    ]
    
    for i, operation in enumerate(operations, 1):
        try:
            print(f"\n--- Attempt {i} ---")
            cb_status = retry_manager.get_circuit_breaker_status()
            print(f"Circuit breaker state: {cb_status['state']}")
            
            result = await retry_manager.execute_with_retry(operation)
            print(f"✅ Operation {i} succeeded: {result['application_id']}")
        except Exception as e:
            print(f"❌ Operation {i} failed: {e}")
        
        # Small delay between operations
        await asyncio.sleep(0.1)
    
    # Show final circuit breaker status
    final_status = retry_manager.get_circuit_breaker_status()
    print(f"\n🔌 Final circuit breaker status: {final_status}")


async def example_parallel_operations():
    """Example with multiple parallel operations"""
    print("\n=== Parallel Operations Example ===")
    
    retry_manager = StaffApplicationRetryManager()
    
    # Create multiple operations to run in parallel
    app_operations = [
        StaffApplicationCreationOperation(
            staff_id=i,
            client_id=i + 200,
            application_type="connection_request" if i % 2 == 0 else "technical_service",
            failure_rate=0.4
        )
        for i in range(1, 6)
    ]
    
    # Run operations in parallel
    tasks = [
        retry_manager.execute_with_retry(op)
        for op in app_operations
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful = 0
    failed = 0
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"❌ Operation {i} failed: {result}")
            failed += 1
        else:
            print(f"✅ Operation {i} succeeded: App ID {result['application_id']}")
            successful += 1
    
    print(f"\n📈 Parallel execution results: {successful} successful, {failed} failed")
    
    # Show statistics
    stats = retry_manager.get_operation_statistics()
    print(f"📊 Final statistics: {stats}")


async def example_decorator_usage():
    """Example using the retry decorator"""
    print("\n=== Decorator Usage Example ===")
    
    # Configure global retry manager
    configure_retry_manager(
        retry_config=RetryConfig(
            max_attempts=4,
            base_delay_seconds=0.2,
            strategy=RetryStrategy.LINEAR_BACKOFF
        )
    )
    
    # Use decorated function
    try:
        result = await update_application_status(12345, "approved")
        print(f"✅ Decorated function succeeded: {result}")
    except Exception as e:
        print(f"❌ Decorated function failed: {e}")


async def example_notification_workflow():
    """Example of complete application creation with notifications"""
    print("\n=== Complete Workflow Example ===")
    
    retry_manager = StaffApplicationRetryManager()
    
    # Step 1: Create application
    app_operation = StaffApplicationCreationOperation(
        staff_id=555,
        client_id=777,
        application_type="technical_service",
        failure_rate=0.3
    )
    
    try:
        app_result = await retry_manager.execute_with_retry(app_operation)
        print(f"✅ Application created: {app_result['application_id']}")
        
        # Step 2: Send client notification
        notification_operation = ClientNotificationOperation(
            client_id=app_result["client_id"],
            application_id=app_result["application_id"],
            notification_type="application_created"
        )
        
        notification_result = await retry_manager.execute_with_retry(notification_operation)
        print(f"✅ Notification sent: {notification_result['notification_id']}")
        
        # Step 3: Update application status
        status_result = await update_application_status(
            app_result["application_id"], 
            "pending_review"
        )
        print(f"✅ Status updated: {status_result}")
        
        print("\n🎉 Complete workflow succeeded!")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
    
    # Show final statistics
    stats = retry_manager.get_operation_statistics()
    print(f"\n📊 Workflow statistics: {stats}")


async def example_operation_monitoring():
    """Example demonstrating operation monitoring capabilities"""
    print("\n=== Operation Monitoring Example ===")
    
    retry_manager = StaffApplicationRetryManager()
    
    # Start a long-running operation
    operation = StaffApplicationCreationOperation(
        staff_id=999,
        client_id=888,
        application_type="connection_request",
        failure_rate=0.8  # High failure rate for multiple attempts
    )
    
    # Start operation in background
    task = asyncio.create_task(retry_manager.execute_with_retry(operation))
    
    # Monitor operation progress
    operation_id = operation.get_operation_id()
    
    for i in range(10):
        await asyncio.sleep(0.5)
        
        # Check operation status
        status = retry_manager.get_operation_status(operation_id)
        if status:
            print(f"📊 Monitoring {i+1}: Attempts={status['total_attempts']}, "
                  f"Active={status['is_active']}, Success={status['final_success']}")
        
        # Check if operation completed
        if task.done():
            break
    
    # Get final result
    try:
        result = await task
        print(f"✅ Monitored operation succeeded: {result}")
    except Exception as e:
        print(f"❌ Monitored operation failed: {e}")
    
    # Show active operations
    active_ops = retry_manager.get_active_operations()
    print(f"🔄 Active operations: {len(active_ops)}")


async def main():
    """Run all examples"""
    print("🚀 Staff Application Retry Manager Examples")
    print("=" * 50)
    
    examples = [
        example_basic_retry,
        example_custom_retry_config,
        example_decorator_usage,
        example_parallel_operations,
        example_notification_workflow,
        example_operation_monitoring,
        example_circuit_breaker,  # Run circuit breaker last as it affects global state
    ]
    
    for example_func in examples:
        try:
            await example_func()
            await asyncio.sleep(1)  # Brief pause between examples
        except Exception as e:
            print(f"❌ Example {example_func.__name__} failed: {e}")
    
    print("\n✨ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())