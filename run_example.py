#!/usr/bin/env python3
"""
Example script demonstrating how to use the Baby Journal App components.
"""

from datetime import datetime
from app.models import BabyProfile, ActivityJournal
from app.activity_processor import ActivityProcessor

def main():
    """Run example usage of the baby journal system."""
    print("🍼 Baby Activity Journal - Example Usage\n")

    # Create a baby profile
    print("1. Creating baby profile...")
    baby = BabyProfile(
        name="Emma",
        birth_date=datetime(2023, 6, 15),
        gender="Female"
    )
    print(f"   Created profile for {baby.name}")
    print(f"   Age: {baby.get_age_in_months()} months ({baby.get_age_in_days()} days)\n")

    # Initialize journal and processor
    journal = ActivityJournal(data_dir="example_data")
    journal.set_profile(baby)
    processor = ActivityProcessor()

    # Example messages to process
    example_messages = [
        "Emma fed 120ml bottle at 10:30am",
        "Changed wet diaper after feeding",
        "Baby napped for 1.5 hours",
        "Emma rolled over for the first time today!",
        "Temperature check: 98.4F - normal",
        "Gave vitamin D drops (400 IU)",
        "Emma weighs 7.2 kg at checkup",
        "Baby was fussy, might be teething",
        "Fed solid food - sweet potato puree",
        "Changed dirty diaper before bedtime"
    ]

    print("2. Processing example messages...")
    for i, message in enumerate(example_messages, 1):
        print(f"   {i}. {message}")
        activity = processor.process_message(message, sender="Parent")
        if activity:
            journal.add_activity(activity)
            print(f"      → Parsed as: {activity.category.value} - {activity.activity_type.value}")
        else:
            print("      → Could not parse activity")
        print()

    # Display statistics
    print("3. Activity Statistics:")
    stats = journal.get_statistics()
    print(f"   Total activities: {stats['total_activities']}")
    print("   By category:")
    for category, count in stats.get('by_category', {}).items():
        print(f"     - {category.capitalize()}: {count}")
    print()

    # Show recent activities
    print("4. Recent Activities:")
    recent = journal.get_recent_activities(limit=5)
    for activity in recent:
        timestamp = activity.timestamp.strftime("%H:%M")
        details = ""
        if activity.amount:
            details += f" ({activity.amount} {activity.unit or ''})"
        if activity.duration_minutes:
            details += f" ({activity.duration_minutes} min)"

        print(f"   {timestamp} - {activity.category.value.title()}: {activity.activity_type.value.replace('_', ' ').title()}{details}")

    print(f"\n5. Data saved to: {journal.data_dir}/")
    print("   You can now run the web app with: python app.py")

if __name__ == "__main__":
    main()