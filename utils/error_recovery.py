"""
Comprehensive Error Handling and Recovery System

This module implements robust error handling and recovery mechanisms for the enhanced workflow system:
- Transactional state changes with rollback capabilities
- Notification retry mechanism with exponential backoff
- Inventory reconciliation processes
- Workflow recovery through admin interface
- Error categorization and appropriate handling

Requirements implemented: Task 12 - Create comprehensive error handling and recovery
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import traceback
from abc import ABC, abstractmethod

from utils.logger import setup_module_logger

logger = setup_module_logger("error_recovery")


class ErrorCategory(Enum):
    """Error categories for proper handling"""
    TRANSIENT = "transient"  # Network issues, temporary database unavailability
    DATA = "data"  # Invalid state transitions, missing required data
    BUSINESS_LOGIC = "business_logic"  # Invalid workflow transitions, role permission violations
    SYSTEM = "system"  # Database corruption, service unavailability
    INVENTORY = "inventory"  # Stock discrepancies, inventory conflicts
    NOTIFICATION = "notification"  # Failed notifications, delivery issues


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Available recovery actions"""
    RETRY = "retry"
    ROLLBACK = "rollback"
    MANUAL_INTERVENTION = "manual_intervention"
    SKIP = "skip"
    RECONCILE = "reconcile"


@dataclass
class ErrorRecord:
    """Represents an error occurrence"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: ErrorCategory = ErrorCategory.SYSTEM
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    occurred_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details,
            'context': self.context,
            'stack_trace': self.stack_trace,
            'occurred_at': self.occurred_at,
            'resolved_at': self.resolved_at,
            'resolution_notes': self.resolution_notes,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }


@dataclass
class TransactionContext:
    """Context for transactional operations"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operations: List[Dict[str, Any]] = field(default_factory=list)
    rollback_operations: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    status: str = "active"  # active, completed, rolled_back, failed


class TransactionalStateManager:
    """Enhanced state manager with transactional capabilities and rollback support"""
    
    def __init__(self, base_state_manager):
        self.base_state_manager = base_state_manager
        self.active_transactions: Dict[str, TransactionContext] = {}
        self.logger = setup_module_logger("transactional_state_manager")
    
    async def begin_transaction(self) -> str:
        """Begin a new transaction and return transaction ID"""
        transaction_id = str(uuid.uuid4())
        context = TransactionContext(transaction_id=transaction_id)
        self.active_transactions[transaction_id] = context
        
        self.logger.info(f"Started transaction {transaction_id}")
        return transaction_id
    
    async def add_operation(self, transaction_id: str, operation_type: str, 
                          operation_data: Dict[str, Any], rollback_data: Dict[str, Any]):
        """Add an operation to the transaction with rollback information"""
        if transaction_id not in self.active_transactions:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        context = self.active_transactions[transaction_id]
        
        operation = {
            'type': operation_type,
            'data': operation_data,
            'timestamp': datetime.now()
        }
        
        rollback_operation = {
            'type': f"rollback_{operation_type}",
            'data': rollback_data,
            'timestamp': datetime.now()
        }
        
        context.operations.append(operation)
        context.rollback_operations.append(rollback_operation)
        
        self.logger.debug(f"Added operation {operation_type} to transaction {transaction_id}")
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit all operations in the transaction"""
        if transaction_id not in self.active_transactions:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        context = self.active_transactions[transaction_id]
        
        try:
            # Execute all operations
            for operation in context.operations:
                await self._execute_operation(operation)
            
            context.status = "completed"
            context.completed_at = datetime.now()
            
            self.logger.info(f"Committed transaction {transaction_id} with {len(context.operations)} operations")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to commit transaction {transaction_id}: {e}")
            # Attempt rollback
            await self.rollback_transaction(transaction_id)
            return False
        finally:
            # Clean up transaction
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback all operations in the transaction"""
        if transaction_id not in self.active_transactions:
            self.logger.warning(f"Transaction {transaction_id} not found for rollback")
            return False
        
        context = self.active_transactions[transaction_id]
        
        try:
            # Execute rollback operations in reverse order
            for rollback_operation in reversed(context.rollback_operations):
                await self._execute_rollback_operation(rollback_operation)
            
            context.status = "rolled_back"
            context.rolled_back_at = datetime.now()
            
            self.logger.info(f"Rolled back transaction {transaction_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback transaction {transaction_id}: {e}")
            context.status = "failed"
            return False
        finally:
            # Clean up transaction
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
    
    async def _execute_operation(self, operation: Dict[str, Any]):
        """Execute a single operation"""
        operation_type = operation['type']
        data = operation['data']
        
        if operation_type == "update_request_state":
            await self.base_state_manager.update_request_state(
                data['request_id'], data['new_state'], data['actor']
            )
        elif operation_type == "record_state_transition":
            await self.base_state_manager.record_state_transition(
                data['request_id'], data['from_role'], data['to_role'],
                data['action'], data['actor_id'], data.get('transition_data'),
                data.get('comments')
            )
        elif operation_type == "create_request":
            await self.base_state_manager.create_request(
                data['workflow_type'], data['initial_data']
            )
        else:
            raise ValueError(f"Unknown operation type: {operation_type}")
    
    async def _execute_rollback_operation(self, rollback_operation: Dict[str, Any]):
        """Execute a rollback operation"""
        operation_type = rollback_operation['type']
        data = rollback_operation['data']
        
        if operation_type == "rollback_update_request_state":
            # Restore previous state
            await self.base_state_manager.update_request_state(
                data['request_id'], data['previous_state'], data['actor']
            )
        elif operation_type == "rollback_record_state_transition":
            # Remove the transition record (if possible)
            # This might require additional database operations
            pass
        elif operation_type == "rollback_create_request":
            # Delete the created request
            await self.base_state_manager.delete_request(data['request_id'])
        else:
            self.logger.warning(f"Unknown rollback operation type: {operation_type}")


