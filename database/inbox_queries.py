"""
Database queries for inbox system
"""

import asyncpg
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from database.inbox_models import (
    InboxMessage, ApplicationTransfer, InboxRole, ApplicationType,
    MessageType, MessagePriority
)

class InboxQueries:
    """Database queries for inbox system"""
    
    @staticmethod
    async def add_role_to_zayavka(zayavka_id: int, assigned_role: str, pool: asyncpg.Pool = None) -> bool:
        """Add role assignment to existing zayavka"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            
            # Validate role
            if assigned_role not in [r.value for r in InboxRole]:
                raise ValueError(f"Invalid role: {assigned_role}")
            
            query = """
                UPDATE zayavki 
                SET assigned_role = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """
            
            async with pool.acquire() as conn:
                result = await conn.execute(query, assigned_role, zayavka_id)
                return result == "UPDATE 1"
            
        except Exception as e:
            print(f"Error adding role to zayavka: {e}")
            return False
    
    @staticmethod
    async def add_role_to_service_request(request_id: str, role_current: str, pool: asyncpg.Pool = None) -> bool:
        """Add role assignment to existing service request"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            # Validate role
            if role_current not in [r.value for r in InboxRole]:
                raise ValueError(f"Invalid role: {role_current}")
            
            query = """
                UPDATE service_requests 
                SET role_current = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """
            
            async with pool.acquire() as conn:
                result = await conn.execute(query, role_current, request_id)
                return result == "UPDATE 1"
            
        except Exception as e:
            print(f"Error adding role to service request: {e}")
            return False
    
    @staticmethod
    async def get_role_applications(
        role: str, 
        limit: int = 50, 
        offset: int = 0,
        include_read: bool = True,
        pool: asyncpg.Pool = None
    ) -> List[Dict[str, Any]]:
        """Get applications assigned to a specific role"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            # Validate role
            if role not in [r.value for r in InboxRole]:
                raise ValueError(f"Invalid role: {role}")
            
            # Query both zayavki and service_requests
            query = """
                WITH role_applications AS (
                    -- Get zayavki assigned to role
                    SELECT 
                        z.id::text as application_id,
                        'zayavka' as application_type,
                        z.assigned_role,
                        z.description,
                        z.status,
                        z.priority,
                        z.created_at,
                        z.updated_at,
                        u.full_name as client_name,
                        u.phone as client_phone,
                        z.address,
                        COALESCE(im.is_read, true) as is_read,
                        COALESCE(im.priority, z.priority) as message_priority
                    FROM zayavki z
                    LEFT JOIN users u ON z.user_id = u.id
                    LEFT JOIN inbox_messages im ON im.application_id = z.id::text 
                        AND im.application_type = 'zayavka' 
                        AND im.assigned_role = $1
                    WHERE z.assigned_role = $1
                    
                    UNION ALL
                    
                    -- Get service_requests assigned to role
                    SELECT 
                        sr.id as application_id,
                        'service_request' as application_type,
                        sr.role_current as assigned_role,
                        sr.description,
                        sr.current_status as status,
                        sr.priority,
                        sr.created_at,
                        sr.updated_at,
                        u.full_name as client_name,
                        u.phone as client_phone,
                        sr.location as address,
                        COALESCE(im.is_read, true) as is_read,
                        COALESCE(im.priority, sr.priority) as message_priority
                    FROM service_requests sr
                    LEFT JOIN users u ON sr.client_id = u.id
                    LEFT JOIN inbox_messages im ON im.application_id = sr.id 
                        AND im.application_type = 'service_request' 
                        AND im.assigned_role = $1
                    WHERE sr.role_current = $1
                )
                SELECT * FROM role_applications
                WHERE ($4 = true OR is_read = false)
                ORDER BY 
                    CASE message_priority 
                        WHEN 'urgent' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        WHEN 'low' THEN 4 
                        ELSE 5 
                    END,
                    created_at DESC
                LIMIT $2 OFFSET $3
            """
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, role, limit, offset, include_read)
                
                applications = []
                for row in rows:
                    applications.append({
                        'application_id': row['application_id'],
                        'application_type': row['application_type'],
                        'assigned_role': row['assigned_role'],
                        'description': row['description'],
                        'status': row['status'],
                        'priority': row['priority'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'client_name': row['client_name'],
                        'client_phone': row['client_phone'],
                        'address': row['address'],
                        'is_read': row['is_read'],
                        'message_priority': row['message_priority']
                    })
                
                return applications
            
        except Exception as e:
            print(f"Error getting role applications: {e}")
            return []
    
    @staticmethod
    async def get_application_details(
        application_id: str, 
        application_type: str,
        pool: asyncpg.Pool = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific application"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            
            if application_type == ApplicationType.ZAYAVKA.value:
                query = """
                    SELECT 
                        z.id::text as application_id,
                        'zayavka' as application_type,
                        z.assigned_role,
                        z.description,
                        z.status,
                        z.priority,
                        z.created_at,
                        z.updated_at,
                        z.address,
                        z.phone,
                        u.full_name as client_name,
                        u.phone as client_phone,
                        u.telegram_id as client_telegram_id,
                        z.technician_id,
                        tech.full_name as technician_name
                    FROM zayavki z
                    LEFT JOIN users u ON z.user_id = u.id
                    LEFT JOIN users tech ON z.technician_id = tech.id
                    WHERE z.id = $1::integer
                """
            elif application_type == ApplicationType.SERVICE_REQUEST.value:
                query = """
                    SELECT 
                        sr.id as application_id,
                        'service_request' as application_type,
                        sr.role_current as assigned_role,
                        sr.description,
                        sr.current_status as status,
                        sr.priority,
                        sr.created_at,
                        sr.updated_at,
                        sr.location as address,
                        sr.contact_info,
                        u.full_name as client_name,
                        u.phone as client_phone,
                        u.telegram_id as client_telegram_id,
                        sr.workflow_type,
                        sr.state_data
                    FROM service_requests sr
                    LEFT JOIN users u ON sr.client_id = u.id
                    WHERE sr.id = $1
                """
            else:
                raise ValueError(f"Invalid application_type: {application_type}")
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, application_id)
                
                if row:
                    return dict(row)
                return None
            
        except Exception as e:
            print(f"Error getting application details: {e}")
            return None
    
    @staticmethod
    async def create_inbox_message(message: InboxMessage, pool: asyncpg.Pool = None) -> Optional[int]:
        """Create a new inbox message"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            query = """
                INSERT INTO inbox_messages (
                    application_id, application_type, assigned_role, message_type,
                    title, description, priority, is_read, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    message.application_id,
                    message.application_type,
                    message.assigned_role,
                    message.message_type,
                    message.title,
                    message.description,
                    message.priority,
                    message.is_read,
                    message.created_at or datetime.now()
                )
                
                return row['id'] if row else None
            
        except Exception as e:
            print(f"Error creating inbox message: {e}")
            return None
    
    @staticmethod
    async def mark_message_as_read(message_id: int, user_id: int, pool: asyncpg.Pool = None) -> bool:
        """Mark an inbox message as read"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            query = """
                UPDATE inbox_messages 
                SET is_read = true, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """
            
            async with pool.acquire() as conn:
                result = await conn.execute(query, message_id)
                return result == "UPDATE 1"
            
        except Exception as e:
            print(f"Error marking message as read: {e}")
            return False
    
    @staticmethod
    async def transfer_application(
        application_id: str,
        application_type: str,
        from_role: Optional[str],
        to_role: str,
        transferred_by: int,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        pool: asyncpg.Pool = None
    ) -> bool:
        """Transfer application from one role to another"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            async with pool.acquire() as conn:
                # Start transaction
                async with conn.transaction():
                    # Update application role
                    if application_type == ApplicationType.ZAYAVKA.value:
                        update_query = """
                            UPDATE zayavki 
                            SET assigned_role = $1, updated_at = CURRENT_TIMESTAMP
                            WHERE id = $2::integer
                        """
                    elif application_type == ApplicationType.SERVICE_REQUEST.value:
                        update_query = """
                            UPDATE service_requests 
                            SET role_current = $1, updated_at = CURRENT_TIMESTAMP
                            WHERE id = $2
                        """
                    else:
                        raise ValueError(f"Invalid application_type: {application_type}")
                    
                    result = await conn.execute(update_query, to_role, application_id)
                    if result != "UPDATE 1":
                        raise Exception("Failed to update application role")
                
                    # Create transfer audit record
                    audit_query = """
                        INSERT INTO application_transfers (
                            application_id, application_type, from_role, to_role,
                            transferred_by, transfer_reason, transfer_notes, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """
                    
                    await conn.execute(
                        audit_query,
                        application_id,
                        application_type,
                        from_role,
                        to_role,
                        transferred_by,
                        reason,
                        notes,
                        datetime.now()
                    )
                    
                    # Update existing inbox messages for this application
                    message_update_query = """
                        UPDATE inbox_messages 
                        SET assigned_role = $1, updated_at = CURRENT_TIMESTAMP
                        WHERE application_id = $2 AND application_type = $3
                    """
                    
                    await conn.execute(message_update_query, to_role, application_id, application_type)
                
                    # Create transfer notification message
                    transfer_message = InboxMessage(
                        application_id=application_id,
                        application_type=application_type,
                        assigned_role=to_role,
                        message_type=MessageType.TRANSFER.value,
                        title=f"Application transferred from {from_role or 'system'}",
                        description=f"Application has been transferred to your role. Reason: {reason or 'No reason provided'}",
                        priority=MessagePriority.MEDIUM.value,
                        created_at=datetime.now()
                    )
                    
                    notification_query = """
                        INSERT INTO inbox_messages (
                            application_id, application_type, assigned_role, message_type,
                            title, description, priority, is_read, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """
                    
                    await conn.execute(
                        notification_query,
                        transfer_message.application_id,
                        transfer_message.application_type,
                        transfer_message.assigned_role,
                        transfer_message.message_type,
                        transfer_message.title,
                        transfer_message.description,
                        transfer_message.priority,
                        transfer_message.is_read,
                        transfer_message.created_at
                    )
            
                return True
            
        except Exception as e:
            print(f"Error transferring application: {e}")
            return False
    
    @staticmethod
    async def get_transfer_history(
        application_id: str, 
        application_type: str,
        pool: asyncpg.Pool = None
    ) -> List[Dict[str, Any]]:
        """Get transfer history for an application"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            query = """
                SELECT 
                    at.*,
                    u.full_name as transferred_by_name
                FROM application_transfers at
                LEFT JOIN users u ON at.transferred_by = u.id
                WHERE at.application_id = $1 AND at.application_type = $2
                ORDER BY at.created_at DESC
            """
            
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, application_id, application_type)
                
                transfers = []
                for row in rows:
                    transfers.append({
                        'id': row['id'],
                        'application_id': row['application_id'],
                        'application_type': row['application_type'],
                        'from_role': row['from_role'],
                        'to_role': row['to_role'],
                        'transferred_by': row['transferred_by'],
                        'transferred_by_name': row['transferred_by_name'],
                        'transfer_reason': row['transfer_reason'],
                        'transfer_notes': row['transfer_notes'],
                        'created_at': row['created_at']
                    })
                
                return transfers
            
        except Exception as e:
            print(f"Error getting transfer history: {e}")
            return []
    
    @staticmethod
    async def get_role_statistics(role: str, pool: asyncpg.Pool = None) -> Dict[str, int]:
        """Get statistics for a role's inbox"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            # Validate role
            if role not in [r.value for r in InboxRole]:
                raise ValueError(f"Invalid role: {role}")
            
            query = """
                WITH role_stats AS (
                    -- Count zayavki
                    SELECT 
                        COUNT(*) as total_zayavki,
                        COUNT(CASE WHEN z.status = 'new' THEN 1 END) as new_zayavki,
                        COUNT(CASE WHEN im.is_read = false THEN 1 END) as unread_zayavki
                    FROM zayavki z
                    LEFT JOIN inbox_messages im ON im.application_id = z.id::text 
                        AND im.application_type = 'zayavka' 
                        AND im.assigned_role = $1
                    WHERE z.assigned_role = $1
                ),
                service_stats AS (
                    -- Count service_requests
                    SELECT 
                        COUNT(*) as total_service_requests,
                        COUNT(CASE WHEN sr.current_status = 'created' THEN 1 END) as new_service_requests,
                        COUNT(CASE WHEN im.is_read = false THEN 1 END) as unread_service_requests
                    FROM service_requests sr
                    LEFT JOIN inbox_messages im ON im.application_id = sr.id 
                        AND im.application_type = 'service_request' 
                        AND im.assigned_role = $1
                    WHERE sr.role_current = $1
                )
                SELECT 
                    COALESCE(rs.total_zayavki, 0) + COALESCE(ss.total_service_requests, 0) as total_applications,
                    COALESCE(rs.new_zayavki, 0) + COALESCE(ss.new_service_requests, 0) as new_applications,
                    COALESCE(rs.unread_zayavki, 0) + COALESCE(ss.unread_service_requests, 0) as unread_applications,
                    COALESCE(rs.total_zayavki, 0) as total_zayavki,
                    COALESCE(ss.total_service_requests, 0) as total_service_requests
                FROM role_stats rs
                FULL OUTER JOIN service_stats ss ON true
            """
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(query, role)
                
                if row:
                    return {
                        'total_applications': row['total_applications'],
                        'new_applications': row['new_applications'],
                        'unread_applications': row['unread_applications'],
                        'total_zayavki': row['total_zayavki'],
                        'total_service_requests': row['total_service_requests']
                    }
                
                return {
                    'total_applications': 0,
                    'new_applications': 0,
                    'unread_applications': 0,
                    'total_zayavki': 0,
                    'total_service_requests': 0
                }
            
        except Exception as e:
            print(f"Error getting role statistics: {e}")
            return {
                'total_applications': 0,
                'new_applications': 0,
                'unread_applications': 0,
                'total_zayavki': 0,
                'total_service_requests': 0
            }
    
    @staticmethod
    async def cleanup_old_messages(days_old: int = 30, pool: asyncpg.Pool = None) -> int:
        """Clean up old read messages"""
        if not pool:
            from loader import bot
            pool = bot.db
        
        try:
            query = """
                DELETE FROM inbox_messages 
                WHERE is_read = true 
                AND created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """
            
            async with pool.acquire() as conn:
                result = await conn.execute(query % days_old)
                
                # Extract number of deleted rows from result string like "DELETE 5"
                deleted_count = int(result.split()[-1]) if result.startswith("DELETE") else 0
                return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old messages: {e}")
            return 0