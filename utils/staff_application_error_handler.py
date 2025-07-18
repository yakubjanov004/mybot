"""
Comprehensive Error Handling for Staff Application Creation

This module implements robust error handling and recovery mechanisms specifically
for staff application creation flows, including user-friendly error messages,
retry logic, and comprehensive logging.

Requirements implemented: Task 18 - Create comprehensive error handling
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import traceback
from abc import ABC, abstractmethod

from utils.logger import setup_module_logger
from utils.form_error_messages import FormErrorMessages, ErrorKeys, MessageType
from utils.error_recovery import ErrorCategory, ErrorSeverity, ErrorRecord

logger = setup_module_logger("staff_application_error_handler")


class StaffApplicationErrorType(Enum):
    """Specific error types for staff application creation"""
    PERMISSION_DENIED = "permission_denied"
    CLIENT_VALIDATION = "client_validation"
    APPLICATION_VALIDATION = "application_validation"
    WORKFLOW_INITIALIZATION = "workflow_initialization"
    NOTIFICATION_FAILURE = "notification_failure"
    DATABASE_ERROR = "database_error"
    SECURITY_VIOLATION = "security_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    FORM_PROCESSING = "form_processing"
    STATE_MANAGEMENT = "state_management"
    AUDIT_LOGGING = "audit_logging"
    CLIENT_SELECTION = "client_selection"
    ROLE_VALIDATION = "role_validation"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types"""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    USER_CORRECTION = "user_correction"
    ADMIN_INTERVENTION = "admin_intervention"
    FALLBACK_WORKFLOW = "fallback_workflow"
    SKIP_OPTIONAL = "skip_optional"
    RESET_STATE = "reset_state"
    ESCALATE = "escalate"


