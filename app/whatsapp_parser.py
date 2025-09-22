"""
WhatsApp message parser for baby activity tracking.
Parses exported WhatsApp chat messages to extract baby activity information.
"""

import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json


class WhatsAppParser:
    """Parse WhatsApp messages to extract baby activities."""

    # Activity keywords for pattern matching
    ACTIVITY_PATTERNS = {
        'feeding': {
            'keywords': ['fed', 'feed', 'feeding', 'bottle', 'breast', 'nursing', 'milk', 'formula', 'eat', 'ate', 'drinking', 'extracted', 'pumped', 'pumping'],
            'units': ['ml', 'oz', 'ounces', 'minutes', 'mins'],
            'category': 'feeding'
        },
        'diaper': {
            'keywords': ['diaper', 'nappy', 'poop', 'poo', 'pee', 'wet', 'dirty', 'changed', 'bowel'],
            'category': 'diaper'
        },
        'sleep': {
            'keywords': ['sleep', 'slept', 'nap', 'napped', 'sleeping', 'asleep', 'woke', 'wake', 'awake', 'bedtime'],
            'units': ['hours', 'hrs', 'minutes', 'mins'],
            'category': 'sleep'
        },
        'medicine': {
            'keywords': ['medicine', 'medication', 'vitamin', 'drops', 'tylenol', 'dose', 'gave'],
            'category': 'medicine'
        },
        'milestone': {
            'keywords': ['rolled', 'crawl', 'walk', 'stood', 'smiled', 'laugh', 'tooth', 'word', 'said'],
            'category': 'milestone'
        },
        'weight': {
            'keywords': ['weight', 'weigh', 'weighs', 'weighted'],
            'units': ['kg', 'g', 'lbs', 'pounds', 'ounces', 'oz'],
            'category': 'measurement'
        },
        'height': {
            'keywords': ['height', 'length', 'tall', 'measured'],
            'units': ['cm', 'inches', 'in', 'feet', 'ft'],
            'category': 'measurement'
        },
        'temperature': {
            'keywords': ['temperature', 'temp', 'fever', 'degrees'],
            'units': ['F', 'C', '°F', '°C', 'fahrenheit', 'celsius'],
            'category': 'health'
        }
    }

    def __init__(self):
        """Initialize the WhatsApp parser."""
        self.messages = []
        self.activities = []

    def parse_whatsapp_export(self, file_path: str) -> List[Dict]:
        """
        Parse a WhatsApp chat export file.

        Args:
            file_path: Path to the WhatsApp chat export text file

        Returns:
            List of parsed activities
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse individual messages
        messages = self._extract_messages(content)

        # Extract activities from messages
        activities = []
        for msg in messages:
            activity = self._parse_message_for_activity(msg)
            if activity:
                activities.append(activity)

        self.activities = activities
        return activities

    def parse_message(self, message: str) -> Optional[Dict]:
        """
        Parse a single WhatsApp message for baby activities.

        Args:
            message: A single WhatsApp message string

        Returns:
            Parsed activity dictionary or None if no activity found
        """
        msg_data = self._parse_single_message(message)
        if msg_data:
            return self._parse_message_for_activity(msg_data)
        return None

    def _extract_messages(self, content: str) -> List[Dict]:
        """Extract individual messages from WhatsApp export."""
        messages = []

        # WhatsApp export format variations:
        # [DD/MM/YY, HH:MM:SS AM/PM] Contact: Message
        # [DD/MM/YYYY, HH:MM:SS] Contact: Message
        # DD/MM/YY, HH:MM - Contact: Message
        patterns = [
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]\s*([^:]+):\s*(.+)',
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.+)',
            r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.+)'
        ]

        lines = content.split('\n')
        current_msg = None

        for line in lines:
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    if current_msg:
                        messages.append(current_msg)

                    date_str = match.group(1)
                    time_str = match.group(2)
                    sender = match.group(3).strip()
                    text = match.group(4).strip()

                    current_msg = {
                        'datetime': self._parse_datetime(date_str, time_str),
                        'sender': sender,
                        'text': text,
                        'raw': line
                    }
                    matched = True
                    break

            if not matched and current_msg:
                # Continuation of previous message
                current_msg['text'] += ' ' + line.strip()
                current_msg['raw'] += '\n' + line

        if current_msg:
            messages.append(current_msg)

        return messages

    def _parse_single_message(self, message: str) -> Optional[Dict]:
        """Parse a single message string."""
        patterns = [
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]\s*([^:]+):\s*(.+)',
            r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.+)',
            r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.+)'
        ]

        for pattern in patterns:
            match = re.match(pattern, message)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                sender = match.group(3).strip()
                text = match.group(4).strip()

                return {
                    'datetime': self._parse_datetime(date_str, time_str),
                    'sender': sender,
                    'text': text,
                    'raw': message
                }

        # If no timestamp, treat as plain message
        return {
            'datetime': datetime.now(),
            'sender': 'Unknown',
            'text': message,
            'raw': message
        }

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        """Parse date and time strings to datetime object."""
        # Clean up time string
        time_str = time_str.strip()

        # Try different date formats
        date_formats = [
            '%d/%m/%Y',
            '%d/%m/%y',
            '%m/%d/%Y',
            '%m/%d/%y'
        ]

        for date_fmt in date_formats:
            try:
                date_part = datetime.strptime(date_str, date_fmt).date()
                break
            except ValueError:
                continue
        else:
            date_part = datetime.now().date()

        # Parse time with various formats including AM/PM
        time_formats = [
            '%I:%M:%S %p',  # 12-hour with seconds and AM/PM
            '%I:%M %p',     # 12-hour with AM/PM
            '%H:%M:%S',     # 24-hour with seconds
            '%H:%M'         # 24-hour without seconds
        ]

        for time_fmt in time_formats:
            try:
                time_part = datetime.strptime(time_str, time_fmt).time()
                break
            except ValueError:
                continue
        else:
            time_part = datetime.now().time()

        return datetime.combine(date_part, time_part)

    def _is_whatsapp_meta_message(self, text: str) -> bool:
        """Check if message is a WhatsApp system/meta message that should be ignored."""
        text_lower = text.lower()

        # WhatsApp system message patterns
        meta_patterns = [
            # Group management
            r'you created group',
            r'you changed the group name',
            r'you changed this group\'s icon',
            r'added you',
            r'left the group',
            r'removed from the group',
            r'group description changed',

            # Media and links that aren't baby related
            r'^https?://',  # URLs by themselves
            r'omitted',     # WhatsApp media omitted messages
            r'document omitted',
            r'image omitted',
            r'video omitted',
            r'audio omitted',

            # System notifications
            r'messages and calls are end-to-end encrypted',
            r'security code changed',
            r'missed voice call',
            r'missed video call',

            # Empty or very short messages that aren't meaningful
            r'^[^a-zA-Z0-9]*$',  # Only symbols/punctuation
            r'^[0-9\s]*$',       # Only numbers and spaces
        ]

        for pattern in meta_patterns:
            if re.search(pattern, text_lower):
                return True

        # Additional check for very short messages without baby activity keywords
        if len(text.strip()) < 5:  # Very short messages
            return True

        return False

    def _parse_message_for_activity(self, msg_data: Dict) -> Optional[Dict]:
        """Extract activity information from a parsed message."""
        text = msg_data['text'].lower()
        original_text = msg_data['text']

        # Filter out WhatsApp meta-messages and system notifications
        if self._is_whatsapp_meta_message(original_text):
            return None

        for activity_type, config in self.ACTIVITY_PATTERNS.items():
            for keyword in config['keywords']:
                if keyword in text:
                    # Check for time in the message content (e.g., "1:18 pm", "4:45 pm")
                    actual_timestamp = self._extract_time_from_message(original_text, msg_data['datetime'])

                    activity = {
                        'timestamp': actual_timestamp.isoformat(),
                        'type': activity_type,
                        'category': config['category'],
                        'sender': msg_data['sender'],
                        'original_message': msg_data['text'],
                        'details': {}
                    }

                    # Special handling for feeding to determine breast vs formula
                    if activity_type == 'feeding':
                        activity['subtype'] = self._determine_feeding_type(text)

                    # Extract quantities if applicable
                    if 'units' in config:
                        quantity = self._extract_quantity(text, config['units'])
                        if quantity:
                            activity['details']['amount'] = quantity['value']
                            activity['details']['unit'] = quantity['unit']

                    # Extract additional context
                    activity['details']['notes'] = self._extract_notes(text, keyword)

                    return activity

        return None

    def _extract_quantity(self, text: str, units: List[str]) -> Optional[Dict]:
        """Extract numerical quantities with units from text."""
        for unit in units:
            # Look for patterns like "150 ml", "6 oz", "2.5 hours"
            pattern = rf'(\d+(?:\.\d+)?)\s*{re.escape(unit)}'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    'value': float(match.group(1)),
                    'unit': unit
                }

        return None

    def _extract_notes(self, text: str, keyword: str) -> str:
        """Extract contextual notes around the activity keyword."""
        # Find sentence containing the keyword
        sentences = text.split('.')
        for sentence in sentences:
            if keyword in sentence.lower():
                return sentence.strip()

        # If no sentence found, return first 100 chars
        return text[:100].strip()

    def _extract_time_from_message(self, text: str, default_datetime: datetime) -> datetime:
        """Extract time mentioned in the message and use it instead of message timestamp."""
        import re

        # Look for time patterns like "1:18 pm", "4:45 PM", "13:30", "1:18pm"
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*([ap]m)',  # 1:18 pm or 1:18pm
            r'(\d{1,2}):(\d{2})\s*([AP]M)',  # 1:18 PM or 1:18PM
            r'(\d{1,2}):(\d{2})(?!\s*[ap]m)',  # 13:30 (24-hour format)
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))

                # Handle AM/PM if present
                if len(match.groups()) == 3:
                    period = match.group(3).lower()
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0

                # Create new datetime with extracted time
                try:
                    new_time = datetime(
                        default_datetime.year,
                        default_datetime.month,
                        default_datetime.day,
                        hour,
                        minute,
                        0
                    )

                    # If the extracted time is later than the message time,
                    # it might be from the previous day
                    if new_time > default_datetime:
                        # The activity likely happened earlier (before the message was sent)
                        # Keep the extracted time as it represents when the activity actually happened
                        pass

                    return new_time

                except ValueError:
                    # Invalid time, use default
                    pass

        # No time found in message, use the message timestamp
        return default_datetime

    def _determine_feeding_type(self, text: str) -> str:
        """Determine if feeding is breast milk or formula/bottle based on keywords."""
        text_lower = text.lower()

        # Check for extraction keywords first
        extraction_keywords = ['extracted', 'pumped', 'pumping', 'expressing', 'expressed milk']
        for keyword in extraction_keywords:
            if keyword in text_lower:
                return 'extraction'

        # Keywords for breast feeding
        breast_keywords = [
            'mummy', 'mother', 'mom', 'mama', 'ma',
            'breast', 'bf', 'nursing', 'nursed',
            'direct', 'latch'
        ]

        # Keywords for formula/bottle feeding
        formula_keywords = [
            'powder', 'formula', 'bottle', 'top feed', 'topfeed',
            'ebm', 'artificial', 'supplement', 'fortified'
        ]

        # Check for breast feeding indicators
        for keyword in breast_keywords:
            if keyword in text_lower:
                return 'breast'

        # Check for formula feeding indicators
        for keyword in formula_keywords:
            if keyword in text_lower:
                return 'formula'

        # Default to bottle if ml/oz is mentioned (usually formula/expressed)
        if 'ml' in text_lower or 'oz' in text_lower:
            return 'bottle'

        # Default to breast feeding if no specific type mentioned
        return 'breast'

    def export_to_json(self, output_path: str):
        """Export parsed activities to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.activities, f, indent=2, default=str)

    def get_activity_summary(self) -> Dict:
        """Get a summary of all parsed activities."""
        summary = {
            'total_activities': len(self.activities),
            'by_type': {},
            'by_category': {},
            'date_range': None
        }

        if self.activities:
            # Count by type and category
            for activity in self.activities:
                act_type = activity['type']
                category = activity['category']

                summary['by_type'][act_type] = summary['by_type'].get(act_type, 0) + 1
                summary['by_category'][category] = summary['by_category'].get(category, 0) + 1

            # Get date range
            dates = [datetime.fromisoformat(a['timestamp']) for a in self.activities]
            summary['date_range'] = {
                'start': min(dates).isoformat(),
                'end': max(dates).isoformat()
            }

        return summary