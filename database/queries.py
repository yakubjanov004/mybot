from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
import logging
from utils.logger import logger
import asyncpg
from contextlib import asynccontextmanager

class DatabaseManager:
    """Database connection manager"""
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    def set_pool(self, pool: asyncpg.Pool) -> None:
        """Set database pool"""
        self._pool = pool
        logger.info("Database pool set successfully")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection with proper error handling"""
        if not self._pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self._pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                logger.error(f"Database operation error: {str(e)}", exc_info=True)
                raise

# Global database manager instance
db_manager = DatabaseManager()

def set_pool(pool: asyncpg.Pool) -> None:
    """Set the database pool"""
    db_manager.set_pool(pool)

async def safe_db_operation(operation_name: str, operation_func):
    """Safe database operation wrapper"""
    try:
        return await operation_func()
    except Exception as e:
        logger.error(f"{operation_name} error: {str(e)}", exc_info=True)
        raise

logger = logging.getLogger(__name__)

# Users queries
async def get_user_by_telegram_id(telegram_id: int) -> Optional[asyncpg.Record]:
    """Get user by telegram ID with proper error handling"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_id
            )
            logger.info(f"get_user_by_telegram_id: {telegram_id}, result: {bool(user)}")
            return user
    
    return await safe_db_operation("get_user_by_telegram_id", _operation)

async def create_user(telegram_id: int, full_name: str, role: str = 'client') -> Dict[str, Any]:
    """Create new user with validation"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            user = await conn.fetchrow('''
                INSERT INTO users (telegram_id, full_name, role)
                VALUES ($1, $2, $3)
                RETURNING *
            ''', telegram_id, full_name, role)
            logger.info(f"create_user: {telegram_id}, {full_name}, {role}")
            return dict(user)
    return await safe_db_operation("create_user", _operation)

async def update_user_language(telegram_id: int, language: str) -> None:
    """Update user language"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            await conn.execute(
                "UPDATE users SET language = $1 WHERE telegram_id = $2",
                language, telegram_id
            )
            logger.info(f"User language updated: {telegram_id} -> {language}")
    
    await safe_db_operation("update_user_language", _operation)

async def update_user_phone(user_id: int, phone_number: str) -> None:
    async def _operation():
        async with db_manager.get_connection() as conn:
            await conn.execute(
                'UPDATE users SET phone_number = $1 WHERE id = $2',
                phone_number, user_id
            )
    await safe_db_operation("update_user_phone", _operation)

# Zayavki queries
async def create_zayavka(user_id: int, description: str, address: Optional[str] = None) -> Dict[str, Any]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                INSERT INTO zayavki (user_id, description, address)
                VALUES ($1, $2, $3)
                RETURNING *
            ''', user_id, description, address)
            return dict(result) if result else None
    return await safe_db_operation("create_zayavka", _operation)

async def get_zayavka_by_id(zayavka_id: int) -> Optional[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                SELECT z.*, u.full_name as user_name, u.phone_number as phone_number, a.full_name as assigned_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                WHERE z.id = $1
            ''', zayavka_id)
            return dict(result) if result else None
    return await safe_db_operation("get_zayavka_by_id", _operation)

async def update_zayavka_status(zayavka_id: int, new_status: str, changed_by: int) -> None:
    async def _operation():
        async with db_manager.get_connection() as conn:
            async with conn.transaction():
                old_status = await conn.fetchval(
                    'SELECT status FROM zayavki WHERE id = $1',
                    zayavka_id
                )
                
                await conn.execute(
                    'UPDATE zayavki SET status = $1 WHERE id = $2',
                    new_status, zayavka_id
                )
                
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
                    VALUES ($1, $2, $3, $4)
                ''', zayavka_id, changed_by, old_status, new_status)
    await safe_db_operation("update_zayavka_status", _operation)

async def assign_zayavka(zayavka_id: int, assigned_to: int) -> None:
    async def _operation():
        async with db_manager.get_connection() as conn:
            await conn.execute(
                'UPDATE zayavki SET assigned_to = $1 WHERE id = $2',
                assigned_to, zayavka_id
            )
    await safe_db_operation("assign_zayavka", _operation)

async def mark_zayavka_ready(zayavka_id: int) -> None:
    async def _operation():
        async with db_manager.get_connection() as conn:
            await conn.execute(
                'UPDATE zayavki SET ready_to_install = TRUE WHERE id = $1',
                zayavka_id
            )
    await safe_db_operation("mark_zayavka_ready", _operation)

# Materials queries
async def get_materials() -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch(
                'SELECT * FROM materials ORDER BY name'
            )
            return [dict(row) for row in result]
    return await safe_db_operation("get_materials", _operation)

async def update_material_stock(material_id: int, quantity: int) -> None:
    async def _operation():
        async with db_manager.get_connection() as conn:
            await conn.execute(
                'UPDATE materials SET stock = stock + $1 WHERE id = $2',
                quantity, material_id
            )
    await safe_db_operation("update_material_stock", _operation)

async def get_materials_by_category(category: str) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT * FROM materials 
                WHERE category = $1 
                ORDER BY name
            ''', category)
            return [dict(row) for row in result]
    return await safe_db_operation("get_materials_by_category", _operation)

