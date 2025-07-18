"""
Client-specific database queries for staff application creation
Provides database operations for client search, creation, and management
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncpg

from loader import bot
from database.models import User, ServiceRequest

logger = logging.getLogger(__name__)


async def get_client_application_history(
    client_id: int, 
    page: int = 1, 
    limit: int = 10,
    status_filter: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get client's application history with pagination
    
    Args:
        client_id: Client database ID
        page: Page number (1-based)
        limit: Number of records per page
        status_filter: Optional status filter
        
    Returns:
        Tuple of (applications_list, total_count)
    """
    try:
        async with bot.db.acquire() as conn:
            # Build query conditions
            where_conditions = ["user_id = $1"]
            params = [client_id]
            param_count = 1
            
            if status_filter:
                param_count += 1
                where_conditions.append(f"status = ${param_count}")
                params.append(status_filter)
            
            where_clause = " AND ".join(where_conditions)
            
            # Get total count
            count_query = f"""
                SELECT COUNT(*) 
                FROM zayavkas 
                WHERE {where_clause}
            """
            total_count = await conn.fetchval(count_query, *params)
            
            # Get paginated results
            offset = (page - 1) * limit
            param_count += 1
            limit_param = param_count
            param_count += 1
            offset_param = param_count
            
            query = f"""
                SELECT 
                    id, user_id, description, address, phone, status, priority,
                    technician_id, assigned_by, created_at, updated_at,
                    completed_at, cancelled_at, notes, client_feedback, rating
                FROM zayavkas 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${limit_param} OFFSET ${offset_param}
            """
            
            params.extend([limit, offset])
            results = await conn.fetch(query, *params)
            
            # Convert to list of dictionaries
            applications = []
            for row in results:
                app_dict = dict(row)
                applications.append(app_dict)
            
            return applications, total_count
            
    except Exception as e:
        logger.error(f"Error getting client application history: {e}")
        return [], 0


async def search_clients_by_phone(phone: str, exact_match: bool = True) -> List[Dict[str, Any]]:
    """
    Search clients by phone number
    
    Args:
        phone: Phone number to search
        exact_match: Whether to use exact match or partial match
        
    Returns:
        List of matching client dictionaries
    """
    try:
        async with bot.db.acquire() as conn:
            if exact_match:
                query = """
                    SELECT id, telegram_id, full_name, phone_number, role, language,
                           is_active, address, created_at, updated_at, last_activity
                    FROM users 
                    WHERE phone_number = $1 OR phone_number = $2
                    ORDER BY created_at DESC
                """
                # Try both with and without + prefix
                phone_variants = [phone, phone.lstrip('+') if phone.startswith('+') else '+' + phone]
                results = await conn.fetch(query, phone_variants[0], phone_variants[1])
            else:
                query = """
                    SELECT id, telegram_id, full_name, phone_number, role, language,
                           is_active, address, created_at, updated_at, last_activity
                    FROM users 
                    WHERE phone_number ILIKE $1
                    ORDER BY created_at DESC
                    LIMIT 10
                """
                results = await conn.fetch(query, f"%{phone}%")
            
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Error searching clients by phone: {e}")
        return []


