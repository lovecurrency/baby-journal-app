"""
Data models for baby activity journal.
"""

from datetime import datetime
from typing import Optional, List, Dict
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum


class ActivityCategory(Enum):
    """Categories of baby activities."""
    FEEDING = "feeding"
    DIAPER = "diaper"
    SLEEP = "sleep"
    HEALTH = "health"
    VACCINE = "vaccine"
    MEASUREMENT = "measurement"
    MEDICINE = "medicine"
    OTHER = "other"


class ActivityType(Enum):
    """Specific types of baby activities."""
    # Feeding
    BOTTLE_FEED = "bottle_feed"
    BREAST_FEED = "breast_feed"
    SOLID_FOOD = "solid_food"
    BREAST_MILK_EXTRACTION = "breast_milk_extraction"

    # Diaper
    WET_DIAPER = "wet_diaper"
    DIRTY_DIAPER = "dirty_diaper"
    DIAPER_CHANGE = "diaper_change"

    # Sleep
    NAP = "nap"
    NIGHT_SLEEP = "night_sleep"
    WAKE_UP = "wake_up"

    # Health
    TEMPERATURE = "temperature"
    SYMPTOM = "symptom"
    DOCTOR_VISIT = "doctor_visit"

    # Measurement
    WEIGHT = "weight"
    HEIGHT = "height"
    HEAD_CIRCUMFERENCE = "head_circumference"

    # Medicine
    MEDICATION = "medication"
    VITAMIN = "vitamin"

    # Vaccine
    VACCINATION = "vaccination"
    IMMUNIZATION = "immunization"
    BOOSTER = "booster"

    OTHER = "other"


@dataclass
class BabyActivity:
    """Represents a single baby activity."""
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

    def __post_init__(self):
        """Generate unique ID if not provided."""
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        """Convert activity to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['category'] = self.category.value
        data['activity_type'] = self.activity_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'BabyActivity':
        """Create activity from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['category'] = ActivityCategory(data['category'])
        data['activity_type'] = ActivityType(data['activity_type'])
        return cls(**data)


class BabyProfile:
    """Baby profile information."""

    def __init__(self, name: str, birth_date: datetime, gender: Optional[str] = None,
                 birth_weight: Optional[float] = None, birth_height: Optional[float] = None):
        self.name = name
        self.birth_date = birth_date
        self.gender = gender
        self.birth_weight = birth_weight  # in kg
        self.birth_height = birth_height  # in cm
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique ID for baby profile."""
        return f"{self.name.lower().replace(' ', '_')}_{self.birth_date.strftime('%Y%m%d')}"

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


class ActivityJournal:
    """Manages collection of baby activities."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.activities: List[BabyActivity] = []
        self.profile: Optional[BabyProfile] = None
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def set_profile(self, profile: BabyProfile):
        """Set baby profile."""
        self.profile = profile
        self._save_profile()

    def _save_profile(self):
        """Save profile to file."""
        if self.profile:
            profile_path = os.path.join(self.data_dir, 'profile.json')
            with open(profile_path, 'w') as f:
                json.dump(self.profile.to_dict(), f, indent=2)

    def load_profile(self) -> Optional[BabyProfile]:
        """Load profile from file."""
        profile_path = os.path.join(self.data_dir, 'profile.json')
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                data = json.load(f)
                self.profile = BabyProfile(
                    name=data['name'],
                    birth_date=datetime.fromisoformat(data['birth_date']),
                    gender=data.get('gender'),
                    birth_weight=data.get('birth_weight'),
                    birth_height=data.get('birth_height')
                )
                return self.profile
        return None

    def add_activity(self, activity: BabyActivity):
        """Add a new activity to journal."""
        self.activities.append(activity)
        self._save_activities()

    def _save_activities(self):
        """Save activities to file."""
        activities_path = os.path.join(self.data_dir, 'activities.json')
        with open(activities_path, 'w') as f:
            data = [activity.to_dict() for activity in self.activities]
            json.dump(data, f, indent=2, default=str)

    def load_activities(self) -> List[BabyActivity]:
        """Load activities from file."""
        activities_path = os.path.join(self.data_dir, 'activities.json')
        if os.path.exists(activities_path):
            with open(activities_path, 'r') as f:
                data = json.load(f)
                self.activities = [BabyActivity.from_dict(item) for item in data]
                return self.activities
        return []

    def get_activities_by_date(self, date: datetime) -> List[BabyActivity]:
        """Get activities for a specific date."""
        target_date = date.date()
        return [a for a in self.activities if a.timestamp.date() == target_date]

    def get_activities_by_category(self, category: ActivityCategory) -> List[BabyActivity]:
        """Get activities by category."""
        return [a for a in self.activities if a.category == category]

    def get_recent_activities(self, limit: int = 10) -> List[BabyActivity]:
        """Get most recent activities."""
        sorted_activities = sorted(self.activities, key=lambda x: x.timestamp, reverse=True)
        return sorted_activities[:limit]

    def get_statistics(self) -> Dict:
        """Get statistics about activities."""
        if not self.activities:
            return {}

        stats = {
            'total_activities': len(self.activities),
            'by_category': {},
            'by_type': {},
            'daily_averages': {},
            'date_range': {
                'start': min(a.timestamp for a in self.activities).isoformat(),
                'end': max(a.timestamp for a in self.activities).isoformat()
            }
        }

        # Count by category
        for category in ActivityCategory:
            count = len([a for a in self.activities if a.category == category])
            if count > 0:
                stats['by_category'][category.value] = count

        # Count by type
        for activity_type in ActivityType:
            count = len([a for a in self.activities if a.activity_type == activity_type])
            if count > 0:
                stats['by_type'][activity_type.value] = count

        # Calculate daily averages
        days = (datetime.now() - min(a.timestamp for a in self.activities)).days + 1

        # Feeding frequency
        feeding_count = len([a for a in self.activities if a.category == ActivityCategory.FEEDING])
        stats['daily_averages']['feedings'] = round(feeding_count / days, 1)

        # Diaper changes
        diaper_count = len([a for a in self.activities if a.category == ActivityCategory.DIAPER])
        stats['daily_averages']['diaper_changes'] = round(diaper_count / days, 1)

        # Sleep sessions
        sleep_count = len([a for a in self.activities if a.category == ActivityCategory.SLEEP])
        stats['daily_averages']['sleep_sessions'] = round(sleep_count / days, 1)

        return stats

    def get_activity_by_id(self, activity_id: str) -> Optional[BabyActivity]:
        """Get activity by ID."""
        for activity in self.activities:
            if activity.id == activity_id:
                return activity
        return None

    def delete_activity_by_id(self, activity_id: str) -> bool:
        """Delete activity by ID."""
        for i, activity in enumerate(self.activities):
            if activity.id == activity_id:
                self.activities.pop(i)
                self._save_activities()
                return True
        return False

    def update_activity_by_id(self, activity_id: str, updates: Dict) -> bool:
        """Update activity by ID."""
        activity = self.get_activity_by_id(activity_id)
        if activity:
            # Update fields
            for field, value in updates.items():
                if hasattr(activity, field):
                    setattr(activity, field, value)
            self._save_activities()
            return True
        return False