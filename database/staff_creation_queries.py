"""
Database queries for staff creation tracking functionality.
Supports Requirements 1.1, 1.2, 1.3 from the multi-role application creation spec.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from database.models import (
    ServiceRequest, ClientSelectionData, StaffApplicationAudit,
    validate_staff_creation_data, validate_client_selection_data
)
from utils.logger import setup_module_logger

logger = setup_module_logger("staff_creation_queries")

# ServiceRequest staff tracking queries

async def create_staff_service_request(service_request: ServiceRequest, pool: asyncpg.Pool = None) -> Optional[str]:
    """
    Create a new service request with staff creation tracking.
    
    Args:
        service_request: ServiceRequest object with staff tracking fields
        pool: Database connection pool
        
    Returns:
        str: Request ID if successful, None if failed
    """
    # Validate staff creation data
    validation_errors = validate_staff_creation_data(service_request)
    if validation_errors:
        logger.error(f"Validation errors for staff service request: {validation_errors}")
        return None
    
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            INSERT INTO service_requests (
                id, workflow_type, client_id, role_current, current_status,
                priority, description, location, contact_info, state_data,
                equipment_used, inventory_updated, completion_rating, feedback_comments,
                created_by_staff, staff_creator_id, staff_creator_role, 
                creation_source, client_notified_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
            ) RETURNING id
            """
            
            result = await conn.fetchval(query,
                service_request.id,
                service_request.workflow_type,
                service_request.client_id,
                service_request.role_current,
                service_request.current_status,
                service_request.priority,
                service_request.description,
                service_request.location,
                json.dumps(service_request.contact_info),
                json.dumps(service_request.state_data),
                json.dumps(service_request.equipment_used),
                service_request.inventory_updated,
                service_request.completion_rating,
                service_request.feedback_comments,
                service_request.created_by_staff,
                service_request.staff_creator_id,
                service_request.staff_creator_role,
                service_request.creation_source,
                service_request.client_notified_at
            )
            
            logger.info(f"Created staff service request: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error creating staff service request: {e}")
        return None

async def get_staff_created_requests(staff_id: int, limit: int = 50, pool: asyncpg.Pool = None) -> List[ServiceRequest]:
    """
    Get service requests created by a specific staff member.
    
    Args:
        staff_id: ID of the staff member
        limit: Maximum number of requests to return
        pool: Database connection pool
        
    Returns:
        List[ServiceRequest]: List of service requests
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            SELECT * FROM service_requests 
            WHERE created_by_staff = true AND staff_creator_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """
            
            rows = await conn.fetch(query, staff_id, limit)
            
            requests = []
            for row in rows:
                row_dict = dict(row)
                # Parse JSON fields
                if row_dict.get('contact_info'):
                    row_dict['contact_info'] = json.loads(row_dict['contact_info']) if isinstance(row_dict['contact_info'], str) else row_dict['contact_info']
                if row_dict.get('state_data'):
                    row_dict['state_data'] = json.loads(row_dict['state_data']) if isinstance(row_dict['state_data'], str) else row_dict['state_data']
                if row_dict.get('equipment_used'):
                    row_dict['equipment_used'] = json.loads(row_dict['equipment_used']) if isinstance(row_dict['equipment_used'], str) else row_dict['equipment_used']
                
                requests.append(ServiceRequest.from_dict(row_dict))
            
            return requests
            
    except Exception as e:
        logger.error(f"Error getting staff created requests: {e}")
        return []

async def update_client_notification_status(request_id: str, notified_at: datetime, pool: asyncpg.Pool = None) -> bool:
    """
    Update client notification timestamp for a staff-created request.
    
    Args:
        request_id: Service request ID
        notified_at: Timestamp when client was notified
        pool: Database connection pool
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            UPDATE service_requests 
            SET client_notified_at = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2 AND created_by_staff = true
            """
            
            result = await conn.execute(query, notified_at, request_id)
            
            if result == "UPDATE 1":
                logger.info(f"Updated client notification for request: {request_id}")
                return True
            else:
                logger.warning(f"No staff-created request found with ID: {request_id}")
                return False
                
    except Exception as e:
        logger.error(f"Error updating client notification status: {e}")
        return False

# ClientSelectionData queries

