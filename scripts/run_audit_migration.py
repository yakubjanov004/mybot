#!/usr/bin/env python3
"""
Script to run audit logging database migration.
Implements Requirements 6.1, 6.2 from multi-role application creation spec.
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import config
from utils.logger import setup_module_logger

logger = setup_module_logger("audit_migration")

async def run_migration():
    """Run the audit logging database migration"""
    try:
        # Read migration SQL
        migration_file = project_root / "database" / "migrations" / "add_audit_tables.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        logger.info("Connecting to database...")
        
        # Connect to database
        conn = await asyncpg.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        
        logger.info("Connected to database successfully")
        
        # Execute migration in a transaction
        async with conn.transaction():
            logger.info("Executing audit tables migration...")
            await conn.execute(migration_sql)
            logger.info("Migration executed successfully")
        
        # Verify tables were created
        logger.info("Verifying table creation...")
        
        tables_query = """
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_name IN ('staff_application_audit', 'client_selection_data')
        ORDER BY table_name
        """
        
        tables = await conn.fetch(tables_query)
        
        if len(tables) >= 2:
            logger.info("✅ Audit tables created successfully:")
            for table in tables:
                logger.info(f"  - {table['table_name']} ({table['table_type']})")
        else:
            logger.error("❌ Not all audit tables were created")
            return False
        
        # Verify indexes
        indexes_query = """
        SELECT indexname, tablename
        FROM pg_indexes 
        WHERE tablename IN ('staff_application_audit', 'client_selection_data')
        AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname
        """
        
        indexes = await conn.fetch(indexes_query)
        logger.info(f"✅ Created {len(indexes)} indexes for audit tables")
        
        # Verify views
        views_query = """
        SELECT table_name
        FROM information_schema.views 
        WHERE table_name IN ('staff_audit_summary', 'creator_performance_summary', 'daily_audit_stats')
        ORDER BY table_name
        """
        
        views = await conn.fetch(views_query)
        logger.info(f"✅ Created {len(views)} audit views:")
        for view in views:
            logger.info(f"  - {view['table_name']}")
        
        await conn.close()
        logger.info("Database connection closed")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

async def test_audit_tables():
    """Test the audit tables by inserting and querying test data"""
    try:
        logger.info("Testing audit tables...")
        
        # Connect to database
        conn = await asyncpg.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        
        # Test staff_application_audit table
        test_audit_sql = """
        INSERT INTO staff_application_audit (
            application_id, creator_id, creator_role, client_id, application_type,
            client_notified, workflow_initiated, metadata, session_id
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9
        ) RETURNING id
        """
        
        audit_id = await conn.fetchval(
            test_audit_sql,
            'test-app-migration-001',
            999,  # Test creator ID
            'manager',
            888,  # Test client ID
            'connection_request',
            True,
            True,
            '{"event_type": "application_submitted", "test": true}',
            'test-session-001'
        )
        
        logger.info(f"✅ Test audit record created with ID: {audit_id}")
        
        # Test client_selection_data table
        test_selection_sql = """
        INSERT INTO client_selection_data (
            search_method, search_value, client_id, verified
        ) VALUES (
            $1, $2, $3, $4
        ) RETURNING id
        """
        
        selection_id = await conn.fetchval(
            test_selection_sql,
            'phone',
            '+998901234567',
            888,
            True
        )
        
        logger.info(f"✅ Test client selection record created with ID: {selection_id}")
        
        # Test views
        summary_query = "SELECT * FROM staff_audit_summary LIMIT 1"
        summary_result = await conn.fetch(summary_query)
        logger.info(f"✅ staff_audit_summary view working: {len(summary_result)} rows")
        
        performance_query = "SELECT * FROM creator_performance_summary LIMIT 1"
        performance_result = await conn.fetch(performance_query)
        logger.info(f"✅ creator_performance_summary view working: {len(performance_result)} rows")
        
        daily_stats_query = "SELECT * FROM daily_audit_stats LIMIT 1"
        daily_stats_result = await conn.fetch(daily_stats_query)
        logger.info(f"✅ daily_audit_stats view working: {len(daily_stats_result)} rows")
        
        # Clean up test data
        await conn.execute("DELETE FROM staff_application_audit WHERE application_id = $1", 'test-app-migration-001')
        await conn.execute("DELETE FROM client_selection_data WHERE id = $1", selection_id)
        
        logger.info("✅ Test data cleaned up")
        
        await conn.close()
        logger.info("✅ Audit tables test completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Audit tables test failed: {e}")
        return False

async def check_existing_tables():
    """Check if audit tables already exist"""
    try:
        conn = await asyncpg.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        
        check_query = """
        SELECT table_name
        FROM information_schema.tables 
        WHERE table_name IN ('staff_application_audit', 'client_selection_data')
        """
        
        existing_tables = await conn.fetch(check_query)
        await conn.close()
        
        return [table['table_name'] for table in existing_tables]
        
    except Exception as e:
        logger.error(f"Error checking existing tables: {e}")
        return []

def main():
    """Main function to run migration"""
    print("🚀 Starting audit logging database migration...")
    
    # Check if tables already exist
    existing_tables = asyncio.run(check_existing_tables())
    
    if existing_tables:
        print(f"⚠️  Some audit tables already exist: {existing_tables}")
        response = input("Do you want to continue? This will create missing tables and indexes. (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Migration cancelled.")
            return
    
    # Run migration
    success = asyncio.run(run_migration())
    
    if success:
        print("✅ Migration completed successfully!")
        
        # Run tests
        test_response = input("Do you want to run tests on the audit tables? (Y/n): ")
        if test_response.lower() not in ['n', 'no']:
            test_success = asyncio.run(test_audit_tables())
            if test_success:
                print("✅ All tests passed!")
            else:
                print("❌ Some tests failed. Check logs for details.")
    else:
        print("❌ Migration failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()