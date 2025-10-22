-- Migration: Create activity_reminders table
-- Created: 2025-10-22
-- Description: Adds table to store activity reminders and notification settings

CREATE TABLE IF NOT EXISTS activity_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES baby_profiles(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL CHECK (reminder_type IN ('recurring', 'scheduled', 'activity_based')),
    activity_category VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    enabled BOOLEAN DEFAULT true,

    -- For recurring reminders (e.g., every 3 hours)
    recurrence_hours INTEGER,

    -- For scheduled reminders (e.g., daily at 2:00 PM)
    scheduled_time TIME,

    -- For activity-based reminders (e.g., if no feeding in last 4 hours)
    last_activity_hours INTEGER,

    -- Tracking fields
    last_triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_recurring CHECK (
        (reminder_type != 'recurring') OR (recurrence_hours IS NOT NULL)
    ),
    CONSTRAINT valid_scheduled CHECK (
        (reminder_type != 'scheduled') OR (scheduled_time IS NOT NULL)
    ),
    CONSTRAINT valid_activity_based CHECK (
        (reminder_type != 'activity_based') OR (last_activity_hours IS NOT NULL)
    )
);

-- Create index for faster profile queries
CREATE INDEX IF NOT EXISTS idx_reminders_profile_id ON activity_reminders(profile_id);

-- Create index for enabled reminders (for scheduler queries)
CREATE INDEX IF NOT EXISTS idx_reminders_enabled ON activity_reminders(enabled) WHERE enabled = true;

-- Add comment
COMMENT ON TABLE activity_reminders IS 'Stores activity reminder configurations for baby journal';
