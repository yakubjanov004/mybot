#!/usr/bin/env python3
"""
Script to fix role inconsistencies in the database
This script updates the database to use consistent role names
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import config

parsed = urlparse(config.DATABASE_URL)
DB_HOST = parsed.hostname
DB_PORT = parsed.port
DB_NAME = parsed.path.lstrip('/')
DB_USER = parsed.username
DB_PASSWORD = parsed.password

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

from utils.logger import logger

async def fix_roles():
    """Fix role inconsistencies in the database"""
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        logger.info("Starting role fix process...")
        
        # Drop existing role constraint
        await conn.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;")
        logger.info("Dropped existing role constraint")
        
        # Add correct role constraint
        await conn.execute("""
            ALTER TABLE users ADD CONSTRAINT users_role_check 
            CHECK (role IN ('admin', 'call_center', 'technician', 'manager', 'controller', 'warehouse', 'client', 'blocked'));
        """)
        logger.info("Added correct role constraint")
        
        # Update existing roles
        result = await conn.execute("UPDATE users SET role = 'call_center' WHERE role = 'operator';")
        logger.info(f"Updated operator roles to call_center: {result}")
        
        result = await conn.execute("UPDATE users SET role = 'controller' WHERE role = 'kontroler';")
        logger.info(f"Updated kontroler roles to controller: {result}")
        
        result = await conn.execute("UPDATE users SET role = 'warehouse' WHERE role = 'sklad';")
        logger.info(f"Updated sklad roles to warehouse: {result}")
        
        result = await conn.execute("UPDATE users SET role = 'call_center' WHERE role = 'callcenter';")
        logger.info(f"Updated callcenter roles to call_center: {result}")
        
        # Add index for better performance
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role_updated ON users(role);")
        logger.info("Added role index")
        
        # Verify the fix
        roles = await conn.fetch("SELECT DISTINCT role FROM users ORDER BY role;")
        logger.info(f"Current roles in database: {[role['role'] for role in roles]}")
        
        await conn.close()
        logger.info("Role fix completed successfully!")
        
    except Exception as e:
        logger.error(f"Error fixing roles: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_roles())
