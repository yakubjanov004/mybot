from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from utils.logger import logger
import asyncpg

# Global pool variable
_pool = None

def set_pool(pool):
    """Set the database pool"""
    global _pool
    _pool = pool
    logger.info("Database pool set in queries module")

logger = logging.getLogger(__name__)

# Users queries
async def get_user_by_telegram_id(telegram_id: int) -> Optional[asyncpg.Record]:
    """Telegram ID bo'yicha foydalanuvchini olish"""
    try:
        async with _pool.acquire() as conn:
            user = await conn.fetchrow(
                """
                SELECT * FROM users 
                WHERE telegram_id = $1
                """,
                telegram_id
            )
            logger.info(f"get_user_by_telegram_id: {telegram_id}, natija: {user}")
            return user
    except Exception as e:
        logger.error(f"Foydalanuvchi olishda xatolik: {str(e)}", exc_info=True)
        raise

async def create_user(conn, telegram_id: int, full_name: str, role: str = 'client') -> Dict[str, Any]:
    try:
        user = await conn.fetchrow('''
            INSERT INTO users (telegram_id, full_name, role)
            VALUES ($1, $2, $3)
            RETURNING *
        ''', telegram_id, full_name, role)
        logger.info(f"create_user: {telegram_id}, {full_name}, {role}, natija: {user}")
        return user
    except Exception as e:
        logger.error(f"create_user xatolik: {str(e)}", exc_info=True)
        raise

