"""
Activity processor to convert WhatsApp messages to structured activities.
"""

from datetime import datetime
from typing import Dict, Optional, List
from app.models import BabyActivity, ActivityCategory, ActivityType
from app.whatsapp_parser import WhatsAppParser
import re


class ActivityProcessor:
    """Process and categorize baby activities from various inputs."""

    # Mapping of keywords to activity types
    ACTIVITY_MAPPINGS = {
        ActivityType.BOTTLE_FEED: ['bottle', 'formula', 'expressed'],
        ActivityType.BREAST_FEED: ['breast', 'nursing', 'breastfeed', 'bf'],
        ActivityType.SOLID_FOOD: ['solid', 'puree', 'cereal', 'food', 'ate', 'breakfast', 'lunch', 'dinner', 'snack'],

        ActivityType.WET_DIAPER: ['wet', 'pee', 'urinated'],
        ActivityType.DIRTY_DIAPER: ['poop', 'poo', 'bowel', 'dirty', 'soiled', 'bm'],
        ActivityType.DIAPER_CHANGE: ['changed', 'diaper change', 'new diaper'],

        ActivityType.NAP: ['nap', 'napped', 'daytime sleep', 'afternoon sleep'],
        ActivityType.NIGHT_SLEEP: ['bedtime', 'night sleep', 'went to bed', 'sleeping through'],
        ActivityType.WAKE_UP: ['woke', 'wake up', 'awake', 'got up'],

        ActivityType.TEMPERATURE: ['temp', 'temperature', 'fever', 'degrees'],
        ActivityType.SYMPTOM: ['cough', 'sneeze', 'rash', 'crying', 'fussy', 'teething', 'sick'],
        ActivityType.DOCTOR_VISIT: ['doctor', 'pediatrician', 'clinic', 'checkup', 'appointment'],

        ActivityType.WEIGHT: ['weight', 'weigh', 'weighs', 'kg', 'lbs', 'pounds'],
        ActivityType.HEIGHT: ['height', 'length', 'tall', 'cm', 'inches'],
        ActivityType.HEAD_CIRCUMFERENCE: ['head circumference', 'head size'],

        ActivityType.MEDICATION: ['medicine', 'medication', 'dose', 'tylenol', 'ibuprofen', 'antibiotic'],
        ActivityType.VITAMIN: ['vitamin', 'supplement', 'd3', 'iron'],

        ActivityType.VACCINATION: ['vaccine', 'vaccination', 'shot', 'immunization', 'immunize'],
        ActivityType.IMMUNIZATION: ['immunization', 'immunize', 'shots'],
        ActivityType.BOOSTER: ['booster', 'booster shot', 'follow up vaccine'],

        ActivityType.BREAST_MILK_EXTRACTION: ['extracted', 'pumped', 'pumping', 'expressing', 'expressed milk']
    }

    # Category mapping for activity types
    TYPE_TO_CATEGORY = {
        ActivityType.BOTTLE_FEED: ActivityCategory.FEEDING,
        ActivityType.BREAST_FEED: ActivityCategory.FEEDING,
        ActivityType.SOLID_FOOD: ActivityCategory.FEEDING,

        ActivityType.WET_DIAPER: ActivityCategory.DIAPER,
        ActivityType.DIRTY_DIAPER: ActivityCategory.DIAPER,
        ActivityType.DIAPER_CHANGE: ActivityCategory.DIAPER,

        ActivityType.NAP: ActivityCategory.SLEEP,
        ActivityType.NIGHT_SLEEP: ActivityCategory.SLEEP,
        ActivityType.WAKE_UP: ActivityCategory.SLEEP,

        ActivityType.TEMPERATURE: ActivityCategory.HEALTH,
        ActivityType.SYMPTOM: ActivityCategory.HEALTH,
        ActivityType.DOCTOR_VISIT: ActivityCategory.HEALTH,

        ActivityType.WEIGHT: ActivityCategory.MEASUREMENT,
        ActivityType.HEIGHT: ActivityCategory.MEASUREMENT,
        ActivityType.HEAD_CIRCUMFERENCE: ActivityCategory.MEASUREMENT,

        ActivityType.MEDICATION: ActivityCategory.MEDICINE,
        ActivityType.VITAMIN: ActivityCategory.MEDICINE,

        ActivityType.VACCINATION: ActivityCategory.VACCINE,
        ActivityType.IMMUNIZATION: ActivityCategory.VACCINE,
        ActivityType.BOOSTER: ActivityCategory.VACCINE,

        ActivityType.BREAST_MILK_EXTRACTION: ActivityCategory.FEEDING,

        ActivityType.OTHER: ActivityCategory.OTHER
    }

    def __init__(self):
        """Initialize the activity processor."""
        self.parser = WhatsAppParser()

    def process_whatsapp_file(self, file_path: str) -> List[BabyActivity]:
        """
        Process a WhatsApp export file and convert to BabyActivity objects.

        Args:
            file_path: Path to WhatsApp export file

        Returns:
            List of BabyActivity objects
        """
        raw_activities = self.parser.parse_whatsapp_export(file_path)
        return [self._convert_to_baby_activity(raw) for raw in raw_activities]

    def process_message(self, message: str, sender: Optional[str] = None) -> Optional[BabyActivity]:
        """
        Process a single message and convert to BabyActivity.

        Args:
            message: Message text
            sender: Optional sender name

        Returns:
            BabyActivity object or None if no activity detected
        """
        # Try to parse as WhatsApp message first
        raw_activity = self.parser.parse_message(message)

        if raw_activity:
            return self._convert_to_baby_activity(raw_activity)

        # Otherwise, process as plain text
        return self._process_plain_text(message, sender)

    def _convert_to_baby_activity(self, raw_activity: Dict) -> BabyActivity:
        """Convert raw parsed activity to BabyActivity object."""
        # Use the activity type from WhatsApp parser if available, otherwise determine from text
        if 'type' in raw_activity:
            # Map WhatsApp parser types to our ActivityType enum
            whatsapp_type = raw_activity['type']
            if whatsapp_type == 'feeding':
                # Use subtype to determine specific feeding type
                feeding_subtype = raw_activity.get('subtype', 'unknown')
                if feeding_subtype == 'breast':
                    activity_type = ActivityType.BREAST_FEED
                elif feeding_subtype == 'extraction':
                    activity_type = ActivityType.BREAST_MILK_EXTRACTION
                elif feeding_subtype in ['formula', 'bottle']:
                    activity_type = ActivityType.BOTTLE_FEED
                else:
                    # Default based on amount - if amount specified, likely bottle
                    details = raw_activity.get('details', {})
                    if details.get('amount'):
                        activity_type = ActivityType.BOTTLE_FEED
                    else:
                        activity_type = ActivityType.BREAST_FEED
            elif whatsapp_type == 'diaper':
                activity_type = ActivityType.DIAPER_CHANGE
            elif whatsapp_type == 'sleep':
                activity_type = ActivityType.NAP
            elif whatsapp_type == 'medicine':
                activity_type = ActivityType.MEDICATION
            elif whatsapp_type == 'vaccine':
                activity_type = ActivityType.VACCINATION
            elif whatsapp_type == 'weight':
                activity_type = ActivityType.WEIGHT
            elif whatsapp_type == 'height':
                activity_type = ActivityType.HEIGHT
            elif whatsapp_type == 'temperature':
                activity_type = ActivityType.TEMPERATURE
            else:
                activity_type = ActivityType.OTHER
        else:
            # Fallback to determine from text
            activity_type = self._determine_activity_type(raw_activity.get('original_message', ''))

        # Get category from activity type
        category = self.TYPE_TO_CATEGORY.get(activity_type, ActivityCategory.OTHER)

        # Extract details
        details = raw_activity.get('details', {})

        # Create BabyActivity object
        return BabyActivity(
            timestamp=datetime.fromisoformat(raw_activity['timestamp']),
            category=category,
            activity_type=activity_type,
            description=raw_activity.get('original_message', ''),
            amount=details.get('amount'),
            unit=details.get('unit'),
            duration_minutes=self._extract_duration(details.get('notes', '')),
            notes=details.get('notes'),
            tags=self._extract_tags(raw_activity.get('original_message', '')),
            source='whatsapp',
            sender=raw_activity.get('sender')
        )

    def _process_plain_text(self, text: str, sender: Optional[str] = None) -> Optional[BabyActivity]:
        """Process plain text message to extract activity."""
        activity_type = self._determine_activity_type(text)

        if activity_type == ActivityType.OTHER:
            # No specific activity detected
            return None

        category = self.TYPE_TO_CATEGORY.get(activity_type, ActivityCategory.OTHER)

        # Extract quantities
        amount, unit = self._extract_amount_and_unit(text)
        duration = self._extract_duration(text)

        return BabyActivity(
            timestamp=datetime.now(),
            category=category,
            activity_type=activity_type,
            description=text,
            amount=amount,
            unit=unit,
            duration_minutes=duration,
            notes=text,
            tags=self._extract_tags(text),
            source='manual',
            sender=sender
        )

    def _determine_activity_type(self, text: str) -> ActivityType:
        """Determine activity type from message text."""
        text_lower = text.lower()

        # Check each activity type's keywords
        for activity_type, keywords in self.ACTIVITY_MAPPINGS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return activity_type

        return ActivityType.OTHER

    def _extract_amount_and_unit(self, text: str) -> tuple[Optional[float], Optional[str]]:
        """Extract numerical amount and unit from text."""
        # Common patterns for amounts
        patterns = [
            (r'(\d+(?:\.\d+)?)\s*(ml|milliliters?)', 'ml'),
            (r'(\d+(?:\.\d+)?)\s*(oz|ounces?)', 'oz'),
            (r'(\d+(?:\.\d+)?)\s*(g|grams?)', 'g'),
            (r'(\d+(?:\.\d+)?)\s*(kg|kilograms?)', 'kg'),
            (r'(\d+(?:\.\d+)?)\s*(lbs?|pounds?)', 'lbs'),
            (r'(\d+(?:\.\d+)?)\s*(mins?|minutes?)', 'minutes'),
            (r'(\d+(?:\.\d+)?)\s*(hrs?|hours?)', 'hours'),
            (r'(\d+(?:\.\d+)?)\s*(°?[FC])', 'degrees'),
            (r'(\d+(?:\.\d+)?)\s*(cm|centimeters?)', 'cm'),
            (r'(\d+(?:\.\d+)?)\s*(in|inches?)', 'inches')
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1))
                    return amount, unit
                except ValueError:
                    continue

        return None, None

    def _extract_duration(self, text: str) -> Optional[int]:
        """Extract duration in minutes from text."""
        # Look for duration patterns
        patterns = [
            (r'(\d+(?:\.\d+)?)\s*(?:hrs?|hours?)', 60),  # hours to minutes
            (r'(\d+(?:\.\d+)?)\s*(?:mins?|minutes?)', 1),  # minutes
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    return int(value * multiplier)
                except ValueError:
                    continue

        return None

    def _extract_tags(self, text: str) -> List[str]:
        """Extract hashtags or relevant tags from text."""
        tags = []

        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text)
        tags.extend(hashtags)

        # Add automatic tags based on content
        text_lower = text.lower()

        if any(word in text_lower for word in ['urgent', 'emergency', 'important']):
            tags.append('urgent')

        if any(word in text_lower for word in ['happy', 'good', 'great', 'excellent']):
            tags.append('positive')

        if any(word in text_lower for word in ['concern', 'worried', 'problem']):
            tags.append('concern')

        if any(word in text_lower for word in ['first', 'milestone', 'new']):
            tags.append('milestone')

        return list(set(tags))  # Remove duplicates

    def categorize_by_time(self, activities: List[BabyActivity]) -> Dict:
        """Categorize activities by time of day."""
        time_categories = {
            'morning': [],    # 6 AM - 12 PM
            'afternoon': [],  # 12 PM - 6 PM
            'evening': [],    # 6 PM - 10 PM
            'night': []       # 10 PM - 6 AM
        }

        for activity in activities:
            hour = activity.timestamp.hour

            if 6 <= hour < 12:
                time_categories['morning'].append(activity)
            elif 12 <= hour < 18:
                time_categories['afternoon'].append(activity)
            elif 18 <= hour < 22:
                time_categories['evening'].append(activity)
            else:
                time_categories['night'].append(activity)

        return time_categories