class StaffApplicationError(Exception):
    """Enhanced exception class for staff application creation"""
    
    def __init__(self, 
                 error_type: StaffApplicationErrorType,
                 message: str,
                 context: Optional[Dict[str, Any]] = None,
                 user_message: str = "",
                 technical_details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.id = str(uuid.uuid4())
        self.error_type = error_type
        self.message = message
        self.user_message = user_message
        self.context = context or {}
        self.technical_details = technical_details or {}
        self.occurred_at = datetime.now()
        self.resolved_at: Optional[datetime] = None
        self.resolution_notes = ""
        self.retry_count = 0
        self.max_retries = 3
        self.creator_id = self.context.get('creator_id')
        self.creator_role = self.context.get('creator_role')
        self.session_id = self.context.get('session_id')
        self.language = self.context.get('language', 'uz')
        
        # Determine category and severity
        self.category = self._determine_category()
        self.severity = self._determine_severity()
        self.recovery_strategy = self._determine_recovery_strategy()
        self.stack_trace = traceback.format_exc()
    
    def _determine_category(self) -> ErrorCategory:
        """Determine error category based on error type"""
        category_map = {
            StaffApplicationErrorType.PERMISSION_DENIED: ErrorCategory.BUSINESS_LOGIC,
            StaffApplicationErrorType.CLIENT_VALIDATION: ErrorCategory.DATA,
            StaffApplicationErrorType.APPLICATION_VALIDATION: ErrorCategory.DATA,
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION: ErrorCategory.BUSINESS_LOGIC,
            StaffApplicationErrorType.NOTIFICATION_FAILURE: ErrorCategory.TRANSIENT,
            StaffApplicationErrorType.DATABASE_ERROR: ErrorCategory.SYSTEM,
            StaffApplicationErrorType.SECURITY_VIOLATION: ErrorCategory.SYSTEM,
            StaffApplicationErrorType.RATE_LIMIT_EXCEEDED: ErrorCategory.TRANSIENT,
            StaffApplicationErrorType.FORM_PROCESSING: ErrorCategory.DATA,
            StaffApplicationErrorType.STATE_MANAGEMENT: ErrorCategory.SYSTEM,
            StaffApplicationErrorType.AUDIT_LOGGING: ErrorCategory.SYSTEM,
            StaffApplicationErrorType.CLIENT_SELECTION: ErrorCategory.DATA,
            StaffApplicationErrorType.ROLE_VALIDATION: ErrorCategory.BUSINESS_LOGIC,
            StaffApplicationErrorType.CIRCUIT_BREAKER_OPEN: ErrorCategory.SYSTEM,
            StaffApplicationErrorType.MAX_RETRIES_EXCEEDED: ErrorCategory.SYSTEM
        }
        return category_map.get(self.error_type, ErrorCategory.DATA)
    
    def _determine_severity(self) -> ErrorSeverity:
        """Determine error severity based on error type"""
        severity_map = {
            StaffApplicationErrorType.SECURITY_VIOLATION: ErrorSeverity.CRITICAL,
            StaffApplicationErrorType.DATABASE_ERROR: ErrorSeverity.CRITICAL,
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION: ErrorSeverity.HIGH,
            StaffApplicationErrorType.STATE_MANAGEMENT: ErrorSeverity.HIGH,
            StaffApplicationErrorType.AUDIT_LOGGING: ErrorSeverity.HIGH,
            StaffApplicationErrorType.PERMISSION_DENIED: ErrorSeverity.MEDIUM,
            StaffApplicationErrorType.NOTIFICATION_FAILURE: ErrorSeverity.MEDIUM,
            StaffApplicationErrorType.ROLE_VALIDATION: ErrorSeverity.MEDIUM,
            StaffApplicationErrorType.CIRCUIT_BREAKER_OPEN: ErrorSeverity.MEDIUM,
            StaffApplicationErrorType.MAX_RETRIES_EXCEEDED: ErrorSeverity.MEDIUM,
        }
        return severity_map.get(self.error_type, ErrorSeverity.LOW)
    
    def _determine_recovery_strategy(self) -> RecoveryStrategy:
        """Determine appropriate recovery strategy"""
        strategy_map = {
            StaffApplicationErrorType.PERMISSION_DENIED: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.CLIENT_VALIDATION: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.APPLICATION_VALIDATION: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION: RecoveryStrategy.RETRY_WITH_BACKOFF,
            StaffApplicationErrorType.NOTIFICATION_FAILURE: RecoveryStrategy.RETRY_WITH_BACKOFF,
            StaffApplicationErrorType.DATABASE_ERROR: RecoveryStrategy.ADMIN_INTERVENTION,
            StaffApplicationErrorType.SECURITY_VIOLATION: RecoveryStrategy.ESCALATE,
            StaffApplicationErrorType.RATE_LIMIT_EXCEEDED: RecoveryStrategy.RETRY_WITH_BACKOFF,
            StaffApplicationErrorType.FORM_PROCESSING: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.STATE_MANAGEMENT: RecoveryStrategy.RESET_STATE,
            StaffApplicationErrorType.AUDIT_LOGGING: RecoveryStrategy.SKIP_OPTIONAL,
            StaffApplicationErrorType.CLIENT_SELECTION: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.ROLE_VALIDATION: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.CIRCUIT_BREAKER_OPEN: RecoveryStrategy.RETRY_WITH_BACKOFF,
            StaffApplicationErrorType.MAX_RETRIES_EXCEEDED: RecoveryStrategy.ESCALATE
        }
        return strategy_map.get(self.error_type, RecoveryStrategy.USER_CORRECTION)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'error_type': self.error_type.value,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'user_message': self.user_message,
            'technical_details': self.technical_details,
            'context': self.context,
            'stack_trace': self.stack_trace,
            'occurred_at': self.occurred_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'recovery_strategy': self.recovery_strategy.value,
            'creator_id': self.creator_id,
            'creator_role': self.creator_role,
            'session_id': self.session_id,
            'language': self.language
        }
    
    def get_localized_user_message(self) -> str:
        """Get localized user-friendly error message"""
        if self.user_message:
            return self.user_message
        
        # Generate user message based on error type
        error_messages = {
            StaffApplicationErrorType.PERMISSION_DENIED: {
                'uz': "Sizda ushbu amalni bajarish huquqi yo'q",
                'ru': "У вас нет разрешения на выполнение этого действия"
            },
            StaffApplicationErrorType.CLIENT_VALIDATION: {
                'uz': "Mijoz ma'lumotlarida xatolik mavjud",
                'ru': "Ошибка в данных клиента"
            },
            StaffApplicationErrorType.APPLICATION_VALIDATION: {
                'uz': "Ariza ma'lumotlarida xatolik mavjud",
                'ru': "Ошибка в данных заявки"
            },
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION: {
                'uz': "Ish jarayonini boshlashda xatolik",
                'ru': "Ошибка при запуске рабочего процесса"
            },
            StaffApplicationErrorType.NOTIFICATION_FAILURE: {
                'uz': "Xabar yuborishda xatolik",
                'ru': "Ошибка при отправке уведомления"
            },
            StaffApplicationErrorType.DATABASE_ERROR: {
                'uz': "Ma'lumotlar bazasida xatolik",
                'ru': "Ошибка базы данных"
            },
            StaffApplicationErrorType.SECURITY_VIOLATION: {
                'uz': "Xavfsizlik buzilishi aniqlandi",
                'ru': "Обнаружено нарушение безопасности"
            },
            StaffApplicationErrorType.RATE_LIMIT_EXCEEDED: {
                'uz': "Juda ko'p so'rov yuborildi. Biroz kuting",
                'ru': "Слишком много запросов. Подождите немного"
            }
        }
        
        messages = error_messages.get(self.error_type, {})
        return messages.get(self.language, messages.get('uz', 'Xatolik yuz berdi'))


