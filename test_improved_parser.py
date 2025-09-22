#!/usr/bin/env python3
"""
Test the improved WhatsApp parser with time extraction and feeding type detection.
"""

from app.whatsapp_parser import WhatsAppParser
from app.activity_processor import ActivityProcessor
from datetime import datetime

def test_improved_parsing():
    """Test the new features."""
    parser = WhatsAppParser()
    processor = ActivityProcessor()

    # Test messages
    test_messages = [
        "[21/09/25, 3:32:40 PM] Priyank Tiwari: 70 ml feed - 1:18 pm - Mummy",
        "[21/09/25, 4:50:15 PM] Mom: 10 ml feed - 4:45 pm - powder",
        "[21/09/25, 2:30:00 PM] Dad: Baby fed from breast at 2:20 pm",
        "[21/09/25, 6:00:00 PM] Caregiver: 120ml formula given at 5:45pm",
        "[21/09/25, 8:15:00 PM] Parent: nursing session - 8:00 pm - direct"
    ]

    print("🍼 Testing Improved Parser\n")

    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")

        # Parse the message
        parsed = parser._parse_single_message(message)
        if parsed:
            print(f"  📅 Message timestamp: {parsed['datetime']}")

            # Get activity
            activity = parser._parse_message_for_activity(parsed)
            if activity:
                print(f"  ✅ Activity detected:")
                print(f"     Type: {activity['type']}")
                print(f"     Subtype: {activity.get('subtype', 'N/A')}")
                print(f"     Activity timestamp: {activity['timestamp']}")
                print(f"     Amount: {activity['details'].get('amount', 'N/A')} {activity['details'].get('unit', '')}")

                # Convert to BabyActivity
                baby_activity = processor._convert_to_baby_activity(activity)
                print(f"     Final type: {baby_activity.activity_type.value}")
                print(f"     Category: {baby_activity.category.value}")

                # Check time extraction
                msg_time = parsed['datetime'].strftime('%H:%M')
                activity_time = baby_activity.timestamp.strftime('%H:%M')
                if msg_time != activity_time:
                    print(f"     ⏰ Time extracted from message: {msg_time} → {activity_time}")

            else:
                print("  ❌ No activity detected")
        else:
            print("  ❌ Message parsing failed")

        print()

if __name__ == "__main__":
    test_improved_parsing()