async def create_client_selection_data(client_data: ClientSelectionData, pool: asyncpg.Pool = None) -> Optional[int]:
    """
    Create client selection data for staff application creation.
    
    Args:
        client_data: ClientSelectionData object
        pool: Database connection pool
        
    Returns:
        int: Selection data ID if successful, None if failed
    """
    # Validate client selection data
    validation_errors = validate_client_selection_data(client_data)
    if validation_errors:
        logger.error(f"Validation errors for client selection data: {validation_errors}")
        return None
    
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            INSERT INTO client_selection_data (
                search_method, search_value, client_id, new_client_data, verified
            ) VALUES ($1, $2, $3, $4, $5) RETURNING id
            """
            
            result = await conn.fetchval(query,
                client_data.search_method,
                client_data.search_value,
                client_data.client_id,
                json.dumps(client_data.new_client_data),
                client_data.verified
            )
            
            logger.info(f"Created client selection data: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error creating client selection data: {e}")
        return None

async def get_client_selection_data(selection_id: int, pool: asyncpg.Pool = None) -> Optional[ClientSelectionData]:
    """
    Get client selection data by ID.
    
    Args:
        selection_id: Selection data ID
        pool: Database connection pool
        
    Returns:
        ClientSelectionData: Selection data if found, None otherwise
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = "SELECT * FROM client_selection_data WHERE id = $1"
            row = await conn.fetchrow(query, selection_id)
            
            if row:
                row_dict = dict(row)
                # Parse JSON field
                if row_dict.get('new_client_data'):
                    row_dict['new_client_data'] = json.loads(row_dict['new_client_data']) if isinstance(row_dict['new_client_data'], str) else row_dict['new_client_data']
                
                return ClientSelectionData.from_dict(row_dict)
            return None
            
    except Exception as e:
        logger.error(f"Error getting client selection data: {e}")
        return None

async def update_client_selection_verification(selection_id: int, verified: bool, client_id: Optional[int] = None, pool: asyncpg.Pool = None) -> bool:
    """
    Update client selection verification status.
    
    Args:
        selection_id: Selection data ID
        verified: Verification status
        client_id: Client ID if verified
        pool: Database connection pool
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            UPDATE client_selection_data 
            SET verified = $1, client_id = $2
            WHERE id = $3
            """
            
            result = await conn.execute(query, verified, client_id, selection_id)
            
            if result == "UPDATE 1":
                logger.info(f"Updated client selection verification: {selection_id}")
                return True
            return False
            
    except Exception as e:
        logger.error(f"Error updating client selection verification: {e}")
        return False

async def cleanup_old_client_selection_data(days_old: int = 7, pool: asyncpg.Pool = None) -> int:
    """
    Clean up old client selection data.
    
    Args:
        days_old: Number of days old to consider for cleanup
        pool: Database connection pool
        
    Returns:
        int: Number of records deleted
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            DELETE FROM client_selection_data 
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """
            
            result = await conn.execute(query.replace('%s', str(days_old)))
            deleted_count = int(result.split()[-1]) if result.startswith("DELETE") else 0
            
            logger.info(f"Cleaned up {deleted_count} old client selection records")
            return deleted_count
            
    except Exception as e:
        logger.error(f"Error cleaning up client selection data: {e}")
        return 0

# StaffApplicationAudit queries

async def create_staff_application_audit(audit: StaffApplicationAudit, pool: asyncpg.Pool = None) -> Optional[int]:
    """
    Create staff application audit record.
    
    Args:
        audit: StaffApplicationAudit object
        pool: Database connection pool
        
    Returns:
        int: Audit ID if successful, None if failed
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            INSERT INTO staff_application_audit (
                application_id, creator_id, creator_role, client_id, application_type,
                creation_timestamp, client_notified, client_notified_at,
                workflow_initiated, workflow_initiated_at, metadata,
                ip_address, user_agent, session_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
            ) RETURNING id
            """
            
            result = await conn.fetchval(query,
                audit.application_id,
                audit.creator_id,
                audit.creator_role,
                audit.client_id,
                audit.application_type,
                audit.creation_timestamp,
                audit.client_notified,
                audit.client_notified_at,
                audit.workflow_initiated,
                audit.workflow_initiated_at,
                json.dumps(audit.metadata),
                audit.ip_address,
                audit.user_agent,
                audit.session_id
            )
            
            logger.info(f"Created staff application audit: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error creating staff application audit: {e}")
        return None