async def search_clients_by_name(name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search clients by name (fuzzy search)
    
    Args:
        name: Name to search for
        limit: Maximum number of results
        
    Returns:
        List of matching client dictionaries
    """
    try:
        async with bot.db.acquire() as conn:
            query = """
                SELECT id, telegram_id, full_name, phone_number, role, language,
                       is_active, address, created_at, updated_at, last_activity
                FROM users 
                WHERE full_name ILIKE $1
                ORDER BY 
                    CASE WHEN full_name ILIKE $2 THEN 1 ELSE 2 END,
                    created_at DESC
                LIMIT $3
            """
            
            # Search patterns: exact match gets priority, then partial
            exact_pattern = name
            partial_pattern = f"%{name}%"
            
            results = await conn.fetch(query, partial_pattern, exact_pattern, limit)
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Error searching clients by name: {e}")
        return []


async def get_client_by_id(client_id: int) -> Optional[Dict[str, Any]]:
    """
    Get client by database ID
    
    Args:
        client_id: Client database ID
        
    Returns:
        Client dictionary or None if not found
    """
    try:
        async with bot.db.acquire() as conn:
            query = """
                SELECT id, telegram_id, full_name, phone_number, role, language,
                       is_active, address, created_at, updated_at, last_activity
                FROM users 
                WHERE id = $1
            """
            
            result = await conn.fetchrow(query, client_id)
            return dict(result) if result else None
            
    except Exception as e:
        logger.error(f"Error getting client by ID: {e}")
        return None


async def create_new_client(client_data: Dict[str, Any]) -> Optional[int]:
    """
    Create a new client record
    
    Args:
        client_data: Dictionary containing client information
        
    Returns:
        New client ID or None if creation failed
    """
    try:
        async with bot.db.acquire() as conn:
            query = """
                INSERT INTO users (
                    full_name, phone_number, role, language, 
                    is_active, address, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $7
                ) RETURNING id
            """
            
            now = datetime.now()
            client_id = await conn.fetchval(
                query,
                client_data.get('full_name'),
                client_data.get('phone_number'),
                client_data.get('role', 'client'),
                client_data.get('language', 'uz'),
                client_data.get('is_active', True),
                client_data.get('address'),
                now
            )
            
            logger.info(f"Created new client with ID: {client_id}")
            return client_id
            
    except Exception as e:
        logger.error(f"Error creating new client: {e}")
        return None


async def update_client_info(client_id: int, update_data: Dict[str, Any]) -> bool:
    """
    Update client information
    
    Args:
        client_id: Client database ID
        update_data: Dictionary containing fields to update
        
    Returns:
        True if update successful, False otherwise
    """
    try:
        if not update_data:
            return True
        
        async with bot.db.acquire() as conn:
            # Build dynamic update query
            set_clauses = []
            params = []
            param_count = 0
            
            for field, value in update_data.items():
                if field in ['full_name', 'phone_number', 'language', 'address', 'is_active']:
                    param_count += 1
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value)
            
            if not set_clauses:
                return True
            
            # Add updated_at
            param_count += 1
            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            
            # Add client_id for WHERE clause
            param_count += 1
            params.append(client_id)
            
            query = f"""
                UPDATE users 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count}
            """
            
            result = await conn.execute(query, *params)
            
            # Check if any rows were updated
            rows_affected = int(result.split()[-1])
            success = rows_affected > 0
            
            if success:
                logger.info(f"Updated client {client_id} with data: {update_data}")
            else:
                logger.warning(f"No rows updated for client {client_id}")
            
            return success
            
    except Exception as e:
        logger.error(f"Error updating client info: {e}")
        return False


async def get_client_statistics(client_id: int) -> Dict[str, Any]:
    """
    Get client statistics (application counts, etc.)
    
    Args:
        client_id: Client database ID
        
    Returns:
        Dictionary containing client statistics
    """
    try:
        async with bot.db.acquire() as conn:
            # Get application counts by status
            status_query = """
                SELECT status, COUNT(*) as count
                FROM zayavkas 
                WHERE user_id = $1
                GROUP BY status
            """
            status_results = await conn.fetch(status_query, client_id)
            
            # Get total applications count
            total_query = """
                SELECT COUNT(*) as total_applications,
                       COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed_applications,
                       AVG(rating) as average_rating
                FROM zayavkas 
                WHERE user_id = $1
            """
            total_result = await conn.fetchrow(total_query, client_id)
            
            # Get recent activity
            recent_query = """
                SELECT created_at
                FROM zayavkas 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            recent_result = await conn.fetchrow(recent_query, client_id)
            
            # Build statistics dictionary
            stats = {
                'total_applications': total_result['total_applications'] or 0,
                'completed_applications': total_result['completed_applications'] or 0,
                'average_rating': float(total_result['average_rating']) if total_result['average_rating'] else 0.0,
                'status_counts': {row['status']: row['count'] for row in status_results},
                'last_application_date': recent_result['created_at'] if recent_result else None
            }
            
            return stats
            
    except Exception as e:
        logger.error(f"Error getting client statistics: {e}")
        return {}


