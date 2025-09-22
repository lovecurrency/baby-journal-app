#!/usr/bin/env python3
"""
Debug specific message to see why it's not categorizing as feeding.
"""

from app.whatsapp_parser import WhatsAppParser

def debug_message():
    """Debug the specific message."""
    message = "70 ml feed - 1:18 pm - Mummy"
    print(f"Debugging message: '{message}'")

    # Test with parser
    parser = WhatsAppParser()

    # Simulate a parsed message
    from datetime import datetime
    msg_data = {
        'datetime': datetime.now(),
        'sender': 'Priyank Tiwari',
        'text': message,
        'original_message': message
    }

    activity = parser._parse_message_for_activity(msg_data)

    if activity:
        print(f"✅ Activity detected:")
        print(f"   Type: {activity['type']}")
        print(f"   Category: {activity['category']}")
        print(f"   Details: {activity.get('details', {})}")
    else:
        print("❌ No activity detected")

        # Debug keyword matching
        text = message.lower()
        print(f"Text to check: '{text}'")

        for activity_type, config in parser.ACTIVITY_PATTERNS.items():
            print(f"\nChecking {activity_type}:")
            for keyword in config['keywords']:
                if keyword in text:
                    print(f"  ✅ Found keyword: '{keyword}'")
                    return activity_type
                else:
                    print(f"  ❌ Missing keyword: '{keyword}'")

if __name__ == "__main__":
    debug_message()