async def update_user_language(telegram_id: int, language: str) -> None:
    """Foydalanuvchi tilini yangilash"""
    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users 
                SET language = $1
                WHERE telegram_id = $2
                """,
                language, telegram_id
            )
            logger.info(f"Foydalanuvchi tili yangilandi: {telegram_id} -> {language}")
    except Exception as e:
        logger.error(f"Til yangilashda xatolik: {str(e)}", exc_info=True)
        raise

async def update_user_phone(conn, user_id: int, phone_number: str) -> None:
    await conn.execute(
        'UPDATE users SET phone_number = $1 WHERE id = $2',
        phone_number, user_id
    )

# Zayavki queries
async def create_zayavka(conn, user_id: int, description: str, address: Optional[str] = None) -> Dict[str, Any]:
    return await conn.fetchrow('''
        INSERT INTO zayavki (user_id, description, address)
        VALUES ($1, $2, $3)
        RETURNING *
    ''', user_id, description, address)

async def get_zayavka_by_id(conn, zayavka_id: int) -> Optional[Dict[str, Any]]:
    return await conn.fetchrow('''
        SELECT z.*, u.full_name as user_name, a.full_name as assigned_name
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users a ON z.assigned_to = a.id
        WHERE z.id = $1
    ''', zayavka_id)

async def update_zayavka_status(conn, zayavka_id: int, new_status: str, changed_by: int) -> None:
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

async def assign_zayavka(conn, zayavka_id: int, assigned_to: int) -> None:
    await conn.execute(
        'UPDATE zayavki SET assigned_to = $1 WHERE id = $2',
        assigned_to, zayavka_id
    )

async def mark_zayavka_ready(conn, zayavka_id: int) -> None:
    await conn.execute(
        'UPDATE zayavki SET ready_to_install = TRUE WHERE id = $1',
        zayavka_id
    )

# Materials queries
async def get_materials(conn) -> List[Dict[str, Any]]:
    return await conn.fetch(
        'SELECT * FROM materials ORDER BY name'
    )

async def update_material_stock(conn, material_id: int, quantity: int) -> None:
    await conn.execute(
        'UPDATE materials SET stock = stock + $1 WHERE id = $2',
        quantity, material_id
    )

async def get_materials_by_category(conn, category: str) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT * FROM materials 
        WHERE category = $1 
        ORDER BY name
    ''', category)

async def get_low_stock_materials(conn, threshold: int = 5) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT * FROM materials 
        WHERE stock <= $1 
        ORDER BY stock ASC
    ''', threshold)

# Solutions queries
async def create_solution(conn, zayavka_id: int, instander_id: int, solution_text: str) -> Dict[str, Any]:
    return await conn.fetchrow('''
        INSERT INTO solutions (zayavka_id, instander_id, solution_text)
        VALUES ($1, $2, $3)
        RETURNING *
    ''', zayavka_id, instander_id, solution_text)

async def get_zayavka_solutions(conn, zayavka_id: int) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT s.*, u.full_name as instander_name 
        FROM solutions s
        JOIN users u ON s.instander_id = u.id
        WHERE s.zayavka_id = $1 
        ORDER BY s.created_at DESC
    ''', zayavka_id)

# Feedback queries
async def create_feedback(conn, zayavka_id: int, user_id: int, rating: int, comment: Optional[str] = None) -> Dict[str, Any]:
    return await conn.fetchrow('''
        INSERT INTO feedback (zayavka_id, user_id, rating, comment)
        VALUES ($1, $2, $3, $4)
        RETURNING *
    ''', zayavka_id, user_id, rating, comment)

async def get_zayavka_feedback(conn, zayavka_id: int) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT f.*, u.full_name as user_name 
        FROM feedback f
        JOIN users u ON f.user_id = u.id
        WHERE f.zayavka_id = $1 
        ORDER BY f.created_at DESC
    ''', zayavka_id)

# Notifications queries
async def create_notification(conn, user_id: int, message: str, channel: str = 'telegram', zayavka_id: Optional[int] = None) -> Dict[str, Any]:
    return await conn.fetchrow('''
        INSERT INTO notifications (user_id, zayavka_id, message, channel)
        VALUES ($1, $2, $3, $4)
        RETURNING *
    ''', user_id, zayavka_id, message, channel)

async def get_user_notifications(conn, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT * FROM notifications 
        WHERE user_id = $1 
        ORDER BY sent_at DESC 
        LIMIT $2
    ''', user_id, limit)

# Login logs queries
async def create_login_log(conn, user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
    return await conn.fetchrow('''
        INSERT INTO login_logs (user_id, ip_address, user_agent)
        VALUES ($1, $2, $3)
        RETURNING *
    ''', user_id, ip_address, user_agent)

# Issued items queries
async def get_zayavka_issued_items(conn, zayavka_id: int) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT i.*, m.name as material_name, u.full_name as issued_by_name 
        FROM issued_items i
        JOIN materials m ON i.material_id = m.id
        JOIN users u ON i.issued_by = u.id
        WHERE i.zayavka_id = $1 
        ORDER BY i.issued_at DESC
    ''', zayavka_id)

# Additional queries for zayavki
async def get_user_zayavki(conn, user_id: int) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT z.*, u.full_name as user_name, a.full_name as assigned_name
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users a ON z.assigned_to = a.id
        WHERE z.user_id = $1 
        ORDER BY z.created_at DESC
    ''', user_id)

async def get_zayavki_by_status(conn, status: str) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT z.*, u.full_name as user_name, a.full_name as assigned_name
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users a ON z.assigned_to = a.id
        WHERE z.status = $1 
        ORDER BY z.created_at DESC
    ''', status)

async def get_zayavki_by_assigned(conn, assigned_to: int) -> List[Dict[str, Any]]:
    return await conn.fetch('''
        SELECT z.*, u.full_name as user_name, a.full_name as assigned_name
        FROM zayavki z
        LEFT JOIN users u ON z.user_id = u.id
        LEFT JOIN users a ON z.assigned_to = a.id
        WHERE z.assigned_to = $1 
        ORDER BY z.created_at DESC
    ''', assigned_to)

async def create_tables(pool):
    """Create all necessary database tables"""
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                description TEXT,
                media TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                address TEXT,
                assigned_to INTEGER REFERENCES users(id),
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
        ''')

async def update_user_language(telegram_id: int, language: str) -> None:
    """Foydalanuvchi tilini yangilash"""
    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users 
                SET language = $1
                WHERE telegram_id = $2
                """,
                language, telegram_id
            )
            logger.info(f"Foydalanuvchi tili yangilandi: {telegram_id} -> {language}")
    except Exception as e:
        logger.error(f"Til yangilashda xatolik: {str(e)}", exc_info=True)
        raise

async def add_missing_columns():
    """Add missing columns to tables if they don't exist"""
    try:
        async with _pool.acquire() as conn:
            # Add columns to zayavki table
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
            logger.info("Missing columns added successfully")
    except Exception as e:
        logger.error(f"Error adding missing columns: {str(e)}", exc_info=True)
        raise

async def get_staff_members(conn) -> List[Dict[str, Any]]:
    """Get all staff members (users with roles other than 'client' and 'blocked')"""
    return await conn.fetch('''
        SELECT id, full_name, role, telegram_id
        FROM users 
        WHERE role IN ('admin', 'operator', 'technician', 'manager', 'instander', 'callcenter', 'kontroler', 'sklad')
        ORDER BY role, full_name
    ''')