async def get_low_stock_materials(threshold: int = 5) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT * FROM materials 
                WHERE stock <= $1 
                ORDER BY stock ASC
            ''', threshold)
            return [dict(row) for row in result]
    return await safe_db_operation("get_low_stock_materials", _operation)

# Solutions queries
async def create_solution(zayavka_id: int, instander_id: int, solution_text: str) -> Dict[str, Any]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                INSERT INTO solutions (zayavka_id, instander_id, solution_text)
                VALUES ($1, $2, $3)
                RETURNING *
            ''', zayavka_id, instander_id, solution_text)
            return dict(result) if result else None
    return await safe_db_operation("create_solution", _operation)

async def get_zayavka_solutions(zayavka_id: int) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT s.*, u.full_name as instander_name 
                FROM solutions s
                JOIN users u ON s.instander_id = u.id
                WHERE s.zayavka_id = $1 
                ORDER BY s.created_at DESC
            ''', zayavka_id)
            return [dict(row) for row in result]
    return await safe_db_operation("get_zayavka_solutions", _operation)

# Feedback queries
async def create_feedback(zayavka_id: int, user_id: int, rating: int, comment: Optional[str] = None) -> Dict[str, Any]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                INSERT INTO feedback (zayavka_id, user_id, rating, comment)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            ''', zayavka_id, user_id, rating, comment)
            return dict(result) if result else None
    return await safe_db_operation("create_feedback", _operation)

async def get_zayavka_feedback(zayavka_id: int) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT f.*, u.full_name as user_name 
                FROM feedback f
                JOIN users u ON f.user_id = u.id
                WHERE f.zayavka_id = $1 
                ORDER BY f.created_at DESC
            ''', zayavka_id)
            return [dict(row) for row in result]
    return await safe_db_operation("get_zayavka_feedback", _operation)

# Notifications queries
async def create_notification(user_id: int, message: str, channel: str = 'telegram', zayavka_id: Optional[int] = None) -> Dict[str, Any]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                INSERT INTO notifications (user_id, zayavka_id, message, channel)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            ''', user_id, zayavka_id, message, channel)
            return dict(result) if result else None
    return await safe_db_operation("create_notification", _operation)

async def get_user_notifications(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT * FROM notifications 
                WHERE user_id = $1 
                ORDER BY sent_at DESC 
                LIMIT $2
            ''', user_id, limit)
            return [dict(row) for row in result]
    return await safe_db_operation("get_user_notifications", _operation)

# Login logs queries
async def create_login_log(user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                INSERT INTO login_logs (user_id, ip_address, user_agent)
                VALUES ($1, $2, $3)
                RETURNING *
            ''', user_id, ip_address, user_agent)
            return dict(result) if result else None
    return await safe_db_operation("create_login_log", _operation)

# Issued items queries
async def get_zayavka_issued_items(zayavka_id: int) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT i.*, m.name as material_name, u.full_name as issued_by_name 
                FROM issued_items i
                JOIN materials m ON i.material_id = m.id
                JOIN users u ON i.issued_by = u.id
                WHERE i.zayavka_id = $1 
                ORDER BY i.issued_at DESC
            ''', zayavka_id)
            return [dict(row) for row in result]
    return await safe_db_operation("get_zayavka_issued_items", _operation)

# Additional queries for zayavki
async def get_user_zayavki(user_id: int) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT z.*, u.full_name as user_name, a.full_name as assigned_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                WHERE z.user_id = $1 
                ORDER BY z.created_at DESC
            ''', user_id)
            return [dict(row) for row in result]
    return await safe_db_operation("get_user_zayavki", _operation)

async def get_zayavki_by_status(status: str) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT z.*, u.full_name as user_name, a.full_name as assigned_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                WHERE z.status = $1 
                ORDER BY z.created_at DESC
            ''', status)
            return [dict(row) for row in result]
    return await safe_db_operation("get_zayavki_by_status", _operation)

async def get_zayavki_by_assigned(assigned_to: int) -> List[Dict[str, Any]]:
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT z.*, u.full_name as user_name, a.full_name as assigned_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                WHERE z.assigned_to = $1 
                ORDER BY z.created_at DESC
            ''', assigned_to)
            return [dict(row) for row in result]
    return await safe_db_operation("get_zayavki_by_assigned", _operation)

