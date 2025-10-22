"""
Database-backed models for baby activity journal.
This replaces the JSON-based models with database persistence.
"""

from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum
import uuid
import logging

from .database import get_db_service
from .models import ActivityCategory, ActivityType  # Import enums from original models

logger = logging.getLogger(__name__)


class ReminderType(Enum):
    """Types of activity reminders."""
    RECURRING = "recurring"  # e.g., every 3 hours
    SCHEDULED = "scheduled"  # e.g., daily at 2:00 PM
    ACTIVITY_BASED = "activity_based"  # e.g., if no feeding in last 4 hours


@dataclass
class DailyActivityGoal:
    """Represents an age-appropriate daily activity goal."""
    activity_key: str
    activity_title: str
    activity_category: str
    age_range_min: int
    age_range_max: int
    target_count: int
    activity_description: Optional[str] = None
    duration_minutes: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    motivational_messages: Optional[Dict] = None
    completion_message: Optional[str] = None
    benefits: Optional[str] = None
    enabled: bool = True
    priority: int = 1
    id: Optional[str] = None
    profile_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Generate unique ID if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        """Convert goal to dictionary."""
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'activity_key': self.activity_key,
            'activity_title': self.activity_title,
            'activity_description': self.activity_description,
            'activity_category': self.activity_category,
            'age_range_min': self.age_range_min,
            'age_range_max': self.age_range_max,
            'target_count': self.target_count,
            'duration_minutes': self.duration_minutes,
            'icon': self.icon,
            'color': self.color,
            'motivational_messages': self.motivational_messages,
            'completion_message': self.completion_message,
            'benefits': self.benefits,
            'enabled': self.enabled,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_db_row(cls, row: Dict) -> 'DailyActivityGoal':
        """Create goal from database row."""
        return cls(
            id=str(row['id']),
            profile_id=str(row['profile_id']),
            activity_key=row['activity_key'],
            activity_title=row['activity_title'],
            activity_description=row['activity_description'],
            activity_category=row['activity_category'],
            age_range_min=row['age_range_min'],
            age_range_max=row['age_range_max'],
            target_count=row['target_count'],
            duration_minutes=row['duration_minutes'],
            icon=row['icon'],
            color=row['color'],
            motivational_messages=row['motivational_messages'],
            completion_message=row['completion_message'],
            benefits=row['benefits'],
            enabled=row['enabled'],
            priority=row['priority'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


@dataclass
class DailyActivityProgress:
    """Represents daily progress for an activity goal."""
    goal_id: str
    profile_id: str
    activity_date: datetime
    current_count: int = 0
    completed: bool = False
    completed_at: Optional[datetime] = None
    streak_days: int = 0
    notes: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Generate unique ID if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        """Convert progress to dictionary."""
        return {
            'id': self.id,
            'goal_id': self.goal_id,
            'profile_id': self.profile_id,
            'activity_date': self.activity_date.date().isoformat() if isinstance(self.activity_date, datetime) else self.activity_date.isoformat(),
            'current_count': self.current_count,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'streak_days': self.streak_days,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_db_row(cls, row: Dict) -> 'DailyActivityProgress':
        """Create progress from database row."""
        return cls(
            id=str(row['id']),
            goal_id=str(row['goal_id']),
            profile_id=str(row['profile_id']),
            activity_date=row['activity_date'],
            current_count=row['current_count'],
            completed=row['completed'],
            completed_at=row['completed_at'],
            streak_days=row['streak_days'],
            notes=row['notes'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


@dataclass
class BabyActivity:
    """Represents a single baby activity with database persistence."""
    timestamp: datetime
    category: ActivityCategory
    activity_type: ActivityType
    description: str
    amount: Optional[float] = None
    unit: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    source: str = "whatsapp"
    sender: Optional[str] = None
    id: Optional[str] = None
    profile_id: Optional[str] = None

    def __post_init__(self):
        """Generate unique ID if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        """Convert activity to dictionary."""
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category.value,
            'activity_type': self.activity_type.value,
            'description': self.description,
            'amount': self.amount,
            'unit': self.unit,
            'duration_minutes': self.duration_minutes,
            'notes': self.notes,
            'tags': self.tags,
            'source': self.source,
            'sender': self.sender
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BabyActivity':
        """Create activity from dictionary."""
        # Handle datetime conversion
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

        # Handle enum conversion
        data['category'] = ActivityCategory(data['category'])
        data['activity_type'] = ActivityType(data['activity_type'])

        return cls(**data)

    @classmethod
    def from_db_row(cls, row: Dict) -> 'BabyActivity':
        """Create activity from database row."""
        try:
            # Try to convert category and activity_type with fallback to OTHER
            try:
                category = ActivityCategory(row['category'])
            except (ValueError, KeyError):
                logger.warning(f"Invalid category '{row.get('category')}' for activity {row.get('id')}, using OTHER")
                category = ActivityCategory.OTHER

            try:
                activity_type = ActivityType(row['activity_type'])
            except (ValueError, KeyError):
                logger.warning(f"Invalid activity_type '{row.get('activity_type')}' for activity {row.get('id')}, using OTHER")
                activity_type = ActivityType.OTHER

            return cls(
                id=str(row['id']),
                profile_id=str(row['profile_id']),
                timestamp=row['timestamp'],
                category=category,
                activity_type=activity_type,
                description=row['description'],
                amount=row['amount'],
                unit=row['unit'],
                duration_minutes=row['duration_minutes'],
                notes=row['notes'],
                tags=row['tags'] or [],
                source=row['source'],
                sender=row['sender']
            )
        except Exception as e:
            logger.error(f"Failed to create activity from database row: {e}")
            logger.error(f"Row data: {row}")
            raise

    def save(self) -> bool:
        """Save activity to database."""
        if not self.profile_id:
            logger.error("Cannot save activity without profile_id")
            return False

        try:
            db = get_db_service()
            if self.id and db.get_activity_by_id(self.id):
                # Update existing activity
                return db.update_activity(
                    self.id,
                    timestamp=self.timestamp,
                    category=self.category.value,
                    activity_type=self.activity_type.value,
                    description=self.description,
                    amount=self.amount,
                    unit=self.unit,
                    duration_minutes=self.duration_minutes,
                    notes=self.notes,
                    tags=self.tags,
                    source=self.source,
                    sender=self.sender
                )
            else:
                # Create new activity
                new_id = db.create_activity(
                    profile_id=self.profile_id,
                    timestamp=self.timestamp,
                    category=self.category.value,
                    activity_type=self.activity_type.value,
                    description=self.description,
                    amount=self.amount,
                    unit=self.unit,
                    duration_minutes=self.duration_minutes,
                    notes=self.notes,
                    tags=self.tags,
                    source=self.source,
                    sender=self.sender
                )
                if new_id:
                    self.id = new_id
                    return True
                return False
        except Exception as e:
            logger.error(f"Error saving activity: {e}")
            return False

    def delete(self) -> bool:
        """Delete activity from database."""
        if not self.id:
            return False

        try:
            db = get_db_service()
            return db.delete_activity(self.id)
        except Exception as e:
            logger.error(f"Error deleting activity: {e}")
            return False


class BabyProfile:
    """Baby profile information with database persistence."""

    def __init__(self, name: str, birth_date: datetime, gender: Optional[str] = None,
                 birth_weight: Optional[float] = None, birth_height: Optional[float] = None,
                 id: Optional[str] = None):
        self.name = name
        self.birth_date = birth_date
        self.gender = gender
        self.birth_weight = birth_weight  # in kg
        self.birth_height = birth_height  # in cm
        self.id = id or str(uuid.uuid4())

    def get_age_in_days(self) -> int:
        """Get baby's age in days."""
        return (datetime.now() - self.birth_date).days

    def get_age_in_months(self) -> float:
        """Get baby's age in months."""
        days = self.get_age_in_days()
        return round(days / 30.44, 1)

    @property
    def age_days(self) -> int:
        """Property to get age in days for template access."""
        return self.get_age_in_days()

    @property
    def age_months(self) -> float:
        """Property to get age in months for template access."""
        return self.get_age_in_months()

    def to_dict(self) -> Dict:
        """Convert profile to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'birth_date': self.birth_date.isoformat(),
            'gender': self.gender,
            'birth_weight': self.birth_weight,
            'birth_height': self.birth_height,
            'age_days': self.get_age_in_days(),
            'age_months': self.get_age_in_months()
        }

    @classmethod
    def from_db_row(cls, row: Dict) -> 'BabyProfile':
        """Create profile from database row."""
        profile = cls(
            id=str(row['id']),
            name=row['name'],
            birth_date=row['birth_date'],
            gender=row['gender'],
            birth_weight=row['birth_weight'],
            birth_height=row['birth_height']
        )
        profile._is_from_db = True  # Mark as loaded from database
        return profile

    def save(self) -> bool:
        """Save profile to database."""
        try:
            db = get_db_service()
            logger.info(f"Attempting to save profile: {self.name}, ID: {self.id}")

            # For new profiles (just created), always try to create
            # Don't check existing since we're creating a new one
            if not hasattr(self, '_is_from_db') or not self._is_from_db:
                logger.info("Creating new profile in database")
                # Create new profile
                new_id = db.create_profile(
                    name=self.name,
                    birth_date=self.birth_date,
                    gender=self.gender,
                    birth_weight=self.birth_weight,
                    birth_height=self.birth_height
                )
                if new_id:
                    logger.info(f"Profile created successfully with ID: {new_id}")
                    self.id = new_id
                    self._is_from_db = True
                    return True
                else:
                    logger.error("Profile creation returned None - database insert failed")
                    return False
            else:
                # Update existing profile
                logger.info(f"Updating existing profile with ID: {self.id}")
                result = db.update_profile(
                    self.id,
                    name=self.name,
                    birth_date=self.birth_date,
                    gender=self.gender,
                    birth_weight=self.birth_weight,
                    birth_height=self.birth_height
                )
                logger.info(f"Profile update result: {result}")
                return result
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def delete(self) -> bool:
        """Delete profile from database."""
        try:
            db = get_db_service()
            return db.delete_profile(self.id)
        except Exception as e:
            logger.error(f"Error deleting profile: {e}")
            return False


@dataclass
class ActivityReminder:
    """Represents an activity reminder with database persistence."""
    reminder_type: ReminderType
    activity_category: ActivityCategory
    title: str
    message: str
    enabled: bool = True
    recurrence_hours: Optional[int] = None
    scheduled_time: Optional[str] = None  # Format: "HH:MM"
    last_activity_hours: Optional[int] = None
    last_triggered_at: Optional[datetime] = None
    id: Optional[str] = None
    profile_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Generate unique ID if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        """Convert reminder to dictionary."""
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'reminder_type': self.reminder_type.value,
            'activity_category': self.activity_category.value,
            'title': self.title,
            'message': self.message,
            'enabled': self.enabled,
            'recurrence_hours': self.recurrence_hours,
            'scheduled_time': self.scheduled_time,
            'last_activity_hours': self.last_activity_hours,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_db_row(cls, row: Dict) -> 'ActivityReminder':
        """Create reminder from database row."""
        try:
            return cls(
                id=str(row['id']),
                profile_id=str(row['profile_id']),
                reminder_type=ReminderType(row['reminder_type']),
                activity_category=ActivityCategory(row['activity_category']),
                title=row['title'],
                message=row['message'],
                enabled=row['enabled'],
                recurrence_hours=row['recurrence_hours'],
                scheduled_time=row['scheduled_time'],
                last_activity_hours=row['last_activity_hours'],
                last_triggered_at=row['last_triggered_at'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        except Exception as e:
            logger.error(f"Failed to create reminder from database row: {e}")
            logger.error(f"Row data: {row}")
            raise

    def save(self) -> bool:
        """Save reminder to database."""
        if not self.profile_id:
            logger.error("Cannot save reminder without profile_id")
            return False

        try:
            db = get_db_service()
            if self.id and db.get_reminder_by_id(self.id):
                # Update existing reminder
                return db.update_reminder(
                    self.id,
                    reminder_type=self.reminder_type.value,
                    activity_category=self.activity_category.value,
                    title=self.title,
                    message=self.message,
                    enabled=self.enabled,
                    recurrence_hours=self.recurrence_hours,
                    scheduled_time=self.scheduled_time,
                    last_activity_hours=self.last_activity_hours,
                    last_triggered_at=self.last_triggered_at
                )
            else:
                # Create new reminder
                new_id = db.create_reminder(
                    profile_id=self.profile_id,
                    reminder_type=self.reminder_type.value,
                    activity_category=self.activity_category.value,
                    title=self.title,
                    message=self.message,
                    enabled=self.enabled,
                    recurrence_hours=self.recurrence_hours,
                    scheduled_time=self.scheduled_time,
                    last_activity_hours=self.last_activity_hours
                )
                if new_id:
                    self.id = new_id
                    return True
                return False
        except Exception as e:
            logger.error(f"Error saving reminder: {e}")
            return False

    def delete(self) -> bool:
        """Delete reminder from database."""
        if not self.id:
            return False

        try:
            db = get_db_service()
            return db.delete_reminder(self.id)
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            return False


class ActivityJournal:
    """Manages collection of baby activities with database persistence."""

    def __init__(self):
        self.profile: Optional[BabyProfile] = None
        self.db = get_db_service()
        self.activities: List[BabyActivity] = []  # Cache for compatibility

    def set_profile(self, profile: BabyProfile):
        """Set baby profile."""
        self.profile = profile
        try:
            if profile.save():
                logger.info(f"Profile saved successfully: {profile.name}")
            else:
                logger.error("Failed to save profile")
                raise Exception("Profile save operation returned False - database insert failed")
        except Exception as e:
            logger.error(f"Error in set_profile: {e}")
            raise e

    def load_profile(self) -> Optional[BabyProfile]:
        """Load profile from database."""
        try:
            profile_data = self.db.get_profile()
            if profile_data:
                self.profile = BabyProfile.from_db_row(profile_data)
                return self.profile
            return None
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            return None

    def add_activity(self, activity: BabyActivity):
        """Add a new activity to journal."""
        # Try to reload profile if missing
        if not self.profile:
            logger.warning("Profile not loaded, attempting to reload from database")
            self.load_profile()

        if not self.profile:
            logger.error("Cannot add activity without a profile - please create profile first")
            raise Exception("Profile is required to add activities. Please create a baby profile first.")

        activity.profile_id = self.profile.id
        if activity.save():
            logger.info(f"Activity saved successfully: {activity.description}")
            # Update cache
            self.activities.append(activity)
            return True
        else:
            logger.error("Failed to save activity")
            raise Exception("Failed to save activity to database")

    def load_activities(self) -> List[BabyActivity]:
        """Load activities from database."""
        if not self.profile:
            return []

        try:
            activity_rows = self.db.get_activities(self.profile.id)
            self.activities = [BabyActivity.from_db_row(row) for row in activity_rows]
            return self.activities
        except Exception as e:
            logger.error(f"Error loading activities: {e}")
            return []

    def get_activities_by_date(self, date: datetime) -> List[BabyActivity]:
        """Get activities for a specific date."""
        if not self.profile:
            return []

        try:
            activity_rows = self.db.get_activities(self.profile.id, date=date)
            return [BabyActivity.from_db_row(row) for row in activity_rows]
        except Exception as e:
            logger.error(f"Error getting activities by date: {e}")
            return []

    def get_activities_by_category(self, category: ActivityCategory) -> List[BabyActivity]:
        """Get activities by category."""
        if not self.profile:
            return []

        try:
            activity_rows = self.db.get_activities(self.profile.id, category=category.value)
            return [BabyActivity.from_db_row(row) for row in activity_rows]
        except Exception as e:
            logger.error(f"Error getting activities by category: {e}")
            return []

    def get_recent_activities(self, limit: int = 10) -> List[BabyActivity]:
        """Get most recent activities."""
        if not self.profile:
            return []

        try:
            activity_rows = self.db.get_activities(self.profile.id, limit=limit)
            return [BabyActivity.from_db_row(row) for row in activity_rows]
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []

    def get_statistics(self) -> Dict:
        """Get statistics about activities."""
        if not self.profile:
            return {}

        try:
            # Try database statistics first
            db_stats = self.db.get_activity_statistics(self.profile.id)
            if db_stats and db_stats.get('total_activities', 0) > 0:
                logger.info(f"Database statistics successful: {db_stats}")
                return db_stats
            else:
                logger.warning("Database statistics returned empty, falling back to activity cache calculation")
                # Fallback to calculating from loaded activities (like original version)
                return self._calculate_statistics_from_activities()
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}, falling back to activity cache")
            return self._calculate_statistics_from_activities()

    def _calculate_statistics_from_activities(self) -> Dict:
        """Calculate statistics from loaded activities (fallback method)."""
        if not self.activities:
            logger.warning("No activities loaded for statistics calculation")
            return {}

        logger.info(f"Calculating statistics from {len(self.activities)} loaded activities")

        stats = {
            'total_activities': len(self.activities),
            'by_category': {},
            'by_type': {},
            'daily_averages': {},
            'date_range': {}
        }

        # Count by category and type
        for activity in self.activities:
            try:
                category = activity.category.value if activity.category else 'unknown'
                activity_type = activity.activity_type.value if activity.activity_type else 'unknown'

                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                stats['by_type'][activity_type] = stats['by_type'].get(activity_type, 0) + 1
            except Exception as e:
                logger.warning(f"Error processing activity for stats: {e}")
                continue

        # Calculate date range
        if self.activities:
            try:
                timestamps = [a.timestamp for a in self.activities if a.timestamp]
                if timestamps:
                    stats['date_range'] = {
                        'start': min(timestamps).isoformat(),
                        'end': max(timestamps).isoformat()
                    }
            except Exception as e:
                logger.warning(f"Error calculating date range: {e}")

        logger.info(f"Calculated statistics: {stats}")
        return stats

    def get_activity_by_id(self, activity_id: str) -> Optional[BabyActivity]:
        """Get activity by ID."""
        try:
            activity_row = self.db.get_activity_by_id(activity_id)
            if activity_row:
                return BabyActivity.from_db_row(activity_row)
            return None
        except Exception as e:
            logger.error(f"Error getting activity by ID: {e}")
            return None

    def delete_activity_by_id(self, activity_id: str) -> bool:
        """Delete activity by ID."""
        try:
            activity = self.get_activity_by_id(activity_id)
            if activity:
                success = activity.delete()
                if success:
                    # Update cache
                    self.activities = [a for a in self.activities if a.id != activity_id]
                return success
            return False
        except Exception as e:
            logger.error(f"Error deleting activity by ID: {e}")
            return False

    def update_activity_by_id(self, activity_id: str, updates: Dict) -> bool:
        """Update activity by ID."""
        try:
            activity = self.get_activity_by_id(activity_id)
            if activity:
                # Update fields
                for field, value in updates.items():
                    if hasattr(activity, field):
                        setattr(activity, field, value)

                success = activity.save()
                if success:
                    # Update cache
                    for i, cached_activity in enumerate(self.activities):
                        if cached_activity.id == activity_id:
                            self.activities[i] = activity
                            break
                return success
            return False
        except Exception as e:
            logger.error(f"Error updating activity by ID: {e}")
            return False

    # Legacy methods for compatibility (no-op since database handles persistence)
    def _save_activities(self):
        """Legacy method - no-op since database handles persistence."""
        pass

    def _save_profile(self):
        """Legacy method - no-op since database handles persistence."""
        pass