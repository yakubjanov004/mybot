"""
Retry Manager for Staff Application Creation

This module implements sophisticated retry mechanisms with exponential backoff,
circuit breaker patterns, and intelligent failure handling for staff application
creation operations.

Requirements implemented: Task 18 - Create comprehensive error handling
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod

from utils.logger import setup_module_logger
from utils.staff_application_error_handler import StaffApplicationErrorType, StaffApplicationError

logger = setup_module_logger("staff_application_retry_manager")


class RetryStrategy(Enum):
    """Different retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"
    NO_RETRY = "no_retry"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0  # 5 minutes
    backoff_multiplier: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_errors: List[StaffApplicationErrorType] = field(default_factory=list)
    non_retryable_errors: List[StaffApplicationErrorType] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.retryable_errors:
            self.retryable_errors = [
                StaffApplicationErrorType.WORKFLOW_INITIALIZATION,
                StaffApplicationErrorType.NOTIFICATION_FAILURE,
                StaffApplicationErrorType.DATABASE_ERROR,
                StaffApplicationErrorType.RATE_LIMIT_EXCEEDED,
                StaffApplicationErrorType.STATE_MANAGEMENT
            ]
        
        if not self.non_retryable_errors:
            self.non_retryable_errors = [
                StaffApplicationErrorType.PERMISSION_DENIED,
                StaffApplicationErrorType.CLIENT_VALIDATION,
                StaffApplicationErrorType.APPLICATION_VALIDATION,
                StaffApplicationErrorType.SECURITY_VIOLATION,
                StaffApplicationErrorType.ROLE_VALIDATION
            ]


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    error: Optional[Exception] = None
    duration_ms: Optional[float] = None
    success: bool = False


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 60.0
    success_threshold: int = 3  # Successes needed to close circuit
    monitoring_window_seconds: float = 300.0  # 5 minutes


@dataclass
class RetryContext:
    """Context information for retry operations"""
    operation_id: str
    operation_type: str
    user_id: Optional[int] = None
    role_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    attempts: List[RetryAttempt] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    final_success: bool = False


