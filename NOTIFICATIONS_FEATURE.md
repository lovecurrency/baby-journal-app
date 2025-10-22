# Activity Reminders & Notifications Feature

## Overview

The Baby Activity Journal now supports **activity reminders and browser notifications** to help parents stay on top of their baby's care schedule. Users can create custom reminders for feeding, diaper changes, sleep, and other activities.

---

## Features

### 1. Three Types of Reminders

#### Recurring Reminders
- **Purpose:** Get notified every X hours
- **Example:** "Feed baby every 3 hours"
- **Use Case:** Regular, time-based activities

#### Scheduled Reminders
- **Purpose:** Get notified daily at a specific time
- **Example:** "Bedtime at 8:00 PM"
- **Use Case:** Daily routines at fixed times

#### Activity-Based Reminders
- **Purpose:** Get notified if no activity for X hours
- **Example:** "Remind if no feeding in last 4 hours"
- **Use Case:** Ensure minimum activity frequency

---

### 2. Browser Push Notifications

- **Real-time alerts:** Even when the tab is not focused
- **Permission-based:** User must grant notification permission
- **Category icons:** Visual indicators for different activity types
- **Interactive:** Click notification to quickly add an activity

---

### 3. Reminder Management

- **Create:** Easily create new reminders with a simple form
- **Enable/Disable:** Toggle reminders on/off without deleting
- **Delete:** Remove reminders you no longer need
- **View Status:** See when each reminder was last triggered

---

## Installation & Setup

### 1. Run Database Migration

First, create the `activity_reminders` table in your database:

```bash
python3 run_reminder_migration.py
```

This will create the necessary table with all required columns and indexes.

### 2. Install Dependencies

The feature requires APScheduler for background task scheduling:

```bash
pip install -r requirements.txt
```

This will install:
- `APScheduler==3.10.4` (for reminder checking)
- All other existing dependencies

### 3. Enable Browser Notifications

When you visit the **Reminders** page for the first time, you'll be prompted to enable browser notifications. Click "Allow" to receive reminder alerts.

---

## How to Use

### Creating a Reminder

1. Navigate to **Reminders** page (bell icon in navigation)
2. Click **"Create New Reminder"**
3. Fill in the form:
   - **Title:** Give your reminder a name (e.g., "Feed Baby")
   - **Category:** Choose activity type (feeding, diaper, sleep, etc.)
   - **Type:** Select reminder type (recurring, scheduled, or activity-based)
   - **Settings:** Configure based on type:
     - **Recurring:** Set hours between reminders
     - **Scheduled:** Set daily time
     - **Activity-Based:** Set hours since last activity
4. Click **"Create Reminder"**

### Managing Reminders

- **Toggle On/Off:** Use the switch on each reminder card
- **Delete:** Click the trash icon to remove a reminder
- **View Details:** See when reminder was last triggered

---

## Technical Architecture

### Database Schema

**Table:** `activity_reminders`

```sql
CREATE TABLE activity_reminders (
    id UUID PRIMARY KEY,
    profile_id UUID REFERENCES baby_profiles(id),
    reminder_type VARCHAR(50),  -- 'recurring', 'scheduled', 'activity_based'
    activity_category VARCHAR(50),
    title VARCHAR(200),
    message TEXT,
    enabled BOOLEAN DEFAULT true,
    recurrence_hours INTEGER,
    scheduled_time TIME,
    last_activity_hours INTEGER,
    last_triggered_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Backend Components

1. **Models** (`app/models_db.py`):
   - `ActivityReminder` dataclass
   - `ReminderType` enum

2. **Database Service** (`app/database.py`):
   - `create_reminder()`
   - `get_reminders()`
   - `update_reminder()`
   - `delete_reminder()`
   - `update_reminder_last_triggered()`

3. **Routes** (`main_db.py`):
   - `GET /reminders` - Reminder management page
   - `POST /reminders/create` - Create new reminder
   - `POST /reminders/<id>/toggle` - Enable/disable reminder
   - `POST /reminders/<id>/delete` - Delete reminder
   - `GET /api/reminders/check` - Check for pending reminders

### Frontend Components

1. **Template** (`templates/reminders.html`):
   - Reminder list view
   - Create reminder form
   - Toggle and delete controls

2. **JavaScript** (`static/js/notifications.js`):
   - `NotificationManager` class
   - Permission handling
   - Notification display
   - Automatic reminder checking (every 1 minute)

---

## API Endpoints

### Check for Pending Reminders

```http
GET /api/reminders/check
```

**Response:**
```json
{
  "reminders": [
    {
      "id": "uuid",
      "title": "Feed Baby",
      "message": "Time to feed!",
      "category": "feeding"
    }
  ]
}
```

**Logic:**
- Checks all enabled reminders for the current profile
- Determines which reminders should trigger based on type
- Returns pending notifications
- Updates `last_triggered_at` timestamp

---

## Notification Checking Logic

### Recurring Reminders
```python
if hours_since_last_trigger >= recurrence_hours:
    notify()
