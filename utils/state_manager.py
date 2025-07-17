"""
State Manager - Manages workflow request state and transitions
Enhanced implementation with audit trail functionality and role-based filtering
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from database.models import ServiceRequest, StateTransition, WorkflowType, RequestStatus, Priority
from utils.logger import setup_module_logger

logger = setup_module_logger("state_manager")


class StateManagerInterface(ABC):
    """Abstract interface for state manager"""
    
    @abstractmethod
    async def create_request(self, workflow_type: str, initial_data: Dict[str, Any]) -> str:
        """Creates new request with initial state and returns request ID"""
        pass
    
    @abstractmethod
    async def update_request_state(self, request_id: str, new_state: Dict[str, Any], actor: str) -> bool:
        """Updates request state with audit logging"""
        pass
    
    @abstractmethod
    async def get_request(self, request_id: str) -> Optional[ServiceRequest]:
        """Gets request by ID"""
        pass
    
    @abstractmethod
    async def get_requests_by_role(self, role: str, status_filter: str = None) -> List[ServiceRequest]:
        """Returns requests assigned to specific role"""
        pass
    
    @abstractmethod
    async def get_request_history(self, request_id: str) -> List[StateTransition]:
        """Returns complete request history"""
        pass
    
    @abstractmethod
    async def record_state_transition(self, request_id: str, from_role: str, to_role: str, 
                                    action: str, actor_id: int, transition_data: Dict[str, Any] = None,
                                    comments: str = None) -> bool:
        """Records state transition with audit trail"""
        pass


class StateManager(StateManagerInterface):
    """Enhanced state manager implementation using PostgreSQL with audit trail functionality"""
    
    def __init__(self, pool=None):
        self.pool = pool
    
    def _get_pool(self):
        """Get database pool"""
        if self.pool:
            return self.pool
        # Fallback to bot's pool
        try:
            from loader import bot
            return bot.db
        except ImportError:
            logger.error("No database pool available")
            return None
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return str(uuid.uuid4())
    
    async def create_request(self, workflow_type: str, initial_data: Dict[str, Any]) -> str:
        """Creates new request with initial state and returns request ID"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return None
            
        request_id = self._generate_request_id()
        current_time = datetime.now()
        
        # Determine initial role based on workflow type and who created the request
        created_by_role = initial_data.get('created_by_role')
        initial_role = self._get_initial_role(workflow_type, created_by_role)
        
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Create the service request with staff creation tracking
                    query = """
                    INSERT INTO service_requests (
                        id, workflow_type, client_id, role_current , current_status,
                        created_at, updated_at, priority, description, location,
                        contact_info, state_data, equipment_used, inventory_updated,
                        completion_rating, feedback_comments, created_by_staff,
                        staff_creator_id, staff_creator_role, creation_source, client_notified_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
                    """
                    
                    await conn.execute(
                        query,
                        request_id,
                        workflow_type,
                        initial_data.get('client_id'),
                        initial_role,
                        RequestStatus.CREATED.value,
                        current_time,
                        current_time,
                        initial_data.get('priority', Priority.MEDIUM.value),
                        initial_data.get('description'),
                        initial_data.get('location'),
                        json.dumps(initial_data.get('contact_info', {})),
                        json.dumps(initial_data),
                        json.dumps([]),
                        False,
                        None,
                        None,
                        initial_data.get('created_by_staff', False),
                        initial_data.get('staff_creator_id'),
                        initial_data.get('staff_creator_role'),
                        initial_data.get('creation_source', 'client'),
                        None  # client_notified_at will be set when notification is sent
                    )
                    
                    # Record initial state transition
                    await self._record_transition(
                        conn, request_id, None, initial_role, 
                        "workflow_initiated", initial_data.get('client_id'),
                        initial_data, "Request created"
                    )
                    
                    logger.info(f"Created request {request_id} with workflow type {workflow_type}")
                    return request_id
                    
        except Exception as e:
            logger.error(f"Error creating request: {e}", exc_info=True)
            return None
    
    async def update_request_state(self, request_id: str, new_state: Dict[str, Any], actor: str) -> bool:
        """Updates request state with audit logging"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
            
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Get current request state
                    current_request = await self._get_request_internal(conn, request_id)
                    if not current_request:
                        logger.error(f"Request {request_id} not found")
                        return False
                    
                    # Prepare update data
                    current_time = datetime.now()
                    old_role = current_request.role_current 
                    old_status = current_request.current_status
                    
                    # Merge state data
                    merged_state_data = {**current_request.state_data, **new_state.get('state_data', {})}
                    
                    # Update the request
                    query = """
                    UPDATE service_requests SET
                        role_current = $2,
                        current_status = $3,
                        updated_at = $4,
                        priority = $5,
                        description = COALESCE($6, description),
                        location = COALESCE($7, location),
                        contact_info = $8,
                        state_data = $9,
                        equipment_used = $10,
                        inventory_updated = $11,
                        completion_rating = COALESCE($12, completion_rating),
                        feedback_comments = COALESCE($13, feedback_comments)
                    WHERE id = $1
                    """
                    
                    result = await conn.execute(
                        query,
                        request_id,
                        new_state.get('role_current ', current_request.role_current ),
                        new_state.get('current_status', current_request.current_status),
                        current_time,
                        new_state.get('priority', current_request.priority),
                        new_state.get('description'),
                        new_state.get('location'),
                        json.dumps(new_state.get('contact_info', current_request.contact_info)),
                        json.dumps(merged_state_data),
                        json.dumps(new_state.get('equipment_used', current_request.equipment_used)),
                        new_state.get('inventory_updated', current_request.inventory_updated),
                        new_state.get('completion_rating'),
                        new_state.get('feedback_comments')
                    )
                    
                    # Record state transition if role or status changed
                    new_role = new_state.get('role_current ', current_request.role_current )
                    new_status = new_state.get('current_status', current_request.current_status)
                    
                    if old_role != new_role or old_status != new_status:
                        await self._record_transition(
                            conn, request_id, old_role, new_role,
                            new_state.get('action', 'state_updated'),
                            new_state.get('actor_id'),
                            new_state,
                            new_state.get('comments', f"State updated by {actor}")
                        )
                    
                    logger.info(f"Updated request {request_id} state")
                    return result == "UPDATE 1"
                    
        except Exception as e:
            logger.error(f"Error updating request state: {e}", exc_info=True)
            return False
    
    def _get_initial_role(self, workflow_type: str, created_by_role: str = None) -> str:
        """Determine initial role based on workflow type and who created the request"""
        from database.models import UserRole
        
        # For call center initiated requests, route according to requirements:
        # - Connection requests → Manager
        # - Technical requests → Controller  
        # - Call center direct → Call center supervisor
        if created_by_role == UserRole.CALL_CENTER.value:
            if workflow_type == WorkflowType.CONNECTION_REQUEST.value:
                return UserRole.MANAGER.value
            elif workflow_type == WorkflowType.TECHNICAL_SERVICE.value:
                return UserRole.CONTROLLER.value
            elif workflow_type == WorkflowType.CALL_CENTER_DIRECT.value:
                return UserRole.CALL_CENTER_SUPERVISOR.value
        
        # For client initiated requests, use workflow definition initial role
        if workflow_type == WorkflowType.CONNECTION_REQUEST.value:
            return UserRole.MANAGER.value  # Client connection requests also go to manager
        elif workflow_type == WorkflowType.TECHNICAL_SERVICE.value:
            return UserRole.CONTROLLER.value  # Client technical requests go to controller
        elif workflow_type == WorkflowType.CALL_CENTER_DIRECT.value:
            return UserRole.CALL_CENTER_SUPERVISOR.value
        else:
            return UserRole.MANAGER.value  # Default fallback
    
    async def _get_request_internal(self, conn, request_id: str) -> Optional[ServiceRequest]:
        """Internal method to get request using existing connection"""
        query = """
        SELECT id, workflow_type, client_id, role_current , current_status,
               created_at, updated_at, priority, description, location,
               contact_info, state_data, equipment_used, inventory_updated,
               completion_rating, feedback_comments, created_by_staff,
               staff_creator_id, staff_creator_role, creation_source, client_notified_at
        FROM service_requests
        WHERE id = $1
        """
        
        row = await conn.fetchrow(query, request_id)
        
        if row:
            return ServiceRequest(
                id=row['id'],
                workflow_type=row['workflow_type'],
                client_id=row['client_id'],
                role_current =row['role_current '],
                current_status=row['current_status'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                priority=row['priority'],
                description=row['description'],
                location=row['location'],
                contact_info=json.loads(row['contact_info']) if row['contact_info'] else {},
                state_data=json.loads(row['state_data']) if row['state_data'] else {},
                equipment_used=json.loads(row['equipment_used']) if row['equipment_used'] else [],
                inventory_updated=row['inventory_updated'],
                completion_rating=row['completion_rating'],
                feedback_comments=row['feedback_comments'],
                created_by_staff=row['created_by_staff'],
                staff_creator_id=row['staff_creator_id'],
                staff_creator_role=row['staff_creator_role'],
                creation_source=row['creation_source'],
                client_notified_at=row['client_notified_at']
            )
        
        return None
    
    async def _record_transition(self, conn, request_id: str, from_role: str, to_role: str,
                               action: str, actor_id: int, transition_data: Dict[str, Any] = None,
                               comments: str = None):
        """Internal method to record state transition using existing connection"""
        query = """
        INSERT INTO state_transitions (
            request_id, from_role, to_role, action, actor_id,
            transition_data, comments, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        await conn.execute(
            query,
            request_id,
            from_role,
            to_role,
            action,
            actor_id,
            json.dumps(transition_data or {}),
            comments,
            datetime.now()
        )
    
    async def get_request(self, request_id: str) -> Optional[ServiceRequest]:
        """Gets request by ID"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return None
            
        try:
            async with pool.acquire() as conn:
                return await self._get_request_internal(conn, request_id)
                
        except Exception as e:
            logger.error(f"Error getting request: {e}", exc_info=True)
            return None
    
    async def get_requests_by_role(self, role: str, status_filter: str = None) -> List[ServiceRequest]:
        """Returns requests assigned to specific role with role-based filtering"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return []
            
        try:
            async with pool.acquire() as conn:
                base_query = """
                SELECT id, workflow_type, client_id, role_current , current_status,
                       created_at, updated_at, priority, description, location,
                       contact_info, state_data, equipment_used, inventory_updated,
                       completion_rating, feedback_comments, created_by_staff,
                       staff_creator_id, staff_creator_role, creation_source, client_notified_at
                FROM service_requests
                WHERE role_current = $1
                """
                
                params = [role]
                
                if status_filter:
                    base_query += " AND current_status = $2"
                    params.append(status_filter)
                
                base_query += " ORDER BY priority DESC, created_at DESC"
                
                rows = await conn.fetch(base_query, *params)
                
                requests = []
                for row in rows:
                    requests.append(ServiceRequest(
                        id=row['id'],
                        workflow_type=row['workflow_type'],
                        client_id=row['client_id'],
                        role_current =row['role_current '],
                        current_status=row['current_status'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        priority=row['priority'],
                        description=row['description'],
                        location=row['location'],
                        contact_info=json.loads(row['contact_info']) if row['contact_info'] else {},
                        state_data=json.loads(row['state_data']) if row['state_data'] else {},
                        equipment_used=json.loads(row['equipment_used']) if row['equipment_used'] else [],
                        inventory_updated=row['inventory_updated'],
                        completion_rating=row['completion_rating'],
                        feedback_comments=row['feedback_comments'],
                        created_by_staff=row['created_by_staff'],
                        staff_creator_id=row['staff_creator_id'],
                        staff_creator_role=row['staff_creator_role'],
                        creation_source=row['creation_source'],
                        client_notified_at=row['client_notified_at']
                    ))
                
                logger.info(f"Retrieved {len(requests)} requests for role {role}")
                return requests
                
        except Exception as e:
            logger.error(f"Error getting requests by role: {e}", exc_info=True)
            return []
    
    async def record_state_transition(self, request_id: str, from_role: str, to_role: str, 
                                    action: str, actor_id: int, transition_data: Dict[str, Any] = None,
                                    comments: str = None) -> bool:
        """Records state transition with audit trail"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
            
        try:
            async with pool.acquire() as conn:
                await self._record_transition(
                    conn, request_id, from_role, to_role, action, 
                    actor_id, transition_data, comments
                )
                
                logger.info(f"Recorded state transition for request {request_id}: {from_role} -> {to_role}")
                return True
                
        except Exception as e:
            logger.error(f"Error recording state transition: {e}", exc_info=True)
            return False
    
    async def add_state_transition(self, transition: StateTransition) -> bool:
        """Adds state transition record (legacy method for compatibility)"""
        return await self.record_state_transition(
            transition.request_id,
            transition.from_role,
            transition.to_role,
            transition.action,
            transition.actor_id,
            transition.transition_data,
            transition.comments
        )
    
    async def get_request_history(self, request_id: str) -> List[StateTransition]:
        """Returns complete request history with audit trail"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return []
            
        try:
            async with pool.acquire() as conn:
                query = """
                SELECT id, request_id, from_role, to_role, action, actor_id,
                       transition_data, comments, created_at
                FROM state_transitions
                WHERE request_id = $1
                ORDER BY created_at ASC
                """
                
                rows = await conn.fetch(query, request_id)
                
                transitions = []
                for row in rows:
                    transitions.append(StateTransition(
                        id=row['id'],
                        request_id=row['request_id'],
                        from_role=row['from_role'],
                        to_role=row['to_role'],
                        action=row['action'],
                        actor_id=row['actor_id'],
                        transition_data=json.loads(row['transition_data']) if row['transition_data'] else {},
                        comments=row['comments'],
                        created_at=row['created_at']
                    ))
                
                logger.info(f"Retrieved {len(transitions)} transitions for request {request_id}")
                return transitions
                
        except Exception as e:
            logger.error(f"Error getting request history: {e}", exc_info=True)
            return []
    
    async def get_requests_by_client(self, client_id: int) -> List[ServiceRequest]:
        """Returns requests for specific client with history tracking"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return []
            
        try:
            async with pool.acquire() as conn:
                query = """
                SELECT id, workflow_type, client_id, role_current , current_status,
                       created_at, updated_at, priority, description, location,
                       contact_info, state_data, equipment_used, inventory_updated,
                       completion_rating, feedback_comments
                FROM service_requests
                WHERE client_id = $1
                ORDER BY created_at DESC
                """
                
                rows = await conn.fetch(query, client_id)
                
                requests = []
                for row in rows:
                    requests.append(ServiceRequest(
                        id=row['id'],
                        workflow_type=row['workflow_type'],
                        client_id=row['client_id'],
                        role_current =row['role_current '],
                        current_status=row['current_status'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        priority=row['priority'],
                        description=row['description'],
                        location=row['location'],
                        contact_info=json.loads(row['contact_info']) if row['contact_info'] else {},
                        state_data=json.loads(row['state_data']) if row['state_data'] else {},
                        equipment_used=json.loads(row['equipment_used']) if row['equipment_used'] else [],
                        inventory_updated=row['inventory_updated'],
                        completion_rating=row['completion_rating'],
                        feedback_comments=row['feedback_comments']
                    ))
                
                logger.info(f"Retrieved {len(requests)} requests for client {client_id}")
                return requests
                
        except Exception as e:
            logger.error(f"Error getting requests by client: {e}", exc_info=True)
            return []
    
    async def get_requests_by_status(self, status: str) -> List[ServiceRequest]:
        """Returns requests filtered by status"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return []
            
        try:
            async with pool.acquire() as conn:
                query = """
                SELECT id, workflow_type, client_id, role_current , current_status,
                       created_at, updated_at, priority, description, location,
                       contact_info, state_data, equipment_used, inventory_updated,
                       completion_rating, feedback_comments
                FROM service_requests
                WHERE current_status = $1
                ORDER BY priority DESC, created_at DESC
                """
                
                rows = await conn.fetch(query, status)
                
                requests = []
                for row in rows:
                    requests.append(ServiceRequest(
                        id=row['id'],
                        workflow_type=row['workflow_type'],
                        client_id=row['client_id'],
                        role_current =row['role_current '],
                        current_status=row['current_status'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        priority=row['priority'],
                        description=row['description'],
                        location=row['location'],
                        contact_info=json.loads(row['contact_info']) if row['contact_info'] else {},
                        state_data=json.loads(row['state_data']) if row['state_data'] else {},
                        equipment_used=json.loads(row['equipment_used']) if row['equipment_used'] else [],
                        inventory_updated=row['inventory_updated'],
                        completion_rating=row['completion_rating'],
                        feedback_comments=row['feedback_comments']
                    ))
                
                logger.info(f"Retrieved {len(requests)} requests with status {status}")
                return requests
                
        except Exception as e:
            logger.error(f"Error getting requests by status: {e}", exc_info=True)
            return []
    
    async def delete_request(self, request_id: str) -> bool:
        """Deletes a request and its history (for testing/cleanup)"""
        pool = self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False
            
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Delete transitions first (foreign key constraint)
                    await conn.execute("DELETE FROM state_transitions WHERE request_id = $1", request_id)
                    
                    # Delete the request
                    result = await conn.execute("DELETE FROM service_requests WHERE id = $1", request_id)
                    
                    logger.info(f"Deleted request {request_id} and its history")
                    return result == "DELETE 1"
                
        except Exception as e:
            logger.error(f"Error deleting request: {e}", exc_info=True)
            return False


class StateManagerFactory:
    """Factory for creating state manager instances"""
    
    @staticmethod
    def create_state_manager() -> StateManager:
        """Creates a new state manager instance"""
        return StateManager()