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

            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_activities_profile_id ON baby_activities(profile_id);",
                "CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON baby_activities(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_activities_category ON baby_activities(category);",
                "CREATE INDEX IF NOT EXISTS idx_activities_type ON baby_activities(activity_type);"
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
        """Create a new activity."""
        query = """
        INSERT INTO baby_activities
        (profile_id, timestamp, category, activity_type, description, amount, unit,
         duration_minutes, notes, tags, source, sender)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        params = (profile_id, timestamp, category, activity_type, description, amount,
                 unit, duration_minutes, notes, tags, source, sender)

        result = self.db.execute_insert_returning(query, params)
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

        stats['daily_averages'] = {}
        for row in result:
            daily_avg = round(row['category_count'] / days, 1)
            stats['daily_averages'][f"{row['category']}_per_day"] = daily_avg

        return stats

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