"""
Age-appropriate daily activity templates with progress tracking and motivational messages.
These activities are automatically generated based on baby's current age.
"""

from typing import Dict, List

# Activity templates organized by age range (in months)
DAILY_ACTIVITY_TEMPLATES = {
    # 0-3 months
    (0, 3): [
        {
            "activity_key": "tummy_time",
            "activity_title": "Tummy Time",
            "activity_description": "Place baby on their tummy for 3-5 minutes while awake and supervised",
            "activity_category": "physical",
            "target_count": 5,
            "duration_minutes": 5,
            "icon": "bi-heart-pulse",
            "color": "#ff6b6b",
            "motivational_messages": {
                0: "Let's start tummy time today! 💪",
                1: "Great start! 4 more sessions to go",
                2: "Awesome! Halfway there! 🎉",
                3: "Amazing! Just 2 more sessions",
                4: "One more to go! {baby_name} is doing fantastic!",
                5: "🎉 Goal reached! {baby_name} is building strong muscles!"
            },
            "completion_message": "Incredible! {baby_name} completed all tummy time sessions today! Those neck and shoulder muscles are getting stronger every day. Keep up the amazing work!",
            "benefits": "Builds neck, shoulder, and core strength. Essential for motor development.",
            "priority": 1
        },
        {
            "activity_key": "face_to_face_talking",
            "activity_title": "Face-to-Face Talking",
            "activity_description": "Hold baby 8-10 inches from your face, make eye contact, smile, and talk warmly",
            "activity_category": "brain",
            "target_count": 6,
            "duration_minutes": 10,
            "icon": "bi-chat-heart",
            "color": "#4ecdc4",
            "motivational_messages": {
                0: "Time for some bonding! Talk to {baby_name} 💕",
                1: "Beautiful! 5 more conversations today",
                2: "You're doing great! Keep talking to {baby_name}",
                3: "Wonderful! Halfway done! {baby_name} loves hearing your voice",
                4: "Amazing connection! Just 2 more sessions",
                5: "One more! {baby_name}'s language skills are blooming",
                6: "🌟 Perfect! {baby_name} is learning so much from you!"
            },
            "completion_message": "Outstanding! You've connected with {baby_name} 6 times today. These conversations are building the foundation for language and emotional bonding!",
            "benefits": "Develops language skills, visual tracking, and emotional bonding.",
            "priority": 2
        },
        {
            "activity_key": "reading_together",
            "activity_title": "Reading Together",
            "activity_description": "Read simple board books with high-contrast images",
            "activity_category": "brain",
            "target_count": 3,
            "duration_minutes": 10,
            "icon": "bi-book",
            "color": "#a29bfe",
            "motivational_messages": {
                0: "Story time! Let's read to {baby_name} 📚",
                1: "Great start! 2 more reading sessions today",
                2: "Almost there! One more book to go",
                3: "📚 Perfect! {baby_name} is loving these stories!"
            },
            "completion_message": "Fantastic! Three reading sessions complete! {baby_name} is developing a love for books and learning.",
            "benefits": "Develops listening skills, language comprehension, and love for books.",
            "priority": 3
        }
    ],

    # 3-6 months
    (3, 6): [
        {
            "activity_key": "tummy_time_play",
            "activity_title": "Tummy Time with Toys",
            "activity_description": "Place colorful toys just out of reach during tummy time",
            "activity_category": "physical",
            "target_count": 5,
            "duration_minutes": 15,
            "icon": "bi-heart-pulse",
            "color": "#ff6b6b",
            "motivational_messages": {
                0: "Tummy time with toys! Let's go! 🧸",
                1: "Excellent! 4 more to strengthen those muscles",
                2: "Halfway there! {baby_name} is getting stronger",
                3: "Terrific! Just 2 more sessions today",
                4: "Almost done! One more to go! 💪",
                5: "🎉 Amazing! {baby_name} is ready to start rolling!"
            },
            "completion_message": "Wonderful! All tummy time sessions done! {baby_name}'s muscles are developing perfectly for rolling and crawling!",
            "benefits": "Strengthens muscles for rolling and crawling. Develops hand-eye coordination.",
            "priority": 1
        },
        {
            "activity_key": "peek_a_boo",
            "activity_title": "Peek-a-Boo",
            "activity_description": "Play peek-a-boo and watch baby's delighted reaction",
            "activity_category": "brain",
            "target_count": 8,
            "duration_minutes": 5,
            "icon": "bi-emoji-smile",
            "color": "#ffeaa7",
            "motivational_messages": {
                0: "Peek-a-boo time! 👀",
                1: "Fun! 7 more giggles to go",
                2: "Great! {baby_name} is learning about object permanence",
                3: "Keep going! Halfway there! 🎭",
                4: "Wonderful! 4 more peek-a-boos",
                5: "Almost there! 3 more games",
                6: "Excellent! Just 2 more",
                7: "One more! {baby_name} loves this game!",
                8: "🎉 Perfect! {baby_name}'s brain is developing beautifully!"
            },
            "completion_message": "Incredible! 8 peek-a-boo games completed! {baby_name} is understanding object permanence and cause-and-effect!",
            "benefits": "Teaches object permanence, cause and effect, memory and social interaction.",
            "priority": 2
        },
        {
            "activity_key": "texture_exploration",
            "activity_title": "Texture Exploration",
            "activity_description": "Let baby touch different safe textures",
            "activity_category": "brain",
            "target_count": 4,
            "duration_minutes": 10,
            "icon": "bi-hand-index-thumb",
            "color": "#fd79a8",
            "motivational_messages": {
                0: "Let's explore textures! 🤲",
                1: "Nice! 3 more sensory experiences today",
                2: "Great! Halfway through! {baby_name} is curious",
                3: "Almost there! One more texture to explore",
                4: "✨ Perfect! {baby_name}'s senses are developing!"
            },
            "completion_message": "Amazing! Four texture explorations done! {baby_name}'s sensory processing is developing wonderfully!",
            "benefits": "Develops sensory processing and curiosity. Builds neural connections.",
            "priority": 3
        }
    ],

    # 6-9 months
    (6, 9): [
        {
            "activity_key": "sitting_playing",
            "activity_title": "Sitting & Playing",
            "activity_description": "Practice sitting while playing with blocks or stacking cups",
            "activity_category": "physical",
            "target_count": 6,
            "duration_minutes": 15,
            "icon": "bi-box",
            "color": "#00b894",
            "motivational_messages": {
                0: "Sitting practice time! 🪑",
                1: "Good start! 5 more sitting sessions",
                2: "Excellent! {baby_name} is building core strength",
                3: "Halfway done! Balance is improving! ⚖️",
                4: "Great job! Just 2 more sessions",
                5: "One more! {baby_name} is sitting like a pro!",
                6: "🎉 Perfect! Independent sitting skills are fantastic!"
            },
            "completion_message": "Wonderful! Six sitting sessions completed! {baby_name}'s core strength and balance are developing beautifully!",
            "benefits": "Develops core strength and balance. Improves fine motor skills.",
            "priority": 1
        },
        {
            "activity_key": "crawling_encouragement",
            "activity_title": "Crawling Encouragement",
            "activity_description": "Place favorite toy just out of reach to encourage movement",
            "activity_category": "physical",
            "target_count": 5,
            "duration_minutes": 10,
            "icon": "bi-arrows-move",
            "color": "#ff6b6b",
            "motivational_messages": {
                0: "Let's encourage crawling! 🚼",
                1: "Nice! 4 more movement sessions",
                2: "Great motivation! Keep encouraging {baby_name}",
                3: "Halfway there! Movement is improving!",
                4: "Almost done! One more encouragement session",
                5: "🎉 Amazing! {baby_name} is getting ready to crawl!"
            },
            "completion_message": "Fantastic! All crawling practice done! {baby_name} is building confidence and will be mobile soon!",
            "benefits": "Motivates gross motor development. Builds confidence and persistence.",
            "priority": 2
        },
        {
            "activity_key": "baby_sign_language",
            "activity_title": "Baby Sign Language",
            "activity_description": "Practice simple signs: 'milk,' 'more,' 'all done'",
            "activity_category": "brain",
            "target_count": 10,
            "duration_minutes": 5,
            "icon": "bi-hand-index",
            "color": "#a29bfe",
            "motivational_messages": {
                0: "Sign language time! 🤟",
                1: "Good! 9 more sign practices today",
                2: "Great! {baby_name} is watching closely",
                3: "Keep going! 7 more repetitions",
                4: "Halfway there! Signs are being learned! 📖",
                5: "Excellent! 5 more signs to go",
                6: "Wonderful! 4 more practices",
                7: "Almost there! 3 more signs",
                8: "Great job! Just 2 more",
                9: "One more! {baby_name} might sign back soon!",
                10: "🌟 Perfect! Communication skills are blooming!"
            },
            "completion_message": "Outstanding! Ten sign language sessions! {baby_name} is learning to communicate and reducing frustration!",
            "benefits": "Reduces frustration, supports language development, improves communication.",
            "priority": 3
        }
    ],

    # 9-12 months
    (9, 12): [
        {
            "activity_key": "cruising_practice",
            "activity_title": "Cruising Practice",
            "activity_description": "Encourage standing and walking while holding furniture",
            "activity_category": "physical",
            "target_count": 6,
            "duration_minutes": 15,
            "icon": "bi-person-walking",
            "color": "#00b894",
            "motivational_messages": {
                0: "Let's practice cruising! 🚶",
                1: "Great start! 5 more practice sessions",
                2: "Excellent! {baby_name}'s legs are getting stronger",
                3: "Halfway there! Balance is improving!",
                4: "Wonderful! Just 2 more sessions",
                5: "One more! {baby_name} will walk soon!",
                6: "🎉 Amazing! First steps are coming!"
            },
            "completion_message": "Incredible! Six cruising sessions complete! {baby_name} is developing the balance and strength needed for walking!",
            "benefits": "Develops leg strength, balance, and coordination for independent walking.",
            "priority": 1
        },
        {
            "activity_key": "simple_puzzles",
            "activity_title": "Simple Puzzles",
            "activity_description": "Offer shape sorters or simple knob puzzles",
            "activity_category": "brain",
            "target_count": 4,
            "duration_minutes": 15,
            "icon": "bi-puzzle",
            "color": "#6c5ce7",
            "motivational_messages": {
                0: "Puzzle time! Let's solve! 🧩",
                1: "Good! 3 more puzzle sessions",
                2: "Great problem-solving! Halfway done!",
                3: "Almost there! One more puzzle",
                4: "🌟 Perfect! {baby_name} is a little genius!"
            },
            "completion_message": "Wonderful! Four puzzle sessions done! {baby_name}'s problem-solving and spatial reasoning are developing excellently!",
            "benefits": "Develops problem-solving, hand-eye coordination, and spatial reasoning.",
            "priority": 2
        },
        {
            "activity_key": "point_and_name",
            "activity_title": "Point & Name",
            "activity_description": "Point to objects and name them clearly",
            "activity_category": "brain",
            "target_count": 12,
            "duration_minutes": 5,
            "icon": "bi-cursor",
            "color": "#fdcb6e",
            "motivational_messages": {
                0: "Let's name things! 👉",
                1: "Nice! 11 more naming sessions",
                2: "Good! Vocabulary is growing",
                3: "Keep going! 9 more to go",
                4: "Great! 8 more naming moments",
                5: "Wonderful! Halfway there! 📚",
                6: "Excellent! 6 more words to learn",
                7: "Keep naming! 5 more sessions",
                8: "Great job! 4 more objects",
                9: "Almost there! 3 more",
                10: "Wonderful! Just 2 more",
                11: "One more! {baby_name}'s vocabulary is expanding!",
                12: "🎉 Perfect! Language explosion happening!"
            },
            "completion_message": "Fantastic! Twelve naming sessions completed! {baby_name}'s vocabulary is expanding rapidly!",
            "benefits": "Builds vocabulary rapidly. Develops understanding of communication and labeling.",
            "priority": 3
        }
    ]
}


def get_motivational_message(activity_messages: Dict, current_count: int, baby_name: str) -> str:
    """Get motivational message based on current progress."""
    message = activity_messages.get(current_count, "Keep going! You're doing great!")
    return message.replace("{baby_name}", baby_name)


def get_completion_message(message_template: str, baby_name: str) -> str:
    """Get completion message with baby's name."""
    return message_template.replace("{baby_name}", baby_name)


def get_activities_for_age(age_months: int) -> List[Dict]:
    """Get appropriate activities for baby's current age."""
    for (min_age, max_age), activities in DAILY_ACTIVITY_TEMPLATES.items():
        if min_age <= age_months < max_age:
            return activities

    # If age is beyond templates, return last age group
    if age_months >= 12:
        return DAILY_ACTIVITY_TEMPLATES[(9, 12)]

    return []