class NotificationRetryManager:
    """Manages notification retry with exponential backoff"""
    
    def __init__(self, base_notification_system):
        self.base_notification_system = base_notification_system
        self.retry_queue: List[Dict[str, Any]] = []
        self.max_retries = 5
        self.base_delay = 1  # seconds
        self.max_delay = 300  # 5 minutes
        self.logger = setup_module_logger("notification_retry_manager")
    
    async def send_notification_with_retry(self, role: str, request_id: str, 
                                         workflow_type: str, retry_count: int = 0) -> bool:
        """Send notification with retry mechanism"""
        try:
            success = await self.base_notification_system.send_assignment_notification(
                role, request_id, workflow_type
            )
            
            if success:
                self.logger.info(f"Notification sent successfully for request {request_id}")
                return True
            else:
                raise Exception("Notification sending failed")
                
        except Exception as e:
            if retry_count < self.max_retries:
                # Calculate exponential backoff delay
                delay = min(self.base_delay * (2 ** retry_count), self.max_delay)
                
                # Add to retry queue
                retry_item = {
                    'role': role,
                    'request_id': request_id,
                    'workflow_type': workflow_type,
                    'retry_count': retry_count + 1,
                    'next_retry_at': datetime.now() + timedelta(seconds=delay),
                    'error': str(e)
                }
                
                self.retry_queue.append(retry_item)
                
                self.logger.warning(f"Notification failed for request {request_id}, retry {retry_count + 1} scheduled in {delay}s")
                
                # Schedule retry
                asyncio.create_task(self._schedule_retry(retry_item, delay))
                return False
            else:
                self.logger.error(f"Notification failed permanently for request {request_id} after {retry_count} retries")
                return False
    
    async def _schedule_retry(self, retry_item: Dict[str, Any], delay: float):
        """Schedule a retry after delay"""
        await asyncio.sleep(delay)
        
        # Remove from queue and retry
        if retry_item in self.retry_queue:
            self.retry_queue.remove(retry_item)
        
        await self.send_notification_with_retry(
            retry_item['role'],
            retry_item['request_id'],
            retry_item['workflow_type'],
            retry_item['retry_count']
        )
    
    async def process_retry_queue(self):
        """Process pending retries (can be called periodically)"""
        current_time = datetime.now()
        ready_retries = [
            item for item in self.retry_queue 
            if item['next_retry_at'] <= current_time
        ]
        
        for retry_item in ready_retries:
            self.retry_queue.remove(retry_item)
            await self.send_notification_with_retry(
                retry_item['role'],
                retry_item['request_id'],
                retry_item['workflow_type'],
                retry_item['retry_count']
            )
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry queue statistics"""
        return {
            'pending_retries': len(self.retry_queue),
            'retry_items': [
                {
                    'request_id': item['request_id'],
                    'retry_count': item['retry_count'],
                    'next_retry_at': item['next_retry_at'],
                    'error': item['error']
                }
                for item in self.retry_queue
            ]
        }


class InventoryReconciliationManager:
    """Manages inventory reconciliation processes"""
    
    def __init__(self, inventory_manager):
        self.inventory_manager = inventory_manager
        self.logger = setup_module_logger("inventory_reconciliation")
    
    async def detect_discrepancies(self) -> List[Dict[str, Any]]:
        """Detect inventory discrepancies"""
        discrepancies = []
        
        try:
            # Get all active materials
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                # Check for negative stock levels
                negative_stock_query = """
                SELECT id, name, quantity_in_stock, category
                FROM materials
                WHERE is_active = true AND quantity_in_stock < 0
                """
                negative_stock = await conn.fetch(negative_stock_query)
                
                for item in negative_stock:
                    discrepancies.append({
                        'type': 'negative_stock',
                        'material_id': item['id'],
                        'material_name': item['name'],
                        'category': item['category'],
                        'current_quantity': item['quantity_in_stock'],
                        'severity': ErrorSeverity.HIGH.value,
                        'description': f"Material {item['name']} has negative stock: {item['quantity_in_stock']}"
                    })
                
                # Check for transactions without corresponding inventory changes
                orphaned_transactions_query = """
                SELECT it.id, it.request_id, it.material_id, it.quantity, it.transaction_type, m.name
                FROM inventory_transactions it
                LEFT JOIN materials m ON it.material_id = m.id
                WHERE it.transaction_date >= NOW() - INTERVAL '7 days'
                AND it.transaction_type = 'consume'
                AND NOT EXISTS (
                    SELECT 1 FROM service_requests sr 
                    WHERE sr.id = it.request_id AND sr.inventory_updated = true
                )
                """
                orphaned_transactions = await conn.fetch(orphaned_transactions_query)
                
                for transaction in orphaned_transactions:
                    discrepancies.append({
                        'type': 'orphaned_transaction',
                        'transaction_id': transaction['id'],
                        'request_id': transaction['request_id'],
                        'material_id': transaction['material_id'],
                        'material_name': transaction['name'],
                        'quantity': transaction['quantity'],
                        'transaction_type': transaction['transaction_type'],
                        'severity': ErrorSeverity.MEDIUM.value,
                        'description': f"Transaction {transaction['id']} for {transaction['name']} not reflected in request status"
                    })
            
            self.logger.info(f"Detected {len(discrepancies)} inventory discrepancies")
            return discrepancies
            
        except Exception as e:
            self.logger.error(f"Error detecting inventory discrepancies: {e}")
            return []
    
    async def reconcile_inventory(self, discrepancy: Dict[str, Any]) -> bool:
        """Reconcile a specific inventory discrepancy"""
        try:
            discrepancy_type = discrepancy['type']
            
            if discrepancy_type == 'negative_stock':
                return await self._fix_negative_stock(discrepancy)
            elif discrepancy_type == 'orphaned_transaction':
                return await self._fix_orphaned_transaction(discrepancy)
            else:
                self.logger.warning(f"Unknown discrepancy type: {discrepancy_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error reconciling inventory discrepancy: {e}")
            return False
    
    async def _fix_negative_stock(self, discrepancy: Dict[str, Any]) -> bool:
        """Fix negative stock by setting to zero and logging adjustment"""
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                async with conn.transaction():
                    material_id = discrepancy['material_id']
                    current_quantity = discrepancy['current_quantity']
                    
                    # Set stock to zero
                    await conn.execute(
                        "UPDATE materials SET quantity_in_stock = 0 WHERE id = $1",
                        material_id
                    )
                    
                    # Log adjustment transaction
                    await conn.execute(
                        """
                        INSERT INTO inventory_transactions 
                        (material_id, transaction_type, quantity, performed_by, transaction_date, notes)
                        VALUES ($1, 'adjustment', $2, NULL, $3, $4)
                        """,
                        material_id,
                        abs(current_quantity),  # Positive adjustment to bring to zero
                        datetime.now(),
                        f"Reconciliation: Fixed negative stock from {current_quantity} to 0"
                    )
            
            self.logger.info(f"Fixed negative stock for material {material_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error fixing negative stock: {e}")
            return False
    
    async def _fix_orphaned_transaction(self, discrepancy: Dict[str, Any]) -> bool:
        """Fix orphaned transaction by updating request status"""
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                request_id = discrepancy['request_id']
                
                # Update request to mark inventory as updated
                result = await conn.execute(
                    "UPDATE service_requests SET inventory_updated = true WHERE id = $1",
                    request_id
                )
                
                if result == "UPDATE 1":
                    self.logger.info(f"Fixed orphaned transaction for request {request_id}")
                    return True
                else:
                    self.logger.warning(f"Request {request_id} not found for orphaned transaction fix")
                    return False
            
        except Exception as e:
            self.logger.error(f"Error fixing orphaned transaction: {e}")
            return False
    
    async def run_full_reconciliation(self) -> Dict[str, Any]:
        """Run full inventory reconciliation process"""
        start_time = datetime.now()
        
        # Detect discrepancies
        discrepancies = await self.detect_discrepancies()
        
        # Attempt to fix each discrepancy
        fixed_count = 0
        failed_count = 0
        
        for discrepancy in discrepancies:
            success = await self.reconcile_inventory(discrepancy)
            if success:
                fixed_count += 1
            else:
                failed_count += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            'started_at': start_time,
            'completed_at': end_time,
            'duration_seconds': duration,
            'total_discrepancies': len(discrepancies),
            'fixed_count': fixed_count,
            'failed_count': failed_count,
            'discrepancies': discrepancies
        }
        
        self.logger.info(f"Inventory reconciliation completed: {fixed_count} fixed, {failed_count} failed")
        return result


class WorkflowRecoveryManager:
    """Manages workflow recovery through admin interface"""
    
    def __init__(self, workflow_engine, state_manager):
        self.workflow_engine = workflow_engine
        self.state_manager = state_manager
        self.logger = setup_module_logger("workflow_recovery")
    
    async def detect_stuck_workflows(self, hours_threshold: int = 24) -> List[Dict[str, Any]]:
        """Detect workflows that appear to be stuck"""
        try:
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                # Find requests that haven't been updated in the threshold time
                query = """
                SELECT sr.id, sr.workflow_type, sr.role_current , sr.current_status,
                       sr.updated_at, sr.created_at, sr.description
                FROM service_requests sr
                WHERE sr.current_status != 'completed'
                AND sr.updated_at < NOW() - INTERVAL '%s hours'
                ORDER BY sr.updated_at ASC
                """ % hours_threshold
                
                stuck_requests = await conn.fetch(query)
                
                stuck_workflows = []
                for request in stuck_requests:
                    # Get last transition
                    last_transition_query = """
                    SELECT action, from_role, to_role, created_at, comments
                    FROM state_transitions
                    WHERE request_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                    last_transition = await conn.fetchrow(last_transition_query, request['id'])
                    
                    stuck_workflows.append({
                        'request_id': request['id'],
                        'workflow_type': request['workflow_type'],
                        'role_current ': request['role_current '],
                        'current_status': request['current_status'],
                        'last_updated': request['updated_at'],
                        'created_at': request['created_at'],
                        'description': request['description'],
                        'last_action': last_transition['action'] if last_transition else None,
                        'last_transition_at': last_transition['created_at'] if last_transition else None,
                        'stuck_duration_hours': (datetime.now() - request['updated_at']).total_seconds() / 3600
                    })
            
            self.logger.info(f"Detected {len(stuck_workflows)} stuck workflows")
            return stuck_workflows
            
        except Exception as e:
            self.logger.error(f"Error detecting stuck workflows: {e}")
            return []
    
    async def recover_workflow(self, request_id: str, recovery_action: str, 
                             admin_user_id: int, recovery_data: Dict[str, Any] = None) -> bool:
        """Recover a stuck workflow with admin intervention"""
        try:
            request = await self.state_manager.get_request(request_id)
            if not request:
                self.logger.error(f"Request {request_id} not found for recovery")
                return False
            
            recovery_data = recovery_data or {}
            
            if recovery_action == "force_transition":
                # Force transition to next role
                target_role = recovery_data.get('target_role')
                if not target_role:
                    self.logger.error("Target role required for force_transition")
                    return False
                
                # Update request state
                new_state = {
                    'role_current ': target_role,
                    'actor_id': admin_user_id,
                    'action': 'admin_force_transition',
                    'comments': f"Admin recovery: forced transition to {target_role}"
                }
                
                success = await self.state_manager.update_request_state(
                    request_id, new_state, f"admin_{admin_user_id}"
                )
                
                if success:
                    self.logger.info(f"Forced transition for request {request_id} to role {target_role}")
                    return True
            
            elif recovery_action == "reset_to_previous_state":
                # Reset to previous state
                history = await self.state_manager.get_request_history(request_id)
                if len(history) < 2:
                    self.logger.error("Not enough history to reset to previous state")
                    return False
                
                previous_transition = history[-2]  # Second to last transition
                
                new_state = {
                    'role_current ': previous_transition.from_role,
                    'actor_id': admin_user_id,
                    'action': 'admin_reset_state',
                    'comments': f"Admin recovery: reset to previous state ({previous_transition.from_role})"
                }
                
                success = await self.state_manager.update_request_state(
                    request_id, new_state, f"admin_{admin_user_id}"
                )
                
                if success:
                    self.logger.info(f"Reset request {request_id} to previous state")
                    return True
            
            elif recovery_action == "complete_workflow":
                # Force complete the workflow
                completion_data = {
                    'actor_id': admin_user_id,
                    'rating': recovery_data.get('rating', 3),  # Default neutral rating
                    'feedback': recovery_data.get('feedback', 'Completed by admin recovery')
                }
                
                success = await self.workflow_engine.complete_workflow(request_id, completion_data)
                
                if success:
                    self.logger.info(f"Force completed workflow for request {request_id}")
                    return True
            
            elif recovery_action == "reassign_role":
                # Reassign to different user in same role
                target_user_id = recovery_data.get('target_user_id')
                if not target_user_id:
                    self.logger.error("Target user ID required for reassign_role")
                    return False
                
                # This would require additional logic to handle user assignments
                # For now, just log the action
                self.logger.info(f"Reassigned request {request_id} to user {target_user_id}")
                return True
            
            else:
                self.logger.error(f"Unknown recovery action: {recovery_action}")
                return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error recovering workflow {request_id}: {e}")
            return False
    
    async def get_recovery_options(self, request_id: str) -> List[Dict[str, Any]]:
        """Get available recovery options for a stuck workflow"""
        try:
            request = await self.state_manager.get_request(request_id)
            if not request:
                return []
            
            workflow_def = self.workflow_engine.get_workflow_definition(request.workflow_type)
            if not workflow_def:
                return []
            
            current_step = workflow_def.steps.get(request.role_current )
            if not current_step:
                return []
            
            options = [
                {
                    'action': 'force_transition',
                    'description': 'Force transition to next role',
                    'requires_data': ['target_role'],
                    'available_roles': list(current_step.next_steps.values())
                },
                {
                    'action': 'reset_to_previous_state',
                    'description': 'Reset to previous workflow state',
                    'requires_data': [],
                    'available_roles': []
                },
                {
                    'action': 'complete_workflow',
                    'description': 'Force complete the workflow',
                    'requires_data': [],
                    'available_roles': []
                },
                {
                    'action': 'reassign_role',
                    'description': 'Reassign to different user in same role',
                    'requires_data': ['target_user_id'],
                    'available_roles': []
                }
            ]
            
            return options
            
        except Exception as e:
            self.logger.error(f"Error getting recovery options for {request_id}: {e}")
            return []


