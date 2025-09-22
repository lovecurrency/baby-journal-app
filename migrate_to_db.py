#!/usr/bin/env python3
"""
Migration script to transfer data from JSON files to Supabase database.
Run this script after setting up the database to migrate existing data.
"""

import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app directory to path to import our modules
sys.path.append('.')

from app.models import BabyActivity as JSONBabyActivity, BabyProfile as JSONBabyProfile, ActivityJournal as JSONActivityJournal
from app.models_db import BabyActivity as DBBabyActivity, BabyProfile as DBBabyProfile, ActivityJournal as DBActivityJournal
from app.database import get_db_service


def migrate_profile(json_journal: JSONActivityJournal, db_journal: DBActivityJournal) -> bool:
    """Migrate baby profile from JSON to database."""
    print("Migrating baby profile...")

    if not json_journal.profile:
        print("No profile found in JSON data")
        return False

    json_profile = json_journal.profile

    # Create new database profile
    db_profile = DBBabyProfile(
        name=json_profile.name,
        birth_date=json_profile.birth_date,
        gender=json_profile.gender,
        birth_weight=json_profile.birth_weight,
        birth_height=json_profile.birth_height
    )

    # Save to database
    if db_profile.save():
        db_journal.profile = db_profile
        print(f"✓ Profile migrated: {db_profile.name}")
        return True
    else:
        print("✗ Failed to save profile to database")
        return False


def migrate_activities(json_journal: JSONActivityJournal, db_journal: DBActivityJournal) -> int:
    """Migrate activities from JSON to database."""
    print("Migrating activities...")

    if not json_journal.activities:
        print("No activities found in JSON data")
        return 0

    if not db_journal.profile:
        print("✗ Cannot migrate activities without a profile")
        return 0

    migrated_count = 0
    failed_count = 0

    for json_activity in json_journal.activities:
        try:
            # Create new database activity
            db_activity = DBBabyActivity(
                timestamp=json_activity.timestamp,
                category=json_activity.category,
                activity_type=json_activity.activity_type,
                description=json_activity.description,
                amount=json_activity.amount,
                unit=json_activity.unit,
                duration_minutes=json_activity.duration_minutes,
                notes=json_activity.notes,
                tags=json_activity.tags,
                source=json_activity.source,
                sender=json_activity.sender,
                profile_id=db_journal.profile.id
            )

            # Save to database
            if db_activity.save():
                migrated_count += 1
                if migrated_count % 10 == 0:
                    print(f"  Migrated {migrated_count} activities...")
            else:
                failed_count += 1
                print(f"  ✗ Failed to save activity: {json_activity.description}")

        except Exception as e:
            failed_count += 1
            print(f"  ✗ Error migrating activity: {e}")

    print(f"✓ Migration complete: {migrated_count} activities migrated, {failed_count} failed")
    return migrated_count


def backup_json_files():
    """Create backup of JSON files."""
    print("Creating backup of JSON files...")

    backup_dir = "data_backup"
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for filename in ['profile.json', 'activities.json']:
        src_path = os.path.join('data', filename)
        if os.path.exists(src_path):
            backup_filename = f"{filename.replace('.json', '')}_{timestamp}.json"
            backup_path = os.path.join(backup_dir, backup_filename)

            # Copy file
            with open(src_path, 'r') as src, open(backup_path, 'w') as backup:
                backup.write(src.read())

            print(f"✓ Backed up {filename} to {backup_path}")


def check_database_connection():
    """Check if database connection is working."""
    print("Checking database connection...")

    try:
        db_service = get_db_service()
        # Try to execute a simple query
        db_service.db.execute_query("SELECT 1 as test;")
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nPlease ensure:")
        print("1. DATABASE_URL environment variable is set")
        print("2. Database server is running and accessible")
        print("3. Database credentials are correct")
        return False


def main():
    """Main migration function."""
    print("🚀 Starting migration from JSON files to Supabase database")
    print("=" * 60)

    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("✗ DATABASE_URL environment variable not set")
        print("Please set up your Supabase database connection string")
        print("Example: export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        return

    # Check database connection
    if not check_database_connection():
        return

    # Check if JSON data exists
    if not os.path.exists('data/profile.json') and not os.path.exists('data/activities.json'):
        print("No JSON data files found. Nothing to migrate.")
        return

    # Create backup
    backup_json_files()

    try:
        # Load JSON data
        print("\nLoading JSON data...")
        json_journal = JSONActivityJournal()
        json_journal.load_profile()
        json_journal.load_activities()

        print(f"Found: {len(json_journal.activities) if json_journal.activities else 0} activities")
        print(f"Profile: {'Yes' if json_journal.profile else 'No'}")

        # Initialize database journal
        db_journal = DBActivityJournal()

        # Migrate profile
        profile_migrated = migrate_profile(json_journal, db_journal)

        if not profile_migrated:
            print("Cannot continue without profile migration")
            return

        # Migrate activities
        activities_migrated = migrate_activities(json_journal, db_journal)

        print("\n" + "=" * 60)
        print("🎉 Migration completed successfully!")
        print(f"✓ Profile migrated: {json_journal.profile.name if json_journal.profile else 'None'}")
        print(f"✓ Activities migrated: {activities_migrated}")
        print("\nYour data is now stored in the Supabase database.")
        print("The original JSON files have been backed up in the 'data_backup' directory.")

        # Ask if user wants to remove JSON files
        response = input("\nWould you like to remove the original JSON files? (y/N): ")
        if response.lower() == 'y':
            for filename in ['profile.json', 'activities.json']:
                file_path = os.path.join('data', filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"✓ Removed {file_path}")
            print("Original JSON files removed. Data is now only in the database.")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("Please check the error and try again.")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()