async def update_audit_notification_status(audit_id: int, notified: bool, notified_at: Optional[datetime] = None, pool: asyncpg.Pool = None) -> bool:
    """
    Update audit record notification status.
    
    Args:
        audit_id: Audit record ID
        notified: Notification status
        notified_at: Notification timestamp
        pool: Database connection pool
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            UPDATE staff_application_audit 
            SET client_notified = $1, client_notified_at = $2
            WHERE id = $3
            """
            
            result = await conn.execute(query, notified, notified_at, audit_id)
            
            if result == "UPDATE 1":
                logger.info(f"Updated audit notification status: {audit_id}")
                return True
            return False
            
    except Exception as e:
        logger.error(f"Error updating audit notification status: {e}")
        return False

async def update_audit_workflow_status(audit_id: int, initiated: bool, initiated_at: Optional[datetime] = None, pool: asyncpg.Pool = None) -> bool:
    """
    Update audit record workflow initiation status.
    
    Args:
        audit_id: Audit record ID
        initiated: Workflow initiation status
        initiated_at: Workflow initiation timestamp
        pool: Database connection pool
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = """
            UPDATE staff_application_audit 
            SET workflow_initiated = $1, workflow_initiated_at = $2
            WHERE id = $3
            """
            
            result = await conn.execute(query, initiated, initiated_at, audit_id)
            
            if result == "UPDATE 1":
                logger.info(f"Updated audit workflow status: {audit_id}")
                return True
            return False
            
    except Exception as e:
        logger.error(f"Error updating audit workflow status: {e}")
        return False

async def get_staff_application_audits(creator_id: Optional[int] = None, 
                                     client_id: Optional[int] = None,
                                     application_type: Optional[str] = None,
                                     limit: int = 100,
                                     pool: asyncpg.Pool = None) -> List[StaffApplicationAudit]:
    """
    Get staff application audit records with optional filters.
    
    Args:
        creator_id: Filter by creator ID
        client_id: Filter by client ID
        application_type: Filter by application type
        limit: Maximum number of records to return
        pool: Database connection pool
        
    Returns:
        List[StaffApplicationAudit]: List of audit records
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            conditions = []
            params = []
            param_count = 0
            
            if creator_id:
                param_count += 1
                conditions.append(f"creator_id = ${param_count}")
                params.append(creator_id)
            
            if client_id:
                param_count += 1
                conditions.append(f"client_id = ${param_count}")
                params.append(client_id)
            
            if application_type:
                param_count += 1
                conditions.append(f"application_type = ${param_count}")
                params.append(application_type)
            
            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
            
            param_count += 1
            query = f"""
            SELECT * FROM staff_application_audit 
            {where_clause}
            ORDER BY creation_timestamp DESC
            LIMIT ${param_count}
            """
            
            params.append(limit)
            rows = await conn.fetch(query, *params)
            
            audits = []
            for row in rows:
                row_dict = dict(row)
                # Parse JSON field
                if row_dict.get('metadata'):
                    row_dict['metadata'] = json.loads(row_dict['metadata']) if isinstance(row_dict['metadata'], str) else row_dict['metadata']
                
                audits.append(StaffApplicationAudit.from_dict(row_dict))
            
            return audits
            
    except Exception as e:
        logger.error(f"Error getting staff application audits: {e}")
        return []

async def get_audit_by_application_id(application_id: str, pool: asyncpg.Pool = None) -> Optional[StaffApplicationAudit]:
    """
    Get audit record by application ID.
    
    Args:
        application_id: Service request ID
        pool: Database connection pool
        
    Returns:
        StaffApplicationAudit: Audit record if found, None otherwise
    """
    if not pool:
        from loader import bot
        pool = bot.db
    
    try:
        async with pool.acquire() as conn:
            query = "SELECT * FROM staff_application_audit WHERE application_id = $1"
            row = await conn.fetchrow(query, application_id)
            
            if row:
                row_dict = dict(row)
                # Parse JSON field
                if row_dict.get('metadata'):
                    row_dict['metadata'] = json.loads(row_dict['metadata']) if isinstance(row_dict['metadata'], str) else row_dict['metadata']
                
                return StaffApplicationAudit.from_dict(row_dict)
            return None
            
    except Exception as e:
        logger.error(f"Error getting audit by application ID: {e}")
        return None