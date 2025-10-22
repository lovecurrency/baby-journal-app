"""
Database service layer for Supabase PostgreSQL integration.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and operations."""

    def __init__(self):
        self.connection_pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not found, using fallback connection parameters")
            # Fallback for development
            database_url = self._build_connection_url()

        try:
            # Create connection pool
            self.connection_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=database_url
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise

    def _build_connection_url(self):
        """Build connection URL from individual environment variables."""
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'baby_journal')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def get_connection(self):
        """Get a connection from the pool."""
        if not self.connection_pool:
            raise Exception("Database connection pool not initialized")
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        if self.connection_pool:
            self.connection_pool.putconn(conn)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """Execute a database query."""
        conn = None
        try:
            logger.debug(f"Executing query: {query[:100]}... with params: {params}")
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    result = [dict(row) for row in cursor.fetchall()]
                    logger.debug(f"Query returned {len(result)} rows")
                    return result
                else:
                    conn.commit()
                    logger.debug("Query executed and committed successfully")
                    return None
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database query error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query with multiple parameter sets."""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database executemany error: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def execute_insert_returning(self, query: str, params: tuple = None) -> Optional[str]:
        """Execute an INSERT query with RETURNING clause and return the single value."""
        conn = None
        try:
            logger.info(f"Executing INSERT with RETURNING: {query[:100]}... with params: {params}")
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                conn.commit()

                if result:
                    # Extract the ID from the result
                    result_dict = dict(result)
                    logger.info(f"INSERT successful, returned: {result_dict}")
                    return str(result_dict['id'])
                else:
                    logger.error("INSERT returned no result")
                    return None

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database INSERT error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def close_pool(self):
        """Close all connections in the pool."""
        if self.connection_pool:
            self.connection_pool.closeall()


class DatabaseService:
    """High-level database service for baby journal operations."""

    def __init__(self):
        self.db = DatabaseConnection()
        self.ensure_tables_exist()

    def ensure_tables_exist(self):
        """Create database tables if they don't exist."""
        try:
            # Create profiles table
            profiles_table = """
            CREATE TABLE IF NOT EXISTS baby_profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                birth_date TIMESTAMP NOT NULL,
                gender VARCHAR(50),
                birth_weight DECIMAL(5,2),
                birth_height DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create activities table
            activities_table = """
            CREATE TABLE IF NOT EXISTS baby_activities (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                profile_id UUID REFERENCES baby_profiles(id) ON DELETE CASCADE,
                timestamp TIMESTAMP NOT NULL,
                category VARCHAR(50) NOT NULL,
                activity_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                amount DECIMAL(10,2),
                unit VARCHAR(20),
                duration_minutes INTEGER,
                notes TEXT,
                tags TEXT[],
                source VARCHAR(50) DEFAULT 'manual',
                sender VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Create indexes and constraints
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_activities_profile_id ON baby_activities(profile_id);",
                "CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON baby_activities(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_activities_category ON baby_activities(category);",
                "CREATE INDEX IF NOT EXISTS idx_activities_type ON baby_activities(activity_type);",
                # Unique constraint to prevent duplicate activities
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_activities_unique ON baby_activities(profile_id, timestamp, description, COALESCE(amount, 0));"
            ]

            # Execute table creation
            self.db.execute_query(profiles_table, fetch=False)
            self.db.execute_query(activities_table, fetch=False)

            # Execute indexes
            for index in indexes:
                self.db.execute_query(index, fetch=False)

            logger.info("Database tables ensured to exist")

        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    # Profile operations
    def create_profile(self, name: str, birth_date: datetime, gender: str = None,
                      birth_weight: float = None, birth_height: float = None) -> str:
        """Create a new baby profile."""
        query = """
        INSERT INTO baby_profiles (name, birth_date, gender, birth_weight, birth_height)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        params = (name, birth_date, gender, birth_weight, birth_height)

        # Use a special method for INSERT with RETURNING
        result = self.db.execute_insert_returning(query, params)
        return str(result) if result else None

    def get_profile(self, profile_id: str = None) -> Optional[Dict]:
        """Get baby profile by ID, or the first profile if no ID provided."""
        if profile_id:
            query = "SELECT * FROM baby_profiles WHERE id = %s;"
            params = (profile_id,)
        else:
            query = "SELECT * FROM baby_profiles ORDER BY created_at LIMIT 1;"
            params = None

        result = self.db.execute_query(query, params)
        return result[0] if result else None

    def update_profile(self, profile_id: str, **updates) -> bool:
        """Update baby profile."""
        if not updates:
            return False

        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        query = f"""
        UPDATE baby_profiles
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s;
        """
        params = list(updates.values()) + [profile_id]

        try:
            self.db.execute_query(query, params, fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return False

    def delete_profile(self, profile_id: str) -> bool:
        """Delete baby profile and all associated activities."""
        query = "DELETE FROM baby_profiles WHERE id = %s;"
        try:
            self.db.execute_query(query, (profile_id,), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error deleting profile: {e}")
            return False

    # Activity operations
    def create_activity(self, profile_id: str, timestamp: datetime, category: str,
                       activity_type: str, description: str, amount: float = None,
                       unit: str = None, duration_minutes: int = None, notes: str = None,
                       tags: List[str] = None, source: str = 'manual', sender: str = None) -> str:
        """Create a new activity, handling duplicates gracefully."""
        query = """
        INSERT INTO baby_activities
        (profile_id, timestamp, category, activity_type, description, amount, unit,
         duration_minutes, notes, tags, source, sender)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT ON CONSTRAINT idx_activities_unique DO NOTHING
        RETURNING id;
        """
        params = (profile_id, timestamp, category, activity_type, description, amount,
                 unit, duration_minutes, notes, tags, source, sender)

        try:
            result = self.db.execute_insert_returning(query, params)
            return str(result) if result else None  # None means duplicate was skipped
        except Exception as e:
            # Fallback for databases that don't support ON CONFLICT
            logger.warning(f"Conflict handling failed, trying duplicate check: {e}")
            return self._create_activity_with_duplicate_check(profile_id, timestamp, category,
                                                            activity_type, description, amount,
                                                            unit, duration_minutes, notes, tags,
                                                            source, sender)

    def _create_activity_with_duplicate_check(self, profile_id: str, timestamp: datetime,
                                             category: str, activity_type: str, description: str,
                                             amount: float = None, unit: str = None,
                                             duration_minutes: int = None, notes: str = None,
                                             tags: List[str] = None, source: str = 'manual',
                                             sender: str = None) -> str:
        """Fallback method to create activity with manual duplicate check."""
        # Check if duplicate exists
        check_query = """
        SELECT id FROM baby_activities
        WHERE profile_id = %s AND timestamp = %s AND description = %s
        AND COALESCE(amount, 0) = COALESCE(%s, 0)
        LIMIT 1;
        """
        check_params = (profile_id, timestamp, description, amount)
        existing = self.db.execute_query(check_query, check_params)

        if existing:
            logger.info("Duplicate activity detected, skipping")
            return None  # Duplicate found, skip insertion

        # No duplicate, proceed with insert
        insert_query = """
        INSERT INTO baby_activities
        (profile_id, timestamp, category, activity_type, description, amount, unit,
         duration_minutes, notes, tags, source, sender)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        insert_params = (profile_id, timestamp, category, activity_type, description, amount,
                        unit, duration_minutes, notes, tags, source, sender)

        result = self.db.execute_insert_returning(insert_query, insert_params)
        return str(result) if result else None

    def get_activities(self, profile_id: str, limit: int = None,
                      category: str = None, date: datetime = None) -> List[Dict]:
        """Get activities with optional filtering."""
        query = "SELECT * FROM baby_activities WHERE profile_id = %s"
        params = [profile_id]

        if category:
            query += " AND category = %s"
            params.append(category)

        if date:
            query += " AND DATE(timestamp) = DATE(%s)"
            params.append(date)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        return self.db.execute_query(query, params) or []

    def get_activity_by_id(self, activity_id: str) -> Optional[Dict]:
        """Get single activity by ID."""
        query = "SELECT * FROM baby_activities WHERE id = %s;"
        result = self.db.execute_query(query, (activity_id,))
        return result[0] if result else None

    def update_activity(self, activity_id: str, **updates) -> bool:
        """Update activity."""
        if not updates:
            return False

        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        query = f"""
        UPDATE baby_activities
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s;
        """
        params = list(updates.values()) + [activity_id]

        try:
            self.db.execute_query(query, params, fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error updating activity: {e}")
            return False

    def delete_activity(self, activity_id: str) -> bool:
        """Delete activity by ID."""
        query = "DELETE FROM baby_activities WHERE id = %s;"
        try:
            self.db.execute_query(query, (activity_id,), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error deleting activity: {e}")
            return False

    def get_activity_statistics(self, profile_id: str) -> Dict:
        """Get activity statistics for a profile."""
        query = """
        SELECT
            COUNT(*) as total_activities,
            category,
            COUNT(*) as category_count,
            MIN(timestamp) as earliest_activity,
            MAX(timestamp) as latest_activity
        FROM baby_activities
        WHERE profile_id = %s
        GROUP BY category;
        """

        result = self.db.execute_query(query, (profile_id,))

        if not result:
            return {}

        stats = {
            'total_activities': sum(row['category_count'] for row in result),
            'by_category': {row['category']: row['category_count'] for row in result},
            'date_range': {
                'start': min(row['earliest_activity'] for row in result).isoformat(),
                'end': max(row['latest_activity'] for row in result).isoformat()
            }
        }

        # Calculate daily averages
        start_date = min(row['earliest_activity'] for row in result)
        days = (datetime.now() - start_date).days + 1

        # Map category names to match template expectations
        category_mapping = {
            'feeding': 'feedings',
            'diaper': 'diaper_changes',
            'sleep': 'sleep_sessions',
            'milestone': 'milestones',
            'health': 'health_events'
        }

        stats['daily_averages'] = {}
        for row in result:
            category = row['category']
            daily_avg = round(row['category_count'] / days, 1)
            # Use mapped name if available, otherwise use original category name
            mapped_name = category_mapping.get(category, category)
            stats['daily_averages'][mapped_name] = daily_avg

        return stats

    # Reminder operations
    def create_reminder(self, profile_id: str, reminder_type: str, activity_category: str,
                       title: str, message: str, enabled: bool = True,
                       recurrence_hours: int = None, scheduled_time: str = None,
                       last_activity_hours: int = None) -> str:
        """Create a new activity reminder."""
        query = """
        INSERT INTO activity_reminders
        (profile_id, reminder_type, activity_category, title, message, enabled,
         recurrence_hours, scheduled_time, last_activity_hours)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        params = (profile_id, reminder_type, activity_category, title, message, enabled,
                 recurrence_hours, scheduled_time, last_activity_hours)

        try:
            result = self.db.execute_insert_returning(query, params)
            return str(result) if result else None
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return None

    def get_reminders(self, profile_id: str, enabled_only: bool = False) -> List[Dict]:
        """Get all reminders for a profile."""
        query = "SELECT * FROM activity_reminders WHERE profile_id = %s"
        params = [profile_id]

        if enabled_only:
            query += " AND enabled = true"

        query += " ORDER BY created_at DESC;"

        try:
            result = self.db.execute_query(query, tuple(params))
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting reminders: {e}")
            return []

    def get_reminder_by_id(self, reminder_id: str) -> Optional[Dict]:
        """Get a specific reminder by ID."""
        query = "SELECT * FROM activity_reminders WHERE id = %s;"
        try:
            result = self.db.execute_query(query, (reminder_id,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting reminder by ID: {e}")
            return None

    def update_reminder(self, reminder_id: str, **updates) -> bool:
        """Update a reminder."""
        if not updates:
            return False

        # Add updated_at timestamp
        updates['updated_at'] = datetime.now()

        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        query = f"""
        UPDATE activity_reminders
        SET {set_clause}
        WHERE id = %s;
        """
        params = list(updates.values()) + [reminder_id]

        try:
            self.db.execute_query(query, tuple(params), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error updating reminder: {e}")
            return False

    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder."""
        query = "DELETE FROM activity_reminders WHERE id = %s;"
        try:
            self.db.execute_query(query, (reminder_id,), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return False

    def update_reminder_last_triggered(self, reminder_id: str, triggered_at: datetime = None) -> bool:
        """Update the last_triggered_at timestamp for a reminder."""
        if triggered_at is None:
            triggered_at = datetime.now()

        query = """
        UPDATE activity_reminders
        SET last_triggered_at = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s;
        """
        try:
            self.db.execute_query(query, (triggered_at, reminder_id), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error updating reminder last_triggered_at: {e}")
            return False

    # Daily Activity Goal operations
    def create_daily_activity_goal(self, profile_id: str, activity_key: str, activity_title: str,
                                   activity_category: str, age_range_min: int, age_range_max: int,
                                   target_count: int, **kwargs) -> str:
        """Create a daily activity goal."""
        import json

        query = """
        INSERT INTO daily_activity_goals
        (profile_id, activity_key, activity_title, activity_description, activity_category,
         age_range_min, age_range_max, target_count, duration_minutes, icon, color,
         motivational_messages, completion_message, benefits, enabled, priority)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (profile_id, activity_key) DO UPDATE SET
        activity_title = EXCLUDED.activity_title,
        activity_description = EXCLUDED.activity_description,
        target_count = EXCLUDED.target_count,
        duration_minutes = EXCLUDED.duration_minutes,
        motivational_messages = EXCLUDED.motivational_messages,
        completion_message = EXCLUDED.completion_message,
        benefits = EXCLUDED.benefits,
        updated_at = CURRENT_TIMESTAMP
        RETURNING id;
        """

        # Convert motivational_messages dict to JSON
        motivational_messages = kwargs.get('motivational_messages', {})
        if isinstance(motivational_messages, dict):
            motivational_messages = json.dumps(motivational_messages)

        params = (
            profile_id, activity_key, activity_title,
            kwargs.get('activity_description'),
            activity_category, age_range_min, age_range_max, target_count,
            kwargs.get('duration_minutes'),
            kwargs.get('icon'),
            kwargs.get('color'),
            motivational_messages,
            kwargs.get('completion_message'),
            kwargs.get('benefits'),
            kwargs.get('enabled', True),
            kwargs.get('priority', 1)
        )

        try:
            result = self.db.execute_insert_returning(query, params)
            return str(result) if result else None
        except Exception as e:
            logger.error(f"Error creating daily activity goal: {e}")
            return None

    def get_daily_activity_goals_for_age(self, profile_id: str, age_months: int) -> List[Dict]:
        """Get daily activity goals appropriate for baby's current age."""
        query = """
        SELECT * FROM daily_activity_goals
        WHERE profile_id = %s
        AND enabled = true
        AND age_range_min <= %s
        AND age_range_max > %s
        ORDER BY priority ASC;
        """

        try:
            result = self.db.execute_query(query, (profile_id, age_months, age_months))
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting activity goals for age: {e}")
            return []

    def get_daily_activity_progress(self, profile_id: str, activity_date: datetime = None) -> List[Dict]:
        """Get daily progress for all activities."""
        if activity_date is None:
            from datetime import date
            activity_date = date.today()
        elif isinstance(activity_date, datetime):
            activity_date = activity_date.date()

        query = """
        SELECT p.*, g.activity_title, g.activity_key, g.activity_category, g.target_count, g.icon, g.color,
               g.motivational_messages, g.completion_message, g.duration_minutes, g.benefits
        FROM daily_activity_progress p
        JOIN daily_activity_goals g ON p.goal_id = g.id
        WHERE p.profile_id = %s AND p.activity_date = %s
        ORDER BY g.priority ASC;
        """

        try:
            result = self.db.execute_query(query, (profile_id, activity_date))
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting daily activity progress: {e}")
            return []

    def increment_activity_progress(self, goal_id: str, profile_id: str, activity_date: datetime = None) -> Dict:
        """Increment progress for an activity. Creates progress row if doesn't exist."""
        from datetime import date

        if activity_date is None:
            activity_date = date.today()
        elif isinstance(activity_date, datetime):
            activity_date = activity_date.date()

        # First, get the goal to know the target
        goal_query = "SELECT target_count FROM daily_activity_goals WHERE id = %s;"
        goal_result = self.db.execute_query(goal_query, (goal_id,))

        if not goal_result:
            logger.error(f"Goal not found: {goal_id}")
            return None

        target_count = goal_result[0]['target_count']

        # Check if progress exists for today
        check_query = """
        SELECT id, current_count FROM daily_activity_progress
        WHERE goal_id = %s AND activity_date = %s;
        """
        existing = self.db.execute_query(check_query, (goal_id, activity_date))

        if existing:
            # Update existing progress
            progress_id = existing[0]['id']
            new_count = existing[0]['current_count'] + 1
            completed = new_count >= target_count

            update_query = """
            UPDATE daily_activity_progress
            SET current_count = %s,
                completed = %s,
                completed_at = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE completed_at END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *;
            """

            result = self.db.execute_query(update_query, (new_count, completed, completed, progress_id))

            # Update streak if completed
            if completed and result:
                self._update_activity_streak(goal_id, profile_id, activity_date)

            # Get full progress with goal details
            if result:
                return self.get_activity_progress_by_id(str(result[0]['id']))
            return None
        else:
            # Create new progress
            new_count = 1
            completed = new_count >= target_count

            insert_query = """
            INSERT INTO daily_activity_progress
            (goal_id, profile_id, activity_date, current_count, completed, completed_at)
            VALUES (%s, %s, %s, %s, %s, CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END)
            RETURNING id;
            """

            result = self.db.execute_insert_returning(insert_query,
                                                     (goal_id, profile_id, activity_date, new_count, completed, completed))

            if completed and result:
                self._update_activity_streak(goal_id, profile_id, activity_date)

            # Get full progress with goal details
            return self.get_activity_progress_by_id(str(result)) if result else None

    def _update_activity_streak(self, goal_id: str, profile_id: str, current_date):
        """Update streak count for an activity."""
        from datetime import timedelta, date

        if isinstance(current_date, datetime):
            current_date = current_date.date()
        elif not isinstance(current_date, date):
            current_date = date.today()

        yesterday = current_date - timedelta(days=1)

        # Check if activity was completed yesterday
        query = """
        SELECT completed, streak_days FROM daily_activity_progress
        WHERE goal_id = %s AND activity_date = %s;
        """

        yesterday_result = self.db.execute_query(query, (goal_id, yesterday))

        if yesterday_result and yesterday_result[0]['completed']:
            # Continue streak
            yesterday_streak = yesterday_result[0]['streak_days'] or 0
            new_streak = yesterday_streak + 1
        else:
            # Start new streak
            new_streak = 1

        # Update streak for today
        update_query = """
        UPDATE daily_activity_progress
        SET streak_days = %s
        WHERE goal_id = %s AND activity_date = %s;
        """

        try:
            self.db.execute_query(update_query, (new_streak, goal_id, current_date), fetch=False)
        except Exception as e:
            logger.error(f"Error updating streak: {e}")

    def get_activity_progress_by_id(self, progress_id: str) -> Optional[Dict]:
        """Get activity progress with goal details by ID."""
        query = """
        SELECT p.*, g.activity_title, g.activity_key, g.activity_category, g.target_count, g.icon, g.color,
               g.motivational_messages, g.completion_message, g.duration_minutes, g.benefits
        FROM daily_activity_progress p
        JOIN daily_activity_goals g ON p.goal_id = g.id
        WHERE p.id = %s;
        """

        try:
            result = self.db.execute_query(query, (progress_id,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting activity progress by ID: {e}")
            return None

    def close(self):
        """Close database connections."""
        self.db.close_pool()


# Global database service instance
db_service = None

def get_db_service() -> DatabaseService:
    """Get global database service instance."""
    global db_service
    if db_service is None:
        db_service = DatabaseService()
    return db_service