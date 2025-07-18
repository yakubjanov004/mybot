"""
Inbox Service for role-based application management.

This service provides functionality for:
- Retrieving applications assigned to specific roles
- Transferring applications between roles
- Managing inbox messages and notifications
- Handling role-based filtering and pagination
"""

import asyncpg
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, field
from utils.logger import setup_module_logger

logger = setup_module_logger("inbox_service")

@dataclass
class InboxMessage:
    """Data model for inbox messages"""
    id: Optional[int] = None
    application_id: str = None
    application_type: str = None  # 'zayavka', 'service_request'
    assigned_role: str = None
    message_type: str = 'application'
    title: Optional[str] = None
    description: Optional[str] = None
    priority: str = 'medium'
    is_read: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'application_id': self.application_id,
            'application_type': self.application_type,
            'assigned_role': self.assigned_role,
            'message_type': self.message_type,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'is_read': self.is_read,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InboxMessage':
        return cls(**data)

@dataclass
class ApplicationTransfer:
    """Data model for application transfers"""
    id: Optional[int] = None
    application_id: str = None
    application_type: str = None
    from_role: Optional[str] = None
    to_role: str = None
    transferred_by: int = None
    transfer_reason: Optional[str] = None
    transfer_notes: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'application_id': self.application_id,
            'application_type': self.application_type,
            'from_role': self.from_role,
            'to_role': self.to_role,
            'transferred_by': self.transferred_by,
            'transfer_reason': self.transfer_reason,
            'transfer_notes': self.transfer_notes,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationTransfer':
        return cls(**data)