async def create_tables(pool):
    """Create all necessary database tables"""
    async def _operation():
        async with pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    full_name TEXT,
                    username TEXT,
                    phone_number TEXT,
                    role VARCHAR(20) DEFAULT 'client',
                    abonent_id VARCHAR(50),
                    language VARCHAR(2) DEFAULT 'uz',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS zayavki (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(id),
                    description TEXT,
                    media TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    address TEXT,
                    assigned_to BIGINT REFERENCES users(id),
                    ready_to_install BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS materials (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    stock INTEGER DEFAULT 0,
                    ready_to_install BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS solutions (
                    id SERIAL PRIMARY KEY,
                    zayavka_id INTEGER REFERENCES zayavki(id),
                    instander_id INTEGER REFERENCES users(id),
                    solution_text TEXT,
                    media TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    zayavka_id INTEGER REFERENCES zayavki(id),
                    user_id INTEGER REFERENCES users(id),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS status_logs (
                    id SERIAL PRIMARY KEY,
                    zayavka_id INTEGER REFERENCES zayavki(id),
                    changed_by INTEGER REFERENCES users(id),
                    old_status VARCHAR(20),
                    new_status VARCHAR(20),
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS issued_items (
                    id SERIAL PRIMARY KEY,
                    zayavka_id INTEGER REFERENCES zayavki(id),
                    material_id INTEGER REFERENCES materials(id),
                    quantity INTEGER,
                    issued_by INTEGER REFERENCES users(id),
                    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS login_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    ip_address TEXT,
                    user_agent TEXT,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    zayavka_id INTEGER REFERENCES zayavki(id),
                    message TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    channel VARCHAR(10)
                );

                CREATE TABLE IF NOT EXISTS zayavka_transfers (
                    id SERIAL PRIMARY KEY,
                    zayavka_id BIGINT REFERENCES zayavki(id),
                    from_technician_id BIGINT REFERENCES users(id),
                    to_technician_id BIGINT REFERENCES users(id),
                    transferred_by BIGINT REFERENCES users(id), -- menejer
                    reason TEXT,
                    transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS technician_workload (
                    id SERIAL PRIMARY KEY,
                    technician_id BIGINT REFERENCES users(id),
                    active_tasks INTEGER DEFAULT 0,
                    max_tasks INTEGER DEFAULT 5, -- maksimal vazifalar soni
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS technician_performance (
                    id SERIAL PRIMARY KEY,
                    technician_id BIGINT REFERENCES users(id),
                    completed_tasks INTEGER DEFAULT 0,
                    average_completion_time DECIMAL(5,2), -- soatlarda
                    rating DECIMAL(3,2) DEFAULT 5.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
    await safe_db_operation("create_tables", _operation)

async def add_missing_columns():
    """Add missing columns to tables if they don't exist"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            # Add columns to zayavki table and other schema changes
            await conn.execute('''
                DO $$ 
                BEGIN
                    -- Add latitude column if it doesn't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name = 'zayavki' AND column_name = 'latitude') THEN
                        ALTER TABLE zayavki ADD COLUMN latitude DECIMAL(10, 8);
                    END IF;

                    -- Add longitude column if it doesn't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name = 'zayavki' AND column_name = 'longitude') THEN
                        ALTER TABLE zayavki ADD COLUMN longitude DECIMAL(11, 8);
                    END IF;

                    -- Add zayavka_type column if it doesn't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name = 'zayavki' AND column_name = 'zayavka_type') THEN
                        ALTER TABLE zayavki ADD COLUMN zayavka_type VARCHAR(50);
                    END IF;

                    -- Add abonent_id column if it doesn't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name = 'zayavki' AND column_name = 'abonent_id') THEN
                        ALTER TABLE zayavki ADD COLUMN abonent_id VARCHAR(50);
                    END IF;

                    -- Add ready_to_install column to materials if it doesn't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name = 'materials' AND column_name = 'ready_to_install') THEN
                        ALTER TABLE materials ADD COLUMN ready_to_install BOOLEAN DEFAULT FALSE;
                    END IF;

                    -- Update status check constraint if it doesn't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                                 WHERE table_name = 'zayavki' AND constraint_name = 'zayavki_status_check') THEN
                        ALTER TABLE zayavki ADD CONSTRAINT zayavki_status_check 
                            CHECK (status IN ('new', 'pending', 'in_progress', 'completed', 'cancelled'));
                    END IF;

                    -- Add or update users role check constraint
                    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                             WHERE table_name = 'users' AND constraint_name = 'users_role_check') THEN
                        ALTER TABLE users DROP CONSTRAINT users_role_check;
                    END IF;
                    ALTER TABLE users ADD CONSTRAINT users_role_check 
                        CHECK (role IN (
                            'admin', 'technician', 'client', 'blocked',
                            'call_center', 'manager', 'controller', 'warehouse'
                        ));
                END $$;
            ''')

            # Fix data types for large IDs (run as a separate DO block)
            await conn.execute('''
                DO $$
                BEGIN
                    -- Ensure assigned_to column is BIGINT
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'zayavki' AND column_name = 'assigned_to' 
                             AND data_type = 'integer') THEN
                        ALTER TABLE zayavki ALTER COLUMN assigned_to TYPE BIGINT;
                    END IF;

                    -- Ensure user_id in zayavki is BIGINT
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'zayavki' AND column_name = 'user_id' 
                             AND data_type = 'integer') THEN
                        ALTER TABLE zayavki ALTER COLUMN user_id TYPE BIGINT;
                    END IF;

                    -- Ensure changed_by in status_logs is BIGINT
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'status_logs' AND column_name = 'changed_by' 
                             AND data_type = 'integer') THEN
                        ALTER TABLE status_logs ALTER COLUMN changed_by TYPE BIGINT;
                    END IF;

                    -- Ensure other ID fields are BIGINT where needed
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'solutions' AND column_name = 'instander_id' 
                             AND data_type = 'integer') THEN
                        ALTER TABLE solutions ALTER COLUMN instander_id TYPE BIGINT;
                    END IF;

                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'feedback' AND column_name = 'user_id' 
                             AND data_type = 'integer') THEN
                        ALTER TABLE feedback ALTER COLUMN user_id TYPE BIGINT;
                    END IF;

                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'issued_items' AND column_name = 'issued_by' 
                             AND data_type = 'integer') THEN
                        ALTER TABLE issued_items ALTER COLUMN issued_by TYPE BIGINT;
                    END IF;

                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'login_logs' AND column_name = 'user_id' 
                             AND data_type = 'integer') THEN
                        ALTER TABLE login_logs ALTER COLUMN user_id TYPE BIGINT;
                    END IF;

                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'notifications' AND column_name = 'user_id' 
                             AND data_type = 'integer') THEN
                        ALTER TABLE notifications ALTER COLUMN user_id TYPE BIGINT;
                    END IF;
                END $$;
            ''')
            logger.info("Data types fixed for large IDs")
            logger.info("Missing columns added successfully")
    await safe_db_operation("add_missing_columns", _operation)

async def get_staff_members() -> List[Dict[str, Any]]:
    """Get all staff members (users with roles other than 'client' and 'blocked')"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT id, full_name, role, telegram_id
                FROM users 
                WHERE role IN ('admin', 'call_center', 'technician', 'manager', 'controller', 'warehouse')
                ORDER BY role, full_name
            ''')
            return [dict(row) for row in result]
    return await safe_db_operation("get_staff_members", _operation)

async def create_application(description: str, user_id: int, created_by_role: str = None) -> Dict[str, Any]:
    """Create a new application"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                INSERT INTO zayavki (description, user_id, status, created_by_role)
                VALUES ($1, $2, 'new', $3)
                RETURNING *
            ''', description, user_id, created_by_role)
            return dict(result) if result else None
    return await safe_db_operation("create_application", _operation)

async def get_applications() -> List[Dict[str, Any]]:
    """Get all applications with detailed information"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT 
                    z.*,
                    u.full_name as user_name,
                    u.phone_number as user_phone,
                    t.full_name as technician_name,
                    t.phone_number as technician_phone,
                    z.created_at as created_time,
                    (
                        SELECT changed_at 
                        FROM status_logs 
                        WHERE zayavka_id = z.id 
                        AND new_status = 'assigned'
                        ORDER BY changed_at DESC 
                        LIMIT 1
                    ) as assigned_time,
                    (
                        SELECT changed_at 
                        FROM status_logs 
                        WHERE zayavka_id = z.id 
                        AND new_status = 'accepted'
                        ORDER BY changed_at DESC 
                        LIMIT 1
                    ) as accepted_time,
                    (
                        SELECT changed_at 
                        FROM status_logs 
                        WHERE zayavka_id = z.id 
                        AND new_status = 'in_progress'
                        ORDER BY changed_at DESC 
                        LIMIT 1
                    ) as started_time,
                    (
                        SELECT changed_at 
                        FROM status_logs 
                        WHERE zayavka_id = z.id 
                        AND new_status = 'completed'
                        ORDER BY changed_at DESC 
                        LIMIT 1
                    ) as completed_time
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users t ON z.assigned_to = t.id
                ORDER BY z.created_at DESC
            ''')
            return [dict(row) for row in result]
    return await safe_db_operation("get_applications", _operation)

async def assign_responsible(application_id: int, user_id: int) -> None:
    """Assign responsible person to application"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            await conn.execute('''
                UPDATE zayavki 
                SET assigned_to = $1
                WHERE id = $2
            ''', user_id, application_id)
    await safe_db_operation("assign_responsible", _operation)

async def get_equipment_list() -> List[Dict[str, Any]]:
    """Get list of available equipment"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT * FROM materials
                WHERE stock > 0
                ORDER BY name
            ''')
            return [dict(row) for row in result]
    return await safe_db_operation("get_equipment_list", _operation)

async def mark_equipment_ready(equipment_id: int) -> None:
    """Mark equipment as ready for installation"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            await conn.execute('''
                UPDATE materials 
                SET ready_to_install = true
                WHERE id = $1
            ''', equipment_id)
    await safe_db_operation("mark_equipment_ready", _operation)

async def get_equipment_applications() -> List[Dict[str, Any]]:
    """Get applications with equipment"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT z.*, m.name as equipment_name, u.full_name as user_name
                FROM zayavki z
                JOIN issued_items i ON z.id = i.zayavka_id
                JOIN materials m ON i.material_id = m.id
                JOIN users u ON z.user_id = u.id
                ORDER BY z.created_at DESC
            ''')
            return [dict(row) for row in result]
    return await safe_db_operation("get_equipment_applications", _operation)

async def update_application_status(application_id: int, new_status: str) -> None:
    """Update application status"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            # Avval eski statusni olish
            old_status = await conn.fetchval('''
                SELECT status FROM zayavki WHERE id = $1
            ''', application_id)

            # Statusni yangilash
            await conn.execute('''
                UPDATE zayavki 
                SET status = $1::VARCHAR(20),
                    completed_at = CASE WHEN $1::VARCHAR(20) = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END
                WHERE id = $2
            ''', new_status, application_id)

            # Status o'zgarish logini saqlash
            if old_status != new_status:
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, old_status, new_status)
                    VALUES ($1, $2, $3::VARCHAR(20))
                ''', application_id, old_status, new_status)
    await safe_db_operation("update_application_status", _operation)

# CRM Integration Functions

async def get_available_technicians() -> List[Dict[str, Any]]:
    """Bo'sh technicianlari olish"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT u.id, u.full_name, u.telegram_id,
                       COUNT(z.id) as active_tasks
                FROM users u
                LEFT JOIN zayavki z ON u.id = z.assigned_to 
                    AND z.status IN ('assigned', 'in_progress')
                WHERE u.role = 'technician'
                GROUP BY u.id, u.full_name, u.telegram_id
                ORDER BY active_tasks ASC, u.full_name
            ''')
            return [dict(row) for row in result]
    return await safe_db_operation("get_available_technicians", _operation)

async def assign_zayavka_to_technician(zayavka_id: int, technician_id: int, assigned_by: int) -> None:
    """Zayavkani technicianga biriktirish"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            async with conn.transaction():
                # Zayavka statusini yangilash
                await conn.execute('''
                    UPDATE zayavki 
                    SET assigned_to = $1, status = 'assigned'
                    WHERE id = $2
                ''', technician_id, zayavka_id)
                
                # Status log yaratish
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
                    VALUES ($1, $2, 'assigned', 'in_progress')
                ''', zayavka_id, assigned_by)
                
        logger.info(f"Zayavka {zayavka_id} technician {technician_id}ga biriktirildi")
    await safe_db_operation("assign_zayavka_to_technician", _operation)

async def get_technician_tasks(technician_id: int) -> List[Dict[str, Any]]:
    """Technician vazifalarini olish"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
                FROM zayavki z
                JOIN users u ON z.user_id = u.id
                WHERE z.assigned_to = $1 
                    AND z.status IN ('assigned', 'accepted', 'in_progress')
                ORDER BY z.created_at ASC
            ''', technician_id)
            return [dict(row) for row in result]
    return await safe_db_operation("get_technician_tasks", _operation)

async def start_task(zayavka_id: int, technician_id: int) -> None:
    """Vazifani boshlash"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            async with conn.transaction():
                await conn.execute('''
                    UPDATE zayavki 
                    SET status = 'in_progress'
                    WHERE id = $1 AND assigned_to = $2
                ''', int(zayavka_id), int(technician_id))
                
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
                    VALUES ($1, $2, 'accepted', 'in_progress')
                ''', int(zayavka_id), int(technician_id))
                
        logger.info(f"Task {zayavka_id} started by technician {technician_id}")
    await safe_db_operation("start_task", _operation)

async def accept_task(zayavka_id: int, technician_id: int) -> None:
    """Vazifani qabul qilish (boshlashsiz)"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            async with conn.transaction():
                await conn.execute('''
                    UPDATE zayavki 
                    SET status = 'accepted'
                    WHERE id = $1 AND assigned_to = $2
                ''', int(zayavka_id), int(technician_id))
                
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
                    VALUES ($1, $2, 'assigned', 'accepted')
                ''', int(zayavka_id), int(technician_id))
                
        logger.info(f"Task {zayavka_id} accepted by technician {technician_id}")
    await safe_db_operation("accept_task", _operation)

async def complete_task(zayavka_id: int, technician_id: int, solution_text: str = None) -> Dict[str, Any]:
    """Vazifani yakunlash"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            async with conn.transaction():
                # Zayavka ma'lumotlarini olish
                zayavka = await conn.fetchrow('''
                    SELECT z.*, u.full_name as client_name, u.telegram_id as client_telegram_id
                    FROM zayavki z
                    JOIN users u ON z.user_id = u.id
                    WHERE z.id = $1
                ''', zayavka_id)
                
                # Status yangilash
                # Fetch old status first
                old_status = zayavka['status'] if zayavka else None
                await conn.execute('''
                    UPDATE zayavki 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE id = $1 AND assigned_to = $2
                ''', zayavka_id, technician_id)
                
                # Status log
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
                    VALUES ($1, $2, $3, $4)
                ''', zayavka_id, technician_id, old_status, 'completed')
                
                # Solution qo'shish
                if solution_text:
                    await conn.execute('''
                        INSERT INTO solutions (zayavka_id, instander_id, solution_text)
                        VALUES ($1, $2, $3)
                    ''', zayavka_id, technician_id, solution_text)
                
                return dict(zayavka) if zayavka else None
    return await safe_db_operation("complete_task", _operation)

async def request_task_transfer(zayavka_id: int, technician_id: int, reason: str) -> None:
    """Vazifani o'tkazish so'rovi"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            await conn.execute('''
                INSERT INTO notifications (user_id, zayavka_id, message, channel)
                SELECT u.id, $1, $2, 'telegram'
                FROM users u
                WHERE u.role = 'manager'
            ''', zayavka_id, f"Transfer so'rovi: {reason}")
        
        logger.info(f"Transfer request created for zayavka {zayavka_id}")
    await safe_db_operation("request_task_transfer", _operation)

async def get_managers_telegram_ids() -> List[Dict[str, Any]]:
    """Menejerlar telegram ID va language larini olish"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT telegram_id, language FROM users WHERE role = 'manager'
            ''')
            return [dict(row) for row in result]
    return await safe_db_operation("get_managers_telegram_ids", _operation)

async def get_orders_by_status(statuses: list) -> List[Dict[str, Any]]:
    """Get orders by status list"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            placeholders = ','.join([f'${i+1}' for i in range(len(statuses))])
            result = await conn.fetch(f'''
                SELECT z.*, u.full_name as client_name, a.full_name as assigned_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                WHERE z.status = ANY($1::text[])
                ORDER BY z.created_at DESC
            ''', statuses)
            return [dict(row) for row in result]
    return await safe_db_operation("get_orders_by_status", _operation)

async def get_all_orders(limit: int = 50) -> List[Dict[str, Any]]:
    """Get all orders with limit"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT z.*, u.full_name as client_name, a.full_name as assigned_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                ORDER BY z.created_at DESC
                LIMIT $1
            ''', limit)
            return [dict(row) for row in result]
    return await safe_db_operation("get_all_orders", _operation)

async def get_technician_performance(technician_id: int) -> Dict[str, Any]:
    """Get technician performance statistics"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            # Active orders count
            active_orders = await conn.fetchval('''
                SELECT COUNT(*) FROM zayavki 
                WHERE assigned_to = $1 AND status IN ('assigned', 'in_progress')
            ''', technician_id)
            
            # Completed today count
            completed_today = await conn.fetchval('''
                SELECT COUNT(*) FROM zayavki 
                WHERE assigned_to = $1 AND status = 'completed' 
                AND DATE(completed_at) = CURRENT_DATE
            ''', technician_id)
            
            # Average rating
            avg_rating = await conn.fetchval('''
                SELECT COALESCE(AVG(f.rating), 0) FROM feedback f
                JOIN zayavki z ON f.zayavka_id = z.id
                WHERE z.assigned_to = $1
            ''', technician_id)
            
            return {
                'active_orders': active_orders or 0,
                'completed_today': completed_today or 0,
                'avg_rating': float(avg_rating or 0)
            }
    return await safe_db_operation("get_technician_performance", _operation)

async def get_system_statistics() -> Dict[str, Any]:
    """Get system-wide statistics"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            total_orders = await conn.fetchval('SELECT COUNT(*) FROM zayavki')
            completed_orders = await conn.fetchval("SELECT COUNT(*) FROM zayavki WHERE status = 'completed'")
            pending_orders = await conn.fetchval("SELECT COUNT(*) FROM zayavki WHERE status IN ('new', 'pending', 'assigned')")
            active_clients = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM zayavki WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'")
            active_technicians = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role = 'technician'")
            
            return {
                'total_orders': total_orders or 0,
                'completed_orders': completed_orders or 0,
                'pending_orders': pending_orders or 0,
                'active_clients': active_clients or 0,
                'active_technicians': active_technicians or 0,
                'revenue_today': 0,  # This would need integration with billing system
                'avg_completion_time': 24  # Default value, would need calculation
            }
    return await safe_db_operation("get_system_statistics", _operation)

async def get_all_technicians(available_only: bool = False) -> List[Dict[str, Any]]:
    """Get all technicians"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            query = '''
                SELECT u.id, u.full_name, u.telegram_id,
                       COUNT(z.id) as active_orders,
                       CASE WHEN COUNT(z.id) < 5 THEN true ELSE false END as is_active
                FROM users u
                LEFT JOIN zayavki z ON u.id = z.assigned_to 
                    AND z.status IN ('assigned', 'in_progress')
                WHERE u.role = 'technician'
                GROUP BY u.id, u.full_name, u.telegram_id
            '''
            
            if available_only:
                query += ' HAVING COUNT(z.id) < 5'
            
            query += ' ORDER BY u.full_name'
            
            result = await conn.fetch(query)
            return [dict(row) for row in result]
    return await safe_db_operation("get_all_technicians", _operation)

async def get_order_details(order_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed order information"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                SELECT z.*, u.full_name as client_name, u.phone_number as client_phone,
                       a.full_name as assigned_name, z.description as service_type
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                WHERE z.id = $1
            ''', order_id)
            return dict(result) if result else None
    return await safe_db_operation("get_order_details", _operation)

async def update_order_priority(order_id: int, priority: str) -> bool:
    """Update order priority"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            # Add priority column if it doesn't exist
            await conn.execute('''
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name = 'zayavki' AND column_name = 'priority') THEN
                        ALTER TABLE zayavki ADD COLUMN priority VARCHAR(20) DEFAULT 'normal';
                    END IF;
                END $$;
            ''')
            
            await conn.execute('''
                UPDATE zayavki SET priority = $1 WHERE id = $2
            ''', priority, order_id)
            return True
    return await safe_db_operation("update_order_priority", _operation)

async def get_client_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Get client by phone number"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow('''
                SELECT * FROM users WHERE phone_number = $1 AND role = 'client'
            ''', phone)
            return dict(result) if result else None
    return await safe_db_operation("get_client_by_phone", _operation)

async def create_client(client_data: Dict[str, Any]) -> Optional[int]:
    """Create new client"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            client_id = await conn.fetchval('''
                INSERT INTO users (full_name, phone_number, role, language)
                VALUES ($1, $2, 'client', $3)
                RETURNING id
            ''', client_data['full_name'], client_data['phone'], client_data.get('language', 'uz'))
            return client_id
    return await safe_db_operation("create_client", _operation)

async def create_order(order_data: Dict[str, Any]) -> Optional[int]:
    """Create new order"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            order_id = await conn.fetchval('''
                INSERT INTO zayavki (user_id, description, status, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                RETURNING id
            ''', order_data['client_id'], 
                f"{order_data['service_type']}: {order_data['description']}", 
                order_data['status'])
            return order_id
    return await safe_db_operation("create_order", _operation)

async def get_orders_by_client(client_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get orders by client ID"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT z.*, z.description as service_type
                FROM zayavki z
                WHERE z.user_id = $1
                ORDER BY z.created_at DESC
                LIMIT $2
            ''', client_id, limit)
            return [dict(row) for row in result]
    return await safe_db_operation("get_orders_by_client", _operation)

async def search_clients(query: str) -> List[Dict[str, Any]]:
    """Search clients by name or phone"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            result = await conn.fetch('''
                SELECT id, full_name, phone_number as phone, 
                       COALESCE(address, 'Manzil kiritilmagan') as address
                FROM users 
                WHERE role = 'client' 
                AND (full_name ILIKE $1 OR phone_number ILIKE $1)
                ORDER BY full_name
                LIMIT 10
            ''', f'%{query}%')
            return [dict(row) for row in result]
    return await safe_db_operation("search_clients", _operation)

async def get_call_center_stats(operator_id: int) -> Dict[str, Any]:
    """Get call center operator statistics"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            # This would need a call_logs table for proper implementation
            orders_today = await conn.fetchval('''
                SELECT COUNT(*) FROM zayavki 
                WHERE DATE(created_at) = CURRENT_DATE
            ''')
            
            return {
                'calls_today': 0,  # Would need call_logs table
                'orders_today': orders_today or 0,
                'avg_call_duration': 5,  # Default value
                'successful_calls': 85,  # Default value
                'conversion_rate': 75  # Default value
            }
    return await safe_db_operation("get_call_center_stats", _operation)

async def get_pending_calls() -> List[Dict[str, Any]]:
    """Get pending calls/callbacks"""
    async def _operation():
        # This would need a proper callbacks table
        return []
    return await safe_db_operation("get_pending_calls", _operation)

async def create_call_log(call_data: Dict[str, Any]) -> Optional[int]:
    """Create call log entry"""
    async def _operation():
        # This would need a proper call_logs table
        logger.info(f"Call log: {call_data}")
        return 1
    return await safe_db_operation("create_call_log", _operation)

async def get_technicians():
    """
    Return a list of all technicians.
    Each technician should be a dict with at least 'id' and 'full_name'.
    """
    async def _operation():
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch("SELECT id, full_name FROM users WHERE role = 'technician'")
            return [{"id": row["id"], "full_name": row["full_name"]} for row in rows]
    return await safe_db_operation("get_technicians", _operation)

async def get_filtered_applications(
    statuses: List[str] = None,
    date_from: date = None,
    date_to: date = None,
    technician_id: int = None,
    assigned_only: bool = None,
    phone_search: str = None,
    page: int = 1,
    limit: int = 10
) -> Dict[str, Any]:
    """Get filtered applications with pagination"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            # Build WHERE clause dynamically
            where_conditions = []
            params = []
            param_count = 0
            
            # Status filter
            if statuses and statuses != ['all']:
                param_count += 1
                where_conditions.append(f"z.status = ANY(${param_count}::text[])")
                params.append(statuses)
            
            # Date range filter
            if date_from:
                param_count += 1
                where_conditions.append(f"DATE(z.created_at) >= ${param_count}::date")
                params.append(date_from)
            
            if date_to:
                param_count += 1
                where_conditions.append(f"DATE(z.created_at) <= ${param_count}::date")
                params.append(date_to)
            
            # Technician filter
            if technician_id:
                param_count += 1
                where_conditions.append(f"z.assigned_to = ${param_count}")
                params.append(technician_id)
            elif technician_id == 0:  # Unassigned
                where_conditions.append("z.assigned_to IS NULL")
            
            # Assigned only filter
            if assigned_only:
                where_conditions.append("z.assigned_to IS NOT NULL")
            
            # Phone search
            if phone_search:
                param_count += 1
                where_conditions.append(f"u.phone_number ILIKE ${param_count}")
                params.append(f"%{phone_search}%")
            
            # Build complete query
            where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"
            
            # Get total count
            count_query = f'''
                SELECT COUNT(*) 
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                WHERE {where_clause}
            '''
            total_count = await conn.fetchval(count_query, *params)
            
            # Get paginated results
            offset = (page - 1) * limit
            param_count += 1
            params.append(limit)
            param_count += 1
            params.append(offset)
            
            result_query = f'''
                SELECT z.*, 
                       u.full_name as client_name, 
                       u.phone_number as client_phone,
                       t.full_name as technician_name,
                       t.phone_number as technician_phone
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users t ON z.assigned_to = t.id
                WHERE {where_clause}
                ORDER BY z.created_at DESC
                LIMIT ${param_count-1} OFFSET ${param_count}
            '''
            
            results = await conn.fetch(result_query, *params)
            
            return {
                'applications': [dict(row) for row in results],
                'total_count': total_count,
                'page': page,
                'total_pages': (total_count + limit - 1) // limit,
                'has_next': page * limit < total_count,
                'has_prev': page > 1
            }
    
    return await safe_db_operation("get_filtered_applications", _operation)

async def get_user_by_id(user_id: int) -> Optional[asyncpg.Record]:
    """Get user by internal user ID"""
    async def _operation():
        async with db_manager.get_connection() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            logger.info(f"get_user_by_id: {user_id}, result: {bool(user)}")
            return user
    return await safe_db_operation("get_user_by_id", _operation)

async def create_feedback(feedback_data: dict) -> int:
    """Create new feedback record"""
    query = """
        INSERT INTO feedback (
            client_id,
            rating,
            comment,
            operator_id,
            created_at
        ) VALUES (
            %(client_id)s,
            %(rating)s,
            %(comment)s,
            %(operator_id)s,
            NOW()
        ) RETURNING id;
    """
    
    async with db_manager.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, feedback_data)
            result = await cur.fetchone()
            return result[0] if result else None

async def get_client_feedback(client_id: int) -> dict:
    """Get client's most recent feedback"""
    query = """
        SELECT 
            id,
            client_id,
            rating,
            comment,
            operator_id,
            created_at
        FROM feedback
        WHERE client_id = %(client_id)s
        ORDER BY created_at DESC
        LIMIT 1;
    """
    
    async with db_manager.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, {'client_id': client_id})
            result = await cur.fetchone()
            if result:
                return {
                    'id': result[0],
                    'client_id': result[1],
                    'rating': result[2],
                    'comment': result[3],
                    'operator_id': result[4],
                    'created_at': result[5]
                }
            return None