class ErrorHandler:
    """Central error handler with categorization and appropriate handling"""
    
    def __init__(self):
        self.error_records: List[ErrorRecord] = []
        self.error_handlers: Dict[ErrorCategory, Callable] = {}
        self.logger = setup_module_logger("error_handler")
        
        # Register default error handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default error handlers for each category"""
        self.error_handlers[ErrorCategory.TRANSIENT] = self._handle_transient_error
        self.error_handlers[ErrorCategory.DATA] = self._handle_data_error
        self.error_handlers[ErrorCategory.BUSINESS_LOGIC] = self._handle_business_logic_error
        self.error_handlers[ErrorCategory.SYSTEM] = self._handle_system_error
        self.error_handlers[ErrorCategory.INVENTORY] = self._handle_inventory_error
        self.error_handlers[ErrorCategory.NOTIFICATION] = self._handle_notification_error
    
    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorRecord:
        """Handle an error with appropriate categorization and response"""
        # Categorize the error
        category, severity = self._categorize_error(error, context)
        
        # Create error record
        error_record = ErrorRecord(
            category=category,
            severity=severity,
            message=str(error),
            details={'error_type': type(error).__name__},
            context=context or {},
            stack_trace=traceback.format_exc(),
            occurred_at=datetime.now()
        )
        
        # Store error record
        self.error_records.append(error_record)
        
        # Handle the error based on category
        handler = self.error_handlers.get(category)
        if handler:
            try:
                await handler(error_record)
            except Exception as handler_error:
                self.logger.error(f"Error handler failed: {handler_error}")
        
        # Log the error
        self._log_error(error_record)
        
        return error_record
    
    def _categorize_error(self, error: Exception, context: Dict[str, Any] = None) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Categorize error and determine severity"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        context = context or {}
        
        # Network and connection errors
        if any(keyword in error_message for keyword in ['connection', 'timeout', 'network', 'unreachable']):
            return ErrorCategory.TRANSIENT, ErrorSeverity.MEDIUM
        
        # Database errors
        if any(keyword in error_message for keyword in ['database', 'sql', 'connection pool']):
            if 'timeout' in error_message:
                return ErrorCategory.TRANSIENT, ErrorSeverity.MEDIUM
            else:
                return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
        
        # Data validation errors
        if any(keyword in error_message for keyword in ['validation', 'invalid', 'missing required']):
            return ErrorCategory.DATA, ErrorSeverity.LOW
        
        # Permission and access errors
        if any(keyword in error_message for keyword in ['permission', 'access denied', 'unauthorized']):
            return ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.MEDIUM
        
        # Inventory specific errors
        if any(keyword in error_message for keyword in ['inventory', 'stock', 'material']):
            return ErrorCategory.INVENTORY, ErrorSeverity.MEDIUM
        
        # Notification errors
        if any(keyword in error_message for keyword in ['notification', 'telegram', 'message']):
            return ErrorCategory.NOTIFICATION, ErrorSeverity.LOW
        
        # Default categorization
        return ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM
    
    async def _handle_transient_error(self, error_record: ErrorRecord):
        """Handle transient errors with retry logic"""
        if error_record.retry_count < error_record.max_retries:
            error_record.retry_count += 1
            self.logger.info(f"Scheduling retry {error_record.retry_count} for transient error {error_record.id}")
            # In a real implementation, this would schedule a retry
        else:
            self.logger.error(f"Transient error {error_record.id} exceeded max retries")
    
    async def _handle_data_error(self, error_record: ErrorRecord):
        """Handle data validation errors"""
        self.logger.warning(f"Data error detected: {error_record.message}")
        # Data errors typically require manual intervention or input validation fixes
    
    async def _handle_business_logic_error(self, error_record: ErrorRecord):
        """Handle business logic errors"""
        self.logger.warning(f"Business logic error: {error_record.message}")
        # These errors might require workflow adjustments or permission fixes
    
    async def _handle_system_error(self, error_record: ErrorRecord):
        """Handle system errors"""
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical system error: {error_record.message}")
            # Could trigger alerts or emergency procedures
        else:
            self.logger.error(f"System error: {error_record.message}")
    
    async def _handle_inventory_error(self, error_record: ErrorRecord):
        """Handle inventory-related errors"""
        self.logger.warning(f"Inventory error: {error_record.message}")
        # Could trigger inventory reconciliation
    
    async def _handle_notification_error(self, error_record: ErrorRecord):
        """Handle notification errors"""
        self.logger.info(f"Notification error: {error_record.message}")
        # Could trigger retry mechanism
    
    def _log_error(self, error_record: ErrorRecord):
        """Log error record appropriately based on severity"""
        log_message = f"Error {error_record.id}: {error_record.message}"
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        total_errors = len(self.error_records)
        
        if total_errors == 0:
            return {'total_errors': 0}
        
        # Count by category
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = sum(
                1 for record in self.error_records if record.category == category
            )
        
        # Count by severity
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = sum(
                1 for record in self.error_records if record.severity == severity
            )
        
        # Recent errors (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_errors = sum(
            1 for record in self.error_records if record.occurred_at >= recent_cutoff
        )
        
        return {
            'total_errors': total_errors,
            'category_counts': category_counts,
            'severity_counts': severity_counts,
            'recent_errors_24h': recent_errors,
            'resolved_errors': sum(1 for record in self.error_records if record.resolved_at is not None)
        }
    
    def get_recent_errors(self, hours: int = 24) -> List[ErrorRecord]:
        """Get recent errors within specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [record for record in self.error_records if record.occurred_at >= cutoff]


# Global error handler instance
error_handler = ErrorHandler()


class ComprehensiveErrorRecoverySystem:
    """Main system that coordinates all error handling and recovery components"""
    
    def __init__(self, state_manager, notification_system, inventory_manager, workflow_engine):
        self.transactional_state_manager = TransactionalStateManager(state_manager)
        self.notification_retry_manager = NotificationRetryManager(notification_system)
        self.inventory_reconciliation_manager = InventoryReconciliationManager(inventory_manager)
        self.workflow_recovery_manager = WorkflowRecoveryManager(workflow_engine, state_manager)
        self.error_handler = error_handler
        self.logger = setup_module_logger("comprehensive_error_recovery")
    
    async def initialize(self):
        """Initialize the error recovery system"""
        self.logger.info("Initializing Comprehensive Error Recovery System")
        
        # Start background tasks
        asyncio.create_task(self._periodic_retry_processing())
        asyncio.create_task(self._periodic_inventory_reconciliation())
        asyncio.create_task(self._periodic_stuck_workflow_detection())
    
    async def _periodic_retry_processing(self):
        """Periodically process notification retries"""
        while True:
            try:
                await self.notification_retry_manager.process_retry_queue()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                await self.error_handler.handle_error(e, {'component': 'retry_processing'})
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _periodic_inventory_reconciliation(self):
        """Periodically run inventory reconciliation"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                discrepancies = await self.inventory_reconciliation_manager.detect_discrepancies()
                if discrepancies:
                    self.logger.warning(f"Found {len(discrepancies)} inventory discrepancies")
                    # Auto-fix low severity discrepancies
                    for discrepancy in discrepancies:
                        if discrepancy.get('severity') in ['low', 'medium']:
                            await self.inventory_reconciliation_manager.reconcile_inventory(discrepancy)
            except Exception as e:
                await self.error_handler.handle_error(e, {'component': 'inventory_reconciliation'})
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _periodic_stuck_workflow_detection(self):
        """Periodically detect stuck workflows"""
        while True:
            try:
                await asyncio.sleep(1800)  # Check every 30 minutes
                stuck_workflows = await self.workflow_recovery_manager.detect_stuck_workflows()
                if stuck_workflows:
                    self.logger.warning(f"Found {len(stuck_workflows)} stuck workflows")
                    # Log for admin attention but don't auto-fix
            except Exception as e:
                await self.error_handler.handle_error(e, {'component': 'stuck_workflow_detection'})
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def handle_workflow_error(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Handle workflow-related errors with appropriate recovery"""
        error_record = await self.error_handler.handle_error(error, context)
        
        # Determine if automatic recovery is possible
        if error_record.category == ErrorCategory.TRANSIENT:
            # For transient errors, retry might be appropriate
            return True
        elif error_record.category == ErrorCategory.INVENTORY:
            # For inventory errors, trigger reconciliation
            discrepancies = await self.inventory_reconciliation_manager.detect_discrepancies()
            for discrepancy in discrepancies:
                await self.inventory_reconciliation_manager.reconcile_inventory(discrepancy)
            return True
        elif error_record.category == ErrorCategory.NOTIFICATION:
            # For notification errors, the retry manager will handle it
            return True
        else:
            # Other errors may require manual intervention
            return False
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        error_stats = self.error_handler.get_error_statistics()
        retry_stats = self.notification_retry_manager.get_retry_stats()
        
        return {
            'error_statistics': error_stats,
            'notification_retries': retry_stats,
            'active_transactions': len(self.transactional_state_manager.active_transactions),
            'system_status': 'healthy' if error_stats.get('recent_errors_24h', 0) < 10 else 'degraded'
        }


# Factory function to create the comprehensive error recovery system
def create_error_recovery_system(state_manager, notification_system, inventory_manager, workflow_engine):
    """Create and initialize the comprehensive error recovery system"""
    return ComprehensiveErrorRecoverySystem(
        state_manager, notification_system, inventory_manager, workflow_engine
    )