class StaffApplicationErrorHandler:
    """Comprehensive error handler for staff application creation"""
    
    def __init__(self):
        self.error_log: List[StaffApplicationError] = []
        self.retry_queue: List[Dict[str, Any]] = []
        self.recovery_handlers: Dict[StaffApplicationErrorType, Callable] = {}
        self._setup_recovery_handlers()
    
    def _setup_recovery_handlers(self):
        """Setup recovery handlers for different error types"""
        self.recovery_handlers = {
            StaffApplicationErrorType.PERMISSION_DENIED: self._handle_permission_error,
            StaffApplicationErrorType.CLIENT_VALIDATION: self._handle_validation_error,
            StaffApplicationErrorType.APPLICATION_VALIDATION: self._handle_validation_error,
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION: self._handle_workflow_error,
            StaffApplicationErrorType.NOTIFICATION_FAILURE: self._handle_notification_error,
            StaffApplicationErrorType.DATABASE_ERROR: self._handle_database_error,
            StaffApplicationErrorType.SECURITY_VIOLATION: self._handle_security_error,
            StaffApplicationErrorType.RATE_LIMIT_EXCEEDED: self._handle_rate_limit_error,
            StaffApplicationErrorType.FORM_PROCESSING: self._handle_form_error,
            StaffApplicationErrorType.STATE_MANAGEMENT: self._handle_state_error,
            StaffApplicationErrorType.AUDIT_LOGGING: self._handle_audit_error,
            StaffApplicationErrorType.CLIENT_SELECTION: self._handle_client_selection_error,
            StaffApplicationErrorType.ROLE_VALIDATION: self._handle_role_validation_error
        }
    
    async def handle_error(self, exception: Exception, context: Dict[str, Any]) -> 'StaffApplicationErrorRecord':
        """
        Handle an error with comprehensive recovery mechanisms.
        
        Args:
            exception: The exception that occurred
            context: Context information about the error
            
        Returns:
            StaffApplicationError record
        """
        try:
            # Create error record
            error_record = self._create_error_record(exception, context)
            
            # Log the error
            await self._log_error(error_record)
            
            # Attempt recovery
            recovery_result = await self._attempt_recovery(error_record)
            
            # Update error record with recovery information
            if recovery_result.get('recovered'):
                error_record.resolved_at = datetime.now()
                error_record.resolution_notes = recovery_result.get('notes', '')
            
            # Store error record
            self.error_log.append(error_record)
            
            # Alert if critical
            if error_record.severity == ErrorSeverity.CRITICAL:
                await self._send_critical_alert(error_record)
            
            return error_record
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}", exc_info=True)
            # Return a basic error record if error handling fails
            return StaffApplicationError(
                error_type=StaffApplicationErrorType.FORM_PROCESSING,
                message=str(exception),
                context=context
            )
    
    def _create_error_record(self, exception: Exception, context: Dict[str, Any]) -> StaffApplicationError:
        """Create detailed error record from exception and context"""
        # Determine error type and category
        error_type, category = self._classify_error(exception, context)
        
        # Determine severity
        severity = self._determine_severity(error_type, exception, context)
        
        # Extract context information
        creator_id = context.get('creator_id')
        creator_role = context.get('creator_role')
        session_id = context.get('session_id')
        language = context.get('language', 'uz')
        
        # Create technical details
        technical_details = {
            'exception_type': type(exception).__name__,
            'exception_args': str(exception.args) if exception.args else '',
            'context_keys': list(context.keys()),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add specific details based on error type
        if hasattr(exception, 'field'):
            technical_details['field'] = exception.field
        if hasattr(exception, 'value'):
            technical_details['value'] = str(exception.value)
        if hasattr(exception, 'reason'):
            technical_details['reason'] = exception.reason
        
        return StaffApplicationError(
            error_type=error_type,
            category=category,
            severity=severity,
            message=str(exception),
            technical_details=technical_details,
            context=context,
            stack_trace=traceback.format_exc(),
            creator_id=creator_id,
            creator_role=creator_role,
            session_id=session_id,
            language=language,
            recovery_strategy=self._determine_recovery_strategy(error_type, severity)
        )
    
    def _classify_error(self, exception: Exception, context: Dict[str, Any]) -> Tuple[StaffApplicationErrorType, ErrorCategory]:
        """Classify error type and category based on exception and context"""
        exception_name = type(exception).__name__
        
        # Permission errors
        if 'Permission' in exception_name or 'Forbidden' in exception_name:
            return StaffApplicationErrorType.PERMISSION_DENIED, ErrorCategory.BUSINESS_LOGIC
        
        # Validation errors
        if 'Validation' in exception_name or hasattr(exception, 'field'):
            if context.get('validation_stage') == 'client':
                return StaffApplicationErrorType.CLIENT_VALIDATION, ErrorCategory.DATA
            else:
                return StaffApplicationErrorType.APPLICATION_VALIDATION, ErrorCategory.DATA
        
        # Database errors
        if 'Database' in exception_name or 'Connection' in exception_name or 'SQL' in exception_name:
            return StaffApplicationErrorType.DATABASE_ERROR, ErrorCategory.SYSTEM
        
        # Workflow errors
        if 'Workflow' in exception_name:
            return StaffApplicationErrorType.WORKFLOW_INITIALIZATION, ErrorCategory.BUSINESS_LOGIC
        
        # Notification errors
        if 'Notification' in exception_name:
            return StaffApplicationErrorType.NOTIFICATION_FAILURE, ErrorCategory.TRANSIENT
        
        # Security errors
        if 'Security' in exception_name or 'XSS' in str(exception) or 'SQL injection' in str(exception):
            return StaffApplicationErrorType.SECURITY_VIOLATION, ErrorCategory.SYSTEM
        
        # Rate limit errors
        if 'Rate' in exception_name or 'Limit' in exception_name:
            return StaffApplicationErrorType.RATE_LIMIT_EXCEEDED, ErrorCategory.TRANSIENT
        
        # State management errors
        if 'State' in exception_name:
            return StaffApplicationErrorType.STATE_MANAGEMENT, ErrorCategory.SYSTEM
        
        # Client selection errors
        if context.get('operation') == 'client_selection':
            return StaffApplicationErrorType.CLIENT_SELECTION, ErrorCategory.DATA
        
        # Role validation errors
        if context.get('operation') == 'role_validation':
            return StaffApplicationErrorType.ROLE_VALIDATION, ErrorCategory.BUSINESS_LOGIC
        
        # Default to form processing error
        return StaffApplicationErrorType.FORM_PROCESSING, ErrorCategory.DATA
    
    def _determine_severity(self, error_type: StaffApplicationErrorType, 
                          exception: Exception, context: Dict[str, Any]) -> ErrorSeverity:
        """Determine error severity based on type and context"""
        # Critical errors
        if error_type in [
            StaffApplicationErrorType.SECURITY_VIOLATION,
            StaffApplicationErrorType.DATABASE_ERROR
        ]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if error_type in [
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION,
            StaffApplicationErrorType.STATE_MANAGEMENT,
            StaffApplicationErrorType.AUDIT_LOGGING
        ]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if error_type in [
            StaffApplicationErrorType.PERMISSION_DENIED,
            StaffApplicationErrorType.NOTIFICATION_FAILURE,
            StaffApplicationErrorType.ROLE_VALIDATION
        ]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors (validation, form processing)
        return ErrorSeverity.LOW
    
    def _determine_recovery_strategy(self, error_type: StaffApplicationErrorType, 
                                   severity: ErrorSeverity) -> RecoveryStrategy:
        """Determine appropriate recovery strategy"""
        strategy_map = {
            StaffApplicationErrorType.PERMISSION_DENIED: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.CLIENT_VALIDATION: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.APPLICATION_VALIDATION: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION: RecoveryStrategy.RETRY_WITH_BACKOFF,
            StaffApplicationErrorType.NOTIFICATION_FAILURE: RecoveryStrategy.RETRY_WITH_BACKOFF,
            StaffApplicationErrorType.DATABASE_ERROR: RecoveryStrategy.ADMIN_INTERVENTION,
            StaffApplicationErrorType.SECURITY_VIOLATION: RecoveryStrategy.ESCALATE,
            StaffApplicationErrorType.RATE_LIMIT_EXCEEDED: RecoveryStrategy.RETRY_WITH_BACKOFF,
            StaffApplicationErrorType.FORM_PROCESSING: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.STATE_MANAGEMENT: RecoveryStrategy.RESET_STATE,
            StaffApplicationErrorType.AUDIT_LOGGING: RecoveryStrategy.SKIP_OPTIONAL,
            StaffApplicationErrorType.CLIENT_SELECTION: RecoveryStrategy.USER_CORRECTION,
            StaffApplicationErrorType.ROLE_VALIDATION: RecoveryStrategy.USER_CORRECTION
        }
        
        return strategy_map.get(error_type, RecoveryStrategy.USER_CORRECTION)
    
    async def _log_error(self, error_record: StaffApplicationError):
        """Log error with appropriate level and context"""
        log_message = (
            f"Staff Application Error [{error_record.error_type.value}]: "
            f"{error_record.message} | "
            f"Creator: {error_record.creator_role}({error_record.creator_id}) | "
            f"Session: {error_record.session_id}"
        )
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={'error_record': error_record.to_dict()})
        elif error_record.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={'error_record': error_record.to_dict()})
        elif error_record.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={'error_record': error_record.to_dict()})
        else:
            logger.info(log_message, extra={'error_record': error_record.to_dict()})
    
    async def _attempt_recovery(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Attempt to recover from the error"""
        try:
            recovery_handler = self.recovery_handlers.get(error_record.error_type)
            if recovery_handler:
                return await recovery_handler(error_record)
            else:
                return {'recovered': False, 'notes': 'No recovery handler available'}
        except Exception as e:
            logger.error(f"Error during recovery attempt: {e}", exc_info=True)
            return {'recovered': False, 'notes': f'Recovery failed: {str(e)}'}
    
    async def _send_critical_alert(self, error_record: StaffApplicationError):
        """Send alert for critical errors"""
        try:
            # In a real implementation, this would send alerts to administrators
            # For now, just log the critical error
            logger.critical(
                f"CRITICAL ERROR ALERT: {error_record.error_type.value} - "
                f"Creator: {error_record.creator_role}({error_record.creator_id}) - "
                f"Message: {error_record.message}"
            )
        except Exception as e:
            logger.error(f"Failed to send critical alert: {e}")
    
    # Recovery handler methods
    
    async def _handle_permission_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle permission denied errors"""
        # For permission errors, user needs to be informed and no automatic recovery
        return {
            'recovered': False,
            'notes': 'Permission error requires user awareness',
            'user_action_required': True,
            'suggested_action': 'contact_admin'
        }
    
    async def _handle_validation_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle validation errors"""
        # Validation errors require user correction
        return {
            'recovered': False,
            'notes': 'Validation error requires user input correction',
            'user_action_required': True,
            'suggested_action': 'correct_input'
        }
    
    async def _handle_workflow_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle workflow initialization errors"""
        # Workflow errors can be retried
        if error_record.retry_count < error_record.max_retries:
            # Schedule retry
            await self._schedule_retry(error_record, delay_seconds=2 ** error_record.retry_count)
            return {
                'recovered': False,
                'notes': f'Scheduled retry {error_record.retry_count + 1}',
                'retry_scheduled': True
            }
        else:
            return {
                'recovered': False,
                'notes': 'Max retries exceeded for workflow error',
                'escalation_required': True
            }
    
    async def _handle_notification_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle notification failures"""
        # Notification failures can be retried or skipped
        if error_record.retry_count < error_record.max_retries:
            await self._schedule_retry(error_record, delay_seconds=5 * (error_record.retry_count + 1))
            return {
                'recovered': False,
                'notes': f'Scheduled notification retry {error_record.retry_count + 1}',
                'retry_scheduled': True
            }
        else:
            # Skip notification after max retries
            return {
                'recovered': True,
                'notes': 'Notification skipped after max retries',
                'partial_success': True
            }
    
    async def _handle_database_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle database errors"""
        # Database errors require admin intervention
        return {
            'recovered': False,
            'notes': 'Database error requires admin intervention',
            'admin_intervention_required': True,
            'escalation_required': True
        }
    
    async def _handle_security_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle security violations"""
        # Security errors require immediate escalation
        return {
            'recovered': False,
            'notes': 'Security violation detected - escalated',
            'escalation_required': True,
            'security_alert_sent': True
        }
    
    async def _handle_rate_limit_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle rate limit exceeded errors"""
        # Rate limit errors require waiting
        delay_seconds = 60  # Wait 1 minute for rate limit
        await self._schedule_retry(error_record, delay_seconds=delay_seconds)
        return {
            'recovered': False,
            'notes': f'Rate limit exceeded - retry scheduled in {delay_seconds}s',
            'retry_scheduled': True
        }
    
    async def _handle_form_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle form processing errors"""
        # Form errors require user correction
        return {
            'recovered': False,
            'notes': 'Form processing error requires user correction',
            'user_action_required': True,
            'suggested_action': 'review_form_data'
        }
    
    async def _handle_state_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle state management errors"""
        # State errors might require state reset
        return {
            'recovered': False,
            'notes': 'State management error - consider state reset',
            'suggested_action': 'reset_state'
        }
    
    async def _handle_audit_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle audit logging errors"""
        # Audit errors can be skipped to not block the main flow
        return {
            'recovered': True,
            'notes': 'Audit logging error - continuing without audit',
            'partial_success': True
        }
    
    async def _handle_client_selection_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle client selection errors"""
        # Client selection errors require user correction
        return {
            'recovered': False,
            'notes': 'Client selection error requires user correction',
            'user_action_required': True,
            'suggested_action': 'select_different_client'
        }
    
    async def _handle_role_validation_error(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Handle role validation errors"""
        # Role validation errors require user awareness
        return {
            'recovered': False,
            'notes': 'Role validation error - insufficient permissions',
            'user_action_required': True,
            'suggested_action': 'contact_admin'
        }
    
    async def _schedule_retry(self, error_record: StaffApplicationError, delay_seconds: int):
        """Schedule a retry for the failed operation"""
        retry_item = {
            'error_record_id': error_record.id,
            'retry_at': datetime.now() + timedelta(seconds=delay_seconds),
            'retry_count': error_record.retry_count + 1,
            'context': error_record.context
        }
        
        self.retry_queue.append(retry_item)
        error_record.retry_count += 1
        
        # Schedule the actual retry
        asyncio.create_task(self._execute_retry(retry_item, delay_seconds))
    
    async def _execute_retry(self, retry_item: Dict[str, Any], delay_seconds: int):
        """Execute a scheduled retry"""
        await asyncio.sleep(delay_seconds)
        
        try:
            # Remove from retry queue
            if retry_item in self.retry_queue:
                self.retry_queue.remove(retry_item)
            
            # In a real implementation, this would re-execute the failed operation
            # For now, just log the retry attempt
            logger.info(f"Executing retry for error {retry_item['error_record_id']}")
            
        except Exception as e:
            logger.error(f"Error during retry execution: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        if not self.error_log:
            return {'total_errors': 0}
        
        # Count by error type
        error_type_counts = {}
        for error in self.error_log:
            error_type = error.error_type.value
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for error in self.error_log:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by creator role
        role_counts = {}
        for error in self.error_log:
            if error.creator_role:
                role_counts[error.creator_role] = role_counts.get(error.creator_role, 0) + 1
        
        # Recent errors (last hour)
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_errors = [e for e in self.error_log if e.occurred_at >= recent_cutoff]
        
        return {
            'total_errors': len(self.error_log),
            'error_type_counts': error_type_counts,
            'severity_counts': severity_counts,
            'role_counts': role_counts,
            'recent_errors_count': len(recent_errors),
            'pending_retries': len(self.retry_queue),
            'resolved_errors': len([e for e in self.error_log if e.resolved_at is not None])
        }
    
    def get_user_friendly_error_message(self, error_record: StaffApplicationError) -> Dict[str, Any]:
        """Get user-friendly error message with recovery suggestions"""
        base_message = error_record.get_localized_user_message()
        
        # Add specific guidance based on error type
        guidance = self._get_error_guidance(error_record)
        
        return {
            'message': base_message,
            'guidance': guidance,
            'severity': error_record.severity.value,
            'can_retry': error_record.retry_count < error_record.max_retries,
            'suggested_action': self._get_suggested_user_action(error_record),
            'error_id': error_record.id
        }
    
    def _get_error_guidance(self, error_record: StaffApplicationError) -> str:
        """Get specific guidance for the error type"""
        guidance_map = {
            StaffApplicationErrorType.PERMISSION_DENIED: {
                'uz': "Administrator bilan bog'laning yoki boshqa foydalanuvchi hisobidan kirib ko'ring",
                'ru': "Обратитесь к администратору или попробуйте войти под другой учетной записью"
            },
            StaffApplicationErrorType.CLIENT_VALIDATION: {
                'uz': "Mijoz ma'lumotlarini tekshiring va to'g'rilang",
                'ru': "Проверьте и исправьте данные клиента"
            },
            StaffApplicationErrorType.APPLICATION_VALIDATION: {
                'uz': "Ariza ma'lumotlarini tekshiring va to'g'rilang",
                'ru': "Проверьте и исправьте данные заявки"
            },
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION: {
                'uz': "Biroz kuting va qayta urinib ko'ring",
                'ru': "Подождите немного и попробуйте снова"
            },
            StaffApplicationErrorType.NOTIFICATION_FAILURE: {
                'uz': "Ariza yaratildi, lekin xabar yuborilmadi",
                'ru': "Заявка создана, но уведомление не отправлено"
            },
            StaffApplicationErrorType.RATE_LIMIT_EXCEEDED: {
                'uz': "Juda tez so'rov yuborayapsiz. 1 daqiqa kuting",
                'ru': "Вы отправляете запросы слишком быстро. Подождите 1 минуту"
            }
        }
        
        guidance = guidance_map.get(error_record.error_type, {})
        return guidance.get(error_record.language, guidance.get('uz', ''))
    
    def _get_suggested_user_action(self, error_record: StaffApplicationError) -> str:
        """Get suggested user action for the error"""
        action_map = {
            StaffApplicationErrorType.PERMISSION_DENIED: 'contact_admin',
            StaffApplicationErrorType.CLIENT_VALIDATION: 'correct_client_data',
            StaffApplicationErrorType.APPLICATION_VALIDATION: 'correct_application_data',
            StaffApplicationErrorType.WORKFLOW_INITIALIZATION: 'retry_later',
            StaffApplicationErrorType.NOTIFICATION_FAILURE: 'continue_or_retry',
            StaffApplicationErrorType.DATABASE_ERROR: 'contact_admin',
            StaffApplicationErrorType.SECURITY_VIOLATION: 'contact_admin',
            StaffApplicationErrorType.RATE_LIMIT_EXCEEDED: 'wait_and_retry',
            StaffApplicationErrorType.FORM_PROCESSING: 'review_form',
            StaffApplicationErrorType.CLIENT_SELECTION: 'select_different_client'
        }
        
        return action_map.get(error_record.error_type, 'retry_or_contact_admin')


# Global error handler instance
staff_application_error_handler = StaffApplicationErrorHandler()


# Convenience functions for external use
async def handle_staff_application_error(exception: Exception, context: Dict[str, Any]) -> StaffApplicationError:
    """Handle staff application error with comprehensive recovery"""
    return await staff_application_error_handler.handle_error(exception, context)


def get_user_friendly_error(error_record: StaffApplicationError) -> Dict[str, Any]:
    """Get user-friendly error message"""
    return staff_application_error_handler.get_user_friendly_error_message(error_record)


def get_error_statistics() -> Dict[str, Any]:
    """Get error statistics for monitoring"""
    return staff_application_error_handler.get_error_statistics()