async def create_application(description: str, user_id: int) -> Dict[str, Any]:
    """Create a new application"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchrow('''
                INSERT INTO zayavki (description, user_id, status)
                VALUES ($1, $2, 'new')
                RETURNING *
            ''', description, user_id)
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise

async def get_applications() -> List[Dict[str, Any]]:
    """Get all applications"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch('''
                SELECT z.*, u.full_name as user_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                ORDER BY z.created_at DESC
            ''')
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        raise

async def assign_responsible(application_id: int, user_id: int) -> None:
    """Assign responsible person to application"""
    try:
        async with _pool.acquire() as conn:
            await conn.execute('''
                UPDATE zayavki 
                SET assigned_to = $1
                WHERE id = $2
            ''', user_id, application_id)
    except Exception as e:
        logger.error(f"Error assigning responsible: {e}")
        raise

async def get_equipment_list() -> List[Dict[str, Any]]:
    """Get list of available equipment"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch('''
                SELECT * FROM materials
                WHERE stock > 0
                ORDER BY name
            ''')
    except Exception as e:
        logger.error(f"Error getting equipment list: {e}")
        raise

async def mark_equipment_ready(equipment_id: int) -> None:
    """Mark equipment as ready for installation"""
    try:
        async with _pool.acquire() as conn:
            await conn.execute('''
                UPDATE materials 
                SET ready_to_install = true
                WHERE id = $1
            ''', equipment_id)
    except Exception as e:
        logger.error(f"Error marking equipment ready: {e}")
        raise

async def get_equipment_applications() -> List[Dict[str, Any]]:
    """Get applications with equipment"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch('''
                SELECT z.*, m.name as equipment_name, u.full_name as user_name
                FROM zayavki z
                JOIN issued_items i ON z.id = i.zayavka_id
                JOIN materials m ON i.material_id = m.id
                JOIN users u ON z.user_id = u.id
                ORDER BY z.created_at DESC
            ''')
    except Exception as e:
        logger.error(f"Error getting equipment applications: {e}")
        raise

async def update_application_status(application_id: int, new_status: str) -> None:
    """Update application status"""
    try:
        async with _pool.acquire() as conn:
            # Avval eski statusni olish
            old_status = await conn.fetchval('''
                SELECT status FROM zayavki WHERE id = $1
            ''', application_id)

            # Statusni yangilash
            await conn.execute('''
                UPDATE zayavki 
                SET status = $1,
                    completed_at = CASE WHEN $1 = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END
                WHERE id = $2
            ''', new_status, application_id)

            # Status o'zgarish logini saqlash
            if old_status != new_status:
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, old_status, new_status)
                    VALUES ($1, $2, $3)
                ''', application_id, old_status, new_status)

    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        raise

# CRM Integration Functions

async def get_available_technicians() -> List[Dict[str, Any]]:
    """Bo'sh technicianlari olish"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch('''
                SELECT u.id, u.full_name, u.telegram_id,
                       COUNT(z.id) as active_tasks
                FROM users u
                LEFT JOIN zayavki z ON u.id = z.assigned_to 
                    AND z.status IN ('assigned', 'in_progress')
                WHERE u.role = 'technician'
                GROUP BY u.id, u.full_name, u.telegram_id
                ORDER BY active_tasks ASC, u.full_name
            ''')
    except Exception as e:
        logger.error(f"Error getting available technicians: {e}")
        raise

async def assign_zayavka_to_technician(zayavka_id: int, technician_id: int, assigned_by: int) -> None:
    """Zayavkani technicianga biriktirish"""
    try:
        async with _pool.acquire() as conn:
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
                    VALUES ($1, $2, 'new', 'assigned')
                ''', zayavka_id, assigned_by, 'new', 'assigned')
                
        logger.info(f"Zayavka {zayavka_id} technician {technician_id}ga biriktirildi")
    except Exception as e:
        logger.error(f"Error assigning zayavka: {e}")
        raise

async def get_technician_tasks(technician_id: int) -> List[Dict[str, Any]]:
    """Technician vazifalarini olish"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch('''
                SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
                FROM zayavki z
                JOIN users u ON z.user_id = u.id
                WHERE z.assigned_to = $1 
                    AND z.status IN ('assigned', 'in_progress')
                ORDER BY z.created_at ASC
            ''', technician_id)
    except Exception as e:
        logger.error(f"Error getting technician tasks: {e}")
        raise

async def start_task(zayavka_id: int, technician_id: int) -> None:
    """Vazifani boshlash"""
    try:
        async with _pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute('''
                    UPDATE zayavki 
                    SET status = 'in_progress'
                    WHERE id = $1 AND assigned_to = $2
                ''', zayavka_id, technician_id)
                
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
                    VALUES ($1, $2, 'assigned', 'in_progress')
                ''', zayavka_id, technician_id, 'assigned', 'in_progress')
                
        logger.info(f"Task {zayavka_id} started by technician {technician_id}")
    except Exception as e:
        logger.error(f"Error starting task: {e}")
        raise

