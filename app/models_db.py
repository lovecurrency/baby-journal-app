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
        return cls(
            id=str(row['id']),
            profile_id=str(row['profile_id']),
            timestamp=row['timestamp'],
            category=ActivityCategory(row['category']),
            activity_type=ActivityType(row['activity_type']),
            description=row['description'],
            amount=row['amount'],
            unit=row['unit'],
            duration_minutes=row['duration_minutes'],
            notes=row['notes'],
            tags=row['tags'] or [],
            source=row['source'],
            sender=row['sender']
        )

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
            return self.db.get_activity_statistics(self.profile.id)
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

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