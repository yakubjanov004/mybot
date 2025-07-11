import asyncpg
from typing import List, Dict, Any, Optional

# Manager role uchun query funksiyalari

async def get_manager_statistics(pool: asyncpg.Pool) -> Dict[str, Any]:
    """Manager uchun umumiy statistika"""
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT COUNT(*) as total_orders, 
                   COUNT(DISTINCT assigned_to) as total_technicians,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders
            FROM zayavki
        """)
        return dict(result) if result else {}

async def get_manager_orders(manager_id: int, pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Managerga biriktirilgan zayavkalar ro'yxati"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM zayavki WHERE assigned_to = $1 ORDER BY created_at DESC
        """, manager_id)
        return [dict(row) for row in rows]

async def assign_technician_to_order(order_id: int, technician_id: int, pool: asyncpg.Pool) -> bool:
    """Manager buyurtmaga texnik biriktiradi"""
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE zayavki SET assigned_to = $1, status = 'assigned' WHERE id = $2
        """, technician_id, order_id)
        return True

async def get_manager_reports(period: str, pool: asyncpg.Pool) -> Dict[str, Any]:
    """Manager uchun hisobotlar (kunlik, haftalik, oylik)"""
    async with pool.acquire() as conn:
        if period == 'daily':
            query = "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed FROM zayavki WHERE DATE(created_at) = CURRENT_DATE"
        elif period == 'weekly':
            query = "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed FROM zayavki WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'monthly':
            query = "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed FROM zayavki WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'"
        else:
            return {}
        result = await conn.fetchrow(query)
        return dict(result) if result else {}

async def get_online_staff(pool: asyncpg.Pool, minutes_threshold: int = 15) -> List[Dict[str, Any]]:
    """
    Get list of online staff members based on their last activity
    
    Args:
        pool: Database connection pool
        minutes_threshold: Number of minutes to consider staff as online
    
    Returns:
        List of online staff members with their details
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.*, 
                   CASE 
                       WHEN u.last_activity_at > NOW() - INTERVAL '%s minutes' THEN 'online'
                       ELSE 'offline'
                   END as status
            FROM users u
            WHERE u.role IN ('technician', 'controller', 'call_center')
            ORDER BY u.last_activity_at DESC
        """, str(minutes_threshold))
        return [dict(row) for row in rows]

async def get_staff_performance(pool: asyncpg.Pool, period: str = 'monthly') -> List[Dict[str, Any]]:
    """
    Get staff performance metrics for the specified period
    
    Args:
        pool: Database connection pool
        period: Time period to calculate performance ('daily', 'weekly', 'monthly')
    
    Returns:
        List of staff performance metrics
    """
    async with pool.acquire() as conn:
        # Get date range based on period
        if period == 'daily':
            date_filter = "DATE(z.created_at) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "z.created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'monthly':
            date_filter = "z.created_at >= CURRENT_DATE - INTERVAL '30 days'"
        else:
            date_filter = "z.created_at >= CURRENT_DATE - INTERVAL '30 days'"

        # Get performance metrics
        rows = await conn.fetch("""
            SELECT 
                u.id,
                u.full_name,
                COUNT(z.id) as total_tasks,
                SUM(CASE WHEN z.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                AVG(CASE WHEN z.status = 'completed' THEN z.completion_time ELSE NULL END) as avg_completion_time,
                COUNT(CASE WHEN z.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_tasks,
                COUNT(CASE WHEN z.status = 'rejected' THEN 1 ELSE 0 END) as rejected_tasks
            FROM users u
            LEFT JOIN zayavki z ON u.id = z.assigned_to
            WHERE u.role = 'technician'
            AND {date_filter}
            GROUP BY u.id, u.full_name
            ORDER BY completed_tasks DESC
        """.format(date_filter=date_filter))
        
        # Calculate additional metrics
        results = []
        for row in rows:
            row_dict = dict(row)
            if row_dict['total_tasks'] > 0:
                row_dict['completion_rate'] = (row_dict['completed_tasks'] / row_dict['total_tasks']) * 100
            else:
                row_dict['completion_rate'] = 0
            results.append(row_dict)
        
        return results

async def get_staff_workload(pool: asyncpg.Pool, period: str = 'daily') -> List[Dict[str, Any]]:
    """
    Get staff workload distribution for the specified period
    
    Args:
        pool: Database connection pool
        period: Time period to calculate workload ('daily', 'weekly', 'monthly')
    
    Returns:
        List of staff workload metrics
    """
    async with pool.acquire() as conn:
        # Get date range based on period
        if period == 'daily':
            date_filter = "DATE(z.created_at) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "z.created_at >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'monthly':
            date_filter = "z.created_at >= CURRENT_DATE - INTERVAL '30 days'"
        else:
            date_filter = "z.created_at >= CURRENT_DATE - INTERVAL '30 days'"

        # Get workload distribution
        rows = await conn.fetch("""
            SELECT 
                u.id,
                u.full_name,
                COUNT(z.id) as total_tasks,
                COUNT(CASE WHEN z.status = 'new' THEN 1 ELSE NULL END) as pending_tasks,
                COUNT(CASE WHEN z.status = 'in_progress' THEN 1 ELSE NULL END) as in_progress_tasks,
                COUNT(CASE WHEN z.status = 'completed' THEN 1 ELSE NULL END) as completed_tasks,
                COUNT(CASE WHEN z.status = 'cancelled' THEN 1 ELSE NULL END) as cancelled_tasks,
                COUNT(CASE WHEN z.status = 'rejected' THEN 1 ELSE NULL END) as rejected_tasks,
                COUNT(CASE WHEN z.status = 'pending' THEN 1 ELSE NULL END) as pending_approval_tasks
            FROM users u
            LEFT JOIN zayavki z ON u.id = z.assigned_to
            WHERE u.role = 'technician'
            AND {date_filter}
            GROUP BY u.id, u.full_name
            ORDER BY total_tasks DESC
        """.format(date_filter=date_filter))
        
        # Calculate workload metrics
        results = []
        for row in rows:
            row_dict = dict(row)
            if row_dict['total_tasks'] > 0:
                row_dict['workload_percentage'] = (row_dict['pending_tasks'] + row_dict['in_progress_tasks']) * 100 / row_dict['total_tasks']
            else:
                row_dict['workload_percentage'] = 0
            results.append(row_dict)
        
        return results

async def get_users_by_role(pool: asyncpg.Pool, role: str) -> List[Dict[str, Any]]:
    """
    Get all users with the specified role
    
    Args:
        pool: Database connection pool
        role: User role to filter by
    
    Returns:
        List of users with the specified role
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM users 
            WHERE role = $1 
            ORDER BY full_name ASC
        """, role)
        return [dict(row) for row in rows]

async def get_filtered_applications(
    pool: asyncpg.Pool,
    statuses: list = None,
    date_from: str = None,
    date_to: str = None,
    assigned_only: bool = None,
    technician_id: int = None,
    page: int = 1,
    limit: int = 5
) -> dict:
    """
    Get filtered applications with pagination
    """
    async with pool.acquire() as conn:
        # Build base query
        query = """
            SELECT z.*, 
                   u.full_name as user_name,
                   u.phone_number as client_phone,
                   t.full_name as technician_name,
                   t.telegram_id as technician_telegram_id
            FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            LEFT JOIN users t ON z.assigned_to = t.id
            WHERE 1=1
        """
        params = []
        if statuses:
            status_filters = " OR ".join([f"z.status = '{status}'" for status in statuses])
            query += f" AND ({status_filters})"
        if date_from:
            query += f" AND z.created_at >= ${len(params)+1}"
            params.append(date_from)
        if date_to:
            query += f" AND z.created_at <= ${len(params)+1}"
            params.append(date_to)
        if assigned_only:
            query += f" AND z.assigned_to IS NOT NULL"
        if technician_id is not None:
            if technician_id == 0:
                query += f" AND z.assigned_to IS NULL"
            else:
                query += f" AND z.assigned_to = {technician_id}"
        query += f" ORDER BY z.created_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        offset = (page - 1) * limit
        params.extend([limit, offset])
        applications = await conn.fetch(query, *params)

        # COUNT query
        count_query = """
            SELECT COUNT(*) FROM zayavki z
            LEFT JOIN users u ON z.user_id = u.id
            LEFT JOIN users t ON z.assigned_to = t.id
            WHERE 1=1
        """
        count_params = []
        if statuses:
            count_query += f" AND ({status_filters})"
        if date_from:
            count_query += f" AND z.created_at >= ${len(count_params)+1}"
            count_params.append(date_from)
        if date_to:
            count_query += f" AND z.created_at <= ${len(count_params)+1}"
            count_params.append(date_to)
        if assigned_only:
            count_query += f" AND z.assigned_to IS NOT NULL"
        if technician_id is not None:
            if technician_id == 0:
                count_query += f" AND z.assigned_to IS NULL"
            else:
                count_query += f" AND z.assigned_to = {technician_id}"
        total_count = await conn.fetchval(count_query, *count_params)
        total_pages = (total_count + limit - 1) // limit if total_count else 1
        return {
            'applications': [dict(app) for app in applications],
            'total_pages': total_pages,
            'page': page,
            'total': total_count
        }

async def get_staff_attendance(pool: asyncpg.Pool, period: str = 'monthly') -> List[Dict[str, Any]]:
    """
    Get staff attendance metrics for the specified period
    
    Args:
        pool: Database connection pool
        period: Time period to calculate attendance ('daily', 'weekly', 'monthly')
    
    Returns:
        List of staff attendance metrics
    """
    async with pool.acquire() as conn:
        # Get date range based on period
        if period == 'daily':
            date_filter = "DATE(a.date) = CURRENT_DATE"
        elif period == 'weekly':
            date_filter = "a.date >= CURRENT_DATE - INTERVAL '7 days'"
        elif period == 'monthly':
            date_filter = "a.date >= CURRENT_DATE - INTERVAL '30 days'"
        else:
            date_filter = "a.date >= CURRENT_DATE - INTERVAL '30 days'"

        # Get attendance metrics
        rows = await conn.fetch("""
            SELECT 
                u.id,
                u.full_name,
                COUNT(DISTINCT a.date) as days_present,
                COUNT(DISTINCT CASE WHEN a.check_in IS NOT NULL THEN a.date END) as days_checked_in,
                COUNT(DISTINCT CASE WHEN a.check_out IS NOT NULL THEN a.date END) as days_checked_out,
                COUNT(DISTINCT CASE WHEN a.check_in IS NOT NULL AND a.check_out IS NOT NULL THEN a.date END) as complete_days,
                COUNT(DISTINCT CASE WHEN a.check_in IS NULL AND a.check_out IS NOT NULL THEN a.date END) as late_check_ins,
                COUNT(DISTINCT CASE WHEN a.check_in IS NOT NULL AND a.check_out IS NULL THEN a.date END) as early_check_outs
            FROM users u
            LEFT JOIN attendance a ON u.id = a.user_id
            WHERE u.role = 'technician'
            AND {date_filter}
            GROUP BY u.id, u.full_name
            ORDER BY days_present DESC
        """.format(date_filter=date_filter))
        
        # Calculate attendance metrics
        results = []
        for row in rows:
            row_dict = dict(row)
            if row_dict['days_present'] > 0:
                row_dict['attendance_rate'] = (row_dict['complete_days'] / row_dict['days_present']) * 100
                row_dict['late_rate'] = (row_dict['late_check_ins'] / row_dict['days_present']) * 100
                row_dict['early_rate'] = (row_dict['early_check_outs'] / row_dict['days_present']) * 100
            else:
                row_dict['attendance_rate'] = 0
                row_dict['late_rate'] = 0
                row_dict['early_rate'] = 0
            results.append(row_dict)
        
        return results

async def get_staff_activity(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Manager uchun xodimlar faolligi"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.id, u.full_name, COUNT(z.id) as total_tasks
            FROM users u
            LEFT JOIN zayavki z ON u.id = z.assigned_to
            WHERE u.role = 'technician'
            GROUP BY u.id, u.full_name
            ORDER BY total_tasks DESC
        """)
        return [dict(row) for row in rows]

async def get_equipment_list(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Manager uchun jihozlar ro'yxati"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM materials ORDER BY created_at DESC")
        return [dict(row) for row in rows]

async def get_manager_notifications(manager_id: int, pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Manager uchun bildirishnomalar"""
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM notifications WHERE user_id = $1 ORDER BY sent_at DESC", manager_id)
        return [dict(row) for row in rows]

async def get_manager_filters(pool: asyncpg.Pool) -> Dict[str, List[Any]]:
    """Manager uchun filtrlash variantlari"""
    async with pool.acquire() as conn:
        statuses = await conn.fetch("SELECT DISTINCT status FROM zayavki")
        types = await conn.fetch("SELECT DISTINCT zayavka_type FROM zayavki")
        return {
            'statuses': [row['status'] for row in statuses],
            'types': [row['zayavka_type'] for row in types]
        }

# Junior Manager uchun qo'shimcha funksiyalar
async def get_orders_for_junior_manager(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Kichik menejer uchun zayavkalarni olish"""
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    z.id,
                    z.description,
                    z.address,
                    z.status,
                    z.created_at,
                    z.assigned_to as assigned_technician_id,
                    u.full_name as client_name,
                    u.phone_number as client_phone,
                    t.full_name as technician_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users t ON z.assigned_to = t.id
                WHERE z.status != 'deleted'
                ORDER BY z.created_at DESC
                LIMIT 50
            """
            result = await conn.fetch(query)
            return [dict(row) for row in result]
    except Exception as e:
        print(f"Error in get_orders_for_junior_manager: {e}")
        return []

async def assign_order_to_technician(order_id: int, technician_id: int, assigned_by: int, pool: asyncpg.Pool) -> bool:
    """Zayavkani texnikka tayinlash"""
    try:
        async with pool.acquire() as conn:
            # Zayavkani yangilash
            update_query = """
                UPDATE zayavki 
                SET assigned_to = $1, 
                    status = 'assigned',
                    updated_at = NOW()
                WHERE id = $2
            """
            await conn.execute(update_query, technician_id, order_id)
            
            # Log qo'shish
            log_query = """
                INSERT INTO order_logs (order_id, action, user_id, details, created_at)
                VALUES ($1, 'assigned', $2, $3, NOW())
            """
            await conn.execute(log_query, order_id, assigned_by, f"Assigned to technician {technician_id}")
            
            return True
    except Exception as e:
        print(f"Error in assign_order_to_technician: {e}")
        return False

async def get_available_technicians(pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Mavjud texniklarni olish"""
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT id, full_name as name, phone_number as phone, telegram_id
                FROM users 
                WHERE role = 'technician' 
                AND is_active = true
                ORDER BY full_name
            """
            result = await conn.fetch(query)
            return [dict(row) for row in result]
    except Exception as e:
        print(f"Error in get_available_technicians: {e}")
        return []

async def get_order_details(order_id: int, pool: asyncpg.Pool) -> Optional[Dict[str, Any]]:
    """Zayavka tafsilotlarini olish"""
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    z.id,
                    z.description,
                    z.address,
                    z.status,
                    z.created_at,
                    z.assigned_to as assigned_technician_id,
                    u.full_name as client_name,
                    u.phone_number as client_phone,
                    t.full_name as assigned_technician
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users t ON z.assigned_to = t.id
                WHERE z.id = $1
            """
            result = await conn.fetchrow(query, order_id)
            return dict(result) if result else None
    except Exception as e:
        print(f"Error in get_order_details: {e}")
        return None

async def get_filtered_orders(filter_type: str, pool: asyncpg.Pool) -> List[Dict[str, Any]]:
    """Filtr bo'yicha zayavkalarni olish"""
    try:
        async with pool.acquire() as conn:
            base_query = """
                SELECT 
                    z.id,
                    z.description,
                    z.status,
                    z.created_at
                FROM zayavki z
                WHERE z.status != 'deleted'
            """
            
            if filter_type == 'new':
                query = base_query + " AND z.status = 'new'"
            elif filter_type == 'assigned':
                query = base_query + " AND z.status = 'assigned'"
            elif filter_type == 'in_progress':
                query = base_query + " AND z.status = 'in_progress'"
            elif filter_type == 'completed':
                query = base_query + " AND z.status = 'completed'"
            elif filter_type == 'cancelled':
                query = base_query + " AND z.status = 'cancelled'"
            elif filter_type == 'today':
                query = base_query + " AND DATE(z.created_at) = CURRENT_DATE"
            elif filter_type == 'yesterday':
                query = base_query + " AND DATE(z.created_at) = CURRENT_DATE - INTERVAL '1 day'"
            else:
                query = base_query
            
            query += " ORDER BY z.created_at DESC"
            result = await conn.fetch(query)
            return [dict(row) for row in result]
    except Exception as e:
        print(f"Error in get_filtered_orders: {e}")
        return []

async def get_junior_manager_reports(pool: asyncpg.Pool) -> Dict[str, Any]:
    """Kichik menejer uchun hisobot ma'lumotlari"""
    try:
        async with pool.acquire() as conn:
            # Jami zayavkalar
            total_query = "SELECT COUNT(*) FROM zayavki WHERE status != 'deleted'"
            total_orders = await conn.fetchval(total_query)
            
            # Status bo'yicha zayavkalar
            status_query = """
                SELECT status, COUNT(*) as count
                FROM zayavki 
                WHERE status != 'deleted'
                GROUP BY status
            """
            status_counts = await conn.fetch(status_query)
            status_dict = {row['status']: row['count'] for row in status_counts}
            
            # Bugungi va kechagi zayavkalar
            today_query = "SELECT COUNT(*) FROM zayavki WHERE DATE(created_at) = CURRENT_DATE"
            today_orders = await conn.fetchval(today_query)
            
            yesterday_query = "SELECT COUNT(*) FROM zayavki WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'"
            yesterday_orders = await conn.fetchval(yesterday_query)
            
            return {
                'total_orders': total_orders,
                'new_orders': status_dict.get('new', 0),
                'assigned_orders': status_dict.get('assigned', 0),
                'in_progress_orders': status_dict.get('in_progress', 0),
                'completed_orders': status_dict.get('completed', 0),
                'cancelled_orders': status_dict.get('cancelled', 0),
                'today_orders': today_orders,
                'yesterday_orders': yesterday_orders
            }
    except Exception as e:
        print(f"Error in get_junior_manager_reports: {e}")
        return {
            'total_orders': 0,
            'new_orders': 0,
            'assigned_orders': 0,
            'in_progress_orders': 0,
            'completed_orders': 0,
            'cancelled_orders': 0,
            'today_orders': 0,
            'yesterday_orders': 0
        }

async def get_technician_by_id(technician_id: int, pool: asyncpg.Pool) -> Optional[Dict[str, Any]]:
    """Texnik ma'lumotlarini ID bo'yicha olish"""
    try:
        async with pool.acquire() as conn:
            query = """
                SELECT id, full_name, phone_number, telegram_id
                FROM users 
                WHERE id = $1 AND role = 'technician'
            """
            result = await conn.fetchrow(query, technician_id)
            return dict(result) if result else None
    except Exception as e:
        print(f"Error in get_technician_by_id: {e}")
        return None

async def get_order_address(order_id: int, pool: asyncpg.Pool) -> Optional[str]:
    """Zayavka manzilini olish"""
    try:
        async with pool.acquire() as conn:
            query = "SELECT address FROM zayavki WHERE id = $1"
            result = await conn.fetchval(query, order_id)
            return result
    except Exception as e:
        print(f"Error in get_order_address: {e}")
        return None 