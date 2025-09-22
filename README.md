# Baby Activity Journal

A web application that processes WhatsApp messages to track and journal baby activities like feeding, diaper changes, sleep patterns, milestones, and health records.

## Features

- **WhatsApp Integration**: Import WhatsApp chat exports to automatically parse baby activities
- **Activity Tracking**: Automatically categorizes feeding, diaper changes, sleep, milestones, health, and measurements
- **Smart Parsing**: Extracts quantities, durations, and contextual information from natural language messages
- **Web Interface**: Clean, responsive web interface for viewing and managing activities
- **Analytics**: Visual charts and statistics showing activity patterns and trends
- **Quick Entry**: Manual activity entry with smart templates
- **Data Export**: Export activities to JSON format

## Supported Activity Types

### Feeding
- Bottle feeding (with amounts in ml/oz)
- Breastfeeding (with duration)
- Solid foods

### Diaper Changes
- Wet diapers
- Dirty diapers
- General diaper changes

### Sleep
- Naps (with duration)
- Night sleep
- Wake up times

### Health & Medicine
- Temperature readings
- Symptoms
- Medications and vitamins
- Doctor visits

### Measurements
- Weight tracking
- Height/length
- Head circumference

### Milestones
- Physical milestones (rolling, crawling, walking)
- Cognitive milestones (smiling, recognition)
- Social milestones (first words, waving)

## Installation

1. **Clone or download the project**
   ```bash
   cd baby-journal-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## Usage

### Initial Setup
1. Visit the application in your browser
2. Click "Setup Baby Profile" to create your baby's profile
3. Enter name, birth date, and optional gender information

### Importing WhatsApp Messages

1. **Export WhatsApp Chat**
   - Open WhatsApp and go to the chat you want to export
   - Tap the contact/group name at the top
   - Scroll down and tap "Export Chat"
   - Choose "Without Media" (text only)
   - Save the .txt file

2. **Upload to Application**
   - Go to "Upload" section in the app
   - Select your exported .txt file
   - Click "Upload and Process"

### Manual Activity Entry
- Use "Quick Add" to manually enter activities
- Type natural language descriptions like:
  - "Baby fed 150ml bottle"
  - "Changed wet diaper"
  - "Napped for 2 hours"
  - "Baby rolled over for the first time!"

### Viewing Analytics
- Visit the "Analytics" section to see:
  - Activity distribution by category
  - Daily trends and patterns
  - Hourly activity patterns
  - Weekly patterns

## Example Messages

The parser recognizes these types of WhatsApp messages:

```
[12/25/2023, 10:30] Mom: Baby fed 150ml formula
[12/25/2023, 14:15] Dad: Changed dirty diaper
[12/25/2023, 15:00] Mom: Baby napped for 2 hours
[12/25/2023, 18:30] Grandma: Baby rolled over for the first time!
[12/25/2023, 20:00] Dad: Temperature 98.6F, all normal
```

## API Endpoints

### POST /api/activity
Add a new activity from a message:
```json
{
  "message": "Baby fed 150ml bottle",
  "sender": "Mom"
}
```

### GET /api/statistics
Get activity statistics:
```json
{
  "total_activities": 45,
  "by_category": {
    "feeding": 15,
    "diaper": 12,
    "sleep": 8
  },
  "daily_averages": {
    "feedings": 3.2,
    "diaper_changes": 2.8
  }
}
```

## Data Storage

- Activity data is stored in `data/activities.json`
- Baby profile is stored in `data/profile.json`
- Uploaded files are stored in `uploads/` directory

## Project Structure

```
baby-journal-app/
├── app/
│   ├── models.py              # Data models for activities and profiles
│   ├── whatsapp_parser.py     # WhatsApp message parsing logic
│   └── activity_processor.py  # Activity categorization and processing
├── templates/                 # HTML templates for web interface
├── static/                    # CSS and JavaScript files
├── data/                      # JSON data storage
├── uploads/                   # Uploaded WhatsApp files
├── app.py                     # Flask web application
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Development

### Adding New Activity Types
1. Add new enum values to `ActivityType` in `models.py`
2. Update `ACTIVITY_MAPPINGS` in `activity_processor.py`
3. Add corresponding category mapping in `TYPE_TO_CATEGORY`

### Customizing Parsing
- Modify keyword lists in `ACTIVITY_PATTERNS` in `whatsapp_parser.py`
- Add new quantity extraction patterns in `_extract_quantity()`
- Customize activity categorization logic in `activity_processor.py`

## Tips for Better Parsing

- Include specific keywords: "fed", "bottle", "diaper", "slept", "nap"
- Mention quantities when relevant: "150ml", "2 hours", "98.6F"
- Use consistent formatting in your WhatsApp messages
- Include context: "fussy", "happy", "first time"

## Security Note

This application is designed for personal use. For production deployment:
- Change the Flask secret key
- Add proper authentication
- Use a proper database instead of JSON files
- Add input validation and sanitization
- Use HTTPS