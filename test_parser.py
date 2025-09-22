#!/usr/bin/env python3
"""
Test script to debug WhatsApp parsing with your specific file.
"""

from app.whatsapp_parser import WhatsAppParser
from app.activity_processor import ActivityProcessor

def test_file_parsing():
    """Test parsing the specific WhatsApp file."""
    file_path = "/Users/priyanktiwari/Downloads/_chat 2.txt"

    print("🍼 Testing WhatsApp Parser with your file...\n")

    # Test raw parsing first
    parser = WhatsAppParser()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"File content preview:")
        lines = content.split('\n')[:10]
        for i, line in enumerate(lines, 1):
            print(f"{i:2d}: {line}")
        print()

        # Try to extract messages
        messages = parser._extract_messages(content)
        print(f"Found {len(messages)} messages")

        for i, msg in enumerate(messages[:5]):  # Show first 5
            print(f"\nMessage {i+1}:")
            print(f"  Sender: {msg['sender']}")
            print(f"  Text: {msg['text']}")
            print(f"  DateTime: {msg['datetime']}")
            print(f"  Raw: {msg['raw']}")

        # Now test activity extraction using the correct parser method
        activities = []

        for msg in messages:
            activity = parser._parse_message_for_activity(msg)
            if activity:
                activities.append(activity)
                print(f"\n✅ Found activity: {activity['type']} - {activity['original_message']}")

        print(f"\n📊 Total activities found: {len(activities)}")

        if not activities:
            print("\n❌ No activities found. Testing individual messages...")

            # Test the specific feeding message
            test_message = "[21/09/25, 3:32:40 PM] Priyank Tiwari: 70 ml feed - 1:18 pm - Mummy"
            print(f"Testing: {test_message}")

            parsed = parser._parse_single_message(test_message)
            if parsed:
                print(f"✅ Message parsed successfully")
                print(f"   Sender: {parsed['sender']}")
                print(f"   Text: {parsed['text']}")

                activity = parser._parse_message_for_activity(parsed)
                if activity:
                    print(f"✅ Activity detected: {activity}")
                else:
                    print("❌ No activity detected from parsed message")
                    # Let's debug what keywords we're looking for
                    text = parsed['text'].lower()
                    print(f"   Checking text: '{text}'")
                    for activity_type, config in parser.ACTIVITY_PATTERNS.items():
                        for keyword in config['keywords']:
                            if keyword in text:
                                print(f"   Found keyword '{keyword}' for {activity_type}")
            else:
                print("❌ Message parsing failed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_file_parsing()