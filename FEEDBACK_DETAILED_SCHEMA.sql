-- ===============================================================================
-- ENHANCED FEEDBACK TABLE - Run in Supabase SQL Editor
-- ===============================================================================

CREATE TABLE IF NOT EXISTS feedback_detailed (
    feedback_id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    feedback_date DATE,
    
    -- LOCATION CONTEXT
    pincode VARCHAR(10),
    area_name VARCHAR(200),
    specific_land VARCHAR(50),
    tamil_season VARCHAR(100),
    weather_condition VARCHAR(100),
    
    -- MORNING MEAL
    morning_notes TEXT,
    morning_rating INT,
    morning_helped VARCHAR(20),
    morning_parsed TEXT,
    
    -- AFTERNOON MEAL
    afternoon_notes TEXT,
    afternoon_rating INT,
    afternoon_helped VARCHAR(20),
    afternoon_parsed TEXT,
    
    -- EVENING MEAL
    evening_notes TEXT,
    evening_rating INT,
    evening_helped VARCHAR(20),
    evening_parsed TEXT,
    
    -- JUNK/SNACKS
    junk_notes TEXT,
    junk_parsed TEXT,
    junk_count INT DEFAULT 0,
    
    -- OVERALL
    energy_level INT,
    digestion VARCHAR(50),
    sleep_quality VARCHAR(50),
    mood VARCHAR(50),
    
    -- AI ANALYSIS
    daily_health_score INT,
    ai_analysis TEXT,
    ai_suggestions TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- VERIFY
SELECT 'feedback_detailed' as tbl, COUNT(*) FROM feedback_detailed;
