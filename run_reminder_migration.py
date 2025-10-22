#!/usr/bin/env python3
"""
Migration script to create activity_reminders table.
Run this once to add reminder functionality to the database.
"""

import os
import sys
from dotenv import load_dotenv
from app.database import get_db_service

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the reminder table migration."""
    print("Starting migration: create_reminders_table.sql")

    # Read migration SQL
    migration_file = 'migrations/create_reminders_table.sql'
    if not os.path.exists(migration_file):
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Execute migration
    try:
        db = get_db_service()
        print("Executing migration SQL...")

        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

        for i, statement in enumerate(statements, 1):
            if statement.strip():
                print(f"Executing statement {i}/{len(statements)}...")
                db.execute_query(statement, fetch=False)

        print("\n✅ Migration completed successfully!")
        print("The activity_reminders table has been created.")

        # Verify table was created
        result = db.execute_query("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'activity_reminders'
        """)

        if result:
            print(f"✅ Verified: activity_reminders table exists")

            # Show table structure
            columns = db.execute_query("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'activity_reminders'
                ORDER BY ordinal_position
            """)

            print("\nTable structure:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  - {col['column_name']}: {col['data_type']} ({nullable})")
        else:
            print("⚠️  Warning: Could not verify table creation")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("=" * 60)
    print("Baby Journal - Reminder Migration")
    print("=" * 60)
    run_migration()