async def check_client_phone_exists(phone: str, exclude_client_id: Optional[int] = None) -> bool:
    """
    Check if phone number already exists for another client
    
    Args:
        phone: Phone number to check
        exclude_client_id: Client ID to exclude from check (for updates)
        
    Returns:
        True if phone exists for another client, False otherwise
    """
    try:
        async with bot.db.acquire() as conn:
            if exclude_client_id:
                query = """
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE (phone_number = $1 OR phone_number = $2) AND id != $3
                """
                phone_variants = [phone, phone.lstrip('+') if phone.startswith('+') else '+' + phone]
                count = await conn.fetchval(query, phone_variants[0], phone_variants[1], exclude_client_id)
            else:
                query = """
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE phone_number = $1 OR phone_number = $2
                """
                phone_variants = [phone, phone.lstrip('+') if phone.startswith('+') else '+' + phone]
                count = await conn.fetchval(query, phone_variants[0], phone_variants[1])
            
            return count > 0
            
    except Exception as e:
        logger.error(f"Error checking phone existence: {e}")
        return False


async def get_clients_with_recent_activity(days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get clients with recent activity
    
    Args:
        days: Number of days to look back
        limit: Maximum number of results
        
    Returns:
        List of client dictionaries with recent activity
    """
    try:
        async with bot.db.acquire() as conn:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT DISTINCT u.id, u.telegram_id, u.full_name, u.phone_number, 
                       u.role, u.language, u.is_active, u.address, 
                       u.created_at, u.updated_at, u.last_activity,
                       COUNT(z.id) as recent_applications
                FROM users u
                LEFT JOIN zayavkas z ON u.id = z.user_id AND z.created_at >= $1
                WHERE u.role = 'client' AND (u.last_activity >= $1 OR z.id IS NOT NULL)
                GROUP BY u.id, u.telegram_id, u.full_name, u.phone_number, 
                         u.role, u.language, u.is_active, u.address, 
                         u.created_at, u.updated_at, u.last_activity
                ORDER BY u.last_activity DESC NULLS LAST, recent_applications DESC
                LIMIT $2
            """
            
            results = await conn.fetch(query, cutoff_date, limit)
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Error getting clients with recent activity: {e}")
        return []


async def update_client_last_activity(client_id: int) -> bool:
    """
    Update client's last activity timestamp
    
    Args:
        client_id: Client database ID
        
    Returns:
        True if update successful, False otherwise
    """
    try:
        async with bot.db.acquire() as conn:
            query = """
                UPDATE users 
                SET last_activity = $1
                WHERE id = $2
            """
            
            result = await conn.execute(query, datetime.now(), client_id)
            rows_affected = int(result.split()[-1])
            
            return rows_affected > 0
            
    except Exception as e:
        logger.error(f"Error updating client last activity: {e}")
        return False


async def get_client_contact_preferences(client_id: int) -> Dict[str, Any]:
    """
    Get client's contact preferences and communication history
    
    Args:
        client_id: Client database ID
        
    Returns:
        Dictionary containing contact preferences
    """
    try:
        async with bot.db.acquire() as conn:
            # Get basic client info
            client_query = """
                SELECT id, telegram_id, full_name, phone_number, language, 
                       created_at, last_activity
                FROM users 
                WHERE id = $1
            """
            client_result = await conn.fetchrow(client_query, client_id)
            
            if not client_result:
                return {}
            
            # Get communication statistics
            comm_query = """
                SELECT 
                    COUNT(*) as total_applications,
                    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as recent_applications,
                    MAX(created_at) as last_application_date
                FROM zayavkas 
                WHERE user_id = $1
            """
            comm_result = await conn.fetchrow(comm_query, client_id)
            
            preferences = {
                'client_id': client_result['id'],
                'telegram_id': client_result['telegram_id'],
                'full_name': client_result['full_name'],
                'phone_number': client_result['phone_number'],
                'preferred_language': client_result['language'],
                'has_telegram': client_result['telegram_id'] is not None,
                'registration_date': client_result['created_at'],
                'last_activity': client_result['last_activity'],
                'total_applications': comm_result['total_applications'] or 0,
                'recent_applications': comm_result['recent_applications'] or 0,
                'last_application_date': comm_result['last_application_date']
            }
            
            return preferences
            
    except Exception as e:
        logger.error(f"Error getting client contact preferences: {e}")
        return {}


# Utility functions for client data validation
async def validate_client_data_integrity(client_id: int) -> Dict[str, Any]:
    """
    Validate client data integrity and return validation report
    
    Args:
        client_id: Client database ID
        
    Returns:
        Dictionary containing validation results
    """
    try:
        async with bot.db.acquire() as conn:
            # Check basic client data
            client_query = """
                SELECT id, full_name, phone_number, role, language, is_active
                FROM users 
                WHERE id = $1
            """
            client_result = await conn.fetchrow(client_query, client_id)
            
            if not client_result:
                return {'valid': False, 'errors': ['Client not found']}
            
            errors = []
            warnings = []
            
            # Validate required fields
            if not client_result['full_name'] or len(client_result['full_name'].strip()) < 2:
                errors.append('Invalid or missing full name')
            
            if not client_result['phone_number']:
                errors.append('Missing phone number')
            
            if client_result['role'] != 'client':
                warnings.append(f'Unusual role: {client_result["role"]}')
            
            if client_result['language'] not in ['uz', 'ru']:
                warnings.append(f'Unusual language: {client_result["language"]}')
            
            # Check for duplicate phone numbers
            duplicate_query = """
                SELECT COUNT(*) 
                FROM users 
                WHERE phone_number = $1 AND id != $2
            """
            duplicate_count = await conn.fetchval(
                duplicate_query, 
                client_result['phone_number'], 
                client_id
            )
            
            if duplicate_count > 0:
                warnings.append('Phone number exists for other clients')
            
            # Check application data consistency
            app_query = """
                SELECT COUNT(*) as total_apps,
                       COUNT(CASE WHEN phone != $1 THEN 1 END) as phone_mismatches
                FROM zayavkas 
                WHERE user_id = $2
            """
            app_result = await conn.fetchrow(app_query, client_result['phone_number'], client_id)
            
            if app_result['phone_mismatches'] > 0:
                warnings.append('Phone number mismatches in applications')
            
            validation_result = {
                'valid': len(errors) == 0,
                'client_id': client_id,
                'errors': errors,
                'warnings': warnings,
                'total_applications': app_result['total_apps'] or 0,
                'checked_at': datetime.now()
            }
            
            return validation_result
            
    except Exception as e:
        logger.error(f"Error validating client data integrity: {e}")
        return {'valid': False, 'errors': [f'Validation error: {str(e)}']}

# --- Client zayavka statistics by telegram_id ---
from database.base_queries import get_user_by_telegram_id

async def get_user_zayavka_statistics(telegram_id: int) -> dict:
    """
    Get statistics of a client's zayavkas by status for the last 7 and 30 days.
    Returns a dict with counts for each status (new, in_progress, completed, cancelled),
    each with 'weekly' and 'monthly' keys.
    If user not found or error, returns -1.
    """
    try:
        user = await get_user_by_telegram_id(telegram_id)
        if not user:
            return -1
        user_id = user['id']
        async with bot.db.acquire() as conn:
            query = """
                SELECT status,
                       COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') AS weekly,
                       COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') AS monthly
                FROM zayavkas
                WHERE user_id = $1
                GROUP BY status
            """
            rows = await conn.fetch(query, user_id)
            # Default structure
            stats = {
                'new': {'weekly': 0, 'monthly': 0},
                'in_progress': {'weekly': 0, 'monthly': 0},
                'completed': {'weekly': 0, 'monthly': 0},
                'cancelled': {'weekly': 0, 'monthly': 0}
            }
            for row in rows:
                status = row['status']
                if status in stats:
                    stats[status]['weekly'] = row['weekly']
                    stats[status]['monthly'] = row['monthly']
            return stats
    except Exception as e:
        logger.error(f"Error in get_user_zayavka_statistics for telegram_id {telegram_id}: {e}", exc_info=True)
        return -1

# Export all functions
__all__ = [
    'get_client_application_history',
    'search_clients_by_phone',
    'search_clients_by_name',
    'get_client_by_id',
    'create_new_client',
    'update_client_info',
    'get_client_statistics',
    'check_client_phone_exists',
    'get_clients_with_recent_activity',
    'update_client_last_activity',
    'get_client_contact_preferences',
    'validate_client_data_integrity'
]


