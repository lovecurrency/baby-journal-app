-- Migration: Create daily activity tracking tables
-- Created: 2025-10-22
-- Description: Adds tables for age-appropriate activity goals and daily progress tracking

-- Activity goals (templates based on baby's age)
CREATE TABLE IF NOT EXISTS daily_activity_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES baby_profiles(id) ON DELETE CASCADE,
    activity_key VARCHAR(100) NOT NULL,  -- e.g., "tummy_time"
    activity_title VARCHAR(200) NOT NULL,
    activity_description TEXT,
    activity_category VARCHAR(50) NOT NULL,
    age_range_min INTEGER NOT NULL,  -- Minimum age in months
    age_range_max INTEGER NOT NULL,  -- Maximum age in months
    target_count INTEGER NOT NULL,  -- Daily goal (e.g., 5 tummy time sessions)
    duration_minutes INTEGER,  -- Optional: duration per session
    icon VARCHAR(50),  -- Bootstrap icon class
    color VARCHAR(20),  -- Hex color for UI
    motivational_messages JSONB,  -- Array of messages for different progress levels
    completion_message TEXT,  -- Message when goal is reached
    benefits TEXT,  -- Why this activity is important
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 1,  -- Higher priority shows first
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(profile_id, activity_key)
);

-- Daily progress tracking
CREATE TABLE IF NOT EXISTS daily_activity_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES daily_activity_goals(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES baby_profiles(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    current_count INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP,
    streak_days INTEGER DEFAULT 0,  -- Consecutive days completed
    notes TEXT,  -- Optional notes from parent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(goal_id, activity_date)
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_activity_goals_profile ON daily_activity_goals(profile_id);
CREATE INDEX IF NOT EXISTS idx_activity_goals_age_range ON daily_activity_goals(age_range_min, age_range_max);
CREATE INDEX IF NOT EXISTS idx_activity_goals_enabled ON daily_activity_goals(enabled) WHERE enabled = true;

CREATE INDEX IF NOT EXISTS idx_activity_progress_goal ON daily_activity_progress(goal_id);
CREATE INDEX IF NOT EXISTS idx_activity_progress_profile ON daily_activity_progress(profile_id);
CREATE INDEX IF NOT EXISTS idx_activity_progress_date ON daily_activity_progress(activity_date);
CREATE INDEX IF NOT EXISTS idx_activity_progress_profile_date ON daily_activity_progress(profile_id, activity_date);

-- Add comments
COMMENT ON TABLE daily_activity_goals IS 'Age-appropriate activity goals for babies';
COMMENT ON TABLE daily_activity_progress IS 'Daily progress tracking for activities';
COMMENT ON COLUMN daily_activity_goals.motivational_messages IS 'JSON array of progress-based motivational messages';
COMMENT ON COLUMN daily_activity_progress.streak_days IS 'Number of consecutive days this activity was completed';
