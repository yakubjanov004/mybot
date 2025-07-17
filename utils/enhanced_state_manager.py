"""
Enhanced State Manager with Transactional Support and Error Recovery

This module extends the base state manager with:
- Transactional state changes with rollback capabilities
- Enhanced error handling and recovery
- Automatic retry mechanisms for transient failures
- Comprehensive audit logging

Requirements implemented: Task 12 - Create comprehensive error handling and recovery
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.state_manager import StateManager, StateManagerInterface
from utils.error_recovery import (
    TransactionalStateManager, error_handler, ErrorCategory, ErrorSeverity
)
from utils.logger import setup_module_logger

logger = setup_module_logger("enhanced_state_manager")


class EnhancedStateManager(StateManagerInterface):
    """Enhanced state manager with transactional support and error recovery"""
    
    def __init__(self, pool=None):
        self.base_state_manager = StateManager(pool)
        self.transactional_manager = TransactionalStateManager(self.base_state_manager)
        self.error_handler = error_handler
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    async def create_request_with_transaction(self, workflow_type: str, initial_data: Dict[str, Any]) -> Optional[str]:
        """Create request with transactional support and error recovery"""
        transaction_id = await self.transactional_manager.begin_transaction()
        
        try:
            # Add create operation to transaction
            await self.transactional_manager.add_operation(
                transaction_id,
                "create_request",
                {
                    'workflow_type': workflow_type,
                    'initial_data': initial_data
                },
                {
                    'request_id': None  # Will be filled after creation
                }
            )
            
            # Execute the creation
            request_id = await self._create_request_with_retry(workflow_type, initial_data)
            
            if request_id:
                # Update rollback data with actual request ID
                context = self.transactional_manager.active_transactions[transaction_id]
                if context.rollback_operations:
                    context.rollback_operations[-1]['data']['request_id'] = request_id
                
                # Commit transaction
                success = await self.transactional_manager.commit_transaction(transaction_id)
                if success:
                    logger.info(f"Successfully created request {request_id} with transaction")
                    return request_id
                else:
                    logger.error(f"Failed to commit transaction for request creation")
                    return None
            else:
                # Rollback on failure
                await self.transactional_manager.rollback_transaction(transaction_id)
                return None
                
        except Exception as e:
            # Handle error and rollback
            await self.error_handler.handle_error(e, {
                'operation': 'create_request_with_transaction',
                'workflow_type': workflow_type,
                'transaction_id': transaction_id
            })
            await self.transactional_manager.rollback_transaction(transaction_id)
            return None
    
    async def update_request_state_with_transaction(self, request_id: str, new_state: Dict[str, Any], 
                                                  actor: str) -> bool:
        """Update request state with transactional support and error recovery"""
        transaction_id = await self.transactional_manager.begin_transaction()
        
        try:
            # Get current state for rollback
            current_request = await self.base_state_manager.get_request(request_id)
            if not current_request:
                await self.transactional_manager.rollback_transaction(transaction_id)
                return False
            
            # Prepare rollback state
            rollback_state = {
                'role_current ': current_request.role_current ,
                'current_status': current_request.current_status,
                'state_data': current_request.state_data,
                'equipment_used': current_request.equipment_used,
                'inventory_updated': current_request.inventory_updated,
                'completion_rating': current_request.completion_rating,
                'feedback_comments': current_request.feedback_comments
            }
            
            # Add update operation to transaction
            await self.transactional_manager.add_operation(
                transaction_id,
                "update_request_state",
                {
                    'request_id': request_id,
                    'new_state': new_state,
                    'actor': actor
                },
                {
                    'request_id': request_id,
                    'previous_state': rollback_state,
                    'actor': actor
                }
            )
            
            # Execute the update with retry
            success = await self._update_request_state_with_retry(request_id, new_state, actor)
            
            if success:
                # Commit transaction
                commit_success = await self.transactional_manager.commit_transaction(transaction_id)
                if commit_success:
                    logger.info(f"Successfully updated request {request_id} with transaction")
                    return True
                else:
                    logger.error(f"Failed to commit transaction for request update")
                    return False
            else:
                # Rollback on failure
                await self.transactional_manager.rollback_transaction(transaction_id)
                return False
                
        except Exception as e:
            # Handle error and rollback
            await self.error_handler.handle_error(e, {
                'operation': 'update_request_state_with_transaction',
                'request_id': request_id,
                'transaction_id': transaction_id
            })
            await self.transactional_manager.rollback_transaction(transaction_id)
            return False
    
    async def _create_request_with_retry(self, workflow_type: str, initial_data: Dict[str, Any]) -> Optional[str]:
        """Create request with retry mechanism for transient failures"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                request_id = await self.base_state_manager.create_request(workflow_type, initial_data)
                if request_id:
                    return request_id
                else:
                    raise Exception("Request creation returned None")
                    
            except Exception as e:
                last_error = e
                
                # Categorize error to determine if retry is appropriate
                error_record = await self.error_handler.handle_error(e, {
                    'operation': 'create_request_retry',
                    'attempt': attempt + 1,
                    'workflow_type': workflow_type
                })
                
                # Only retry for transient errors
                if error_record.category == ErrorCategory.TRANSIENT and attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request creation failed (attempt {attempt + 1}), retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                else:
                    break
        
        # All retries failed
        logger.error(f"Request creation failed after {self.max_retries} attempts: {last_error}")
        return None
    
    async def _update_request_state_with_retry(self, request_id: str, new_state: Dict[str, Any], 
                                             actor: str) -> bool:
        """Update request state with retry mechanism for transient failures"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                success = await self.base_state_manager.update_request_state(request_id, new_state, actor)
                if success:
                    return True
                else:
                    raise Exception("Request state update returned False")
                    
            except Exception as e:
                last_error = e
                
                # Categorize error to determine if retry is appropriate
                error_record = await self.error_handler.handle_error(e, {
                    'operation': 'update_request_state_retry',
                    'attempt': attempt + 1,
                    'request_id': request_id
                })
                
                # Only retry for transient errors
                if error_record.category == ErrorCategory.TRANSIENT and attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request state update failed (attempt {attempt + 1}), retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                else:
                    break
        
        # All retries failed
        logger.error(f"Request state update failed after {self.max_retries} attempts: {last_error}")
        return False
    
    # Delegate other methods to base state manager with error handling
    async def create_request(self, workflow_type: str, initial_data: Dict[str, Any]) -> str:
        """Create request with error handling (non-transactional)"""
        try:
            return await self._create_request_with_retry(workflow_type, initial_data)
        except Exception as e:
            await self.error_handler.handle_error(e, {
                'operation': 'create_request',
                'workflow_type': workflow_type
            })
            return None
    
    async def update_request_state(self, request_id: str, new_state: Dict[str, Any], actor: str) -> bool:
        """Update request state with error handling (non-transactional)"""
        try:
            return await self._update_request_state_with_retry(request_id, new_state, actor)
        except Exception as e:
            await self.error_handler.handle_error(e, {
                'operation': 'update_request_state',
                'request_id': request_id
            })
            return False
    
    async def get_request(self, request_id: str):
        """Get request with error handling"""
        try:
            return await self.base_state_manager.get_request(request_id)
        except Exception as e:
            await self.error_handler.handle_error(e, {
                'operation': 'get_request',
                'request_id': request_id
            })
            return None
    
    async def get_requests_by_role(self, role: str, status_filter: str = None):
        """Get requests by role with error handling"""
        try:
            return await self.base_state_manager.get_requests_by_role(role, status_filter)
        except Exception as e:
            await self.error_handler.handle_error(e, {
                'operation': 'get_requests_by_role',
                'role': role,
                'status_filter': status_filter
            })
            return []
    
    async def get_request_history(self, request_id: str):
        """Get request history with error handling"""
        try:
            return await self.base_state_manager.get_request_history(request_id)
        except Exception as e:
            await self.error_handler.handle_error(e, {
                'operation': 'get_request_history',
                'request_id': request_id
            })
            return []
    
    async def record_state_transition(self, request_id: str, from_role: str, to_role: str, 
                                    action: str, actor_id: int, transition_data: Dict[str, Any] = None,
                                    comments: str = None) -> bool:
        """Record state transition with error handling"""
        try:
            return await self.base_state_manager.record_state_transition(
                request_id, from_role, to_role, action, actor_id, transition_data, comments
            )
        except Exception as e:
            await self.error_handler.handle_error(e, {
                'operation': 'record_state_transition',
                'request_id': request_id,
                'from_role': from_role,
                'to_role': to_role,
                'action': action
            })
            return False
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information"""
        try:
            # Get basic statistics
            from loader import bot
            pool = bot.db
            async with pool.acquire() as conn:
                # Count active requests
                active_requests = await conn.fetchval(
                    "SELECT COUNT(*) FROM service_requests WHERE current_status != 'completed'"
                )
                
                # Count recent errors
                recent_errors = len(self.error_handler.get_recent_errors(hours=24))
                
                # Count active transactions
                active_transactions = len(self.transactional_manager.active_transactions)
                
                return {
                    'active_requests': active_requests,
                    'recent_errors_24h': recent_errors,
                    'active_transactions': active_transactions,
                    'status': 'healthy' if recent_errors < 10 else 'degraded',
                    'last_check': datetime.now()
                }
                
        except Exception as e:
            await self.error_handler.handle_error(e, {'operation': 'get_system_health'})
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now()
            }


class EnhancedStateManagerFactory:
    """Factory for creating enhanced state manager instances"""
    
    @staticmethod
    def create_enhanced_state_manager(pool=None) -> EnhancedStateManager:
        """Creates a new enhanced state manager instance"""
        return EnhancedStateManager(pool)