class RetryableOperation(ABC):
    """Abstract base class for retryable operations"""
    
    @abstractmethod
    async def execute(self, context: RetryContext) -> Any:
        """Execute the operation"""
        pass
    
    @abstractmethod
    def get_operation_id(self) -> str:
        """Get unique operation identifier"""
        pass
    
    @abstractmethod
    def get_operation_type(self) -> str:
        """Get operation type for logging/monitoring"""
        pass


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.failures_in_window: List[datetime] = []
        
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        now = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and \
               (now - self.last_failure_time).total_seconds() >= self.config.recovery_timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.failures_in_window.clear()
                logger.info("Circuit breaker closed after successful recovery")
        elif self.state == CircuitBreakerState.CLOSED:
            # Clean old failures from monitoring window
            self._clean_failure_window()
    
    def record_failure(self):
        """Record failed operation"""
        now = datetime.now()
        self.failure_count += 1
        self.last_failure_time = now
        self.failures_in_window.append(now)
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker opened due to failure in HALF_OPEN state")
        elif self.state == CircuitBreakerState.CLOSED:
            self._clean_failure_window()
            if len(self.failures_in_window) >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker opened due to {len(self.failures_in_window)} failures")
    
    def _clean_failure_window(self):
        """Remove old failures outside monitoring window"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.config.monitoring_window_seconds)
        self.failures_in_window = [f for f in self.failures_in_window if f > cutoff]


class StaffApplicationRetryManager:
    """Main retry manager for staff application operations"""
    
    def __init__(self, 
                 retry_config: Optional[RetryConfig] = None,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config or CircuitBreakerConfig())
        self.active_operations: Dict[str, RetryContext] = {}
        self.operation_history: List[RetryContext] = []
        
    async def execute_with_retry(self, 
                               operation: RetryableOperation,
                               context: Optional[RetryContext] = None) -> Any:
        """Execute operation with retry logic"""
        
        if context is None:
            context = RetryContext(
                operation_id=operation.get_operation_id(),
                operation_type=operation.get_operation_type()
            )
        
        self.active_operations[context.operation_id] = context
        
        try:
            return await self._execute_with_retry_internal(operation, context)
        finally:
            context.completed_at = datetime.now()
            self.active_operations.pop(context.operation_id, None)
            self.operation_history.append(context)
            
            # Keep history limited
            if len(self.operation_history) > 1000:
                self.operation_history = self.operation_history[-500:]
    
    async def _execute_with_retry_internal(self, 
                                         operation: RetryableOperation,
                                         context: RetryContext) -> Any:
        """Internal retry execution logic"""
        
        last_error = None
        
        for attempt_num in range(1, self.retry_config.max_attempts + 1):
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                raise StaffApplicationError(
                    StaffApplicationErrorType.CIRCUIT_BREAKER_OPEN,
                    f"Circuit breaker is open for operation {context.operation_type}",
                    {"operation_id": context.operation_id}
                )
            
            attempt = RetryAttempt(
                attempt_number=attempt_num,
                scheduled_at=datetime.now()
            )
            context.attempts.append(attempt)
            
            try:
                logger.info(f"Executing {context.operation_type} attempt {attempt_num}/{self.retry_config.max_attempts}")
                
                start_time = datetime.now()
                attempt.executed_at = start_time
                
                result = await operation.execute(context)
                
                end_time = datetime.now()
                attempt.duration_ms = (end_time - start_time).total_seconds() * 1000
                attempt.success = True
                context.final_success = True
                
                self.circuit_breaker.record_success()
                
                logger.info(f"Operation {context.operation_type} succeeded on attempt {attempt_num}")
                return result
                
            except Exception as e:
                end_time = datetime.now()
                attempt.duration_ms = (end_time - attempt.executed_at).total_seconds() * 1000
                attempt.error = e
                attempt.success = False
                last_error = e
                
                self.circuit_breaker.record_failure()
                
                # Check if error is retryable
                if isinstance(e, StaffApplicationError):
                    if e.error_type in self.retry_config.non_retryable_errors:
                        logger.error(f"Non-retryable error in {context.operation_type}: {e}")
                        raise e
                    elif e.error_type not in self.retry_config.retryable_errors:
                        logger.error(f"Unknown error type in {context.operation_type}: {e}")
                        raise e
                
                logger.warning(f"Attempt {attempt_num} failed for {context.operation_type}: {e}")
                
                # If this was the last attempt, raise the error
                if attempt_num >= self.retry_config.max_attempts:
                    break
                
                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt_num)
                logger.info(f"Retrying {context.operation_type} in {delay:.2f} seconds")
                await asyncio.sleep(delay)
        
        # All attempts failed
        logger.error(f"All {self.retry_config.max_attempts} attempts failed for {context.operation_type}")
        if last_error:
            raise last_error
        else:
            raise StaffApplicationError(
                StaffApplicationErrorType.MAX_RETRIES_EXCEEDED,
                f"Maximum retry attempts exceeded for {context.operation_type}",
                {"operation_id": context.operation_id, "attempts": self.retry_config.max_attempts}
            )
    
    def _calculate_delay(self, attempt_number: int) -> float:
        """Calculate delay before next retry attempt"""
        if self.retry_config.strategy == RetryStrategy.NO_RETRY:
            return 0
        elif self.retry_config.strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif self.retry_config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.retry_config.base_delay_seconds
        elif self.retry_config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.retry_config.base_delay_seconds * attempt_number
        elif self.retry_config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.retry_config.base_delay_seconds * (self.retry_config.backoff_multiplier ** (attempt_number - 1))
        else:
            delay = self.retry_config.base_delay_seconds
        
        # Apply maximum delay limit
        delay = min(delay, self.retry_config.max_delay_seconds)
        
        # Apply jitter if enabled
        if self.retry_config.jitter and delay > 0:
            import random
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)  # Ensure non-negative
        
        return delay
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an operation"""
        # Check active operations first
        if operation_id in self.active_operations:
            context = self.active_operations[operation_id]
            return self._context_to_status(context, is_active=True)
        
        # Check history
        for context in reversed(self.operation_history):
            if context.operation_id == operation_id:
                return self._context_to_status(context, is_active=False)
        
        return None
    
    def _context_to_status(self, context: RetryContext, is_active: bool) -> Dict[str, Any]:
        """Convert retry context to status dictionary"""
        return {
            "operation_id": context.operation_id,
            "operation_type": context.operation_type,
            "user_id": context.user_id,
            "role_type": context.role_type,
            "is_active": is_active,
            "started_at": context.started_at.isoformat(),
            "completed_at": context.completed_at.isoformat() if context.completed_at else None,
            "final_success": context.final_success,
            "total_attempts": len(context.attempts),
            "attempts": [
                {
                    "attempt_number": attempt.attempt_number,
                    "scheduled_at": attempt.scheduled_at.isoformat(),
                    "executed_at": attempt.executed_at.isoformat() if attempt.executed_at else None,
                    "duration_ms": attempt.duration_ms,
                    "success": attempt.success,
                    "error": str(attempt.error) if attempt.error else None
                }
                for attempt in context.attempts
            ],
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "metadata": context.metadata
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "state": self.circuit_breaker.state.value,
            "failure_count": self.circuit_breaker.failure_count,
            "success_count": self.circuit_breaker.success_count,
            "last_failure_time": self.circuit_breaker.last_failure_time.isoformat() if self.circuit_breaker.last_failure_time else None,
            "failures_in_window": len(self.circuit_breaker.failures_in_window),
            "can_execute": self.circuit_breaker.can_execute()
        }
    
    def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        self.circuit_breaker.state = CircuitBreakerState.CLOSED
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.success_count = 0
        self.circuit_breaker.last_failure_time = None
        self.circuit_breaker.failures_in_window.clear()
        logger.info("Circuit breaker manually reset")
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Get list of currently active operations"""
        return [
            self._context_to_status(context, is_active=True)
            for context in self.active_operations.values()
        ]
    
    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get overall operation statistics"""
        total_operations = len(self.operation_history)
        successful_operations = sum(1 for ctx in self.operation_history if ctx.final_success)
        
        if total_operations == 0:
            return {
                "total_operations": 0,
                "success_rate": 0.0,
                "average_attempts": 0.0,
                "operation_types": {}
            }
        
        # Calculate statistics by operation type
        type_stats = {}
        total_attempts = 0
        
        for context in self.operation_history:
            op_type = context.operation_type
            if op_type not in type_stats:
                type_stats[op_type] = {
                    "total": 0,
                    "successful": 0,
                    "total_attempts": 0
                }
            
            type_stats[op_type]["total"] += 1
            type_stats[op_type]["total_attempts"] += len(context.attempts)
            total_attempts += len(context.attempts)
            
            if context.final_success:
                type_stats[op_type]["successful"] += 1
        
        # Calculate success rates for each type
        for stats in type_stats.values():
            stats["success_rate"] = stats["successful"] / stats["total"] if stats["total"] > 0 else 0.0
            stats["average_attempts"] = stats["total_attempts"] / stats["total"] if stats["total"] > 0 else 0.0
        
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": total_operations - successful_operations,
            "success_rate": successful_operations / total_operations,
            "average_attempts": total_attempts / total_operations,
            "active_operations": len(self.active_operations),
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "operation_types": type_stats
        }


