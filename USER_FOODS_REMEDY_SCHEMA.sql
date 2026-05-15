-- ===============================================================================
-- USER PROFILES + DISCOVERED FOODS + REMEDY MAPPING
-- Run in Supabase SQL Editor
-- ===============================================================================

-- 1. USER PROFILES
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) UNIQUE,
    pincode VARCHAR(10),
    area_name VARCHAR(200),
    district VARCHAR(100),
    specific_land VARCHAR(50),
    date_joined DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. DISCOVERED FOODS (Auto-growing from feedback)
CREATE TABLE IF NOT EXISTS discovered_foods (
    food_id SERIAL PRIMARY KEY,
    food_name VARCHAR(200),
    food_type VARCHAR(50),
    discovered_by VARCHAR(100),
    times_mentioned INT DEFAULT 1,
    associated_symptoms TEXT,
    dosha_assessment VARCHAR(100),
    land_discovered VARCHAR(50),
    season_discovered VARCHAR(50),
    first_discovered DATE DEFAULT CURRENT_DATE,
    last_mentioned DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. REMEDY MAPPING (Food-to-Symptom effectiveness)
CREATE TABLE IF NOT EXISTS remedy_mapping (
    remedy_id SERIAL PRIMARY KEY,
    food_name VARCHAR(200),
    ingredient VARCHAR(200),
    symptom VARCHAR(200),
    dosha VARCHAR(50),
    land_type VARCHAR(50),
    season VARCHAR(50),
    times_reported INT DEFAULT 1,
    times_helped INT DEFAULT 0,
    times_partial INT DEFAULT 0,
    times_not_helped INT DEFAULT 0,
    effectiveness_percent DECIMAL(5,2) DEFAULT 0,
    last_reported DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- VERIFY
SELECT 'user_profiles' as tbl, COUNT(*) FROM user_profiles
UNION ALL SELECT 'discovered_foods', COUNT(*) FROM discovered_foods
UNION ALL SELECT 'remedy_mapping', COUNT(*) FROM remedy_mapping;