```

### Scheduled Reminders
```python
if current_time == scheduled_time and not_triggered_today:
    notify()
```

### Activity-Based Reminders
```python
if hours_since_last_activity >= threshold:
    notify()
```

---

## Browser Notification API

The feature uses the standard [Web Notifications API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API):

```javascript
const notification = new Notification(title, {
    body: message,
    icon: '/path/to/icon.png',
    tag: 'reminder-id',
    requireInteraction: true
});
```

---

## Permissions

### Database
- Reminders are scoped to the user's `profile_id`
- Only the profile owner can create/edit/delete their reminders

### Browser
- **Notification Permission:** Required to display browser notifications
- **Location:** Requested on first visit to Reminders page
- **Persistence:** Permission is remembered by browser

---

## Testing

### Manual Testing

1. **Create a recurring reminder** (e.g., every 1 hour)
2. **Wait for notification** to appear
3. **Check reminder status** on Reminders page
4. **Toggle reminder off** and verify no more notifications
5. **Delete reminder** and verify it's removed

### Test Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| Create recurring reminder (1 hour) | Notification after 1 hour |
| Create scheduled reminder (current time + 1 min) | Notification in 1 minute |
| Create activity-based reminder (feeding, 2 hours) | Notification if no feeding for 2 hours |
| Toggle reminder off | No notifications |
| Delete reminder | Reminder removed from list |
| Browser notification denied | Reminders still work, but no notifications |

---

## Troubleshooting

### No Notifications Appearing

1. **Check browser permission:**
   - Look for notification icon in browser address bar
   - Go to browser settings → Notifications
   - Ensure site is allowed

2. **Check reminder status:**
   - Is the reminder enabled (toggle switch on)?
   - Has enough time passed since last trigger?

3. **Check JavaScript console:**
   - Open DevTools → Console
   - Look for errors related to notifications

### Reminders Not Triggering

1. **Check database:**
   - Run migration script: `python3 run_reminder_migration.py`
   - Verify table exists: `SELECT * FROM activity_reminders;`

2. **Check reminder configuration:**
   - Verify type-specific fields are set correctly
   - Check `last_triggered_at` timestamp

### Migration Errors

If you get database errors:

```bash
# Check DATABASE_URL environment variable
echo $DATABASE_URL

# Verify database connection
python3 -c "from app.database import get_db_service; db = get_db_service(); print('Connected!')"

# Run migration with verbose output
python3 run_reminder_migration.py
```

---

## Future Enhancements

Potential improvements for future versions:

1. **Email/SMS Notifications:** Send reminders via email or SMS
2. **Snooze Feature:** Delay a reminder by X minutes
3. **Reminder Templates:** Pre-configured reminders for common scenarios
4. **Statistics:** Track reminder completion rate
5. **Smart Scheduling:** AI-suggested reminder times based on activity history
6. **Push Notifications:** PWA push notifications for mobile
7. **Multiple Profiles:** Different reminders for multiple babies

---

## Code Examples

### Creating a Reminder Programmatically

```python
from app.models_db import ActivityReminder, ReminderType, ActivityCategory

reminder = ActivityReminder(
    profile_id=journal.profile.id,
    reminder_type=ReminderType.RECURRING,
    activity_category=ActivityCategory.FEEDING,
    title="Feed Baby",
    message="Time for feeding!",
    enabled=True,
    recurrence_hours=3
)

reminder.save()
```

### Checking Reminders from JavaScript

```javascript
// Check for pending reminders
const response = await fetch('/api/reminders/check');
const data = await response.json();

data.reminders.forEach(reminder => {
    console.log(`Reminder: ${reminder.title}`);
});
```

---

## Security Considerations

1. **Profile Isolation:** Reminders are scoped to profile_id
2. **Input Validation:** All reminder fields are validated
3. **SQL Injection:** Parameterized queries prevent injection
4. **CSRF Protection:** Flask CSRF tokens (if enabled)

---

## Performance

- **Database Queries:** Indexed on `profile_id` and `enabled`
- **Check Frequency:** Every 1 minute (configurable)
- **Notification Throttling:** `last_triggered_at` prevents duplicate notifications
- **Browser API:** Lightweight, native browser notifications

---

## Browser Compatibility

| Browser | Notification Support | Tested |
|---------|---------------------|--------|
| Chrome | ✅ Yes | ✅ |
| Firefox | ✅ Yes | ✅ |
| Safari | ✅ Yes (macOS 10.14+) | ⚠️ |
| Edge | ✅ Yes | ✅ |
| Mobile Safari | ❌ Limited | ❌ |

---

## Support

For issues or questions:
1. Check this documentation
2. Review browser console for errors
3. Check database migration status
4. Create a GitHub issue with details

---

## Credits

Built with:
- **Flask** - Web framework
- **PostgreSQL** - Database
- **APScheduler** - Background task scheduling
- **Web Notifications API** - Browser notifications
- **Bootstrap 5** - UI components
- **Bootstrap Icons** - Icon library

---

**Version:** 1.0
**Last Updated:** October 2025
**Author:** Claude Code AI Assistant
