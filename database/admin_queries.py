import asyncpg
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import logging
from config import config
from loader import bot

# Setup logger
logger = logging.getLogger(__name__)

# ==================== ADMIN SPECIFIC QUERIES ====================

async def get_admin_dashboard_stats() -> Dict:
    """Get admin dashboard statistics"""
    async with bot.db.acquire() as conn:
        try:
            # Total users by role
            users_query = """
            SELECT role, COUNT(*) as count
            FROM users
            WHERE is_active = true
            GROUP BY role
            ORDER BY count DESC
            """
            users_stats = await conn.fetch(users_query)
            
            # Total orders by status
            orders_query = """
            SELECT status, COUNT(*) as count
            FROM zayavki
            GROUP BY status
            ORDER BY count DESC
            """
            orders_stats = await conn.fetch(orders_query)
            
            # Today's statistics
            today_query = """
            SELECT 
                COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today_orders,
                COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE AND status = 'completed' THEN 1 END) as today_completed,
                COUNT(CASE WHEN status IN ('new', 'pending') THEN 1 END) as pending_orders
            FROM zayavki
            """
            today_stats = await conn.fetchrow(today_query)
            
            # System health
            system_query = """
            SELECT 
                COUNT(*) as total_users,
                COUNT(DISTINCT user_id) as total_orders,
                COUNT(DISTINCT assigned_to) as active_technicians
            FROM zayavki
            """
            system_stats = await conn.fetchrow(system_query)
            
            return {
                'users_by_role': [dict(row) for row in users_stats],
                'orders_by_status': [dict(row) for row in orders_stats],
                'today_orders': today_stats['today_orders'] if today_stats else 0,
                'today_completed': today_stats['today_completed'] if today_stats else 0,
                'pending_orders': today_stats['pending_orders'] if today_stats else 0,
                'total_users': system_stats['total_users'] if system_stats else 0,
                'total_orders': system_stats['total_orders'] if system_stats else 0,
                'active_technicians': system_stats['active_technicians'] if system_stats else 0
            }
        except Exception as e:
            logger.error(f"Error getting admin dashboard stats: {e}")
            return {}
        finally:
            pass

async def get_user_management_stats() -> Dict:
    """Get user management statistics"""
    async with bot.db.acquire() as conn:
        try:
            query = """
            SELECT 
                role,
                COUNT(*) as total,
                COUNT(CASE WHEN is_active = true THEN 1 END) as active,
                COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as new_this_week
            FROM users
            GROUP BY role
            ORDER BY total DESC
            """
            results = await conn.fetch(query)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return []
        finally:
            pass

async def search_users_by_criteria(search_type: str, search_value: Union[str, int]) -> List[Dict]:
    """Search users by different criteria"""
    async with bot.db.acquire() as conn:
        try:
            if search_type == 'telegram_id':
                # Convert to int if it's a string
                if isinstance(search_value, str):
                    try:
                        search_value = int(search_value)
                    except ValueError:
                        return []
                
                query = """
                SELECT *
                FROM users
                WHERE telegram_id = $1
                AND is_active = true
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query, search_value)
            elif search_type == 'full_name':
                query = """
                SELECT *
                FROM users
                WHERE full_name ILIKE $1
                AND is_active = true
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query, f"%{search_value}%")
            elif search_type == 'phone_number':
                query = """
                SELECT *
                FROM users
                WHERE phone_number ILIKE $1
                AND is_active = true
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query, f"%{search_value}%")
            elif search_type == 'role':
                query = """
                SELECT *
                FROM users
                WHERE role = $1
                AND is_active = true
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query, search_value)
            else:
                raise ValueError(f"Invalid search type: {search_type}")
            
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
        finally:
            pass