# Global retry manager instance
_global_retry_manager: Optional[StaffApplicationRetryManager] = None


def get_retry_manager() -> StaffApplicationRetryManager:
    """Get global retry manager instance"""
    global _global_retry_manager
    if _global_retry_manager is None:
        _global_retry_manager = StaffApplicationRetryManager()
    return _global_retry_manager


def configure_retry_manager(retry_config: Optional[RetryConfig] = None,
                          circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
    """Configure global retry manager"""
    global _global_retry_manager
    _global_retry_manager = StaffApplicationRetryManager(retry_config, circuit_breaker_config)


# Convenience decorator for retryable functions
def retryable_operation(operation_type: str, 
                       retry_config: Optional[RetryConfig] = None):
    """Decorator to make functions retryable"""
    def decorator(func: Callable):
        class DecoratorOperation(RetryableOperation):
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs
                self.func = func
                
            async def execute(self, context: RetryContext) -> Any:
                if asyncio.iscoroutinefunction(self.func):
                    return await self.func(*self.args, **self.kwargs)
                else:
                    return self.func(*self.args, **self.kwargs)
            
            def get_operation_id(self) -> str:
                return f"{operation_type}_{id(self)}"
            
            def get_operation_type(self) -> str:
                return operation_type
        
        async def wrapper(*args, **kwargs):
            operation = DecoratorOperation(*args, **kwargs)
            manager = get_retry_manager()
            if retry_config:
                manager.retry_config = retry_config
            return await manager.execute_with_retry(operation)
        
        return wrapper
    return decorator