async def complete_task(zayavka_id: int, technician_id: int, solution_text: str = None) -> Dict[str, Any]:
    """Vazifani yakunlash"""
    try:
        async with _pool.acquire() as conn:
            async with conn.transaction():
                # Zayavka ma'lumotlarini olish
                zayavka = await conn.fetchrow('''
                    SELECT z.*, u.full_name as client_name, u.telegram_id as client_telegram_id
                    FROM zayavki z
                    JOIN users u ON z.user_id = u.id
                    WHERE z.id = $1
                ''', zayavka_id)
                
                # Status yangilash
                await conn.execute('''
                    UPDATE zayavki 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE id = $1 AND assigned_to = $2
                ''', zayavka_id, technician_id)
                
                # Status log
                await conn.execute('''
                    INSERT INTO status_logs (zayavka_id, changed_by, old_status, new_status)
                    VALUES ($1, $2, 'in_progress', 'completed')
                ''', zayavka_id, technician_id, 'in_progress', 'completed')
                
                # Solution qo'shish
                if solution_text:
                    await conn.execute('''
                        INSERT INTO solutions (zayavka_id, instander_id, solution_text)
                        VALUES ($1, $2, $3)
                    ''', zayavka_id, technician_id, solution_text)
                
                return zayavka
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        raise

async def request_task_transfer(zayavka_id: int, technician_id: int, reason: str) -> None:
    """Vazifani o'tkazish so'rovi"""
    try:
        async with _pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO notifications (user_id, zayavka_id, message, channel)
                SELECT u.id, $1, $2, 'telegram'
                FROM users u
                WHERE u.role = 'manager'
            ''', zayavka_id, f"Transfer so'rovi: {reason}")
        
        logger.info(f"Transfer request created for zayavka {zayavka_id}")
    except Exception as e:
        logger.error(f"Error creating transfer request: {e}")
        raise

async def get_managers_telegram_ids() -> List[int]:
    """Menejerlar telegram ID larini olish"""
    try:
        async with _pool.acquire() as conn:
            result = await conn.fetch('''
                SELECT telegram_id FROM users WHERE role = 'manager'
            ''')
            return [row['telegram_id'] for row in result]
    except Exception as e:
        logger.error(f"Error getting managers: {e}")
        return []

async def get_orders_by_status(statuses: list) -> List[Dict[str, Any]]:
    """Get orders by status list"""
    try:
        async with _pool.acquire() as conn:
            placeholders = ','.join([f'${i+1}' for i in range(len(statuses))])
            return await conn.fetch(f'''
                SELECT z.*, u.full_name as client_name, a.full_name as assigned_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                WHERE z.status = ANY($1::text[])
                ORDER BY z.created_at DESC
            ''', statuses)
    except Exception as e:
        logger.error(f"Error getting orders by status: {e}")
        return []

async def get_all_orders(limit: int = 50) -> List[Dict[str, Any]]:
    """Get all orders with limit"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch('''
                SELECT z.*, u.full_name as client_name, a.full_name as assigned_name
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                ORDER BY z.created_at DESC
                LIMIT $1
            ''', limit)
    except Exception as e:
        logger.error(f"Error getting all orders: {e}")
        return []

async def get_technician_performance(technician_id: int) -> Dict[str, Any]:
    """Get technician performance statistics"""
    try:
        async with _pool.acquire() as conn:
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
    except Exception as e:
        logger.error(f"Error getting technician performance: {e}")
        return {'active_orders': 0, 'completed_today': 0, 'avg_rating': 0}

async def get_system_statistics() -> Dict[str, Any]:
    """Get system-wide statistics"""
    try:
        async with _pool.acquire() as conn:
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
    except Exception as e:
        logger.error(f"Error getting system statistics: {e}")
        return {
            'total_orders': 0, 'completed_orders': 0, 'pending_orders': 0,
            'active_clients': 0, 'active_technicians': 0, 'revenue_today': 0,
            'avg_completion_time': 0
        }

async def get_all_technicians(available_only: bool = False) -> List[Dict[str, Any]]:
    """Get all technicians"""
    try:
        async with _pool.acquire() as conn:
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
            
            return await conn.fetch(query)
    except Exception as e:
        logger.error(f"Error getting technicians: {e}")
        return []

async def get_order_details(order_id: int) -> Optional[Dict[str, Any]]:
    """Get detailed order information"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT z.*, u.full_name as client_name, u.phone_number as client_phone,
                       a.full_name as assigned_name, z.description as service_type
                FROM zayavki z
                LEFT JOIN users u ON z.user_id = u.id
                LEFT JOIN users a ON z.assigned_to = a.id
                WHERE z.id = $1
            ''', order_id)
    except Exception as e:
        logger.error(f"Error getting order details: {e}")
        return None