async def search_all_users_by_criteria(search_type: str, search_value: Union[str, int]) -> List[Dict]:
    """Search users by different criteria without is_active restriction"""
    async with bot.db.acquire() as conn:
        try:
            if search_type == 'telegram_id':
                # Convert to int if it's a string
                if isinstance(search_value, str):
                    try:
                        search_value = int(search_value)
                    except ValueError:
                        return []
                
                query = """
                SELECT *
                FROM users
                WHERE telegram_id = $1
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query, search_value)
            elif search_type == 'full_name':
                query = """
                SELECT *
                FROM users
                WHERE full_name ILIKE $1
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query, f"%{search_value}%")
            elif search_type == 'phone_number':
                query = """
                SELECT *
                FROM users
                WHERE phone_number ILIKE $1
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query, f"%{search_value}%")
            elif search_type == 'role':
                query = """
                SELECT *
                FROM users
                WHERE role = $1
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query, search_value)
            else:
                raise ValueError(f"Invalid search type: {search_type}")
            
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error searching all users: {e}")
            return []
        finally:
            pass

async def update_user_role(telegram_id: int, new_role: str, updated_by: int) -> bool:
    """Update user role with logging"""
    async with bot.db.acquire() as conn:
        try:
            # Get current role
            current_user = await conn.fetchrow(
                'SELECT role FROM users WHERE telegram_id = $1',
                telegram_id
            )
            
            if not current_user:
                return False
            
            old_role = current_user['role']
            
            # Check if trying to remove last admin
            if old_role == 'admin' and new_role != 'admin':
                admin_count = await conn.fetchval(
                    'SELECT COUNT(*) FROM users WHERE role = $1 AND telegram_id != $2',
                    'admin',
                    telegram_id
                )
                if admin_count < 1:
                    return False
            
            # Update role
            await conn.execute(
                'UPDATE users SET role = $1, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = $2',
                new_role,
                telegram_id
            )
            
            # Log role change
            await conn.execute(
                """
                INSERT INTO role_change_logs (user_telegram_id, old_role, new_role, changed_by, changed_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                """,
                telegram_id, old_role, new_role, updated_by
            )
            
            return True
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return False
        finally:
            pass