async def create_chat_session(chat_data: dict) -> int:
    """Create new chat session"""
    query = """
        INSERT INTO chat_sessions (
            client_id,
            operator_id,
            status,
            created_at
        ) VALUES (
            %(client_id)s,
            %(operator_id)s,
            %(status)s,
            NOW()
        ) RETURNING id;
    """
    
    async with db_manager.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, chat_data)
            result = await cur.fetchone()
            return result[0] if result else None

async def get_active_chat_sessions(client_id: int) -> list:
    """Get active chat sessions for client"""
    query = """
        SELECT 
            id,
            client_id,
            operator_id,
            status,
            created_at
        FROM chat_sessions
        WHERE client_id = %(client_id)s
        AND status = 'active'
        ORDER BY created_at DESC;
    """
    
    async with db_manager.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, {'client_id': client_id})
            results = await cur.fetchall()
            return [
                {
                    'id': row[0],
                    'client_id': row[1],
                    'operator_id': row[2],
                    'status': row[3],
                    'created_at': row[4]
                }
                for row in results
            ]

async def save_chat_message(message_data: dict) -> int:
    """Save chat message"""
    query = """
        INSERT INTO chat_messages (
            chat_id,
            sender_id,
            message_text,
            message_type,
            created_at
        ) VALUES (
            %(chat_id)s,
            %(sender_id)s,
            %(message_text)s,
            %(message_type)s,
            NOW()
        ) RETURNING id;
    """
    
    async with db_manager.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, message_data)
            result = await cur.fetchone()
            return result[0] if result else None

async def close_chat_session(chat_id: int) -> bool:
    """Close chat session"""
    query = """
        UPDATE chat_sessions
        SET 
            status = 'closed',
            closed_at = NOW()
        WHERE id = %(chat_id)s
        AND status = 'active';
    """
    
    async with db_manager.get_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, {'chat_id': chat_id})
            return cur.rowcount > 0