async def update_order_priority(order_id: int, priority: str) -> bool:
    """Update order priority"""
    try:
        async with _pool.acquire() as conn:
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
    except Exception as e:
        logger.error(f"Error updating order priority: {e}")
        return False

async def get_client_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Get client by phone number"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT * FROM users WHERE phone_number = $1 AND role = 'client'
            ''', phone)
    except Exception as e:
        logger.error(f"Error getting client by phone: {e}")
        return None

async def create_client(client_data: Dict[str, Any]) -> Optional[int]:
    """Create new client"""
    try:
        async with _pool.acquire() as conn:
            client_id = await conn.fetchval('''
                INSERT INTO users (full_name, phone_number, role, language)
                VALUES ($1, $2, 'client', $3)
                RETURNING id
            ''', client_data['full_name'], client_data['phone'], client_data.get('language', 'uz'))
            return client_id
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        return None

async def create_order(order_data: Dict[str, Any]) -> Optional[int]:
    """Create new order"""
    try:
        async with _pool.acquire() as conn:
            order_id = await conn.fetchval('''
                INSERT INTO zayavki (user_id, description, status, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                RETURNING id
            ''', order_data['client_id'], 
                f"{order_data['service_type']}: {order_data['description']}", 
                order_data['status'])
            return order_id
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return None

async def get_orders_by_client(client_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get orders by client ID"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch('''
                SELECT z.*, z.description as service_type
                FROM zayavki z
                WHERE z.user_id = $1
                ORDER BY z.created_at DESC
                LIMIT $2
            ''', client_id, limit)
    except Exception as e:
        logger.error(f"Error getting orders by client: {e}")
        return []

async def search_clients(query: str) -> List[Dict[str, Any]]:
    """Search clients by name or phone"""
    try:
        async with _pool.acquire() as conn:
            return await conn.fetch('''
                SELECT id, full_name, phone_number as phone, 
                       COALESCE(address, 'Manzil kiritilmagan') as address
                FROM users 
                WHERE role = 'client' 
                AND (full_name ILIKE $1 OR phone_number ILIKE $1)
                ORDER BY full_name
                LIMIT 10
            ''', f'%{query}%')
    except Exception as e:
        logger.error(f"Error searching clients: {e}")
        return []

async def get_call_center_stats(operator_id: int) -> Dict[str, Any]:
    """Get call center operator statistics"""
    try:
        async with _pool.acquire() as conn:
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
    except Exception as e:
        logger.error(f"Error getting call center stats: {e}")
        return {
            'calls_today': 0, 'orders_today': 0, 'avg_call_duration': 0,
            'successful_calls': 0, 'conversion_rate': 0
        }

async def get_pending_calls() -> List[Dict[str, Any]]:
    """Get pending calls/callbacks"""
    try:
        # This would need a proper callbacks table
        return []
    except Exception as e:
        logger.error(f"Error getting pending calls: {e}")
        return []

async def create_call_log(call_data: Dict[str, Any]) -> Optional[int]:
    """Create call log entry"""
    try:
        # This would need a proper call_logs table
        logger.info(f"Call log: {call_data}")
        return 1
    except Exception as e:
        logger.error(f"Error creating call log: {e}")
        return None

async def get_technicians():
    """
    Return a list of all technicians.
    Each technician should be a dict with at least 'id' and 'full_name'.
    """
    async with _pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, full_name FROM users WHERE role = 'technician'")
        return [{"id": row["id"], "full_name": row["full_name"]} for row in rows]