async def block_unblock_user(telegram_id: int, action: str, admin_id: int) -> bool:
    """Block or unblock user"""
    async with bot.db.acquire() as conn:
        try:
            # Get current user info
            user = await conn.fetchrow(
                'SELECT role, is_active FROM users WHERE telegram_id = $1',
                telegram_id
            )
            
            if not user:
                return False
            
            # For blocking
            if action == 'block':
                await conn.execute(
                    'UPDATE users SET is_active = false, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = $1',
                    telegram_id
                )
                status = 'blocked'
            else:  # unblock
                # Restore previous role when unblocking
                await conn.execute(
                    'UPDATE users SET is_active = true, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = $1',
                    telegram_id
                )
                status = 'unblocked'
            
            # Log action
            await conn.execute(
                """
                INSERT INTO user_action_logs (user_telegram_id, action, performed_by, performed_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                telegram_id, status, admin_id
            )
            
            return True
        except Exception as e:
            logger.error(f"Error {action}ing user: {e}")
            return False
        finally:
            pass

async def get_system_logs(log_type: str = 'all', limit: int = 50) -> List[Dict]:
    """Get system logs"""
    async with bot.db.acquire() as conn:
        try:
            if log_type == 'role_changes':
                query = """
                SELECT rcl.*, u1.full_name as user_name, u2.full_name as admin_name
                FROM role_change_logs rcl
                LEFT JOIN users u1 ON rcl.user_telegram_id = u1.telegram_id
                LEFT JOIN users u2 ON rcl.changed_by = u2.id
                ORDER BY rcl.changed_at DESC
                LIMIT $1
                """
            elif log_type == 'user_actions':
                query = """
                SELECT ual.*, u1.full_name as user_name, u2.full_name as admin_name
                FROM user_action_logs ual
                LEFT JOIN users u1 ON ual.user_telegram_id = u1.telegram_id
                LEFT JOIN users u2 ON ual.performed_by = u2.id
                ORDER BY ual.performed_at DESC
                LIMIT $1
                """
            else:  # all logs
                query = """
                SELECT 'role_change' as log_type, changed_at as timestamp, 
                       user_telegram_id, old_role || ' -> ' || new_role as details
                FROM role_change_logs
                UNION ALL
                SELECT 'user_action' as log_type, performed_at as timestamp,
                       user_telegram_id, action as details
                FROM user_action_logs
                ORDER BY timestamp DESC
                LIMIT $1
                """
            
            results = await conn.fetch(query, limit)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return []
        finally:
            pass

async def get_orders_management_stats() -> Dict:
    """Get orders management statistics"""
    async with bot.db.acquire() as conn:
        try:
            # Orders by status
            status_query = """
            SELECT status, COUNT(*) as count
            FROM zayavki
            GROUP BY status
            """
            status_stats = await conn.fetch(status_query)
            
            # Orders by date
            date_query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM zayavki
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """
            date_stats = await conn.fetch(date_query)
            
            # Unassigned orders
            unassigned_query = """
            SELECT COUNT(*) as count
            FROM zayavki
            WHERE assigned_to IS NULL AND status IN ('new', 'pending')
            """
            unassigned_count = await conn.fetchval(unassigned_query)
            
            # Overdue orders
            overdue_query = """
            SELECT COUNT(*) as count
            FROM zayavki
            WHERE status IN ('assigned', 'in_progress') 
            AND created_at < CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """
            overdue_count = await conn.fetchval(overdue_query)
            
            return {
                'by_status': [dict(row) for row in status_stats],
                'by_date': [dict(row) for row in date_stats],
                'unassigned': unassigned_count or 0,
                'overdue': overdue_count or 0
            }
        except Exception as e:
            logger.error(f"Error getting orders management stats: {e}")
            return {}
        finally:
            pass
async def get_filtered_orders(filters: Dict) -> List[Dict]:
    """Get filtered orders for admin management"""
    async with bot.db.acquire() as conn:
        try:
            conditions = []
            params = []
            param_count = 1
        
            base_query = """
            SELECT z.*, 
                   u.full_name as client_name, u.phone_number as client_phone,
                   t.full_name as technician_name, t.phone_number as technician_phone
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            LEFT JOIN users t ON z.assigned_to = t.id
            """
            
            if filters.get('status'):
                conditions.append(f"z.status = ${param_count}")
                params.append(filters['status'])
                param_count += 1
            
            if filters.get('date_from'):
                conditions.append(f"z.created_at >= ${param_count}")
                params.append(filters['date_from'])
                param_count += 1
            
            if filters.get('date_to'):
                conditions.append(f"z.created_at <= ${param_count}")
                params.append(filters['date_to'])
                param_count += 1
            
            if filters.get('technician_id'):
                if filters['technician_id'] == 0:  # Unassigned
                    conditions.append("z.assigned_to IS NULL")
                else:
                    conditions.append(f"z.assigned_to = ${param_count}")
                    params.append(filters['technician_id'])
                    param_count += 1
            
            if filters.get('priority'):
                conditions.append(f"z.priority = ${param_count}")
                params.append(filters['priority'])
                param_count += 1
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            query = f"{base_query} {where_clause} ORDER BY z.created_at DESC LIMIT 100"
            
            results = await conn.fetch(query, *params)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting filtered orders: {e}")
            return []
        finally:
            pass
async def bulk_assign_orders(order_ids: List[int], technician_id: int, admin_id: int) -> bool:
    """Bulk assign orders to technician"""
    async with bot.db.acquire() as conn:
        try:
            async with conn.transaction():
                for order_id in order_ids:
                    await conn.execute(
                        """
                        UPDATE zayavki 
                        SET assigned_to = $1, status = 'assigned', 
                            assigned_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                        """,
                        technician_id, order_id
                    )
                    
                    # Log assignment
                    await conn.execute(
                        """
                        INSERT INTO assignment_logs (order_id, technician_id, assigned_by, assigned_at)
                        VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                        """,
                        order_id, technician_id, admin_id
                    )
                return True
        except Exception as e:
            logger.error(f"Error bulk assigning orders: {e}")
            return False
        finally:
            pass

async def get_system_settings() -> Dict:
    """Get system settings"""
    async with bot.db.acquire() as conn:
        try:
            query = """
            SELECT setting_key, setting_value, description
            FROM system_settings
            ORDER BY setting_key
            """
            results = await conn.fetch(query)
            return {row['setting_key']: {
                'value': row['setting_value'],
                'description': row['description']
        } for row in results}
        except Exception as e:
            logger.error(f"Error getting system settings: {e}")
            return {}
        finally:
            pass
async def update_system_setting(setting_key: str, setting_value: str, admin_id: int) -> bool:
    """Update system setting"""
    async with bot.db.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO system_settings (setting_key, setting_value, updated_by, updated_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (setting_key)
            DO UPDATE SET 
                setting_value = EXCLUDED.setting_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = EXCLUDED.updated_at
            """,
            setting_key, setting_value, admin_id
        )
            return True
        except Exception as e:
            logger.error(f"Error updating system setting: {e}")
            return False
        finally:
            pass
async def get_notification_templates() -> List[Dict]:
    """Get notification templates"""
    async with bot.db.acquire() as conn:
        try:
            query = """
            SELECT * FROM notification_templates
            ORDER BY template_type, language
            """
            results = await conn.fetch(query)
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting notification templates: {e}")
            return []
        finally:
            pass

async def update_notification_template(template_id: int, content: str, admin_id: int) -> bool:
    """Update notification template"""
    async with bot.db.acquire() as conn:
        try:
            await conn.execute(
                """
                UPDATE notification_templates 
                SET content = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP
                WHERE id = $3
                """,
                content, admin_id, template_id
            )
            return True
        except Exception as e:
            logger.error(f"Error updating notification template: {e}")
            return False

async def get_performance_metrics(period: str = 'daily') -> Dict:
    """Get system performance metrics"""
    async with bot.db.acquire() as conn:
        try:
            if period == 'daily':
                date_filter = "DATE(created_at) = CURRENT_DATE"
            elif period == 'weekly':
                date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
            elif period == 'monthly':
                date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
            else:
                date_filter = "created_at >= CURRENT_DATE - INTERVAL '1 day'"
            
            # Order completion rate
            completion_query = f"""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders
            FROM orders 
            WHERE {date_filter}
            """
            completion_result = await conn.fetchrow(completion_query)
            
            # Average response time
            response_query = f"""
            SELECT 
                AVG(EXTRACT(EPOCH FROM (first_response_at - created_at))) as avg_response_time
            FROM orders 
            WHERE {date_filter} AND first_response_at IS NOT NULL
            """
            response_result = await conn.fetchrow(response_query)
            
            # Technician efficiency
            efficiency_query = f"""
            SELECT 
                t.id as technician_id,
                t.full_name,
                COUNT(*) as total_orders,
                AVG(EXTRACT(EPOCH FROM (completed_at - assigned_at))) as avg_completion_time
            FROM orders o
            JOIN users t ON o.technician_id = t.telegram_id
            WHERE {date_filter} AND o.status = 'completed'
            GROUP BY t.id, t.full_name
            ORDER BY avg_completion_time
            LIMIT 5
            """
            efficiency_results = await conn.fetch(efficiency_query)
            
            return {
                'order_completion_rate': {
                    'total_orders': completion_result['total_orders'],
                    'completed_orders': completion_result['completed_orders'],
                    'completion_rate': (completion_result['completed_orders'] / completion_result['total_orders'] * 100) if completion_result['total_orders'] > 0 else 0
                } if completion_result else None,
                'avg_response_time': response_result['avg_response_time'] if response_result else None,
                'top_technicians': [{
                    'technician_id': row['technician_id'],
                    'full_name': row['full_name'],
                    'total_orders': row['total_orders'],
                    'avg_completion_time': row['avg_completion_time']
                } for row in efficiency_results] if efficiency_results else None
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
        finally:
            pass
async def export_admin_data(export_type: str, filters: Dict = None) -> Optional[str]:
    """Export admin data to CSV"""
    async with bot.db.acquire() as conn:
        try:
            import csv
            import tempfile
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if export_type == 'users':
                query = """
                SELECT telegram_id, full_name, phone_number, role, 
                       is_active, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
                """
                results = await conn.fetch(query)
                
                # Create CSV file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
                    writer = csv.writer(tmp_file)
                    writer.writerow(['Telegram ID', 'Full Name', 'Phone Number', 'Role', 
                                   'Is Active', 'Created At', 'Updated At'])
                    for row in results:
                        writer.writerow([
                            row['telegram_id'],
                            row['full_name'],
                            row['phone_number'],
                            row['role'],
                            row['is_active'],
                            row['created_at'].isoformat(),
                            row['updated_at'].isoformat() if row['updated_at'] else ''
                        ])
                
                return tmp_file.name
            elif export_type == 'orders':
                query = """
                SELECT o.*, u.full_name as technician_name
                FROM orders o
                LEFT JOIN users u ON o.technician_id = u.telegram_id
                ORDER BY o.created_at DESC
                """
                results = await conn.fetch(query)
                
                # Create CSV file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
                    writer = csv.writer(tmp_file)
                    writer.writerow(['Order ID', 'Client Name', 'Technician Name', 'Status', 
                                   'Created At', 'Assigned At', 'Completed At', 'Description'])
                    for row in results:
                        writer.writerow([
                            row['id'],
                            row['client_name'],
                            row['technician_name'],
                            row['status'],
                            row['created_at'].isoformat(),
                            row['assigned_at'].isoformat() if row['assigned_at'] else '',
                            row['completed_at'].isoformat() if row['completed_at'] else '',
                            row['description']
                        ])
                
                return tmp_file.name
            else:
                return None
        except Exception as e:
            logger.error(f"Error exporting admin data: {e}")
            return None
        finally:
            pass
# ==================== ADMIN UTILITY FUNCTIONS ====================

async def is_admin(telegram_id: int) -> bool:
    """Check if user is admin"""
    try:
        conn = await asyncpg.connect(config.DATABASE_URL)
        result = await conn.fetchval("SELECT role FROM users WHERE telegram_id = $1", telegram_id)
        await conn.close()
        return result == 'admin'
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def has_admin_permissions(telegram_id: int, required_permissions: List[str] = None) -> bool:
    """Check if user has admin permissions"""
    async with bot.db.acquire() as conn:
        try:
            user = await conn.fetchrow(
                "SELECT role, permissions FROM users WHERE telegram_id = $1",
                str(telegram_id)
            )
            if not user or user['role'] != 'admin':
                return False
            if not required_permissions:
                return True
            user_permissions = user.get('permissions', [])
            if isinstance(user_permissions, str):
                user_permissions = json.loads(user_permissions)
            return all(perm in user_permissions for perm in required_permissions)
        except Exception as e:
            logger.error(f"Error checking admin permissions: {e}")
            return False
        finally:
            pass

async def log_admin_action(admin_id: int, action: str, details: Dict = None) -> bool:
    """Log admin action"""
    async with bot.db.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO admin_action_logs (admin_id, action, details, performed_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                admin_id, action, json.dumps(details) if details else None
            )
            return True
        except Exception as e:
            logger.error(f"Error logging admin action: {e}")
            return False
        finally:
            pass
