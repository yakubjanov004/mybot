#!/usr/bin/env python3
"""
Migration faylini ishga tushirish uchun script
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def run_migration():
    """Run the messages table migration"""
    try:
        # Database connection parameters
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = int(os.getenv('DB_PORT', 5432))
        DB_NAME = os.getenv('DB_NAME', 'alfaconnect')
        DB_USER = os.getenv('DB_USER', 'postgres')
        DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
        
        # Connect to database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        print("✅ Database connection established")
        
        # Read migration file
        migration_file = Path(__file__).parent.parent / "database" / "migrations" / "013_messages_table.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print("📄 Migration file loaded")
        
        # Execute migration
        await conn.execute(migration_sql)
        
        print("✅ Migration completed successfully")
        
        # Verify table creation
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'messages'
            )
        """)
        
        if result:
            print("✅ Messages table created successfully")
        else:
            print("❌ Messages table creation failed")
        
        await conn.close()
        print("✅ Database connection closed")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration()) 