class InboxService:
    """Service class for inbox functionality"""
    
    # Valid roles for inbox system
    VALID_ROLES = [
        'manager', 'junior_manager', 'technician', 'warehouse',
        'call_center', 'call_center_supervisor', 'controller'
    ]
    
    # Valid application types
    VALID_APPLICATION_TYPES = ['zayavka', 'service_request']
    
    # Valid message types
    VALID_MESSAGE_TYPES = ['application', 'transfer', 'notification', 'reminder']
    
    # Valid priorities
    VALID_PRIORITIES = ['low', 'medium', 'high', 'urgent']

    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        """Initialize InboxService with database pool"""
        self.pool = pool

    def _get_pool(self) -> asyncpg.Pool:
        """Get database pool, fallback to global pool if not provided"""
        if self.pool:
            return self.pool
        
        # Fallback to global pool from loader
        try:
            from loader import bot
            return bot.db
        except ImportError:
            raise RuntimeError("Database pool not available. Initialize InboxService with a pool or ensure loader.bot.db is available.")

    async def get_role_applications(
        self, 
        role: str, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20,
        application_type: Optional[str] = None,
        priority: Optional[str] = None,
        include_read: bool = True
    ) -> Dict[str, Any]:
        """
        Get applications assigned to a specific role with pagination and filtering.
        
        Args:
            role: Role to get applications for
            user_id: User ID requesting the applications (for access control)
            page: Page number (1-based)
            page_size: Number of applications per page
            application_type: Filter by application type ('zayavka', 'service_request', or None for all)
            priority: Filter by priority ('low', 'medium', 'high', 'urgent', or None for all)
            include_read: Whether to include read messages
            
        Returns:
            Dict containing applications, pagination info, and metadata
        """
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {self.VALID_ROLES}")
        
        if application_type and application_type not in self.VALID_APPLICATION_TYPES:
            raise ValueError(f"Invalid application_type: {application_type}. Must be one of {self.VALID_APPLICATION_TYPES}")
        
        if priority and priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {self.VALID_PRIORITIES}")

        pool = self._get_pool()
        offset = (page - 1) * page_size
        
        # Build WHERE conditions
        where_conditions = ["assigned_role = $1"]
        params = [role]
        param_count = 2
        
        if application_type:
            where_conditions.append(f"application_type = ${param_count}")
            params.append(application_type)
            param_count += 1
        
        if priority:
            where_conditions.append(f"priority = ${param_count}")
            params.append(priority)
            param_count += 1
        
        if not include_read:
            where_conditions.append(f"is_read = ${param_count}")
            params.append(False)
            param_count += 1

        where_clause = " AND ".join(where_conditions)
        
        # Query for applications with details
        applications_query = f"""
            WITH inbox_apps AS (
                SELECT DISTINCT 
                    im.application_id,
                    im.application_type,
                    im.assigned_role,
                    im.priority,
                    im.is_read,
                    im.created_at as inbox_created_at,
                    im.updated_at as inbox_updated_at
                FROM inbox_messages im
                WHERE {where_clause}
            )
            SELECT 
                ia.*,
                CASE 
                    WHEN ia.application_type = 'zayavka' THEN
                        (SELECT row_to_json(z_data) FROM (
                            SELECT 
                                z.id,
                                z.description,
                                z.address,
                                z.phone,
                                z.status,
                                z.priority as app_priority,
                                z.created_at,
                                z.updated_at,
                                u.full_name as client_name,
                                u.phone_number as client_phone,
                                u.language as client_language
                            FROM zayavki z
                            LEFT JOIN users u ON z.user_id = u.id
                            WHERE z.id::text = ia.application_id
                        ) z_data)
                    WHEN ia.application_type = 'service_request' THEN
                        (SELECT row_to_json(sr_data) FROM (
                            SELECT 
                                sr.id,
                                sr.workflow_type,
                                sr.current_status,
                                sr.priority as app_priority,
                                sr.description,
                                sr.location,
                                sr.contact_info,
                                sr.created_at,
                                sr.updated_at,
                                u.full_name as client_name,
                                u.phone_number as client_phone,
                                u.language as client_language
                            FROM service_requests sr
                            LEFT JOIN users u ON sr.client_id = u.id
                            WHERE sr.id = ia.application_id
                        ) sr_data)
                END as application_details
            FROM inbox_apps ia
            ORDER BY ia.inbox_created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        
        # Count query for pagination
        count_query = f"""
            SELECT COUNT(DISTINCT application_id) 
            FROM inbox_messages 
            WHERE {where_clause}
        """
        
        params.extend([page_size, offset])
        
        try:
            async with pool.acquire() as conn:
                # Get applications
                applications_result = await conn.fetch(applications_query, *params[:-2])
                
                # Get total count
                total_count = await conn.fetchval(count_query, *params[:-2])
                
                # Process results
                applications = []
                for row in applications_result:
                    app_data = dict(row)
                    
                    # Parse application details JSON
                    if app_data['application_details']:
                        app_data['application_details'] = dict(app_data['application_details'])
                    
                    applications.append(app_data)
                
                # Calculate pagination info
                total_pages = (total_count + page_size - 1) // page_size
                has_next = page < total_pages
                has_prev = page > 1
                
                return {
                    'applications': applications,
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_count': total_count,
                        'total_pages': total_pages,
                        'has_next': has_next,
                        'has_prev': has_prev
                    },
                    'filters': {
                        'role': role,
                        'application_type': application_type,
                        'priority': priority,
                        'include_read': include_read
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting role applications for role {role}: {str(e)}", exc_info=True)
            raise

    async def get_application_details(
        self, 
        application_id: str, 
        application_type: str,
        user_role: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific application.
        
        Args:
            application_id: ID of the application
            application_type: Type of application ('zayavka' or 'service_request')
            user_role: Role of the user requesting details (for access control)
            
        Returns:
            Application details or None if not found/accessible
        """
        if application_type not in self.VALID_APPLICATION_TYPES:
            raise ValueError(f"Invalid application_type: {application_type}")
        
        if user_role not in self.VALID_ROLES:
            raise ValueError(f"Invalid user_role: {user_role}")

        pool = self._get_pool()
        
        try:
            async with pool.acquire() as conn:
                if application_type == 'zayavka':
                    query = """
                        SELECT 
                            z.*,
                            u.full_name as client_name,
                            u.phone_number as client_phone,
                            u.telegram_id as client_telegram_id,
                            u.language as client_language,
                            u.address as client_address,
                            t.full_name as technician_name,
                            t.telegram_id as technician_telegram_id
                        FROM zayavki z
                        LEFT JOIN users u ON z.user_id = u.id
                        LEFT JOIN users t ON z.technician_id = t.id
                        WHERE z.id = $1 AND (z.assigned_role = $2 OR z.assigned_role IS NULL)
                    """
                    result = await conn.fetchrow(query, int(application_id), user_role)
                    
                elif application_type == 'service_request':
                    query = """
                        SELECT 
                            sr.*,
                            u.full_name as client_name,
                            u.phone_number as client_phone,
                            u.telegram_id as client_telegram_id,
                            u.language as client_language,
                            u.address as client_address
                        FROM service_requests sr
                        LEFT JOIN users u ON sr.client_id = u.id
                        WHERE sr.id = $1 AND (sr.role_current = $2 OR sr.role_current IS NULL)
                    """
                    result = await conn.fetchrow(query, application_id, user_role)
                
                if result:
                    app_details = dict(result)
                    
                    # Parse JSON fields for service_requests
                    if application_type == 'service_request':
                        for json_field in ['contact_info', 'state_data', 'equipment_used']:
                            if app_details.get(json_field):
                                try:
                                    app_details[json_field] = json.loads(app_details[json_field]) if isinstance(app_details[json_field], str) else app_details[json_field]
                                except (json.JSONDecodeError, TypeError):
                                    app_details[json_field] = {}
                    
                    return app_details
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting application details for {application_type} {application_id}: {str(e)}", exc_info=True)
            raise

    async def get_transfer_options(self, current_role: str, application_type: str) -> List[str]:
        """
        Get valid transfer options for a role and application type.
        
        Args:
            current_role: Current role holding the application
            application_type: Type of application
            
        Returns:
            List of valid target roles
        """
        if current_role not in self.VALID_ROLES:
            raise ValueError(f"Invalid current_role: {current_role}")
        
        if application_type not in self.VALID_APPLICATION_TYPES:
            raise ValueError(f"Invalid application_type: {application_type}")

        # Define transfer rules based on workflow logic
        transfer_rules = {
            'zayavka': {
                'manager': ['junior_manager', 'controller', 'call_center'],
                'junior_manager': ['manager', 'controller', 'call_center'],
                'controller': ['technician', 'manager'],
                'technician': ['warehouse', 'controller', 'manager'],
                'warehouse': ['technician', 'controller'],
                'call_center': ['call_center_supervisor', 'manager'],
                'call_center_supervisor': ['call_center', 'manager']
            },
            'service_request': {
                'manager': ['junior_manager', 'controller', 'technician'],
                'junior_manager': ['manager', 'controller', 'technician'],
                'controller': ['technician', 'manager'],
                'technician': ['warehouse', 'controller', 'manager'],
                'warehouse': ['technician', 'controller'],
                'call_center': ['call_center_supervisor', 'manager'],
                'call_center_supervisor': ['call_center', 'manager']
            }
        }
        
        return transfer_rules.get(application_type, {}).get(current_role, [])

    async def create_inbox_message(
        self,
        application_id: str,
        application_type: str,
        assigned_role: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        message_type: str = 'application',
        priority: str = 'medium'
    ) -> bool:
        """
        Create a new inbox message for an application.
        
        Args:
            application_id: ID of the application
            application_type: Type of application
            assigned_role: Role to assign the message to
            title: Message title
            description: Message description
            message_type: Type of message
            priority: Message priority
            
        Returns:
            True if message was created successfully
        """
        if application_type not in self.VALID_APPLICATION_TYPES:
            raise ValueError(f"Invalid application_type: {application_type}")
        
        if assigned_role not in self.VALID_ROLES:
            raise ValueError(f"Invalid assigned_role: {assigned_role}")
        
        if message_type not in self.VALID_MESSAGE_TYPES:
            raise ValueError(f"Invalid message_type: {message_type}")
        
        if priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}")

        pool = self._get_pool()
        
        query = """
            INSERT INTO inbox_messages (
                application_id, application_type, assigned_role, 
                title, description, message_type, priority
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        
        try:
            async with pool.acquire() as conn:
                message_id = await conn.fetchval(
                    query, 
                    application_id, application_type, assigned_role,
                    title, description, message_type, priority
                )
                
                if message_id:
                    logger.info(f"Created inbox message {message_id} for {application_type} {application_id} assigned to {assigned_role}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error creating inbox message: {str(e)}", exc_info=True)
            return False

    async def mark_as_read(self, message_id: int, user_id: int) -> bool:
        """
        Mark an inbox message as read.
        
        Args:
            message_id: ID of the message to mark as read
            user_id: ID of the user marking the message as read
            
        Returns:
            True if message was marked as read successfully
        """
        pool = self._get_pool()
        
        query = """
            UPDATE inbox_messages 
            SET is_read = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING id
        """
        
        try:
            async with pool.acquire() as conn:
                result = await conn.fetchval(query, message_id)
                
                if result:
                    logger.info(f"Marked inbox message {message_id} as read by user {user_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}", exc_info=True)
            return False

    async def cleanup_old_messages(self, days_old: int = 30) -> int:
        """
        Clean up old read messages to prevent database bloat.
        
        Args:
            days_old: Number of days after which read messages should be cleaned up
            
        Returns:
            Number of messages cleaned up
        """
        pool = self._get_pool()
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = """
            DELETE FROM inbox_messages 
            WHERE is_read = TRUE 
            AND updated_at < $1
            AND message_type IN ('notification', 'reminder')
        """
        
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(query, cutoff_date)
                
                # Extract number of deleted rows from result
                deleted_count = int(result.split()[-1]) if result and result.split() else 0
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old inbox messages")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {str(e)}", exc_info=True)
            return 0

    async def get_unread_count(self, role: str) -> int:
        """
        Get count of unread messages for a role.
        
        Args:
            role: Role to get unread count for
            
        Returns:
            Number of unread messages
        """
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")

        pool = self._get_pool()
        
        query = """
            SELECT COUNT(*) 
            FROM inbox_messages 
            WHERE assigned_role = $1 AND is_read = FALSE
        """
        
        try:
            async with pool.acquire() as conn:
                count = await conn.fetchval(query, role)
                return count or 0
                
        except Exception as e:
            logger.error(f"Error getting unread count for role {role}: {str(e)}", exc_info=True)
            return 0


class ApplicationTransferService:
    """Service class for handling application transfers between roles"""
    
    def __init__(self, pool: Optional[asyncpg.Pool] = None):
        """Initialize ApplicationTransferService with database pool"""
        self.pool = pool
        self.inbox_service = InboxService(pool)

    def _get_pool(self) -> asyncpg.Pool:
        """Get database pool, fallback to global pool if not provided"""
        if self.pool:
            return self.pool
        
        # Fallback to global pool from loader
        try:
            from loader import bot
            return bot.db
        except ImportError:
            raise RuntimeError("Database pool not available. Initialize ApplicationTransferService with a pool or ensure loader.bot.db is available.")

    async def validate_transfer(
        self, 
        application_id: str, 
        application_type: str,
        from_role: str, 
        to_role: str,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        Validate if an application transfer is allowed.
        
        Args:
            application_id: ID of the application to transfer
            application_type: Type of application ('zayavka' or 'service_request')
            from_role: Current role holding the application
            to_role: Target role for transfer
            user_id: ID of user requesting the transfer
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate roles
        if from_role not in InboxService.VALID_ROLES:
            return False, f"Invalid from_role: {from_role}"
        
        if to_role not in InboxService.VALID_ROLES:
            return False, f"Invalid to_role: {to_role}"
        
        if application_type not in InboxService.VALID_APPLICATION_TYPES:
            return False, f"Invalid application_type: {application_type}"
        
        # Check if transfer is to the same role
        if from_role == to_role:
            return False, "Cannot transfer to the same role"
        
        # Check if target role is valid for this application type
        valid_targets = await self.inbox_service.get_transfer_options(from_role, application_type)
        if to_role not in valid_targets:
            return False, f"Transfer from {from_role} to {to_role} is not allowed for {application_type}"
        
        # Verify application exists and is currently assigned to from_role
        pool = self._get_pool()
        
        try:
            async with pool.acquire() as conn:
                if application_type == 'zayavka':
                    query = """
                        SELECT id, assigned_role, status 
                        FROM zayavki 
                        WHERE id = $1
                    """
                    result = await conn.fetchrow(query, int(application_id))
                    
                elif application_type == 'service_request':
                    query = """
                        SELECT id, role_current, current_status 
                        FROM service_requests 
                        WHERE id = $1
                    """
                    result = await conn.fetchrow(query, application_id)
                
                if not result:
                    return False, f"Application {application_id} not found"
                
                # Check current role assignment
                current_role = result.get('assigned_role') or result.get('role_current')
                if current_role != from_role:
                    return False, f"Application is currently assigned to {current_role}, not {from_role}"
                
                # Check if application is in a transferable state
                status = result.get('status') or result.get('current_status')
                non_transferable_statuses = ['completed', 'cancelled', 'closed']
                if status in non_transferable_statuses:
                    return False, f"Cannot transfer application with status: {status}"
                
                return True, "Transfer validation successful"
                
        except Exception as e:
            logger.error(f"Error validating transfer: {str(e)}", exc_info=True)
            return False, f"Validation error: {str(e)}"

    async def execute_transfer(
        self,
        application_id: str,
        application_type: str,
        from_role: str,
        to_role: str,
        user_id: int,
        transfer_reason: Optional[str] = None,
        transfer_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an application transfer between roles with atomic database operations.
        
        Args:
            application_id: ID of the application to transfer
            application_type: Type of application
            from_role: Current role holding the application
            to_role: Target role for transfer
            user_id: ID of user performing the transfer
            transfer_reason: Reason for the transfer
            transfer_notes: Additional notes about the transfer
            
        Returns:
            Dict with transfer result and details
        """
        # Validate transfer first
        is_valid, error_message = await self.validate_transfer(
            application_id, application_type, from_role, to_role, user_id
        )
        
        if not is_valid:
            return {
                'success': False,
                'error': error_message,
                'transfer_id': None
            }

        pool = self._get_pool()
        
        try:
            async with pool.acquire() as conn:
                # Start transaction for atomic operations
                async with conn.transaction():
                    # Update application role assignment
                    if application_type == 'zayavka':
                        update_query = """
                            UPDATE zayavki 
                            SET assigned_role = $1, updated_at = CURRENT_TIMESTAMP
                            WHERE id = $2
                            RETURNING id
                        """
                        result = await conn.fetchval(update_query, to_role, int(application_id))
                        
                    elif application_type == 'service_request':
                        update_query = """
                            UPDATE service_requests 
                            SET role_current = $1, updated_at = CURRENT_TIMESTAMP
                            WHERE id = $2
                            RETURNING id
                        """
                        result = await conn.fetchval(update_query, to_role, application_id)
                    
                    if not result:
                        raise Exception("Failed to update application role assignment")
                    
                    # Log the transfer in application_transfers table
                    transfer_query = """
                        INSERT INTO application_transfers (
                            application_id, application_type, from_role, to_role,
                            transferred_by, transfer_reason, transfer_notes
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id
                    """
                    
                    transfer_id = await conn.fetchval(
                        transfer_query,
                        application_id, application_type, from_role, to_role,
                        user_id, transfer_reason, transfer_notes
                    )
                    
                    if not transfer_id:
                        raise Exception("Failed to log transfer")
                    
                    # Create inbox message for target role
                    await self.inbox_service.create_inbox_message(
                        application_id=application_id,
                        application_type=application_type,
                        assigned_role=to_role,
                        title=f"Application transferred from {from_role}",
                        description=f"Application {application_id} has been transferred to your role",
                        message_type='transfer',
                        priority='medium'
                    )
                    
                    # Remove old inbox messages for the from_role (mark as read)
                    cleanup_query = """
                        UPDATE inbox_messages 
                        SET is_read = TRUE, updated_at = CURRENT_TIMESTAMP
                        WHERE application_id = $1 
                        AND application_type = $2 
                        AND assigned_role = $3
                        AND is_read = FALSE
                    """
                    
                    await conn.execute(cleanup_query, application_id, application_type, from_role)
                    
                    logger.info(f"Successfully transferred {application_type} {application_id} from {from_role} to {to_role} by user {user_id}")
                    
                    return {
                        'success': True,
                        'transfer_id': transfer_id,
                        'application_id': application_id,
                        'application_type': application_type,
                        'from_role': from_role,
                        'to_role': to_role,
                        'transferred_by': user_id,
                        'transfer_reason': transfer_reason,
                        'transfer_notes': transfer_notes
                    }
                    
        except Exception as e:
            logger.error(f"Error executing transfer: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"Transfer failed: {str(e)}",
                'transfer_id': None
            }

    async def get_transfer_history(
        self,
        application_id: str,
        application_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get transfer history for an application.
        
        Args:
            application_id: ID of the application
            application_type: Type of application
            
        Returns:
            List of transfer records
        """
        if application_type not in InboxService.VALID_APPLICATION_TYPES:
            raise ValueError(f"Invalid application_type: {application_type}")

        pool = self._get_pool()
        
        query = """
            SELECT 
                at.*,
                u.full_name as transferred_by_name,
                u.role as transferred_by_role
            FROM application_transfers at
            LEFT JOIN users u ON at.transferred_by = u.id
            WHERE at.application_id = $1 AND at.application_type = $2
            ORDER BY at.created_at DESC
        """
        
        try:
            async with pool.acquire() as conn:
                results = await conn.fetch(query, application_id, application_type)
                
                transfers = []
                for row in results:
                    transfer_data = dict(row)
                    transfers.append(transfer_data)
                
                return transfers
                
        except Exception as e:
            logger.error(f"Error getting transfer history: {str(e)}", exc_info=True)
            return []

    async def rollback_transfer(
        self,
        transfer_id: int,
        user_id: int,
        rollback_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rollback a transfer (move application back to previous role).
        
        Args:
            transfer_id: ID of the transfer to rollback
            user_id: ID of user performing the rollback
            rollback_reason: Reason for the rollback
            
        Returns:
            Dict with rollback result
        """
        pool = self._get_pool()
        
        try:
            async with pool.acquire() as conn:
                # Get transfer details
                transfer_query = """
                    SELECT * FROM application_transfers 
                    WHERE id = $1
                """
                
                transfer = await conn.fetchrow(transfer_query, transfer_id)
                if not transfer:
                    return {
                        'success': False,
                        'error': 'Transfer not found'
                    }
                
                transfer_data = dict(transfer)
                
                # Execute reverse transfer
                result = await self.execute_transfer(
                    application_id=transfer_data['application_id'],
                    application_type=transfer_data['application_type'],
                    from_role=transfer_data['to_role'],
                    to_role=transfer_data['from_role'],
                    user_id=user_id,
                    transfer_reason=f"Rollback of transfer {transfer_id}",
                    transfer_notes=rollback_reason
                )
                
                if result['success']:
                    logger.info(f"Successfully rolled back transfer {transfer_id} by user {user_id}")
                
                return result
                
        except Exception as e:
            logger.error(f"Error rolling back transfer: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"Rollback failed: {str(e)}"
            }

    async def notify_target_role(
        self,
        application_id: str,
        application_type: str,
        to_role: str,
        notification_type: str = 'transfer'
    ) -> bool:
        """
        Send notification to target role about application transfer.
        
        Args:
            application_id: ID of the application
            application_type: Type of application
            to_role: Role to notify
            notification_type: Type of notification
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # This would integrate with the existing notification system
            # For now, we create an inbox message
            return await self.inbox_service.create_inbox_message(
                application_id=application_id,
                application_type=application_type,
                assigned_role=to_role,
                title=f"New {application_type} assigned",
                description=f"You have been assigned {application_type} {application_id}",
                message_type='notification',
                priority='medium'
            )
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}", exc_info=True)
            return False

    async def get_role_transfer_stats(self, role: str, days: int = 30) -> Dict[str, Any]:
        """
        Get transfer statistics for a role.
        
        Args:
            role: Role to get stats for
            days: Number of days to look back
            
        Returns:
            Dict with transfer statistics
        """
        if role not in InboxService.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")

        pool = self._get_pool()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
            SELECT 
                COUNT(*) as total_transfers,
                COUNT(CASE WHEN from_role = $1 THEN 1 END) as transfers_out,
                COUNT(CASE WHEN to_role = $1 THEN 1 END) as transfers_in,
                COUNT(DISTINCT application_id) as unique_applications,
                COUNT(DISTINCT transferred_by) as unique_transferers
            FROM application_transfers
            WHERE (from_role = $1 OR to_role = $1)
            AND created_at >= $2
        """
        
        try:
            async with pool.acquire() as conn:
                result = await conn.fetchrow(query, role, cutoff_date)
                
                if result:
                    stats = dict(result)
                    stats['period_days'] = days
                    stats['role'] = role
                    return stats
                
                return {
                    'role': role,
                    'period_days': days,
                    'total_transfers': 0,
                    'transfers_out': 0,
                    'transfers_in': 0,
                    'unique_applications': 0,
                    'unique_transferers': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting transfer stats: {str(e)}", exc_info=True)
            return {}